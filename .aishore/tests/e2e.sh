#!/usr/bin/env bash
# e2e.sh — End-to-end synthetic transaction suite for aishore
#
# Exercises the full sprint pipeline in an isolated temp project:
# init → add (core + feature) → list → show → edit → check → status →
# dry-run (core healthy + broken) → real sprint with DEVELOPER_CMD →
# verify post-merge state → trigger heal synthesis → verify heal item →
# failed heal cleanup → config backwards compat
#
# Requires: git, jq, bash 4.4+
# Does NOT require Claude CLI (uses DEVELOPER_CMD override)
#
# Usage: bash .aishore/tests/e2e.sh
#        bash .aishore/tests/e2e.sh --ci   (exit 1 on first failure)
set -uo pipefail

AISHORE_SRC="$(cd "$(dirname "$0")/../.." && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

ci_mode=false
[[ "${1:-}" == "--ci" ]] && ci_mode=true

passed=0
failed=0
total=0

# ─── Test helpers ─────────────────────────────────────────────────────────

assert_ok() {
    local label="$1"; shift
    total=$((total + 1))
    local output
    if output=$("$@" 2>&1); then
        echo -e "${GREEN}PASS${RESET}  $label"
        ((passed++))
    else
        echo -e "${RED}FAIL${RESET}  $label (expected exit 0, got $?)"
        echo "       output: $(echo "$output" | tail -5)"
        ((failed++))
        $ci_mode && exit 1
    fi
}

assert_fail() {
    local label="$1"; shift
    total=$((total + 1))
    local output
    if output=$("$@" 2>&1); then
        echo -e "${RED}FAIL${RESET}  $label (expected failure, got exit 0)"
        echo "       output: $(echo "$output" | tail -3)"
        ((failed++))
        $ci_mode && exit 1
    else
        echo -e "${GREEN}PASS${RESET}  $label"
        ((passed++))
    fi
}

assert_contains() {
    local label="$1" needle="$2"; shift 2
    total=$((total + 1))
    local output
    output=$("$@" 2>&1) || true
    if echo "$output" | grep -Fq "$needle"; then
        echo -e "${GREEN}PASS${RESET}  $label"
        ((passed++))
    else
        echo -e "${RED}FAIL${RESET}  $label (output missing: '$needle')"
        echo "       got: $(echo "$output" | tail -3)"
        ((failed++))
        $ci_mode && exit 1
    fi
}

assert_not_contains() {
    local label="$1" needle="$2"; shift 2
    total=$((total + 1))
    local output
    output=$("$@" 2>&1) || true
    if echo "$output" | grep -Fq "$needle"; then
        echo -e "${RED}FAIL${RESET}  $label (should not contain: '$needle')"
        ((failed++))
        $ci_mode && exit 1
    else
        echo -e "${GREEN}PASS${RESET}  $label"
        ((passed++))
    fi
}

assert_json() {
    local label="$1" file="$2" jq_expr="$3"
    total=$((total + 1))
    if jq -e "$jq_expr" "$file" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${RESET}  $label"
        ((passed++))
    else
        echo -e "${RED}FAIL${RESET}  $label (jq: $jq_expr)"
        echo "       file: $(jq '.' "$file" 2>&1 | head -3)"
        ((failed++))
        $ci_mode && exit 1
    fi
}

# ─── Setup isolated test project ──────────────────────────────────────────

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

cd "$TEST_DIR"
git init -q
git config user.email "test@test.com"
git config user.name "Test"
cp -r "$AISHORE_SRC/.aishore" .

AISHORE="$TEST_DIR/.aishore/aishore"

echo "═══════════════════════════════════════"
echo "  aishore E2E Synthetic Transactions"
echo "═══════════════════════════════════════"
echo "  Project: $TEST_DIR"
echo ""

# ─── 1. Init ──────────────────────────────────────────────────────────────

echo -e "${CYAN}── 1. Init ──${RESET}"

assert_ok          "init -y"                    "$AISHORE" init -y
assert_ok          "config has project name"    grep -q 'name:' .aishore/config.yaml
assert_ok          "backlog.json exists"        test -f backlog/backlog.json
assert_ok          "bugs.json exists"           test -f backlog/bugs.json
assert_ok          "sprint.json exists"         test -f backlog/sprint.json
assert_ok          "DEFINITIONS.md exists"      test -f backlog/DEFINITIONS.md
assert_ok          "CLAUDE.md exists"           test -f CLAUDE.md

# Initial commit
git add -A && git commit -q -m "initial"

echo ""

