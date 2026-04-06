# Configuration Reference

Every configurable option in aishore, in one place.

## Configuration Precedence

Settings are resolved in this order (first match wins):

1. **Environment variables** (`AISHORE_*`)
2. **Config file** (`.aishore/config.yaml`)
3. **Built-in defaults**

Example: if `AISHORE_VALIDATE_CMD="pytest"` is set and `config.yaml` has `validation.command: "npm test"`, the environment variable wins and `pytest` is used.

---

## Configuration File

All settings live in `.aishore/config.yaml`. The file is optional — aishore works out of the box with sensible defaults.

```yaml
# .aishore/config.yaml — override defaults here or via env vars

# Project metadata
project:
  name: "your-project"

# Validation command for your stack (e.g., "npm test && npm run lint")
validation:
  command: ""
  timeout: 120

# Setup command runs in each worktree before sprint (e.g., "npm install")
# setup:
#   command: ""

# Auto-fix command run after developer agent (e.g., "npm run lint -- --fix")
# fix:
#   command: ""

# Models (uncomment to override)
# models:
#   primary: "claude-opus-4-6"
#   fast: "claude-sonnet-4-6"

# Agent settings
# agent:
#   timeout: 3600
#   max_turns:
#     developer: 75
#     validator: 45
#     groomer: 45

# Merge strategy: "merge" (default, --no-ff) or "squash" (single commit per item)
# merge:
#   strategy: merge

# Notifications on sprint completion
# notifications:
#   on_complete: "notify-send 'aishore' \"Sprint $1: $2\""

# Auto-groom settings
# auto:
#   groom_threshold: 3
#   max_failures: 5

# Grooming settings
# groom:
#   max_items: 10
#   min_priority: should

# Output truncation
# output:
#   truncate_lines: 50

# Output streaming
# streaming:
#   enabled: true
#   max_lines: 20

# Run session defaults (override with CLI flags)
# run:
#   retries: 0
#   session_limit: 0        # 0 = unlimited
```

### Every Option Explained

#### `project.name`

| | |
|---|---|
| **Type** | string |
| **Default** | *(auto-detected from directory name)* |
| **Env var** | — |
| **What it controls** | Project name used in logs and agent context. |
| **When to change** | When the directory name doesn't match the project name. |

#### `validation.command`

| | |
|---|---|
| **Type** | string |
| **Default** | `""` (empty — no validation) |
| **Env var** | `AISHORE_VALIDATE_CMD` |
| **What it controls** | Shell command that validates the codebase after the developer agent finishes. Also runs as a baseline pre-flight before the agent starts — if it fails, the sprint is aborted. |
| **When to change** | Set this to your test/lint command (e.g., `npm test && npm run lint`, `make check`, `pytest`). |

#### `validation.timeout`

| | |
|---|---|
| **Type** | integer (seconds) |
| **Default** | `120` |
| **Env var** | `AISHORE_VALIDATE_TIMEOUT` |
| **What it controls** | How long the validation command can run before being killed. |
| **When to change** | Increase for slow test suites; decrease to fail fast. |

#### `setup.command`

| | |
|---|---|
| **Type** | string |
| **Default** | `""` (empty — no setup) |
| **Env var** | `AISHORE_SETUP_CMD` |
| **What it controls** | Shell command run in each worktree before the sprint starts. Use for installing dependencies that aren't in git (node_modules, venv, etc.). |
| **When to change** | Set to your dependency installer (e.g., `npm install`, `pip install -e .`). |

#### `fix.command`

| | |
|---|---|
| **Type** | string |
| **Default** | `""` (empty — no auto-fix) |
| **Env var** | `AISHORE_FIX_CMD` |
| **What it controls** | Shell command run after the developer agent finishes, before validation. Used for auto-formatters and lint fixers. |
| **When to change** | Set to your formatter (e.g., `npm run lint -- --fix`, `black .`, `gofmt -w .`). |

#### `models.primary`

| | |
|---|---|
| **Type** | string (model ID) |
| **Default** | `claude-opus-4-6` |
| **Env var** | `AISHORE_MODEL_PRIMARY` |
| **What it controls** | AI model used for developer and architecture review agents. |
| **When to change** | To use a different model for implementation work. |

