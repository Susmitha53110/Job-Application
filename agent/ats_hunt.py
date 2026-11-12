from __future__ import annotations

import html
import re
from dataclasses import asdict
from datetime import date

from .job_search import JobPosting, _get_json, _parse_dt, filter_jobs, is_us_remote, within_max_age


DEFAULT_GH_BOARDS = [
    "tebra",
    "consumeredge",
    "keebo",
    "databricks",
    "snowflake",
    "fivetran",
    "airbyte",
    "notion",
    "stripe",
    "cloudflare",
    "duolingo",
    "reddit",
    "discord",
    "figma",
    "asana",
    "dropbox",
    "affirm",
    "chime",
    "brex",
    "ramp",
    "carta",
    "gusto",
    "rippling",
    "samsara",
    "toast",
    "shopify",
    "datadog",
    "elastic",
    "hashicorp",
    "gitlab",
    "twilio",
    "okta",
    "pagerduty",
    "mongodb",
    "confluent",
    "census",
    "hightouch",
    "segment",
    "amplitude",
    "mixpanel",
    "posthog",
    "zendesk",
    "intercom",
    "hubspot",
    "plaid",
    "unit",
    "column",
    "vanta",
    "drata",
    "persona",
    "alloy",
    "zapier",
    "workato",
    "dagster",
    "prefect",
    "astronomer",
    "clickhouse",
    "firebolt",
    "materialize",
    "redpanda",
    "atlan",
    "bigeye",
    "datafold",
    "branch",
    "workos",
    "adyen",
    "perfectserve",
    "flatironhealth",
    "talkspace",
    "natera",
    "veracyte",
    "oscarhealth",
    "lyrahealth",
    "springhealth",
    "sezzle",
    "machinifyinc",
    "zipcolimited",
    "ninjaone",
    "zocdoc",
    "omadahealth",
    "komodohealth",
    "dbtlabs",
    "betterhelpcom",
    "life360",
    "tempus",
    "athenahealth",
    "headway",
    "goodrx",
    "doximity",
    "datavant",
    "montecarlodata",
    "constantcontact",
    "extend",
]


TITLE_HINTS = (
    "data engineer",
    "analytics engineer",
    "etl engineer",
    "data platform",
    "warehouse engineer",
    "snowflake engineer",
    "databricks engineer",
    "data & analytics",
    "data and analytics",
    "data integration",
    "analytics platform",
    "data analytics engineer",
)


def _strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _title_match(title: str) -> bool:
    tl = (title or "").lower()
    if any(x in tl for x in ("director", "vp ", "vice president", "chief ", "intern", "co-op")):
        return False
    if any(x in tl for x in TITLE_HINTS):
        return True
    # Healthcare/product SWE titles that are clearly data-platform roles
    if "software engineer" in tl and any(
        x in tl for x in ("data", "analytics", "etl", "pipeline", "warehouse")
    ):
        return True
    return False


def hunt_greenhouse(boards: list[str] | None = None, max_age_days: int = 4) -> list[JobPosting]:
    out: list[JobPosting] = []
    for board in boards or DEFAULT_GH_BOARDS:
        try:
            listing = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
        except Exception:
            continue
        for j in listing.get("jobs") or []:
            if not _title_match(j.get("title") or ""):
                continue
            jid = j.get("id")
            if not jid:
                continue
            # Prefer first_published via detail endpoint
            try:
                detail = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}")
            except Exception:
                continue
            posted = detail.get("first_published") or detail.get("updated_at")
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            loc = ((detail.get("location") or {}).get("name") if isinstance(detail.get("location"), dict) else "") or ""
            desc = _strip_html(detail.get("content") or "")
            title = detail.get("title") or j.get("title") or ""
            if not is_us_remote(str(loc), desc, source="greenhouse", title=title):
                continue
            out.append(
                JobPosting(
                    title=title,
                    company=detail.get("company_name") or board,
                    url=detail.get("absolute_url") or j.get("absolute_url") or "",
                    location=str(loc),
                    description=desc,
                    source="greenhouse",
                    posted_at=posted,
                    apply_url=detail.get("absolute_url") or j.get("absolute_url"),
                    is_open=True,
                    country_hint="US",
                )
            )
    return out


