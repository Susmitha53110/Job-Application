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
]


TITLE_HINTS = (
    "data engineer",
    "analytics engineer",
    "etl engineer",
    "data platform",
    "warehouse engineer",
    "snowflake engineer",
    "databricks engineer",
)


def _strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _title_match(title: str) -> bool:
    tl = (title or "").lower()
    return any(x in tl for x in TITLE_HINTS)


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
        desc_html = ""
        desc_obj = detail.get("description") or {}
        if isinstance(desc_obj, dict):
            desc_html = desc_obj.get("company") or desc_obj.get("role") or ""
            if isinstance(desc_html, dict):
                desc_html = " ".join(str(v) for v in desc_html.values())
        desc = _strip_html(str(desc_html))
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


def hunt_all(*, max_age_days: int = 4) -> list[JobPosting]:
    from .job_search import search_arbeitnow, search_remotive

    jobs: list[JobPosting] = []
    jobs.extend(hunt_greenhouse(max_age_days=max_age_days))
    jobs.extend(
        hunt_ashby(
            [
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
            ],
            max_age_days=max_age_days,
        )
    )
    jobs.extend(hunt_rippling("curve-dental", max_age_days=max_age_days))
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


if __name__ == "__main__":
    found = hunt_all()
    print(f"found {len(found)} on {date.today().isoformat()}")
    for j in found:
        print(f"{j.posted_at} | {j.company} | {j.title} | {j.location} | {j.url}")
        print(asdict(j).keys())
