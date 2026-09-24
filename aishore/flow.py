"""Task lifecycle, run from the main checkout.

  new T-042 "title"      scaffold tasks/T-042 and a placeholder acceptance test
  brief-review T-042     reviewer's counterexamples prove gaps in the acceptance tests
  start T-042            validate, prove acceptance tests are red, create worktree, lock paths
  plan-review T-042      reviewer attacks PLAN.md
  review T-042           reviewer checks the diff; findings count only with a failing test
  adopt T-042 1 3        promote REAL finding tests to acceptance tests, sync into worktree
  sync T-042             merge the base branch into the task branch (after you change specs or tests)
  merge T-042            full gate, show diff, human approves, merge, goldens, log, clean up
  abandon T-042 "why"    record escalation, remove worktree and branch
  status                 list open task worktrees
"""
from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from aishore import briefcheck, findings, lib, logbook, tasks

PKG = Path(__file__).resolve().parent
SCAFFOLD = PKG / "scaffold"
PROMPTS = PKG / "prompts"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def main_checkout() -> tuple[Path, dict]:
    try:
        root = lib.repo_root()
        cfg = lib.config(root)
    except lib.HarnessError as e:
        die(str(e))
    if lib.task_id(root):
        die("run this from the main checkout, not a task worktree")
    if lib.branch(root) != base_name(cfg):
        die(f"main checkout must be on '{base_name(cfg)}'")
    return root, cfg


def base_name(cfg: dict) -> str:
    return cfg.get("base", "main")


def git(root: Path, *args: str) -> str:
    return lib.sh("git", *args, cwd=root)


def worktree(root: Path, cfg: dict, tid: str, must_exist: bool = True) -> Path:
    wt = lib.worktree_path(root, cfg, tid)
    if must_exist and not wt.exists():
        die(f"no worktree for {tid} at {wt}")
    return wt


def task_env(wt: Path, cfg: dict, tid: str) -> dict:
    """Gate environment pinned to the task, so a worktree off its branch cannot skip task checks."""
    head = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=wt, capture_output=True, text=True).stdout.strip()
    if head != f"refs/heads/t/{tid}":
        die(f"{wt} is on '{head or 'a detached HEAD'}', not t/{tid}. Check what happened there before anything merges.")
    return dict(lib.env(wt, cfg), AISHORE_TASK=tid, AISHORE_BRANCH=f"t/{tid}")


def remove_worktree(root: Path, cfg: dict, tid: str, force_branch: bool) -> None:
    wt = lib.worktree_path(root, cfg, tid)
    if wt.exists():
        lib.set_locked(wt, cfg, False)
        git(root, "worktree", "remove", "--force", str(wt))
    git(root, "branch", "-D" if force_branch else "-d", f"t/{tid}")


def ask(prompt: str, default: str = "") -> str:
    try:
        return input(prompt).strip() or default
    except EOFError:
        return default


def load(root: Path, tid: str) -> tasks.Task:
    try:
        return tasks.load(root, tid)
    except lib.HarnessError as e:
        die(str(e))
        raise


def claude_env(**extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in lib.NESTED_ENV}
    env.update(extra)
    return env


def prompt(cfg: dict, name: str) -> str:
    acc = cfg["acceptance"]
    return ((PROMPTS / name).read_text()
            .replace("{{LANG}}", acc.get("lang", ""))
            .replace("{{RUNNER}}", acc["cmd"])
            .replace("{{TEST_PATH}}", acc["path"]))


# ---------------------------------------------------------------- commands

def cmd_new(root: Path, cfg: dict, a) -> None:
    d = root / "tasks" / a.id
    if d.exists():
        die(f"{d} exists")
    if not tasks.ID.fullmatch(a.id):
        die("id must look like T-042")
    acc_rel = lib.acceptance_path(cfg, lib.slug(a.id))
    d.mkdir(parents=True)
    for name in ("task.toml", "spec.md"):
        text = (SCAFFOLD / name).read_text()
        (d / name).write_text(text.replace("{{ID}}", a.id).replace("{{TITLE}}", a.title)
                              .replace("{{ACCEPTANCE}}", acc_rel))
    acc = root / acc_rel
    if not acc.exists():
        acc.parent.mkdir(parents=True, exist_ok=True)
        tpl = SCAFFOLD / "acceptance" / f"test{acc.suffix}"
        acc.write_text(tpl.read_text() if tpl.exists()
                       else f"{lib.comment(acc_rel)} {lib.PLACEHOLDER}: write tests for the acceptance table, "
                            "then delete this line.\n")
    print(f"created tasks/{a.id}/ and {acc_rel}")
    print("next: fill spec.md, task.toml and the acceptance test (or run /brief in Claude Code),")
    print(f"      aishore brief-review {a.id}, remove every {lib.PLACEHOLDER} line, commit on {base_name(cfg)},")
    print(f"      then: aishore start {a.id}")


