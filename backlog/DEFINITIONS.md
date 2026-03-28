# Sprint Definitions

## Definition of Ready (DoR)

| # | Gate | Required |
|---|------|----------|
| 1 | **Intent** | `intent` field states what must be true when done |
| 2 | **Steps** | Clear enough for implementation |
| 3 | **AC** | Acceptance criteria are verifiable |
| 4 | **No blockers** | Dependencies resolved |
| 5 | **Right size** | Completable in one sprint |
| 6 | **readyForSprint** | Tech Lead has marked it ready |

## Definition of Done (DoD)

| # | Gate |
|---|------|
| 1 | Implementation matches AC |
| 2 | All tests pass (existing + new) |
| 3 | Type-check, lint, tests all pass |
| 4 | Each AC verified (verify commands pass, validator confirms) |
| 5 | Regression suite passes (no prior sprint's guarantees broken) |

## Priority Levels

| Priority | Code | Description |
|----------|------|-------------|
| Must | P0 | Critical, blocking other work |
| Should | P1 | Important, not blocking |
| Could | P2 | Nice to have |
| Future | P3 | Long-term consideration |

## Size Estimates

| Size | Scope |
|------|-------|
| XS | Single file, < 50 lines |
| S | Few files, < 200 lines |
| M | Multiple files, 200-500 lines |
| L | Significant feature, multiple components |
| XL | Large feature — consider splitting |

## Commander's Intent

A non-negotiable directive — what must be true when done. The developer follows it when the spec is ambiguous. Items without intent cannot enter a sprint.

**Rules:** Write like an order, not a description. State outcome, not implementation. 1-2 sentences max.

| Good | Bad (and why) |
|------|---------------|
| "Ops must know instantly if the service is alive or dead." | "Add health check endpoint" (implementation, not outcome) |
| "Users authenticate securely or are told why not. Never a blank screen." | "Improve auth" (vague, no bar) |
| "Large uploads complete or give clear progress. No frozen screens." | "Make it faster" (no specific bar) |
| "Webhooks deliver or tell the user why not. Silent failure is unacceptable." | "Improve webhook reliability" (vague) |

## Backlog Item Structure

```json
{
  "id": "FEAT-001",
  "title": "Short title",
  "intent": "What must be true when done.",
  "description": "Context and technical notes",
  "priority": "should",
  "category": "core",
  "steps": ["Step 1", "Step 2"],
  "acceptanceCriteria": [
    "Plain string AC (validated by judgment)",
    {"text": "CLI prints usage on --help", "verify": ".aishore/aishore help | grep -q Usage"}
  ],
  "scope": ["src/**", "tests/**"],
  "dependsOn": ["FEAT-000"],
  "status": "todo",
  "passes": false,
  "readyForSprint": false
}
```

### Field Reference

| Field | Type | Set by | Description |
|-------|------|--------|-------------|
| `id` | string | CLI (`backlog add`) | Unique item ID (e.g., `FEAT-001`, `BUG-042`) |
| `title` | string | User / groom agent | Short title |
| `intent` | string | User / groom agent | Commander's intent — what must be true when done. Hard gate: ≥20 chars required for sprint |
| `description` | string | User / groom agent | Full context and scope boundaries |
| `priority` | string | User / groom agent | `must` \| `should` \| `could` \| `future` |
| `category` | string | User / groom agent | Arbitrary tag for filtering (e.g., `api`, `docs`) |
| `steps` | string[] | User / groom agent | Implementation steps |
| `acceptanceCriteria` | (string \| object)[] | User / groom agent | Plain strings or `{text, verify}` objects. `verify` is a shell command (an eval) |
| `scope` | string[] | User / groom agent | File glob patterns constraining where changes should land |
| `dependsOn` | string[] | User / groom agent | Item IDs that must be done before this item can be picked |
| `status` | string | Orchestrator / CLI | `todo` \| `in-progress` \| `done` \| `skip` |
| `passes` | boolean | Orchestrator | `true` when sprint passed validation |
| `readyForSprint` | boolean | Groom agent / CLI | `true` when item passes readiness gates |
| `groomedAt` | string | Groom agent / CLI | Date of last grooming (`YYYY-MM-DD`) |
| `groomingNotes` | string | Groom agent / CLI | Free-text grooming notes |
| `completedAt` | string | Orchestrator | ISO timestamp when sprint completed |
| `lastFailReason` | string | Orchestrator | Reason for most recent sprint failure |
| `lastFailAt` | string | Orchestrator | ISO timestamp of most recent failure |
| `failCount` | integer | Orchestrator | Number of sprint failures |

## Executable AC (Verify Commands)

AC entries with a `verify` field are **evals** — shell commands that prove the criterion is met. They are:

1. **Run after each sprint** as part of validation (failures trigger retries)
2. **Saved to the regression suite** on sprint success (`backlog/archive/regression.jsonl`)
3. **Run before every future sprint** as pre-flight (protects prior work from regressions)

Prefer verify commands over plain-string AC wherever behavior is observable via shell command. Plain-string AC are validated by the Validator agent's judgment; verify commands are validated deterministically.
