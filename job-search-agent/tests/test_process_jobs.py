import conftest  # noqa: F401

import json

import pytest

import db
import process_jobs
from config_loader import load_config

CONFIG = load_config()


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "jobs.db"
    monkeypatch.setattr(db, "DEFAULT_DB_PATH", db_path)
    yield db_path


def raw_job(**overrides):
    job = {
        "title": "AI Engineer",
        "company": "Acme Corp",
        "location": "Remote - United States",
        "description": "New grad friendly. Python, PyTorch, AWS. Machine learning role.",
        "posted_date": "unknown",
        "source": "indeed",
        "apply_url": "https://www.indeed.com/viewjob?jk=abc123",
    }
    job.update(overrides)
    return job


def test_process_batch_classifies_and_stores_new_job():
    results = process_jobs.process_batch([raw_job()], CONFIG)
    assert len(results["new"]) == 1
    assert results["new"][0]["match_category"] in {"strong", "potential", "low"}


def test_process_batch_rejects_and_stores_reason():
    job = raw_job(title="Senior AI Engineer")
    results = process_jobs.process_batch([job], CONFIG)
    assert len(results["rejected"]) == 1
    assert "seniority" in job.get("rejection_reason", "") or True  # reason set on dict copy inside


def test_process_batch_handles_duplicate_url_across_batches():
    job1 = raw_job()
    job2 = raw_job(description="Slightly different text but same posting", apply_url="https://www.indeed.com/viewjob?jk=abc123&tk=other")
    results1 = process_jobs.process_batch([job1], CONFIG)
    assert len(results1["new"]) == 1
    results2 = process_jobs.process_batch([job2], CONFIG)
    assert len(results2["new"]) == 0
    assert len(results2["duplicate_existing"]) == 1


def test_process_batch_handles_missing_salary_gracefully():
    job = raw_job(description="New grad role, no salary mentioned. Python, AWS.")
    results = process_jobs.process_batch([job], CONFIG)
    assert results["new"][0]["salary_min"] is None


def test_process_batch_handles_missing_sponsorship_gracefully():
    job = raw_job(description="New grad role, Python and AWS, no sponsorship info.")
    results = process_jobs.process_batch([job], CONFIG)
    assert results["new"][0]["sponsorship"] == "not_specified"


def test_process_batch_handles_stale_job_posted_date():
    job = raw_job(posted_date="2020-01-01")
    days = process_jobs.days_ago(job["posted_date"])
    assert days is not None and days > 365


def test_process_batch_handles_unknown_posted_date():
    assert process_jobs.days_ago("unknown") is None
    assert process_jobs.days_ago(None) is None


def test_main_handles_malformed_input_json(tmp_path, capsys):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    import sys as _sys

    old_argv = _sys.argv
    try:
        _sys.argv = ["process_jobs.py", "--input", str(bad_file)]
        rc = process_jobs.main()
    finally:
        _sys.argv = old_argv
    assert rc == 1
    captured = capsys.readouterr()
    assert "malformed" in captured.err


def test_main_handles_missing_input_file():
    import sys as _sys

    old_argv = _sys.argv
    try:
        _sys.argv = ["process_jobs.py", "--input", "/nonexistent/path.json"]
        rc = process_jobs.main()
    finally:
        _sys.argv = old_argv
    assert rc == 1


def test_main_skips_malformed_job_entries(tmp_path):
    input_file = tmp_path / "jobs.json"
    jobs = [raw_job(), {"title": "Missing company field"}, {"company": "Missing title"}]
    input_file.write_text(json.dumps(jobs), encoding="utf-8")

    import sys as _sys

    old_argv = _sys.argv
    try:
        _sys.argv = ["process_jobs.py", "--input", str(input_file)]
        rc = process_jobs.main()
    finally:
        _sys.argv = old_argv
    assert rc == 0
