from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class JobPosting:
    title: str
    company: str
    url: str
    location: str
    description: str
    source: str
    posted_at: str | None = None
    salary_text: str | None = None
    apply_url: str | None = None


def _get_json(url: str, timeout: int = 30) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "SusmithaJobAgent/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_remotive(search: str = "data engineer", limit: int = 20) -> list[JobPosting]:
    """Free Remotive public API — remote jobs. No paid account."""
    q = urllib.parse.quote(search)
    url = f"https://remotive.com/api/remote-jobs?search={q}&limit={limit}"
    data = _get_json(url)
    jobs = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for item in data.get("jobs", []):
        pub = item.get("publication_date")
        posted = None
        if pub:
            try:
                posted_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if posted_dt.tzinfo is None:
                    posted_dt = posted_dt.replace(tzinfo=timezone.utc)
                posted = posted_dt.date().isoformat()
                if posted_dt < cutoff:
                    continue
            except ValueError:
                posted = pub
        title = item.get("title") or ""
        title_l = title.lower()
        if "data engineer" not in title_l and "analytics engineer" not in title_l:
            continue
        loc = item.get("candidate_required_location") or item.get("job_type") or "Remote"
        loc_l = str(loc).lower()
        # Prefer US / worldwide / Americas; skip clearly EU-only boards when possible
        if any(x in loc_l for x in ("germany", "france", "india only", "europe only", "uk only")):
            continue
        jobs.append(
            JobPosting(
                title=title,
                company=item.get("company_name") or "Unknown",
                url=item.get("url") or "",
                location=str(loc),
                description=item.get("description") or "",
                source="remotive",
                posted_at=posted,
                salary_text=item.get("salary") or None,
                apply_url=item.get("url"),
            )
        )
    return jobs


def search_arbeitnow(search: str = "data engineer", limit: int = 20) -> list[JobPosting]:
    """Arbeitnow public API — often includes US remote roles."""
    q = urllib.parse.quote(search)
    url = f"https://www.arbeitnow.com/api/job-board-api?search={q}"
    try:
        data = _get_json(url)
    except Exception:
        return []
    jobs = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for item in data.get("data", [])[: limit * 3]:
        created = item.get("created_at")
        posted = None
        if created:
            try:
                # unix timestamp
                posted_dt = datetime.fromtimestamp(int(created), tz=timezone.utc)
                posted = posted_dt.date().isoformat()
                if posted_dt < cutoff:
                    continue
            except (TypeError, ValueError, OSError):
                posted = str(created)
        title = item.get("title") or ""
        title_l = title.lower()
        if "data engineer" not in title_l and "analytics engineer" not in title_l:
            continue
        loc = ", ".join(item.get("location") or []) if isinstance(item.get("location"), list) else (
            item.get("location") or ("Remote" if item.get("remote") else "")
        )
        loc_l = str(loc).lower()
        blob = f"{title_l} {loc_l} {(item.get('description') or '')[:500].lower()}"
        if any(x in blob for x in ("germany", "berlin", "frankfurt", "m/f/d", "mwd", "deutsch", "austria", "switzerland")):
            continue
        if not item.get("remote") and "united states" not in loc_l and "usa" not in loc_l and "remote" not in loc_l:
            continue
        jobs.append(
            JobPosting(
                title=title,
                company=item.get("company_name") or "Unknown",
                url=item.get("url") or "",
                location=str(loc),
                description=item.get("description") or "",
                source="arbeitnow",
                posted_at=posted,
                apply_url=item.get("url"),
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


def filter_jobs(
    jobs: list[JobPosting],
    *,
    min_pay: int | None = 120000,
    skip_keywords: list[str] | None = None,
    require_remoteish: bool = True,
) -> list[JobPosting]:
    skip_keywords = [s.lower() for s in (skip_keywords or [])]
    out = []
    for j in jobs:
        blob = f"{j.title} {j.company} {j.location} {j.description} {j.salary_text or ''}".lower()
        if any(s in blob for s in skip_keywords):
            continue
        if require_remoteish:
            if not any(k in blob for k in ("remote", "anywhere", "united states", "usa", "us only", "north america")):
                # Remotive is remote-first; keep Remotive even if location string odd
                if j.source != "remotive":
                    continue
        if min_pay and j.salary_text:
            # If salary clearly below min, skip
            nums = []
            import re

            for m in re.findall(r"\$?\s*(\d{2,3})\s*[kK]|\$\s*(\d{3},\d{3})", j.salary_text):
                if m[0]:
                    nums.append(int(m[0]) * 1000)
                elif m[1]:
                    nums.append(int(m[1].replace(",", "")))
            if nums and max(nums) < min_pay:
                continue
        out.append(j)
    return out
