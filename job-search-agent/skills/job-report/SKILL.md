---
name: job-report
description: Generate and display the daily job search report from the local database, without running a new search. Use when the user runs /job-report or asks to "show today's report", "show the last job report", or "regenerate the report for <date>".
---

# Job Report Skill

Produces the daily report format from data already in the database — no
Indeed calls, no new searching. Use `skills/indeed-search/SKILL.md` first if
the user actually wants fresh results.

## Procedure

```bash
cd job-search-agent
python3 scripts/report.py                # today
python3 scripts/report.py --date 2026-09-20
python3 scripts/report.py --save         # also writes reports/YYYY-MM-DD.md
```

Print the full report text back to the user — it's short enough to always
show in full, don't summarize it.

## Report contract

The report is generated entirely by `scripts/report.py` from the `jobs`
table. It must always contain, in this order:

1. Header: `DAILY JOB SEARCH` + date.
2. Summary counts: new jobs found, strong matches, potential matches,
   rejected, duplicates.
3. `NEW JOBS` section: every job first seen on the report date, grouped
   strong → potential → low, each with title / company / location / salary
   (or "salary not listed") / experience requirement / posted-date-or-
   "unknown" / a factual "Why it matches" line / sponsorship value / apply
   link.
4. `APPLY FIRST` section: the strong matches only, repeated in full so the
   user doesn't have to scroll back up.

**Never add a numeric score** (no "87/100", no star ratings) anywhere in the
report — match category and the factual reasons list are the only signal.
If there are no strong matches, say so plainly rather than promoting a
potential match to fill the section.
