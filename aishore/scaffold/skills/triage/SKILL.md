---
name: triage
description: Triage an aishore task that escalated (ESCALATE.md) or whose review produced findings - propose the spec change or split, and which proven findings to adopt. Use on the base branch when asked about an escalation, a stuck task, review findings, or what to adopt.
argument-hint: T-042
---
Task: $ARGUMENTS. You advise the human on the base branch. You change nothing in the worktree
and run no aishore command that changes state (adopt, sync, merge, abandon).

Read `tasks/<id>/spec.md`, `task.toml`, ENGINEERING.md, and whichever exist of: the worktree's
ESCALATE.md and PLAN.md (`.aishore/bin/aishore status` shows the worktree path),
`tasks/<id>/plan-review.md`, `review.md`, `findings.md`, and `brief-review.md`.

## Escalation
Classify the cause: the spec is ambiguous, the spec contradicts the architecture, the allowlist
or budget is too small for any correct change, the acceptance tests are wrong, or the task
is two tasks. Then give the fix as concrete edits: the spec lines to change, the table rows to
add, the `allow` entries or budget to change, or the split (titles, order, one-line criterion
each). End with the commands the human runs: `aishore abandon <id> "<cause>"`, then
`/brief` for the revised or split tasks.

## Findings
For each REAL finding in findings.md, read its test in review.md and decide:
- adopt: the test encodes behavior the spec, an invariant, or ENGINEERING.md requires
- reject: the test encodes the reviewer's preference, or behavior the spec leaves open
  (then say which spec line should settle it, if it matters)
- spec gap: the behavior matters but the spec is silent; propose the table row
Give a one-line reason each, citing the spec line. End with the command:
`aishore adopt <id> <numbers>`, and any spec edit to make first.
