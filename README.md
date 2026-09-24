# aishore

An engineering harness for Claude Code. Claude implements; the harness owns correctness.

| Mechanism | Effect |
|---|---|
| Human-owned briefs | spec and acceptance tests are written or approved by you; agents cannot change them |
| Task worktrees | one worktree and branch (`t/T-042`) per task; human-owned paths are read-only there |
| Blocking hooks | edits outside the allowlist, writes to locked paths, gate bypasses, and red finishes are refused |
| Diff gate | ownership, allowlist, gate weakening, LOC budget, new files, new classes |
| Oracles | per-task acceptance tests, replay against goldens, mutation on changed Python lines |
| Independent reviewer | a different model, headless and read-only; a finding counts only if its test fails on the branch |
| Human merge | full gate, diff, your y/N, logged outcome |

Stdlib Python 3.11+. Target projects can use any language; gates and test runners are commands
in `aishore.toml`. Profiles: `python`, `node` (node test runner, vitest, jest), `generic`.

## Requirements

- `python3` >= 3.11 and git >= 2.30 on PATH
- Claude Code, logged in with access to the implementer and reviewer models
- the project's own test runner
- a non-root user (file permissions do not bind root)

## Install

From the repository root, on the base branch:

```
curl -fsSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
```

Options: `bash -s -- --profile python|node|generic`. `AISHORE_REF` selects a branch or tag;
`GITHUB_TOKEN`, `GH_TOKEN` or a `gh auth` login is used when present.

| Path | Content | On update |
|---|---|---|
| `.aishore/aishore/`, `.aishore/bin/aishore` | harness and CLI | replaced |
| `aishore.toml` | commands, src roots, test runner, models, budgets, locked paths | kept |
| `ENGINEERING.md` | engineering rules; section 3 is project-specific | kept |
| `CLAUDE.md` | imports ENGINEERING.md and the role file | appended once |
| `.claude/settings.json` | four hooks, deny rules for `git push` and `sudo` | merged |
| `.claude/commands/implement.md` | `/implement` | replaced |
| `.claude/skills/` | `/brief`, `/decompose`, `/aishore-setup`, `/triage`, `/retro` | replaced |
| `.gitignore` | `.aishore/state/`, `PLAN.md`, `ESCALATE.md`, `tests/_review/` | merged |
| `.github/workflows/aishore-verify.yml` | full gate on pull requests and the base branch | kept |
| `docs/adr/0000-template.md` | decision record template | kept |

A pre-existing bash aishore install (`.aishore/aishore` script, `.aishore/data/`, its CLAUDE.md
section) is removed. `backlog/` is not touched.

Setup:

1. Run `/aishore-setup` in Claude Code on the base branch. It makes the gate commands pass,
   drafts ENGINEERING.md section 3 and `docs/architecture.md`, proposes locked schema and
   interface paths, and proposes a replay command. Review the diff.
2. Run `.aishore/bin/aishore gate fast`.
3. Commit on the base branch. `aishore start` refuses to run until the harness is committed.

Update with `aishore update [--ref REF]`. Examples below assume `.aishore/bin` is on PATH.

## Workflow

All `aishore` commands run from the main checkout. Implementation runs only in a task worktree.

| Step | Where | Command |
|---|---|---|
| Plan a goal into tasks | Claude Code, base branch | `/decompose <goal or issue>` |
| Brief one task | Claude Code, base branch | `/brief T-042 <intent>` |
| Attack the brief | shell | `aishore brief-review T-042` |
| Validate and commit | shell | `aishore validate T-042`, then `git commit` |
| Start | shell | `aishore start T-042` |
| Implement, interactive | Claude Code, worktree | `/implement` |
| Implement, headless | shell | `aishore run T-042 [--approve-plan]` |
| Review the plan (tier 1) | shell | `aishore plan-review T-042` |
| Review the diff (tiers 1-2) | shell | `aishore review T-042` |
| Adopt proven findings | shell | `aishore adopt T-042 1 3` |
| Triage findings or an escalation | Claude Code, base branch | `/triage T-042` |
| Merge | shell | `aishore merge T-042` |
| Abandon | shell | `aishore abandon T-042 "reason"` |
| Improve the process | Claude Code, base branch | `/retro` |

### Brief

The brief (`tasks/T-042/spec.md`, `task.toml`, acceptance tests) is the only definition of done.

`/brief` does four things:

