# Sprint Definitions

## Definition of Ready (DoR)

An item is ready for sprint when:

| #   | Criteria                     | Description                                                    |
| --- | ---------------------------- | -------------------------------------------------------------- |
| 1   | **Clear Value**              | The "why" is understood - ties to a user outcome               |
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

## Backlog Item Structure

```json
{
  "id": "FEAT-001",
  "title": "Short title",
  "description": "User-focused description",
  "priority": "should",
  "category": "core",
  "steps": ["Step 1", "Step 2"],
  "acceptanceCriteria": ["AC 1", "AC 2"],
  "status": "todo",
  "passes": false,
  "readyForSprint": false,
  "groomedAt": "2026-01-24",
  "groomingNotes": "Notes from grooming"
}
```
