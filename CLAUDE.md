# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aishore** is an AI Sprint Runner — a drop-in sprint orchestration tool for Claude Code that autonomously runs development sprints. It picks features from a backlog, has an AI developer implement them, validates the implementation, and archives completed work.

The tool is self-contained in `.aishore/` and user content lives in `backlog/` at project level.

## Commands

```bash
# Lint & validate
shellcheck .aishore/aishore
jq empty backlog/*.json

# CLI commands
.aishore/aishore init               # Interactive setup wizard
.aishore/aishore init -y            # Non-interactive (accept detected defaults)
.aishore/aishore backlog list       # List all items
.aishore/aishore backlog add        # Add item with flags
.aishore/aishore backlog show <ID>  # Show full detail of one item
.aishore/aishore backlog edit <ID>  # Update fields on an item
.aishore/aishore backlog check <ID> # Check readiness gates for an item
.aishore/aishore backlog rm <ID>    # Remove an item (--force to skip confirmation)
.aishore/aishore backlog history    # List completed sprint items
.aishore/aishore backlog populate   # AI-populate backlog from PRODUCT.md
.aishore/aishore auto done           # Autonomous: drain entire backlog
.aishore/aishore auto p0             # Autonomous: complete all must items
.aishore/aishore auto p1             # Autonomous: complete all must + should items
.aishore/aishore auto p2             # Autonomous: complete all must + should + could items
.aishore/aishore auto done --retries 2        # With per-item retries
.aishore/aishore auto p1 --max-failures 3     # Custom circuit breaker
.aishore/aishore auto done --limit 3           # Cap session at 3 items
.aishore/aishore auto done --no-merge         # Keep feature branches for PR review
.aishore/aishore auto p1 --refine            # Refine spec on failure and retry
.aishore/aishore auto done --quick            # Skip maturity protocol
.aishore/aishore auto done --auto-review     # Auto-run architecture review on completion
.aishore/aishore auto done --dry-run          # Preview first item without running
.aishore/aishore run [N]            # Run N sprints (branch, commit, merge, push per item)
.aishore/aishore run <ID>           # Run specific item (e.g., FEAT-001)
.aishore/aishore run --dry-run      # Preview without running agents
.aishore/aishore run --no-merge     # Keep feature branches for PR review
.aishore/aishore run --retries N    # Allow N retries on validation failure
.aishore/aishore run --refine       # Refine spec on failure and retry once more
.aishore/aishore run --quick        # Skip maturity protocol (fast iteration)
.aishore/aishore groom              # Tech lead: groom bugs
.aishore/aishore groom --backlog    # Product owner: groom features
.aishore/aishore review             # Architecture review
.aishore/aishore review --update-docs          # Review and update docs
.aishore/aishore review --since <commit>       # Review changes since commit
.aishore/aishore metrics            # Sprint metrics
.aishore/aishore metrics --json     # Metrics as JSON
.aishore/aishore clean              # Remove done items from backlogs
.aishore/aishore clean --dry-run    # Show what would be removed
.aishore/aishore status             # Show backlog overview and sprint readiness
.aishore/aishore status --watch    # Live refresh until sprint completes
.aishore/aishore update             # Update from upstream (checksum-verified)
.aishore/aishore update --dry-run   # Check for updates without applying
.aishore/aishore update --force     # Update even if already on latest
.aishore/aishore diagnose            # Show last sprint failure diagnostics
.aishore/aishore checksums          # Regenerate checksums after editing .aishore/ files
.aishore/aishore version            # Show version
.aishore/aishore help               # Show usage
```

No build step — the tool is pure Bash.

## Architecture

**Sprint execution flow:**
```
Pick Item → Create Branch (aishore/<ID>) → Developer Agent (with maturity protocol) → Validation Command → Validator Agent → Commit → Merge → Archive
```

**Maturity protocol:** By default, the developer agent runs a 3-phase cycle within a single session: (1) Implement — write the code, (2) Critique — shift to reviewer mindset, re-read all changes, verify each AC, hunt bugs/edge cases, fix everything found, (3) Harden — run full validation again, fix regressions, confirm all AC provably met. This keeps quality iteration inside the session where context is hot, rather than relying on external retry loops. Disable with `--quick` flag or `maturity.enabled: false` in config. Env var: `AISHORE_MATURITY`.

**Autonomous mode (`auto` command):** `auto <scope>` wraps the sprint loop with: priority-scoped item selection (p0/p1/p2/done), auto-grooming when ready items drop below threshold, session failure tracking passed to subsequent developer agents, and a circuit breaker that stops after N consecutive failures. `cmd_auto()` validates the scope and delegates to `cmd_run` via an internal `--_auto` flag — all sprint logic lives in one place.

**Git branching model:** Each sprint item runs on its own feature branch (`aishore/<ITEM-ID>`), created from the current branch. The developer agent commits its own work. On success, the branch is merged back with `--no-ff`, pushed, and the base branch pulls latest before the next item. On failure, the branch is deleted. Use `--no-merge` to keep branches for PR review (they get pushed to origin instead).

