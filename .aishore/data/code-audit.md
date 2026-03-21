# aishore CLI Code Audit — `.aishore/aishore`

**Date:** 2026-03-20
**Total lines:** 5,328 (up from 727 original — 7.3x growth)
**Total functions:** 82
**Function lines:** 4,730 (89%)
**Non-function overhead:** 598 lines (globals, constants, section headers, main dispatch)

---

## Function Map (sorted by size within each section)

### Core Sprint Engine — 1,238 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `cmd_run` | 2156–2633 | **478** | Main sprint loop — arg parsing, stash/worktree, item picking, retry orchestration, auto-mode, post-review |
| `_run_retry_loop` | 1858–2019 | **162** | Developer → fix_cmd → scope check → validate_cmd → AC verify → validator agent retry loop |
| `_handle_sprint_success` | 2026–2154 | **129** | Post-sprint: mark complete, safety commit, merge/squash/no-merge, push, PR creation |
| `refine_item_spec` | 1743–1856 | **114** | `--refine` feature: calls Claude to rewrite steps/AC after failure |
| `print_batch_summary` | 1590–1651 | **62** | Pretty-print pass/fail/skip table after multi-sprint run |
| `_run_dry_run` | 1681–1741 | **61** | Dry-run preview: picks item, prints prompt, shows config |
| `handle_sprint_failure` | 1553–1584 | **32** | Cleanup on failure: delete branch, restore backlog snapshot |
| `cmd_auto` | 1653–1677 | **25** | Thin wrapper: validates scope arg, delegates to `cmd_run --_auto` |
| `cleanup_exit` | 30–52 | **23** | Trap handler: clean worktree/branch, restore stash |
| `_store_failure_context` | 1530–1551 | **22** | Save diagnostic JSON for `diagnose` command |
| `mark_item_failed` | 1496–1512 | **17** | Record failure reason + timestamp on item |
| `_cleanup_worktree` | 1514–1528 | **15** | Remove git worktree and restore paths |
| `save_backlog_snapshot` | 1481–1487 | **7** | Copy backlog files for rollback |
| `restore_backlog_snapshot` | 1489–1494 | **6** | Restore backlog files from snapshot |

### Agent Execution — 305 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `build_agent_prompt` | 1124–1259 | **136** | Assemble prompt: agent .md + maturity protocol + intent injection + populate mode docs |
| `run_agent_process` | 1010–1122 | **113** | Launch claude subprocess, poll for result.json, timeout/kill, logging |
| `run_agent` | 1261–1315 | **55** | Orchestrate: clear result, build context, resolve permissions, call `run_agent_process` |

### Validation & Checks — 174 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `check_readiness_gates` | 568–665 | **98** | Validate: title, intent (>=20 chars), steps, AC, short steps, deps, complexity heuristic |
| `check_scope_violations` | 1366–1425 | **60** | Diff changed files against declared scope globs |
| `run_ac_verification` | 1428–1475 | **48** | Run AC `verify` commands and report pass/fail |
| `check_result` | 1331–1363 | **33** | Parse result.json for pass/fail |
| `show_failure_log_tail` | 1317–1329 | **13** | Print last 20 lines of agent log on failure |

### Item Selection — 178 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `pick_item` | 424–522 | **99** | Select item: by ID with intent/dep validation, or auto-pick by priority |
| `list_pickable_ids` | 725–751 | **27** | List all auto-pickable IDs (used by `cmd_run` to pre-build queue) |
| `collect_done_ids` | 753–762 | **10** | Scan backlogs + archive for done item IDs |

### Backlog CRUD — 815 lines (BIGGEST SECTION)

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `cmd_backlog_add` | 4242–4502 | **261** | Add item — interactive mode (100+ lines of prompts) + CLI flags |
| `cmd_backlog_edit` | 4537–4748 | **212** | Edit item — 25+ flags parsed, AC/step/scope/depends accumulation |
| `cmd_backlog_sync` | 4843–4994 | **152** | Detect manually completed items by scope vs git history |
| `cmd_backlog_history` | 4758–4841 | **84** | List archive with --since/--failed/--limit, title lookup map |
| `cmd_backlog_populate` | 4097–4179 | **83** | Find PRODUCT.md, run product-owner agent, enforce groom limits |
| `cmd_backlog_list` | 4181–4240 | **60** | List items with filters, blocked column, priority sort |
| `cmd_backlog_show` | 4504–4535 | **32** | Pretty-print one item |
| `cmd_backlog_rm` | 4996–5048 | **33** | Remove item with confirmation |
| `cmd_backlog` (router) | 4058–4078 | **21** | Subcommand dispatch |
| `cmd_backlog_check` | 4080–4095 | **16** | Thin wrapper around `check_readiness_gates` |

