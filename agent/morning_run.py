from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import paths
from .ats_hunt import hunt_all
from .job_search import JobPosting, within_max_age
from .process_job import process_job
from .resume_parse import load_base_resume
from .salary import salary_from_memory
from .setup_gate import find_base_resume
from .window import check_apply_window, chicago_today


CURVE_URL = "https://ats.rippling.com/curve-dental/jobs/81161b01-ae38-49d2-9ca8-3b618d31c394"


@dataclass
class ReadyItem:
    company: str
    role: str
    url: str
    score_b: float | None
    blockers: list[str]
    notes: str


def _salary_from_memory() -> str | None:
    return salary_from_memory()


def _curve_override() -> bool:
    if not paths.STATE.exists():
        return False
    return "curve_dental_score_override: true" in paths.STATE.read_text(encoding="utf-8")


def readiness_report(*, day: str | None = None) -> dict:
    day = day or chicago_today().isoformat()
    window = check_apply_window()
    salary = _salary_from_memory()
    hunt = hunt_all()
    items: list[ReadyItem] = []

    # Known queue specials
    curve_blockers = []
    if not window.open:
        curve_blockers.append(window.reason)
    if not salary:
        curve_blockers.append("Salary expectations number missing in Memory/FORM_ANSWERS")
    if not _curve_override():
        curve_blockers.append("Score b=5.6 requires override (not set)")
    items.append(
        ReadyItem(
            company="Curve Dental",
            role="Data Engineer",
            url=CURVE_URL,
            score_b=5.6,
            blockers=curve_blockers,
            notes="Approved filter-pass dry-run packet; resume (a) ready",
        )
    )

    for job in hunt:
        if CURVE_URL in (job.url or ""):
            continue
        # Keebo "visa support will not be provided" is OK — Memory sponsorship=No / F1-OPT.
        if "consumer edge" in job.company.lower() or "consumeredge" in (job.url or "").lower():
            items.append(
                ReadyItem(
                    company=job.company,
                    role=job.title,
                    url=job.url,
                    score_b=2.5,
                    blockers=["8+ years stretch", "score b=2.5 < 7", "salary missing" if not salary else ""],
                    notes="Skip unless Susmitha overrides years+score",
                )
            )
            continue
        # New unknown hit — process for scoring
        resume_path = find_base_resume()
        if resume_path is None:
            continue
        resume = load_base_resume(resume_path)
        if not resume.name:
            resume.name = "SUSMITHA CHOWDARY"
        pkt = process_job(resume, job, dry_run=True, my_years=5, day=day)
        blockers = []
        if not window.open:
            blockers.append(window.reason)
        if not salary:
            blockers.append("Salary expectations number missing")
        if pkt.score_b < 7:
            blockers.append(f"Honest score (b)={pkt.score_b}/10 below 7")
        items.append(
            ReadyItem(
                company=pkt.company,
                role=pkt.role,
                url=pkt.url,
                score_b=pkt.score_b,
                blockers=[b for b in blockers if b],
                notes=pkt.reason or "Prepared",
            )
        )

    ready = [i for i in items if not i.blockers]
    blocked = [i for i in items if i.blockers]

    report_dir = paths.REPORTS / day
    report_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Morning readiness — {day}",
        "",
        f"- Window open: **{window.open}** ({window.reason})",
        f"- Salary in Memory: **{salary or 'MISSING'}**",
        f"- Curve score override: **{_curve_override()}**",
        f"- Hunt filter-pass count: **{len(hunt)}**",
        f"- Ready to submit now: **{len(ready)}**",
        "",
        "## Ready",
    ]
    if not ready:
        lines.append("_None — blockers remain._")
    for i in ready:
        lines.append(f"- {i.company} / {i.role} — {i.url} (b={i.score_b})")
    lines.extend(["", "## Blocked / skip"])
    for i in blocked:
        lines.append(f"- {i.company} / {i.role} — {i.url}")
        lines.append(f"  - blockers: {'; '.join(i.blockers)}")
        lines.append(f"  - notes: {i.notes}")

    out = report_dir / "MORNING_READINESS.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "window_open": window.open,
        "salary": salary,
        "ready": [i.__dict__ for i in ready],
        "blocked": [i.__dict__ for i in blocked],
        "hunt_count": len(hunt),
        "report": str(out),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(readiness_report(), indent=2))
