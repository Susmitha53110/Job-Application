from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import paths
from .docx_build import ats_order_check, build_ats_docx, extract_plain_text_from_docx
from .jd_tier import tier_jd
from .job_search import JobPosting
from .log_writer import append_applied_index, append_log_row, write_catch_note, write_interview_prep, write_scorecard
from .resume_parse import Resume
from .score import keyword_coverage, score_resume_against_jd
from .tailor import tailor


@dataclass
class JobPacket:
    company: str
    role: str
    url: str
    status: str
    reason: str
    score_a: float
    score_b: float
    score_c: float
    top5_missing: list[str]
    resume_a: Path | None
    resume_b: Path | None
    catch_note: Path | None
    scorecard: Path | None
    interview_prep: Path | None
    additions_flagged: list[str]
    ats_checks: dict
    dealbreakers: list[dict]


def _safe_name(company: str, role: str) -> str:
    s = f"Susmitha_{company}_{role}"
    s = re.sub(r"[^\w\-]+", "_", s)
    return s[:100]


def _years_required(jd_text: str) -> int | None:
    m_range = re.search(
        r"(\d+)\s*[–\-to]{1,3}\s*(\d+)\s*years?.{0,60}(?:experience|engineering|data)",
        jd_text,
        re.I,
    )
    if m_range:
        # For stretch detection, use the low end of mid-level bands
        return int(m_range.group(1))
    m = re.search(
        r"(?:around\s+)?(\d+)\+?\s*(?:or more\s+)?years?.{0,60}(?:experience|engineering|data)",
        jd_text,
        re.I,
    )
    return int(m.group(1)) if m else None


def build_catch_note(
    *,
    company: str,
    role: str,
    stretch: str,
    must_be_true: list[str],
    dealbreakers: list[str],
    remove_if_unbacked: list[str],
    timeline: str,
    additions: list[str],
    score_b: float,
) -> str:
    return "\n".join(
        [
            f"# Catch note — {company} / {role}",
            "",
            f"- Stretch: {stretch}",
            "- Must be true before applying:",
            *[f"  - {x}" for x in must_be_true],
            "- Dealbreakers checked:",
            *[f"  - {x}" for x in dealbreakers],
            "- Remove if I cannot back it up in an interview:",
            *[f"  - {x}" for x in (remove_if_unbacked or ["(none beyond base resume facts)"])],
            f"- Timeline flags: {timeline}",
            f"- Honest tailored score (b): {score_b}/10 (apply threshold ≥ 7)",
            "- Version to submit: **(a) reorder-only** unless (b) approved",
            "- Additions flagged verify-before-applying:",
            *[f"  - {x}" for x in (additions or ["(none)"])],
            "- Work auth: F1-OPT → Authorized to work **Yes**; sponsorship answer **No** (Memory)",
            "",
        ]
    )


