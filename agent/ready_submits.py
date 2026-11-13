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
    ats: str = "unknown"


MONGODB = {
    "key": "mongodb",
    "company": "MongoDB",
    "role": "Senior Software Engineer, Database Integration & Observability",
    "url": "https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433",
    "ats": "greenhouse",
    "gh_board": "mongodb",
    "gh_id": 8352433,
    "resume_globs": [
        "*/Susmitha_MongoDB_Senior_Software_Engineer_Database_Integration_Observability.docx",
    ],
    "kit": paths.APPLICATIONS / "ready" / "2026-11-14" / "MongoDB_SUBMIT_KIT.md",
    "needs_salary": False,
    "prompt_extra": (
        "Use Greenhouse embed URL (not mongodb.com careers wrapper).\n"
        "Fill exactly:\n"
        "- First Name: Susmitha / Last Name: Chowdary / Preferred Name: Susmitha\n"
        "- Email: dsusmitha55@gmail.com / Phone: 9132073787\n"
        "- Country: United States / Location (City): Austin\n"
        "- Resume: upload resumes/submit/Susmitha_mongodb.docx\n"
        "- LinkedIn: blank; if forced N/A / Website: blank\n"
        "- How did you learn about this job?: Company website (or closest)\n"
        "- Culture/careers content / similar-job alerts: No or skip if optional\n"
        "- Will you now or in the future require employment sponsorship?: No\n"
        "- Have you ever worked at MongoDB before?: No\n"
        "- EEO required: Gender Female / Gender Identity Female / Race Asian / "
        "Hispanic No / Veteran I am not a protected veteran / "
        "Disability No, I don't have a disability\n"
        "- Check demographic survey consent box (required)\n"
        "If email security code appears: STOP needs-me and ask Susmitha to paste the 8-char code "
        "(Gmail declined). If CAPTCHA/unexpected required field: STOP needs-me.\n"
    ),
}

MACHINIFY = {
    "key": "machinify",
    "company": "Machinify",
    "role": "Senior Data Engineer",
    "url": "https://job-boards.greenhouse.io/machinifyinc/jobs/4478208009",
    "ats": "greenhouse",
    "gh_board": "machinifyinc",
    "gh_id": 4478208009,
    "resume_globs": [
        "*/Susmitha_Machinify_Senior_Data_Engineer*.docx",
    ],
    "kit": paths.APPLICATIONS / "ready" / "2026-11-14" / "Machinify_SUBMIT_KIT.md",
    "needs_salary": False,
    "prompt_extra": (
        "Greenhouse form. Fill exactly:\n"
        "- First Name: Susmitha / Last Name: Chowdary / Preferred First Name: Susmitha\n"
        "- Email: dsusmitha55@gmail.com / Phone + Phone Number: 9132073787\n"
        "- Country: United States\n"
        "- Resume: upload resumes/submit/Susmitha_machinify.docx\n"
        "- LinkedIn Profile* (required): N/A\n"
        "- Website: blank\n"
        "- EEO optional if shown: Female / Hispanic No / Asian / not protected veteran\n"
        "Enterprise reCAPTCHA present — if email security code / captcha blocks submit: "
        "STOP needs-me (paste code; Gmail declined). Unexpected required field: STOP needs-me.\n"
    ),
}

MUX = {
    "key": "mux",
    "company": "mux",
    "role": "Senior Data Engineer",
    "url": "https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe",
    "ats": "ashby",
    "ashby_org": "mux",
    "ashby_id": "bf4007f4-3610-4a67-acd6-0e7a7f11dbbe",
    "resume_globs": [
        "*/Susmitha_mux_Senior_Data_Engineer.docx",
    ],
    "kit": paths.APPLICATIONS / "ready" / "2026-11-14" / "mux_SUBMIT_KIT.md",
    "needs_salary": False,
    "prompt_extra": (
        "Ashby form. Fill exactly:\n"
        "- Name: Susmitha Chowdary\n"
        "- Email: dsusmitha55@gmail.com\n"
        "- Resume: upload resumes/submit/Susmitha_mux.docx\n"
        "- LinkedIn: blank; if required N/A\n"
        "- Why Mux fit: short honest DE/platform note from submit kit (no invented Mux experience)\n"
        "- How did you hear about us?: Company website\n"
        "- Eligible to work in the US?: Yes\n"
        "- Sponsorship for employment visa?: No\n"
        "- Spell the number '12': twelve\n"
        "- EEO: Female / Asian (Not Hispanic or Latino) / I am not a protected veteran\n"
        "If CAPTCHA/unexpected required field: STOP needs-me.\n"
    ),
}

