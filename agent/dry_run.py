from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from . import paths
from .job_search import filter_jobs, search_arbeitnow, search_remotive
from .process_job import process_job
from .resume_parse import load_base_resume
from .setup_gate import check_setup, find_base_resume, write_needs_me_packet


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def run_dry_run(limit: int = 3) -> dict:
    gate = check_setup()
    # Allow dry-run if resume + core identity present even if START/END still null,
    # but record needs-me for schedule confirmation.
    resume_path = find_base_resume()
    hard_blockers = [b for b in gate.blockers if "START" not in b and "Daily window" not in b and "SETUP INCOMPLETE" not in b and "bracketed placeholder" not in b]
    # Re-check: if profile no longer has placeholders, gate may still fail on schedule only
    profile = paths.PROFILE.read_text(encoding="utf-8") if paths.PROFILE.exists() else ""
    schedule_only = (not resume_path is None) and ("Susmitha Chowdary" in profile) and (
        "window_start" in paths.STATE.read_text(encoding="utf-8") or True
    )

    if resume_path is None:
        packet = write_needs_me_packet(gate)
        return {"ok": False, "needs_me": str(packet), "blockers": gate.blockers, "jobs": []}

    # Soft-gate: proceed with dry-run if name + resume exist; collect remaining needs-me
    remaining_needs = []
    if "null" in paths.STATE.read_text(encoding="utf-8") or "window_start: null" in paths.STATE.read_text(encoding="utf-8"):
        remaining_needs.append("Confirm daily START and END times (Central Time already set).")
    if "CONFIRM" in profile:
        remaining_needs.append("Confirm inferred targets marked CONFIRM in memory/PROFILE.md (location preference, titles, seniority).")

    resume = load_base_resume(resume_path)
    # Force contact from known profile if parser missed
    if not resume.name:
        resume.name = "SUSMITHA CHOWDARY"
    if not resume.contact_lines:
        resume.contact_lines = [
            "Susmithachowdary67@gmail.com | 9132073787",
            "1601 Scottsdale Ln, Austin, Texas, 78754",
        ]

    raw = []
    for q in ("data engineer", "databricks data engineer", "snowflake data engineer"):
        try:
            raw.extend(search_remotive(q, limit=15))
        except Exception as e:
            remaining_needs.append(f"Remotive search error for '{q}': {e}")
        try:
            raw.extend(search_arbeitnow(q, limit=15))
        except Exception as e:
            remaining_needs.append(f"Arbeitnow search error for '{q}': {e}")

    # Dedupe by URL/title+company
    seen = set()
    uniq = []
    for j in raw:
        j.description = _strip_html(j.description)
        key = (j.url or f"{j.company}:{j.title}").lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(j)

    skip = ["clearance", "ts/sci", "staffing agency", "citizenship required", "us citizen only"]
    filtered = filter_jobs(uniq, min_pay=120000, skip_keywords=skip, require_remoteish=True)

    # Prefer titles with data engineer
    filtered.sort(key=lambda j: (0 if "data engineer" in j.title.lower() else 1, j.title.lower()))
    selected = filtered[:limit]

    day = date.today().isoformat()
    packets = []
    for job in selected:
        packets.append(process_job(resume, job, dry_run=True, my_years=5, day=day))

    # Write dry-run report
    report_dir = paths.REPORTS / day
    report_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Dry run report — {day}",
        "",
        "Status: **awaiting Susmitha's approval before any submits**",
        "",
        "## Needs me before normal daily schedule",
        *[f"- {x}" for x in remaining_needs],
        "- On every application: sponsorship/visa questions (F1-OPT) → needs me",
        "",
        "## Jobs prepared (not submitted)",
        "",
    ]
    for p in packets:
        lines.extend(
            [
                f"### {p.company} — {p.role}",
                f"- Link: {p.url}",
                f"- Scores (orig / tailored / +additions): {p.score_a} / {p.score_b} / {p.score_c}",
                f"- Top 5 missing keywords: {', '.join(p.top5_missing)}",
                f"- Status: {p.status}",
                f"- Reason: {p.reason or '(n/a)'}",
                f"- Resume (a): `{p.resume_a}`",
                f"- Resume (b) hedged — verify before applying: `{p.resume_b}`",
                f"- Catch note: `{p.catch_note}`",
                f"- Scorecard: `{p.scorecard}`",
                f"- Additions flagged: {', '.join(p.additions_flagged) or '(none)'}",
                f"- Interview prep: `{p.interview_prep}`" if p.interview_prep else "- Interview prep: (score < 8)",
                "",
            ]
        )
    if not packets:
        lines.append("_No jobs found in free public APIs for the last 7 days matching filters. Needs broader LinkedIn/Indeed/company-page search with browser once you approve login._")

    report_path = report_dir / "DRY_RUN.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Update state
    state = paths.STATE.read_text(encoding="utf-8")
    state = state.replace("dry_run_complete: false", "dry_run_complete: true")
    paths.STATE.write_text(state, encoding="utf-8")

    return {
        "ok": True,
        "report": str(report_path),
        "jobs": packets,
        "needs_me": remaining_needs,
        "hard_blockers": hard_blockers,
        "schedule_only": schedule_only,
    }
