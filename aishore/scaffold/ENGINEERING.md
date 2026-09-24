# ENGINEERING.md

The single source of engineering rules for this repository. Claude Code reads it through
CLAUDE.md, in both the implementer and reviewer sessions. Humans own it. Any rule an agent
breaks twice becomes a gate in aishore.toml or gets deleted from this file.

## 1. Roles

| Role | Who | Owns |
|---|---|---|
| Architect and merger | the maintainer | architecture, schemas, interfaces, invariants, tasks, acceptance tests, goldens, merges |
| Implementer | Claude Code (`implement.model`), one session per task, in a task worktree | code inside the task allowlist, unit tests |
| Reviewer | Claude Code headless (`review.model`), separate process, read-only tools | findings backed by failing tests |
| Gates | aishore | everything that can be checked mechanically |

No agent merges, pushes, edits human-owned paths, or changes a gate.

Implementer and reviewer can share blind spots. Two rules compensate: the reviewer runs a
different model in a fresh process that never sees the implementer's session, and a finding
counts only with a test that fails on the branch. Replay, property, and mutation gates are
model-independent and carry the rest.

## 2. Human-owned paths

Listed in `aishore.toml` under `ownership.locked`: the harness and its config, this file,
agent instructions, build and dependency files, CI, `tasks/`, `docs/`, `replay/`,
`tests/acceptance/`, `tests/property/`, and any schema or interface paths added there.
Agents read these. Agents never write them. If a task needs one changed, the agent writes
ESCALATE.md and stops.

## 3. Architecture rules

Replace this section with the rules of this system. Each rule names its enforcement: a gate
command in aishore.toml, a property test, replay, or review. Rules with no enforcement are wishes.

1. <module boundary: what may never import what>. Enforced: <import linter / review>.
2. <purity: which logic takes time and I/O as parameters>. Enforced: <property tests / review>.
3. <boundary types: what crosses a module boundary>. Enforced: <type checker>.
4. <source of truth: which store every view renders from>. Enforced: <replay>.
5. Errors fail closed: no swallowed exceptions, no defaults that hide a failed read. Enforced: <linter / review>.
6. New dependencies need a decision record in `docs/adr/`. Enforced: dependency files are human-owned.

## 4. Change rules for the implementer

1. One task per session. Touch only files in the task allowlist.
2. Plan first (PLAN.md), then wait for approval.
3. Make the smallest change that makes the acceptance tests pass.
4. No new class or abstraction without a second caller in the same diff.
5. No refactoring, renaming, reformatting, or cleanup outside the task.
6. Reuse existing types and helpers before writing new ones.
7. Never weaken a gate: no skip, only, xfail, type or lint suppressions, coverage pragmas,
   loosened tolerances, or tautological assertions.
8. Unit tests test behavior, never the implementation's internals.
9. When the spec conflicts with the architecture, or two gate runs fail, write ESCALATE.md
   and stop. Escalating is a successful outcome.

## 5. Tests and oracles

| Kind | Location | Written by | Purpose |
|---|---|---|---|
| Acceptance | tests/acceptance | human (drafts allowed, human reviews) | defines done for a task |
| Property | tests/property | human | invariants that must always hold |
| Replay | replay/cases, replay/golden | human | recorded inputs to golden event streams |
| Unit | the project's unit test location | implementer | internals the acceptance tests do not pin |
| Mutation | aishore (Python) | gate | proves tests constrain changed lines |

Goldens change only through `aishore merge` for cases listed in `replay_may_change`, after the
human has read the replay diff.

## 6. Tiers

| Tier | Scope | Review | Mutation | Human reads |
|---|---|---|---|---|
| 1 | critical path: money, data integrity, security, anything irreversible | plan review and diff review | 80% | every line |
| 2 | features, analysis, reporting | diff review | 60% | diff stat and replay diff |
| 3 | tooling, formatting | gates only | off | diff stat |

## 7. Task lifecycle

`aishore new` then the human edits spec and acceptance tests and commits on the base branch.
`aishore start` proves the acceptance tests are red and creates the worktree. The implementer
plans, gets approval, builds to green. Tier 1: `plan-review` before approval. Tier 1 and 2:
`review`, then `adopt` for findings that are real. `aishore run` does plan, approval by the
reviewer, build, and review headless. `merge` runs the full gate and asks the human.
`abandon` records an escalation.

## 8. Gates

Fast gate (Stop hook, every agent turn end once code changed): lint, types, imports, diffcheck,
tests, acceptance. Full gate (merge and CI): escalation check, fast gate, replay, mutation.
Diffcheck enforces: human-owned paths, allowlist, gate weakening, LOC budget, new files, new
classes. The acceptance step runs the tests of merged tasks and of the current task.

## 9. Records

`tasks/log.csv`: one row per task outcome with human minutes, net LOC, review results, the
gate that caught a problem, and the gate that was missing. `entropy.csv`: size and complexity
snapshots. Escaped defects become a replay case or a property test before the fix.
