# Architecture — aishore

This document describes how aishore works as a system — the pipeline, the agents, the quality model, and the design decisions behind them. It is the single reference for anyone evaluating or contributing to the project.

## Overview

aishore is an autonomous sprint orchestration tool for Claude Code. It takes a prioritized backlog of work items, develops each one through an AI agent pipeline, validates the result, and archives completed work. The core loop is: **pick, branch, develop, validate, merge, archive**.

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

Each stage in detail:

1. **Pick** — selects the highest-priority ready item from the backlog. Items must pass readiness gates (intent, steps, AC) to be eligible. In autonomous mode, priority scoping (p0/p1/p2/done) filters which items are considered.
2. **Branch** — creates an isolated feature branch (`aishore/<ITEM-ID>`) from the current branch.
3. **Preflight** — runs the project's validation command against the unmodified codebase. If the baseline is already broken, the sprint aborts immediately rather than producing confusing failures later.
4. **Develop** — the Developer agent implements the feature following the maturity protocol (see below).
5. **Verify** — changed files are checked against scope globs, the validation command runs, and any AC verification commands execute.
6. **Validate** — the Validator agent reviews changes against acceptance criteria and commander's intent.
7. **Merge & Archive** — the branch is merged back with `--no-ff`, pushed, and the completed item is archived to `sprints.jsonl`.

The orchestrator is a single Bash script (`.aishore/aishore`) with no build step. All agent invocations go through `run_agent()`, which assembles the prompt, appends the completion contract, and delegates to `run_agent_process()`.

## The Maturity Protocol

The maturity protocol is the core quality mechanism. Rather than relying on external retry loops to catch defects, it keeps quality iteration inside the developer session where implementation context is still hot.

Every developer session runs three phases:

1. **Implement** — write the code. Follow the spec, match existing patterns.
2. **Critique** — stop coding. Re-read every changed file. Verify intent is fulfilled and each AC is provably met. Hunt bugs, edge cases, dead code, missing error handling. Fix everything found.
3. **Harden** — run validation again. Fix regressions. Re-verify all AC. Only then commit and signal done.

**Why this exists:** One-shot AI implementation produces code that works for the happy path but often misses edge cases, introduces subtle bugs, or drifts from the stated intent. The critique phase forces the AI to shift from "writer" to "reviewer" mindset while it still holds the full implementation context. The harden phase catches anything the critique introduced. This three-phase cycle consistently produces higher quality output than implement-then-retry.

The protocol is enabled by default. Disable it with the `--quick` flag or `maturity.enabled: false` in config when fast iteration matters more than thoroughness (e.g., during prototyping). The `AISHORE_MATURITY` environment variable also controls this.

## Agent System

aishore models a real sprint team with five specialized AI agents, each with a distinct role and restricted permissions:

| Agent | Role | Invoked by | Permissions |
|-------|------|------------|-------------|
| **Developer** | Implements features following project conventions and the maturity protocol | `run` | `Bash,Edit,Write,Read,Glob,Grep` |
| **Validator** | Checks acceptance criteria and commander's intent against actual changes | `run` | `Bash,Read,Write,Glob,Grep` |
| **Tech Lead** | Grooms bugs and features for technical clarity — adds steps, testable AC, marks items ready | `groom` | CLI commands |
| **Product Owner** | Grooms features for value alignment, sets priorities, populates backlog from requirements | `groom --backlog`, `backlog populate` | CLI commands |
| **Architect** | Reviews patterns, risks, code quality, technical debt, and documentation | `review` | `Read,Glob,Grep` (+ `Edit,Write` with `--update-docs`) |

### Data flow between agents

The agents communicate through files, not directly:

- **Backlog files** (`backlog.json`, `bugs.json`) are the shared work queue. The Product Owner and Tech Lead write to them (via CLI); the orchestrator reads from them to pick items.
- **Sprint file** (`sprint.json`) carries the current item's spec. The orchestrator writes it; the Developer and Validator read it.
- **Result file** (`result.json`) is the completion contract. Agents write `{"status": "pass", "summary": "..."}` or `{"status": "fail", "reason": "..."}` to signal they are done. The orchestrator polls for this file.
- **Project context** (`CLAUDE.md`, `PRODUCT.md`, `ARCHITECTURE.md`) is auto-detected and injected into every agent's prompt for project awareness.

### Agent permissions

Permissions are deliberately restricted by role. The Developer gets full file manipulation. The Validator can read and run commands but cannot silently fix code (it reports, not repairs). The Architect is read-only by default to prevent accidental changes during review. Permissions are configurable in `.aishore/config.yaml`.

## Git Branching Model

Each sprint item runs on its own feature branch:

1. Branch `aishore/<ITEM-ID>` is created from the current branch.
2. The Developer agent commits its own work directly to the feature branch.
3. On success: the branch is merged back with `--no-ff`, pushed, and the base branch pulls latest before the next item starts.
4. On failure: the branch is deleted and the base branch is restored cleanly.

The `--no-merge` flag changes this behavior: instead of merging, the branch is pushed to origin for PR review. This supports teams that require human review before merge.

