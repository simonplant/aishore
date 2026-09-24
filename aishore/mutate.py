"""Mutation gate on changed Python lines only. Proves the tests constrain the new code.

Copies the checkout to a temp dir, applies one AST mutation at a time to lines changed
since the merge base, and runs the mutation test command. A mutant is killed when the
tests fail or time out. The kill ratio must meet the task's mutation_min_kill.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from aishore import lib, tasks

CMP = {ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt, ast.Eq: ast.NotEq,
       ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}
BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
BOOL = {ast.And: ast.Or, ast.Or: ast.And}
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv", "node_modules",
                                ".pytest_cache", ".ruff_cache", ".mypy_cache", "state")


def sites(tree: ast.AST, lines: set[int]) -> list[tuple[ast.AST, str]]:
    out = []
    for node in ast.walk(tree):
        if getattr(node, "lineno", None) not in lines:
            continue
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in CMP:
            out.append((node, "flip comparison"))
        elif isinstance(node, ast.BinOp) and type(node.op) in BIN:
            out.append((node, "swap operator"))
        elif isinstance(node, ast.BoolOp) and type(node.op) in BOOL:
            out.append((node, "swap and/or"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            out.append((node, "flip bool"))
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float):
            out.append((node, "constant +1"))
        elif isinstance(node, ast.If):
            out.append((node, "negate condition"))
        elif isinstance(node, ast.Return) and node.value is not None and not (
                isinstance(node.value, ast.Constant) and node.value.value is None):
            out.append((node, "return None"))
    return out


def apply(node: ast.AST, kind: str) -> None:
    if kind == "flip comparison":
        node.ops = [CMP[type(node.ops[0])]()]
    elif kind == "swap operator":
        node.op = BIN[type(node.op)]()
    elif kind == "swap and/or":
        node.op = BOOL[type(node.op)]()
    elif kind == "flip bool":
        node.value = not node.value
    elif kind == "constant +1":
        node.value = node.value + 1
    elif kind == "negate condition":
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
    elif kind == "return None":
        node.value = ast.Constant(value=None)


def changed_lines(root: Path, base: str, path: str, untracked: bool) -> set[int]:
    if untracked:
        return set(range(1, len((root / path).read_text().splitlines()) + 1))
    lines: set[int] = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", lib.sh("git", "diff", "-U0", base, "--", path, cwd=root), re.M):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        lines.update(range(start, start + count))
    return lines


def run_tests(cmd: str, cwd: Path, env: dict, timeout: float) -> tuple[bool, float]:
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        return r.returncode == 0, time.monotonic() - t0
    except subprocess.TimeoutExpired:
        return False, time.monotonic() - t0


def main() -> int:
    root = lib.repo_root()
    cfg = lib.config(root)
    tid = lib.task_id(root)
    if not tid:
        print("mutation: not a task branch, skipped")
        return 0
    task = tasks.load(root, tid)
    if task.mutation_min_kill is None:
        print(f"mutation: off for tier {task.tier}")
        return 0
    mcfg = cfg.get("mutation", {})
    parts = [mcfg.get("tests") or cfg.get("commands", {}).get("tests", "")]
    suite = lib.acceptance_suite(root, cfg)
    if suite:
        parts.append(lib.acceptance_cmd(cfg, suite))
    cmd = " && ".join(f"({c})" for c in parts if c)
    if not cmd:
        print("mutation: no test command configured")
        return 1
    base = lib.merge_base(root, cfg)
    changed, untracked = lib.changed_files(root, base)
    targets = sorted(f for f in changed | untracked if lib.in_src(f, cfg) and f.endswith(".py") and (root / f).exists())

    candidates: list[tuple[str, int, str, int, str]] = []
    originals: dict[str, str] = {}
    for f in targets:
        text = (root / f).read_text()
        originals[f] = text
        lines = changed_lines(root, base, f, f in untracked)
        for i, (node, kind) in enumerate(sites(ast.parse(text), lines)):
            candidates.append((f, i, kind, node.lineno, ast.unparse(node).splitlines()[0][:70]))
    if not candidates:
        print("mutation: no mutable changed Python lines")
        return 0
    cap = int(mcfg.get("max_mutants", 40))
    if len(candidates) > cap:
        step = len(candidates) / cap
        candidates = [candidates[int(i * step)] for i in range(cap)]

    tmp = Path(tempfile.mkdtemp(prefix="aishore-mut-"))
    try:
        copy = tmp / "repo"
        shutil.copytree(root, copy, ignore=IGNORE, symlinks=True)
        for dirpath, dirnames, filenames in os.walk(copy):
            for name in dirnames + filenames:
                p = Path(dirpath) / name
                if not p.is_symlink():
                    os.chmod(p, p.stat().st_mode | stat.S_IWUSR)
        env = lib.env(copy, cfg)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        ok, baseline = run_tests(cmd, copy, env, timeout=1800)
        if not ok:
            print("mutation: tests fail before mutation, fix the suite first")
            return 1
        timeout = max(10.0, float(mcfg.get("timeout_factor", 5)) * baseline)
        survivors = []
        for f, idx, kind, line, desc in candidates:
            tree = ast.parse(originals[f])
            node, _ = sites(tree, changed_lines(root, base, f, f in untracked))[idx]
            apply(node, kind)
            ast.fix_missing_locations(tree)
            (copy / f).write_text(ast.unparse(tree))
            passed, _ = run_tests(cmd, copy, env, timeout)
            (copy / f).write_text(originals[f])
            if passed:
                survivors.append(f"{f}:{line} {kind}: {desc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(candidates)
    killed = total - len(survivors)
    ratio = killed / total
    report = [f"mutation: killed {killed}/{total} ({ratio:.0%}), required {task.mutation_min_kill:.0%}"]
    report += [f"  survived: {s}" for s in survivors[:20]]
    (root / lib.STATE).mkdir(parents=True, exist_ok=True)
    (root / lib.STATE / "mutation.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    if ratio < task.mutation_min_kill:
        print("mutation FAILED: add tests that fail on the surviving mutants")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
