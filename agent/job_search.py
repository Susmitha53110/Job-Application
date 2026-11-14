from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# Locked search policy from Susmitha (PROFILE: prefer remote; hybrid/on-site US OK)
DEFAULT_MAX_AGE_DAYS = 10
US_ONLY = True
REMOTE_ONLY = False  # prefer remote; allow US hybrid/on-site (relocate Yes)
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


def _explicit_us_mention(text: str) -> bool:
    """True when text clearly names the United States (word-bounded; avoids 'reusable')."""
    t = (text or "").lower()
    if re.search(r"\bunited states\b|\bu\.s\.a?\b|\bus-based\b|\bus based\b", t):
        return True
    if re.search(r"\busa\b", t):  # word-bounded — not 'reusable' / 'usability'
        return True
    # Greenhouse-style "US - TX" / "US-Remote" / leading "US" location tokens
    if re.search(r"(?:^|[\s,;(])us(?:\s*[-–—/,]|\s*$)", t):
        return True
    if re.search(
        r"\bus[\s\-–—]?remote\b|\bremote[\s\-–,–—]?us\b|\bremote,\s*u\.?s\.?\b|\bu\.?s\.?\s*remote\b|"
        r"\banywhere in the us\b|\bwithin the united states\b|\bus only\b|"
        r"\bremote - us\b|\bremote us\b|\bremote, us\b|\bus - remote\b|\bus remote\b|"
        r"\bremote \(us|\bremote \(u\.s",
        t,
    ):
        return True
    return False


def is_us_location(location: str, description: str = "", *, title: str = "") -> bool:
    """True when the role is clearly US-based (remote, hybrid, or on-site)."""
    loc_l = (location or "").lower()
    blob = f"{title} {location} {description[:1500]}".lower()
    if _explicit_us_mention(loc_l) or _explicit_us_mention(blob):
        # Still reject pure EU/APAC location strings with no US in location
        non_us_loc = any(
            x in loc_l
            for x in (
                "netherlands",
                "germany",
                "spain",
                "united kingdom",
                "ireland",
                "france",
                "portugal",
                "poland",
                "india",
                "canada",
                "australia",
                "singapore",
                "israel",
                "emea",
                "europe",
                "latam",
                "apac",
            )
        )
        if non_us_loc and not _explicit_us_mention(loc_l):
            return False
        return True
    if re.search(
        r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|"
        r"hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|"
        r"michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|"
        r"new mexico|new york|nyc|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|"
        r"rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|"
        r"west virginia|wisconsin|wyoming|austin|seattle|chicago|denver|boston|atlanta|dallas|"
        r"san francisco|los angeles|san jose|brooklyn|manhattan)\b",
        loc_l,
    ):
        return True
    # Common US state abbreviations in location strings (e.g. "US - TX", "NY, USA")
    if re.search(
        r"(?:^|[\s,;\-/])(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|"
        r"mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)(?:\s|$|[,;/\)])",
        loc_l,
    ):
        return True
    return False


def is_us_remote(location: str, description: str = "", *, source: str = "", title: str = "") -> bool:
    loc_l = (location or "").lower()
    blob = f"{title} {location} {description[:2000]}".lower()
    # Structured location wins: EU/UK/etc. office lists without US → not US-remote.
    non_us_loc = any(
        x in loc_l
        for x in (
            "netherlands",
            "amsterdam",
            "germany",
            "berlin",
            "frankfurt",
            "spain",
            "madrid",
            "barcelona",
            "united kingdom",
            "england",
            "london",
            "ireland",
            "dublin",
            "france",
            "paris",
            "portugal",
            "lisbon",
            "poland",
            "warsaw",
            "india",
            "bangalore",
            "bengaluru",
            "hyderabad",
            "canada",
            "toronto",
            "vancouver",
            "australia",
            "sydney",
            "melbourne",
            "singapore",
            "israel",
            "tel aviv",
            "emea",
            "europe",
            "latam",
            "apac",
        )
    )
    loc_has_us = _explicit_us_mention(loc_l) or bool(
        re.search(
            r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|"
            r"hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|"
            r"michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|"
            r"new mexico|new york|nyc|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|"
            r"rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|"
            r"west virginia|wisconsin|wyoming|austin|seattle|chicago|denver|boston|atlanta|dallas)\b",
            loc_l,
        )
    )
    if non_us_loc and not loc_has_us:
        return False
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
            "netherlands",
            "spain",
        )
    ):
        # Allow only if also explicitly US remote (word-bounded)
        if not _explicit_us_mention(blob):
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
    us_ok = _explicit_us_mention(blob)
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


