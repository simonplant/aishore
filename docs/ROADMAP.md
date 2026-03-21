# Roadmap

Where aishore is, where it's going, and what's missing.

## Current Version (v0.3.x)

aishore v0.3.x is a working sprint runner that can autonomously drain a backlog:

- **Autonomous mode** — `auto done` drives the backlog to completion with priority scoping, auto-grooming, failure tracking, and circuit breaker
- **Sprint orchestration** — branch, implement, validate, commit, merge per item
- **Maturity protocol** — implement → critique → harden cycle keeps quality inside the session
- **Backlog management** — full CLI CRUD, AI-powered `backlog populate` from PRODUCT.md
- **Grooming** — tech-lead (bugs) and product-owner (features) agents
- **Architecture review** — on-demand or post-sprint with optional doc updates
- **Checksum-verified updates** — self-update from GitHub releases
- **Scope checking** — warn or fail when changes land outside declared scope
- **Testable acceptance criteria** — AC entries with `verify` shell commands

## Now

Active work in the current sprint cycle:

- Unified architecture document (`docs/ARCHITECTURE.md`)
- This roadmap (`docs/ROADMAP.md`)
- Docs consolidation — move CONTRIBUTING.md into `docs/` (CHANGELOG.md done)
- Slim README.md to storefront format (problem, solution, quickstart, links)

## Next

Committed direction for upcoming releases:

- **Doc structure enforcement** — `.doc-standard.yaml` schema for consistent documentation
- **Multi-backlog support** — work across multiple backlog files in a single sprint session
- **Retry intelligence** — smarter failure analysis to avoid repeating the same mistakes
- **PR workflow integration** — `--no-merge` already exists; tighter GitHub PR creation and review loops
- **Agent output streaming** — real-time visibility into what the developer agent is doing

## Later

Vision items — not yet committed, but where the project could go:

- **Multi-repo support** — orchestrate sprints across multiple repositories
- **CI/CD execution mode** — run aishore in headless CI pipelines (GitHub Actions, etc.)
- **Plugin system** — custom agents, custom validation steps, lifecycle hooks
- **Non-Claude agent support** — swap in other LLM backends beyond Claude Code
- **Remote execution** — trigger sprints from a web UI or API
- **Team collaboration** — shared backlogs, sprint history, and metrics across contributors

## Known Limitations

Honest constraints of the current version:

- **Claude Code dependency** — requires the `claude` CLI; no other LLM backend supported
- **Bash-only** — the entire tool is a single Bash script; no Windows support
- **macOS/Linux only** — relies on POSIX tools and `flock` for concurrency
- **Single-repo** — one backlog, one repo; no cross-repo orchestration
- **No remote/CI mode** — requires a local terminal session with Claude Code installed
- **No plugin system** — agent prompts and validation are configurable but not extensible
- **Sequential execution** — one sprint item at a time; no parallel agent runs

## Want to help?

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved.
