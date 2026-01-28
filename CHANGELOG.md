# Changelog

All notable changes to aishore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Version management**: `VERSION` file is the single source of truth; CLI reads it at runtime with inline fallback for installed copies
- **Update command**: Fetches remote `VERSION` file instead of grepping the script for version comparison
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
