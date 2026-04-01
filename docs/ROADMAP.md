# Roadmap

Where aishore is, where it's going, and what's not worth building yet.

## Current (v0.5.x)

aishore ships working autonomous sprints today:

- **Full sprint lifecycle** — branch, pre-flight, develop (with maturity protocol), validate, merge, archive — per item, hands-off
- **Autonomous mode** — `run done` drains the backlog with priority scoping, auto-grooming, failure tracking, and circuit breaker
- **Intent as hard gate** — items without commander's intent don't enter sprints. Validator checks intent fulfillment, not just AC pass/fail.
- **Executable evals** — AC verify commands run real behavior checks. Regression suite compounds automatically across sprints.
- **Scaffolding detection** — architect agent identifies fragment risk before features sprint. Scaffolding items wire the skeleton first.
- **Retry with context** — failures feed back structured context (validator AC results, error logs, prior diffs). Spec refinement rewrites steps/AC as a last resort.
- **Checksum-verified updates** — self-update from GitHub releases with SHA-256 integrity checks

## Next

Things that directly improve the core loop of shipping working code:

- **Enforce maturity protocol mechanically** — the 3-phase cycle (implement, critique, harden) is currently a prompt instruction. The orchestrator should verify phases executed, not trust self-reporting. This is the biggest gap between philosophy and implementation.
- **Targeted retry context** — validator AC results with file:line references should always reach the developer on retry, not just when the validator happens to provide structured output. Make `ac_results` mandatory, not optional.
- **Regression suite management** — provide escape hatches for flaky or obsolete regression entries. Behavior evolves; the regression suite needs to evolve with it without blocking all future sprints.
- **PR workflow integration** — `--no-merge` and `--pr` exist; tighter GitHub PR creation with intent and AC summary in the PR body.
- **Agent output streaming** — real-time visibility into what the developer agent is doing during long sprints.

## Later

Direction that extends the model, not committed yet:

- **CI/CD execution mode** — run aishore in headless pipelines (GitHub Actions). Requires solving credential management and result reporting without a terminal.
- **Multi-repo orchestration** — sprint across repositories when a feature spans services. Hard problem; needs cross-repo dependency tracking.
- **Cross-session learning** — failure patterns from prior sessions informing future sprints. Currently session-local only.
- **Non-Claude agent support** — swap in other LLM backends. Worth building when a second backend is actually competitive for full-repo autonomous work.

## Not Building

Things that sound useful but conflict with the core philosophy:

- **Dashboard / web UI** — aishore is a CLI tool. A dashboard is process visualization, not working code. Use `status` and the archive.
- **Team coordination features** — shared backlogs, role assignments, approval workflows. These are project management; aishore is sprint execution.
- **Plugin system for custom agents** — agent prompts are already configurable text files. A plugin API adds abstraction without adding capability until there's a proven need.
- **Test generation** — aishore validates against intent, not coverage. Generating tests to hit a coverage number is the ceremony it exists to replace.

## Known Limitations

- Claude Code CLI is the only supported AI backend
- Bash-only, macOS/Linux only (no Windows)
- Single-repo — one backlog, one project
- No remote/headless mode — requires a terminal with Claude Code installed
- Config requires `yq` for anything beyond validation command — most settings silently ignored without it
