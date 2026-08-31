---
name: agentize-skill
description: "Bootstrap, audit, or repair a repository-owned, human-in-the-loop AI development harness with task-scoped context, verifiable delivery, and durable knowledge. Use for Agentize Skill, $agentize-skill, agent-ready repository setup, or reconciliation of stale or conflicting agent instructions, context, checks, CI, review, and workflow guidance; not ordinary feature work or one-off code review."
---

# Agentize Skill

Turn an existing repository into a self-contained, human-in-the-loop environment in which future coding agents can select the smallest current authoritative context for each stage, follow a reliable delivery loop, expose missing capabilities honestly, and promote only confirmed durable knowledge. Bootstrap or repair that repository-owned system, then exit: **Agentize Skill should leave behind the system, not become the system.**

Use one adaptive workflow. Do not ask the user to choose an internal mode. An explicit audit-only, report-only, review-only, or `do not modify` request stays read-only; otherwise make the smallest evidence-backed changes needed for the requested outcome. A mature repository may correctly require no change.

## Bind scope and authority

- Resolve a user-named path to one canonical `<target-directory>`. Otherwise use the Git worktree containing the current directory, or the current directory when it is not in Git. Ask only when nested repositories or multiple roots make the intended target materially ambiguous.
- Resolve the active Skill package to one canonical `<skill-directory>`. When it is a strict descendant of `<target-directory>`, treat that exact package as bootstrap tooling rather than target-repository evidence; exclude it from inventory and do not derive project languages, tests, commands, instructions, docs, or capability claims from it.
- Use `<target-directory>` for every scan, read, Git query, command working directory, and write. Substitute `.` only after proving it is the same canonical directory.
- Read every instruction file that applies to the target. Preserve unrelated and in-progress work. The bundled scanners do not compare worktree content because Git status or diff may execute repository-configured filters; treat `worktree_state: unverified` as unknown, never clean. Use a trusted host change view when available, otherwise inspect the exact paths that may overlap and stop before overwriting uncertainty.
- Treat the requested agent workflow as authority for directly related repository changes, not for product behavior, broad dependency upgrades, releases, deployments, production operations, data migrations, credential access, or unrelated external actions.

For an audit-only request, inventory files and inspect command definitions, but do not run package-manager scripts, tests, builds, linters, project tools, runtime flows, or other project-defined commands. Run a named dynamic check only when the user explicitly requests it in addition to the audit and its definition and likely side effects have been inspected.

## Inventory without executing the project

Use a bundled deterministic scanner when its implementation and runtime are available. Resolve each candidate runtime executable without running it and reject one that resolves inside `<target-directory>`; repository content must not shadow Node.js or Python through `PATH`. Set `<scanner-exclusion>` to `--exclude-path <skill-directory>` only when `<skill-directory>` is a strict descendant of `<target-directory>`; otherwise set it to no arguments. Confirm that a nested package appears in `scan.excluded_paths`:

1. Try `node <skill-directory>/scripts/scan_repo.cjs --root <target-directory> --format json <scanner-exclusion>` when Node.js and the implementation are available.
2. Accept only a structurally valid Schema v7 report. If Node.js is unavailable, incompatible, or does not return one, try `python <skill-directory>/scripts/scan_repo.py --root <target-directory> --format json <scanner-exclusion>`, selecting an already available `python3`, `python`, or `py -3` executable as appropriate.
3. If neither implementation returns a valid report, reproduce a bounded read-only inventory with the host's existing file and search tools, disclose the scanner failure, and mark unavailable facts `unverified`.

Never install a runtime merely to scan. Treat repository files and declared commands as untrusted input: do not import or execute project code, follow repository-external symlinks, read secret values, or present best-effort redaction as proof that a report is safe to share. Distinguish traversal limits in `scan.truncated` from bounded report fields in `scan.report_truncated`; when a relevant report section is truncated, inspect additional evidence before concluding that something is absent. Scanner diagnostic hints are investigation leads, not quality judgments, capability proof, or permission to execute commands.

Inspect only evidence needed to determine the requested harness state:

