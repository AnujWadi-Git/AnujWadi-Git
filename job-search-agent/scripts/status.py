#!/usr/bin/env python3
"""Query and update job statuses.

Usage:
    python status.py list [--status saved]
    python status.py set <job_id> <status> [--note "..."]
    python status.py show <job_id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db


def cmd_list(args) -> int:
    with db.connect() as conn:
        if args.status:
            rows = db.jobs_by_status(conn, args.status)
        else:
            rows = conn.execute(
                "SELECT jobs.*, companies.name AS company_name FROM jobs "
                "JOIN companies ON jobs.company_id = companies.id "
                "WHERE jobs.status != 'rejected' "
                "ORDER BY jobs.last_seen_date DESC"
            ).fetchall()

    if not rows:
        print("No jobs found for that filter.")
        return 0

    for row in rows:
        print(f"[{row['id']}] {row['status']:8s} {row['title']} — {row['company_name']} "
              f"({row['location'] or 'unknown location'}) — {row['match_category'] or 'n/a'}")
    return 0


def cmd_set(args) -> int:
    with db.connect() as conn:
        try:
            db.set_status(conn, args.job_id, args.status, note=args.note or "")
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    print(f"Job {args.job_id} -> {args.status}")
    return 0


def cmd_show(args) -> int:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT jobs.*, companies.name AS company_name FROM jobs "
            "JOIN companies ON jobs.company_id = companies.id WHERE jobs.id = ?",
            (args.job_id,),
        ).fetchone()
        if not row:
            print(f"error: no job with id {args.job_id}", file=sys.stderr)
            return 1
        history = conn.execute(
            "SELECT * FROM job_status_history WHERE job_id = ? ORDER BY changed_at",
            (args.job_id,),
        ).fetchall()

    data = dict(row)
    data["skills"] = json.loads(data.get("skills") or "[]")
    data["match_reasons"] = json.loads(data.get("match_reasons") or "[]")
    print(json.dumps(data, indent=2, default=str))
    print("\nStatus history:")
    for h in history:
        print(f"  {h['changed_at']}: {h['old_status']} -> {h['new_status']} ({h['note']})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--status", default=None, choices=sorted(db.VALID_STATUSES))
    p_list.set_defaults(func=cmd_list)

    p_set = sub.add_parser("set")
    p_set.add_argument("job_id", type=int)
    p_set.add_argument("status", choices=sorted(db.VALID_STATUSES))
    p_set.add_argument("--note", default="")
    p_set.set_defaults(func=cmd_set)

    p_show = sub.add_parser("show")
    p_show.add_argument("job_id", type=int)
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args()
    db.init_db()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
