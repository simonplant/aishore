#!/usr/bin/env bash
# check-drift.sh — Detect drift between code, help output, and docs
#
# Checks:
#   1. Syntax & integrity (bash -n, jq, checksums)
#   2. Version consistency (VERSION file, CLI, help, README badge)
#   3. Command routing (main() case vs help)
#   4. Environment variables (_apply_env_overrides vs README)
#   5. Flag parity — code vs help (per-command case-statement flags)
#   6. Flag parity — help vs README (all documented flags)
#   7. Command parity — help vs CLAUDE.md
#
# Usage: bash tests/check-drift.sh
#        bash tests/check-drift.sh --ci   (exit 1 on drift)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$SCRIPT_DIR/.aishore/aishore"
README="$SCRIPT_DIR/README.md"
CLAUDE_MD="$SCRIPT_DIR/CLAUDE.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

ci_mode=false
[[ "${1:-}" == "--ci" ]] && ci_mode=true

drift_count=0

drift() {
    local severity="$1" msg="$2"
    if [[ "$severity" == "error" ]]; then
        echo -e "${RED}DRIFT${RESET}  $msg"
        ((drift_count++))
    else
        echo -e "${YELLOW}NOTE${RESET}  $msg"
    fi
}

ok() {
    echo -e "${GREEN}OK${RESET}    $1"
}

# Grep wrapper that handles -- flags safely (uses -F for fixed strings)
has_line() {
    local needle="$1"
    shift
    echo "$@" | grep -Fxq -- "$needle"
}

echo "═══════════════════════════════════════"
echo "  aishore Drift Report"
echo "═══════════════════════════════════════"
echo ""

# ─── 1. Syntax & basics ─────────────────────────────────────────────────────

echo "── Syntax & Integrity ──"

if bash -n "$CLI" 2>/dev/null; then
    ok "CLI syntax valid"
else
    drift error "CLI has syntax errors"
fi

