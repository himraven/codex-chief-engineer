# Model routing

Read before selecting an executor. Model refresh: 2026-09-24.

## Decision owner and effort floor

- Codex chief and architecture/plan/RCA advice: **`gpt-6-astra` / `xhigh`**.
  Do not silently change the model of an already-running task. Another provider
  supplies bounded execution or non-binding advice, never a second chief.
- All selectable executors and fallbacks use **high or above**. This owner
  preference is stricter than product defaults; do not lower it, disable thinking,
  or assume effort labels are equivalent across generations.
- Astra is not a worker or implementation reviewer. Sol is now an executor
  model, not a second chief. Keep architecture and unresolved contracts with
  the active chief. Same-model children require a concrete context or latency need.
- Keep the smallest useful topology. Do deterministic searches/checks directly
  when delegation would add no value; do not make a chief poll idle workers.

## Bounded executors

| Role | Responsibility | Primary / effort | Availability fallback / effort |
|---|---|---|---|
| scout | Read-only search, inventory, logs, triage | `gpt-6-luna` / high | `gpt-5.6-luna` / high |
| mechanic | Deterministic formatting, renames, boilerplate | `gpt-6-luna` / high | `gpt-5.6-luna` / high |
| worker | Bounded implementation, tests, fixes | `gpt-6-sol` / high | `gpt-5.6-terra` / high |
| senior | Cross-file refactors, concurrency, performance | `gpt-6-sol` / high | `gpt-5.6-sol` / high |
| reviewer | Independent focused implementation review | `gpt-6-sol` / high | `gpt-5.6-sol` / high |

Scouts and reviewers always use the adapter's real read-only boundary. Senior
has a larger bounded work budget, not permission to redesign the architecture.
Do not broaden Luna to judgment-heavy implementation merely because it is newer;
first establish representative task quality. Preserve separate reviewer context
and authorship independence even when author and reviewer use Sol.

`scripts/ce-dispatch.sh` owns executable pins, budgets and sandboxes. Native
write-role TOMLs must match. A loaded stale native definition is not a substitute:
use the adapter until the host reloads and exposes the matching model/effort.
Request the default service tier; Fast and Ultra are not automatic. A native
profile accepting `service_tier` does not prove the child honors it. Verify the
effective tier as well as model/effort and sandbox before native dispatch; if
that evidence is unavailable, use the adapter with its explicit per-call tier.
Ultra's automatic delegation conflicts with the bounded no-redelegation contract.

Use `--fallback` once only after verified model/client availability failure;
record the error and selected route. A failed task, weak answer or tool permission
error is not model unavailability. Investigate those failures and reslice or
escalate to the chief; never silently retry through a different provider.
Worker fallback retains the previous bounded Terra route. Senior and reviewer
fallbacks use the stronger previous-generation Sol route for complex contracts
and review. Sol is no longer assigned the chief role in this workflow.
The fallback must also be available on the same authorized surface or the lane
remains unavailable. Retired `gpt-5.4` and `gpt-5.4-mini` are not fallbacks.

## Client, subscription and activation

The tested CLI baseline is **Codex 0.156.1** with ChatGPT sign-in. On the same
account, 0.153.4 rejected GPT-6 Sol/Luna while 0.156.1 completed real requests.
Check the actual executor binary, login surface and a bounded real call before
activating a route; a catalog entry or accepted model flag is insufficient.
A newer CLI does not update an already-loaded Desktop agent definition.

Prefer the existing subscription transport; do not introduce API-key billing
as an implicit availability fallback. API prices or credit rates do not establish
included subscription consumption. Evaluate useful completed work, latency and
retries; do not claim an exact quota saving from the published price ratio.

## Other providers and independent challenge

Any Claude or Grok lane requires repository/data-policy permission or explicit
owner authorization. Send only the authorized, redacted context. The active
surface keeps its chief. This refresh does not change the Claude entrypoint or
its runtime settings. Preserve its existing assignments until its owner updates
them: Fable 5 chief at high or above, Haiku 4.5 mechanical-only, Sonnet 5 bounded
implementation/tests/debugging, and Opus 5 senior work. Fable is not a review
throughput target. The effort floor applies to each route; prefer the Codex
mechanic when a Claude mechanical route cannot honor it. Current Claude model
upgrade recommendations are a separate handoff, not silently activated here.

The Codex-owned cross-model lane uses **`claude-opus-5-5` / high**, with
**`claude-opus-5` / high** only after verified availability failure. The separate
eligible third-provider route is **`grok-4.7` / high**, review/challenge-only.
Use the eligibility and fallback order in [review policy](review-policy.md);
never send the same work to all three providers by default. Grok does not become
an implementation, testing or debugging executor in this workflow. GitHub's
hosted bot model is not selectable; its required closure remains unchanged.

Current product guidance: [Codex models](https://learn.chatgpt.com/docs/models),
[subscription usage](https://learn.chatgpt.com/docs/pricing),
[Claude models](https://platform.claude.com/docs/en/models/overview), and
[Grok 4.7](https://docs.x.ai/developers/models/grok-4.7). Recheck actual availability
at the next model-generation change; do not use unbounded `latest` aliases.
