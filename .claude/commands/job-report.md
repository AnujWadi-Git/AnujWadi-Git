---
description: Show the daily job search report from the local database (no new search).
---

Invoke the `job-report` skill (see `job-search-agent/skills/job-report/SKILL.md`).

Argument (optional): `$ARGUMENTS` — a date in `YYYY-MM-DD` format. If empty,
show today's report.

Run `python3 job-search-agent/scripts/report.py [--date $ARGUMENTS]` and show
the full output to the user.
