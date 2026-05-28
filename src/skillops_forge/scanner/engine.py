"""Scanner engine: rule loading + per-file dispatch."""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml

from skillops_forge.exceptions import RuleLoadError
from skillops_forge.models import SecurityFinding, SkillFile
from skillops_forge.scanner.rule import Rule

_BUILTIN_RULES_PACKAGE = "skillops_forge.rules"


class ScannerEngine:
    """Loads rules and applies them against :class:`SkillFile` instances."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules: tuple[Rule, ...] = tuple(rules)

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Return the loaded rules."""
        return self._rules

    @classmethod
    def from_builtins(cls) -> ScannerEngine:
        """Load every YAML file shipped under ``skillops_forge/rules``."""
        rules: list[Rule] = []
        package = files(_BUILTIN_RULES_PACKAGE)
        for entry in package.iterdir():
            if not entry.name.endswith(".yaml"):
                continue
            with as_file(entry) as concrete_path:
                rules.extend(_parse_rule_file(Path(concrete_path)))
        rules.sort(key=lambda r: r.id)
        return cls(rules)

    @classmethod
    def from_dirs(cls, rule_dirs: list[Path]) -> ScannerEngine:
        """Load rules from one or more directories of ``*.yaml`` files."""
        rules: list[Rule] = []
        for d in rule_dirs:
            if not d.is_dir():
                raise RuleLoadError(f"rule directory does not exist: {d}")
            for f in sorted(d.glob("*.yaml")):
                rules.extend(_parse_rule_file(f))
        rules.sort(key=lambda r: r.id)
        return cls(rules)

    def scan(self, skill: SkillFile) -> list[SecurityFinding]:
        """Apply every rule to ``skill`` and return deduplicated findings.

        Two-stage dedup so the same evidence is never reported twice:

        1. **Strong key** ``(rule_id, file_posix, line, matched_text)`` — kept
           for the canonical body scan; line is reliable here.
        2. **Weak key** ``(rule_id, file_posix, matched_text)`` — applied
           across the union of all targets. The body scan registers its
           weak key first; later target domains (``frontmatter`` /
           ``examples``) skip a finding when the same matched text was
           already reported on the same file. This stops the previous
           failure mode where the same ``sudo`` mention was reported once
           in body and again as the same line being re-scanned inside an
           example fenced block.
        """
        line_keys: set[tuple[str, str, int, str]] = set()
        text_keys: set[tuple[str, str, str]] = set()
        out: list[SecurityFinding] = []
        for rule in self._rules:
            for finding in rule.match(skill):
                rid = finding.rule_id or finding.id
                file_posix = finding.file.as_posix()
                strong = (rid, file_posix, finding.line, finding.matched_text)
                weak = (rid, file_posix, finding.matched_text)
                if strong in line_keys or weak in text_keys:
                    continue
                line_keys.add(strong)
                text_keys.add(weak)
                out.append(finding)
        return out


def _parse_rule_file(path: Path) -> list[Rule]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError as exc:
        raise RuleLoadError(f"bad YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise RuleLoadError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuleLoadError(f"rule file root must be a mapping: {path}")
    items: Any = raw.get("rules", [])
    if not isinstance(items, list):
        raise RuleLoadError(f"'rules' must be a list in {path}")
    rules: list[Rule] = []
    for entry in items:
        if not isinstance(entry, dict):
            raise RuleLoadError(f"rule entry must be a mapping in {path}")
        # Coerce list `targets` → tuple via pydantic validator
        try:
            rules.append(Rule.model_validate(entry))
        except Exception as exc:  # pragma: no cover - re-raise as RuleLoadError
            raise RuleLoadError(f"invalid rule {entry.get('id')!r} in {path}: {exc}") from exc
    return rules


__all__ = ["ScannerEngine"]
