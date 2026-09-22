"""Deduplication: URL normalization and stable job identity.

A job is considered the same posting if it shares a normalized URL, or if it
shares the same (normalized company, normalized title, normalized location)
tuple. Indeed job IDs (the `vjk`/`jk` query parameter) are also used when
present, since they're the most reliable stable identifier Indeed exposes.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Query params that carry tracking/session noise and don't affect identity.
_TRACKING_PARAMS = {
    "tk", "from", "utm_source", "utm_medium", "utm_campaign", "utm_term",
    "utm_content", "advn", "adid", "sjdu", "cmp", "gclid", "fbclid", "ref",
    "rgtk", "pp", "vjs", "spa", "gt", "s",
}
# Params that DO identify the job and should be preserved.
_IDENTITY_PARAMS = {"jk", "vjk"}


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Strip tracking params, keep identity params, drop fragment, lowercase host."""
    if not url:
        return None
    parsed = urlparse(url.strip())
    query = parse_qs(parsed.query)
    kept = {k: v for k, v in query.items() if k.lower() in _IDENTITY_PARAMS}
    normalized_query = urlencode(sorted(kept.items()), doseq=True)
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme.lower(), netloc, path, "", normalized_query, ""))


def extract_indeed_job_id(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"[?&](?:jk|vjk)=([a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def _norm_text(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def compute_job_key(job: dict) -> str:
    """Build a stable identity key for a job posting.

    Priority:
    1. An explicit source job_id (e.g. Indeed's jk/vjk), scoped to the source.
    2. The normalized apply/source URL.
    3. A hash of (company, title, location) as a last resort.
    """
    source = _norm_text(job.get("source", "indeed"))
    job_id = job.get("job_id") or extract_indeed_job_id(job.get("apply_url") or job.get("source_url"))
    if job_id:
        return f"{source}:{job_id}"

    norm_url = normalize_url(job.get("apply_url") or job.get("source_url"))
    if norm_url:
        return f"{source}:url:{norm_url}"

    fallback = f"{_norm_text(job.get('company'))}|{_norm_text(job.get('title'))}|{_norm_text(job.get('location'))}"
    digest = hashlib.sha256(fallback.encode("utf-8")).hexdigest()[:16]
    return f"{source}:fallback:{digest}"


def dedupe_batch(jobs: list[dict]) -> tuple[list[dict], int]:
    """Remove duplicates *within* a single batch (e.g. same job appearing in
    two different search queries in one run). Returns (unique_jobs, dup_count).
    The first occurrence of each job_key wins.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    dup_count = 0
    for job in jobs:
        key = job.get("job_key") or compute_job_key(job)
        job["job_key"] = key
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        unique.append(job)
    return unique, dup_count