**Directory structure:**
```
project/
├── backlog/                 # User content (never touched by update)
│   ├── backlog.json
│   ├── bugs.json
│   ├── sprint.json
│   ├── DEFINITIONS.md       # DoR, DoD, priority/size definitions
│   └── archive/
│       └── sprints.jsonl
└── .aishore/                # Tool (can be updated)
    ├── aishore              # Single-file CLI (Bash)
    ├── VERSION              # Version (single source of truth)
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── agents/*.md          # Agent prompts
    ├── config.yaml          # Optional overrides
    └── data/                # Runtime (logs, status)
        ├── logs/
        └── status/
            ├── result.json      # Agent completion signal
            ├── .item_source     # Tracks which backlog file the current item came from
            └── .aishore.lock    # flock-based concurrency guard
```

**Completion contract:** Agents signal completion by writing to `.aishore/data/status/result.json`:
```json
{"status": "pass", "summary": "..."}
```
The orchestrator polls for this file, then proceeds to the next step.

**Context auto-detection:** aishore automatically finds and uses `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` from the project root (or `docs/` directory) as agent context.

**Agent invocation:** All agent invocations go through `run_agent()`, which assembles the prompt, appends the completion contract (and validation command hint for developers), and delegates to `run_agent_process()`. Permissions vary by role: developer gets `Bash,Edit,Write,Read,Glob,Grep`; validator gets `Bash,Read,Write,Glob,Grep`; reviewer gets `Read,Glob,Grep` (or with `Edit,Write` when `--update-docs` is used). Permissions are configurable in `config.yaml`.

**Concurrency:** Only one aishore process runs at a time, enforced via `flock` on `.aishore/data/status/.aishore.lock`.

**Safe failure recovery:** Pre-existing uncommitted changes are stashed before sprints and restored afterward. Sprint failures delete the feature branch and return to the base branch cleanly. The developer agent commits directly; the orchestrator has a safety net commit if the agent misses it.

**Scope checking:** Items can have a `scope` array of glob patterns (e.g., `["src/**", "tests/**"]`). After the developer agent runs, changed files are checked against scope. `scope.mode: warn` (default) logs warnings; `scope.mode: strict` fails the sprint. Configure in `config.yaml` or `AISHORE_SCOPE_MODE` env var.

**Testable acceptance criteria:** AC entries can be plain strings or `{text, verify}` objects. The `verify` field is a shell command run after validation; failures trigger retries. Use `--ac "text" --ac-verify "command"` in `backlog add`/`backlog edit`.

**Readiness gates:** `backlog check <ID>` validates an item has a title, commander's intent (>=20 chars, must be a directive not a label), steps, acceptance criteria, and no too-short steps. `backlog edit <ID> --ready` warns on gate failures but doesn't block. **Intent is a hard gate at sprint time** — items without intent (or with intent <20 chars) are silently skipped by auto-pick and explicitly rejected when run by ID.

**Baseline pre-flight:** Before the developer agent runs, the validation command is executed on the current codebase. If baseline fails, the sprint is aborted immediately.

**Spec refinement:** `run --refine` uses an AI agent to refine the spec (steps + AC) when all retries are exhausted, then attempts one more developer cycle.

**Configuration precedence:** env vars > config.yaml > built-in defaults.

**Update integrity:** Both `install.sh` and `cmd_update()` resolve the latest GitHub release tag via the API, then fetch files from that tagged snapshot (falling back to `main` if no release exists). The file list is discovered dynamically from the remote `checksums.sha256` manifest. All paths are validated (must start with `.aishore/`, no `..` traversal, no absolute paths) and `config.yaml` is explicitly skipped to protect user config. Files are staged to a temp directory, verified against SHA-256 checksums, and only installed if all checks pass. Adding a new distributable file requires only dropping the file and running `aishore checksums`.

**Version management:** `.aishore/VERSION` is the single source of truth. The CLI reads it at runtime.

## Code Style

- Use `set -euo pipefail` at the start
- Quote all variables: `"$var"` not `$var`
- Use `[[ ]]` for conditionals, not `[ ]`
- Use `$(command)` not backticks
- Functions: `snake_case`, Constants: `UPPER_SNAKE_CASE`

## Dependencies

- Bash 4.4+
- jq
- git
- claude (Claude Code CLI)
- On macOS: `brew install coreutils` (for `gtimeout`)

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Sprint Orchestration (aishore)

AI sprint runner. Backlog lives in `backlog/`, tool lives in `.aishore/`. Run `.aishore/aishore help` for full usage.

```bash
.aishore/aishore run [N|ID]         # Run sprints (branch, commit, merge, push per item)
.aishore/aishore groom [--backlog]  # Groom bugs or features
.aishore/aishore review             # Architecture review
.aishore/aishore status             # Backlog overview
```

After modifying `.aishore/` files, run `.aishore/aishore checksums` before committing.
