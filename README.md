# aishore

**Autonomous sprint execution for Claude Code.**

aishore is a drop-in tool that runs development sprints without you. You describe what needs building in a backlog, and aishore picks items, implements them with AI agents, validates the work, and archives the results. You come back to committed, tested code.

```
You: "Build these features"  →  aishore runs sprints  →  You: review completed work
```

## How It Works

aishore models a real sprint team with specialized AI agents:

```
┌─────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌─────────┐
│  Pick   │───▶│ Developer │───▶│ Validation │───▶│ Validator │───▶│ Archive │
│  Item   │    │   Agent   │    │  Command   │    │   Agent   │    │  Done   │
└─────────┘    └───────────┘    └────────────┘    └───────────┘    └─────────┘
```

1. **Pick** — selects the highest-priority ready item from your backlog
2. **Develop** — a Developer agent implements the feature, following your project's conventions
3. **Test** — your validation command runs (test suite, linter, type-checker)
4. **Validate** — a Validator agent checks acceptance criteria against the actual changes
5. **Archive** — completed work is recorded and the item is marked done

Run `aishore run 5` and it executes five sprints back-to-back. Failed items are skipped in subsequent picks so the batch keeps moving.

## Getting Started

### Install

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
```

Then run the setup wizard:

```bash
.aishore/aishore init
```

The wizard checks prerequisites, detects your project type, configures validation, and scaffolds `backlog/`.

<details>
<summary>Manual installation</summary>

Copy the `.aishore/` directory into your project:

```bash
cp -r /path/to/aishore/.aishore /path/to/your/project/
cd /path/to/your/project && .aishore/aishore init
```

</details>

### Your First Sprint

```bash
# 1. Add a feature to the backlog
.aishore/aishore backlog add --title "Add health check endpoint" \
  --desc "GET /health returns 200 with {status: ok}"

# 2. Groom it (adds steps, acceptance criteria, marks it ready)
.aishore/aishore groom

# 3. Run a sprint
.aishore/aishore run
```

That's it. The developer agent reads the item, explores your codebase, implements the feature, and the validator confirms it meets the acceptance criteria.

## The Workflow

aishore follows a **populate → groom → run → review** cycle. This mirrors how a real team works: product fills the backlog, leads refine it, developers execute, and architects review.

### 1. Populate the Backlog

Add features and bugs to your backlog. Each item gets an ID, priority, and description.

```bash
.aishore/aishore backlog add --title "OAuth2 login flow" --priority must
.aishore/aishore backlog add --title "Fix timeout on large uploads" --type bug
```

List what's in the backlog at any time:

```bash
.aishore/aishore backlog list
.aishore/aishore backlog list --ready    # Only sprint-ready items
.aishore/aishore backlog list --type bug  # Only bugs
```

### 2. Groom

Grooming turns rough ideas into sprint-ready items by adding implementation steps and testable acceptance criteria.

```bash
.aishore/aishore groom              # Tech Lead: grooms bugs + marks features ready
.aishore/aishore groom --backlog    # Product Owner: grooms features for value alignment
```

The **Tech Lead agent** focuses on technical clarity — are the steps actionable? Are the acceptance criteria testable? The **Product Owner agent** focuses on value — are we building the right things in the right order?

### 3. Run Sprints

```bash
.aishore/aishore run           # Run one sprint
.aishore/aishore run 5         # Run five sprints back-to-back
.aishore/aishore run FEAT-003  # Run a specific item
.aishore/aishore run --dry-run # Preview what would run without executing
```

Each sprint is isolated. Pre-existing uncommitted changes are stashed beforehand and restored afterward. If a sprint fails, the working tree resets cleanly — your other work is never lost.

Commits happen automatically on feature branches. Use `--retries N` to let failing items retry.

### 4. Review

After sprints complete, the Architect agent can review the accumulated changes:

```bash
.aishore/aishore review                        # Architecture review
.aishore/aishore review --update-docs          # Review and update project docs
.aishore/aishore review --since abc123f        # Review changes since a specific commit
```

### Monitor Progress

```bash
.aishore/aishore status          # Backlog overview and sprint readiness
.aishore/aishore metrics         # Sprint velocity, pass rates, trends
.aishore/aishore metrics --json  # Machine-readable metrics
```

Clean up completed items when they accumulate:

```bash
.aishore/aishore clean           # Remove done items
.aishore/aishore clean --dry-run # Preview what would be removed
```

## Agent Roles

| Agent | Role | When |
|-------|------|------|
| **Developer** | Implements features following project conventions | `run` |
| **Validator** | Checks acceptance criteria against actual changes | `run` |
| **Tech Lead** | Grooms bugs, ensures technical readiness | `groom` |
| **Product Owner** | Grooms features, aligns with product vision | `groom --backlog` |
| **Architect** | Reviews patterns, risks, and code quality | `review` |

All agents automatically read your `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` for project context.

## Project Structure

```
your-project/
├── backlog/                 # YOUR CONTENT (version controlled)
│   ├── backlog.json         # Feature backlog
│   ├── bugs.json            # Bug/tech-debt backlog
│   ├── sprint.json          # Current sprint state
│   ├── DEFINITIONS.md       # DoR, DoD, priority/size definitions
│   └── archive/
│       └── sprints.jsonl    # Completed sprint history
├── CLAUDE.md                # Project context (auto-detected)
└── .aishore/                # TOOL (updatable, replaceable)
    ├── aishore              # Single-file CLI (Bash)
    ├── agents/              # Agent prompts
    ├── config.yaml          # Optional overrides
    └── data/                # Runtime logs and status
