#!/usr/bin/env python3
"""Generate the daily job search report from the database.

Usage:
    python report.py                 # today's report, printed to stdout
    python report.py --save          # also save to reports/YYYY-MM-DD.md
    python report.py --date 2026-09-20
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _fmt_salary(row) -> str:
    lo, hi = row["salary_min"], row["salary_max"]
    if lo is None and hi is None:
        return "salary not listed"
    period = "/hr" if row["salary_period"] == "hourly" else ""
    if lo and hi and lo != hi:
        return f"${lo:,}{period}–${hi:,}{period}"
    val = lo or hi
    return f"${val:,}{period}"


def _fmt_job_block(row) -> str:
    reasons = json.loads(row["match_reasons"] or "[]")
    why = "; ".join(reasons) if reasons else "meets basic role/skill criteria"
    posted = row["posted_date"] or "unknown"
    posted_str = "unknown" if posted == "unknown" else f"posted {posted}"
    lines = [
        row["title"],
        row["company_name"],
        row["location"] or "location unknown",
        _fmt_salary(row),
        row["experience_required"] or "unknown",
        posted_str,
        "",
        "Why it matches:",
        why,
        "",
        f"Sponsorship: {row['sponsorship']}",
        f"Apply: {row['apply_url'] or row['source_url'] or 'link unavailable'}",
    ]
    return "\n".join(lines)


def generate_report(date: str | None = None) -> str:
    with db.connect() as conn:
        if date:
            rows = conn.execute(
                "SELECT jobs.*, companies.name AS company_name FROM jobs "
                "JOIN companies ON jobs.company_id = companies.id "
                "WHERE jobs.first_seen_date = ? ORDER BY jobs.match_category",
                (date,),
            ).fetchall()
        else:
            rows = db.jobs_seen_today(conn)
            date = db.today_iso()

        strong = [r for r in rows if r["match_category"] == "strong"]
        potential = [r for r in rows if r["match_category"] == "potential"]
        low = [r for r in rows if r["match_category"] == "low"]
        rejected_today = conn.execute(
            "SELECT COUNT(*) AS c FROM jobs WHERE first_seen_date = ? AND status = 'rejected'",
            (date,),
        ).fetchone()["c"]
        dup_today = conn.execute(
            "SELECT SUM(duplicate_count) AS c FROM search_runs WHERE run_date = ?",
            (date,),
        ).fetchone()["c"] or 0

    lines = []
    lines.append("DAILY JOB SEARCH")
    lines.append(date)
    lines.append("")
    lines.append(f"New jobs found: {len(rows)}")
    lines.append(f"Strong matches: {len(strong)}")
    lines.append(f"Potential matches: {len(potential)}")
    lines.append(f"Rejected: {rejected_today}")
    lines.append(f"Duplicates: {dup_today}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("")

    if rows:
        lines.append("NEW JOBS")
        lines.append("")
        for row in strong + potential + low:
            lines.append(_fmt_job_block(row))
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
    else:
        lines.append("No new jobs found in this run.")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")

    lines.append("APPLY FIRST")
    lines.append("")
    if strong:
        for row in strong:
            lines.append(_fmt_job_block(row))
            lines.append("")
    else:
        lines.append("No strong matches today. Review potential matches above.")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None, help="Report date (YYYY-MM-DD), default: today")
    parser.add_argument("--save", action="store_true", help="Save the report to reports/")
    args = parser.parse_args()

    report_text = generate_report(args.date)
    print(report_text)

    if args.save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = args.date or db.today_iso()
        out_path = REPORTS_DIR / f"{date_str}.md"
        out_path.write_text(report_text, encoding="utf-8")
        print(f"\nSaved to {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
