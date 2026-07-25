# Chief Engineer for Codex

> Made by GPT-5.6 Sol.

> A quality-preserving lifecycle orchestration skill for Codex: keep
> architecture and accountability with Sol, preserve decisions outside the
> live context, and route bounded execution to the right model.

[![License: MIT](https://img.shields.io/badge/License-MIT-4c1.svg)](LICENSE)
[![Codex skill](https://img.shields.io/badge/Codex-skill-111827.svg)](skill/chief-engineer/SKILL.md)

`chief-engineer` treats Sol as the architect, not the execution pool. Sol owns
design, decomposition, risk, task topology, and final convergence. Luna and
Terra execute bounded briefs; their output remains untrusted until verified.

The skill reduces waste through context isolation and right-sized execution,
not shorter briefs, weaker review, or lower reasoning on chief decisions.

```mermaid
flowchart TB
  O["Objective\nDurable chief-state"] --> P1["Chief phase 1\nSol xhigh decisions"]
  P1 --> G{"Approved topology?"}
  G -->|"No"| S["Read-only discovery"]
  G -->|"Yes"| E["Ephemeral executors\nLuna / Terra"]
  G -->|"Only when stateful"| W["Reusable workstream task"]
  E --> V["Reproduced verification\nTerra review"]
  W --> V
  V --> H["Persisted handoff"]
  H --> P2["Fresh chief phase when justified\nPrevious chief retires"]
```

## What it enforces

| Concern | Policy |
|---|---|
| Chief boundary | Sol holds decisions, not routine execution or unlimited history |
| Architecture and red-line decisions | Chief-only; never delegated to a worker |
| Session lifecycle | One active chief; a fresh phase replaces it at a real boundary |
| Task topology | Visible phase/workstream tasks require approval and are reused, not multiplied |
| Compaction | Health signal only; never an automatic “create task” trigger |
| Routine execution | Model-pinned Luna or Terra workers with a sufficient standalone brief |
| Code review | Read-only Terra reviewer; use an independent external reviewer for cross-model QA |
| Approval | Write workers require an explicit, brief-bound approval record |
| Repository boundary | Every adapter role is limited to a local allowlist of Git roots |
| Write isolation | Every write worker uses a dedicated project-local linked worktree and lock |
| Repeated work | Unchanged successful input is rejected unless new evidence is recorded |
| Observability | Exact daily turn usage; reasoning is never double-counted |
| Privacy | Run artifacts stay local; task titles are hidden by default |

## Quick start

Requirements: Codex CLI, Git, Bash, `jq`, Python 3.9+, and either `shasum` or
`sha256sum`, plus the model IDs used by your account.

```bash
git clone https://github.com/himraven/codex-chief-engineer.git
cd codex-chief-engineer
./install.sh --dry-run
./install.sh
```

The installer is deliberately non-destructive: it refuses to overwrite an
existing skill or agent configuration.

## Configure the local repository boundary

The package installs with an empty allowlist. This is intentional: no
adapter-based role—including a read-only scout or reviewer—can run until you
add a narrow Git repository root. The boundary prevents accidental access to a
home directory or unrelated checkout.

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
$EDITOR "$CODEX_HOME/skills/chief-engineer/references/approved-repo-roots.local.txt"
```

Add one canonical repository root per line, for example:

```text
/absolute/path/to/your/repository
```

The local file is ignored by Git. Never commit personal paths, generated
worker artifacts, JSONL event logs, or token-report output.

After allowlisting the main repository, write-capable workers must additionally
run in a dedicated linked worktree beneath it, for example:

```bash
git -C /absolute/path/to/your/repository worktree add \
  /absolute/path/to/your/repository/.worktrees/worker-1 -b agent/worker-1
```

## Use the skill

Ask Codex to use `$chief-engineer` for a multi-workstream task. The chief will
inspect reality, design the solution and task topology, then wait for explicit
approval before write-capable work begins.

The lifecycle has three levels:

- **Objective:** one durable outcome and one persisted `chief-state`.
- **Phase:** one active Sol decision context. A fresh phase starts only at a
  natural boundary or verified context-health failure and replaces the old one.
- **Workstream:** one bounded ownership lane. Keep a visible task only when it
  needs repeated future exchanges; ordinary workers stay ephemeral.

A compaction does not create a task. A small objective normally uses one chief
task, a medium objective one or two sequential phases, and a genuinely large
objective two to four named phases across its lifetime—not hundreds of
sessions. Outside a natural phase boundary, compaction or high context must be
paired with observed quality degradation before rollover. When the active Codex
surface supports task messaging, reuse the same workstream task and follow it
with compact waits. Do not fork a long history and call that a context reset.

For an approved standalone worker, use the installed adapter:

```bash
CE="${CODEX_HOME:-$HOME/.codex}/skills/chief-engineer"
"$CE/scripts/ce-dispatch.sh" \
  --role worker \
  --objective-id OBJ-001 \
  --phase-id P2-implementation \
  --workstream-id WS-api \
  --cwd /absolute/path/to/your/repository/.worktrees/worker-1 \
  --brief /absolute/path/to/brief.md \
  --approval-file /absolute/path/to/write-approval.md \
  --result-dir /absolute/path/to/local-results
```

Use the included [worker brief template](skill/chief-engineer/references/worker-brief.md).
After a human explicitly approves the write, create the
[approval record](skill/chief-engineer/references/write-approval.md) with the
brief SHA-256. The adapter refuses write dispatch without a matching record,
Sol as a worker, non-Git directories, shared checkouts, roots outside the local
allowlist, oversized briefs, and result directories inside the repository.
Keeping `--result-dir`, `CE_RUN_HOME`, and `CODEX_HOME` outside the repository
prevents adapter artifacts from becoming new evidence. The adapter also
fingerprints the objective/workstream identity, brief, commit, and repository
state, plus the canonical repository root and effective working directory.
Deduplication intentionally excludes the phase ID: unchanged evidence remains
unchanged after a phase rollover, while an identical brief aimed at another
repository or subdirectory remains a distinct dispatch. Repository state
includes tracked and untracked files—including untracked regular-file
modes—plus dirty state inside initialized submodules. The operational
`.worktrees/` container is excluded from the primary checkout's untracked
evidence; each linked worktree is fingerprinted when it is the dispatch target.
Final diff fingerprints stay relative to the tree captured at dispatch, even
when an executor commits before returning. Repeating an unchanged input requires
a non-blank `--repeat-reason` with the new evidence or question.

Ignored files are deliberately outside automatic repository fingerprinting:
hashing caches, dependencies, build output, and secrets would be expensive and
unsafe. If an ignored artifact affects an executor decision, put its digest in
the reviewed brief; if it changes later, update that digest or provide a
non-blank `--repeat-reason`.

The brief ceiling is a runaway guardrail, not a quality target. Keep every
decision and contract the executor needs; remove copied conversation and raw
logs. If a brief contains multiple objectives, reslice it.

## Model routing

The bundled defaults use the GPT-5.6 family available to the original setup.
Edit both the skill table and `agents/` TOML files if your Codex account exposes
different model IDs.

| Tier | Role | Default model / effort |
|---|---|---|
| T0 | Scout and mechanic | Luna / low |
| T1 | Bounded implementation | Terra / medium |
| T2 | Cross-file implementation | Terra / high |
| Review | Read-only code review | Terra / high |
| T3 | Architecture and integration | Sol / xhigh |

The `agents/` directory provides optional custom-agent definitions. Native
ephemeral agents are suitable when the active surface proves the requested
role, model, reasoning effort, sandbox, and fresh-context behavior. The direct
dispatch adapter is the portable fallback when any of those properties is not
observable.

## Optional token observability

`ce-token-report.py` reads local Codex rollouts and manifests in read-only mode.
It attributes `last_token_usage` to the day each turn actually occurred,
separates cached from uncached input, and reports reasoning as a subset of
output. This avoids the common errors of assigning a thread's lifetime total to
its most recent day or adding reasoning twice.

```bash
python3 "$CE/scripts/ce-token-report.py" --date 2026-07-11
python3 "$CE/scripts/ce-token-report.py" \
  --date 2026-07-11 \
  --objective-id OBJ-001
```

The report follows the absolute `CE_RUN_HOME`, matching the dispatch adapter.
Relative environment paths are rejected so dispatch and reporting cannot
silently resolve different indexes. Use `--run-home` to inspect a different
local manifest index explicitly.

Direct-run gates use execution-time overlap across the full manifest index, so
a run crossing local midnight is visible on both days. Because ephemeral JSONL
events do not carry per-event timestamps, aggregate direct-run tokens are
counted once on the local completion day rather than guessed or double-counted.

Use `--include-titles` only when it is safe for those local titles to appear in
your terminal output. Historical compaction and long-context signals are
advisory: they can justify a fresh phase but never create one automatically or
block unrelated work. The general report does not evaluate a blocking gate.
Add `--objective-id` to gate the next wave for one objective; only its failed
dispatches, invalid manifests, unchanged repeats, budget violations, and
concurrent write fan-out above two across all of its phases make the report
exit nonzero. Phase rows remain diagnostic; a mistaken or incomplete rollover
cannot hide objective-wide write concurrency. This is an explicit pre-wave
check, not an automatic adapter hook: the chief or caller must run it and stop
on failure.

## Privacy and security design

- No account credentials, repository names, home-directory paths, or private
  project policy are included in this repository.
- The local repository allowlist is created after installation and is ignored.
- Dispatch logs, manifests, JSONL events, local environment files, and Python
  caches are ignored.
- The adapter uses an explicit model pin and sandbox for every worker, then
  emits a local manifest for verification.

## Repository layout

```text
skill/chief-engineer/   Installable Codex skill, references, and adapters
agents/                 Optional custom-agent TOML definitions
install.sh              Non-overwriting installer
```

## Development

The repository keeps verification intentionally small and local:

```bash
bash -n install.sh skill/chief-engineer/scripts/ce-dispatch.sh
shellcheck install.sh skill/chief-engineer/scripts/ce-dispatch.sh
ruff check skill/chief-engineer/scripts/ce-token-report.py tests
ruff format --check skill/chief-engineer/scripts/ce-token-report.py tests
python3 -m unittest -v
```

Pull requests run the same regression suite in GitHub Actions.

## License

[MIT](LICENSE)
