# Task schema

A task is a directory `tasks/T-NNN/` on the base branch containing `task.toml` and `spec.md`, plus
acceptance tests at the paths `acceptance_tests` names (under `tests/acceptance/` by default). All of
it is human-owned. Validate with `aishore validate T-NNN`. `aishore start` refuses invalid tasks.

## task.toml

| key | type | required | rule |
|---|---|---|---|
| id | string | yes | `T-` plus 3+ digits, equal to the directory name |
| title | string | yes | non-empty |
| tier | int | yes | 1 critical path, 2 features and reporting, 3 tooling |
| kind | string | yes | feature, fix, refactor, delete, test |
| allow | list of globs | yes | non-empty; may not cover human-owned paths |
| acceptance_tests | list of paths | feature and fix | human-owned, exist, no AISHORE_PLACEHOLDER |
| loc_budget | int | no | positive; max net production LOC (default from aishore.toml) |
| max_new_files | int | no | new files under the src roots (default 1) |
| max_new_classes | int | no | new classes under the src roots (default 0) |
| replay_may_change | list of case names | no | cases allowed to differ; must be empty for refactor and delete |
| mutation_min_kill | number 0..1 | no | Python only; default by tier: 1 is 0.8, 2 is 0.6, 3 is off |
| notes | string | no | free text |

Unknown keys are errors.

## Kind rules

- feature, fix: acceptance tests must be red on the base branch at `aishore start`.
- refactor: replay identical, behavior identical, budget still applies.
- delete: net production LOC must be negative, replay identical.
- test: adds unit tests only; allow should cover the unit test paths.

## spec.md

Required sections, in any order: `## Intent`, `## Interface`, `## Acceptance`, `## Invariants`,
`## Out of scope`. No AISHORE_PLACEHOLDER line.

If you cannot write the Acceptance table or state which replay cases change, split the task.
