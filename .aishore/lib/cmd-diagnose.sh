#!/usr/bin/env bash
# Module: cmd-diagnose — show last sprint failure diagnostics
# Lazy-loaded by _load_module; all globals (STATUS_DIR, colors, jq) come from the main script.

cmd_diagnose() {
    local failure_file="$STATUS_DIR/last-failure.json"
    if [[ ! -f "$failure_file" ]]; then
        log_info "No failure context found — no recent sprint failures recorded"
        return 0
    fi

    local item_id reason detail timestamp agent_log log_tail
    {
        IFS= read -r -d '' item_id
        IFS= read -r -d '' reason
        IFS= read -r -d '' detail
        IFS= read -r -d '' timestamp
        IFS= read -r -d '' agent_log
        IFS= read -r -d '' log_tail || true
    } < <(jq -j '(.itemId // "unknown"), "\u0000",
                  (.reason // "unknown"), "\u0000",
                  (.detail // "unknown"), "\u0000",
                  (.timestamp // "unknown"), "\u0000",
                  (.agentLog // ""), "\u0000",
                  (.logTail // ""), "\u0000"' "$failure_file")

    echo -e "${RED}═══ Sprint Failure Diagnostics ═══${NC}"
    echo ""
    echo -e "${CYAN}Item:${NC}      $item_id"
    echo -e "${CYAN}Reason:${NC}    $reason"
    echo -e "${CYAN}Detail:${NC}    $detail"
    echo -e "${CYAN}Timestamp:${NC} $timestamp"
    echo ""

    # Show result.json content
    echo -e "${YELLOW}── Agent Result ──${NC}"
    jq -r '.result' "$failure_file" 2>/dev/null | jq . 2>/dev/null || echo "(no result data)"
    echo ""

    # Show stored log tail (50 lines from failure context)
    echo -e "${YELLOW}── Agent Log Tail (last 50 lines at failure time) ──${NC}"
    if [[ -n "$log_tail" ]]; then
        printf '%s\n' "$log_tail"
    else
        echo "(no log output captured)"
    fi
    echo ""

    # If full log file still exists, offer path
    if [[ -n "$agent_log" && -f "$agent_log" ]]; then
        local total_lines
        total_lines=$(wc -l < "$agent_log" 2>/dev/null || echo 0)
        echo -e "${CYAN}Full agent log:${NC} $agent_log ($total_lines lines)"
    elif [[ -n "$agent_log" ]]; then
        echo -e "${YELLOW}Agent log file no longer exists:${NC} $agent_log"
    fi

    echo ""
    echo -e "${RED}═══ End Diagnostics ═══${NC}"
}
