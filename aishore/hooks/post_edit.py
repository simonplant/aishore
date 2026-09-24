"""PostToolUse on Edit|Write|MultiEdit: run the configured formatter for the file's extension.

`[format]` in aishore.toml maps an extension to a command with {file}. A non-zero exit feeds the
output back to the agent. A missing tool (exit 127) is ignored.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

from aishore import lib


def main() -> int:
    data = json.load(sys.stdin)
    target = (data.get("tool_input") or {}).get("file_path", "")
    if not target:
        return 0
    root = lib.repo_root()
    cmd = lib.config(root).get("format", {}).get(Path(target).suffix)
    if not cmd:
        return 0
    r = subprocess.run(cmd.replace("{file}", shlex.quote(target)), shell=True, cwd=root,
                       capture_output=True, text=True, timeout=50)
    if r.returncode not in (0, 127):
        print(f"formatter found problems in {target}:\n{(r.stdout + r.stderr)[-2000:]}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
