# Worker brief template

The brief should be sufficient, not artificially short. Remove copied
conversation and raw logs; preserve every decision, contract, and fact needed
to execute without consulting the chief transcript.

## Lifecycle identity

- Objective ID:
- Phase ID:
- Workstream ID:
- Persisted chief-state path:
- Dispatch form: ephemeral | persistent continuation

## Objective

One sentence describing the exact outcome and why this slice exists.

## Verified facts and fixed decisions

- Current commit, runtime, and evidence:
- Relevant files, symbols, interfaces, and prior work:
- Architecture and product decisions already made:
- Decision that remains with the chief:

## Ownership and constraints

- Owned paths:
- Forbidden paths:
- Risk tier and red-line boundary:
- Network and setup boundary: <none | pre-warmed cache at PATH | --network "<reason>" authorized>
  (read roles needing temp files: dispatch with --scratch-tmp; see operations.md
  "Sandbox boundaries" — SSH/GitHub facts are pre-staged by the chief, never
  fetched by the worker)
- Other active workstreams and convergence contract:

## Work and stop condition

1. Exact work or evidence to produce:
2. Decision-relevant question, if any:
3. Stop immediately and return if:

## Verification

```text
<exact commands>
```

Success means: <observable criterion>.

## Budget and return format

- Tool budget: <N>.
- Output: concise evidence, without raw-log or transcript dumps.
- Return: changed files or findings; commands run; actual results; artifact or
  diff fingerprint; unresolved uncertainty; and the next smallest decision if
  blocked.
