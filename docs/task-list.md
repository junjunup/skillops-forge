# SkillOps Forge — 任务清单（工程师执行版）

**配套文档**：`docs/architecture.md`
**总数**：22 个任务 / 8 个 Wave
**预计工期**：单工程师 10–12 个工作日

> 列说明：`涉及文件` 中以相对路径列出；`依赖` 为前置任务编号；`并行` 标识可与同 Wave 其他任务并发；`实现要点` 抽取自架构文档；`验收` 为可机器/人工核验的判定标准。

---

## Wave 1：基础设施

### T01 项目骨架与构建配置

- **依赖**：—
- **并行**：否
- **涉及文件**：
  - `pyproject.toml`
  - `LICENSE`（MIT）
  - `.gitignore`
  - `README.md`、`README_CN.md`（占位）
  - `src/skillops_forge/__init__.py`（暴露 `__version__ = "0.1.0"`）
  - `src/skillops_forge/__main__.py`
  - `src/skillops_forge/exceptions.py`
  - `src/skillops_forge/config.py`（默认阈值 70、默认 out_dir、退出码常量）
  - `src/skillops_forge/logging_setup.py`（RichHandler）
- **要点**：
  - hatchling 构建后端；PEP 621 元数据
  - `[project.scripts] skillops = "skillops_forge.cli:app"`
  - 在 pyproject 内同时声明 ruff/mypy/pytest/coverage 配置框架（具体规则在 T20 完善）
  - 依赖按 architecture §9 写入
- **验收**：`pip install -e .` 通过；`skillops --help` 输出（即便 cli 仅做 stub）；`pytest --collect-only` 不报错

---

## Wave 2：模型与解析层

### T02 核心数据模型

- **依赖**：T01
- **并行**：否
- **涉及文件**：`src/skillops_forge/models.py`、`tests/unit/test_models.py`
- **要点**：pydantic v2；`Severity / SkillFormat / Example / SkillFile / SkillInventory / Finding / AuditFinding / SecurityFinding / ExampleRun / SkillReport`；`model_config = frozen + extra=forbid`
- **验收**：`SkillReport.to_json()` 可解析；模型字段单测全覆盖

### T03 SKILL.md 解析器 + Inventory 遍历 `[parallel]`

- **依赖**：T02
- **涉及文件**：`src/skillops_forge/parser/__init__.py`、`parser/base.py`、`parser/skill_md.py`、`parser/inventory.py`、`tests/unit/test_parser_skill_md.py`
- **要点**：YAML frontmatter 切片；fenced code block 识别 examples；`allowed-tools` 字段抽取；目录遍历自动探测格式
- **验收**：fixture 解析正确，含 frontmatter & ≥1 example

### T04 CLAUDE.md 解析器 `[parallel]`

- **依赖**：T02
- **涉及文件**：`parser/claude_md.py`、`tests/unit/test_parser_claude_md.py`
- **要点**：按 `## section` 切片；examples 识别 fenced bash/python
- **验收**：fixture 输出正确 sections

### T05 Cursor rules 解析器 `[parallel]`

- **依赖**：T02
- **涉及文件**：`parser/cursor_rules.py`、`tests/unit/test_parser_cursor_rules.py`
- **要点**：`.cursor/rules/*.md` 与 `*.mdc`（含 frontmatter）
- **验收**：fixture 输出 rules 列表

---

## Wave 3：审计 / 扫描 / 运行

### T06 结构审计模块 `[parallel]`

- **依赖**：T03 T04 T05
- **涉及文件**：`auditor/__init__.py` + `frontmatter/description/permissions/io_schema/examples.py`、`tests/unit/test_auditor_*.py`
- **要点**：每子模块产出 `AuditFinding`；包含触发词启发式（`Use this skill when ...`）
- **验收**：bad/missing-frontmatter 至少 3 条 finding；good 样本 0 条

### T07 安全规则 YAML 包（≥10 条 P0） `[parallel]`

