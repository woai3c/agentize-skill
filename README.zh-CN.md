# Agentize Skill

[English](README.md) | [简体中文](README.zh-CN.md)

**Agentize your codebase.**

Agentize 是一个厂商中立的 Coding Agent Skill，用于把现有仓库一次性改造成可靠、Human-in-the-loop 的 AI 开发环境。它会检查项目，修复或补充最小且有价值的仓库自有上下文与工作流，报告仍需配置的能力，验证变更，然后退出。

> **Agentize should leave behind the system, not become the system.**

最终结果留在目标仓库中。后续 Codex、Claude Code、Gemini CLI、Kimi CLI 或其他 Coding Agent 会依赖仓库留下的指令、文档、检查、CI、工具和决策路径工作，不应把 Agentize 当作运行时依赖。

## 快速开始

把下面这段话发给具备安装能力的 Coding Agent，让它为你的所有仓库安装这个 Skill：

```text
请帮我安装这个 Agent Skill，让它在我的所有仓库中都可用：
https://github.com/woai3c/agentize-skill
```

然后打开需要改造的仓库并发送：

```text
使用 Agentize 把这个现有仓库一次性改造成可独立运行、Human-in-the-loop 的 AI 开发 Harness。保留当前工具和约定，只做最小且有证据支持的变更，诚实暴露尚不支持的能力和人工配置，验证最终结果，并分别交接有明确作用域的 Harness Capability Report 和本次任务结果。
```

