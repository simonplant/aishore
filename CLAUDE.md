# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aishore** is an AI Sprint Runner - a drop-in sprint orchestration tool for Claude Code that autonomously runs development sprints. It picks features from a backlog, has an AI developer implement them, validates the implementation, and archives completed work.

The tool is self-contained in `.aishore/` and designed to be copied into target projects.

## Commands

```bash
# Lint
shellcheck .aishore/aishore .aishore/lib/common.sh

# Validate JSON
jq empty .aishore/plan/*.json

# Test basic functionality
.aishore/aishore help
.aishore/aishore version
.aishore/aishore metrics
```

No build step - the tool is pure Bash.

## Architecture

**Sprint execution flow:**
```
Pick Item → Developer Agent → Validator Agent → Archive (done/failed)
```

**Key components:**
- `.aishore/aishore` - Main CLI entry point (Bash)
- `.aishore/lib/common.sh` - Shared utilities
- `.aishore/agents/*.md` - Agent prompts (developer, validator, tech-lead, architect, product-owner)
- `.aishore/plan/` - Backlog files (backlog.json, bugs.json, sprint.json)
- `.aishore/config.yaml` - Configuration (validation command, models, timeouts)
- `.aishore/data/` - Runtime data (logs, archive, status)

**Completion contract:** Agents signal completion by writing to `.aishore/data/status/result.json`:
```json
{"status": "pass", "summary": "..."}
```
The orchestrator polls for this file, then proceeds to the next step.

**Agent invocation:** The CLI invokes Claude Code via `claude --model` with agent prompt, sprint context, and project context. Agents have permissions for: `Bash(git:*)`, `Edit`, `Write`, `Read`, `Glob`, `Grep`.

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
- On macOS: `brew install coreutils` (for gtimeout)

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
