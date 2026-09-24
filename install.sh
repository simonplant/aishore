#!/usr/bin/env bash
# Install or update aishore in the git repository at the current directory.
#   curl -fsSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --profile node      # python | node | generic
# AISHORE_REF selects a branch, tag or commit (default main). A GITHUB_TOKEN, GH_TOKEN or
# `gh auth` login is used when present, so a private fork works.
set -euo pipefail
ref="${AISHORE_REF:-main}"
repo="${AISHORE_REPO:-simonplant/aishore}"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null \
  || { echo "aishore needs python3 >= 3.11 on PATH" >&2; exit 1; }
token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [[ -z "$token" ]] && command -v gh >/dev/null; then
  token=$(gh auth token 2>/dev/null || true)
fi
auth=()
[[ -n "$token" ]] && auth=(-H "Authorization: Bearer $token")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL "${auth[@]}" "https://api.github.com/repos/$repo/tarball/$ref" | tar xz -C "$tmp" --strip-components=1
PYTHONPATH="$tmp" python3 -m aishore install --dir "$PWD" "$@"
