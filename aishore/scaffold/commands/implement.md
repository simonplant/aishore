---
description: Implement the task for this worktree (plan first, then build to green)
---
You are the implementer for one task. Follow these steps exactly.

1. Run `git branch --show-current`. The task id is the branch name without `t/`.
2. Read ENGINEERING.md, `tasks/<id>/spec.md`, `tasks/<id>/task.toml`, every file listed in `allow`,
   and every file in `acceptance_tests`. The acceptance tests define done. You cannot edit them.
3. Write PLAN.md with exactly these sections, then stop and wait for approval:
   ## Add            files, functions, classes (classes need a second caller in this diff)
   ## Change         existing functions and what changes in each
   ## Delete         code this task makes unnecessary
   ## Leave alone    nearby code you will not touch, and why it is tempting
   ## Replay         copy `replay_may_change` from task.toml, or "identical"
   ## Size           estimated net production LOC against `loc_budget`
   ## Risks          what could break, and which test covers it
   Do not edit any other file before approval.
4. After approval, implement the plan and nothing else. If the plan must change, stop and say what and why.
5. Write unit tests only for behavior the acceptance tests do not already pin down, in allowlisted paths.
6. Run `.aishore/bin/aishore gate fast`. Fix failures. After two red runs, write ESCALATE.md
   (what fails, what you tried, what in the spec or architecture would need to change) and stop.
7. Finish with: files changed, net production LOC vs budget, and any spec requirement you could not verify.
