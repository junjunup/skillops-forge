"""Audit: internal markdown link sanity (LK series, AUD-200..201).

Inspired by skilllint LK001-LK002. Resolves relative markdown links against
the skill file's parent directory and emits findings when:

* the target does not exist on disk (AUD-200, medium)
* a relative link omits the leading ``./`` (AUD-201, low)

External links (``http``/``https``/``mailto``) and absolute paths are skipped.
Anchor-only links (``#section``) are also ignored.
"""

from __future__ import annotations

import re

from skillops_forge.models import AuditFinding, Severity, SkillFile

# ``[link text](target)`` — minimum-effort markdown link match. We do NOT try
# to handle escaped ``\)`` because skill files rarely use them; the audit is a
# lint, not a parser.
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

# Non-relative protocol prefixes we ignore.
_EXTERNAL_PREFIXES: tuple[str, ...] = (
    "http://",
    "https://",
    "mailto:",
    "ftp://",
    "data:",
    "tel:",
)


def audit_links(skill: SkillFile) -> list[AuditFinding]:
    """Return AuditFinding entries for broken / dotless internal links."""
    findings: list[AuditFinding] = []
    body = skill.body or ""
    if not body:
        return findings

    parent = skill.path.parent
    seen: set[tuple[str, str]] = set()  # (target, kind) — keep dedup local

    for match in _MD_LINK_RE.finditer(body):
        target = match.group(2).strip()
        # Anchor-only / external / absolute → skip
        if not target or target.startswith("#"):
            continue
        if target.lower().startswith(_EXTERNAL_PREFIXES):
            continue
        # Strip URL fragments before resolving (e.g. ``./foo.md#sec`` → ``./foo.md``).
        bare = target.split("#", 1)[0]
        if not bare:
            continue
        if bare.startswith("/"):
            # Absolute filesystem paths are not portable; skip rather than
            # try to resolve them.
            continue

        is_dotless = not bare.startswith("./") and not bare.startswith("../")
        # Resolve against the SKILL.md parent directory.
        resolved = (parent / bare).resolve()

        if not resolved.exists():
            key = ("missing", bare)
            if key not in seen:
                seen.add(key)
                findings.append(
                    AuditFinding(
                        id="AUD-200",
                        severity=Severity.MEDIUM,
                        message=f"broken internal link: '{bare}' does not resolve to an existing path.",
                        file=skill.path,
                        rule_kind="links",
                        field=bare,
                        remediation="Either create the missing file at the referenced path, or correct the link to point to an existing file.",
                        category="links",
                    )
                )
        if is_dotless:
            key = ("dotless", bare)
            if key not in seen:
                seen.add(key)
                findings.append(
                    AuditFinding(
                        id="AUD-201",
                        severity=Severity.LOW,
                        message=f"relative link '{bare}' omits the leading './'.",
                        file=skill.path,
                        rule_kind="links",
                        field=bare,
                        remediation=f"Prefix relative paths with './' for explicit relativity (e.g. './{bare}').",
                        category="links",
                    )
                )

    return findings


__all__ = ["audit_links"]