def process_job(
    resume: Resume,
    job: JobPosting,
    *,
    dry_run: bool = True,
    my_years: int = 5,
    day: str | None = None,
) -> JobPacket:
    day = day or date.today().isoformat()
    jd = tier_jd(job.title, job.company, job.url, job.location, job.description)

    # Dealbreaker evaluation for this candidate
    fail_reasons = []
    for db in jd.dealbreakers:
        name = db["name"]
        snippet = db.get("snippet", "")
        if name in {"clearance", "citizen_only"}:
            fail_reasons.append(f"Dealbreaker {name}: {snippet}")
        if name == "sponsorship" and re.search(r"citizen|no sponsorship|without sponsorship|cannot sponsor", snippet, re.I):
            # F1-OPT may still work short-term but often blocked — flag as needs review / likely skip
            fail_reasons.append(f"Sponsorship/citizenship constraint: {snippet}")
        if name == "on_site" and "austin" not in (job.location or "").lower():
            fail_reasons.append(f"On-site outside Austin: {snippet}")

    # Greenhouse application-question preflight (multi-year no-sponsorship, citizen-only, salary)
    try:
        from .form_preflight import preflight_from_url

        pf = preflight_from_url(job.url or job.apply_url or "")
        if pf and pf.blockers:
            fail_reasons.extend(pf.blockers)
    except Exception as e:
        fail_reasons.append(f"Form preflight error: {e}")

    yrs = _years_required(job.description)
    stretch = "No major years stretch detected."
    if yrs and yrs > my_years:
        stretch = f"JD asks for {yrs}+ years; Susmitha has ~{my_years}. Call this a **stretch** — do not hide the gap in the score."
    # Snowflake / specialty tenure stretches
    snow = re.search(r"(?:at least|minimum of)?\s*(\d+)\+?\s*years?.{0,40}snowflake", job.description, re.I)
    if snow and int(snow.group(1)) > 1:
        stretch = (
            (stretch + " " if stretch != "No major years stretch detected." else "")
            + f"JD asks ~{snow.group(1)}+ years production Snowflake; Optum Snowflake ownership starts May 2025 — disclose honestly."
        )

    score_orig = score_resume_against_jd(resume, jd, my_years=my_years)
    tailored = tailor(resume, jd)
    score_b = score_resume_against_jd(tailored.version_a, jd, my_years=my_years)
    score_c = score_resume_against_jd(tailored.version_b, jd, my_years=my_years)
    covered, gaps = keyword_coverage(resume, jd.keywords[:5] if jd.keywords else score_orig.top5_missing_keywords)
    top5 = score_orig.top5_missing_keywords or gaps[:5]

    status = "dry-run" if dry_run else "skipped"
    reason = "Prepared for approval; not submitted." if dry_run else ""

    if fail_reasons:
        status = "skipped" if not dry_run else "dry-run"
        reason = "; ".join(fail_reasons)
        # In dry run we still prepare packets but mark likely skip
        if fail_reasons:
            reason = "LIKELY SKIP / needs review: " + reason

    if score_b.fit_10 < 7 and not fail_reasons:
        reason = (reason + " " if reason else "") + f"Honest score (b)={score_b.fit_10}/10 below 7/10 threshold."
        if not dry_run:
            status = "skipped"

    # Build resumes a/b
    out_dir = paths.RESUMES_TAILORED / day
    out_dir.mkdir(parents=True, exist_ok=True)
    ver_dir = paths.RESUMES_VERSIONS / day
    ver_dir.mkdir(parents=True, exist_ok=True)
    base = _safe_name(job.company, job.title)
    path_a = out_dir / f"{base}.docx"
    path_b = ver_dir / f"{base}_WITH_HEDGED_ADDITIONS.docx"
    # Ensure contact from profile-ish resume fields
    if not tailored.version_a.contact_lines:
        tailored.version_a.contact_lines = list(resume.contact_lines)
        tailored.version_b.contact_lines = list(resume.contact_lines)
    if not tailored.version_a.name:
        tailored.version_a.name = resume.name or "Susmitha Chowdary"
        tailored.version_b.name = tailored.version_a.name

    build_ats_docx(tailored.version_a, path_a)
    build_ats_docx(tailored.version_b, path_b)
    plain = extract_plain_text_from_docx(path_a)
    ats = ats_order_check(plain)

    catch_body = build_catch_note(
        company=job.company,
        role=job.title,
        stretch=stretch,
        must_be_true=[
            "All bullets remain factual from base resume",
            "Work auth Yes (F1-OPT); sponsorship No (Susmitha-confirmed in Memory)",
            "Posted pay >= $120k if pay is listed",
            "Apply on company ATS only (never LinkedIn Easy Apply)",
        ],
        dealbreakers=[
            f"location={job.location}",
            "sponsorship answer No (Memory); skip employers that forbid OPT/F1 outright",
            "travel/on-site checked via JD patterns",
            "min pay $120k when posted",
            *fail_reasons,
        ],
        remove_if_unbacked=tailored.additions_flagged,
        timeline="Citi Jan 2020–May 2023; education Jan 2024–Dec 2025; Optum May 2025–Present; gap ~May 2023–Jan 2024",
        additions=tailored.additions_flagged,
        score_b=score_b.fit_10,
    )
    catch_path = write_catch_note(job.company, job.title, catch_body, day=day)

    scorecard_body = "\n".join(
        [
            f"# Scorecard — {job.company} / {job.title}",
            "",
            f"- Link: {job.url}",
            f"- Source: {job.source}",
            f"- Posted: {job.posted_at or 'unknown'}",
            "",
            "| Stage | Fit /10 | Notes |",
            "|-------|---------|-------|",
            f"| (a) Original | {score_orig.fit_10} | raw {score_orig.raw_points}/{score_orig.max_points} |",
            f"| (b) Reorder-only | {score_b.fit_10} | apply if ≥ 7 |",
            f"| (c) + hedged additions | {score_c.fit_10} | do not submit without approval |",
            "",
            "## Top 5 missing keywords (vs original)",
            *[f"- {k}" for k in top5],
            "",
            f"## Keywords covered honestly after tailor: {', '.join(covered) if covered else '(see score)'}",
            f"## Gaps remaining: {', '.join(gaps[:10])}",
            "",
            f"## Stretch call: {stretch}",
            "",
            "## ATS checks (not a 100% claim)",
            *[f"- {k}: {v}" for k, v in ats.items()],
            "",
        ]
    )
    score_path = write_scorecard(job.company, job.title, scorecard_body, day=day)

    interview_path = None
    if score_b.fit_10 >= 8:
        interview_body = _interview_prep(job.company, job.title)
        interview_path = write_interview_prep(job.company, job.title, interview_body, day=day)

    append_log_row(
        {
            "date": day,
            "company": job.company,
            "role": job.title,
            "link": job.url,
            "score_original": score_orig.fit_10,
            "score_tailored": score_b.fit_10,
            "score_with_additions": score_c.fit_10,
            "top5_missing_keywords": "; ".join(top5),
            "status": status,
            "reason": reason.strip(),
            "resume_file": str(path_a.relative_to(paths.ROOT)),
            "catch_note_file": str(catch_path.relative_to(paths.ROOT)),
            "additions_verify": "; ".join(tailored.additions_flagged),
            "interview_prep_file": str(interview_path.relative_to(paths.ROOT)) if interview_path else "",
        }
    )
    append_applied_index(job.company, job.title, job.url, status, day=day)

    return JobPacket(
        company=job.company,
        role=job.title,
        url=job.url,
        status=status,
        reason=reason.strip(),
        score_a=score_orig.fit_10,
        score_b=score_b.fit_10,
        score_c=score_c.fit_10,
        top5_missing=top5,
        resume_a=path_a,
        resume_b=path_b,
        catch_note=catch_path,
        scorecard=score_path,
        interview_prep=interview_path,
        additions_flagged=tailored.additions_flagged,
        ats_checks=ats,
        dealbreakers=jd.dealbreakers,
    )


