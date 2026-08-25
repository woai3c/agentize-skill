# Repository assessment

Use this reference to turn repository evidence into a bounded improvement plan.
The objective is not a maximum score. It is the smallest trustworthy,
repository-owned harness that lets an ordinary coding agent specify, plan,
implement, verify, review, and learn after Agentize Skill has been removed, while
handing real intent, risk, and acceptance decisions to the right humans.

## Evidence hierarchy

When sources disagree, prefer evidence in this order while accounting for the
question being answered:

1. Executable configuration, schemas, and current tests for actual behavior.
2. CI and maintained task-runner scripts for commands that the project relies
   on.
3. Current implementation and public interfaces for architecture and data flow.
4. Repository instructions and maintained documentation for intent and local
   conventions.
5. Git history, issues, and decision records for rationale.
6. Naming conventions or common industry practice only as a lead to verify.

No source is universally authoritative. A test can encode obsolete behavior;
CI can omit an important local check; documentation can describe intended
behavior not yet shipped. Resolve contradictions with multiple direct signals
and state uncertainty when they remain.

Scanner diagnostics describe observed absence or ambiguity; they are prompts to
classify, not defects by themselves. For example, no CI configuration may be a
material shared-branch verification gap, an optional investment, or
`not_applicable` for the repository. Do not report the same absent surface as
both a current defect and an optional improvement without separate evidence and
scope explaining the distinction.

## Enforcement evidence

Treat a statement such as "Plan mode is read-only," "this review is required,"
or "the Agent sees this file" as a claim to verify, not as proof. When the claim
materially affects safety or workflow readiness, read
[compatibility.md](compatibility.md) and record:

- the behavior and scope being claimed;
- the host, tool, CI system, or human process expected to consume it;
- whether the mechanism is advisory guidance, tool filtering, an approval or
  policy decision, a sandbox or operating-system boundary, a repository check,
  or external governance;
- whether failure blocks the action, asks a person, warns and continues, or is
  unknown;
- the direct evidence that the mechanism is active in the target environment.

Configuration presence proves only that a file exists. A prompt can be useful
guidance without being an enforced restriction, and a documented provider
feature may be disabled at the project tier or unavailable in the current host.
Describe those states accurately instead of flattening them into "supported."

## Capability rubric

Classify each applicable or requested capability independently. A repository can
be strong in one, missing another, and have no need for a third.

