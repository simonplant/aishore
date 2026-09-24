"""Replay oracle: run each recorded case and diff the event stream against its golden.

  aishore replay check           gate step; only task.replay_may_change cases may differ
  aishore replay diff            print unified diffs for every changed case
  aishore replay update CASE...  write goldens (base branch only; merge runs this)

The configured command prints one event per line (JSON) to stdout for one input file.
"""
from __future__ import annotations

import difflib
import shlex
import subprocess
import sys
from pathlib import Path

from aishore import lib, tasks


def case_files(root: Path, cfg: dict) -> list[Path]:
    d = root / cfg["replay"]["cases"]
    return sorted(p for p in d.iterdir() if p.is_file() and not p.name.startswith(".")) if d.exists() else []


def run_case(root: Path, cfg: dict, path: Path, env: dict) -> list[str]:
    cmd = cfg["replay"]["cmd"].replace("{input}", shlex.quote(str(path)))
    r = subprocess.run(cmd, shell=True, cwd=root, env=env, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise lib.HarnessError(f"replay case {path.stem} exited {r.returncode}:\n{r.stderr[-1500:]}")
    return [line.rstrip() for line in r.stdout.splitlines() if line.strip()]


def results(root: Path, cfg: dict) -> dict[str, tuple[list[str] | None, list[str]]]:
    env = lib.env(root, cfg)
    out_dir = root / lib.STATE / "replay"
    out_dir.mkdir(parents=True, exist_ok=True)
    golden_dir = root / cfg["replay"]["golden"]
    res = {}
    for p in case_files(root, cfg):
        actual = run_case(root, cfg, p, env)
        (out_dir / f"{p.stem}.jsonl").write_text("\n".join(actual) + "\n")
        g = golden_dir / f"{p.stem}.jsonl"
        golden = [x.rstrip() for x in g.read_text().splitlines() if x.strip()] if g.exists() else None
        res[p.stem] = (golden, actual)
    return res


def udiff(name: str, golden: list[str] | None, actual: list[str], limit: int = 60) -> str:
    lines = list(difflib.unified_diff(golden or [], actual, f"golden/{name}", f"actual/{name}", lineterm="", n=1))
    more = f"\n  ... {len(lines) - limit} more lines" if len(lines) > limit else ""
    return "\n".join(lines[:limit]) + more


def main(argv: list[str]) -> int:
    root = lib.repo_root()
    cfg = lib.config(root)
    if not cfg.get("replay", {}).get("cmd"):
        print("replay: not configured, skipped")
        return 0
    action = argv[0] if argv else "check"
    try:
        res = results(root, cfg)
    except lib.HarnessError as e:
        print(e)
        return 1
    changed = {k: v for k, v in res.items() if v[0] != v[1]}
    if action == "diff":
        for name, (g, a) in changed.items():
            print(udiff(name, g, a))
        print(f"replay: {len(changed)} of {len(res)} cases differ")
        return 0
    if action == "update":
        if lib.task_id(root):
            print("replay update refused on a task branch. Goldens are human-owned.")
            return 1
        golden_dir = root / cfg["replay"]["golden"]
        golden_dir.mkdir(parents=True, exist_ok=True)
        for name in argv[1:] or list(res):
            if name not in res:
                print(f"unknown case {name}")
                return 1
            (golden_dir / f"{name}.jsonl").write_text("\n".join(res[name][1]) + "\n")
            print(f"golden written: {name}")
        return 0
    tid = lib.task_id(root)
    allowed = set(tasks.load(root, tid).replay_may_change) if tid else set()
    unexpected = {k: v for k, v in changed.items() if k not in allowed}
    for name, (g, a) in unexpected.items():
        print(("MISSING GOLDEN " if g is None else "UNEXPECTED CHANGE ") + name)
        print(udiff(name, g, a, limit=30))
    if unexpected:
        print(f"replay FAILED: {len(unexpected)} case(s) changed that the task does not allow")
        return 1
    print(f"replay: {len(res)} cases, {len(changed)} changed (allowed: {sorted(allowed) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
