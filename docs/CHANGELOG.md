# Changelog

All notable changes to aishore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.6] - 2026-04-06

### Fixed

- **Install/update resilient to GitHub CDN blocking** — both `install.sh` and `cmd-update.sh` now try `raw.githubusercontent.com` first, then fall back to the GitHub Contents API (base64-decoded). Auth tokens from `gh` CLI or `GITHUB_TOKEN` env var are injected into both routes automatically.

## [0.5.5] - 2026-04-06

### Fixed

- **Pre-existing test issues identified** — `checksums` command no longer rejected (became valid), drift check references missing script
- Stress-tested all 0.5.4 worktree/merge paths: 5-sprint cycles, groom-modified backlogs, developer `git add -A`, interrupted sprints — all clean

## [0.5.4] - 2026-04-06

### Fixed

- **Backlog JSON corruption on multi-sprint sessions** — backlog mutations (mark complete, archive, remove) moved from worktree to base branch post-merge, eliminating stash/pop conflicts that corrupted JSON and stopped subsequent sprints
- **Stash/pop removed from merge path** — feature branches now contain only code changes; merges are clean with no backlog file conflicts
- **Ctrl+C no longer destroys committed work** — EXIT trap preserves the feature branch for recovery, only cleans up the worktree directory
- **Failure metadata lost with worktree** — agent logs, result.json, and failure context are now copied to base branch before worktree destruction; failCount and lastFailReason persist across sessions
- **`_record_sprint_failure` called with wrong arguments** — was passing 4 args (ITEM_ID, source, reason, detail) to a 2-arg function, corrupting failure tracking
- **Double-counted failures on setup command failure** — removed duplicate counter increments and redundant `_cleanup_worktree` call
- **Sprint loop counter corruption** — `_build_prior_failure_context` now declares `local i`, preventing clobber of the outer sprint loop variable when retries > 0
- **Safety commit scope** — `_safety_commit` now excludes `backlog/` and `.aishore/` via pathspec, preventing operational files from landing on feature branches
- **`--no-merge` diff stats** — archive entries now record accurate line stats by diffing against the feature branch tip instead of HEAD
- **`_remove_worktree` `&&`/`||` precedence** — restructured to prevent silent error swallowing

## [0.5.3] - 2026-04-03

### Added

- **Explicit mode indicator in architect prompt** — `build_agent_prompt()` injects 'You are in [groom|review] mode.' for both groom and review branches (FEAT-100)
- **Verify count cross-check** — `check_result()` rejects developer results where reported verify command count doesn't match actual AC verify count
- **Groomer: structural verify guidance** — prefer `test -f`/`test -d` over content greps on built output (build tools transform/bundle/minify)

### Changed

- **Scope injection wording** — developer prompt now says 'advisory, not strict' — out-of-scope changes flagged as warnings, not failures (FEAT-098)
- **Intent hard gate context in developer prompt** — developers informed that items with intent <20 chars are auto-skipped/rejected (FEAT-097)

### Fixed

- **Lock PID write failure** — cleanup lockdir on PID write failure, closing TOCTOU window (BUG-150)
- **Silent `cd` failure** — `cd "$PROJECT_ROOT" || true` replaced with loud failure in sprint loop (BUG-151)
- **Predictable worktree paths** — `mktemp -d` replaces `$$`-based pattern, defeating symlink pre-staging (FEAT-096)
- **Groom parse failure swallowed** — `return 0` changed to `return 1` on jq parse failure (BUG-149)
- **Merge failure leaves dirty state** — `git merge --abort` called before branch cleanup on both squash and --no-ff merge failures (BUG-148)
- **jq variable interpolation** — `now` → `$now` in spec refinement jq expression

## [0.5.2] - 2026-04-01

### Added

