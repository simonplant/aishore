# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aishore** ships working code, not evidence of process. It is an autonomous sprint orchestration layer for Claude Code — humans own what to build (intent, priority), machines own how fast and how correctly (implementation, validation, regression protection).

The tool picks items from a backlog, has an AI developer implement them through a quality protocol, validates against intent and executable checks, and merges the result. The proof is that it runs — not that tests pass, not that a reviewer approved, not that coverage hit a number.

The tool is self-contained in `.aishore/` and user content lives in `backlog/` at project level.

## Commands

```bash
# Lint & validate
shellcheck .aishore/aishore
jq empty backlog/*.json

# CLI commands
.aishore/aishore init               # Interactive setup wizard
.aishore/aishore init -y            # Non-interactive (accept detected defaults)
.aishore/aishore backlog list       # List all items
.aishore/aishore backlog add        # Add item with flags
.aishore/aishore backlog show <ID>  # Show full detail of one item
.aishore/aishore backlog edit <ID>  # Update fields on an item
.aishore/aishore backlog check <ID> # Check readiness gates for an item
.aishore/aishore backlog check --all # Audit all non-done items in one pass
.aishore/aishore backlog rm <ID>    # Remove an item (--force to skip confirmation)
.aishore/aishore run [N]            # Run N sprints (branch, commit, merge, push per item)
.aishore/aishore run <ID>           # Run specific item (e.g., FEAT-001)
.aishore/aishore run done           # Drain entire backlog (auto-grooms when ready items low)
.aishore/aishore run p0             # Complete all P0 (must) items
.aishore/aishore run p1             # Complete all P0+P1 (must + should) items
.aishore/aishore run p2             # Complete all P0-P2 (must + should + could) items
.aishore/aishore run done --retries 2        # With per-item retries
.aishore/aishore run p1 --max-failures 3     # Custom circuit breaker
.aishore/aishore run done --limit 3           # Cap session at 3 items
.aishore/aishore run --no-merge 3            # Keep feature branches for PR review
.aishore/aishore run --pr FEAT-001           # Create GitHub PR for review
.aishore/aishore run --dry-run      # Preview without running agents
.aishore/aishore groom              # Groom bugs, features, and tech debt
.aishore/aishore scaffold           # Scaffolding review (detect fragment risk)
.aishore/aishore review             # Architecture review
.aishore/aishore review --update-docs          # Review and update docs
.aishore/aishore review --since <commit>       # Review changes since commit
.aishore/aishore clean              # Remove done items from backlogs
.aishore/aishore clean --dry-run    # Show what would be removed
.aishore/aishore status             # Show backlog overview and sprint readiness
.aishore/aishore update             # Update from upstream (checksum-verified)
.aishore/aishore update --dry-run   # Check for updates without applying
.aishore/aishore update --force     # Update even if already on latest
.aishore/aishore version            # Show version
.aishore/aishore help               # Show usage
```

No build step — the tool is pure Bash. The core orchestrator lazy-loads command modules from `.aishore/lib/` at dispatch time.

## Architecture

**Sprint execution flow:**
```
Pick Item → Create Branch (aishore/<ID>) → Preflight (regression + baseline) → Developer Agent (with maturity protocol) → Validation Command → AC Verify Commands → Validator Agent → Commit → Merge → Archive
```

**Maturity protocol:** The developer agent is instructed to run a 3-phase cycle within a single session: (1) Implement — write the code, (2) Critique — shift to reviewer mindset, re-read all changes, verify each AC, hunt bugs/edge cases, fix everything found, (3) Harden — run full validation again, fix regressions, confirm all AC provably met. This keeps quality iteration inside the session where context is hot, rather than relying on external retry loops. The protocol is enforced via prompt instruction; the orchestrator verifies the final result (pass/fail + validation), not phase execution.

**Autonomous mode:** `run <scope>` (where scope is `done`, `p0`, `p1`, or `p2`) wraps the sprint loop with: priority-scoped item selection, auto-grooming when ready items drop below threshold, session failure tracking passed to subsequent developer agents, and a circuit breaker that stops after N consecutive failures. Auto-groom runs the architect first (scaffolding detection), then the groomer.

**Top-down scaffolding enforcement:** The system prevents fragment accumulation — building isolated pieces that never connect into a working whole. The architect agent (`scaffold`, also runs in auto-groom) detects fragment risk signals (stub entry points, mock-only dependencies, disconnected modules) and creates scaffolding backlog items with `must` priority and `dependsOn` chains. The developer agent is instructed to wire code to real entry points. The validator flags disconnected code as advisory notes. The groomer watches for feature priorities outrunning the skeleton during grooming.

