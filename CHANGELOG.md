# Changelog

All notable changes to **SkillOps Forge** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-05-28

### Honesty release

This release was triggered by a third-party blind audit of 0.2.0
(`docs/blind-audit-2026-05-28.md`). The audit verified two structural P0
defects, four P1 defects, and several over-promised claims in the README.
We refuse to ship demo-grade code or marketing dressed up as capability,
so this release fixes the documented issues and tightens the language.

### Fixed (P0 from blind audit)

- **Scanner dedup no longer fails when the same evidence appears in
  multiple target domains.** ``scanner/engine.py:scan`` now uses a
  two-stage dedup (strong key with line, weak key without). The previous
  implementation reported a single ``sudo`` mention twice (once in body,
  once in the example fenced block extracted from that body), distorting
  the score. Verified on the real ``skill-vetter`` dataset: the same
  evidence now contributes a single finding and a single score deduction.
- **Frontmatter / examples line numbers no longer report a virtual
  offset.** ``scanner/rule.py`` now emits ``line=0, column=0`` for
  ``frontmatter`` and ``examples`` target hits. The previous behaviour
  returned the offset inside the flattened-string scan space, which did
  not map back to the SKILL.md source — a misleading number.

### Added (P1 from blind audit)

- **SEC-018 — Reflective dynamic execution.** Catches
  ``getattr(__builtins__, "exec")(payload)``,
  ``__import__("builtins").exec``, ``vars(__builtins__)["eval"]``.
- **SEC-019 — String-concatenated eval / exec / compile names.** Catches
  obfuscation patterns like ``'ev' + 'al'``, ``"ex" + "ec"``,
  ``'comp' + 'ile'``.
- After these additions, all 8 ``eval`` / ``exec`` bypass scenarios that
  defeated 0.2.0 are now caught by SEC-014 + SEC-018 + SEC-019.
- The README now lists every remaining bypass scenario (Unicode
  confusables, ``bash -c "$(curl …)"``, two-step ``curl -o && sh``,
  ``python -c "exec(urlopen())"``, base64 split blobs) under the new
  **Limitations** section. We will not pretend this list is empty.

### Fixed (P1 from blind audit — false positives)

- ``auditor/description.py`` AUD-013 (description < 30 chars) is now
  silenced when AUD-121 (description < 20 chars) is already firing on
  the same text. Same defect, single finding.
- ``auditor/disclosure.py`` AUD-300 / AUD-301 / AUD-302 only fire when
  the SKILL.md body has more than 200 lines — single-file simple skills
  no longer get three "missing references/examples/scripts/" warnings
  that are demonstrably noise. Empty placeholder directories are now
  treated as "missing" so authors cannot game the check with a
  ``.gitkeep`` file.

### Changed — README / README_CN

- Removed unsupported ``AGENTS.md`` claim (parser does not match it).
- Replaced "static security & risk auditor" with "static lint +
  risk-hint auditor" in the tagline. The tool catches plaintext patterns,
  not obfuscated code; the tagline now reflects that.
- Replaced "first CLI for agent identity files" with a plain capability
  description. Marketing claims that ranked the project against named
  competitors are kept, but the disputed superlatives are removed.
- Added a full **Limitations** section listing what the tool does well,
  what it cannot do (with a concrete bypass table), the recommended
  posture, and the explicit out-of-scope list. README and README_CN are
  in sync.

### Internal

- ``rule_catalog._security_rules`` is unchanged — it still introspects
  the YAML-loaded engine, so SEC-018 / SEC-019 surface in
  ``skillops rules`` without manual edits.

### Sources

- Third-party blind audit feedback (`docs/blind-audit-2026-05-28.md`).
- skilllint by jamie-bitflight (MIT) and skillcheck by joacanovaro (MIT)
  remain credited (already acknowledged in 0.1.4 / 0.2.0 entries).

## [0.2.0] - 2026-05-28

### Added — five v0.2 enhancements derived from skilllint / skillcheck source review

