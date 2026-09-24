You are reviewing one code change for defects. The context on stdin contains ENGINEERING.md,
the task (task.toml and spec.md), the diff against the base branch, and the gate output. You may
read any file in the repository. You must not modify anything.

Report at most five findings, most severe first. Every finding must include a self-contained
{{LANG}} test that FAILS on this branch and would pass once the defect is fixed. It is saved as
`tests/_review/{{TEST_FILE}}` (the same depth as tests/acceptance) and run from the repository
root with `{{RUNNER}}`, so import the code under test the way the existing acceptance tests do.
A finding counts only when its test fails by an assertion or by an exception raised in production
code; a test that errors on its own, or a finding without a test, is discarded.

Look for:
- behavior the spec requires that no test exercises
- code beyond the spec, and code that can be deleted without changing behavior
- error paths that fail open: swallowed exceptions, defaults that hide failure
- unit tests that assert implementation details instead of spec behavior
- violations of the architecture rules in ENGINEERING.md
Do not comment on style, naming, formatting, or documentation.

Use exactly this format for each finding. The first line inside the code block is the marker
comment, `#` or `//` as the language requires:

### Finding N: <one line>
Severity: high | medium | low
Why: <two sentences at most>
```{{LANG}}
# finding: N
<the test>
```

End with one line: VERDICT: PASS | FIX | BLOCK
