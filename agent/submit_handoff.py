from __future__ import annotations

import json
from pathlib import Path

from . import paths
from .curve_apply import evaluate_curve_gate, write_gate_report
from .ready_submits import evaluate_all_ready_submits, write_ready_submits_report
from .salary import salary_from_memory
from .window import check_apply_window, chicago_today


SUBMIT_DIR = paths.ROOT / "resumes" / "submit"


def _proof_day() -> str:
    """Use next CT calendar morning when preparing overnight for an 08:00 submit."""
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    now = __import__("datetime").datetime.now(ZoneInfo("America/Chicago"))
    window = check_apply_window()
    if window.open:
        return now.date().isoformat()
    # After noon CT, overnight prep targets tomorrow's apply day
    if now.hour >= 12:
        return (now.date() + timedelta(days=1)).isoformat()
    return now.date().isoformat()


def _safe_proof_name(company: str, role: str) -> str:
    raw = f"{company}_{role}"
    cleaned = "".join(ch if ch.isalnum() or ch in "-_ " else " " for ch in raw)
    return "_".join(cleaned.split())[:120]


def build_submit_handoff(*, day: str | None = None) -> dict:
    """Machine-readable morning submit plan for computer-use."""
    day = day or _proof_day()
    window = check_apply_window()
    salary = salary_from_memory()
    ready = evaluate_all_ready_submits()
    ready_report = write_ready_submits_report(day=day)
    gate = evaluate_curve_gate()
    gate_report = write_gate_report(day=day)

    queue = []
    for item in ready:
        short = SUBMIT_DIR / f"Susmitha_{item.key}.docx"
        queue.append(
            {
                "order": len(queue) + 1,
                "key": item.key,
                "company": item.company,
                "role": item.role,
                "url": item.url,
                "needs_salary": item.needs_salary,
                "ok_now": item.ok,
                "blockers": item.blockers,
                "kit": str(item.kit),
                "resume": str(item.resume),
                "resume_short": str(short if short.exists() else item.resume),
                "proof_dir": str(paths.APPLICATIONS / "applied" / day / _safe_proof_name(item.company, item.role)),
                "computer_use_prompt": item.computer_use_prompt,
            }
        )

    # Curve Dental already applied 2026-11-12 — keep gate report for audit only, do not re-queue.

    payload = {
        "day": day,
        "window_open": window.open,
        "window_reason": window.reason,
        "salary": salary,
        "ready_submits_report": str(ready_report),
        "curve_gate_report": str(gate_report),
        "runbook": str(paths.APPLICATIONS / "ready" / day / "README.md"),
        "submit_order": [q["key"] for q in queue],
        "queue": queue,
        "instructions": [
            "Submit only while window_open is true (08:00–12:00 America/Chicago).",
            "Never Easy Apply — company ATS only.",
            "Do not invent salary; use Memory 120000 when asked.",
            "Prefer resume_short paths under resumes/submit/.",
            "Email security code / captcha → needs-me (Gmail declined; paste code in chat).",
            "After each confirmation, write proof files then python3 -m agent proof.",
        ],
    }

    out_dir = paths.REPORTS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "SUBMIT_HANDOFF.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = out_dir / "SUBMIT_HANDOFF.md"
    lines = [
        f"# Submit handoff — {day}",
        "",
        f"- Window open: **{window.open}**",
        f"- Salary: **{salary or 'MISSING'}**",
        f"- Runbook: `{payload['runbook']}`",
        "",
        "## Queue",
    ]
    for q in queue:
        lines.append(
            f"{q['order']}. **{q['company']} / {q['role']}** — ready_now={q['ok_now']} — {q['url']}"
        )
        lines.append(f"   - resume: `{q['resume_short']}`")
        lines.append(f"   - kit: `{q['kit']}`")
        if q["blockers"]:
            lines.append(f"   - blockers: {', '.join(q['blockers'])}")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload["handoff_json"] = str(path)
    payload["handoff_md"] = str(md)
    return payload
