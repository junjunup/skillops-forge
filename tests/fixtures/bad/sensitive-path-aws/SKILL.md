---
name: sensitive-path-aws
description: Use this skill when you want to read AWS credentials from disk. (BAD example.)
allowed-tools: [Read]
---

# Skill: AWS Credential Reader (BAD)

Reads credentials from `~/.aws/credentials`. Triggers SEC-003.

## Examples

```bash
cat ~/.aws/credentials
```
