# Worker brief template

## Objective

One sentence describing the exact outcome and why this slice exists.

## Verified facts

- Current commit, runtime, and evidence:
- Relevant files and symbols:
- Existing parallel work:

## Ownership and constraints

- Owned paths:
- Forbidden paths:
- Fixed decisions and interfaces:
- Risk tier and red-line boundary:
- Network and setup boundary:

## Work and stop condition

1. Exact work to perform:
2. Decision-relevant question, if any:
3. Stop immediately and return if:

## Verification

```text
<exact commands>
```

Success means: <observable criterion>.

## Budget and return format

- Tool budget: <N>.
- Final response: concise and within the role's fixed byte ceiling.
- Return: changed files or findings; commands run; actual results; unresolved
  uncertainty; and the next smallest decision if blocked.
