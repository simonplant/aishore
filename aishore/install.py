"""Install or update aishore in a git repository.

  aishore install [--dir PATH] [--profile python|node|generic]
  aishore update [--ref REF]

Writes .aishore/ (the harness, human-owned), and on first install aishore.toml and ENGINEERING.md.
Merges hooks into .claude/settings.json, imports into CLAUDE.md, and lines into .gitignore.
Never overwrites aishore.toml or ENGINEERING.md. Removes a pre-harness (bash) aishore install.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from aishore import __version__, lib

REPO = os.environ.get("AISHORE_REPO", "simonplant/aishore")
PKG = Path(__file__).resolve().parent
SCAFFOLD = PKG / "scaffold"
MARK = "<!-- aishore -->"
CLAUDE_BLOCK = f"{MARK}\n@ENGINEERING.md\n@.aishore/aishore/scaffold/claude-role.md\n"
GITIGNORE = [".aishore/state/", "ESCALATE.md", "PLAN.md", "tests/_review/", "__pycache__/"]
DENY = ["Bash(git push:*)", "Bash(sudo:*)"]
HOOK = '"$CLAUDE_PROJECT_DIR"/.aishore/bin/aishore hook {}'
HOOKS = {
    "PreToolUse": [("Edit|Write|MultiEdit|NotebookEdit", "guard_edit", 15), ("Bash", "guard_bash", 15)],
    "PostToolUse": [("Edit|Write|MultiEdit", "post_edit", 60)],
    "Stop": [(None, "stop", 600)],
}
LOCKED = [
    "aishore.toml", ".aishore/aishore/**", ".aishore/bin/**", "ENGINEERING.md", "CLAUDE.md", "AGENTS.md",
    ".claude/settings.json", ".claude/commands/**", ".claude/agents/**", ".claude/skills/**",
    ".github/**", ".gitignore", "Makefile",
    "tasks/**", "docs/**", "replay/**", "tests/acceptance/**", "tests/property/**",
    "pyproject.toml", "requirements*.txt", "uv.lock", "poetry.lock", "setup.cfg", "setup.py",
    "pytest.ini", "tox.ini", "*conftest.py", ".python-version",
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", ".npmrc", "tsconfig*.json",
    "vitest.config.*", "jest.config.*", "eslint.config.*", ".eslintrc*", ".prettierrc*",
    "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
]
MODELS = {"implement": "claude-opus-5-5", "review": "claude-fable-5-1"}
REVIEW_CMD = ["claude", "-p", "--output-format", "text", "--tools", "Read,Grep,Glob",
              "--allowedTools", "Read,Grep,Glob", "--max-turns", "40"]


# ---------------------------------------------------------------- profiles

def detect(root: Path) -> str:
    if (root / "package.json").exists():
        return "node"
    if any((root / f).exists() for f in ("pyproject.toml", "setup.py", "setup.cfg")) or any(root.glob("requirements*.txt")):
        return "python"
    files = lib.sh("git", "ls-files", cwd=root).splitlines()
    code = [Path(f).suffix for f in files if Path(f).suffix in (".py", ".js", ".ts", ".go", ".rs", ".sh", ".rb", ".java")]
    return "python" if code and max(set(code), key=code.count) == ".py" else "generic"


def base_branch(root: Path) -> str:
    """The default branch: origin/HEAD, else main or master, else the current branch."""
    head = subprocess.run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=root,
                          capture_output=True, text=True).stdout.strip()
    if head:
        return head.split("/", 1)[1]
    for name in ("main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/heads/{name}"], cwd=root,
                          capture_output=True).returncode == 0:
            return name
    return lib.sh("git", "branch", "--show-current", cwd=root).strip() or "main"


def src_dirs(root: Path, profile: str) -> list[str]:
    if (root / "src").is_dir():
        return ["src"]
    if profile == "python":
        pkgs = sorted(p.parent.name for p in root.glob("*/__init__.py") if p.parent.name not in ("tests", "test"))
        if pkgs:
            return pkgs
    return ["."]


def text(root: Path, name: str) -> str:
    p = root / name
    return p.read_text() if p.exists() else ""


def python_profile(root: Path) -> dict:
    pp = text(root, "pyproject.toml")
    ruff = "[tool.ruff" in pp or (root / "ruff.toml").exists() or (root / ".ruff.toml").exists()
    types = ("pyright" if "[tool.pyright" in pp or (root / "pyrightconfig.json").exists()
             else "mypy ." if "[tool.mypy" in pp or (root / "mypy.ini").exists() else "")
    if "[project.optional-dependencies]" in pp and re.search(r"^dev\s*=", pp, re.M):
        install = 'pip install -e ".[dev]"'
    elif (root / "requirements.txt").exists():
        install = "pip install -r requirements.txt pytest"
    else:
        install = "pip install pytest" + (" -e ." if pp else "")
    return {
        "commands": {
            "setup": "",
            "lint": "ruff check . && ruff format --check ." if ruff else "",
            "types": types,
            "imports": "lint-imports" if "[tool.importlinter" in pp or (root / ".importlinter").exists() else "",
            "tests": "python3 -m pytest -q -x -p no:cacheprovider --ignore=tests/acceptance --ignore=tests/_review",
        },
        "acceptance": {"cmd": "python3 -m pytest -q -p no:cacheprovider {tests}", "fail_codes": [1], "empty_codes": [5],
                       "assert_pattern": r"^E\s+(assert\b|AssertionError|Failed:)",
                       "path": "tests/acceptance/test_{name}.py", "lang": "python"},
        "format": {".py": "ruff format -q {file} && ruff check -q --fix {file} && "
                          "ruff check --output-format concise {file}"} if ruff else {},
        "ci": {"setup": "", "install": install},
    }


def node_profile(root: Path) -> dict:
    pkg = json.loads(text(root, "package.json") or "{}")
    scripts = pkg.get("scripts", {})
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    test = scripts.get("test", "")
    if (root / "pnpm-lock.yaml").exists():
        setup = "pnpm install --frozen-lockfile"
    elif (root / "yarn.lock").exists():
        setup = "yarn install --frozen-lockfile"
    elif (root / "package-lock.json").exists():
        setup = "npm ci --no-audit --no-fund"
    else:
        setup = "npm install --no-package-lock --no-audit --no-fund"
    ts = (root / "tsconfig.json").exists()
    if "vitest" in test or "vitest" in deps:
        acc = "npx vitest run --passWithNoTests --config .aishore/aishore/scaffold/runners/vitest.config.mjs {tests}"
    elif "jest" in test or "jest" in deps:
        acc = ("npx jest --passWithNoTests --roots '<rootDir>' "
               "--testMatch '**/tests/{acceptance,_review}/**/*.[jt]s?(x)' {tests}")
    else:
        acc = "node --test {tests}"
    fmt = "npx --no-install prettier --write {file}" if "prettier" in deps else ""
    return {
        "commands": {
            "setup": setup,
            "lint": "npm run lint --silent" if "lint" in scripts else "",
            "types": "npx tsc --noEmit" if ts else "",
            "imports": "",
            "tests": "npm test --silent" if test else "",
        },
        # .accept. matches no default discovery (node --test, jest, vitest), so npm test never runs them.
        "acceptance": {"cmd": acc, "fail_codes": [], "empty_codes": [], "lang": "typescript" if ts else "javascript",
                       "assert_pattern": r"AssertionError|ERR_ASSERTION|expect\(received\)",
                       "path": "tests/acceptance/{name}.accept." + ("ts" if ts else "js")},
        "format": {ext: fmt for ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")} if fmt else {},
        "ci": {"setup": "node", "install": setup.replace(" --no-package-lock", "")},
    }


def generic_profile(root: Path) -> dict:
    return {
        "commands": {"setup": "", "lint": "", "types": "", "imports": "", "tests": ""},
        "acceptance": {"cmd": 'for t in {tests}; do bash "$t" || exit 1; done', "fail_codes": [], "empty_codes": [],
                       "assert_pattern": "",
                       "path": "tests/acceptance/test_{name}.sh", "lang": "bash"},
        "format": {},
        "ci": {"setup": "", "install": "true"},
    }


PROFILES = {"python": python_profile, "node": node_profile, "generic": generic_profile}


# ---------------------------------------------------------------- rendering

def tv(v) -> str:
    """TOML value for strings, numbers, and lists of them."""
    if isinstance(v, list):
        return "[" + ", ".join(tv(x) for x in v) + "]"
    return json.dumps(v) if isinstance(v, str) else str(v)


def render_config(root: Path, profile: str, p: dict) -> str:
    context = ["ENGINEERING.md"] + [f for f in ("docs/architecture.md", "docs/ARCHITECTURE.md", "ARCHITECTURE.md")
                                    if (root / f).is_file()]
    locked = ",\n  ".join(tv(x) for x in LOCKED)
    fmt = "\n".join(f"{tv(k)} = {tv(v)}" for k, v in p["format"].items())
    c, a = p["commands"], p["acceptance"]
    return f"""# aishore configuration ({profile} profile). Human-owned: listed in ownership.locked.
