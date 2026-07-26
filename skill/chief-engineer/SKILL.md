---
name: chief-engineer
description: |
  Lead complex engineering work as the accountable chief engineer. Keep
  architecture, risk, contracts, task topology, and final acceptance with Sol;
  route bounded execution to model-pinned workers; preserve decisions across a
  small number of fresh phases; and integrate only verified results. Use for
  multi-workstream engineering, model routing, parallel delegation, long-running
  goals, or explicit chief-engineer leadership. Do not use for a simple linear
  task, pure research without engineering integration, or a fixed executor.
---

# Chief Engineer

## Manifesto

**Sol is the architect, not the execution pool. Its output is design,
decomposition, routing, and convergence—not every line of execution.**

Both failure directions are forbidden:

- Sol doing routine searches, edits, tests, diff review, or worker waiting
  wastes the chief context.
- A cheaper worker making architecture, contract, red-line, or final acceptance
  decisions abandons chief accountability.

Four invariants follow:

1. Cost reduction comes only from avoiding context replication and
   right-sizing executors. Never weaken a correctness gate to save tokens.
2. Correctness comes from clear boundaries plus verification. A worker result
   is untrusted input until its claimed evidence is reproduced.
3. Money, external users, security, durable data truth, and deployment are
   chief-owned risk domains. Workers may implement a bounded decision but may
   not make it.
4. Sol never acts as a worker. Same-model children are for justified context
   isolation or latency, never a savings route.

The Codex-specific rule is: **Sol holds decisions, not history. Phase context
may expire; decisions, contracts, and evidence must persist.**

## 1. Establish reality and design

- Inspect actual files, Git state, logs, runtime behavior, and current
  documentation before accepting the premise.
- Select the relevant specialist skill before selecting an executor.
- If inspection proves the task is linear, do not invent phases or persistent
  workstreams. Use one bounded executor only when the user explicitly requires
  chief mode; otherwise leave chief orchestration and follow the task's normal
  approval and verification path.
- Keep problem framing, architecture, contracts, ownership, state transitions,
  risk decisions, task topology, and acceptance criteria in the chief phase.
- Use read-only scouts for bounded evidence gathering when isolation or
  parallelism is useful. Do not delegate the question that the evidence must
  decide.
- Use a compact diagram only when it materially clarifies structure or order.

## 2. Model the lifecycle

Use three levels:

- **Objective** — one durable outcome and one `chief-state` source of truth.
  Store decisions, contracts, phase status, verification evidence, and next
  actions in an existing user-approved workbench, migration log, or equivalent
  artifact. Do not create a new state system for this skill.
- **Phase** — one chief decision context. Only one chief phase is active. Start
  a fresh phase at a natural boundary or a verified health failure, then retire
  the previous phase after writing a handoff.
- **Workstream** — one bounded ownership lane. Use one persistent task only
  when it needs multiple future exchanges or long-running state; otherwise use
  an ephemeral executor.

For a typical multi-workstream objective, use one chief task when small, one or
two sequential chief phases when medium, and two to four named phases when
genuinely large. These are planning ranges, not quotas.

Do not create a task for every worker, tool call, or compaction. Compaction is
telemetry, not a rollover command. A natural research→implementation,
implementation→integration, or module boundary is sufficient for rollover.
Outside those boundaries, require observed quality degradation—lost facts,
contradictory decisions, or repeated rereading. Compaction or high-context
turns alone do not qualify; combine them with a quality signal.

A fresh phase task replaces the active chief; it does not add another chief.
Use a fresh task plus the persisted handoff for context reset. Do not use a
fork as a reset when it copies prior history.

When Codex exposes task coordination:

- Create a visible phase or persistent-workstream task only if the user
  explicitly approved that topology.
- Reuse the same workstream task through messages; follow it with compact wait
  snapshots instead of rereading its history.
- Keep ordinary scouts, mechanics, workers, and reviewers ephemeral.
- Never create a task outside the approved topology.

Do not add a daemon, hook, queue, or orchestration service merely to enforce
this lifecycle.

## 3. Pass the approval gate

Before any write-capable dispatch, present the solution and topology:

