# aishore

**AI Sprint Runner** - Drop-in sprint orchestration for Claude Code.

Copy `.aishore/` into any project to get automated feature development with AI agents.

## What It Does

aishore runs sprints autonomously:

1. **Picks** the next ready item from your backlog
2. **Developer agent** implements the feature
3. **Validator agent** runs tests and checks acceptance criteria
4. **Archives** completed work

```
Pick Item → Developer → Validator → Done
```

## Quick Start

```bash
# Copy to your project
cp -r .aishore /path/to/your/project/
cd /path/to/your/project

# Initialize
.aishore/aishore init

# Configure (edit validation command for your stack)
vim .aishore/config.yaml

# Add your project context
ln -sf ../CLAUDE.md .aishore/context/project.md

# Add features to backlog
vim .aishore/plan/backlog.json

# Groom items (marks them ready)
.aishore/aishore groom

# Run a sprint
.aishore/aishore run
```

## Commands

| Command | Description |
|---------|-------------|
| `run [N]` | Run N sprints (default: 1) |
| `run --auto-commit` | Auto-commit after each sprint |
| `groom` | Groom bugs/tech debt (Tech Lead) |
| `groom --backlog` | Groom features (Product Owner) |
| `review` | Architecture review |
| `metrics` | Show sprint metrics |
| `init` | Initialize in new project |

## Configuration

Edit `.aishore/config.yaml`:

```yaml
validation:
  command: "npm run type-check && npm run lint && npm test"
  timeout: 120

models:
  primary: "claude-opus-4-5-20251101"
  fast: "claude-sonnet-4-20250514"
```

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/claude-code) (`claude` command)
- `jq` - JSON processor
- `bash` 4.4+
- `git`

## Structure

```
.aishore/
├── aishore           # CLI
├── config.yaml       # Settings
├── context/          # Project docs (you provide)
├── agents/           # AI agent prompts
├── plan/             # Backlogs
├── data/             # Runtime (logs, archive)
└── lib/              # Utilities
```

## How It Works

Agents communicate via a simple completion contract. When done, they write to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

The orchestrator waits for this file, then proceeds to the next step.

## License

Proprietary - All Rights Reserved. See [LICENSE](LICENSE).
