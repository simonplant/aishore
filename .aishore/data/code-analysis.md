# aishore CLI Deep Code Analysis

**Date:** 2026-03-20
**Scope:** Every function in `.aishore/aishore` (5,328 lines, 82 functions)
**Goal:** Identify code that is not concise, has redundancy, or is a candidate for refactoring/removal — beyond the 13 items already filed (BUG-060 through BUG-072).

---

## Verdict Legend

- **RETAIN** — Production quality, concise, earns its lines
- **TRIM** — Correct but has dead weight that can be removed
- **REFACTOR** — Structural issue; logic is sound but implementation is bloated or duplicated

---

## 1. Core Sprint Engine (lines 1858–2633)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `_run_preflight` | 17 | RETAIN | 1 | `truncate_output` called on success path but result unused |
| `_run_developer_cycle` | 39 | RETAIN | ~5 | Session-failures loop could use `printf`; `fail_reason` inlinable |
| `_run_validation_cycle` | 62 | REFACTOR | ~4 | `truncate_output` + `rm` duplicated in both branches of validate cmd |
| `_validation_failure_reason` | 9 | RETAIN | 0 | Clean dispatch table |
| `_run_retry_loop` | 37 | RETAIN | 0 | Symmetric, readable |
| `_handle_sprint_success` | 129 | **REFACTOR** | **14–17** | Remote sync block duplicated between squash (2132–2138) and no-ff (2162–2168) — 7 lines identical. `merge_msg` if/else collapsible to one expression. Safety-commit message pattern repeated. |
| `cmd_run` arg parsing | 44 | RETAIN | 0 | Standard boilerplate |
| `cmd_run` setup | 97 | RETAIN | ~4 | Double `auto_mode` check; worktree isolation log expendable |
| `cmd_run` sprint loop | 219 | **REFACTOR** | **~13** | Skip-list builder: 4-line loop → `IFS=,; echo "${!FAILED_IDS[*]}"`. Priority scope check: 13-line loop → `[[ " $auto_priorities " == *" $item_priority "* ]]` saves 8. Failure-ctx builder → `printf`. |
| `cmd_run` post-summary | 95 | RETAIN | ~3 | Duplicate `[[ -s "$review_output" ]]` check |
| `cmd_run` entry | 30 | RETAIN | 0 | Clean |

**Section total: ~40–47 saveable lines**

### Key findings:
- **`_handle_sprint_success`** is the worst offender: 7 lines of push/pull/cleanup code copy-pasted between squash and no-ff merge paths. Extract `_sync_remote()`.
- **Sprint loop** has 3 bash idioms that are 3–8 lines each where 1-line alternatives exist.
- **Auto-groom block** (31 lines inside the loop) duplicates `cmd_groom` pipeline — already captured by BUG-069.

---

## 2. Agent Execution (lines 964–1315)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `_file_hash` | 9 | RETAIN | 0 | Portable hash, correct |
| `_check_groom_progress` | 34 | RETAIN | 0 | Monitoring helper, clean |
| `run_agent_process` | 113 | RETAIN | 0 | Complex but necessary: setsid, --print vs stream, pid management |
| `build_agent_prompt` | 136 | TRIM | ~5 | After BUG-062 extracts populate docs: remaining maturity protocol text has one duplicated `$validate_hint="$validate_hint` append pattern |
| `run_agent` | 55 | RETAIN | 0 | Clean orchestrator |
| `show_failure_log_tail` | 13 | RETAIN | 0 | |
| `check_result` | 33 | RETAIN | 0 | |

**Section total: ~5 saveable lines**

### Key finding:
- Agent execution is the **most well-written section** of the codebase. `run_agent_process` is complex but earns every line (process management, timeout, setsid, logging).

---

## 3. Validation & Checks (lines 568–665, 1366–1475)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `check_readiness_gates` | 98 | **REFACTOR** | **~10** | 6 imperative checks follow identical 4-line pattern (extract → test → append warning → set flag). Not data-driveable in bash, but the 12-line **advisory complexity hints** block (lines 648–660) is not a gate — it belongs in the caller `cmd_backlog_check`, not polluting the gate function. |
| `check_scope_violations` | 60 | RETAIN | 0 | Correct glob matching |
| `run_ac_verification` | 48 | RETAIN | 0 | Clean verify loop |

**Section total: ~10 saveable lines**

---

## 4. Item Selection (lines 424–762)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `pick_item` | 99 | RETAIN | ~4 | `skip_json` construction (2 lines) duplicated with `list_pickable_ids`; extract `_build_skip_json()` |
| `list_pickable_ids` | 27 | RETAIN | 0 | Shares `ITEM_PROJECTION` constant correctly |
| `collect_done_ids` | 10 | RETAIN | 0 | |