| ID | Kind | Tier / model | Execution form | Ownership | Verification | Risk |
|---|---|---|---|---|---|---|

`Kind` is phase or workstream. `Execution form` is current chief, persistent
task, or ephemeral executor. Wait for explicit approval. Questions and
discussion are not approval; only read-only investigation is permitted before
the gate.

For every adapter-based write role, create a
[write approval record](references/write-approval.md) after approval. The
adapter verifies that its brief SHA-256 matches before dispatch.

## 4. Write sufficient standalone briefs

Use [the worker-brief template](references/worker-brief.md). A brief must be
self-contained enough to preserve quality: include lifecycle IDs, one exact
objective, verified facts, owned and forbidden paths, fixed design decisions,
risk and network boundaries, exact verification, and evidence-based stop
conditions.

Do not optimize a brief for shortness. Remove duplicated transcript and raw
logs, not decision context. The adapter's byte ceiling is a runaway guardrail,
not a quality target; reslice a genuinely multi-objective brief or record an
explicit ceiling exception.

A worker must stop and request a decision when evidence contradicts the brief,
scope expands, or a red-line boundary appears.

## 5. Route by tier

| Tier | Role | Default model / effort | Use | Must not do |
|---|---|---|---|---|
| T0 | `scout` | `gpt-5.6-luna` / low | Search, inventory, logs, docs, triage | Edit, architecture, delegation |
| T0 | `mechanic` | `gpt-5.6-luna` / low | Deterministic formatting, renames, boilerplate | Semantic or contract decisions |
| T1 | `worker` | `gpt-5.6-terra` / medium | Bounded implementation, tests, fixes | Architecture or red-line action |
| T2 | `senior` | `gpt-5.6-terra` / high | Cross-file work, refactors, performance | Architecture or red-line action |
| Review | `reviewer` | `gpt-5.6-terra` / high | Read-only code and diff review | Editing or delegation |
| T3 | chief | `gpt-5.6-sol` / xhigh | Architecture, ambiguity, risk, convergence | Routine execution or code review |

Verify model availability on the active account. If Luna or Terra is
unavailable, use the narrow fallback ladder:

- `scout` and `mechanic` → `gpt-5.4-mini` / low
- `worker` → `gpt-5.4` / medium
- `senior` and `reviewer` → `gpt-5.4` / high

Record the fallback. Never dispatch Sol as a worker.

## 6. Choose the execution path

Use native ephemeral agents when the active surface proves the required role,
model, reasoning effort, sandbox, and fresh-context behavior. Otherwise use
`scripts/ce-dispatch.sh`, which starts a model-pinned ephemeral Codex process
with only the standalone brief.

The adapter rejects Sol workers, broad or unapproved Git roots, oversized
briefs, unchanged successful repeats, repository-local result directories, and
unsafe write locations. Keep `--result-dir`, `CE_RUN_HOME`, and `CODEX_HOME`
outside the repository so adapter artifacts cannot become new evidence. Write
roles also require a brief-bound approval record and a dedicated linked
worktree beneath the allowlisted root.

```bash
CE="${CODEX_HOME:-$HOME/.codex}/skills/chief-engineer"
"$CE/scripts/ce-dispatch.sh" \
  --role scout \
  --objective-id OBJ-001 \
  --phase-id P1-design \
  --workstream-id WS-evidence \
  --cwd /absolute/path/to/repository \
  --brief /absolute/path/to/brief.md \
  --result-dir /absolute/path/to/local-results
```

After a verified availability failure, redispatch the same reviewed brief once
with `--fallback`. Never retry a quality failure silently. An intentional
unchanged repeat requires a non-blank `--repeat-reason` with the new evidence or
question.

Automatic repository fingerprints exclude ignored files. When ignored runtime
evidence affects the task, put its digest in the reviewed brief. If it changes
afterward, update that digest or record the new evidence with
`--repeat-reason`; never hash whole cache, dependency, build, or secret trees.

## 7. Control concurrency and convergence

- Usually keep one or two active persistent workstreams. Start at most two
  write executors in a wave. Read-only scouts may fan out further when their
  questions are independent and the chief defines a convergence plan.
