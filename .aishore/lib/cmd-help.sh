#!/usr/bin/env bash
# Module: cmd-help — help and usage commands
# Lazy-loaded by _load_module; all globals (AISHORE_VERSION, AISHORE_ROOT,
# log_error) come from the main script.

cmd_usage() {
    _help_compact
}

cmd_help() {
    local arg="${1:-}"
    case "$arg" in
        --full) sed "s/__VERSION__/$AISHORE_VERSION/g" "$AISHORE_ROOT/help.txt" ;;
        run)    _help_run ;;
        backlog) _help_backlog ;;
        groom)    _help_groom ;;
        scaffold) _help_scaffold ;;
        refine) _help_refine ;;
        review) _help_review ;;
        status) _help_status ;;
        update) _help_update ;;
        clean)  _help_clean ;;
        insights) _help_insights ;;
        init)   _help_init ;;
        doctor) _help_doctor ;;
        logs)   _help_logs ;;
        "")     _help_compact ;;
        *)      log_error "No help topic for: $arg"; _help_compact >&2; return 1 ;;
    esac
}

_help_compact() {
    cat <<EOF
aishore - iterative intent-based development with evals (v${AISHORE_VERSION})

Usage: aishore <command> [options]

Getting started:
  1. aishore init                  # setup wizard
  2. aishore refine                # describe what you're building (PRODUCT.md)
  3. aishore backlog populate      # create items from PRODUCT.md
  4. aishore groom                 # prepare items for sprint
  5. aishore run                   # execute first sprint

Commands:
  run [N|ID|scope] Run sprints, or drain backlog with scope (done|p0|p1|p2)
  backlog <sub>    Manage backlog (list|add|show|edit|check|rm|requeue|populate)
  groom            Groom backlog items (AI adds steps, AC, priority)
  refine           Improve PRODUCT.md through interactive interview
  scaffold         Detect fragment risk, inject scaffolding items
  review           Architecture review
  status           Backlog overview and sprint readiness
  init             Setup wizard
  help <command>   Show detailed help for a command
  help --full      Show complete reference

Other: clean, doctor, insights, logs, update, checksums, version
EOF
}

_help_run() {
    cat <<EOF
aishore run — Run sprint items

Usage: aishore run [<count>|<ID>|<scope>] [options]

  aishore run              Run 1 sprint (next ready item)
  aishore run 3            Run 3 sprints
  aishore run FEAT-001     Run specific item by ID
  aishore run done         Drain entire backlog (auto-grooms when ready items low)
  aishore run p0           Complete all P0 (must) items
  aishore run p1           Complete all P0+P1 (must + should) items
  aishore run p2           Complete all P0-P2 (must + should + could) items

When a scope (done/p0/p1/p2) is given, auto-grooming and the circuit breaker
activate automatically.

Options:
  --context <text>      One-time developer hint injected into the prompt (not persisted)
  --dry-run             Preview without running agents
  --no-merge            Keep feature branches for review
  --pr                  Create GitHub PRs instead of merging (requires gh CLI)
  --retries N           Retry attempts on validation failure
  --max-failures N      Circuit breaker: stop after N consecutive failures
  --limit N             Stop after N successful items

Examples:
  aishore run FEAT-001               # Run specific item
  aishore run --no-merge 3           # Keep branches for review
  aishore run --pr done              # Drain backlog, open PRs for review
  aishore run done                   # Drain entire backlog
  aishore run p1 --retries 2         # Must + should, with retries
EOF
}

_help_backlog() {
    cat <<EOF
aishore backlog — Manage backlog items

Usage: aishore backlog <subcommand> [options]

Subcommands:
  list              List all items (features + bugs)
    --status <s>      Filter by status (todo, in-progress, done)
    --type <t>        Filter by type (feat, bug)
    --priority <p>    Filter by priority (must, should, could, future)
    --track <t>       Filter by track (core, feature)
    --ready           Show only sprint-ready items
    --no-ready        Show only items not yet ready
    --failed          Show only items that have failed
  add --json '{..}' Add a new item (JSON object, or pipe via stdin)
  show <ID>         Show full detail of one item
  edit <ID> --json '{..}' Update fields on an item (merges onto existing)
  check <ID>        Check readiness gates for an item
    --all             Audit every non-done item
    --quick           Skip verify command execution (metadata gates only)
  rm <ID>           Remove an item (--force to skip confirmation)
  requeue <ID>      Reset a failed item back to todo (clears failure tracking)
  populate          Create items from PRODUCT.md (AI-assisted)

Examples:
  aishore backlog list --ready         # Show sprint-ready items
  aishore backlog add --json '{"title": "Add auth", "intent": "Users can log in securely"}'
  aishore backlog edit FEAT-001 --json '{"priority": "must", "readyForSprint": true}'
  aishore backlog check --all          # Audit all items
  aishore backlog populate             # Populate from PRODUCT.md
EOF
}

