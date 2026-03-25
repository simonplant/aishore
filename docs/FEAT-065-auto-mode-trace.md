# FEAT-065 Code Trace: auto_mode / _auto / auto_scope References

This document maps every reference to `auto_mode`, the internal `--_auto` flag, and `auto_scope` in `.aishore/aishore` to support the FEAT-065 run/auto merge. Line numbers are approximate — verify before editing.

## 1. Entry Point: `cmd_auto()` (line ~2234)

`cmd_auto()` validates the scope argument (done/p0/p1/p2) and delegates:

```bash
cmd_run --_auto "$scope" "$@"
```

This is the **only** caller of `--_auto`. The entire auto mode is activated by this single internal flag passed from `cmd_auto` → `cmd_run`.

**Merge plan:** `cmd_auto` disappears. Its scope validation moves into `cmd_run_parse_args`. The `auto` CLI verb becomes a hidden alias that calls `cmd_run` with the scope as a positional arg.

## 2. Flag Parsing: `cmd_run_parse_args()` (line ~2935)

```bash
"val:auto_scope:--_auto"   # parses --_auto <scope> into auto_scope
[[ -n "$auto_scope" ]] && auto_mode=true   # line 2941
```

`auto_scope` holds the raw scope string (done/p0/p1/p2). `auto_mode` is a derived boolean — true whenever a scope is present.

**Merge plan:** Replace `--_auto` with direct positional arg detection. If a positional arg matches `done|p0|p1|p2`, set `auto_scope` and `auto_mode=true`. Otherwise, treat it as a count or item ID (existing behavior).

## 3. Variable Initialization: `cmd_run()` (line ~3876)

```bash
local auto_mode=false auto_scope="" auto_priorities=""
```

These are local to `cmd_run` and flow through all helper functions via outer-scope access.

**Merge plan:** No change needed — these locals stay in `cmd_run`.

## 4. All `auto_mode` Conditionals — Categorized by Behavior

### 4a. Dry-run display: `_run_dry_run()` (line ~2267)

```bash
if [[ "$auto_mode" == "true" ]]; then
    log_header "aishore auto $auto_scope - Dry Run"
    # shows auto-groom threshold, circuit breaker settings
else
    log_header "aishore - Dry Run"
fi
```

**Purpose:** Different header and extra info for auto mode dry runs.
**Merge plan:** Keep the conditional — when scope is given, show scope-specific info.

### 4b. Session failure context: `_run_developer_cycle()` (line ~2459)

```bash
if [[ "$auto_mode" == "true" && ${#session_failures[@]} -gt 0 ]]; then
    # Append last 5 session failure patterns to developer prompt
fi
```

**Purpose:** In auto mode, subsequent developer agents get context about prior failures in the session to avoid repeating mistakes.
**Merge plan:** This should activate whenever `count > 1` or scope is present (multi-item sessions). Consider: `if [[ ($auto_mode == "true" || $count -gt 1) && ... ]]` or simply always include when session_failures is non-empty.

### 4c. Sprint environment setup: `setup_sprint_environment()` (lines ~3034–3097)

**Line 3034 — Set count and priority scope:**
```bash
if [[ "$auto_mode" == "true" ]]; then
    count=9999
    case "$auto_scope" in
        p0)   auto_priorities="must" ;;
        p1)   auto_priorities="must should" ;;
        p2)   auto_priorities="must should could" ;;
        done) auto_priorities="" ;;
    esac
    log_header "aishore auto $auto_scope"
fi
```
**Purpose:** Auto mode runs until drained (count=9999) and maps scope to priority filters.
**Merge plan:** When scope is given, set count=9999 and map priorities. When scope is absent, use count from positional arg (default 1).

**Line 3047 — Header display:**
```bash
if [[ "$auto_mode" == "true" ]]; then
    echo "Scope: $scope_label"
    echo "Circuit breaker: ..."
elif [[ -n "$specific_id" ]]; then
    echo "Item: $specific_id"
else
    echo "Sprints: $count"
fi
```
**Purpose:** Auto mode shows scope and circuit breaker in header.
**Merge plan:** Show scope/circuit-breaker info whenever auto_mode is true (i.e., scope was given).

