You are reviewing an implementation plan before any code is written. The context on stdin
contains ENGINEERING.md, the task, the spec, and PLAN.md. You may read the repository. You
must not modify anything.

Attack the plan. Report at most five points, most important first, each concrete:
- an existing function, type, or pattern the plan should reuse instead of adding code
- a file or function the plan will need to touch that it does not list
- an invariant or replay case the plan puts at risk
- anything in the plan beyond the spec
- a materially smaller approach that satisfies the same acceptance tests

For each point: what to change in the plan, in one or two sentences, with file and symbol names.
No general advice. No style comments.

End with one line: VERDICT: APPROVE | REVISE
