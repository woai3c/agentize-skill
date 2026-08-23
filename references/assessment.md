# Repository assessment

Use this reference to turn repository evidence into a bounded improvement plan.
The objective is not a maximum score. It is the smallest trustworthy harness
that lets an agent act with high autonomy, verify its work, and hand the result
to the right human decisions without pretending those decisions were automated.

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
| Verification | Fast feedback and broader confidence commands are exact and runnable. | Only "run tests"; one full-suite command for every change; green checks that do not cover user behavior. |
| Validation ownership | Agent evidence and human acceptance are distinct, and risk determines who must decide what. | Green CI is treated as product approval; an agent accepts its own interpretation; every change gets the same ceremony. |
| Change workflow | An agent can explore, plan, implement, retest, review, and hand off without manual copy-paste. | Commands require undocumented setup; no way to reproduce CI; no evidence or human-decision expectations. |
| Delivery and observation | Applicable merge, release, rollback, operational checks, and success signals are discoverable with their owners and permissions. | Deployment is mixed into routine checks; no rollback or success signal; production access is assumed. |
| Feedback retention | Repeated mistakes become durable constraints or executable checks. | The same review comment recurs; instructions grow while tests and linters do not. |
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

Classify capabilities independently; do not collapse them into a score. An
Agentize run can finish honestly with unresolved work, but if a request-critical
capability remains `missing`, `conflicting`, or `unverified` without a safe
human decision path, the handoff must describe the repository as only partially
prepared and must not claim it is fully agent-ready. This is an outcome rule,
not another user-selectable mode.

## Scenario handling

### No effective workflow

Create the minimum spine: a root instruction source, exact commands that are
actually supported, a short repository map, verification expectations, and an
explicit knowledge-gap section when necessary. Establish where material work
gets its intent and human acceptance only when no existing owned path is
discoverable. Add architecture or domain docs only when the codebase is complex
enough that the root file would become an encyclopedia.

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
repository resemble another project. Report why the existing harness is sound
and any optional improvements separately.

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
- absence of CI described as a defect solely because the scanner observed it,
  or described simultaneously as a defect and optional investment without a
  distinct consequence;
- prose-only rules where a cheap mechanical check can enforce the invariant;
- a test suite presented as proof that the underlying product intent is correct;
- a workflow in which an agent silently supplies its own acceptance or risk
  decision;
- a provider policy, Hook, Plan mode, approval, or sandbox described as enforced
  solely because its file or prompt text exists;
- universal approval tiers, deployment steps, or observability scaffolds that do
  not match the project;
- an "unknowns" document filled with low-impact questions;
- a workflow that requires Agentize to remain installed after initialization.
