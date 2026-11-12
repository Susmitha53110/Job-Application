from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths
from .job_search import _get_json, within_max_age
from .morning_run import _curve_override
from .salary import salary_from_memory
from .window import check_apply_window, chicago_today


CURVE_JOB_ID = "81161b01-ae38-49d2-9ca8-3b618d31c394"
CURVE_URL = f"https://ats.rippling.com/curve-dental/jobs/{CURVE_JOB_ID}"
SUBMIT_KIT = paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Curve_Dental_SUBMIT_KIT.md"


def _curve_resume_a() -> Path:
    """Prefer newest tailored Curve resume (a)."""
    candidates = sorted(
        paths.RESUMES_TAILORED.glob("*/Susmitha_Curve_Dental_Data_Engineer.docx"),
        reverse=True,
    )
    return candidates[0] if candidates else paths.RESUMES_TAILORED / "2026-11-12" / "Susmitha_Curve_Dental_Data_Engineer.docx"


@dataclass
class CurveGate:
    ok: bool
    blockers: list[str]
    salary: str | None
    created_on: str | None
    url: str
    computer_use_prompt: str


PLATFORM_STORY = (
    "At Optum I own production Azure Data Factory + Databricks ingestion into ADLS Gen2 / "
    "Delta Lake bronze-silver-gold for claims, eligibility, and provider feeds, and deliver "
    "Snowflake loads via external stages, COPY INTO, and MERGE for analytics dimensions. I cut "
    "new-source onboarding from ~2 weeks to ~4 days with a config-driven PySpark framework, "
    "reduced a claims workflow from ~2 hours to 75 minutes, and raised scheduled pipeline "
    "success from ~97% to 99.5% with dependency checks, bounded retries, and idempotent "
    "backfills. Honest gap if asked: JD prefers 2+ years production Snowflake and dbt/Fivetran; "
    "my Snowflake production ownership is since May 2025, and I do not claim production "
    "dbt/Fivetran ownership."
)


def build_computer_use_prompt(salary: str) -> str:
    from .window import chicago_today

    resume = str(_curve_resume_a())
    day = chicago_today().isoformat()
    proof_dir = f"applications/applied/{day}/Curve_Dental_Data_Engineer"
    return f"""
SUBMIT Curve Dental Data Engineer on Rippling ATS. REAL submit authorized by Susmitha.
Field map: applications/needs-me/2026-11-12/CURVE_FORM_MAP.md + Curve_Dental_SUBMIT_KIT.md

URL: {CURVE_URL}
Window: must still be 08:00–12:00 America/Chicago. If outside, STOP without submitting.
If salary is NEEDS_ME or blank, STOP without submitting.
Resume file on disk: {resume}

Fill in this exact order (no login/CAPTCHA expected):
1) Resume*: upload the .docx above (.doc/.docx/.pdf accepted)
2) First name*: Susmitha
3) Last name*: Chowdary
4) Email*: Susmithachowdary67@gmail.com
5) Pronouns: skip
6) Current company: Optum
7) Phone number*: +1 9132073787
8) Location*: Austin (use Austin, TX if autocomplete requires a match)
9) Cover letter: skip
10) Will you now or in the future require sponsorship to work in the US?*: No
11) How many years of related experience do you have?*: 5
12) Do you have a home office, with reliable internet, that you can work from?*: Yes
13) Describe a data platform you built or significantly improved...*: {PLATFORM_STORY}
14) What are your salary expectations for this role?*: {salary}
15) How did you hear about, or where did you find, this job posting?*: Company careers / Rippling ATS research
16) Gender (voluntary): Choose not to disclose
17) Please identify your race (voluntary): Choose not to disclose
18) Are you Hispanic/Latino? (voluntary): Choose not to disclose
19) Veteran Status (voluntary): Choose not to disclose
20) Text message consent*: select "No - I do not consent to receiving text messages"

Click Apply ONCE.
Save proof under {proof_dir}/ and /opt/cursor/artifacts/curve_dental_confirmation.png
Also write confirmation.txt with the on-screen confirmation text.
If CAPTCHA/login/unexpected required field/error: STOP needs-me. Do not invent answers.
""".strip()


def evaluate_curve_gate() -> CurveGate:
    blockers: list[str] = []
    window = check_apply_window()
    if not window.open:
        blockers.append(window.reason)
    salary = salary_from_memory()
    if not salary:
        blockers.append("Salary expectations number missing in Memory/FORM_ANSWERS")
    # Score override is optional backup; honest score is now ≥7 after prose JD fix.
    # Keep override flag as non-blocking documentation only.
    resume_a = _curve_resume_a()
    if not resume_a.exists():
        blockers.append(f"Missing tailored resume: {resume_a}")
    if not SUBMIT_KIT.exists():
        blockers.append(f"Missing submit kit: {SUBMIT_KIT}")

    created_on = None
    try:
        detail = _get_json(
            f"https://ats.rippling.com/api/v2/board/curve-dental/jobs/{CURVE_JOB_ID}"
        )
        created_on = detail.get("createdOn")
        if not within_max_age(created_on):
            blockers.append(f"Curve posting age fail-closed: createdOn={created_on}")
        if not detail.get("url"):
            blockers.append("Curve job URL missing from Rippling API (possibly closed)")
    except Exception as e:
        blockers.append(f"Curve job verification failed: {e}")

    salary_for_prompt = salary or "NEEDS_ME"
    prompt = build_computer_use_prompt(salary_for_prompt)
    return CurveGate(
        ok=not blockers,
        blockers=blockers,
        salary=salary,
        created_on=created_on,
        url=CURVE_URL,
        computer_use_prompt=prompt if not blockers else "",
    )


def write_gate_report(day: str | None = None) -> Path:
    day = day or chicago_today().isoformat()
    gate = evaluate_curve_gate()
    out_dir = paths.REPORTS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "CURVE_GATE.md"
    lines = [
        f"# Curve Dental submit gate — {day}",
        "",
        f"- Ready: **{gate.ok}**",
        f"- Salary: **{gate.salary or 'MISSING'}**",
        f"- createdOn: **{gate.created_on}**",
        f"- URL: {gate.url}",
        "",
        "## Blockers",
        *([f"- {b}" for b in gate.blockers] or ["- (none)"]),
        "",
        "## Computer-use prompt (only if Ready)",
        "```",
        gate.computer_use_prompt or "(blocked)",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    # also machine-readable
    (out_dir / "CURVE_GATE.json").write_text(
        json.dumps({k: getattr(gate, k) for k in gate.__dataclass_fields__}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    print(json.dumps(asdict(evaluate_curve_gate()), indent=2))
    print("report", write_gate_report())