**Line 3097 — Queued item logging:**
```bash
if [[ "$auto_mode" == "true" && -z "$specific_id" ]]; then
    # Log per-priority breakdown of queued items
fi
```
**Purpose:** Auto mode shows priority breakdown (N must, N should, etc.).
**Merge plan:** Show whenever scope is present.

### 4d. Sprint loop: `run_sprint_loop()` (lines ~3496–3760)

**Line 3498 — Circuit breaker:**
```bash
if [[ "$auto_mode" == "true" && "$consecutive_failures" -ge "$max_consecutive_failures" ]]; then
    log_error "Circuit breaker: ... — stopping"
    break
fi
```
**Purpose:** Stop after N consecutive failures. Only meaningful in multi-item sessions.
**Merge plan:** Activate when scope is present OR count > 1.

**Line 3503 — Progress display:**
```bash
if [[ "$auto_mode" == "true" ]]; then
    # Show elapsed time, progress count, sprint sub-header
else
    [[ $count -gt 1 ]] && log_subheader "Sprint $i/$count"
fi
```
**Purpose:** Richer progress info in auto mode vs simple "Sprint N/M" in run mode.
**Merge plan:** Use scope-style progress when scope is present; count-style when running N items.

**Line 3526 — Auto-groom trigger:**
```bash
if [[ "$auto_mode" == "true" && "$groom_exhausted" != "true" ]]; then
    local total_ready=$(_count_total_ready)
    if [[ "$total_ready" -lt "$AUTO_GROOM_THRESHOLD" ]]; then
        # Run architect → tech-lead → product-owner grooming
    fi
fi
```
**Purpose:** Auto-groom when ready items drop below threshold. This is a **core auto-mode-only behavior** — replenishes the backlog mid-session.
**Merge plan:** Activate when scope is present. This is the key feature that distinguishes scoped runs from simple N-item runs.

**Line 3600 — Parallel dispatch:**
```bash
if [[ "$parallel_count" -gt 1 && "$auto_mode" == "true" && -z "$specific_id" ]]; then
    # Pick batch of items with disjoint scopes, run in parallel
fi
```
**Purpose:** Parallel execution only in auto mode (multi-item drain).
**Merge plan:** Activate when scope is present or count > 1 (any multi-item run).

**Line 3621, 3735, 3759 — Progress logging (3 occurrences):**
```bash
[[ "$auto_mode" == "true" ]] && log_info "Progress: $passed passed, $failed failed, $(_count_total_ready) remaining ready"
```
**Purpose:** Progress updates after parallel batch, after failure, and after success.
**Merge plan:** Show whenever scope is present.

**Line 3634 — Backlog drained message:**
```bash
elif [[ "$auto_mode" == "true" ]]; then
    log_success "No more ready items — backlog drained"
```
**Purpose:** Friendly message when auto mode runs out of items (vs warning in run mode).
**Merge plan:** Show when scope is present.

**Line 3643 — Priority scope check:**
```bash
if [[ "$auto_mode" == "true" && -n "$auto_priorities" ]]; then
    # Check if picked item's priority is within auto_priorities
    # Break if out of scope
fi
```
**Purpose:** Stop when remaining items are below the requested priority tier.
**Merge plan:** Activate when scope is present and scope != "done".

### 4e. Summary: `print_sprint_summary()` (lines ~3793–3861)

**Line 3795 — Batch summary:**
```bash
if [[ "$auto_mode" == "true" || $count -gt 1 ]]; then
    print_batch_summary ...
fi
```
**Purpose:** Print summary table after multi-item runs. Already handles both modes!
**Merge plan:** No change needed.