- reads the code to find the types to reuse, the call sites, and the minimal allowlist;
- asks only the decisions the code cannot answer: boundaries, failure behavior, scope;
- writes the brief;
- confirms the tests fail for the right reason. For a fix, one test reproduces the bug.

`aishore new T-042 "title"` scaffolds the files without Claude.

`aishore brief-review T-042` has the reviewer write up to three counterexamples. Each is a
plausible wrong implementation of the allowlisted files. Each runs against the acceptance tests
in a scratch worktree that holds the brief as it is on disk. The results go to
`tasks/T-042/brief-review.md`, together with the reviewer's open questions:

| Result | Meaning | Action |
|---|---|---|
| GAP | the tests pass a wrong implementation | add the proposed row and test, re-run |
| caught | the tests reject it | none |
| invalid | the counterexample errored or wrote outside `allow` | none |

Delete every `AISHORE_PLACEHOLDER` line before committing.

### Start

`aishore start` does the following, in order:

1. validates the task;
2. requires the acceptance tests to fail on the base branch;
3. creates `../.wt/<repo>-T-042` on branch `t/T-042`;
4. runs `commands.setup` there;
5. makes human-owned paths read-only.

### Implement

Interactive: run `cd ../.wt/<repo>-T-042 && claude`, then `/implement`. Claude writes PLAN.md and
waits. You approve or cut the plan; for tier 1, run `aishore plan-review` first. Claude then
builds under the hooks:

| Hook | Event | Effect |
|---|---|---|
| guard_edit | PreToolUse Edit/Write | blocks locked paths, `.aishore/`, and files outside `allow`; fails closed |
| guard_bash | PreToolUse Bash | blocks push, branch and history changes, git aliases, permission changes, dependency installs, golden updates, shell writes to locked paths |
| post_edit | PostToolUse Edit/Write | runs the `[format]` command for the extension; feeds problems back |
| stop | Stop | once code has changed, blocks a red finish twice, then requires ESCALATE.md |

Headless: `aishore run T-042` runs these steps:

1. starts the task if needed;
2. the implementer writes PLAN.md;
3. the reviewer approves or asks for revisions once;
4. the implementer builds to green;
5. for tiers 1 and 2, the diff is reviewed and proven findings go back to the implementer once.

It never merges. State (session, plan approval, build) is kept in the worktree, and re-running
resumes from it. After two REVISE verdicts it stops. Edit PLAN.md or the spec, then run
`aishore run T-042 --approve-plan`.

### Review

`aishore review` runs the reviewer in the worktree. The reviewer is `claude -p` with the reviewer
model, Read/Grep/Glob only, and no access to the implementer session. Each finding carries a
test, and the harness runs it with `acceptance.cmd`:

| Verdict | Condition |
|---|---|
| REAL | an assertion fails, or production code raises |
| discard | the test passes |
| invalid | the test itself errors, crashes, or does not collect |

Results go to `tasks/T-042/findings.md`. `aishore adopt` commits the chosen findings as
acceptance tests on main and syncs them into the worktree.

### Merge and escalation

`aishore merge` does the following:

- refuses a worktree that is not on `t/T-042`;
- runs the full gate and commits the work;
- shows the diff stat, the replay diff, and for tier 1 the full diff;
- asks y/N and records your minutes, the gate that caught a problem, and the missing gate;
- on yes, merges, writes approved goldens, commits the records, and removes the worktree.

ESCALATE.md means the spec or architecture must change. Run `/triage` to get a proposed fix,
then `aishore abandon` to file the escalation and remove the worktree. To change a spec
mid-task, commit the change on main and run `aishore sync T-042`.

`aishore status` lists open worktrees with PLAN, ESCALATE, and finding flags.

## Commands

| Command | Effect |
|---|---|
| `new ID "title"` | scaffold `tasks/ID/` and a placeholder acceptance test |
| `validate ID` | check a task against the schema |
| `brief-review ID` | run reviewer counterexamples against the acceptance tests |
| `start ID` | prove red, create the worktree, lock paths |
| `run ID [--approve-plan]` | headless plan, build, review, one fix round |
| `plan-review ID` | reviewer attacks PLAN.md |
| `review ID` | reviewer checks the diff; findings are executed |
| `adopt ID N...` | promote findings to acceptance tests |
| `sync ID` | merge the base branch into the task branch |
| `merge ID [--yes]` | full gate, approval, merge, log |
| `abandon ID "why"` | file the escalation, remove the worktree and branch |
| `status` | open task worktrees |
| `gate fast\|full` | run the gate in the current checkout |
| `replay check\|diff\|update [CASE...]` | replay oracle |
| `entropy` | append size and complexity to `entropy.csv` |
| `install`, `update`, `selftest`, `version` | setup and maintenance |

