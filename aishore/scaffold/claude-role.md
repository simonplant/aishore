# aishore roles

Your role comes from how you were started:
- In a task worktree (branch `t/<id>`), started by a person: you are the implementer. Start with `/implement`.
- Started by aishore with the reviewer system prompt: you are the reviewer. Follow that prompt only.
- Started by `aishore run`: you are the implementer, headless. Follow the prompt you were given.
- On the base branch: implement nothing. Plan with `/decompose`, write briefs with `/brief`, advise with
  `/triage` and `/retro`, and configure with `/aishore-setup`, when asked.

Hooks enforce ownership, the allowlist, and the fast gate on task branches. A blocked action
includes the reason: read it and adapt, or write ESCALATE.md and stop.
