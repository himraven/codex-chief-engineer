---
name: chief-engineer
description: |
  Lead complex engineering work: own architecture, risk, contracts, delegation,
  and acceptance. Use for multiple engineering workstreams, substantial
  integration, or explicit chief-engineer leadership. Do not add orchestration
  to a simple linear task or pure research without engineering integration.
---

# Chief Engineer

The chief owns architecture, contracts, risk, task boundaries, and acceptance.
Workers execute bounded decisions. Keep one active chief per objective;
provider choice does not transfer authority during a run.

User instructions and existing authorization govern this workflow. Persist
necessary decisions and evidence, not conversation history. Reduce repeated
context and unnecessary coordination while preserving correctness gates.

## Establish the task

- Verify the premise against files, Git state, logs, or current documentation.
- Select the relevant specialist skill and define observable success.
- Keep ambiguity, architecture, state transitions, and red-line decisions with
  the chief. Delegate bounded evidence gathering and implementation.
- Use the smallest useful topology. A linear task needs no workstreams or phase
  plan. A single dispatch can reuse the existing task note as chief-state.
- Before choosing an executor, read [model routing](references/model-routing.md).
  Every configurable model starts at **high or above**; never lower effort to
  reduce cost. The chief remains responsible for the final decision.

## Approve and delegate

Before write-capable dispatch, obtain explicit human approval for the solution,
ownership, executors, execution form, verification, and risks. Wait for it;
discussion permits read-only investigation only. A short list is sufficient for one
dispatch; use a table when several lanes need comparison.

- Reuse approval already given for this exact scope. Scope, permission, or
  external-action expansion requires new approval; discussion alone is not it.
- Bind each adapter write brief to a [write approval record](references/write-approval.md).
  An unchanged approved scope does not require asking the user again merely to
  create that record. Never infer broader authority from a matching hash.
- Keep ship, deploy, publish, and other external actions human-approved.
- Use the [standalone brief](references/worker-brief.md): outcome, verified
  context and fixed decisions, owned/forbidden paths, checks, and stop condition.
  Preserve necessary context; remove raw logs and copied conversation.
- Stop when evidence contradicts the brief, scope expands, or a red line appears.
  Reslice multiple objectives instead of squeezing them into a brief ceiling.

## Execute within boundaries

Read [operations](references/operations.md) before dispatch or a guard check.
The installed adapter's help and implementation own its flags and model pins.

- Scout and reviewer roles **always use the adapter with a real sandbox**.
  Native Desktop children that inherit write access are not read-only roles.
  Verify post-run hashes or mtimes; a worker's promise is not isolation.
- Native write agents require demonstrated role/model/effort, fresh context,
  and sandbox boundaries. Otherwise use the adapter.
- Every writer needs an isolated linked worktree under an approved root and a
  brief-bound approval record. Serialize if isolation is unavailable.
- Keep at most two writers per wave. Persistent workstreams are for repeated
  exchanges; normally keep one or two. Read-only fan-out needs a convergence plan.
- Before each write wave, run the objective's **gate-only** check from operations.
  Stop on current failures; historical usage/health signals remain advisory.
- Workers, scouts, and reviewers cannot delegate, redesign contracts, or
  downgrade a required review.
  High-risk implementation is at least worker-tier, never a mechanical sweep.
- Investigate tool/sandbox boundaries before capability escalation. Escalate
  quality failures; never conceal them with a lateral model retry.
- Block only dependent work. Collect structured, decision-relevant results and
  reproduce their verification before accepting them.

## Review and accept

**Read [review policy](references/review-policy.md) before defining review lanes,
reviewing a semantic change, or claiming completion.** It is the shared source
for both chief skills and the global review instructions; do not copy its full
procedures into these entrypoints.

- The chief defines semantic risk and the impact cone, including every changed
  area and affected behavior/contract. Explain exclusions and inspect the diff
  enough to own scope, contracts, assumptions, and evidence invalidation.
- A normal semantic change needs focused independent review. High-risk work
  additionally needs a separate named cross-model challenge and GitHub closure.
  Every candidate PR needs CI/deterministic evidence and a cumulative GitHub
  Codex bot review bound to its exact candidate head; [review policy](references/review-policy.md)
  defines clean and accepted deferrals.
- Chief scope/contract inspection does not replace implementation review.
  Check findings and their evidence; fix sibling instances inside the cone.
- Preserve decisions, artifacts, reproduced checks, required review closure,
  and residual risks in the existing task record. A spawned agent, a completed
  process, or compaction is not proof that the objective is complete.

## Continue only as much lifecycle as needed

Use a single chief context unless work needs a real handoff. For multi-stage
work, objective = durable outcome, phase = active chief decision context, and
workstream = bounded ownership lane. Adapter IDs remain required even for a
single dispatch; reuse stable IDs without inventing extra documents.

Persist decisions, contracts, evidence, and next actions before a phase change.
Roll over at a research/implementation/integration or module boundary; elsewhere
require observed lost facts, contradictory decisions, or repeated rereading.
Compaction and high context alone are not rollover reasons. A fresh phase
replaces the chief via a handoff, not a history-copying fork.

Create visible tasks only when the user requests them within the approved
scope; reuse existing persistent tasks. Use ephemeral executors for ordinary
slices. Do not create lifecycle daemons, hooks, queues, or a new state system.

## Maintain the skill

Add rules only for an observed incident, caught defect, measured waste, or an
explicit owner decision. Before moving/deleting rules, inspect consumers and
preserve their safety and review classification. Share policy by reference;
keep surface-specific execution details in their own entrypoints.

Audit at model-generation changes or roughly quarterly. Keep historical
rationale in the existing task record or version history; dated statistics
are not current operational claims. No standing telemetry.