base = {tv(base_branch(root))}
src = {tv(src_dirs(root, profile))}          # production code roots: LOC budget, new files and classes, mutation
worktree_root = "../.wt"         # task worktrees: ../.wt/<repo>-<task id>

[commands]
# Gate steps in order. An empty string skips the step. setup runs once in each new worktree.
setup = {tv(c["setup"])}
lint = {tv(c["lint"])}
types = {tv(c["types"])}
imports = {tv(c["imports"])}
tests = {tv(c["tests"])}      # everything except tests/acceptance; the harness runs those per task

[acceptance]
# Runs acceptance and reviewer-finding tests. {{tests}} becomes the quoted file list.
cmd = {tv(a["cmd"])}
fail_codes = {tv(a["fail_codes"])}    # exit codes that prove a finding (assertion failed); empty: any non-zero
empty_codes = {tv(a["empty_codes"])}   # exit codes meaning "no tests found"; start refuses them
assert_pattern = {tv(a["assert_pattern"])}   # a finding is REAL only if its output matches; empty: any failure
path = {tv(a["path"])}   # {{name}} is the task slug (t_042) or a finding (t_042_f1); never auto-discovered by commands.tests
lang = {tv(a["lang"])}

[format]
# PostToolUse formatter per extension; {{file}} is the edited file. Non-zero exit is fed back to the agent.
{fmt}

