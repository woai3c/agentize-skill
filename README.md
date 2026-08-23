# Agentize

Agentize turns an existing codebase into a repository where coding agents can
find the right context, make scoped changes, verify their work efficiently, and
hand product judgment and consequential risk decisions to the right humans.

```text
repository -> inspect -> assess -> reconcile -> verify -> human-agent harness
```

It adapts to what the project already has instead of installing a fixed
scaffold. The useful result lives in the target repository; Agentize is not a
runtime layer, generated-file manager, Hook, or CI dependency that later
sessions must keep installed.

## Model and host neutrality

The core is an Agent Skills-format `SKILL.md` plus optional scripts and
references. It does not depend on OpenAI, Anthropic, Google, a particular model,
or one invocation syntax.

Each agent host decides how Skills are discovered or selected and how file,
shell, sandbox, and approval capabilities work. Thin host-specific metadata such
as `agents/openai.yaml` can improve one host's UI, but it is optional and does
not change the canonical workflow.

Agentize preserves and reconciles the instruction surfaces the target project
actually uses, including `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, nested rules, and
repository-local Skills. It does not create provider files speculatively.

## What it does

Agentize follows one adaptive workflow:

1. inspect the repository and current worktree;
2. assess high-value agent workflow capabilities from direct evidence;
3. repair existing sources of truth and fill consequential gaps;
4. verify paths, commands, checks, and the complete diff;
5. hand off changes, evidence, unknowns, and optional next investments.

Users do not need to choose an internal mode. A request to make a project
agent-ready runs the complete workflow. A request that explicitly says “audit
only,” “report only,” or “do not modify” remains a static, read-only assessment
by default: project-defined tests, builds, package scripts, linters, and browser
flows are not run unless the user separately asks for a named dynamic check.

Agentize adapts to the starting point:

| Starting point | Behavior |
| --- | --- |
| No effective workflow | Creates the smallest verified instruction and validation spine. |
| Partial workflow | Preserves useful material and fills consequential gaps. |
| Correct and incorrect material | Resolves actual behavior with direct evidence and records unresolved intent. |
| Mature workflow | Makes a narrow repair or reports that no material change is needed. |

Depending on evidence, a run may improve repository instructions, architecture
or domain context, work-definition and review guidance, verification commands,
focused scripts, tests, Lint, type checks, E2E, CI, delivery or observation
runbooks, decision records, or knowledge gaps. None is added unconditionally.
Existing tools are preferred, current behavior is not assumed to be intended
behavior, and generic Agent habits are not copied into every project.

## The workflow it prepares

Agentize's own reconciliation steps above are not the future development
workflow. It prepares the repository-side harness for the applicable parts of:

```text
Specify -> Explore -> Plan -> Execute -> Agent Verify -> Human Validate
        -> Ship -> Observe -> Learn
```

This is deliberately human-in-the-loop:

- agents can structure requests, explore, propose plans, implement, debug, run
  checks, report evidence, and propose durable improvements;
- humans retain material business intent, acceptance, risk tolerance, and
  authorization for consequential or irreversible actions;
- tests and CI prove only what they check, so Agent verification and Human
  validation remain separate;
- existing policy may pre-authorize low-risk transitions, while consequential
  business, security, data, money, migration, or production decisions keep an
  appropriate human owner;
- unavailable human-owned facts become precise questions or blockers, not
  invented rules;
- shipping, production observation, and parallel agents appear only where the
  project has a real need, safe path, and appropriate ownership.

For each applicable stage, a ready repository has a working path, an explicit
human decision point, or an evidence-backed gap with a way to resolve it. This
does not promise full autonomy or semantic correctness. It makes the automation
boundary visible and maintainable. A request-critical unresolved gap is reported
as partial preparation, not as proof that the repository is fully agent-ready.
The normative responsibility and transition rules live in
[`references/delivery-workflow.md`](references/delivery-workflow.md).

## Current status

The repository currently includes:

- the vendor-neutral Agentize Skill;
- evidence, artifact, human-agent delivery, and multi-agent compatibility
  references;
- dependency-free Python and Node.js read-only scanners with shared semantic
  parity tests;
- scanner unit tests plus forward-test specifications for runtime fallback,
  effective enforcement, Human validation, recovery, and learning boundaries;
- a recorded Codex audit-only forward run that provides evidence for that case
  and snapshot, not every host, model, or behavior case;
- optional OpenAI UI metadata that is not required by the core.

Public support for a particular Agent host still requires representative
behavior evidence for that host's discovery, context refresh, tools, sandbox,
approval, Hook, session, and delegation semantics. No installable Plugin
artifact is currently shipped. The behavior-case document is a qualification
protocol, not evidence that every host/model combination has passed it.

## Install and invoke

Install this folder wherever the chosen agent host discovers Agent Skills. Host
paths and invocation syntax vary, so follow that host's documentation and keep
this directory as the canonical copy.

For example, Codex can discover personal Skills under:

```text
~/.agents/skills/agentize/
```

and repository-scoped Skills under:

```text
<repository>/.agents/skills/agentize/
```

Example requests, using whatever Skill-selection syntax the host supports:

```text
Make this repository agent-ready with the smallest evidence-backed changes.
Agentize this existing project and preserve its current tools and conventions.
Audit the repository's agent workflow, but do not modify anything.
Reconcile AGENTS.md, CLAUDE.md, and the real CI verification commands.
```

Repeated runs are convergent: a sound, unchanged repository should produce no
material diff.

## Scanner

Both shipped scanners use only their runtime standard library and do not modify
the target:

```text
node scripts/scan_repo.cjs --root /path/to/repository --format markdown
node scripts/scan_repo.cjs --root /path/to/repository --format json
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

It inventories instruction surfaces, Skills, host configuration, manifests,
declared commands, documentation, tests, quality configuration, and CI.
Verification commands in supported instruction-file code fences are recognized
conservatively but never executed. Diagnostic hints are investigation leads,
not automatic quality judgments, evidence that a host policy is active, or
permission to execute project commands. Collected text receives best-effort
redaction for common credential syntax, but reports remain sensitive local
evidence and must be inspected before sharing. Git metadata calls disable
repository fsmonitor execution, strip inherited `GIT_*` repository selectors,
and query only repository identity and branch. They deliberately do not run
status or diff because Git may execute repository-configured content filters;
Schema v3 therefore reports worktree dirtiness as `unverified` and its count as
`null`, never silently “clean.” Agentize prefers the Node.js implementation when
available, falls back to Python, and otherwise reproduces a bounded inventory
with the host's existing read-only tools while marking unavailable deterministic
fields `unverified`. It never installs a runtime merely to run a scan.

## Development

Run the local tests and inspect the Skill against itself:

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
git diff --check
```

[`DESIGN.md`](DESIGN.md) defines the product boundary and acceptance criteria.
Observable expectations for repository states, runtime fallback, safety, and
cross-host behavior live in [`tests/behavior-cases.md`](tests/behavior-cases.md).

## License

MIT
