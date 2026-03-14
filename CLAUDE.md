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
.aishore/aishore backlog list       # List all items
.aishore/aishore backlog add        # Add item (interactive or with flags)
.aishore/aishore backlog show <ID>  # Show full detail of one item
.aishore/aishore backlog edit <ID>  # Update fields on an item
.aishore/aishore backlog rm <ID>    # Remove an item
.aishore/aishore run [N]            # Run N sprints (branch, commit, merge, push per item)
.aishore/aishore run <ID>           # Run specific item (e.g., FEAT-001)
.aishore/aishore run --dry-run      # Preview without running agents
.aishore/aishore run --no-merge     # Keep feature branches for PR review
.aishore/aishore run --retries N    # Allow N retries on validation failure
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
.aishore/aishore update             # Update from upstream (checksum-verified)
.aishore/aishore update --dry-run   # Check for updates without applying
.aishore/aishore checksums          # Regenerate checksums after editing .aishore/ files
.aishore/aishore version            # Show version
.aishore/aishore help               # Show usage
```

No build step — the tool is pure Bash.

## Architecture

**Sprint execution flow:**
```
Pick Item → Create Branch (aishore/<ID>) → Developer Agent → Validation Command → Validator Agent → Commit → Merge → Archive
```

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

**Agent invocation:** All agent invocations go through `run_agent()`, which assembles the prompt, appends the completion contract, and delegates to `run_agent_process()`. Permissions vary by role: developer gets `Bash(git:*),Edit,Write,Read,Glob,Grep`; validator gets `Bash(git:*),Read,Glob,Grep`; reviewer gets `Read,Glob,Grep` (or with `Edit,Write` when `--update-docs` is used). Permissions are configurable in `config.yaml`.

**Concurrency:** Only one aishore process runs at a time, enforced via `flock` on `.aishore/data/status/.aishore.lock`.

**Safe failure recovery:** Pre-existing uncommitted changes are stashed before sprints and restored afterward. Sprint failures delete the feature branch and return to the base branch cleanly. The developer agent commits directly; the orchestrator has a safety net commit if the agent misses it.

**Configuration precedence:** env vars > config.yaml > built-in defaults.

**Update integrity:** The `update` command fetches the remote `.aishore/VERSION` for comparison, then stages all files into a temp directory, verifies SHA-256 checksums against `checksums.sha256`, and only installs if all files pass verification.

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
