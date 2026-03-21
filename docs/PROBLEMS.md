# Problems aishore solves

Real problems that show up when you use AI coding tools on anything beyond a single file.

---

## AI coding sessions lose all context between runs

Every time you start a new Claude Code session, the AI starts from zero. It doesn't remember what it built yesterday, what patterns it established, what decisions it made, or what it tried and rejected. You end up re-explaining context, watching the AI rediscover your codebase from scratch, and dealing with inconsistent approaches across sessions.

This gets worse as projects grow. A feature that spans multiple sessions accumulates drift — different naming conventions, conflicting patterns, duplicated logic — because the AI has no continuity between runs.

**Evidence:**
- The "context window problem" is widely discussed in AI coding communities — sessions are stateless, and there's no built-in way to carry forward what was learned
- Developers report spending significant time per session just re-establishing context with the AI
- TODO: Link forum posts and discussions about context loss in long-running AI projects

**How aishore addresses this:**
aishore's backlog system (`backlog/backlog.json`) persists the full specification — intent, steps, acceptance criteria, description — across sessions. The commander's intent field captures *what must be true when done*, not implementation details that go stale. When a sprint runs, the developer agent gets the complete item specification plus your `CLAUDE.md`, `PRODUCT.md`, and `ARCHITECTURE.md` as context. The archive (`backlog/archive/sprints.jsonl`) preserves what was done and why. Context isn't in the AI's memory — it's in structured files that survive across any number of sessions.

---

## AI-generated code has no quality gate before merge

When you vibe code a feature, the output goes straight from "AI wrote it" to "it's in main." There's no review step, no self-check, no structured validation. The AI generates code, you glance at it, and it ships. Bugs that a reviewer would catch in five seconds survive because nobody reviewed — not the AI, not you, not a test suite.

This isn't about test coverage. Even with tests, the AI can write code that passes tests but misses the actual intent, introduces subtle regressions, or adds dead code and unnecessary complexity.

**Evidence:**
- "Vibe coding" explicitly deprioritizes code review — the ethos is speed over scrutiny
- Studies on AI-generated code show higher rates of subtle bugs compared to human-written code, especially in edge cases
- TODO: Link articles on quality issues in AI-generated code at scale

**How aishore addresses this:**
Every sprint item goes through a maturity protocol: implement, then critique, then harden — all inside a single session while context is hot. In the critique phase, the developer agent re-reads every changed file, verifies each acceptance criterion is provably met, and hunts for bugs and edge cases. In the harden phase, it runs validation again and fixes regressions. After the developer finishes, a separate Validator agent independently checks whether the acceptance criteria and commander's intent were actually fulfilled. The validation command (your test suite, linter, type checker) runs as a gate between development and merge. Code doesn't reach your main branch until it passes the developer's self-review, automated validation, and an independent validator check.

---

## One-shot prompting fails at project scale

"Build me a login page" works. "Build me an authentication system with OAuth2, session management, rate limiting, audit logging, and password reset flows" doesn't — at least not in a single prompt. One-shot prompting hits a wall when features have multiple interdependent parts, when they need to integrate with existing code, or when the implementation requires decisions the AI can't make without more context.

The workaround is breaking work into smaller prompts manually, but then you're back to the context loss problem — each prompt is isolated, and you're doing the project management in your head.

**Evidence:**
- Complex features attempted via single prompts frequently produce incomplete implementations or miss integration points
- Developers report reverting to manual step-by-step prompting for anything non-trivial, effectively becoming a human orchestrator
- TODO: Link discussions about prompt complexity limits and multi-step AI development

**How aishore addresses this:**
aishore's backlog items decompose complex work into structured steps with explicit acceptance criteria. Instead of one massive prompt, each feature gets a specification with a commander's intent (the non-negotiable outcome), ordered implementation steps, and verifiable acceptance criteria. The grooming agents (`groom`, `groom --backlog`) break rough ideas into sprint-ready items with the right granularity. The `backlog populate` command can decompose an entire product requirements document into individual backlog items. Each item runs as a complete sprint — branched, implemented, validated, and merged — so complex projects progress as a sequence of well-defined, achievable units rather than one impossible prompt.

---

## No audit trail for AI development decisions

When you prompt an AI to build something and it produces code, there's no record of what was asked, what was decided, why it was built that way, or what was verified. The git history shows *what* changed but not *what was intended*. If a feature breaks three weeks later, you can't trace back to the original specification to understand whether the implementation deviated from intent or the intent itself was wrong.

This makes debugging, onboarding, and handoffs painful. Nobody can reconstruct why the code looks the way it does.

