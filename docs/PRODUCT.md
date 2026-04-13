# Product Requirements — aishore

## Vision

aishore is a sprint orchestration layer for AI coding agents. You write a product doc describing what to build. AI turns it into a backlog, implements each item, validates against intent, and merges — autonomously, item by item, while you sleep.

**The workflow:** Write PRODUCT.md → `backlog populate` → `groom` → `run done`. Humans own what to build. Machines own how fast, how correctly, and how to heal when things break — the machine auto-generates heal items to fix regressions, but never adds new features to the backlog. The backlog is the contract between the two.

aishore rejects process-as-product. No standups, no velocity charts, no sprint retrospectives, no test coverage targets. The only measure is: does the code work, does it fulfill intent, and did it break anything that worked before?

## Target Users

Solo developers and small teams using AI coding tools (currently Claude Code) who want to go from "AI can write a function" to "AI can ship 20 features while I sleep." People who have backlogs of real work and want autonomous batch execution with quality they can trust.

Not for: teams that need approval workflows, compliance gates, or human review on every change. aishore merges autonomously by design — add `--no-merge` if you need human checkpoints.

## Core Capabilities

- **Working core first** — every project has a core: the one end-to-end path the product exists for. A possessions app's core is GET /items returning real data from a real database, rendered on screen. An MCP server's core is client connects, discovers tools, calls one, gets a result. The core is declared in PRODUCT.md as a product-level statement, not a shell command. The groomer reads it and assigns each backlog item to a track: `core` (builds/fixes the core path) or `feature` (decorates it). The architect proposes the core verification command from the definition and the codebase — the user reviews and refines it. Nothing else gets built until the core works — secure, performant, lean, correct. If the core breaks, the machine auto-generates a heal item and fixes it before any feature work proceeds. Features are decoration on a working core, never construction on a dead frame.
- **Intent-driven specs** — every item has a commander's intent that defines *what must be true*, not *what to build*. Intent is the north star for developers, the bar for validators, and a hard gate for entering a sprint.
- **Autonomous batch execution** — `run done` drains the backlog. Each item gets its own branch, implementation, validation, merge, and archival. Failures retry with context; the circuit breaker stops cascading failures.
- **Quality through execution** — the maturity protocol (implement, critique, harden) keeps quality iteration inside the session. The validator agent runs commands to probe behavior, not just reads diffs. AC verify commands are executable checks, not opinions.
- **Compounding regression protection** — every passing sprint's verify commands are saved. Before every future sprint, the full suite runs. Sprint 51 cannot silently break what sprint 12 proved. No manual test maintenance.
- **Top-down wiring** — code must be reachable from real entry points. Mocks in production code and stub endpoints are treated as risks, not progress.

## Boundaries

- **Core before features.** If the core doesn't work, feature work is blocked. The machine fixes what's broken before building what's new. No decorating a dead frame.
- **Quality is mechanical, not procedural.** If the system can't check it automatically (readiness gates, validation command, AC verify, regression suite, core check), it doesn't gate on it.
- **Autonomous merge is the default.** Human review is opt-in (`--no-merge`). The assumed workflow is hands-off.
- **Behavior proof over coverage metrics.** A verify command that proves the feature works end-to-end outweighs coverage percentages. Verify commands are the quality signal.
- **Single backend: Claude Code CLI.** No abstraction layer until a second backend is competitive for full-repo autonomous work.
- **CLI-only.** aishore orchestrates from the terminal. It wraps the coding agent, not the editor.
