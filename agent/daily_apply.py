from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import paths
from .ats_hunt import hunt_all
from .log_writer import append_applied_index, append_log_row
from .morning_run import readiness_report, _salary_from_memory, CURVE_URL
from .process_job import process_job
from .proof import require_proof_for_applied, write_proof_manifest
from .resume_parse import load_base_resume
from .setup_gate import find_base_resume
from .window import check_apply_window


def _load_resume():
    resume_path = find_base_resume()
    if resume_path is None:
        raise FileNotFoundError("Base resume missing under resumes/base/")
    resume = load_base_resume(resume_path)
    if not resume.name:
        resume.name = "SUSMITHA CHOWDARY"
    if not resume.contact_lines:
        resume.contact_lines = [
            "Susmithachowdary67@gmail.com | 9132073787",
            "1601 Scottsdale Ln, Austin, Texas, 78754",
        ]
    return resume


def write_daily_report(day: str, payload: dict) -> Path:
    report_dir = paths.REPORTS / day
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{day}.md" if False else report_dir.joinpath("DAILY.md")
    lines = [
        f"# Daily report — {day}",
        "",
        f"- Window open at run: **{payload.get('window_open')}**",
        f"- Salary present: **{payload.get('salary') or 'MISSING'}**",
        f"- Hunt count: **{payload.get('hunt_count')}**",
        f"- Ready: **{len(payload.get('ready') or [])}**",
        f"- Applied: **{len(payload.get('applied') or [])}**",
        f"- Unconfirmed: **{len(payload.get('unconfirmed') or [])}**",
        f"- Skipped: **{len(payload.get('skipped') or [])}**",
        f"- Needs me: **{len(payload.get('needs_me') or [])}**",
        "",
        "## Applied",
        *([f"- {x}" for x in payload.get("applied") or ["(none)"]]),
        "",
        "## Unconfirmed",
        *([f"- {x}" for x in payload.get("unconfirmed") or ["(none)"]]),
        "",
        "## Skipped",
        *([f"- {x}" for x in payload.get("skipped") or ["(none)"]]),
        "",
        "## Needs me",
        *([f"- {x}" for x in payload.get("needs_me") or ["(none)"]]),
        "",
        "## Notes",
        payload.get("notes") or "(none)",
        "",
        "## Curve submit kit",
        "- applications/needs-me/2026-11-12/Curve_Dental_SUBMIT_KIT.md",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_daily(*, day: str | None = None, dry: bool = False) -> dict:
    """Orchestrate one daily cycle.

    dry=True: never claim submits; always prepare/hunt/report only.
    Outside window or missing salary: prepare only + needs-me.
    Actual browser submits happen via computer-use follow-up using the submit kit;
    this function records readiness and proof when provided.
    """
    day = day or date.today().isoformat()
    window = check_apply_window()
    salary = _salary_from_memory()
    ready_payload = readiness_report(day=day)
    hunt = hunt_all()

    applied: list[str] = []
    unconfirmed: list[str] = []
    skipped: list[str] = []
    needs_me: list[str] = []
    notes = []

    if not window.open:
        notes.append(window.reason)
        needs_me.append("Wait for 08:00–12:00 America/Chicago window before any ATS submit")
    if not salary:
        needs_me.append(
            "Salary expectations number missing — set in applications/FORM_ANSWERS.md "
            "as `Salary expectations | 120000` (exact figure Susmitha chooses)"
        )

    # Process new hunt hits into dry-run packets for later
    resume = _load_resume()
    for job in hunt:
        if CURVE_URL in (job.url or ""):
            continue
        company_l = (job.company or "").lower()
        url_l = (job.url or "").lower()
        if "keebo" in url_l or company_l == "keebo":
            skipped.append(f"{job.company} / {job.title} — visa support will not be provided")
            append_applied_index(job.company, job.title, job.url, "skipped", day=day)
            continue
        if "consumer edge" in company_l or "consumeredge" in url_l:
            skipped.append(f"{job.company} / {job.title} — 8+ years stretch / score << 7")
            continue
        pkt = process_job(resume, job, dry_run=True, my_years=5, day=day)
        if pkt.score_b < 7:
            skipped.append(
                f"{pkt.company} / {pkt.role} — honest score (b)={pkt.score_b}/10 below 7 ({pkt.url})"
            )
            append_log_row(
                {
                    "date": day,
                    "company": pkt.company,
                    "role": pkt.role,
                    "link": pkt.url,
                    "score_original": pkt.score_a,
                    "score_tailored": pkt.score_b,
                    "score_with_additions": pkt.score_c,
                    "top5_missing_keywords": "; ".join(pkt.top5_missing),
                    "status": "skipped",
                    "reason": pkt.reason,
                    "resume_file": str(pkt.resume_a or ""),
                    "catch_note_file": str(pkt.catch_note or ""),
                    "additions_verify": "; ".join(pkt.additions_flagged),
                    "interview_prep_file": str(pkt.interview_prep or ""),
                }
            )
        else:
            needs_me.append(
                f"NEW ≥7 fit ready to apply when window+salary clear: {pkt.company} / {pkt.role} — {pkt.url}"
            )
            append_log_row(
                {
                    "date": day,
                    "company": pkt.company,
                    "role": pkt.role,
                    "link": pkt.url,
                    "score_original": pkt.score_a,
                    "score_tailored": pkt.score_b,
                    "score_with_additions": pkt.score_c,
                    "top5_missing_keywords": "; ".join(pkt.top5_missing),
                    "status": "dry-run" if dry or not window.open else "needs me",
                    "reason": "Prepared; submit only in-window with salary answered",
                    "resume_file": str(pkt.resume_a or ""),
                    "catch_note_file": str(pkt.catch_note or ""),
                    "additions_verify": "; ".join(pkt.additions_flagged),
                    "interview_prep_file": str(pkt.interview_prep or ""),
                }
            )

    # Curve guidance
    if window.open and salary and not dry:
        notes.append(
            "Curve Dental is authorized to submit now using "
            "applications/needs-me/2026-11-12/Curve_Dental_SUBMIT_KIT.md — "
            "use computer-use on Rippling ATS, then record proof via `python3 -m agent proof`."
        )
    else:
        notes.append("Curve Dental remains queued: approved packet + submit kit ready.")

    payload = {
        "window_open": window.open,
        "salary": salary,
        "hunt_count": len(hunt),
        "ready": ready_payload.get("ready"),
        "applied": applied,
        "unconfirmed": unconfirmed,
        "skipped": skipped,
        "needs_me": needs_me,
        "notes": " | ".join(notes),
        "readiness_report": ready_payload.get("report"),
    }
    report = write_daily_report(day, payload)
    payload["daily_report"] = str(report)

    # Update state summary
    if paths.STATE.exists():
        state = paths.STATE.read_text(encoding="utf-8")
        import re

        summary = (
            f"daily_apply {day}: window={window.open}; salary={'set' if salary else 'MISSING'}; "
            f"hunt={len(hunt)}; ready={len(ready_payload.get('ready') or [])}; "
            f"needs_me={len(needs_me)}"
        )
        state2, n = re.subn(
            r"(?m)^- last_run_summary:.*$",
            f"- last_run_summary: \"{summary}\"",
            state,
        )
        if n:
            state2 = re.sub(r"(?m)^- last_run_date:.*$", f"- last_run_date: {day}", state2)
            paths.STATE.write_text(state2, encoding="utf-8")

    return payload


if __name__ == "__main__":
    print(json.dumps(run_daily(dry=True), indent=2))