def cmd_start(root: Path, cfg: dict, a) -> Path:
    task = load(root, a.id)
    for p in (lib.CONFIG, ".aishore/bin/aishore", ".aishore/aishore/hooks/guard_edit.py", ".claude/settings.json"):
        if subprocess.run(["git", "ls-files", "--error-unmatch", p], cwd=root, capture_output=True).returncode:
            die(f"{p} is not committed on {base_name(cfg)}; the worktree would run without hooks")
    paths = [f"tasks/{a.id}", *task.acceptance_tests]
    if git(root, "status", "--porcelain", "--", *paths).strip():
        die(f"commit tasks/{a.id} and its acceptance tests on {base_name(cfg)} first")
    for p in paths:
        if subprocess.run(["git", "ls-files", "--error-unmatch", p], cwd=root, capture_output=True).returncode:
            die(f"{p} is not committed")
    if task.kind in ("feature", "fix"):
        r = subprocess.run(lib.acceptance_cmd(cfg, task.acceptance_tests), shell=True, cwd=root,
                           env=lib.env(root, cfg), capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            die("acceptance tests already pass on main, so they cannot prove this task")
        if lib.tests_empty(cfg, r.returncode):
            die(f"acceptance runner found no tests (exit {r.returncode}):\n{out[-1500:]}")
        print("acceptance tests are red on main (expected):")
        print("\n".join(out.splitlines()[-6:]))
    wt = worktree(root, cfg, a.id, must_exist=False)
    if wt.exists():
        die(f"{wt} already exists")
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(root, "worktree", "add", "-q", "-b", f"t/{a.id}", str(wt), base_name(cfg))
    (wt / lib.STATE).mkdir(parents=True, exist_ok=True)
    setup = cfg.get("commands", {}).get("setup", "")
    if setup:
        print(f"setup: {setup}", flush=True)
        if subprocess.run(setup, shell=True, cwd=wt, env=lib.env(wt, cfg)).returncode:
            die(f"setup failed in {wt}; fix commands.setup, then: aishore abandon {a.id}")
    n = lib.set_locked(wt, cfg, True)
    print(f"\nworktree ready: {wt} (branch t/{a.id}, {n} human-owned paths made read-only)")
    model = cfg.get("implement", {}).get("model")
    print(f"  interactive: cd {wt} && claude" + (f" --model {model}" if model else "") + ", then /implement")
    print(f"  headless:    aishore run {a.id}")
    if task.tier == 1:
        print(f"  Tier 1: after PLAN.md exists, run from main: aishore plan-review {a.id}")
    return wt


def reviewer(root: Path, cfg: dict, wt: Path, prompt_file: str, context: str, out: Path) -> str:
    """Run the reviewer as a separate headless Claude Code process in the worktree."""
    rcfg = cfg.get("review", {})
    cmd = list(rcfg.get("cmd", ["claude", "-p", "--output-format", "text", "--tools", "Read,Grep,Glob"]))
    if rcfg.get("model"):
        cmd += ["--model", rcfg["model"]]
    cmd += ["--append-system-prompt", (PROMPTS / "reviewer_role.md").read_text()]
    print(f"reviewer running ({rcfg.get('model', 'default model')}) ...", flush=True)
    r = subprocess.run(cmd + [prompt(cfg, prompt_file)], input=context, text=True, cwd=wt,
                       env=claude_env(AISHORE_ROLE="reviewer"), capture_output=True)
    if r.returncode != 0 or not r.stdout.strip():
        die(f"reviewer failed (exit {r.returncode}): {r.stderr.strip()[-1500:]}")
    out.write_text(r.stdout)
    return r.stdout


def context_for(root: Path, cfg: dict, task: tasks.Task, extra: list[tuple[str, str]]) -> str:
    parts = [(f, (root / f).read_text()) for f in cfg.get("review", {}).get("context", ["ENGINEERING.md"])
             if (root / f).is_file()]
    parts += [("task.toml", (task.dir / "task.toml").read_text()), ("spec.md", (task.dir / "spec.md").read_text())]
    return "\n\n".join(f"===== {name} =====\n{body}" for name, body in parts + extra)


def plan_review(root: Path, cfg: dict, task: tasks.Task, wt: Path) -> str:
    plan = wt / "PLAN.md"
    if not plan.exists():
        die("PLAN.md not found in the worktree; run /implement first")
    out = task.dir / "plan-review.md"
    text = reviewer(root, cfg, wt, "plan_review.md", context_for(root, cfg, task, [("PLAN.md", plan.read_text())]), out)
    m = re.search(r"VERDICT:\s*(\w+)", text)
    return m.group(1).upper() if m else "MISSING"


def cmd_brief_review(root: Path, cfg: dict, a) -> None:
    """Independent attack on the brief before start. The brief may still be uncommitted."""
    try:
        task = tasks.load(root, a.id, allow_placeholder=True)
    except lib.HarnessError as e:
        die(str(e))
        raise
    acc = [(t, (root / t).read_text()) for t in task.acceptance_tests]
    raw = task.dir / "brief-review-raw.md"
    reviewer(root, cfg, root, "brief_review.md", context_for(root, cfg, task, acc), raw)
    out = task.dir / "brief-review.md"
    gaps, _, _ = briefcheck.run(root, cfg, task, raw, out)
    print(out.read_text())
    print(f"saved {out.relative_to(root)}" + (f"; {gaps} proven gap(s): add the rows and tests, then re-run" if gaps else ""))


def cmd_plan_review(root: Path, cfg: dict, a) -> None:
    task = load(root, a.id)
    plan_review(root, cfg, task, worktree(root, cfg, a.id))
    out = task.dir / "plan-review.md"
    print(out.read_text())
    print(f"\nsaved {out.relative_to(root)}. Paste accepted points into the Claude session, then approve.")


def review(root: Path, cfg: dict, task: tasks.Task, wt: Path) -> tuple[int, int, int]:
    gate = subprocess.run(lib.harness("gate", "fast"), cwd=wt, env=task_env(wt, cfg, task.id),
                          capture_output=True, text=True)
    if gate.returncode != 0:
        print(gate.stdout[-3000:])
        die("fast gate is red; review only green work")
    base = lib.merge_base(wt, cfg)
    subprocess.run(["git", "add", "-N", "."], cwd=wt, capture_output=True)
    diff = git(wt, "diff", base)
    out = task.dir / "review.md"
    reviewer(root, cfg, wt, "review.md",
             context_for(root, cfg, task, [("diff against base", diff), ("gate output", gate.stdout[-4000:])]), out)
    return findings.run(wt, out, task.dir / "findings.md", cfg)


def cmd_review(root: Path, cfg: dict, a) -> None:
    task = load(root, a.id)
    real, _, _ = review(root, cfg, task, worktree(root, cfg, a.id))
    print((task.dir / "findings.md").read_text())
    if real:
        nums = " ".join(findings.real_numbers(task.dir / "findings.md"))
        print(f"next: aishore adopt {a.id} {nums}  (read each test first), then tell Claude to make them pass")


def cmd_adopt(root: Path, cfg: dict, a) -> None:
    """Promote REAL finding tests to human-owned acceptance tests and sync them into the worktree."""
    task = load(root, a.id)
    wt = worktree(root, cfg, a.id)
    rv = task.dir / "review.md"
    if not rv.exists():
        die(f"no review.md; run aishore review {a.id} first")
    blocks = dict(findings.BLOCK.findall(rv.read_text()))
    written = []
    for n in a.numbers:
        if n not in blocks:
            die(f"finding {n} has no test block")
        rel = lib.acceptance_path(cfg, f"{lib.slug(a.id)}_f{n}")
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"{lib.comment(rel)} Adopted from review finding {n} of {a.id}.\n" + blocks[n])
        written.append(rel)
    git(root, "add", *written)
    git(root, "commit", "-q", "-m", f"{a.id}: adopt review findings {' '.join(a.numbers)} as acceptance tests")
    sync(root, cfg, wt)
    print(f"adopted {written}; synced into {wt}. Tell the Claude session: new acceptance tests, make them pass.")