**Safe failure recovery:** Pre-existing uncommitted changes are stashed before a sprint begins and restored afterward, regardless of outcome. The orchestrator includes a safety-net commit in case the Developer agent fails to commit. Sprint failures never leave the working tree in a dirty state.

## Directory Structure

```
project/
├── backlog/                 # User content (never touched by update)
│   ├── backlog.json         # Feature backlog
│   ├── bugs.json            # Bug/tech-debt backlog
│   ├── sprint.json          # Current sprint state
│   ├── DEFINITIONS.md       # DoR, DoD, priority/size definitions
│   └── archive/
│       └── sprints.jsonl    # Completed sprint history
└── .aishore/                # Tool (can be updated independently)
    ├── aishore              # Single-file CLI (Bash)
    ├── VERSION              # Version (single source of truth)
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── agents/              # Agent prompts (one per role)
    │   ├── architect.md
    │   ├── developer.md
    │   ├── product-owner.md
    │   ├── tech-lead.md
    │   └── validator.md
    ├── config.yaml          # Optional overrides
    └── data/                # Runtime (not version controlled)
        ├── logs/
        └── status/
            ├── result.json      # Agent completion signal
            ├── .item_source     # Tracks which backlog the current item came from
            └── .aishore.lock    # flock-based concurrency guard
```

The separation between `backlog/` (user content) and `.aishore/` (tool) is fundamental. Updates replace `.aishore/` files but never touch `backlog/` or `config.yaml`. This means the tool can be upgraded without risk to user data.

## Design Decisions

### Single-file CLI

All orchestration logic lives in one Bash script. This keeps the tool zero-dependency (beyond Bash 4.4+, jq, git, and the Claude CLI), makes installation a single `cp`, and ensures the entire system can be understood by reading one file.

### Separation of tool and content

The `.aishore/` directory is the tool; `backlog/` is user data. Updates replace tool files via checksum-verified downloads but skip `config.yaml` and never touch `backlog/`. This lets teams version-control their backlogs alongside their code while still receiving tool updates.

### Completion contract over streaming

Agents signal completion by writing a JSON file (`result.json`) rather than through streaming output. This makes the interface between orchestrator and agent simple, testable, and resilient to agent output format changes.

### Sensible defaults with layered overrides

The tool works out of the box with no configuration. When customization is needed, configuration follows a clear precedence: environment variables override `config.yaml`, which overrides built-in defaults. This supports both local development (env vars) and team-wide settings (committed config).

### Context auto-detection

aishore automatically finds and injects `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` from the project root or `docs/` directory. This means agents always have project context without requiring explicit configuration.

### Concurrency guard

Only one aishore process runs at a time, enforced via `flock` on `.aishore/data/status/.aishore.lock`. This prevents race conditions on shared state files (sprint.json, result.json) without requiring a database or external coordinator.

### Checksum-verified updates

The `update` command resolves the latest GitHub release tag, fetches files listed in the remote `checksums.sha256` manifest, validates all paths (must start with `.aishore/`, no `..` traversal, no absolute paths), stages to a temp directory, verifies SHA-256 checksums, and installs only if all checks pass. Adding a new distributable file requires only dropping the file and running `aishore checksums`.

## Quality Gates

### Definition of Ready

An item must pass these gates before it can enter a sprint:

| Gate | Requirement |
|------|-------------|
| **Intent** | `intent` field states what must be true when done (>=20 chars, must be a directive not a label) |
| **Steps** | Implementation steps are clear enough to act on |
| **AC** | Acceptance criteria are verifiable |
| **No blockers** | Dependencies are resolved |
| **Right size** | Completable in one sprint |
| **readyForSprint** | Tech Lead has marked it ready |

Intent is a **hard gate at sprint time** — items without intent (or with intent shorter than 20 characters) are silently skipped by auto-pick and explicitly rejected when run by ID.

### Commander's Intent

The `intent` field is a non-negotiable directive — what must be true when done. When the spec is unclear or steps seem wrong, intent is the order the developer follows. It is written as an outcome ("Users authenticate securely or are told why not"), never as an implementation label ("Add auth").

### Definition of Done

| Gate |
|------|
| Implementation matches all acceptance criteria |
| All tests pass (existing + new) |
| Type-check, lint, and test suites all pass |
| Each AC individually verified |
| No regressions introduced |

### Completion Contract

Agents signal completion by writing to `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "what was done"}
```

The orchestrator polls for this file. On `"pass"`, it proceeds to the next pipeline stage. On `"fail"`, it triggers retry logic (if configured) or aborts the sprint.

### Scope Checking

Items can declare a `scope` array of glob patterns (e.g., `["src/**", "tests/**"]`). After the Developer agent runs, changed files are checked against these patterns. In `warn` mode (default), out-of-scope changes are logged. In `strict` mode, they fail the sprint. This prevents feature creep and unintended side effects.

### Testable Acceptance Criteria

AC entries can be plain strings or `{text, verify}` objects. The `verify` field is a shell command run after validation; failures trigger retries. This allows automated verification of criteria that would otherwise require human judgment.

### Spec Refinement

When all retries are exhausted, `--refine` invokes an AI agent to improve the item's steps and acceptance criteria based on what went wrong, then attempts one more developer cycle. This closes the loop between failure and specification quality.
