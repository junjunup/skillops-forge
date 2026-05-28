---
name: rm-rf-root
description: Use this skill when the user wants to wipe the entire filesystem (BAD example, do not do this).
allowed-tools: [Bash]
---

# Skill: Filesystem Wipe (BAD)

Triggers SEC-005 because of the destructive command below.

## Examples

```bash
rm -rf /
```
