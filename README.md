# Agentize Skill

[English](README.md) | [简体中文](README.zh-CN.md)

**Agentize your codebase.**

Agentize is a vendor-neutral coding-agent Skill that bootstraps an existing repository for reliable, human-in-the-loop AI development. It inspects the project, repairs or adds the smallest useful repository-owned context and workflow, reports capabilities that still need setup, verifies its changes, and exits.

> **Agentize should leave behind the system, not become the system.**

The result lives in the target repository. Future Codex, Claude Code, Gemini CLI, Kimi CLI, or other coding-agent sessions should work from the instructions, docs, checks, CI, tools, and decision paths left there; they should not need Agentize as a runtime dependency.

## What it does

A normal bootstrap run:

1. binds the exact target and inventories its existing agent instructions, documentation, manifests, commands, tests, CI, runtime paths, and learning mechanisms without executing project code during discovery;
2. compares direct evidence with the ideal AI-native workflow and distinguishes observed facts, inference, unknowns, operational readiness, and current-task outcomes;
3. repairs existing sources of truth or adds only the smallest missing repository-owned instruction, context, verification, review, acceptance, and knowledge-capture paths;
4. creates focused setup guidance when credentials, permissions, accounts, test data, browser control, runners, external settings, or model integration still require a human;
5. verifies the resulting paths, claims, commands, checks, and diff, then hands off a scoped Harness Capability Report.

It adapts instead of installing a fixed scaffold:

| Starting point | Result |
| --- | --- |
| No effective agent workflow | Establish the smallest useful harness and expose remaining gaps. |
| Partial workflow | Preserve useful material and fill consequential gaps. |
| Conflicting or stale workflow | Reconcile effective behavior from evidence and surface unresolved intent. |
| Mature workflow | Make a narrow repair or produce an evidence-backed no-change result. |

An explicit `audit only`, `report only`, or `do not modify` request is static and read-only by default. Agentize may inspect command definitions but does not run project-defined tests, builds, package scripts, linters, or runtime flows unless the user separately requests a named dynamic check.

## Workflow it leaves behind

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Local Fast Verification -> Targeted Runtime Verification <-> Human Local Acceptance -> Create / Mark MR/PR Ready for Review <-> AI Review + MR/PR CI -> Merge
```

Continuous Knowledge Capture spans active development. Full E2E follows the repository's explicit cost- and risk-aware policy and may run per MR/PR, at test or staging promotion, on a schedule, before release, or in a documented combination. Shipping and production observation are conditional on the kind of project. Automatic Post-Merge Knowledge Audit is an optional configured backstop for durable knowledge missed late in the lifecycle, not a minimum daily step.

This is the ideal workflow, not a claim that every repository already supports every stage. Agentize keeps the workflow contract, repository evidence, capability readiness, human setup, and current execution results separate. The detailed responsibility and return-loop rules live in [`references/delivery-workflow.md`](references/delivery-workflow.md).

Every applicable capability is reported with one operational status:

| Status | Meaning |
| --- | --- |
| `READY` | The complete path is configured and verified for the named scope. |
| `PARTIAL` | A useful bounded subset works and the missing portion is explicit. |
| `SETUP REQUIRED` | A concrete path is selected and repository-side work is present, but a named human action or external prerequisite remains. |
| `NOT CONFIGURED` | The capability applies, but no usable path is currently configured or selected. |
| `UNVERIFIED` | Evidence is insufficient or safe verification could not be completed. |
| `NOT APPLICABLE` | The capability does not apply to this repository or scope. |

Current-task checks use `PASSED`, `FAILED`, `NOT EXECUTED`, or `NOT APPLICABLE` separately. A file, dependency, workflow definition, or green test is not by itself proof that a capability is ready or that the implementation matches human intent.

Agentize cannot invent product intent, approve its own plan or acceptance, choose risk tolerance, provide unavailable credentials or infrastructure, prove external branch protection, or create an independent AI reviewer or post-merge agent without a real runner and project-selected model integration. When a required capability cannot be established safely, the correct output is an explicit gap, setup path, and human fallback rather than pretend automation.

## Install and use

### Ask an installation-capable agent to install it (recommended)

Send the agent this repository URL:

```text
https://github.com/woai3c/agentize-skill
```

Suggested prompt:

```text
Install this Agent Skill for me and make it available in all my repositories:
https://github.com/woai3c/agentize-skill
```

The distribution repository is named `agentize-skill`; the Skill name and installation directory remain `agentize`. To keep it only in the current repository, say so explicitly. An installation-capable agent should follow the active host's documented discovery mechanism, copy the complete Skill directory, verify discovery, and report the exact installed path. Some hosts require a new session before a newly installed Skill appears. Inspect the source and revision before installing any third-party Skill.

### Invoke it after installation

Open the repository you want to prepare, select Agentize in the host's Skill picker when available, or name Agentize directly in your request. You do not need to run the bundled scanner yourself.

One-time bootstrap:

```text
Use Agentize to bootstrap this existing repository as a self-contained, human-in-the-loop AI development harness. Preserve its current tools and conventions, make the smallest evidence-backed changes, expose unsupported capabilities and human setup honestly, verify the result, and finish with a scoped Harness Capability Report and separate task outcomes.
```

Read-only audit:

```text
Use Agentize to audit this repository's AI development harness. Do not modify files or run project-defined commands. Report evidence, conflicts, gaps, unknowns, setup needs, and fallbacks.
```

Focused repair:

```text
Use Agentize to reconcile this repository's agent instructions and real verification paths. Keep unrelated files unchanged.
```

Normally one successful bootstrap is enough. Future feature and bug work should follow the harness left in the repository. Run Agentize again only when you intentionally want to audit or repair that harness after the project or tooling changes.

### Manual installation scope

The open [Agent Skills specification](https://agentskills.io/specification) standardizes the Skill directory contents, not a universal installation path. Follow the active host's documentation.

For example, [Codex discovers Skills from several scopes](https://developers.openai.com/codex/skills). A reusable user-scoped installation normally uses:

```text
~/.agents/skills/agentize/
```

A repository-scoped installation uses:

```text
<repository>/.agents/skills/agentize/
```

The first is available across repositories for that user; the second is limited to the repository tree. Other hosts may use different conventions, so `.agents/skills` is not a universal requirement.

## Scanner

Ordinary users do not need to run the scanner manually. The two implementations use only their runtime standard library, perform a static read-only inventory, and never execute declared project commands:

```text
node scripts/scan_repo.cjs --root /path/to/repository --format markdown
node scripts/scan_repo.cjs --root /path/to/repository --format json
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

