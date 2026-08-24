# Repository assessment

Use this reference to turn repository evidence into a bounded improvement plan.
The objective is not a maximum score. It is the smallest trustworthy,
repository-owned harness that lets an ordinary coding agent specify, plan,
implement, verify, review, and learn after Agentize has been removed, while
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
| Browser business verification | Applicable Web/UI work has an Agent-accessible browser controller, safe application start path, test identity/data, authentication setup, a focused Acceptance Criteria flow, and evidence bound to the tested change, environment, and precise state predicates. | E2E is relabeled as browser verification; a host tool is assumed available to every future Agent; a fixed delay, ambiguous text match, or screenshot without provenance is treated as proof; production credentials or ad hoc clicks are required. |
| Validation ownership | Agent evidence and human acceptance are distinct, and risk determines who must decide what. | Green CI is treated as product approval; an agent accepts its own interpretation; every change gets the same ceremony. |
| Change workflow | An agent can explore, plan, implement, debug, retest, and hand off through explicit correction loops without Agentize. | Commands require undocumented setup; feedback has no return path; future sessions depend on the bootstrap chat. |
| MR/PR review and full CI | Reviewed-branch projects distinguish implementing-Agent evidence, independent AI review where configured, full CI including full E2E where available, risk-based technical review, and Human Validation. Every applicable required gate has explicit result accounting. | An Agent approves itself; full E2E is claimed from framework presence; a YAML file is assumed active without a runner or permissions; a green aggregate ignores a failed, cancelled, missing, or unexpectedly skipped required result. |
| Delivery and observation | Applicable merge, release, rollback, operational checks, and success signals are discoverable with their owners and permissions. | Deployment is mixed into routine checks; no rollback or success signal; production access is assumed. |
| Continuous knowledge capture | During implementation, authoritative durable, non-obvious, reusable knowledge is routed into the current change and the smallest long-term owner. | Every note is deferred until merge; human corrections remain only in chat; unconfirmed inference becomes policy. |
| Post-merge knowledge audit | A configured merge trigger can inspect only late lifecycle evidence and open a separate human-reviewed knowledge change when continuous capture missed something. | The audit re-summarizes everything; instructions are mistaken for a trigger; automation writes directly to the default branch. |
| Knowledge provenance | Observed, Inferred, and Unknown claims retain evidence, confidence where relevant, impact, and decision ownership. | Model interpretation is presented as fact; current behavior silently becomes a business rule. |
| Knowledge adoption | Feedback-derived knowledge has authoritative semantic meaning, final-state evidence of adoption, and a recorded disposition before promotion. | A comment, resolved thread, “fixed” claim, same-file edit, or merge is treated as proof that the proposed lesson was adopted. |
| Parallel readiness | When parallel work is actually used, tasks, worktrees, shared resources, and integration ownership are separable. | More agents are added before verification is reliable; sessions share ports, state, or generated files without coordination. |
| Host enforcement | Consequential restrictions identify their real consumer, enforcement layer, failure behavior and tested scope. | Prompt-only guidance is called a sandbox; an unused policy file is called enforced; approval, review and product acceptance are conflated. |
| Safety and boundaries | Destructive, costly, credentialed, generated, and release paths are clear. | Blanket prohibitions; copied secrets; release commands mixed into routine verification. |
| Knowledge gaps | Unknowns are explicit, evidence-backed questions with a path to resolution. | Confident invented rules; vague TODO lists; questions with no impact or owner. |
| Maintainability | Artifacts have clear owners and update triggers and survive without Agentize. | Generated banners; timestamps that churn; duplicated facts; an external runtime is required. |

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
| `SETUP REQUIRED` | Agentize installed or documented the repository-side path, but a named human action, secret, account, permission, external setting, or environment is still required. It is not ready until verified. |
| `NOT AVAILABLE` | No usable path is configured and Agentize could not safely establish one within scope. Give an evidence-backed option, not a promise. |
| `UNVERIFIED` | Configuration appears to exist, but effective activation or behavior could not be safely proven. |
| `NOT APPLICABLE` | Direct evidence shows the capability does not apply to this repository or scope. |

Capability status is not a task result. Status is scoped. `AI Browser
Verification: READY (Codex with Browser MCP)`
does not mean it is ready in Claude Code, a headless CI runner, or every future
host. `READY` describes capability availability, not whether a check ran for the
current task.

For task execution, report a separate outcome: `PASSED`, `FAILED`, `NOT EXECUTED`,
or `NOT APPLICABLE`. A `NOT EXECUTED` result includes the capability status,
reason, consequence, and fallback or human action. Never turn `SETUP REQUIRED`,
`NOT AVAILABLE`, or `UNVERIFIED` into a silent skip or an all-gates-passed claim.

Classify capabilities independently; do not collapse them into a score. The
ideal workflow, evidence assessment, operational status, and current-task
execution outcome are four different things. An Agentize run can finish honestly
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
working conventions, or install Agentize artifacts merely to make the
repository resemble another project. Verify that the workflow survives without
Agentize, that its Capability Report is accurate, that confirmed knowledge can be
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

Reject patches that primarily produce any of the following:

- a universal `AGENTS.md` template filled with generic advice;
- unverified build and test commands;
- an exhaustive codebase summary that will age immediately;
- several provider files containing copied policy;
- a new CI workflow without a proven command or repository need;
- an ideal-stage checklist presented as a report of configured capabilities;
- `READY` inferred from a file, dependency, framework, or documented intention
  without verifying the effective consumer and prerequisites;
- a missing browser, E2E, Reviewer Agent, CI, or merge trigger recorded only as
  "skipped" without capability status, consequence, and fallback;
- a generic setup TODO that omits the human action, owner, permissions, secrets,
  validation step, or status transition needed to close it;
- absence of CI described as a defect solely because the scanner observed it,
  or described simultaneously as a defect and optional investment without a
  distinct consequence;
- prose-only rules where a cheap mechanical check can enforce the invariant;
- a test suite presented as proof that the underlying product intent is correct;
- a workflow in which an agent silently supplies its own acceptance or risk
  decision;
- a workflow in which non-trivial implementation starts before its assumptions
  and plan can be reviewed, or every trivial edit waits on an unnecessary gate;
- E2E and browser business-flow validation presented as the same evidence;
- browser evidence that is not tied to the tested change, environment, test state,
  and precise observable predicate, or relies on fixed delays or ambiguous matches;
- a full E2E suite inserted into every local edit loop when it belongs in shared
  MR/PR CI;
- an aggregate CI success that ignores failed, cancelled, timed-out, missing, or
  unexpectedly skipped applicable required gates;
- an implementing Agent's self-review presented as independent review;
- a post-merge YAML file described as AI learning without a verified trigger,
  Agent runner, permissions, data boundary, and failure behavior;
- all knowledge deferred to a post-merge job even when authoritative corrections
  can be captured in the current implementation MR/PR;
- learning automation that commits directly to the default branch or promotes
  unconfirmed `Inferred` knowledge;
- review comments, resolved threads, “fixed” claims, same-file edits, or merge
  treated as sufficient evidence that feedback became durable knowledge;
- a provider policy, Hook, Plan mode, approval, or sandbox described as enforced
  solely because its file or prompt text exists;
- universal approval tiers, deployment steps, or observability scaffolds that do
  not match the project;
- an "unknowns" document filled with low-impact questions;
- a workflow that requires Agentize to remain installed after initialization.
