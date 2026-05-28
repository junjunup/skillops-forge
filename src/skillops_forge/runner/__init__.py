"""Examples dry-run subsystem.

**Hard rule**: this module MUST NEVER call :func:`subprocess.run` or any other
function that actually launches a process. The runner only performs static
inspection of example commands.
"""

from __future__ import annotations

from skillops_forge.models import ExampleRun, SkillInventory
from skillops_forge.runner.dry_run import dry_run_example


def run_examples(inventory: SkillInventory) -> list[ExampleRun]:
    """Run dry-run analysis over every example in every file."""
    runs: list[ExampleRun] = []
    for skill in inventory.files:
        for example in skill.examples:
            runs.append(dry_run_example(skill_path=skill.path, example=example))
    return runs


__all__ = ["run_examples"]
