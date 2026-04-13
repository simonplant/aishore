# Quickstart: Zero to First Completed Sprint

Go from `git clone` to a completed sprint in under 10 minutes.

## 1. Prerequisites

You need these installed before starting:

| Tool | Check | Install |
|------|-------|---------|
| Bash 4.4+ | `bash --version` | Pre-installed on Linux; macOS: `brew install bash` |
| Git | `git --version` | [git-scm.com](https://git-scm.com) |
| jq | `jq --version` | `brew install jq` / `apt install jq` |
| Claude Code CLI | `claude --version` | [docs.anthropic.com/en/docs/claude-code](https://docs.anthropic.com/en/docs/claude-code) |

macOS only: `brew install coreutils` (provides `gtimeout`).

Verify everything at once:

```bash
bash --version | head -1 && git --version && jq --version && claude --version
```

Output (approximate):

```
GNU bash, version 5.2.37(1)-release ...
git version 2.47.1
jq-1.7.1
1.0.x (Claude Code)
```

## 2. Install aishore

From your project root:

```bash
curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash

# Or via GitHub API (authenticated, bypasses CDN cache):
gh api repos/simonplant/aishore/contents/install.sh --jq '.content' | base64 -d | bash
```

Output (approximate):

```
Installing aishore...
  ✓ Downloaded .aishore/aishore
  ✓ Downloaded .aishore/VERSION
  ...
  ✓ Checksums verified
aishore installed successfully. Run: .aishore/aishore init
```

**Or clone and copy** (no piping to bash):

```bash
git clone --depth 1 https://github.com/simonplant/aishore.git /tmp/aishore-install
cp -r /tmp/aishore-install/.aishore .
rm -rf /tmp/aishore-install
```

<details>
<summary>Manual install</summary>

```bash
cp -r /path/to/aishore/.aishore /path/to/your/project/
```

</details>

## 3. Initialize

Run the setup wizard:

```bash
.aishore/aishore init
```

The wizard checks prerequisites, detects your project type, configures validation, and creates `backlog/`. Accept the defaults or customize as prompted.

Output (approximate):

```
aishore init
============
Checking prerequisites...
  ✓ bash 5.2
  ✓ jq 1.7.1
  ✓ git 2.47
  ✓ claude 1.0.x

Detecting project type...
  → Node.js project detected

Validation command: npm test && npm run lint
Accept? [Y/n]: Y

  ✓ Created backlog/backlog.json
  ✓ Created backlog/bugs.json
  ✓ Created backlog/sprint.json
  ✓ Created backlog/DEFINITIONS.md

Ready! Add your first backlog item with: .aishore/aishore backlog add
```

For fully automated setup (no prompts): `.aishore/aishore init -y`

**Set your validation command** in `.aishore/config.yaml` if auto-detection missed it:

```yaml
validation:
  command: "npm test && npm run lint"   # Your stack's test/lint command
```

## 4. Write Your Product Doc

aishore works best when you start from a product requirements document. Write a `docs/PRODUCT.md` (or fill in the template `init` created) describing what you're building — vision, features, constraints. This is the input the groomer uses to create backlog items.

**Define the working core.** The single most important thing in PRODUCT.md is the core definition: the one end-to-end path the product exists for. "A user opens the app and sees their items list, populated from a real API, backed by a real database." This drives everything — the groomer assigns items to core vs feature tracks, the architect generates core verification, and the engine blocks feature work until the core passes. Be specific.

Even a short description helps. The more specific you are, the better the generated items will be.

## 5. Populate the Backlog

Generate backlog items from your product doc:

```bash
.aishore/aishore backlog populate
```

The groomer agent reads your PRODUCT.md, creates sprint-ready items with intent, steps, and executable acceptance criteria. It assigns each item to a track: `core` (builds the primary end-to-end path) or `feature` (decorates it). Core items are generated first and right-sized for single sprints.

Verify what was created:

```bash
.aishore/aishore backlog list
.aishore/aishore backlog show FEAT-001   # Full detail of one item
```

**Edit, add, or remove items** to shape the backlog:

```bash
.aishore/aishore backlog edit FEAT-001 --json '{"priority": "must", "intent": "..."}'
.aishore/aishore backlog add --json '{"title": "...", "intent": "...", "acceptanceCriteria": [{"text": "...", "verify": "..."}]}'
.aishore/aishore backlog rm FEAT-003 --force
```

Every item needs a **commander's intent** — a directive stating what must be true when done. Not "add health check" but "ops must know instantly if the service is alive or dead." Intent gates sprint entry and guides the developer when specs are ambiguous.

## 6. Groom

Grooming refines items — adds steps, tightens AC, attaches verify commands, and marks items sprint-ready:

```bash
.aishore/aishore groom
```

Check readiness:

```bash
.aishore/aishore backlog check --all
```

## 7. Run Your First Sprint

```bash
.aishore/aishore run
```

The sprint goes through these stages:

```
[Core Gate] → Pick Item → Create Branch → Pre-flight Check → Developer Agent → Validation → Validator Agent → Merge → [Core Re-check] → Archive
```

> Stages in brackets are upcoming — see [Roadmap](ROADMAP.md).

Expected output (abbreviated):

```
Sprint 1 of 1
=============
  → Picked: FEAT-001 — Add health check endpoint
  → Branch: aishore/FEAT-001
  → Pre-flight: PASS

  ▶ Developer agent running...
    Phase 1: Implement
    Phase 2: Critique
    Phase 3: Harden
  ✓ Developer agent complete

  → Validation: PASS
  ▶ Validator agent running...
  ✓ Validator: PASS

  → Merging aishore/FEAT-001 → main
  → Pushing to origin
  → Archived FEAT-001

Sprint complete: 1 passed, 0 failed
```

**What happened:** The developer agent read the item, explored your codebase, implemented the feature through three phases (implement, critique, harden), then the validator confirmed it meets acceptance criteria and intent. The branch was merged and the item archived.

## 8. Verify Success

Check the git log to see the merge:

```bash
git log --oneline -5
```

Output (approximate):

```
abc1234 Merge branch 'aishore/FEAT-001'
def5678 feat: add health check endpoint
...
```

Review what was built:

```bash
git diff HEAD~2..HEAD --stat
```

## 9. Troubleshooting

**Items not being picked?**
- Missing or short intent (<20 chars) → `backlog edit <ID> --intent "..."`
- Not marked ready → run `groom` or `backlog edit <ID> --ready`
- Dependency blocking → check `dependsOn` field
- Run `backlog check <ID>` to see which gates fail

**Core check fails and features are blocked?** (upcoming feature)
The working core isn't passing. Only `track: "core"` items will be picked until it does. Run your `CORE_CMD` manually to see what's broken. If you don't have core items in the backlog, run `scaffold` to generate them.

**Pre-flight fails?**
Your baseline is broken. Run your validation command manually and fix:
```bash
npm test && npm run lint   # or whatever your validation command is
```

**Sprint failing after developer runs?**
- Use retries: `.aishore/aishore run --retries 2` (failure context is fed back to the developer on retry)
- Check logs: `ls -lt .aishore/data/logs/` (most recent agent log has failure details)

**Stuck state?**
```bash
rm .aishore/data/status/result.json     # Clear completion signal
rm -rf .aishore/data/status/.aishore.lock   # Clear concurrency lock
```

**Reinstall (preserves backlog):**
```bash
gh api repos/simonplant/aishore/contents/install.sh --jq '.content' | base64 -d | bash -s -- --force
.aishore/aishore init
```

## Next Steps

- Drain the backlog: `.aishore/aishore run done`
- Must-haves only: `.aishore/aishore run p0`
- With retries: `.aishore/aishore run done --retries 2`
- Establish working core: `.aishore/aishore scaffold`
- Architecture review: `.aishore/aishore review`
- Full command reference: `.aishore/aishore help`
- Full docs: [README.md](../README.md)
