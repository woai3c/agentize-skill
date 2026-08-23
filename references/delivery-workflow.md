# Human-agent delivery workflow

Use this reference when the assessment finds a consequential gap or conflict in
work definition, planning expectations, validation ownership, risk handling,
delivery, observation, learning, or parallel execution. It defines the target
repository capability; it is not a fixed ceremony to copy into every project.

## Separate the two workflows

An Agentize run uses this reconciliation loop:

```text
inspect -> assess -> reconcile -> verify -> handoff
```

The repository it leaves behind should support the applicable parts of this
ongoing engineering loop:

```text
Specify -> Explore -> Plan -> Execute -> Agent Verify -> Human Validate
        -> Ship -> Observe -> Learn
```

Do not confuse the two. Agentize prepares and repairs the repository-side
harness; it does not become the runtime orchestrator for future changes.

## Responsibility and evidence

| Stage | Agent contribution | Human responsibility when needed | Useful durable evidence |
| --- | --- | --- | --- |
| Specify | Structure the request, find contradictions, and identify missing facts. | Confirm intent, priority, non-goals, business meaning, and acceptance criteria. | Existing issue, product spec, RFC, acceptance example, or precise unresolved question. |
| Explore | Trace relevant code, configuration, tests, history, and boundaries. | Supply material context that is unavailable to the repository or authorized tools. | Repository map, owned architecture or domain source, and cited findings. |
| Plan | Propose a scoped approach, alternatives, risks, and verification strategy. | Approve consequential product, architecture, migration, security, or cost tradeoffs. | Task plan, RFC, ADR, or issue comment when the decision needs to survive the session. |
| Execute | Implement the authorized change and keep it within the agreed scope. | Grant additional authority for destructive, credentialed, external, or irreversible actions. | Reviewable diff and focused supporting artifacts. |
| Agent Verify | Run the safe relevant checks, debug failures, retest, and report evidence and exclusions. | Define or confirm evidence sufficiency where consequence requires judgment. | Test, type, lint, build, E2E, screenshot, CI, log, metric, or trace result. |
| Human Validate | Present the result and the gap between technical evidence and product acceptance. | When acceptance is required, judge whether the outcome is actually wanted and accept, reject, or revise it. | Explicit acceptance, review decision, policy-authorized automated transition, or concrete corrective feedback. |
| Ship | Prepare or follow the repository's delivery and rollback path. | Authorize merge, release, migration, rollout, or other production-affecting action when required. | CI gates, release procedure, approvals, rollback plan, and deployment record. |
| Observe | Gather authorized operational and user-facing signals against stated expectations. | Decide whether the signals represent product success and whether intervention is needed. | Runbook, dashboard or query reference, alert, support signal, and rollback trigger. |
| Learn | Propose the smallest durable correction after a confirmed failure or review finding. | Confirm semantic lessons before they become product policy or permanent constraints. | Test, lint rule, schema, script, instruction, decision record, or owned knowledge update. |

The human-responsibility column is a real system boundary when its decision is
applicable, not a mandatory meeting at every stage or a temporary automation gap.
Existing policy may pre-authorize low-risk transitions. An agent may help
articulate or challenge a decision, but it must not claim to have supplied human
intent, accepted its own result, or assumed organizational risk on a person's
behalf.

## Work-definition contract

Use the repository's existing issue, specification, RFC, task, or planning
system. Do not create a second system merely to match these labels. For a
consequential change, the available sources should establish enough of the
following to proceed safely:

- goal and desired user or system outcome;
- constraints and relevant invariants;
- success criteria that can be demonstrated;
- acceptance criteria that are independent of the proposed implementation;
- non-goals or scope boundaries when plausible interpretations differ;
- known risk, validation owner, and unresolved questions.

The agent can draft or normalize this information. A human with relevant
authority must confirm material business meaning. When the missing answer could
change the implementation or make a test preserve the wrong behavior, keep it
as a precise knowledge gap and stop that dependent work instead of guessing.

Do not require heavyweight specifications for trivial, reversible work whose
intent and acceptance are already obvious from direct evidence.

## Two-layer validation

Keep these decisions separate in repository guidance and handoff:

1. **Agent verification:** what was checked, what passed or failed, what the
   evidence proves, and what was not checked.
2. **Human validation:** which outcomes still require human observation or
   judgment, who is able to decide, and whether that decision has actually been
   recorded.