def _interview_prep(company: str, role: str) -> str:
    return f"""# Interview prep — {company} / {role}

Built ONLY from Susmitha's real background (Optum + Citi Data Engineer, Azure/AWS/Databricks/Snowflake).

## 1) Walk me through a production pipeline you owned end-to-end.
Model answer (~spoken):
At Optum I own production ingestion in Azure Data Factory and Databricks for claims, eligibility, and provider feeds into ADLS Gen2 and Delta Lake bronze, silver, and gold. I built a config-driven PySpark framework so a new source feed went from about two weeks of onboarding to about four days. I also put automated data-quality checks in front of publication and applied HIPAA-aligned PHI controls like column masking and role-based access in Snowflake and Azure. On the Snowflake side I load validated Parquet with external stages and COPY INTO, MERGE for new and adjusted claims, and model claims, member, and provider dimensions for analytics teams. I can go deeper on any layer you care about.

## 2) How did you improve pipeline reliability or runtime with real impact?
Model answer (~spoken):
Two concrete examples. At Optum I reduced a critical claims workflow from about two hours to seventy-five minutes using incremental Delta merges, partition pruning, and fixing skewed Spark joins. I also raised scheduled pipeline success from about ninety-seven percent to ninety-nine point five with dependency checks, bounded retries, and idempotent backfills that recover failed runs without duplicating data. At Citi I shortened the overnight batch window from about five hours to three with watermark-based incremental extraction and join optimization while processing about five million payment and transaction records per business day.

## 3) How do you handle data quality and compliance in regulated data?
Model answer (~spoken):
At Optum I built automated checks for duplicate claim lines, missing identifiers, invalid service dates, and eligibility mismatches, and I quarantine failed records before publication. Because this is PHI, I applied HIPAA-aligned controls: column-level masking, role-based access, and PHI-safe logging in Snowflake and Azure. At Citi I automated source-to-target reconciliation on counts, transaction totals, and account balances, produced exception files, and prepared datasets for regulatory and risk reporting with lineage and control checks for audit review. I do not claim tools or certifications that are not on my resume.
"""
