# Chief-engineer operations

Read this reference only when invoking the Codex adapter, an external review
lane, or the usage report. `SKILL.md` owns doctrine; this file owns CLI and
substrate mechanics.

## Codex adapter

Set `CE="${CODEX_HOME:-$HOME/.codex}/skills/chief-engineer"` and run
`"$CE/scripts/ce-dispatch.sh" --help` before dispatch. Its help and
implementation are authoritative for flags, model pins, budgets, sandbox
selection, approved roots, approval records, repeat detection, and result
manifests.

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

## Sandbox boundaries (2026-07-29 policy; evidence = 45 ledger incidents)

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
  --model claude-opus-5 \
  --effort low \
  --tools "" \
  --no-session-persistence \
  --safe-mode \
  --output-format json \
  < /absolute/path/to/review-prompt.txt
```

Use `medium` or `high` only under the effort rules in `SKILL.md`. For the
recorded Opus 4.8 availability fallback, substitute model
`claude-opus-4-8` and effort `high`.

- Keep the prompt outside the repository. Include only the minimum authorized,
  redacted named question, diff/context, and exact evidence contract.
- Do not interpolate a raw diff into shell arguments.
- Disable prior-memory carryover, redelegation, subagents, web, MCP, and writes.
- Keep thinking enabled; control cost with effort rather than disabling it.
- Ask for every finding with severity and confidence; filter downstream.
- Treat listed commands/results as the evidence contract. Do not request
  generic double-checking or rerun verification prose.
- Report out-of-cone risk without investigating it.

If quality requires `Read,Grep,Glob`, expose only the authorized cone through an
OS/filesystem sandbox or projection. Then add both flags:

```text
--tools "Read,Grep,Glob"
--allowedTools "Read,Grep,Glob"
```

Prompt-only path restrictions are not access control.

For pinned Grok 4.5, send only authorized redacted non-secret context. Use a
fresh single read-only/plan turn with memory, subagents, and web disabled where
supported.

## Usage and dispatch health

Run:

```bash
CE="${CODEX_HOME:-$HOME/.codex}/skills/chief-engineer"
python3 "$CE/scripts/ce-token-report.py" --objective-id <objective-id>
```

The report reads local rollouts and manifests. It shows exact daily usage,
cached versus uncached input, repeated fingerprints, phase diagnostics, and
objective-wide write concurrency. A nonzero current dispatch/guardrail gate
blocks the next write wave. See `ce-token-report.py --help` for optional flags.