## Skills

| Skill | Purpose |
|---|---|
| `/aishore-setup` | fit the harness to the repository: gates, architecture rules and their enforcement, module map, locked paths, replay |
| `/decompose` | split a goal into ordered tasks that each fit one acceptance table and the budgets |
| `/brief` | write a grounded brief with red-for-the-right-reason acceptance tests |
| `/triage` | propose the spec change or split for an escalation; sort findings into adopt, reject, or spec gap |
| `/retro` | propose the next gate, rule deletions, and budget changes from `tasks/log.csv` |

Skills draft human-owned files for your review. Judgments come from the separate reviewer process.

## Gates

| Step | Fast (Stop hook) | Full (merge, CI) |
|---|---|---|
| no ESCALATE.md | | yes |
| lint, types, imports, tests (`[commands]`) | yes | yes |
| diffcheck (task branches) | yes | yes |
| acceptance tests of merged tasks and the current task | yes | yes |
| replay | | yes |
| mutation on changed Python lines, by tier | | yes |

Tests of open tasks are red on main by design and never gate other work. `commands.tests` must
not run `tests/acceptance`. The pytest profile passes `--ignore`. Node acceptance files are
named `*.accept.js|ts`, a pattern that no default discovery matches.

Diffcheck detects gate weakening (skips, suppressions, loosened tolerances) in Python, JS/TS,
Go, Rust, and shell. Extensionless scripts are classified by shebang.

## Configuration

`aishore.toml`:

| Key | Meaning |
|---|---|
| `base`, `worktree_root` | base branch; worktree parent (`../.wt`) |
| `src` | production roots for the LOC budget, new files, new classes, and mutation |
| `commands.setup` | runs in each new worktree before paths lock |
| `commands.lint`, `types`, `imports`, `tests` | gate steps; empty skips |
| `acceptance.cmd` | runs acceptance, finding, and counterexample tests; `{tests}` is the file list |
| `acceptance.fail_codes`, `empty_codes` | exit codes for "a test failed" and "no tests found" |
| `acceptance.assert_pattern` | output that marks a failed assertion; empty accepts any failure |
| `acceptance.path`, `lang` | test file template (`{name}` is `t_042` or `t_042_f1`); language for reviewer tests |
| `format` | formatter per extension; `{file}` is the edited file |
| `replay.cmd`, `cases`, `golden` | one JSON event per line for the recorded input `{input}`; empty disables replay |
| `mutation.*` | test command, mutant cap, timeout factor |
| `implement.model`, `implement.headless` | implementer model; headless command for `run` |
| `review.model`, `review.cmd`, `review.context` | reviewer model and command; files sent with every review |
| `defaults.*` | per-task LOC budget, new files, new classes |
| `ownership.locked` | human-owned globs |

Vitest acceptance runs use a shipped config that loads the project's own config and adds
`tests/acceptance` and `tests/_review` to its `include`. Jest runs get `--roots` and
`--testMatch`.

Task schema: `.aishore/aishore/scaffold/SCHEMA.md`, with a JSON Schema beside it.

## Session rules

- One fresh session per task, started in its worktree.
- On the base branch, only skills; never implement there. Hooks guard task branches only.
- A request to edit a human-owned file is answered by changing the brief.
- The implementer never reviews its own diff, directly or through a subagent.

## Records

| File | Content |
|---|---|
| `tasks/log.csv` | one row per merged, rejected, escalated, or abandoned task |
| `tasks/ID/` | brief, brief review, plan review, review, findings, escalations |
| `entropy.csv` | files, LOC, dependencies, and Python complexity and dead code |

## Limits

- guard_bash is heuristic. Writes it misses are caught by diffcheck at merge.
- A hook that times out does not block.
- The Stop hook allows the third red stop. The merge gate still refuses red work.
- Mutation covers changed Python lines only, up to `max_mutants`, with a fixed operator set.
- Reviewer and counterexample code runs in the worktree or a scratch worktree. Read finding
  tests before adopting them.
- The generic profile has no `assert_pattern`, so there any failing finding counts as REAL.

## Development

```
bin/aishore selftest
ruff check aishore
```

The selftest installs into throwaway Python, flat-layout, node, vitest, and shell repositories
and drives every command and hook through the CLI. A stub `claude` stands in for the models.
It needs pytest, and node and npm for the node and vitest parts.
