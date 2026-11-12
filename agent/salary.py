from __future__ import annotations

import re
from pathlib import Path

from . import paths


_LINE = re.compile(
    r"(?im)^(?:[-*]\s*)?(?:salary expectations?(?: number)?|expected salary|salary_expectation)\s*[:=]\s*\$?\s*([0-9]{2,3}(?:,?[0-9]{3})?)\b"
)
_TABLE = re.compile(
    r"(?im)^\|\s*Salary expectations\s*\|\s*\$?\s*([0-9]{2,3}(?:,?[0-9]{3})?)\s*\|"
)


def parse_salary_from_text(blob: str) -> str | None:
    """Parse an explicit salary number. Ignores NEEDS ME placeholders."""
    for pat in (_TABLE, _LINE):
        for m in pat.finditer(blob):
            # Skip if the matched line still says NEEDS ME nearby
            line = blob[m.start() : blob.find("\n", m.start())]
            if re.search(r"NEEDS\s*ME", line, re.I):
                continue
            return m.group(1).replace(",", "")
    return None


_BARE_AMOUNT = re.compile(r"(?m)^\s*\$?\s*([0-9]{5,6}|[0-9]{2,3},[0-9]{3})\s*$")


def ingest_salary_reply_file() -> str | None:
    """If Susmitha drops a number into SALARY_REPLY.md/.txt, persist it via set_salary."""
    for name in ("SALARY_REPLY.md", "SALARY_REPLY.txt"):
        path = paths.APPLICATIONS / "needs-me" / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text or re.search(r"NEEDS\s*ME", text, re.I):
            continue
        amount = parse_salary_from_text(text)
        if not amount:
            m = _BARE_AMOUNT.search(text)
            if m:
                amount = m.group(1).replace(",", "")
        if not amount:
            continue
        # Already set to same value — no-op
        existing = _salary_from_authoritative()
        if existing == amount:
            return amount
        set_salary(amount)
        return amount
    return None


def _salary_from_authoritative() -> str | None:
    """Return salary only from authoritative Memory fields — never from example docs."""
    # 1) STATE explicit field
    if paths.STATE.exists():
        m = re.search(r"(?m)^- salary_expectation:\s*\$?\s*([0-9]{5,6})\s*$", paths.STATE.read_text(encoding="utf-8"))
        if m:
            return m.group(1)

    # 2) FORM_ANSWERS table row (ignore NEEDS ME)
    form = paths.APPLICATIONS / "FORM_ANSWERS.md"
    if form.exists():
        for line in form.read_text(encoding="utf-8").splitlines():
            if "salary expectations" not in line.lower():
                continue
            if re.search(r"NEEDS\s*ME", line, re.I):
                return None
            m = _TABLE.search(line) or _LINE.search(line)
            if m:
                return m.group(1).replace(",", "")

    # 3) SALARY.md only if marked SET (not NEEDS ME heading/examples)
    salary_md = paths.APPLICATIONS / "needs-me" / "SALARY.md"
    if salary_md.exists():
        text = salary_md.read_text(encoding="utf-8")
        if re.search(r"(?im)^#\s*Salary expectation\s*—\s*SET\s*$", text):
            m = _LINE.search(text)
            if m:
                return m.group(1).replace(",", "")
    return None


def salary_from_memory() -> str | None:
    """Authoritative salary, after ingesting any drop-file reply."""
    ingested = ingest_salary_reply_file()
    if ingested:
        return ingested
    return _salary_from_authoritative()


def set_salary(amount: str | int) -> dict:
    """Persist Susmitha-provided salary expectation into Memory/form bank."""
    raw = str(amount).strip().replace(",", "").replace("$", "")
    if not re.fullmatch(r"[0-9]{5,6}", raw):
        raise ValueError(f"Invalid salary amount: {amount!r} (expected 5–6 digit USD yearly)")
    value = str(int(raw))

    form = paths.APPLICATIONS / "FORM_ANSWERS.md"
    form.parent.mkdir(parents=True, exist_ok=True)
    if form.exists():
        text = form.read_text(encoding="utf-8")
        text2, n = re.subn(
            r"(?im)^(\|\s*Salary expectations\s*\|\s*).*$",
            rf"\g<1>{value} |",
            text,
            count=1,
        )
        if n == 0:
            text2 = text.rstrip() + f"\n| Salary expectations | {value} |\n"
        form.write_text(text2, encoding="utf-8")
    else:
        form.write_text(
            "# Form answer bank\n\n"
            f"| Salary expectations | {value} |\n",
            encoding="utf-8",
        )

    salary_md = paths.APPLICATIONS / "needs-me" / "SALARY.md"
    salary_md.parent.mkdir(parents=True, exist_ok=True)
    salary_md.write_text(
        "# Salary expectation — SET\n\n"
        f"Salary expectations: {value}\n\n"
        "Unlocked for ATS forms. Curve Dental can submit in the next open CT window.\n",
        encoding="utf-8",
    )

    if paths.STATE.exists():
        state = paths.STATE.read_text(encoding="utf-8")
        if re.search(r"(?m)^- salary_expectation:", state):
            state = re.sub(r"(?m)^- salary_expectation:.*$", f"- salary_expectation: {value}", state)
        else:
            state = state.rstrip() + f"\n- salary_expectation: {value}\n"
        paths.STATE.write_text(state, encoding="utf-8")

    if paths.SETUP_STATUS.exists():
        setup = paths.SETUP_STATUS.read_text(encoding="utf-8")
        setup = setup.replace(
            "- [ ] Salary expectation number for required form fields",
            "- [x] Salary expectation number for required form fields",
        )
        paths.SETUP_STATUS.write_text(setup, encoding="utf-8")

    return {"salary_expectation": value, "form_answers": str(form), "salary_md": str(salary_md)}
