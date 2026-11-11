from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from . import paths


CSV_HEADER = [
    "date",
    "company",
    "role",
    "link",
    "score_original",
    "score_tailored",
    "score_with_additions",
    "top5_missing_keywords",
    "status",
    "reason",
    "resume_file",
    "catch_note_file",
    "additions_verify",
    "interview_prep_file",
]


def ensure_csv() -> Path:
    paths.LOGS.mkdir(parents=True, exist_ok=True)
    if not paths.APPLICATIONS_CSV.exists() or paths.APPLICATIONS_CSV.stat().st_size == 0:
        with paths.APPLICATIONS_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)
    return paths.APPLICATIONS_CSV


def append_log_row(row: dict) -> None:
    ensure_csv()
    with paths.APPLICATIONS_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writerow({k: row.get(k, "") for k in CSV_HEADER})


def write_catch_note(company: str, role: str, body: str, day: str | None = None) -> Path:
    day = day or date.today().isoformat()
    out_dir = paths.APPLICATIONS / "needs-me" / day
    # catch notes live with the job packet under reports as well
    out_dir = paths.REPORTS / day / "catch-notes"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = f"{company}_{role}".replace("/", "-").replace(" ", "_")[:80]
    path = out_dir / f"{safe}.md"
    path.write_text(body, encoding="utf-8")
    return path


def write_scorecard(company: str, role: str, body: str, day: str | None = None) -> Path:
    day = day or date.today().isoformat()
    out_dir = paths.REPORTS / day / "scorecards"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = f"{company}_{role}".replace("/", "-").replace(" ", "_")[:80]
    path = out_dir / f"{safe}.md"
    path.write_text(body, encoding="utf-8")
    return path


def write_interview_prep(company: str, role: str, body: str, day: str | None = None) -> Path:
    day = day or date.today().isoformat()
    out_dir = paths.INTERVIEW_PREP / day
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = f"{company}_{role}".replace("/", "-").replace(" ", "_")[:80]
    path = out_dir / f"{safe}.md"
    path.write_text(body, encoding="utf-8")
    return path


def append_applied_index(company: str, role: str, url: str, status: str, day: str | None = None) -> None:
    day = day or date.today().isoformat()
    paths.APPLIED_INDEX.parent.mkdir(parents=True, exist_ok=True)
    if not paths.APPLIED_INDEX.exists():
        paths.APPLIED_INDEX.write_text("# Applied / seen index\n\n## Entries\n", encoding="utf-8")
    with paths.APPLIED_INDEX.open("a", encoding="utf-8") as f:
        f.write(f"{day} | {company} | {role} | {url} | {status}\n")