**Line 3812 — Architecture review offer:**
```bash
if [[ "$auto_mode" == "true" && $failed -eq 0 && $passed -gt 0 ]]; then
    # Offer or auto-run architecture review
fi
```
**Purpose:** Offer review after successful auto drain.
**Merge plan:** Offer when scope is present (draining entire tiers warrants review).

**Line 3840 — Zero-items warning:**
```bash
if [[ "$auto_mode" == "true" && $passed -eq 0 && $failed -eq 0 ]]; then
    # Warn about unready items in backlog
fi
```
**Purpose:** Help users understand why auto mode processed nothing.
**Merge plan:** Show when scope is present.

**Line 3848 — Final status messages:**
```bash
if [[ "$auto_mode" == "true" ]]; then
    # "Mission complete/aborted/ended" messages with notifications
else
    log_header "Results: $passed passed, $failed failed"
fi
```
**Purpose:** Richer completion messages and desktop notifications in auto mode.
**Merge plan:** Use mission-style messages when scope is present.

## 5. CLI Dispatch (line ~6014)

```bash
auto)    cmd_auto "$@" ;;
```

**Merge plan:** Keep as hidden alias: `auto) shift; cmd_run "$@" ;;` or similar.

## 6. Summary: Behaviors That Activate Only in Auto Mode

| Behavior | Lines | Condition After Merge |
|----------|-------|-----------------------|
| **Auto-groom** (replenish backlog mid-session) | ~3526 | scope is present |
| **Circuit breaker** (stop after N failures) | ~3498 | scope is present OR count > 1 |
| **Session failure context** (feed failure patterns to next dev) | ~2459 | session_failures non-empty (any multi-item) |
| **Priority filtering** (stop at priority boundary) | ~3643 | scope is present and != "done" |
| **Parallel dispatch** | ~3600 | parallel_count > 1 (any multi-item) |
| **Progress logging** | ~3503,3621,3735,3759 | scope is present |
| **Architecture review offer** | ~3812 | scope is present |
| **Zero-items warning** | ~3840 | scope is present |
| **Mission-style messages + notifications** | ~3848 | scope is present |
| **count=9999** (run until drained) | ~3035 | scope is present |

## 7. Planned Merge Approach for FEAT-065

### Core change
`cmd_run` accepts an optional positional scope (`done|p0|p1|p2`). When present, `auto_mode=true` and all auto behaviors activate. When absent, existing `run` behavior is unchanged.

### What stays the same
- All auto-mode behaviors remain — they just activate based on "scope is present" instead of "came from cmd_auto".
- `auto_scope`, `auto_mode`, `auto_priorities` locals stay in `cmd_run`.
- `print_batch_summary` already handles both modes (line 3795).

### What changes
1. **`cmd_auto()`** — reduced to hidden alias (scope validation moves to `cmd_run_parse_args`).
2. **`cmd_run_parse_args()`** — detect `done|p0|p1|p2` as positional args, set `auto_scope` + `auto_mode`.
3. **`--_auto` flag** — removed. No longer needed since scope is parsed directly.
4. **CLI dispatch** — `auto)` becomes `auto) cmd_run "$1" "${@:2}" ;;` (passes scope as positional to run).
5. **Help text** — updated to show `run [N|ID|done|p0|p1|p2]`.

### What does NOT change
- No conditional logic inside the sprint loop changes. Every `if [[ "$auto_mode" == "true" ]]` stays exactly as-is.
- `auto_mode` remains a boolean. It's just set by positional arg detection instead of `--_auto`.
- Session failure tracking, circuit breaker, auto-groom, parallel dispatch — all untouched.

### Risk assessment
- **Low risk:** The merge is essentially moving scope validation from `cmd_auto` to `cmd_run_parse_args` and removing the `--_auto` bridge. No sprint loop logic changes.
- **Backward compat:** `auto done` continues to work as a hidden alias.
- **Testing:** Run `aishore run`, `aishore run 2`, `aishore run FEAT-xxx`, `aishore run done`, `aishore auto done` — all should produce identical behavior to current state.
