# aishore

[![Version](https://img.shields.io/github/v/release/simonplant/aishore)](https://github.com/simonplant/aishore/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)]()
[![Shell](https://img.shields.io/badge/shell-bash%204.4%2B-green)]()
[![Claude Code](https://img.shields.io/badge/requires-Claude%20Code%20CLI-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

**Autonomous sprint orchestration for Claude Code -- from backlog to merged code, hands-off.**

aishore is a drop-in sprint orchestration tool that reliably develops software in a guided and automated way -- aligned to commander's intent and quality standards. You define what must be true (intent), what to build (backlog), and how to verify it (acceptance criteria). aishore picks items, implements them through a maturity protocol (implement, critique, harden), validates against your intent, and archives completed work. You come back to code that was built right, for the right reasons.

```
You: define intent + backlog  -->  aishore develops, critiques, hardens  -->  You: review quality work
```

## Why aishore?

Vibe coding showed that AI can write code from natural language, but "just vibe it" breaks down at project scale -- no memory between sessions, no quality gate, no way to batch work or hold the AI to a standard. aishore is the next step: **structured intent-based batch development with inline critic loops**. You express *intent* (what must be true when done) and aishore runs full development sprints autonomously, catching bugs and edge cases before they escape. This is not vibe coding. This is **sprint coding**.

## Quick Start

```bash
# Install
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
.aishore/aishore init -y

# Run your first sprint
.aishore/aishore backlog add --title "Add health check endpoint" \
  --intent "Ops must know instantly if the service is alive or dead."
.aishore/aishore groom
.aishore/aishore run
```

See the [full quickstart guide](docs/QUICKSTART.md) for detailed setup, configuration, and examples.

## How It Works

aishore models a real sprint team with specialized AI agents (Developer, Validator, Tech Lead, Product Owner, Architect), coordinated by a central orchestrator. Each sprint item is picked from the backlog, developed on an isolated feature branch through a 3-phase maturity protocol (implement, critique, harden), validated against acceptance criteria and commander's intent, then merged and archived.

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                  Sprint Orchestrator                                  │
│                                                                                       │
│  ┌──────┐  ┌────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐  ┌─────────┐  ┌──────────┐
│  │ Pick │->│ Branch │->│ Preflight │->│ Developer │->│ Verify │->│Validator│->│  Merge   │
│  │ Item │  │ Create │  │  Check    │  │   Agent   │  │  Suite │  │  Agent  │  │ Archive  │
│  └──────┘  └────────┘  └───────────┘  └───────────┘  └────────┘  └─────────┘  └──────────┘
│                                              │                         │              │
│                                              └──── retry on failure ───┘              │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

See [Architecture](docs/ARCHITECTURE.md) for the full pipeline, agent system, and design decisions.

## Status

**Version:** 0.3.4 — **Alpha**

What works well: sprint orchestration, maturity protocol, autonomous mode with circuit breakers, backlog grooming, architecture review, checksum-verified updates, scope checking, spec refinement.

What's rough: single-repo only (no monorepo support), error messages could be friendlier, limited to Claude Code CLI as the AI backend.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | Pipeline, agents, quality model, and design decisions |
| [Quickstart](docs/QUICKSTART.md) | Installation, setup, and first sprint walkthrough |
| [Configuration](docs/CONFIGURATION.md) | Config file, environment variables, and all options |
| [Problems](docs/PROBLEMS.md) | Troubleshooting common issues |
| [Roadmap](docs/ROADMAP.md) | Planned features and project direction |
| [Contributing](docs/CONTRIBUTING.md) | Development setup, code style, and PR process |
| [Changelog](docs/CHANGELOG.md) | Release history and breaking changes |

## Author

**Simon Plant** — building AI infrastructure tools.

- GitHub: [@simonplant](https://github.com/simonplant)
- Open to roles in AI tooling and developer infrastructure.

## License

Licensed under the [Apache License 2.0](LICENSE).
