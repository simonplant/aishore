# aishore

**AI Sprint Runner** - Drop-in sprint orchestration for Claude Code.

## Installation

**One-line install** (in your project directory):

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
```

Then initialize:

```bash
.aishore/aishore init
cat .aishore/gitignore-entries.txt >> .gitignore
```

<details>
<summary>Manual installation</summary>

Copy only the `.aishore/` directory to your target project:

```bash
cp -r /path/to/aishore/.aishore /path/to/your/project/
cd /path/to/your/project && .aishore/aishore init
cat .aishore/gitignore-entries.txt >> .gitignore
```

</details>

### Migrating from older versions

If you have an existing aishore installation with the old structure:

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash -s -- --migrate
```

## What It Does

aishore runs sprints autonomously:

1. **Picks** the next ready item from your backlog (or a specific ID)
2. **Developer agent** implements the feature
3. **Validator agent** runs tests and checks acceptance criteria
4. **Archives** completed work

```
Pick Item → Developer → Validator → Done
```

## Quick Start

```bash
cd /path/to/your/project

# Initialize (creates backlog/ directory)
.aishore/aishore init

# Add features to backlog
vim backlog/backlog.json

# Groom items (marks them ready)
.aishore/aishore groom

# Run a sprint
.aishore/aishore run

# Or run a specific item
.aishore/aishore run FEAT-001
```

aishore auto-detects `CLAUDE.md` in your project root - no configuration needed.

## Commands

| Command | Description |
|---------|-------------|
| `run [N]` | Run N sprints (default: 1) |
| `run <ID>` | Run specific item by ID (e.g., TEST-006) |
| `run --auto-commit` | Auto-commit after each sprint |
| `groom` | Groom bugs/tech debt (Tech Lead) |
| `groom --backlog` | Groom features (Product Owner) |
| `review` | Architecture review |
| `metrics` | Show sprint metrics |
| `update` | Update aishore from upstream |
| `init` | Initialize in new project |

## Project Structure

```
your-project/
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

**Key design:** Your backlogs (`backlog/`) are separate from the tool (`.aishore/`). You can safely update or replace `.aishore/` without losing your content.

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

Or use environment variables: `AISHORE_MODEL_PRIMARY`, `AISHORE_MODEL_FAST`, `AISHORE_AGENT_TIMEOUT`

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/claude-code) (`claude` command)
- `jq` - JSON processor
- `bash` 4.4+
- `git`

## Keeping Updated

```bash
.aishore/aishore update --dry-run  # Check for updates
.aishore/aishore update            # Update from upstream
```

Updates fetch the latest script and agent prompts. Your `backlog/` and `config.yaml` are never modified.

## How It Works

Agents communicate via a simple completion contract. When done, they write to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

The orchestrator waits for this file, then proceeds to the next step.

## License

Proprietary - All Rights Reserved. See [LICENSE](LICENSE).
