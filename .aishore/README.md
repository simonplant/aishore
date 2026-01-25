# aishore - AI Sprint Runner

A self-contained AI sprint orchestration tool for Claude Code.

Drop `.aishore/` into any project to get automated sprint execution.

## Quick Start

```bash
# Initialize
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

.aishore/aishore metrics          # Show sprint metrics
.aishore/aishore metrics --json   # Output as JSON

.aishore/aishore update           # Update from upstream
.aishore/aishore update --dry-run # Check for updates (or --check)
.aishore/aishore update --force   # Re-download even if same version

.aishore/aishore init             # Initialize in new project
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
├── CLAUDE.md                # Project context (auto-detected)
└── .aishore/                # TOOL (can be updated/replaced)
    ├── aishore              # Self-contained CLI
    ├── config.yaml          # Optional overrides
    ├── agents/              # Agent prompts
    └── data/                # Runtime (logs, status)
```

**Key insight:** Your backlogs are at project level, separate from the tool. You can safely update or replace `.aishore/` without losing your content.

## Context

aishore auto-detects `CLAUDE.md` in your project root and passes it to agents.
No configuration needed - just have a `CLAUDE.md` file.

## Configuration (Optional)

Edit `.aishore/config.yaml` only if you need to override defaults:

```yaml
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
export AISHORE_AGENT_TIMEOUT=3600
```

## Sprint Flow

```
Pick Item → Developer → Validator → Done
   ↓            ↓           ↓         ↓
backlog    implement    validate   archive
```

1. **Pick**: Select first item with `readyForSprint: true` (or specific ID)
2. **Developer**: Implements the feature
3. **Validator**: Runs validation, checks acceptance criteria
4. **Done**: Item marked complete, archived

## Completion Contract

Agents signal completion by writing to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

## Requirements

- **claude** - Claude Code CLI
- **jq** - JSON processor
- **bash** - Shell (4.4+)
- **git** - Version control

## Installation

**One-line install** (in your project directory):

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
.aishore/aishore init
cat .aishore/gitignore-entries.txt >> .gitignore
```

Or manually copy `.aishore/` directory to your project.

## Keeping Updated

```bash
.aishore/aishore update --dry-run  # Check for updates
.aishore/aishore update            # Update from upstream
```

Updates fetch the latest script and agent prompts. Your `backlog/` and `config.yaml` are never modified.

## Backlog Format

```json
{
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