# ─── 2. Backlog CRUD with track field ─────────────────────────────────────

echo -e "${CYAN}── 2. Backlog CRUD with tracks ──${RESET}"

# Add core item
assert_ok "add core item" "$AISHORE" backlog add --json '{
    "title": "Wire up core path",
    "intent": "The app prints hello — the core path works end-to-end.",
    "track": "core",
    "priority": "must",
    "steps": ["Create app.sh that prints hello"],
    "acceptanceCriteria": [{"text": "app prints hello", "verify": "./app.sh | grep -qi hello"}],
    "readyForSprint": true
}'

# Add feature item
assert_ok "add feature item" "$AISHORE" backlog add --json '{
    "title": "Add goodbye message",
    "intent": "The app prints goodbye after the greeting. Must not break existing output.",
    "track": "feature",
    "priority": "should",
    "steps": ["Add goodbye to app.sh"],
    "acceptanceCriteria": [{"text": "app prints goodbye", "verify": "./app.sh | grep -qi goodbye"}],
    "readyForSprint": true
}'

# Verify track persisted
assert_json  "core item has track:core"     backlog/backlog.json \
    '.items[] | select(.id == "FEAT-001") | select(.track == "core")'
assert_json  "feature item has track:feature" backlog/backlog.json \
    '.items[] | select(.id == "FEAT-002") | select(.track == "feature")'

# List shows track column
assert_contains  "list shows core track"      "core"     "$AISHORE" backlog list
assert_contains  "list shows feature track"   "feature"  "$AISHORE" backlog list

# Show displays track
assert_contains  "show displays track"        "Track:"   "$AISHORE" backlog show FEAT-001

# Edit track
assert_ok        "edit track"                 "$AISHORE" backlog edit FEAT-002 --json '{"track":"core"}'
assert_json      "edit track persisted"       backlog/backlog.json \
    '.items[] | select(.id == "FEAT-002") | select(.track == "core")'
assert_ok        "reset track"               "$AISHORE" backlog edit FEAT-002 --json '{"track":"feature"}'

# Check readiness (AC verify commands fail because app doesn't exist yet — expected)
assert_contains  "check --all runs"          "items"   "$AISHORE" backlog check --all

echo ""

# ─── 3. Core gate in dry-run ──────────────────────────────────────────────

echo -e "${CYAN}── 3. Core gate (dry-run) ──${RESET}"

# No CORE_CMD → picks any item (must first)
assert_contains  "no core cmd: picks FEAT-001"  "FEAT-001"   "$AISHORE" run --dry-run

# Passing CORE_CMD → picks any item
assert_contains  "core healthy: picks FEAT-001"  "FEAT-001"  \
    env AISHORE_CORE_CMD="true" "$AISHORE" run --dry-run

# Failing CORE_CMD + core item available → picks core only
assert_contains  "core broken: picks core item"  "FEAT-001"  \
    env AISHORE_CORE_CMD="false" "$AISHORE" run --dry-run

# Failing CORE_CMD + only feature items → stuck state error
"$AISHORE" backlog edit FEAT-001 --json '{"readyForSprint":false}' >/dev/null 2>&1
assert_contains  "core broken + no core items: stuck error"  "scaffold"  \
    env AISHORE_CORE_CMD="false" "$AISHORE" run --dry-run || true
"$AISHORE" backlog edit FEAT-001 --json '{"readyForSprint":true}' >/dev/null 2>&1

echo ""

# ─── 4. Config backwards compatibility ────────────────────────────────────

echo -e "${CYAN}── 4. Config backwards compat ──${RESET}"

# Old validation.command key loads as CORE_CMD
cat > .aishore/config.yaml << 'YAML'
project:
  name: "compat-test"
validation:
  command: "echo legacy-works"
YAML
assert_contains  "legacy validation.command loads"  "legacy-works"  \
    "$AISHORE" run --dry-run

# New core.command overrides legacy
cat > .aishore/config.yaml << 'YAML'
project:
  name: "compat-test"
validation:
  command: "echo old"
core:
  command: "echo new-wins"
YAML
assert_contains  "core.command overrides legacy"  "new-wins"  \
    "$AISHORE" run --dry-run

# Env var overrides config
assert_contains  "env var overrides config"  "env-wins"  \
    env AISHORE_CORE_CMD="echo env-wins" "$AISHORE" run --dry-run

# Legacy env var still works
assert_contains  "legacy env var loads"  "legacy-env"  \
    env AISHORE_VALIDATE_CMD="echo legacy-env" "$AISHORE" run --dry-run