[replay]
# Prints one event per line to stdout for one recorded input ({{input}}, quoted). Empty cmd disables replay.
cmd = ""
cases = "replay/cases"
golden = "replay/golden"

[mutation]
# Python only. tests defaults to commands.tests; the task's acceptance tests always run too.
tests = ""
max_mutants = 40
timeout_factor = 5

[implement]
model = {tv(MODELS["implement"])}
# `aishore run` appends --model, --resume and the prompt, and reads the JSON result.
headless = ["claude", "-p", "--output-format", "json", "--permission-mode", "acceptEdits",
            "--allowedTools", "Bash,Edit,Write,MultiEdit,Read,Glob,Grep"]

[review]
# A separate headless process in the worktree: fresh context, read-only tools, a different model.
model = {tv(MODELS["review"])}
cmd = {tv(REVIEW_CMD)}
context = {tv(context)}   # files the reviewer receives with every review

[defaults]
loc_budget = 200
max_new_files = 1
max_new_classes = 0

[ownership]
# Agents read these and never write them: hooks, read-only files in the worktree, and the diff gate.
locked = [
  {locked},
]
"""


def render_ci(p: dict, base: str) -> str:
    node = "\n      - uses: actions/setup-node@v7\n        with:\n          node-version: lts/*" \
        if p["ci"]["setup"] == "node" else ""
    return f"""name: aishore-verify
on:
  pull_request:
  push:
    branches: [{base}]

jobs:
  gate:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"{node}
      - name: Install
        run: {p["ci"]["install"]}
      - name: Full gate
        env:
          AISHORE_BRANCH: ${{{{ github.head_ref || github.ref_name }}}}
        run: .aishore/bin/aishore gate full
