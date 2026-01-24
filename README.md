# aishore

**AI Sprint Runner** - Drop-in sprint orchestration for Claude Code.

## Installation

**Copy only the `.aishore/` directory** to your target project:

```bash
# From this repository
cp -r .aishore /path/to/your/project/

# Add gitignore entries to your project's .gitignore
cat .aishore/gitignore-entries.txt >> /path/to/your/project/.gitignore
```

> **Note:** Do NOT copy the root-level files (README.md, LICENSE, etc.) - those are for this repository only. The `.aishore/` directory is self-contained.

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

After copying `.aishore/` to your project:

```bash
cd /path/to/your/project

# Initialize
.aishore/aishore init

# Configure validation command for your stack
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

## Repository Structure

```
aishore/                    ← This repository
├── .aishore/               ← COPY THIS to target projects
│   ├── aishore             # CLI
│   ├── config.yaml         # Settings (customize)
│   ├── context/            # Project docs (you provide)
│   ├── agents/             # AI agent prompts
│   ├── plan/               # Backlogs
│   ├── data/               # Runtime (logs, archive)
│   └── lib/                # Utilities
├── README.md               ← You are here (don't copy)
├── LICENSE                 ← Tool license (don't copy)
├── CHANGELOG.md            ← Version history (don't copy)
├── CONTRIBUTING.md         ← For contributors (don't copy)
└── migrate.sh              ← Migration helper (don't copy)
```

## How It Works

Agents communicate via a simple completion contract. When done, they write to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

The orchestrator waits for this file, then proceeds to the next step.

## License

Proprietary - All Rights Reserved. See [LICENSE](LICENSE).
