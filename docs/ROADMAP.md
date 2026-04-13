# Roadmap

Where aishore is, where it's going, and what's not worth building yet.

## Current (v0.5.x)

aishore ships working autonomous sprints: full sprint lifecycle (branch, develop, validate, merge, archive), autonomous batch execution with priority scoping, intent-gated quality, executable evals with a compounding regression suite, and structured retry with spec refinement. See the [changelog](CHANGELOG.md) for the complete feature history.

## Next

Things that directly improve the core loop of shipping working code:

- **Working core gate** — two-track backlog (`core` / `feature`), `CORE_CMD` verification before every pick and after every merge, heal-first queue for core regressions. Features blocked until core passes. The groomer assigns tracks; the architect generates `CORE_CMD`.
- **PR workflow integration** — `--no-merge` keeps branches for external PR creation; tighter integration possible.

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
- **Test generation** — aishore validates via synthetic transactions (verify commands that exercise the real system), not test suites. Generating mocked unit tests to hit a coverage number is the ceremony it exists to replace.

## Known Limitations

- Claude Code CLI is the only supported AI backend
- Bash-only, macOS/Linux only (no Windows)
- Single-repo — one backlog, one project
- No remote/headless mode — requires a terminal with Claude Code installed
- Config requires `yq` for full yaml support — most settings silently ignored without it