#### `models.fast`

| | |
|---|---|
| **Type** | string (model ID) |
| **Default** | `claude-sonnet-4-6` |
| **Env var** | `AISHORE_MODEL_FAST` |
| **What it controls** | AI model used for grooming, validation, and spec refinement agents. |
| **When to change** | To use a different model for lighter-weight agent tasks. |

#### `agent.timeout`

| | |
|---|---|
| **Type** | integer (seconds) |
| **Default** | `3600` (1 hour) |
| **Env var** | `AISHORE_AGENT_TIMEOUT` |
| **What it controls** | Maximum time an agent process can run before being killed. |
| **When to change** | Increase for large features; decrease to bound costs. |

#### `agent.max_turns.developer`

| | |
|---|---|
| **Type** | integer |
| **Default** | `75` |
| **Env var** | `AISHORE_MAX_TURNS_DEVELOPER` |
| **What it controls** | Maximum conversation turns for the developer agent. Limits how many tool-call round trips the agent can make within a single invocation. |
| **When to change** | Increase for complex features that need more iteration; decrease to bound token costs. |

#### `agent.max_turns.validator`

| | |
|---|---|
| **Type** | integer |
| **Default** | `45` |
| **Env var** | `AISHORE_MAX_TURNS_VALIDATOR` |
| **What it controls** | Maximum conversation turns for the validator agent. Validators need enough turns to complete multi-step verification without hitting the limit. |
| **When to change** | Increase if validation involves complex multi-step probing. |

#### `agent.max_turns.groomer`

| | |
|---|---|
| **Type** | integer |
| **Default** | `45` |
| **Env var** | `AISHORE_MAX_TURNS_GROOMER` |
| **What it controls** | Maximum conversation turns for grooming agents (groomer, architect). |
| **When to change** | Increase for larger grooming sessions; decrease to keep grooming focused. |

#### `merge.strategy`

| | |
|---|---|
| **Type** | `merge` \| `squash` |
| **Default** | `merge` |
| **Env var** | `AISHORE_MERGE_STRATEGY` |
| **What it controls** | How feature branches are merged back. `merge` uses `--no-ff` (preserves branch history); `squash` creates a single commit per item. |
| **When to change** | Set to `squash` for a cleaner linear history. |

#### `notifications.on_complete`

| | |
|---|---|
| **Type** | string (shell command) |
| **Default** | `""` (no notifications) |
| **Env var** | `AISHORE_NOTIFY_CMD` |
| **What it controls** | Command run when a sprint completes. Receives the item ID as `$1` and status as `$2`. |
| **When to change** | Set to send desktop notifications, Slack messages, etc. Example: `notify-send 'aishore' "Sprint $1: $2"` |

#### `auto.groom_threshold`

| | |
|---|---|
| **Type** | integer |
| **Default** | `3` |
| **Env var** | `AISHORE_AUTO_GROOM_THRESHOLD` |
| **What it controls** | In autonomous mode, auto-grooming triggers when the number of ready items drops below this threshold. |
| **When to change** | Increase to keep a deeper ready queue; set to `0` to disable auto-grooming. |

#### `auto.max_failures`

| | |
|---|---|
| **Type** | integer |
| **Default** | `5` |
| **Env var** | `AISHORE_AUTO_MAX_FAILURES` |
| **What it controls** | Circuit breaker for autonomous mode. Stops after this many consecutive failures. |
| **When to change** | Lower for fail-fast behavior; raise if failures are expected (e.g., experimental backlog). |

#### `groom.max_items`

| | |
|---|---|
| **Type** | integer |
| **Default** | `10` |
| **Env var** | `AISHORE_GROOM_MAX_ITEMS` |
| **What it controls** | Maximum items the grooming agent creates or refines per session. |
| **When to change** | Lower for smaller batches; raise if your backlog needs heavy population. |

#### `groom.min_priority`

| | |
|---|---|
| **Type** | `must` \| `should` \| `could` \| `future` |
| **Default** | `should` |
| **Env var** | `AISHORE_GROOM_MIN_PRIORITY` |
| **What it controls** | Minimum priority level the grooming agent assigns to new items. |
| **When to change** | Set to `must` to only groom high-priority items; `could` for broader coverage. |

