#!/usr/bin/env python3
"""Ingest raw job postings, filter/classify them, store in SQLite, and report
on the run.

This script does NOT talk to Indeed itself — job search happens through the
Indeed MCP tool inside the Claude Code session (see
skills/indeed-search/SKILL.md). Claude collects raw postings into a JSON
file matching the schema below, then calls this script to do the
deterministic, testable work: dedup, filtering, classification, and
persistence.

Input JSON schema (list of objects):
[
  {
    "title": "...",
    "company": "...",
    "location": "...",
    "description": "...",       # full job description text if available
    "posted_date": "2026-09-20", # ISO date, or omit if unknown
    "employment_type": "fulltime",
    "source": "indeed",
    "source_url": "https://...",
    "apply_url": "https://...",
    "job_id": "abc123"           # optional explicit source job id
  },
  ...
]

Usage:
    python process_jobs.py --input raw_jobs.json [--query "AI Engineer"] [--location "Phoenix, AZ"]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db
import dedup
from config_loader import load_config
from filters import evaluate_job


def days_ago(posted_date: str | None) -> int | None:
    if not posted_date or posted_date == "unknown":
        return None
    try:
        posted = dt.date.fromisoformat(posted_date)
    except ValueError:
        return None
    return (dt.date.today() - posted).days


def process_batch(raw_jobs: list[dict], config: dict) -> dict:
    """Run the full pipeline over a batch of raw jobs. Returns a summary dict
    with the per-job outcomes, for reporting."""
    unique_jobs, in_batch_dupes = dedup.dedupe_batch(raw_jobs)

    results = {
        "new": [],
        "duplicate_existing": [],
        "rejected": [],
        "in_batch_duplicates": in_batch_dupes,
    }

    db.init_db()
    with db.connect() as conn:
        existing_keys = db.all_job_keys(conn)

        for job in unique_jobs:
            job_key = job["job_key"]
            if job_key in existing_keys:
                # Already known: just bump last_seen_date.
                db.upsert_job(conn, job)
                results["duplicate_existing"].append(job)
                continue

            evaluation = evaluate_job(job, config)

            if evaluation.rejected:
                job["status"] = "rejected"
                job["rejection_reason"] = evaluation.rejection_reason
                job["match_category"] = None
                job_id, is_new = db.upsert_job(conn, job)
                results["rejected"].append(job)
                existing_keys.add(job_key)
                continue

            job["salary_min"] = evaluation.salary.min
            job["salary_max"] = evaluation.salary.max
            job["salary_currency"] = evaluation.salary.currency
            job["salary_period"] = evaluation.salary.period
            job["sponsorship"] = evaluation.sponsorship
            job["work_arrangement"] = evaluation.work_arrangement
            job["experience_required"] = evaluation.experience_required
            job["skills"] = evaluation.skills_found
            job["match_category"] = evaluation.match_category
            job["match_reasons"] = evaluation.match_reasons
            job["status"] = "new"
            job.setdefault("posted_date", "unknown")

            db.upsert_job(conn, job)
            existing_keys.add(job_key)
            results["new"].append(job)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to raw jobs JSON file")
    parser.add_argument("--query", default=None, help="Search query used to produce this batch")
    parser.add_argument("--location", default=None, help="Search location used to produce this batch")
    parser.add_argument("--config", default=None, help="Path to job_preferences.yaml")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        raw_jobs = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: malformed input JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(raw_jobs, list):
        print("error: input JSON must be a list of job objects", file=sys.stderr)
        return 1

    config = load_config(Path(args.config)) if args.config else load_config()

    # Skip malformed entries rather than crashing the whole batch.
    clean_jobs = []
    skipped = 0
    for job in raw_jobs:
        if not isinstance(job, dict) or not job.get("title") or not job.get("company"):
            skipped += 1
            continue
        clean_jobs.append(job)

    results = process_batch(clean_jobs, config)

    with db.connect() as conn:
        db.record_search_run(
            conn,
            query=args.query or "unspecified",
            location=args.location or "unspecified",
            results_count=len(raw_jobs),
            new_count=len(results["new"]),
            duplicate_count=len(results["duplicate_existing"]) + results["in_batch_duplicates"],
            rejected_count=len(results["rejected"]),
        )

    print(f"Processed {len(raw_jobs)} raw postings ({skipped} skipped as malformed).")
    print(f"  New:                 {len(results['new'])}")
    print(f"  Duplicates (in-batch): {results['in_batch_duplicates']}")
    print(f"  Duplicates (existing): {len(results['duplicate_existing'])}")
    print(f"  Rejected:            {len(results['rejected'])}")
    if results["new"]:
        strong = sum(1 for j in results["new"] if j.get("match_category") == "strong")
        potential = sum(1 for j in results["new"] if j.get("match_category") == "potential")
        low = sum(1 for j in results["new"] if j.get("match_category") == "low")
        print(f"  Strong matches:      {strong}")
        print(f"  Potential matches:   {potential}")
        print(f"  Low relevance:       {low}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