- **依赖**：T02
- **涉及文件**：`rules/remote_scripts.yaml`、`rules/sensitive_paths.yaml`、`rules/dangerous_commands.yaml`、`rules/hidden_instructions.yaml`、`rules/privilege.yaml`、`rules/exfiltration.yaml`、`docs/rules.md`
- **要点**：每条含 id/name/severity/pattern/engine/targets/message/remediation；与架构 §6 完全一致
- **验收**：≥11 条规则；YAML 全部 `safe_load` 通过

### T08 安全扫描引擎

- **依赖**：T03 T04 T05 T07
- **涉及文件**：`scanner/__init__.py`、`scanner/engine.py`、`scanner/rule.py`、`scanner/heuristics.py`、`tests/unit/test_scanner_engine.py`、`tests/unit/test_scanner_rules_*.py`
- **要点**：regex/keyword/heuristic 三引擎；熵 / 零宽字符 / base64 长串
- **验收**：每条规则 ≥1 正例 + ≥1 反例测试；scanner 模块覆盖率 ≥95%

### T09 示例 dry-run 与拦截器 `[parallel]`

- **依赖**：T03 T04 T05
- **涉及文件**：`runner/__init__.py`、`runner/dry_run.py`、`runner/interceptors.py`、`tests/unit/test_runner_dry_run.py`
- **要点**：**绝不调用 subprocess**；shlex 分词 + 命令黑/白名单
- **验收**：含 `curl ... \| sh` 自动 critical 拦截；测试中断言 subprocess.run 未被调用

### T10 评分模型 `[parallel]`

- **依赖**：T02
- **涉及文件**：`reporter/scoring.py`、`tests/unit/test_scoring.py`
- **要点**：架构 §7 公式；CRITICAL 一票否决
- **验收**：边界用例（0 / 1 critical / 3 high / 阈值附近）全部通过

---

## Wave 4：报告渲染

### T11 Markdown 报告 `[parallel]`

- **依赖**：T10
- **涉及文件**：`reporter/markdown.py`、`templates/report.md.j2`、`tests/unit/test_reporter_markdown.py`、`tests/snapshots/reports/sample.md`
- **验收**：snapshot 测试通过；含分数/风险/findings/修复建议章节

### T12 HTML 报告（README 截图友好） `[parallel]`

- **依赖**：T10
- **涉及文件**：`reporter/html.py`、`templates/report.html.j2`、`tests/unit/test_reporter_html.py`
- **要点**：单文件 HTML（内联 CSS）；色卡见架构 §8.3
- **验收**：可双击打开；含 score 大字、风险色卡、findings 表

### T13 JSON 报告 `[parallel]`

- **依赖**：T10
- **涉及文件**：`reporter/json_report.py`、`reporter/__init__.py`（render 工厂）、`tests/unit/test_reporter_json.py`
- **要点**：`SkillReport.to_json()` 直接序列化；导出 `skillops-result.schema.json`（见 T22）
- **验收**：JSON 可被 schema 校验

---

## Wave 5：CLI 集成

### T14 Pipeline 编排器

- **依赖**：T06 T08 T09 T10
- **涉及文件**：`pipeline.py`、`plugins/__init__.py`、`plugins/protocol.py`、`tests/integration/test_pipeline_end_to_end.py`
- **要点**：parser→audit→scan→run→score→report；PluginProtocol 钩子（P1 预留）
- **验收**：fixture 输入 → SkillReport 字段正确

### T15 CLI 命令实现

- **依赖**：T11 T12 T13 T14
- **涉及文件**：`cli.py`、`tests/integration/test_cli.py`
- **要点**：typer app；`scan/init-ci/version`；`--report html|md|json|all`；退出码（0/1/2/3）；rich 摘要
- **验收**：good 样本退出 0；bad 样本退出 1；`--report all` 输出 3 文件

---

## Wave 6：CI 模板

### T16 GitHub Actions 模板与 init-ci

