# aishore

An engineering harness for Claude Code. Claude implements; the harness owns correctness.

- **Human-owned specs and tests.** Each task has a spec and acceptance tests that you write (or
  approve) on the base branch. Agents read them and cannot change them.
- **One worktree per task** (`../.wt/<repo>-T-042`, branch `t/T-042`). Human-owned paths are made
  read-only there.
- **Hooks that block.** Edits outside the task allowlist, writes to human-owned paths, gate
  bypasses, and red finishes are all refused.
- **A diff gate.** Checks ownership, the allowlist, gate weakening, the LOC budget, new files and
  new classes.
- **Oracles.** Acceptance tests per task, a replay of recorded inputs against golden output, and
  mutation testing on changed lines (Python).
- **An independent reviewer.** A different model runs headless and read-only. A finding counts
  only when its test fails on the branch.
- **A merge you approve.** The full gate runs, you see the diff, and you answer y/N. The outcome
  is logged.

Works in any git repository. The harness is stdlib Python 3.11+. Your project can be in any
language: gates and test runners are commands in `aishore.toml`. Python projects also get AST
mutation and ruff-on-edit when ruff is configured.

## Requirements

`python3` >= 3.11 and git 2.30+ on PATH. The hooks call python3. You also need Claude Code,
logged in with access to the implementer and reviewer models. Your project's own test runner
must be installed. Do not run Claude Code as root: file permissions do not bind root.

## Install

From the repository root, on the base branch:

```
curl -fsSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
```

This detects a profile: `node` (package.json), `python` (pyproject, setup, requirements, or
mostly .py) or `generic`. Pass `bash -s -- --profile <name>` to override it. It then writes:

| Path | What | Rewritten by update? |
|---|---|---|
| `.aishore/aishore/`, `.aishore/bin/aishore` | the harness and its CLI | yes |
| `aishore.toml` | commands, src roots, test runner, models, budgets, locked paths | no |
| `ENGINEERING.md` | the rulebook; section 3 is yours to fill | no |
| `CLAUDE.md` | appends `@ENGINEERING.md` and the role file import | once |
| `.claude/settings.json` | four hooks merged into your existing settings | merged |
| `.claude/commands/` | `/implement`, `/draft-task` | yes |
| `.gitignore` | `.aishore/state/`, `PLAN.md`, `ESCALATE.md`, `tests/_review/` | merged |
| `.github/workflows/aishore-verify.yml` | full gate on PRs and the base branch | no |
| `docs/adr/0000-template.md` | decision record template (new dependencies need one) | no |

It removes an old bash aishore (`.aishore/aishore` script, `.aishore/data/`, and the CLAUDE.md
sprint section). It leaves `backlog/` alone.

Then:

1. Read `aishore.toml`. Check `src`, the gate commands, and `acceptance.cmd`. Blank out any
   step you are not ready for.
2. Fill ENGINEERING.md section 3 with the real architecture rules. Each rule names its
   enforcement.
3. Optional: set a replay command that prints one JSON event per line for one recorded input,
   put the inputs in `replay/cases/`, run `aishore replay update` and review the goldens.
4. Run `.aishore/bin/aishore gate fast` and fix what it finds.
5. Commit on the base branch. `aishore start` refuses to run until the harness is committed,
   because a worktree without it would have no hooks.

Put `.aishore/bin` on PATH or alias `aishore` to `.aishore/bin/aishore`. The examples below
assume one of these.

Update: `aishore update` (or re-run install.sh). This keeps `aishore.toml` and ENGINEERING.md.

## Operating procedure

Every `aishore` command runs from the main checkout. Claude Code runs only in a worktree.

### 1. Define the task (you, on the base branch)

```
aishore new T-042 "Trail stop to swing low"
```

Optional: in Claude Code on the base branch, run `/draft-task T-042 <intent>`. It fills the
spec, task.toml and the acceptance test, and leaves `AISHORE_PLACEHOLDER` lines that force you to
review.

