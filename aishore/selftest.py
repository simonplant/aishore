"""End-to-end self-test: installs aishore into throwaway repos and drives every gate through the CLI.

  aishore selftest

Python profile: install and legacy removal, hooks exactly as settings.json runs them, diffcheck,
replay, mutation, reviewer findings, adopt, merge, pending-task isolation, and a headless
`aishore run` against a stub `claude`. Node and generic profiles: install, red proof, guards,
language cheats, findings, merge. Vitest: a project whose config `include` excludes tests/acceptance.
Needs git, Python 3.11+, and pytest; the node part needs node; the vitest part needs npm and the registry.
Never calls a model.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
INSTALLER = [sys.executable, "-m", "aishore", "install", "--dir"]
RESULTS: list[tuple[bool, str]] = []

STUB = r'''#!/usr/bin/env python3
"""Stub `claude`: reviewer (--tools) or headless implementer, driven by files in $STUB_DIR."""
import json, os, sys
from pathlib import Path

args, d = sys.argv[1:], Path(os.environ["STUB_DIR"])
prompt = args[-1]
def bump(name):
    f = d / name
    n = int(f.read_text()) + 1 if f.exists() else 1
    f.write_text(str(n))
    return n
assert "CLAUDECODE" not in os.environ, "nested session variables leaked"
assert "--model" in args, args
if "--tools" in args:
    assert "--append-system-prompt" in args, args
    assert os.environ.get("AISHORE_ROLE") == "reviewer"
    ctx = sys.stdin.read()
    assert "===== spec.md =====" in ctx and "===== ENGINEERING.md =====" in ctx, ctx[:300]
    if "===== PLAN.md =====" in ctx:
        n = bump("plan_reviews")
        print("1. Reuse the existing module.")
        print("VERDICT: " + ("REVISE" if n == 1 or os.environ.get("STUB_PLAN") == "revise" else "APPROVE"))
    elif "diff against base" in ctx:
        print((d / "review.md").read_text())
    else:
        assert "===== tests/acceptance/" in ctx, ctx[-300:]
        print((d / "brief.md").read_text())
    sys.exit(0)
assert os.environ.get("AISHORE_ROLE") == "implementer"
resumed = "--resume" in args
if "steps 1-3" in prompt:
    assert not resumed
    Path("PLAN.md").write_text("## Add\nthe function\n")
elif "plan changes" in prompt:
    assert resumed and "Reuse the existing module" in prompt
    Path("PLAN.md").write_text(Path("PLAN.md").read_text() + "## Change\nreuse\n")
elif "steps 4-7" in prompt:
    assert resumed
    Path(os.environ["STUB_TARGET"]).write_text((d / "impl").read_text())
elif "proved defects" in prompt:
    assert resumed and "Finding 1" in prompt
    Path(os.environ["STUB_TARGET"]).write_text((d / "fix").read_text())
else:
    raise SystemExit(f"unexpected prompt: {prompt[:200]}")
bump("implementer_calls")
print(json.dumps({"type": "result", "session_id": "stub-session", "is_error": False, "result": "done"}))
'''

CALC = '''def clamp(x: int, lo: int, hi: int) -> int:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
'''

REPLAY = '''import json
import sys

from toy.calc import clamp

with open(sys.argv[1]) as fh:
    for v in json.load(fh):
        print(json.dumps({"x": v, "c": clamp(v, 0, 10)}))
'''

TASK = '''id = "{id}"
title = "{title}"
tier = 2
kind = "feature"
allow = [{allow}]
acceptance_tests = ["{test}"]
loc_budget = 40
'''

SPEC = """# {id}: {title}
## Intent
{title}.
## Interface
see acceptance
## Acceptance
| input | expected |
## Invariants
- none
## Out of scope
- everything else
"""

ACCEPT = '''from toy.calc import wrap


def test_wrap():
    assert wrap(12, 10) == 2
    assert wrap(-1, 10) == 9
'''

REVIEW_PY = """### Finding 1: negative modulus unhandled
Severity: medium
Why: spec says 0 <= wrap(x, n) < n.
```python
# finding: 1
from toy.calc import wrap

def test_negative_n():
    assert 0 <= wrap(3, -2) < 2
```
VERDICT: FIX
"""


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}", flush=True)
    if not ok and detail:
        print("      " + detail.strip().replace("\n", "\n      ")[-2500:])


def run(args, cwd, env=None, stdin=None, shell=False) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, shell=shell)


def git(cwd, *args):
    r = run(["git", *args], cwd)
    if r.returncode:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        os.chmod(path, 0o644)
    path.write_text(text)


def new_repo(root: Path) -> None:
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "selftest@example.com")
    git(root, "config", "user.name", "selftest")


def commit(root: Path, msg: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)


def set_config(root: Path, **values: str) -> None:
    """Replace top-level-in-section `key = ...` lines of aishore.toml; values are TOML literals."""
    p = root / "aishore.toml"
    lines = p.read_text().splitlines()
    for key, val in values.items():
        section, name = key.split(".") if "." in key else ("", key)
        current, done = "", False
        for i, line in enumerate(lines):
            if line.startswith("["):
                current = line.strip("[] ")
            elif current == section and line.split("=")[0].strip() == name and not done:
                lines[i], done = f"{name} = {val}", True
        if not done:
            raise RuntimeError(f"no {key} in aishore.toml")
    p.write_text("\n".join(lines) + "\n")
    tomllib.loads(p.read_text())


class Repo:
    def __init__(self, root: Path, env: dict):
        self.root, self.env = root, env

    @property
    def cli(self) -> str:
        return str(self.root / ".aishore" / "bin" / "aishore")

    def aishore(self, *args: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        return run([self.cli, *args], cwd or self.root, env or self.env)

    def wt(self, tid: str) -> Path:
        return (self.root.parent / ".wt" / f"{self.root.name}-{tid}").resolve()

    def hook(self, name: str, cwd: Path, payload: dict) -> subprocess.CompletedProcess:
        """Run the hook exactly as .claude/settings.json does."""
        settings = json.loads((cwd / ".claude" / "settings.json").read_text())
        cmd = next(h["command"] for groups in settings["hooks"].values() for g in groups for h in g["hooks"]
                   if h["command"].endswith(f"hook {name}"))
        return run(cmd, cwd, dict(self.env, CLAUDE_PROJECT_DIR=str(cwd)), json.dumps(payload), shell=True)

    def task(self, tid: str, title: str, allow: str, test_rel: str, test_body: str) -> None:
        r = self.aishore("new", tid, title)
        check(r.returncode == 0 and (self.root / test_rel).exists(), f"{self.root.name}: new {tid} scaffolds task",
              r.stdout + r.stderr)
        write(self.root / f"tasks/{tid}/task.toml", TASK.format(id=tid, title=title, allow=allow, test=test_rel))
        write(self.root / f"tasks/{tid}/spec.md", SPEC.format(id=tid, title=title))
        write(self.root / test_rel, test_body)
        commit(self.root, f"{tid} task")


def python_part(tmp: Path, env: dict, py: str, stub_dir: Path) -> None:
    root = tmp / "pyrepo"
    root.mkdir()
    new_repo(root)
    write(root / "pyproject.toml", '[project]\nname = "toy"\nversion = "0"\n\n[tool.pytest.ini_options]\npythonpath = ["src"]\n')
    write(root / "src/toy/__init__.py", "")
    write(root / "src/toy/calc.py", CALC)
    write(root / "src/toy/replay.py", REPLAY)
    write(root / "tests/unit/test_calc.py", "from toy.calc import clamp\n\n\ndef test_clamp():\n"
          "    assert clamp(-5, 0, 10) == 0\n    assert clamp(12, 0, 10) == 10\n    assert clamp(3, 0, 10) == 3\n")
    write(root / "replay/cases/basic.json", "[-5, 3, 12]")
    write(root / ".aishore/aishore", "#!/usr/bin/env bash\necho legacy\n")
    write(root / ".aishore/data/logs/x.log", "old\n")
    write(root / "CLAUDE.md", "# Toy\n\nProject rules.\n\n## Sprint Orchestration (aishore)\nold stuff\n\n## Other\nkeep\n")
    write(root / ".gitignore", "# aishore runtime files\n.aishore/data/logs/\n")
    commit(root, "init")

    # install
    r = run([*INSTALLER, str(root)], root, env)
    repo = Repo(root, env)
    check(r.returncode == 0, "install runs", r.stdout + r.stderr)
    cfg = tomllib.loads((root / "aishore.toml").read_text())
    check("(python profile)" in (root / "aishore.toml").read_text() and cfg["src"] == ["src"]
          and cfg["acceptance"]["fail_codes"] == [1], "install detects python profile and src root")
    check(os.access(repo.cli, os.X_OK) and (root / ".aishore/aishore/flow.py").exists()
          and not (root / ".aishore/data").exists(), "install vendors the harness and removes the bash aishore")
    cm = (root / "CLAUDE.md").read_text()
    check("Sprint Orchestration" not in cm and "## Other\nkeep" in cm and "@ENGINEERING.md" in cm,
          "install strips the old CLAUDE.md section and adds imports", cm)
    gi = (root / ".gitignore").read_text()
    check(".aishore/data" not in gi and ".aishore/state/" in gi, "install rewrites .gitignore entries", gi)
    r = run([*INSTALLER, str(root)], root, env)
    settings = json.loads((root / ".claude/settings.json").read_text())
    n_hooks = sum(len(g["hooks"]) for gs in settings["hooks"].values() for g in gs)
    deny = settings["permissions"]["deny"]
    marks = (root / "CLAUDE.md").read_text().count("<!-- aishore -->")
    check(r.returncode == 0 and n_hooks == 4 and deny == ["Bash(git push:*)", "Bash(sudo:*)"] and marks == 1
          and "kept aishore.toml" in r.stdout, "second install is idempotent", r.stdout + json.dumps(settings))
    check((root / ".github/workflows/aishore-verify.yml").exists() and (root / "docs/adr/0000-template.md").exists(),
          "install writes the CI workflow and the ADR template")

    lint = f'"{shutil.which("ruff")} check --isolated src"' if shutil.which("ruff") else '""'
    set_config(root, **{
        "commands.lint": lint,
        "commands.tests": f'"{py} -m pytest -q -x -p no:cacheprovider tests/unit"',
        "acceptance.cmd": f'"{py} -m pytest -q -p no:cacheprovider {{tests}}"',
        "replay.cmd": f'"{py} -m toy.replay {{input}}"',
        "mutation.max_mutants": "20",
        "defaults.loc_budget": "40",
    })
    r = repo.aishore("replay", "update")
    check(r.returncode == 0, "replay goldens written on main", r.stdout + r.stderr)
    commit(root, "install aishore")

    # task scaffolding and validation
    r = repo.aishore("new", "T-001", "Add wrap")
    check(r.returncode == 0, "new scaffolds task and placeholder test", r.stderr)
    r = repo.aishore("validate", "T-001")
    check(r.returncode == 1 and "AISHORE_PLACEHOLDER" in r.stdout and "allow" in r.stdout,
          "validator rejects the unedited template", r.stdout)
    task = TASK.format(id="T-001", title="Add wrap", allow='"src/toy/calc.py", "tests/unit/*"',
                       test="tests/acceptance/test_t_001.py") + "mutation_min_kill = 0.8\n"
    write(root / "tasks/T-001/task.toml", task.replace('"tests/unit/*"', '"tests/acceptance/*"'))
    write(root / "tasks/T-001/spec.md", SPEC.format(id="T-001", title="Add wrap"))
    write(root / "tests/acceptance/test_t_001.py", ACCEPT)
    r = repo.aishore("validate", "T-001")
    check(r.returncode == 1 and "human-owned" in r.stdout, "validator rejects allowlist covering locked path", r.stdout)
    write(root / "tasks/T-001/task.toml", task)
    r = repo.aishore("validate", "T-001")
    check(r.returncode == 0, "validator accepts a complete task", r.stdout)
    r = repo.aishore("start", "T-001")
    check(r.returncode == 1 and "commit" in r.stderr, "start refuses uncommitted task", r.stderr)
    commit(root, "T-001 task")
    r = repo.aishore("start", "T-001")
    wt = repo.wt("T-001")
    check(r.returncode == 0 and "red on main" in r.stdout and wt.exists(),
          "start proves acceptance red, creates ../.wt/<repo>-<id>", r.stdout + r.stderr)

    acc = wt / "tests/acceptance/test_t_001.py"
    if os.geteuid() == 0:
        check(True, "locked files read-only (skipped: running as root)")
    else:
        check(not os.access(acc, os.W_OK) and not os.access(wt / ".aishore/aishore/lib.py", os.W_OK),
              "locked files and the vendored harness are read-only in the worktree")

    def edit(path: str) -> int:
        return repo.hook("guard_edit", wt, {"tool_input": {"file_path": str(wt / path)}}).returncode

    check(edit("tests/acceptance/test_t_001.py") == 2, "guard_edit blocks acceptance test")
    check(edit("aishore.toml") == 2, "guard_edit blocks harness config")
    check(edit(".aishore/aishore/gate.py") == 2, "guard_edit blocks the vendored harness")
    check(edit("src/toy/replay.py") == 2, "guard_edit blocks file outside allowlist")
    check(edit("src/toy/calc.py") == 0, "guard_edit allows allowlisted file")
    check(edit("ESCALATE.md") == 0, "guard_edit allows ESCALATE.md")
    r = repo.hook("guard_edit", root, {"tool_input": {"file_path": str(root / "aishore.toml")}})
    check(r.returncode == 0, "guard_edit is inactive on the base branch")

    def bash(cmd: str) -> int:
        return repo.hook("guard_bash", wt, {"tool_input": {"command": cmd}}).returncode

    check(bash("git push origin t/T-001") == 2, "guard_bash blocks git push")
    check(bash("sed -i 's/12/13/' tests/acceptance/test_t_001.py") == 2, "guard_bash blocks sed -i on locked file")
    check(bash("echo x > aishore.toml") == 2, "guard_bash blocks redirect into locked file")
    check(bash("pip install requests") == 2 and bash("npm install left-pad") == 2, "guard_bash blocks dependency installs")
    check(bash("git checkout main") == 2 and bash("git -c advice.detachedHead=false checkout --detach") == 2
          and bash("git -C . switch -") == 2, "guard_bash blocks branch switch, also after git global options")
    check(bash("echo 99 > .aishore/state/stop_failures") == 2, "guard_bash blocks writes to harness state")
    check(bash("git commit -qm 'push the fix'") == 0, "guard_bash allows a commit message that mentions push")
    check(bash(".aishore/bin/aishore replay update") == 2, "guard_bash blocks golden updates")
    check(bash("cat tests/acceptance/test_t_001.py 2>&1 | head") == 0, "guard_bash allows reading locked file")
    check(bash("python -m pytest -q tests/unit > /tmp/out.txt") == 0, "guard_bash allows normal commands")

    # stop hook: planning is exempt, red work is blocked twice, then allowed
    r = repo.hook("stop", wt, {"stop_hook_active": False})
    check(r.returncode == 0, "stop hook allows stopping before any change", r.stderr)
    write(wt / "PLAN.md", "## Add\nwrap\n")
    r = repo.hook("stop", wt, {"stop_hook_active": False})
    check(r.returncode == 0, "stop hook allows stopping with only PLAN.md (awaiting approval)", r.stderr)
    calc = wt / "src/toy/calc.py"
    calc.write_text(CALC + "\n\ndef wrap(x: int, n: int) -> int:\n    return 0\n")
    r = repo.hook("stop", wt, {"stop_hook_active": False})
    check(r.returncode == 2 and "red" in r.stderr, "stop hook blocks while gate is red", r.stderr)
    r = repo.hook("stop", wt, {"stop_hook_active": True})
    check(r.returncode == 2 and "ESCALATE.md" in r.stderr, "second red stop demands escalation", r.stderr)
    r = repo.hook("stop", wt, {"stop_hook_active": True})
    check(r.returncode == 0, "third red stop is allowed (loop guard)", r.stderr)
    (wt / ".aishore/state/stop_failures").unlink(missing_ok=True)

    good = CALC + "\n\ndef wrap(x: int, n: int) -> int:\n    return x % n\n"

    def diffcheck() -> subprocess.CompletedProcess:
        return repo.aishore("diffcheck", cwd=wt)

    calc.write_text(good.replace("return x % n", "return x % n  # type: ignore"))
    r = diffcheck()
    check(r.returncode == 1 and "type: ignore" in r.stdout, "diffcheck catches type: ignore", r.stdout)
    calc.write_text(good + "\n\nclass Helper:\n    pass\n")
    r = diffcheck()
    check(r.returncode == 1 and "new classes" in r.stdout, "diffcheck catches unrequested class", r.stdout)
    calc.write_text(good + "\n" + "\n".join(f"V{i} = {i}" for i in range(60)) + "\n")
    r = diffcheck()
    check(r.returncode == 1 and "exceeds budget" in r.stdout, "diffcheck catches LOC budget overrun", r.stdout)
    calc.write_text(good)
    os.chmod(acc, 0o644)
    acc.write_text(ACCEPT.replace("== 2", "== 2 or True"))
    r = diffcheck()
    check(r.returncode == 1 and "human-owned path modified" in r.stdout,
          "diffcheck catches a locked file edited behind the hooks", r.stdout)
    acc.write_text(ACCEPT)
    os.chmod(acc, 0o444)
    write(wt / "src/toy/extra.py", "X = 1\n")
    r = diffcheck()
    check(r.returncode == 1 and "outside allowlist" in r.stdout, "diffcheck catches new file outside allowlist", r.stdout)
    (wt / "src/toy/extra.py").unlink()

    calc.write_text(good.replace("        return hi\n", "        return hi - 1\n"))
    r = repo.aishore("replay", "check", cwd=wt)
    check(r.returncode == 1 and "UNEXPECTED CHANGE basic" in r.stdout, "replay catches unallowed behavior change", r.stdout)

    calc.write_text(good)
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 0 and "acceptance: 1 files" in r.stdout, "fast gate green, runs the task's acceptance test",
          r.stdout + r.stderr)
    r = repo.hook("stop", wt, {"stop_hook_active": False})
    check(r.returncode == 0, "stop hook allows a green finish", r.stderr)
    r = repo.aishore("gate", "full", cwd=wt)
    check(r.returncode == 0 and "killed" in r.stdout, "full gate green incl. replay and mutation", r.stdout + r.stderr)

    calc.write_text(CALC + "\n\ndef wrap(x: int, n: int) -> int:\n    if n <= 0:\n        raise ValueError(n)\n"
                    "    return x % n\n")
    r = repo.aishore("mutate", cwd=wt)
    check(r.returncode == 1 and "survived" in r.stdout, "mutation gate reports surviving mutants", r.stdout)
    calc.write_text(good)

    # reviewer: headless stub gets role, model, context; its findings are executed
    write(stub_dir / "review.md", REVIEW_PY)
    r = repo.aishore("review", "T-001")
    fm = root / "tasks/T-001/findings.md"
    check(r.returncode == 0 and fm.exists() and "REAL" in fm.read_text(),
          "review runs headless reviewer and executes its finding", r.stdout + r.stderr)
    write(stub_dir / "review.md", REVIEW_PY + REVIEW_PY.replace("Finding 1", "Finding 2").replace(
        "finding: 1", "finding: 2").replace("assert 0 <= wrap(3, -2) < 2", "assert wrap(5, 3) == 2")
        + REVIEW_PY.replace("Finding 1", "Finding 3").replace("finding: 1", "finding: 3").replace(
        "from toy.calc import wrap", "import toy.calc as calc").replace("assert 0 <= wrap(3, -2) < 2",
                                                                         "assert calc.wrap_around(3, 10) == 3"))
    from aishore import findings
    real, discarded, invalid = findings.run(wt, stub_dir / "review.md", stub_dir / "findings.md",
                                            tomllib.loads((root / "aishore.toml").read_text()))
    check((real, discarded, invalid) == (1, 1, 1),
          "findings: failing assertion is REAL, passing test discarded, crashing test invalid",
          (stub_dir / "findings.md").read_text())
    r = repo.aishore("adopt", "T-001", "1")
    check(r.returncode == 0 and (wt / "tests/acceptance/test_t_001_f1.py").exists(),
          "adopt promotes finding to acceptance test and syncs worktree", r.stdout + r.stderr)
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 1, "adopted finding test gates the task", r.stdout)
    calc.write_text(good.replace("return x % n", "return x % abs(n)"))
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 0 and "acceptance: 2 files" in r.stdout, "implementation passes adopted finding", r.stdout)

    f1 = wt / "tests/acceptance/test_t_001_f1.py"
    os.chmod(f1.parent, 0o755)
    f1.rename(wt / "src/toy/f1.py")
    git(wt, "add", "-A")
    r = repo.aishore("diffcheck", cwd=wt)
    check(r.returncode == 1 and "human-owned path modified: tests/acceptance/test_t_001_f1.py" in r.stdout,
          "diffcheck sees a locked test moved into src (no rename folding)", r.stdout)
    (wt / "src/toy/f1.py").rename(f1)
    git(wt, "add", "-A")
    os.chmod(f1.parent, 0o555)
    write(wt / "src/toy/café.py", "X = 1\n")
    r = repo.aishore("diffcheck", cwd=wt)
    check(r.returncode == 1 and "outside allowlist: src/toy/café.py" in r.stdout, "diffcheck reports non-ASCII paths as is",
          r.stdout)
    (wt / "src/toy/café.py").unlink()

    git(wt, "commit", "-q", "-m", "wip")
    git(wt, "checkout", "-q", "--detach")
    r = repo.aishore("merge", "T-001", "--yes", "--minutes", "1", "--caught", "", "--missing", "")
    check(r.returncode == 1 and "not t/T-001" in r.stderr, "merge refuses a worktree that left its task branch",
          r.stdout + r.stderr)
    git(wt, "checkout", "-q", "t/T-001")

    r = repo.aishore("merge", "T-001", "--yes", "--minutes", "7", "--caught", "", "--missing", "")
    check(r.returncode == 0 and "merged T-001" in r.stdout, "merge runs full gate, merges, logs, cleans up",
          r.stdout + r.stderr)
    check(not wt.exists(), "worktree removed after merge")
    log = (root / "tasks/log.csv").read_text() if (root / "tasks/log.csv").exists() else ""
    check("T-001" in log and "merged" in log, "log.csv row written", log)
    check("def wrap" in (root / "src/toy/calc.py").read_text(), "main contains the merged change")

    # brief review: counterexamples run against the brief as it is on disk
    base_calc = (root / "src/toy/calc.py").read_text()
    wrong_zero = base_calc + "\n\ndef sign(x: int) -> int:\n    return 1 if x > 0 else -1\n"
    always_one = base_calc + "\n\ndef sign(x: int) -> int:\n    return 1\n"
    write(stub_dir / "brief.md", "### Counterexample 1: zero gets -1\nViolates: sign(0) is 0\nRow to add: 0 -> 0\n"
          f"```file:src/toy/calc.py\n{wrong_zero}```\n"
          "### Counterexample 2: always 1\nViolates: negatives\nRow to add: -3 -> -1\n"
          f"```file:src/toy/calc.py\n{always_one}```\n"
          "### Counterexample 3: edits a locked file\nViolates: x\nRow to add: x\n```file:aishore.toml\nx = 1\n```\n"
          "### Question 1: what is sign(0)? 0 or error\nVERDICT: REVISE\n")
    r = repo.aishore("new", "T-002", "Add sign")
    write(root / "tasks/T-002/task.toml", TASK.format(id="T-002", title="Add sign", allow='"src/toy/calc.py"',
                                                      test="tests/acceptance/test_t_002.py"))
    write(root / "tasks/T-002/spec.md", SPEC.format(id="T-002", title="Add sign"))
    write(root / "tests/acceptance/test_t_002.py", "# AISHORE_PLACEHOLDER: review\nfrom toy.calc import sign\n\n\n"
          "def test_sign():\n    assert sign(5) == 1\n    assert sign(-3) == -1\n")
    r = repo.aishore("brief-review", "T-002")
    br = (root / "tasks/T-002/brief-review.md").read_text() if (root / "tasks/T-002/brief-review.md").exists() else ""
    check(r.returncode == 0 and "Gaps 1, caught 1, invalid 1" in br and "what is sign(0)" in br
          and "worktree" not in git(root, "worktree", "list").split("\n", 1)[-1],
          "brief-review proves a gap, credits a caught counterexample, rejects files outside allow",
          r.stdout + r.stderr + br)
    shutil.rmtree(root / "tasks/T-002")
    (root / "tests/acceptance/test_t_002.py").unlink()

    # a second task's red acceptance test does not gate main; merged tasks' tests do
    repo.task("T-002", "Add sign", '"src/toy/calc.py"', "tests/acceptance/test_t_002.py",
              "from toy.calc import sign\n\n\ndef test_sign():\n    assert sign(5) == 1\n    assert sign(-3) == -1\n")
    r = repo.aishore("gate", "fast")
    check(r.returncode == 0 and "acceptance: 2 files" in r.stdout,
          "main gate runs merged tasks' tests and ignores the open task's red test", r.stdout)

    # headless run against the stub claude
    write(stub_dir / "impl", (root / "src/toy/calc.py").read_text() +
          "\n\ndef sign(x: int) -> int:\n    return 1 if x > 0 else -1\n")
    write(stub_dir / "fix", (root / "src/toy/calc.py").read_text() +
          "\n\ndef sign(x: int) -> int:\n    if x > 0:\n        return 1\n    if x < 0:\n        return -1\n    return 0\n")
    write(stub_dir / "review.md", "### Finding 1: sign(0) is wrong\nSeverity: high\nWhy: zero has no sign.\n"
          "```python\n# finding: 1\nfrom toy.calc import sign\n\ndef test_zero():\n    assert sign(0) == 0\n```\n"
          "VERDICT: FIX\n")
    run_env = dict(env, STUB_TARGET="src/toy/calc.py", CLAUDECODE="1")
    r = repo.aishore("run", "T-002", env=run_env)
    wt2 = repo.wt("T-002")
    fm2 = (root / "tasks/T-002/findings.md").read_text() if (root / "tasks/T-002/findings.md").exists() else ""
    check(r.returncode == 0 and "ready for you" in r.stdout and "plan review 1: REVISE" in r.stdout
          and "plan review 2: APPROVE" in r.stdout, "run: plan, REVISE loop, approval, build, review",
          r.stdout + r.stderr)
    check("discard: test passes" in fm2 and "still failing" not in r.stdout,
          "run: proven finding sent back once and now passes", fm2 + r.stdout)
    check((stub_dir / "implementer_calls").read_text() == "4" and
          (wt2 / ".aishore/state/session").read_text() == "stub-session",
          "run: implementer resumed one session across plan, revise, build, fix")
    r = repo.aishore("run", "T-002", env=run_env)
    check(r.returncode == 0 and (stub_dir / "implementer_calls").read_text() == "4",
          "run: re-run resumes from state without new implementer calls", r.stdout + r.stderr)
    r = repo.aishore("merge", "T-002", "--yes", "--minutes", "1", "--caught", "", "--missing", "")
    check(r.returncode == 0 and not wt2.exists(), "merge after headless run", r.stdout + r.stderr)

    # the reviewer never approves the plan: the run stops for you, and --approve-plan resumes it
    repo.task("T-003", "Add double", '"src/toy/calc.py"', "tests/acceptance/test_t_003.py",
              "from toy.calc import double\n\n\ndef test_double():\n    assert double(4) == 8\n")
    write(stub_dir / "impl", (root / "src/toy/calc.py").read_text() + "\n\ndef double(x: int) -> int:\n    return 2 * x\n")
    write(stub_dir / "review.md", "No defects found.\nVERDICT: PASS\n")
    wt_state = repo.wt("T-003") / ".aishore/state"
    rev_env = dict(run_env, STUB_PLAN="revise")
    r = repo.aishore("run", "T-003", env=rev_env)
    check(r.returncode == 1 and "--approve-plan" in r.stderr, "run: two REVISE verdicts stop for the human",
          r.stdout + r.stderr)
    r = repo.aishore("run", "T-003", "--approve-plan", env=rev_env)
    check(r.returncode == 0 and "plan approved by you" in r.stdout and "plan review" not in r.stdout
          and "ready for you" in r.stdout and (wt_state / "built").exists(),
          "run --approve-plan builds without another plan review", r.stdout + r.stderr)
    r = repo.aishore("abandon", "T-003", "selftest")
    check(r.returncode == 0 and not repo.wt("T-003").exists(), "abandon removes the worktree", r.stdout + r.stderr)


def flat_part(tmp: Path, env: dict, py: str) -> None:
    """A flat-layout package with a module named like a stdlib module must not shadow the stdlib."""
    root = tmp / "flatrepo"
    root.mkdir()
    new_repo(root)
    write(root / "pyproject.toml", '[project]\nname = "mypkg"\nversion = "0"\n')
    write(root / "mypkg/__init__.py", "")
    write(root / "mypkg/types.py", "from dataclasses import dataclass\n\n\n@dataclass\nclass Point:\n    x: int\n")
    write(root / "tests/test_types.py", "from mypkg.types import Point\n\n\ndef test_point():\n    assert Point(1).x == 1\n")
    commit(root, "init")
    r = run([*INSTALLER, str(root)], root, env)
    repo = Repo(root, env)
    set_config(root, **{"commands.tests": f'"{py} -m pytest -q -p no:cacheprovider tests"'})
    commit(root, "install aishore")
    r = repo.aishore("gate", "fast")
    check(r.returncode == 0 and tomllib.loads((root / "aishore.toml").read_text())["src"] == ["mypkg"],
          "flat layout: package root on src, stdlib not shadowed, gate green", r.stdout + r.stderr)


NODE_CALC = "export function clamp(x, lo, hi) {\n  return Math.min(hi, Math.max(lo, x));\n}\n"
NODE_ACCEPT = ('import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
               'import { wrap } from "../../src/calc.js";\n\ntest("wrap", () => {\n'
               '  assert.equal(wrap(12, 10), 2);\n  assert.equal(wrap(-1, 10), 9);\n});\n')
NODE_GOOD = NODE_CALC + "\nexport function wrap(x, n) {\n  return ((x % n) + n) % n;\n}\n"


def node_part(tmp: Path, env: dict, stub_dir: Path) -> None:
    root = tmp / "noderepo"
    root.mkdir()
    new_repo(root)
    write(root / "package.json", json.dumps({"name": "toy", "type": "module",
                                             "scripts": {"test": "node --test"}}, indent=2))
    write(root / "src/calc.js", NODE_CALC)
    write(root / "tests/unit/calc.test.js", 'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
          'import { clamp } from "../../src/calc.js";\n\ntest("clamp", () => assert.equal(clamp(12, 0, 10), 10));\n')
    commit(root, "init")
    r = run([*INSTALLER, str(root)], root, env)
    repo = Repo(root, env)
    cfg = tomllib.loads((root / "aishore.toml").read_text()) if (root / "aishore.toml").exists() else {}
    check(r.returncode == 0 and cfg.get("acceptance", {}).get("cmd") == "node --test {tests}"
          and cfg["acceptance"]["path"].endswith(".accept.js") and cfg["commands"]["tests"] == "npm test --silent",
          "node: install detects node profile and runner", r.stdout + r.stderr)
    set_config(root, **{"commands.setup": '""'})
    commit(root, "install aishore")
    repo.task("T-001", "Add wrap", '"src/calc.js"', "tests/acceptance/t_001.accept.js", NODE_ACCEPT)
    r = repo.aishore("start", "T-001")
    wt = repo.wt("T-001")
    check(r.returncode == 0 and "red on main" in r.stdout, "node: start proves acceptance red", r.stdout + r.stderr)
    r = repo.aishore("gate", "fast")
    check(r.returncode == 0, "node: npm test on main does not discover the open task's red acceptance test",
          r.stdout + r.stderr)
    code = repo.hook("guard_edit", wt, {"tool_input": {"file_path": str(wt / "tests/acceptance/t_001.accept.js")}})
    check(code.returncode == 2, "node: guard_edit blocks acceptance test")
    calc = wt / "src/calc.js"
    calc.write_text(NODE_GOOD.replace("return ((x", "// eslint-disable-next-line\n  return ((x"))
    r = repo.aishore("diffcheck", cwd=wt)
    check(r.returncode == 1 and "eslint-disable added" in r.stdout, "node: diffcheck catches eslint-disable", r.stdout)
    calc.write_text(NODE_GOOD + "\nexport class Helper {}\n")
    r = repo.aishore("diffcheck", cwd=wt)
    check(r.returncode == 1 and "Helper" in r.stdout, "node: diffcheck catches a new class", r.stdout)
    calc.write_text(NODE_GOOD)
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 0, "node: fast gate green", r.stdout + r.stderr)
    write(stub_dir / "review.md",
          "### Finding 1: zero modulus\nSeverity: low\nWhy: n=0.\n```javascript\n// finding: 1\n"
          'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
          'import { wrap } from "../../src/calc.js";\ntest("zero", () => assert.throws(() => wrap(1, 0)));\n```\n'
          "### Finding 2: fine\nSeverity: low\nWhy: none.\n```javascript\n// finding: 2\n"
          'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
          'import { wrap } from "../../src/calc.js";\ntest("ok", () => assert.equal(wrap(5, 3), 2));\n```\n'
          "VERDICT: FIX\n")
    r = repo.aishore("review", "T-001")
    fm = (root / "tasks/T-001/findings.md").read_text() if (root / "tasks/T-001/findings.md").exists() else ""
    check(r.returncode == 0 and "Real 1, discarded 1" in fm, "node: findings REAL and discard with node --test",
          r.stdout + r.stderr + fm)
    r = repo.aishore("merge", "T-001", "--yes", "--minutes", "1", "--caught", "", "--missing", "")
    check(r.returncode == 0 and "wrap" in (root / "src/calc.js").read_text(), "node: merge", r.stdout + r.stderr)


def vitest_part(tmp: Path, env: dict) -> None:
    root = tmp / "vitestrepo"
    root.mkdir()
    new_repo(root)
    write(root / "package.json",
          json.dumps({"name": "vt", "type": "module", "scripts": {"test": "vitest run"}}, indent=2))
    r = run(["npm", "install", "--silent", "--no-audit", "--no-fund", "--save-dev", "vitest@4"], root, env)
    if r.returncode:
        print(f"SKIP  vitest profile (npm install failed: {r.stderr.strip()[-200:]})")
        return
    write(root / ".gitignore", "node_modules\n")
    write(root / "tsconfig.json", '{"compilerOptions": {"strict": true, "module": "esnext", "moduleResolution": "bundler"}}\n')
    write(root / "vitest.config.ts", 'import { defineConfig } from "vitest/config";\n\n'
          'export default defineConfig({ test: { include: ["src/**/*.test.ts"] } });\n')
    write(root / "src/calc.ts", "export const add = (a: number, b: number): number => a + b;\n")
    write(root / "src/calc.test.ts", 'import { expect, test } from "vitest";\nimport { add } from "./calc";\n\n'
          'test("add", () => expect(add(1, 2)).toBe(3));\n')
    commit(root, "init")
    r = run([*INSTALLER, str(root)], root, env)
    repo = Repo(root, env)
    cfg = tomllib.loads((root / "aishore.toml").read_text()) if (root / "aishore.toml").exists() else {}
    check(r.returncode == 0 and "runners/vitest.config.mjs" in cfg.get("acceptance", {}).get("cmd", ""),
          "vitest: install selects the vitest runner", r.stdout + r.stderr)
    set_config(root, **{"commands.setup": '""', "commands.types": '""'})
    commit(root, "install aishore")
    repo.task("T-001", "Add sub", '"src/calc.ts"', "tests/acceptance/t_001.accept.ts",
              'import { expect, test } from "vitest";\nimport * as calc from "../../src/calc";\n\n'
              'test("sub", () => expect((calc as any).sub?.(5, 3)).toBe(2));\n')
    r = repo.aishore("start", "T-001")
    wt = repo.wt("T-001")
    check(r.returncode == 0 and "red on main" in r.stdout,
          "vitest: acceptance test outside the config include is collected and red", r.stdout + r.stderr)
    if not wt.exists():
        return
    os.symlink(root / "node_modules", wt / "node_modules")
    (wt / "src/calc.ts").write_text((root / "src/calc.ts").read_text() +
                                    "export const sub = (a: number, b: number): number => a - b;\n")
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 0 and "acceptance: 1 files" in r.stdout, "vitest: gate green with unit and acceptance tests",
          r.stdout + r.stderr)


def generic_part(tmp: Path, env: dict) -> None:
    root = tmp / "shrepo"
    root.mkdir()
    new_repo(root)
    write(root / "bin/greet", '#!/usr/bin/env bash\necho "hello"\n')
    commit(root, "init")
    r = run([*INSTALLER, str(root)], root, env)
    repo = Repo(root, env)
    check(r.returncode == 0 and "generic profile" in (root / "aishore.toml").read_text(),
          "generic: install detects generic profile", r.stdout + r.stderr)
    set_config(root, src='["bin"]')
    write(root / "tasks/T-001/task.toml", TASK.format(id="T-001", title="Greet by name", allow='"bin/greet"',
                                                      test="tests/acceptance/test_t_001.sh"))
    write(root / "tasks/T-001/spec.md", SPEC.format(id="T-001", title="Greet by name"))
    write(root / "tests/acceptance/test_t_001.sh", '#!/usr/bin/env bash\nset -e\n[ "$(bash bin/greet Ann)" = "hello Ann" ]\n')
    git(root, "add", "tasks", "tests", "aishore.toml")
    git(root, "commit", "-q", "-m", "task without the harness")
    r = repo.aishore("start", "T-001")
    check(r.returncode == 1 and "without hooks" in r.stderr and not repo.wt("T-001").exists(),
          "generic: start refuses while the harness is uncommitted", r.stdout + r.stderr)
    commit(root, "install aishore")
    r = repo.aishore("start", "T-001")
    wt = repo.wt("T-001")
    check(r.returncode == 0 and "red on main" in r.stdout, "generic: start proves shell acceptance test red",
          r.stdout + r.stderr)
    (wt / "bin/greet").write_text('#!/usr/bin/env bash\n# shellcheck disable=SC2086\necho "hello $1"\n')
    r = repo.aishore("gate", "fast", cwd=wt)
    check(r.returncode == 1 and "shellcheck disable added" in r.stdout, "generic: diffcheck catches shellcheck disable",
          r.stdout)
    (wt / "bin/greet").write_text('#!/usr/bin/env bash\necho "hello $1"\n')
    r = repo.aishore("merge", "T-001", "--yes", "--minutes", "1", "--caught", "", "--missing", "")
    check(r.returncode == 0 and "$1" in (root / "bin/greet").read_text(), "generic: gate and merge", r.stdout + r.stderr)


def main(argv: list[str] | None = None) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="aishore-selftest-"))
    py = sys.executable
    stub_dir = tmp / "stub"
    stub_bin = tmp / "stubbin"
    write(stub_bin / "claude", STUB)
    os.chmod(stub_bin / "claude", 0o755)
    stub_dir.mkdir()
    path = os.pathsep.join([str(stub_bin), str(Path(py).parent), os.environ.get("PATH", "")])
    env = dict(os.environ, STUB_DIR=str(stub_dir), PYTHONPATH=str(SOURCE), PATH=path,
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("AISHORE_TASK", None)
    env.pop("AISHORE_BRANCH", None)
    try:
        python_part(tmp, env, py, stub_dir)
        if shutil.which("node"):
            node_part(tmp, env, stub_dir)
        else:
            print("SKIP  node profile (node not installed)")
        if shutil.which("npm"):
            vitest_part(tmp, env)
        else:
            print("SKIP  vitest profile (npm not installed)")
        generic_part(tmp, env)
        flat_part(tmp, env, py)
    finally:
        for dirpath, dirnames, filenames in os.walk(tmp):
            for n in dirnames + filenames:
                p = Path(dirpath) / n
                if not p.is_symlink():
                    os.chmod(p, p.stat().st_mode | 0o200)
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [label for ok, label in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