_help_groom() {
    cat <<EOF
aishore groom — AI-assisted backlog grooming

Usage: aishore groom

Grooms the entire backlog — bugs, features, and tech debt. Adds steps,
acceptance criteria, sets priorities, and marks items ready for sprint.

Examples:
  aishore groom                # Groom entire backlog
EOF
}

_help_scaffold() {
    cat <<EOF
aishore scaffold — Scaffolding review

Usage: aishore scaffold

Runs the architect agent to detect fragment risk — stub entry points,
mock-only dependencies, disconnected modules — and creates scaffolding
items to wire up the top-down skeleton before feature work continues.

Examples:
  aishore scaffold             # Detect missing scaffolding, add skeleton items
EOF
}

_help_review() {
    cat <<EOF
aishore review — Architecture review

Usage: aishore review [options]

Options:
  --update-docs       Allow updates to documentation files
  --since <hash>      Review changes since specific commit

Examples:
  aishore review                       # Read-only review
  aishore review --update-docs         # Review and update docs
  aishore review --since abc123        # Review recent changes
EOF
}

_help_status() {
    cat <<EOF
aishore status — Backlog overview and sprint readiness

Shows item counts, ready items, currently running sprint, and recent history.
EOF
}

_help_update() {
    cat <<EOF
aishore update — Update from upstream

Usage: aishore update [options]

Options:
  --dry-run     Check for updates without applying
  --force       Update even if already on latest version
  --ref REF     Update to a specific git ref (commit SHA, branch, or tag)
EOF
}

_help_clean() {
    cat <<EOF
aishore clean — Archive and remove done items

Usage: aishore clean [options]

Options:
  --dry-run       Preview what would be removed
  --no-archive    Remove without archiving
  --regression    Clear the regression suite (backup created before removal)
                  Use with --dry-run to preview entry count by item

Examples:
  aishore clean                          # Archive and remove done items
  aishore clean --regression --dry-run   # Preview regression suite entries
  aishore clean --regression             # Backup and clear regression suite
EOF
}

_help_insights() {
    cat <<EOF
aishore insights — Cross-session sprint insights from archive analysis

Usage: aishore insights

Analyzes sprint archive (sprints.jsonl, regression.jsonl) to reveal patterns:
  - Failure patterns: which items needed retries, failure rates by priority/type
  - Fragile files: files most referenced in regression checks
  - Velocity trends: sprints per session, duration stats, code churn
  - Actionable recommendations based on the data

Examples:
  aishore insights             # Full insights report
EOF
}

_help_init() {
    cat <<EOF
aishore init — Setup wizard

Usage: aishore init [options]

Checks prerequisites, detects project settings, and configures aishore.

Options:
  -y, --yes     Accept all detected defaults (non-interactive)
  --demo        Create a tiny demo project and run sprints on it so you
                can experience the full lifecycle before configuring your
                own project
EOF
}

_help_doctor() {
    cat <<EOF
aishore doctor — Diagnose health and configuration

Usage: aishore doctor [options]

Checks the runtime environment and reports health:
  - Required tools: jq, git, claude (PASS/FAIL)
  - Optional tools: yq (PASS/WARN)
  - Backlog files: validates JSON syntax (PASS/FAIL)
  - Config: checks config.yaml is parseable (PASS/WARN/FAIL)
  - Core status: reports CORE_CMD value (PASS/WARN)

Options:
  --regression    Run the regression suite (backlog/archive/regression.jsonl)
                  Reports PASS/FAIL per entry with item ID and description.
                  Useful for debugging pre-flight failures without running
                  a full sprint.

Exit code:
  0   All checks pass (or regression file absent/empty)
  1   One or more checks failed

Examples:
  aishore doctor                   # Run all health checks
  aishore doctor --regression      # Run regression suite diagnostics
EOF
}

_help_refine() {
    cat <<EOF
aishore refine — Improve PRODUCT.md interactively

Usage: aishore refine [options]

Launches an interactive AI interview to improve your product requirements
document. The Refiner agent reads the codebase and existing backlog, then
asks targeted questions to fill gaps in PRODUCT.md.

Options:
  --from-sprints    Feed sprint learnings back into PRODUCT.md

The refine → populate → groom → run cycle:
  1. aishore refine                # Improve PRODUCT.md
  2. aishore backlog populate      # Generate backlog items
  3. aishore groom                 # Polish items for sprint
  4. aishore run done              # Execute sprints
  5. aishore refine --from-sprints # Learn and iterate

Examples:
  aishore refine                   # Interactive interview
  aishore refine --from-sprints    # Post-sprint feedback loop
EOF
}

_help_logs() {
    cat <<EOF
aishore logs — Show recent agent run history

Usage: aishore logs [options]

Displays recent entries from the agent run log (.aishore/data/logs/agent-runs.log).
Each entry shows when an agent ran, which agent, what command, how long it took,
and which model was used.

Options:
  --last N    Show last N entries (default: 20)

Examples:
  aishore logs                       # Show last 20 agent runs
  aishore logs --last 5              # Show last 5 agent runs
EOF
}