### Backlog Helpers — 74 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `resolve_backlog_file` | 533–553 | **21** | Find which .json file contains an ID |
| `next_id` | 667–685 | **19** | Generate next FEAT-NNN / BUG-NNN |
| `update_item` | 764–778 | **15** | Update item via jq expression |
| `add_item` | 780–791 | **12** | Append item to backlog |
| `find_item` | 555–565 | **11** | Get full item JSON by ID |
| `remove_item` | 793–802 | **10** | Remove item by ID |
| `remove_items_by_status` | 804–813 | **10** | Remove all items with given status |
| `validate_priority` | 687–693 | **7** | Validate priority value |
| `validate_status` | 695–701 | **7** | Validate status value |
| `validate_arg` | 4750–4756 | **7** | Check flag has a value |
| `count_items` | 703–706 | **4** | Count items in file |
| `count_by_status` | 708–711 | **4** | Count items by status |
| `count_ready_items` | 713–716 | **4** | Count sprint-ready items |
| `list_ready_items` | 718–721 | **4** | List sprint-ready items |
| `get_item_source` | 524–527 | **4** | Read .item_source file |

### Grooming — 244 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `enforce_groom_limits` | 2850–2925 | **76** | Cap new items by count and min priority |
| `protect_items_from_groom` | 2761–2833 | **73** | Restore pre-existing items that groomer overwrote |
| `cmd_groom` | 2635–2695 | **61** | Run tech-lead or product-owner agent with snapshot/protection |
| `print_groom_summary` | 2698–2755 | **58** | Pre-groom backlog status display |
| `print_groom_diff` | 2928–2964 | **37** | Post-groom before/after comparison |
| `_check_groom_progress` | 975–1008 | **34** | Monitor backlog file changes during groom agent poll |
| `snapshot_backlogs` | 2836–2843 | **8** | Capture item counts for diffing |

### Init Wizard — 493 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `_init_scaffold_files` | 3429–3703 | **275** | Create dirs, config.yaml, backlogs, DEFINITIONS.md template, PRODUCT.md template, ARCHITECTURE.md template, .gitignore, CLAUDE.md |
| `_init_detect_project` | 3314–3424 | **111** | Detect project name, validation cmd, product docs |
| `cmd_init` | 3705–3794 | **90** | Main init flow: prereqs → detect → scaffold → summary |
| `_init_check_prereqs` | 3282–3310 | **29** | Check git, claude, jq |

### Info Commands — 262 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `cmd_metrics` | 3028–3141 | **114** | Sprint metrics: counts, trends, by-priority, by-category, JSON + human modes |
| `_status_output` | 3143–3224 | **82** | Render backlog status, ready items, current sprint, recent history |
| `cmd_status` | 3226–3279 | **54** | Status display + --watch loop |
| `cmd_diagnose` | 5132–5180 | **49** | Show last failure diagnostics |

### Update — 252 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `cmd_update` | 3800–4010 | **211** | Fetch release tag, download files, verify checksums, stage + install |
| `cmd_checksums` | 4012–4052 | **41** | Regenerate checksums.sha256 |

### Help Text — 155 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `cmd_help` | 5182–5291 | **110** | Full help text with all flags and examples |
| `cmd_usage` | 5086–5130 | **45** | Short usage text (subset of cmd_help) |

### Sprint State — 127 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `mark_complete` | 864–941 | **78** | Mark item done, update sprint.json, append archive with git stats/duration/priority |
| `create_sprint` | 819–862 | **44** | Create sprint.json from item |
| `reset_sprint` | 943–947 | **5** | Reset sprint.json to idle |

### Config — 76 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `load_config` | 328–375 | **48** | Read config.yaml via yq (or grep fallback) |
| `_apply_env_overrides` | 377–404 | **28** | Env vars override config |

### Context Assembly — 70 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `build_context` | 191–210 | **20** | Build @file context list for agent role |
| `get_claudemd_snippet` | 306–322 | **17** | CLAUDE.md aishore section template |
| `recent_sprints_file` | 290–304 | **15** | Tail archive for agent context |
| `find_claude_md` | 270–277 | **8** | Find CLAUDE.md in project |
| `find_project_docs` | 279–287 | **9** | Find ARCHITECTURE.md, PRODUCT.md |

### Misc Utilities — ~80 lines

| Function | Lines | Size | Purpose |
|---|---|---|---|
| `restore_stash` | 169–185 | **17** | Pop git stash with conflict handling |
| `truncate_output` | 144–154 | **11** | Truncate file to last N lines |
| `run_validated_command` | 159–167 | **9** | Run command with optional timeout |
| `_file_hash` | 964–972 | **9** | Portable file hash (sha256sum/shasum/cksum) |
| `build_completion_contract` | 212–220 | **9** | Agent completion contract heredoc |
| `send_notification` | 410–418 | **9** | Run notification command |
| `acquire_lock` | 222–234 | **13** | flock-based concurrency guard |
| `verify_checksum` | 242–256 | **15** | Verify SHA-256 checksum |
| `require_tool` | 258–264 | **7** | Check tool is installed |
| `append_log` | 236–240 | **5** | Append line to log file |
| `ensure_tmpdir` | 55–58 | **4** | Create/return temp directory |
| `cmd_version` | 3816–3818 | **3** | Print version |

---

