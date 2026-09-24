# Chief-engineer operations

Read this reference only when invoking the Codex adapter, an external review
lane, or the usage report. `SKILL.md` owns orchestration; [review policy](review-policy.md) owns review
requirements; this file owns CLI and substrate mechanics.

## Codex adapter

Set `CE="${CODEX_HOME:-$HOME/.codex}/skills/chief-engineer"` and run
`"$CE/scripts/ce-dispatch.sh" --help` before dispatch. Its help and
implementation are authoritative for flags, model pins, budgets, sandbox
selection, approved roots, approval records, repeat detection, and result
manifests.

Canonical dispatch (add a matching `--approval-file` for write roles):

```bash
"$CE/scripts/ce-dispatch.sh" \
  --role scout --objective-id OBJ-001 --phase-id P1 --workstream-id WS-evidence \
  --cwd /absolute/path/to/repository \
  --brief /absolute/path/to/brief.md --result-dir /absolute/path/to/local-results
```

Reuse stable IDs and the existing task note for a single dispatch. IDs do not
require separate lifecycle documents. Read [model routing](model-routing.md)
before choosing a role; all adapter/native routes start at high or above.

- Keep `--result-dir`, `CE_RUN_HOME`, and `CODEX_HOME` outside the repository.
- If a genuinely indivisible brief exceeds the default ceiling, record the
  exception and set `CE_MAX_BRIEF_BYTES` only for that reviewed dispatch.
- After verified model unavailability, reuse the reviewed brief once with
  `--fallback`. Do not retry a quality failure.
- Repeat an unchanged successful input only for new evidence or a new question;
  record it with `--repeat-reason`.
- Repository fingerprints exclude ignored files. If ignored runtime evidence
  matters, bind its narrow digest in the brief. Never hash dependency, build,
  cache, secret, or whole runtime trees.
- `plutil -extract KEYPATH FMT FILE` is read-only by default and writes to
  stdout; `-o PATH` selects an explicit output file. Use `raw`, `xml1`, or
  `json` for machine consumption; `-p` is human-readable but unstable.

Before activating new model pins, check the actual `codex --version` and perform
a bounded real request on that login surface. Codex 0.156.1 is the tested baseline;
0.153.4 rejected GPT-6 Sol/Luna on the same ChatGPT account. Use the existing
client update mechanism, then verify adapter isolation and a real bounded run.
Do not interpret a catalog entry as successful account access.

## Sandbox boundaries

These restrictions preserve the 2026-07-29 policy. The version-specific
observations below describe the audited 0.144.x runtime, not a new audit of
today’s binary. Recheck capabilities before changing a boundary.

Four boundary classes, four different answers. Do not improvise others.

1. **Writable temp for read roles** (largest class, ~18 dispatches: pytest
   `tmp_path`, heredocs, Vite temp) → dispatch scout/reviewer with
   `--scratch-tmp`. The run becomes workspace-write, but codex's cwd is a fresh
   scratch dir under the result dir — the repository is not a writable root, so
   it stays read-only at the kernel while temp works. The adapter fails the run
   (exit 76) if the repo fingerprint changed. No write approval record needed.
2. **Package-registry network for write roles** (npm/PyPI DNS) → add
   `--network "<reason>"` to a mechanic/worker/senior dispatch. This sets
   `sandbox_workspace_write.network_access=true` for that run only. Radius is
   ALL outbound (codex 0.144.x has no domain scoping; `network_proxy` is
   experimental/off; `allow_unix_sockets` parses but is INERT — do not use).
   Prefer pre-warmed caches/`node_modules` when deps are already pinned; the
   flag is for genuine dependency-closure work. Reason lands in the manifest.
3. **Git metadata writes outside cwd** (linked-worktree `index.lock`,
   `FETCH_HEAD`, rebase state) → **intentional; do not open.** Three ledgers
   independently converged on the doctrine: workers edit files, git operations
   belong to the dispatcher. With `--network` this also keeps `git push`
   structurally blocked.
4. **SSH / GitHub from read roles** → **stays fail-closed by design** (scouts
   returning UNKNOWN instead of inventing causes is praised behavior). The
   chief pre-stages instead: `git fetch` + pin `refs/ce/<name>` refs locally,
   pre-warm caches, or gather remote facts on the chief's own authorized
   surface, then dispatch offline work against the staged state.

Standing exposure to remember when writing briefs: codex's Seatbelt policy
allows **machine-wide reads in every mode** (`(allow file-read*)`) — `~/.ssh`
private keys and any local secret are readable by every worker. Do not paste
secret paths into briefs, and treat "the sandbox will hide it" as false.

## Claude review or challenge

Default to a fresh, tool-less, non-persistent turn:

```bash
claude -p \
  --model claude-opus-5-5 \
  --effort high \
  --tools "" \
  --no-session-persistence \
  --safe-mode \
  --output-format json \
  < /absolute/path/to/review-prompt.txt
```

The normal eligible lane is Opus 5.5 high; the recorded availability fallback is
`claude-opus-5` high. Follow [review policy](review-policy.md) for eligibility,
provider authorization, fallback order, and the exact evidence contract.
`--safe-mode` disables customizations (CLAUDE.md, skills, plugins, hooks, MCP,
custom agents); `--no-session-persistence` prevents resume. Keep thinking on.

If quality requires `Read,Grep,Glob`, expose only the authorized cone through an
OS/filesystem sandbox or projection. Then add both flags:

```text
--tools "Read,Grep,Glob"
--allowedTools "Read,Grep,Glob"
```

Prompt-only path restrictions are not access control.

For pinned `grok-4.7` at high effort, send only authorized redacted non-secret
context. Verify `grok models` and a real request on the intended login. Use a
fresh single turn with no resume, memory, subagents, web or model-accessible
tools. On the tested Grok Build 0.2.72 surface, the relevant flags are
`--model grok-4.7 --effort high --tools "" --no-memory --no-subagents
--disable-web-search --max-turns 1`. Pass a prompt file rather than shell-expanded
content. These flags are not a filesystem or configuration-isolation claim;
Grok may discover local configuration. If the authorized context boundary
cannot be demonstrated, use a suitably isolated projection or leave the lane
unavailable. Do not substitute a floating `grok-build`/`latest` alias.

## Dispatch gate and optional usage report

Before each write wave, run the existing guard with compact output:

```bash
python3 "$CE/scripts/ce-token-report.py" --objective-id <objective-id> --gate-only
```

This uses the same manifest validation, failed-run, budget, repeat, and write
concurrency checks as the full report. It prints only the objective's blocking
result and reasons; it does not load the session database or rollout telemetry.
A nonzero guard result blocks the next write wave. `--gate-only` requires an
objective ID; it is not a way to skip the guard.

For a cost investigation or periodic audit, omit `--gate-only`. The full report
adds daily usage, cache breakdown, and session/phase diagnostics. Historical
health signals are advisory. Do not run a standing telemetry process.
