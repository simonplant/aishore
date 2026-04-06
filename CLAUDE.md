# CLAUDE.md

## Project Overview

**aishore** is an autonomous sprint orchestration layer for Claude Code. It picks items from a backlog, has an AI developer implement them through a quality protocol, validates against intent and executable checks, and merges the result.

- Tool: `.aishore/` (Bash, no build step)
- User content: `backlog/` (backlog.json, bugs.json, sprint.json, archive/)
- Config: `.aishore/config.yaml` (optional, env vars override)

## Sprint Flow

```
Pick Item → Branch (aishore/<ID>) → Preflight (regression + baseline) → Developer Agent → Validation Command → AC Verify Commands → Validator Agent → Merge → Archive
```

Each item runs in an isolated git worktree on its own feature branch. Backlog mutations happen on the base branch after merge, never in the worktree.

## Agent Roles

| Agent | When | Permissions |
|-------|------|-------------|
| Developer | `run` | Agent,Bash,Edit,Write,Read,Glob,Grep,EnterPlanMode,ExitPlanMode |
| Validator | `run` (after dev) | Bash,Read,Glob,Grep |
| Groomer | `groom` | CLI commands |
| Architect | `scaffold`, `review` | Read,Glob,Grep (+ Edit,Write with `--update-docs`) |

## Completion Contract

Agents signal completion by writing `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "what was done"}
{"status": "fail", "reason": "what went wrong"}
```

The orchestrator polls for this file. On pass, the pipeline continues. On fail, retry logic triggers.

## Quality Model

- **Maturity protocol**: Developer runs 3 phases in one session — implement, critique (re-read all changes, verify each AC, hunt bugs), harden (run validation, fix regressions, confirm all AC met)
- **Validation sequence**: (1) validation command (test suite/linter), (2) AC verify commands, (3) Validator agent
- **Regression suite**: All verify commands from completed sprints saved to `backlog/archive/regression.jsonl`, run as pre-flight before every future sprint
- **Intent gate**: Items without `intent` (or < 20 chars) cannot enter a sprint
- **Scope**: Items can declare `scope` glob patterns — advisory, not strict

## Key Rules for Agents

- **Intent is the north star.** When steps or AC are ambiguous, follow intent.
- **Prove it runs.** Wire code to real entry points. Working code that's reachable beats tested code that's isolated.
- **No mocks or stubs** in production code unless the item explicitly requests them.
- **Stay in scope.** Implement only the assigned item. Don't fix unrelated code or add unrequested features.
- **Commit before signaling.** Always commit with a meaningful message before writing result.json.

## Commands

```bash
# Core workflow
.aishore/aishore run [N|ID|done|p0|p1|p2]  # Run sprints
.aishore/aishore groom                      # Groom backlog items
.aishore/aishore scaffold                   # Detect fragment risk
.aishore/aishore review [--update-docs]     # Architecture review
.aishore/aishore status                     # Backlog overview

# Backlog management
.aishore/aishore backlog list               # List items
.aishore/aishore backlog add --title "..." --intent "..."  # Add item
.aishore/aishore backlog show <ID>          # Full item detail
.aishore/aishore backlog edit <ID> [flags]  # Update item
.aishore/aishore backlog check <ID|--all>   # Validate readiness
.aishore/aishore backlog rm <ID>            # Remove item
.aishore/aishore backlog populate           # Populate from PRODUCT.md

# Maintenance
.aishore/aishore clean [--dry-run]          # Archive done items
.aishore/aishore update [--dry-run]         # Self-update
.aishore/aishore init [-y]                  # Setup wizard
.aishore/aishore checksums                   # Regenerate checksums
.aishore/aishore version                    # Show version
.aishore/aishore help [command]             # Help
```

## Code Style

- `set -euo pipefail` at the start
- Quote all variables: `"$var"` not `$var`
- `[[ ]]` for conditionals, not `[ ]`
- `$(command)` for substitution, not backticks
- Functions: `snake_case`, Constants: `UPPER_SNAKE_CASE`

## Dependencies

Bash 4.4+, jq, git, claude (Claude Code CLI). Optional: yq (full config.yaml support). macOS: `brew install coreutils` (for `gtimeout`).

## Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Lint & Validate

```bash
shellcheck .aishore/aishore
jq empty backlog/*.json
```

## Directory Layout

```
backlog/                    # User content (preserved across updates)
  backlog.json, bugs.json, sprint.json, DEFINITIONS.md
  archive/sprints.jsonl, archive/regression.jsonl
.aishore/                   # Tool (replaceable via update)
  aishore                   # Core orchestrator
  agents/*.md               # Agent prompts
  lib/cmd-*.sh              # Lazy-loaded command modules
  config.yaml               # Optional overrides
  data/status/result.json   # Agent completion signal
  data/logs/                # Agent output logs
```