#### F. `docs_url` + `suggestion` enrichment on every finding
- ``Finding`` now exposes ``docs_url`` (auto-populated to
  ``https://github.com/junjunup/skillops-forge/blob/main/docs/rules/<RULE_ID>.md``)
  and ``suggestion`` (first sentence of ``remediation``, ≤ 180 chars).
- Implemented in ``pipeline._enrich_finding`` so the 30+ existing rules need
  no edits. Plugins receive enriched findings in the ``on_findings`` hook.

#### G. ``skillops rules`` / ``skillops rule`` CLI
- ``skillops rules`` lists every audit + security rule with optional
  ``--severity`` / ``--kind`` filters.
- ``skillops rule SEC-012`` shows a single-rule detail card (severity, name,
  message, remediation, docs URL).
- Backed by ``rule_catalog.py`` — security entries introspected from the
  YAML-loaded ``ScannerEngine``; audit entries hand-curated to mirror the
  Python audit modules.

#### H. AdapterProtocol groundwork (no behaviour change)
- New ``parser/protocol.py`` defines the ``AdapterProtocol`` for v0.3
  multi-platform refactor. Existing parsers continue to dispatch by file
  pattern; this is forward-looking infrastructure only.

#### I. Internal Markdown link audit (``auditor/links.py``)
- **AUD-200** *medium* — broken internal link (``./refs/missing.md``).
- **AUD-201** *low* — relative link missing ``./`` prefix.
- External (``http://``, ``mailto:``), absolute, and anchor-only links are
  skipped. Inspired by skilllint LK001-LK002.

#### J. Progressive-disclosure audit (``auditor/disclosure.py``)
- **AUD-300/301/302** *low* — recommend ``references/`` / ``examples/`` /
  ``scripts/`` subdirectories per the Anthropic skill organization
  guideline. Inspired by skilllint PD001-PD003.

### Changed
- ``pipeline.run_pipeline`` now enriches every finding (audit, security,
  runner-blocked) with ``docs_url`` + ``suggestion``.
- Good fixtures (``skill-md-basic`` / ``skill-md-with-examples`` /
  ``skill-md-permissioned``) gained ``references/``, ``examples/``,
  ``scripts/`` placeholder subdirectories so existing
  ``audit_findings == ()`` integration assertions still hold.

### Tests
- ``tests/unit/test_v02_features.py`` (15 cases) — pipeline enrichment
  on audit + security findings, rule catalog lookup, CLI ``rules`` /
  ``rule`` commands, broken link / dotless link audit, three-finding
  disclosure default and the "all dirs present" silent path.
- Total suite: **194 passed** (was 179 in 0.1.4) / overall coverage 91%.

### Sources
- skilllint by jamie-bitflight (MIT) — LK / PD rule semantics, rule
  catalog UX (``skilllint rule FM001``).
- skillcheck by joacanovaro (MIT) — diagnostic schema (``Diagnostic``
  with ``rule``, ``severity``, ``message``, ``line``, ``context``).

## [0.1.4] - 2026-05-27

### Added — competitive parity with `skillcheck` / `skilllint`

After a line-by-line review of the four direct competitors on PyPI
(`skillcheck`, `skilllint`, `skill-tester`, `claude-skill-check`) we ported
their highest-value structural checks while keeping our offline / no-LLM
red lines intact.

#### New audit module: `auditor/sizing.py`
- **AUD-100** *low* — body line count exceeds `LINE_WARNING_THRESHOLD` (500)
- **AUD-101** *low*  — body token estimate ≥ `TOKEN_WARNING_THRESHOLD` (4400)
- **AUD-102** *high* — body token estimate ≥ `TOKEN_ERROR_THRESHOLD` (8800)
- Token estimator: prefers `tiktoken`'s `cl100k_base` (~5% error) and falls
  back to a word/punctuation heuristic (~15% error, zero deps), inspired by
  `skillcheck/tokenizer.py`. Thresholds match `skilllint/token_counter.py`.

#### New audit module: `auditor/naming.py`
- **AUD-110** *high* — name not kebab-case `^[a-z0-9]+(-[a-z0-9]+)*$`
- **AUD-111** *high* — name length > 64 (Anthropic spec)
- **AUD-112** *high* — name embeds reserved vendor tokens
  (`anthropic` / `claude` / `openai` / `cursor` / `codex`)
- **AUD-120** *high* — description length > 1024
- **AUD-121** *low*  — description length < 20 (Anthropic guideline)
- **AUD-122** *high* — description contains XML/HTML tags
- **AUD-123** *low*  — description uses first-person voice
  (`I can / I will / My …`)
- **AUD-124** *low*  — description uses second-person voice
  (`You can / You should …`)
- **AUD-125** *low*  — description spans multiple lines
  (literal `|` block scalar — keeps the newline post-parse)
- **AUD-126** *low*  — description has no recognized trigger phrase from the
  11-entry Anthropic list (`use when` / `use this` / `when ` / `trigger` /
  `activate` / `invoke` / …); replaces the older 4-pattern check
- **AUD-130** *low*  — frontmatter contains an unknown field
  (15-entry whitelist: name, description, version, author, source, tags,
  allowed-tools, model, context, agent, hooks, user-invocable,
  disable-model-invocation, skills, trigger_words, license)

### Changed
- `auditor/description.py` keeps only the legacy "too short for review"
  warning (now **AUD-013** *low*) so that AUD-121 from the new naming
  module is the single authoritative description-length rule.
- `pipeline.run_audit` calls the new sizing + naming modules in addition
  to the existing audit chain; cascade is unchanged when `parse_errors`
  are present.

### Tests
- `tests/unit/test_sizing.py` (10 cases) — heuristic estimator parity,
  threshold constants are Anthropic-aligned, line + token rules.
- `tests/unit/test_naming.py` (22 cases) — kebab-case violations,
  reserved vendor tokens, description length / XML / voice / multiline /
  trigger phrasing, unknown-field whitelist.
- Total suite: **179 passed** (was 147 in 0.1.3) / overall coverage 92%.

### Sources
- skilllint by jamie-bitflight (MIT) — token thresholds, SK001-SK005
  pattern set, 11-entry trigger phrase list.
- skillcheck by joacanovaro (MIT) — heuristic token estimator, person-voice
  regexes, frontmatter field whitelist.

## [0.1.3] - 2026-05-27

### Fixed
- **Scanner-layer finding deduplication.** When a rule's `targets` overlap
  (e.g. `body` and `examples` both cover the same fenced code block), the
  same `(rule_id, file, line, matched_text)` tuple could be reported twice.
  `ScannerEngine.scan` now collapses such duplicates while keeping legitimate
  multi-location matches (different lines, different matched fragments).
  Detected via real-data scan of 37 user skills.

### Added
- `tests/unit/test_scanner_dedup.py` — 3 tests covering overlap dedup,
  multi-fragment preservation, and engine-layer guarantee.

### Real-data regression
- Re-ran `scripts/scan_real_skills.py` against 37 user skills.
  Distribution unchanged from 0.1.2 (9 SEC findings total: SEC-006 ×2,
  SEC-009 ×1, SEC-012 ×2, SEC-014 ×4). Confirms dedup only removes true
  duplicates and never silences distinct evidence.

## [0.1.2] - 2026-05-26

### Added — 6 new SEC rules (LLM-era differentiation)
- **SEC-012 / CRITICAL — Agent identity / memory file access.** Detects
  references to `MEMORY.md`, `USER.md`, `SOUL.md`, `IDENTITY.md`, `CLAUDE.md`,
  `AGENTS.md`, `HOME.md` and to agent-private directories
  (`~/.workbuddy/{memory,identity,profile}`, `~/.codebuddy/`,
  `~/.cursor/identity`). The pattern requires either a path-prefix or an
  explicit access verb (`cat`/`open`/`read`/`Read(`/`read_text`/…), so plain
  Markdown headings like `# CLAUDE.md — Project Notes` no longer false-fire.
- **SEC-013 / HIGH — Base64 / hex decode action.** Detects `base64 -d`,
  `base64.b64decode(`, `atob(`, `String.fromCharCode(`, `codecs.decode(...,
  'base64')`, `binascii.unhexlify(`. Targets the *action* of decoding rather
  than the high-entropy blob (which SEC-008 already covers and which can be
  evaded by splitting / padding).
- **SEC-014 / HIGH — Dynamic `eval` / `exec` / `Function`.** Classic SAST red
  flag, now extended with `setTimeout("…")`, `getattr(o, "__dunder__")`, and
  `new Function(...)`.
- **SEC-015 / HIGH — Network call to bare IP.** Catches `http(s)://A.B.C.D[:port]`
  patterns that bypass DNS allowlists.
- **SEC-016 / CRITICAL — Browser cookie / saved-credential access.** Matches
  `cookies.sqlite`, `Login Data`, Chrome `Default/Cookies`, Firefox profile
  cookie stores, and the macOS / Windows Chrome user-data paths.
- **SEC-017 / HIGH — Writes to system / privileged paths.** Requires both a
  write-action token (`>`, `>>`, `tee`, `cp`, `mv`, `install`) AND a system
  destination (`/etc/`, `/usr/{bin,local}/`, `/System/`, `C:\Windows\`,
  `C:\Program Files\`).

### Added — 2 new AUD rules (recommended frontmatter)
- **AUD-010 / LOW** — recommend `version` field for trust / changelog tracking.
- **AUD-011 / LOW** — recommend at least one of `author` or `source` so the
  Source-Trust hierarchy can be evaluated.

### Added — Reporter enhancements
- **RPT-A — Permission Summary.** New `PermissionSummary` model with
  `files_read`, `files_write`, `commands`, `network` tuples. The pipeline now
  populates `SkillReport.permission_summary`; both Markdown and HTML reports
  include a four-column "Permissions" section in the header.
- **RPT-B — Recommended Action.** Each report now includes a one-line
  decision aid mapped from `overall_risk`:
  | Risk | Recommended Action |
  |------|--------------------|
  | info | Safe to install. |
  | low | Basic review, install OK. |
  | medium | Full code review required before install. |
  | high | Human approval required; do not install without review. |
  | critical | DO NOT INSTALL. Address all critical findings first. |
- **RPT-C — ⚠️ CAUTION middle-state.** When `is_passed=True` but at least one
  HIGH severity finding is present, both reports display a yellow CAUTION
  pill / "PASSED WITH CAUTION" banner. CRITICAL findings still produce a
  full FAILED state.

### Fixed
- **FIX-1 — `SkillReport.target` populated.** Previously the JSON output had
  `target: null` for aggregate scans. The pipeline now stores the CLI-supplied
  scan entry path (POSIX-serialized) on the report.

### Real-data regression (37 installed skills, v0.1.2)
- PARSE_ERROR=0; no `null` summary fields.
- **SEC-012 (CRITICAL) true-positive hits**: `proactive-agent` × 2
  (`Read SOUL.md`, `Read USER.md` — actual identity file access).
- **SEC-014 (HIGH) hits**: `skill-vetter` × 4 (the meta-vetter skill
  *describes* `eval()` / `exec()` as red flags in its checklist; this is a
  documentation-vs-usage edge case, but the matched_text is preserved so
  reviewers can disambiguate).
- SEC-013 / 015 / 016 / 017: 0 hits across the 37 installed skills (none of
  them perform base64 decode / bare-IP fetch / cookie theft / system writes).
- Risk distribution v0.1.1 → v0.1.2:
  `1 critical / 1 high / 3 medium / 9 low / 23 info`
  → `2 critical / 1 high / 3 medium / 8 low / 23 info` (proactive-agent moved
  to CRITICAL; pass count 32 → 29 because 3 skills lost the AUD-010/011
  recommendations).

### Added — Tests
- 35 new tests in `tests/unit/test_scanner_v012_rules.py` (positive/negative
  for each of SEC-012..017).
- 6 fixtures under `tests/fixtures/qa-coverage/sec01{2..7}/SKILL.md`.
- 3 new tests in `tests/unit/test_auditor.py` (AUD-010, AUD-011, source-only
  satisfies AUD-011).
- 13 new tests in `tests/unit/test_reporter_v012.py` (FIX-1 target, RPT-A
  extractor on good fixture / synthetic / broken frontmatter / pipeline
  integration, RPT-B mapping × 5, RPT-B in MD/HTML, RPT-C HTML pill, RPT-C MD
  phrasing, RPT-C absent on clean pass, RPT-C absent on FAILED).
- Total: 89 → **144** passing tests; 91% → **92%** total coverage.

## [0.1.1] - 2026-05-26

### Fixed
- **P0 #1 — Parser no longer aborts the CLI on a single bad YAML frontmatter.**
  Files like `humanizer/SKILL.md` (multi-line `description:` without folded /
  literal scalar quoting) used to bubble a `yaml.YAMLError` → `ParseError` all
  the way to the CLI top-level, exiting with code 3 and skipping every
  remaining skill in the directory tree. The parser now captures the YAML
  failure into a new `SkillFile.parse_errors: tuple[str, ...]` field, returns
  an empty `frontmatter`, and continues. The frontmatter auditor emits exactly
  one `AUD-000 / CRITICAL` finding for that file (and short-circuits the per-
  field cascade), so the rest of the inventory still gets scanned and the run
  exits cleanly with code 1 (audit failed) instead of 3 (internal error).
- **P0 #2 — `SkillReport.is_passed` is now correctly populated in JSON output.**
  Previously the field was named `passed` on the model but consumers (incl.
  the real-skills scan summary) read `is_passed`, yielding `null` for every
  scan. The model now exposes `is_passed` as a pydantic v2 `@computed_field`
  (frozen-compatible) that re-derives the verdict from `score` / `threshold` /
  CRITICAL findings on every access, and the legacy `passed` field has been
  removed from the public schema. CLI exit code, summary table, MD/HTML
  templates, and the integration tests have all been updated to read the
  computed field.

### Active bug-hunt findings (real-data regression on 37 installed skills)
- PARSE_ERROR count dropped from 1 → **0**; no `null` fields in
  `reports/real-skills/summary.json`.
- Risk distribution: 1 CRITICAL (humanizer, malformed YAML) · 1 HIGH
  (skill-vetter, two `sudo` mentions matched as SEC-006) · 3 MEDIUM · 9 LOW ·
  23 INFO. 32 PASS / 5 FAIL.
- Sampled `skill-vetter`, `agentmail`, `drawio-skill`, `thesis-writer`:
  every security finding is a true positive (literal `sudo`, literal
  `Ignore previous instructions` prompt-injection trigger). No SEC-008
  high-entropy false positives across all 37 skills (zero SEC-007/SEC-008
  findings emitted, SHA256 docs etc. were correctly ignored).
- MD / HTML / JSON outputs are byte-consistent for `skill-vetter`: same
  score (61), risk (HIGH), is_passed (false), and matching count of
  finding rows in all three formats.
- HTML / MD reports contain **zero** literal Windows backslashes —
  README-screenshot safe.
- CLI on the full skills tree exits with code 1 (audit failed), not 3.
- `grep subprocess src/` returns only the docstring red-line in the
  runner package — no imports, no calls.

### Added
- New tests:
  - `tests/unit/test_parser_skill_md.py::test_split_frontmatter_handles_malformed_yaml`
  - `tests/unit/test_parser_skill_md.py::test_split_frontmatter_handles_non_mapping_yaml`
  - `tests/unit/test_parser_skill_md.py::test_split_frontmatter_handles_empty_yaml`
  - `tests/unit/test_parser_skill_md.py::test_malformed_frontmatter_degrades_gracefully`
  - `tests/integration/test_pipeline_end_to_end.py::test_pipeline_continues_on_bad_frontmatter`
  - `tests/unit/test_scoring.py::test_is_passed_computed_in_report_*` (4 cases)

## [0.1.0] - 2026-05-25

### Added
- Initial MVP release of SkillOps Forge.
- Parsers for `SKILL.md`, `CLAUDE.md`, and `.cursor/rules/*.md(c)`.
- Structural auditor (frontmatter, description, permissions, IO schema, examples).
- Security scanner with 11 built-in P0 rules (regex / keyword / heuristic engines).
- Examples dry-run runner with hard-coded `subprocess` ban (interceptors only).
- Risk-weighted scoring model with CRITICAL veto.
- Markdown / HTML / JSON reporters (offline, README screenshot-friendly HTML).
- Typer + Rich CLI: `skillops scan`, `skillops init-ci`, `skillops version`.
- Pinned GitHub Actions template (`actions/checkout@v4`, `actions/setup-python@v5`).
- 5 good fixtures + 6 bad fixtures + end-to-end pipeline tests.