def sync(root: Path, cfg: dict, wt: Path) -> None:
    lib.set_locked(wt, cfg, False)
    try:
        git(wt, "merge", "-q", "--no-edit", base_name(cfg))
    finally:
        lib.set_locked(wt, cfg, True)


def cmd_sync(root: Path, cfg: dict, a) -> None:
    sync(root, cfg, worktree(root, cfg, a.id))
    print(f"merged {base_name(cfg)} into t/{a.id}")


def cmd_merge(root: Path, cfg: dict, a) -> None:
    task = load(root, a.id)
    wt = worktree(root, cfg, a.id)
    if (wt / "ESCALATE.md").exists():
        print((wt / "ESCALATE.md").read_text())
        die(f"task escalated. Fix the spec, then: aishore abandon {a.id} \"why\"")
    env = task_env(wt, cfg, a.id)
    print("running full gate in the worktree ...", flush=True)
    if subprocess.run(lib.harness("gate", "full"), cwd=wt, env=env).returncode != 0:
        die("full gate failed; nothing merged")
    git(wt, "add", "-A")
    if git(wt, "status", "--porcelain").strip():
        git(wt, "commit", "-q", "-m", f"{a.id}: {task.title}")
    rng = f"{base_name(cfg)}...t/{a.id}"
    print("\n" + git(root, "diff", "--stat", rng))
    net = 0
    for row in lib.sh(*lib.DIFF, "--numstat", rng, cwd=root).splitlines():
        x, y, f = row.split("\t", 2)
        if x != "-" and lib.in_src(f, cfg):
            net += int(x) - int(y)
    replay = subprocess.run(lib.harness("replay", "diff"), cwd=wt, env=env, capture_output=True, text=True)
    print(replay.stdout[-4000:])
    if task.tier == 1 and not a.yes:
        subprocess.run(["git", "diff", rng], cwd=root)
    if not a.yes and ask(f"merge {a.id} (tier {task.tier}, net LOC {net})? [y/N] ").lower() != "y":
        minutes = a.minutes or ask("human minutes spent: ", "")
        logbook.append(root, id=a.id, tier=task.tier, kind=task.kind, outcome="rejected",
                       human_minutes=minutes, net_loc=net, note=ask("why rejected: ", ""))
        print("not merged; worktree kept for rework")
        return
    minutes = a.minutes or ask("human minutes spent: ", "")
    caught = a.caught if a.caught is not None else ask("gate that caught a problem (blank if none): ", "")
    missing = a.missing if a.missing is not None else ask("missing gate (blank if none): ", "")
    git(root, "merge", "--no-ff", "-q", f"t/{a.id}", "-m", f"Merge {a.id}: {task.title}")
    if task.replay_may_change:
        subprocess.run(lib.harness("replay", "update", *task.replay_may_change),
                       cwd=root, env=lib.env(root, cfg), check=True)
        git(root, "add", cfg["replay"]["golden"])
    real = discarded = ""
    fm = task.dir / "findings.md"
    if fm.exists():
        m = re.search(r"Real (\d+), discarded (\d+)", fm.read_text())
        real, discarded = (m.group(1), m.group(2)) if m else ("", "")
    logbook.append(root, id=a.id, tier=task.tier, kind=task.kind, outcome="merged", human_minutes=minutes,
                   net_loc=net, review_real=real, review_discarded=discarded, gate_caught=caught, missing_gate=missing)
    git(root, "add", f"tasks/{a.id}", "tasks/log.csv")
    if git(root, "diff", "--cached", "--name-only").strip():
        git(root, "commit", "-q", "-m", f"{a.id}: records" + (" and approved goldens" if task.replay_may_change else ""))
    remove_worktree(root, cfg, a.id, force_branch=False)
    print(f"merged {a.id}; worktree removed; logged")


