"""Turn reviewer findings into evidence: each finding's test must fail on the branch to count."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from aishore import lib

BLOCK = re.compile(r"```[^\n]*\n\s*(?:#|//|--)\s*finding:\s*(\d+)\s*\n(.*?)```", re.S)
TITLE = re.compile(r"^###\s*Finding\s+(\d+):\s*(.+)$", re.M)
REVIEW_DIR = "tests/_review"


def run(wt: Path, review: Path, out: Path, cfg: dict) -> tuple[int, int, int]:
    text = review.read_text()
    titles = dict(TITLE.findall(text))
    blocks = BLOCK.findall(text)
    tmp = wt / REVIEW_DIR
    tmp.mkdir(parents=True, exist_ok=True)
    env = lib.env(wt, cfg)
    rows, real, discarded, invalid = [], 0, 0, 0
    try:
        for n, code in blocks:
            f = tmp / Path(lib.acceptance_path(cfg, f"finding_{n}")).name
            f.write_text(code)
            try:
                r = subprocess.run(lib.acceptance_cmd(cfg, [f.relative_to(wt)]), shell=True, cwd=wt, env=env,
                                   capture_output=True, text=True, timeout=300)
                code_, output = r.returncode, r.stdout + r.stderr
            except subprocess.TimeoutExpired:
                code_, output = -1, ""
            if code_ == 0:
                verdict, discarded = "discard: test passes", discarded + 1
            elif lib.proves(cfg, wt, output, code_, f.relative_to(wt).as_posix()):
                verdict, real = "REAL: test fails on branch", real + 1
            elif lib.test_failed(cfg, code_):
                verdict, invalid = "invalid: the test itself errored, no failed assertion", invalid + 1
            else:
                verdict, invalid = f"invalid: runner exit {code_}", invalid + 1
            rows.append(f"| {n} | {titles.get(n, '').strip()} | {verdict} |")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    verdict_line = re.search(r"VERDICT:\s*(\w+)", text)
    lines = ["# Review findings", "",
             f"Reviewer verdict: {verdict_line.group(1) if verdict_line else 'missing'}", "",
             "| # | Finding | Evidence |", "|---|---|---|", *rows, "",
             f"Real {real}, discarded {discarded}, invalid {invalid}. Findings without a test were ignored."]
    out.write_text("\n".join(lines) + "\n")
    return real, discarded, invalid


def verdicts(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    return re.findall(r"^\| (\d+) \| .*? \| (.+?) \|$", path.read_text(), re.M)


def real_numbers(path: Path) -> list[str]:
    return [n for n, v in verdicts(path) if v.startswith("REAL")]