Passing tests, CI, browser automation, or reviewer-agent checks proves only what
those checks assert. It does not prove that the acceptance criteria express the
right business outcome. Likewise, human acceptance does not excuse missing
mechanical verification that is cheap, relevant, and available.

Never label a result accepted, approved, merged, shipped, or production-safe
unless the corresponding event is directly observed or explicitly supplied by
an authorized source.

Record evidence provenance when it changes the conclusion: a check run by the
implementing Agent, an independent reviewer-agent finding, CI, a deterministic
policy gate, and a human acceptance decision are different signals. Independent
machine review can reduce correlated implementation errors, but it remains Agent
verification and does not become Human validation merely because another model
produced it.

## Risk-proportional human validation

Reuse the project's existing risk and ownership policy. When none exists and the
distinction materially affects the workflow, identify project-specific triggers
rather than imposing a universal scoring system. Relevant signals include:

- authentication, authorization, privacy, secrets, safety, or security boundaries;
- billing, money movement, entitlements, legal, or regulatory behavior;
- destructive data operations, schema migrations, compatibility, or rollback cost;
- production configuration, releases, external side effects, or shared infrastructure;
- ambiguous core business rules or changes with a wide blast radius.

An agent may recommend a risk level and corresponding evidence. A responsible
human or existing governance policy owns consequential classification and final
acceptance. Low-impact, reversible changes should not inherit heavyweight gates
merely because high-risk paths exist elsewhere in the repository.

## Interrupted external effects

For workflows that can deploy, migrate data, charge money, change remote state,
or perform another non-idempotent effect, distinguish a failed call from an
unknown outcome. If dispatch is known to have started but no authoritative
result was recorded:

1. retry directly only when the operation is read-only or demonstrably
   idempotent;
2. otherwise inspect the real external state using an authorized, non-mutating
   path;
3. if the state cannot be established, request confirmation from the responsible
   person before retrying or attempting compensation.

A conversation restart, missing tool result, or red error indicator is not proof
that the external effect did not occur. Add repository guidance for this case
only where such effects actually exist, and prefer an existing idempotency key,
status command, recovery runbook, or deployment record over generic prose.

## Ship, observe, and learn

These stages apply only when the project actually ships or operates something.
A local library or documentation repository may end at package checks or human
review. A service may need discoverable rollout, rollback, operational checks,
and success or failure signals.

Agentize may repair repository-owned instructions, runbooks, commands, or safe
automation for these stages when evidence and authorization support the change.
It does not itself deploy, access production, change branch protection, create
credentials, or operate an external service merely because those stages exist.
Represent inaccessible external controls as links, named owners, or verified
handoff steps rather than pretending they are repository-local automation.

After a human correction, failed verification, incident, or production finding,
ask what allowed the failure and choose the smallest durable response. Encode
only confirmed learning. A one-time preference or ambiguous observation should
remain feedback or a question, not become a universal rule.

Use a simple promotion path:

```text
feedback or finding -> candidate lesson -> authorized confirmation
                    -> durable owner -> verification
```

The candidate may live in an existing Issue, review thread, incident action, or
other inbox; do not create a second feedback system solely for Agentize. Record
what evidence supports the generalization and who may confirm semantic meaning.
Only after confirmation should it update a test, rule, instruction, decision, or
Skill. Raw ratings, one reviewer-agent opinion, and the implementing Agent's own
reflection are inputs to evaluate, not self-applying policy.

## Parallel readiness

Parallel agents are an optional throughput optimization, not part of the minimum
harness. Recommend or document them only when work can be separated, verification
is reliable, and the repository has a safe answer for worktree setup, generated
files, ports, databases, caches, credentials, and integration ownership. More
agents must not be used to compensate for unclear intent or weak validation.

## Completion condition

For each applicable stage, a trustworthy repository has at least one of:

- a working, discoverable repository or external workflow;
- an explicit human decision point with an appropriate owner or authority;
- a precise evidence-backed gap explaining what is missing, why it matters, and
  what can resolve it.

This is workflow readiness, not a guarantee of semantic correctness. Agentize
must report the distinction and must not claim full autonomy. If a
request-critical path is still missing, conflicting, or unverified and has no
safe human resolution path, the run may still finish with an accurate handoff
but the repository must be described as only partially prepared, not fully
agent-ready.
