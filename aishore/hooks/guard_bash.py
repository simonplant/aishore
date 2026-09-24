"""PreToolUse on Bash: block gate bypasses and shell writes to human-owned paths.

Heuristic by nature. The diff gate at merge is the backstop for anything this misses.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

from aishore import lib

BLOCKED = [
    (r"\bgit\s+push\b", "git push"),
    (r"--no-verify\b", "--no-verify"),
    (r"\bgit\s+(checkout|switch|worktree|rebase|merge|stash)\b", "branch or worktree changes"),
    (r"\bgit\s+reset\s+--hard\b|\bgit\s+branch\s+-[dDmM]\b|\bgit\s+update-ref\b", "history rewrites"),
    (r"\b(chmod|chown|chattr|sudo)\b", "permission changes"),
    (r"\b(pip3?|uv\s+pip)\s+install\b|\buv\s+(add|remove)\b|\bpoetry\s+(add|remove)\b"
     r"|\b(npm|pnpm)\s+(i|install|add|uninstall|remove|rm)\b|\byarn\s+(add|remove)\b"
     r"|\bcargo\s+(add|remove)\b|\bgo\s+get\b", "dependency changes"),
    (r"\breplay\s+update\b", "golden updates"),
    (r"\bAISHORE_(TASK|BRANCH|ROLE)=", "harness context override"),
]
WRITERS = {"tee", "rm", "truncate", "mv", "cp", "ln", "touch", "install", "rsync"}
REDIRECT = re.compile(r"\d*>>?(?!&)\s*([^\s;|&<>]+)")


def targets(cmd: str) -> list[str]:
    found = REDIRECT.findall(cmd)
    for segment in re.split(r"&&|\|\||[;|\n]", cmd):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        prog, args = tokens[0].rsplit("/", 1)[-1], [t for t in tokens[1:] if not t.startswith("-")]
        if prog in WRITERS:
            found += args
        elif prog == "sed" and any(t.startswith("-i") or t == "--in-place" for t in tokens[1:]):
            found += args[1:]
        elif prog == "dd":
            found += [t[3:] for t in tokens if t.startswith("of=")]
        elif prog == "git" and len(tokens) > 1 and tokens[1] in ("restore", "rm", "mv"):
            found += [t for t in tokens[2:] if not t.startswith("-")]
    return found


def main() -> int:
    data = json.load(sys.stdin)
    root = lib.repo_root()
    if not lib.task_id(root):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    for pat, label in BLOCKED:
        if re.search(pat, cmd):
            print(f"Blocked by aishore: {label} are not allowed in a task session.", file=sys.stderr)
            return 2
    locked = lib.config(root)["ownership"]["locked"]
    for t in targets(cmd):
        rel = lib.relpath(root, t)
        if rel and lib.match(rel, locked):
            print(f"Blocked by aishore: this command writes to human-owned path {rel}. "
                  "If the task needs it changed, write ESCALATE.md and stop.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # fail closed
        print(f"Blocked by aishore: guard error: {e}", file=sys.stderr)
        sys.exit(2)
