"""Preflight ATS application questions for F1-OPT / Memory hard answers.

Never invent salary. Flag sponsorship traps that conflict with F1-OPT honesty.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .job_search import _get_json


# Multi-year "without sponsorship" gates — F1-OPT cannot honestly Yes.
MULTIYEAR_NO_SPONSOR = re.compile(
    r"without\s+(?:visa\s+)?sponsorship.{0,40}(?:\d+\s*years?|next\s+\d+)|"
    r"(?:for\s+the\s+)?next\s+\d+\s*years?.{0,60}without\s+(?:visa\s+)?sponsorship|"
    r"able to work.{0,40}without.{0,20}sponsorship.{0,40}\d+\s*years?",
    re.I,
)

CITIZEN_ONLY = re.compile(
    r"must be (a )?u\.?s\.? citizen|us citizenship required|citizen(ship)? only|"
    r"green card (holder )?required|permanent resident required",
    re.I,
)

SALARY_FIELD = re.compile(
    r"salary expectation|expected salary|compensation expectation|desired (salary|comp)|"
    r"what is your salary|pay expectation",
    re.I,
)


@dataclass
class FormPreflight:
    source: str
    url: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers


def _scan_label(label: str, *, required: bool) -> tuple[list[str], list[str]]:
    from .salary import salary_from_memory

    blockers: list[str] = []
    warnings: list[str] = []
    if not label:
        return blockers, warnings
    if MULTIYEAR_NO_SPONSOR.search(label):
        # Standing Memory: Susmitha does not require sponsorship → answer Yes on these.
        warnings.append(
            f"Multi-year no-sponsorship Q (answer Yes per Memory sponsorship=No): {label.strip()}"
        )
    if CITIZEN_ONLY.search(label):
        blockers.append(f"Citizenship/green-card only question: {label.strip()}")
    if SALARY_FIELD.search(label) and required:
        if salary_from_memory():
            warnings.append(f"Required salary field — use Memory {salary_from_memory()}: {label.strip()}")
        else:
            blockers.append(f"Required salary field — STOP needs-me: {label.strip()}")
    elif SALARY_FIELD.search(label):
        warnings.append(f"Optional salary field present: {label.strip()}")
    return blockers, warnings


def preflight_greenhouse(board: str, job_id: int | str) -> FormPreflight:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}?questions=true"
    try:
        detail = _get_json(url)
    except Exception as e:
        return FormPreflight(source="greenhouse", url=url, blockers=[f"Greenhouse questions fetch failed: {e}"])

    pf = FormPreflight(
        source="greenhouse",
        url=detail.get("absolute_url") or url,
    )
    for q in detail.get("questions") or []:
        label = q.get("label") or ""
        req = bool(q.get("required"))
        pf.questions.append(label)
        b, w = _scan_label(label, required=req)
        for item in b:
            if item not in pf.blockers:
                pf.blockers.append(item)
        for item in w:
            if item not in pf.warnings:
                pf.warnings.append(item)

    # Compliance / EEO — warn only unless clearly required with no decline option
    for block in detail.get("compliance") or []:
        for q in block.get("questions") or []:
            label = q.get("label") or block.get("type") or "compliance"
            pf.warnings.append(f"Compliance section present ({block.get('type')}): {label}")

    return pf


def preflight_from_url(url: str) -> FormPreflight | None:
    """If URL is a known Greenhouse job board link, run questions preflight."""
    m = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url or "")
    if not m:
        # embed: .../embed/job_app?for=BOARD&token=JOBID
        m = re.search(r"greenhouse\.io/embed/job_app\?[^#]*for=([^&]+).*?[?&]token=(\d+)", url or "")
    if not m:
        m = re.search(r"[?&]gh_jid=(\d+)", url or "")
        if m and "mongodb" in (url or "").lower():
            return preflight_greenhouse("mongodb", m.group(1))
        return None
    return preflight_greenhouse(m.group(1), m.group(2))
