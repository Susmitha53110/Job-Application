from __future__ import annotations

import html
import json
import re
from dataclasses import asdict
from pathlib import Path

from . import paths
from .job_search import JobPosting, _get_json, filter_jobs, is_us_remote, is_us_work_ok, within_max_age
from .window import chicago_today


# Companies / boards aligned to Susmitha's Optum + Azure/Databricks/Snowflake stack
GREENHOUSE_WATCH = [
    "tebra",
    "athenahealth",
    "flatironhealth",
    "tempus",
    "natera",
    "guardanthealth",
    "veracyte",
    "oscarhealth",
    "springhealth",
    "lyrahealth",
    "headway",
    "talkspace",
    "zocdoc",
    "doximity",
    "goodrx",
    "datavant",
    "healthcatalyst",
    "evolenthealth",
    "cotiviti",
    "machinifyinc",
    "perfectserve",
    "consumeredge",
    "keebo",
    "databricks",
    "fivetran",
    "airbyte",
    "dbtlabs",
    "census",
    "hightouch",
    "montecarlodata",
    "bigeye",
    "datafold",
    "atlan",
    "plaid",
    "stripe",
    "brex",
    "ramp",
    "toast",
    "samsara",
    "discord",
    "cloudflare",
    "datadog",
    "twilio",
    "okta",
    "pagerduty",
    "mongodb",
    "confluent",
    "constantcontact",
    "rackner",
    "sezzle",
    "extend",
    "branch",
    "ninjaone",
    "omadahealth",
    "komodohealth",
    "airtable",
    "retool",
    "launchdarkly",
    "cockroachlabs",
    "cribl",
    "klaviyo",
    "braze",
    "benchling",
    "color",
    "cityblockhealth",
    "noom",
    "calm",
    "whatnot",
    "faire",
    "flexport",
    "webflow",
    "doordash",
    "lyft",
    "robinhood",
    "coinbase",
    "neon",
    "planetscale",
    "anomalo",
]

ASHBY_WATCH = [
    "people-data-labs",
    "troveo",
    "workos",
    "base-operations",
    "mux",
    "clera",
    "sentilink",
    "commure",
    "kit",
    "vanta",
    "drata",
    "persona",
    "plaid",
    "ramp",
    "brex",
    "posthog",
    "hex",
    "atlan",
    "datafold",
    "bigeye",
    "airbyte",
    "fivetran",
    "census",
    "hightouch",
    "lumin-digital",
    "cruxclimate",
    "bayesianhealth",
    "instructure",
    "rula",
    "talkiatry",
    "notion",
    "retool",
    "temporal",
    "supabase",
    "statsig",
    "metronome",
    "modal",
    "replicate",
    "elevenlabs",
]

RIPPLING_WATCH = [
    "curve-dental",
    "intertwine-associates",
    "urban-sdk",
    "sumersports",
    "joinroot",
    "accelerant",
]

TITLE_HINTS = (
    "data engineer",
    "analytics engineer",
    "etl engineer",
    "data platform",
    "azure data",
    "snowflake",
    "databricks",
)


SENIOR_SKIP = ("principal", "staff", "director", "manager", "vp ", "head of", "chief ")


def _strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _title_ok(title: str, *, allow_senior: bool = False) -> bool:
    tl = (title or "").lower()
    if not any(x in tl for x in TITLE_HINTS):
        return False
    if not allow_senior and any(x in tl for x in SENIOR_SKIP):
        return False
    return True


def _visa_block(text: str) -> bool:
    return bool(
        re.search(
            r"visa support will not|visa sponsorship is not available|will not sponsor|cannot sponsor|"
            r"no sponsorship|citizen(ship)? required|us citizen only|public trust|security clearance|"
            r"clearance required|tier\s*3 federal|background investigation",
            text or "",
            re.I,
        )
    )


