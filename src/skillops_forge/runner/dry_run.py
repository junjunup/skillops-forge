"""Static dry-run for fenced-code example blocks.

Implementation guarantee: never spawns a child process. Only string analysis.
"""

from __future__ import annotations

from pathlib import Path

from skillops_forge.models import Example, ExampleRun, SecurityFinding, Severity
from skillops_forge.runner.interceptors import inspect_command


def dry_run_example(*, skill_path: Path, example: Example) -> ExampleRun:
    """Statically inspect an example, building an :class:`ExampleRun`.

    Args:
        skill_path: Path to the originating skill file.
        example: The example block to analyze.

    Returns:
        An :class:`ExampleRun`. ``success`` is False when any blocker fires.
    """
    blocked: list[SecurityFinding] = []
    log_lines: list[str] = []
    log_lines.append(f"# dry-run for: {example.title or '(untitled)'}")
    if not example.commands:
        log_lines.append("# no shell commands in this block — nothing to dry-run")
        return ExampleRun(
            example_title=example.title,
            file=skill_path,
            success=True,
            blocked_actions=(),
            dry_run_log="\n".join(log_lines),
        )
    for cmd in example.commands:
        log_lines.append(f"$ {cmd}")
        verdict = inspect_command(cmd, skill_path=skill_path)
        log_lines.append(f"  -> verdict: {verdict.kind} ({verdict.reason})")
        if verdict.severity is not None:
            blocked.append(
                SecurityFinding(
                    id="RUN-001",
                    rule_id="RUN-001",
                    severity=verdict.severity,
                    message=f"dry-run blocked: {verdict.reason}",
                    file=skill_path,
                    line=0,
                    column=0,
                    remediation=verdict.remediation,
                    category="runner",
                    matched_text=cmd[:120],
                    engine="heuristic",
                )
            )
    success = all(f.severity not in {Severity.CRITICAL, Severity.HIGH} for f in blocked)
    return ExampleRun(
        example_title=example.title,
        file=skill_path,
        success=success,
        blocked_actions=tuple(blocked),
        dry_run_log="\n".join(log_lines),
    )


__all__ = ["dry_run_example"]
