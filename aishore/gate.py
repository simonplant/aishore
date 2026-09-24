"""The gate. `fast` runs inside the agent loop (Stop hook). `full` runs at merge and in CI.

  aishore gate fast|full

Steps run in order and stop at the first failure.
"""
from __future__ import annotations

import subprocess
import sys
import time

from aishore import lib

FAST = ("lint", "types", "imports", "diff", "tests", "acceptance")
FULL = ("escalation",) + FAST + ("replay", "mutation")
MODULE_STEPS = {"diff": ("diffcheck",), "replay": ("replay", "check"), "mutation": ("mutate",)}


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else "fast"
    if mode not in ("fast", "full"):
        print("usage: aishore gate fast|full")
        return 2
    root = lib.repo_root()
    cfg = lib.config(root)
    env = lib.env(root, cfg)
    commands = cfg.get("commands", {})
    started = time.monotonic()
    for step in FAST if mode == "fast" else FULL:
        t0 = time.monotonic()
        if step == "escalation":
            ok = not (root / "ESCALATE.md").exists()
            if not ok:
                print("== escalation: ESCALATE.md present. The task cannot merge.")
        elif step == "acceptance":
            suite = lib.acceptance_suite(root, cfg)
            if not suite:
                print("-- acceptance: no merged or current task tests, skipped")
                continue
            cmd = lib.acceptance_cmd(cfg, suite)
            print(f"== acceptance: {len(suite)} files", flush=True)
            ok = subprocess.run(cmd, shell=True, cwd=root, env=env).returncode == 0
        elif step in MODULE_STEPS:
            print(f"== {step}", flush=True)
            ok = subprocess.run(lib.harness(*MODULE_STEPS[step]), cwd=root, env=env).returncode == 0
        else:
            cmd = commands.get(step, "")
            if not cmd:
                print(f"-- {step}: not configured, skipped")
                continue
            print(f"== {step}: {cmd}", flush=True)
            ok = subprocess.run(cmd, shell=True, cwd=root, env=env).returncode == 0
        if not ok:
            print(f"\nGATE FAILED at '{step}' ({mode})")
            return 1
        print(f"   {step} ok ({time.monotonic() - t0:.1f}s)", flush=True)
    print(f"\nGATE PASSED ({mode}, {time.monotonic() - started:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
