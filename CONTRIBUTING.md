# Contributing to aishore

Thanks for your interest in contributing to aishore!

## Development Setup

```bash
git clone https://github.com/simonplant/aishore.git
cd aishore

# No build step needed — the tool is ready to use
.aishore/aishore help
```

## Requirements

- Bash 4.4+
- jq
- shellcheck (for linting)
- git
- On macOS: `brew install coreutils` (for `gtimeout`)

## Code Style

### Bash

- `set -euo pipefail` at the top of every script
- Quote all variables: `"$var"` not `$var`
- `[[ ]]` for conditionals, not `[ ]`
- `$(command)` for substitution, not backticks
- `${var:-default}` for optional variables
- Declare and assign on separate lines to avoid masking return values (`local var; var=$(cmd)`)

### Naming

| Kind               | Convention         | Example              |
|--------------------|--------------------|----------------------|
| Functions          | `snake_case`       | `run_sprint`         |
| Local variables    | `snake_case`       | `item_id`            |
| Constants/exports  | `UPPER_SNAKE_CASE` | `AISHORE_VERSION`    |

## Linting and Testing

Run all of these before submitting a PR:

```bash
# Lint
shellcheck .aishore/aishore

# Syntax check
bash -n .aishore/aishore
bash -n install.sh
bash -n migrate.sh

# Smoke test
.aishore/aishore help
.aishore/aishore version
.aishore/aishore metrics

# Validate JSON
jq empty backlog/*.json

# Regenerate checksums (if you changed any .aishore/ files)
.aishore/aishore checksums
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run shellcheck and smoke tests (see above)
5. Regenerate checksums if you changed files in `.aishore/`
6. Commit using conventional commits (see below)
7. Push and open a PR

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix      | Use for                  |
|-------------|--------------------------|
| `feat:`     | New feature              |
| `fix:`      | Bug fix                  |
| `docs:`     | Documentation only       |
| `refactor:` | Code restructuring       |
| `test:`     | Adding or fixing tests   |
| `chore:`    | Maintenance, CI, tooling |

## Architecture

```
project/
├── backlog/              # User content (version controlled by user)
│   ├── backlog.json      # Feature backlog
│   ├── bugs.json         # Bug/tech-debt backlog
│   ├── sprint.json       # Current sprint state
│   ├── definitions.md    # DoR, DoD, priority/size definitions
│   └── archive/          # Completed sprint history
│       └── sprints.jsonl
└── .aishore/             # Tool (this is what gets updated)
    ├── aishore           # Self-contained CLI (~1370 lines)
    ├── checksums.sha256  # SHA-256 checksums for update verification
    ├── config.yaml       # Optional overrides
    ├── agents/           # Agent prompts (developer, validator, tech-lead, architect, product-owner)
    └── data/             # Runtime data (logs, status, lock)
```

### Key Design Decisions

- **Separation of concerns** — Tool (`.aishore/`) vs user content (`backlog/`)
- **Single-file CLI** — All logic in one self-contained Bash script
- **Sensible defaults** — Config is optional; env vars available for overrides
- **Auto-detect context** — Finds `CLAUDE.md` automatically
- **Checksum-verified updates** — `update` command verifies SHA-256 before installing
- **Concurrency guard** — `flock`-based locking prevents parallel runs
- **Completion contract** — Agents write to `result.json` to signal done

## Questions?

Open an issue for questions or suggestions.
