# aishore

[![Version](https://img.shields.io/github/v/release/simonplant/aishore)](https://github.com/simonplant/aishore/releases)
[![CI](https://github.com/simonplant/aishore/actions/workflows/ci.yml/badge.svg)](https://github.com/simonplant/aishore/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/simonplant/aishore)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)]()
[![Shell](https://img.shields.io/badge/bash-4.4%2B-green?logo=gnubash&logoColor=white)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-required-blueviolet?logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)
[![Last Commit](https://img.shields.io/github/last-commit/simonplant/aishore)](https://github.com/simonplant/aishore/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/simonplant/aishore?style=flat)](https://github.com/simonplant/aishore/stargazers)

**Ship working code, not evidence of process.**

Humans own what to build. Machines own how fast and how correctly. You write intent and priority. An AI implements, critiques its own work, and hardens it — all in one session while context is hot. A separate AI validates against intent. A regression suite compounds proof that prior work still holds. The result is merged, working code.

```bash
.aishore/aishore run done   # drain the entire backlog, hands-off
```

## The Problem

AI coding tools are single-session. You prompt, it codes, the session ends. To ship 20 features you sit through 20 sessions — managing branches, reviewing output, catching regressions, re-prompting on failures. There's no batch execution, no quality gates between items, no memory of what was already built.

TDD and agile ceremony don't help — they produce green tests on broken products, velocity metrics on stalled deliveries, and approved PRs that nobody actually ran. The process becomes the product.

**aishore is the layer between "AI can write code" and "AI can ship a sprint."**

## Why Intent + Evals

"Build me a login page" is an instruction. "Users authenticate securely or are told exactly why they cannot — never a blank screen" is **intent**. `--ac-verify "curl -s localhost:3000/login | grep -q 'Sign in'"` is an **eval**.

Instructions tell the AI *what to type*. Intent tells it *what must be true when done*. Evals prove it. When you combine all three — intent drives the implementation, evals gate the merge, and the regression suite compounds across sprints — you get software that converges on correct, not software that happens to pass on the first try.

## How It Works

You provide three things per item: **what must be true** (commander's intent), **how to verify it** (acceptance criteria with verify commands), and **what to build** (steps). aishore handles the rest.

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
2. **Pre-flights** your test suite and the regression suite against the unmodified codebase (catches broken baselines and regressions before wasting a sprint)
3. **Develops** through a maturity protocol — implement, critique, harden — all in one session while the AI still holds full context
4. **Validates** — runs your test suite, executes AC verify commands, then an independent Validator agent probes the implementation against acceptance criteria and commander's intent
5. **Merges** the feature branch, pushes, and archives the completed item

Failed items retry with failure context fed back to the developer. A circuit breaker stops the session if failures cascade.

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

**Quality through execution, not ceremony.** The maturity protocol keeps quality iteration inside the session where the AI holds full context. The Validator agent runs commands to probe behavior. AC verify commands are executable checks that prove the feature works — not opinions, not coverage metrics, not green badges on broken software.

**Evals that compound.** Every sprint's verify commands are saved to a regression suite. Before each subsequent sprint, the full suite runs as pre-flight. Sprint 51 cannot silently break what sprint 12 proved. The regression suite grows automatically. No manual test maintenance.

**Full sprint lifecycle.** Feature branches, pre-flight checks, independent validation, merge, push, and archival. Every completed item is recorded with its original spec, outcome, and metadata.

**Self-healing failures.** Retries carry full failure context (prior diff, validator feedback, error logs). Circuit breaker stops runaway sessions.

**Top-down wiring.** The scaffolding detector prevents fragment accumulation — building isolated pieces that never connect. Code must be reachable from real entry points. Auto-groom keeps the pipeline filled during long autonomous runs.

## Built by aishore

This project builds itself. Nearly every commit was generated by aishore's own sprint orchestrator. Browse the [git history](https://github.com/simonplant/aishore/commits/main) — the conventional commit messages, feature branches, and merge commits are all aishore's work.

## Why Not Just Prompt?

**"I already use Claude Code / Cursor / Aider."**
Those are session tools. aishore is the sprint layer on top. It handles what happens *between* sessions: backlog priority, git branching, quality gates, failure recovery, batch execution, and result archival. You keep your AI coding tool — aishore orchestrates it.

**"Can't I just loop over prompts in a shell script?"**
You'd need to build: git branching per item, baseline pre-flight, a maturity protocol, retries with failure context, auto-grooming, circuit breakers, independent validation, a regression suite, and sprint archival. That's what aishore is.

**"What about AI coding agents (SWE-agent, Devin, etc.)?"**
Those are agents that solve individual tasks. aishore manages the *sprint*, not the *task*. It handles item selection, quality gates, batch execution, and the workflow around the agent. It could wrap any coding agent; it currently uses Claude Code because it's the most capable for full-repo work.

## Documentation

| | |
|---|---|
| **[Quickstart](docs/QUICKSTART.md)** | Install, configure, run your first sprint |
| **[Architecture](docs/ARCHITECTURE.md)** | Pipeline, agents, quality model, design decisions |
| **[Configuration](docs/CONFIGURATION.md)** | Config file, env vars, CLI flags |
| **[Product](docs/PRODUCT.md)** | Vision, target users, non-goals |
| **[Problems](docs/PROBLEMS.md)** | Problems aishore solves |
| **[Roadmap](docs/ROADMAP.md)** | What's next and what's not worth building |
| **[Contributing](docs/CONTRIBUTING.md)** | Dev setup, code style, PR process |
| **[Changelog](docs/CHANGELOG.md)** | Release history |

## Status

**Alpha** (v0.5.8). Battle-tested on its own codebase, used daily on real projects.

Known limits: single-repo only, Claude Code CLI as the only AI backend, macOS/Linux only.

## Author

**Simon Plant** — building AI infrastructure tools.

- GitHub: [@simonplant](https://github.com/simonplant)

## License

[Apache License 2.0](LICENSE)
