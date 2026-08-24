# Agentize 可实施设计

状态：仓库侧实施基线已交付；跨宿主完整验收尚未完成。

## 1. 目标

Agentize 是一次性的 **AI Development Harness Bootstrap**。它把已有项目改造成适合
Coding Agent 高效、可靠工作的仓库：审计现状，修复错误或过期信息，安装长期运行所需
的上下文、阶段契约、验证、评审、持续知识捕获和学习路径，并把结果留在项目自身可维护
的文件、命令和自动化中。它不追求让 Agent 代替人提供业务意图、承担风险或验收自己的
结果。

核心设计约束是：**Agentize should leave behind the system, not become the system.**

它只有一条自适应工作流，不要求用户理解或选择内部模式：

```text
scope -> inventory -> assess -> install or repair -> verify -> handoff -> exit
```

这是 Agentize 一次协调任务的流程。它需要为目标仓库建立或修复的是另一条长期研发
闭环：

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Fast Verification -> Targeted Browser Verification -> MR/PR <-> AI Review + Full CI -> Human Validate -> Merge -> Post-Merge Knowledge Audit -> Improve Harness
```

`Continuous Knowledge Capture` 从 Specify 贯穿到 Merge；Post-Merge Knowledge Audit
只是捕获 Review、CI、Human Validation 与最终返工中遗漏知识的兜底。Ship 和 Observe
仍是部署型项目的条件阶段。

两条流程不能混淆。双向箭头表示真实返工循环：Plan 反馈可以要求重新 Explore，验证
失败返回 Execute，AI Review、Full CI 或 Human Validation 不通过后必须重新修改、快速
验证、按条件执行 Browser Verification 并更新 MR/PR。第二条是 **Ideal Workflow**，不是
当前仓库已经配置所有能力的声明。Agentize 必须分别表达：理想流程、当前实际能力、仍需
Human Setup 的能力和本次任务的真实执行结果。

产品约束：

- 用户要求“agentize”“make this repository agent-ready”“建立或修复 AI 开发工作流”
  或同等结果时，Agentize 完成一次端到端协调。
- 用户明确要求只审计、只报告或不修改时，默认执行静态评估：流程停在有证据的报告，
  不写目标仓库，也不执行项目定义的测试、构建、Lint、包管理器或浏览器命令。只有用户
  在审计请求中另外明确要求某项动态检查时，才检查其定义和副作用后执行该项检查。
- 用户给出的文件、目录、工具或风险限制始终优先；不把宽泛请求扩大成无关产品改造。
- 目标是最小可靠状态，不是固定脚手架或最大工具集合；成熟仓库允许零修改。
- 理想流程只是规范目标。文件、依赖或文字说明的存在不能把 Browser、E2E、AI Review、
  CI、Observability 或 Post-Merge Audit 自动标记为可用。
- 完整 Planning Loop 是非琐碎或重大任务的默认路径；小、可逆、意图明确且有现成验证
  的低风险修改可以走有边界的 fast path，但不能跳过必要探索、验证和真实交接。
- Human-in-the-loop 是目标系统的正式组成：Agent 可以整理、质疑和建议，不能替有权
  负责人确认业务含义、风险容忍度、产品验收或不可逆操作。
- 自动检查证明的是其断言覆盖的行为，不自动证明需求本身正确；Human Validation 也
  不替代成本合理、与风险相称的 Agent Verification。
- Agentize 运行后，目标仓库不依赖本 Skill。用户可以卸载它而不影响后续 Agent。
- 开发中持续捕获已经确认的 Durable、Non-obvious、Reusable 知识，与当前 Feature/Bug
  一起进入 MR/PR；Inferred 和 Unknown 仍保留 Evidence、Confidence、影响与确认所有者。
- MR/PR、独立 Reviewer Agent、Full CI/E2E、浏览器业务流、发布、观测和自动 Post-Merge
  Audit 只有在项目确有平台、Runner、环境、数据、权限和责任人时才标记 READY；缺少
  Human 配置时生成 Setup Guide 并标记 SETUP REQUIRED，不能靠 YAML 或框架文件伪装。
- Post-Merge Knowledge Audit 只检查持续捕获遗漏的晚期知识，不重新总结全部改动；自动
  触发必须真实存在，Candidate 不直接写默认分支，经 Knowledge MR/PR 或等价评审确认。
- 再次运行是新的用户请求，不由 Hook、CI、启动事件或定时任务自动触发。

职责边界：

| Agentize Bootstrap 当次负责 | 目标仓库长期负责 |
| --- | --- |
| 定界、静态清点、证据分级和冲突识别 | 给未来 Agent 提供可发现的 Context 与真实规则 |
| 选择并安装最小适用 Harness | 驱动 Specify、Plan Review、Execute、Verify、Review 和 Human Validate |
| 验证新增路径、命令、规则与差异 | 通过 Test/Lint/Type/Schema/CI 持续执行机械约束 |
| 自动安装安全且有证据的仓库侧能力，为 Human Setup 生成 Guide | 按 Capability Report 完成外部配置，并验证状态转为 READY |
| 建立 Continuous Knowledge Capture，条件满足时安装 Post-Merge Audit | 开发中更新 Harness；合并后只审计遗漏的晚期知识 |
| 准确交接、报告缺口并退出 | 在完全卸载 Agentize 后独立运行和维护 |

## 2. 厂商和模型中立

Agentize 的核心面向 Agent Harness，而不是某个模型名称。模型负责判断，宿主负责
Skill 发现、文件访问、进程执行、沙箱和审批；同一个模型也可能运行在能力不同的
宿主中。因此兼容性以宿主实际能力为准，不以 OpenAI、Anthropic、Google 或其他
模型厂商为产品前提。

可移植核心只依赖 Agent Skills 的通用结构：

```text
agentize/
├── SKILL.md
├── references/
├── scripts/
└── tests/
```

- `SKILL.md` 的 `name` 和 `description` 负责让支持 Agent Skills 的宿主发现何时使用
  该能力；宿主可以自动选择，也可以允许用户显式选择。
- 不规定 `$agentize`、`@agentize`、slash command 或命令面板中的哪一种是唯一入口。
- `agents/openai.yaml`、Claude/Gemini 配置或其他厂商文件只能是可选的薄元数据，不
  进入核心工作流，也不能成为其他宿主的安装前提。
- Skill 不选择或要求特定大模型，不维护厂商专用正文副本。
- 当目标项目已有 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 或其他有效表面时，先验证
  各宿主如何发现和叠加它们，再保留权威来源和必要差异。

宿主不能写入时仍可完成只读评估，但不得声称已经 agentize。宿主没有脚本运行时
可以使用自身的只读文件和搜索工具降级，不因此失去核心判断能力。

## 3. 目标与授权边界

- 用户提供路径时，规范化为一个可访问的目标目录。
- 未提供路径时，使用当前目录所属 Git 工作树的根；没有 Git 时使用当前目录。
- 后续扫描、读取、Git 查询、命令工作目录和写入始终使用这个规范化目标；只有确认当前
  工作目录与其相同时才能用 `.` 代替。
- 多根工作区、嵌套仓库或目标意图不唯一时，在大量读取或写入前请求选择。
- 先读取适用的 Agent 指令。扫描器只安全确认 Git 仓库身份与分支，不运行可能触发
  clean/process filter 的 status 或 diff；其 `worktree_state: unverified` 表示未知而非
  干净。已有可信宿主变更视图时可以复用；否则在写入前逐个核对会重叠的路径，无法安全
  判断时停止，而不是为了填空在静态审计中执行内容比较命令。
- 扫描和修改只作用于目标根；宿主提供的上级指令仍需遵守，但不是修改对象。

“让项目适合 Agent 工作”授权的是目标仓库内与该结果直接相关的改进，例如指令、
聚焦文档、验证入口和有证据支持的反馈回路。它不自动授权：

- 改变产品需求或业务行为；
- 发布、部署、生产操作或数据迁移；
- 提交、推送、创建 PR 或操作外部系统；
- 读取或复制凭据；
- 与 Agent 工作流无关的依赖升级或重构。

新增依赖、修改 lockfile、下载工具、增加组织级 CI 成本或采用多个同样合理的新框架
时，遵守宿主权限并在影响重大时先说明取舍。不要把这些边界变成要求用户预先选择
“模式”的界面。

## 4. 双运行时扫描器

扫描器把重复、机械的仓库清点变成稳定证据；它不替代 Agent 判断。双运行时覆盖
Node-only 和 Python-only 环境：

1. Node.js 可用且 `scripts/scan_repo.cjs` 已交付时，运行 Node.js 实现。
2. 否则依次检测 `python3`、`python`，Windows 再检测 `py -3`，运行
   `scripts/scan_repo.py`。
3. 两者都不可用，或对应执行器尚未交付时，使用宿主已有的只读工具完成有界清点，
   并把不能确定的内容标记为 `unverified`。
4. 不为了扫描自动安装 Node.js、Python 或第三方包。

两个执行器提供同一接口：

```text
node <skill-root>/scripts/scan_repo.cjs --root <repo> --format json|markdown
<python> <skill-root>/scripts/scan_repo.py --root <repo> --format json|markdown
```

共同契约：

- 只读清点指令、Skill、宿主配置、文档、清单、任务、测试、质量配置和 CI；保守识别
  支持的指令代码块中的验证命令，但绝不在清点阶段执行。
- 只静态解析白名单格式，不 import、构建或执行项目代码。
- 对文件数和单文件大小设界限；只有观察到第 `max_files + 1` 个可纳入文件时才报告
  截断，并记录权限错误和跳过项。
- Git 身份调用先移除继承环境中的全部 `GIT_*` 变量，再只设置非交互、无可选锁和无
  Pager 的允许项，同时禁用仓库 `core.fsmonitor` 与 untracked cache。扫描器只运行
  `rev-parse` / `symbolic-ref` 类身份查询，不运行 status、diff 或其他会比较工作树内容
  的命令，因此不会启动仓库配置的 clean/process filter。
- Schema v4 的 `is_repository` 使用三态：Git 身份已验证为仓库时是 `true`，沿目标祖先
  确认没有 `.git` 标记时是 `false`，存在标记但 Git 不可用、超时、配置损坏或身份查询
  失败时是 `null`。后者同时给出稳定的 `repository_state: unverified` 与原因枚举，不把
  查询失败误报成非仓库。
- Git 工作树脏状态明确为 `unverified`，`dirty_path_count` 为 `null`；不能安全采集时绝
  不以空列表或零计数表示“干净”。
- 不跟随仓库外符号链接，不主动读取已知凭据文件；对收集到的标题和命令正文执行常见
  凭据语法的尽力脱敏。扫描报告仍按敏感的本地证据处理，启发式脱敏不能证明其中绝无
  未知格式的秘密。
- 输出带版本的稳定 Schema；诊断只是调查线索，不是质量结论或执行授权。
- 输出标识扫描器实现，跨运行时比较时只规范化实现标识、平台路径和已记录的错误文本差异。
- `package.json` 使用严格 JSON（拒绝 `NaN`/`Infinity`）；常规
  `[project.scripts]` 字符串入口、Make、Just 和 Taskfile 顶层 `tasks` 只按明确的静态
  子集解析；不为获得更宽松的配置解析而加载或执行项目代码。
- Node.js 与 Python 共享 Schema、fixture、排序和截断规则。规范化平台路径、错误文案
  和实现标识后，字段语义必须等价，不要求原始字节完全一致。

当前实现已经交付 Python 和 Node.js 两个扫描器。共享 fixture 覆盖清单、任务与文档
验证入口、常见凭据脱敏、Unicode 和空格路径、畸形百分号链接、Vendored 目录、文件
上限、仓库外符号链接、畸形 JSON 以及 JSON/Markdown 输出 parity；没有对应运行时
时仍按上述顺序降级。

## 5. 自适应协调流程

### 5.1 定界和清点

1. 确定目标、用户限制、适用指令和工作区状态。
2. 运行可用扫描器；没有运行时时用宿主工具降级。
3. 读取 `references/assessment.md`，按其中的证据规则和能力 rubric 判断现状。
4. 只补充读取解决当前判断需要的清单、任务配置、CI、入口、代表性测试、维护文档
   和必要 Git 历史。

### 5.2 选择最小可靠状态

根据证据决定需要什么，而不是套模板：

1. 修复已有权威来源中的错误、过期路径和冲突。
2. 确保未来普通 Coding Agent 能从一个简洁入口找到长期工作流、项目上下文、真实验证
   命令、人类决策点和学习所有者；优先补到已有文件或工作流。
3. 信息没有合适所有者时才创建一个聚焦的厂商中立文档或确定性脚本，不生成空的示例
   `docs/` 树、通用 Agent 教程或 Agentize 标记。
4. 已确认规则能被廉价、确定地机械验证时，优先增加或修复 Test、Lint、Type、Schema、
   Architecture Check、脚本或 CI，而不是只加自然语言。
5. Browser、Full E2E、AI Reviewer、MR/PR CI、Observability 和 Post-Merge Audit 等能力
   先核对平台、环境、数据、权限、Runner、成本与失败行为；能安全自动配置的就配置，
   需要 Human 外部配置的生成 Setup Guide，无法选择或建立的保留 Recommendation。
6. 项目已经可靠时不修改，只说明证据和可选投资。

#### Harness Capability Status

证据质量仍使用 `sound/weak/missing/conflicting/stale/unverified/not_applicable`；面向开发者
和未来 Agent 的运行状态单独使用：

| Status | 含义 |
| --- | --- |
| `READY` | 对明确 Host/Platform Scope 的完整路径和前置条件已配置，并有安全代表性验证或直接平台证据。 |
| `PARTIAL` | 有用子集可运行，但明确列出的部分或 Scope 仍缺失，并提供降级路径。 |
| `SETUP REQUIRED` | 仓库侧已尽量安装，但 Secret、Account、Permission、External Setting、Environment 或 Provider Choice 仍需 Human 完成；验证前不算 Ready。 |
| `NOT AVAILABLE` | 当前没有可用实现，也没有在范围内安全选择或安装一条路径；只给有证据的建议。 |
| `UNVERIFIED` | 表面配置存在，但无法安全证明实际激活或行为。 |
| `NOT APPLICABLE` | 直接证据表明能力不适用于该仓库或 Scope。 |

能力状态与当前任务执行结果分开。本次 Gate 使用 `PASSED`、`FAILED`、`NOT EXECUTED` 或
`NOT APPLICABLE`；`NOT EXECUTED` 必须写明 Capability Status、原因、证据缺口、影响、
Fallback 和 Human Action。不能把 `SETUP REQUIRED`、`NOT AVAILABLE` 或 `UNVERIFIED`
压成一个无声的 skipped，也不能因此声称 all gates passed。

非审计运行必须留下可发现的 Harness Capability Report。每行包含 Capability、Scope、
Status、Evidence、当前可工作路径、缺少的 Setup、Guide/Owner、Fallback、Consequence 和
重新评估触发条件。Audit-only 只在报告中输出，不写入仓库。若需 Human 配置，复用已有
Setup 文档；没有所有者时可创建聚焦的 `docs/setup/<capability>.md`，但不强制整棵目录。
Guide 只记录 Secret 名称而非值，并包含安全验证步骤；生成文件本身不能把状态升级为
`READY`。

`references/delivery-workflow.md` 是每次审计和协调长期工作流的规范输入；它定义能力，
不要求复制原文。写入前读取 `references/artifacts.md`。目标仓库涉及多个 Agent 产品、
provider 文件、Skill、Hook 或配置时，再读取 `references/compatibility.md`。

### 5.3 安装长期 Harness

Agentize 的输出不是固定文件集合，而是以下能力在项目现有所有者中的最小实现：

1. **入口与 Context**：保留正确、项目特有的内容和既有术语；根指令简洁导航，详细
   架构、产品、开发、验证和运维知识进入现有权威来源。一个事实只有一个所有者，
   provider 表面只保留必要差异。
2. **Specify / Explore**：复用 Issue、Spec、RFC 或任务系统承载 Goal、Requirement
   Context、Constraints、Success Criteria、Acceptance Criteria、风险和 Unknowns；
   明确 Explore 要检查的源码、测试、配置、历史和已有模式，不让实现步骤替代真实目标。
3. **Plan Review**：非琐碎任务必须先给出需求理解、方案、范围、受影响模块、架构影响、
   风险、验证计划和未知项，并有 Human Plan Review 返回重新 Explore/Re-plan 的路径；
   fast path 的适用条件必须窄而可解释。
4. **Execute / Fast Verification / Browser**：本地循环只执行相关 Unit/Integration、
   Typecheck、Lint、必要 Build 和低成本目标检查。Fast Verify 通过后，涉及 Web/UI 且
   Browser Capability 为 `READY` 时，Agent 按 Acceptance Criteria 操作当前业务流；否则
   明确 `NOT EXECUTED`、影响和 Manual Fallback。Browser Evidence 绑定实际测试的 Change、
   Build/Start State、Environment、Controller、Test State 与精确状态断言；固定等待、模糊
   字符串或无 Provenance 的截图不能单独证明通过。Full E2E 不进入每次编辑循环。
5. **MR/PR / AI Review / Full CI**：使用项目既有 MR/PR 或等价 Review 表面携带 Plan 偏差、
   风险、能力状态、验证结果和仍需 Human Validation 的内容。配置好的独立 AI Reviewer
   与 Full CI 并行；Full E2E 只有 Framework、Command、Environment、Seed/Test Database、
   Runner 与权限均可用时才是 Gate。失败返回修改、Fast Verify、条件 Browser Verify 和
   MR/PR 更新。每个适用 Required Gate 都必须有显式结果；失败、超时、取消、缺失或意外
   skipped 不能被绿色 Aggregate 隐藏。只有已证明存在重复定义或漂移风险时才建立统一的
   Machine-readable Gate Inventory。重大领域保留风险驱动的 Human Technical Review。
6. **Human Validate / Merge**：机器证据回答技术实现是否满足已知检查，人类或已有治理
   回答结果是否真是想要的。Human Validation 不通过后完整返回修改、验证和评审；Merge、
   发布、迁移与生产操作继续遵守独立授权。
7. **Continuous Knowledge Capture**：开发全程识别 Durable、Non-obvious、Reusable
   Knowledge；已经由权威来源或 Human 明确确认的内容立即路由到 Product、Architecture、
   Development、Verification、Operations 或 Executable Constraint，并随当前 MR/PR 评审。
   Comment、Resolved Thread、“fixed”声明、同文件修改或 Merge 只是 Candidate Signal；
   只有语义权威与 Final-state Adoption Evidence 均成立时才能升级为长期知识。
8. **Post-Merge Knowledge Audit**：只审计 Review、Full CI、Human Validation、最终返工与
   Observe 中持续捕获遗漏的晚期知识。自动运行必须具备真实 Merge Trigger、Headless
   Agent、Model Integration、Credentials、Permissions 与 Context Access；否则分别标记
   `SETUP REQUIRED` 或 `NOT AVAILABLE`。发现遗漏时走独立 Knowledge MR/PR；无遗漏零改动。

持续与合并后知识处理都必须区分：`Observed` 具有直接证据或明确授权决定；`Inferred`
保留 Evidence 和 Confidence 但不是规范；`Unknown` 说明问题、工程影响和确认来源。只有
有权的人确认后，重要推断或未知项才能升级成 Business Rule、Acceptance Criteria 或
永久机械约束。

Provider 文件、Plan 提示、Hook、审批、Sandbox、Reviewer 配置或 CI 文件的存在不自动
证明约束生效；记录实际消费者、执行层、范围、失败行为和直接证据。若修改只在显式
Reload 或新会话后可见，交接要说明刷新边界。不写 generated-by banner、Agentize 标记、
空模板或项目未使用的厂商文件。

### 5.4 验证和交接

1. 重跑可用扫描器或重复有界清点。
2. 检查新增路径、相对链接和记录的命令。
3. 在执行项目命令前检查其定义、工作目录、前置条件和明显副作用。
4. 运行与修改相称且在当前权限内的目标检查；每项相关 Gate 单独记录 `PASSED`、
   `FAILED`、`NOT EXECUTED` 或 `NOT APPLICABLE`。未执行时同时记录 Capability Status、
   原因、影响、Fallback 和 Human Action。
5. 通过可信宿主 diff 或本次精确补丁检查完整变更，确认没有覆盖无关用户改动。只有已
   信任仓库转换驱动时才运行 `git diff --check`；否则使用非 Git 空白检查并把该项记为
   `NOT EXECUTED`，同时说明原因与影响。
6. 生成或更新 Harness Capability Report 和所需 Setup Guide，逐项核对 `READY` 证据；
   Setup 文件、YAML、Framework 或 Instruction 存在本身不能作为 Ready 证据。
7. 分开报告 Agent Verification 与仍需 Human Validation 的内容；没有直接证据或有权
   人员明确决定时，不声称结果已验收、all gates passed、发布或生产安全。
8. 报告起点、实质变化、未验证项、Capability Gaps、知识缺口和可选下一步。请求关键
   能力不为 `READY` 且没有安全 Fallback 或 Human 解决路径时，只能报告部分准备完成，
   不能声称仓库已经完全 agent-ready。

本节适用于全部非审计协调，包括经评估后刻意零修改的成熟仓库结果；零修改不等于跳过
验证和交接。如果用户要求只审计，第 5.3 节和面向修改任务的动态验证命令都不执行，
交接必须明确这是静态评估而不是已完成初始化。用户在同一请求中另行点名的动态检查是
唯一例外，其结果和产生的副作用必须单独报告。
如果流程中途受阻，准确列出已经发生的改动，不通过破坏性 Git 操作隐藏部分结果。

## 6. 高效 AI 工作流的能力目标

`references/delivery-workflow.md` 是长期研发阶段、返工循环、责任边界和完成条件的唯一
规范源；
`references/assessment.md` 维护状态与能力 rubric，`references/artifacts.md` 维护仓库
侧产物选择。Agentize 关注以下能力，而不是给目标仓库写一套通用 Agent 教程：

- **快速定位**：目的、入口、模块和所有权边界容易找到。
- **范围化约束**：Agent 能知道当前目录适用的真实规则和安全边界。
- **宿主执行真实度**：重要约束明确区分提示指导、工具策略、审批、Sandbox、仓库检查
  和外部治理，并能说明当前宿主是否真的加载、执行和阻断。
- **稳定上下文**：非显然的架构、领域和决策原因有明确所有者。
- **工作定义**：重要任务有可发现的 Goal、Constraints、Success Criteria、Acceptance
  Criteria、范围、风险和未决问题来源，不从实现步骤反推产品意图。
- **Planning Loop**：非琐碎任务先 Explore 并输出需求理解、方案、范围、架构影响、风险、
  Verification Plan 和 Unknowns，经 Human Plan Review 后执行；低风险显然改动有窄范围
  fast path。
- **执行路径**：Agent 能实施、调试和交接，失败会返回 Modify/Retest，不把一次输出当作
  完成。
- **Fast Verification**：开发循环只使用相关 Unit/Integration、Typecheck、Lint、必要 Build
  与低成本目标检查，命令准确且可执行，结果说明证据覆盖与排除项。
- **Browser Capability**：Agent 真实操作浏览器的目标业务流与 E2E 分开定义；Controller、
  App Start、Test Account、Seed/Auth、Environment 和 Host Scope 均有证据才标记 READY；
  执行证据能追溯到实际 Change、运行环境、Test State 和精确状态断言。
- **MR/PR 与 Full CI**：适用项目在 Fast/Browser Verification 后进入 MR/PR，配置好的独立
  AI Review 与 Full CI 并行；Full E2E 在这里做广泛 Regression，而不是每次本地修改都跑；
  任何适用 Required Gate 的失败、取消、超时、缺失或意外 skipped 都不会汇总成绿色结果。
- **Human Validation**：项目明确哪些结果仍需人根据产品意图和风险作出接受、拒绝或
  修改决定；Agent 不验收自己的解释。
- **交付与观察**：适用项目能找到合并、发布、回滚、运行状态和成功信号，以及需要的
  权限和责任人；仓库文档不伪装成外部控制已生效。
- **持续知识捕获**：Human/Agent 交互、实现、测试和 Review 中已确认的 Durable、
  Non-obvious、Reusable 知识随当前 MR/PR 更新 Harness；Review 生命周期信号必须结合权威
  语义和最终采纳证据，不能仅凭 Thread resolved 或 Merge 自动升级。
- **合并后审计**：只兜底检查持续捕获遗漏的晚期知识；没有真实 Trigger 和 Agent Runtime
  时不能自动发生，有遗漏才创建独立 Knowledge MR/PR。
- **能力透明度**：Ideal Workflow、Capability Status、Human Setup 与 Task Execution Outcome
  各自独立；未来 Agent 能找到 Capability Report 和 Setup Guide。
- **知识来源**：Observed、Inferred、Unknown 保留不同语义、Evidence、Confidence、影响
  和确认所有者；当前实现或模型推断不会静默升级成产品政策。
- **知识缺口**：重要未知项明确说明为什么影响决策以及谁能解决。
- **持续维护**：项目特有事实变化时能找到应该同步更新的规范源。
- **恢复安全**：存在外部副作用的项目能区分失败与未知结果，并在重试前检查状态、
  使用幂等路径或交给有权的人决定。
- **并行准备度**：只有任务可分离、验证可靠且共享资源有隔离方案时，才把 Worktree
  或多 Agent 作为可选吞吐优化。

这些能力不意味着机械增加文件或工具：

- 不把完整教程复制进每个 `AGENTS.md`；但必须留下一个简洁、规范的流程入口和项目特有
  路由，否则未来 Agent 无法只依赖仓库执行上述闭环。
- Web/UI 项目只有在 Browser Controller、启动方式、Test Account/Data、Auth 和安全环境
  已验证时才标记 Browser READY；否则生成 Setup Guide 或 Recommendation，并明确 Manual
  Verification Fallback。
- 当前实现可以证明“现在怎样”，但不能单独证明“应该怎样”。测试预期来自用户
  说明、产品规范、稳定公共契约或多个一致的直接信号。
- 低风险、可逆的小改动不需要重型 Spec 或审批；高影响业务、安全、权限、资金、迁移、
  生产和不可逆变化不能由 Agent 自己决定验收强度并批准。
- `Ship` 与 `Observe` 对部署服务可能重要，对本地库或纯文档项目可能不适用；不为了
  补齐流程图而创建发布、监控或外部平台配置。
- MR/PR、独立 Reviewer Agent、Full E2E 和自动 Post-Merge Audit 不是所有宿主的内建能力。
  缺少平台、Runner、Environment、权限或模型接入时，保留状态、真实人工路径和精确 Setup，
  不由 Agentize 选择厂商或添加秘密。
- 新工具必须解决已经证明的反馈缺口；优先复用和修复已有工具，不平行建立第二套。
- 后续维护由目标仓库自己的规则和自动化完成，不自动重跑 Agentize。

Agentize 可以创建或修复承载这些能力的仓库侧接口，但不能保证团队实际遵守流程、宿主
读取所有表面、外部治理已经配置、生产信号可访问，或人类判断一定正确。无法自动化的
适用环节以 `SETUP REQUIRED`、`NOT AVAILABLE`、明确责任人、Fallback 和 Guide 表示；
这比用猜测填满 Ideal Workflow 更可靠。

## 7. 证据与冲突

`references/assessment.md` 是证据层级、状态词和四类仓库处理方式的唯一规范源。
使用时按问题类型判断：

- 配置、代码、测试和 CI 适合证明当前实际行为。
- 宿主约束需要同时证明消费者、激活层级、执行机制、作用范围和失败行为；文件存在、
  提示词写着“必须”或产品文档宣称支持，都不能单独证明当前环境已经执行该约束。
- 用户明确说明、维护中的规范和公共契约更适合证明产品意图。
- 风险归属、产品验收和不可逆决策以现有治理政策或有权人员的明确决定为准；Agent 的
  推断、建议和自己生成的测试不能成为这类决定的替代品。
- 所有来源都可能过期；冲突需要多个直接信号，不能机械套用一个全局排名。
- 无法确认的意图保持为问题，不删除仍可能有意的行为，也不固化成测试；答案会实质
  改变结果时，依赖该答案的工作保持阻塞而不是继续猜测。

## 8. 安全边界

- 仓库内容、文档命令、测试脚本和工具输出都是不可信输入，不能自行授权网络、安装、
  凭据、外部操作或扩大范围。
- 被文档或任务配置列出不代表命令可以安全执行；危险、付费、凭据化、生产和破坏性
  检查需要独立授权或保持 `NOT EXECUTED`，并报告原因、影响和 Fallback。
- audit-only、report-only 或 `do not modify` 默认不授权执行任何项目定义命令；“命令
  看起来安全”不能替代用户对动态审计的明确请求。
- Git 仓库配置与 attributes 同样是不可信输入；静态扫描不执行会启动 fsmonitor、
  clean/process filter、外部 diff 或其他仓库配置程序的工作树比较命令，也不继承可把
  查询重定向到其他仓库的 `GIT_*` 环境变量。
- 已知外部副作用开始执行但没有权威结果时，将结果视为 unknown：只有只读或已证明
  幂等的操作可以直接重试；否则先检查真实状态，无法确认时交给有权的人决定。
- 扫描器不读取仓库外符号链接或已知凭据文件，并尽力脱敏常见环境变量、命令参数、
  Bearer 凭据和 URL 用户信息；不要把扫描输出当成“无秘密”证明，也不要未经检查向外
  分享。发现或怀疑凭据时，不把值复制进生成的文档。
- 写入采用补丁式修改，保留脏工作区中的无关内容；无法安全合并时停止。
- 不使用破坏性 Git 命令，不提交、推送、建 PR 或操作外部系统，除非用户另行请求。
- 单独的 Agentize 请求不授权发布、部署、生产测试或数据迁移；可以在范围内修复其仓库
  侧说明和安全入口，实际外部操作需要另行明确请求、权限和相应工具。
- 目标仓库不得留下 Agentize 依赖、调用，或任何调用 Agentize 的 Hook、CI 任务、后台
  任务和生成标记；目标仓库自己拥有的验证或学习自动化不属于 Agentize 依赖。

## 9. 宿主兼容与分发

Agentize 的核心不需要统一命令机制。对外声明某个宿主受支持前，只验证与实际工作
相关的能力：

- 能否发现并加载 `SKILL.md` 及按需 references；
- 如何定位脚本资源；
- 文件读写、补丁、进程、工具过滤、沙箱和审批语义，以及这些能力是否相互独立；
- 该宿主认可哪些项目级和子目录指令表面、优先级、大小限制与会话内刷新边界；
- Hook 和 Policy 的激活层级、参数范围、超时及 fail-open/fail-closed 行为；
- Session、Compaction、Resume、Checkpoint 和未知工具结果的语义；
- Subagent 的上下文、权限、工作区隔离、并发上限、结果来源与集成责任；
- Node-only、Python-only 或无运行时情况下如何降级。

宿主专用 UI 元数据可以随 Skill 提供，但不得改变核心判断或制造另一份正文。直接
Skill 安装是开发和本地使用方式；未来若确有分发需求，可以从同一规范源生成
Plugin 或宿主包。未实际生成和测试的分发物不能在 README 中宣称已支持。

## 10. 测试方案

### 10.1 扫描器

- 自动化 fixture 分别直接调用已交付的 Python 与 Node.js 扫描器，并在两者都可用的
  测试环境中检查共享 Schema 和规范化后的语义 parity。
- Node-only、Python-only 和两者均无属于隔离运行时前向测试矩阵；只有保存实际环境与
  执行证据后，才能把对应路径记为已验收。
- fixture 覆盖空白、部分、冲突、成熟、Monorepo、大仓库、Unicode/空格路径、Git
  子目录范围、vendored 目录、权限错误、截断、畸形配置、循环链接和仓库外符号链接。
- 扫描器不执行项目代码；Git fixture 证明仓库配置的 fsmonitor 与 clean/process filter
  不会运行，继承的仓库选择环境变量不能把身份查询重定向到范围外目标。工作树内容状态
  保持 `unverified`；Git 缺失与损坏配置会得到身份 `unverified`，而不是“非仓库”。严格
  JSON、Taskfile、精确文件上限等边界通过双运行时回归测试。

### 10.2 仓库行为

- 空白、部分、混合和成熟仓库分别得到最小、有证据的结果。
- 用户要求只审计时目标零修改且默认零项目命令执行；用户要求 agentize 时不要求额外
  选择内部模式。
- 通用 Agent 行为不会被机械写入目标仓库。
- 新工具、测试、E2E、Hook 和 CI 只在有证据、与请求相关且收益明确时出现；文件或
  Framework 存在不自动把相应能力标记为 `READY`。
- Web/UI、后端、CLI、库和纯文档仓库得到与自身验证面相称的结果。
- 未知业务规则不会依据单一当前实现生成规范或测试。
- 工作定义来自现有权威系统；Goal、Success Criteria 或 Acceptance Criteria 关键缺失时，
  Agentize 生成精确问题而不是替人确认业务含义。
- 非琐碎任务在 Execute 前具有可观测的 Plan 与 Human Plan Review 路径；Human Feedback
  会触发重新 Explore/Re-plan。显然、低风险、可逆任务可以走定义明确的 fast path。
- 本地实现循环默认运行 Fast Verification；Full E2E 属于 MR/PR Full CI，不在每次编辑后
  重跑，除非项目已有廉价且聚焦的子集并明确把它归入快速检查。
- E2E 与真实 Browser Business Flow Validation 分开声明和取证；Browser Controller、
  安全启动路径、测试身份/数据、认证、环境和当前宿主范围都有证据时才标记 `READY`。
  无法安全运行时不会安装工具、使用生产凭据或伪造浏览器验证，而是记录
  `NOT EXECUTED`、影响、人工 Fallback 和 Setup Guide。
- Agent Verification 与 Human Validation 在产物和交接中可区分；绿色检查不会被报告
  为产品验收。
- 使用 reviewed branches 的项目在 Fast Verification 与适用的 Targeted Browser
  Verification 后进入 MR/PR；实现 Agent 自审、独立 AI Review、Full CI、Human Technical
  Review 与 Human Validation 保留不同 provenance。Full E2E 只在其命令、环境、Runner、
  数据与认证路径均有证据时成为真实 Gate，Review/CI/验收失败都会返回修改与再验证。
- 提示指导、工具过滤、审批、Sandbox、仓库检查和外部治理不会被压成一个
  “已强制执行”状态；失效或未加载的 Provider 配置不能成为安全证据。
- 只在新会话或显式 Reload 时加载的指令变更，会在交接中保留刷新要求。
- 高风险变化保留有权的人类决策点，低风险可逆变化不被强制套用同等审批仪式。
- 部署服务只在有真实路径时获得交付、回滚和观察指导；不适用的仓库不会得到虚构的
  生产 Harness。
- Continuous Knowledge Capture 是主要路径：开发过程中确认的 Durable、Non-obvious、
  Reusable 知识与必要的可执行约束进入当前分支/MR/PR；未确认推断继续标记候选而不是
  成为永久政策。
- Post-Merge Knowledge Audit 只审计 AI/Human Review、Full CI、Human Validation 和最终
  返工中遗漏的晚期知识，不重新总结整个变更；没有合格遗漏时零修改。
- Candidate Knowledge 标记 Observed/Inferred/Unknown；自动化不直接写默认分支，经独立
  Knowledge MR/PR 或等价人工评审后才固化为最小文档或可执行约束。
- GitHub/GitLab/Webhook 自动 Post-Merge Audit 只有在真实平台、合并事件、上下文收集、
  Headless Agent Runner、项目已选择的模型接入、凭据、权限、成本、数据边界、失败行为和
  Knowledge MR/PR 路径都已验证时才标记 `READY`；仓库侧已安装但仍需外部配置时标记
  `SETUP REQUIRED`，没有可行实现路径时标记 `NOT AVAILABLE`。人工检查路径单独定级，
  不能让自动能力变成 Ready。
- 外部操作在 dispatch 后丢失结果时不会被自动当作失败重试；状态检查、幂等性和人类
  确认按项目真实能力决定。
- 多 Agent 或 Worktree 只在可分离任务、可靠验证和共享资源边界有证据时出现。
- 非审计运行留下 Harness Capability Report，逐项区分理想流程、当前 Evidence、Operational
  Status、Setup Guide/Fallback 与单次任务的 `PASSED`、`FAILED`、`NOT EXECUTED` 或
  `NOT APPLICABLE`；缺失、冲突或未验证的请求关键能力不会被描述成 all gates passed 或
  完全 agent-ready。
- 二次运行在证据不变时产生零实质 diff。
- 脏工作区无法安全确认时明确报告 `unverified`；已知危险命令、部分写入和验证失败被
  准确报告。
- 卸载 Agentize 后，fixture 仓库仍能被普通 Agent 理解、修改和验证。

### 10.3 跨宿主

- 对每个公开支持的宿主运行相同的代表性请求和隔离 fixture。
- 比较能力结果和目标产物，不要求宿主 UI、调用语法或交接措辞一致。
- 某宿主缺少写入或进程能力时，准确降级并记录限制，不伪造完整支持。

`tests/behavior-cases.md` 是跨模型、跨宿主的前向测试协议，不因文件存在就视为通过。
行为验收必须保存或引用目标宿主、模型/版本、隔离 fixture、工具/命令轨迹、前后状态、
实际产物和交接结果；评价行为而不是固定措辞或固定文件列表。扫描器单元测试不能替代
这些证据，前向测试也不能替代确定性脚本回归。

当前只保存了一条修订后 Codex audit-only 前向记录。它能证明该快照在该环境中遵守静态
审计边界，不能证明其他行为案例、运行时矩阵、宿主或模型版本已经通过。

## 11. 实施顺序

1. 保持 `SKILL.md` 厂商中立，并固定单一自适应协调流程。
2. 固定目标仓库的 Planning、Fast Verification、Targeted Browser Verification、MR/PR
   AI Review + Full CI、Human Validation、Continuous Knowledge Capture 和 Post-Merge
   Knowledge Audit，同时保留 fast path 与不可自动化的人类边界。
3. 固定 Ideal Workflow、Evidence、Operational Status、Setup Guide/Fallback 与单次执行
   Outcome 的分层契约，并生成 Harness Capability Report。
4. 固定自适应产物选择、Observed/Inferred/Unknown 知识协议、Knowledge MR/PR 与
   Documentation-to-Executable-Constraints 路由。
5. 建立四类仓库、计划返工、概念错误、快速/完整验证、能力缺失、Review/CI、风险、持续
   知识捕获和合并后兜底审计的隔离前向测试。
6. 维护 Python 与 Node.js 扫描器的共享 Schema、fixture、边界和语义 parity。
7. 按实际需求验证宿主和 GitHub/GitLab 等平台兼容性；不预建空适配器或选择模型厂商。
8. 只有出现真实分发需求时才生成和测试 Plugin 或宿主包。

README 只声明已经交付并验证的能力。

## 12. 完整验收

以下是发布门槛，不是当前状态声明。只有自动化检查与适用宿主的隔离前向测试都有可
复核证据，并同时满足以下条件，才可声明完整 Agentize：

1. 核心 `SKILL.md`、references 和扫描器不依赖任何模型厂商或宿主命令语法。
2. 用户只需描述想把项目变得 agent-ready，不需要学习内部模式。
3. 明确的只读请求不修改目标；普通协调请求产生最小必要修改或可信零修改结论。
4. Node-only 与 Python-only 环境能生成 Schema 语义等价的确定性清点。
5. 无两种运行时时可以安全降级并准确标记 `unverified`，不强制安装运行时。
6. 空白、部分、冲突和成熟仓库分别得到适配其现状的最小结果。
7. Agentize 自身协调流程与目标仓库长期研发闭环被明确区分。
8. 理想流程、仓库 Evidence、Operational Status、人类 Setup 和当前任务 Outcome 明确分层；
   每个适用的长期研发环节和返工转移都有可工作路径、人类决策点或精确 Capability Gap。
9. 目标仓库拥有一个简洁可发现的长期工作流入口，但只获得项目特有上下文、命令、
   责任和路由，不被写入通用 Agent 教程、空文档树或固定流程脚手架。
10. Agent Verification 与 Human Validation 可区分，Agent 不替人确认意图、重大风险
    或产品验收，也不把绿色检查描述成业务正确性的证明。
11. 非琐碎任务支持 Plan ↔ Human Plan Review，验证失败支持 Execute ↔ Fast Verification
    与适用的 Targeted Browser Verification；fast path 只覆盖明确、可逆、低风险且有现成
    验证的变更。
12. Fast Verification 不默认包含全量 E2E；Full E2E 位于 MR/PR Full CI。E2E 与 Browser
    Business Flow Verification 不被混为同一证据；MR/PR 项目能区分实现 Agent、自审、
    独立 AI Review、Full CI、Human Technical Review 与 Human Validation。
13. 新工具和测试有明确证据与收益，不固化未经确认的业务行为；确认过的重复反馈能
    落到最小可靠的长期所有者。
14. Continuous Knowledge Capture 是主要知识路径：开发中确认的 Durable、Non-obvious、
    Reusable 规则进入当前 MR/PR 的最小长期所有者；Observed、Inferred、Unknown 不被混淆。
15. Post-Merge Knowledge Audit 只是晚期遗漏的兜底，不重新总结全部改动、不直接写默认
    分支；遗漏知识通过独立 Knowledge MR/PR 或等价人工评审确认。
16. GitHub/GitLab/Webhook 自动 Audit 只在平台、合并事件、上下文、Runner、项目已选择的
    模型接入、凭据、权限、成本、数据边界、失败行为和 Knowledge MR/PR 路径已验证时标记
    `READY`；否则准确标记 `SETUP REQUIRED`、`NOT AVAILABLE` 或 `UNVERIFIED`，并保留
    可工作的人工路径而不伪造自动化。
17. 非审计运行留下可发现的 Harness Capability Report。每个适用能力都有 Scope、Status、
    Evidence、Missing Setup、Guide、Fallback、Consequence 和 Re-evaluation Trigger；文件、
    YAML、依赖或说明文字的存在不能单独证明 `READY`。
18. 单次检查分别记录 `PASSED`、`FAILED`、`NOT EXECUTED` 或 `NOT APPLICABLE`；任何未执行
    的必需 Gate 都包含原因、影响和 Fallback，不能被静默跳过或汇总成 all gates passed。
19. 交付、观察、回滚、浏览器/E2E 和并行 Agent 只在项目与任务确实适用时出现。
20. 高风险路径保留项目真实的人类责任与授权边界，低风险改动不承担无关仪式。
21. 正确内容、用户改动和必要 provider 表面被保留。
22. 所有文件、命令和外部操作遵守第 8 节安全边界。
23. 完成后目标仓库不包含 Agentize 运行时依赖或自动触发器。
24. 二次运行幂等，卸载后目标仓库仍可独立使用。
25. 每项宿主支持声明都有真实行为证据，但核心不要求所有宿主使用相同入口。
26. README、SKILL、references、可选厂商元数据和行为案例没有能力声明冲突。
27. 单元测试、具有实际运行记录的行为前向测试、运行时 parity、Skill 校验和
    `git diff --check` 全部通过；行为案例清单本身不算运行记录。
28. 重要宿主约束能说明实际消费者、执行层、范围、刷新或失败行为和验证状态；提示、
    配置文件、审批、Sandbox、CI 与 Human Validation 不被错误等同。
29. 存在外部副作用的适用流程能区分失败与未知结果，不会在缺少状态证据时盲目重试。
30. 本次协调可以带着诚实缺口结束，但请求关键能力仍未解决时不会宣称目标仓库已经
    完全 agent-ready。
