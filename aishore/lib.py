"""Shared helpers: repo root, config, task lookup, ownership, environment."""
from __future__ import annotations

import csv
import fnmatch
import os
import shlex
import stat
import subprocess
import sys
import tomllib
from pathlib import Path

PKG_PARENT = Path(__file__).resolve().parent.parent
CONFIG = "aishore.toml"
TASK_PREFIX = "t/"
SCRATCH = ("ESCALATE.md", "PLAN.md")
STATE = ".aishore/state"
PLACEHOLDER = "AISHORE_PLACEHOLDER"
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "state", ".pytest_cache",
             ".ruff_cache", ".mypy_cache", "dist", "build", "target"}
# Variables a parent Claude Code session sets that would confuse a nested `claude` process.
NESTED_ENV = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_SSE_PORT")


class HarnessError(Exception):
    pass


def sh(*args: str, cwd: Path | None = None, check: bool = True, env: dict | None = None) -> str:
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise HarnessError(f"{' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r.stdout


def repo_root(start: Path | None = None) -> Path:
    if start is None:
        env = os.environ.get("CLAUDE_PROJECT_DIR")
        start = Path(env) if env else Path.cwd()
    return Path(sh("git", "rev-parse", "--show-toplevel", cwd=start).strip())


def config(root: Path) -> dict:
    path = root / CONFIG
    if not path.exists():
        raise HarnessError(f"missing {path}; run `aishore install` in the repo root")
    return tomllib.loads(path.read_text())


def branch(root: Path) -> str:
    return os.environ.get("AISHORE_BRANCH") or sh("git", "branch", "--show-current", cwd=root).strip()


def task_id(root: Path) -> str | None:
    """Task id from AISHORE_TASK, else from a t/<id> branch. None means not a task context."""
    if os.environ.get("AISHORE_TASK"):
        return os.environ["AISHORE_TASK"]
    b = branch(root)
    return b[len(TASK_PREFIX):] if b.startswith(TASK_PREFIX) else None


def base_ref(root: Path, cfg: dict) -> str:
    name = cfg.get("base", "main")
    for ref in (name, f"origin/{name}"):
        ok = subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=root,
                            capture_output=True).returncode == 0
        if ok:
            return ref
    raise HarnessError(f"base branch '{name}' not found")


def merge_base(root: Path, cfg: dict) -> str:
    return sh("git", "merge-base", "HEAD", base_ref(root, cfg), cwd=root).strip()


def match(path: str, patterns) -> str | None:
    for pat in patterns:
        if fnmatch.fnmatch(path, pat):
            return pat
    return None


def relpath(root: Path, target: str) -> str | None:
    p = Path(target)
    p = p if p.is_absolute() else root / p
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def src_roots(cfg: dict) -> list[str]:
    """Production code roots as path prefixes. "." means the whole repository."""
    roots = cfg.get("src", ["src"])
    roots = [roots] if isinstance(roots, str) else roots
    return ["" if r.strip("/") in ("", ".") else r.strip("/") + "/" for r in roots]


def in_src(path: str, cfg: dict) -> bool:
    return any(path.startswith(r) for r in src_roots(cfg))


def changed_files(root: Path, base: str) -> tuple[set[str], set[str]]:
    """(tracked files changed vs base including working tree, untracked files)."""
    changed = set(sh("git", "diff", "--name-only", base, cwd=root).splitlines())
    untracked = set(sh("git", "ls-files", "--others", "--exclude-standard", cwd=root).splitlines())
    return changed - {""}, untracked - {""}


def exists_in(root: Path, ref: str, path: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=root,
                          capture_output=True).returncode == 0


def worktree_path(root: Path, cfg: dict, tid: str) -> Path:
    return (root / cfg.get("worktree_root", "../.wt") / f"{root.name}-{tid}").resolve()


def env(root: Path, cfg: dict) -> dict:
    """Environment that imports the harness and this checkout's code, even with an install elsewhere."""
    e = dict(os.environ)
    parts = [str(PKG_PARENT)] + [str(root / r) for r in src_roots(cfg) if r] + [str(root)]
    if e.get("PYTHONPATH"):
        parts.append(e["PYTHONPATH"])
    e["PYTHONPATH"] = os.pathsep.join(parts)
    return e


def harness(module: str, *args: str) -> list[str]:
    return [sys.executable, "-m", f"aishore.{module}", *args]


def acceptance_cmd(cfg: dict, tests) -> str:
    return cfg["acceptance"]["cmd"].replace("{tests}", shlex.join(str(t) for t in tests))


def test_failed(cfg: dict, code: int) -> bool:
    """True when the runner's exit code means an assertion failed, not a crash or a collection error."""
    codes = cfg["acceptance"].get("fail_codes", [])
    return code in codes if codes else code > 0


def tests_empty(cfg: dict, code: int) -> bool:
    """True when the runner's exit code means it found no tests."""
    return code in cfg["acceptance"].get("empty_codes", [])


def acceptance_path(cfg: dict, name: str) -> str:
    return cfg["acceptance"]["path"].replace("{name}", name)


def slug(tid: str) -> str:
    return tid.lower().replace("-", "_")


def task_tests(root: Path, cfg: dict, tid: str) -> list[str]:
    """Acceptance tests of one task: those listed in task.toml plus adopted finding tests."""
    tf = root / "tasks" / tid / "task.toml"
    listed = tomllib.loads(tf.read_text()).get("acceptance_tests", []) if tf.exists() else []
    adopted = sorted(p.relative_to(root).as_posix()
                     for p in root.glob(acceptance_path(cfg, f"{slug(tid)}_f*")) if p.is_file())
    return [t for t in dict.fromkeys([*listed, *adopted]) if (root / t).is_file()]


def merged_ids(root: Path) -> set[str]:
    """Tasks whose last logged outcome is merged. Their acceptance tests guard main from then on."""
    log = root / "tasks" / "log.csv"
    last: dict[str, str] = {}
    if log.exists():
        for row in csv.DictReader(log.open()):
            last[row["id"]] = row["outcome"]
    return {k for k, v in last.items() if v == "merged"}


def acceptance_suite(root: Path, cfg: dict) -> list[str]:
    """Acceptance tests that must pass here: every merged task's, plus the current task's.

    Tests of tasks still open elsewhere are red by design and never gate this checkout.
    """
    ids = merged_ids(root) | ({task_id(root)} - {None})
    return [t for tid in sorted(ids) for t in task_tests(root, cfg, tid)]


def comment(path: str) -> str:
    return "#" if Path(path).suffix in (".py", ".sh", ".bash", ".rb", ".toml", ".yaml", ".yml") else "//"


def set_locked(root: Path, cfg: dict, locked: bool) -> int:
    """Remove (locked=True) or restore write bits on human-owned paths. Returns paths touched."""
    patterns = cfg["ownership"]["locked"]
    dir_patterns = [p for p in patterns if p.endswith("/**")]
    touched = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        here = Path(dirpath)
        rel_dir = here.relative_to(root).as_posix()
        targets: list[tuple[Path, str | None]] = [
            (here / f, f if rel_dir == "." else f"{rel_dir}/{f}") for f in filenames
        ]
        if rel_dir != "." and match(f"{rel_dir}/__probe__", dir_patterns):
            targets.append((here, None))
        for path, rel in targets:
            if path.is_symlink() or (rel is not None and not match(rel, patterns)):
                continue
            mode = path.stat().st_mode
            new = mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) if locked else mode | stat.S_IWUSR
            if new != mode:
                os.chmod(path, new)
                touched += 1
    return touched
