# Roadmap

Where aishore is, where it's going, and what's not worth building yet.

## Current (v0.5.x)

aishore ships working autonomous sprints today:

- **Full sprint lifecycle** — branch, pre-flight, develop (with maturity protocol), validate, merge, archive — per item, hands-off
- **Autonomous mode** — `run done` drains the backlog with priority scoping, auto-grooming, failure tracking, and circuit breaker
- **Intent as hard gate** — items without commander's intent don't enter sprints. Validator checks intent fulfillment, not just AC pass/fail.
- **Executable evals** — AC verify commands run real behavior checks. Regression suite compounds automatically across sprints.
- **Scaffolding detection** — architect agent identifies fragment risk before features sprint. Scaffolding items wire the skeleton first.
- **Retry with structured context** — failures feed back file:line references from validator AC results. Retry cap increased to 4000 chars with compact summaries preserved on truncation. Spec refinement rewrites steps/AC as a last resort.
- **Maturity protocol enforcement** — `check_result("developer")` rejects pass results missing `.phases` evidence. Developer must prove critique findings and harden verification counts.
- **Mandatory validator ac_results** — validator must include structured per-AC results (ac_index, met, issue, file, line). Warning on degraded retry when missing.
- **AC verify deduplication** — developer runs verify commands for feedback, orchestrator runs authoritatively, validator trusts results and focuses on intent and integration.
- **Integration enforcement** — disconnected code is a hard failure when item has verify commands, advisory for scaffolding items.
- **Scope enforcement** — post-commit warning when files modified outside declared scope globs.
- **Regression suite management** — `clean --regression` with backup, `regression-skip.json` to skip flaky entries by item ID.
- **Agent output streaming** — real-time visibility into what the developer agent is doing during long sprints.
- **Checksum-verified updates** — self-update from GitHub releases with SHA-256 integrity checks

## Next

Things that directly improve the core loop of shipping working code:

- **PR workflow integration** — `--no-merge` and `--pr` exist; tighter GitHub PR creation with intent and AC summary in the PR body.

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
