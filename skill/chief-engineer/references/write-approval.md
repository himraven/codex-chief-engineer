# Write approval record

Create this file only after a human explicitly approves the write-capable
dispatch. The adapter checks `approval` and binds the record to the exact brief
content through its SHA-256.

```text
approval: approved
brief_sha256: <output of shasum -a 256 /absolute/path/to/brief.md>
approved_by: <human handle or name>
approved_at: <ISO 8601 timestamp>
```

Keep the record local with the task or result artifacts. Do not commit private
project metadata merely to satisfy this check.
