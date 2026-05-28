# SkillOps Forge — Built-in Rules

This document is the canonical reference for the rules shipped under
`src/skillops_forge/rules/*.yaml`. The set is intentionally small (P0 only) to
keep false-positive rates predictable.

| Rule ID | Name | Severity | Engine | Targets |
|---|---|---|---|---|
| SEC-001 | Remote script piped to shell | critical | regex | body, examples, all |
| SEC-002 | Download-then-execute pattern | high | regex | body, examples, all |
| SEC-003 | Sensitive credential file path | critical | regex | body, examples, all |
| SEC-004 | Implicit credential env-var read | high | regex | body, examples, all |
| SEC-005 | Destructive shell command | critical | regex | body, examples, all |
| SEC-006 | Privilege escalation / over-permissive chmod | high | regex | body, examples, all |
| SEC-007 | Hidden zero-width characters | high | heuristic | body, frontmatter, all |
| SEC-008 | Suspicious long base64 / high-entropy blob | medium | heuristic | body, examples, all |
| SEC-009 | Prompt injection keyword | high | keyword | body, frontmatter, all |
| SEC-010 | Exfiltration to non-allowlisted domain | medium | heuristic | body, examples, all |
| SEC-011 | Shell injection via unsanitized variable | high | regex | body, examples, all |

## Severity → Score Weight

| Severity | Weight |
| -------- | -----: |
| critical | 25 |
| high | 12 |
| medium | 5 |
| low | 2 |
| info | 0 |

A single CRITICAL finding sets `passed = false` regardless of the score.

## Audit Rules (Structural)

| Rule ID | Severity | Trigger |
| --- | --- | --- |
| AUD-001 | high | `SKILL.md` is missing YAML frontmatter |
| AUD-002 | high | required field missing in frontmatter (`name`, `description`) |
| AUD-003 | low | recommended field missing (e.g. `name` in `CLAUDE.md`) |
| AUD-010 | medium | `description` shorter than 30 characters |
| AUD-011 | low | `description` longer than 1024 characters |
| AUD-012 | low | `description` lacks trigger phrasing |
| AUD-020 | medium | shell example present but `allowed-tools` is empty |
| AUD-021 | high | `allowed-tools` uses wildcard (`*`, `all`, `any`) |
| AUD-030 | low | no `Inputs/Outputs` sections documented |
| AUD-040 | low | no fenced example blocks |

## Customization

You can pass `--rule-dir` to `skillops scan` (programmatic API:
`run_scan(inventory, rule_dirs=[...])`) to load additional rule packs without
patching the package.

## Roadmap

- SEC-012 — Auto-install via `sudo apt-get install -y` without verification
- SEC-013 — SSH reverse shell (`bash -i >& /dev/tcp/...`)
- SEC-014 — Implicit `chmod +x` of remotely-fetched files
