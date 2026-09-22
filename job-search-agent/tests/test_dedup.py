import conftest  # noqa: F401

from dedup import compute_job_key, dedupe_batch, extract_indeed_job_id, normalize_url


def test_normalize_url_strips_tracking_params():
    url = "https://www.indeed.com/viewjob?jk=abc123&tk=xyz&from=serp&utm_source=foo"
    normalized = normalize_url(url)
    assert "tk=" not in normalized
    assert "utm_source" not in normalized
    assert "jk=abc123" in normalized


def test_normalize_url_none():
    assert normalize_url(None) is None


def test_extract_indeed_job_id():
    assert extract_indeed_job_id("https://www.indeed.com/viewjob?jk=abc123&tk=xyz") == "abc123"
    assert extract_indeed_job_id("https://www.indeed.com/viewjob?vjk=def456") == "def456"
    assert extract_indeed_job_id("https://example.com/no-id-here") is None


def test_compute_job_key_prefers_job_id():
    job = {"job_id": "abc123", "company": "Acme", "title": "Engineer", "source": "indeed"}
    assert compute_job_key(job) == "indeed:abc123"


def test_compute_job_key_uses_normalized_url_when_no_job_id():
    job = {
        "company": "Acme",
        "title": "Engineer",
        "location": "Phoenix, AZ",
        "source": "indeed",
        "apply_url": "https://www.indeed.com/viewjob?jk=xyz789&tk=noise",
    }
    key1 = compute_job_key(job)
    job2 = dict(job)
    job2["apply_url"] = "https://www.indeed.com/viewjob?jk=xyz789&tk=different-noise&utm_source=bar"
    key2 = compute_job_key(job2)
    assert key1 == key2


def test_compute_job_key_fallback_hash_stable():
    job = {"company": "Acme Corp", "title": "Software Engineer", "location": "Phoenix, AZ", "source": "indeed"}
    assert compute_job_key(job) == compute_job_key(dict(job))


def test_dedupe_batch_removes_exact_duplicates():
    jobs = [
        {"company": "Acme", "title": "Engineer", "location": "Phoenix, AZ", "source": "indeed", "job_id": "1"},
        {"company": "Acme", "title": "Engineer", "location": "Phoenix, AZ", "source": "indeed", "job_id": "1"},
        {"company": "Acme", "title": "Engineer", "location": "Phoenix, AZ", "source": "indeed", "job_id": "2"},
    ]
    unique, dup_count = dedupe_batch(jobs)
    assert len(unique) == 2
    assert dup_count == 1


def test_dedupe_batch_different_tracking_params_still_dedupes():
    jobs = [
        {
            "company": "Acme",
            "title": "Engineer",
            "location": "Phoenix, AZ",
            "source": "indeed",
            "apply_url": "https://www.indeed.com/viewjob?jk=xyz&tk=one",
        },
        {
            "company": "Acme",
            "title": "Engineer",
            "location": "Phoenix, AZ",
            "source": "indeed",
            "apply_url": "https://www.indeed.com/viewjob?jk=xyz&tk=two",
        },
    ]
    unique, dup_count = dedupe_batch(jobs)
    assert len(unique) == 1
    assert dup_count == 1
