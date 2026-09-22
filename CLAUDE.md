# CLAUDE.md

This repository is Anuj Wadi's GitHub profile repo (`AnujWadi-Git/AnujWadi-Git`
— the special repo whose `README.md` renders on the GitHub profile page) and
**also** hosts the `job-search-agent/` project: a self-contained AI job
search automation system, primarily targeting Indeed.

Root-level `README.md` and `AnujWadi-GitHub-Profile/` are the GitHub profile
content — do not modify them as part of job-search-agent work unless
explicitly asked.

Everything below concerns `job-search-agent/`.

## Project architecture

```
job-search-agent/
  config/
    job_preferences.yaml   # ALL candidate/search settings live here
  scripts/
    db.py                  # SQLite schema + helpers (companies, jobs, applications,
                            #   search_runs, job_status_history)
    config_loader.py       # loads job_preferences.yaml (requires PyYAML)
    dedup.py               # URL normalization + stable job identity/dedup
    filters.py             # pure rule-based filtering, extraction, classification
    process_jobs.py        # CLI: raw jobs JSON -> filter/dedupe/store -> summary
    report.py              # CLI: daily report generator (reads DB only)
    status.py              # CLI: list/show/set job status
    stats.py               # CLI: aggregate statistics
  skills/
    indeed-search/SKILL.md # drives Indeed MCP search + the pipeline above
    job-report/SKILL.md    # regenerates/shows the report without searching
    job-stats/SKILL.md     # shows aggregate stats
  tests/                   # pytest suite, run from job-search-agent/
  data/jobs.db             # SQLite database (gitignored)
  reports/YYYY-MM-DD.md    # saved daily reports (gitignored)
.claude/commands/
  indeed-search.md, job-report.md, job-stats.md, job-status.md
```

`.claude/commands/*.md` are the `/indeed-search`, `/job-report`, `/job-stats`,
`/job-status` slash commands — thin wrappers that point at the skills above.

## How search actually works (important)

There is no scraper in this repo. Job search happens through the **Indeed
MCP tool** (`mcp__Indeed__search_jobs`, `mcp__Indeed__get_job_details`)
available directly to Claude Code in this environment. The division of
labor is deliberate:

- **Claude** calls the Indeed MCP tools to fetch real postings, and
  assembles them into a raw-jobs JSON file. This is the only part of the
  system that talks to Indeed.
- **`scripts/process_jobs.py`** (deterministic, unit-tested Python) does
  everything else: deduplication, hard-exclusion filtering, salary/
  sponsorship/experience extraction, match classification, and database
  storage.

This split exists so the judgment calls (what counts as a duplicate, what
counts as a rejection, what salary a description implies) are testable code
paths, not one-off LLM guesses that can't be regression-tested.

When adding a new source later (LinkedIn, Greenhouse, Lever, YC, company
pages), follow the same pattern: a skill that collects raw postings into the
same JSON schema, feeding the same `process_jobs.py`. Add a `source` field
value like `"linkedin"` — `dedup.py`'s job-key scheme already namespaces by
source.

## Configuration

All candidate-specific and search-specific settings live in
`job-search-agent/config/job_preferences.yaml`. Never hardcode a skill,
location, role, or threshold in Python — read it from config. If the user
asks to change target roles, locations, salary target, excluded categories,
or experience thresholds, edit this YAML file, not the scripts.

## Database

SQLite at `job-search-agent/data/jobs.db` (gitignored — it's a local,
personal database, not repo content). Tables: `companies`, `jobs`,
`applications`, `search_runs`, `job_status_history`. See `scripts/db.py` for
the full schema and helper functions (`upsert_job`, `set_status`,
`record_search_run`, `stats_summary`, etc.). Job identity is a `job_key`
computed by `dedup.py` (source-scoped Indeed job id > normalized URL >
hash of company+title+location) — always go through `dedup.compute_job_key`
or `upsert_job`, never insert directly.

