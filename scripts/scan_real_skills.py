"""Scan every real skill under a skills root, robustly.

Defaults to ``~/.workbuddy/skills/`` so it works on any developer's machine.
Override with environment variables when needed::

    SKILLOPS_REAL_SKILLS_ROOT=/path/to/skills \
    SKILLOPS_REAL_SKILLS_OUT=/tmp/out \
    SKILLOPS_BIN=/path/to/skillops \
    python scripts/scan_real_skills.py

Even if a single skill has malformed frontmatter we keep scanning the rest
and record the failure as ``PARSE_ERROR`` in ``summary.json``.
"""

from __future__ import annotations

import json
import os
import subprocess  # noqa: S404 — calling our own bundled CLI, not user input
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILLS_ROOT = Path(
    os.environ.get(
        "SKILLOPS_REAL_SKILLS_ROOT",
        str(Path.home() / ".workbuddy" / "skills"),
    )
)
OUT_ROOT = Path(
    os.environ.get(
        "SKILLOPS_REAL_SKILLS_OUT",
        str(REPO_ROOT / "reports" / "real-skills"),
    )
)
_default_cli = REPO_ROOT / ".venv" / "Scripts" / "skillops.exe"
if not _default_cli.exists():
    _default_cli = REPO_ROOT / ".venv" / "bin" / "skillops"
SKILLOPS = Path(os.environ.get("SKILLOPS_BIN", str(_default_cli)))

if not SKILLS_ROOT.is_dir():
    print(f"skills root not found: {SKILLS_ROOT}", file=sys.stderr)
    sys.exit(2)
if not SKILLOPS.exists():
    print(
        f"skillops CLI not found: {SKILLOPS}\n"
        "Install with `pip install -e .` and re-run, or set SKILLOPS_BIN.",
        file=sys.stderr,
    )
    sys.exit(2)

OUT_ROOT.mkdir(parents=True, exist_ok=True)

results = []
for skill_dir in sorted(SKILLS_ROOT.iterdir()):
    if not skill_dir.is_dir():
        continue
    name = skill_dir.name
    out_dir = OUT_ROOT / name.replace(" ", "_")
    out_dir.mkdir(exist_ok=True)
    proc = subprocess.run(
        [str(SKILLOPS), "scan", str(skill_dir), "--report", "json", "--out-dir", str(out_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    json_path = out_dir / "skillops-result.json"
    if proc.returncode == 3 or not json_path.exists():
        results.append({
            "skill": name,
            "exit": proc.returncode,
            "score": None,
            "risk": "PARSE_ERROR",
            "passed": False,
            "audit": None,
            "security": None,
            "error": (proc.stderr or proc.stdout).strip().splitlines()[-1][:200] if (proc.stderr or proc.stdout) else "unknown",
        })
        continue
    data = json.loads(json_path.read_text(encoding="utf-8"))
    results.append({
        "skill": name,
        "exit": proc.returncode,
        "score": data.get("score"),
        "risk": data.get("overall_risk"),
        "passed": data.get("is_passed"),
        "audit": len(data.get("audit_findings", [])),
        "security": len(data.get("security_findings", [])),
        "error": None,
    })

# 摘要
total = len(results)
parse_err = sum(1 for r in results if r["risk"] == "PARSE_ERROR")
passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if r["passed"] is False and r["risk"] != "PARSE_ERROR")

print(f"\n{'='*78}")
print(f"扫描真实 skills 仓库：{SKILLS_ROOT}")
print(f"{'='*78}")
print(f"共扫描：{total}  | 通过：{passed}  | 不通过：{failed}  | parse 失败：{parse_err}")
print(f"{'='*78}\n")

# 按 risk 分组打印
risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4, "PARSE_ERROR": 5, None: 6}
results.sort(key=lambda r: (risk_order.get(r["risk"], 9), -(r["score"] or 0)))

print(f"{'Skill':<45} {'Score':>6} {'Risk':>10} {'Pass':>5} {'Aud':>4} {'Sec':>4}")
print("-" * 78)
for r in results:
    score = r["score"] if r["score"] is not None else "  -"
    risk = r["risk"] or "-"
    passed_s = "yes" if r["passed"] else ("no" if r["passed"] is False else "-")
    aud = r["audit"] if r["audit"] is not None else "-"
    sec = r["security"] if r["security"] is not None else "-"
    print(f"{r['skill'][:44]:<45} {score!s:>6} {risk:>10} {passed_s:>5} {aud!s:>4} {sec!s:>4}")
    if r["error"]:
        print(f"  └─ {r['error'][:100]}")

# 保存 summary
summary_path = OUT_ROOT / "summary.json"
summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n汇总保存到：{summary_path}")
