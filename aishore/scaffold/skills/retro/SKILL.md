---
name: retro
description: Review aishore task outcomes and propose the next gate, rule deletions, and budget changes. Use when asked for a retro, weekly review, how the harness is doing, or what to improve in the process.
---
You analyze on the base branch and propose edits; the human decides.

1. Read `tasks/log.csv`, every `tasks/*/escalations/*.md`, `findings.md`, `plan-review.md`, and
   `brief-review.md`, ENGINEERING.md, `aishore.toml`, and `entropy.csv` if present.
2. Report the numbers, each with its sample size: tasks by outcome, median human minutes, net LOC
   per task, escalation rate, REAL vs discarded findings, and which gates caught problems.
3. Find the patterns:
   - `missing_gate` named more than once: propose the gate (a command, a diffcheck pattern, a
     property test, or a replay case) that would have caught it.
   - escalations with the same cause: propose the brief or spec change that prevents it.
   - findings adopted often for the same kind of defect: propose an acceptance table row or an
     ENGINEERING.md rule, with its enforcement.
   - ENGINEERING.md rules that no outcome touched and no gate enforces: propose deleting them.
   - budgets that tasks hit or never approach: propose new `defaults`.
   - rising LOC or complexity in entropy.csv: propose a `kind = "delete"` task.
4. Give each proposal as a concrete edit (file, lines) with the evidence rows. Change no file
   unless the human approves.
