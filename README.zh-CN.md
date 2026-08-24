# Agentize Skill

[English](README.md) | [简体中文](README.zh-CN.md)

Agentize 是一个厂商中立的 Coding Agent Skill，也是一次性的 AI Development Harness Bootstrap。它把现有代码库改造成这样的仓库：Coding Agent 能找到正确上下文，在重大修改前先规划，在实现与验证之间闭环，通过评审和人工验收，在开发过程中持续捕获已确认知识，并在真实配置了自动化时于合并后审计晚期遗漏。

```text
仓库 -> 检查 -> 评估 -> 安装或修复 -> 验证 -> 可独立运行的 AI 开发 Harness
```

它会适应项目已有内容，而不是安装一套固定脚手架。有价值的结果会留在目标仓库中；Agentize 完成 Bootstrap 后就退出，不是运行时层、生成文件管理器、Hook 或 CI 依赖，后续会话无需持续安装它。简而言之：**Agentize should leave behind the system, not become the system.**

## 模型与宿主中立

核心是一个符合 Agent Skills 格式的 `SKILL.md`，以及可选的脚本和参考文档。它不依赖 OpenAI、Anthropic、Google、特定模型或某种调用语法。

每个 Agent 宿主自行决定如何发现或选择 Skill，以及文件、Shell、沙箱和审批能力如何工作。`agents/openai.yaml` 这类轻量的宿主专用元数据可以改善某个宿主的 UI，但它是可选的，也不会改变规范工作流。

Agentize 会保留并协调目标项目实际使用的指令表面，包括 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、嵌套规则和仓库内 Skill。它不会在没有证据时推测并创建供应商专用文件。

## 它做什么

Agentize 遵循一套自适应工作流：

1. 检查仓库和当前工作树；
2. 根据直接证据比较理想工作流与仓库真实具备的能力；
3. 安装或修复最小且安全的仓库侧上下文、工作流、验证、评审和学习路径；
4. 为仍依赖人类基础设施、凭据、权限、账号或平台设置的能力生成可执行的 Setup Guide；
5. 验证路径、命令、检查项和完整差异，并交付有明确作用域的能力报告、单次任务结果、未知项与可选投资。

用户无需选择内部模式。要求让项目适配 Agent 时，会运行自适应 Bootstrap，并报告理想流程中哪些环节真正建立成功。如果请求明确写明“仅审计”、“仅报告”或“不要修改”，默认保持静态只读评估：不会运行项目定义的测试、构建、包管理脚本、Lint 或浏览器流程，除非用户另外明确要求某项动态检查。

Agentize 会根据起点进行适配：

| 起始状态           | 行为                                             |
| ------------------ | ------------------------------------------------ |
| 没有有效工作流     | 创建最小且有证据支撑的指令、工作流、验证与学习骨架，并明确能力缺口。 |
| 部分工作流         | 保留有用内容，并补齐重要缺口。                   |
| 正确与错误内容并存 | 通过直接证据确认实际行为，并记录尚未明确的意图。 |
| 成熟工作流         | 进行窄范围修复，或报告无需实质变更。             |

一次非审计 Bootstrap 成功后，未来 Agent 应能找到简洁的仓库入口、理想开发流程、说明真实可用能力的 Harness Capability Report、项目特有的验证和人类决策点、持续知识捕获路径，以及已配置时才存在的合并后兜底审计。这些能力可以位于已有文件和外部 Review 系统中；Agentize 不要求固定文件名或示例 `docs/` 树。

根据证据，一次运行可能改进仓库指令、架构或领域上下文、任务定义和 Plan Review 指南、验证命令、聚焦脚本、测试、Lint、类型检查、E2E、浏览器业务流验证、MR/PR 模板、独立 AI Review 集成、CI、Setup Guide、交付或观测手册、持续知识捕获、合并后知识审计、决策记录或知识缺口。这些都不会被无条件添加。Agentize 优先使用已有工具，不把当前行为默认视为预期行为，并用简洁工作流契约路由到项目自己的详细资料，而不是把通用 Agent 教程复制到每个文件中。

## 它所准备的工作流

