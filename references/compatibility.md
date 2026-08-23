# Agent and automation compatibility

Read this reference only when the repository targets multiple coding agents or
already contains provider-specific instructions, skills, hooks, or agent
configuration.

## Choose an instruction authority

Inventory all recognized instruction sources and determine which tools consume
them before editing:

- neutral or shared files such as `AGENTS.md`;
- provider files such as `CLAUDE.md` and `GEMINI.md`;
- nested instruction files;
- editor rules, prompt files, and repository-local skills;
- configuration that injects other files into model context.

Use the established working source as authority when it is clear. For a new
tool-neutral repository, `AGENTS.md` is a reasonable default. Do not rename a
working provider file solely for uniformity.

When several tools must receive the same base policy, prefer a verified import,
include, or symlink mechanism supported by the repository and target platforms.
Otherwise keep a short provider file that points to the canonical source and
contains only provider-specific deltas. Do not assume that a plain filename in
a file body acts as an include; verify the tool's syntax. Consider Windows and
archive behavior before introducing symlinks.

Build a small conflict table when sources overlap. Resolve identical guidance
to one owner, preserve true provider differences, and remove a duplicate only
after proving no tool depends on its current contents.

## Skills, prompts, and commands

Use a repository-local skill for a recognizable, repeated workflow with its own
trigger and success criteria. Use a prompt or command for a lightweight manual
shortcut. Keep general project facts in repository instructions or maintained
docs, not inside every skill.

Discovery paths and frontmatter rules vary by agent. Install or mirror a skill
only in paths documented for the tools the repository actually uses. If one
canonical skill is exposed through several paths, verify updates cannot diverge
and document the source of truth.

Split a large skill when workflows have different triggers, permissions, or
definitions of done. Keep deterministic parsing and repeated transformations
in scripts; keep judgment and repository adaptation in instructions.

## Hooks and rules

Hooks and command policies are enforcement surfaces, not general workflow
documents. Add them only when all of the following are true:

- the event or command boundary is stable and documented for the target tool;
- the handler is deterministic, bounded, and locally testable;
- failure behavior is explicit and does not strand normal development;
- the repository can review and trust the hook source;
- an ordinary test, lint rule, task runner, or CI check would not be simpler.

Keep security approval rules separate from coding conventions. Never weaken a
user or organization policy to make an automated workflow smoother.

## CI and orchestration

CI is appropriate for reproducible gates that must protect shared branches.
Before adding or changing it, prove the underlying local command, understand
credentials and platform requirements, and reuse existing workflow conventions.

Parallel agents and worktrees improve throughput only after tasks are separable
and verification is reliable. Document repository-specific worktree setup or
shared-resource hazards when they exist. Do not prescribe a fixed number of
agents or introduce orchestration infrastructure during ordinary bootstrap.

## Choosing a larger product surface

Keep Agentize as a skill plus local scanner while existing model tools can
inspect and edit the repository. Escalate only for demonstrated needs:

| Need | Appropriate surface |
| --- | --- |
| Repeatable judgment and file adaptation | Skill |
| Deterministic inventory or transformation | Local script or CLI |
| Installable bundle of related skills/configuration | Plugin |
| Private live data, authentication, or controlled remote action | MCP server or connector |
| Mandatory lifecycle enforcement | Hook, rule, task runner, or CI gate |
| Scheduled or durable recurring execution | Automation or orchestration service |

Do not add an MCP server for local files, a plugin for one unpublished skill,
or a runtime service for a one-time repository migration.
