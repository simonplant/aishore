"""PreToolUse on Edit|Write|MultiEdit|NotebookEdit: ownership and the task allowlist.

Active only on task branches (t/<id>). Fails closed: any error blocks the edit.
"""
from __future__ import annotations

import json
import sys

from aishore import lib, tasks


def block(msg: str) -> None:
    print(f"Blocked by aishore: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    data = json.load(sys.stdin)
    root = lib.repo_root()
    tid = lib.task_id(root)
    if not tid:
        return 0
    ti = data.get("tool_input") or {}
    target = ti.get("file_path") or ti.get("notebook_path")
    if not target:
        return 0
    rel = lib.relpath(root, target)
    if rel is None:
        block(f"{target} is outside this worktree.")
    if rel in lib.SCRATCH:
        return 0
    cfg = lib.config(root)
    pat = lib.match(rel, [*cfg["ownership"]["locked"], *lib.HARNESS_OWNED])
    if pat:
        block(f"{rel} is human-owned ({pat}). If the task needs it changed, write ESCALATE.md and stop.")
    try:
        task = tasks.load(root, tid)
    except lib.HarnessError as e:
        block(f"no edits allowed while the task is invalid.\n{e}")
    if not lib.match(rel, task.allow):
        block(f"{rel} is outside the allowlist for {tid}: {list(task.allow)}. "
              "If the task needs it, write ESCALATE.md and stop.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # fail closed
        print(f"Blocked by aishore: guard error: {e}", file=sys.stderr)
        sys.exit(2)
