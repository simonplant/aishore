"""Diff gate: ownership, allowlist, gate weakening, LOC budget, new files, new classes.

Runs only on task branches. Catches writes made through Bash that the Edit hook never sees.
"""
from __future__ import annotations

import re
import sys

from aishore import langs, lib, tasks


def added_lines(root, base, untracked) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    current = ""
    for line in lib.sh("git", "diff", "-U0", base, cwd=root).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("+") and current:
            out.append((current, line[1:]))
    for f in untracked:
        p = root / f
        if p.is_file() and langs.cheats(f, root):
            out += [(f, text) for text in p.read_text(errors="replace").splitlines()]
    return out


def main() -> int:
    root = lib.repo_root()
    cfg = lib.config(root)
    tid = lib.task_id(root)
    if not tid:
        print("diffcheck: not a task branch, skipped")
        return 0
    try:
        task = tasks.load(root, tid)
    except lib.HarnessError as e:
        print(e)
        return 1
    base = lib.merge_base(root, cfg)
    changed, untracked = lib.changed_files(root, base)
    files = sorted((changed | untracked) - set(lib.SCRATCH))
    locked = cfg["ownership"]["locked"]
    errors: list[str] = []

    for f in files:
        pat = lib.match(f, locked)
        if pat:
            errors.append(f"human-owned path modified: {f} ({pat})")
        elif not lib.match(f, task.allow):
            errors.append(f"outside allowlist: {f}")

    for f, line in added_lines(root, base, untracked):
        for pat, label in langs.cheats(f, root):
            if re.search(pat, line):
                errors.append(f"{label}: {f}: {line.strip()[:100]}")

    net = 0
    for row in lib.sh("git", "diff", "--numstat", base, cwd=root).splitlines():
        a, d, f = row.split("\t", 2)
        if a != "-" and lib.in_src(f, cfg) and f not in lib.SCRATCH:
            net += int(a) - int(d)
    for f in untracked:
        if lib.in_src(f, cfg) and f not in lib.SCRATCH and (root / f).is_file():
            net += len((root / f).read_text(errors="replace").splitlines())
    if net > task.loc_budget:
        errors.append(f"net production LOC {net} exceeds budget {task.loc_budget}")
    if task.kind == "delete" and net >= 0:
        errors.append(f"delete task must reduce production LOC (net {net})")

    new_src = [f for f in files if lib.in_src(f, cfg) and (f in untracked or not lib.exists_in(root, base, f))
               and (root / f).exists()]
    if len(new_src) > task.max_new_files:
        errors.append(f"{len(new_src)} new production files, max {task.max_new_files}: {new_src}")

    new_classes: list[str] = []
    for f in files:
        if not (lib.in_src(f, cfg) and (root / f).is_file()):
            continue
        try:
            head = langs.type_names(f, (root / f).read_text(errors="replace"), root)
            before = (langs.type_names(f, lib.sh("git", "show", f"{base}:{f}", cwd=root), root)
                      if lib.exists_in(root, base, f) else set())
        except SyntaxError as e:
            errors.append(f"syntax error in {f}: {e}")
            continue
        new_classes += [f"{f}:{name}" for name in sorted(head - before)]
    if len(new_classes) > task.max_new_classes:
        errors.append(f"{len(new_classes)} new classes, max {task.max_new_classes}: {new_classes}")

    if errors:
        print("diffcheck FAILED")
        print("\n".join(f"  - {e}" for e in errors))
        return 1
    print(f"diffcheck clean: {len(files)} files, net production LOC {net}/{task.loc_budget}, "
          f"new files {len(new_src)}/{task.max_new_files}, new classes {len(new_classes)}/{task.max_new_classes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
