# SkillOps Forge

> **Static security & risk auditor for AI Agent skill packs.**
> Offline CLI for `SKILL.md`, `CLAUDE.md`, and `.cursor/rules/*.mdc` —
> 19 plaintext-pattern security rules + 27 audit rules, zero LLM,
> zero `subprocess`.

[![CI](https://img.shields.io/badge/CI-pending-lightgrey)]()
[![PyPI](https://img.shields.io/badge/PyPI-skillops--forge-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.1-informational)]()

## Why another tool?

The skill ecosystem already has structural linters and quality scorers. None of
them treat **AI-era attack surfaces** — agent memory exfiltration, identity-file
reads, prompt-injection keywords, hidden zero-width payloads — as first-class
detections.

| Tool | Form | Focus | Security rules | Offline | LLM-era checks |
| --- | --- | --- | --- | --- | --- |
| `skilllint` | CLI | structural lint, cross-platform | partial (pattern-level) | ✓ | ✗ |
| `skill-tester` | CLI | AST + sample exec + quality scoring | ✗ | ✓ | ✗ |
| `skillcheck` | CLI | frontmatter-only validator | ✗ | ✓ | ✗ |
| `claude-skill-check` | GH Action | secrets in skill body | 7 secret patterns | ✓ | ✗ |
| `kevinsong0/skills-vetter` | Prompt skill | LLM-driven vetting | qualitative | ✗ (needs LLM) | partial |
| **`skillops-forge`** | **CLI + GH Action** | **lint + plaintext-pattern security hint + score + report** | **19 plaintext rules** | **✓** | **✓** |

SkillOps Forge ships dedicated rules for *agent-private* files
(`MEMORY.md`, `USER.md`, `SOUL.md`, `IDENTITY.md`, `~/.workbuddy/memory`),
combined with an auditor, a deterministic scorer, a CRITICAL-veto policy, and
self-contained HTML/Markdown/JSON reports.

> **Disclaimer.** Risk-assistance only. A passing score reduces obvious failure
> modes; it does not certify safety. **Read the [Limitations](#limitations)
> section below before relying on this tool as a security gate.**

## Limitations

SkillOps Forge is a **plaintext-pattern static linter**, not a full security
solution. We were tested under adversarial conditions — here is what it can
and cannot do, in plain terms:

### What it does well
- Catches **plaintext occurrences** of the 19 documented patterns (`curl | sh`,
  `sudo`, `eval(`, `~/.ssh/id_rsa`, `MEMORY.md` references, etc.) when the
  attacker writes them in the canonical, unobfuscated form.
- Surfaces **structural and naming issues** in skill packs (frontmatter
  schema, kebab-case names, token budgets, missing trigger phrases).
- Generates **deterministic, machine-readable reports** that are stable
  enough to use as PR-blocking CI gates for honest authors.

### What it does not do — bypass scenarios we verified
The following techniques **defeat** SkillOps Forge today:

| Bypass | What slips through |
| --- | --- |
| Unicode confusables (`ѕudo` with Cyrillic `ѕ` U+0455) | SEC-006 misses; only SEC-005 may catch the trailing `rm` |
| `bash -c "$(curl …)"` instead of `curl … \| sh` | SEC-001 misses; only SEC-010 medium domain hint fires |
| `curl -o /tmp/x && sh /tmp/x` (download-then-execute) | SEC-001 misses |
| `python -c "exec(urlopen(...).read())"` | SEC-001 misses |
| `__import__("builtins").exec(payload)` | SEC-014 misses; **SEC-018 catches it** |
| `getattr(__builtins__, 'ev'+'al')(payload)` | SEC-014 misses; **SEC-018 + SEC-019 catch it** |
| Base64-encoded payload split across two strings | SEC-008 / SEC-013 miss unless one half is long-enough alone |

The fundamental constraint: **regex-based plaintext scanning cannot read
intent.** Determined attackers can always reach an obfuscation layer that
defeats finite pattern sets. SEC-018 and SEC-019 (added in 0.2.1) close the
two most common reflection / string-concat bypasses, but the list is not
exhaustive and never will be.

### Recommended posture
- Use this tool as **one signal among several**, not as a sole security
  gate. Pair it with code review, runtime sandboxing, and source-trust
  evaluation.
- Treat a **clean SkillOps Forge run** as "no obvious red flag in plaintext",
  not as "this skill is safe".
- Treat a **failed run** as "review required before install", not as proof
  of malicious intent — false positives exist and are documented.
- For high-stakes targets (skills handling credentials, money, system
  config), do not skip a human review even on a green run.

### Out of scope
- AGENTS.md / Codex `agents.json` files — not parsed.
- Python AST / runtime sample execution — not implemented (red line:
  no `subprocess`, no LLM, no untrusted code execution).
- Network reputation lookup of domains in skill bodies — fully offline.
- Cryptographic signature verification of skill packs — not implemented.

We will keep growing the bypass coverage in future releases and explicitly
list each new defense + each known limitation in `CHANGELOG.md`.

## Quick Start (30 seconds)

```bash
# from source (until PyPI release)
pip install -e ".[dev]"

# verify install
skillops --help          # 3 commands
skillops version         # skillops-forge 0.1.3

# scan a skill (or a whole skill repo)
skillops scan ./my-skill --report all

# bootstrap a CI workflow that fails the PR if score drops below 70
skillops init-ci --github-actions
```

Reports land in `./reports/` by default:

| File | Purpose |
| --- | --- |
| `reports/skillops-report.html` | Self-contained HTML (drop into a README, share as artifact) |
| `reports/skillops-report.md` | Markdown summary (PR comment friendly) |
| `reports/skillops-result.json` | Machine-readable, schema-stable (CI artifact) |

## CLI

```text
skillops scan PATH [--report md|html|json|all] [--out-dir DIR]
                   [--threshold 70] [--no-cursor-rules] [--no-runner] [-v]
skillops init-ci [--github-actions / --no-github-actions]
                 [--out FILE] [--force]
skillops version
```

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Pass (score ≥ threshold AND zero CRITICAL findings) |
| 1 | Audit failed (below threshold or any CRITICAL finding) |
| 2 | User error (bad path, bad arguments) |
| 3 | Internal error (rare; malformed YAML now degrades to a finding) |

## What gets checked

### 19 security rules (SEC-001 → SEC-019)

| ID | Severity | Detection |
| --- | --- | --- |
| SEC-001 | critical | Remote script piped to shell (`curl … \| sh`) |
| SEC-002 | high | Download-then-execute (`wget -O … && bash`) |
| SEC-003 | critical | Sensitive credential file path (`~/.ssh`, `~/.aws`, `id_rsa`, `.netrc`) |
| SEC-004 | high | Implicit credential env-var read (`AWS_*`, `OPENAI_API_KEY`, `GITHUB_TOKEN`) |
| SEC-005 | critical | Destructive shell command (`rm -rf /`, `dd if=`, `mkfs`, fork bomb) |
| SEC-006 | high | Privilege escalation (`sudo`, `chmod 777`, `chown -R root`) |
| SEC-007 | high | Hidden zero-width characters (U+200B/200C/200D/FEFF) |
| SEC-008 | medium | Long base64 / high-entropy blob (heuristic) |
| SEC-009 | high | Prompt-injection keyword (`ignore previous instructions`, `jailbreak`) |
| SEC-010 | medium | Exfiltration to non-allowlisted domain |
| SEC-011 | high | Shell injection via unsanitized variable |
| **SEC-012** | **critical** | **Agent identity / memory file access** (`MEMORY.md`, `USER.md`, `SOUL.md`, `IDENTITY.md`, `CLAUDE.md`, `~/.workbuddy/memory`) |
| SEC-013 | high | Base64 / hex decode action (`base64 -d`, `atob(`, `fromCharCode`) |
| SEC-014 | high | Dynamic execution (`eval(`, `exec(`, `Function(...)`) |
| SEC-015 | high | Network call to a raw IPv4 address |
| SEC-016 | critical | Browser cookie / Login Data / saved-credential access |
| SEC-017 | high | Writes to system / privileged paths (`/etc`, `/usr`, `C:\Windows`) |
| SEC-018 | high | Reflective dynamic execution (`getattr(__builtins__, ...)`, `__import__("builtins").exec`) |
| SEC-019 | high | String-concatenated `eval` / `exec` / `compile` name (e.g. `'ev'+'al'`) |

### Structural audit (auditor)

`frontmatter` (required + recommended fields), `description` (length + trigger
phrasing), `permissions` (declared `allowed-tools` vs. detected shell usage),
`io_schema` (Inputs / Outputs sections), `examples` (≥1 fenced block, runnable).

### Runner

Examples are *interpreted, never executed*. The runner uses `shlex` plus a strict
allow / deny list, and the test suite asserts `subprocess.run`, `Popen`,
`check_call`, and `check_output` are never invoked.

## Reports

Each report includes (since 0.1.2):

- **Score / Risk / Threshold / Result** — with a `⚠️ PASSED WITH CAUTION` middle
  state when score ≥ threshold but a HIGH finding exists.
- **Recommended Action** — risk-tier-mapped guidance (e.g. CRITICAL →
  *“DO NOT INSTALL. Address all critical findings first.”*).
- **Permissions Summary** — auto-extracted *Files Read / Files Write /
  Commands / Network* from the skill body and examples.
- **Inventory / Findings / Examples Dry-Run / Compliance Checklist**.

## Scoring

```
score = max(0, 100 - Σ(weight × count))
weights: critical=25, high=12, medium=5, low=2, info=0
```

A single CRITICAL finding sets `is_passed = false` regardless of score (one-vote
veto). The CRITICAL veto applies to both `audit_findings` and
`security_findings`; `is_passed` is a Pydantic v2 `@computed_field` so JSON,
Markdown and HTML reports stay in sync automatically.

## CI in one line

```bash
skillops init-ci --github-actions
```

Generates `.github/workflows/skillops.yml` with **pinned**
`actions/checkout@v4` and `actions/setup-python@v5`, an artifact upload, and a
`fail-under` threshold (default `70`). Default policy refuses to overwrite an
existing workflow; pass `--force` to replace it.

## Real-world example

Running SkillOps Forge against 37 skills installed on a developer machine
(`~/.workbuddy/skills/`) surfaced two **true-positive** CRITICAL findings:

| Skill | Finding | Evidence |
| --- | --- | --- |
| `proactive-agent` | SEC-012 × 2 | `Read SOUL.md` / `Read USER.md` (lines 499–500) |
| `humanizer` | AUD-000 (CRITICAL) | Multi-line YAML description without quoting (parser degrades gracefully instead of crashing) |

The full distribution: 2 critical · 1 high · 3 medium · 9 low · 22 info.
See `docs/v0.1.2-improvements.md` for the rule-by-rule rationale.

## Design red lines

1. **Never `subprocess`** — the runner has zero `subprocess` import; tests
   monkey-patch and assert non-invocation.
2. **Fully offline** — no network calls (not even GitHub API); `init-ci`
   only writes a template file.
3. **Never upload user content** — every byte of analysis stays local.
4. **Never execute risky commands** — examples are interpreted via `shlex`
   plus an allow / deny list; `curl … | sh` is intercepted.
5. **Risk-assistance, not certification** — explicit disclaimer in every
   report.

## Project layout

```
skillops-forge/
├── src/skillops_forge/
│   ├── parser/        # SKILL.md / CLAUDE.md / .cursor/rules
│   ├── auditor/       # frontmatter / description / permissions / io / examples
│   ├── scanner/       # rule loader + dedup engine
│   ├── runner/        # shlex-based dry-run, never subprocess
│   ├── reporter/      # md / html / json + scoring
│   ├── pipeline.py    # parser → audit → scan → run → score → report
│   ├── plugins/       # PluginProtocol (P1: LLM judge, cross-format export)
│   ├── rules/         # YAML data-driven SEC rules
│   ├── templates/     # Jinja2 (HTML/MD reports + GH Actions yaml)
│   └── ci/            # init-ci generator
├── tests/             # 147 tests, 92 % coverage (scanner ≥95 %)
├── docs/              # architecture, rules, schema, qa-report
└── pyproject.toml
```

## License

[MIT](LICENSE) · See [README_CN.md](README_CN.md) for 中文版.
