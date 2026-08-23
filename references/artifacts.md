# Durable repository artifacts

Use existing names and locations when they already have clear ownership. The
patterns below are options, not a scaffold to generate in every repository.
For the responsibility and transition rules behind work definition, Agent
verification, Human validation, delivery, observation, and learning, read
[delivery-workflow.md](delivery-workflow.md) when those capabilities need repair.

## Scope boundary

If the user explicitly requests an audit or report only, create or modify no
target artifact. Otherwise choose artifacts from direct repository evidence and
the requested agent-ready outcome; do not require the user to select an internal
mode. A new tool or automation surface must solve a consequential demonstrated
gap, be proportionate to the repository, and remain within normal permission and
external-action boundaries.

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

## Work definition and planning

Use the project's existing issue tracker, specification, proposal, PR, or task
format as the owner of intent. Repair its repository-visible template or guidance
when a consequential gap in outcome, constraint, acceptance, scope, risk, or
unresolved-question context prevents reliable execution. Repeated failures make
the investment stronger evidence but are not required when the user directly
requested this capability and the missing contract is already demonstrable.

Plans should describe a proposed route and verification strategy, not replace
the desired outcome. Persist a plan only when coordination, review, resumption,
or a consequential tradeoff benefits from it. Do not require a plan document for
small, obvious, reversible work or create a repository-local task system when an
existing external system is authoritative.

Agentize may draft missing structure and precise questions. It must not invent
business meaning, mark its own proposal accepted, or convert an implementation-
derived test into acceptance criteria without independent intent evidence.

## Verification ladder

Describe verification from fast and local to broad and expensive:

1. focused test or check for the changed unit;
2. package or subsystem checks;
3. repository lint, type, build, or integration checks;
4. end-to-end, snapshot, browser, performance, real-service, or full-suite
   checks when the affected surface warrants them;
5. CI or human review signals that cannot be reproduced locally.

Do not make browser verification mandatory merely because a repository has a
Web/UI surface. Persist browser or E2E instructions only when a safe, repeatable
project workflow already exists or establishing that capability directly serves
the current request.

For each non-obvious command, capture what it proves, where to run it, required
environment, expected cost, and meaningful exclusions. Do not equate a passing
unit suite with verified user behavior.

When the project uses a durable handoff or review format, keep Agent verification
evidence separate from Human validation: record checks actually run, failures,
exclusions, remaining observations or decisions, and evidence provenance when
it matters. A result from the implementing Agent, a reviewer Agent, CI, a policy
gate, and an authorized person must not be flattened into one "verified" flag.
Do not add a second handoff template when the existing PR, issue, or review
system can own these fields.

If a reliable command is repeatedly assembled by hand, add a small script or
task-runner target and test it. If the command is already stable in CI, expose a
targeted local equivalent rather than duplicating the pipeline.

## Human validation and risk ownership

Persist project-specific review ownership and high-consequence triggers only
when they are not already clear. Suitable owners may include existing review
guidance, `CODEOWNERS`, contribution docs, security policy, migration procedure,
release checklist, or a thin PR template. Link rather than duplicate policy.

State which outcomes require human judgment and what evidence helps that person
decide. Do not use documentation as proof that an external approval, branch
protection rule, or required review is actually enforced. Changing those external
controls requires separate evidence, authorization, and an appropriate tool.

Avoid a universal low/medium/high matrix. Use the repository's real risk
language and distinguish high-consequence paths from routine reversible changes
so that human attention is concentrated rather than applied mechanically.

## Delivery, observation, and rollback

For projects that ship or operate software, make the existing delivery and
operational paths discoverable when that knowledge materially affects safe Agent
work. Depending on the project, useful owned artifacts include:

- merge and release prerequisites;
- rollout, migration, compatibility, and rollback procedures;
- safe staging or smoke checks;
- links or commands for relevant logs, metrics, traces, alerts, or user signals;
- status, idempotency, or recovery paths for an external action whose outcome
  may be unknown after interruption;
- named external systems, permissions, and human owners where repository-local
  automation cannot perform the step.

Document what a signal establishes and any safe boundary around obtaining it.
Do not place credentials, private endpoints, or production data in agent-facing
prose. Do not create deployment or observability infrastructure merely to make
the workflow look complete, and do not add these artifacts to projects for which
shipping and operation are not applicable.

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

A new mechanical feedback loop must satisfy the scope boundary above. A test
must protect intended behavior supported by a specification, stable contract,
user confirmation, or multiple direct signals; implementation behavior alone
is not sufficient evidence that the behavior should be preserved.

Keep an unconfirmed lesson as a candidate in the repository's existing Issue,
review, incident, or feedback system. Before promotion, record the evidence for
generalizing it and the owner who can confirm semantic meaning. Only confirmed
lessons move into a durable rule or executable check; Agent reflection, a raw
rating, or one reviewer finding does not apply itself.

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
