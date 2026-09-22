# Job Search Agent

An AI job search automation system built for Claude Code, focused on
finding relevant, new-grad-appropriate jobs on Indeed — filtered,
deduplicated, tracked in a local database, and summarized in a daily
report you can act on.

It's designed to be run *from inside a Claude Code session* (not as a
standalone script), because the actual Indeed search happens through
Claude's Indeed MCP tool. This repo is the "brain" around that search:
filtering, deduplication, history, and reporting.

## What this does

1. You run `/indeed-search` (optionally with a location or role hint).
2. Claude searches Indeed for your target roles/locations.
3. This project's Python pipeline filters out irrelevant/senior/excluded
   roles, extracts salary/location/experience/sponsorship info when
   stated, deduplicates against everything you've seen before, and
   classifies each new posting as a **Strong match**, **Potential match**,
   or **Low relevance** — using explicit rules, never a fake score.
4. Everything is saved to a local SQLite database so you never see the
   same job twice, and can track which ones you've saved, applied to, or
   rejected.
5. You get a clean daily report, with an **APPLY FIRST** section at the
   bottom highlighting your strongest matches.

## Installation

```bash
cd job-search-agent
pip install -r requirements.txt
```

That's it — SQLite is in the Python standard library, and the only real
dependency is PyYAML (for the config file) plus pytest (for the test
suite).

## Configuration

Everything about *you* — education, skills, target roles, locations,
salary target, exclusion rules — lives in one file:

```
config/job_preferences.yaml
```

It comes pre-filled with a sensible default profile (new grad, M.S.
Robotics & AI from ASU, full-stack/AI/ML/robotics skill set, Phoenix/
Tempe/remote-US locations). Edit it directly — no Python code changes are
ever required to change what gets searched for or filtered out.

Common edits:
- Add/remove a target role under `roles.target`.
- Add a city under `locations.primary`, or set
  `locations.relocation_friendly: false` to stop considering other US
  cities.
- Raise/lower `filters.max_experience_years` if you want more or fewer
  "3+ years" postings let through.
- Change `salary.target_min_usd` — note this only affects the "why it
  matches" text and prioritization, it never causes an automatic
  rejection.

## Running your first search

From inside Claude Code, in this repository:

```
/indeed-search
```

Or scope it:

```
/indeed-search phoenix
/indeed-search remote
/indeed-search ai
```

Claude will search Indeed, run the results through the filtering pipeline,
save everything to `data/jobs.db`, and show you the report. The same thing
happens under the hood as:

```bash
cd job-search-agent
python3 scripts/process_jobs.py --input raw_jobs.json --query "AI Engineer" --location "Phoenix, AZ"
python3 scripts/report.py --save
```

(`raw_jobs.json` is produced by Claude from live Indeed results — see
`skills/indeed-search/SKILL.md` for the exact schema if you want to feed it
data manually, e.g. from a test fixture.)

## Daily workflow

```
/indeed-search        # run a new search, see the report
/job-report            # re-show today's report without searching again
/job-status list       # see everything you've saved/applied/rejected
/job-status set 14 applied --note "applied via Indeed Apply"
/job-stats              # totals, by status, by match category, recent runs
```

## Tracking applications

Every job has a status: `new` → `seen` → `saved` → `applied` (or
`rejected` / `expired`). Update it with:

```bash
python3 scripts/status.py set <job_id> applied --note "applied 2026-09-22"
```

This automatically logs an entry in the `applications` table and the
`job_status_history` table — nothing is ever silently overwritten, so you
always have a full history of every status change.

## GitHub setup

This project lives inside your existing repository. If you want to keep
your job search history private:

- Make sure the repository (or this subdirectory, if you're vendoring it
  elsewhere) is in a **private** GitHub repo.
- `data/jobs.db` and `reports/*.md` are gitignored by default — the search
  history stays local unless you deliberately commit it.
- Never commit `.env` (copy `.env.example` to `.env` for any future
  integration credentials).

If you *do* want your job search history version-controlled (e.g. to sync
between machines), remove the `data/*.db` and `reports/*.md` lines from
`.gitignore` and commit deliberately.

## Scheduling

To run this automatically (e.g. every morning), you need something that
can invoke a Claude Code session with `/indeed-search` on a schedule —
this repo doesn't ship its own scheduler because the search step needs
live Claude+Indeed tool access, not just a cron job running Python.

Options, depending on your environment:
- **Claude Code on the web**: use a scheduled trigger that fires
  `/indeed-search` (see the Claude Code docs on triggers/scheduling for
  your platform).
- **Local cron + `claude` CLI**, if your Claude Code setup supports
  headless/non-interactive invocation:
  ```cron
  0 8 * * * cd /path/to/repo && claude -p "/indeed-search" >> /path/to/logfile 2>&1
  ```
  (Twice a day: add a second line at, e.g., `0 17 * * *`.)
- Whatever you choose, the Python pipeline itself (`process_jobs.py`,
  `report.py`) is fully idempotent and safe to re-run — duplicates are
  always caught, nothing is double-counted.

## Troubleshooting

**"No module named yaml"** — run `pip install -r requirements.txt`.

**"No new jobs found"** — check `python3 scripts/stats.py` for recent
search run counts; if `results_count` is 0, Indeed's search likely
returned nothing for that query/location (or the MCP tool call failed) —
re-run `/indeed-search` and check Claude's summary of what it searched.

**A job I care about was rejected** — check its `rejection_reason` via
`python3 scripts/status.py show <job_id>` (rejected jobs are still stored,
never deleted). If a filter is too aggressive for your taste, adjust
`config/job_preferences.yaml` (`filters.max_experience_years`,
`roles.excluded_categories`) rather than editing `scripts/filters.py`
directly.

**I keep seeing near-duplicate postings** — dedup keys off the Indeed job
id or normalized URL first; if a company reposts the exact same role under
a new listing with no shared id/URL, it will look "new" once — that's
expected, Indeed doesn't expose a cross-listing identity for that case.

**Salary/sponsorship shows "not listed"/"not_specified"** — this is by
design: the system never invents missing information. If Indeed's posting
didn't state it, the report says so explicitly instead of guessing.

## Expanding to other sources

The pipeline (`scripts/process_jobs.py`) is source-agnostic — it just wants
a JSON list of postings with a `source` field. To add LinkedIn, Greenhouse,
Lever, YC, or company career pages later:

1. Add a new skill (e.g. `skills/linkedin-search/SKILL.md`) that collects
   postings into the same JSON schema used by `indeed-search`.
2. Set `"source": "linkedin"` (etc.) on each posting — deduplication is
   already scoped per-source, so this won't collide with Indeed job keys.
3. Flip the corresponding flag on in `config/job_preferences.yaml` under
   `sources:`.

No changes to `filters.py`, `dedup.py`, or `db.py` are needed for a new
source unless it needs source-specific extraction logic.