#### `output.truncate_lines`

| | |
|---|---|
| **Type** | integer |
| **Default** | `50` |
| **Env var** | `AISHORE_OUTPUT_TRUNCATE_LINES` |
| **What it controls** | Number of lines shown when truncating long command output in logs. |
| **When to change** | Increase to see more output in logs; decrease to reduce noise. |

#### `streaming.enabled`

| | |
|---|---|
| **Type** | boolean |
| **Default** | `true` |
| **Env var** | `AISHORE_STREAMING` |
| **What it controls** | Whether agent output is streamed to the terminal in real time. When `false`, output is only shown after the agent completes. |
| **When to change** | Set to `false` to reduce terminal noise during autonomous sessions. |

#### `streaming.max_lines`

| | |
|---|---|
| **Type** | integer |
| **Default** | `20` |
| **Env var** | `AISHORE_STREAMING_MAX_LINES` |
| **What it controls** | Maximum number of trailing output lines shown during agent streaming. |
| **When to change** | Increase to see more live output; decrease to reduce terminal clutter. |

#### `run.retries`

| | |
|---|---|
| **Type** | integer |
| **Default** | `0` (no retries) |
| **Env var** | `AISHORE_RETRIES` |
| **CLI flag** | `--retries N` |
| **What it controls** | Per-item retry attempts when a sprint fails validation. |
| **When to change** | Set to 1-3 for resilience. Higher values cost more agent time. |

#### `run.session_limit`

| | |
|---|---|
| **Type** | integer |
| **Default** | `0` (unlimited) |
| **Env var** | `AISHORE_SESSION_LIMIT` |
| **CLI flag** | `--limit N` |
| **What it controls** | Cap the session at N successfully completed items, then exit cleanly. |
| **When to change** | Useful for bounded batch runs (e.g., "do 3 items then stop"). |

---

## Environment Variables

All `AISHORE_*` environment variables and what they map to:

| Environment Variable | Config Path | Default | Description |
|---|---|---|---|
| `AISHORE_VALIDATE_CMD` | `validation.command` | `""` | Validation command (tests, lint) |
| `AISHORE_VALIDATE_TIMEOUT` | `validation.timeout` | `120` | Validation timeout (seconds) |
| `AISHORE_SETUP_CMD` | `setup.command` | `""` | Worktree setup command (dependency install) |
| `AISHORE_FIX_CMD` | `fix.command` | `""` | Auto-fix command (formatters) |
| `AISHORE_MODEL_PRIMARY` | `models.primary` | `claude-opus-4-6` | Primary AI model |
| `AISHORE_MODEL_FAST` | `models.fast` | `claude-sonnet-4-6` | Fast AI model |
| `AISHORE_AGENT_TIMEOUT` | `agent.timeout` | `3600` | Agent timeout (seconds) |
| `AISHORE_MERGE_STRATEGY` | `merge.strategy` | `merge` | Merge strategy |
| `AISHORE_NOTIFY_CMD` | `notifications.on_complete` | `""` | Completion notification command |
| `AISHORE_AUTO_GROOM_THRESHOLD` | `auto.groom_threshold` | `3` | Auto-groom item threshold |
| `AISHORE_AUTO_MAX_FAILURES` | `auto.max_failures` | `5` | Circuit breaker limit |
| `AISHORE_GROOM_MAX_ITEMS` | `groom.max_items` | `10` | Max items per groom session |
| `AISHORE_GROOM_MIN_PRIORITY` | `groom.min_priority` | `should` | Min priority for grooming |
| `AISHORE_OUTPUT_TRUNCATE_LINES` | `output.truncate_lines` | `50` | Log truncation lines |
| `AISHORE_STREAMING` | `streaming.enabled` | `true` | Enable/disable output streaming |
| `AISHORE_STREAMING_MAX_LINES` | `streaming.max_lines` | `20` | Max trailing lines during streaming |
| `AISHORE_TIMEOUT_MINUTES` | `timeout_minutes` | `0` | Agent timeout in minutes (overrides `agent.timeout`; 0 = no override) |
| `AISHORE_RETRIES` | `run.retries` | `0` | Per-item retry attempts on failure |
| `AISHORE_SESSION_LIMIT` | `run.session_limit` | `0` | Cap session at N items (0 = unlimited) |
| `AISHORE_MAX_TURNS_DEVELOPER` | `agent.max_turns.developer` | `75` | Max turns for developer agent |
| `AISHORE_MAX_TURNS_VALIDATOR` | `agent.max_turns.validator` | `45` | Max turns for validator agent |
| `AISHORE_MAX_TURNS_GROOMER` | `agent.max_turns.groomer` | `45` | Max turns for grooming agents |