如果新安装的 Skill 尚未出现，请新建一个 Agent 会话。仓库级安装、不同宿主的路径、只读审计和聚焦修复说明见[安装与使用](#安装与使用)。

## 它能做什么

一次普通 Bootstrap 会：

1. 绑定准确目标，并在 Discovery 阶段不执行项目代码的前提下，清点现有 Agent 指令、文档、Manifest、命令、测试、CI、运行时路径和知识学习机制；
2. 用直接证据对照理想的 AI Native Workflow，并区分 Observed Fact、Inference、Unknown、Operational Readiness 和当前任务结果；
3. 优先修复已有事实来源，只补充最小必要的仓库自有指令、上下文、验证、评审、验收和知识捕获路径；
4. 当凭据、权限、账号、测试数据、浏览器控制、Runner、外部设置或模型接入仍需要人类处理时，生成聚焦的配置说明；
5. 验证最终路径、能力声明、命令、检查和 Diff，并交接一份有明确作用域的 Harness Capability Report。

它会适配仓库现状，而不是安装固定脚手架：

| 初始状态 | 结果 |
| --- | --- |
| 没有有效 Agent 工作流 | 建立最小可用 Harness，并暴露剩余缺口。 |
| 工作流不完整 | 保留有用内容，补齐重要缺口。 |
| 工作流冲突或过期 | 根据证据协调实际行为，并暴露尚未解决的意图问题。 |
| 工作流成熟 | 只做聚焦修复，或给出有证据支持的零修改结论。 |

Agentize 会让根 Agent 指令文件保持简洁并主要承担导航职责。它优先复用仍在维护的知识 Owner；如果不存在合适 Owner，并且有证据支持的内容确实值得沉淀，则在 `docs/product/`、`docs/architecture/`、`docs/development/`、`docs/verification/` 或 `docs/operations/` 下创建聚焦文件。这些目录是默认 Fallback，不是每个仓库都要生成的空目录树。语义知识与负责执行其中确定性部分的 Test、Lint、Type Rule、Architecture Check、Script 或 CI Gate 分开表达。已有 `ARCHITECTURE.md` 可以保留，但 Agentize 默认不会创建它。

明确要求“仅审计”“只报告”或“不要修改”时，默认执行静态只读评估。Agentize 可以检查命令定义，但不会运行项目定义的测试、构建、包管理器脚本、Lint 或 Runtime Flow；除非用户另外明确要求某项动态检查。

## 它留下的工作流

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Local Fast Verification -> Targeted Runtime Verification <-> Human Local Acceptance -> Create / Mark MR/PR Ready for Review <-> AI Review + MR/PR CI -> Merge
```

Continuous Knowledge Capture 贯穿整个开发过程。Full E2E 遵循仓库明确的 Cost/Risk-aware Policy，可以放在每个 MR/PR、测试或预发布环境晋级、固定时间、Release 前，或采用有文档说明的组合策略。Ship 与生产观察只适用于相应类型的项目。自动 Post-Merge Knowledge Audit 只是用于检查开发后期遗漏 Durable Knowledge 的可选兜底，不是最小日常步骤。

这是理想工作流，不表示每个仓库已经支持所有阶段。Agentize 会分别表达 Workflow Contract、Repository Evidence、Capability Readiness、Human Setup 和当前执行结果。详细的职责与返工循环规则位于 [`references/delivery-workflow.md`](references/delivery-workflow.md)。

每项适用能力使用一种 Operational Status：

| 状态 | 含义 |
| --- | --- |
| `READY` | 对明确作用域，完整路径已经配置并验证。 |
| `PARTIAL` | 一个有用且边界明确的子集可用，缺失部分已明确。 |
| `SETUP REQUIRED` | 已选择具体路径且仓库侧工作已存在，但仍需要明确的人类操作或外部前置条件。 |
| `NOT CONFIGURED` | 能力适用，但当前没有可用且已选择的实现路径。 |
| `UNVERIFIED` | 证据不足，或无法安全完成验证。 |
| `NOT APPLICABLE` | 该能力不适用于当前仓库或作用域。 |

当前任务中的检查另行使用 `PASSED`、`FAILED`、`NOT EXECUTED` 或 `NOT APPLICABLE`。一个文件、依赖、Workflow 定义或绿色测试，本身不能证明能力已经 Ready，也不能证明实现符合人类真实意图。

Agentize 不能虚构产品意图、批准自己的 Plan 或 Acceptance、替人选择风险容忍度、提供不存在的凭据或基础设施、证明外部分支保护已经生效，也不能在缺少真实 Runner 和项目已选择模型接入时凭空创建独立 AI Reviewer 或合并后 Agent。无法安全建立必需能力时，正确结果是明确缺口、配置路径和人工 Fallback，而不是伪造自动化。

## 安装与使用

### 安装细节

用于分发的仓库名是 `agentize-skill`；Skill 名称和安装目录仍然是 `agentize`。快速开始中的 Prompt 请求的是可跨仓库复用的用户级安装；如果只想在当前仓库使用，请明确说明。具备安装能力的 Agent 应遵循当前宿主的 Skill 发现机制，复制完整 Skill 目录，验证能否发现，并报告准确安装路径。安装任何第三方 Skill 前，都应检查源码和安装的 Revision。

安装后，在宿主提供 Skill Picker 时选择 Agentize，或直接在请求中明确写出 Agentize。你不需要自己运行随附扫描器。

### 其他使用方式

只读审计：

```text
使用 Agentize 审计这个仓库的 AI 开发 Harness。不要修改文件，也不要运行项目定义的命令。报告证据、冲突、缺口、未知项、配置需求和 Fallback。
```

聚焦修复：

```text
使用 Agentize 协调这个仓库的 Agent 指令与真实验证路径。保持无关文件不变。
```

通常一次成功的 Bootstrap 就够了。后续 Feature 和 Bug 工作应直接遵循仓库中留下的 Harness。只有当项目或工具变化后，你明确想重新审计或修复 Harness 时，才需要再次运行 Agentize。

### 手动安装作用域

开放的 [Agent Skills 规范](https://agentskills.io/specification) 标准化 Skill 目录内容，但没有规定通用安装路径。请遵循当前宿主的文档。

例如，[Codex 会从多个作用域发现 Skill](https://developers.openai.com/codex/skills)。可跨仓库复用的用户级安装通常使用：

```text
~/.agents/skills/agentize/
```

仓库级安装使用：

```text
<repository>/.agents/skills/agentize/
```

前者可供该用户的多个仓库使用；后者只作用于对应仓库树。其他宿主可能采用不同约定，所以 `.agents/skills` 不是通用强制规则。

## 扫描器

普通用户无需手动运行扫描器。两套实现都只使用对应运行时的标准库，执行静态只读清点，并且绝不会执行已声明的项目命令：

```text
node scripts/scan_repo.cjs --root /path/to/repository --format markdown
node scripts/scan_repo.cjs --root /path/to/repository --format json
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

Schema v5 会限制文件数、目录数、扫描深度和单文件字节数；跳过非普通文件与指向仓库外部的符号链接；保守识别验证命令；并对常见凭据语法做尽力脱敏。报告仍然属于敏感本地证据，共享前必须检查。可以通过 `--max-files`、`--max-directories` 和 `--max-depth` 调整限制；任何触发的限制都会明确记录在 `scan.limit_reasons` 和诊断信息中。

Git 查询会清除继承的 `GIT_*` 仓库选择变量，并且只检查仓库身份与分支。它不会运行 `status` 或 `diff`，因为内容比较可能执行仓库配置的 Filter。因此 Worktree State 会报告为 `unverified`，绝不会静默当作 Clean。Repository Identity 使用三态：`true` 表示已验证，`false` 表示目标路径没有 Git Marker，`null` 表示存在 Marker 但无法验证身份。

Agentize 会先尝试 Node.js 扫描器；如果第一套实现不可用、不兼容或无法返回有效报告，再尝试 Python。两者都无法工作时，它会使用宿主已有的只读工具，明确披露扫描器失败，并将无法获得的确定性事实标为 `unverified`。它不会仅为扫描而安装或升级运行时。

## 仓库结构

- `SKILL.md` 包含激活边界、安全、协调和交接规则。
- `references/assessment.md` 负责证据与能力分类。
- `references/delivery-workflow.md` 负责长期开发阶段和返工循环契约。
- `references/artifacts.md` 负责自适应 Repository Output 的选择和内容。
- `references/compatibility.md` 负责多宿主与 Provider-specific 协调。
- `scripts/scan_repo.py` 和 `scripts/scan_repo.cjs` 实现同一个无第三方依赖的扫描器契约。
- `tests/test_scanners.py` 包含确定性的扫描器安全、边界和跨运行时 parity 回归测试。
- `agents/openai.yaml` 是可选的 OpenAI UI 元数据，不属于厂商中立核心。

## 开发

在仓库根目录运行确定性检查：

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
git diff --check
```

另外还应使用当前开发环境可用的 Agent Skills Validator 验证 Skill。在 Codex 源码环境中可使用已安装 `skill-creator` 的 Validator；其绝对路径和 PyYAML 环境与宿主有关，不能写入便携脚本或 CI。

Python `unittest` Suite 只属于开发 Harness，不是安装依赖；Node.js 可用时它会同时验证两套扫描器。扫描器行为已有确定性回归覆盖，但本仓库没有交付跨宿主 Agent 行为 Eval Harness，也不声称所有宿主具有相同的 Skill 发现、Sandbox、审批、Hook、Context Refresh 或委派语义。

## 许可证

MIT
