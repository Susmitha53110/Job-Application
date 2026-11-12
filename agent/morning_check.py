from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths
from .curve_apply import evaluate_curve_gate
from .job_search import _get_json, within_max_age
from .ready_submits import evaluate_all_ready_submits, packet_ready_except_window
from .salary import salary_from_memory
from .submit_handoff import build_submit_handoff
from .window import check_apply_window, chicago_today


@dataclass
class CheckItem:
    name: str
    ok: bool
    detail: str


def run_morning_check() -> dict:
    """Go/no-go checklist for the next CT apply window."""
    checks: list[CheckItem] = []
    window = check_apply_window()
    salary = salary_from_memory()
    handoff = build_submit_handoff()
    ready = evaluate_all_ready_submits()
    gate = evaluate_curve_gate()

    # Files
    for key in ("clera", "bayesian", "curve"):
        docx = paths.ROOT / "resumes" / "submit" / f"Susmitha_{key}.docx"
        checks.append(CheckItem(f"resume_short_{key}", docx.exists(), str(docx)))

    kits = {
        "clera": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Clera_SUBMIT_KIT.md",
        "bayesian": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Bayesian_Health_SUBMIT_KIT.md",
        "curve": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Curve_Dental_SUBMIT_KIT.md",
        "first_applies": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "FIRST_APPLIES.md",
        "form_map": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "CURVE_FORM_MAP.md",
    }
    for name, path in kits.items():
        checks.append(CheckItem(f"kit_{name}", path.exists(), str(path)))

    # Live packet readiness (window may still be closed)
    for item in ready:
        checks.append(
            CheckItem(
                f"packet_{item.key}",
                packet_ready_except_window(item),
                f"blockers={item.blockers}; url={item.url}",
            )
        )
        # Live URL fetch
        try:
            if "ashbyhq.com" in item.url:
                org = "Clera" if item.key == "clera" else "bayesianhealth"
                data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
                found = any(item.url in (j.get("jobUrl") or "") for j in (data.get("jobs") or []))
                checks.append(CheckItem(f"live_{item.key}", found, item.url))
            else:
                checks.append(CheckItem(f"live_{item.key}", True, item.url))
        except Exception as e:
            checks.append(CheckItem(f"live_{item.key}", False, str(e)))

    # Curve age
    try:
        detail = _get_json(
            "https://ats.rippling.com/api/v2/board/curve-dental/jobs/81161b01-ae38-49d2-9ca8-3b618d31c394"
        )
        created = detail.get("createdOn")
        checks.append(
            CheckItem(
                "curve_age_le_4d",
                within_max_age(created, 4),
                f"createdOn={created}",
            )
        )
    except Exception as e:
        checks.append(CheckItem("curve_age_le_4d", False, str(e)))

    checks.append(CheckItem("salary_set_for_curve", bool(salary), salary or "MISSING"))
    checks.append(
        CheckItem(
            "curve_packet_except_salary_window",
            all(
                ("Outside window" in b) or ("Salary expectations" in b)
                for b in gate.blockers
            )
            if gate.blockers
            else gate.ok,
            f"blockers={gate.blockers}",
        )
    )

    # Authorization flags from Memory
    state = paths.STATE.read_text(encoding="utf-8") if paths.STATE.exists() else ""
    checks.append(
        CheckItem(
            "real_applies_authorized",
            "real_applies_authorized: true" in state,
            "memory/STATE.md",
        )
    )
    checks.append(
        CheckItem(
            "dry_run_approved",
            "dry_run_approved: true" in state,
            "memory/STATE.md",
        )
    )

    failed = [c for c in checks if not c.ok]
    # Soft fails: salary and window are expected overnight
    soft = {"salary_set_for_curve"}
    hard_failed = [c for c in failed if c.name not in soft and "Outside window" not in c.detail]

    day = handoff.get("day") or chicago_today().isoformat()
    out_dir = paths.REPORTS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "day": day,
        "window_open": window.open,
        "window_reason": window.reason,
        "salary": salary,
        "go": len(hard_failed) == 0,
        "hard_failures": [asdict(c) for c in hard_failed],
        "soft_failures": [asdict(c) for c in failed if c.name in soft],
        "checks": [asdict(c) for c in checks],
        "handoff_json": handoff.get("handoff_json"),
        "submit_order": handoff.get("submit_order"),
    }
    path = out_dir / "MORNING_GO_NOGO.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = out_dir / "MORNING_GO_NOGO.md"
    lines = [
        f"# Morning go/no-go — {day}",
        "",
        f"- GO (hard checks): **{payload['go']}**",
        f"- Window open: **{window.open}**",
        f"- Salary: **{salary or 'MISSING'}**",
        "",
        "## Hard failures",
        *([f"- {c.name}: {c.detail}" for c in hard_failed] or ["- (none)"]),
        "",
        "## Soft failures (expected until answered / window)",
        *([f"- {c['name']}: {c['detail']}" for c in payload["soft_failures"]] or ["- (none)"]),
        "",
        "## All checks",
        *[f"- {'PASS' if c.ok else 'FAIL'} `{c.name}` — {c.detail}" for c in checks],
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    payload["report_md"] = str(md)
    payload["report_json"] = str(path)
    return payload