def hunt_ashby(orgs: list[str], max_age_days: int = 4) -> list[JobPosting]:
    out: list[JobPosting] = []
    for org in orgs:
        try:
            data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
        except Exception:
            continue
        for j in data.get("jobs") or []:
            if not _title_match(j.get("title") or ""):
                continue
            posted = j.get("publishedAt") or j.get("updatedAt")
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            loc = j.get("location") or ""
            wt = j.get("workplaceType") or ""
            desc = _strip_html(j.get("descriptionPlain") or j.get("descriptionHtml") or "")
            title = j.get("title") or ""
            if not is_us_remote(f"{loc} {wt}", desc, source="ashby", title=title):
                continue
            out.append(
                JobPosting(
                    title=title,
                    company=org,
                    url=j.get("jobUrl") or j.get("applyUrl") or "",
                    location=str(loc),
                    description=desc,
                    source="ashby",
                    posted_at=posted,
                    apply_url=j.get("applyUrl") or j.get("jobUrl"),
                    is_open=True,
                    country_hint="US",
                )
            )
    return out


def hunt_rippling(board_slug: str, max_age_days: int = 4) -> list[JobPosting]:
    """Rippling board list lacks dates; fetch each job detail for createdOn."""
    try:
        listing = _get_json(f"https://ats.rippling.com/api/v2/board/{board_slug}/jobs")
    except Exception:
        return []
    items = listing.get("items") if isinstance(listing, dict) else listing
    if not isinstance(items, list):
        return []
    seen = set()
    out: list[JobPosting] = []
    for item in items:
        jid = item.get("id") or item.get("uuid")
        title = item.get("name") or item.get("title") or ""
        if not jid or jid in seen or not _title_match(title):
            continue
        seen.add(jid)
        try:
            detail = _get_json(f"https://ats.rippling.com/api/v2/board/{board_slug}/jobs/{jid}")
        except Exception:
            continue
        posted = detail.get("createdOn")
        if not within_max_age(posted, max_age_days=max_age_days):
            continue
        locs = detail.get("workLocations") or item.get("locations") or []
        loc_names = []
        remote_us = False
        for loc in locs:
            if isinstance(loc, str):
                name = loc
                workplace = ""
                country = ""
            elif isinstance(loc, dict):
                name = loc.get("name") or ""
                workplace = (loc.get("workplaceType") or "").upper()
                country = (loc.get("countryCode") or loc.get("country") or "").upper()
            else:
                continue
            loc_names.append(name)
            name_l = name.lower()
            if workplace == "REMOTE" and (
                country in {"US", "USA", "UNITED STATES"}
                or "united states" in name_l
                or re.search(r"\bus\b", name_l)
            ):
                remote_us = True
            elif "remote" in name_l and ("united states" in name_l or re.search(r"\bus\b", name_l)):
                remote_us = True
        location = ", ".join(loc_names) or "Remote"
        company = detail.get("companyName") or board_slug
        parts: list[str] = []
        desc_obj = detail.get("description") or {}
        if isinstance(desc_obj, dict):
            for key in ("role", "company", "responsibilities", "requirements"):
                chunk = desc_obj.get(key) or ""
                if isinstance(chunk, dict):
                    chunk = " ".join(str(v) for v in chunk.values())
                if chunk:
                    parts.append(str(chunk))
        elif desc_obj:
            parts.append(str(desc_obj))
        desc = _strip_html(" ".join(parts))
        full_title = detail.get("name") or title
        if not remote_us and not is_us_remote(location, desc, source="rippling", title=full_title):
            continue
        out.append(
            JobPosting(
                title=full_title,
                company=company,
                url=detail.get("url") or item.get("url") or f"https://ats.rippling.com/{board_slug}/jobs/{jid}",
                location=location,
                description=desc,
                source="rippling",
                posted_at=posted,
                apply_url=detail.get("url") or item.get("url"),
                is_open=True,
                country_hint="US",
            )
        )
    return out


DEFAULT_ASHBY_ORGS = [
    "people-data-labs",
    "troveo",
    "workos",
    "base-operations",
    "notion",
    "ramp",
    "linear",
    "vercel",
    "posthog",
    "vanta",
    "drata",
    "persona",
    "plaid",
    "airbyte",
    "fivetran",
    "census",
    "hightouch",
    "atlan",
    "datafold",
    "bigeye",
    "mux",
    "clera",
    "kit",
    "lumin-digital",
    "cruxclimate",
    "sentilink",
    "commure",
    "hex",
    "bayesianhealth",
    "Deepgram",
    "instructure",
    "rula",
    "talkiatry",
]

DEFAULT_RIPPLING_BOARDS = [
    "curve-dental",
    "urban-sdk",
    "sumersports",
    "joinroot",
    "accelerant",
    "intertwine-associates",
    "included-health",
    "modern-health",
]

DEFAULT_LEVER_COMPANIES = [
    "palantir",
    "netflix",
    "twitch",
    "anduril",
    "benchling",
    "color",
    "spotify",
    "affirm",
    "discord",
    "cloudflare",
]