**Section total: ~4 saveable lines**

---

## 5. Backlog CRUD (lines 4058–4998)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `cmd_backlog` router | 21 | RETAIN | 0 | Clean dispatch |
| `cmd_backlog_check` | 16 | RETAIN | 0 | Clean delegate |
| `cmd_backlog_populate` | 83 | TRIM | ~3 | Empty flag-loop (3 lines) for a command that takes no flags → one-liner guard |
| `cmd_backlog_list` | 60 | TRIM | ~3 | `blocked_display` variable used once, inlinable |
| `cmd_backlog_add` | 261 | **REFACTOR** | **~16** | AC JSON array built by manual string concat (10 lines) — identical pattern in `cmd_backlog_edit`. Extract shared `_build_ac_json` helper. Array-build boilerplate (steps/scope/deps) each 4 lines with an `if` guard → one-liner with `|| echo "[]"`. |
| `cmd_backlog_show` | 32 | RETAIN | 0 | Excellent — one `jq -r` call does everything |
| `cmd_backlog_edit` | 212 | **REFACTOR** | **~34** | Same AC builder duplication. Three identical scope/steps/deps append blocks (23 lines → 3 with helper). 14 `update_desc` accumulation lines for a cosmetic log message — removable. |
| `cmd_backlog_history` | 84 | RETAIN | ~4 | Minor: `tail -n "$limit"` semantics (last N, not first N) may be unintentional |
| `cmd_backlog_sync` | 152 | TRIM | ~10 | Mark-done logic duplicated between `--auto` and interactive branches. Per-item dual jq calls combinable. |
| `cmd_backlog_rm` | 33 | RETAIN | 0 | Clean |

**Section total: ~70 saveable lines**

### Key findings:
- **AC JSON builder duplication** is the #1 cross-cutting issue in CRUD: 10 identical lines in `add` and `edit`. A 6-line helper eliminates both.
- **Array-append pattern** (scope, steps, deps) repeats 3 times in `edit` with identical structure. A parameterized helper collapses 23 lines to 3 calls.
- **`update_desc` tracking** in edit is 14 lines of string concatenation for `"Updated FEAT-001: title priority ready"` — marginal UX value vs 14 lines of code.

---

## 6. Backlog Helpers (lines 533–813)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `resolve_backlog_file` | 21 | RETAIN | 0 | |
| `find_item` | 11 | RETAIN | 0 | |
| `next_id` | 19 | RETAIN | 0 | |
| `update_item` | 15 | RETAIN | 0 | |
| `add_item` | 12 | RETAIN | 0 | |
| `remove_item` | 10 | RETAIN | 0 | |
| `remove_items_by_status` | 10 | RETAIN | 0 | |
| `validate_priority/status/arg` | 21 | RETAIN | 0 | |
| `count_*/list_ready_*` | 19 | RETAIN | 0 | |
| `get_item_source` | 4 | RETAIN | 0 | |

**Section total: 0 saveable lines** — All helpers are tight and earn their lines.

---

## 7. Grooming (lines 2635–2964)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `cmd_groom` | 61 | REFACTOR | ~12 | Pipeline boilerplate (snapshot → agent → protect → enforce → diff) duplicated with `cmd_backlog_populate` — already captured by BUG-069 |
| `print_groom_summary` | 58 | TRIM | (already in BUG-067) | |
| `print_groom_diff` | 37 | TRIM | (already in BUG-067) | |
| `protect_items_from_groom` | 73 | RETAIN | ~3 | Safety-critical; minor jq consolidation only. Two jq calls (`was_modified` check + `merged` construction) combinable into one. |
| `enforce_groom_limits` | 76 | REFACTOR | ~8 | Per-item loop calls `jq -r ".[$i].id"` and `jq -r ".[$i].priority"` separately — 2 forks per item, combinable to 1. Global `GROOM_ITEMS_ADDED=0` declared outside function — move inside. |
| `snapshot_backlogs` | 8 | RETAIN | 0 | |

**Section total: ~23 saveable lines** (beyond what BUG-067/068/069 already cover)

---

## 8. Sprint State (lines 817–947)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `create_sprint` | 44 | **REFACTOR** | **~8** | 5 sub-shell `$(echo "$item_json" | jq ...)` calls extract fields that could be accessed inline by passing `item_json` as `--argjson item`. Saves 5 forks and ~8 lines. |
| `mark_complete` | 78 | REFACTOR | ~5 | Two separate `jq` calls for `item_priority` and `item_category` (lines 920–922) — combinable to one. Cross-platform date fallback (6 lines) is verbose but necessary. |
| `reset_sprint` | 5 | RETAIN | 0 | |

