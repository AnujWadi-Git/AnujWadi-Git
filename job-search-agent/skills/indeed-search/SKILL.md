---
name: indeed-search
description: Search Indeed for jobs matching the candidate profile in config/job_preferences.yaml, filter/dedupe/store results in the local database, and produce the daily report. Use when the user runs /indeed-search, asks to "search for jobs", "find AI engineer jobs", "run today's job search", or names a location/role filter like "/indeed-search phoenix" or "/indeed-search remote".
---

# Indeed Search Skill

This skill drives the end-to-end job search: querying Indeed through the
`mcp__Indeed__search_jobs` / `mcp__Indeed__get_job_details` tools, then
handing the raw postings to this repo's deterministic Python pipeline
(`job-search-agent/scripts/process_jobs.py`) for filtering, deduplication,
classification, and storage. **Claude does the searching (it has the Indeed
tool access); the scripts do the judging (they're testable and don't
hallucinate).**

## Working directory

All commands below assume `job-search-agent/` as the working directory
(paths are relative to it). Read `job-search-agent/config/job_preferences.yaml`
before every run — it is the single source of truth for queries, locations,
skills, and filter thresholds. Never hardcode candidate details in this
skill file; if something needs to change, it changes in the config, not here.

## Step-by-step procedure

### 1. Parse the invocation

- `/indeed-search` with no argument → use `search.default_queries` ×
  `search.default_locations` from the config.
- `/indeed-search phoenix` or `/indeed-search tempe` → restrict locations to
  that city, still run all default role queries.
- `/indeed-search remote` → restrict to `location: "remote"`.
- `/indeed-search ai` (or `ml`, `robotics`, etc.) → restrict queries to the
  roles matching that theme (e.g. "ai" → AI Engineer, ML Engineer, LLM
  Engineer, Agentic AI Engineer).
- Any other free-text argument → treat it as an additional search query on
  top of the defaults, not a replacement.

### 2. Search Indeed

For each (query, location) pair to run:

1. Call `mcp__Indeed__search_jobs` with `search=<query>`, `location=<location>`,
   `country_code="US"`, and `job_type` set from `employment.preferred` when the
   tool supports it (try `fulltime`, then `contract` if the user wants
   contract roles too — don't set `job_type` to `internship`).
2. The tool returns markdown with job listings and links. Parse out each
   distinct job posting: title, company, location, a snippet of the
   description, and the apply/source URL. Do not fabricate any field you
   cannot see in the tool output.
3. For postings that look like strong candidates (title matches a target
   role, no obvious hard-exclusion keyword in the title) but whose returned
   snippet is too short to judge salary/experience/sponsorship, call
   `mcp__Indeed__get_job_details` with that job's id to get the full
   description. Do this for at most ~15 postings per run to keep it fast —
   prioritize postings whose titles look most relevant.
4. Skip calling `get_job_details` for postings that are obviously excluded
   by title alone (e.g. "Senior Staff Engineer", "IT Help Desk Technician")
   — no need to spend a tool call confirming an exclusion in the title.

### 3. Build the raw jobs JSON

Assemble every collected posting into a JSON array matching this schema and
write it to a scratch file (use your scratchpad directory, not the repo):

```json
[
  {
    "title": "...",
    "company": "...",
    "location": "...",
    "description": "...",            // full text if you fetched details, else the snippet
    "posted_date": "2026-09-20",      // ISO date ONLY if Indeed states it; else omit (defaults to "unknown")
    "employment_type": "fulltime",
    "source": "indeed",
    "source_url": "https://www.indeed.com/viewjob?jk=...",
    "apply_url": "https://www.indeed.com/viewjob?jk=...",
    "job_id": "abc123"                // the Indeed job id if you have it
  }
]
```

Rules:
- **Never invent a URL, salary, date, or job id.** If Indeed's output didn't
  give you one, omit the field entirely — the pipeline treats missing data
  as "unknown" / "not_specified", never as a guess.
- Keep URLs exactly as returned, including query parameters — the pipeline's
  deduplication logic normalizes them itself.
- Include jobs even if you think they might get rejected by the filters —
  rejection should happen in the (testable, auditable) filter code, not by
  you silently dropping postings.

### 4. Run the pipeline

```bash
cd job-search-agent
python3 scripts/process_jobs.py --input /path/to/scratch/raw_jobs.json \
    --query "<query used>" --location "<location used>"
```

Run this once per (query, location) batch, or combine everything from one
`/indeed-search` invocation into a single JSON file and run it once — either
is fine, the pipeline dedupes and upserts either way.

The script prints a summary (new / duplicate / rejected / match category
counts). Read it and surface it to the user in your own reply.

### 5. Generate the report

```bash
python3 scripts/report.py --save
```

This prints the daily report (see `skills/job-report/SKILL.md` for the
report contract) and saves it to `reports/YYYY-MM-DD.md`. Show the report
content to the user in your reply — don't just say "done, check the file".

### 6. Commit

If the user has git configured for this repo and hasn't asked you not to,
stage and commit the changes (`data/jobs.db`, `reports/*.md`) with a message
like `Job search run: N new, M rejected (<date>)`. Push only if the user has
already established that pushes are expected for this workflow (e.g. they
said so earlier in the session) — otherwise leave it committed locally and
mention that a push is pending.

## Filtering rules this skill relies on (implemented in `scripts/filters.py`)

- **Hard exclusions** (title): senior, staff, principal, lead, manager,
  director, architect.
- **Hard exclusions** (category): IT support/help desk, embedded/firmware/
  hardware/electrical/electronics engineering, QA/test-only, data analyst/BI
  analyst, pure data engineer/DevOps/SRE (unless AI/ML-flavored), cybersecurity,
  sales engineering, nontechnical consulting, internships.
- **Hard exclusions** (requirements): security clearance, ITAR, mandatory US
  citizenship. Generic "must be authorized to work in the US" is **not**
  excluded.
- **Experience**: rejects postings explicitly requiring more than
  `filters.max_experience_years` (default 2) years, unless the posting also
  contains new-grad/entry-level language.
- **Never auto-rejects** for missing or low salary, or missing sponsorship
  info — those are tracked and reported, not filtered.
- **Match categories** (`strong` / `potential` / `low`) come from explicit,
  auditable rules in `evaluate_job()` — never a numeric score.

## Avoiding hallucination

- If you're unsure whether a posting is a duplicate, let `dedup.py` decide —
  it hashes on job id / normalized URL / (company, title, location), don't
  try to eyeball it yourself.
- If a posted date isn't explicitly visible, use `"unknown"`. Do not infer
  "posted today" just because it appeared in today's search.
- If a salary isn't stated, leave it out of the JSON entirely. The regex
  extractor in `filters.py` will correctly report "not listed" downstream.
- Quote job requirements/descriptions close to verbatim in the `description`
  field — the filters and match-reason generator work off that text, and
  paraphrasing risks losing a disqualifying or qualifying detail.
