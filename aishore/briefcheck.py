"""Brief review: counterexample implementations prove where the acceptance tests are too weak.

Each counterexample is written into a scratch worktree of the base branch that carries the
brief as it is on disk. The acceptance tests run there: a pass proves a gap in the brief.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from aishore import lib

SECTION = re.compile(r"^###\s*Counterexample\s+(\d+):\s*(.+?)$(.*?)(?=^###\s|\Z)", re.M | re.S)
FILE = re.compile(r"```file:\s*([^\n`]+)\n(.*?)```", re.S)
QUESTION = re.compile(r"^###\s*Question\s+\d+:\s*(.+)$", re.M)


def scratch(root: Path, cfg: dict, paths: list[str]) -> Path:
    """Detached worktree of HEAD with the brief's files copied in from the working tree."""
    tmp = Path(tempfile.mkdtemp(prefix="aishore-brief-")) / "repo"
    lib.sh("git", "worktree", "add", "-q", "--detach", str(tmp), "HEAD", cwd=root)
    for rel in paths:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, tmp / rel, dirs_exist_ok=True)
        elif src.is_file():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, tmp / rel)
    for dep in ("node_modules", ".venv", "venv"):
        if (root / dep).is_dir() and not (tmp / dep).exists():
            os.symlink(root / dep, tmp / dep)
    return tmp


def drop(root: Path, tmp: Path) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", str(tmp)], cwd=root, capture_output=True)
    shutil.rmtree(tmp.parent, ignore_errors=True)


def run(root: Path, cfg: dict, task, review: Path, out: Path) -> tuple[int, int, int]:
    text = review.read_text()
    tests = list(task.acceptance_tests)
    rows, proven, caught, invalid = [], 0, 0, 0
    for n, title, body in SECTION.findall(text):
        files = FILE.findall(body)
        rel_files = [(p.strip(), content) for p, content in files]
        bad = [p for p, _ in rel_files if lib.relpath(root, p) is None or not lib.match(p, task.allow)]
        if not rel_files or bad or not tests:
            invalid += 1
            why = f"files outside allow: {bad}" if bad else "no files" if not rel_files else "task has no acceptance tests"
            rows.append(f"| {n} | {title.strip()} | invalid: {why} |")
            continue
        tmp = scratch(root, cfg, [f"tasks/{task.id}", *tests])
        try:
            for p, content in rel_files:
                (tmp / p).parent.mkdir(parents=True, exist_ok=True)
                (tmp / p).write_text(content)
            try:
                r = subprocess.run(lib.acceptance_cmd(cfg, tests), shell=True, cwd=tmp, env=lib.env(tmp, cfg),
                                   capture_output=True, text=True, timeout=600)
                code = r.returncode
            except subprocess.TimeoutExpired:
                code = -1
        finally:
            drop(root, tmp)
        if code == 0:
            proven += 1
            rows.append(f"| {n} | {title.strip()} | GAP: acceptance tests pass this wrong implementation |")
        elif lib.test_failed(cfg, code):
            caught += 1
            rows.append(f"| {n} | {title.strip()} | caught: acceptance tests fail it |")
        else:
            invalid += 1
            rows.append(f"| {n} | {title.strip()} | invalid: runner exit {code} |")
    questions = QUESTION.findall(text)
    verdict = re.search(r"VERDICT:\s*(\w+)", text)
    lines = ["# Brief review", "", f"Reviewer verdict: {verdict.group(1) if verdict else 'missing'}", "",
             "| # | Counterexample | Evidence |", "|---|---|---|", *rows, "",
             f"Gaps {proven}, caught {caught}, invalid {invalid}. For each GAP, add the reviewer's 'Row to add' "
             "to the spec and a test for it (see brief-review-raw.md).", "", "## Open questions", "",
             *([f"- {q.strip()}" for q in questions] or ["- none"])]
    out.write_text("\n".join(lines) + "\n")
    return proven, caught, invalid