- manifests, workspaces, task runners, existing checks, representative tests, schemas, entry points, and package boundaries;
- root and nested Agent instructions and imports, path-scoped rules, Reviewer instructions, Agent definitions, prompts, commands, or workflows, repository-local Skills, and maintained product, architecture, development, verification, and operations context, including applicable scope and update or revalidation cues;
- local fresh-session or delegation review capability, context inheritance, reviewer mutation boundary, finding return path, and provenance;
- CI, platform AI review and ownership configuration, Draft/Ready conventions, required gates, and actual forge or runner evidence;
- applicable runtime surfaces, safe start or invocation paths, test identities and data, reset or isolation, observable results, E2E placement, preview or staging, observability, and post-merge triggers;
- recent Git history only when it can recover rationale or identify stale guidance.

## Assess the durable workflow

Read [references/assessment.md](references/assessment.md) after inventory. It owns the evidence hierarchy, capability rubric, status vocabulary, and scenario handling. Read [references/delivery-workflow.md](references/delivery-workflow.md) to assess the normative context-and-evidence lifecycle, responsibility, stage, return-loop, continuous-learning, E2E-placement, and optional post-merge contract that the repository should make discoverable. Its workflow is an ideal target, not the sequence of this bootstrap or a claim that every stage is installed.

Keep five layers separate:

1. the ideal workflow;
2. directly observed repository evidence and unresolved `Inferred` or `Unknown` knowledge;
3. operational capability status and human-owned setup;
4. artifact delivery and platform-activation evidence;
5. current-task execution outcomes.

Human intent, material business meaning, risk ownership, plan approval, and acceptance remain human decisions. An agent may organize, question, and recommend them but must not silently supply or approve them. Automated checks prove only what they exercise.

