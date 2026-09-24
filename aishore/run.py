"""Headless task run. The reviewer model stands in for the human at plan approval; merge stays human.

  aishore run T-042

1. start the task if it has no worktree
2. implementer (headless Claude Code in the worktree, hooks active) writes PLAN.md
3. reviewer attacks the plan; REVISE sends the points back; a second REVISE stops the run
4. implementer builds to green under the Stop hook
5. tier 1 and 2: reviewer checks the diff; proven findings go back to the implementer once
6. stop; print the findings and the merge command

Re-running resumes: the implementer session id and plan approval live in the worktree's state dir.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from aishore import findings, flow, lib

DEFAULT_CMD = ["claude", "-p", "--output-format", "json", "--permission-mode", "acceptEdits",
               "--allowedTools", "Bash,Edit,Write,MultiEdit,Read,Glob,Grep"]
PLAN = ("You are the implementer, running headless. Read .claude/commands/implement.md and follow steps 1-3 "
        "only: write PLAN.md, then stop. Approval comes in a later message.")
BUILD = ("PLAN.md is approved. Follow steps 4-7 of .claude/commands/implement.md: implement the plan and nothing "
         "else, run the fast gate until it is green, or write ESCALATE.md and stop.")


def implementer(cfg: dict, wt: Path, text: str) -> str:
    state = wt / lib.STATE
    sid_file = state / "session"
    icfg = cfg.get("implement", {})
    cmd = list(icfg.get("headless", DEFAULT_CMD))
    if icfg.get("model"):
        cmd += ["--model", icfg["model"]]
    if sid_file.exists():
        cmd += ["--resume", sid_file.read_text().strip()]
    print(f"implementer running ({icfg.get('model', 'default model')}) ...", flush=True)
    r = subprocess.run(cmd + [text], cwd=wt, env=flow.claude_env(AISHORE_ROLE="implementer"),
                       capture_output=True, text=True)
    with (state / "run.log").open("a") as fh:
        fh.write(f"$ {' '.join(cmd[:3])} ... (exit {r.returncode})\n{r.stdout}\n{r.stderr}\n")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        flow.die(f"implementer exited {r.returncode} without JSON output: {(r.stderr or r.stdout)[-1500:]}")
    if data.get("session_id"):
        sid_file.write_text(data["session_id"])
    if r.returncode or data.get("is_error"):
        flow.die(f"implementer failed (exit {r.returncode}): {str(data.get('result', ''))[-1500:]}")
    result = str(data.get("result", "")).strip()
    print(result[-2000:])
    return result


def stop_if_escalated(wt: Path, tid: str) -> None:
    esc = wt / "ESCALATE.md"
    if esc.exists():
        print(esc.read_text())
        flow.die(f"implementer escalated. Fix the spec, then: aishore abandon {tid} \"why\"")


def fast_green(cfg: dict, wt: Path, show: bool = False) -> bool:
    r = subprocess.run(lib.harness("gate", "fast"), cwd=wt, env=lib.env(wt, cfg), capture_output=True, text=True)
    if r.returncode and show:
        print(r.stdout[-3000:])
    return r.returncode == 0


def resume_hint(wt: Path) -> str:
    sid = wt / lib.STATE / "session"
    return f"cd {wt} && claude --resume {sid.read_text().strip()}" if sid.exists() else f"cd {wt} && claude"


def main(root: Path, cfg: dict, a) -> None:
    task = flow.load(root, a.id)
    wt = lib.worktree_path(root, cfg, a.id)
    if not wt.exists():
        flow.cmd_start(root, cfg, a)
    state = wt / lib.STATE
    state.mkdir(parents=True, exist_ok=True)
    approved = state / "plan-approved"
    stop_if_escalated(wt, a.id)

    if not approved.exists():
        if not (wt / "PLAN.md").exists():
            implementer(cfg, wt, PLAN)
            stop_if_escalated(wt, a.id)
        if not (wt / "PLAN.md").exists():
            flow.die(f"implementer did not write PLAN.md. Continue by hand: {resume_hint(wt)}")
        for attempt in (1, 2):
            verdict = flow.plan_review(root, cfg, task, wt)
            print(f"plan review {attempt}: {verdict}")
            if verdict == "APPROVE":
                approved.touch()
                break
            points = (task.dir / "plan-review.md").read_text()
            if attempt == 2:
                print(points)
                flow.die(f"plan not approved after two reviews (tasks/{a.id}/plan-review.md). "
                         f"Approve or revise it yourself: {resume_hint(wt)}")
            implementer(cfg, wt, f"The reviewer asks for plan changes:\n\n{points}\n\n"
                                 "Revise PLAN.md where the points hold. Edit no other file. Then stop.")
            stop_if_escalated(wt, a.id)

    built = state / "built"
    if not built.exists():
        implementer(cfg, wt, BUILD)
        stop_if_escalated(wt, a.id)
        built.touch()
    elif not fast_green(cfg, wt):
        implementer(cfg, wt, "The fast gate is red: the base branch changed (new acceptance tests or spec). "
                             "Read the changes, make the gate green within the plan, or write ESCALATE.md and stop.")
        stop_if_escalated(wt, a.id)
    if not fast_green(cfg, wt, show=True):
        flow.die(f"implementer stopped with the fast gate red. Continue by hand: {resume_hint(wt)}")

    fm = task.dir / "findings.md"
    if task.tier < 3:
        real, _, _ = flow.review(root, cfg, task, wt)
        if real:
            nums = findings.real_numbers(fm)
            blocks = dict(findings.BLOCK.findall((task.dir / "review.md").read_text()))
            tests = "\n\n".join(f"Finding {n}:\n```\n{blocks[n]}```" for n in nums if n in blocks)
            implementer(cfg, wt, "An independent reviewer proved defects with tests that fail on this branch. "
                                 "Fix the code so each test would pass, within the allowlist and the plan's intent. "
                                 f"Then run the fast gate until it is green.\n\n{tests}")
            stop_if_escalated(wt, a.id)
            findings.run(wt, task.dir / "review.md", fm, cfg)
        print(fm.read_text())
    still = findings.real_numbers(fm) if fm.exists() and task.tier < 3 else []
    print(f"\n{a.id} ready for you.")
    if still:
        print(f"  findings still failing: {' '.join(still)}. Adopt the ones you agree with: aishore adopt {a.id} "
              f"{' '.join(still)}, then: aishore run {a.id}")
    print(f"  merge (full gate, you approve): aishore merge {a.id}")


if __name__ == "__main__":
    sys.exit("use: aishore run T-042")
