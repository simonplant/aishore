"""Entropy snapshot appended to entropy.csv: size, complexity, dependencies, dead code.

Size covers every tracked file under the src roots. Complexity and dead code cover Python only.
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import json
import shutil
import subprocess
import sys
import tomllib

from aishore import lib

BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.Assert,
            ast.comprehension, ast.match_case)


def complexity(fn: ast.AST) -> int:
    c = 1
    for n in ast.walk(fn):
        if isinstance(n, BRANCHES):
            c += 1
        elif isinstance(n, ast.BoolOp):
            c += len(n.values) - 1
    return c


def dependencies(root) -> int:
    n = 0
    pp, pj = root / "pyproject.toml", root / "package.json"
    if pp.exists():
        n += len(tomllib.loads(pp.read_text()).get("project", {}).get("dependencies", []))
    if pj.exists():
        n += len(json.loads(pj.read_text()).get("dependencies", {}))
    return n


def main() -> int:
    root = lib.repo_root()
    cfg = lib.config(root)
    files = [f for f in lib.sh(*lib.LS, cwd=root).splitlines() if lib.in_src(f, cfg)]
    loc, funcs = 0, []
    for f in files:
        try:
            text = (root / f).read_text()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        loc += sum(1 for line in text.splitlines() if line.strip())
        if f.endswith(".py"):
            funcs += [complexity(n) for n in ast.walk(ast.parse(text))
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    dead = ""
    py_roots = [r.rstrip("/") or "." for r in lib.src_roots(cfg)]
    if shutil.which("vulture") and any(f.endswith(".py") for f in files):
        r = subprocess.run(["vulture", *py_roots, "--min-confidence", "80"], cwd=root, capture_output=True, text=True)
        dead = len([x for x in r.stdout.splitlines() if x.strip()])
    row = {
        "date": dt.date.today().isoformat(), "files": len(files), "loc": loc, "py_functions": len(funcs),
        "complexity_avg": round(sum(funcs) / len(funcs), 2) if funcs else 0,
        "complexity_max": max(funcs, default=0), "functions_over_10": sum(1 for c in funcs if c > 10),
        "dependencies": dependencies(root), "dead_code": dead,
    }
    path = root / "entropy.csv"
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(", ".join(f"{k}={v}" for k, v in row.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