- **Maturity protocol enforcement** — `check_result("developer")` rejects pass results missing `.phases` evidence. Developer must prove critique findings and harden verification counts.
- **Mandatory validator ac_results** — validator prompt injection requires structured per-AC results. Warning logged when missing.
- **AC verify deduplication** — validator told to trust orchestrator AC results, not re-run. Focus redirected to intent and integration.
- **Integration enforcement** — disconnected code is a hard failure when item has verify commands, advisory for scaffolding items.
- **Scope enforcement** — post-commit `_check_scope_warnings()` compares changed files against declared scope globs, logs warnings.
- **Regression suite management** — `clean --regression` with backup, `regression-skip.json` to skip entries by item ID.
- **`--clear-depends` flag for `backlog edit`** — clear all dependencies from an item.
- **Stale dependency cleanup** — `backlog rm` now removes the deleted item from `dependsOn` arrays in all other items.

### Changed

- **Retry context** — cap increased from 2000 to 4000 chars. `_capture_retry_failure` extracts file:line from ac_results. Truncated entries preserve compact failure summaries.
- **Validator prompt** — "run every one of them" replaced with "trust orchestrator results."
- **All docs** — PRODUCT.md, ROADMAP.md, README.md, CLAUDE.md rewritten to carry core philosophy: "Ship working code, not evidence of process."

### Fixed

- Guard `git commit` after squash merge — previously commit failure left worktree in bad state.
- Guard `cp` before `rm` in regression clean — previously backup failure still deleted original.
- Clarify AC verify command schema in developer maturity protocol injection.

## [0.5.1] - 2026-04-01

### Changed

- 3x max_turns defaults (75/45/45 for developer/validator/groomer)

## [0.5.0] - 2026-03-31

### Changed

- Purged regression suite — all 17 prior checks were structure tests (grep-based), not behavior tests
- Philosophy shift — execute behavior, not grep for structure

## [0.4.4] - 2026-03-31

### Fixed

- Guard cd and git checkout in lib modules and sprint success path
- Spec refinement runs without worktree, groom crash on bad JSON, sed stat capture
- Safety commit crash, worktree path, sprint item shape
- Sed injection, git error handling, jq masking, worktree TOCTOU race
- Unbound sprint_file in refine_item_spec
- Add Agent to developer permissions for Claude Code parallelism

## [0.4.3] - 2026-03-28

### Changed

- No feature changes (patch release)

## [0.4.2] - 2026-03-27

### Added

- Doc maintenance in sprint pipeline — developer updates docs in same commit
- Backlog sprint quality optimizations

### Changed

- Merge tech-lead + product-owner into unified groomer agent
- Promote scaffold to top-level command
- Downgrade validator from Opus to Sonnet (MODEL_FAST)

### Fixed

- Resolve worktree merge conflicts on sprint tracking files
- Dry-run priority scope and stale scope advisory

## [0.4.1] - 2026-03-26

### Fixed

- Dry-run priority scope and stale scope advisory, clean backlog

## [0.4.0] - 2026-03-25

### Added

- **Regression suite** — AC verify commands saved to regression.jsonl, run as pre-flight before every sprint
- **Adversarial validation** — validator probes implementations with Bash commands, not just diff review
- **Executable AC enforcement** — groomer agents write verify commands for every testable AC
- **Modular architecture** — CLI split into core orchestrator + lazy-loaded lib modules
- Per-file checksum verification in update output

### Changed

- Rebrand: remove CLI theatre, kill parallel mode, fix lock mechanism
- Complete documentation overhaul for modularized codebase

### Fixed

- 35 stale doc references removed
- Hardcoded version removed from README

## [0.3.10] - 2026-03-25

### Added

- Module loader infrastructure for lazy-loaded lib modules
- Modularization backlog — plan for extracting commands to lib/

## [0.3.9] - 2026-03-24

### Added

- Architect scaffolding detection and top-down backlog ordering
- Top-down scaffolding enforcement across all agents

### Fixed

- Copyright headers aligned with Apache-2.0 LICENSE
- Checksum paths regenerated with correct .aishore/ prefix
- Terminology aligned — "mock-only infrastructure" → "mock-only dependencies"

## [0.3.8] - 2026-03-23

### Added

- Warn when auto-pick skips items with missing or too-short intent
- Promote validator agent to Opus for stronger quality gate

### Changed

