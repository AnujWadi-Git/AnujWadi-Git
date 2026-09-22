import conftest  # noqa: F401

import pytest

import db
import report


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "jobs.db"
    monkeypatch.setattr(db, "DEFAULT_DB_PATH", db_path)
    db.init_db(db_path)
    yield db_path


def insert_job(conn, **overrides):
    job = {
        "job_key": overrides.get("job_key", "indeed:1"),
        "title": "AI Engineer",
        "company": "Acme Corp",
        "location": "Remote - United States",
        "match_category": "strong",
        "match_reasons": ["strong skill overlap", "role is AI/ML focused"],
        "sponsorship": "not_specified",
        "status": "new",
        "posted_date": "unknown",
    }
    job.update(overrides)
    return db.upsert_job(conn, job)


def test_report_with_no_jobs_today():
    text = report.generate_report()
    assert "New jobs found: 0" in text
    assert "No new jobs found in this run." in text


def test_report_includes_strong_match_in_apply_first():
    with db.connect() as conn:
        insert_job(conn)
    text = report.generate_report()
    assert "APPLY FIRST" in text
    assert "AI Engineer" in text
    assert "Acme Corp" in text


def test_report_handles_missing_salary():
    with db.connect() as conn:
        insert_job(conn, salary_min=None, salary_max=None)
    text = report.generate_report()
    assert "salary not listed" in text


def test_report_never_shows_numeric_score():
    with db.connect() as conn:
        insert_job(conn)
    text = report.generate_report()
    assert "/100" not in text


def test_report_no_strong_matches_message():
    with db.connect() as conn:
        insert_job(conn, match_category="potential", match_reasons=["some skill overlap"])
    text = report.generate_report()
    assert "No strong matches today" in text