def is_us_work_ok(location: str, description: str = "", *, source: str = "", title: str = "") -> bool:
    """US remote (preferred) OR US hybrid/on-site per PROFILE standing answers."""
    if is_us_remote(location, description, source=source, title=title):
        return True
    # Hybrid / on-site US — Susmitha relocates Yes, hybrid Yes
    blob = f"{title} {location} {description[:1500]}".lower()
    loc_l = (location or "").lower().strip()
    # Bare "Remote" + US work-auth language in JD → treat as US-remote eligible
    if loc_l in {"remote", "remote work", "fully remote"} and re.search(
        r"\bunited states\b|\bu\.s\.a?\b|\bus-based\b|\bus based\b|\bauthorization to work\b|"
        r"\blegally authorized to work in the (us|u\.s|united states)\b",
        blob,
    ):
        return True
    if not is_us_location(location, description, title=title):
        return False
    if any(
        x in blob
        for x in (
            "hybrid",
            "on-site",
            "onsite",
            "on site",
            "in-office",
            "in office",
            "office days",
            "days in office",
        )
    ):
        return True
    # Explicit US city/state location without remote/EU → treat as US on-site eligible
    loc_l = (location or "").lower()
    if loc_l and "remote" not in loc_l and is_us_location(location, "", title=title):
        return True
    return False


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


def resolve_posted_at(url: str) -> str | None:
    """Best-effort posted/updated timestamp for age-gating web-found URLs.

    Prefer Greenhouse boards API first_published/updated_at; else Ashby/LD+JSON
    datePosted via a short Playwright read. Returns ISO date/time string or None.
    """
    if not url:
        return None
    # Rippling ATS API
    m_rip = re.search(r"ats\.rippling\.com/([^/]+)/jobs/([0-9a-f-]{36})", url, re.I)
    if m_rip:
        board, jid = m_rip.group(1), m_rip.group(2)
        try:
            meta = _get_json(f"https://ats.rippling.com/api/v2/board/{board}/jobs/{jid}")
            if isinstance(meta, dict):
                return meta.get("createdOn") or meta.get("publishedOn") or meta.get("updatedAt")
        except Exception:
            pass
    # Greenhouse board API
    m = re.search(
        r"(?:boards|job-boards)\.greenhouse\.io/([^/]+)/jobs/(\d+)|"
        r"greenhouse\.io/([^/]+)/jobs/(\d+)|gh_jid=(\d+)",
        url,
        re.I,
    )
    if m:
        board = m.group(1) or m.group(3)
        jid = m.group(2) or m.group(4) or m.group(5)
        if board and jid:
            try:
                meta = greenhouse_job_meta(board, jid)
                return meta.get("first_published") or meta.get("updated_at") or meta.get("created_at")
            except Exception:
                pass
        elif jid and not board:
            # gh_jid alone — try common scrape of absolute_url later via LD
            pass
    # LD+JSON datePosted (Ashby and many career pages)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(800)
            posted = page.evaluate(
                """() => {
              for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
                try {
                  const j = JSON.parse(s.textContent || '');
                  const jobs = Array.isArray(j) ? j : (j['@graph'] || [j]);
                  for (const item of jobs) {
                    if (item && item.datePosted) return item.datePosted;
                  }
                } catch (e) {}
              }
              return null;
            }"""
            )
            browser.close()
            if posted:
                return str(posted)
    except Exception:
        return None
    return None


def assert_url_within_max_age(url: str, max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> tuple[bool, str]:
    """Return (ok, detail). Fail closed when posted date cannot be resolved."""
    posted = resolve_posted_at(url)
    if not posted:
        return False, f"unknown posted date for {url} (fail closed)"
    if within_max_age(posted, max_age_days=max_age_days):
        return True, f"posted={posted}"
    return False, f"posted={posted} older than {max_age_days}d"


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
            ok_geo = (
                is_us_remote(j.location, j.description, source=j.source, title=j.title)
                if remote_only
                else is_us_work_ok(j.location, j.description, source=j.source, title=j.title)
            )
            if not ok_geo:
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