- README rewritten as value-focused pitch
- Deduplicate shared patterns across CLI

## [0.3.7] - 2026-03-21

### Added

- **`--remove-ac N` flag for `backlog edit`**: Remove a specific acceptance criterion by 1-based index (BUG-116)
- **Queued item count with per-priority breakdown logged at auto session start** (BUG-117)

## [0.3.6] - 2026-03-21

### Added

- **`--priority` filter for `backlog list`**: Filter items by priority level (e.g., `--priority must`) (BUG-109)
- **`--ready` / `--no-ready` filters for `backlog list`**: Filter items by readiness state (BUG-106)
- **`--limit` and `--all` flags for `backlog history`**: Default output capped at 20 items, `--all` shows everything (BUG-104)
- **`--preview` flag for `backlog populate`**: Snapshot backlog, run agent, display new items, then restore originals (FEAT-035)
- **Scope display in `backlog show`**: Scope globs now rendered when present (BUG-105)
- **Item titles in `status` recent sprints**: Status output includes item titles alongside IDs (BUG-107)

### Fixed

- `cmd_status --watch` now exits cleanly when sprint status is `completed` (BUG-096)
- Corrected field name in `protect_items_from_groom` from `groomedNotes` to `groomingNotes` (BUG-097)
- Preserved sprint archive entry before worktree cleanup destroys it (BUG-098)
- Prevent `auto --no-merge` from re-picking already-completed items via `COMPLETED_IDS` associative array (BUG-099)
- Consolidated 6 `jq` calls in `cmd_diagnose` into one (BUG-080)
- Unset `GROOM_MONITOR` after each groom `run_agent` call to prevent leaking into subsequent calls (BUG-101)
- Use real newlines in scope violations string instead of literal `\n` (BUG-102)
- Atomic temp-file-then-move writes in `protect_items_from_groom` and `enforce_groom_limits` (BUG-103)
- Sort new groom items by priority rank before applying cap (BUG-108)
- Guard `cmd_checksums` against overwriting `checksums.sha256` with empty temp file (BUG-111)

## [0.3.5] - 2026-03-21

### Added

- **Multi-backlog support**: `config.yaml` accepts a `backlog_files` list; `pick_item`, `list_pickable_ids`, and related helpers scan all declared backlog files (FEAT-027)
- **Retry intelligence**: `_capture_retry_failure` captures git diff and failure context, carried into subsequent developer retry cycles (FEAT-028)
- **`--category` flag**: Filter items by category in `run` and `auto` commands (FEAT-029)
- **Completion notification**: Terminal bell fires on all auto session exit paths — drain complete, circuit-breaker, and `--limit` reached (FEAT-030)
- **`--limit N` flag**: Cap the number of items processed per auto/run session (FEAT-031)
- **Real-time streaming**: Developer agent output streams to terminal during sprint execution (FEAT-032)
- **Live session progress counter**: Auto mode prints item count at start of each sprint (FEAT-033)
- **End-of-session summary table**: Auto runs print a summary table on all exit paths with `--no-summary` opt-out (FEAT-034)

### Fixed

- `collect_done_ids` now scans `sprints.jsonl` for archived items — cleaned items no longer cause false unmet-dependency warnings (BUG-035)
- Trimmed `print_groom_summary` and `print_groom_diff` to bare essentials (BUG-067)
- Removed unused `update_desc` variable from `cmd_backlog_edit` (BUG-079)
- `mark_complete` now archives item title alongside priority/category for `backlog history` (BUG-081)
- Converted `context_args` and `groom_context` from word-split strings to Bash arrays (BUG-083)
- Consolidated `_status_output` to one `jq` pass per file (BUG-084)
- `cmd_review` resolves architect permissions from `--update-docs` flag directly, not `output_file` proxy (BUG-085)
- `mark_complete` uses `AISHORE_BASE_BRANCH` for diff stats instead of `HEAD~1` (BUG-086)
- Preserved refinement hint through `_run_retry_loop` so developer agent receives it on retry (BUG-087)
- Replaced GNU-only `head -n -1` with portable `sed '$d'` in `protect_items_from_groom` (BUG-088)
- Return to base branch when `mark_complete` fails in `_handle_sprint_success` (BUG-089)
- Accumulate `total_attempts` across both retry loops in `--refine` path (BUG-090)
- Removed spurious `log_error` from `pick_item` when no eligible item found — auto-mode exits cleanly (BUG-091)
- Added `GROOM_MONITOR=true` to auto-groom `run_agent` calls in sprint loop (BUG-092)
- Removed undefined `release_lock` call from `setup_sprint_environment` early-exit path (BUG-093)
- `run_ac_verification` now catches jq failures explicitly — `2>/dev/null` suppression removed (BUG-094)