**Evidence:**
- Git commit messages from AI coding sessions are often generic ("implement feature", "fix bug") with no connection to requirements
- Teams using AI coding tools report difficulty tracing implementation decisions back to product requirements
- TODO: Link discussions about traceability gaps in AI-assisted development

**How aishore addresses this:**
Every sprint produces a structured trail: the original backlog item (with intent, steps, and acceptance criteria) is archived in `backlog/archive/sprints.jsonl` along with the completion timestamp, pass/fail status, and summary. Feature branches are named by item ID (`aishore/FEAT-001`), and commits reference the item. The sprint history (`backlog history`) shows what was done, when, and whether it succeeded. The commander's intent field preserves *why* something was built, not just what was built. If a feature breaks, you can trace from the code change back to the branch, back to the archived item, back to the original intent and acceptance criteria that were (or weren't) met.

---

## AI agents don't self-critique without structure

Left to their own devices, AI coding agents implement what you asked and declare success. They don't step back and review their own work. They don't check whether what they built actually fulfills the intent. They don't look for edge cases, dead code, or missed requirements. The implementation-to-done pipeline has zero friction, which means zero quality checks.

This is the fundamental gap: AI agents are eager to complete, not eager to be correct. Without external structure forcing a review step, the first implementation is the final implementation.

**Evidence:**
- AI agents consistently report "done" on first attempt without self-review unless explicitly prompted to critique their work
- The "yes-man" problem in AI assistants is well-documented — agents are biased toward confirmation and completion over skepticism
- TODO: Link research on AI self-evaluation and the tendency to skip self-review

**How aishore addresses this:**
The maturity protocol forces structured self-critique into every sprint. After implementation (Phase 1), the developer agent must stop coding and shift to reviewer mindset (Phase 2: Critique) — re-reading every changed file, verifying each acceptance criterion against the actual code, and actively hunting for bugs and edge cases. Only after fixing everything found does it proceed to harden (Phase 3) — running validation again, fixing regressions, and re-verifying all acceptance criteria. This isn't optional prompting; it's a mandatory multi-phase protocol built into the agent's instructions. The critique happens while implementation context is still in the session, making it far more effective than a separate review pass.

---

## No way to batch AI development work

Current AI coding workflows are inherently serial and manual. You prompt, wait, review, prompt again. If you have ten features to build, you run ten separate sessions, each requiring your attention to start, monitor, and verify. There's no way to say "here are the next five features, go build them" and come back to finished, validated work.

This caps throughput at what you can personally supervise. AI coding is faster than manual coding, but it still requires a human in the loop for every feature.

**Evidence:**
- AI coding tools are session-based with no native batching — each task requires manual initiation and oversight
- Developers report that AI coding saves time per feature but doesn't reduce the *number* of sessions they need to manage
- TODO: Link discussions about scaling AI development beyond one-at-a-time workflows

**How aishore addresses this:**
The `run N` command executes N sprints back-to-back, each on its own feature branch. The `auto` command drains the entire backlog unattended — picking items by priority, auto-grooming when ready items run low, tracking failures across items, and stopping via circuit breaker after repeated failures. Each sprint is isolated (branched, validated, merged independently), so a failure on one item doesn't block the rest. You define the backlog, run `auto done`, and come back to merged, validated features with a complete audit trail of what passed and what didn't.

---

## AI coding has no concept of intent — only instructions

When you prompt an AI to "add a health check endpoint," it does exactly that — adds an endpoint. It doesn't consider *why* you need it (ops needs to know instantly if the service is alive), what the success criteria are (no false positives, sub-second response), or what trade-offs matter (reliability over feature richness). The AI follows instructions literally without understanding the outcome you need.

This means every prompt must be perfectly specified, or the output will be technically correct but miss the point. You end up either over-specifying every detail (slow) or accepting implementations that solve the letter of the request but not the spirit.

**Evidence:**
- AI coding tools treat every prompt as an implementation instruction, not an outcome specification
- Common failure mode: AI builds exactly what was asked but misses implicit requirements that a human developer would infer from context
- TODO: Link discussions about the gap between instruction-following and intent-fulfillment in AI development

**How aishore addresses this:**
Every backlog item has a commander's intent field — a non-negotiable directive that defines what must be true when done. Intent is written as an order ("Ops must know instantly if the service is alive or dead. No false positives.") not as implementation ("Add health check endpoint"). The developer agent follows intent when steps are ambiguous or seem wrong. The Validator agent checks whether intent was actually fulfilled, not just whether acceptance criteria passed mechanically. Items without intent (or with intent shorter than 20 characters) are blocked from entering a sprint entirely. This forces every piece of work to have a clear "why" before any code gets written.
