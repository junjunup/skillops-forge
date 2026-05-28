---
name: skill-md-basic
description: Use this skill when the user wants a Hello World demonstration in Python. Provides a minimal verified example without any side effects.
version: 0.1.0
author: skillops-forge tests
allowed-tools: [Read]
---

# Skill: Hello World Demo

Use this skill when you need to verify the toolchain end-to-end with a tiny,
side-effect-free Python script. The demo only prints to stdout and returns 0.

## Inputs

- `name` (string, optional): Person to greet. Defaults to `world`.

## Outputs

A single line of text on stdout.

## Examples

```python
print("hello, world")
```

## Notes

This skill is intentionally tiny so it can be used as a smoke test. It does not
reach the network and does not write to disk.