### Changed

- Slimmed `README.md` from ~500 lines to storefront format (FEAT-021)

## [0.3.4] - 2026-03-20

### Added

- **`backlog history` command**: Query completed sprints from the archive with `--limit N` flag
- **`diagnose` command**: Show last sprint failure diagnostics with inline 20-line log tail and agent log path
- **`status --watch` mode**: Live refresh status display until sprint completes
- **`--depends-on` flag**: Add dependency relationships via `backlog add` and `backlog edit`; dependencies now append instead of replace
- **`--scope` flag for `backlog add`**: Set scope globs when adding items
- **`--step` flag**: Add implementation steps via `backlog add` and `backlog edit`
- **`--pr` flag**: Create GitHub PRs instead of merging (`run --pr`)
- **`--auto-review` flag**: Auto-run architecture review after auto mode completes
- **Dependency readiness gate**: `backlog check` verifies `dependsOn` items are complete, shows each dependency's current status
- **Blocked dependency indicator**: `backlog list` shows blocked items
- **Complexity gate**: Warns on under-specified items during grooming
- **Configurable auto-fix command**: `fix_cmd` config option for automatic code fixes between retries
- **Configurable squash-merge strategy**: Merge strategy configuration in config.yaml
- **Git worktree isolation**: `--worktree` mode for running sprints in isolated worktrees
- **Groom convergence limits**: Prevent unbounded grooming busywork with max-rounds cap
- **Intent semantics in agent prompts**: Developer and validator agents now understand intent as the north star when AC conflicts with spec

### Fixed

- Use ANSI-C quoting for real newlines in AC verify report
- Log skipped items when merge conflict aborts multi-sprint run
- Remove dead if/else branch in AC JSON construction
- Replace byte-based output truncation with line-based truncation
- Warn unconditionally when config.yaml has content but yq is missing
- Display AC `{text, verify}` objects as plain text in `backlog show`
- Truncate VALIDATE_CMD output in retry prompts to prevent prompt bloat
- Add `--clear-ac` and `--clear-scope` flags to `backlog edit`
- Make `remove_items_by_status` accept relative filename
- Reject unknown options across all subcommands (`run`, `review`, `update`, `groom`, `metrics`, `backlog populate/show/check`)
- Include all supported flags in `backlog edit` usage messages
- Add `validate_arg` calls for all value-bearing flags across CLI commands
- Return non-zero exit from `backlog check` when gates fail
- JSON-encode pending AC entry in mid-loop flush of `backlog edit`
- Check `remove_items_by_status` return code in `clean`
- Surface errors from `mark_item_failed` instead of swallowing with `|| true`
- Make stash pop failures visible with actionable guidance
- Use agent summary in commit messages instead of generic text
- Verify item existence in `resolve_backlog_file` before returning
- Show currently running sprint item in `status` output
- Format duration column in `backlog history` as human-readable time
- Add TITLE column to `backlog history` output
- Filter non-numeric ID suffixes in `next_id()`
- Robust JSON extraction in `refine_item_spec`
- Replace `md5sum` with portable `_file_hash` in groom progress tracking
- Protect existing items from groomer rewrites in all code paths
- Suppress ShellCheck SC1010 false positive in backlog list jq filter

### Changed