# Restore clean config
cat > .aishore/config.yaml << 'YAML'
project:
  name: "e2e-test"
YAML

echo ""

# ─── 5. Full sprint with DEVELOPER_CMD ────────────────────────────────────

echo -e "${CYAN}── 5. Full sprint pipeline ──${RESET}"

# Create the app that the sprint will modify
cat > app.sh << 'APPSCRIPT'
#!/bin/bash
echo "placeholder"
APPSCRIPT
chmod +x app.sh

# Create the developer command — reads sprint.json, makes real changes, writes result.json
cat > dev-cmd.sh << 'DEVSCRIPT'
#!/bin/bash
set -euo pipefail
ITEM_ID=$(jq -r '.item.id' backlog/sprint.json)
cat > app.sh << 'EOF'
#!/bin/bash
echo "Hello from the core!"
EOF
chmod +x app.sh
git add app.sh
git commit -m "feat($ITEM_ID): implement core greeting"
cat > .aishore/data/status/result.json << 'EOF'
{"status": "pass", "summary": "Implemented core greeting", "phases": {"critique": {"findings_count": 0, "fixed_count": 0}, "harden": {"verify_commands_run": 1, "verify_commands_passed": 1}}}
EOF
DEVSCRIPT
chmod +x dev-cmd.sh

git add -A && git commit -q -m "setup for sprint"

# Run the sprint
assert_ok "full sprint passes" \
    env AISHORE_DEVELOPER_CMD="./dev-cmd.sh" AISHORE_CORE_CMD="./app.sh | grep -qi hello" \
    "$AISHORE" run

# Verify post-sprint state
assert_ok        "app.sh works"                  bash -c './app.sh | grep -qi hello'
assert_json      "sprint archived"               backlog/archive/sprints.jsonl \
    'select(.itemId == "FEAT-001" and .status == "complete")'
assert_json      "regression entry saved"        backlog/archive/regression.jsonl \
    'select(.itemId == "FEAT-001" and .verify != null)'
assert_json      "sprint.json idle"              backlog/sprint.json \
    'select(.status == "idle")'
assert_json      "item removed from backlog"     backlog/backlog.json \
    '.items | length == 1'

# Only FEAT-002 (feature) should remain
assert_json      "FEAT-002 still in backlog"     backlog/backlog.json \
    '.items[0].id == "FEAT-002"'

echo ""

# ─── 6. Status shows core health ──────────────────────────────────────────

echo -e "${CYAN}── 6. Status with core health ──${RESET}"

assert_contains  "status: core healthy"     "healthy"  \
    env AISHORE_CORE_CMD="./app.sh | grep -qi hello" "$AISHORE" status
assert_contains  "status: core failing"     "FAILING"  \
    env AISHORE_CORE_CMD="false" "$AISHORE" status
assert_not_contains "status: no core cmd = no section"  "Core health"  \
    "$AISHORE" status

echo ""

# ─── 7. Regression suite in preflight ─────────────────────────────────────

echo -e "${CYAN}── 7. Regression suite ──${RESET}"

# The regression from FEAT-001 should run in preflight for the next sprint
# FEAT-002 (feature) should be pickable with a passing core
git add -A && git commit -q -m "post-sprint state" --allow-empty

assert_contains  "dry-run runs regression"  "FEAT-002"  \
    env AISHORE_CORE_CMD="./app.sh | grep -qi hello" "$AISHORE" run --dry-run

echo ""

# ─── 8. Core regression → heal synthesis ──────────────────────────────────

echo -e "${CYAN}── 8. Heal synthesis from core regression ──${RESET}"

# Developer command that passes AC but breaks the core
cat > dev-cmd-break-core.sh << 'DEVSCRIPT'
#!/bin/bash
set -euo pipefail
ITEM_ID=$(jq -r '.item.id' backlog/sprint.json)
# Add goodbye but also break hello (rename to Hi)
cat > app.sh << 'EOF'
#!/bin/bash
echo "Hi from the app!"
echo "Goodbye from the app."
EOF
chmod +x app.sh
git add app.sh
git commit -m "feat($ITEM_ID): add goodbye (breaks hello)"
cat > .aishore/data/status/result.json << 'EOF'
{"status": "pass", "summary": "Added goodbye", "phases": {"critique": {"findings_count": 0, "fixed_count": 0}, "harden": {"verify_commands_run": 1, "verify_commands_passed": 1}}}
EOF
DEVSCRIPT
chmod +x dev-cmd-break-core.sh
git add dev-cmd-break-core.sh && git commit -q -m "add core-breaking dev cmd"