| Capability | Sound when | Common weak signals |
| --- | --- | --- |
| Orientation | Purpose, entry points, and repository map are discoverable quickly. | README is marketing-only; maps list every folder without explaining ownership. |
| Scoped instructions | The applicable instruction file says what differs from normal agent behavior. | One giant global file; duplicate provider files; nested rules contradict parents. |
| Context delivery | Relevant hosts discover the intended instruction chain, precedence and refresh boundary. | A file exists but no target host reads it; nested rules are loaded too late; an edit is assumed visible in an already-running session. |
| Architecture context | Boundaries, dependencies, data flow, and important invariants are findable. | A stale diagram; directory tree presented as architecture; unwritten cross-module constraints. |
| Domain context | Non-obvious business rules and vocabulary have an owned source of truth. | Rules live only in prompts, tickets, or tests; plausible facts are guessed. |
| Work definition | Consequential work has discoverable goals, constraints, success and acceptance criteria, scope, and unresolved questions in an existing owned system. | Imperative implementation steps with no desired outcome; tests derived only from the proposed code; no owner for ambiguous intent. |
| Planning and plan review | Non-trivial work produces a scoped, evidence-backed plan and has a real route for Human Plan Review; a bounded fast path exists for obvious low-risk work. | The Agent edits before surfacing assumptions; silence is approval; every typo requires heavyweight ceremony. |
| Fast verification | Relevant Unit and Integration tests, typecheck, Lint, and necessary build commands are exact, safe, and cheap enough for the implementation loop. | Only "run tests"; the full E2E suite is required after every edit; commands need undocumented state. |
| Targeted runtime verification | Each applicable changed surface has a safe focused runtime path: browser interaction for Web/UI, representative requests for APIs, isolated execution for migrations, controlled messages for workers/queues, or real invocation for CLIs/scripts. Evidence is bound to the tested change, environment, inputs or test state, exact actions, observable predicates, and permitted side effects. | Browser is forced onto non-Web work; Unit tests are presented as runtime proof; a framework or command is assumed usable without environment, data, reset, permissions, or an active host; fixed delays, ambiguous matches, or artifacts without provenance are treated as proof. |
| Human Local Acceptance | After applicable local Agent verification, a human or established policy decides whether the outcome is actually wanted before the change becomes Ready for Review; failed acceptance returns through implementation and local verification. | Green checks are treated as product approval; an Agent accepts its own interpretation; acceptance first appears after technical MR/PR gates; routine work repeats an identical human ceremony locally and remotely. |
| Change workflow | An agent can explore, plan, implement, debug, retest, and hand off through explicit correction loops without Agentize Skill. | Commands require undocumented setup; feedback has no return path; future sessions depend on the bootstrap chat. |
| Draft/Ready MR/PR review and CI | Reviewed-branch projects allow Draft MR/PR early without treating it as ready, gate Ready for Review on local verification and Human Local Acceptance, distinguish implementing-Agent evidence from independent AI review where configured, and run the complete applicable per-change MR/PR CI gate set. Every fix returns through local checks, MR/PR update, AI Review, and MR/PR CI. | Draft creation is treated as readiness; an Agent approves itself; a YAML file is assumed active without a runner or permissions; a fix bypasses rerun gates; a green aggregate ignores a failed, cancelled, missing, or unexpectedly skipped result assigned to the MR/PR boundary. |
| E2E placement and evidence | A cost- and risk-aware policy places targeted or full E2E per MR/PR, at test/staging promotion, on a schedule, before release, or in an explicit combination. Each path names its suite, trigger, revision/candidate, environment/data, cost, owner, blocking target, and failure route; task evidence states when E2E did not run. | Full E2E is forced onto every MR/PR regardless of cost; expensive E2E is deferred with no trigger or owner; framework presence is called readiness; a scheduled result is attributed to a different change; “all regression passed” is claimed when only MR/PR gates ran. |
| Delivery and observation | Applicable merge, release, rollback, operational checks, and success signals are discoverable with their owners and permissions. | Deployment is mixed into routine checks; no rollback or success signal; production access is assumed. |
| Continuous knowledge capture | During implementation, authoritative durable, non-obvious, reusable knowledge is routed into the current change and the smallest semantic owner; deterministic enforcement is added separately when proportionate. | Every note is deferred until merge; human corrections remain only in chat; unconfirmed inference becomes policy; detailed knowledge is left in root instructions; a test is treated as the sole source of consequential business intent. |
| Optional post-merge knowledge audit | When the project chooses and configures it, a real merge trigger can inspect only late lifecycle evidence and open a separate human-reviewed knowledge change when continuous capture missed something. | The optional backstop is presented as mandatory or already active; the audit re-summarizes everything; instructions are mistaken for a trigger; automation writes directly to the default branch. |
| Knowledge provenance | Observed, Inferred, and Unknown claims retain evidence, confidence where relevant, impact, and decision ownership. | Model interpretation is presented as fact; current behavior silently becomes a business rule. |
| Knowledge adoption | Feedback-derived knowledge has authoritative semantic meaning, final-state evidence of adoption, and a recorded disposition before promotion. | A comment, resolved thread, “fixed” claim, same-file edit, or merge is treated as proof that the proposed lesson was adopted. |
| Parallel readiness | When parallel work is actually used, tasks, worktrees, shared resources, and integration ownership are separable. | More agents are added before verification is reliable; sessions share ports, state, or generated files without coordination. |
| Host enforcement | Consequential restrictions identify their real consumer, enforcement layer, failure behavior and tested scope. | Prompt-only guidance is called a sandbox; an unused policy file is called enforced; approval, review and product acceptance are conflated. |
| Safety and boundaries | Destructive, costly, credentialed, generated, and release paths are clear. | Blanket prohibitions; copied secrets; release commands mixed into routine verification. |
| Knowledge gaps | Unknowns are explicit, evidence-backed questions with a path to resolution. | Confident invented rules; vague TODO lists; questions with no impact or owner. |
| Maintainability | Artifacts have clear owners and update triggers and survive without Agentize Skill. | Generated banners; timestamps that churn; duplicated facts; an external runtime is required. |

Use these statuses:

- `sound`: sufficient, current, and supported by evidence;
- `weak`: useful but missing information needed for reliable action;
- `missing`: no adequate artifact or executable path exists;
- `conflicting`: two current-looking sources disagree;
- `stale`: direct evidence disproves material content;
- `unverified`: plausible, but not yet checked;
- `not_applicable`: direct evidence shows the capability is outside this
  repository or request, so its absence is not a gap.

### Operational capability status

These assessment states describe evidence quality. They do not tell a developer
whether a capability can currently run. Map each material capability separately
to one operational status in the final Harness Capability Report:

| Operational status | Meaning |
| --- | --- |
| `READY` | The complete path and its prerequisites are configured for the named scope, and a safe representative check or direct platform evidence verifies it. |
| `PARTIAL` | A useful subset works, but one or more named parts or scopes do not. State exactly what works and what fallback applies. |
| `SETUP REQUIRED` | A concrete path has been selected and its safe repository-side pieces are present, but a named human action, secret, account, permission, external setting, or environment is still required. It is not ready until verified. |
| `NOT CONFIGURED` | The capability applies, but no usable path is currently configured or selected in the named scope. Give an evidence-backed recommendation and fallback, not a promise. |
| `UNVERIFIED` | Configuration appears to exist, but effective activation or behavior could not be safely proven. |
| `NOT APPLICABLE` | Direct evidence shows the capability does not apply to this repository or scope. |