Agentize 自身的协调步骤并不是项目未来的开发工作流。它会记录下面这套理想工作流，并为仓库实际能够支持的部分准备 Harness：

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Fast Verification -> Targeted Browser Verification -> MR/PR <-> AI Review + Full CI -> Human Validate -> Merge -> Post-Merge Knowledge Audit -> Improve Harness
```

Continuous Knowledge Capture 从 Specify 一直贯穿到 Merge。Ship 和生产 Observe 是合并后的条件路径，只适用于确实运行可部署服务的仓库。

上面这条线表示理想流程，不代表每个环节都已安装，也不代表本次真的执行过。Agentize 会分别记录理想目标、仓库证据、实际就绪状态、需要人类完成的配置，以及本次任务的执行结果。这仍是一套有意保留人类参与的工作流：

- 非琐碎任务在执行前进入 Plan 与 Human Plan Review 循环；显然、可逆、低风险的修改可以走有边界的 fast path；
- Agent 可以结构化需求、探索项目、提出计划、实现、调试、运行检查、报告证据，并提议可持久的改进；
- 人类保留对重要业务意图、验收、风险容忍度，以及重大或不可逆操作授权的责任；
- 测试和 CI 只能证明它们实际检查到的内容，因此 Agent Verification 与 Human Validation 必须保持分离；
- 本地实现循环运行 Fast Verification：相关 Unit/Integration Test、Typecheck、Lint，以及必要的 Build，而不是每次修改后都运行全量 E2E；
- Targeted AI Browser Verification 只验证当前 Web/UI 变更涉及的验收流程，而且只有当前 Agent 宿主具备 Browser Controller、安全启动路径、测试身份/数据、认证和环境时才执行；证据必须标识实际测试的 Change 与环境，并以精确的状态断言而不是固定等待或模糊匹配作为通过依据；
- 使用 reviewed branches 的项目可以在 Fast Verification 后并行运行独立 AI Review 与 Full CI；Full E2E 和其他 Gate 只有在命令、Runner、环境、数据与权限均已配置时才算真实能力，绿色结果必须覆盖每个适用 Required Gate，包括取消、缺失或意外 skipped 的结果，并在重大风险需要时增加 Human Technical Review；
- 已有策略可以预先授权低风险流程流转，而重大的业务、安全、数据、资金、迁移或生产决策仍应由合适的人类负责；
- 无法获取的人类持有事实应转化为精确问题或阻塞项，而不是被虚构成规则；
- Continuous Knowledge Capture 是主要学习路径：开发中已确认且 Durable、Non-obvious、Reusable 的知识与适合的可执行约束随当前分支或 MR/PR 一起提交，Inferred 或 Unknown 内容继续保持未确认状态；Comment、Resolved Thread、“fixed”声明、同文件修改或 Merge 都只是 Candidate Signal，不是采纳证明；
- Post-Merge Knowledge Audit 只兜底检查 Review、CI、验收或最终返工中被持续捕获遗漏的晚期知识；自动执行需要真实合并 Trigger、上下文收集、Headless Agent Runner、项目已选择的模型接入、凭据、权限，以及经过人工评审的 Knowledge MR/PR 路径；
- 只有当项目具备真实平台、安全路径、权限和合适责任归属时，才会引入 MR/PR、独立 Reviewer Agent、托管学习自动化、发布、生产观测和并行 Agent。

对每个适用阶段，就绪的仓库应具备一条可行路径、一个明确的人类决策点，或一个有证据支撑且有解决方式的缺口。Workflow 文件、依赖、Framework、Instruction 或检测到的工具只是待核验证据，不是能力已经就绪的证明。前置条件不足时，Agentize 会尽可能安装安全的仓库侧部分，并留下聚焦的 Setup Guide 或建议，而不是替项目选择模型厂商、虚构凭据或假装该环节已经执行。规范的责任与转移规则位于 [`references/delivery-workflow.md`](references/delivery-workflow.md)。

## 能力状态与诚实降级

每次非审计 Bootstrap 都应留下或更新一份可发现的 Harness Capability Report。每个适用能力都要说明宿主或平台作用域、状态、证据、已可用部分、缺失配置、Setup Guide、Fallback、影响，以及重新评估条件。

| 状态 | 含义 |
| --- | --- |
| `READY` | 对明确作用域，完整路径已经配置并验证。 |
| `PARTIAL` | 一个有用且边界明确的子集可用，缺失部分已明确。 |
| `SETUP REQUIRED` | 仓库侧工作已完成，但仍需要具体的人类操作、账号、Secret、权限、环境或外部设置。 |
| `NOT AVAILABLE` | 当前没有安全可行的实现路径；报告应给出建议或 Fallback。 |
| `UNVERIFIED` | 证据不足，或无法安全完成验证。 |
| `NOT APPLICABLE` | 该能力不适用于当前仓库或作用域。 |

能力状态不等于单次任务结果。某项检查还要单独记录为 `PASSED`、`FAILED`、`NOT EXECUTED` 或 `NOT APPLICABLE`。如果 Browser Verification、E2E、AI Review、CI、Observability 或合并后自动化没有运行，交接必须说明原因、损失的置信度和适用的人类 Fallback；不能只写一句“已跳过”，随后却声称所有 Gate 都通过。

## 客观边界

- Agentize 不能替人推断并批准缺失的产品意图、业务含义、风险容忍度或最终验收。
- 它无法保证每种 Coding Agent 产品都读取相同指令文件；Provider 适配必须保持轻量，而且只为项目实际使用并验证过的宿主添加。
- 没有需要的 Browser Controller 或 E2E Framework、安全环境、应用启动路径、测试账号/数据、认证、Runner 与权限时，它无法让 Browser Verification 或 Full E2E 凭空可用。
- 没有真实 Agent Runner、项目已选择的模型接入、凭据、权限、上下文访问和平台 Trigger 时，它无法凭空创建独立 AI Reviewer 或自动 Post-Merge Knowledge Auditor。
- 它不能仅凭仓库文件和绿色测试证明外部分支保护已经生效、人类一定在线、生产安全或语义正确。
- 当上述能力是必需但不可用时，正确结果是明确的人类决策点或缺口，而不是伪造自动化。

## 当前状态

仓库当前包含：

- 供应商中立的 Agentize Skill；
- 证据、产物、人机协作交付和多 Agent 兼容性参考文档；
- 无第三方依赖的 Python 和 Node.js 只读扫描器，以及确定性的扫描器安全、边界和跨运行时 parity 测试；
- 可选的 OpenAI UI 元数据，核心能力不依赖它。

对某个 Agent 宿主宣称公开支持之前，仍需要可独立复现的行为证据，覆盖该宿主的 Skill 发现、上下文刷新、工具、沙箱、审批、Hook、会话和委派语义。当前没有交付跨宿主 Eval Harness、适用于当前版本的宿主资格记录或可安装 Plugin 产物。

## 安装与调用

### 让 AI 自动安装（推荐）

最简单的方式是把这个仓库地址发给具备安装能力的编程 Agent：

```text
https://github.com/woai3c/agentize-skill
```

建议使用以下请求：

```text
请帮我安装这个 Agent Skill，让它在我的所有仓库中都可用：
https://github.com/woai3c/agentize-skill
```

用于分发的 GitHub 仓库名是 `agentize-skill`；Skill 的规范名称和安装目录仍然是 `agentize`，所以调用示例继续使用 Agentize 或 `$agentize`。

如果只想在当前仓库中使用，需要在请求中明确说明。具备安装能力的 Agent 应根据当前宿主的文档选择发现路径，保留完整的 Skill 目录，验证可发现性，并报告准确的安装路径。安装需要网络和文件系统权限；部分宿主可能需要新建会话才能发现新安装的 Skill。安装任何第三方 Skill 前，都应检查其源码和安装的修订版本。

### 安装后如何使用

1. 在编程 Agent 中打开要改造的现有仓库。如果 Agentize 是在当前会话开始后安装的，但 Skill 列表中还看不到它，请新建会话。
2. 宿主有 Skill 选择器时，直接选择 Agentize；也可以在请求中明确写出“使用 Agentize”。你不需要自己运行仓库扫描器。
3. 说明你想要的结果。普通 Agentize 请求可能修改仓库文件，并运行宿主允许的安全相关检查；如果只需静态只读评估，需要明确写出“仅审计”或“不要修改”。
4. 检查最终差异、验证证据、未知项，以及保留给人类判断的问题。如果存在阻塞性产品或风险问题，回答后在同一会话中继续即可。

推荐的一次性 Bootstrap 请求：

```text
使用 Agentize 一次性把这个现有仓库改造成可独立运行的 AI 开发 Harness。保留它当前的工具和约定，记录理想工作流，并用最小且有证据支持的变更安装当前真正能够支持的 Planning、Fast Verification、Targeted Browser、MR/PR Review 与 Full CI、Human Validation、Continuous Knowledge Capture 和 Post-Merge Audit 路径。不要替项目选择模型厂商，也不要仅凭文件推断能力已经就绪。为人类持有的前置条件生成聚焦的 Setup Guide，安全验证能够验证的部分，最后分别报告有明确作用域的 Harness Capability Report、单次任务结果、差异、未知项、Fallback 和仍需人类决定的问题。
```

只读审计：

```text
使用 Agentize 审计这个仓库的 Agent 工作流。不要修改文件，也不要运行项目定义的命令。报告证据、缺口、冲突和未知项。
```

聚焦修复：

```text
使用 Agentize 协调这个仓库的 Agent 指令与真实验证命令。保持无关文件不变。
```

通常一次成功的 Bootstrap 就够了。后续 Feature 和 Bug 开发应直接遵循目标仓库留下的指令、上下文、检查、评审关卡与学习路径，无需再次调用 Agentize。只有当仓库或工具变化后，你明确想重新审计或修复 Harness 时才再次运行它。用户级安装仍可用于改造其他项目；仓库级安装只限该仓库树。重复运行是收敛的：一个正确且未变化的仓库不应产生实质差异。

### 手动安装与作用域

开放的 [Agent Skills 规范](https://agentskills.io/specification) 标准化的是 Skill 目录的内容，并不规定宿主必须从哪个路径发现 Skill。安装位置属于各宿主的约定。

例如，[Codex 当前会从多个位置发现本地 Skill](https://developers.openai.com/codex/skills)。可在多个仓库中复用的 Agentize 通常安装到用户级路径：

```text
~/.agents/skills/agentize/
```

如果要将 Agentize 固定在某个仓库中，则使用：

```text
<repository>/.agents/skills/agentize/
```

Codex 会从当前工作目录一直到仓库根目录，扫描各级 `.agents/skills` 目录。用户级 Skill 可在多个仓库中使用；仓库级 Skill 只对该仓库树生效。其他宿主可能使用不同路径，因此应遵循当前宿主的文档，不能把 Codex 的目录布局当成通用规则。

## 扫描器

普通使用无需手动运行扫描器；Agentize 会在工作流中运行可用的实现。以下命令用于手动检查和开发。两个随附扫描器都只使用各自运行时的标准库，并且不会修改目标：

```text
node scripts/scan_repo.cjs --root /path/to/repository --format markdown
node scripts/scan_repo.cjs --root /path/to/repository --format json
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