Edit until the spec is exact: signatures, an acceptance table with edge and failure cases, the
invariants that apply, and what is out of scope. Keep `allow` minimal. Delete every placeholder
line, then:

```
aishore validate T-042
git add tasks/T-042 tests/acceptance && git commit -m "T-042: task"
```

If you cannot write the acceptance table, or cannot say which replay cases change, split the task.

### 2. Start

```
aishore start T-042
```

This validates the task, proves the acceptance tests fail on the base branch, creates the
worktree, runs `commands.setup` there (for example `npm ci`), and makes human-owned paths
read-only.

### 3a. Interactive: plan and build

```
cd ../.wt/<repo>-T-042 && claude --model claude-opus-5-5
/implement
```

Claude writes PLAN.md and stops. For Tier 1, run `aishore plan-review T-042` from main and paste
the points you accept into the session. Approve when the Leave alone section is honest, the size
fits the budget, and nothing is added that the acceptance tests do not need. Otherwise cut it:
"Drop X. Reuse Y." Then say "approved". Claude builds while the hooks supervise:

| Hook | Effect |
|---|---|
| guard_edit | blocks edits to human-owned paths and outside the allowlist (fails closed) |
| guard_bash | blocks push, branch switching, chmod, dependency installs, golden updates, shell writes to locked paths |
| post_edit | runs the `[format]` command for the file's extension and feeds problems back |
| stop | once code has changed, refuses a red finish twice, then requires ESCALATE.md |

If Claude goes idle after a blocked tool call, type `continue`.

### 3b. Headless: `aishore run T-042`

`aishore run` starts the task if needed, then:
1. The implementer runs headless in the worktree with the same hooks and writes PLAN.md.
2. The reviewer attacks the plan. REVISE sends the points back once; a second REVISE stops the
   run for you to decide.
3. The implementer builds under the Stop hook.
4. Tier 1 and 2: the reviewer checks the diff. Findings that fail on the branch go back to the
   implementer once, then are re-run.
5. It prints the findings and the merge command.

It never merges. Re-running resumes from the worktree's state: the session id, plan approval,
and build status. After you adopt findings, `aishore run` again makes the new tests pass.

### 4. Review (Tier 1 and 2)

```
aishore review T-042
```

The reviewer is a separate `claude -p` process in the worktree. It runs the reviewer model with
only Read, Grep and Glob, and never sees the implementer's session. Each finding must carry a
test in the project's language. The harness runs each test with `acceptance.cmd` and writes
`tasks/T-042/findings.md`:
- **REAL**: the test fails on the branch.
- **discard**: the test passes.
- **invalid**: the test crashed or did not collect.

Read each REAL test, then promote the ones you agree with:

```
aishore adopt T-042 1 3
```

They become acceptance tests on main and are merged into the worktree. Tell Claude "New
acceptance tests: make them pass", or re-run `aishore run T-042`.

### 5. Merge (you)

```
aishore merge T-042
```

Runs the full gate in the worktree, commits the work, and shows the diff stat and the replay
diff. For Tier 1 it also shows the full diff. You answer y/N and record your minutes, which gate
caught a problem, and which gate was missing. On yes it merges, writes approved goldens for
`replay_may_change` cases, commits the task records and log, and removes the worktree. Reject
any diff larger than you expected, even when it is green.

### 6. Escalations

ESCALATE.md is a statement about the spec or the architecture. Fix the spec or split the task,
then `aishore abandon T-042 "spec missed partial fills"`. This files the escalation under
`tasks/T-042/escalations/`, removes the worktree and branch, and logs the outcome.

Changing a spec mid-task: edit it on main, commit, run `aishore sync T-042`, and tell Claude
what changed. `aishore status` lists open worktrees with PLAN, ESCALATE and findings flags.

## Gates

