---
name: skill-md-permissioned
description: Use this skill when the user wants to commit staged changes with a conventional-commits style message. The skill carefully scopes its tool access to git only.
version: 0.1.0
author: skillops-forge tests
allowed-tools: [Bash, Read]
---

# Skill: Conventional Commit Helper

Use this skill when you have staged changes and want a tidy conventional-commits
message. The skill never amends history and never force-pushes.

## Inputs

- `subject` (string): commit subject following `type(scope): description`.
- `body` (string, optional): longer body.

## Outputs

A single git commit on the current branch.

## Examples

```bash
git status --short
git diff --staged
git commit -m "feat(scan): add zero-width detector"
```
