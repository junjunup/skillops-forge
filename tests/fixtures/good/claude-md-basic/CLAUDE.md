---
name: claude-md-basic
---

# CLAUDE.md — Project Notes

## Overview

This project uses pytest for testing and ruff for linting. Run `pytest -q` to
verify the suite, and `ruff check .` to lint the codebase.

## Inputs

The agent should accept a path to a directory and return a list of issues.

## Outputs

A JSON-shaped list of issues with severity and message.

## Examples

```bash
pytest -q
ruff check .
```
