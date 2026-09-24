---
name: brief
description: Write an aishore task brief (spec.md, task.toml, acceptance tests) for one change, grounded in the code and your decisions. Use on the base branch when asked to brief, spec, or draft task T-NNN, or to turn an intent, bug report, or issue into a task.
argument-hint: T-042 <intent>
---
Arguments: $ARGUMENTS. The first token is the task id; the rest is the intent.

You draft the brief, on the base branch, for the human to approve. You implement nothing.
The brief is the only thing that tells the implementer what "right" means: every gap in it
is a defect the gates will let through.

## 1. Scaffold
If `tasks/<id>/` does not exist, run `.aishore/bin/aishore new <id> "<short title>"`.
Read ENGINEERING.md, `.aishore/aishore/scaffold/SCHEMA.md`, and `aishore.toml` (`src`,
`acceptance`, `ownership.locked`).

## 2. Ground in the code before asking anything
- Find where the change lands: the functions to change, their callers, and existing tests.
- List the types and helpers the implementation must reuse. Put them in the Interface section.
- Derive `allow` from that: the exact files to change, plus one unit test file. No directory globs
  unless a new file is needed.
- For kind `fix`: reproduce the bug first, in a scratch command, and keep the exact input that
  shows it.
- Pick the tier from ENGINEERING.md section 6 and the kind from SCHEMA.md.
If the intent needs more than one acceptance table, or more than `loc_budget` lines, or
changes an interface and its callers, stop: the task needs `/decompose`.

## 3. Ask only what the code cannot answer
Use AskUserQuestion, at most four questions per round, each with concrete options and your
recommendation first. Ask about decisions, never facts you can look up:
- behavior at each boundary (empty, zero, negative, max, duplicate, missing, concurrent)
- failure semantics: raise, return a sentinel, log and continue, or reject
- which existing invariants apply, and whether recorded behavior (replay) may change
- what is out of scope that a helpful implementer would be tempted to do
Stop asking when every row of the acceptance table has a definite expected output.

## 4. Write the brief
- `spec.md`: Intent (one or two sentences), Interface (exact typed signatures), Acceptance
  (a table of concrete inputs and expected outputs: the normal case, each boundary, each
  failure), Invariants (one line each), Out of scope.
- `task.toml`: tier, kind, the minimal `allow`, `loc_budget` sized to the change (estimate,
  then add half), `max_new_files` and `max_new_classes` at the minimum the plan needs,
  `replay_may_change` only for cases the intent changes on purpose.
- The acceptance test file in `acceptance_tests`: one test per table row, asserting observable
  behavior through the public interface, never internals. Tests must be runnable by
  `acceptance.cmd` from the repository root. For a fix, one test reproduces the bug exactly.

## 5. Prove the tests are red for the right reason
Run `acceptance.cmd` on the tests. Each must fail because the behavior is missing: a missing
symbol or a failing assertion. A syntax error, a bad import path in the test, a fixture error,
or a test that passes is a broken brief; fix it. Then run `.aishore/bin/aishore validate <id>`
and fix everything except the placeholder lines.

## 6. Hand over
Keep one `AISHORE_PLACEHOLDER` line at the top of spec.md and of the acceptance test so the
human must read both. Report: the decisions the human made, anything you assumed (each is a
question they should confirm), and the next step:
`.aishore/bin/aishore brief-review <id>` to have an independent reviewer look for wrong
implementations that would still pass these tests.
