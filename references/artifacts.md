# Durable repository artifacts

Use existing names and locations when they already have clear ownership. The
patterns below are options, not a scaffold to generate in every repository.

## Root instruction source

A useful root instruction file is an operational index. Include only verified,
repository-specific information that changes an agent's decisions, such as:

- one-sentence purpose and the primary source locations;
- a map of major ownership boundaries, not every directory;
- exact setup, run, and verification commands, including the working directory
  or prerequisites when non-obvious;
- the fastest targeted check and when a broader suite is justified;
- generated, vendored, credentialed, destructive, or release-sensitive paths;
- non-obvious architectural or domain invariants;
- links to deeper authoritative documents and nested instructions;
- update triggers for docs, schemas, snapshots, or generated artifacts.

Do not restate the host agent's generic behavior, teach the programming
language, prescribe style already enforced by a formatter, or copy the README.
When the file becomes hard to scan, move owned detail into a focused document
or nested instruction file and leave a short routing link.

## Nested instructions

Add a nested instruction file only when a subtree differs materially in at
least one of these dimensions:

- toolchain or working directory;
- architecture or ownership;
- verification commands;
- safety constraints;
- generated or vendored source policy;
- release or compatibility requirements.

The nested file should state the delta from its parent. Avoid copying parent
content. Verify the target agent's instruction precedence before relying on
nested behavior.

## Architecture context

Create or repair an architecture document when agents otherwise need broad
source exploration for routine changes. Prefer stable relationships:

- system boundaries and dependency direction;
- entry points and major execution or data flows;
- state ownership and persistence;
- extension points and deliberately forbidden couplings;
- important failure, concurrency, security, or compatibility invariants;
- links to implementation owners and decision records.

A directory listing is not an architecture document. Avoid volatile inventories
of every type or file. Use a small diagram only when it communicates a
relationship more clearly than prose.

## Domain and business context

Document a domain rule only when direct evidence establishes it. Name the
source and distinguish:

- invariant behavior that code and tests must preserve;
- current product policy that may change;
- examples that illustrate but do not define the rule;
- unanswered questions that require an owner.

Prefer the repository's existing domain docs, schemas, and acceptance tests.
Never reverse-engineer sensitive business policy from a few incidental code
paths and present it as authoritative.

## Verification ladder

Describe verification from fast and local to broad and expensive:

1. focused test or check for the changed unit;
2. package or subsystem checks;
3. repository lint, type, build, or integration checks;
4. end-to-end, snapshot, browser, performance, real-service, or full-suite
   checks when the affected surface warrants them;
5. CI or human review signals that cannot be reproduced locally.

For each non-obvious command, capture what it proves, where to run it, required
environment, expected cost, and meaningful exclusions. Do not equate a passing
unit suite with verified user behavior.

If a reliable command is repeatedly assembled by hand, add a small script or
task-runner target and test it. If the command is already stable in CI, expose a
targeted local equivalent rather than duplicating the pipeline.

## Knowledge gaps

Create a dedicated knowledge-gap document only when unresolved questions would
materially affect future changes. Otherwise keep a short section in the root
instruction file or final handoff.

Each gap should contain:

- the precise question;
- why the answer changes an engineering decision;
- evidence already checked and why it was insufficient;
- the likely owner or source that can resolve it;
- the artifact, test, or code that should be updated after resolution.

Do not turn ordinary backlog work into knowledge gaps. Remove a gap when its
answer has been incorporated into the owning source of truth.

## Decision records

Use the repository's existing ADR, RFC, proposal, or decision-note convention.
Add a record when future maintainers are likely to revisit a non-obvious
tradeoff and code cannot preserve the rationale. Capture the problem, decision
or proposal status, alternatives actually considered, consequences, and
verification or migration implications.

Do not introduce a new decision-record system for a one-line local choice.

## Mechanical feedback loops

Choose the strongest economical representation for a learned constraint:

| Repeated problem | Preferred durable form |
| --- | --- |
| Behavioral regression | Focused test or end-to-end assertion |
| Invalid dependency or API direction | Lint, type, schema, or dependency rule |
| Generated-file drift | Checked generator and CI gate |
| Fragile repeated command | Script or task-runner target |
| Repository-specific judgment | Concise instruction with rationale or link |
| Non-obvious tradeoff | Decision record |
| Private live system fact | Authorized connector or MCP tool, not copied prose |

Hooks are appropriate for lifecycle enforcement that must run mechanically and
has a stable, trusted command. Instructions are appropriate when judgment is
required. Do not use a hook merely to inject more prose into every session.

## Reconciliation rules

- Patch owned sections; do not replace an existing document wholesale unless
  it is demonstrably obsolete and the replacement preserves all valid facts.
- Keep one home per fact and link to it elsewhere.
- Preserve established vocabulary and relative-link style.
- Prefer stable facts over generated timestamps and exhaustive inventories.
- Keep provider compatibility thin; never maintain identical policy manually
  in several files.
- Run existing formatters and doc validators that govern changed artifacts.
- On a repeat Agentize run, a sound repository should produce no material diff.