**Git branching model:** Each sprint item runs in an isolated worktree on its own feature branch (`aishore/<ITEM-ID>`). The worktree contains only code changes — backlog mutations (mark complete, archive, remove) happen on the base branch after merge, never inside the worktree. This prevents merge conflicts on JSON backlog files. On success, the branch is merged back with `--no-ff`, pushed, and the base branch pulls latest before the next item. On failure, the branch is deleted but diagnostics (agent logs, result.json, failure metadata) are preserved on the base branch. On unexpected exit (Ctrl+C, crash), the feature branch is preserved for recovery. Use `--no-merge` to keep branches for PR review (they get pushed to origin instead).

**Modular architecture:** The CLI is split into a core orchestrator (`.aishore/aishore`) and lazy-loaded command modules in `.aishore/lib/`. Modules are loaded on demand via `_load_module <name>`, which sources `.aishore/lib/<name>.sh` once per process. This keeps startup fast and the main script focused on orchestration (agent invocation, git branching, sprint loop).

**Directory structure:**
```
project/
├── backlog/                 # User content (never touched by update)
│   ├── backlog.json
│   ├── bugs.json
│   ├── sprint.json
│   ├── DEFINITIONS.md       # DoR, DoD, priority/size definitions
│   └── archive/
│       ├── sprints.jsonl
│       └── regression.jsonl
└── .aishore/                # Tool (can be updated)
    ├── aishore              # Core orchestrator (Bash)
    ├── VERSION              # Version (single source of truth)
    ├── checksums.sha256     # SHA-256 checksums for update verification
    ├── agents/*.md          # Agent prompts
    ├── config.yaml          # Optional overrides (requires yq for full support)
    ├── templates/           # Init wizard templates
    ├── tests/               # Integration and smoke tests
    ├── lib/                 # Lazy-loaded command modules
    │   ├── cmd-backlog-read.sh   # backlog list/show/check/rm
    │   ├── cmd-backlog-write.sh  # backlog add/edit
    │   ├── cmd-clean.sh          # clean command
    │   ├── cmd-groom.sh          # groom command
    │   ├── cmd-scaffold.sh       # scaffold command (architect agent)
    │   ├── cmd-help.sh           # help/usage
    │   ├── cmd-init.sh           # init wizard
    │   ├── cmd-review.sh         # review command
    │   ├── cmd-status.sh         # status command
    │   └── cmd-update.sh         # update command
    └── data/                # Runtime (logs, status)
        ├── logs/
        └── status/
            ├── result.json      # Agent completion signal
            ├── .item_source     # Tracks which backlog file the current item came from
            └── .aishore.lock/   # mkdir+PID-based concurrency guard
```

**Completion contract:** Agents signal completion by writing to `.aishore/data/status/result.json`:
```json
{"status": "pass", "summary": "..."}
```
The orchestrator polls for this file, then proceeds to the next step.

**Context auto-detection:** aishore automatically finds and uses `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` from the project root (or `docs/` directory) as agent context.

**Module loading:** Command implementations are extracted into `.aishore/lib/cmd-*.sh` modules. The core script lazy-loads them via `_load_module <name>` at dispatch time — each module is sourced at most once per process. The core retains orchestration logic (sprint loop, agent invocation, git operations) while modules handle individual commands. All lib files are included in `checksums.sha256` for update verification.

**Agent invocation:** All agent invocations go through `run_agent()`, which assembles the prompt, appends the completion contract (and validation command hint for developers), and delegates to `run_agent_process()`. Permissions vary by role: developer gets `Agent,Bash,Edit,Write,Read,Glob,Grep`; validator gets `Bash,Read,Glob,Grep`; reviewer gets `Read,Glob,Grep` (or with `Edit,Write` when `--update-docs` is used). Permissions are configurable in `config.yaml`.

**Concurrency:** Only one aishore process runs at a time, enforced via a mkdir+PID lock at `.aishore/data/status/.aishore.lock/`. The lock is self-healing — stale locks from crashed processes are detected via PID liveness check and automatically cleaned up.

**Safe failure recovery:** Sprint failures preserve diagnostics (agent logs, result.json, failure context) to the base branch before destroying the worktree, then delete the feature branch. Failure metadata (failCount, lastFailReason) is written to the base branch's backlog so it persists across sessions. On unexpected exit (Ctrl+C, OOM), the worktree is cleaned up but the feature branch is preserved for manual recovery. The safety commit excludes `backlog/` and `.aishore/` — only code changes belong on the feature branch.

**Scope checking:** Items can have a `scope` array of glob patterns (e.g., `["src/**", "tests/**"]`). Scope is advisory — injected into the developer prompt as preferred file constraints but not mechanically enforced post-commit.