VELOSIO = {
    "key": "velosio",
    "company": "Velosio",
    "role": "Data Engineer",
    "url": "https://careers.velosio.com/jobs/3162",
    "ats": "jsonld",
    "jsonld_url": "https://careers.velosio.com/jobs/3162",
    "resume_globs": [
        "*/Susmitha_Velosio_Data_Engineer.docx",
    ],
    "kit": paths.APPLICATIONS / "needs-me" / "2026-11-12" / "Velosio_SUBMIT_KIT.md",
    "needs_salary": False,
    # apply_url redirects to careers-velosio.icims.com/.../login — Susmitha must sign in herself.
    "hard_blockers": [
        "Velosio iCIMS apply requires candidate login (careers-velosio.icims.com/jobs/3162/login) — STOP needs-me; never create accounts or use Indeed Easy Apply"
    ],
    "prompt_extra": (
        "DO NOT auto-submit. iCIMS login required. Susmitha must sign in herself.\n"
        "Never Indeed Easy Apply.\n"
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
            if not within_max_age(posted, max_age_days=10):
                return False, posted, f"age fail-closed: publishedAt={posted}"
            return True, posted, None
    return False, None, "job id not found on Ashby board (possibly closed)"


def _greenhouse_still_open(board: str, job_id: int | str) -> tuple[bool, str | None, str | None]:
    """Return (open_and_fresh, first_published, error) for a Greenhouse job id."""
    try:
        detail = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}")
    except Exception as e:
        return False, None, str(e)
    posted = detail.get("first_published") or detail.get("updated_at")
    if not within_max_age(posted, max_age_days=10):
        return False, posted, f"age fail-closed: first_published={posted}"
    return True, posted, None


def _jsonld_still_open(page_url: str) -> tuple[bool, str | None, str | None]:
    """Fetch a careers page and require JobPosting JSON-LD datePosted ≤10d."""
    import json
    import re
    import urllib.request

    try:
        req = urllib.request.Request(page_url, headers={"User-Agent": "SusmithaJobAgent/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as e:
        return False, None, str(e)
    m = re.search(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    )
    if not m:
        return False, None, "no JSON-LD JobPosting on page"
    try:
        data = json.loads(m.group(1))
    except Exception as e:
        return False, None, f"JSON-LD parse failed: {e}"
    if isinstance(data, list):
        data = next((x for x in data if isinstance(x, dict) and x.get("@type") == "JobPosting"), {})
    posted = data.get("datePosted")
    if not within_max_age(posted, max_age_days=10):
        return False, posted, f"age fail-closed: datePosted={posted}"
    return True, posted, None


def _proof_apply_day() -> str:
    """Calendar day used for applications/applied/<day>/ when preparing overnight."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("America/Chicago"))
    if check_apply_window().open:
        return now.date().isoformat()
    if now.hour >= 12:
        return (now.date() + timedelta(days=1)).isoformat()
    return now.date().isoformat()


def _build_prompt(spec: dict, resume: Path, salary: str | None) -> str:
    day = _proof_apply_day()
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

    for hb in spec.get("hard_blockers") or []:
        blockers.append(hb)

    # Live Greenhouse question preflight (catches multi-year no-sponsorship traps).
    if (spec.get("ats") or "") == "greenhouse" and spec.get("gh_board") and spec.get("gh_id"):
        try:
            from .form_preflight import preflight_greenhouse

            pf = preflight_greenhouse(spec["gh_board"], spec["gh_id"])
            for b in pf.blockers:
                if b not in blockers:
                    blockers.append(b)
        except Exception as e:
            blockers.append(f"Greenhouse preflight error: {e}")

    resume = _newest_resume(spec["resume_globs"])
    if resume is None or not resume.exists():
        blockers.append(f"Missing tailored resume for {spec['company']}")
        resume = Path("(missing)")

    kit = Path(spec["kit"])
    if not kit.exists():
        blockers.append(f"Missing submit kit: {kit}")

    ats = spec.get("ats") or "ashby"
    if ats == "ashby":
        open_ok, posted, err = _ashby_still_open(spec["ashby_org"], spec["ashby_id"])
    elif ats == "greenhouse":
        open_ok, posted, err = _greenhouse_still_open(spec["gh_board"], spec["gh_id"])
    elif ats == "jsonld":
        open_ok, posted, err = _jsonld_still_open(spec.get("jsonld_url") or spec["url"])
    else:
        open_ok, posted, err = False, None, f"unknown ats={ats}"
    if err and not open_ok:
        blockers.append(f"{spec['company']} verification failed: {err}")
    elif not open_ok:
        blockers.append(f"{spec['company']} not open/fresh: {err or posted}")

    # Keep the full computer-use prompt even when the only blocker is the CT window,
    # so overnight / 07:00 prep handoffs are usable the moment the window opens.
    window_only = bool(blockers) and all(
        ("Outside window" in b) or ("08:00" in b) for b in blockers
    )
    prompt = ""
    if (not blockers or window_only) and resume != Path("(missing)"):
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
        ats=str(spec.get("ats") or ats or "unknown"),
    )


def evaluate_all_ready_submits() -> list[ReadySubmit]:
    # 2026-11-14 morning queue. Already-applied (BetterHelp/Clera/Bayesian/Life360/Curve) removed.
    # Velosio/Natera/lumin-digital: needs-me — not auto-queued.
    return [
        evaluate_ready_submit(MONGODB),
        evaluate_ready_submit(MUX),
        evaluate_ready_submit(MACHINIFY),
    ]


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
            "### Computer-use prompt"
            + (" (ready when window opens)" if (not item.ok and item.computer_use_prompt) else ""),
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