它会清点指令表面、Skill、宿主配置、清单、已声明命令、文档、测试、质量配置和 CI。支持的指令文件代码块中的验证命令会被保守识别，但绝不会执行。诊断提示只是调查线索，不是自动质量判断、宿主策略已生效的证据，也不代表获得了执行项目命令的权限。收集到的文本会对常见凭据语法做尽力脱敏，但报告仍然是敏感的本地证据，共享前必须检查。Git 元数据调用会禁用仓库 fsmonitor 执行，移除继承的 `GIT_*` 仓库选择器，并且只查询仓库身份与分支。它们不会运行 status 或 diff，因为 Git 可能执行仓库配置的内容过滤器；因此 Schema v4 会将工作树脏状态报告为 `unverified`，计数报告为 `null`，绝不会默认为“干净”。仓库身份也是三态：`true` 表示已验证，`false` 表示在目标路径上未找到 `.git` 标记，`null` 表示存在标记但无法验证 Git 身份。Agentize 优先使用 Node.js 实现，不可用时回退到 Python；如果两者都不可用，就使用宿主现有的只读工具复现有界的清点，并将无法确定的字段标记为 `unverified`。它绝不会仅为运行扫描而安装运行时。

## 开发

运行扫描器回归测试，并用 Skill 检查它自身：

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
git diff --check
```

Python `unittest` Harness 只属于开发依赖；Node.js 可用时它会同时验证两套扫描器。安装或使用 Agentize 时，只要 Node.js 扫描器或宿主工具降级路径可用，就不需要 Python 测试环境。[`DESIGN.md`](DESIGN.md) 定义产品边界、验证策略与验收标准。

## 许可证

MIT