Valid job statuses: `new`, `seen`, `saved`, `applied`, `rejected`, `expired`.
Status changes are always recorded in `job_status_history` — use
`db.set_status()`, never a raw UPDATE.

## Filtering rules (implemented in `scripts/filters.py`)

- **Hard exclusions** (never shown): seniority keywords in title (senior,
  staff, principal, lead, manager, director, architect); IT support/help
  desk; embedded/firmware/hardware/electrical/electronics engineering;
  QA/test-only; data analyst/BI analyst; pure data engineer/DevOps/SRE roles
  (allowed through if the posting has clear AI/ML/LLM signal); cybersecurity;
  sales engineering; nontechnical consulting; internships; security
  clearance/ITAR/mandatory-citizenship requirements.
- Generic "must be authorized to work in the US" is **not** an exclusion —
  only explicit clearance/citizenship-mandatory language is.
- **Experience**: rejects postings explicitly requiring more years than
  `filters.max_experience_years` (default 2), unless new-grad/entry-level
  language is also present.
- **Never auto-rejects** for missing/low salary or missing sponsorship info
  — tracked and surfaced, not filtered.
- **Match category** (`strong` / `potential` / `low`) comes from explicit
  rule counting in `evaluate_job()` (skill overlap, AI/ML signal, location
  fit, experience fit, salary) — **never** a numeric score. Do not add
  scoring; if you touch this function, keep reasons as factual sentences.

## Safety rules

- Never invent a salary, posted date, job id, URL, or sponsorship status
  that wasn't present in what Indeed actually returned. Missing data stays
  `null` / `"unknown"` / `"not_specified"` — this is enforced end-to-end
  (extraction functions return `None` on no match; the report renders
  "salary not listed" etc.).
- Never commit `data/jobs.db`, `.env`, or anything under `reports/` other
  than the markdown reports themselves — see `.gitignore`.
- Never fabricate an apply URL. If Indeed didn't give you a link, omit
  `apply_url`/`source_url` rather than guessing one.

## Git workflow

- Commit `job-search-agent/` changes (code, config, skills, generated
  reports/db if the user wants history tracked) with descriptive messages.
- The database and daily reports are gitignored by default (see
  `job-search-agent/.gitignore`) since they're personal, frequently-changing
  data — only commit them if the user explicitly asks to track search
  history in git.
- Push only when explicitly asked, or when already established as expected
  for a recurring workflow.

## Running the system

```bash
cd job-search-agent
pip install -r requirements.txt   # PyYAML, pytest

# Run a search (via Claude + the indeed-search skill/command, not directly)
/indeed-search
/indeed-search phoenix
/indeed-search remote
/indeed-search ai

# Or, once you have a raw jobs JSON (e.g. from a skill run):
python3 scripts/process_jobs.py --input /path/to/raw_jobs.json --query "AI Engineer" --location "Phoenix, AZ"

# Reports and stats
python3 scripts/report.py --save
python3 scripts/stats.py
python3 scripts/status.py list --status saved
```

## Testing

```bash
cd job-search-agent
python3 -m pytest tests/ -q
```

Tests cover: config loading, hard-exclusion rules, experience/salary/
sponsorship/location extraction, match classification, URL normalization
and deduplication (including cross-batch and tracking-parameter variants),
database CRUD and status-history tracking, report generation (including
missing-salary and no-strong-match cases), and CLI error handling
(malformed JSON, missing files, malformed job entries). Any change to
`filters.py`, `dedup.py`, or `db.py` should come with a test.

## Coding conventions

- Python 3.11+, stdlib + PyYAML only — no heavy dependencies, no scraping
  libraries (search goes through the Indeed MCP tool, not HTTP scraping).
- Every extraction/classification function in `filters.py` is a pure
  function over plain dicts/strings, so it's unit-testable without a
  database.
- CLI scripts (`process_jobs.py`, `report.py`, `status.py`, `stats.py`) are
  thin argparse wrappers around the pure functions/db helpers — keep new
  logic in a testable module, not inline in `main()`.
