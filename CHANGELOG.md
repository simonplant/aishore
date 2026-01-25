# Changelog

All notable changes to aishore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- `data/` for runtime files (logs, status, archive)
