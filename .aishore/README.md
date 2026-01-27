# aishore — AI Sprint Runner

A self-contained AI sprint orchestration tool for Claude Code.

Drop `.aishore/` into any project to get automated sprint execution.

## Quick Start

```bash
# Initialize (interactive setup wizard)
.aishore/aishore init

# Add features to backlog
vim backlog/backlog.json

# Groom items for sprint
.aishore/aishore groom

# Run a sprint
.aishore/aishore run

# Run specific item by ID
.aishore/aishore run FEAT-001
```

## Commands

```bash
.aishore/aishore run [count]      # Run sprints (default: 1)
.aishore/aishore run TEST-006     # Run specific item by ID
.aishore/aishore run --auto-commit 5   # Run 5 sprints with auto-commit

.aishore/aishore groom            # Groom bugs/tech debt (Tech Lead)
.aishore/aishore groom --backlog  # Groom features (Product Owner)

.aishore/aishore review           # Architecture review (read-only)
.aishore/aishore review --update-docs  # Allow doc updates
.aishore/aishore review --since <hash> # Review since specific commit

.aishore/aishore metrics          # Show sprint metrics
.aishore/aishore metrics --json   # Output as JSON

.aishore/aishore update           # Update from upstream (checksum-verified)
.aishore/aishore update --dry-run # Check for updates (or --check)
.aishore/aishore update --force   # Re-download even if same version
.aishore/aishore update --force --no-verify  # Skip checksum verification

.aishore/aishore checksums        # Regenerate checksums.sha256
.aishore/aishore init             # Interactive setup wizard
.aishore/aishore help             # Show help
```

## Directory Structure

```
project/
├── backlog/                 # YOUR CONTENT (version controlled)
│   ├── backlog.json         # Feature backlog
│   ├── bugs.json            # Tech debt backlog
│   ├── sprint.json          # Current sprint state
│   └── archive/             # Completed sprint history
│       └── sprints.jsonl
├── CLAUDE.md                # Project context (auto-detected)
└── .aishore/                # TOOL (can be updated/replaced)
    ├── aishore              # Self-contained CLI
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── config.yaml          # Optional overrides
    ├── agents/              # Agent prompts
    └── data/                # Runtime (logs, status, lock)
```

**Key insight:** Your backlogs are at project level, separate from the tool. You can safely update or replace `.aishore/` without losing your content.

## Context

aishore auto-detects `CLAUDE.md` in your project root and passes it to agents.
No configuration needed — just have a `CLAUDE.md` file.

## Configuration (Optional)

Edit `.aishore/config.yaml` only if you need to override defaults:

```yaml
project:
  name: "my-project"

validation:
  command: "npm run type-check && npm run lint && npm test"
  timeout: 120

models:
  primary: "claude-opus-4-5-20251101"
  fast: "claude-sonnet-4-20250514"

agent:
  timeout: 3600
```

Or use environment variables:
```bash
export AISHORE_MODEL_PRIMARY="claude-opus-4-5-20251101"
export AISHORE_MODEL_FAST="claude-sonnet-4-20250514"
export AISHORE_AGENT_TIMEOUT=3600
export AISHORE_VALIDATE_CMD="npm test"
export AISHORE_VALIDATE_TIMEOUT=120
```

## Sprint Flow

```
Pick Item → Developer → Validate → Validator → Done
   ↓            ↓           ↓          ↓         ↓
backlog    implement    run tests   check AC   archive
```

1. **Pick**: Select first item with `readyForSprint: true` (or specific ID)
2. **Developer**: Implements the feature
3. **Validate**: Runs your validation command (if configured in config.yaml)
4. **Validator**: Agent checks acceptance criteria
5. **Done**: Item marked complete, archived

Failed items are skipped in subsequent picks during the same session.

## Completion Contract

Agents signal completion by writing to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

## Concurrency

Only one aishore process runs at a time. The CLI acquires a `flock`-based lock on `.aishore/data/status/.aishore.lock` before running sprints, grooming, or reviews.

## Update Integrity

The `update` command:
1. Fetches all files into a temporary staging directory
2. Fetches `checksums.sha256` from upstream
3. Verifies every file against its expected SHA-256 checksum
4. Only installs files if all checksums pass

If verification fails, no files are modified. Use `--force --no-verify` to bypass (not recommended).

## Requirements

- **claude** — Claude Code CLI
- **jq** — JSON processor
- **bash** — Shell (4.4+)
- **git** — Version control

## Installation

**One-line install** (in your project directory):

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
.aishore/aishore init
```

Or manually copy `.aishore/` directory to your project.

## Keeping Updated

```bash
.aishore/aishore update --dry-run  # Check for updates
.aishore/aishore update            # Update from upstream
```

Updates fetch the latest script and agent prompts, verified via SHA-256 checksums. Your `backlog/` and `config.yaml` are never modified.

## Backlog Format

```json
{
  "description": "Feature backlog",
  "items": [
    {
      "id": "FEAT-001",
      "title": "Add user authentication",
      "description": "Implement login/logout",
      "steps": ["Create auth service", "Add endpoint"],
      "acceptanceCriteria": ["User can log in", "Session persists"],
      "priority": "must",
      "status": "todo",
      "readyForSprint": true
    }
  ]
}
```

Items need `readyForSprint: true` to be picked. Use `groom` command to prepare items.