- **Extract `run_validated_command()` helper**: Eliminates 3 duplicated timeout-aware command execution blocks
- **Decompose `_run_retry_loop()`**: Split into `_run_preflight`, `_run_developer_cycle`, `_run_validation_cycle`
- **Decompose `cmd_run()`**: Split into `cmd_run_parse_args`, `setup_sprint_environment`, `run_sprint_loop`, `print_sprint_summary` (30 lines, down from ~200)
- **Extract shared `PICKABLE_ITEMS_FILTER`**: Single source of truth for item filtering in `pick_item()` and `list_pickable_ids()`
- **Replace global side-effect variables**: Five globals eliminated, functions return via stdout with explicit capture
- **Standardize error handling**: Functions `log_error` + `return 1`; only `main`, `acquire_lock`, and `require_tool` may `exit`
- **Extract shared backlog iteration helpers**: `map_backlog_files`, `find_first_backlog`, `snapshot_backlog_files`, `restore_backlog_files`, `sum_backlog_count`
- **Extract init scaffold heredocs to template files**: 6 template files in `.aishore/templates/`, `_init_scaffold_files` uses `cp`/`sed` exclusively
- **Extract help text to `.aishore/help.txt`**: `cmd_help` reads via `sed`; `cmd_usage` is now an alias
- **Move populate-mode docs to files**: Product-owner guidance and CLAUDE.md snippet moved out of bash string literals

### Removed

- **Interactive mode from `backlog add`**: `--interactive` flag removed; use flags (`--title`, `--priority`, etc.) exclusively
- **`backlog sync` command**: 152 lines of dead code removed

### Documentation

- **docs/ARCHITECTURE.md**: Unified system architecture document covering pipeline, agents, quality gates, and design decisions
- **docs/CONTRIBUTING.md**: Moved from root, added Agent Prompt Authoring section
- **docs/CHANGELOG.md**: Moved from project root to `docs/`
- **docs/QUICKSTART.md**: Zero to first completed sprint guide
- **docs/CONFIGURATION.md**: Comprehensive configuration reference
- **docs/PROBLEMS.md**: Known issues and workarounds
- **docs/ROADMAP.md**: Project roadmap
- Synced 5 missing flags (`--refine`, `--quick`, `--auto-review`, `--dry-run` for auto, `status --watch`) to README and CLAUDE.md

## [0.3.3] - 2026-03-19

### Fixed

- **Update/install output**: Improved output with clear installed-files summary

## [0.3.2] - 2026-03-19

### Added

- **`backlog populate` command**: AI-populates the backlog from PRODUCT.md (or PRD.md, README.md) using the Product Owner agent. Reads the product requirements document, decomposes the vision into concrete, right-sized backlog items with intent, acceptance criteria, and priorities. Checks existing items to avoid duplicates. Fully non-interactive — designed for agent-driven workflows.
- **`init -y/--yes` flag**: Non-interactive initialization that accepts all auto-detected defaults (project name, validation command) without prompting. Enables fully hands-off setup: `init -y && backlog populate && auto done`.
- **Intent-driven populate prompt**: The populate agent receives comprehensive guidance on intent-driven development — why intent matters to the downstream pipeline, gold-standard examples, bad-item examples with failure explanations, right-sizing guidance, and anti-patterns to avoid. DEFINITIONS.md is passed as additional context.
- **Empty PRODUCT.md guard**: `backlog populate` detects scaffold templates (mostly comments/blanks) and refuses to run, preventing wasted agent calls on empty docs.

### Fixed

- **Init summary display**: Replaced fragile `ls` piping with explicit file existence checks — prevents spurious `<not found>` for freshly scaffolded docs.
- **Populate init guard**: `backlog populate` checks for `backlog.json` and gives a clear "run init first" message instead of a confusing error.
- **Drift script regex**: Fixed flag extraction to detect flags after pipe characters (e.g., `-y|--yes`), added `cmd_init` to flag parity checks.
- **Copyright notice**: Help and usage output now show the copyright notice.

### Documentation

- Updated How It Works diagram to reflect actual sprint flow
- All docs synced: README.md, CLAUDE.md, .aishore/README.md, help text

## [0.3.1] - 2026-03-18

### Fixed

