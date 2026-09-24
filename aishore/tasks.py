"""Task schema and validation. The schema is also published as scaffold/task.schema.json.

  aishore validate T-042
"""
from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from aishore import lib

KINDS = ("feature", "fix", "refactor", "delete", "test")
TIER_KILL = {1: 0.8, 2: 0.6, 3: None}
SECTIONS = ("## Intent", "## Interface", "## Acceptance", "## Invariants", "## Out of scope")
KEYS = {"id", "title", "tier", "kind", "allow", "acceptance_tests", "loc_budget", "max_new_files",
        "max_new_classes", "replay_may_change", "mutation_min_kill", "notes"}
ID = re.compile(r"T-\d{3,}")


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    tier: int
    kind: str
    allow: tuple[str, ...]
    acceptance_tests: tuple[str, ...]
    loc_budget: int
    max_new_files: int
    max_new_classes: int
    replay_may_change: tuple[str, ...]
    mutation_min_kill: float | None
    dir: Path


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _str_list(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) and x for x in v)


def validate(root: Path, tid: str, allow_placeholder: bool = False) -> tuple[dict, list[str]]:
    cfg = lib.config(root)
    defaults = cfg.get("defaults", {})
    locked = cfg["ownership"]["locked"]
    d = root / "tasks" / tid
    errs: list[str] = []
    if not ID.fullmatch(tid):
        errs.append(f"id '{tid}' must look like T-042")
    tf = d / "task.toml"
    if not tf.exists():
        return {}, errs + [f"missing {tf.relative_to(root)}"]
    try:
        data = tomllib.loads(tf.read_text())
    except tomllib.TOMLDecodeError as e:
        return {}, errs + [f"task.toml does not parse: {e}"]

    unknown = set(data) - KEYS
    if unknown:
        errs.append(f"unknown keys: {sorted(unknown)}")
    if data.get("id") != tid:
        errs.append(f"id must equal the directory name '{tid}'")
    if not isinstance(data.get("title"), str) or not data["title"].strip() or "{{" in data["title"]:
        errs.append("title: required non-empty string")
    if data.get("tier") not in (1, 2, 3) or isinstance(data.get("tier"), bool):
        errs.append("tier: must be 1, 2 or 3")
    kind = data.get("kind")
    if kind not in KINDS:
        errs.append(f"kind: must be one of {KINDS}")

    allow = data.get("allow")
    if not _str_list(allow) or not allow:
        errs.append("allow: required non-empty list of path globs")
    else:
        for a in allow:
            if lib.match(a, locked) or lib.match(a.replace("*", "x"), locked):
                errs.append(f"allow: '{a}' covers a human-owned path")

    acc = data.get("acceptance_tests", [])
    if not _str_list(acc):
        errs.append("acceptance_tests: must be a list of paths")
        acc = []
    if kind in ("feature", "fix") and not acc:
        errs.append("acceptance_tests: required for feature and fix tasks")
    for a in acc:
        p = root / a
        if not lib.match(a, locked):
            errs.append(f"acceptance_tests: '{a}' must be in a human-owned path")
        if not p.is_file():
            errs.append(f"acceptance_tests: '{a}' does not exist")
        elif lib.PLACEHOLDER in p.read_text() and not allow_placeholder:
            errs.append(f"acceptance_tests: '{a}' still contains {lib.PLACEHOLDER}")

    for key in ("loc_budget", "max_new_files", "max_new_classes"):
        v = data.get(key, defaults.get(key))
        if not _is_int(v) or v < 0 or (key == "loc_budget" and v == 0):
            errs.append(f"{key}: must be a {'positive' if key == 'loc_budget' else 'non-negative'} integer")

    rmc = data.get("replay_may_change", [])
    if not isinstance(rmc, list) or not all(isinstance(x, str) for x in rmc):
        errs.append("replay_may_change: must be a list of case names")
    elif rmc and kind in ("refactor", "delete"):
        errs.append("replay_may_change: must be empty for refactor and delete tasks")
    elif rmc and cfg.get("replay", {}).get("cmd"):
        cases_dir = root / cfg["replay"]["cases"]
        known = {p.stem for p in cases_dir.iterdir() if p.is_file()} if cases_dir.exists() else set()
        for c in rmc:
            if c not in known:
                errs.append(f"replay_may_change: unknown case '{c}'")

    mk = data.get("mutation_min_kill")
    if mk is not None and (not isinstance(mk, (int, float)) or isinstance(mk, bool) or not 0 <= mk <= 1):
        errs.append("mutation_min_kill: must be a number from 0 to 1")

    spec = d / "spec.md"
    if not spec.exists():
        errs.append("missing spec.md")
    else:
        text = spec.read_text()
        for s in SECTIONS:
            if s not in text:
                errs.append(f"spec.md: missing section '{s}'")
        if lib.PLACEHOLDER in text and not allow_placeholder:
            errs.append(f"spec.md: still contains {lib.PLACEHOLDER}")
    return data, errs


def load(root: Path, tid: str, allow_placeholder: bool = False) -> Task:
    data, errs = validate(root, tid, allow_placeholder)
    if errs:
        raise lib.HarnessError(f"task {tid} is invalid:\n  - " + "\n  - ".join(errs))
    defaults = lib.config(root).get("defaults", {})
    tier = data["tier"]
    mk = data.get("mutation_min_kill", TIER_KILL[tier])
    return Task(
        id=data["id"], title=data["title"], tier=tier, kind=data["kind"],
        allow=tuple(data["allow"]), acceptance_tests=tuple(data.get("acceptance_tests", [])),
        loc_budget=data.get("loc_budget", defaults.get("loc_budget", 200)),
        max_new_files=data.get("max_new_files", defaults.get("max_new_files", 1)),
        max_new_classes=data.get("max_new_classes", defaults.get("max_new_classes", 0)),
        replay_may_change=tuple(data.get("replay_may_change", [])),
        mutation_min_kill=None if mk is None else float(mk),
        dir=root / "tasks" / tid,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: aishore validate T-042")
        return 2
    root = lib.repo_root()
    _, errs = validate(root, argv[0])
    if errs:
        print(f"{argv[0]}: INVALID\n  - " + "\n  - ".join(errs))
        return 1
    print(f"{argv[0]}: valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