**Section total: ~13 saveable lines**

---

## 9. Config (lines 328–404)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `load_config` | 48 | RETAIN | ~2 | Already data-driven `_cfg_map` array. Redundant `return 0`. |
| `_apply_env_overrides` | 28 | RETAIN | ~1 | Parallel structure to `load_config`. Could unify both tables into one master table — saves ~10 lines but adds complexity. |

**Section total: ~3 saveable lines** (or ~13 with unified table refactor)

---

## 10. Init Wizard (lines 3282–3794)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `_init_check_prereqs` | 29 | RETAIN | 0 | Tight |
| `_init_detect_project` | 111 | **REFACTOR** | **~20** | npm script detection: 22-line block with 3 separate `jq` calls for `has_test`/`has_build`/`has_check` → collapsible to ~8 lines with priority-ordered single jq. PRD candidate list (10 elements) is copy-pasted verbatim in 3 places (here, `_init_scaffold_files`, `cmd_backlog_populate`). `docs/WEBSITE_BRIEF.md` is a leaked project-specific filename. |
| `_init_scaffold_files` | 275 | REFACTOR | ~15 | Beyond heredoc extraction (BUG-060): product/arch existence detected 3 times across the init flow with 3 different variable names (`prd_found`, `product_found`, `found_product`). gitignore fallback hardcodes paths already in `gitignore-entries.txt` — dead code if the file always ships. |
| `cmd_init` | 90 | RETAIN | ~5 | Re-discovers product/arch files for summary after scaffold already found them. |

**Section total: ~40 saveable lines** (beyond what BUG-060 already covers)

### Key findings:
- **PRD candidate list** appears in 3 functions with identical content. Extract to `PRD_CANDIDATES` array or `_find_prd()` function.
- **Product/arch existence** is checked 3 separate times with 3 variable names. Single-pass detection eliminates ~15 lines.
- **npm detection** is 22 lines for what is "pick the best of check/build/test" — 8 lines with a better approach.

---

## 11. Info Commands (lines 3028–3279, 5132–5180)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `cmd_metrics` | 114 | **REFACTOR** | **~12** | 6 jq computations duplicated across JSON and human branches. Both compute `avg_attempts`, `items_per_day`, `by_priority`, `by_category`, `recent_avg_*`. A shared `_compute_metrics_json()` → render pattern eliminates all duplication. **Highest value-per-line refactor in the file.** |
| `_status_output` | 82 | RETAIN | 0 | Clean rendering |
| `cmd_status` | 54 | RETAIN | 0 | Watch loop is straightforward |
| `cmd_diagnose` | 49 | TRIM | ~5 | 6 separate `jq -r` calls on the same file (lines 4979–4984) → one `jq` invocation with `@sh` or array output |

**Section total: ~17 saveable lines**

---

## 12. Update (lines 3800–4052)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `cmd_update` | 211 | REFACTOR | ~12 | `get_expected_checksum` (5 lines) and `verify_or_abort` (21 lines) are single-call-site nested helpers. Inlining removes wrapper overhead without hurting clarity. "Not modified" output misleadingly lists `backlog/*` (not in manifest). |
| `cmd_checksums` | 41 | RETAIN | 0 | Clean |

**Section total: ~12 saveable lines**

---

## 13. Context & Utilities (scattered)

| Function | Lines | Verdict | Saveable | Issue |
|---|---|---|---|---|
| `build_context` | 20 | RETAIN | 0 | |
| `find_claude_md` | 8 | RETAIN | 0 | |
| `find_project_docs` | 9 | RETAIN | 0 | |
| `recent_sprints_file` | 15 | RETAIN | 0 | |
| `get_claudemd_snippet` | 17 | (BUG-062) | — | |
| `build_completion_contract` | 9 | RETAIN | 0 | |
| `restore_stash` | 17 | RETAIN | 0 | |
| `truncate_output` | 11 | RETAIN | 0 | |
| `run_validated_command` | 9 | RETAIN | 0 | |
| `send_notification` | 9 | RETAIN | 0 | |
| `acquire_lock` | 13 | RETAIN | 0 | |
| `verify_checksum` | 15 | RETAIN | 0 | |
| `require_tool` | 7 | RETAIN | 0 | |
| `append_log` | 5 | RETAIN | 0 | |
| `ensure_tmpdir` | 4 | RETAIN | 0 | |
| `cmd_version` | 3 | RETAIN | 0 | |
| `cmd_clean` | 35 | RETAIN | 0 | Model of conciseness |

**Section total: 0 saveable lines** — Utilities are tight.

