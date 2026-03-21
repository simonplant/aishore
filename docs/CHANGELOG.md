# Changelog

All notable changes to aishore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.5] - 2026-03-21

### Fixed

- **BUG-035**: `collect_done_ids` now scans archive entries for dependency resolution — archived/cleaned items no longer cause false "unmet dependency" blocks
- **BUG-036**: `refine_item_spec` JSON extraction handles indented or wrapped agent output correctly
- **BUG-037**: `backlog history` title column now populated from archive (was always showing `-`)
- **BUG-038**: Replaced `md5sum` with portable `_file_hash` in groom progress tracking (fixes macOS/BSD compatibility)
- **BUG-039**: `backlog edit --depends-on` now appends to the `dependsOn` array instead of replacing it
- **BUG-041**: Timeout command detection cached at startup instead of repeated per-sprint runtime checks
- **BUG-057**: `resolve_backlog_file` no longer redundantly re-checks expected file in the fallback loop
- **BUG-058**: Date portability — BSD fallback added to all `date` calls that were Linux-only
- **BUG-059**: Removed TODO placeholder links from `docs/PROBLEMS.md`
- **BUG-064**: Simplified AC and step accumulation logic in `backlog add` and `backlog edit`
- **BUG-066**: `backlog history` output simplified to essential listing; extraneous fields removed
- **BUG-079**: Removed `update_desc` tracking from `cmd_backlog_edit` (dead state, never read)
- **BUG-081**: `backlog history` title column now stored in archive at sprint completion — was always `-`
- **BUG-083**: `context_args` passed as array instead of word-split string — prevents argument splitting bugs
- **BUG-084**: `_status_output` consolidated 6 separate `count_by_status` jq calls into one pass per file
- **BUG-085**: Review architect agent now correctly gets read-only permissions unless `--update` flag is set
- **BUG-086**: `mark_complete` sprint diff stats use full commit range instead of `HEAD~1..HEAD` (fixes multi-commit sprints)
- **BUG-087**: Refinement context (`retry_extra_prompt`) preserved across `_run_retry_loop` invocations — was being cleared on each call
- **BUG-088**: Replaced `head -n -1` with portable equivalent in `protect_items_from_groom` (BSD `head` compatibility)
- **BUG-089**: `_handle_sprint_success` now returns to main branch if `mark_complete` fails — no longer strands git on feature branch
- **BUG-090**: `total_attempts` correctly accumulates across `--refine` path; second `_run_retry_loop` no longer resets count to zero

### Changed

- **BUG-040**: Extracted `run_validated_command()` helper — eliminates 3 duplicated timeout-aware command execution blocks
- **BUG-042**: Extracted `require_numeric_arg()` helper — numeric argument validation no longer duplicated across multiple commands
- **BUG-043**: Decomposed `_run_retry_loop()` into `_run_preflight`, `_run_developer_cycle`, `_run_validation_cycle`
- **BUG-044**: Decomposed `cmd_run()` into `cmd_run_parse_args`, `setup_sprint_environment`, `run_sprint_loop`, `print_sprint_summary` (~30 lines, down from ~200)
- **BUG-045**: Extracted `PICKABLE_ITEMS_FILTER` constant — single source of truth for item filtering in `pick_item()` and `list_pickable_ids()`
- **BUG-046**: Replaced five global side-effect variables with explicit function returns via stdout capture
- **BUG-047**: Standardized error handling — functions use `log_error` + `return 1`; only `main`, `acquire_lock`, and `require_tool` may `exit`
- **BUG-048**: Extracted shared backlog iteration helpers: `map_backlog_files`, `find_first_backlog`, `snapshot_backlog_files`, `restore_backlog_files`, `sum_backlog_count`
- **BUG-049**: Extracted shared option parser to reduce duplication across `cmd_*` functions
- **BUG-050**: Replaced JSON array string concatenation with `jq -s` in `backlog add`
- **BUG-051**: Reduced double jq parsing — all needed fields extracted in one pass
- **BUG-052**: Removed unused and redundant variable declarations throughout
- **BUG-053**: Replaced `echo` with `printf` for variable output throughout the script
- **BUG-054**: Hardcoded safe fields in `protect_items_from_groom()` extracted to a declared constant
- **BUG-055**: Duplicate CLI commands section in groom agent prompts factored out to shared preamble
- **BUG-060**: Init scaffold heredocs extracted to template files in `.aishore/templates/`; `_init_scaffold_files` uses `cp`/`sed` exclusively
- **BUG-061**: Help text extracted to `.aishore/help.txt`; `cmd_help` reads via `sed`; `cmd_usage` is now an alias
- **BUG-062**: Populate-mode docs and `CLAUDE.md` snippet moved from bash string literals to files
- **BUG-067**: Groom presentation functions trimmed to bare essentials; `cmd_groom` output slimmed
- **BUG-068**: `enforce_groom_limits` and `protect_items_from_groom` tightened — redundant checks removed
- **BUG-069**: Backlog `populate` deduplicated with `cmd_groom` flow — shared grooming path
- **BUG-070**: Three merge strategies consolidated into parameterized merge flow
- **BUG-071**: `cmd_run` auto-review and verbosity trimmed; `--auto-review` flag now cleaner
- **BUG-073**: Extracted `_find_prd` helper; product/arch detection unified in init flow
- **BUG-074**: `cmd_metrics` refactored to compute once, render twice — eliminates redundant jq passes
- **BUG-075**: Sub-shell jq extractions in `create_sprint` and `mark_complete` collapsed into single calls
- **BUG-076**: npm detection block in `_init_detect_project` collapsed to single conditional
- **BUG-077**: Single-use nested helpers in `cmd_update` inlined — reduces call indirection
- **BUG-078**: Advisory complexity hints moved out of `check_readiness_gates` into a dedicated advisory function

### Removed

- **BUG-063**: Interactive mode (`--interactive` flag) removed from `backlog add` — use flags exclusively
- **BUG-065**: `backlog sync` command removed (152 lines of dead code)

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
- **Validation command execution**: Sprint runner now executes `validation.command` from config between developer and validator agents
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
