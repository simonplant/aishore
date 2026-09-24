# ENGINEERING.md

Engineering rules for this repository. Human-owned. Claude Code reads this file through CLAUDE.md.
A rule an agent breaks twice becomes a gate in `aishore.toml` or is deleted.

## 1. Roles

| Role | Who | Owns |
|---|---|---|
| Architect and merger | maintainer | architecture, schemas, interfaces, invariants, briefs, acceptance tests, goldens, merges |
| Implementer | Claude Code (`implement.model`), one session per task, in its worktree | code inside the task allowlist, unit tests |
| Reviewer | Claude Code headless (`review.model`), separate process, read-only | counterexamples and findings backed by tests |
| Gates | aishore | every mechanical check |

No agent merges, pushes, edits a human-owned path, or changes a gate. The reviewer uses a
different model in a fresh process, and its claims count only when a test proves them.

## 2. Human-owned paths

`ownership.locked` in `aishore.toml`: the harness and its config, this file, agent instructions,
build and dependency files, CI, `tasks/`, `docs/`, `replay/`, `tests/acceptance/`,
`tests/property/`, and the schema and interface paths listed there. Agents read them and never
write them. A task that needs one changed ends in ESCALATE.md.

## 3. Architecture rules

Project-specific. Each rule names its enforcement: a gate command, a property test, replay, or
review.

1. <module boundary>. Enforced: <import linter | review>.
2. <pure logic: time and I/O are parameters>. Enforced: <property tests | review>.
3. <types at module boundaries>. Enforced: <type checker>.
4. <source of truth for derived views>. Enforced: <replay>.
5. Errors fail closed: no swallowed exceptions, no defaults that hide a failed read. Enforced: <linter | review>.
6. A new dependency needs a decision record in `docs/adr/`. Enforced: dependency files are locked.

## 4. Implementer rules

1. One task per session. Touch only files in the task allowlist.
2. Write PLAN.md first; wait for approval.
3. Make the smallest change that passes the acceptance tests.
4. No new class or abstraction without a second caller in the same diff.
5. No refactoring, renaming, reformatting, or cleanup outside the task.
6. Reuse existing types and helpers.
7. Never weaken a gate: no skip, only, xfail, lint or type suppressions, coverage pragmas,
   loosened tolerances, or tautological assertions.
8. Unit tests assert behavior, not internals.
9. A spec that conflicts with the architecture, or two red gate runs: write ESCALATE.md and stop.

## 5. Tests and oracles

| Kind | Location | Author | Purpose |
|---|---|---|---|
| Acceptance | `tests/acceptance` | human (drafts reviewed) | defines done for a task |
| Property | `tests/property` | human | invariants that always hold |
| Replay | `replay/cases`, `replay/golden` | human | recorded inputs to golden outputs |
| Unit | project unit test location | implementer | internals the acceptance tests do not pin |
| Mutation | aishore (Python) | gate | tests constrain the changed lines |

Goldens change only through `aishore merge`, for cases in `replay_may_change`.

## 6. Tiers

| Tier | Scope | Review | Mutation kill | Human reads |
|---|---|---|---|---|
| 1 | critical path: money, data integrity, security, irreversible actions | brief, plan, diff | 80% | every line |
| 2 | features, analysis, reporting | brief, diff | 60% | diff stat, replay diff |
| 3 | tooling, formatting | gates only | off | diff stat |

## 7. Gates

Fast (Stop hook): lint, types, imports, diffcheck, tests, acceptance.
Full (merge, CI): no ESCALATE.md, fast gate, replay, mutation.

## 8. Records

`tasks/log.csv` has one row per task outcome. An escaped defect becomes a replay case or a
property test before its fix.
