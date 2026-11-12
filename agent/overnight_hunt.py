from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import paths
from .ats_hunt import hunt_all, hunt_near_miss
from .process_job import process_job
from .resume_parse import load_base_resume
from .setup_gate import find_base_resume
from .watchlist import poll_watchlist, write_watchlist_report
from .window import check_apply_window
from .salary import salary_from_memory
from .curve_apply import evaluate_curve_gate, write_gate_report
from .ready_submits import evaluate_all_ready_submits, write_ready_submits_report


def run_overnight_hunt(*, day: str | None = None) -> dict:
    """Prepare-only hunt between windows. Never submits."""
    tz = ZoneInfo("America/Chicago")
    now = datetime.now(tz)
    day = day or now.date().isoformat()
    window = check_apply_window()
    salary = salary_from_memory()
    gate = evaluate_curve_gate()
    write_gate_report(day=day)
    ready_items = evaluate_all_ready_submits()
    ready_report = write_ready_submits_report(day=day)

    watch = poll_watchlist()
    write_watchlist_report(watch, day=day)
    hunted = hunt_all()
    near = hunt_near_miss(lookback_days=10)

    resume_path = find_base_resume()
    packets = []
    if resume_path is not None:
        resume = load_base_resume(resume_path)
        if not resume.name:
            resume.name = "SUSMITHA CHOWDARY"
        for job in hunted:
            if "curve" in (job.url or "").lower():
                continue
            if any(x in job.title.lower() for x in ("staff", "principal", "director", "manager")):
                continue
            if "keebo" in (job.url or "").lower():
                continue
            pkt = process_job(resume, job, dry_run=True, my_years=5, day=day)
            packets.append(
                {
                    "company": pkt.company,
                    "role": pkt.role,
                    "url": pkt.url,
                    "scores": [pkt.score_a, pkt.score_b, pkt.score_c],
                    "status": "candidate" if pkt.score_b >= 7 else "skip_low_score",
                }
            )

    eligible = [p for p in packets if p["status"] == "candidate"]
    report_dir = paths.REPORTS / day
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "OVERNIGHT_HUNT.md"
    lines = [
        f"# Overnight hunt — {day} {now.strftime('%H:%M %Z')}",
        "",
        f"- Window open: **{window.open}**",
        f"- Salary set: **{salary or 'MISSING'}**",
        f"- Curve gate ok: **{gate.ok}**",
        f"- Curve blockers: {', '.join(gate.blockers) or '(none)'}",
        f"- Ready submits report: `{ready_report}`",
        *[
            f"- {i.company} ready (ignoring window check in overnight): "
            f"**{i.ok or (len(i.blockers)==1 and 'Outside window' in i.blockers[0])}** blockers={i.blockers}"
            for i in ready_items
        ],
        f"- Watchlist hits: **{len(watch)}**",
        f"- Hunt hits (≤4d): **{len(hunted)}**",
        f"- Near-miss (5–10d, watch only): **{len(near)}**",
        f"- New ≥7 packets (non-Curve): **{len(eligible)}**",
        "",
        "## Eligible ≥7",
        *([f"- {p['company']} / {p['role']} — {p['scores']} — {p['url']}" for p in eligible] or ["- (none)"]),
        "",
        "## All scored non-Curve",
        *([f"- {p['company']} / {p['role']} — {p['scores']} — {p['status']}" for p in packets] or ["- (none)"]),
        "",
        "## Near-miss watch (do not apply — age >4d)",
        *(
            [
                f"- {j.company} / {j.title} — posted {j.posted_at} — {j.location} — {j.url}"
                for j in near[:25]
            ]
            or ["- (none)"]
        ),
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    (report_dir / "NEAR_MISS.json").write_text(
        json.dumps(
            [
                {
                    "company": j.company,
                    "title": j.title,
                    "posted_at": j.posted_at,
                    "location": j.location,
                    "url": j.url,
                    "source": j.source,
                }
                for j in near
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Update state breadcrumb
    if paths.STATE.exists():
        import re

        summary = (
            f"overnight_hunt {now.isoformat(timespec='minutes')}: "
            f"window={window.open}; salary={'set' if salary else 'MISSING'}; "
            f"hunt={len(hunted)}; ge7={len(eligible)}; curve_gate={gate.ok}"
        )
        state = paths.STATE.read_text(encoding="utf-8")
        state2, n = re.subn(r"(?m)^- last_run_summary:.*$", f'- last_run_summary: "{summary}"', state)
        if n:
            paths.STATE.write_text(state2, encoding="utf-8")

    return {
        "when": now.isoformat(),
        "window_open": window.open,
        "salary": salary,
        "curve_gate_ok": gate.ok,
        "watch_count": len(watch),
        "hunt_count": len(hunted),
        "near_miss_count": len(near),
        "eligible_ge7": eligible,
        "report": str(report),
    }


if __name__ == "__main__":
    print(json.dumps(run_overnight_hunt(), indent=2))
