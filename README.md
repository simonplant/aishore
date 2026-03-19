# aishore

![Version](https://img.shields.io/badge/version-0.3.1-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)
![Shell](https://img.shields.io/badge/shell-bash%204.4%2B-green)
![Claude Code](https://img.shields.io/badge/requires-Claude%20Code%20CLI-blueviolet)

**Intent-driven autonomous development for Claude Code.**

aishore is a drop-in sprint orchestration tool that reliably develops software in a guided and automated way — aligned to commander's intent and quality standards. You define what must be true (intent), what to build (backlog), and how to verify it (acceptance criteria). aishore picks items, implements them through a maturity protocol (implement → critique → harden), validates against your intent, and archives completed work. You come back to code that was built right, for the right reasons.

```
You: define intent + backlog  →  aishore develops, critiques, hardens  →  You: review quality work
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
2. **Develop** — a Developer agent implements the feature using a 3-phase maturity protocol (implement → critique → harden)
3. **Test** — your validation command runs (test suite, linter, type-checker)
4. **Validate** — a Validator agent checks acceptance criteria and commander's intent against the actual changes
5. **Archive** — completed work is recorded and the item is marked done

Run `.aishore/aishore run 5` and it executes five sprints back-to-back. Failed items are skipped in subsequent picks so the batch keeps moving.

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
  --intent "Ops must know instantly if the service is alive or dead." \
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

Add features and bugs to your backlog. Each item gets an ID, priority, and a commander's intent — a clear directive that defines what must be true when the work is done.

```bash
.aishore/aishore backlog add --title "OAuth2 login flow" --priority must \
  --intent "Users must authenticate securely or be told exactly why they can't."
.aishore/aishore backlog add --title "Fix timeout on large uploads" --type bug \
  --intent "Large uploads must complete or give clear progress. Users must never stare at a frozen screen."
```

List what's in the backlog at any time:

```bash
.aishore/aishore backlog list
.aishore/aishore backlog list --ready     # Only sprint-ready items
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
.aishore/aishore run                # Run one sprint
.aishore/aishore run 5              # Run five sprints back-to-back
.aishore/aishore run FEAT-003       # Run a specific item
.aishore/aishore run --dry-run      # Preview what would run without executing
```

Each sprint is isolated. Pre-existing uncommitted changes are stashed beforehand and restored afterward. If a sprint fails, the working tree resets cleanly — your other work is never lost.

Commits happen automatically on feature branches. Use `--retries N` to let failing items retry, and `--refine` to have an AI agent improve the spec when retries are exhausted.

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

## Autonomous Mode

Let aishore drain the backlog unattended. It auto-grooms when ready items run low and stops on repeated failures.

```bash
.aishore/aishore auto done                     # Drain entire backlog
.aishore/aishore auto p0                       # Complete all must (P0) items
.aishore/aishore auto p1                       # Complete all must + should items
.aishore/aishore auto p2                       # Complete all must + should + could items
.aishore/aishore auto done --retries 2         # Per-item retries on failure
.aishore/aishore auto p1 --max-failures 3      # Stop after 3 consecutive failures
```

## Agent Roles

| Agent | Role | Invoked by |
|-------|------|------------|
| **Developer** | Implements features following project conventions and maturity protocol | `run` |
| **Validator** | Checks acceptance criteria and commander's intent against actual changes | `run` |
| **Tech Lead** | Grooms bugs, adds steps and AC, ensures technical readiness | `groom` |
| **Product Owner** | Grooms features, aligns priorities with product vision | `groom --backlog` |
| **Architect** | Reviews patterns, risks, code quality, and documentation | `review` |

All agents automatically read your `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` for project context.

## Complete Flag Reference

### `backlog add`

```bash
.aishore/aishore backlog add                         # Interactive mode
.aishore/aishore backlog add --title "..." [flags]   # Non-interactive
```

| Flag | Description | Default |
|------|-------------|---------|
| `--title "..."` | Item title | *(required)* |
| `--intent "..."` | Commander's intent — what must be true when done | *(required for sprint)* |
| `--type feat\|bug` | Feature or bug | `feat` |
| `--desc "..."` | Full description | *(none)* |
| `--priority must\|should\|could\|future` | Priority level | `should` |
| `--category "..."` | Category tag | *(none)* |
| `--ready` | Mark as sprint-ready immediately | `false` |
| `--ac "text"` | Add acceptance criterion *(repeatable)* | *(none)* |
| `--ac-verify "cmd"` | Attach verification command to preceding `--ac` | *(none)* |

IDs are auto-generated: `FEAT-001`, `FEAT-002`, ... or `BUG-001`, `BUG-002`, ...

> **Note:** Items without a commander's intent (or with intent shorter than 20 characters) will not be picked for sprints. You can add items without intent for tracking, but they must have intent before they can execute.

### `backlog edit`

```bash
.aishore/aishore backlog edit <ID> [flags]
```

| Flag | Description |
|------|-------------|
| `--title "..."` | Change title |
| `--intent "..."` | Set commander's intent |
| `--desc "..."` | Change description |
| `--priority must\|should\|could\|future` | Change priority |
| `--status todo\|in-progress\|done` | Change status |
| `--category "..."` | Change category |
| `--ready` | Mark as sprint-ready |
| `--no-ready` | Unmark from sprint-ready |
| `--groomed-at [YYYY-MM-DD]` | Set groomed date (defaults to today) |
| `--groomed-notes "..."` | Set grooming notes |
| `--ac "text"` | Add acceptance criterion *(repeatable)* |
| `--ac-verify "cmd"` | Attach verification command to preceding `--ac` |

Multiple flags can be combined in a single edit command.

### `backlog list`

| Flag | Description |
|------|-------------|
| `--type feat\|bug` | Filter by type |
| `--status todo\|in-progress\|done` | Filter by status |
| `--ready` | Show only sprint-ready items |

### `backlog check`

```bash
.aishore/aishore backlog check <ID>    # Validate readiness gates for an item
```

Checks: title, commander's intent (≥20 chars, must be a directive), steps, acceptance criteria, and step length.

### `run`

```bash
.aishore/aishore run [N|ID] [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `[N]` | Number of sprints to run | `1` |
| `[ID]` | Run a specific item by ID (e.g., `FEAT-001`) | — |
| `--dry-run` | Preview what would run without executing | — |
| `--no-merge` | Keep feature branches for PR review (push instead of merge) | — |
| `--retries N` | Allow N retry attempts on validation failure | `0` |
| `--refine` | Refine spec (steps + AC) when retries exhausted, then retry once more | — |
| `--quick` | Skip maturity protocol (fast iteration) | — |

### `auto`

```bash
.aishore/aishore auto <scope> [flags]
```

| Scope | Items included |
|-------|---------------|
| `p0` | `must` priority only |
| `p1` | `must` + `should` |
| `p2` | `must` + `should` + `could` |
| `done` | All priorities (drain entire backlog) |

| Flag | Description | Default |
|------|-------------|---------|
| `--retries N` | Per-item retries on failure | `0` |
| `--max-failures N` | Stop after N consecutive failures (circuit breaker) | `5` |

### `groom`

| Flag | Description |
|------|-------------|
| `--backlog` | Product Owner mode: groom features instead of bugs |

### `review`

| Flag | Description |
|------|-------------|
| `--update-docs` | Allow the architect to update `ARCHITECTURE.md` / `PRODUCT.md` and add backlog items |
| `--since <commit>` | Review changes since a specific commit |

### Other Commands

| Command | Description |
|---------|-------------|
| `status` | Backlog overview and sprint readiness |
| `metrics` | Sprint velocity, pass rates, trends |
| `metrics --json` | Machine-readable metrics |
| `clean` | Remove done items from backlogs |
| `clean --dry-run` | Preview what would be removed |
| `update` | Update from upstream (checksum-verified) |
| `update --dry-run` | Check for updates without applying |
| `update --force` | Update even if already on latest version |
| `update --force --no-verify` | Skip checksum verification |
| `checksums` | Regenerate checksums after editing `.aishore/` files |
| `version` | Show version |
| `help` | Show full command reference |

## Item Schema

Each backlog item has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Auto-generated (`FEAT-001`, `BUG-001`) |
| `title` | string | Short descriptive title |
| `intent` | string | Commander's intent — non-negotiable directive |
| `description` | string | Full description — what to build, context, scope boundaries |
| `priority` | string | `must`, `should`, `could`, or `future` |
| `category` | string | Organizational tag |
| `steps` | array | Implementation steps (added by grooming) |
| `acceptanceCriteria` | array | Verifiable acceptance criteria (string or `{text, verify}` objects) |
| `scope` | array | Glob patterns for scope checking (e.g., `["src/**", "tests/**"]`) |
| `status` | string | `todo`, `in-progress`, or `done` |
| `readyForSprint` | boolean | Whether item is ready for sprint execution |
| `passes` | boolean | Set automatically after successful sprint |
| `dependsOn` | array | IDs of items this depends on |
| `groomedAt` | string | Date of last grooming (YYYY-MM-DD) |
| `groomingNotes` | string | Notes from grooming |
| `completedAt` | string | Completion timestamp (auto-set) |
| `failCount` | number | Number of failed sprint attempts (auto-set) |
| `lastFailAt` | string | Timestamp of last failure (auto-set) |
| `lastFailReason` | string | Reason for last failure (auto-set) |

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
    ├── VERSION              # Version (single source of truth)
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── agents/              # Agent prompts (developer, validator, tech-lead, product-owner, architect)
    ├── config.yaml          # Optional overrides
    └── data/                # Runtime (logs, status)
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

# Scope checking: "warn" (log and continue) or "strict" (fail sprint)
scope:
  mode: warn

# Maturity protocol: implement → critique → harden (disable with --quick)
maturity:
  enabled: true

# Agent permissions (restrict for tighter sandbox)
permissions:
  developer: "Bash,Edit,Write,Read,Glob,Grep"
  validator: "Bash,Read,Write,Glob,Grep"
  reviewer: "Read,Glob,Grep"

notifications:
  on_complete: "notify-send 'aishore' \"Sprint $1: $2\""
```

Or use environment variables (these take precedence over config.yaml):

| Setting | Config key | Env var | Default |
|---------|-----------|---------|---------|
| Validation command | `validation.command` | `AISHORE_VALIDATE_CMD` | *(none)* |
| Validation timeout | `validation.timeout` | `AISHORE_VALIDATE_TIMEOUT` | `120` |
| Primary model | `models.primary` | `AISHORE_MODEL_PRIMARY` | `claude-opus-4-6` |
| Fast model | `models.fast` | `AISHORE_MODEL_FAST` | `claude-sonnet-4-6` |
| Agent timeout | `agent.timeout` | `AISHORE_AGENT_TIMEOUT` | `3600` |
| Notify command | `notifications.on_complete` | `AISHORE_NOTIFY_CMD` | *(none)* |
| Maturity protocol | `maturity.enabled` | `AISHORE_MATURITY` | `true` |
| Scope mode | `scope.mode` | `AISHORE_SCOPE_MODE` | `warn` |

**Precedence:** env vars > config.yaml > built-in defaults.

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

The updatable file list is discovered dynamically from the checksums manifest — no hardcoded lists. All paths are validated against traversal attacks. Your `backlog/` and `config.yaml` are never modified.

## License

Proprietary — All Rights Reserved. See [LICENSE](LICENSE).
