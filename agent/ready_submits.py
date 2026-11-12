from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths
from .job_search import _get_json, within_max_age
from .salary import salary_from_memory
from .window import check_apply_window, chicago_today


@dataclass
class ReadySubmit:
    key: str
    company: str
    role: str
    url: str
    resume: Path
    kit: Path
    needs_salary: bool
    ok: bool
    blockers: list[str]
    computer_use_prompt: str


CLERA = {
    "key": "clera",
    "company": "Clera",
    "role": "Senior Data Integration Engineer",
    "url": "https://jobs.ashbyhq.com/Clera/782c2049-c72a-4920-a278-e5b1ee6fd2b3",
    "ashby_org": "Clera",
    "ashby_id": "782c2049-c72a-4920-a278-e5b1ee6fd2b3",
    "resume_globs": [
        "*/Susmitha_clera_Senior_Data_Integration_Engineer.docx",
        "*/Susmitha_Clera_Senior_Data_Integration_Engineer.docx",
    ],
    "kit": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Clera_SUBMIT_KIT.md",
    "needs_salary": False,
    "prompt_extra": (
        "Fill exactly:\n"
        "- Name*: Susmitha Chowdary\n"
        "- Email*: Susmithachowdary67@gmail.com\n"
        "- Resume*: upload the .docx\n"
        "- LinkedIn*: https://www.linkedin.com/in/susmitha-dodla-a05ab92b8\n"
        "- Do you have work authorization to work in that country?*: Yes\n"
        "No salary field. No sponsorship field on this form.\n"
    ),
}

BAYESIAN = {
    "key": "bayesian",
    "company": "Bayesian Health",
    "role": "Software Engineer, Data & Analytics Platform",
    "url": "https://jobs.ashbyhq.com/bayesianhealth/3ea2fcfb-9a68-4b8d-a9aa-600a733ef655",
    "ashby_org": "bayesianhealth",
    "ashby_id": "3ea2fcfb-9a68-4b8d-a9aa-600a733ef655",
    "resume_globs": [
        "*/Susmitha_bayesianhealth_Software_Engineer_Data_Analytics_Platform.docx",
        "*/Susmitha_Bayesian_Health_Software_Engineer_Data_Analytics_Platform.docx",
    ],
    "kit": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Bayesian_Health_SUBMIT_KIT.md",
    "needs_salary": False,
    "prompt_extra": (
        "Fill exactly:\n"
        "- Name*: Susmitha Chowdary\n"
        "- Email*: Susmithachowdary67@gmail.com\n"
        "- Resume*: upload the .docx\n"
        "- Are you legally authorized to work in the United States?*: Yes\n"
        "- Do you now or will you in the future require employer sponsorship?*: No\n"
        "- Why are you a good fit for this role?*: paste the Why good fit draft from the submit kit "
        "(resume facts only; do not invent dbt/BI ownership)\n"
        "- LinkedIn: https://www.linkedin.com/in/susmitha-dodla-a05ab92b8\n"
        "- Years with BI tools: 0\n"
        "- Years developing data/analytics platform in production: 5\n"
        "- 2-3 most proficient languages: Python, SQL, PySpark\n"
        "- Location: Austin, TX\n"
        "No salary field on this form.\n"
    ),
}


def _newest_resume(globs: list[str]) -> Path | None:
    found: list[Path] = []
    for g in globs:
        found.extend(paths.RESUMES_TAILORED.glob(g))
    if not found:
        return None
    return sorted(found, reverse=True)[0]


def _ashby_still_open(org: str, job_id: str) -> tuple[bool, str | None, str | None]:
    """Return (open_and_fresh, published_at, error)."""
    try:
        data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
    except Exception as e:
        return False, None, str(e)
    for j in data.get("jobs") or []:
        url = j.get("jobUrl") or ""
        jid = (j.get("id") or "")
        if job_id in url or jid == job_id:
            posted = j.get("publishedAt") or j.get("updatedAt")
            if not within_max_age(posted, max_age_days=4):
                return False, posted, f"age fail-closed: publishedAt={posted}"
            return True, posted, None
    return False, None, "job id not found on Ashby board (possibly closed)"


