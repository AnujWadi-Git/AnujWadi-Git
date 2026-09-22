"""SQLite database layer for the job search agent.

Schema is intentionally simple and dependency-free (stdlib sqlite3 only).
All timestamps are ISO-8601 UTC strings. Nothing here calls any network API;
this module only ever reads/writes the local database file.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

VALID_STATUSES = {"new", "seen", "saved", "applied", "rejected", "expired"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    location TEXT,
    work_arrangement TEXT,
    employment_type TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT,
    salary_period TEXT,
    posted_date TEXT,
    experience_required TEXT,
    sponsorship TEXT DEFAULT 'not_specified',
    description TEXT,
    skills TEXT,              -- JSON list
    source TEXT,
    source_url TEXT,
    apply_url TEXT,
    match_category TEXT,       -- strong | potential | low
    match_reasons TEXT,        -- JSON list of factual reasons
    rejection_reason TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    first_seen_date TEXT NOT NULL,
    last_seen_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    applied_date TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'applied'
);

CREATE TABLE IF NOT EXISTS search_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    query TEXT,
    location TEXT,
    results_count INTEGER DEFAULT 0,
    new_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS job_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    note TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
"""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def today_iso() -> str:
    return dt.date.today().isoformat()


@contextmanager
def connect(db_path: Optional[Path] = None):
    path = db_path if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def normalize_company_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def get_or_create_company(conn: sqlite3.Connection, name: str) -> int:
    norm = normalize_company_name(name)
    row = conn.execute(
        "SELECT id FROM companies WHERE normalized_name = ?", (norm,)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO companies (name, normalized_name) VALUES (?, ?)",
        (name.strip(), norm),
    )
    return cur.lastrowid


def get_job_by_key(conn: sqlite3.Connection, job_key: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs WHERE job_key = ?", (job_key,)).fetchone()


def upsert_job(conn: sqlite3.Connection, job: dict[str, Any]) -> tuple[int, bool]:
    """Insert a new job or update last_seen_date on an existing one.

    Returns (job_id, is_new).
    """
    job_key = job["job_key"]
    existing = get_job_by_key(conn, job_key)
    ts = now_iso()
    today = today_iso()

    if existing:
        conn.execute(
            "UPDATE jobs SET last_seen_date = ?, updated_at = ? WHERE id = ?",
            (today, ts, existing["id"]),
        )
        return existing["id"], False

    company_id = get_or_create_company(conn, job["company"])
    cur = conn.execute(
        """
        INSERT INTO jobs (
            job_key, title, company_id, location, work_arrangement, employment_type,
            salary_min, salary_max, salary_currency, salary_period, posted_date,
            experience_required, sponsorship, description, skills, source,
            source_url, apply_url, match_category, match_reasons, rejection_reason,
            status, first_seen_date, last_seen_date, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job_key,
            job["title"],
            company_id,
            job.get("location"),
            job.get("work_arrangement"),
            job.get("employment_type"),
            job.get("salary_min"),
            job.get("salary_max"),
            job.get("salary_currency"),
            job.get("salary_period"),
            job.get("posted_date", "unknown"),
            job.get("experience_required"),
            job.get("sponsorship", "not_specified"),
            job.get("description"),
            json.dumps(job.get("skills", [])),
            job.get("source"),
            job.get("source_url"),
            job.get("apply_url"),
            job.get("match_category"),
            json.dumps(job.get("match_reasons", [])),
            job.get("rejection_reason"),
            job.get("status", "new"),
            today,
            today,
            ts,
            ts,
        ),
    )
    job_id = cur.lastrowid
    conn.execute(
        "INSERT INTO job_status_history (job_id, old_status, new_status, changed_at, note) "
        "VALUES (?, NULL, ?, ?, ?)",
        (job_id, job.get("status", "new"), ts, "initial insert"),
    )
    return job_id, True


def set_status(conn: sqlite3.Connection, job_id: int, new_status: str, note: str = "") -> None:
    if new_status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {new_status}")
    row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise ValueError(f"no such job id: {job_id}")
    old_status = row["status"]
    ts = now_iso()
    conn.execute(
        "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, ts, job_id),
    )
    conn.execute(
        "INSERT INTO job_status_history (job_id, old_status, new_status, changed_at, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (job_id, old_status, new_status, ts, note),
    )
    if new_status == "applied":
        conn.execute(
            "INSERT INTO applications (job_id, applied_date, notes, status) VALUES (?, ?, ?, ?)",
            (job_id, today_iso(), note, "applied"),
        )


def record_search_run(
    conn: sqlite3.Connection,
    query: str,
    location: str,
    results_count: int,
    new_count: int,
    duplicate_count: int,
    rejected_count: int,
) -> None:
    conn.execute(
        """
        INSERT INTO search_runs (run_date, query, location, results_count, new_count,
                                  duplicate_count, rejected_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (today_iso(), query, location, results_count, new_count, duplicate_count, rejected_count),
    )


def all_job_keys(conn: sqlite3.Connection) -> set[str]:
    return {r["job_key"] for r in conn.execute("SELECT job_key FROM jobs")}


def jobs_by_status(conn: sqlite3.Connection, status: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT jobs.*, companies.name AS company_name FROM jobs "
        "JOIN companies ON jobs.company_id = companies.id "
        "WHERE jobs.status = ? ORDER BY jobs.first_seen_date DESC",
        (status,),
    ).fetchall()


def jobs_seen_today(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    today = today_iso()
    return conn.execute(
        "SELECT jobs.*, companies.name AS company_name FROM jobs "
        "JOIN companies ON jobs.company_id = companies.id "
        "WHERE jobs.first_seen_date = ? ORDER BY jobs.match_category",
        (today,),
    ).fetchall()


def stats_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"]
    by_status = {
        r["status"]: r["c"]
        for r in conn.execute("SELECT status, COUNT(*) AS c FROM jobs GROUP BY status")
    }
    by_category = {
        r["match_category"]: r["c"]
        for r in conn.execute(
            "SELECT match_category, COUNT(*) AS c FROM jobs GROUP BY match_category"
        )
    }
    total_applications = conn.execute("SELECT COUNT(*) AS c FROM applications").fetchone()["c"]
    total_companies = conn.execute("SELECT COUNT(*) AS c FROM companies").fetchone()["c"]
    total_runs = conn.execute("SELECT COUNT(*) AS c FROM search_runs").fetchone()["c"]
    return {
        "total_jobs": total,
        "by_status": by_status,
        "by_match_category": by_category,
        "total_applications": total_applications,
        "total_companies": total_companies,
        "total_search_runs": total_runs,
    }
