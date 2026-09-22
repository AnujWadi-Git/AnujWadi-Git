import conftest  # noqa: F401  (adds scripts/ to sys.path)

from config_loader import load_config
from filters import (
    evaluate_job,
    extract_min_experience_years,
    extract_salary,
    extract_sponsorship,
    extract_work_arrangement,
    has_new_grad_language,
    matches_excluded_category,
    matches_excluded_experience,
    matches_excluded_seniority,
    matches_clearance_exclusion,
)

CONFIG = load_config()


def make_job(**overrides):
    job = {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Phoenix, AZ",
        "description": "Great opportunity for a new grad. Python, AWS, and backend experience helpful.",
        "posted_date": "unknown",
    }
    job.update(overrides)
    return job


def test_config_loads():
    assert CONFIG["candidate"]["experience_level"] == "new_graduate"
    assert "Phoenix, AZ" in CONFIG["locations"]["primary"]


def test_seniority_exclusion():
    assert matches_excluded_seniority("Senior Software Engineer") == "senior"
    assert matches_excluded_seniority("Staff AI Engineer") == "staff"
    assert matches_excluded_seniority("Software Engineer") is None


def test_category_exclusion_hard():
    assert matches_excluded_category("Help Desk Technician", "") == "help desk"
    assert matches_excluded_category("QA Engineer", "manual testing") == "qa engineer"


def test_category_exclusion_conditional_data_engineer():
    # Pure data engineer -> excluded
    assert matches_excluded_category("Data Engineer", "ETL pipelines and warehousing") == "data engineer"
    # ML-flavored data engineer -> not excluded
    assert matches_excluded_category("Data Engineer", "Building machine learning feature pipelines") is None


def test_experience_extraction():
    assert extract_min_experience_years("Requires 3+ years of experience") == 3
    assert extract_min_experience_years("5-7 years of experience needed") == 5
    assert extract_min_experience_years("No experience requirement mentioned") is None


def test_new_grad_override():
    assert has_new_grad_language("This role is great for a new grad")
    assert not has_new_grad_language("Senior only")


def test_excluded_experience_respects_new_grad_override():
    desc = "Requires 4+ years experience, but new grads with equivalent experience are encouraged to apply."
    assert matches_excluded_experience(desc, max_years=2) is None
    desc2 = "Requires 5+ years of professional experience."
    assert matches_excluded_experience(desc2, max_years=2) is not None


def test_clearance_exclusion():
    assert matches_clearance_exclusion("Must hold an active security clearance") is not None
    assert matches_clearance_exclusion("Must be authorized to work in the US") is None


def test_salary_range_extraction():
    s = extract_salary("Compensation: $100,000 - $130,000 per year")
    assert s.min == 100000
    assert s.max == 130000
    assert s.period == "yearly"


def test_salary_k_shorthand():
    s = extract_salary("Pay range $100k-$120k")
    assert s.min == 100000
    assert s.max == 120000


def test_salary_missing():
    s = extract_salary("No compensation info here")
    assert s.min is None and s.max is None


def test_sponsorship_not_specified_by_default():
    assert extract_sponsorship("We are a great place to work") == "not_specified"


def test_sponsorship_not_available():
    assert extract_sponsorship("We are unable to sponsor visas at this time") == "explicitly_not_available"


def test_sponsorship_available():
    assert extract_sponsorship("Visa sponsorship provided for qualified candidates") == "potentially_available"


def test_work_arrangement_detection():
    assert extract_work_arrangement("Remote - United States", "") == "remote"
    assert extract_work_arrangement("Phoenix, AZ", "This is a hybrid role") == "hybrid"
    assert extract_work_arrangement("Phoenix, AZ", "") is None


def test_evaluate_job_rejects_senior():
    job = make_job(title="Senior Software Engineer")
    result = evaluate_job(job, CONFIG)
    assert result.rejected
    assert "seniority" in result.rejection_reason


def test_evaluate_job_rejects_clearance():
    job = make_job(description="Requires an active security clearance.")
    result = evaluate_job(job, CONFIG)
    assert result.rejected


def test_evaluate_job_strong_match():
    job = make_job(
        title="AI Engineer",
        description=(
            "New grad friendly AI Engineer role. Python, PyTorch, AWS, LangChain, "
            "and machine learning experience desired. Remote - United States."
        ),
        location="Remote",
    )
    result = evaluate_job(job, CONFIG)
    assert not result.rejected
    assert result.match_category == "strong"
    assert len(result.match_reasons) > 0


def test_evaluate_job_never_invents_salary():
    job = make_job(description="Great new grad backend role, Python and AWS.")
    result = evaluate_job(job, CONFIG)
    assert result.salary.min is None
    assert result.salary.max is None


def test_evaluate_job_never_invents_sponsorship():
    job = make_job(description="Great new grad backend role, Python and AWS.")
    result = evaluate_job(job, CONFIG)
    assert result.sponsorship == "not_specified"
