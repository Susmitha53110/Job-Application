from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# Locked search policy from Susmitha (2026-11-11)
DEFAULT_MAX_AGE_DAYS = 4
US_ONLY = True
REMOTE_ONLY = True
OPEN_ONLY = True


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
    is_open: bool = True
    country_hint: str | None = None


def _get_json(url: str, timeout: int = 30) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "SusmithaJobAgent/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _cutoff(max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=max_age_days)


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    s = str(value).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def is_us_remote(location: str, description: str = "", *, source: str = "", title: str = "") -> bool:
    blob = f"{title} {location} {description[:2000]}".lower()
    if any(
        x in blob
        for x in (
            "germany",
            "berlin",
            "frankfurt",
            "france",
            "uk only",
            "united kingdom only",
            "india only",
            "europe only",
            "emea only",
            "canada only",
            "latam",
            "latin america only",
            "m/f/d",
            "peru",
            "colombia",
            "costa rica only",
            "vietnam",
            "ho chi minh",
            "philippines",
            "nigeria",
            "kenya",
            "poland only",
        )
    ):
        # Allow if also explicitly US remote
        if not any(x in blob for x in ("united states", "usa", "u.s.", "us-based", "us based", "remote - us", "remote us")):
            return False
    remote_ok = any(
        x in blob
        for x in (
            "remote",
            "work from home",
            "work from anywhere in the us",
            "work from anywhere in the united states",
            "digital-first",
            "fully remote",
        )
    )
    us_ok = any(
        x in blob
        for x in (
            "united states",
            "usa",
            "u.s.",
            "us-based",
            "us based",
            "remote - us",
            "remote us",
            "remote, us",
            "us - remote",
            "us remote",
            "remote (us",
            "remote (u.s",
            "remote - united states",
            "anywhere in the us",
            "within the united states",
            "us only",
        )
    ) or bool(
        re.search(
            r"\bus[\s\-–—]?remote\b|\bremote[\s\-–,–—]?us\b|\bremote,\s*u\.?s\.?\b|\bu\.?s\.?\s*remote\b",
            blob,
        )
    )
    # Greenhouse-style "Remote - Austin" / "Remote - CA" / "Remote - NYC" (US city/state, no country word)
    if not us_ok and remote_ok:
        loc_l = (location or "").lower()
        if re.search(
            r"\bremote\s*[-–—]\s*(usa|us|u\.s\.|united states|"
            r"alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|"
            r"hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|"
            r"michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|"
            r"new mexico|new york|nyc|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|"
            r"rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|"
            r"west virginia|wisconsin|wyoming|ca|ny|tx|wa|ma|il|ga|fl|nc|co|or|az|nv|ut|mn|mi|pa|nj|va|"
            r"seattle|austin|dallas|chicago|denver|boston|atlanta|miami|portland|phoenix|sf bay|bay area)\b",
            loc_l,
        ):
            us_ok = True
        # Multi-state lists like "California, USA; Texas, USA" already covered by usa; also bare ", USA"
        if ", usa" in loc_l or "; usa" in loc_l or loc_l.endswith(" usa"):
            us_ok = True
    # Remotive: require US/Worldwide/America style candidate location
    if source == "remotive":
        loc = location.lower()
        if "usa" in loc or "united states" in loc or loc.strip() in {"usa", "us", "united states"}:
            return True
        if "worldwide" in loc or "anywhere" in loc:
            # Still require US eligibility language in description when possible
            return us_ok or "visa" not in blob
        return us_ok
    # Jobicy remote-jobs API: jobGeo often "USA" without the word "remote" in the short payload.
    # Still require a US geo; treat the remote-jobs feed as remote_ok.
    if source == "jobicy":
        loc = location.lower().strip()
        if loc in {"usa", "us", "united states"} or "usa" in loc or "united states" in loc:
            return True
        return remote_ok and us_ok
    return remote_ok and us_ok


