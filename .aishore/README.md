# aishore - AI Sprint Runner

A self-contained AI sprint orchestration tool for Claude Code.

Drop `.aishore/` into any project to get automated sprint execution.

## Quick Start

```bash
# Initialize (creates config, sets up directories)
.aishore/aishore init

# Configure validation command
# Edit .aishore/config.yaml

# Add project context
# Edit .aishore/context/project.md (or symlink to CLAUDE.md)

# Add features to backlog
# Edit .aishore/plan/backlog.json

# Groom items for sprint
.aishore/aishore groom

# Run a sprint
.aishore/aishore run
```

## Commands

```bash
.aishore/aishore run [count]      # Run sprints (default: 1)
.aishore/aishore run --auto-commit 5   # Run 5 sprints with auto-commit

.aishore/aishore groom            # Groom bugs/tech debt (Tech Lead)
.aishore/aishore groom --backlog  # Groom features (Product Owner)

.aishore/aishore review           # Architecture review (read-only)
.aishore/aishore review --update-docs  # Allow doc updates

.aishore/aishore metrics          # Show sprint metrics
.aishore/aishore metrics --json   # Output as JSON

.aishore/aishore init             # Initialize in new project
.aishore/aishore help             # Show help
```

## Directory Structure

```
.aishore/
├── aishore              # CLI entry point
├── config.yaml          # All configuration
├── context/
│   └── project.md       # Project conventions (read by agents)
├── agents/
│   ├── developer.md     # Implements features
│   ├── validator.md     # Validates implementations
│   ├── tech-lead.md     # Grooms bugs, marks ready
│   ├── architect.md     # Architecture reviews
│   └── product-owner.md # Product direction
├── plan/
│   ├── backlog.json     # Feature backlog
│   ├── bugs.json        # Tech debt backlog
│   ├── icebox.json      # Future ideas
│   ├── sprint.json      # Current sprint state
│   └── definitions.md   # DoR, DoD, sizing
├── data/
│   ├── archive/         # Sprint history (sprints.jsonl)
│   ├── logs/            # Agent execution logs
│   └── status/          # Agent completion signals
└── lib/
    └── common.sh        # Shared utilities
```

## Configuration

Edit `.aishore/config.yaml`:

```yaml
validation:
  command: "npm run type-check && npm run lint && npm test"
  timeout: 120

models:
  primary: "claude-opus-4-5-20251101"
  fast: "claude-sonnet-4-20250514"

context:
  project: "context/project.md"
```

## Sprint Flow

```
Pick Item → Developer → Validator → Done
   ↓            ↓           ↓         ↓
backlog    implement    validate   archive
```

1. **Pick**: Select first item with `readyForSprint: true`
2. **Developer**: Implements the feature
3. **Validator**: Runs validation, checks acceptance criteria
4. **Done**: Item marked complete, archived

## Completion Contract

Agents signal completion by writing to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

or

```json
{"status": "fail", "reason": "tests failing in module Y"}
```

## Requirements

- **claude** - Claude Code CLI
- **jq** - JSON processor
- **bash** - Shell (4.4+)
- **git** - Version control

## Installation

Copy `.aishore/` directory to your project root:

```bash
# Copy the directory
cp -r .aishore /path/to/your/project/

# Add gitignore entries to your project
cat .aishore/gitignore-entries.txt >> /path/to/your/project/.gitignore

# Initialize
cd /path/to/your/project
.aishore/aishore init
```

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
