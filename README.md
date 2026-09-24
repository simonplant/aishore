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
| `.claude/commands/implement.md` | `/implement` for the implementer session | yes |
| `.claude/skills/` | `/brief`, `/decompose`, `/aishore-setup`, `/triage`, `/retro` | yes |
| `.gitignore` | `.aishore/state/`, `PLAN.md`, `ESCALATE.md`, `tests/_review/` | merged |
| `.github/workflows/aishore-verify.yml` | full gate on PRs and the base branch | no |
| `docs/adr/0000-template.md` | decision record template (new dependencies need one) | no |

It removes an old bash aishore (`.aishore/aishore` script, `.aishore/data/`, and the CLAUDE.md
sprint section). It leaves `backlog/` alone.

Then:

1. In Claude Code on the base branch, run `/aishore-setup`. It makes the gate commands pass,
   drafts ENGINEERING.md section 3 (architecture rules, each with its enforcement) and
   `docs/architecture.md`, proposes schema and interface paths to lock, and a replay command.
   Review its diff: all of it is human-owned from here on.
2. Or by hand: check `src`, the gate commands and `acceptance.cmd` in `aishore.toml`, fill
   ENGINEERING.md section 3, and optionally set `replay.cmd` (`{input}` is the recorded file;
   it prints one JSON event per line), add `replay/cases/`, and run `aishore replay update`.
3. Run `.aishore/bin/aishore gate fast` and fix what it finds.
4. Commit on the base branch. `aishore start` refuses to run until the harness is committed,
   because a worktree without it would have no hooks.

Put `.aishore/bin` on PATH or alias `aishore` to `.aishore/bin/aishore`. The examples below
assume one of these.

Update: `aishore update` (or re-run install.sh). This keeps `aishore.toml` and ENGINEERING.md.
Both fetch through the GitHub API with `GITHUB_TOKEN`, `GH_TOKEN` or a `gh auth` login when
present, so a private fork works (`AISHORE_REPO=owner/name`).

## Operating procedure

Every `aishore` command runs from the main checkout. Claude Code runs only in a worktree.

### 0. Plan the work (optional, for anything bigger than one task)

In Claude Code on the base branch: `/decompose <goal or issue>`. It splits the goal into ordered
tasks that each fit one acceptance table and the budgets. Refactors with identical replay come
first, then one behavior change per task. You approve the plan, and it scaffolds the task ids.

### 1. Brief the task (you, on the base branch)

The brief is the only definition of "right" the implementer is held to. Every gap in it is a
defect the gates will let through.

```
/brief T-042 trail the stop to the last swing low
```

`/brief` works in Claude Code and does four things:
- It grounds itself in the code: the types to reuse, the call sites, and the minimal allowlist.
- It asks you only the decisions the code cannot answer: boundaries, failure behavior, and
  what is out of scope.
- It writes spec.md, task.toml and the acceptance tests.
- It checks the tests are red for the right reason: missing behavior, not a broken test.

For a fix, one test reproduces the bug. Without Claude, `aishore new T-042 "title"` scaffolds
the same files for you to fill.

Then have an independent reviewer attack the brief:

```
aishore brief-review T-042
```

The reviewer writes up to three counterexamples: plausible wrong implementations of the
allowlisted files. The harness runs your acceptance tests against each one in a scratch
worktree. Results go to `tasks/T-042/brief-review.md`, alongside the reviewer's open questions:
- **GAP**: the tests pass a wrong implementation. Add the reviewer's row and a test for it,
  then re-run.
- **caught**: the tests already reject it.

Delete every placeholder line, then:

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

### 3b. Headless: `aishore run T-042 [--approve-plan]`

`aishore run` starts the task if needed, then:
1. The implementer runs headless in the worktree with the same hooks and writes PLAN.md.
2. The reviewer attacks the plan. REVISE sends the points back once. A second REVISE stops the
   run for you: edit PLAN.md or the spec, then `aishore run T-042 --approve-plan`. That flag
   records your approval and skips the reviewer's plan review.
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
acceptance tests: make them pass", or re-run `aishore run T-042`. `/triage T-042` sorts each
REAL finding into "spec requires it", "reviewer preference", or "spec gap", and recommends
which to adopt.

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

`/triage T-042` reads it and proposes the spec edit or split. ESCALATE.md is a statement about the spec or the architecture. Fix the spec or split the task,
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

`commands.tests` must not run `tests/acceptance`. The profiles handle this: pytest gets
`--ignore`, and node acceptance files are named `*.accept.js|ts`, which no default discovery
picks up. The acceptance step runs
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
| `acceptance.assert_pattern` | a finding is REAL only when its output matches: a failed assertion, not a crash |
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
- On the base branch: `/decompose`, `/brief`, `/triage`, `/retro`, `/aishore-setup`. Never
  implement there; the hooks guard task branches only.
- A request to edit a human-owned file is answered by changing the spec, never by permission.
- Never ask the implementer session to review its own diff, and never use a subagent inside it
  for review. Both inherit its context and its mistakes.
- Keep CLAUDE.md and ENGINEERING.md short. A rule broken twice becomes a gate or is deleted.

## Records

Run `/retro` weekly. It reads the log, escalations and findings, and proposes the next gate, rule
deletions, and budget changes, each backed by the rows that justify it.

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
- A finding is REAL only when its test fails with an assertion (`assert_pattern`). A test that
  crashes, errors or does not collect is invalid. The generic profile has no pattern: there,
  any failure counts as REAL, so read the test. Vitest and jest pass when no test is collected,
  so a misplaced test shows as "already passes", never as a false red.

## Development

```
bin/aishore selftest     # installs into throwaway python, node and shell repos; drives every gate
ruff check aishore
```

The selftest needs pytest (and node for the node profile). It never calls a model: a stub
`claude` plays the reviewer and the headless implementer.
