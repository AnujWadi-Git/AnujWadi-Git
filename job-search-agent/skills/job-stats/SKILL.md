---
name: job-stats
description: Show aggregate statistics about the job search database (totals by status/match category, recent search runs). Use when the user runs /job-stats or asks "how many jobs have I found", "how many have I applied to", "show search history".
---

# Job Stats Skill

Read-only summary of the whole job database — no searching, no filtering
changes.

## Procedure

```bash
cd job-search-agent
python3 scripts/stats.py
```

This prints total jobs tracked, breakdown by status (`new` / `seen` /
`saved` / `applied` / `rejected` / `expired`), breakdown by match category,
total applications, total companies, and the last 10 search runs with their
new/duplicate/rejected counts.

Show the output to the user as-is; add one or two sentences of narrative
interpretation only if something stands out (e.g. rejection rate spiking,
no strong matches in several days), don't just repeat the numbers back.

## Related: job-status

To list or change individual job statuses (mark something `saved`,
`applied`, or `rejected` manually), use:

```bash
python3 scripts/status.py list [--status saved]
python3 scripts/status.py show <job_id>
python3 scripts/status.py set <job_id> <new_status> --note "..."
```

Valid statuses: `new`, `seen`, `saved`, `applied`, `rejected`, `expired`.
Setting a job to `applied` automatically creates a row in the
`applications` table with today's date.
