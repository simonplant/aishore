# aishore

[![Version](https://img.shields.io/github/v/release/simonplant/aishore)](https://github.com/simonplant/aishore/releases)
[![CI](https://github.com/simonplant/aishore/actions/workflows/ci.yml/badge.svg)](https://github.com/simonplant/aishore/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/simonplant/aishore)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)]()
[![Shell](https://img.shields.io/badge/bash-4.4%2B-green?logo=gnubash&logoColor=white)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-required-blueviolet?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)
[![Last Commit](https://img.shields.io/github/last-commit/simonplant/aishore)](https://github.com/simonplant/aishore/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/simonplant/aishore?style=flat)](https://github.com/simonplant/aishore/stargazers)

**Queue 50 features. Walk away. Come back to merged, validated code.**

aishore is the sprint orchestration layer for Claude Code. You define what to build and why. It picks items from your backlog, develops each one through a quality protocol, validates against your intent, and merges the result — autonomously, in batch, with full git workflow.

```bash
.aishore/aishore run done   # drain the entire backlog, hands-off
```

## The Problem

AI coding tools are single-session. You prompt, it codes, the session ends. To ship 20 features you sit through 20 sessions — managing branches, reviewing output, catching regressions, re-prompting on failures. There's no batch execution, no quality gates between items, no memory of what was already built.

**aishore is the layer between "AI can write code" and "AI can run a sprint."**

## How It Works

You provide three things per item: **what to build** (title + steps), **why it matters** (commander's intent), and **how to verify it** (acceptance criteria + your test suite). aishore handles the rest.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Sprint Orchestrator                            │
│                                                                         │
│  Pick ─→ Branch ─→ Preflight ─→ Develop ─→ Validate ─→ Merge/Archive  │
│                                     │            │                      │
│                                     └── retry ───┘                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**For each item, the orchestrator:**

1. **Picks** the highest-priority ready item and creates a feature branch
2. **Pre-flights** your test suite and the regression suite against the unmodified codebase (catches broken baselines and regressions from prior sprints before wasting a sprint)
3. **Develops** through a 3-phase maturity protocol — all in one session while context is hot:
   - **Implement** — write the code
   - **Critique** — stop, re-read everything, verify each AC, hunt bugs and edge cases, fix what's found
   - **Harden** — run validation again, fix regressions, confirm all AC are provably met
4. **Validates** — runs your test suite, executes AC verify commands, then an independent Validator agent probes the implementation and reviews against acceptance criteria and commander's intent
5. **Merges** the feature branch, pushes, and archives the completed item with full metadata

Failed items retry with failure context fed back to the developer. If all retries exhaust, an AI agent refines the spec and tries once more. A circuit breaker stops the session if failures cascade.

## Quick Start

```bash
# Install (into .aishore/ — no global dependencies)
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash

# Initialize (auto-detects your stack and test command)
.aishore/aishore init -y

# Add a backlog item with intent
.aishore/aishore backlog add \
  --title "Add health check endpoint" \
  --intent "Ops must know instantly if the service is alive or dead. No false positives."

# Run one sprint
.aishore/aishore run

# Or drain the entire backlog autonomously
.aishore/aishore run done --retries 2
```

See the [full quickstart guide](docs/QUICKSTART.md) for detailed setup and your first sprint walkthrough.

## Commander's Intent

The most important concept in aishore. Every item requires a **commander's intent** — a directive stating what must be true when the work is done. Not implementation instructions. The outcome.

| Intent (good) | Not intent (bad) |
|----------------|-------------------|
| "Ops must know instantly if the service is alive or dead." | "Add health check endpoint" |
| "Users authenticate securely or are told exactly why they cannot. Never a blank screen." | "Implement OAuth login" |
| "Deploys that break the API contract must be caught before reaching production." | "Add contract tests" |

Intent is a **hard gate**. Items without it are skipped. When the spec is ambiguous, intent is what the developer follows. When the validator checks results, intent is the bar.

## What You Get

**Autonomous batch execution.** `run done` drains the backlog. `run p0` does just the must-haves. Set `--limit 10` for a capped session. Walk away; come back to merged code.

**Quality that survives scale.** The maturity protocol (implement, critique, harden) runs inside each session while the AI still holds full context. The Validator agent actively probes implementations — running commands to verify behavior, not just reading diffs. Acceptance criteria with verify commands are deterministic evals, not opinions.

**Evals that compound.** Every sprint's verify commands are saved to a regression suite. Before each subsequent sprint, the full suite runs as pre-flight — sprint 51 cannot silently break what sprint 12 proved worked. The regression suite grows automatically from the specs groom agents write. No manual test maintenance.

**Full sprint lifecycle.** Feature branches, pre-flight checks, scope enforcement, independent validation, merge, push, and archival. Every completed item is recorded with its original spec, outcome, duration, and line count.

**Self-healing failures.** Retries carry full failure context (prior diff, validator feedback, error logs). Spec refinement rewrites the steps and AC based on what went wrong. Circuit breaker stops runaway sessions.

**AI-powered grooming.** Tech Lead, Product Owner, and Architect agents decompose rough ideas into sprint-ready items. `backlog populate` reads your PRODUCT.md and generates a scaffolded backlog — skeleton items first, then features. `groom --architect` detects when a project is building fragments without a working top-down skeleton and injects scaffolding items. Auto-groom keeps the pipeline filled during long autonomous runs.

**Zero config.** Pure Bash, no build step. `init -y` detects your project type and test command. Works out of the box. Customize later via `config.yaml` or environment variables.

## Built by aishore

This project builds itself. Nearly every commit was generated by aishore's own sprint orchestrator.

| Metric | Value |
|--------|-------|
| Sprints completed | 305 |
| Commits generated | 731 (96% of repo history) |
| Bugs fixed autonomously | 215 |
| Features shipped | 75 |
| Days of development | 63 |

Browse the [git history](https://github.com/simonplant/aishore/commits/main) — the conventional commit messages, feature branches, and merge commits are all aishore's work.

## Why Not Just Prompt?

**"I already use Claude Code / Cursor / Aider."**
Those are session tools. aishore is the sprint layer on top. It handles what happens *between* sessions: backlog priority, git branching, quality gates, failure recovery, batch execution, and result archival. You keep your AI coding tool — aishore orchestrates it.

**"Can't I just loop over prompts in a shell script?"**
You'd need to build: git branching per item, baseline pre-flight, a maturity protocol, retries with failure context, scope enforcement, auto-grooming, circuit breakers, spec refinement, independent validation, a regression suite, and sprint archival. That's what aishore is — already built, tested across 305 sprints.

**"What about SWE-agent / OpenHands / Devin?"**
Those are AI agents that solve individual tasks. aishore manages the *sprint*, not the *task*. It handles item selection, quality gates, batch execution, and the workflow around the agent. It could wrap any coding agent; it currently uses Claude Code because it's the most capable for full-repo work.

## Documentation

| | |
|---|---|
| **[Quickstart](docs/QUICKSTART.md)** | Install, configure, run your first sprint |
| **[Architecture](docs/ARCHITECTURE.md)** | Pipeline, agents, quality model, design decisions |
| **[Configuration](docs/CONFIGURATION.md)** | Config file, env vars, CLI flags |
| **[Problems](docs/PROBLEMS.md)** | Problems aishore solves |
| **[Roadmap](docs/ROADMAP.md)** | What's next |
| **[Contributing](docs/CONTRIBUTING.md)** | Dev setup, code style, PR process |
| **[Changelog](docs/CHANGELOG.md)** | Release history |

## Status

**Alpha** (see `.aishore/VERSION` for current version). Battle-tested on its own codebase, used daily on real projects.

Works well: sprint orchestration, maturity protocol, autonomous mode, backlog grooming, scaffolding detection, architecture review, regression suite, adversarial validation, executable AC, spec refinement, checksum-verified updates.

Known limits: single-repo only, Claude Code CLI as the only AI backend, macOS/Linux only.

## Author

**Simon Plant** — building AI infrastructure tools.

- GitHub: [@simonplant](https://github.com/simonplant)

## License

[Apache License 2.0](LICENSE)