---

## Grand Summary

### By verdict

| Verdict | Functions | Lines in scope | Saveable |
|---|---|---|---|
| RETAIN | 56 | ~2,100 | 0 |
| TRIM | 7 | ~370 | ~29 |
| REFACTOR | 19 | ~2,260 | ~208 |
| **Total** | **82** | **4,730** | **~237** |

### Top refactor targets (ranked by saveable lines)

| # | Function | Saveable | Issue |
|---|---|---|---|
| 1 | `cmd_backlog_edit` | **34** | Triplicated array-append pattern; duplicated AC builder; cosmetic `update_desc` |
| 2 | `_init_detect_project` | **20** | npm detection bloat; triplicated PRD candidate list |
| 3 | `cmd_backlog_add` | **16** | Duplicated AC builder; array-build boilerplate |
| 4 | `_handle_sprint_success` | **15** | Duplicated remote sync block; collapsible merge_msg |
| 5 | `_init_scaffold_files` | **15** | Triple product/arch detection; dead gitignore fallback |
| 6 | `cmd_run` sprint loop | **13** | Verbose bash idioms with 1-line alternatives |
| 7 | `cmd_metrics` | **12** | 6 jq computations duplicated across JSON/human branches |
| 8 | `cmd_groom` | **12** | Pipeline boilerplate shared with populate (BUG-069) |
| 9 | `cmd_update` | **12** | Single-call-site nested helpers; misleading output |
| 10 | `check_readiness_gates` | **10** | Advisory hints belong in caller, not gate function |

### Cross-cutting patterns (affect multiple functions)

| Pattern | Occurrences | Lines wasted | Fix |
|---|---|---|---|
| **AC JSON manual string-cat builder** | 2 (add, edit) | ~20 | Extract `_build_ac_json` helper |
| **Array-append boilerplate** (scope/steps/deps) | 3 in edit | ~18 | Extract `_append_array_field` helper |
| **PRD candidate list** copy-paste | 3 (detect, scaffold, populate) | ~20 | Extract `_find_prd` or `PRD_CANDIDATES` array |
| **Product/arch existence detection** | 3 passes in init flow | ~15 | Single-pass with exported path |
| **Remote sync (push+pull)** | 2 (squash, no-ff merge) | ~7 | Extract `_sync_remote` |
| **Per-item dual jq calls** | 3 (enforce_limits, create_sprint, mark_complete) | ~15 | Combine into single jq per item |
| **Redundant `return 0`** | ~5 functions | ~5 | Delete |

### What's actually good

These sections are **production quality and should not be touched**:

- **All backlog helpers** (74 lines) — tight, single-purpose, correct
- **All utilities** (~80 lines) — `restore_stash`, `truncate_output`, `acquire_lock`, etc.
- **Agent execution** (305 lines) — the most well-written section; `run_agent_process` is complex but earns every line
- **`cmd_backlog_show`** (32 lines) — one jq call does everything, exemplary
- **`cmd_clean`** (35 lines) — model of conciseness
- **`cmd_backlog_rm`** (33 lines) — clean
- **Config loading** (76 lines) — already data-driven

### Realistic savings from this analysis

| Category | Lines | Status |
|---|---|---|
| Already filed (BUG-060–072) | ~1,191 | Backlogged |
| New refactors from this analysis | ~237 | Candidates below |
| **Combined potential** | **~1,428** | → script from 5,328 to **~3,900** |

### New candidates for backlog items

These are distinct from BUG-060–072 and worth filing:

1. **Extract shared `_build_ac_json` helper** — eliminates 20 lines of duplication across `add` and `edit` (~20 lines)
2. **Extract `_append_array_field` helper for edit** — collapses 3 identical scope/steps/deps blocks (~18 lines)
3. **Extract `_find_prd` / `PRD_CANDIDATES`** — eliminates 3 copy-pasted candidate lists across init and populate (~20 lines)
4. **Unify product/arch detection in init** — single pass replaces 3 variable-name variants (~15 lines)
5. **`cmd_metrics` compute-once-render-twice** — highest value-per-line refactor (~12 lines)
6. **`create_sprint` pass item as --argjson** — fewer forks, fewer lines (~8 lines)
7. **Collapse npm detection in init** — 22 lines → 8 lines (~14 lines)
8. **Extract `_sync_remote` from merge paths** — already partially covered by BUG-070 but the specific duplication is worth noting (~7 lines)
9. **Inline `cmd_update` single-use nested helpers** — `get_expected_checksum` + `verify_or_abort` (~12 lines)
10. **Remove `update_desc` tracking from edit** — 14 cosmetic lines for marginal UX (~14 lines)