**Testable acceptance criteria:** AC entries can be plain strings or `{text, verify}` objects. The `verify` field is a shell command run by the orchestrator after development; failures trigger retries. Use `--ac "text" --ac-verify "command"` in `backlog add`/`backlog edit`. Groom agents are instructed to generate verify commands that prove behavior works — not commands that grep for code structure. Items with 0% verify coverage trigger advisory warnings during sprint.

**Regression suite:** When a sprint completes successfully, all `verify` commands from its AC are saved to `backlog/archive/regression.jsonl`. Before every subsequent sprint, the full regression suite runs as part of pre-flight — if any prior sprint's verify command fails, the sprint is aborted. This ensures sprints cannot silently break work completed by earlier sprints. The regression suite compounds automatically and requires no manual maintenance.

**Adversarial validation:** The validator agent is instructed by the orchestrator to actively probe implementations using Bash commands, not just read diffs. When AC claims observable behavior, the validator must execute commands to verify it. This is injected at runtime by the orchestrator, not in the agent prompt.

**Validation sequence:** After the developer finishes, the orchestrator runs three checks in order: (1) validation command (your test suite/linter), (2) all AC verify commands from the item, (3) the Validator agent with AC results passed as context. All three must pass. The validator receives the AC verification report but may also re-run commands independently.

**Readiness gates:** `backlog check <ID>` validates an item has a title, commander's intent (>=20 chars, must be a directive not a label), steps, acceptance criteria, and no too-short steps. `backlog edit <ID> --ready` warns on gate failures but doesn't block. **Intent is a hard gate at sprint time** — items without intent (or with intent <20 chars) are silently skipped by auto-pick and explicitly rejected when run by ID.

**Baseline pre-flight:** Before the developer agent runs, the validation command is executed on the current codebase. If baseline fails, the sprint is aborted immediately.

**Spec refinement:** When all retries are exhausted, an AI agent automatically refines the spec (steps + AC, not intent) and attempts one more developer cycle.

**Configuration precedence:** env vars > config.yaml > built-in defaults. Note: full config.yaml support requires `yq`; without it, only `validation.command` is parsed via grep fallback.

**Update integrity:** Both `install.sh` and `cmd_update()` resolve the latest GitHub release tag via the API, then fetch files from that tagged snapshot (falling back to `main` if no release exists). The file list is discovered dynamically from the remote `checksums.sha256` manifest. All paths are validated (must start with `.aishore/`, no `..` traversal, no absolute paths) and `config.yaml` is explicitly skipped to protect user config. Files are staged to a temp directory, verified against SHA-256 checksums, and only installed if all checks pass.

**Version management:** `.aishore/VERSION` is the single source of truth. The CLI reads it at runtime.

## Code Style

- Use `set -euo pipefail` at the start
- Quote all variables: `"$var"` not `$var`
- Use `[[ ]]` for conditionals, not `[ ]`
- Use `$(command)` not backticks
- Functions: `snake_case`, Constants: `UPPER_SNAKE_CASE`

## Dependencies

- Bash 4.4+
- jq
- git
- claude (Claude Code CLI)
- yq (optional, for full config.yaml support)
- On macOS: `brew install coreutils` (for `gtimeout`)

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

<!-- This section is managed by aishore and will be overwritten on `aishore update`. -->
<!-- Customizations here will be lost. Add project-specific instructions above this section. -->
## Sprint Orchestration (aishore)

This project uses aishore for autonomous sprint execution. Backlog lives in `backlog/`, tool lives in `.aishore/`. Run `.aishore/aishore help` for full usage.

**How it works:** aishore picks items from the backlog by priority, implements each on a feature branch, validates against commander's intent and executable acceptance criteria, and merges. Quality comes from execution — code must run and prove it works, not just pass review or hit coverage numbers.

**What this means for you (if you're an AI agent in this project):**
- **Intent is the north star.** Every item has a commander's intent field. When steps or AC are ambiguous, follow intent.
- **Prove it runs.** Wire code to real entry points. If the build command exists, run it. If a verify command exists, execute it. Working code that's reachable beats tested code that's isolated.
- **No mocks or stubs.** Never use mocks or stubs unless the item explicitly requests them. Connect to the real system.
- **Stay in scope.** Implement the item you're assigned. Don't fix unrelated code, add unrequested features, or refactor surrounding code.

```bash
.aishore/aishore run [N|ID]         # Run sprints (branch, commit, merge, push per item)
.aishore/aishore groom              # Groom bugs, features, and tech debt
.aishore/aishore scaffold           # Scaffolding review
.aishore/aishore review             # Architecture review
.aishore/aishore status             # Backlog overview
```
