"""aishore CLI. Task commands run from the main checkout; `gate` and `hook` run anywhere in the repo."""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("aishore needs Python 3.11 or newer")

from aishore import __version__  # noqa: E402

MODULES = {"gate": "gate", "validate": "tasks", "replay": "replay", "entropy": "entropy",
           "selftest": "selftest", "diffcheck": "diffcheck", "mutate": "mutate"}
HOOKS = ("guard_edit", "guard_bash", "post_edit", "stop")
USAGE = """aishore <command>

task lifecycle (main checkout)
  new T-042 "title"       scaffold tasks/T-042 and a placeholder acceptance test
  brief-review T-042      reviewer tries wrong implementations that pass the acceptance tests
  start T-042             prove acceptance tests red, create the worktree, lock human-owned paths
  run T-042 [--approve-plan]  headless: plan, reviewer approves (or you do), build, review, one fix round
  plan-review T-042       reviewer attacks PLAN.md
  review T-042            reviewer checks the diff; findings count only with a failing test
  adopt T-042 1 3         promote REAL findings to acceptance tests, sync into the worktree
  sync T-042              merge the base branch into the task branch
  merge T-042             full gate, diff, you approve, merge, log, clean up
  abandon T-042 "why"     file the escalation, remove worktree and branch
  status                  open task worktrees

gates and records
  gate fast|full          run the gate here
  validate T-042          check a task against the schema
  replay check|diff|update [CASE...]
  entropy                 append a size and complexity snapshot to entropy.csv

setup
  install [--dir PATH] [--profile python|node|generic]
  update [--ref REF]      reinstall .aishore/ from GitHub, keep aishore.toml and ENGINEERING.md
  selftest                end-to-end check of the harness in throwaway repos
  version
"""


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "version":
        print(__version__)
        return 0
    if cmd in MODULES:
        sys.argv = [f"aishore {cmd}", *rest]
        runpy.run_module(f"aishore.{MODULES[cmd]}", run_name="__main__")
        return 0
    if cmd == "hook":
        if not rest or rest[0] not in HOOKS:
            print(f"usage: aishore hook {'|'.join(HOOKS)}", file=sys.stderr)
            return 2
        runpy.run_module(f"aishore.hooks.{rest[0]}", run_name="__main__")
        return 0

    from aishore import flow, install, run

    p = argparse.ArgumentParser(prog="aishore", usage=USAGE)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("id"); s.add_argument("title")
    for name in ("start", "brief-review", "plan-review", "review", "sync"):
        sub.add_parser(name).add_argument("id")
    s = sub.add_parser("run"); s.add_argument("id")
    s.add_argument("--approve-plan", action="store_true",
                   help="you approve PLAN.md; skip the reviewer's plan review")
    s = sub.add_parser("adopt"); s.add_argument("id"); s.add_argument("numbers", nargs="+")
    s = sub.add_parser("merge"); s.add_argument("id")
    s.add_argument("--yes", action="store_true", help="skip prompts (scripted use)")
    s.add_argument("--minutes", default=""); s.add_argument("--caught"); s.add_argument("--missing")
    s = sub.add_parser("abandon"); s.add_argument("id"); s.add_argument("why", nargs="?", default="")
    s.add_argument("--minutes", default="")
    sub.add_parser("status")
    s = sub.add_parser("install"); s.add_argument("--dir", default=".")
    s.add_argument("--profile", choices=sorted(install.PROFILES))
    s = sub.add_parser("update"); s.add_argument("--ref", default="main")
    a = p.parse_args([cmd, *rest])

    if a.cmd == "install":
        install.install(Path(a.dir), a.profile)
        return 0
    if a.cmd == "update":
        install.update(Path.cwd(), a.ref)
        return 0
    root, cfg = flow.main_checkout()
    {"new": flow.cmd_new, "brief-review": flow.cmd_brief_review, "start": flow.cmd_start, "run": run.main,
     "plan-review": flow.cmd_plan_review,
     "review": flow.cmd_review, "adopt": flow.cmd_adopt, "sync": flow.cmd_sync, "merge": flow.cmd_merge,
     "abandon": flow.cmd_abandon, "status": flow.cmd_status}[a.cmd](root, cfg, a)
    return 0


def entry() -> None:
    from aishore.lib import HarnessError

    try:
        sys.exit(main(sys.argv[1:]))
    except HarnessError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    entry()
