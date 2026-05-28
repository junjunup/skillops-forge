"""Export the SkillReport JSON schema to ``docs/schema/skillops-result.schema.json``."""

from __future__ import annotations

import json
from pathlib import Path

from skillops_forge.models import SkillReport


def main() -> None:
    """Write the schema and report a summary."""
    schema = SkillReport.model_json_schema()
    target = Path(__file__).resolve().parents[1] / "docs" / "schema" / "skillops-result.schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