- **依赖**：T15
- **涉及文件**：`ci/__init__.py`、`ci/github_actions.py`、`templates/ci/skillops.yml.j2`、`.github/workflows/skillops.yml`、`tests/unit/test_ci_init.py`
- **要点**：Jinja2 渲染；包含 `actions/checkout@v4` + `actions/setup-python@v5`（pinned）；artifact 上传；阈值 fail
- **验收**：`skillops init-ci --github-actions` 生成 yml 通过 actionlint；`--force` 才覆盖

---

## Wave 7：Fixture 与系统测试

### T17 Good fixtures `[parallel]`

- **依赖**：T03 T04 T05
- **涉及文件**：`tests/fixtures/good/skill-md-basic/`、`good/claude-md-basic/`、`good/cursor-rules-basic/`、`good/skill-md-with-examples/`、`good/skill-md-permissioned/`、`tests/conftest.py`
- **验收**：pipeline 跑分 ≥85；audit + security finding 数为 0

### T18 Bad fixtures `[parallel]`

- **依赖**：T03 T04 T05 T07
- **涉及文件**：`tests/fixtures/bad/missing-frontmatter/`、`bad/curl-pipe-bash/`、`bad/sensitive-path-aws/`、`bad/hidden-zerowidth/`、`bad/rm-rf-root/`、`bad/base64-blob/`
- **验收**：每个对应类别 finding 触发；总分 <70

### T19 端到端 + Snapshot 回归 `[parallel]`

- **依赖**：T14 T15 T17 T18
- **涉及文件**：`tests/integration/test_pipeline_end_to_end.py`、`tests/integration/test_cli.py`、`tests/snapshots/reports/*`
- **验收**：总覆盖率 ≥85%；scanner 单模块 ≥95%

---

## Wave 8：质量门禁与文档

### T20 质量工具配置与自身 CI `[parallel]`

- **依赖**：T15
- **涉及文件**：`pyproject.toml`（追加 `[tool.ruff]/[tool.mypy]/[tool.pytest]/[tool.coverage]`）、`.github/workflows/ci.yml`、`tests/conftest.py`
- **要点**：ruff/ruff-format/mypy strict/bandit/pip-audit；GH Actions matrix 3.10/3.11/3.12 × ubuntu/macos/windows
- **验收**：4 项工具本地零错误；CI 通过

### T21 README 与 Quick Start `[parallel]`

- **依赖**：T15 T16 T17 T18
- **涉及文件**：`README.md`、`README_CN.md`、`CHANGELOG.md`、`docs/rules.md`（占位）
- **要点**：30 秒 Quick Start；HTML 报告截图占位；badge（CI/PyPI/coverage）；明确"风险辅助评估"
- **验收**：干净 venv 中按 README 步骤可复现

### T22 规则文档与 schema 导出 `[parallel]`

- **依赖**：T07 T13
- **涉及文件**：`docs/rules.md`（自动生成段落）、`docs/schema/skillops-result.schema.json`、`scripts/export_schema.py`
- **验收**：rules.md 与 yaml 一致；schema 可校验 fixture 报告

---

## 关键路径与并行总结

- **关键路径**：T01 → T02 → T03 → T08 → T14 → T15 → T19
- **可并行 Wave**：Wave 2（T03/T04/T05）、Wave 3（T06/T07/T09/T10）、Wave 4（T11/T12/T13）、Wave 7（T17/T18/T19）、Wave 8（T20/T21/T22）

## Definition of Done（全局 DoD）

1. 所有任务对应代码 + 单测合并
2. ruff / ruff format / mypy(strict) / bandit / pip-audit 零错误
3. pytest 总覆盖率 ≥85%，scanner 模块 ≥95%
4. GH Actions（自身 CI）三平台三 Python 版本通过
5. `pip install -e .` 后 Quick Start 命令在干净 venv 可复现
6. README/README_CN 不夸大安全能力，包含明确 disclaimer
