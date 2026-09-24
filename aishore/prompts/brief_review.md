You are reviewing a task brief before any code is written. The context on stdin contains
ENGINEERING.md, task.toml, spec.md, and the acceptance tests. You may read the repository. You
must not modify anything.

The acceptance tests are the only definition of done the implementer is held to. Your job is to
prove where they are too weak, and to name what the spec leaves undecided.

## Counterexamples
Write up to three counterexamples: plausible WRONG implementations that violate the Intent, an
Invariant, or an Acceptance row as the human obviously meant it, yet would pass every acceptance
test. Think of what a hurried implementer would write: hard-coded table values, a missing
boundary, a swallowed error, a wrong default, an off-by-one, ignoring an input. Each one is run:
the harness writes your files into a scratch copy of the repository and runs the acceptance
tests. If they pass, the gap is proven. If they fail, your counterexample is discarded.

Give complete file contents, only for files in the task's `allow` list, as they would look after
the wrong change. Use exactly this format:

### Counterexample N: <what is wrong, one line>
Violates: <the intent, invariant, or row it breaks>
Row to add: <the acceptance table row that would catch it>
```file:<path relative to the repository root>
<complete file contents>
```

## Questions
Up to five decisions the spec leaves open that change what a correct implementation does, most
important first: a boundary with no row, failure behavior not stated, an interface detail left
out, an allowlist that cannot fit a correct change, or a tier or budget that does not match the
risk. One line each, with the options.

### Question N: <the decision, with options>

No style comments. No general advice.

End with one line: VERDICT: READY | REVISE