def search_remotive(
    search: str = "data engineer",
    limit: int = 30,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> list[JobPosting]:
    # Remotive's free-text search is noisy; also probe the data category feed.
    urls = [
        f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(search)}&limit={limit}",
        f"https://remotive.com/api/remote-jobs?category=data&limit={limit}",
    ]
    jobs: list[JobPosting] = []
    seen: set[str] = set()
    cutoff = _cutoff(max_age_days)
    for url in urls:
        try:
            data = _get_json(url)
        except Exception:
            continue
        for item in data.get("jobs", []):
            posted_dt = _parse_dt(item.get("publication_date"))
            if posted_dt and posted_dt < cutoff:
                continue
            title = item.get("title") or ""
            title_l = title.lower()
            if "data engineer" not in title_l and "analytics engineer" not in title_l:
                continue
            if any(x in title_l for x in ("staff", "principal", "director", "intern")):
                continue
            loc = item.get("candidate_required_location") or "Remote"
            desc = item.get("description") or ""
            if not is_us_remote(str(loc), desc, source="remotive", title=title):
                continue
            key = (item.get("url") or f"{item.get('company_name')}:{title}").lower()
            if key in seen:
                continue
            seen.add(key)
            jobs.append(
                JobPosting(
                    title=title,
                    company=item.get("company_name") or "Unknown",
                    url=item.get("url") or "",
                    location=str(loc),
                    description=desc,
                    source="remotive",
                    posted_at=posted_dt.date().isoformat() if posted_dt else None,
                    salary_text=item.get("salary") or None,
                    apply_url=item.get("url"),
                    is_open=True,
                    country_hint="US",
                )
            )
    return jobs


def search_arbeitnow(
    search: str = "data engineer",
    limit: int = 30,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> list[JobPosting]:
    q = urllib.parse.quote(search)
    url = f"https://www.arbeitnow.com/api/job-board-api?search={q}"
    try:
        data = _get_json(url)
    except Exception:
        return []
    jobs = []
    cutoff = _cutoff(max_age_days)
    for item in data.get("data", [])[: limit * 5]:
        posted_dt = _parse_dt(item.get("created_at"))
        if posted_dt and posted_dt < cutoff:
            continue
        title = item.get("title") or ""
        title_l = title.lower()
        if "data engineer" not in title_l and "analytics engineer" not in title_l:
            continue
        loc = (
            ", ".join(item.get("location") or [])
            if isinstance(item.get("location"), list)
            else (item.get("location") or ("Remote" if item.get("remote") else ""))
        )
        desc = item.get("description") or ""
        if not item.get("remote"):
            continue
        if not is_us_remote(str(loc), desc, source="arbeitnow", title=title):
            continue
        jobs.append(
            JobPosting(
                title=title,
                company=item.get("company_name") or "Unknown",
                url=item.get("url") or "",
                location=str(loc),
                description=desc,
                source="arbeitnow",
                posted_at=posted_dt.date().isoformat() if posted_dt else None,
                apply_url=item.get("url"),
                is_open=True,
                country_hint="US",
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


def greenhouse_job_meta(board: str, job_id: str) -> dict:
    return _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}")


def within_max_age(posted_at: str | None, max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> bool:
    if not posted_at:
        return False  # fail closed: unknown age is not eligible under 4-day rule
    dt = _parse_dt(posted_at)
    if not dt:
        # date-only YYYY-MM-DD
        try:
            dt = datetime.fromisoformat(posted_at).replace(tzinfo=timezone.utc)
        except ValueError:
            return False
    return dt >= _cutoff(max_age_days)


def filter_jobs(
    jobs: list[JobPosting],
    *,
    min_pay: int | None = 120000,
    skip_keywords: list[str] | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    us_only: bool = US_ONLY,
    remote_only: bool = REMOTE_ONLY,
    open_only: bool = OPEN_ONLY,
) -> list[JobPosting]:
    skip_keywords = [s.lower() for s in (skip_keywords or [])]
    out = []
    for j in jobs:
        if open_only and not j.is_open:
            continue
        if not within_max_age(j.posted_at, max_age_days=max_age_days):
            continue
        if us_only or remote_only:
            if not is_us_remote(j.location, j.description, source=j.source, title=j.title):
                continue
        blob = f"{j.title} {j.company} {j.location} {j.description} {j.salary_text or ''}".lower()
        if any(s in blob for s in skip_keywords):
            continue
        if min_pay and j.salary_text:
            nums = []
            for m in re.findall(r"\$?\s*(\d{2,3})\s*[kK]|\$\s*(\d{3},\d{3})", j.salary_text):
                if m[0]:
                    nums.append(int(m[0]) * 1000)
                elif m[1]:
                    nums.append(int(m[1].replace(",", "")))
            if nums and max(nums) < min_pay:
                continue
        out.append(j)
    return out