---

## CLI Flag Reference

### `init` — Setup wizard

```
.aishore/aishore init [flags]
```

| Flag | Description |
|------|-------------|
| `-y`, `--yes` | Accept auto-detected defaults without prompting |

### `run` — Execute sprints

```
.aishore/aishore run [N|ID|scope] [flags]
```

| Positional | Description |
|------------|-------------|
| *(none)* | Run 1 sprint (default) |
| `N` | Run N sprints |
| `ID` | Run a specific item by ID (e.g., `FEAT-001`) |
| `done` | Drain entire backlog (enables auto-grooming + circuit breaker) |
| `p0` | Complete all `must` items |
| `p1` | Complete all `must` + `should` items |
| `p2` | Complete all `must` + `should` + `could` items |

When a scope (`done`, `p0`, `p1`, `p2`) is given, auto-grooming activates when ready items drop below threshold, and the circuit breaker stops after N consecutive failures.

**Flags:**

| Flag | Argument | Description |
|------|----------|-------------|
| `--dry-run` | — | Preview what would run without executing |
| `--retries` | `N` | Per-item retries on failure (default: `0`) |
| `--limit` | `N` | Cap session at N successful items then exit cleanly |
| `--no-merge` | — | Keep feature branches; push instead of merging |
| `--max-failures` | `N` | Circuit breaker: stop after N consecutive failures (default: `5`) |

### `groom` — Refine backlog

```
.aishore/aishore groom [flags]
```

| Flag | Description |
|------|-------------|
| `--backlog` | *(deprecated, no-op)* Groom now covers all items by default |
| `--architect` | *(deprecated)* Redirects to `scaffold` command |

### `review` — Architecture review

```
.aishore/aishore review [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--update-docs` | — | Allow reviewer to update docs and add backlog items |
| `--since` | `<commit>` | Review changes since a specific commit |

### `backlog add` — Add item

```
.aishore/aishore backlog add [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--title` | `"text"` | Item title |
| `--intent` | `"text"` | Commander's intent (must be >= 20 chars for sprint readiness) |
| `--type` | `feat` \| `bug` | Item type (default: `feat`) |
| `--desc` | `"text"` | Full description |
| `--priority` | `must` \| `should` \| `could` \| `future` | Priority level (default: `should`) |
| `--category` | `"text"` | Category label |
| `--ready` | — | Mark as sprint-ready immediately |
| `--steps` | `"text"` | Implementation step *(repeatable, replaces all steps)* |
| `--ac` | `"text"` | Add acceptance criterion *(repeatable)* |
| `--ac-verify` | `"cmd"` | Attach verification command to preceding `--ac` |
| `--depends-on` | `ID` | Add dependency on another item *(repeatable)* |

### `backlog edit` — Update item

```
.aishore/aishore backlog edit <ID> [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--title` | `"text"` | Change title |
| `--intent` | `"text"` | Set commander's intent |
| `--desc` | `"text"` | Change description |
| `--priority` | `must` \| `should` \| `could` \| `future` | Change priority |
| `--category` | `"text"` | Change category |
| `--status` | `todo` \| `in-progress` \| `done` | Change status |
| `--ready` | — | Mark as sprint-ready |
| `--no-ready` | — | Unmark from sprint-ready |
| `--groomed-at` | `[YYYY-MM-DD]` | Set groomed date (defaults to today) |
| `--groomed-notes` | `"text"` | Set grooming notes |
| `--steps` | `"text"` | Implementation step *(repeatable, replaces all steps)* |
| `--remove-step` | `N` | Remove step by 1-based index |
| `--clear-steps` | — | Reset steps to empty |
| `--ac` | `"text"` | Add acceptance criterion *(repeatable)* |
| `--ac-verify` | `"cmd"` | Attach verification command to preceding `--ac` |
| `--remove-ac` | `N` | Remove acceptance criterion by 1-based index |
| `--clear-ac` | — | Reset acceptance criteria to empty |
| `--scope` | `"glob"` | Add scope glob *(repeatable)* |
| `--clear-scope` | — | Reset scope to empty |
| `--depends-on` | `ID` | Add dependency *(repeatable)* |
| `--clear-depends-on` | — | Reset dependencies to empty |