## Top 10 Largest Functions (2,439 lines — 46% of file)

| # | Function | Lines | Notes |
|---|---|---|---|
| 1 | `cmd_run` | **478** | God function: arg parse + stash + worktree + auto-mode + groom trigger + circuit breaker + review prompt |
| 2 | `_init_scaffold_files` | **275** | 150+ lines of heredoc templates (DEFINITIONS.md, PRODUCT.md, ARCHITECTURE.md, config.yaml) |
| 3 | `cmd_backlog_add` | **261** | Interactive mode alone is ~100 lines of echo/read prompts |
| 4 | `cmd_backlog_edit` | **212** | 25+ flag cases, each with accumulation logic |
| 5 | `cmd_update` | **211** | File-by-file fetch/verify/stage/install |
| 6 | `_run_retry_loop` | **162** | Retry orchestration with 5 different failure paths |
| 7 | `cmd_backlog_sync` | **152** | Scope-matching against git history — entire feature is niche |
| 8 | `build_agent_prompt` | **136** | Prompt assembly with 80+ lines of embedded populate-mode documentation |
| 9 | `_handle_sprint_success` | **129** | Three merge strategies (merge, squash, no-merge) + PR creation, all inlined |
| 10 | `cmd_metrics` | **114** | Two complete output paths (JSON and human-readable) |

---

## Root Causes of 7x Growth

### 1. Embedded documentation as code (~400 lines)
- `_init_scaffold_files`: full templates for DEFINITIONS.md (80 lines), PRODUCT.md, ARCHITECTURE.md, config.yaml heredocs
- `build_agent_prompt`: 80 lines of populate-mode documentation inlined in bash
- `cmd_help`: 110 lines of help text
- **Fix:** Move templates to `.aishore/templates/` files. Move populate docs to agent prompt file.

### 2. Interactive CLI mode (~200 lines)
- `cmd_backlog_add` interactive prompts, confirmations, examples
- A CLI tool used primarily by AI agents has a full interactive TUI
- **Fix:** Remove interactive mode — agents use flags, humans can too.

### 3. Feature sprawl (~600 lines)
- `backlog sync` (152) — niche scope-matching feature
- `backlog populate` (83) — product-owner agent wrapper
- `backlog history` with filters (84) — full query engine
- `print_groom_summary` (58) + `print_groom_diff` (37) — presentation
- `enforce_groom_limits` (76) + `protect_items_from_groom` (73) — defensive grooming
- **Fix:** Evaluate which features justify their weight. `backlog sync` is 152 lines for a rarely-used feature.

### 4. `cmd_run` is a god function (478 lines)
- Handles auto-mode, stash/worktree, grooming, circuit breaker, review — all inlined
- Contains nested function definitions (`_count_total_ready`, `_record_sprint_failure`)
- **Fix:** Extract auto-mode setup, worktree/stash management, and post-run review into separate functions.

### 5. Duplicated help text (155 lines)
- `cmd_usage` (45 lines) and `cmd_help` (110 lines) are overlapping — `cmd_usage` is a subset
- **Fix:** Single help function, possibly with `--verbose` flag.

### 6. Three merge strategies inlined (~80 lines)
- `_handle_sprint_success` has three separate code paths (merge, squash, no-merge)
- **Fix:** Parameterize merge operation.

### 7. Verbose defensive coding (~200 lines)
- Every jq call has `2>/dev/null || true`
- Every file operation has existence checks
- Every error has a suggestion message with full command examples
- Good individually, adds up across 82 functions

---

## Section Size Summary

| Section | Lines | % of total |
|---|---|---|
| Core Sprint Engine | 1,238 | 23% |
| Backlog CRUD | 815 | 15% |
| Non-function overhead | 598 | 11% |
| Init Wizard | 493 | 9% |
| Agent Execution | 305 | 6% |
| Info Commands | 262 | 5% |
| Update | 252 | 5% |
| Grooming | 244 | 5% |
| Item Selection | 178 | 3% |
| Validation & Checks | 174 | 3% |
| Help Text | 155 | 3% |
| Sprint State | 127 | 2% |
| Context Assembly | 70 | 1% |
| Config | 76 | 1% |
| Backlog Helpers | 74 | 1% |
| Misc Utilities | 80 | 2% |

---

## Estimated Reducible Lines

| Category | Lines | Approach |
|---|---|---|
| Heredoc templates → external files | ~250 | Move to `.aishore/templates/` |
| Interactive mode removal | ~150 | Agents use flags; humans can too |
| Duplicate help text | ~45 | Single help function |
| Populate docs → agent prompt file | ~80 | Move to `product-owner.md` |
| `backlog sync` removal or simplification | ~100 | Evaluate if feature is used |
| `cmd_run` decomposition | ~0 (moves lines) | Readability, not size reduction |
| **Total reducible** | **~625** | **Would bring file to ~4,700** |

To get back toward ~2,500 lines (a reasonable ceiling for a single bash file), deeper structural changes would be needed: splitting into multiple files, removing niche features, or extracting the backlog CLI into a separate script.
