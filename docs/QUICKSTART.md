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

Expected output:

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
```

Expected output:

```
Installing aishore...
  ✓ Downloaded .aishore/aishore
  ✓ Downloaded .aishore/VERSION
  ...
  ✓ Checksums verified
aishore installed successfully. Run: .aishore/aishore init
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

Expected output:

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

For fully automated setup (no prompts): `.aishore/aishore init --yes`

**Set your validation command** in `.aishore/config.yaml` if auto-detection missed it:

```yaml
validation:
  command: "npm test && npm run lint"   # Your stack's test/lint command
```

## 4. Write Your First Intent

Every backlog item needs a **commander's intent** — a non-negotiable directive stating what must be true when done. This is the most important field. Without it, items cannot enter a sprint.

Write intent like an order, not a description:

| Good | Bad |
|------|-----|
| "Ops must know instantly if the service is alive or dead." | "Add health check endpoint" (implementation, not outcome) |
| "Users authenticate securely or are told why not. Never a blank screen." | "Improve auth" (vague, no bar) |

Intent guides the developer agent when the spec is ambiguous and the validator when checking results.

## 5. Add a Backlog Item

```bash
.aishore/aishore backlog add \
  --title "Add health check endpoint" \
  --intent "Ops must know instantly if the service is alive or dead." \
  --desc "GET /health returns 200 with {status: ok}" \
  --priority must
```

Expected output:

```
Added FEAT-001: Add health check endpoint
  Priority: must
  Intent: Ops must know instantly if the service is alive or dead.
```

Verify it was added:

```bash
.aishore/aishore backlog list
```

Expected output:

```
backlog.json (1 item)
  FEAT-001  todo  must  Add health check endpoint
```

## 6. Groom

Grooming adds implementation steps, acceptance criteria, and marks the item sprint-ready:

```bash
.aishore/aishore groom
```

Expected output:

```
Grooming 1 item...
  ✓ FEAT-001: Added 3 steps, 2 acceptance criteria
  ✓ FEAT-001: Marked ready for sprint

Grooming complete. 1 item ready.
```

Verify readiness:

```bash
.aishore/aishore backlog check FEAT-001
```

Expected output:

```
FEAT-001: Add health check endpoint
  ✓ Intent present (52 chars)
  ✓ Steps defined (3)
  ✓ Acceptance criteria defined (2)
  ✓ No blocking dependencies
  ✓ Marked ready for sprint

All gates pass — item is sprint-ready.
```

## 7. Run Your First Sprint

```bash
.aishore/aishore run
```

The sprint goes through these stages:

```
Pick Item → Create Branch → Pre-flight Check → Developer Agent → Validation → Validator Agent → Merge → Archive
```

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

Check that the sprint completed:

```bash
.aishore/aishore backlog history
```

Expected output:

```
Completed sprints:
  FEAT-001  complete  Add health check endpoint  (2026-03-20)
```

Check the git log to see the merge:

```bash
git log --oneline -5
```

Expected output:

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

**Pre-flight fails?**
Your baseline is broken. Run your validation command manually and fix:
```bash
npm test && npm run lint   # or whatever your validation command is
```

**Sprint failing after developer runs?**
- Use retries: `.aishore/aishore run --retries 2`
- Use spec refinement: `.aishore/aishore run --retries 2 --refine`
- Check logs: `.aishore/aishore diagnose`

**Stuck state?**
```bash
rm .aishore/data/status/result.json     # Clear completion signal
rm .aishore/data/status/.aishore.lock   # Clear concurrency lock
```

**Reinstall (preserves backlog):**
```bash
rm -rf .aishore && curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
.aishore/aishore init
```

## Next Steps

- Run multiple sprints: `.aishore/aishore run 5`
- Autonomous mode: `.aishore/aishore auto done` (drains the entire backlog)
- Architecture review: `.aishore/aishore review`
- Full command reference: `.aishore/aishore help`
- Full docs: [README.md](../README.md)
