# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aishore** is an AI Sprint Runner — a drop-in sprint orchestration tool for Claude Code that autonomously runs development sprints. It picks features from a backlog, has an AI developer implement them, validates the implementation, and archives completed work.

The tool is self-contained in `.aishore/` and user content lives in `backlog/` at project level.

## Commands

```bash
# Lint
shellcheck .aishore/aishore

# Validate JSON
jq empty backlog/*.json

# Test basic functionality
.aishore/aishore help
.aishore/aishore version
.aishore/aishore metrics
```

No build step — the tool is pure Bash.

## Architecture

**Sprint execution flow:**
```
Pick Item → Developer Agent → Validation Command → Validator Agent → Archive
```

**Directory structure:**
```
project/
├── backlog/                 # User content (never touched by update)
│   ├── backlog.json
│   ├── bugs.json
│   ├── sprint.json
│   └── archive/
│       └── sprints.jsonl
└── .aishore/                # Tool (can be updated)
    ├── aishore              # Self-contained CLI (~1340 lines)
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

**Context auto-detection:** aishore automatically finds and uses `CLAUDE.md` from the project root.

**Agent invocation:** The CLI invokes Claude Code via `claude --model` with agent prompt, sprint context, and CLAUDE.md. Agents have permissions for: `Bash(git:*)`, `Edit`, `Write`, `Read`, `Glob`, `Grep`.

**Concurrency:** Only one aishore process runs at a time, enforced via `flock` on `.aishore/data/status/.aishore.lock`.

**Update integrity:** The `update` command fetches files into a staging directory, verifies SHA-256 checksums against `checksums.sha256`, and only installs if all files pass verification.

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
