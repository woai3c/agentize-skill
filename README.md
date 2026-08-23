# Agentize

Agentize your codebase.

Agentize is a coding-agent skill that turns an existing codebase into an
agent-ready repository with trustworthy context, exact verification paths, and
durable engineering guardrails.

It works like an initializer and reconciler:

```text
repository -> inspect -> assess -> reconcile -> verify -> human-owned harness
```

Agentize is not a runtime layer that every future agent session must depend on.
After a run, the useful result lives in the target repository.

Implementation is in progress. [`DESIGN.md`](DESIGN.md) defines one complete
acceptance boundary rather than a sequence of reduced product versions.

## What it does

Agentize adapts to the repository it finds:

| Starting point | Behavior |
| --- | --- |
| No effective workflow | Creates the smallest verified instruction and validation spine. |
| Partial workflow | Preserves useful material and fills consequential gaps. |
| Correct and incorrect material | Resolves claims with executable evidence and records real unknowns. |
| Mature workflow | Makes a narrow repair or reports that no material change is needed. |

Depending on the project, a run may create or improve repository instructions,
architecture or domain context, a verification ladder, nested guidance,
decision records, focused scripts, CI gates, or a knowledge-gap list. None of
those artifacts is generated unconditionally.

## Why a skill plus a scanner

The skill owns judgment: what evidence matters, which existing files to retain,
and what the smallest useful target state is. The bundled scanner owns the
repeatable read-only inventory that would otherwise be reconstructed on every
run.

The complete delivery supports both direct Skill installation and a
reproducibly generated Codex skills-only Plugin. Both use the same canonical
source; the Plugin is only a distribution wrapper. Agentize intentionally has
no MCP server or resident harness-management service because its work is local
to the repository and does not require authenticated live data or remote
actions.

## Install

Place this repository where your coding agent discovers skills. For Codex, a
personal installation can live at:

```text
~/.agents/skills/agentize/
```

For a repository-scoped installation, place it under:

```text
<repository>/.agents/skills/agentize/
```

Other agents may use different discovery paths. Keep this directory as the
canonical copy rather than maintaining divergent versions.

## Use

Invoke the skill from the repository you want to improve:

```text
$agentize Make this repository agent-ready.
```

You can narrow the request without selecting a separate mode:

```text
$agentize Audit the existing agent workflow and repair only proven gaps.
$agentize Reconcile AGENTS.md, CLAUDE.md, and CI verification without changing product code.
```

Repeated runs are convergent: a sound repository should produce no material
diff.

## Scanner

The scanner has no third-party dependencies and does not modify the target:

```text
python scripts/scan_repo.py --root /path/to/repository --format markdown
python scripts/scan_repo.py --root /path/to/repository --format json
```

It inventories instruction surfaces, skills, manifests, declared commands,
documentation, tests, quality configuration, and CI. Its diagnostic hints are
leads for the agent, not automatic judgments about repository quality.

## Development

Run the local tests and inspect the skill against itself:

```text
python -m unittest discover -s tests -v
python scripts/scan_repo.py --root . --format markdown
```

Behavioral expectations for empty, partial, conflicting, and mature
repositories live in [`tests/behavior-cases.md`](tests/behavior-cases.md).

## License

MIT
