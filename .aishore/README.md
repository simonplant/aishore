# .aishore — Internal Tool Directory

This directory contains the aishore sprint runner. See the [project README](../README.md) for full documentation.

## Contents

```
.aishore/
├── aishore              # Self-contained CLI (Bash)
├── checksums.sha256     # SHA-256 checksums for update verification
├── config.yaml          # Optional overrides (sensible defaults built-in)
├── gitignore-entries.txt
├── agents/              # Agent prompts
│   ├── developer.md     # Implements backlog items
│   ├── validator.md     # Checks acceptance criteria
│   ├── tech-lead.md     # Grooms bugs/tech debt
│   ├── product-owner.md # Grooms feature backlog
│   └── architect.md     # Architecture review
└── data/                # Runtime (gitignored)
    ├── logs/            # Sprint and review logs
    └── status/          # result.json, lock file
```

## Quick Reference

```bash
.aishore/aishore run [N]          # Run N sprints (default: 1)
.aishore/aishore run <ID>         # Run specific item
.aishore/aishore groom            # Groom bugs/tech debt
.aishore/aishore groom --backlog  # Groom features
.aishore/aishore review           # Architecture review
.aishore/aishore metrics          # Sprint metrics
.aishore/aishore update           # Update from upstream
.aishore/aishore init             # Setup wizard
.aishore/aishore help             # Full command list
```

## Updating

This directory can be safely replaced or updated without affecting `backlog/` or `config.yaml`:

```bash
.aishore/aishore update           # Checksum-verified update
```

## Configuration

Edit `config.yaml` to override defaults, or use environment variables:

| Setting            | Config key            | Env var                    |
|--------------------|-----------------------|----------------------------|
| Validation command | `validation.command`  | `AISHORE_VALIDATE_CMD`     |
| Validation timeout | `validation.timeout`  | `AISHORE_VALIDATE_TIMEOUT` |
| Primary model      | `models.primary`      | `AISHORE_MODEL_PRIMARY`    |
| Fast model         | `models.fast`         | `AISHORE_MODEL_FAST`       |
| Agent timeout      | `agent.timeout`       | `AISHORE_AGENT_TIMEOUT`    |
