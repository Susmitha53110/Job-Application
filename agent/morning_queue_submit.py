"""Submit prepared morning-queue kits at 08:00 CT (window-gated).

Reads applications/ready/<day>/README.md + SUBMIT_KIT.md files, or the
hardcoded FALLBACK_QUEUE for 2026-11-15. Never Easy Apply. Stops on needs-me.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import paths
from .ashby_pw import submit_ashby_basic
from .greenhouse_pw import submit_greenhouse_basic
from .log_writer import append_applied_index, load_applied_urls, url_already_applied
from .window import check_apply_window, chicago_today


LINKEDIN = "https://www.linkedin.com/in/susmitha-dodla-a05ab92b8"
EMAIL = "dsusmitha55@gmail.com"
PHONE = "9132073787"
NAME = "Susmitha Chowdary"


@dataclass
class QueueItem:
    key: str
    company: str
    role: str
    url: str
    ats: str  # greenhouse | ashby
    resume: Path


# Authoritative 2026-11-15 order (also in reports/.../MORNING_QUEUE.md)
FALLBACK_QUEUE: list[dict] = [
    {
        "key": "xAI",
        "company": "xAI",
        "role": "Analytics Engineer (X)",
        "url": "https://job-boards.greenhouse.io/xai/jobs/5286889007",
        "ats": "greenhouse",
        "resume": "resumes/submit/Susmitha_xai_2026-11-15.docx",
    },
    {
        "key": "Verkada",
        "company": "Verkada",
        "role": "Senior Software Engineer, Business Systems - Data Trust",
        "url": "https://job-boards.greenhouse.io/verkada/jobs/5264711007",
        "ats": "greenhouse",
        "resume": "resumes/submit/Susmitha_verkada_2026-11-15.docx",
    },
    {
        "key": "Abnormal",
        "company": "Abnormal",
        "role": "Software Engineer I, Data Platforms",
        "url": "https://job-boards.greenhouse.io/embed/job_app?for=abnormalsecurity&token=8196352003",
        "ats": "greenhouse",
        "resume": "resumes/submit/Susmitha_abnormal_2026-11-15.docx",
    },
    {
        "key": "Merge",
        "company": "Merge",
        "role": "Analytics Engineer",
        "url": "https://jobs.ashbyhq.com/merge/fbb35f9d-d38c-4187-8811-85355a3929dd",
        "ats": "ashby",
        "resume": "resumes/submit/Susmitha_merge_2026-11-15.docx",
    },
    {
        "key": "SpotOn",
        "company": "SpotOn",
        "role": "Senior Analytics Platform Engineer",
        "url": "https://jobs.ashbyhq.com/spoton/bb2d12c6-859d-459e-96f8-489c2bfd6681",
        "ats": "ashby",
        "resume": "resumes/submit/Susmitha_spoton_2026-11-15.docx",
    },
    {
        "key": "Clera",
        "company": "Clera",
        "role": "Senior Data Engineer",
        "url": "https://jobs.ashbyhq.com/Clera/0c1db99d-2e28-4277-87e2-c4d2a6f17b44",
        "ats": "ashby",
        "resume": "resumes/submit/Susmitha_clera_2026-11-15.docx",
    },
    {
        "key": "BranchInsurance",
        "company": "BranchInsurance",
        "role": "Analytics Engineer II",
        "url": "https://jobs.ashbyhq.com/BranchInsurance/728e3815-8d03-40ca-8f6f-86cef305965b",
        "ats": "ashby",
        "resume": "resumes/submit/Susmitha_branchinsurance_2026-11-15.docx",
    },
]


def _parse_kits(day: str) -> list[QueueItem]:
    ready = paths.APPLICATIONS / "ready" / day
    items: list[QueueItem] = []
    if not ready.exists():
        return items
    for kit in sorted(ready.glob("*_SUBMIT_KIT.md")):
        text = kit.read_text(encoding="utf-8")
        url_m = re.search(r"- URL:\s*(\S+)", text)
        resume_m = re.search(r"- Resume \(tailored b\):\s*`([^`]+)`", text)
        head_m = re.search(r"# Submit kit —\s*(.+?)\s*/\s*(.+)\s*$", text, re.M)
        if not (url_m and head_m):
            continue
        company, role = head_m.group(1).strip(), head_m.group(2).strip()
        url = url_m.group(1).strip()
        resume = Path(resume_m.group(1)) if resume_m else Path()
        if not resume.exists():
            # try resumes/submit basename
            alt = Path("resumes/submit") / resume.name if resume.name else Path()
            resume = alt if alt.exists() else resume
        ats = "ashby" if "ashbyhq.com" in url else "greenhouse"
        items.append(
            QueueItem(
                key=kit.stem.replace("_SUBMIT_KIT", ""),
                company=company,
                role=role,
                url=url,
                ats=ats,
                resume=resume,
            )
        )
    return items


def load_queue(day: str | None = None) -> list[QueueItem]:
    day = day or chicago_today().isoformat()
    parsed = _parse_kits(day)
    # Prefer FALLBACK_QUEUE order (xAI first — age edge); overlay kit metadata when present.
    by_url = {p.url.rstrip("/").lower(): p for p in parsed}
    by_key = {p.key.lower(): p for p in parsed}
    out: list[QueueItem] = []
    seen: set[str] = set()
    for row in FALLBACK_QUEUE:
        hit = by_url.get(row["url"].rstrip("/").lower()) or by_key.get(row["key"].lower())
        item = hit or QueueItem(
            key=row["key"],
            company=row["company"],
            role=row["role"],
            url=row["url"],
            ats=row["ats"],
            resume=Path(row["resume"]),
        )
        # Always prefer canonical URL/resume from FALLBACK when kit parse drifts
        if not item.resume.exists():
            item.resume = Path(row["resume"])
        if row["url"] and (not item.url or "ashby" in row["ats"] or "greenhouse" in row["ats"]):
            item.url = row["url"]
            item.ats = row["ats"]
        out.append(item)
        seen.add(item.url.rstrip("/").lower())
    for p in parsed:
        if p.url.rstrip("/").lower() not in seen:
            out.append(p)
    return out


def submit_queue(*, day: str | None = None, dry: bool = False, limit: int | None = None) -> dict:
    day = day or chicago_today().isoformat()
    window = check_apply_window()
    if not window.open and not dry:
        return {"ok": False, "reason": window.reason, "results": []}

    applied = load_applied_urls()
    results = []
    for i, item in enumerate(load_queue(day)):
        if limit is not None and i >= limit:
            break
        if url_already_applied(item.url, applied):
            results.append({"company": item.company, "role": item.role, "status": "skip_already_applied"})
            continue
        if not item.resume.exists():
            results.append(
                {
                    "company": item.company,
                    "role": item.role,
                    "status": "needs-me",
                    "detail": f"missing resume {item.resume}",
                }
            )
            continue
        safe = re.sub(r"[^\w\-]+", "_", f"{item.company}_{item.role}")[:100]
        proof = paths.APPLICATIONS / "applied" / day / safe
        proof.mkdir(parents=True, exist_ok=True)
        if dry:
            results.append({"company": item.company, "role": item.role, "status": "dry", "url": item.url})
            continue
        if item.ats == "ashby":
            r = submit_ashby_basic(
                url=item.url,
                resume=item.resume,
                proof_dir=proof,
                company=item.company,
                name=NAME,
                email=EMAIL,
                phone=PHONE,
                linkedin=LINKEDIN,
                require_window=True,
            )
            ok, needs, conf = r.success, r.needs_me, r.confirmation_text
        else:
            r = submit_greenhouse_basic(
                url=item.url,
                resume=item.resume,
                proof_dir=proof,
                company=item.company,
                email=EMAIL,
                phone=PHONE,
                linkedin=LINKEDIN,
                require_window=True,
            )
            ok, needs, conf = r.success, r.needs_me, r.confirmation_text
        if ok:
            append_applied_index(item.company, item.role, item.url, "applied", day=day)
            applied.add(item.url.lower().rstrip("/"))
            results.append({"company": item.company, "role": item.role, "status": "applied", "conf": (conf or "")[:200]})
        elif needs:
            (proof / "NEEDS_ME.txt").write_text(str(needs), encoding="utf-8")
            append_applied_index(item.company, item.role, item.url, "needs-me", day=day)
            results.append({"company": item.company, "role": item.role, "status": "needs-me", "detail": needs})
        else:
            append_applied_index(item.company, item.role, item.url, "unconfirmed", day=day)
            results.append({"company": item.company, "role": item.role, "status": "unconfirmed"})
    return {"ok": True, "day": day, "results": results}


if __name__ == "__main__":
    import json
    import sys

    dry = "--dry" in sys.argv
    out = submit_queue(dry=dry)
    print(json.dumps(out, indent=2))