```

Your backlogs (`backlog/`) are always separate from the tool (`.aishore/`). Updates never touch your content.

## Configuration

aishore works out of the box. Configure only if you need to override defaults.

Edit `.aishore/config.yaml`:

```yaml
validation:
  command: "npm run type-check && npm run lint && npm test"
  timeout: 120

models:
  primary: "claude-opus-4-6"
  fast: "claude-sonnet-4-6"

agent:
  timeout: 3600

notifications:
  on_complete: "notify-send 'aishore' \"Sprint $1: $2\""
```

Or use environment variables (these take precedence over config.yaml):

| Setting | Env var | Default |
|---------|---------|---------|
| Primary model | `AISHORE_MODEL_PRIMARY` | `claude-opus-4-6` |
| Fast model | `AISHORE_MODEL_FAST` | `claude-sonnet-4-6` |
| Agent timeout | `AISHORE_AGENT_TIMEOUT` | `3600` |
| Validation command | `AISHORE_VALIDATE_CMD` | *(none)* |
| Validation timeout | `AISHORE_VALIDATE_TIMEOUT` | `120` |
| Notify command | `AISHORE_NOTIFY_CMD` | *(none)* |

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude` command)
- `jq`
- `bash` 4.4+
- `git`
- On macOS: `brew install coreutils` (for `gtimeout`)

## Keeping Updated

```bash
.aishore/aishore update --dry-run  # Check for updates
.aishore/aishore update            # Update (checksum-verified)
```

Updates are verified against SHA-256 checksums. Your `backlog/` and `config.yaml` are never modified.

## Command Reference

<details>
<summary>Full command list</summary>

| Command | Description |
|---------|-------------|
| `init` | Interactive setup wizard |
| `status` | Backlog overview and sprint readiness |
| `backlog list` | List all items (features + bugs) |
| `backlog list --status todo` | Filter by status |
| `backlog list --type feat` | Filter by type (feat, bug) |
| `backlog list --ready` | Show only sprint-ready items |
| `backlog add` | Add a new item (interactive) |
| `backlog add --title "..." --type bug` | Add with flags |
| `backlog show <ID>` | Show full detail of one item |
| `backlog edit <ID> --priority must` | Update fields on an item |
| `backlog rm <ID>` | Remove an item |
| `auto done` | Autonomous: drain entire backlog |
| `auto p0` | Autonomous: complete all must items |
| `auto p1` | Autonomous: complete all must + should items |
| `auto p2` | Autonomous: complete all must + should + could items |
| `auto <scope> --max-failures N` | Consecutive failures before stopping |
| `groom` | Groom bugs/tech debt (Tech Lead agent) |
| `groom --backlog` | Groom features (Product Owner agent) |
| `run [N]` | Run N sprints (default: 1) |
| `run <ID>` | Run specific item by ID |
| `run --dry-run` | Preview without running agents |
| `run --retries N` | Allow N retry attempts on failure |
| `run --no-merge` | Keep feature branches for PR review |
| `review` | Architecture review |
| `review --update-docs` | Review and update project docs |
| `review --since <commit>` | Review changes since commit |
| `metrics` | Sprint metrics |
| `metrics --json` | Metrics as JSON |
| `clean` | Remove done items from backlogs |
| `clean --dry-run` | Preview what would be removed |
| `update` | Update from upstream (checksum-verified) |
| `update --dry-run` | Check for updates without applying |
| `checksums` | Regenerate checksums |
| `version` | Show version |
| `help` | Show usage |

</details>

## License

Proprietary — All Rights Reserved. See [LICENSE](LICENSE).
