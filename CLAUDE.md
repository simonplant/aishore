# CLAUDE.md

aishore: an engineering harness for Claude Code, vendored into target repositories as
`.aishore/aishore/`. README.md is the user manual.

## Layout

| Path | Content |
|---|---|
| `aishore/__main__.py` | CLI dispatch |
| `aishore/lib.py` | repo and config access, task context, ownership, acceptance runner, failure classification |
| `aishore/langs.py` | per-language gate-weakening patterns and class detection |
| `aishore/tasks.py` | task.toml and spec.md validation |
| `aishore/flow.py` | new, brief-review, start, plan-review, review, adopt, sync, merge, abandon, status |
| `aishore/briefcheck.py` | runs brief-review counterexamples in a scratch worktree |
| `aishore/run.py` | headless plan, approval, build, review, fix round |
| `aishore/gate.py`, `diffcheck.py`, `replay.py`, `mutate.py`, `findings.py`, `logbook.py`, `entropy.py` | gates, oracles, records |
| `aishore/hooks/` | guard_edit, guard_bash, post_edit, stop (`aishore hook <name>`) |
| `aishore/install.py` | profiles (python, node, generic), install, update |
| `aishore/selftest.py` | end-to-end test in throwaway repositories with a stub `claude` |
| `aishore/prompts/` | reviewer role, brief review, plan review, diff review |
| `aishore/scaffold/` | files written into targets: rulebook, role, `/implement`, skills, task templates, vitest runner, CLI shim |
| `bin/aishore` | symlink to the shim, for running from source |
| `install.sh` | installer |

## Rules

- Stdlib only. Target projects need no pip install to run hooks.
- No project-specific facts in the package. They belong in the target's `aishore.toml` or
  ENGINEERING.md.
- Guards fail closed. The formatter hook never blocks on its own error.
- Every behavior has a selftest check that drives the installed CLI and fails without the behavior.

## Verify

```
bin/aishore selftest     # needs pytest; node and npm for the node and vitest parts
ruff check aishore
```
