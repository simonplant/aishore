# CI / GitHub Actions

Run aishore sprints in GitHub Actions — push a backlog change, wake up to PRs.

## Quick Setup

1. Add your Anthropic API key as a repository secret: **Settings → Secrets → Actions → `ANTHROPIC_API_KEY`**

2. Copy the sample workflow:

```bash
cp .github/workflows/aishore.yml .github/workflows/aishore.yml
```

3. Push to main. The workflow triggers on schedule, manual dispatch, or when `backlog/backlog.json` changes.

## How It Works

The GitHub Action (defined in `action.yml`) runs `scripts/ci-entrypoint.sh`, which:

1. Validates that `ANTHROPIC_API_KEY` is set and `.aishore/aishore` exists
2. Installs Claude Code CLI if not present
3. Sets git identity for commits
4. Runs `.aishore/aishore run` with `--pr` mode (creates PRs instead of auto-merging)

Each sprint item gets its own feature branch and PR. Review and merge at your pace.

## Action Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | Yes | — | Anthropic API key |
| `run_args` | No | `1` | Arguments to `aishore run` (`done`, `p0`, `FEAT-123`, etc.) |
| `pr_mode` | No | `true` | Create PRs instead of merging |
| `model` | No | — | Claude model override |
| `agent_timeout` | No | `3600` | Agent timeout in seconds |
| `setup_command` | No | — | Worktree setup command (e.g. `npm install`) |
| `core_command` | No | — | Core verification command override |
| `retries` | No | `1` | Per-item retry count |

## Sample Workflows

### Nightly drain (recommended)

```yaml
name: aishore
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
    inputs:
      run_args:
        default: 'done'

permissions:
  contents: write
  pull-requests: write

jobs:
  sprint:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - name: Install dependencies
        run: sudo apt-get install -y jq
      - uses: simonplant/aishore@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          run_args: ${{ inputs.run_args || 'done' }}
```

### On backlog change

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'backlog/backlog.json'
      - 'backlog/bugs.json'
```

### Must-haves only with custom model

```yaml
- uses: simonplant/aishore@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    run_args: 'p0'
    model: 'claude-sonnet-4-6'
    agent_timeout: '1800'
```

## Environment Variables

All `AISHORE_*` environment variables work in CI. Set them in the workflow:

```yaml
env:
  AISHORE_MERGE_STRATEGY: squash
  AISHORE_STREAMING: 'false'
```

Or pass them through action inputs (`model`, `agent_timeout`, `setup_command`, `core_command`).

## Troubleshooting

**"ANTHROPIC_API_KEY is required"** — Add the secret in repository settings.

**"claude: command not found"** — The entrypoint installs Claude Code CLI automatically. Ensure Node.js is available (use `actions/setup-node`).

**Timeout** — Increase `timeout-minutes` on the job and `agent_timeout` on the action input. Default agent timeout is 3600s (1 hour).

**PR creation fails** — Ensure the workflow has `permissions: { contents: write, pull-requests: write }`. The `GITHUB_TOKEN` is provided automatically by GitHub Actions.

**Concurrent runs** — The sample workflow uses `concurrency` with `cancel-in-progress: false` so running sprints finish. Only one sprint session runs at a time.
