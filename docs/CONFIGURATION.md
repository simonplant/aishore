# Configuration Reference

Every configurable option in aishore, in one place.

## Configuration Precedence

Settings are resolved in this order (first match wins):

1. **Environment variables** (`AISHORE_*`)
2. **Config file** (`.aishore/config.yaml`)
3. **Built-in defaults**

Example: if `AISHORE_SCOPE_MODE=strict` is set and `config.yaml` has `scope.mode: warn`, the environment variable wins and scope checking is strict.

---

## Configuration File

All settings live in `.aishore/config.yaml`. The file is optional — aishore works out of the box with sensible defaults.

```yaml
# .aishore/config.yaml — override defaults here or via env vars

# Project metadata
project:
  name: "your-project"

# Backlog files to read from (relative to backlog/ directory)
# backlog_files:
#   - backlog.json
#   - bugs.json
#   - infra.json

# Validation command for your stack (e.g., "npm test && npm run lint")
validation:
  command: ""
  timeout: 120

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

# Permissions (restrict for tighter sandbox)
# permissions:
#   developer: "Bash,Edit,Write,Read,Glob,Grep"
#   validator: "Bash,Read,Write,Glob,Grep"
#   reviewer: "Read,Glob,Grep"

# Scope checking: "warn" or "strict"
# scope:
#   mode: warn

# Maturity protocol (implement -> critique -> harden). Disable with --quick flag.
# maturity:
#   enabled: true

# Merge strategy: "merge" (default, --no-ff) or "squash" (single commit per item)
# merge:
#   strategy: merge

# Notifications on sprint completion
# notifications:
#   on_complete: "notify-send 'aishore' \"Sprint $1: $2\""
#   system: false      # System notification on auto session end (osascript/notify-send)

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

# PR creation
# pr:
#   create: false

# Isolation mode: "stash" (default) or "worktree"
# isolation:
#   mode: stash
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

#### `backlog_files`

| | |
|---|---|
| **Type** | list of strings (file paths relative to `backlog/`) |
| **Default** | `["backlog.json", "bugs.json"]` |
| **Env var** | `AISHORE_BACKLOG_FILES` (comma-separated) |
| **What it controls** | Which backlog files aishore reads from. Items are picked by priority across all declared files. |
| **When to change** | When you split work across component-specific backlogs (e.g., `infra.json`, `api.json`). Omitting this key preserves the default two-file behavior. Missing files produce a warning, not an abort. |

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

#### `permissions.developer`

| | |
|---|---|
| **Type** | string (comma-separated tool names) |
| **Default** | `Bash,Edit,Write,Read,Glob,Grep` |
| **Env var** | — |
| **What it controls** | Claude Code tools available to the developer agent. Full access by default. |
| **When to change** | Remove `Bash` to prevent shell commands, or restrict further for a tighter sandbox. |

#### `permissions.validator`

| | |
|---|---|
| **Type** | string (comma-separated tool names) |
| **Default** | `Bash,Read,Write,Glob,Grep` |
| **Env var** | — |
| **What it controls** | Claude Code tools available to the validator agent. No `Edit` by default — validators read and run tests, but don't modify code. |
| **When to change** | Rarely. Only if your validation workflow requires editing files. |

#### `permissions.reviewer`

| | |
|---|---|
| **Type** | string (comma-separated tool names) |
| **Default** | `Read,Glob,Grep` |
| **Env var** | — |
| **What it controls** | Claude Code tools available to the architecture reviewer agent. Read-only by default. When `review --update-docs` is used, `Edit,Write` are added automatically. |
| **When to change** | Rarely. The `--update-docs` flag handles the common case. |

#### `scope.mode`

| | |
|---|---|
| **Type** | `warn` \| `strict` |
| **Default** | `warn` |
| **Env var** | `AISHORE_SCOPE_MODE` |
| **What it controls** | Behavior when the developer agent changes files outside an item's `scope` globs. `warn` logs a warning; `strict` fails the sprint. |
| **When to change** | Set to `strict` when you need hard boundaries on what an agent can touch. |

#### `maturity.enabled`

| | |
|---|---|
| **Type** | boolean |
| **Default** | `true` |
| **Env var** | `AISHORE_MATURITY` |
| **What it controls** | Whether the developer agent runs the 3-phase maturity protocol (implement, critique, harden). The `--quick` flag overrides this to `false` per-run. |
| **When to change** | Set to `false` globally for fast iteration on low-risk items. Prefer the `--quick` flag for one-off skips. |

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

#### `notifications.system`

| | |
|---|---|
| **Type** | boolean |
| **Default** | `false` |
| **Env var** | `AISHORE_NOTIFY` |
| **What it controls** | When `true`, sends a platform-native system notification when an auto session ends. Uses `osascript` on macOS and `notify-send` on Linux. A terminal bell (`tput bel`) always fires regardless of this setting. |
| **When to change** | Enable when you run long autonomous sessions and want a desktop notification when the session completes or hits the circuit breaker. |

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

#### `pr.create`

| | |
|---|---|
| **Type** | boolean |
| **Default** | `false` |
| **Env var** | `AISHORE_CREATE_PR` |
| **What it controls** | When `true`, creates a GitHub pull request instead of merging the feature branch. Equivalent to using the `--pr` flag on every run. |
| **When to change** | Enable for teams that require PR review before merging. |

#### `isolation.mode`

| | |
|---|---|
| **Type** | `stash` \| `worktree` |
| **Default** | `stash` |
| **Env var** | `AISHORE_ISOLATION` |
| **What it controls** | How aishore isolates sprint work from uncommitted changes. `stash` uses `git stash`; `worktree` uses `git worktree` for full isolation. |
| **When to change** | Use `worktree` if you want to keep working in the main tree while sprints run. |

---

## Environment Variables

All `AISHORE_*` environment variables and what they map to:

| Environment Variable | Config Path | Default | Description |
|---|---|---|---|
| `AISHORE_BACKLOG_FILES` | `backlog_files` | `backlog.json,bugs.json` | Comma-separated backlog file list |
| `AISHORE_VALIDATE_CMD` | `validation.command` | `""` | Validation command (tests, lint) |
| `AISHORE_VALIDATE_TIMEOUT` | `validation.timeout` | `120` | Validation timeout (seconds) |
| `AISHORE_FIX_CMD` | `fix.command` | `""` | Auto-fix command (formatters) |
| `AISHORE_MODEL_PRIMARY` | `models.primary` | `claude-opus-4-6` | Primary AI model |
| `AISHORE_MODEL_FAST` | `models.fast` | `claude-sonnet-4-6` | Fast AI model |
| `AISHORE_AGENT_TIMEOUT` | `agent.timeout` | `3600` | Agent timeout (seconds) |
| `AISHORE_SCOPE_MODE` | `scope.mode` | `warn` | Scope checking mode |
| `AISHORE_MATURITY` | `maturity.enabled` | `true` | Maturity protocol toggle |
| `AISHORE_MERGE_STRATEGY` | `merge.strategy` | `merge` | Merge strategy |
| `AISHORE_NOTIFY_CMD` | `notifications.on_complete` | `""` | Completion notification command |
| `AISHORE_NOTIFY` | `notifications.system` | `false` | System notification on auto session end |
| `AISHORE_AUTO_GROOM_THRESHOLD` | `auto.groom_threshold` | `3` | Auto-groom item threshold |
| `AISHORE_AUTO_MAX_FAILURES` | `auto.max_failures` | `5` | Circuit breaker limit |
| `AISHORE_GROOM_MAX_ITEMS` | `groom.max_items` | `10` | Max items per groom session |
| `AISHORE_GROOM_MIN_PRIORITY` | `groom.min_priority` | `should` | Min priority for grooming |
| `AISHORE_OUTPUT_TRUNCATE_LINES` | `output.truncate_lines` | `50` | Log truncation lines |
| `AISHORE_CREATE_PR` | `pr.create` | `false` | Create PR instead of merging |
| `AISHORE_ISOLATION` | `isolation.mode` | `stash` | Isolation mode |

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
.aishore/aishore run [N|ID] [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| *(positional)* | `N` | Number of sprints to run (default: `1`) |
| *(positional)* | `ID` | Run a specific item by ID (e.g., `FEAT-001`) |
| `--dry-run` | — | Preview what would run without executing |
| `--no-merge` | — | Keep feature branches; push instead of merging |
| `--pr` | — | Create GitHub PR instead of merging |
| `--retries` | `N` | Retry N times on validation failure (default: `0`) |
| `--refine` | — | Refine spec when retries exhausted, then retry once more |
| `--quick` | — | Skip maturity protocol for this run |

### `auto` — Autonomous mode

```
.aishore/aishore auto <scope> [flags]
```

**Scopes:**

| Scope | Items included |
|-------|----------------|
| `p0` | `must` priority only |
| `p1` | `must` + `should` |
| `p2` | `must` + `should` + `could` |
| `done` | All priorities (drain entire backlog) |

**Flags:**

| Flag | Argument | Description |
|------|----------|-------------|
| `--retries` | `N` | Per-item retries on failure (default: `0`) |
| `--max-failures` | `N` | Circuit breaker: stop after N consecutive failures (default: `5`) |
| `--no-merge` | — | Keep feature branches; push instead of merging |
| `--pr` | — | Create GitHub PR instead of merging |
| `--refine` | — | Refine spec when retries exhausted, then retry once more |
| `--quick` | — | Skip maturity protocol |
| `--auto-review` | — | Run architecture review after all items complete |
| `--dry-run` | — | Preview first item without running |

### `groom` — Refine backlog

```
.aishore/aishore groom [flags]
```

| Flag | Description |
|------|-------------|
| `--backlog` | Product owner mode: groom features (default: groom bugs) |

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
| `--category` | `"text"` | Category tag |
| `--ready` | — | Mark as sprint-ready immediately |
| `--step` | `"text"` | Add implementation step *(repeatable, ordered)* |
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
| `--status` | `todo` \| `in-progress` \| `done` | Change status |
| `--category` | `"text"` | Change category |
| `--ready` | — | Mark as sprint-ready |
| `--no-ready` | — | Unmark from sprint-ready |
| `--groomed-at` | `[YYYY-MM-DD]` | Set groomed date (defaults to today) |
| `--groomed-notes` | `"text"` | Set grooming notes |
| `--step` | `"text"` | Append implementation step *(repeatable)* |
| `--clear-steps` | — | Reset steps to empty |
| `--ac` | `"text"` | Add acceptance criterion *(repeatable)* |
| `--ac-verify` | `"cmd"` | Attach verification command to preceding `--ac` |
| `--clear-ac` | — | Reset acceptance criteria to empty |
| `--scope` | `"glob"` | Add scope glob *(repeatable)* |
| `--clear-scope` | — | Reset scope to empty |
| `--depends-on` | `ID` | Add dependency *(repeatable)* |

### `backlog list` — List items

```
.aishore/aishore backlog list [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--type` | `feat` \| `bug` | Filter by type |
| `--status` | `todo` \| `in-progress` \| `done` | Filter by status |
| `--ready` | — | Show only sprint-ready items |

### `backlog show` — Display item detail

```
.aishore/aishore backlog show <ID>
```

No flags. Shows full item details including steps, AC, and scope.

### `backlog check` — Validate readiness

```
.aishore/aishore backlog check <ID>
```

No flags. Validates: title, commander's intent (>= 20 chars, must be a directive), steps, acceptance criteria, and step length.

### `backlog rm` — Remove item

```
.aishore/aishore backlog rm <ID> [flags]
```

| Flag | Description |
|------|-------------|
| `--force`, `-f` | Skip confirmation prompt |

### `backlog history` — Completed items

```
.aishore/aishore backlog history [flags]
```

| Flag | Argument | Description |
|------|----------|-------------|
| `--since` | `YYYY-MM-DD` | Show items completed on or after date |
| `--failed` | — | Show only failed items |

### `backlog populate` — AI-populate backlog

```
.aishore/aishore backlog populate
```

No flags. Reads `PRODUCT.md` (or `PRD.md`, `README.md`) and uses a product owner agent to create backlog items.

### `backlog sync` — Detect completed items

```
.aishore/aishore backlog sync [flags]
```

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview without marking items |
| `--auto` | Auto-mark detected items as done |

### `clean` — Remove done items

```
.aishore/aishore clean [flags]
```

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview what would be removed |

### `update` — Update from upstream

```
.aishore/aishore update [flags]
```

| Flag | Description |
|------|-------------|
| `--dry-run`, `--check` | Check for updates without applying |
| `--force` | Update even if already on latest |
| `--no-verify` | Skip checksum verification (requires `--force`) |

### `metrics` — Sprint metrics

```
.aishore/aishore metrics [flags]
```

| Flag | Description |
|------|-------------|
| `--json` | Output metrics as JSON |

### `status` — Backlog overview

```
.aishore/aishore status
```

No flags. Shows backlog summary and sprint readiness.

### `diagnose` — Failure diagnostics

```
.aishore/aishore diagnose
```

No flags. Shows last sprint failure details.

### `checksums` — Regenerate checksums

```
.aishore/aishore checksums
```

No flags. Regenerates `.aishore/checksums.sha256` after editing files in `.aishore/`.

### `version` — Show version

```
.aishore/aishore version
```

Also available as `-v` or `--version`.

### `help` — Show usage

```
.aishore/aishore help
```

Also available as `-h` or `--help`.

---

## Agent Permissions

Agents run with restricted Claude Code tool permissions. Each role has a default set:

### Developer Agent

**Default:** `Bash,Edit,Write,Read,Glob,Grep`

Full access. The developer agent can run shell commands, read and write files, and search the codebase. This is the most permissive role because it needs to implement features.

**Security note:** The developer agent can execute arbitrary shell commands. If your project has sensitive credentials accessible via the shell, consider removing `Bash` from the permission set.

### Validator Agent

**Default:** `Bash,Read,Write,Glob,Grep`

Can run tests and read files, but cannot use `Edit`. The validator checks the developer's work by running the validation command and inspecting outputs. `Write` is included so it can write the result signal file.

### Reviewer Agent

**Default:** `Read,Glob,Grep`

Read-only. The architecture reviewer can examine code but cannot modify it. When `review --update-docs` is used, `Edit,Write` are added automatically so it can update documentation files.

### Customizing Permissions

Override in `config.yaml`:

```yaml
permissions:
  developer: "Read,Edit,Write,Glob,Grep"    # No Bash — no shell access
  validator: "Bash,Read,Glob,Grep"           # No Write
  reviewer: "Read,Glob,Grep"                 # Default (read-only)
```

Permissions are comma-separated Claude Code tool names. Available tools: `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`.
