import conftest  # noqa: F401

import pytest

import db


@pytest.fixture()
def tmp_db(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


def sample_job(**overrides):
    job = {
        "job_key": "indeed:abc123",
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Phoenix, AZ",
        "status": "new",
        "match_category": "strong",
        "match_reasons": ["skills overlap"],
        "skills": ["Python"],
    }
    job.update(overrides)
    return job


def test_init_db_creates_tables(tmp_db):
    with db.connect(tmp_db) as conn:
        tables = {
            r["name"]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"jobs", "companies", "applications", "search_runs", "job_status_history"} <= tables


def test_upsert_job_inserts_new(tmp_db):
    with db.connect(tmp_db) as conn:
        job_id, is_new = db.upsert_job(conn, sample_job())
        assert is_new is True
        row = db.get_job_by_key(conn, "indeed:abc123")
        assert row["title"] == "Software Engineer"
        assert row["status"] == "new"


def test_upsert_job_updates_last_seen_on_duplicate(tmp_db):
    with db.connect(tmp_db) as conn:
        db.upsert_job(conn, sample_job())
        job_id, is_new = db.upsert_job(conn, sample_job())
        assert is_new is False
        count = conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"]
        assert count == 1


def test_set_status_valid_transition(tmp_db):
    with db.connect(tmp_db) as conn:
        job_id, _ = db.upsert_job(conn, sample_job())
        db.set_status(conn, job_id, "saved", note="looks good")
        row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert row["status"] == "saved"
        history = conn.execute(
            "SELECT * FROM job_status_history WHERE job_id = ? ORDER BY id", (job_id,)
        ).fetchall()
        assert len(history) == 2  # initial insert + this transition


def test_set_status_invalid_raises(tmp_db):
    with db.connect(tmp_db) as conn:
        job_id, _ = db.upsert_job(conn, sample_job())
        with pytest.raises(ValueError):
            db.set_status(conn, job_id, "not_a_real_status")


def test_set_status_applied_creates_application_record(tmp_db):
    with db.connect(tmp_db) as conn:
        job_id, _ = db.upsert_job(conn, sample_job())
        db.set_status(conn, job_id, "applied", note="submitted via Indeed")
        apps = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,)).fetchall()
        assert len(apps) == 1


def test_stats_summary(tmp_db):
    with db.connect(tmp_db) as conn:
        db.upsert_job(conn, sample_job(job_key="a", match_category="strong"))
        db.upsert_job(conn, sample_job(job_key="b", match_category="potential", company="Other Co"))
        summary = db.stats_summary(conn)
        assert summary["total_jobs"] == 2
        assert summary["total_companies"] == 2
