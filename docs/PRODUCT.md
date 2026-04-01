# Product Requirements — aishore

## Vision

aishore is a sprint orchestration layer for AI coding agents. It exists because AI can write code but can't ship a sprint — there's no batch execution, no quality gates, no failure recovery, and no memory of what was already built.

The core belief: **humans own what to build, machines own how fast and how correctly.** A human writes intent and priority. An AI implements, critiques its own work, and hardens it — all in one session while context is hot. A separate AI validates against intent, not just acceptance criteria. A regression suite compounds proof that prior work still holds. The result is merged, working code — not a PR waiting for review, not a green CI badge on broken software, not a demo that works once.

aishore rejects process-as-product. No standups, no velocity charts, no sprint retrospectives, no test coverage targets. The only measure is: does the code work, does it fulfill intent, and did it break anything that worked before?

## Target Users

Solo developers and small teams using AI coding tools (currently Claude Code) who want to go from "AI can write a function" to "AI can ship 20 features while I sleep." People who have backlogs of real work and want autonomous batch execution with quality they can trust.

Not for: teams that need approval workflows, compliance gates, or human review on every change. aishore merges autonomously by design — add `--no-merge` or `--pr` if you need human checkpoints.

## Core Capabilities

- **Intent-driven specs** — every item has a commander's intent that defines *what must be true*, not *what to build*. Intent is the north star for developers, the bar for validators, and a hard gate for entering a sprint.
- **Autonomous batch execution** — `run done` drains the backlog. Each item gets its own branch, implementation, validation, merge, and archival. Failures retry with context; the circuit breaker stops cascading failures.
- **Quality through execution** — the maturity protocol (implement, critique, harden) keeps quality iteration inside the session. The validator agent runs commands to probe behavior, not just reads diffs. AC verify commands are executable checks, not opinions.
- **Compounding regression protection** — every passing sprint's verify commands are saved. Before every future sprint, the full suite runs. Sprint 51 cannot silently break what sprint 12 proved. No manual test maintenance.
- **Top-down wiring** — scaffolding detection prevents fragment accumulation. Code must be reachable from real entry points. Mocks in production code and stub endpoints are treated as risks, not progress.

## Non-Goals

- **Process ceremony.** No burndown charts, no sprint planning meetings, no definition-of-ready checklists beyond what's mechanically enforced. If the system can't check it automatically, it doesn't gate on it.
- **Human-in-the-loop by default.** The default path is autonomous merge. Human review is opt-in (`--no-merge`, `--pr`), not the assumed workflow.
- **Test coverage as a metric.** aishore cares whether verify commands pass, not what percentage of lines they cover. A single verify command that proves the feature works end-to-end is worth more than 90% coverage of unit tests that mock everything.
- **Multi-LLM abstraction.** Currently Claude Code only. Building a provider abstraction layer before there's a second provider would be speculative engineering.
- **IDE integration.** aishore is a CLI tool that orchestrates from the terminal. It wraps the coding agent, not the editor.
