# Agentize Skill

[English](README.md) | [简体中文](README.zh-CN.md)

**Make your codebase agent-ready.**

Agentize Skill is a vendor-neutral coding-agent Skill that bootstraps an existing repository for reliable, human-in-the-loop AI development. It inspects the project, repairs or adds the smallest useful repository-owned context and workflow, reports capabilities that still need setup, verifies its changes, and exits.

> **Agentize Skill should leave behind the system, not become the system.**

The result lives in the target repository. Future Codex, Claude Code, Gemini CLI, Kimi CLI, or other coding-agent sessions should work from the instructions, docs, checks, CI, tools, and decision paths left there; they should not need Agentize Skill as a runtime dependency.

## Quick start

Send this prompt to a coding agent with Skill installation support:

```text
Use this host's Skill installer (in Codex, use $skill-installer) to install the repository-root Agent Skill from:
https://github.com/woai3c/agentize-skill

Use agentize-skill as the canonical Skill name and installation-directory name. If the installer requires a path inside the repository, use . and explicitly name the destination agentize-skill. Install it at user scope so it is available in all my repositories. If this host has no installer but supports Agent Skills, use its documented manual installation mechanism and copy the complete repository root into a user-scoped directory named agentize-skill. Verify that the installed SKILL.md declares name: agentize-skill, then report the exact installed path and source revision. If this host cannot load Agent Skills, say that Agentize Skill was not installed and stop; do not substitute another Skill or tool. Do not run the Skill yet.
```

Then open the repository you want to prepare and ask:

```text
Use Agentize Skill ($agentize-skill where explicit Skill selectors are supported) to bootstrap this existing repository as a self-contained, human-in-the-loop AI development harness. Preserve its current tools and conventions, make the smallest evidence-backed changes, expose unsupported capabilities and human setup honestly, verify the result, and finish with a scoped Harness Capability Report and separate task outcomes.
```

Installation is complete only when the Skill exists in a discovery path and its `SKILL.md` has been verified; an unrelated analysis report is not installation evidence. If the newly installed Agentize Skill is not visible, refresh the host's Skill list or start a new agent session. See [Install and use](#install-and-use) for repository-only installation, host-specific paths, read-only audits, and focused repairs.

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

Agentize Skill keeps the root Agent instruction file concise and navigational. It reuses maintained knowledge owners first; when none exists and evidence-backed content warrants a new owner, it uses focused files under `docs/product/`, `docs/architecture/`, `docs/development/`, `docs/verification/`, or `docs/operations/`. These are fallback locations, not an empty tree generated in every repository. Semantic knowledge remains distinct from any Test, Lint, Type Rule, Architecture Check, script, or CI Gate that enforces its deterministic portion. An existing `ARCHITECTURE.md` may be preserved, but Agentize Skill does not create it by default.

An explicit `audit only`, `report only`, or `do not modify` request is static and read-only by default. Agentize Skill may inspect command definitions but does not run project-defined tests, builds, package scripts, linters, or runtime flows unless the user separately requests a named dynamic check.

## Workflow it leaves behind

```text
Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> Local Fast Verification -> Targeted Runtime Verification <-> Human Local Acceptance -> Create / Mark MR/PR Ready for Review <-> AI Review + MR/PR CI -> Merge
```

Continuous Knowledge Capture spans active development. Full E2E follows the repository's explicit cost- and risk-aware policy and may run per MR/PR, at test or staging promotion, on a schedule, before release, or in a documented combination. Shipping and production observation are conditional on the kind of project. Automatic Post-Merge Knowledge Audit is an optional configured backstop for durable knowledge missed late in the lifecycle, not a minimum daily step.

This is the ideal workflow, not a claim that every repository already supports every stage. Agentize Skill keeps the workflow contract, repository evidence, capability readiness, human setup, and current execution results separate. The detailed responsibility and return-loop rules live in [`references/delivery-workflow.md`](references/delivery-workflow.md).

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

Agentize Skill cannot invent product intent, approve its own plan or acceptance, choose risk tolerance, provide unavailable credentials or infrastructure, prove external branch protection, or create an independent AI reviewer or post-merge agent without a real runner and project-selected model integration. When a required capability cannot be established safely, the correct output is an explicit gap, setup path, and human fallback rather than pretend automation.

## Install and use

### Installation details

The repository name, `SKILL.md` machine name, canonical installation-directory name, and explicit selector are all `agentize-skill`; the user-facing display name is `Agentize Skill`. The quick-start prompt requests a reusable user-scoped installation. To keep it only in the current repository, say so explicitly. An installation-capable agent should follow the active host's documented discovery mechanism, copy the complete repository-root Skill, verify discovery and the installed frontmatter, and report the exact path and source revision. A bare GitHub URL identifies the source but is not a complete helper invocation when that installer also requires an in-repository path; for this repository the path is `.` and the explicit destination name is `agentize-skill`. A host without Agent Skill support cannot install this package as a Skill and must report that limitation instead of running an unrelated tool.

After installation, select `Agentize Skill` in the host's Skill picker or invoke `$agentize-skill` where supported. You do not need to run the bundled scanner yourself.

### Other ways to use it

Read-only audit:

```text
Use Agentize Skill ($agentize-skill where supported) to audit this repository's AI development harness. Do not modify files or run project-defined commands. Report evidence, conflicts, gaps, unknowns, setup needs, and fallbacks.
```

Focused repair:

```text
Use Agentize Skill ($agentize-skill where supported) to reconcile this repository's agent instructions and real verification paths. Keep unrelated files unchanged.
```

Normally one successful bootstrap is enough. Future feature and bug work should follow the harness left in the repository. Run Agentize Skill again only when you intentionally want to audit or repair that harness after the project or tooling changes.

### Manual installation scope

The open [Agent Skills specification](https://agentskills.io/specification) standardizes the Skill directory contents, not a universal installation path. Follow the active host's documentation.

For example, [Codex discovers Skills from several scopes](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills). A reusable user-scoped installation normally uses:

```text
~/.agents/skills/agentize-skill/
```

A repository-scoped installation uses:

```text
<repository>/.agents/skills/agentize-skill/
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

Agentize Skill tries the Node.js scanner first, then Python when the first implementation is unavailable, incompatible, or fails to return a valid report. If neither works, it uses the host's existing read-only tools, discloses the scanner failure, and marks unavailable deterministic facts `unverified`. It never installs or upgrades a runtime merely to scan.

## Repository layout

- `SKILL.md` contains activation, safety, coordination, and handoff rules.
- `references/assessment.md` owns evidence and capability classification.
- `references/delivery-workflow.md` owns the durable development-stage and return-loop contract.
- `references/artifacts.md` owns adaptive repository output selection and artifact contents.
- `references/compatibility.md` owns multi-host and provider-specific reconciliation.
- `scripts/scan_repo.py` and `scripts/scan_repo.cjs` implement the same dependency-free scanner contract.
- `tests/test_scanners.py` contains deterministic scanner safety, boundary, and cross-runtime parity regressions.
- `tests/test_package_identity.py` prevents the repository name, Skill name, selector, and installation path from drifting apart again.
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