### `backlog list` — List items

```
.aishore/aishore backlog list [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--type` | `feat` \| `bug` | Filter by type |
| `--status` | `todo` \| `in-progress` \| `done` | Filter by status |
| `--priority` | `must` \| `should` \| `could` \| `future` | Filter by priority |
| `--ready` | — | Show only sprint-ready items |
| `--no-ready` | — | Show only items not yet ready |

### `backlog show` — Display item detail

```
.aishore/aishore backlog show <ID>
```

No flags. Shows full item details including steps, AC, and scope.

### `backlog check` — Validate readiness

```
.aishore/aishore backlog check <ID|--all>
```

| Flag | Description |
|------|-------------|
| `--all` | Audit every non-done item and print a summary table |

Validates: title, commander's intent (>= 20 chars, must be a directive), steps, acceptance criteria, and step length.

### `backlog rm` — Remove item

```
.aishore/aishore backlog rm <ID> [flags]
```

| Flag | Description |
|------|-------------|
| `--force`, `-f` | Skip confirmation prompt |

### `clean` — Remove done items

```
.aishore/aishore clean [flags]
```

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview what would be removed |
| `--no-archive` | Skip archiving removed items |
| `--regression` | Clear the regression suite (backup created before removal) |

### `update` — Update from upstream

```
.aishore/aishore update [flags]
```

| Flag | Description |
|------|-------------|
| `--dry-run` | Check for updates without applying |
| `--force` | Update even if already on latest |
| `--ref` | Update to a specific git ref (commit SHA, branch, or tag) |
| `--no-verify` | Skip checksum verification (requires `--force`) |

### `status` — Backlog overview

```
.aishore/aishore status [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--watch` | — | Live refresh until sprint completes or Ctrl-C |
| `--interval` | `N` | Refresh interval in seconds (default: `30`) |

Shows backlog summary and sprint readiness.

### `version` — Show version

```
.aishore/aishore version
```

Also available as `-v` or `--version`.

### `help` — Show usage

```
.aishore/aishore help [command]
.aishore/aishore help --full
```

| Flag | Description |
|------|-------------|
| *(positional)* | Show detailed help for a specific command (e.g., `help run`, `help backlog`) |
| `--full` | Show complete reference (all commands, all flags) |

Also available as `-h` or `--help`.

---

## Agent Permissions

Agents run with restricted Claude Code tool permissions. Each role has a default set:

### Developer Agent

**Default:** `Agent,Bash,Edit,Write,Read,Glob,Grep,EnterPlanMode,ExitPlanMode`

Full access. The developer agent can run shell commands, read and write files, search the codebase, spawn sub-agents for parallel work, and enter plan mode for structured implementation planning. This is the most permissive role because it needs to implement features.

**Security note:** The developer agent can execute arbitrary shell commands. If your project has sensitive credentials accessible via the shell, consider removing `Bash` from the permission set.

### Validator Agent

**Default:** `Bash,Read,Glob,Grep`

Can run tests and read files, but cannot use `Edit` or `Write`. The validator checks the developer's work by running the validation command and inspecting outputs. The result signal file is written via Bash (`echo`/`jq` to file).

### Reviewer Agent

**Default:** `Read,Glob,Grep`

Read-only. The architecture reviewer can examine code but cannot modify it. When `review --update-docs` is used, `Edit,Write` are added automatically so it can update documentation files.

Permissions are hardcoded per role and not configurable via config.yaml.