def hunt_lever(companies: list[str] | None = None, max_age_days: int = 4) -> list[JobPosting]:
    from datetime import datetime, timezone

    out: list[JobPosting] = []
    for company in companies or DEFAULT_LEVER_COMPANIES:
        try:
            data = _get_json(f"https://api.lever.co/v0/postings/{company}?mode=json")
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for j in data:
            title = j.get("text") or ""
            if not _title_match(title):
                continue
            created = j.get("createdAt")
            if isinstance(created, (int, float)):
                posted = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
            else:
                posted = str(created) if created else None
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            cats = j.get("categories") or {}
            loc = cats.get("location") or ""
            workplace = cats.get("workplaceType") or j.get("workplaceType") or ""
            desc = _strip_html(j.get("descriptionPlain") or j.get("description") or "")
            if not is_us_remote(f"{loc} {workplace}", desc, source="lever", title=title):
                continue
            out.append(
                JobPosting(
                    title=title,
                    company=company,
                    url=j.get("hostedUrl") or j.get("applyUrl") or "",
                    location=str(loc),
                    description=desc,
                    source="lever",
                    posted_at=posted,
                    apply_url=j.get("applyUrl") or j.get("hostedUrl"),
                    is_open=True,
                    country_hint="US",
                )
            )
    return out


# Himalayas companyName → Greenhouse board slug when known (prefer company ATS over himalayas.app).
HIMALAYAS_GH_BOARDS = {
    "betterhelp": "betterhelpcom",
    "life360": "life360",
    "talkspace": "talkspace",
}


def hunt_himalayas(*, max_age_days: int = 4, max_pages: int = 8) -> list[JobPosting]:
    """Probe Himalayas public jobs API; prefer Greenhouse apply URLs when board is known."""
    out: list[JobPosting] = []
    cursor = None
    for _ in range(max_pages):
        url = "https://himalayas.app/jobs/api?limit=50"
        if cursor:
            url += f"&cursor={cursor}"
        try:
            data = _get_json(url)
        except Exception:
            break
        for j in data.get("jobs") or []:
            title = j.get("title") or ""
            if not _title_match(title):
                continue
            tl = title.lower()
            if any(x in tl for x in ("staff", "principal", "director", "manager", "intern", "extern")):
                continue
            pub = j.get("pubDate")
            posted = str(pub) if pub is not None else None
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            locs = j.get("locationRestrictions") or []
            if isinstance(locs, list) and locs:
                if not any(
                    "united states" in str(x).lower() or str(x).lower() in {"usa", "us", "worldwide", "anywhere"}
                    for x in locs
                ):
                    continue
                loc_s = ", ".join(str(x) for x in locs)
            else:
                loc_s = "Remote, United States"
            company = j.get("companyName") or "Unknown"
            desc = j.get("description") or ""
            if isinstance(desc, list):
                desc = " ".join(str(x) for x in desc)
            desc = _strip_html(str(desc))
            apply = j.get("applicationLink") or j.get("guid") or ""
            # Prefer company Greenhouse board when we know the slug
            board = HIMALAYAS_GH_BOARDS.get(company.lower().replace(" ", ""))
            if board:
                try:
                    listing = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
                    for gj in listing.get("jobs") or []:
                        if (gj.get("title") or "").strip().lower() != title.strip().lower():
                            continue
                        jid = gj.get("id")
                        if not jid:
                            continue
                        detail = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}")
                        posted_gh = detail.get("first_published") or detail.get("updated_at") or posted
                        if not within_max_age(posted_gh, max_age_days=max_age_days):
                            continue
                        loc = ((detail.get("location") or {}).get("name") if isinstance(detail.get("location"), dict) else "") or loc_s
                        desc_gh = _strip_html(detail.get("content") or "") or desc
                        apply_gh = detail.get("absolute_url") or gj.get("absolute_url") or apply
                        if not is_us_remote(str(loc), desc_gh, source="greenhouse", title=title):
                            continue
                        out.append(
                            JobPosting(
                                title=detail.get("title") or title,
                                company=company,
                                url=apply_gh,
                                location=str(loc),
                                description=desc_gh,
                                source="greenhouse",
                                posted_at=posted_gh,
                                apply_url=apply_gh,
                                is_open=True,
                                country_hint="US",
                            )
                        )
                        break
                    else:
                        board = None  # fall through to himalayas link
                except Exception:
                    board = None
            if board:
                continue
            if not is_us_remote(loc_s, desc, source="himalayas", title=title):
                continue
            out.append(
                JobPosting(
                    title=title,
                    company=company,
                    url=apply,
                    location=loc_s,
                    description=desc,
                    source="himalayas",
                    posted_at=posted,
                    apply_url=apply,
                    is_open=True,
                    country_hint="US",
                )
            )
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return out


