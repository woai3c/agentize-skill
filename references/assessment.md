# Repository assessment

Use this reference to turn repository evidence into a bounded improvement plan.
The objective is not a maximum score. It is the smallest trustworthy harness
that lets an agent act with high autonomy and verify its work.

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

## Capability rubric

Classify every capability independently. A repository can be strong in one and
missing another.

| Capability | Sound when | Common weak signals |
| --- | --- | --- |
| Orientation | Purpose, entry points, and repository map are discoverable quickly. | README is marketing-only; maps list every folder without explaining ownership. |
| Scoped instructions | The applicable instruction file says what differs from normal agent behavior. | One giant global file; duplicate provider files; nested rules contradict parents. |
| Architecture context | Boundaries, dependencies, data flow, and important invariants are findable. | A stale diagram; directory tree presented as architecture; unwritten cross-module constraints. |
| Domain context | Non-obvious business rules and vocabulary have an owned source of truth. | Rules live only in prompts, tickets, or tests; plausible facts are guessed. |
| Verification | Fast feedback and broader confidence commands are exact and runnable. | Only "run tests"; one full-suite command for every change; green checks that do not cover user behavior. |
| Change workflow | An agent can explore, implement, test, review, and hand off without manual copy-paste. | Commands require undocumented setup; no way to reproduce CI; no diff or review expectations. |
| Feedback retention | Repeated mistakes become durable constraints or executable checks. | The same review comment recurs; instructions grow while tests and linters do not. |
| Safety and boundaries | Destructive, costly, credentialed, generated, and release paths are clear. | Blanket prohibitions; copied secrets; release commands mixed into routine verification. |
| Knowledge gaps | Unknowns are explicit, evidence-backed questions with a path to resolution. | Confident invented rules; vague TODO lists; questions with no impact or owner. |
| Maintainability | Artifacts have clear owners and update triggers and survive without Agentize. | Generated banners; timestamps that churn; duplicated facts; an external runtime is required. |

Use these statuses:

- `sound`: sufficient, current, and supported by evidence;
- `weak`: useful but missing information needed for reliable action;
- `missing`: no adequate artifact or executable path exists;
- `conflicting`: two current-looking sources disagree;
- `stale`: direct evidence disproves material content;
- `unverified`: plausible, but not yet checked.

## Scenario handling

### No effective workflow

Create the minimum spine: a root instruction source, exact commands that are
actually supported, a short repository map, verification expectations, and an
explicit knowledge-gap section when necessary. Add architecture or domain docs
only when the codebase is complex enough that the root file would become an
encyclopedia.

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
  boundaries and stronger executable checks.
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
- prose-only rules where a cheap mechanical check can enforce the invariant;
- an "unknowns" document filled with low-impact questions;
- a workflow that requires Agentize to remain installed after initialization.
