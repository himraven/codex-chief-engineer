# Chief Engineer for Codex

> Originally made by GPT-5.6 Sol; updated for GPT-6 Astra.

Keep architecture, contracts, risk, and acceptance with the chief; delegate
bounded execution with enough context and verify the result. GPT-6 Astra xhigh
is the default Codex chief. Luna and Terra handle bounded work at high effort.

[![License: MIT](https://img.shields.io/badge/License-MIT-4c1.svg)](LICENSE)
[![Codex skill](https://img.shields.io/badge/Codex-skill-111827.svg)](skill/chief-engineer/SKILL.md)

The entrypoint stays short. Load [model routing](skill/chief-engineer/references/model-routing.md)
when choosing an executor, [operations](skill/chief-engineer/references/operations.md)
when dispatching, and the shared [review policy](skill/chief-engineer/references/review-policy.md)
when defining review lanes or accepting work. A small task needs no extra phases
or lifecycle documents.

## What it enforces

| Concern | Policy |
|---|---|
| Chief boundary | The chief holds decisions, not routine execution or unlimited history |
| Architecture and red-line decisions | Chief-only; never delegated to a worker |
| Session lifecycle | One active chief; a fresh phase replaces it at a real boundary |
| Task topology | Visible phase/workstream tasks require approval and are reused, not multiplied |
| Compaction | Health signal only; never an automatic “create task” trigger |
| Routine execution | Model-pinned Luna or Terra workers with a sufficient standalone brief |
| Review intensity | Semantic risk and impact, never LOC |
| Normal semantic code | Focused read-only Terra high review by default (recorded reviewer fallback only after verified availability failure) |
| High-risk change | Chief risk/contract confirmation, targeted independent cross-model challenge, the focused reviewer lane above, then final GitHub review |
| Review repair | Re-verify fixes that can change logic, contracts, configuration, policy, machine-consumed docs, generated output, or runtime behavior; skip only when none can change, and re-verify when uncertain |
| PR closure | Appropriate deterministic verification/CI and one clean cumulative GitHub Codex bot review whose recorded head SHA equals the merge-candidate tip |
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

The installer handles first-time setup and refuses to overwrite existing targets.
For an existing installation, update manually (`CODEX_HOME` defaults to `~/.codex`):

1. Back up the installed `skills/chief-engineer/` directory and `ce-*.toml`
   profiles outside `CODEX_HOME`; compare local customizations with the reviewed source.
2. Copy the reviewed `skill/chief-engineer/` contents into
   `CODEX_HOME/skills/chief-engineer/`, including every reference and script.
   Preserve `references/approved-repo-roots.local.txt` and reconcile custom edits.
3. Apply the matching `agents/ce-{mechanic,worker,senior}.toml` changes to
   `CODEX_HOME/agents/`, preserving custom instructions. Move legacy native
   `ce-scout.toml` and `ce-reviewer.toml` outside that directory: read roles use
   the adapter, and the installer refuses those profiles.

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

Use one active chief per objective. Adapter dispatches require stable objective,
phase, and workstream IDs; a single dispatch can use the existing task note.
Create a fresh phase only at a real handoff or demonstrated context-health
failure, persisting decisions and evidence first. Compaction alone does not
justify rollover. Visible tasks require a user request; reuse persistent tasks
when repeated exchanges justify them.

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
chief models as workers, non-Git directories, shared checkouts, roots outside the local
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

For dispatch flags, review invocation details, and usage-report mechanics, read
[`references/operations.md`](skill/chief-engineer/references/operations.md).
The adapter's `--help` remains authoritative for its interface.

## Model routing and review

| Responsibility | Default model / effort |
|---|---|
| Chief, architecture, plan and RCA advice | GPT-6 Astra / xhigh |
| Scout and mechanic | Luna / high |
| Bounded or senior implementation | Terra / high |
| Independent implementation review | Terra / high |

All selectable routes and availability fallbacks start at high. The hosted
GitHub bot's model is not selectable. Read
[model routing](skill/chief-engineer/references/model-routing.md) for provider
roles, availability fallbacks, and exact chief model ID. Adapter model pins,
effort, budgets, and sandboxes live in `ce-dispatch.sh`; keep the optional
write-agent TOMLs in `agents/` aligned when changing them. Scout and reviewer
always use the adapter's real sandbox. Native write agents are usable only when
the active surface proves model, effort, fresh context, and sandbox behavior.

Read the shared [review policy](skill/chief-engineer/references/review-policy.md)
before selecting lanes or claiming completion. Normal semantic code requires
focused independent Terra high review. High-risk work adds a separate named
cross-model challenge. Every PR requires appropriate deterministic checks/CI
and a clean cumulative GitHub Codex bot verdict bound to the candidate head;
a new commit invalidates that GitHub clean. Moving the policy into a reference
does not change these requirements.

## Pre-wave dispatch guard

Before each write wave:

```bash
python3 "$CE/scripts/ce-token-report.py" --objective-id OBJ-001 --gate-only
```

This runs the same manifest, failed-run, budget, repeat, and writer-concurrency
checks as the full report, with only the blocking result and reasons. It needs
an objective ID and skips the session database and rollout telemetry. A nonzero
result blocks the next write wave. This is a caller-run check, not an adapter hook.

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
advisory: rollover also needs a natural boundary or observed quality degradation;
these signals never create tasks automatically or block unrelated work. The
general report does not evaluate a blocking gate.
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
skill/chief-engineer/   Installable doctrine, on-demand operations, and adapters
agents/                 Optional write-capable custom-agent TOML definitions
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