- **Installer stdout pollution**: Fixed staging_dir scope errors in install.sh
- **Update checksum verification**: Hardened checksum verification in both update and install paths
- **Distribution pipeline**: Checksum verification, dynamic file discovery from manifest

## [0.3.0] - 2026-03-18

### Changed

- **Shared constants**: Extracted `BACKLOG_FILES` array and `ITEM_PROJECTION` jq expression, replacing ~10 hardcoded loops and 2 inline projections
- **Config loading**: Consolidated 11 individual yq calls in `load_config()` and 8 env var checks in `_apply_env_overrides()` into data-driven mapping loops
- **`cmd_run` decomposition**: Extracted `_run_dry_run()`, `_run_retry_loop()`, and `_handle_sprint_success()` — main loop is now a clear pick → branch → retry → success sequence
- **`cmd_init` decomposition**: Extracted `_init_check_prereqs()`, `_init_detect_project()`, and `_init_scaffold_files()` — cmd_init is now a thin orchestrator
- **`cmd_update` helper**: Extracted `_fetch_and_stage()` replacing 6 repetitive fetch+verify blocks with one-liner calls

### Fixed

- **Stale README**: Removed non-existent `--auto-commit` flag reference, added `auto` command rows to command reference table

## [0.2.3] - 2026-03-18

### Added

