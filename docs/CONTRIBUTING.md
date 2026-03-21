# Contributing to aishore

Thanks for your interest in contributing to aishore!

## Development Setup

```bash
git clone https://github.com/simonplant/aishore.git
cd aishore

# No build step needed — the tool is ready to use
.aishore/aishore help
```

## Requirements

- Bash 4.4+
- jq
- shellcheck (for linting)
- git
- On macOS: `brew install coreutils` (for `gtimeout`)

## Code Style

### Bash

- `set -euo pipefail` at the top of every script
- Quote all variables: `"$var"` not `$var`
- `[[ ]]` for conditionals, not `[ ]`
- `$(command)` for substitution, not backticks
- `${var:-default}` for optional variables
- Declare and assign on separate lines to avoid masking return values (`local var; var=$(cmd)`)

### Naming

| Kind               | Convention         | Example              |
|--------------------|--------------------|----------------------|
| Functions          | `snake_case`       | `run_sprint`         |
| Local variables    | `snake_case`       | `item_id`            |
| Constants/exports  | `UPPER_SNAKE_CASE` | `AISHORE_VERSION`    |

## Linting and Testing

Run all of these before submitting a PR:

```bash
# Lint
shellcheck .aishore/aishore

# Syntax check
bash -n .aishore/aishore
bash -n install.sh

# Smoke test
.aishore/aishore help
.aishore/aishore version
.aishore/aishore metrics

# Validate JSON
jq empty backlog/*.json

# Regenerate checksums (if you changed any .aishore/ files)
.aishore/aishore checksums
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run shellcheck and smoke tests (see above)
5. Regenerate checksums if you changed files in `.aishore/`
6. Commit using conventional commits (see below)
7. Push and open a PR

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix      | Use for                  |
|-------------|--------------------------|
| `feat:`     | New feature              |
| `fix:`      | Bug fix                  |
| `docs:`     | Documentation only       |
| `refactor:` | Code restructuring       |
| `test:`     | Adding or fixing tests   |
| `chore:`    | Maintenance, CI, tooling |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture and design decisions.

## Agent Prompt Authoring

aishore uses markdown prompt files in `.aishore/agents/` to define each agent's behavior. If you want to modify how an agent works, this is where to look.

### Agent files

| File | Agent | Controls |
|------|-------|----------|
| `developer.md` | Developer | How features are implemented — process, rules, output format |
| `validator.md` | Validator | How acceptance criteria and intent are verified |
| `tech-lead.md` | Tech Lead | How bugs and features are groomed for technical clarity |
| `product-owner.md` | Product Owner | How features are groomed for value alignment and backlog is populated |
| `architect.md` | Architect | How architecture reviews are conducted |

### How prompts are assembled

The orchestrator (`run_agent()`) assembles the final prompt by combining:

1. The agent's markdown file (`.aishore/agents/<role>.md`)
2. Project context files (`CLAUDE.md`, `PRODUCT.md`, `ARCHITECTURE.md` — auto-detected)
3. The sprint item spec (for developer and validator)
4. The completion contract (appended automatically)

You only edit the agent markdown file. The orchestrator handles injection of context and the completion contract.

### Modifying agent prompts

1. Edit the relevant file in `.aishore/agents/`
2. Run `.aishore/aishore checksums` to update checksums
3. Test by running a sprint: `.aishore/aishore run --quick` (use `--quick` to skip the maturity protocol for faster iteration)
4. Review the agent's output in `.aishore/data/logs/`

### Guidelines

- Keep prompts focused on the agent's role — don't duplicate orchestrator logic
- Use markdown structure (headings, lists, tables) for clarity
- Behavioral changes that affect all agents (e.g., new completion signals) belong in the orchestrator, not in individual prompts
- Test prompt changes against a real backlog item before committing

## Contributor License Agreement (CLA)

By submitting a pull request to this project, you agree that:

1. **You grant the project maintainer (Simon Plant) a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license** to use, reproduce, modify, distribute, sublicense, and otherwise exploit your contributions in any form and for any purpose, including under licenses other than the AGPL-3.0.

2. **You confirm that you have the right** to grant this license for all contributions you submit.

3. **You understand that your contributions are public** and that a record of the contribution (including your name and email) may be maintained indefinitely.

4. **This CLA allows the maintainer to relicense** the software (including your contributions) under different terms if needed, without requiring further permission from you.

This agreement ensures the project can evolve its licensing while incorporating community contributions. The project is currently licensed under the Apache License 2.0.

## Questions?

Open an issue for questions or suggestions.