def cmd_abandon(root: Path, cfg: dict, a) -> None:
    wt = worktree(root, cfg, a.id)
    esc = wt / "ESCALATE.md"
    d = root / "tasks" / a.id
    outcome = "escalated" if esc.exists() else "abandoned"
    if esc.exists():
        target = d / "escalations" / f"{dt.datetime.now():%Y%m%d-%H%M%S}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(esc, target)
    tier = kind = ""
    try:
        t = tasks.load(root, a.id)
        tier, kind = t.tier, t.kind
    except lib.HarnessError:
        pass
    logbook.append(root, id=a.id, tier=tier, kind=kind, outcome=outcome, human_minutes=a.minutes or "", note=a.why)
    remove_worktree(root, cfg, a.id, force_branch=True)
    git(root, "add", "tasks/log.csv", f"tasks/{a.id}")
    if git(root, "diff", "--cached", "--name-only").strip():
        git(root, "commit", "-q", "-m", f"{a.id}: {outcome}")
    print(f"{a.id} {outcome}; worktree and branch removed. Fix the spec and start again.")


def cmd_status(root: Path, cfg: dict, a) -> None:
    blocks = git(root, "worktree", "list", "--porcelain").strip().split("\n\n")
    found = False
    for b in blocks:
        path = re.search(r"^worktree (.+)$", b, re.M)
        br = re.search(r"^branch refs/heads/t/(.+)$", b, re.M)
        if not (path and br):
            continue
        found = True
        wt = Path(path.group(1))
        flags = [f for f in ("PLAN.md", "ESCALATE.md") if (wt / f).exists()]
        fm = root / "tasks" / br.group(1) / "findings.md"
        if fm.exists():
            flags.append(f"findings REAL {len(findings.real_numbers(fm))}")
        print(f"{br.group(1):10} {wt}  {' '.join(flags)}")
    if not found:
        print("no open tasks")