if jq empty "$SCRIPT_DIR"/backlog/*.json 2>/dev/null; then
    ok "Backlog JSON valid"
else
    drift error "Backlog JSON has parse errors"
fi

if sha256sum -c "$SCRIPT_DIR/.aishore/checksums.sha256" >/dev/null 2>&1; then
    ok "Checksums match"
else
    drift error "Checksums out of date — run: .aishore/aishore checksums"
fi

echo ""

# ─── 2. Version consistency ──────────────────────────────────────────────────

echo "── Version ──"

file_version=$(cat "$SCRIPT_DIR/.aishore/VERSION")
cli_version=$("$CLI" version 2>&1 | grep -oP 'version \K[\d.]+')
help_version=$("$CLI" help 2>&1 | grep -oP '\(v\K[\d.]+')

if [[ "$file_version" == "$cli_version" && "$cli_version" == "$help_version" ]]; then
    ok "VERSION=$file_version matches CLI and help"
else
    drift error "Version mismatch: file=$file_version cli=$cli_version help=$help_version"
fi

echo ""

# ─── 3. Command routing ─────────────────────────────────────────────────────

echo "── Commands ──"

# Extract commands from main() case statement (exclude aliases like -v, -h, *)
code_commands=$(sed -n '/^main()/,/^}/p' "$CLI" \
    | grep -oP '[\w]+(?=\))' \
    | grep -v '^esac$' \
    | sort -u)

# Extract commands from help output (2-space indented words)
help_commands=$("$CLI" help 2>&1 \
    | grep -oP '^\s{2}(\w[\w-]+)' \
    | awk '{print $1}' \
    | grep -v '^--' \
    | sort -u)

for cmd in $code_commands; do
    [[ "$cmd" == "usage" ]] && continue  # internal default
    if has_line "$cmd" "$help_commands"; then
        ok "Command '$cmd' in code and help"
    else
        drift error "Command '$cmd' in code but missing from help"
    fi
done

echo ""

# ─── 4. Environment variables ───────────────────────────────────────────────

echo "── Environment Variables ──"

# Extract user-facing env vars from _apply_env_overrides only
code_envvars=$(sed -n '/_apply_env_overrides()/,/^}/p' "$CLI" \
    | grep -oP 'AISHORE_\w+' \
    | sort -u)

for var in $code_envvars; do
    if grep -Fq "$var" "$README" 2>/dev/null; then
        ok "Env var $var documented in README"
    else
        drift error "Env var $var in code but missing from README"
    fi
done

echo ""

# ─── 5. Flag parsing vs help — per command ───────────────────────────────────

echo "── Flags: Code vs Help ──"

# Extract flags from arg parsing within a function.
# Catches both case-statement patterns (--flag) or --flag|) and == comparisons.
extract_code_flags() {
    local func_name="$1"
    local body
    body=$(sed -n "/^${func_name}()/,/^[a-z_]*() *{*$/p" "$CLI")
    {
        # Case-statement patterns: --flag) or --flag| or -x|--flag)
        echo "$body" | grep -oP '(?<=[\s|])--[\w-]+(?=\)|\|)'
        # Equality checks: == "--flag" or == '--flag'
        echo "$body" | grep -oP '==\s*["\x27]--[\w-]+["\x27]' | grep -oP '\-\-[\w-]+'
    } | grep -v '^--_' | sort -u
}

# Extract flags from help for a specific command section.
# Uses awk to capture from the command line to the next command or blank line.
extract_help_flags() {
    local cmd_label="$1"
    local help_text
    help_text=$("$CLI" help 2>&1)

    # For commands like "run", "auto", "review" etc., the help section starts
    # with "  command" and ends at the next "  command" or empty line.
    # Include the command line itself (for inline flags like "update ... --dry-run").
    echo "$help_text" \
        | awk -v cmd="$cmd_label" '
            BEGIN { found=0 }
            # Match the start: 2-space indent + command name
            $0 ~ "^  " cmd "([ ,[]|$)" { found=1; print; next }
            # Stop at next command (2-space indent + letter) or empty line
            found && /^  [a-z]/ { found=0 }
            found && /^$/ { found=0 }
            found { print }
        ' \
        | grep -oP '\-\-[\w-]+' \
        | sort -u
}

# Intentionally undocumented flags (escape hatches, aliases)
is_intentionally_undocumented() {
    local cmd="$1" flag="$2"
    case "$cmd:$flag" in
        update:--check|update:--no-verify) return 0 ;;
        run:--max-failures) return 0 ;;  # only meaningful via auto pass-through
        *) return 1 ;;
    esac
}

check_command_flags() {
    local func_name="$1" cmd_label="$2"

    local code_flags help_flags
    code_flags=$(extract_code_flags "$func_name") || true
    help_flags=$(extract_help_flags "$cmd_label") || true

    [[ -z "$code_flags" && -z "$help_flags" ]] && return

    local flag
    while IFS= read -r flag; do
        [[ -z "$flag" ]] && continue
        if has_line "$flag" "$help_flags"; then
            ok "$cmd_label $flag in code and help"
        elif is_intentionally_undocumented "$cmd_label" "$flag"; then
            drift note "$cmd_label $flag in code, intentionally undocumented"
        else
            drift error "$cmd_label $flag parsed in code but missing from help"
        fi
    done <<< "$code_flags"

    while IFS= read -r flag; do
        [[ -z "$flag" ]] && continue
        if ! has_line "$flag" "$code_flags"; then
            # Auto flags are parsed in cmd_run (pass-through via --_auto)
            if [[ "$cmd_label" == "auto" ]]; then
                local run_flags
                run_flags=$(extract_code_flags "cmd_run") || true
                if has_line "$flag" "$run_flags"; then
                    ok "$cmd_label $flag parsed via run pass-through"
                    continue
                fi
            fi
            drift error "$cmd_label $flag in help but not parsed in code"
        fi
    done <<< "$help_flags"
}

check_command_flags "cmd_run" "run"
check_command_flags "cmd_auto" "auto"
check_command_flags "cmd_update" "update"
check_command_flags "cmd_init" "init"
check_command_flags "cmd_backlog_add" "backlog add"
check_command_flags "cmd_backlog_edit" "backlog edit"
check_command_flags "cmd_backlog_list" "backlog list"
check_command_flags "cmd_review" "review"
check_command_flags "cmd_groom" "groom"
check_command_flags "cmd_clean" "clean"

echo ""

# ─── 6. Help vs README flag parity ──────────────────────────────────────────

echo "── Flags: Help vs README ──"

all_help_flags=$("$CLI" help 2>&1 | grep -oP '\-\-[\w-]+' | sort -u)

while IFS= read -r flag; do
    [[ -z "$flag" ]] && continue
    if grep -Fq -- "$flag" "$README" 2>/dev/null; then
        ok "Help flag $flag in README"
    else
        case "$flag" in
            --help|--version) ok "Help flag $flag (standard, README skip OK)" ;;
            *) drift error "Help flag $flag missing from README" ;;
        esac
    fi
done <<< "$all_help_flags"

echo ""

# ─── 7. Help vs CLAUDE.md command parity ─────────────────────────────────────

echo "── Commands: Help vs CLAUDE.md ──"

help_primary_cmds=$("$CLI" help 2>&1 \
    | grep -oP '^\s{2}(\w[\w-]+)' \
    | awk '{print $1}' \
    | grep -v '^--' \
    | sort -u)

for cmd in $help_primary_cmds; do
    if grep -Fq "$cmd" "$CLAUDE_MD" 2>/dev/null; then
        ok "Command '$cmd' in CLAUDE.md"
    else
        drift error "Command '$cmd' in help but missing from CLAUDE.md"
    fi
done

echo ""

# ─── 8. Getting-started guide (.aishore/README.md) ──────────────────────────

GUIDE="$SCRIPT_DIR/.aishore/README.md"

if [[ -f "$GUIDE" ]]; then
    echo "── Getting-Started Guide (.aishore/README.md) ──"

    # Check that primary commands from help appear in the guide
    # (guide is a quick-reference, so we check major commands only)
    major_cmds="auto run groom review status metrics clean update"
    for cmd in $major_cmds; do
        if grep -Fq "$cmd" "$GUIDE" 2>/dev/null; then
            ok "Guide mentions '$cmd'"
        else
            drift error "Guide missing command '$cmd'"
        fi
    done

    # Check that flags mentioned in the guide actually exist in help
    guide_flags=$(grep -oP '\-\-[\w-]+' "$GUIDE" | sort -u)
    while IFS= read -r flag; do
        [[ -z "$flag" ]] && continue
        if grep -Fq -- "$flag" <<< "$all_help_flags" 2>/dev/null; then
            ok "Guide flag $flag exists in help"
        else
            # Check if it's a valid code flag not in help (like --force for update)
            if grep -Fq -- "$flag" "$CLI" 2>/dev/null; then
                ok "Guide flag $flag exists in code"
            else
                drift error "Guide mentions $flag but it doesn't exist in code or help"
            fi
        fi
    done <<< "$guide_flags"

    # Check env vars mentioned in guide exist in code
    guide_envvars=$(grep -oP 'AISHORE_\w+' "$GUIDE" | sort -u)
    for var in $guide_envvars; do
        if grep -Fq "$var" "$CLI" 2>/dev/null; then
            ok "Guide env var $var exists in code"
        else
            drift error "Guide mentions $var but it doesn't exist in code"
        fi
    done

    # Check config keys mentioned in guide exist in code's config parser
    # Match config keys like "models.primary", "scope.mode" — exclude URLs, filenames, etc.
    guide_config_keys=$(grep -oP '(?<![/\w])[\w]+\.[\w]+(?![\w./])' "$GUIDE" \
        | grep -v '\.\(sh\|md\|json\|yaml\|yml\|jsonl\|lock\|txt\)$' \
        | grep -v 'github\.\|githubusercontent\.\|aishore\.' \
        | sort -u)
    while IFS= read -r key; do
        [[ -z "$key" ]] && continue
        if grep -Fq "$key" "$CLI" 2>/dev/null; then
            ok "Guide config key $key exists in code"
        else
            drift error "Guide mentions config key $key but it doesn't exist in code"
        fi
    done <<< "$guide_config_keys"

    echo ""
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════"
if [[ "$drift_count" -eq 0 ]]; then
    echo -e "${GREEN}No drift detected${RESET}"
else
    echo -e "${RED}$drift_count drift issue(s) found${RESET}"
fi
echo "═══════════════════════════════════════"

if $ci_mode && [[ "$drift_count" -gt 0 ]]; then
    exit 1
fi
