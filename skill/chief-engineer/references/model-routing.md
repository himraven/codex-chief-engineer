# Model routing

Read before selecting an executor. Owner decision: 2026-09-12.

## Decision owner and effort floor

- Codex chief and architecture/plan/RCA advice: **`gpt-6-astra` / `xhigh`**,
  replacing the former Sol chief/adviser assignment. This is a role default,
  not permission to change the model of an already-running task silently.
- Claude-side interactive chief remains Fable 5, at high or above. In a Codex
  run it can provide non-binding architecture/risk/RCA advice or a named
  non-binding challenge only. In a Claude run, Codex architecture advice is non-binding.
  The active chief retains the decision; neither adviser becomes a second chief.
- All selectable executors and fallbacks use **high or above**. Do not use
  none/minimal/low/medium or disable thinking. Verify that the chosen surface
  can actually pin a supported high-or-above setting; if it cannot, use an
  authorized role-compatible surface that can, or report the lane unavailable.
- Never dispatch a chief model as a worker or an implementation reviewer.
  Same-model children are only for justified context isolation or latency,
  never a cheaper execution pool.

## Bounded executors

| Role | Responsibility | Codex route |
|---|---|---|
| scout | Read-only search, inventory, logs, triage | Luna high via adapter |
| mechanic | Deterministic formatting, renames, boilerplate | Luna high |
| worker | Bounded implementation, tests, fixes | Terra high |
| senior | Cross-file refactors, concurrency, performance | Terra high |
| reviewer | Focused independent, read-only implementation review | Terra high via adapter |

The executable model IDs, role budgets, and sandbox pins are owned by
`scripts/ce-dispatch.sh`. Native write-role TOMLs under `~/.codex/agents/` must
match these role/effort contracts. A loaded stale native definition is not a
valid substitute: use the adapter until the host reloads the matching profile.

After **verified availability failure**, the adapter's `--fallback` maps
scout/mechanic to `gpt-5.4-mini` high and worker/senior/reviewer to `gpt-5.4` high.
Record the failure and fallback. Quality failures require investigation and
reslicing/escalation, not an availability fallback.

Any Claude lane (execution, review, or advice) requires repository/data policy
permission or explicit owner authorization. Verify that basis before dispatch.
On those authorized surfaces, Haiku 4.5 is mechanical-only, Sonnet 5 handles
bounded implementation/tests/debugging, and Opus 5 handles senior work. The
effort floor applies to every route; an unsupported high setting is not a
license to invent a flag or silently run at a lower setting. Prefer the Codex
mechanic route when a mechanical Claude route cannot honor the floor.

For independent cross-model challenges, use the eligibility and fallback rules
in [review policy](review-policy.md). Opus 5 and the recorded Opus 4.8 fallback
run at **high**. Grok 4.5 is review/challenge-only in this workflow; never route
implementation, tests, or debugging to that fallback. Fable is not a review
throughput target. GitHub's hosted bot model is not selectable; its required
closure is unaffected by local model routing.
