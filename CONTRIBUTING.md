# Contributing to aishore

Thanks for your interest in contributing to aishore!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/simonplant/aishore.git
cd aishore

# The tool is ready to use - no build step needed
.aishore/aishore help
```

## Requirements

- Bash 4.4+
- jq
- shellcheck (for linting)
- On macOS: `brew install coreutils` (for `gtimeout`)

## Code Style

### Bash Scripts

- Use `set -euo pipefail` at the start
- Quote all variables: `"$var"` not `$var`
- Use `[[ ]]` for conditionals, not `[ ]`
- Use `$(command)` not backticks
- Use `${var:-default}` for optional variables

### Naming

- Functions: `snake_case`
- Local variables: `snake_case`
- Constants/exports: `UPPER_SNAKE_CASE`

## Testing

Before submitting a PR:

```bash
# Run shellcheck
shellcheck .aishore/aishore

# Syntax check all scripts
bash -n .aishore/aishore
bash -n install.sh
bash -n migrate.sh

# Test basic commands
.aishore/aishore help
.aishore/aishore version
.aishore/aishore metrics

# Validate JSON
jq empty backlog/*.json

# Regenerate checksums after modifying tool files
.aishore/aishore checksums
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run shellcheck and tests
5. Regenerate checksums if you changed files in `.aishore/`
6. Commit with conventional commits: `feat:`, `fix:`, `docs:`, etc.
7. Push and create a PR

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `refactor:` — Code refactoring
- `test:` — Tests
- `chore:` — Maintenance

## Architecture

```
project/
├── backlog/              # User content (version controlled by user)
│   ├── backlog.json
│   ├── bugs.json
│   ├── sprint.json
│   └── archive/
└── .aishore/             # Tool (this is what gets updated)
    ├── aishore           # Self-contained CLI
    ├── checksums.sha256  # SHA-256 checksums for update verification
    ├── agents/*.md       # Agent prompts
    ├── config.yaml       # Optional overrides
    └── data/             # Runtime data (logs, status, lock)
```

Key design decisions:

- **Separation of concerns**: Tool (`.aishore/`) vs user content (`backlog/`)
- **Single file CLI**: All logic in one self-contained script (~1340 lines)
- **Sensible defaults**: Config is optional, env vars for overrides
- **Auto-detect context**: Finds CLAUDE.md automatically
- **Checksum-verified updates**: `update` command verifies SHA-256 before installing
- **Concurrency guard**: `flock`-based locking prevents parallel runs
- **Completion contract**: Agents write to `result.json` to signal done

## Questions?

Open an issue for questions or suggestions.