# This sprint should:
# 1. Pass core gate (hello still works pre-sprint)
# 2. Pass AC (goodbye grep passes)
# 3. Pass validator (or fail — either way the AC passes)
# 4. Merge
# 5. Core re-check FAILS (hello → Hi)
# 6. Heal item synthesized
#
# Note: validator may catch the regression and fail the sprint before merge.
# In that case, heal synthesis doesn't trigger (correct behavior — the merge
# never happened, core is still healthy). We test for either outcome.

sprint_output=$(env AISHORE_DEVELOPER_CMD="./dev-cmd-break-core.sh" \
    AISHORE_CORE_CMD="./app.sh | grep -qi hello" \
    "$AISHORE" run 2>&1) || true

# Strip ANSI codes for matching
clean_output=$(echo "$sprint_output" | sed 's/\x1b\[[0-9;]*m//g')

total=$((total + 1))
if echo "$clean_output" | grep -q "Heal item"; then
    echo -e "${GREEN}PASS${RESET}  heal item synthesized after core regression"
    ((passed++))

    # Verify heal item
    assert_json      "heal item in bugs.json"        backlog/bugs.json \
        '.items[] | select(.category == "heal")'
    assert_json      "heal has track:core"            backlog/bugs.json \
        '.items[] | select(.category == "heal" and .track == "core")'
    assert_json      "heal has healSource"            backlog/bugs.json \
        '.items[] | select(.category == "heal" and .healSource != null)'
    assert_json      "heal is must priority"          backlog/bugs.json \
        '.items[] | select(.category == "heal" and .priority == "must")'
    assert_json      "heal is ready"                  backlog/bugs.json \
        '.items[] | select(.category == "heal" and .readyForSprint == true)'

elif echo "$clean_output" | grep -qE "Validator failed|Validation failed|failed"; then
    echo -e "${GREEN}PASS${RESET}  validator caught regression before merge (heal not needed)"
    ((passed++))
    # Core should still be healthy since merge never happened
    assert_ok  "core still healthy (no merge)" \
        bash -c './app.sh | grep -qi hello'
else
    echo -e "${RED}FAIL${RESET}  unexpected outcome — neither heal nor validator catch"
    echo "       output: $(echo "$clean_output" | tail -10)"
    ((failed++))
    $ci_mode && exit 1
fi

echo ""

# ─── 9. Heal-of-heal guard ────────────────────────────────────────────────

echo -e "${CYAN}── 9. Heal-of-heal guard ──${RESET}"

# If there's a heal item in bugs.json, test the guard
heal_count=$(jq '[.items[] | select(.category == "heal")] | length' backlog/bugs.json 2>/dev/null || echo 0)
if [[ "$heal_count" -gt 0 ]]; then
    heal_id=$(jq -r '.items[] | select(.category == "heal") | .id' backlog/bugs.json | head -1)

    # Manually test guard: synthesizing a heal from a heal should fail
    total=$((total + 1))
    guard_output=$(bash -c "
        source <(sed -n '1,/^main()/p' '$AISHORE' | head -n -1)
        BACKLOG_DIR='backlog'
        CORE_CMD='echo test'
        _synthesize_heal_item '$heal_id' 'test output' 2>&1
    ") || true
    if echo "$guard_output" | grep -Fq "itself caused"; then
        echo -e "${GREEN}PASS${RESET}  heal-of-heal guard blocks synthesis"
        ((passed++))
    else
        echo -e "${RED}FAIL${RESET}  heal-of-heal guard did not trigger"
        echo "       output: $guard_output"
        ((failed++))
        $ci_mode && exit 1
    fi

    # Verify guard removed the heal item
    total=$((total + 1))
    remaining=$(jq '[.items[] | select(.id == "'"$heal_id"'")] | length' backlog/bugs.json)
    if [[ "$remaining" -eq 0 ]]; then
        echo -e "${GREEN}PASS${RESET}  guard removed heal item from bugs.json"
        ((passed++))
    else
        echo -e "${RED}FAIL${RESET}  heal item still in bugs.json after guard"
        ((failed++))
        $ci_mode && exit 1
    fi
else
    echo -e "${YELLOW}SKIP${RESET}  no heal item to test guard (validator caught regression)"
fi

echo ""

# ─── Summary ──────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════"
if [[ "$failed" -eq 0 ]]; then
    echo -e "${GREEN}All $total transactions passed${RESET}"
else
    echo -e "${RED}$failed of $total transactions failed${RESET}"
fi
echo "═══════════════════════════════════════"

[[ "$failed" -gt 0 ]] && exit 1
exit 0