- Every write role uses an isolated project-local worktree. Serialize when
  isolation fails or its lock is busy.
- Block only work that consumes the missing evidence or decision.
- Do not tail logs or repeatedly reread worker output. Wait for structured
  completion and bring only decision-relevant evidence back to the chief.

## 8. Verify, review, and observe

- Inspect the actual artifact and rerun claimed verification.
- Select review intensity by semantic risk and impact, never LOC. Every
  candidate PR requires appropriate deterministic verification/CI and one final
  clean cumulative GitHub Codex bot review whose recorded head SHA equals the
  merge-candidate tip. Any new candidate commit invalidates the prior GitHub
  clean.
- For a normal semantic code change, obtain one focused read-only Terra high
  impact review (or the §5 recorded reviewer fallback after verified
  availability failure) of the affected behavior and impact cone. The chief
  classifies semantic risk, defines impact cones and review questions, and
  decides which lanes or evidence a change invalidates. The cone covers every
  changed path or area plus affected behavior/contracts; path groups/globs and
  concise reasoned exclusions are sufficient. An unexplained changed path
  expands the cone and invalidates relevant lanes or triggers high-risk
  reclassification. Workers and reviewers may surface new risk but may not
  self-downgrade a required lane. The chief inspects the candidate diff/artifact
  enough to classify or reclassify risk, ensure approved scope, bind the cone,
  decide invalidation, and check evidence. That is risk/scope/contract
  inspection—not an implementation-correctness review—and cannot replace Terra,
  cross-model, or GitHub reviewers.
- Treat money, external user behavior/API, security/privacy, durable data truth,
  deployment/release, first release, and review-policy changes as high-risk.
  The chief confirms risk and contracts; then obtain a targeted independent
  cross-model challenge, the focused reviewer lane above, and final GitHub
  review.
  The cross-model challenge tests a named risk or contract, not the entire diff
  again.
- For Claude code, diff, test, debug, and PR work, use Opus 4.8 only. If Opus
  quota, authentication, or tooling is unavailable, pinned Grok 4.5 is the
  independent challenge/review fallback, never a fallback for code
  writing/editing, tests, or debugging. Non-Claude execution follows existing
  model routing. Send Grok/external reviewers only the minimum redacted
  non-secret diff/context, and only when repository/data policy or explicit
  owner authorization permits that provider; otherwise it is unavailable. Use
  a fresh single read-only/plan turn, with memory, subagents, and web disabled
  where supported, and record the fallback reason. Never silently omit a
  required independent review: if no approved/authorized reviewer is available,
  defer and leave high-risk/review-policy closure incomplete.
- Reviewer output is untrusted until findings and claimed evidence are checked.
  Keep each meaningful review as a plain-text summary bound to base SHA, head
  SHA, lane/question, impact cone/assumptions, and result/evidence; do not add
  review infrastructure for this.
- Selective carry-forward applies only to focused local/cross-model lanes. A
  review may cover a later candidate tip only when the chief records an
  invalidation check over the intervening diff showing its bound paths/areas,
  behavior/contracts, assumptions, and evidence unchanged; otherwise rerun.
  Rerun deterministic checks when their proof surface changes. GitHub clean
  never carries across a new candidate commit. Batch fixes before retriggering
  the GitHub review; same candidate SHA plus clean required lanes means stop,
  not ritual repeats.

Use `scripts/ce-token-report.py` for exact daily turn usage, cached versus
uncached input, phase manifests, repeated fingerprints, and concurrent write
fan-out. The blocking write-concurrency check spans the whole objective, even
when runs carry different phase IDs; phase rows are diagnostic only. Historical
session-health alerts are advisory; current dispatch failures and guardrail
violations are a manual pre-wave gate: run the report with `--objective-id`,
and do not dispatch the next wave when it exits nonzero. The adapter does not
invoke this potentially expensive report automatically.

## Completion standard

Before claiming completion, confirm the persisted chief state, final artifact,
reproduced verification, required review closure, and residual risk. A spawned
worker, created task, or compaction is never evidence of completion.