"""


# ---------------------------------------------------------------- merging into the target

def remove_legacy(root: Path) -> list[str]:
    done = []
    bash_install = root / ".aishore" / "aishore"
    if bash_install.is_file():
        lib.set_locked(root / ".aishore", {"ownership": {"locked": ["**"]}}, False)
        shutil.rmtree(root / ".aishore")
        done.append("removed the bash aishore in .aishore/ (backlog/ left as is)")
    cm = root / "CLAUDE.md"
    if cm.exists():
        t = cm.read_text()
        new = re.sub(r"^## Sprint Orchestration \(aishore\)\n.*?(?=^## |\Z)", "", t, flags=re.M | re.S)
        if new != t:
            cm.write_text(new)
            done.append("removed the bash aishore section from CLAUDE.md")
    gi = root / ".gitignore"
    if gi.exists():
        lines = gi.read_text().splitlines()
        keep = [x for x in lines if not x.startswith(".aishore/data") and x != "# aishore runtime files"]
        if keep != lines:
            gi.write_text("\n".join(keep) + "\n")
    return done


def merge_settings(root: Path) -> None:
    path = root / ".claude" / "settings.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    deny = data.setdefault("permissions", {}).setdefault("deny", [])
    deny += [d for d in DENY if d not in deny]
    hooks = data.setdefault("hooks", {})
    for event, entries in HOOKS.items():
        groups = hooks.setdefault(event, [])
        for matcher, name, timeout in entries:
            cmd = HOOK.format(name)
            if any(h.get("command") == cmd for g in groups for h in g.get("hooks", [])):
                continue
            g = {"hooks": [{"type": "command", "command": cmd, "timeout": timeout}]}
            if matcher:
                g = {"matcher": matcher, **g}
            groups.append(g)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def append_missing(path: Path, lines: list[str], header: str = "") -> None:
    t = path.read_text() if path.exists() else ""
    have = set(t.splitlines())
    add = [x for x in lines if x not in have]
    if add:
        sep = "" if not t or t.endswith("\n") else "\n"
        path.write_text(t + sep + (header + "\n" if header else "") + "\n".join(add) + "\n")


def install(root: Path, profile: str | None) -> None:
    root = Path(lib.sh("git", "rev-parse", "--show-toplevel", cwd=root).strip())
    notes = remove_legacy(root)
    dot = root / ".aishore"
    pkg = dot / "aishore"
    if pkg.resolve() != PKG:
        if pkg.exists():
            lib.set_locked(dot, {"ownership": {"locked": ["**"]}}, False)
            shutil.rmtree(pkg)
        shutil.copytree(PKG, pkg, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shim = dot / "bin" / "aishore"
        shim.parent.mkdir(parents=True, exist_ok=True)
        shim.unlink(missing_ok=True)
        shutil.copy(SCAFFOLD / "aishore.sh", shim)
        shim.chmod(0o755)

    cfg_path = root / lib.CONFIG
    if cfg_path.exists():
        notes.append(f"kept {lib.CONFIG}")
    else:
        profile = profile or detect(root)
        p = PROFILES[profile](root)
        cfg_path.write_text(render_config(root, profile, p))
        notes.append(f"wrote {lib.CONFIG} ({profile} profile): review commands, src and locked paths")
        ci = root / ".github" / "workflows" / "aishore-verify.yml"
        if not ci.exists():
            ci.parent.mkdir(parents=True, exist_ok=True)
            ci.write_text(render_ci(p, base_branch(root)))
            notes.append("wrote .github/workflows/aishore-verify.yml: check its install step")
    adr = root / "docs" / "adr" / "0000-template.md"
    if not adr.exists():
        adr.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SCAFFOLD / "adr" / "0000-template.md", adr)
        notes.append("wrote docs/adr/0000-template.md")
    eng = root / "ENGINEERING.md"
    if not eng.exists():
        shutil.copy(SCAFFOLD / "ENGINEERING.md", eng)
        notes.append("wrote ENGINEERING.md: fill in section 3 (architecture rules)")

    cm = root / "CLAUDE.md"
    t = cm.read_text() if cm.exists() else ""
    if MARK not in t:
        cm.write_text(t + ("\n" if t and not t.endswith("\n") else "") + ("\n" if t else "") + CLAUDE_BLOCK)
    cmds = root / ".claude" / "commands"
    cmds.mkdir(parents=True, exist_ok=True)
    for f in (SCAFFOLD / "commands").iterdir():
        shutil.copy(f, cmds / f.name)
    (cmds / "draft-task.md").unlink(missing_ok=True)
    for d in (SCAFFOLD / "skills").iterdir():
        shutil.copytree(d, root / ".claude" / "skills" / d.name, dirs_exist_ok=True)
    merge_settings(root)
    append_missing(root / ".gitignore", GITIGNORE, "# aishore")

    print(f"aishore {__version__} installed in {root}")
    for n in notes:
        print(f"  - {n}")
    print("next: review the files above, then commit them on the base branch:")
    print("  git add -A .aishore aishore.toml ENGINEERING.md CLAUDE.md .claude .gitignore .github docs/adr "
          "&& git commit -m 'chore: install aishore'")
    print("then in Claude Code on the base branch: /aishore-setup   (gates, architecture rules, locked paths)")


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token and shutil.which("gh"):
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    return token


def update(root: Path, ref: str) -> None:
    """Fetch the tarball through the API so a private fork works with a gh or GITHUB_TOKEN login."""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/tarball/{ref}",
                                 headers={"Accept": "application/vnd.github+json"})
    token = github_token()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(data)) as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(tmp, filter="data")
            else:
                tf.extractall(tmp)  # noqa: S202 - our own GitHub tarball
        src = next(Path(tmp).iterdir())
        r = subprocess.run([sys.executable, "-m", "aishore", "install", "--dir", str(root)],
                           env={**os.environ, "PYTHONPATH": str(src)})
        if r.returncode:
            sys.exit(r.returncode)