- **`auto` command — autonomous sprint orchestration** ([#6](https://github.com/simonplant/aishore/issues/6)): New top-level command that drives the backlog to completion autonomously. Scoped by priority: `auto done` (all items), `auto p1` (must + should), `auto p0` (must only), `auto p2` (must + should + could).
  - Auto-grooms when ready items drop below threshold (tech-lead + product-owner agents)
  - Tracks failure patterns across the session, passes context to subsequent developer agents
  - Circuit breaker stops after N consecutive failures (default: 5, configurable via `--max-failures`)
  - Priority scope filtering: stops when all in-scope items are complete
  - Mission-oriented exit messages: "Mission complete", "Mission aborted" (circuit breaker), "Mission ended"
  - Composes with `--retries`, `--no-merge`, and `--dry-run`
- **Validation command injection**: Developer agent prompt now includes the configured validation command, so the agent knows what to run before signaling completion
- **Auto mode configuration**: `auto.groom_threshold` and `auto.max_failures` in `config.yaml`, plus `AISHORE_AUTO_GROOM_THRESHOLD` and `AISHORE_AUTO_MAX_FAILURES` env vars

## [0.2.2] - 2026-03-14

### Fixed

- **Default agent permissions too restrictive for non-git commands** ([#2](https://github.com/simonplant/aishore/issues/2)): Changed default developer permissions from `Bash(git:*),Edit,Write,Read,Glob,Grep` to `Bash,Edit,Write,Read,Glob,Grep` and validator from `Bash(git:*),Read,Glob,Grep` to `Bash,Read,Write,Glob,Grep`. This allows developer agents to run build/test/lint toolchain commands (`npm install`, `npm test`, `pytest`, `go test`, `cargo build`, etc.) without requiring a permissions override in `config.yaml`. The `--permission-mode acceptEdits` flag already provides a safety gate; restricting Bash to `git:*` was redundant and broke real workflows.

## [0.2.1] - 2026-03-12

### Changed

- **Consolidated backlog helpers**: Extracted shared JSON operations (`update_item`, `add_item`, `remove_item`, `remove_items_by_status`) into reusable helper functions, reducing duplication across backlog CRUD and sprint completion logic

## [0.2.0] - 2026-03-12

### Added

- **`backlog` CRUD commands**: Full CLI management of backlog items without editing JSON
  - `backlog list` — List all items with filtering by status, type, and readiness
  - `backlog add` — Add items interactively or with flags (`--title`, `--type`, `--priority`, etc.)
  - `backlog show <ID>` — Show full detail of any item
  - `backlog edit <ID>` — Update fields (`--title`, `--priority`, `--status`, `--ready`, etc.)
  - `backlog rm <ID>` — Remove items with confirmation (or `--force`)
- **Auto-detect project docs**: Agents automatically receive `ARCHITECTURE.md` and `PRODUCT.md` from root or `docs/` as context during sprints
- **Scaffold project docs**: `init` wizard now creates `PRODUCT.md`, `ARCHITECTURE.md`, and `DEFINITIONS.md` templates when they don't already exist

### Fixed

- **Graceful VERSION handling**: CLI no longer crashes when `.aishore/VERSION` is missing — falls back to "unknown" instead of hard-exiting

### Changed

- **VERSION moved into `.aishore/`**: VERSION file now lives at `.aishore/VERSION` alongside the rest of the tool

### Removed

- **Migration script**: Removed `migrate.sh` and all migration references

## [0.1.9] - 2026-03-12

### Fixed

- **Graceful VERSION handling**: CLI no longer crashes when `.aishore/VERSION` is missing — falls back to "unknown" instead of hard-exiting, so commands like `groom` and `run` work even without a VERSION file

### Changed

- **VERSION moved into `.aishore/`**: VERSION file now lives at `.aishore/VERSION` alongside the rest of the tool, keeping the project root clean

## [0.1.8] - 2026-03-11

### Fixed

- **VERSION as single source of truth**: CLI reads version from `.aishore/VERSION` at runtime instead of hardcoding it inline

## [0.1.7] - 2026-03-10

### Fixed

- **Init file detection**: Added missing `docs/prd.md` to project type detection
- **ShellCheck compliance**: Renamed jq variable `done` to avoid SC1010 warning
- **Case consistency**: Standardized `PRODUCT.md` references to uppercase

### Changed

- **Groom uses fast model**: Groom agent now uses Sonnet (fast model) instead of Opus for faster turnaround

## [0.1.6] - 2026-02-24

### Changed

- **Default models updated**: Primary model now uses `claude-opus-4-6`, fast model uses `claude-sonnet-4-6`

## [0.1.5] - 2026-01-28

### Added

- **`clean` command**: Remove done items from `backlog.json` and `bugs.json` with `--dry-run` support

## [0.1.4] - 2026-01-28

### Added

- **Progress indication**: Agent polling loop now shows periodic elapsed-time messages instead of silent waiting
- **Prerequisite checks**: `require_tool` helper validates `jq` and `git` are installed before runtime commands, with clear error messages
- **Actionable error messages**: All error messages now suggest remediation (e.g., "No ready items" tells you to run `groom` or edit the backlog)
- **Safe failure recovery**: Sprint failures stash pre-existing uncommitted changes and restore them afterward, instead of destroying them with `git checkout -- .`

### Fixed

- **Config precedence**: Environment variables now correctly override `config.yaml` values (previously config.yaml silently won)
- **macOS compatibility**: `setsid` fallback for systems where it's unavailable (macOS)
- **`pick_item` field consistency**: Both specific-ID and auto-pick paths now return the same JSON shape
- **`_apply_env_overrides` exit code**: Added `return 0` to prevent `set -e` from killing the script when no env vars are set
- **yq warning false positive**: No longer warns about yq when only `validation.timeout` is set in config.yaml
- **`read` calls**: Added `-r` flag to all 5 interactive `read -p` calls to prevent backslash interpretation
- **`hash_cmd` quoting**: Converted from string to array for safe word-splitting

### Changed

- **Unified agent invocation**: `cmd_groom` and `cmd_review` now use `run_agent()` instead of calling `run_agent_process()` directly
- **Version management**: `.aishore/VERSION` is the single source of truth; CLI reads it at runtime
- **Update command**: Fetches remote `.aishore/VERSION` for version comparison
- **`migrate.sh`**: Reads version dynamically instead of hardcoding it

### Removed

- **`icebox.json` references** in `migrate.sh` (file was previously removed from the project)
- **Hardcoded gitignore entries** in `cmd_init` (now reads from `gitignore-entries.txt`)
- **Machine-specific entries** in `.claude/settings.local.json`

### Documentation

- Fixed `config.yaml` init template showing agent timeout as 600 instead of 3600
- Added `AISHORE_VALIDATE_CMD` and `AISHORE_VALIDATE_TIMEOUT` to help text
- Marked Product Owner Review/Evolve modes as planned in agent prompt
- Removed hardcoded line count references from CLAUDE.md and CONTRIBUTING.md
- Archive file now passed as context to groom command when it exists

## [0.1.3] - 2026-01-27

### Added

- **Checksum-verified updates**: `update` command fetches SHA-256 checksums and verifies all files before installing
- **`checksums` command**: Regenerate `checksums.sha256` for update verification
- **Concurrency guard**: `flock`-based locking prevents concurrent aishore processes
- **Setup wizard**: `init` is now an interactive 6-step wizard that checks prerequisites (git, claude, jq), detects project name and validation command, and scaffolds all files
- **Validation command execution**: aishore now executes `validation.command` from config between developer and validator agents
- **Failed item skipping**: When running multiple sprints, failed items are excluded from subsequent picks
- **Temp directory management**: All temp files use a single cleaned-up `mktemp` directory
- **Refactored agent execution**: Shared `run_agent_process()` with `AGENT_OUTPUT_FILE` support for capturing `--print` output
- **Shared utilities**: `build_context()`, `build_completion_contract()`, `count_ready_items()` reduce duplication

### Fixed

- **Archive path inconsistency**: `migrate.sh` copied archives to `.aishore/data/archive/` but CLI reads from `backlog/archive/` — now consistent
- **Dead directory**: `install.sh` no longer creates unused `.aishore/data/archive/`
- **Gitignore consistency**: All scripts (`cmd_init`, `migrate.sh`, `gitignore-entries.txt`) now produce identical entries
- `mark_complete()` uses proper jq for archive entries instead of string interpolation
- `create_sprint()` uses jq for safe JSON generation instead of heredoc with string interpolation

### Changed

- `init` command is now an interactive wizard instead of a silent scaffolder
- `review` command saves output to a persistent log file and prints it to stdout
- `update` command uses staged fetch-then-verify-then-install approach (atomic)
- `update --no-verify` requires `--force` as a safety measure
- `groom` command exits non-zero on agent failure

## [0.1.2] - 2025-01-25

### Added

- **Curl installer**: One-line install via `curl -sSL .../install.sh | bash`
- **Migration dry-run**: `migrate.sh --dry-run` shows what would change without modifying files
- **Migration force mode**: `migrate.sh --force` skips confirmation prompts
- **Update enhancements**: `--check` alias for `--dry-run`, `--force` to re-download
- Update command now also fetches `gitignore-entries.txt`

### Changed

- README now shows curl install as primary installation method
- Migration script shows visual state analysis before changes

## [0.1.1] - 2025-01-24

### Added

- **Backlog separation**: User content now lives in `backlog/` at project root (not inside `.aishore/`)
- **Self-update command**: `aishore update` fetches latest from GitHub
- **Run by ID**: `aishore run TEST-006` runs specific item
- **Auto-detect CLAUDE.md**: No longer need `context/project.md`
- **Self-contained CLI**: All library functions inlined (no `lib/common.sh`)
- **Migration script**: `migrate.sh` upgrades from old structures

### Changed

- Agent timeout increased from 600s to 3600s (1 hour)
- Config is now optional (sensible defaults built-in)

### Removed

- `.aishore/lib/` directory (inlined into script)
- `.aishore/context/` directory (auto-detect CLAUDE.md)
- `.aishore/plan/` directory (moved to `backlog/`)

## [0.1.0] - 2025-01-24

### Added

- Initial release of aishore as a standalone tool
- Single CLI entry point: `run`, `groom`, `review`, `metrics`, `init`, `version`, `help`
- Configuration via `config.yaml` with environment variable overrides
- Support for custom validation commands (any language/framework)
- Agent prompts: developer, validator, tech-lead, architect, product-owner
- Completion contract via `result.json`
- Sprint archive in JSONL format
- macOS compatibility (gtimeout support)

### Structure

- `.aishore/` self-contained directory
- `backlog/` for user content (backlog.json, bugs.json, sprint.json)
- `data/` for runtime files (logs, status)