| Step | Fast (Stop hook) | Full (merge, CI) |
|---|---|---|
| escalation: no ESCALATE.md | | yes |
| lint, types, imports, tests: commands from aishore.toml | yes | yes |
| diffcheck: ownership, allowlist, weakening, budgets (task branches) | yes | yes |
| acceptance: tests of merged tasks and the current task | yes | yes |
| replay against goldens | | yes |
| mutation on changed Python lines, per tier | | yes |

`commands.tests` must exclude `tests/acceptance`; the profiles do this. The acceptance step runs
the tests of merged tasks (from `tasks/log.csv`) plus the current task's. A task that is still
open elsewhere has red tests on main by design, and they never block other work.

Gate weakening is detected per language: skip, only, xfail, and lint, type and coverage
suppressions for Python, JS/TS, Go, Rust and shell. An extensionless script is classified by
its shebang.

## Configuration: `aishore.toml`

| Key | Meaning |
|---|---|
| `base`, `worktree_root` | base branch; where worktrees go (`../.wt`) |
| `src` | production roots: LOC budget, new files, new classes, mutation |
| `commands.setup` | runs once in each new worktree before paths lock |
| `commands.lint/types/imports/tests` | gate steps; empty skips |
| `acceptance.cmd` | runs acceptance and finding tests; `{tests}` is the quoted file list. Vitest runs through a shipped config that loads yours and adds `tests/acceptance` and `tests/_review` to `include`; jest gets `--roots` and `--testMatch` |
| `acceptance.fail_codes` | exit codes that prove a finding (pytest: 1); empty means any non-zero |
| `acceptance.empty_codes` | exit codes meaning no tests found (pytest: 5) |
| `acceptance.path`, `lang` | test file template (`{name}` = `t_042`, `t_042_f1`); reviewer's language |
| `format` | extension to formatter command, `{file}` |
| `replay.*`, `mutation.*` | oracle settings; empty replay cmd disables it |
| `implement.model`, `implement.headless` | interactive model; headless command for `aishore run` |
| `review.model`, `review.cmd`, `review.context` | reviewer model and command; files it always receives |
| `defaults.*` | LOC budget, new files, new classes per task |
| `ownership.locked` | human-owned globs |

Task files: `.aishore/aishore/scaffold/SCHEMA.md`, with a JSON Schema beside it for TOML
language servers.

## Rules for Claude Code sessions

- One fresh session per task, started inside that task's worktree. Exit between tasks.
- On the base branch, only `/draft-task`. The hooks guard task branches only.
- A request to edit a human-owned file is answered by changing the spec, never by permission.
- Never ask the implementer session to review its own diff, and never use a subagent inside it
  for review. Both inherit its context and its mistakes.
- Keep CLAUDE.md and ENGINEERING.md short. A rule broken twice becomes a gate or is deleted.

## Records

- `tasks/log.csv`: one row per merged, rejected, escalated or abandoned task. Rising human
  minutes, rising escalations, or a repeated `missing_gate` names the next gate to build.
- `aishore entropy`: appends files, LOC, dependencies, and Python complexity and dead code to
  `entropy.csv`.

## Known limits

- guard_bash is heuristic. A write through `python -c` gets past it; diffcheck at merge catches
  the result.
- A hook that times out does not block. The guards run in well under a second.
- The Stop hook allows a third red stop to avoid an infinite loop. The merge gate still refuses
  red work.
- Mutation covers changed Python lines only, samples at most `max_mutants`, and uses a fixed
  operator set.
- Reviewer tests are model-written code executed in the worktree. Read them before `adopt`.
- Runners without distinct exit codes (node, jest, vitest, shell) cannot tell a failing
  assertion from a crash. For them a crashing finding test counts as REAL, so read it. Vitest
  and jest pass when no test is collected, so a misplaced test shows as "already passes", never
  as a false red.

## Development

```
bin/aishore selftest     # installs into throwaway python, node and shell repos; drives every gate
ruff check aishore
```

The selftest needs pytest (and node for the node profile). It never calls a model: a stub
`claude` plays the reviewer and the headless implementer.
