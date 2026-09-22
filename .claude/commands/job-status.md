---
description: List jobs by status, or update a job's status (list, show, set).
---

Argument: `$ARGUMENTS` — one of:

- (empty) or `list` → list all non-rejected jobs.
- `list <status>` → list jobs with a specific status (`new`, `seen`,
  `saved`, `applied`, `rejected`, `expired`).
- `show <job_id>` → show full details + status history for one job.
- `set <job_id> <status> [note...]` → change a job's status, optionally
  with a note (e.g. `set 14 applied "applied via Indeed Apply"`).

Translate the argument into the matching `job-search-agent/scripts/status.py`
invocation, e.g.:

```bash
python3 job-search-agent/scripts/status.py list --status saved
python3 job-search-agent/scripts/status.py show 14
python3 job-search-agent/scripts/status.py set 14 applied --note "applied via Indeed Apply"
```

Show the command's output to the user. If the argument doesn't parse into
one of the above forms, ask for clarification rather than guessing.
