# Agentize

[English](README.md) | [简体中文](README.zh-CN.md)

Agentize is a one-time AI development harness bootstrap. It turns an existing codebase into a repository where coding agents can find the right context, plan before consequential changes, implement and verify in a loop, pass through review and human validation, capture confirmed knowledge during the work, and audit late lessons after merge when that automation is actually configured.

```text
repository -> inspect -> assess -> install or repair -> verify -> self-contained AI development harness
```

It adapts to what the project already has instead of installing a fixed scaffold. The useful result lives in the target repository; Agentize exits after bootstrap and is not a runtime layer, generated-file manager, Hook, or CI dependency that later sessions must keep installed. In short: **Agentize should leave behind the system, not become the system.**

## Model and host neutrality

The core is an Agent Skills-format `SKILL.md` plus optional scripts and references. It does not depend on OpenAI, Anthropic, Google, a particular model, or one invocation syntax.

Each agent host decides how Skills are discovered or selected and how file, shell, sandbox, and approval capabilities work. Thin host-specific metadata such as `agents/openai.yaml` can improve one host's UI, but it is optional and does not change the canonical workflow.

Agentize preserves and reconciles the instruction surfaces the target project actually uses, including `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, nested rules, and repository-local Skills. It does not create provider files speculatively.

## What it does

Agentize follows one adaptive workflow:

1. inspect the repository and current worktree;
2. compare the ideal workflow with capabilities proven by direct evidence;
3. install or repair the smallest safe repository-owned context, workflow, verification, review, and learning paths;
4. create actionable setup guidance for capabilities that still need human-owned infrastructure, credentials, permissions, accounts, or platform settings;
5. verify paths, commands, checks, and the complete diff, then hand off a scoped capability report, task results, unknowns, and optional next investments.

Users do not need to choose an internal mode. A request to make a project agent-ready runs the adaptive bootstrap and reports which ideal stages it could actually establish. A request that explicitly says “audit only,” “report only,” or “do not modify” remains a static, read-only assessment by default: project-defined tests, builds, package scripts, linters, and browser flows are not run unless the user separately asks for a named dynamic check.

Agentize adapts to the starting point:

| Starting point | Behavior |
| --- | --- |
| No effective workflow | Creates the smallest evidence-backed instruction, workflow, validation, and learning spine, with explicit capability gaps. |
| Partial workflow | Preserves useful material and fills consequential gaps. |
| Correct and incorrect material | Resolves actual behavior with direct evidence and records unresolved intent. |
| Mature workflow | Makes a narrow repair or reports that no material change is needed. |

After a successful non-audit bootstrap, future agents can discover a concise repository entrypoint, the ideal development path, a Harness Capability Report showing what is really available, project-specific verification and human decision points, the route for continuous knowledge capture, and any configured post-merge fallback. Those capabilities may live in existing files and external review systems; Agentize does not require particular filenames or a sample `docs/` tree.

Depending on evidence, a run may improve repository instructions, architecture or domain context, work-definition and Plan Review guidance, verification commands, focused scripts, tests, Lint, type checks, E2E, browser business-flow validation, MR/PR templates, independent AI review integration, CI, setup guides, delivery or observation runbooks, continuous knowledge capture, post-merge knowledge audit, decision records, or knowledge gaps. None is added unconditionally. Existing tools are preferred, current behavior is not assumed to be intended behavior, and a concise workflow contract is routed to project-owned detail instead of copying a generic Agent tutorial into every file.

## The workflow it prepares

Agentize's own reconciliation steps above are not the future development workflow. It records this ideal repository-side workflow and prepares the parts the repository can actually support:

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Fast Verification -> Targeted Browser Verification -> MR/PR <-> AI Review + Full CI -> Human Validate -> Merge -> Post-Merge Knowledge Audit -> Improve Harness
```

Continuous Knowledge Capture spans Specify through Merge. Shipping and production observation are conditional paths after merge for repositories that operate a deployable service.

The line above is an ideal workflow, not a claim that every stage is installed or ran. Agentize keeps the desired process, repository evidence, operational readiness, required human setup, and this task's execution results separate. The workflow remains deliberately human-in-the-loop:

- non-trivial work uses a Plan and Human Plan Review loop before execution, while obvious, reversible, low-risk work may use a bounded fast path;
- agents can structure requests, explore, propose plans, implement, debug, run checks, report evidence, and propose durable improvements;
- humans retain material business intent, acceptance, risk tolerance, and authorization for consequential or irreversible actions;
- tests and CI prove only what they check, so Agent verification and Human validation remain separate;
- the local implementation loop uses Fast Verification: relevant Unit and Integration tests, typecheck, Lint, and a necessary build, rather than the full E2E suite after every edit;
- Targeted AI Browser Verification exercises only the affected Web/UI acceptance flow and runs only when the active Agent host has a browser controller plus a safe app start, test identity/data, authentication, and environment; its evidence identifies the tested change and environment and uses precise state-based acceptance predicates rather than fixed delays or ambiguous matches;
- reviewed-branch projects can run independent AI review and Full CI after Fast Verification, with full E2E and other gates only when their commands, runner, environment, data, and permissions are configured; a green result must account for every applicable required gate, including cancelled, missing, or unexpectedly skipped results;
- existing policy may pre-authorize low-risk transitions, while consequential business, security, data, money, migration, or production decisions keep an appropriate human owner;
- unavailable human-owned facts become precise questions or blockers, not invented rules;
- Continuous Knowledge Capture is the primary learning path: confirmed durable, non-obvious, reusable knowledge and suitable executable constraints join the current branch or MR/PR, while inferred or unknown claims remain visibly unconfirmed; comments, resolved threads, “fixed” claims, edits, and merge are candidate signals rather than proof of adoption;
- Post-Merge Knowledge Audit is only a fallback for late review, CI, validation, or rework lessons missed during continuous capture; automatic execution needs a real merge trigger, context collector, headless Agent runner, project-selected model integration, credentials, permissions, and a human-reviewed Knowledge MR/PR path;
- MR/PR, independent Reviewer Agents, hosted learning automation, shipping, production observation, and parallel agents appear only where the project has a real platform, safe path, permissions, and appropriate ownership.

For each applicable stage, a ready repository has a working path, an explicit human decision point, or an evidence-backed gap with a way to resolve it. A workflow file, dependency, framework, instruction, or detected tool is evidence to investigate, not proof that a capability is ready. When prerequisites are absent, Agentize installs safe repository-side pieces where useful and leaves a focused Setup Guide or recommendation rather than choosing a model vendor, inventing credentials, or pretending the stage ran. The normative responsibility and transition rules live in [`references/delivery-workflow.md`](references/delivery-workflow.md).

## Capability status and honest degradation

Every non-audit bootstrap leaves or updates a discoverable Harness Capability Report. Each applicable row identifies its host or platform scope, status, evidence, working portion, missing setup, Setup Guide, fallback, consequence, and re-evaluation trigger.

| Status | Meaning |
| --- | --- |
| `READY` | The complete path is configured and verified for the named scope. |
| `PARTIAL` | A useful bounded subset works, but the missing portion is explicit. |
| `SETUP REQUIRED` | Repository-side work is present, but a named human action, account, secret, permission, environment, or external setting remains. |
| `NOT AVAILABLE` | No safe implementation path currently exists; the report gives a recommendation or fallback. |
| `UNVERIFIED` | Evidence is insufficient or safe verification could not be completed. |
| `NOT APPLICABLE` | The capability does not apply to this repository or scope. |

Capability status is not a task result. A particular check is reported separately as `PASSED`, `FAILED`, `NOT EXECUTED`, or `NOT APPLICABLE`. If Browser Verification, E2E, AI Review, CI, observability, or post-merge automation did not run, the handoff states why, what confidence is lost, and which human fallback applies; it cannot silently say “skipped” and then claim all gates passed.

## Objective limits

- Agentize cannot infer and approve missing product intent, business meaning, risk tolerance, or final acceptance on a human's behalf.
- It cannot guarantee that every coding-agent product reads the same instruction files; provider adapters remain thin and are added only for hosts the repository actually uses and verifies.
- It cannot make Browser Verification or full E2E available without the required controller or framework, safe environment, application start, test accounts/data, authentication, runner, and permissions.
- It cannot create an independent AI reviewer or automatic post-merge knowledge auditor without a real Agent runner, project-selected model integration, credentials, permissions, context access, and platform trigger.
- It cannot prove external branch protection, human availability, production safety, or semantic correctness merely from repository files and green tests.
- When one of these is required but unavailable, the correct result is a human decision point or an explicit gap, not pretend automation.

## Current status

The repository currently includes:

- the vendor-neutral Agentize Skill;
- evidence, artifact, human-agent delivery, and multi-agent compatibility references;
- dependency-free Python and Node.js read-only scanners with shared semantic parity tests;
- scanner unit tests plus forward-test specifications for runtime fallback, effective enforcement, Plan Review and fast paths, capability status, Fast versus Full Verification, MR/PR and Human Validation loops, required-gate accounting, browser provenance, knowledge adoption, recovery, and post-merge audit boundaries;
- a recorded Codex audit-only forward run that provides evidence for that case and snapshot, not every host, model, or behavior case;
- optional OpenAI UI metadata that is not required by the core.

Public support for a particular Agent host still requires representative behavior evidence for that host's discovery, context refresh, tools, sandbox, approval, Hook, session, and delegation semantics. No installable Plugin artifact is currently shipped. The behavior-case document is a qualification protocol, not evidence that every host/model combination has passed it.

## Install and invoke

### Ask your AI agent to install it (recommended)

The simplest setup is to give an installation-capable coding agent this repository URL:

```text
https://github.com/woai3c/agentize
```

Suggested prompt:

```text
Install this Agent Skill for me and make it available in all my repositories:
https://github.com/woai3c/agentize
```

To keep it only in the current repository, ask for that explicitly. An installation-capable agent should use the current host's documented discovery mechanism, preserve the complete Skill directory, verify discovery, and report the exact path. It needs network and filesystem access, and some hosts may require a new session before a newly installed Skill appears. Inspect the source and revision before installing any third-party Skill.

### Use it after installation

1. Open the existing repository you want to prepare in your coding agent. If Agentize was installed after the current session started and is not visible, start a new session.
2. Select Agentize from the host's Skill picker when available, or name Agentize directly in your request. You do not need to run the bundled scanner yourself.
3. Ask for the outcome you want. A normal Agentize request may modify repository files and run safe relevant checks allowed by the host; explicitly say `audit only` or `do not modify` for a static read-only assessment.
4. Review the final diff, verification evidence, unknowns, and questions reserved for human judgment. Answer any blocking product or risk questions and continue the same session.

Recommended one-time bootstrap:

```text
Use Agentize once to bootstrap this existing repository as a self-contained AI development harness. Preserve its tools and conventions. Record the ideal workflow, install the smallest evidence-backed planning, Fast Verification, targeted browser, MR/PR review and Full CI, Human Validation, continuous knowledge capture, and post-merge audit paths that are actually supportable. Do not choose a model vendor or infer readiness from files alone. Create focused Setup Guides for human-owned prerequisites, verify what can be verified safely, and finish with a scoped Harness Capability Report plus separate task results, diff, unknowns, fallbacks, and human decisions still required.
```

Read-only audit:

```text
Use Agentize to audit this repository's agent workflow. Do not modify files or run project-defined commands. Report the evidence, gaps, conflicts, and unknowns.
```

Focused repair:

```text
Use Agentize to reconcile this repository's agent instructions and real verification commands. Keep unrelated files unchanged.
```

Normally, one successful bootstrap is enough. Future feature and bug work should follow the instructions, context, checks, review gates, and learning path left in the target repository without invoking Agentize. Run Agentize again only when you intentionally want to audit or repair the harness after the repository or tooling changes. A user-scoped installation can still be reused to bootstrap other projects; a repository-scoped installation remains limited to that repository tree. Repeated runs are convergent: a sound, unchanged repository should produce no material diff.

### Manual installation and scope

The open [Agent Skills specification](https://agentskills.io/specification) standardizes the contents of a Skill directory, not where hosts discover it. Installation locations are host conventions.

For example, [Codex currently discovers local Skills](https://developers.openai.com/codex/skills) from several locations. A reusable user-scoped Agentize installation normally belongs under:

```text
~/.agents/skills/agentize/
```

To pin Agentize to one repository, use:

```text
<repository>/.agents/skills/agentize/
```

Codex scans repository `.agents/skills` directories from the current working directory up to the repository root. A user-scoped Skill is available across repositories; a repository-scoped Skill applies only in that repository tree. Other hosts may use different paths, so follow the active host's documentation rather than assuming the Codex layout is universal.

## Scanner

Ordinary use does not require running a scanner manually; Agentize runs an available implementation as part of its workflow. The commands below are for manual inspection and development. Both shipped scanners use only their runtime standard library and do not modify the target:

```text
node scripts/scan_repo.cjs --root /path/to/repository --format markdown
node scripts/scan_repo.cjs --root /path/to/repository --format json
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

It inventories instruction surfaces, Skills, host configuration, manifests, declared commands, documentation, tests, quality configuration, and CI. Verification commands in supported instruction-file code fences are recognized conservatively but never executed. Diagnostic hints are investigation leads, not automatic quality judgments, evidence that a host policy is active, or permission to execute project commands. Collected text receives best-effort redaction for common credential syntax, but reports remain sensitive local evidence and must be inspected before sharing. Git metadata calls disable repository fsmonitor execution, strip inherited `GIT_*` repository selectors, and query only repository identity and branch. They deliberately do not run status or diff because Git may execute repository-configured content filters; Schema v4 therefore reports worktree dirtiness as `unverified` and its count as `null`, never silently “clean.” Repository identity is also tri-state: `true` means verified, `false` means no `.git` marker was found along the target path, and `null` means a marker exists but Git identity could not be verified. Agentize prefers the Node.js implementation when available, falls back to Python, and otherwise reproduces a bounded inventory with the host's existing read-only tools while marking unavailable deterministic fields `unverified`. It never installs a runtime merely to run a scan.

## Development

Run the local tests and inspect the Skill against itself:

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
git diff --check
```

[`DESIGN.md`](DESIGN.md) defines the product boundary and acceptance criteria. Observable expectations for repository states, runtime fallback, safety, and cross-host behavior live in [`tests/behavior-cases.md`](tests/behavior-cases.md).

## License

MIT