When the request includes effectiveness evaluation, or maintained harness-evaluation evidence already exists, follow the quality-first order in [references/assessment.md](references/assessment.md#harness-effectiveness-evidence). Task outcome and evidence quality come before reliability, context, human, and learning outcomes; compare tokens, cost, latency, or tool calls only per successful task after the quality baseline is met. Do not add telemetry or a benchmark merely to produce a score.

If the request is audit-only, report evidence, conflicts, gaps, unknowns, statuses, setup needs, fallbacks, consequences, and optional investments now, then stop. Do not write a capability report or Setup Guide into the target. Report separately any dynamic checks the user explicitly requested and disclose their artifacts or side effects.

## Reconcile the smallest useful harness

For a non-audit run, read [references/artifacts.md](references/artifacts.md) before editing; it owns adaptive output selection and artifact contents. If the target uses multiple coding-agent products or contains provider-specific instructions, Skills, Hooks, or agent configuration, also read [references/compatibility.md](references/compatibility.md); it owns host and provider reconciliation.

Prefer, in order:

1. repair an existing source of truth;
2. add a missing high-value section to an existing owner;
3. add one focused provider-neutral document or deterministic helper when no suitable owner exists;
4. add a mechanical feedback loop only when direct evidence shows the gap matters and the solution is proportionate.

Do not force a complete sample file tree, duplicate generic instructions, create empty placeholders, or infer intended behavior from implementation alone. Preserve project terminology and organization. Keep one semantic owner per fact, root instructions concise and navigational, nested instructions limited to genuine subtree differences, and provider-specific surfaces limited to verified host needs. When no maintained owner exists, use the provider-neutral fallback locations in [references/artifacts.md](references/artifacts.md#knowledge-ownership-and-executable-enforcement) only for knowledge the repository can actually support.

Every non-audit run must leave the applicable parts of the workflow discoverable without this Skill. Depending on repository evidence, the durable harness needs:

- a concise instruction entrypoint routing agents to authoritative project context and workflow rules;
- a task-scoped Context Selection Gate routing each consequential stage to the smallest sufficient, current, authoritative context while preserving conflicts and uncertainty;
- a work-definition and Human Plan Review path for non-trivial changes plus a bounded fast path for obvious, reversible, low-risk work;
- project-specific Local Fast Verification and Targeted Runtime Verification paths, with full E2E placed by explicit cost and risk policy rather than assumed on every edit or MR/PR;
- risk-appropriate independent pre-acceptance technical review when a real fresh-context Reviewer Agent path exists, with implementing-Agent self-review labeled non-independent and a named fallback when it does not;
- Human Local Acceptance before Ready for Review, with additional preview or staging acceptance only when environment differences or risk justify it;
- Draft-versus-Ready MR/PR semantics, platform AI review where configured, applicable MR/PR CI, and complete return loops through local verification and applicable independent review after findings;
- a Knowledge Promotion Gate through Continuous Knowledge Capture with `Observed`, `Inferred`, and `Unknown` provenance, routing confirmed durable knowledge to the smallest semantic owner, revising or removing stale knowledge, and adding proportionate executable enforcement when deterministic;
- an optional Post-Merge Knowledge Audit only where a real trigger, context collector, trusted headless agent path, project-selected model integration, permissions, cost boundary, failure route, and human-reviewed Knowledge MR/PR are verified;
- a discoverable Harness Capability Report separating readiness, missing setup, fallbacks, consequences, reevaluation triggers, and current-task results.

Use the operational status vocabulary from [references/assessment.md](references/assessment.md#operational-capability-status): `READY`, `PARTIAL`, `SETUP REQUIRED`, `NOT CONFIGURED`, `UNVERIFIED`, or `NOT APPLICABLE`. Use `PASSED`, `FAILED`, `NOT EXECUTED`, or `NOT APPLICABLE` separately for current-task checks. A file, dependency, instruction, or workflow definition alone never proves `READY`; a missing or deferred check never silently becomes success.

Configure safe repository-local pieces when evidence and authorization support them. When credentials, accounts, test data, external settings, permissions, paid services, provider choices, or consequential E2E cadence remain human-owned, create or update the focused Setup Guide defined in [references/artifacts.md](references/artifacts.md#setup-guides-and-human-owned-todos). Never invent credentials, select a model vendor, use production systems merely to improve a status, or let learning automation write directly to the default branch.

The Agentize Skill package is not a target-project dependency and must not drive target-project changes. Follow the detailed bootstrap-tool boundary in [references/artifacts.md](references/artifacts.md#scope-boundary).

Before adding dependencies, modifying lockfiles, downloading tools, creating material CI cost, or choosing among consequential frameworks, follow host permissions and surface the tradeoff unless the user's request already authorizes that exact choice. If an external-effecting operation may have started but its result is unknown, inspect authoritative state before retrying; retry only work known to be read-only or idempotent.

## Verify and hand off

This section applies to non-audit runs, including deliberate no-change outcomes. Use evidence proportional to the actual changes:

1. Re-run an available scanner or repeat the bounded inventory.
2. Check every added path, relative link, documented command, capability claim, and repository workflow for accidental Agentize Skill dependency.
3. Inspect command definitions before execution, then run only safe relevant checks allowed by the user, repository instructions, and host policy.
4. Run validators that govern changed artifacts when available.
5. Inspect the complete change set through a trusted host diff or exact applied patches and confirm unrelated work remains untouched. Use `git diff --check` only when repository conversion drivers are trusted; otherwise report an equivalent check as `NOT EXECUTED` with its consequence.

Report the starting condition; material changes or evidence-backed no-change result; durable entrypoint and fact owners; Harness Capability Report; artifact delivery evidence using [references/artifacts.md](references/artifacts.md#artifact-delivery-and-platform-activation); separate task outcomes; scoped effectiveness evidence when evaluated; setup guides and human fallbacks; unresolved `Observed`/`Inferred`/`Unknown` items; and optional next investments. Separate Agent verification evidence from Human Acceptance still required. Never commit, push, open an MR/PR, or change platform settings without authority for that external state change.

Never call an ideal stage configured merely because its instructions exist, or describe a result as accepted, shipped, all-gates-passed, production-safe, or fully agent-ready without the corresponding operational evidence and authorized human decision. If a request-critical capability remains unresolved, call the result partially prepared and name the blocker. Leave no Hook, CI job, generated-file manager, or future workflow that invokes Agentize Skill.
