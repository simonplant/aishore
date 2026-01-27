# aishore

**AI Sprint Runner** — Drop-in sprint orchestration for Claude Code.

## Installation

**One-line install** (in your project directory):

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
```

Then run the setup wizard:

```bash
.aishore/aishore init
```

The wizard checks prerequisites (git, claude, jq), detects your project type, configures validation, and sets up `backlog/` and `.gitignore`.

<details>
<summary>Manual installation</summary>

Copy only the `.aishore/` directory to your target project:

```bash
cp -r /path/to/aishore/.aishore /path/to/your/project/
cd /path/to/your/project && .aishore/aishore init
```

</details>

### Migrating from older versions

If you have an existing aishore installation with the old structure (`.aishore/plan/` or `aishore/`):

```bash
# Preview what would change (no modifications)
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/migrate.sh | bash -s -- --dry-run .

# Apply migration
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/migrate.sh | bash -s -- .
```

## What It Does

aishore runs sprints autonomously:

1. **Picks** the next ready item from your backlog (or a specific ID)
2. **Developer agent** implements the feature
3. **Validation command** runs your test suite (if configured)
4. **Validator agent** checks acceptance criteria
5. **Archives** completed work

```
Pick Item → Developer → Validate → Validator → Done
```

## Quick Start

```bash
cd /path/to/your/project

# Initialize (interactive setup wizard)
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

aishore auto-detects `CLAUDE.md` in your project root — no configuration needed.

## Commands

| Command | Description |
|---------|-------------|
| `run [N]` | Run N sprints (default: 1) |
| `run <ID>` | Run specific item by ID (e.g., FEAT-001) |
| `run --auto-commit` | Auto-commit after each sprint |
| `groom` | Groom bugs/tech debt (Tech Lead) |
| `groom --backlog` | Groom features (Product Owner) |
| `review` | Architecture review |
| `review --update-docs` | Architecture review with doc updates |
| `metrics` | Show sprint metrics |
| `metrics --json` | Metrics as JSON |
| `update` | Update aishore from upstream (checksum-verified) |
| `update --dry-run` | Check for updates without applying |
| `update --force --no-verify` | Force update, skip checksum verification |
| `checksums` | Regenerate `checksums.sha256` |
| `init` | Interactive setup wizard |

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
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── config.yaml          # Optional overrides
    ├── agents/              # Agent prompts
    └── data/                # Runtime (logs, status)
```

**Key design:** Your backlogs (`backlog/`) are separate from the tool (`.aishore/`). You can safely update or replace `.aishore/` without losing your content.

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

Or use environment variables: `AISHORE_MODEL_PRIMARY`, `AISHORE_MODEL_FAST`, `AISHORE_AGENT_TIMEOUT`, `AISHORE_VALIDATE_CMD`, `AISHORE_VALIDATE_TIMEOUT`

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude` command)
- `jq` — JSON processor
- `bash` 4.4+
- `git`
- On macOS: `brew install coreutils` (for `gtimeout`)

## Keeping Updated

```bash
.aishore/aishore update --check    # Check for updates (dry-run)
.aishore/aishore update            # Update from upstream (checksum-verified)
.aishore/aishore update --force    # Re-download even if same version
```

Updates fetch the CLI, agent prompts, and gitignore-entries — verified against SHA-256 checksums. Your `backlog/` and `config.yaml` are never modified.

If checksums cannot be fetched, the update aborts. Use `--force --no-verify` to bypass verification (not recommended).

## How It Works

**Concurrency guard:** Only one aishore process runs at a time (uses `flock` on Linux).

**Sprint execution:** The orchestrator picks a ready backlog item, invokes the developer agent via `claude --model`, then runs your validation command (if configured), then invokes the validator agent.

**Completion contract:** Agents signal completion by writing to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "implemented feature X"}
```

The orchestrator polls for this file, then proceeds to the next step. On failure, the working tree is reset and the next item is tried.

**Failed item skipping:** When running multiple sprints (`run 5`), items that fail are excluded from subsequent picks in the same session.

## License

Proprietary — All Rights Reserved. See [LICENSE](LICENSE).
