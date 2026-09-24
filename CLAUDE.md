# CLAUDE.md

aishore is an engineering harness for Claude Code, installed into other repositories. README.md
is the operating manual; this file maps the source.

## Layout

```
aishore/                 the package, stdlib only, Python 3.11+ (vendored into targets as .aishore/aishore/)
  __main__.py            CLI dispatch
  lib.py                 repo, config, task context, ownership, acceptance runner helpers
  langs.py               per-language cheat patterns and class detection
  tasks.py               task.toml and spec.md validation
  flow.py                new, brief-review, start, plan-review, review, adopt, sync, merge, abandon, status
  briefcheck.py          runs brief-review counterexamples against the acceptance tests in a scratch worktree
  run.py                 headless run: plan, reviewer approval, build, review, one fix round
  gate.py diffcheck.py replay.py mutate.py findings.py logbook.py entropy.py
  hooks/                 guard_edit, guard_bash, post_edit, stop (run via `aishore hook <name>`)
  install.py             profiles (python, node, generic), install, update
  selftest.py            end-to-end test in throwaway repos with a stub claude
  prompts/               reviewer role, brief review, plan review, diff review
  scaffold/              files written into targets: ENGINEERING.md, role, /implement, skills (brief,
                         decompose, aishore-setup, triage, retro), task templates, vitest runner, shim
bin/aishore              symlink to the shim, for running from source
install.sh               curl installer
```

## Rules

- Stdlib only. Target projects must not need a pip install to run their hooks.
- Nothing project-specific in the package: every project fact lives in the target's aishore.toml
  or ENGINEERING.md.
- A change is done when `bin/aishore selftest` passes (it needs pytest, and node for the node
  part) and `ruff check aishore` is clean. A new behavior gets a selftest check driving the
  installed CLI, not a fragment test.
- Hooks fail closed (guards) or stay out of the way (formatter). Never let a guard error allow an edit.
