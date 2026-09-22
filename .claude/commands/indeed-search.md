---
description: Search Indeed for jobs matching the candidate profile, filter/dedupe/store results, and produce the daily report.
---

Invoke the `indeed-search` skill (see `job-search-agent/skills/indeed-search/SKILL.md`)
to run today's job search.

Argument (optional): `$ARGUMENTS`

- If empty, run the default queries/locations from
  `job-search-agent/config/job_preferences.yaml`.
- If it names a place (e.g. `phoenix`, `tempe`, `remote`), restrict the
  location(s) for this run to that place while still running all default
  role queries.
- If it names a role theme (e.g. `ai`, `ml`, `robotics`, `backend`),
  restrict the queries for this run to roles matching that theme while
  still using the default locations.
- Otherwise, treat it as an additional free-text search query alongside the
  defaults.

Follow the skill's step-by-step procedure exactly: search via the Indeed MCP
tools, assemble a raw-jobs JSON file (never inventing missing fields), run
`job-search-agent/scripts/process_jobs.py` on it, then
`job-search-agent/scripts/report.py --save`, and show the resulting report
to the user in full.
