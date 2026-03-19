# Sprint Definitions

## Definition of Ready (DoR)

An item is ready for sprint when:

| #   | Criteria                     | Description                                                    |
| --- | ---------------------------- | -------------------------------------------------------------- |
| 1   | **Commander's Intent**       | The `intent` field states what must be true when done          |
| 2   | **Actionable Steps**         | Steps are clear enough for implementation                      |
| 3   | **Testable AC**              | Acceptance criteria can be verified                            |
| 4   | **No Blockers**              | Dependencies are resolved                                      |
| 5   | **Right Size**               | Can be completed in one sprint                                 |
| 6   | **readyForSprint: true**     | Tech Lead has marked it ready                                  |

## Definition of Done (DoD)

An item is done when:

| #   | Criteria                     | Description                                                    |
| --- | ---------------------------- | -------------------------------------------------------------- |
| 1   | **Code Complete**            | Implementation matches acceptance criteria                     |
| 2   | **Tests Pass**               | All tests pass (existing + new)                               |
| 3   | **Validation Pass**          | Type-check, lint, tests all pass                              |
| 4   | **AC Verified**              | Each acceptance criterion is met                              |
| 5   | **No Regressions**           | Existing functionality still works                            |

## Priority Levels

| Priority | Code | Description                           |
| -------- | ---- | ------------------------------------- |
| Must     | P0   | Critical, blocking other work         |
| Should   | P1   | Important, not blocking               |
| Could    | P2   | Nice to have                          |
| Future   | P3   | Long-term consideration               |

## Size Estimates

| Size | Typical Scope                                    |
| ---- | ------------------------------------------------ |
| XS   | Single file change, < 50 lines                   |
| S    | Few files, < 200 lines, straightforward          |
| M    | Multiple files, new patterns, 200-500 lines      |
| L    | Significant feature, multiple components         |
| XL   | Large feature, consider splitting                |

## Writing Commander's Intent

Intent is a non-negotiable directive — what must be true when the work is done. The developer follows it when the spec is ambiguous or steps seem wrong. Items without intent cannot enter a sprint.

### Rules

- Write it like an order, not a description
- State the outcome, not the implementation
- Include the consequence of failure when it matters
- Keep it to 1-2 sentences

### Good Examples

| Title | Intent |
|-------|--------|
| Add health check endpoint | Ops must know instantly if the service is alive or dead. No false positives. |
| OAuth2 login flow | Users must authenticate securely or be told exactly why they can't. Never a blank screen. |
| Fix timeout on large uploads | Large uploads must complete or give clear progress. Users must never stare at a frozen screen. |
| Webhook retry logic | Webhooks must deliver or tell the user why not. Silent failure is not acceptable. |
| Docker multi-stage build | Developers must get a working container or a clear error. Build time under 3 minutes. |
| Rate limiting | The API must stay responsive under load. Abusers get throttled, legitimate users never notice. |

### Bad Examples (and why)

| Bad Intent | Problem | Better |
|-----------|---------|--------|
| "Improve webhook reliability" | Vague — improve how? by how much? | "Webhooks must deliver or tell the user why not." |
| "Add Docker support" | Describes implementation, not outcome | "Developers must get a working container or a clear error." |
| "Make it faster" | No specific bar, no consequence | "Page load must be under 2 seconds or users abandon checkout." |
| "Refactor auth module" | Refactoring is a method, not an outcome | "Auth must handle 10x current load without token leaks." |

## Backlog Item Structure

```json
{
  "id": "FEAT-001",
  "title": "Short title",
  "intent": "Webhooks must deliver or tell the user why not. Silent failure is not acceptable.",
  "description": "Full description — what to build, context, technical notes, user scenarios",
  "priority": "should",
  "category": "core",
  "steps": ["Step 1", "Step 2"],
  "acceptanceCriteria": ["AC 1", "AC 2"],
  "scope": ["src/**", "tests/**"],
  "status": "todo",
  "passes": false,
  "readyForSprint": false,
  "groomedAt": "2026-01-24",
  "groomingNotes": "Notes from grooming"
}
```
