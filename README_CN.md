# SkillOps Forge（中文版）

[English](README.md) · **中文**

> **AI Agent Skill 的静态 lint + 风险提示工具。**
> 面向 `SKILL.md`、`CLAUDE.md` 和 `.cursor/rules/*.mdc` 的离线 CLI ——
> 19 条明文模式安全规则 + 27 条审计规则，零 LLM、零 `subprocess`。

[![CI](https://github.com/junjunup/skillops-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/junjunup/skillops-forge/actions/workflows/ci.yml)
[![SkillOps self-scan](https://github.com/junjunup/skillops-forge/actions/workflows/skillops.yml/badge.svg)](https://github.com/junjunup/skillops-forge/actions/workflows/skillops.yml)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.1-informational)]()

## 为什么再造一个轮子？

Skill 生态已有结构 lint 与质量评分工具。**但没有任何工具把"AI 时代独有的攻击面"
当作一等公民检测**——例如 Agent 记忆文件外泄、身份文件偷读、提示词注入关键词、
零宽字符隐藏载荷等。

| 工具 | 形态 | 关注点 | 安全规则 | 离线 | LLM 时代检测 |
| --- | --- | --- | --- | --- | --- |
| `skilllint` | CLI | 结构 lint、跨平台 | 部分（模式级）| ✓ | ✗ |
| `skill-tester` | CLI | AST + 样例执行 + 质量评分 | ✗ | ✓ | ✗ |
| `skillcheck` | CLI | 仅 frontmatter 校验 | ✗ | ✓ | ✗ |
| `claude-skill-check` | GH Action | skill 中的密钥泄漏 | 7 种密钥模式 | ✓ | ✗ |
| `kevinsong0/skills-vetter` | Prompt skill | LLM 驱动审查 | 定性 | ✗（依赖 LLM）| 部分 |
| **`skillops-forge`** | **CLI + GH Action** | **lint + 明文模式风险提示 + 评分 + 报告** | **19 条明文规则** | **✓** | **✓** |

SkillOps Forge 为 Agent 私有文件（`MEMORY.md` / `USER.md` / `SOUL.md` /
`IDENTITY.md` / `~/.workbuddy/memory`）配备了专用规则，并整合了结构审计、
确定性评分模型、CRITICAL 一票否决、以及自包含的 HTML / Markdown / JSON 报告。

> **声明**：仅辅助风险评估，**不是完整的安全方案**。本工具是基于明文模式
> 的静态扫描器，无法读取代码意图。**正式依赖前请阅读下方
> [局限性](#局限性) 段落。**

## 局限性

SkillOps Forge 是一个**明文模式静态 lint**，不是完整的安全方案。我们已对它
做过对抗性测试，下面是它能做和不能做的事，直说不夸：

### 能做好的事
- 当作者用规范、未混淆的形式写出 19 条规则覆盖的明文模式
  （`curl | sh`、`sudo`、`eval(`、`~/.ssh/id_rsa`、`MEMORY.md` 引用 等等）
  时，SkillOps Forge 都能识别。
- 标记 skill 包的**结构与命名问题**（frontmatter schema、kebab-case 名称、
  token 预算、缺触发短语等）。
- 输出**确定性、机读**的报告，足以作为对诚实作者的 PR 阻塞 CI 门禁。

### 做不到的事 —— 我们已验证可绕过的场景
以下技巧今天**可以绕过** SkillOps Forge：

| 绕过手法 | 漏过去什么 |
| --- | --- |
| Unicode 同形字符（`ѕudo`，西里尔字母 `ѕ` U+0455） | SEC-006 失明，仅可能命中后接的 `rm` |
| `bash -c "$(curl …)"` 替代 `curl … \| sh` | SEC-001 失明，仅 SEC-010 中级提示 |
| `curl -o /tmp/x && sh /tmp/x`（下载-后执行） | SEC-001 失明 |
| `python -c "exec(urlopen(...).read())"` | SEC-001 失明 |
| `__import__("builtins").exec(payload)` | SEC-014 失明；**SEC-018 可捕获** |
| `getattr(__builtins__, 'ev'+'al')(payload)` | SEC-014 失明；**SEC-018 + SEC-019 可捕获** |
| Base64 载荷拆成两段字符串 | 只要单段长度不够，SEC-008 / SEC-013 都漏 |

根本约束：**正则的明文扫描不能读取意图**。坚定的攻击者总能找到一种混淆方式
绕过有限的规则集。SEC-018 / SEC-019（0.2.1 新增）封住了"反射访问 / 字符串
拼接"两类最常见的绕过，但这个清单不可能穷尽，且永远不会穷尽。

### 推荐使用姿态
- 把这个工具当作**多个信号之一**，而不是唯一的安全门禁。结合代码审查、
  运行时沙箱、来源信任评估一起用。
- **干净通过**应理解为"明文上没有明显红旗"，不是"这个 skill 是安全的"。
- **失败结果**应理解为"安装前需要审查"，不应作为恶意意图的证据
  ——误报存在并已记录。
- 对高风险目标（处理凭据、资金、系统配置的 skill），**即使报告全绿**
  也不要省略人工审核。

### 不在范围内
- AGENTS.md / Codex `agents.json` 文件 —— 不解析。
- Python AST / 运行时样例执行 —— 不实现（红线：无 `subprocess`、
  无 LLM、不执行不受信代码）。
- skill body 中域名的网络声誉查询 —— 完全离线。
- skill 包加密签名校验 —— 不实现。

后续版本会持续扩大绕过覆盖；每个新防御 + 每个已知限制都会在 `CHANGELOG.md`
明确列出。

## 30 秒上手

```bash
# 源码安装（PyPI 发布前）
pip install -e ".[dev]"

# 验证安装
skillops --help          # 3 个命令
skillops version         # skillops-forge 0.2.1

# 扫描一个 skill（或整个 skill 仓库）
skillops scan ./my-skill --report all

# 一键生成 CI 工作流，分数低于 70 时让 PR 失败
skillops init-ci --github-actions
```

报告默认输出到 `./reports/`：

| 文件 | 用途 |
| --- | --- |
| `reports/skillops-report.html` | 自包含 HTML（嵌入 README、作为 artifact 分享） |
| `reports/skillops-report.md` | Markdown 摘要（PR 评论友好） |
| `reports/skillops-result.json` | 机读、schema 稳定（CI artifact） |

## CLI

```text
skillops scan PATH [--report md|html|json|all] [--out-dir DIR]
                   [--threshold 70] [--no-cursor-rules] [--no-runner] [-v]
skillops init-ci [--github-actions / --no-github-actions]
                 [--out FILE] [--force]
skillops version
```

退出码：

| 码 | 含义 |
| --- | --- |
| 0 | 通过（分数 ≥ 阈值 **且** 无 CRITICAL finding） |
| 1 | 审计失败（低于阈值或任意 CRITICAL finding） |
| 2 | 用户错误（路径不存在、参数非法） |
| 3 | 内部错误（少见；坏 YAML 已降级为 finding 不再退 3） |

## 检测内容

### 19 条安全规则（SEC-001 → SEC-019）

| ID | 严重等级 | 检测内容 |
| --- | --- | --- |
| SEC-001 | critical | 远程脚本管道 shell（`curl … \| sh`） |
| SEC-002 | high | 下载然后执行（`wget -O … && bash`） |
| SEC-003 | critical | 敏感凭据文件路径（`~/.ssh`、`~/.aws`、`id_rsa`、`.netrc`） |
| SEC-004 | high | 隐式凭据环境变量读取（`AWS_*`、`OPENAI_API_KEY`、`GITHUB_TOKEN`） |
| SEC-005 | critical | 破坏性 shell 命令（`rm -rf /`、`dd if=`、`mkfs`、fork bomb） |
| SEC-006 | high | 提权（`sudo`、`chmod 777`、`chown -R root`） |
| SEC-007 | high | 隐藏零宽字符（U+200B/200C/200D/FEFF） |
| SEC-008 | medium | 长 base64 / 高熵 blob（启发式） |
| SEC-009 | high | 提示词注入关键词（`ignore previous instructions`、`jailbreak`） |
| SEC-010 | medium | 外发到非白名单域名 |
| SEC-011 | high | 未消毒变量造成的 shell 注入 |
| **SEC-012** | **critical** | **Agent 身份 / 记忆文件偷读**（`MEMORY.md`、`USER.md`、`SOUL.md`、`IDENTITY.md`、`CLAUDE.md`、`~/.workbuddy/memory`） |
| SEC-013 | high | base64 / hex 解码动作（`base64 -d`、`atob(`、`fromCharCode`） |
| SEC-014 | high | 动态执行（`eval(`、`exec(`、`Function(...)`） |
| SEC-015 | high | 直接调用 IPv4 地址 |
| SEC-016 | critical | 浏览器 cookie / Login Data / 保存的凭据访问 |
| SEC-017 | high | 写入系统 / 特权路径（`/etc`、`/usr`、`C:\Windows`） |
| SEC-018 | high | 反射动态执行（`getattr(__builtins__, ...)`、`__import__("builtins").exec`） |
| SEC-019 | high | 字符串拼接的 `eval` / `exec` / `compile` 名称（如 `'ev'+'al'`） |

### 结构审计（auditor）

`frontmatter`（必填 + 推荐字段）、`description`（长度 + 触发词）、`permissions`
（`allowed-tools` 声明 vs 实际 shell 使用）、`io_schema`（Inputs / Outputs 段
落）、`examples`（≥1 个 fenced 块，可解释执行）。

### Runner

示例是**解释，从不执行**。Runner 用 `shlex` 加严格的允许/拒绝列表，
测试套件断言 `subprocess.run`、`Popen`、`check_call`、`check_output` **从未被调用**。

## 报告产物

每份报告（自 0.1.2 起）包含：

- **Score / Risk / Threshold / Result** —— 当分数 ≥ 阈值但有 HIGH finding 时
  显示 `⚠️ PASSED WITH CAUTION` 中间态。
- **Recommended Action** —— 按风险等级映射的明确建议
  （例：CRITICAL → "DO NOT INSTALL. Address all critical findings first."）。
- **Permissions Summary** —— 自动从 skill body 与 examples 抽取
  *Files Read / Files Write / Commands / Network*。
- **Inventory / Findings / Examples Dry-Run / Compliance Checklist**。

## 评分

```
score = max(0, 100 - Σ(权重 × 命中数))
权重：critical=25, high=12, medium=5, low=2, info=0
```

任意 1 条 CRITICAL → `is_passed = false`，无视分数（一票否决）。
该一票否决同时作用于 `audit_findings` 与 `security_findings`；
`is_passed` 是 Pydantic v2 `@computed_field`，JSON / Markdown / HTML
三份报告自动保持一致。

## 一行命令接入 CI

```bash
skillops init-ci --github-actions
```

生成 `.github/workflows/skillops.yml`，使用 **pinned** 的
`actions/checkout@v4` + `actions/setup-python@v5`，含 artifact 上传与
`fail-under` 阈值（默认 `70`）。默认拒绝覆盖已存在的工作流文件，加 `--force`
才覆盖。

## 真实场景示例

用 SkillOps Forge 扫描某开发者本机安装的 37 个 skill（`~/.workbuddy/skills/`），
抓出两条 **真阳** CRITICAL：

| Skill | Finding | 证据 |
| --- | --- | --- |
| `proactive-agent` | SEC-012 × 2 | `Read SOUL.md` / `Read USER.md`（第 499-500 行） |
| `humanizer` | AUD-000 (CRITICAL) | 多行 YAML description 未加引号（解析器优雅降级而非崩溃） |

完整分布：2 critical · 1 high · 3 medium · 9 low · 22 info。
逐条规则的设计动机与对 skilllint / skillcheck 的致谢，见 `CHANGELOG.md` 的
`[0.1.2]` / `[0.1.4]` / `[0.2.0]` / `[0.2.1]` 段。

## 设计红线

1. **绝不 `subprocess`** —— runner 模块零 `subprocess` 导入；测试用
   monkey-patch 守住。
2. **完全离线** —— 无任何网络调用（包括 GitHub API）；`init-ci` 仅生成模板。
3. **绝不上传用户内容** —— 所有分析在本地完成。
4. **绝不执行危险命令** —— 示例通过 `shlex` + 允许/拒绝列表解释；`curl … | sh`
   会被直接拦截。
5. **风险辅助而非认证** —— 每份报告都有明确 disclaimer。

## 项目结构

```
skillops-forge/
├── src/skillops_forge/
│   ├── parser/        # SKILL.md / CLAUDE.md / .cursor/rules
│   ├── auditor/       # frontmatter / description / permissions / io / examples
│   ├── scanner/       # 规则加载器 + dedup 引擎
│   ├── runner/        # 基于 shlex 的 dry-run，永不 subprocess
│   ├── reporter/      # md / html / json + 评分
│   ├── pipeline.py    # parser → audit → scan → run → score → report
│   ├── plugins/       # PluginProtocol（P1: LLM judge、跨格式导出）
│   ├── rules/         # 数据驱动的 YAML SEC 规则
│   ├── templates/     # Jinja2（HTML/MD 报告 + GH Actions yml）
│   └── ci/            # init-ci 生成器
├── tests/             # 206 测试，91% 行覆盖率（scanner ≥95%）
├── docs/              # 架构 / 规则 / JSON schema / mermaid 图
└── pyproject.toml
```

## 许可

[MIT](LICENSE) · 英文版见 [README.md](README.md)。
