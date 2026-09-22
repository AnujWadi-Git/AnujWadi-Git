"""Rule-based filtering, extraction, and match classification.

Every function here is a pure function over plain dicts/strings so it can be
unit tested without a database or network access. Nothing in this module
invents data: if a field can't be verified from the posting text, it is left
as None / "unknown" / "not_specified".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _norm(text: Optional[str]) -> str:
    return (text or "").lower()


def _contains_any(text: str, phrases: list[str]) -> Optional[str]:
    """Return the first matching phrase found in text, else None."""
    for phrase in phrases:
        if phrase.lower() in text:
            return phrase
    return None


# ---------------------------------------------------------------------------
# Hard exclusion rules
# ---------------------------------------------------------------------------

# Categories that are excluded outright regardless of AI/ML wording.
_ALWAYS_EXCLUDE_CATEGORIES = {
    "it support",
    "help desk",
    "technical support",
    "firmware",
    "hardware engineer",
    "electrical engineer",
    "electronics engineer",
    "qa engineer",
    "quality assurance",
    "test engineer",
    "data analyst",
    "bi analyst",
    "business intelligence analyst",
    "cybersecurity",
    "security engineer",
    "sales engineer",
    "consultant",
    "internship",
    "intern",
    "embedded",
}

# Categories that are only excluded when the posting has no AI/ML/LLM signal
# (a "Data Engineer" role that is actually about ML pipelines is fine, a pure
# ETL/warehouse role is not).
_CONDITIONAL_EXCLUDE_CATEGORIES = {
    "data engineer",
    "devops",
    "site reliability",
    "sre",
}

_AI_ML_SIGNAL_WORDS = [
    "machine learning",
    "ml ",
    "artificial intelligence",
    " ai ",
    "ai/ml",
    "llm",
    "large language model",
    "genai",
    "generative ai",
    "agentic",
    "deep learning",
    "neural network",
    "nlp",
    "computer vision",
    "pytorch",
    "tensorflow",
    "transformer",
]


def has_ai_ml_signal(text: str) -> bool:
    padded = f" {text} "
    return any(sig in padded for sig in _AI_ML_SIGNAL_WORDS)


def matches_excluded_category(title: str, description: str) -> Optional[str]:
    text = f"{_norm(title)} {_norm(description)}"
    hit = _contains_any(text, sorted(_ALWAYS_EXCLUDE_CATEGORIES))
    if hit:
        return hit
    hit = _contains_any(text, sorted(_CONDITIONAL_EXCLUDE_CATEGORIES))
    if hit and not has_ai_ml_signal(text):
        return hit
    return None


_SENIORITY_WORDS = ["senior", "sr.", "sr ", "staff", "principal", "lead", "manager", "director", "architect"]


def matches_excluded_seniority(title: str) -> Optional[str]:
    return _contains_any(_norm(title), _SENIORITY_WORDS)


_CLEARANCE_PHRASES = [
    "security clearance",
    "active clearance",
    "secret clearance",
    "top secret",
    "itar",
    "must be a us citizen",
    "u.s. citizenship required",
    "us citizenship required",
    "citizenship required",
]


def matches_clearance_exclusion(description: str) -> Optional[str]:
    return _contains_any(_norm(description), _CLEARANCE_PHRASES)


_NEW_GRAD_OVERRIDE_PHRASES = [
    "new grad",
    "new graduate",
    "recent graduate",
    "entry level",
    "entry-level",
    "0-1 year",
    "0-2 years",
    "equivalent experience",
    "no prior experience",
]


def has_new_grad_language(text: str) -> bool:
    return _contains_any(_norm(text), _NEW_GRAD_OVERRIDE_PHRASES) is not None


# Matches "3+ years", "3-5 years", "3 to 5 years", "5 years of experience"
_EXPERIENCE_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|(?:-|to|–)\s*(\d{1,2}))?\s*years?\s*(?:of\s*)?"
    r"(?:relevant\s*|professional\s*|industry\s*)?experience",
    re.IGNORECASE,
)


def extract_min_experience_years(description: str) -> Optional[int]:
    """Return the smallest 'years of experience' figure explicitly stated, if any."""
    matches = _EXPERIENCE_YEARS_RE.findall(description or "")
    years = []
    for g1, g2 in matches:
        if g1:
            years.append(int(g1))
        if g2:
            years.append(int(g2))
    if not years:
        return None
    return min(years)


def matches_excluded_experience(description: str, max_years: int) -> Optional[str]:
    """Reject when description clearly requires more than max_years, unless the
    posting also contains new-grad override language."""
    min_years = extract_min_experience_years(description)
    if min_years is None:
        return None
    if min_years > max_years and not has_new_grad_language(description):
        return f"requires {min_years}+ years experience"
    return None


# ---------------------------------------------------------------------------
# Extraction: salary, location, sponsorship, experience label
# ---------------------------------------------------------------------------

_SALARY_RANGE_RE = re.compile(
    r"\$\s?([\d,]{2,7})(?:k)?\s*(?:-|to|–)\s*\$?\s?([\d,]{2,7})(?:k)?\s*"
    r"(?:(per\s*hour|/hr|hourly|per\s*year|/yr|annually))?",
    re.IGNORECASE,
)
_SALARY_SINGLE_RE = re.compile(r"\$\s?([\d,]{2,7})(?:k)?\s*(per\s*hour|/hr|hourly|per\s*year|/yr|annually)?", re.IGNORECASE)


def _parse_amount(raw: str, had_k: bool) -> int:
    val = int(raw.replace(",", ""))
    if had_k or val < 1000:
        val *= 1000
    return val


@dataclass
class SalaryInfo:
    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = None
    period: Optional[str] = None


def extract_salary(text: str) -> SalaryInfo:
    if not text:
        return SalaryInfo()
    m = _SALARY_RANGE_RE.search(text)
    if m:
        lo_raw, hi_raw, period_raw = m.group(1), m.group(2), m.group(3)
        had_k = "k" in m.group(0).lower()
        lo = _parse_amount(lo_raw, had_k)
        hi = _parse_amount(hi_raw, had_k)
        period = _normalize_period(period_raw)
        return SalaryInfo(min=min(lo, hi), max=max(lo, hi), currency="USD", period=period)
    m = _SALARY_SINGLE_RE.search(text)
    if m:
        had_k = "k" in m.group(0).lower()
        val = _parse_amount(m.group(1), had_k)
        period = _normalize_period(m.group(2))
        return SalaryInfo(min=val, max=val, currency="USD", period=period)
    return SalaryInfo()


def _normalize_period(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.lower()
    if "hour" in raw or "hr" in raw:
        return "hourly"
    if "year" in raw or "yr" in raw or "annual" in raw:
        return "yearly"
    return None


_SPONSORSHIP_NOT_AVAILABLE = [
    "does not provide sponsorship",
    "does not offer sponsorship",
    "no visa sponsorship",
    "not provide visa sponsorship",
    "sponsorship not available",
    "sponsorship is not available",
    "will not sponsor",
    "unable to sponsor",
    "not able to sponsor",
    "cannot sponsor",
]
_SPONSORSHIP_REQUIRED = [
    "sponsorship required",
]
_SPONSORSHIP_AVAILABLE = [
    "sponsorship available",
    "we sponsor",
    "visa sponsorship provided",
    "open to sponsorship",
    "sponsorship is available",
]


def extract_sponsorship(text: str) -> str:
    t = _norm(text)
    if _contains_any(t, _SPONSORSHIP_NOT_AVAILABLE):
        return "explicitly_not_available"
    if _contains_any(t, _SPONSORSHIP_REQUIRED):
        return "required"
    if _contains_any(t, _SPONSORSHIP_AVAILABLE):
        return "potentially_available"
    return "not_specified"


def extract_work_arrangement(location: str, description: str) -> Optional[str]:
    t = f"{_norm(location)} {_norm(description)}"
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    if "on-site" in t or "onsite" in t or "in office" in t or "in-office" in t:
        return "onsite"
    return None


def extract_experience_label(description: str) -> str:
    if has_new_grad_language(description):
        return "new grad / entry level"
    min_years = extract_min_experience_years(description)
    if min_years is not None:
        return f"{min_years}+ years"
    return "unknown"


# ---------------------------------------------------------------------------
# Location fit
# ---------------------------------------------------------------------------


def location_fit(location: str, work_arrangement: Optional[str], locations_cfg: dict) -> tuple[bool, str]:
    """Return (fits, reason)."""
    loc = _norm(location)
    primary = [p.lower() for p in locations_cfg.get("primary", [])]
    if any(p.split(",")[0].strip() in loc for p in primary):
        return True, "primary target location"
    if work_arrangement == "remote":
        return True, "remote (US)"
    if work_arrangement == "hybrid" and locations_cfg.get("hybrid_allowed", True):
        return True, "hybrid, US-based"
    if locations_cfg.get("relocation_friendly", True) and "united states" in loc or _is_us_location(loc):
        return True, "other US location, relocation-friendly"
    return False, "location outside configured preferences"


_US_STATE_ABBRS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia",
    "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt",
    "va", "wa", "wv", "wi", "wy",
}


def _is_us_location(loc: str) -> bool:
    parts = [p.strip() for p in loc.split(",")]
    if len(parts) >= 2 and parts[-1][:2] in _US_STATE_ABBRS:
        return True
    return False


# ---------------------------------------------------------------------------
# Recency
# ---------------------------------------------------------------------------


def recency_bucket(days_ago: Optional[int]) -> str:
    if days_ago is None:
        return "unknown"
    if days_ago <= 0:
        return "today"
    if days_ago == 1:
        return "yesterday"
    if days_ago <= 3:
        return "last 3 days"
    if days_ago <= 7:
        return "last 7 days"
    if days_ago <= 14:
        return "last 14 days"
    if days_ago <= 30:
        return "last 30 days"
    return "stale"


# ---------------------------------------------------------------------------
# Skill overlap
# ---------------------------------------------------------------------------


def skill_overlap(description: str, my_skills: list[str]) -> list[str]:
    t = _norm(description)
    found = []
    for skill in my_skills:
        s = skill.lower()
        if s in t:
            found.append(skill)
    return found


# ---------------------------------------------------------------------------
# Top-level evaluation
# ---------------------------------------------------------------------------


@dataclass
class Evaluation:
    rejected: bool
    rejection_reason: Optional[str] = None
    match_category: Optional[str] = None  # strong | potential | low
    match_reasons: list[str] = field(default_factory=list)
    salary: SalaryInfo = field(default_factory=SalaryInfo)
    sponsorship: str = "not_specified"
    work_arrangement: Optional[str] = None
    experience_required: str = "unknown"
    skills_found: list[str] = field(default_factory=list)


def evaluate_job(job: dict[str, Any], config: dict[str, Any]) -> Evaluation:
    title = job.get("title", "")
    description = job.get("description", "") or ""
    location = job.get("location", "") or ""
    full_text = f"{title} {description}"

    filters_cfg = config.get("filters", {})
    locations_cfg = config.get("locations", {})
    max_years = filters_cfg.get("max_experience_years", 2)

    # --- hard exclusions ---
    reason = matches_excluded_seniority(title)
    if reason:
        return Evaluation(rejected=True, rejection_reason=f"seniority keyword in title: '{reason}'")

    reason = matches_excluded_category(title, description)
    if reason:
        return Evaluation(rejected=True, rejection_reason=f"excluded category: '{reason}'")

    if filters_cfg.get("exclude_clearance", True):
        reason = matches_clearance_exclusion(description)
        if reason:
            return Evaluation(rejected=True, rejection_reason=f"clearance/citizenship requirement: '{reason}'")

    reason = matches_excluded_experience(description, max_years)
    if reason:
        return Evaluation(rejected=True, rejection_reason=reason)

    # --- extraction (never invents missing data) ---
    salary = extract_salary(description) if description else SalaryInfo()
    if salary.min is None and job.get("salary_text"):
        salary = extract_salary(job["salary_text"])
    sponsorship = extract_sponsorship(description)
    work_arrangement = extract_work_arrangement(location, description) or job.get("work_arrangement")
    experience_required = extract_experience_label(description)
    skills_found = skill_overlap(full_text, config.get("candidate", {}).get("skills", []))
    fits_location, location_reason = location_fit(location, work_arrangement, locations_cfg)

    # --- classification (explicit rules, never a numeric score) ---
    reasons = []
    strong_signals = 0
    potential_signals = 0

    if len(skills_found) >= 4:
        strong_signals += 1
        reasons.append(f"strong skill overlap ({len(skills_found)} matching skills: {', '.join(skills_found[:6])})")
    elif len(skills_found) >= 1:
        potential_signals += 1
        reasons.append(f"some skill overlap ({', '.join(skills_found)})")

    if has_ai_ml_signal(_norm(full_text)):
        strong_signals += 1
        reasons.append("role is AI/ML/LLM focused")

    if fits_location:
        strong_signals += 1
        reasons.append(location_reason)
    else:
        potential_signals += 1

    if has_new_grad_language(description) or experience_required == "unknown":
        strong_signals += 1
        reasons.append(
            "explicitly welcomes new grads" if has_new_grad_language(description) else "no experience floor stated"
        )
    else:
        potential_signals += 1
        reasons.append(f"requires {experience_required}")

    if salary.min and salary.min >= config.get("salary", {}).get("target_min_usd", 100000):
        reasons.append(f"salary meets target (${salary.min:,}+)")

    if strong_signals >= 3:
        category = "strong"
    elif strong_signals >= 1 or potential_signals >= 2:
        category = "potential"
    else:
        category = "low"

    return Evaluation(
        rejected=False,
        match_category=category,
        match_reasons=reasons,
        salary=salary,
        sponsorship=sponsorship,
        work_arrangement=work_arrangement,
        experience_required=experience_required,
        skills_found=skills_found,
    )
