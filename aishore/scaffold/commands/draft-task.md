---
description: Draft a task spec and acceptance test on the base branch for human editing (args: T-042 intent...)
---
Arguments: $ARGUMENTS
The first token is the task id. The rest is the intent.

You are drafting, on the base branch, for a human to review. You are not implementing.

1. If `tasks/<id>/` does not exist, run `.aishore/bin/aishore new <id> "<short title>"`.
2. Read ENGINEERING.md, `.aishore/aishore/scaffold/SCHEMA.md`, `aishore.toml`, and the code the intent touches.
3. Fill `tasks/<id>/spec.md`:
   - Intent: one or two sentences.
   - Interface: exact signatures, typed. Reuse existing types.
   - Acceptance: a table of concrete inputs and expected outputs, including edge cases and failure cases.
   - Invariants: which existing invariants apply, one line each.
   - Out of scope: what a helpful implementer would be tempted to also do.
4. Fill `tasks/<id>/task.toml`: the smallest `allow` list that can work, tier, kind, loc_budget
   sized to the change, `replay_may_change` only if the intent changes recorded behavior.
5. Write the acceptance test file named in `acceptance_tests` to implement the table exactly, runnable
   by `acceptance.cmd` in aishore.toml. Keep an `AISHORE_PLACEHOLDER` comment line at the top so the
   human must review.
6. Keep the AISHORE_PLACEHOLDER line in spec.md as well. Report what you were unsure about.
