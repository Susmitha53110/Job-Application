from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import paths
from .ats_hunt import hunt_all
from .log_writer import append_applied_index, append_log_row, load_applied_urls, url_already_applied
from .curve_apply import evaluate_curve_gate, write_gate_report
from .morning_run import readiness_report, CURVE_URL
from .process_job import JobPacket, process_job
from .ready_submits import evaluate_all_ready_submits, write_ready_submits_report
from .resume_parse import load_base_resume
from .salary import salary_from_memory
from .setup_gate import find_base_resume
from .window import check_apply_window, chicago_today
# Playwright submit helpers imported lazily inside run_daily when window is open.


def detect_ats(url: str) -> str | None:
    u = (url or "").lower()
    if "greenhouse.io" in u or "gh_jid=" in u or "boards.greenhouse.io" in u:
        return "greenhouse"
    if "ashbyhq.com" in u:
        return "ashby"
    return None


def _seniority_blocked(title: str) -> bool:
    tl = (title or "").lower()
    return any(x in tl for x in ("staff", "principal", "director", "manager", "vp ", "vice president"))


def _packet_auto_submitable(pkt: JobPacket) -> tuple[bool, str | None]:
    """Return (ok, skip_reason) for in-window Playwright auto-submit."""
    if pkt.score_b < 7:
        return False, "score < 7"
    if _seniority_blocked(pkt.role):
        return False, "seniority staff/principal/director/manager"
    reason_l = (pkt.reason or "").lower()
    if "citizen" in reason_l or "green-card only" in reason_l or "green card" in reason_l:
        return False, "citizen/green-card gate"
    if "icims" in reason_l or "login" in reason_l:
        return False, "login-gated ATS"
    if "likely skip" in reason_l and ("dealbreaker" in reason_l or "citizenship" in reason_l):
        return False, "dealbreaker skip"
    company_l = (pkt.company or "").lower()
    url_l = (pkt.url or "").lower()
    if "velosio" in company_l or "velosio" in url_l:
        return False, "Velosio iCIMS needs-me"
    if "lumin" in company_l or "lumin-digital" in url_l:
        return False, "lumin biometric needs-me"
    if "ninjaone" in company_l or "ninjaone" in url_l:
        return False, "NinjaOne citizen_only"
    if "natera" in company_l or "natera" in url_l:
        return False, "Natera OTP needs-me (Gmail declined)"
    ats = detect_ats(pkt.url or "")
    if ats not in {"greenhouse", "ashby"}:
        return False, f"ATS not auto-submittable ({ats})"
    if not pkt.resume_a or not Path(pkt.resume_a).exists():
        return False, "missing tailored resume"
    return True, None


def _playwright_submit(
    *,
    ats: str,
    url: str,
    resume: Path,
    proof_dir: Path,
    company: str,
) -> tuple[bool, str | None, str, object]:
    """Submit via Playwright. Returns (success, needs_me, confirmation, raw_result)."""
    from .ashby_pw import submit_ashby_basic
    from .greenhouse_pw import submit_greenhouse_basic

    # Prefer short resumes/submit/Susmitha_<key>.docx when present.
    short = paths.ROOT / "resumes" / "submit" / f"Susmitha_{company.lower().replace(' ', '_')}.docx"
    resume_path = short if short.exists() else Path(resume)
    if ats == "greenhouse":
        res = submit_greenhouse_basic(
            url=url,
            resume=resume_path,
            proof_dir=proof_dir,
            company=company,
            require_window=True,
            fill_only=False,
        )
    elif ats == "ashby":
        res = submit_ashby_basic(
            url=url,
            resume=resume_path,
            proof_dir=proof_dir,
            company=company,
            require_window=True,
            fill_only=False,
        )
    else:
        return False, f"unsupported ats={ats}", "", None
    return bool(res.success and not res.needs_me), res.needs_me, res.confirmation_text or "", res


