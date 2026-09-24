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
    (r"--no-verify\b", "--no-verify"),
    (r"\b(chmod|chown|chattr|sudo)\b", "permission changes"),
    (r"\b(pip3?|uv\s+pip)\s+install\b|\buv\s+(add|remove)\b|\bpoetry\s+(add|remove)\b"
     r"|\b(npm|pnpm)\s+(i|install|add|uninstall|remove|rm)\b|\byarn\s+(add|remove)\b"
     r"|\bcargo\s+(add|remove)\b|\bgo\s+get\b", "dependency changes"),
    (r"\breplay\s+update\b", "golden updates"),
    (r"\b(AISHORE_(TASK|BRANCH|ROLE)|GIT_CONFIG_\w+|GIT_DIR|GIT_WORK_TREE)=", "harness or git context override"),
]
GIT_BLOCKED = {"push": "git push", "checkout": "branch or worktree changes", "switch": "branch or worktree changes",
               "worktree": "branch or worktree changes", "rebase": "branch or worktree changes",
               "merge": "branch or worktree changes", "stash": "branch or worktree changes",
               "symbolic-ref": "branch or worktree changes", "update-ref": "history rewrites"}
GIT_VALUE_OPTS = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
SHELLS = {"sh", "bash", "zsh", "dash", "eval"}


def segments(cmd: str) -> list[list[str]]:
    out = []
    for segment in re.split(r"&&|\|\||[;|\n]|\$\(|`|\)", cmd):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        while tokens and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]) or tokens[0] in ("(", "{", "!")):
            tokens = tokens[1:]
        if tokens:
            out.append(tokens)
    return out


def git_violation(cmd: str, depth: int = 0) -> str | None:
    """Parse each git invocation: skip global options, then judge the subcommand. Recurse into sh -c."""
    for tokens in segments(cmd):
        prog = tokens[0].rsplit("/", 1)[-1]
        if prog in SHELLS and depth < 3:
            inner = tokens[tokens.index("-c") + 1] if "-c" in tokens[:-1] else " ".join(tokens[1:]) if prog == "eval" else ""
            found = git_violation(inner, depth + 1) if inner else None
            if found:
                return found
            continue
        if prog != "git":
            continue
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            opt = tokens[i].split("=", 1)[0]
            value = tokens[i + 1] if opt in GIT_VALUE_OPTS and "=" not in tokens[i] and i + 1 < len(tokens) else ""
            setting = value or (tokens[i].split("=", 1)[1] if "=" in tokens[i] else "")
            if opt in ("-c", "--config-env") and setting.lower().startswith("alias."):
                return "git aliases"
            i += 2 if value else 1
        if i >= len(tokens):
            continue
        sub, args = tokens[i], tokens[i + 1:]
        if sub in GIT_BLOCKED:
            return GIT_BLOCKED[sub]
        if sub == "reset" and "--hard" in args:
            return "history rewrites"
        if sub == "branch" and any(re.fullmatch(r"-[dDmMcCf]+|--(delete|move|copy|force)", a) for a in args):
            return "history rewrites"
        if sub == "config" and any(a.lower().startswith(("alias.", "core.hookspath", "include")) for a in args):
            return "git config changes"
    return None


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
    labels = [label for pat, label in BLOCKED if re.search(pat, cmd)]
    git = git_violation(cmd)
    for label in labels + ([git] if git else []):
        print(f"Blocked by aishore: {label} are not allowed in a task session.", file=sys.stderr)
        return 2
    locked = [*lib.config(root)["ownership"]["locked"], *lib.HARNESS_OWNED]
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
