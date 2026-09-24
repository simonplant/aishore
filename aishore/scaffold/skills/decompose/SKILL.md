---
name: decompose
description: Break a goal, feature, epic, or issue into an ordered set of small aishore tasks that each fit one brief and the budgets. Use on the base branch when asked to plan, break down, scope, or groom work into tasks.
argument-hint: <goal or issue reference>
---
Goal: $ARGUMENTS

You plan, on the base branch, for the human to approve. You implement nothing.

1. Read ENGINEERING.md, `aishore.toml` (`defaults`, `src`), `tasks/` (existing ids and
   `tasks/log.csv`), and the code the goal touches. If the goal names an issue, read it with `gh`.
2. Find the seams: which modules change, which interfaces change, which recorded behavior
   (replay cases) changes. Name the existing types and helpers to reuse.
3. Split into tasks. Each task:
   - has one acceptance table and one kind (feature, fix, refactor, delete, test)
   - fits `loc_budget`, `max_new_files`, and `max_new_classes` from `defaults`
   - touches the fewest files that can work
   - leaves the base branch green and shippable when merged alone
   Order them: preparatory refactors first (kind refactor, replay identical), then interface
   additions, then behavior changes one at a time, then deletions of what the new code replaced.
   Split out anything tier 1 (ENGINEERING.md section 6) so the critical path gets its own review.
4. Present the plan as a table: id, title, kind, tier, depends on, files, the one-line
   acceptance criterion, estimated LOC. Ask the human to approve, cut, or reorder with
   AskUserQuestion. Take out anything the goal does not need.
5. For each approved task, in order: run `.aishore/bin/aishore new <id> "<title>"` and put the
   dependency and the one-line criterion in task.toml `notes`. Do not write full briefs here.
6. Report the ids in order and the next step: run `/brief <id> <intent>` for the first task,
   then `.aishore/bin/aishore brief-review <id>`. Brief a task only after the tasks it depends
   on have merged, so it describes the code as it is.