def _load_resume():
    resume_path = find_base_resume()
    if resume_path is None:
        raise FileNotFoundError("Base resume missing under resumes/base/")
    resume = load_base_resume(resume_path)
    if not resume.name:
        resume.name = "SUSMITHA CHOWDARY"
    if not resume.contact_lines:
        resume.contact_lines = [
            "dsusmitha55@gmail.com | 9132073787",
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


def _report_day() -> str:
    """Evening prepare-only runs target tomorrow's CT apply day after noon."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("America/Chicago"))
    if check_apply_window().open:
        return now.date().isoformat()
    if now.hour >= 12:
        return (now.date() + timedelta(days=1)).isoformat()
    return now.date().isoformat()


def run_daily(*, day: str | None = None, dry: bool = False) -> dict:
    """Orchestrate one daily cycle.

    dry=True: never claim submits; always prepare/hunt/report only.
    Outside window or missing salary: prepare only + needs-me.
    Actual browser submits happen via computer-use follow-up using the submit kit;
    this function records readiness and proof when provided.
    """
    day = day or _report_day()
    window = check_apply_window()
    salary = salary_from_memory()
    ready_payload = readiness_report(day=day)
    hunt = hunt_all()
    gate = evaluate_curve_gate()
    gate_report = write_gate_report(day=day)
    ready_items = evaluate_all_ready_submits()
    ready_report = write_ready_submits_report(day=day)

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
            "Salary expectations number missing for forms that ask (Curve Dental). "
            "Clera + Bayesian + Life360 forms have no salary field — submit those in-window without it. "
            "Unlock Curve via `python3 -m agent set-salary <n>` after Susmitha replies."
        )

    # Process new hunt hits into dry-run packets for later / in-window auto-submit
    resume = _load_resume()
    applied_urls = load_applied_urls()
    hunt_auto: list[JobPacket] = []
    daily_limit = 25
    try:
        if paths.STATE.exists():
            import re as _re

            m = _re.search(r"(?m)^- daily_limit:\s*(\d+)", paths.STATE.read_text(encoding="utf-8"))
            if m:
                daily_limit = int(m.group(1))
    except Exception:
        pass

    for job in hunt:
        if CURVE_URL in (job.url or ""):
            continue
        company_l = (job.company or "").lower()
        url_l = (job.url or "").lower()
        if url_already_applied(job.url or job.apply_url or "", applied_urls):
            skipped.append(f"{job.company} / {job.title} — already applied")
            continue
        if "keebo" in url_l or company_l == "keebo":
            skipped.append(f"{job.company} / {job.title} — visa support will not be provided")
            append_applied_index(job.company, job.title, job.url, "skipped", day=day)
            continue
        # Company ATS only — skip contractor marketplaces / aggregator apply links
        if any(
            x in url_l or x in company_l
            for x in ("lemon.io", "remotive.com", "himalayas.app", "arbeitnow.com", "weworkremotely")
        ):
            skipped.append(f"{job.company} / {job.title} — not company ATS (marketplace/aggregator)")
            continue
        # Standing exclusion: never apply to Citi / Optum / UHG (incl. recruiter postings)
        excluded_blob = f"{company_l} {url_l} {job.title or ''}".lower()
        if any(
            x in excluded_blob
            for x in (
                "citi",
                "citigroup",
                "citibank",
                "optum",
                "unitedhealth",
                "united health",
                "uhg",
            )
        ):
            skipped.append(f"{job.company} / {job.title} — skipped: excluded company")
            append_applied_index(job.company, job.title, job.url, "skipped: excluded company", day=day)
            continue
        if "consumer edge" in company_l or "consumeredge" in url_l:
            skipped.append(f"{job.company} / {job.title} — 8+ years stretch / score << 7")
            continue
        if _seniority_blocked(job.title or ""):
            skipped.append(f"{job.company} / {job.title} — seniority skip (staff/principal/director/manager)")
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
            ok_auto, skip_why = _packet_auto_submitable(pkt)
            if ok_auto and window.open and not dry:
                hunt_auto.append(pkt)
                notes.append(
                    f"Queued in-window auto-submit: {pkt.company} / {pkt.role} (b={pkt.score_b})"
                )
            elif skip_why:
                needs_me.append(
                    f"{pkt.company} / {pkt.role} ≥7 but {skip_why}: {pkt.url}"
                )
            else:
                needs_me.append(
                    f"NEW ≥7 fit ready to apply when window open: {pkt.company} / {pkt.role} — {pkt.url}"
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
                    "status": "dry-run" if dry or not window.open else ("queued" if ok_auto else "needs me"),
                    "reason": (
                        "In-window auto-submit queued"
                        if ok_auto and window.open and not dry
                        else (skip_why or "Prepared; submit only in-window")
                    ),
                    "resume_file": str(pkt.resume_a or ""),
                    "catch_note_file": str(pkt.catch_note or ""),
                    "additions_verify": "; ".join(pkt.additions_flagged),
                    "interview_prep_file": str(pkt.interview_prep or ""),
                }
            )

    # SUBMIT_NOW: always refresh with prompts. Outside window / dry = prepare packet
    # for the next open window (do NOT delete — morning computer-use depends on it).
    submit_now = paths.REPORTS / day / "SUBMIT_NOW.md"
    live_submit = bool(window.open and not dry)
    lines = [
        f"# SUBMIT NOW — {day}",
        "",
        (
            "Window is OPEN. Submit company ATS only (never Easy Apply). Proof required."
            if live_submit
            else "PREPARE / frozen packet. Submit only 08:00–12:00 America/Chicago. Never Easy Apply."
        ),
        "",
        f"Ready-submits report: `{ready_report}`",
        "",
    ]
    any_prompt = False
    for item in ready_items:
        lines.append(f"## {item.company} — {item.role}")
        lines.append(f"- Ready now: **{item.ok}**")
        lines.append(f"- URL: {item.url}")
        lines.append(f"- Kit: `{item.kit}`")
        if item.blockers:
            lines.extend(["", "### Blockers", *[f"- {b}" for b in item.blockers]])
        if item.computer_use_prompt:
            any_prompt = True
            if live_submit and item.ok:
                notes.append(f"{item.company} READY TO SUBMIT — use prompt below; then proof.")
            lines.extend(
                [
                    "",
                    "### Computer-use prompt"
                    + ("" if (live_submit and item.ok) else " (use when window opens)"),
                    "```",
                    item.computer_use_prompt,
                    "```",
                    "",
                ]
            )
        else:
            lines.append("")
    if gate.ok and gate.computer_use_prompt:
        any_prompt = True
        if live_submit:
            notes.append(
                "Curve Dental READY TO SUBMIT — run computer-use with prompt from "
                f"{gate_report}; then `python3 -m agent proof`."
            )
        lines.extend(
            [
                "## Curve Dental (salary present)",
                f"- URL: {gate.url}",
                f"- Salary: {gate.salary}",
                f"- Gate report: {gate_report}",
                "",
                "### Computer-use prompt",
                "```",
                gate.computer_use_prompt,
                "```",
                "",
            ]
        )
    else:
        notes.append("Curve Dental queued — salary and/or other gate blockers remain.")
        lines.extend(
            [
                "## Curve Dental",
                f"- Blocked: {', '.join(gate.blockers) or '(unknown)'}",
                "",
            ]
        )
    if not live_submit:
        notes.append("Outside window or dry run — prepare only. Ready-submit prompts frozen in SUBMIT_NOW.")

    # In-window: Playwright submits for ready queue, then new ≥7 Greenhouse/Ashby hunt hits
    if live_submit:
        submitted_count = 0

        def _record_submit(company: str, role: str, url: str, proof: Path, ok: bool, needs: str | None, conf: str) -> None:
            nonlocal submitted_count
            if ok:
                applied.append(f"{company} / {role} — {url}")
                append_applied_index(company, role, url, "applied", day=day)
                notes.append(f"{company} submitted via Playwright; proof in {proof}")
                submitted_count += 1
                applied_urls.add(url.lower().rstrip("/"))
            elif needs:
                needs_me.append(f"{company}: {needs}")
                append_applied_index(company, role, url, "needs-me", day=day)
            else:
                unconfirmed.append(f"{company} / {role} — {url}")
                append_applied_index(company, role, url, "unconfirmed", day=day)

        for item in ready_items:
            if not item.ok:
                continue
            if submitted_count >= daily_limit:
                notes.append(f"Daily limit {daily_limit} reached — stopping ready-queue submits")
                break
            if url_already_applied(item.url, applied_urls):
                skipped.append(f"{item.company} / {item.role} — already applied")
                continue
            ats = (item.ats or detect_ats(item.url) or "").lower()
            if ats not in {"greenhouse", "ashby"}:
                needs_me.append(f"{item.company}: ATS {ats or 'unknown'} not auto-submittable — use kit/computer-use")
                continue
            proof = paths.APPLICATIONS / "applied" / day / f"{item.company}_{item.role}".replace(" ", "_")[:100]
            try:
                ok, needs, conf, _raw = _playwright_submit(
                    ats=ats,
                    url=item.url,
                    resume=Path(item.resume),
                    proof_dir=proof,
                    company=item.company,
                )
            except Exception as e:
                needs_me.append(f"{item.company} Playwright submit error: {e}")
                continue
            _record_submit(item.company, item.role, item.url, proof, ok, needs, conf)

        for pkt in hunt_auto:
            if submitted_count >= daily_limit:
                notes.append(f"Daily limit {daily_limit} reached — remaining hunt ≥7 stay queued/needs-me")
                break
            if url_already_applied(pkt.url, applied_urls):
                continue
            ats = detect_ats(pkt.url) or ""
            proof = (
                paths.APPLICATIONS
                / "applied"
                / day
                / f"{pkt.company}_{pkt.role}".replace(" ", "_")[:100]
            )
            try:
                ok, needs, conf, _raw = _playwright_submit(
                    ats=ats,
                    url=pkt.url,
                    resume=Path(pkt.resume_a),
                    proof_dir=proof,
                    company=pkt.company,
                )
            except Exception as e:
                needs_me.append(f"{pkt.company} Playwright submit error: {e}")
                continue
            _record_submit(pkt.company, pkt.role, pkt.url, proof, ok, needs, conf)

    if any_prompt or gate.blockers:
        submit_now.write_text("\n".join(lines), encoding="utf-8")
        # Mirror into needs-me kit folder for the first-applies runbook.
        kit_dir = paths.APPLICATIONS / "needs-me" / "2026-11-12"
        if kit_dir.exists():
            (kit_dir / "SUBMIT_NOW.md").write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "window_open": window.open,
        "salary": salary,
        "hunt_count": len(hunt),
        "curve_gate_ok": gate.ok,
        "curve_blockers": gate.blockers,
        "ready_submits": [
            {"company": i.company, "role": i.role, "ok": i.ok, "blockers": i.blockers, "url": i.url}
            for i in ready_items
        ],
        "ready": ready_payload.get("ready"),
        "applied": applied,
        "unconfirmed": unconfirmed,
        "skipped": skipped,
        "needs_me": needs_me,
        "notes": " | ".join(notes),
        "readiness_report": ready_payload.get("report"),
        "curve_gate_report": str(gate_report),
        "ready_submits_report": str(ready_report),
        "submit_now": str(submit_now) if submit_now.exists() else None,
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