def poll_greenhouse(boards: list[str] | None = None, *, max_age_days: int = 10) -> list[JobPosting]:
    out: list[JobPosting] = []
    for board in boards or GREENHOUSE_WATCH:
        try:
            listing = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
        except Exception:
            continue
        for j in listing.get("jobs") or []:
            title = j.get("title") or ""
            if not _title_ok(title):
                continue
            jid = j.get("id")
            try:
                detail = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}")
            except Exception:
                continue
            posted = detail.get("first_published") or detail.get("updated_at")
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            loc = ((detail.get("location") or {}).get("name") if isinstance(detail.get("location"), dict) else "") or ""
            desc = _strip_html(detail.get("content") or "")
            if _visa_block(desc):
                continue
            if not is_us_work_ok(str(loc), desc, source="greenhouse", title=title):
                continue
            out.append(
                JobPosting(
                    title=title,
                    company=detail.get("company_name") or board,
                    url=detail.get("absolute_url") or "",
                    location=str(loc),
                    description=desc,
                    source="greenhouse",
                    posted_at=posted,
                    apply_url=detail.get("absolute_url"),
                    is_open=True,
                    country_hint="US",
                )
            )
    return out


def poll_ashby(orgs: list[str] | None = None, *, max_age_days: int = 10) -> list[JobPosting]:
    out: list[JobPosting] = []
    for org in orgs or ASHBY_WATCH:
        try:
            data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
        except Exception:
            continue
        for j in data.get("jobs") or []:
            title = j.get("title") or ""
            if not _title_ok(title):
                continue
            posted = j.get("publishedAt") or j.get("updatedAt")
            if not within_max_age(posted, max_age_days=max_age_days):
                continue
            loc = j.get("location") or ""
            wt = j.get("workplaceType") or ""
            desc = _strip_html(j.get("descriptionPlain") or j.get("descriptionHtml") or "")
            if _visa_block(desc):
                continue
            if not is_us_work_ok(f"{loc} {wt}", desc, source="ashby", title=title):
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


def poll_rippling(slugs: list[str] | None = None, *, max_age_days: int = 10) -> list[JobPosting]:
    out: list[JobPosting] = []
    for slug in slugs or RIPPLING_WATCH:
        try:
            listing = _get_json(f"https://ats.rippling.com/api/v2/board/{slug}/jobs")
        except Exception:
            continue
        items = listing.get("items") if isinstance(listing, dict) else listing
        if not isinstance(items, list):
            continue
        seen = set()
        for item in items:
            jid = item.get("id") or item.get("uuid")
            title = item.get("name") or item.get("title") or ""
            if not jid or jid in seen or not _title_ok(title):
                continue
            seen.add(jid)
            try:
                detail = _get_json(f"https://ats.rippling.com/api/v2/board/{slug}/jobs/{jid}")
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
            desc_obj = detail.get("description") or {}
            desc_html = ""
            if isinstance(desc_obj, dict):
                desc_html = str(desc_obj.get("company") or "") + " " + str(desc_obj.get("role") or "")
            desc = _strip_html(desc_html)
            if _visa_block(desc):
                continue
            full_title = detail.get("name") or title
            if not remote_us and not is_us_work_ok(location, desc, source="rippling", title=full_title):
                continue
            out.append(
                JobPosting(
                    title=full_title,
                    company=detail.get("companyName") or slug,
                    url=detail.get("url") or item.get("url") or "",
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


def poll_watchlist(*, max_age_days: int = 10) -> list[JobPosting]:
    jobs: list[JobPosting] = []
    jobs.extend(poll_greenhouse(max_age_days=max_age_days))
    jobs.extend(poll_ashby(max_age_days=max_age_days))
    jobs.extend(poll_rippling(max_age_days=max_age_days))
    seen = set()
    uniq = []
    for j in jobs:
        key = (j.url or f"{j.company}:{j.title}").lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(j)
    return filter_jobs(uniq, max_age_days=max_age_days)


def write_watchlist_report(jobs: list[JobPosting], day: str | None = None) -> Path:
    day = day or chicago_today().isoformat()
    out_dir = paths.REPORTS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "WATCHLIST.md"
    lines = [
        f"# Watchlist poll — {day}",
        "",
        f"Mid-level US-remote ≤{4}d filter-pass hits: **{len(jobs)}**",
        "",
    ]
    if not jobs:
        lines.append("_No new mid-level hits on the target watchlist._")
    for j in jobs:
        lines.append(f"- {j.posted_at} | {j.company} | {j.title} | {j.location} | {j.url}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "WATCHLIST.json").write_text(
        json.dumps([asdict(j) for j in jobs], indent=2) + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    found = poll_watchlist()
    report = write_watchlist_report(found)
    print(json.dumps({"count": len(found), "report": str(report), "jobs": [asdict(j) for j in found]}, indent=2))
