# aishore

[![Version](https://img.shields.io/github/v/release/simonplant/aishore)](https://github.com/simonplant/aishore/releases)
[![CI](https://github.com/simonplant/aishore/actions/workflows/ci.yml/badge.svg)](https://github.com/simonplant/aishore/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/simonplant/aishore)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-required-blueviolet?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)

Autonomous sprint orchestration for Claude Code. You write a backlog with intent. AI implements, validates, and merges — item by item, branch by branch, hands-off.

```bash
.aishore/aishore run done   # drain the entire backlog autonomously
```

## Install

```bash
# One-line install (into .aishore/ — no global dependencies)
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash

# Or via GitHub API (authenticated, bypasses CDN cache)
gh api repos/simonplant/aishore/contents/install.sh --jq '.content' | base64 -d | bash

# Initialize (auto-detects your stack and test command)
.aishore/aishore init -y
```

**Requirements:** Bash 4.4+, jq, git, [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code). Optional: yq (full config.yaml support).

## Usage

```bash
# Populate backlog from your product doc
.aishore/aishore backlog populate

# Groom items for sprint readiness
.aishore/aishore groom

# Run sprints
.aishore/aishore run              # one item
.aishore/aishore run done         # drain entire backlog
.aishore/aishore run p0           # must-haves only
.aishore/aishore run p1 --retries 2  # must + should, with retries
```

## Intent-Based Development

aishore doesn't work like TDD or agile ceremony. There are no standups, no velocity charts, no coverage targets. The quality model is: **prove the software works by running it, not by counting tests.**

**The backlog item is the unit of quality.** Each item has three things:

1. **Commander's intent** — a directive stating what must be true when done. Not "add health check endpoint" but "ops must know instantly if the service is alive or dead." Intent is the north star when specs are ambiguous, the bar the validator checks against, and a hard gate for sprint entry.

2. **Steps and acceptance criteria** — specific enough that an AI developer can implement without guessing. Bad AC: "it works." Good AC: "health endpoint returns 200 when the service is running."

3. **Executable evals** — `--ac-verify` shell commands that prove the AC is met. Not `grep -q 'healthCheck' src/app.js` (that's structure, not behavior). Instead: `curl -sf http://localhost:3000/health` (that's proof it runs). These are the difference between testing and hoping.

**Evals compound into a regression suite.** Every passing sprint's verify commands are saved. Before every future sprint, the full suite runs as pre-flight. Sprint 51 cannot silently break what sprint 12 proved. No manual test maintenance — the suite grows automatically from well-written AC.

**The groomer is the quality bottleneck.** A vague backlog produces vague implementations that fail validation and burn retries. A precise backlog — clear intent, right-sized steps, executable AC — produces sprints that pass autonomously. `backlog populate` and `groom` exist because the quality of the input determines the quality of the output.

## How It Works

```
Pick ─→ Branch ─→ Preflight ─→ Develop ─→ Validate ─→ Merge/Archive
                                   │            │
                                   └── retry ───┘
```

1. **Pick** — highest-priority ready item with valid intent
2. **Branch** — isolated git worktree per sprint
3. **Preflight** — regression suite + validation command on unmodified baseline
4. **Develop** — implement, critique (re-read all changes, verify each AC), harden (run all verify commands, fix regressions)
5. **Validate** — validation command, AC verify commands, then independent Validator agent probes against intent
6. **Merge** — feature branch merged, pushed, item archived

## Example Item

```bash
.aishore/aishore backlog add \
  --title "Add health check endpoint" \
  --intent "Ops must know instantly if the service is alive or dead. No false positives." \
  --steps "Add GET /health route that checks DB connection and returns 200/503" \
  --ac "Health endpoint returns 200 when service is running" \
  --ac-verify "curl -sf http://localhost:3000/health" \
  --ac "Health endpoint returns 503 when DB is unreachable" \
  --ac-verify "DB_HOST=nowhere curl -sf http://localhost:3000/health; test $? -ne 0"
```

Intent is the north star. Steps tell the developer how. AC verify commands prove it works. The verify commands become regression tests automatically.

## Commands

```bash
.aishore/aishore run [N|ID|done|p0|p1|p2]   # Run sprints
.aishore/aishore backlog populate             # Create items from PRODUCT.md
.aishore/aishore backlog add --title "..."    # Add item manually
.aishore/aishore groom                        # Groom backlog items
.aishore/aishore scaffold                     # Detect fragment risk
.aishore/aishore review [--update-docs]       # Architecture review
.aishore/aishore status                       # Backlog overview
.aishore/aishore update [--ref main]          # Self-update (or pin to commit/branch)
```

## Documentation

| | |
|---|---|
| **[Quickstart](docs/QUICKSTART.md)** | Install, configure, first sprint walkthrough |
| **[Configuration](docs/CONFIGURATION.md)** | Config file, env vars, all CLI flags |
| **[Architecture](docs/ARCHITECTURE.md)** | Pipeline, agents, quality model |
| **[Changelog](docs/CHANGELOG.md)** | Release history |

Additional: [Product vision](docs/PRODUCT.md) | [Problems solved](docs/PROBLEMS.md) | [Roadmap](docs/ROADMAP.md) | [Contributing](docs/CONTRIBUTING.md)

## Comparison

**vs. Claude Code / Cursor / Aider** — those are session tools. aishore is the sprint layer: backlog priority, git branching, quality gates, failure recovery, batch execution, archival. You keep your AI tool — aishore orchestrates it.

**vs. SWE-agent / Devin** — those solve individual tasks. aishore manages the sprint: item selection, quality gates, batch execution, regression protection. It wraps Claude Code; it could wrap any agent.

**vs. shell script loop** — you'd need: branching per item, worktree isolation, pre-flight regression, maturity protocol, retries with context, auto-grooming, circuit breaker, independent validation, and archival.

## Status

**Alpha** (v0.5.9). Self-hosting — nearly every commit generated by its own sprint orchestrator. Used daily on real projects.

Known limits: single-repo, Claude Code CLI only, macOS/Linux only.

## Author

**Simon Plant** — [@simonplant](https://github.com/simonplant)

## License

[Apache License 2.0](LICENSE)
