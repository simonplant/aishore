"""Stop: the agent cannot finish a task session while the fast gate is red.

Planning is exempt: while the branch changes nothing but PLAN.md, stopping is allowed.
Blocks up to twice per red streak. The second block instructs escalation. The third stop
is allowed so the session cannot loop forever; the merge gate still refuses the work.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from aishore import lib

MAX_BLOCKS = 2


def main() -> int:
    json.load(sys.stdin)
    root = lib.repo_root()
    if os.environ.get("AISHORE_ROLE") == "reviewer":
        return 0
    if not lib.task_id(root) or (root / "ESCALATE.md").exists():
        return 0
    cfg = lib.config(root)
    changed, untracked = lib.changed_files(root, lib.merge_base(root, cfg))
    if not (changed | untracked) - set(lib.SCRATCH):
        return 0
    state = root / lib.STATE
    state.mkdir(parents=True, exist_ok=True)
    counter = state / "stop_failures"
    try:
        r = subprocess.run(lib.harness("gate", "fast"), cwd=root, env=lib.env(root, cfg),
                           capture_output=True, text=True, timeout=540)
        ok, output = r.returncode == 0, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        ok, output = False, "gate timed out after 540s"
    if ok:
        counter.unlink(missing_ok=True)
        return 0
    n = (int(counter.read_text()) if counter.exists() else 0) + 1
    counter.write_text(str(n))
    if n > MAX_BLOCKS:
        return 0
    if n == MAX_BLOCKS:
        msg = ("The fast gate is still red (second failure). Stop fixing. Write ESCALATE.md with: "
               "what fails, what you tried, and what in the spec or architecture would need to change. Then stop.")
    else:
        msg = "The fast gate is red. Fix the failure below, then stop again."
    print(f"{msg}\n\n{output[-3000:]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
