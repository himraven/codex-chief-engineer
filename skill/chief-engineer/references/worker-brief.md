# Standalone worker brief

Use one existing task note or brief. Include enough context to work without the
chief transcript; omit copied conversation and raw logs. For a single dispatch,
keep lifecycle IDs inline rather than creating separate phase/workstream docs.

## Task and context

- Objective / phase / workstream IDs; existing chief-state path:
- Exact outcome and why this slice exists:
- Verified commit/runtime, relevant files/symbols, and evidence:
- Fixed architecture/product decisions; decisions reserved for the chief:

## Ownership and boundaries

- Owned paths; forbidden paths; other active writers and integration boundary:
- Risk tier; red-line boundary; approved scope:
- Network/setup: none, pre-warmed cache, or authorized `--network "reason"`.
  Read roles needing temp files use `--scratch-tmp`; chief pre-stages remote facts.
- Dispatch form: ephemeral by default; persistent only for repeated exchanges.
- You are not alone in the workspace. Preserve unrelated changes. Do not
  delegate, expand scope, change contracts, or downgrade a required review lane.
- Stop and return when evidence contradicts the brief, scope expands, or a
  red line/undecided contract is reached.

## Work, verification, and return

- Exact work or named question:
- Exact verification commands and observable success criterion:
- Tool budget:
- Return changed files/findings, actual commands/results, artifact or diff
  fingerprint, remaining uncertainty, and the smallest blocked decision.

For reviews, include the named cone, base/head SHA, evidence contract, and
required finding severity/confidence from [review policy](review-policy.md).