def _build_prompt(spec: dict, resume: Path, salary: str | None) -> str:
    day = chicago_today().isoformat()
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in f"{spec['company']}_{spec['role']}")
    safe = safe.strip().replace(" ", "_")[:120]
    proof = f"applications/applied/{day}/{safe}"
    short = paths.ROOT / "resumes" / "submit" / f"Susmitha_{spec['key']}.docx"
    resume_line = str(short if short.exists() else resume)
    salary_line = ""
    if spec["needs_salary"]:
        salary_line = f"Salary expectations*: {salary}\n"
    return f"""
SUBMIT {spec['company']} — {spec['role']} on company ATS. REAL submit authorized by Susmitha.
Kit: {spec['kit']}

URL: {spec['url']}
Window: must still be 08:00–12:00 America/Chicago. If outside, STOP.
Resume file on disk (prefer short path): {resume_line}
Fallback resume: {resume}
{salary_line}
{spec['prompt_extra']}
Click Submit Application ONCE.
Save proof under {proof}/ and /opt/cursor/artifacts/{spec['key']}_confirmation.png
Write confirmation.txt with on-screen confirmation text.
If CAPTCHA/login/unexpected required field/error: STOP needs-me. Do not invent answers.
""".strip()


def evaluate_ready_submit(spec: dict) -> ReadySubmit:
    blockers: list[str] = []
    window = check_apply_window()
    if not window.open:
        blockers.append(window.reason)

    salary = salary_from_memory()
    if spec["needs_salary"] and not salary:
        blockers.append("Salary expectations number missing in Memory/FORM_ANSWERS")

    resume = _newest_resume(spec["resume_globs"])
    if resume is None or not resume.exists():
        blockers.append(f"Missing tailored resume for {spec['company']}")
        resume = Path("(missing)")

    kit = Path(spec["kit"])
    if not kit.exists():
        blockers.append(f"Missing submit kit: {kit}")

    open_ok, posted, err = _ashby_still_open(spec["ashby_org"], spec["ashby_id"])
    if err and not open_ok:
        blockers.append(f"{spec['company']} verification failed: {err}")
    elif not open_ok:
        blockers.append(f"{spec['company']} not open/fresh: {err or posted}")

    prompt = ""
    if not blockers:
        prompt = _build_prompt(spec, resume, salary)

    return ReadySubmit(
        key=spec["key"],
        company=spec["company"],
        role=spec["role"],
        url=spec["url"],
        resume=resume,
        kit=kit,
        needs_salary=bool(spec["needs_salary"]),
        ok=not blockers,
        blockers=blockers,
        computer_use_prompt=prompt,
    )


def evaluate_all_ready_submits() -> list[ReadySubmit]:
    return [evaluate_ready_submit(CLERA), evaluate_ready_submit(BAYESIAN)]


def packet_ready_except_window(item: ReadySubmit) -> bool:
    """True when the only blocker is the CT apply window."""
    if item.ok:
        return True
    return bool(item.blockers) and all("Outside window" in b or "08:00" in b for b in item.blockers)


def write_ready_submits_report(day: str | None = None) -> Path:
    day = day or chicago_today().isoformat()
    items = evaluate_all_ready_submits()
    out_dir = paths.REPORTS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "READY_SUBMITS.md"
    lines = [
        f"# Ready submits — {day}",
        "",
        "Jobs that can be computer-use submitted when the CT window is open.",
        "",
    ]
    for item in items:
        lines += [
            f"## {item.company} — {item.role}",
            f"- Ready: **{item.ok}**",
            f"- Needs salary: **{item.needs_salary}**",
            f"- URL: {item.url}",
            f"- Resume: `{item.resume}`",
            f"- Kit: `{item.kit}`",
            "## Blockers" if item.blockers else "## Blockers",
            *([f"- {b}" for b in item.blockers] or ["- (none)"]),
            "",
            "### Computer-use prompt" if item.ok else "### Computer-use prompt",
            "```",
            item.computer_use_prompt or "(blocked)",
            "```",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "READY_SUBMITS.json").write_text(
        json.dumps(
            [
                {
                    **{k: (str(v) if isinstance(v, Path) else v) for k, v in asdict(i).items()}
                }
                for i in items
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
