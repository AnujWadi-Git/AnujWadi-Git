#!/usr/bin/env python3
"""Print aggregate statistics about the job search database.

Usage:
    python stats.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db


def main() -> int:
    db.init_db()
    with db.connect() as conn:
        summary = db.stats_summary(conn)
        recent_runs = conn.execute(
            "SELECT * FROM search_runs ORDER BY id DESC LIMIT 10"
        ).fetchall()

    print("JOB SEARCH STATISTICS")
    print("=" * 40)
    print(f"Total jobs tracked:     {summary['total_jobs']}")
    print(f"Total companies:       {summary['total_companies']}")
    print(f"Total applications:    {summary['total_applications']}")
    print(f"Total search runs:     {summary['total_search_runs']}")
    print()
    print("By status:")
    for status, count in sorted(summary["by_status"].items()):
        print(f"  {status:10s} {count}")
    print()
    print("By match category:")
    for cat, count in sorted((k or "n/a", v) for k, v in summary["by_match_category"].items()):
        print(f"  {cat:10s} {count}")
    print()
    print("Recent search runs:")
    for run in recent_runs:
        print(
            f"  {run['run_date']} | {run['query'] or '-':25s} | {run['location'] or '-':15s} | "
            f"results={run['results_count']:<4} new={run['new_count']:<4} "
            f"dup={run['duplicate_count']:<4} rejected={run['rejected_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
