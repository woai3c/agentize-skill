---
name: agentize
description: Audit, create, or repair a repository's coding-agent workflow, including repo instructions, durable context, verification commands, and feedback loops. Use when asked to agentize, bootstrap, or make a codebase agent-ready, or to reconcile incomplete, conflicting, or stale AGENTS.md, CLAUDE.md, GEMINI.md, skills, docs, and CI guidance. Do not use for ordinary feature implementation or a one-off code review.
---

# Agentize

Make the target repository easier for coding agents to understand, change, and
verify. Leave durable, human-owned repository artifacts behind. Treat this
skill as an initializer and reconciler, not as a runtime dependency.

## Establish scope

- Use the repository containing the current working directory unless the user
  names another target.
- Read every instruction file that applies to the target before changing it.
- Inspect `git status` and preserve unrelated or in-progress work.
- Treat the user's requested outcome as authority to improve the repository
  workflow, but do not infer permission for unrelated product changes,
  external actions, dependency upgrades, or destructive cleanup.
- Ask only when the target repository cannot be determined, a business rule has
  multiple materially different interpretations, or a proposed change would
  remove intentional behavior without decisive evidence.

## Inventory the repository

Run the bundled read-only scanner from the repository root:

```text
python <skill-directory>/scripts/scan_repo.py --root . --format json
```

If `python` is unavailable, reproduce the scan with available read-only tools.
Do not install a runtime merely to run the scanner.

Read [references/assessment.md](references/assessment.md) after the scan. Use
its evidence hierarchy and capability rubric to classify each area as sound,
weak, missing, conflicting, stale, or unverified.

Then inspect the smallest set of high-signal sources needed to resolve the
classification:

- manifests, task runners, and workspace configuration;
- CI workflows and existing verification scripts;
- entry points, package boundaries, schemas, and representative tests;
- current repository instructions and maintained documentation;
- recent Git history only when it can recover rationale or expose stale paths.

Ignore generated outputs, dependency caches, vendored code, and secrets unless
they are directly relevant. Never copy credentials or sensitive values into
agent-facing documentation.

## Choose the smallest useful target state

Plan a convergent patch, not a fixed scaffold. Correct repositories may need no
changes; partial repositories need additions; conflicting repositories need
reconciliation. Prefer, in order:

1. Repair an existing source of truth.
2. Add a missing high-value section to an existing document.
3. Add a focused document or deterministic check when the information cannot
   stay clear where it is.
4. Add tool-specific compatibility files only for tools the repository uses.

Do not create empty directories, speculative business documentation, generic
best-practice lists, or duplicate command catalogs. Do not add a hook, CI job,
MCP server, plugin, or custom CLI unless its mechanical or distribution value
is demonstrated by the repository and fits the user's scope.

Before editing, read [references/artifacts.md](references/artifacts.md). If the
repository already has multiple agent products, provider-specific instruction
files, skills, hooks, or agent configuration, also read
[references/compatibility.md](references/compatibility.md).

## Reconcile instead of replacing

- Preserve correct, project-specific guidance and the repository's established
  terminology and file organization.
- Correct a claim only when current executable evidence, code, tests, or CI
  disproves it. Record unresolved conflicts as explicit knowledge gaps.
- Keep the root instruction file concise and navigational. Put detailed domain,
  architecture, testing, or release guidance near its owning code or in a
  focused linked document.
- Use nested instruction files only where a subtree genuinely has different
  commands, constraints, or ownership.
- State exact commands with their working directory, purpose, prerequisites,
  and cost when those details affect whether an agent should run them.
- Turn repeated review feedback into the strongest appropriate durable form:
  a test, lint rule, type/schema constraint, script, CI gate, instruction, or
  decision record.
- Mark facts that cannot be established as questions. Never promote guesses to
  repository policy.
- Avoid generated-by banners and opaque managed sections. The resulting files
  belong to the repository and must remain maintainable without this skill.

## Verify the resulting harness

Use evidence proportional to the changes:

1. Re-run the scanner and confirm the new inventory is internally consistent.
2. Check every added path, relative link, and documented command.
3. Run cheap, targeted verification commands that cover changed scripts or
   configuration. Follow existing repository guidance before running expensive
   suites, networked checks, or commands with external side effects.
4. Run the repository's documentation or configuration validators when the
   patch affects their inputs.
5. Inspect the complete diff, run `git diff --check`, and confirm unrelated
   user changes remain untouched.
6. Confirm a fresh agent can discover: the repository's purpose, where to make
   a change, applicable constraints, the fastest relevant verification path,
   and which questions still require human judgment.

Do not claim that a command or behavior was verified when it was only inferred.
A failed verification is evidence to investigate, not a reason to weaken or
delete a valid check.

## Handoff

Report:

- the starting condition and material gaps;
- files created, repaired, retained, or deliberately left alone;
- verification commands actually run and their results;
- unresolved knowledge gaps and who can answer them;
- optional next investments, separated from the completed baseline.

The run is complete when the repository itself carries the useful context and
feedback loop. Future feature work should maintain those artifacts as part of
the change that makes them stale.