Capability status is not a task result. Status is scoped. `Targeted Runtime
Verification (Web/UI): READY (<named host with browser controller>)` does not mean
the same path is ready in another coding-agent host, a headless CI runner, or for
an API or migration surface. `READY` describes capability availability, not
whether a check ran for the current task.

For task execution, report a separate outcome: `PASSED`, `FAILED`, `NOT EXECUTED`,
or `NOT APPLICABLE`. A `NOT EXECUTED` result includes the capability status,
reason, consequence, and fallback or human action. Never turn `SETUP REQUIRED`,
`NOT CONFIGURED`, or `UNVERIFIED` into a silent skip or an all-gates-passed claim.

Classify capabilities independently; do not collapse them into a score. The
ideal workflow, evidence assessment, operational status, and current-task
execution outcome are four different things. An Agentize Skill run can finish honestly
with unresolved work, but if a request-critical capability is not `READY` and
has no safe fallback or human decision path, the handoff must describe the
repository as only partially prepared. This is an outcome rule, not another
user-selectable mode.

## Scenario handling

### No effective workflow

Create the minimum spine: a root instruction source, short repository map,
exact supported commands, and a concise durable workflow contract covering the
full path, fast path, verification evidence, human decision points, and learning
owner. Add focused architecture, domain, review, or knowledge-gap material only
when no existing owned source can carry a consequential fact. Do not generate
an empty example documentation tree.

### A useful partial workflow

Retain the existing source of truth and fill only consequential gaps. Prefer
linking to maintained material over copying it. If commands exist but are slow
or ambiguous, document a targeted-to-broad verification ladder rather than
inventing new automation immediately.

### Correct and incorrect material coexist

Build a conflict table before editing: claim, source A, source B, executable
evidence, resolution, and remaining uncertainty. Correct demonstrably stale
claims in place. When the business meaning is ambiguous, keep both observations
out of normative instructions and add a precise human question.

### A mature workflow already exists

Prefer no change or a narrow repair. Do not rename established files, replace
working conventions, or install Agentize Skill artifacts merely to make the
repository resemble another project. Verify that the workflow survives without
Agentize Skill, that its Capability Report is accurate, that confirmed knowledge can be
captured in active work, and that late post-merge corrections have a durable
fallback. Report why the existing harness is sound and any optional improvements
separately.

## Depth and investment decisions

Use repository complexity and demonstrated failure modes, not file count alone:

- A small library may need only one instruction file and existing tests.
- A monorepo often benefits from a concise root map plus nested instructions for
  subtrees with different toolchains.
- A system with irreversible operations or regulated data needs explicit safety
  boundaries, stronger executable checks, and named human decision points.
- A deployed service may need discoverable rollout, rollback, operational
  verification, and success signals; a local library may not.
- Parallel-agent guidance is useful only after work can be isolated and relevant
  verification is reliable.
- Frequently repeated, deterministic discovery may justify a local script.
- Organization-wide installation may justify a skills-only plugin.
- Live private data, authentication, or controlled remote actions may justify
  an MCP server. None is required for ordinary repository bootstrap.

## Anti-patterns

Reject the common weak signals in the rubric above, especially patches that primarily produce:

- a generic fixed scaffold, exhaustive codebase summary, copied provider policy, or unverified command;
- a new dependency, CI workflow, E2E cadence, approval tier, deployment path, or observability surface without a demonstrated repository need and working underlying path;
- an ideal-stage checklist, configuration file, dependency, or documented intention presented as operational `READY` evidence;
- a missing or deferred capability recorded only as “skipped,” without status, consequence, fallback, owner, and reevaluation trigger;
- the same observed absence described as both a current defect and an optional investment without distinct evidence and scope;
- prose-only policy where a cheap deterministic constraint is appropriate, or a green check presented as proof of product intent;
- an Agent silently approving its own material plan, acceptance, risk decision, or inferred business rule;
- a runtime surface selected by habit rather than the changed behavior, evidence without change/environment/action/predicate provenance, or E2E conflated with targeted runtime verification;
- full E2E forced into every edit or MR/PR regardless of cost, or deferred without an exact trigger, tested revision, owner, blocking target, and failure route;
- Draft represented as Ready, a repair bypassing applicable review or CI reruns, or an aggregate hiding failed, cancelled, timed-out, missing, or unexpectedly skipped required gates;
- an implementing Agent's self-review labeled independent, or a provider control called enforced solely because its prompt or configuration exists;
- knowledge deferred unnecessarily until merge, promoted from unconfirmed feedback, written directly to the default branch, or generated by supposed post-merge automation with no verified trigger and Agent path;
- low-impact unknowns, duplicated facts, or any future workflow that requires Agentize Skill to remain installed.
