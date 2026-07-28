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
- `plutil -extract KEYPATH FMT FILE` writes back to `FILE` when `-o` is omitted.
  For inspection use `plutil -p` or pass `-o -`.

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