def hunt_jsonld_pages(pages: list[tuple[str, str]], *, max_age_days: int = 4) -> list[JobPosting]:
    """Fetch company careers pages that expose schema.org JobPosting JSON-LD."""
    import json
    import urllib.request

    out: list[JobPosting] = []
    for company, page_url in pages:
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "SusmithaJobAgent/0.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_html = resp.read().decode("utf-8", "replace")
        except Exception:
            continue
        m = re.search(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            raw_html,
            re.I | re.S,
        )
        if not m:
            continue
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(data, list):
            data = next((x for x in data if isinstance(x, dict) and x.get("@type") == "JobPosting"), None)
        if not isinstance(data, dict) or data.get("@type") != "JobPosting":
            continue
        title = data.get("title") or ""
        if not _title_match(title):
            continue
        posted = data.get("datePosted")
        if not within_max_age(posted, max_age_days=max_age_days):
            continue
        desc = _strip_html(
            " ".join(
                str(data.get(k) or "")
                for k in ("description", "qualifications", "responsibilities", "skills")
            )
        )
        loc_obj = data.get("jobLocation") or {}
        if isinstance(loc_obj, list) and loc_obj:
            loc_obj = loc_obj[0]
        addr = (loc_obj.get("address") if isinstance(loc_obj, dict) else {}) or {}
        country = addr.get("addressCountry") if isinstance(addr, dict) else ""
        country_s = str(country).strip() or "United States"
        # Benefits "remote" often sits past is_us_remote's description[:2000] window —
        # stamp Remote into location when the full JSON-LD text mentions it.
        remote_in_page = "remote" in desc.lower() or "work from home" in desc.lower()
        location = f"{country_s}, Remote" if remote_in_page else country_s
        if not is_us_remote(location, desc, source="jsonld", title=title):
            if country_s.lower() not in {"united states", "usa", "us"} and "united states" not in desc.lower():
                continue
            if not remote_in_page:
                continue
        out.append(
            JobPosting(
                title=title,
                company=company,
                url=(data.get("url") or page_url).rstrip("?"),
                location=location,
                description=desc,
                source="jsonld",
                posted_at=posted,
                apply_url=(data.get("url") or page_url).rstrip("?"),
                is_open=True,
                country_hint="US",
            )
        )
    return out


JSONLD_CAREERS_PAGES = [
    ("Velosio", "https://careers.velosio.com/jobs/3162"),
]


def hunt_all(*, max_age_days: int = 4) -> list[JobPosting]:
    from .job_search import search_arbeitnow, search_remotive
    from .watchlist import poll_watchlist

    jobs: list[JobPosting] = []
    jobs.extend(hunt_greenhouse(max_age_days=max_age_days))
    jobs.extend(hunt_ashby(DEFAULT_ASHBY_ORGS, max_age_days=max_age_days))
    for slug in DEFAULT_RIPPLING_BOARDS:
        jobs.extend(hunt_rippling(slug, max_age_days=max_age_days))
    jobs.extend(hunt_lever(max_age_days=max_age_days))
    try:
        jobs.extend(hunt_himalayas(max_age_days=max_age_days))
    except Exception:
        pass
    try:
        jobs.extend(hunt_jsonld_pages(JSONLD_CAREERS_PAGES, max_age_days=max_age_days))
    except Exception:
        pass
    jobs.extend(poll_watchlist(max_age_days=max_age_days))
    for q in ("data engineer", "analytics engineer", "snowflake data engineer", "databricks data engineer"):
        try:
            jobs.extend(search_remotive(q, limit=25, max_age_days=max_age_days))
        except Exception:
            pass
        try:
            jobs.extend(search_arbeitnow(q, limit=25, max_age_days=max_age_days))
        except Exception:
            pass
    # Deduplicate
    seen = set()
    uniq = []
    for j in jobs:
        key = (j.url or f"{j.company}:{j.title}").lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(j)
    return filter_jobs(uniq, max_age_days=max_age_days)


def hunt_near_miss(*, lookback_days: int = 10) -> list[JobPosting]:
    """US-remote DE/AE roles 5–10 days old — watch only, never apply (fail-closed ≤4d)."""
    wide = hunt_all(max_age_days=lookback_days)
    return [j for j in wide if not within_max_age(j.posted_at, max_age_days=4)]


if __name__ == "__main__":
    found = hunt_all()
    print(f"found {len(found)} on {date.today().isoformat()}")
    for j in found:
        print(f"{j.posted_at} | {j.company} | {j.title} | {j.location} | {j.url}")
        print(asdict(j).keys())