Schema v5 bounds the scan by files, directories, depth, and per-file bytes; skips non-regular files and repository-external symlinks; conservatively recognizes verification commands; and redacts common credential syntax on a best-effort basis. Reports remain sensitive local evidence and should be inspected before sharing. Limits can be adjusted with `--max-files`, `--max-directories`, and `--max-depth`; any reached limit is explicit in `scan.limit_reasons` and diagnostics.

Git queries strip inherited `GIT_*` repository selectors and inspect only repository identity and branch. They do not run `status` or `diff`, because content comparison may execute repository-configured filters. Worktree state is therefore `unverified`, never silently clean. Repository identity is tri-state: `true` is verified, `false` means no Git marker was found for the target, and `null` means a marker exists but identity could not be verified.

Agentize tries the Node.js scanner first, then Python when the first implementation is unavailable, incompatible, or fails to return a valid report. If neither works, it uses the host's existing read-only tools, discloses the scanner failure, and marks unavailable deterministic facts `unverified`. It never installs or upgrades a runtime merely to scan.

## Repository layout

- `SKILL.md` contains activation, safety, coordination, and handoff rules.
- `references/assessment.md` owns evidence and capability classification.
- `references/delivery-workflow.md` owns the durable development-stage and return-loop contract.
- `references/artifacts.md` owns adaptive repository output selection and artifact contents.
- `references/compatibility.md` owns multi-host and provider-specific reconciliation.
- `scripts/scan_repo.py` and `scripts/scan_repo.cjs` implement the same dependency-free scanner contract.
- `tests/test_scanners.py` contains deterministic scanner safety, boundary, and cross-runtime parity regressions.
- `agents/openai.yaml` is optional OpenAI UI metadata and is not part of the vendor-neutral core.

## Development

Run the deterministic checks from the repository root:

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
git diff --check
```

Also validate the Skill with an Agent Skills validator available in the current development environment. In a Codex source checkout, use the installed `skill-creator` validator; its absolute path and PyYAML environment are host-specific and must not be committed to portable scripts or CI.

The Python `unittest` suite is a development harness, not an installation dependency. It exercises both scanners when Node.js is available. Scanner behavior has deterministic regression coverage, but this repository does not ship a cross-host agent-behavior evaluation harness or claim that every host has identical discovery, sandbox, approval, Hook, context-refresh, or delegation semantics.

## License

MIT
