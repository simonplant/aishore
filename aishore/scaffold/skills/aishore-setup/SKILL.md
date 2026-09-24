---
name: aishore-setup
description: Tailor a fresh aishore install to this repository - architecture rules with their enforcement, module map, locked schema and interface paths, gate commands, and replay. Use once after installing aishore, or when asked to set up, configure, or calibrate the harness.
---
You configure the harness on the base branch. The human reviews the whole diff before committing.
Everything you write here is human-owned afterwards, so write only what the code supports.

1. Read `aishore.toml`, ENGINEERING.md, CLAUDE.md, the README, the build and dependency files,
   and enough of the source to know the modules and how data flows through them.
2. Gates. Run each `commands` step (setup, lint, types, imports, tests) and `acceptance.cmd` on the
   base branch. For each one that fails or is missing, find the command this project really
   uses (package scripts, Makefile, CI workflow). Set it, or leave it empty with a comment
   saying what is missing. Confirm `commands.tests` excludes `tests/acceptance`. Check `src`
   lists the production roots and nothing else. Iterate until
   `.aishore/bin/aishore gate fast` passes on the base branch.
3. Module map. Write `docs/architecture.md`: one table of modules with their responsibility
   and what each may import, the data flow in one line, and each state machine with its legal
   transitions. Keep it to one page. Add it to `review.context` in aishore.toml.
4. Architecture rules. Replace ENGINEERING.md section 3 with the rules this code already
   follows or clearly intends: module boundaries, purity, boundary types, source of truth,
   error handling. Each rule names its enforcement. Where a tool can enforce it (import-linter
   contracts, a type checker in strict mode, a lint rule), add the config and the gate command.
   Where only review can enforce it, write "Enforced: review". Drop any rule you cannot point to
   in the code.
5. Ownership. Add to `ownership.locked` the paths that define contracts: schemas, interface and
   protocol modules, migrations, public API definitions, fixtures that tests treat as truth.
6. Replay. If the system turns recorded inputs into outputs (events, orders, rendered files, API
   responses), propose a replay command that prints one JSON line per output for one input file,
   and two or three recorded cases for `replay/cases/`. Write the command only if it exists or is
   a thin wrapper over an existing entry point. Otherwise leave `replay.cmd` empty and say what
   would be needed.
7. Report what you changed, each rule you added and its enforcement, and every judgment call the
   human should confirm. Do not commit.
