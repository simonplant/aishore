#!/usr/bin/env bash
# ci-entrypoint.sh — Run aishore in CI (GitHub Actions)
# Called by action.yml. Sets up headless environment and runs sprints.
set -euo pipefail

# ── Validate requirements ────────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "::error::ANTHROPIC_API_KEY is required. Set it as a repository secret."
    exit 1
fi

if [[ ! -x ".aishore/aishore" ]]; then
    echo "::error::.aishore/aishore not found or not executable. Run install.sh first."
    exit 1
fi

command -v jq  >/dev/null 2>&1 || { echo "::error::jq is required but not installed."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "::error::git is required but not installed."; exit 1; }

# ── Check for Claude Code CLI ────────────────────────────────────────
if ! command -v claude >/dev/null 2>&1; then
    echo "::group::Installing Claude Code CLI"
    npm install -g @anthropic-ai/claude-code 2>&1 || {
        echo "::error::Failed to install Claude Code CLI. Ensure Node.js is available."
        exit 1
    }
    echo "::endgroup::"
fi

# ── Git identity (required for commits/merges in CI) ─────────────────
if [[ -z "$(git config user.name 2>/dev/null || true)" ]]; then
    git config user.name "aishore[bot]"
    git config user.email "aishore[bot]@users.noreply.github.com"
fi

# ── Build run command ────────────────────────────────────────────────
run_args="${AISHORE_RUN_ARGS:-1}"
pr_flag=""
if [[ "${AISHORE_PR_MODE:-true}" == "true" ]]; then
    pr_flag="--pr"
fi

retries_flag=""
if [[ -n "${AISHORE_RETRIES:-}" && "${AISHORE_RETRIES:-0}" -gt 0 ]]; then
    retries_flag="--retries ${AISHORE_RETRIES}"
fi

# ── Export config overrides (empty values are ignored by aishore) ─────
# AISHORE_MODEL_PRIMARY, AISHORE_AGENT_TIMEOUT, AISHORE_SETUP_CMD,
# AISHORE_CORE_CMD are already in the environment from action.yml.

# ── Run ──────────────────────────────────────────────────────────────
echo "::group::aishore sprint"
echo "Running: .aishore/aishore run ${run_args} ${pr_flag} ${retries_flag}"

# shellcheck disable=SC2086
exit_code=0
.aishore/aishore run ${run_args} ${pr_flag} ${retries_flag} || exit_code=$?

echo "::endgroup::"
exit "${exit_code}"
