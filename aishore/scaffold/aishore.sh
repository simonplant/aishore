#!/bin/sh
# aishore CLI. Needs python3 >= 3.11 and git.
here=$(cd "$(dirname "$0")/.." && pwd)
PYTHONPATH="$here${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m aishore "$@"
