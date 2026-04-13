# Architecture — aishore

## Overview

aishore is an autonomous sprint orchestration tool for Claude Code. It takes a prioritized backlog, develops each item through an AI agent pipeline, validates the result, and archives completed work.

## Pipeline

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Sprint Orchestrator                                         │
│                                                                                                │
│  ┌──────┐  ┌──────┐  ┌────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐  ┌─────────┐  ┌────────┐
│  │ Core │->│ Pick │->│ Branch │->│ Preflight │->│ Developer │->│ Verify │->│Validator│->│ Merge  │
│  │ Gate │  │ Item │  │ Create │  │  Check    │  │   Agent   │  │  Suite │  │  Agent  │  │Archive │
│  └──────┘  └──────┘  └────────┘  └───────────┘  └───────────┘  └────────┘  └─────────┘  └────────┘
│      │                                                  │                         │          │
│      │ core broken → only core-track items pickable     └──── retry on failure ───┘          │
│      │ core passing → all items pickable                                                     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Stage | What happens |
|-------|-------------|
| **Core Gate** | Runs `CORE_CMD` (if configured). If it fails, only `track: "core"` items are pickable — feature items are blocked. If it passes (or is unconfigured), all items are pickable. |
| **Pick** | Selects highest-priority ready item from the active track. Heal items (auto-generated from regressions) jump the queue. Must pass readiness gates (intent >= 20 chars, steps, AC). Priority scoping filters by `p0`/`p1`/`p2`/`done`. |
| **Branch** | Creates isolated feature branch `aishore/<ITEM-ID>` in a git worktree. |
| **Preflight** | Runs full regression suite (accumulated verify commands from prior sprints) against unmodified codebase. Aborts if baseline is broken. |
| **Develop** | Developer agent implements via maturity protocol (implement → critique → harden). |
| **Verify** | All AC verify commands execute — synthetic transactions that prove each feature works for real. |
| **Validate** | Validator agent reviews changes against AC and commander's intent. |
| **Merge** | Branch merged with `--no-ff`, pushed, item archived to `sprints.jsonl`. Core gate re-checked after merge — if a feature broke the core, a heal item is synthesized and jumps the queue. |

## Working Core

Every project has a core — the one end-to-end path the product exists for. The core is declared in PRODUCT.md as a product-level statement (e.g., "A user opens the app and sees their items list, populated from a real API, backed by a real database"). The system manages it through three mechanisms:

### Two-Track Backlog

Every backlog item has a `track` field: `"core"` or `"feature"` (default: `"feature"`).

- **Core track** — items that build, wire up, or fix the primary end-to-end path. Pickable anytime.
- **Feature track** — items that extend, decorate, or enhance the core. Gated: only pickable when `CORE_CMD` passes.

The architect is the track authority — it sets initial track assignments via `scaffold`. The groomer preserves and validates them during grooming. The architect proposes the `CORE_CMD` — a verification command derived from the core definition and the codebase (e.g., build, start, hit primary endpoint, verify response). The user should review and refine it before relying on it.

### Core Gate

Before picking an item, the orchestrator runs `CORE_CMD`:

- **Fails + core items available** → only `track: "core"` items are pickable. Feature items are blocked.
- **Fails + no core items available** → the system is stuck. A heal item is synthesized from the `CORE_CMD` failure (the command itself becomes the verify AC). If no heal can be generated, the circuit breaker fires with a clear message: "CORE_CMD fails but no core-track items exist — run `scaffold` or fix manually."
- **Passes** → all items are pickable. Features are unlocked.
- **Not configured** → no gating. All items pickable (backwards-compatible).

After every successful merge, `CORE_CMD` is re-checked. If a sprint broke the core, a heal item is auto-generated.

### Heal-First Queue

When the core breaks (a previously-passing `CORE_CMD` or regression command fails), the orchestrator synthesizes a heal item:

- Extracts the broken verification commands as acceptance criteria
- Creates a `track: "core"`, `priority: "must"`, `category: "heal"` item in bugs.json with a `healSource` field tracing back to the original item
- The heal item jumps the pick queue — ahead of all other items
- Goes through the normal sprint loop (worktree, developer, validation, merge)
- Guard: heal items never spawn child heals. If a heal fails, the original item's `failCount` increments and the heal item is removed from bugs.json (no accumulation). If the heal fails and exhausts retries, the circuit breaker fires — the system stops rather than looping on an unfixable regression

## Completion Contract

Agents signal completion by writing `.aishore/data/status/result.json`:

```json
{"status": "pass", "summary": "what was done"}
{"status": "fail", "reason": "what went wrong"}
```

The orchestrator polls for this file. On `"pass"`, it proceeds. On `"fail"`, retry logic triggers.

## Maturity Protocol

Every developer session runs three phases:

| Phase | Action | Purpose |
|-------|--------|---------|
| **Implement** | Write the code following spec and existing patterns | Produce the implementation |
| **Critique** | Stop coding. Re-read every changed file. Verify intent fulfilled, each AC provably met. Hunt bugs, edge cases, dead code. Fix everything found. | Catch defects while context is hot |
| **Harden** | Run validation again. Fix regressions. Re-verify all AC. Commit and signal done. | Ensure the critique phase didn't break anything |

The protocol is always on. Skipping it produces measurably worse outcomes.

## Agent System

