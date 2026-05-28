---
name: skill-md-with-examples
description: Use this skill when the user wants to format JSON files in place. The skill demonstrates a typical read → transform → write pipeline using only standard library tools.
version: 0.1.0
author: skillops-forge tests
allowed-tools: [Read, Write]
---

# Skill: JSON Formatter

Use this skill when you need to pretty-print one or more JSON files in place.
The skill operates only on files explicitly passed as arguments.

## Inputs

- `paths` (list[string]): files to format.

## Outputs

In-place rewrites with stable two-space indentation.

## Examples

```python
import json
from pathlib import Path

def format_file(path: str) -> None:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

```bash
python -m json.tool input.json > output.json
```
