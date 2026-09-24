#!/usr/bin/env bash
# Install or update aishore in the git repository at the current directory.
#   curl -fsSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --profile node      # python | node | generic
# AISHORE_REF selects a branch, tag or commit (default main).
set -euo pipefail
ref="${AISHORE_REF:-main}"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null \
  || { echo "aishore needs python3 >= 3.11 on PATH" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL "https://codeload.github.com/simonplant/aishore/tar.gz/$ref" | tar xz -C "$tmp" --strip-components=1
PYTHONPATH="$tmp" python3 -m aishore install --dir "$PWD" "$@"
