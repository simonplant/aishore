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
| 4 | Each AC verified |
| 5 | No regressions |

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
  "steps": ["Step 1", "Step 2"],
  "acceptanceCriteria": ["AC 1", "AC 2"],
  "scope": ["src/**", "tests/**"],
  "status": "todo",
  "readyForSprint": false
}
```
