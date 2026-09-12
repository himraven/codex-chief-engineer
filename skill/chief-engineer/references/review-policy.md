# Engineering review policy

Shared source for the Codex and Claude chief skills and global review
instructions. Read before classifying review risk, selecting lanes, or claiming
completion. Current model/effort selection lives in [model routing](model-routing.md);
command isolation lives in [operations](operations.md). Explicit user decisions
and stricter applicable repository/data rules remain binding.

## Risk, scope, and required lanes

- Set review intensity by semantic risk and impact, never LOC. The chief owns
  risk classification, contracts, named review questions, and the impact cone:
  all changed paths/areas plus affected behavior/contracts. Explain exclusions.
  An unexplained changed path expands the cone, invalidates relevant lanes,
  or requires high-risk reclassification. Workers/reviewers may raise risk but
  cannot downgrade a required lane.
- The chief inspects enough to own risk, scope, contracts, and invalidation.
  This is not implementation-correctness review and cannot replace the focused
  reviewer, cross-model challenge, or GitHub lane. Connector tools retrieve or
  write review data; they do not supply review judgment.
- Every normal semantic code change needs one focused read-only Terra high
  review of its impact cone, using the recorded fallback only after verified
  availability failure.
- Money, external user behavior/APIs, security/privacy, durable data truth,
  deployment/release, first release, and **review-policy changes** are high-risk.
  They require chief-owned risk/contract confirmation, the focused reviewer,
  a **separate targeted independent cross-model challenge**, and final GitHub
  review. Challenge one named risk or contract, not another generic full diff.
- Preserve existing structural-risk GitHub gates: interface signatures or
  re-exports, state machines, CLI/schema changes, external side effects, data
  destruction, and deployment/operations changes retain required GitHub closure.
  Relocating their policy does not lower their review classification.
- Every candidate PR requires appropriate deterministic checks/CI and one
  final clean **cumulative** `chatgpt-codex-connector[bot]` review. Its recorded
  head SHA must equal the merge-candidate tip. Every new candidate commit
  invalidates the GitHub clean. Use the repository's existing ship workflow.
- An authoring agent/session cannot QA its own work. Focused local review and
  the targeted cross-model challenge are distinct lanes and cannot be supplied
  by the same review. Apply provider-level authorship independence to the
  cross-model lane, including authored code, design, and contract decisions.

## Cross-model eligibility and fallback

Use a provider only when repository/data policy or explicit owner authorization
allows it. Send only the minimum authorized, redacted non-secret context.

1. An eligible independent Claude lane uses **`claude-opus-5` / high**, with
   thinking enabled. Do not start below high or default to xhigh/max.
2. If Claude authored the affected change or lacks data authorization, it is
   **ineligible**. Record why and route the separate named challenge directly
   to an authorized, non-authoring pinned Grok 4.5. This is not an Opus
   availability failure. If that route is unavailable, defer closure.
3. For eligible Claude availability failures only: verify Opus 5 failure, then
   try the recorded **`claude-opus-4-8` / high** fallback. Only after separately
   verified failure of that fallback may authorized, non-authoring pinned
   Grok 4.5 supply the independent review/challenge. Never use this fallback
   for implementation, editing, tests, or debugging.
4. Record all failures, ineligibility, and fallback use. If an approved,
   authorized independent reviewer is unavailable, leave high-risk/review-policy
   closure incomplete. Never silently omit a required lane.

Use a fresh, non-resumed, tool-less stdin turn with no prior-memory carryover,
redelegation/subagents, web, MCP, or writes. Keep the prompt outside the repo.
Operations provides the exact safe-mode/non-persistence invocation. If tools
are necessary, enforce the authorized cone with a real OS/filesystem sandbox
or projection before allowing Read/Grep/Glob. Prompt-only path restrictions
are not access control. Never interpolate raw diffs into shell arguments.

## Findings, repair, and verification

- Treat worker/reviewer claims as untrusted until checked. Inspect artifacts
  and reproduce the relevant verification; include exact commands and actual
  results in review packets. Do not ask reviewers for generic double-check or
  re-verify rituals when the listed evidence already answers that question.
- Report every evidence-backed finding with severity and confidence; do not
  suppress findings because either is low. Put unsupported concerns under
  open questions. Report out-of-cone risks without investigating them.
- State each finding's mechanism and sweep sibling instances inside the cone.
  Fix the class. Known bugs cannot be called complete. If a finding is deferred,
  record the chief-verified dormant/unreachable condition, owner, and forcing function in an
  existing tracked backlog; currently actionable findings require resolution.
- Re-verify fixes affecting logic, contracts, configuration, policy,
  machine-consumed docs, generated output, or runtime behavior. Skip targeted
  re-verification only when none of those can change; if uncertain, re-verify.

## Evidence records and stopping

Keep plain-text records bound to base SHA, head SHA, lane/question, impact
cone/assumptions, and result/evidence. Do not build review infrastructure.

A focused local or cross-model verdict may cover a later tip only after the
chief records an intervening-diff check proving its paths/areas, affected
behavior/contracts, assumptions, and evidence are unchanged. Otherwise rerun
that lane. Deterministic checks rerun when their proof surface changes.
GitHub clean never carries across a new commit.

Batch fixes before requesting another GitHub review. Same candidate SHA plus
clean required lanes ends review; no ritual repeats. Confidence scores are
secondary evidence and cannot substitute for required closure. Persist final
artifacts, reproduced checks, review status, and residual risks before claiming
completion; record unavailable required lanes explicitly.
