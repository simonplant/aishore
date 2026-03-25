#!/usr/bin/env bash
# Module: cmd-groom — groom command entry point
# Lazy-loaded by _load_module; all globals (BACKLOG_DIR, BACKLOG_FILES, ARCHIVE_DIR,
# PROJECT_ROOT, jq, count_items, count_ready_items, log_*, parse_opts, acquire_lock,
# load_config, _build_groom_context, run_groom_flow) come from the main script.
# Groom helpers (_build_groom_context, run_groom_flow, protect_items_from_groom, etc.)
# remain in core because the sprint loop calls them directly.

cmd_groom() {
    require_tool jq

    local mode="bugs" _backlog=false _architect=false
    parse_opts "bool:_backlog:--backlog" "bool:_architect:--architect" -- "$@" || return 1
    [[ "$_backlog" == "true" ]] && mode="backlog"
    [[ "$_architect" == "true" ]] && mode="architect"

    acquire_lock
    load_config
    cd "$PROJECT_ROOT"

    local agent
    if [[ "$mode" == "architect" ]]; then
        log_header "Architect: Scaffolding Review"
        agent="architect"
    elif [[ "$mode" == "backlog" ]]; then
        log_header "Product Owner: Backlog Grooming"
        agent="product-owner"
    else
        log_header "Tech Lead: Bugs/Tech Debt Grooming"
        agent="tech-lead"
    fi

    print_groom_summary

    local -a context_args
    mapfile -t context_args < <(_build_groom_context)

    run_groom_flow "$agent" "groom" context_args
}

print_groom_summary() {
    local backlog_file="$BACKLOG_DIR/backlog.json"
    local bugs_file="$BACKLOG_DIR/bugs.json"
    local total_f=0 total_b=0 ready_f=0 ready_b=0
    [[ -f "$backlog_file" ]] && { total_f=$(count_items "$backlog_file"); ready_f=$(count_ready_items "$backlog_file"); }
    [[ -f "$bugs_file" ]] && { total_b=$(count_items "$bugs_file"); ready_b=$(count_ready_items "$bugs_file"); }
    log_info "Items: $((total_f + total_b)) ($total_f features, $total_b bugs)  |  Ready: $((ready_f + ready_b)) ($ready_f features, $ready_b bugs)"
}
