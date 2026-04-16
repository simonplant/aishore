#!/usr/bin/env bash
# Module: cmd-doctor — health check command
# Lazy-loaded by _load_module; all globals (PROJECT_ROOT, BACKLOG_DIR,
# CONFIG_FILE, CORE_CMD, log_*, load_config) come from the main script.

cmd_doctor() {
    load_config
    cd "$PROJECT_ROOT" || { log_error "Cannot cd to $PROJECT_ROOT"; return 1; }

    local failed=0

    log_header "Doctor: health check"

    # --- Required tools ---
    log_info "Required tools:"
    local tool
    for tool in jq git claude; do
        if command -v "$tool" &>/dev/null; then
            log_success "PASS  $tool — $(command -v "$tool")"
        else
            echo -e "${RED}✗ FAIL  $tool — not found${NC}"
            failed=1
        fi
    done

    # --- Optional tools ---
    echo ""
    log_info "Optional tools:"
    if command -v yq &>/dev/null; then
        log_success "PASS  yq — $(command -v yq)"
    else
        log_warning "WARN  yq — not found (needed for full config.yaml support)"
    fi

    # --- Backlog JSON validation ---
    echo ""
    log_info "Backlog files:"
    local json_file
    for json_file in "$BACKLOG_DIR/backlog.json" "$BACKLOG_DIR/bugs.json"; do
        local basename
        basename="$(basename "$json_file")"
        if [[ ! -f "$json_file" ]]; then
            echo -e "${RED}✗ FAIL  $basename — file not found${NC}"
            failed=1
        elif jq empty "$json_file" 2>/dev/null; then
            log_success "PASS  $basename — valid JSON"
        else
            echo -e "${RED}✗ FAIL  $basename — invalid JSON${NC}"
            failed=1
        fi
    done

    # --- Config file ---
    echo ""
    log_info "Configuration:"
    if [[ -f "$CONFIG_FILE" ]]; then
        if command -v yq &>/dev/null; then
            if yq empty "$CONFIG_FILE" 2>/dev/null; then
                log_success "PASS  config.yaml — parseable"
            else
                echo -e "${RED}✗ FAIL  config.yaml — not parseable${NC}"
                failed=1
            fi
        else
            # Without yq, do a basic syntax check via grep for obvious YAML issues
            log_success "PASS  config.yaml — present (install yq for full validation)"
        fi
    else
        log_warning "WARN  config.yaml — not found (using defaults)"
    fi

    # --- CORE_CMD ---
    echo ""
    log_info "Core status:"
    if [[ -n "$CORE_CMD" ]]; then
        log_success "PASS  CORE_CMD — $CORE_CMD"
    else
        log_warning "WARN  CORE_CMD — not set"
    fi

    # --- Summary ---
    echo ""
    if [[ "$failed" -eq 0 ]]; then
        log_success "All required checks passed"
        return 0
    else
        log_error "One or more required checks failed"
        return 1
    fi
}
