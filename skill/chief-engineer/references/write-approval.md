# Write approval record

Create only after explicit human approval covers the write-capable dispatch.
Existing approval remains valid within its approved solution, ownership,
permissions, and topology; do not ask again just to record it. If these expand,
obtain new approval before dispatch. Bind each record to the exact brief.

```text
approval: approved
brief_sha256: <SHA-256 of the exact approved brief>
approved_by: <human handle or name>
approved_at: <ISO 8601 timestamp>
```

The adapter checks approval state, approver, and brief hash. A hash proves which
brief was bound, not that broader authority was granted. Keep the record local
with task/result artifacts; do not commit private metadata to satisfy this check.