| Agent | Role | Invoked by | Permissions |
|-------|------|------------|-------------|
| **Developer** | Implements features following maturity protocol | `run` | `Agent,Bash,Edit,Write,Read,Glob,Grep,EnterPlanMode,ExitPlanMode` |
| **Validator** | Checks AC and intent against actual changes | `run` | `Bash,Read,Glob,Grep` |
| **Groomer** | Adds steps, testable AC, sets priorities, marks items ready | `groom` | CLI commands |
| **Architect** | Establishes working core, proposes `CORE_CMD`, assigns tracks (track authority), reviews patterns/risks | `review`, `scaffold` | `Read,Glob,Grep` (+ `Edit,Write` with `--update-docs`) |

### Data flow

Agents communicate through files:

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `backlog.json`, `bugs.json` | Groomer, Architect (via CLI), Orchestrator (heal items) | Orchestrator | Shared work queue (items have `track: "core"\|"feature"`) |
| `sprint.json` | Orchestrator | Developer, Validator | Current item spec |
| `result.json` | Agents | Orchestrator | Completion signal |
| `CLAUDE.md`, `PRODUCT.md`, `ARCHITECTURE.md` | Human | All agents (auto-injected) | Project context (PRODUCT.md includes core definition) |

### Permission model

Developer gets full file manipulation. Validator can read and run commands but cannot modify code (reports, not repairs). Architect is read-only by default. Configurable in `.aishore/config.yaml`.

## Git Branching

1. Branch `aishore/<ITEM-ID>` created in isolated worktree from current branch
2. Developer commits directly to feature branch
3. **Success**: merge with `--no-ff`, push, pull latest before next item
4. **Failure**: branch deleted, diagnostics preserved on base branch
5. **`--no-merge`**: branch pushed to origin for PR review instead of merging

Backlog mutations (mark complete, archive) happen on the base branch after merge — never in the worktree. This prevents merge conflicts on JSON files.

## Quality Gates

### Definition of Ready

| Gate | Requirement |
|------|-------------|
| **Intent** | `intent` field >= 20 chars, must be a directive not a label (see `backlog/DEFINITIONS.md` for examples) |
| **Steps** | Implementation steps clear enough to act on |
| **AC** | Acceptance criteria are verifiable |
| **No blockers** | Dependencies resolved |
| **readyForSprint** | Groomer has marked it ready |

Intent is a **hard gate at sprint time** — items without it are silently skipped.

### Core Check

`CORE_CMD` runs before picking (gates which track is available) and after every merge (detects core regressions). If a merge breaks the core, a heal item is synthesized and jumps the queue. See [Working Core](#working-core) above.

### Synthetic Validation

All validation in aishore is synthetic — commands that exercise the real system, not tests that mock it. Two mechanisms, both must pass:

1. **AC verify commands** — shell commands from the item's acceptance criteria that prove each feature works for real (e.g., `curl -sf localhost:3000/items | jq -e '.length > 0'`). These are the primary quality signal.
2. **Validator agent** — independent check of AC and intent fulfillment against the actual code changes.

`CORE_CMD` runs separately — before pick (gates tracks) and after merge (detects regressions). It is not part of the per-item validation sequence; it validates the system as a whole.

### Regression Suite

Completed sprints' verify commands are saved to `backlog/archive/regression.jsonl`. Before every sprint, the full suite runs as pre-flight. Sprint 51 cannot break what sprint 12 proved. Grows automatically.

### Executable AC

AC entries can be plain strings or `{text, verify}` objects. `verify` is a shell command run by the orchestrator — failures trigger retries. Plain-string AC are validated by the Validator agent's judgment; verify commands are validated deterministically.

## Directory Structure

```
project/
├── backlog/                 # User content (never touched by update)
│   ├── backlog.json         # Feature backlog
│   ├── bugs.json            # Bug/tech-debt backlog
│   ├── sprint.json          # Current sprint state
│   ├── DEFINITIONS.md       # DoR, DoD, priority/size definitions
│   └── archive/
│       ├── sprints.jsonl    # Completed sprint history
│       └── regression.jsonl # Accumulated regression suite
└── .aishore/                # Tool (replaceable via update)
    ├── aishore              # Core orchestrator (Bash)
    ├── VERSION              # Version (single source of truth)
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── agents/              # Agent prompts (one per role)
    ├── config.yaml          # Optional overrides
    ├── lib/                 # Lazy-loaded command modules
    └── data/                # Runtime (not version controlled)
        ├── logs/
        └── status/
            ├── result.json
            └── .aishore.lock/
```

## Design Constraints

| Constraint | Implication |
|-----------|-------------|
| Pure Bash, no build step | Only Bash 4.4+, jq, git, claude required. Lazy-loaded modules in `.aishore/lib/`. |
| Tool and content separated | `.aishore/` is the tool, `backlog/` is user data. Updates replace tool files, never user data or `config.yaml`. |
| Completion via file, not streaming | Agents write `result.json`. Interface is simple, testable, resilient to output format changes. |
| Config precedence: env > yaml > defaults | Supports local development (env vars) and team settings (committed config). Full yaml requires `yq`. |
| Context auto-detection | `CLAUDE.md`, `PRODUCT.md`, `ARCHITECTURE.md` found from project root or `docs/` and injected into agent prompts. |
| Single process | `mkdir` + PID lock at `.aishore/data/status/.aishore.lock/`. Self-healing on stale PIDs. |
| Checksum-verified updates | Remote `checksums.sha256` manifest drives file list. All paths validated (must start `.aishore/`, no traversal). |
