from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from .jd_tier import TieredJd
from .resume_parse import Experience, Resume


HEDGE_PREFIXES = (
    "familiarity with ",
    "working knowledge of ",
    "exposure to ",
)


@dataclass
class TailorResult:
    version_a: Resume  # reorder only
    version_b: Resume  # reorder + hedged additions
    additions_flagged: list[str] = field(default_factory=list)
    summary_a: str = ""
    summary_b: str = ""
    notes: list[str] = field(default_factory=list)


def _jd_terms(jd: TieredJd) -> list[str]:
    terms = []
    for item in jd.required + jd.preferred:
        terms.extend(re.findall(r"[A-Za-z0-9+.#]{3,}", item.text.lower()))
    terms.extend(k.lower() for k in jd.keywords)
    # unique preserve order
    seen = set()
    out = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _bullet_score(bullet: str, terms: list[str]) -> int:
    b = bullet.lower()
    return sum(1 for t in terms if t in b)


def rewrite_summary(resume: Resume, jd: TieredJd) -> str:
    """Keep the human-written summary. Never prepend ATS/tailoring-tool lead-ins."""
    base = resume.summary.strip() or (
        f"{resume.experiences[0].title} with experience across "
        f"{', '.join(resume.skills[:6])}."
        if resume.experiences and resume.skills
        else resume.headline
    )
    # Reject legacy auto-tailor phrasing if it leaked into a saved resume.
    base = re.sub(
        r"(?i)^\s*Candidate aligned to .+? priorities including [^.]+\.\s*",
        "",
        base,
    ).strip()
    return base


def reorder_experience(resume: Resume, terms: list[str]) -> list[Experience]:
    out = []
    for exp in resume.experiences:
        scored = sorted(
            exp.bullets,
            key=lambda b: _bullet_score(b, terms),
            reverse=True,
        )
        out.append(
            Experience(
                title=exp.title,  # never change titles
                employer=exp.employer,
                dates=exp.dates,
                bullets=scored,
            )
        )
    return out


def reorder_skills(skills: list[str], jd: TieredJd) -> list[str]:
    terms = set(_jd_terms(jd))
    # Relabel lightly: if JD uses a synonym already in skill text, keep skill text
    ranked = sorted(
        skills,
        key=lambda s: (0 if s.lower() in terms or any(t in s.lower() for t in terms) else 1, s.lower()),
    )
    return ranked


def reorder_skills_raw(skills_raw: str, jd: TieredJd) -> str:
    """Keep Category: item lines intact; rank categories and items by JD relevance."""
    lines = [ln.strip() for ln in (skills_raw or "").splitlines() if ln.strip()]
    if not lines:
        return skills_raw
    terms = set(_jd_terms(jd))

    def score_text(text: str) -> int:
        low = text.lower()
        return sum(1 for t in terms if t in low)

    ranked_lines: list[str] = []
    for ln in sorted(lines, key=lambda x: -score_text(x)):
        if ":" not in ln:
            ranked_lines.append(ln)
            continue
        cat, _, items = ln.partition(":")
        parts = [p.strip() for p in items.split(",") if p.strip()]
        parts = sorted(
            parts,
            key=lambda s: (0 if score_text(s) else 1, s.lower()),
        )
        ranked_lines.append(f"{cat.strip()}: {', '.join(parts)}")
    return "\n".join(ranked_lines)


def flat_skills_from_raw(skills_raw: str) -> list[str]:
    """Flatten categorized skills_raw into a list for scoring (no category labels)."""
    out: list[str] = []
    for ln in (skills_raw or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        items = ln.split(":", 1)[-1] if ":" in ln else ln
        for p in re.split(r"[,|•]+", items):
            s = p.strip()
            if s:
                out.append(s)
    return out


ALLOWED_HEDGES = [
    ("airflow", "familiarity with Apache Airflow"),
    ("kafka", "familiarity with Apache Kafka"),
    ("dbt", "familiarity with dbt"),
    ("dagster", "working knowledge of Dagster"),
    ("prefect", "working knowledge of Prefect"),
    ("bigquery", "familiarity with BigQuery"),
    ("tableau", "familiarity with Tableau"),
    ("looker", "familiarity with Looker"),
    ("power bi", "familiarity with Power BI"),
    ("flink", "exposure to Apache Flink"),
    ("feature engineering", "familiarity with feature engineering for ML datasets"),
    ("vector", "exposure to vector databases"),
]


def hedged_additions(resume: Resume, jd: TieredJd, max_additions: int = 3) -> list[str]:
    corpus = (
        resume.summary
        + " "
        + resume.skills_raw
        + " "
        + " ".join(resume.skills)
        + " "
        + " ".join(b for e in resume.experiences for b in e.bullets)
    ).lower()
    jd_low = jd.raw.lower()
    additions = []
    for needle, phrase in ALLOWED_HEDGES:
        if needle not in jd_low:
            continue
        if needle in corpus or phrase.split()[-1].lower() in corpus:
            continue
        additions.append(phrase)
        if len(additions) >= max_additions:
            break
    return additions


def tailor(resume: Resume, jd: TieredJd) -> TailorResult:
    terms = _jd_terms(jd)
    notes: list[str] = []

    a = copy.deepcopy(resume)
    a.summary = rewrite_summary(resume, jd)
    a.experiences = reorder_experience(resume, terms)
    if resume.skills_raw and "\n" in resume.skills_raw.strip():
        a.skills_raw = reorder_skills_raw(resume.skills_raw, jd)
        a.skills = flat_skills_from_raw(a.skills_raw)
    else:
        a.skills = reorder_skills(list(resume.skills), jd)
        a.skills_raw = ", ".join(a.skills)

    b = copy.deepcopy(a)
    additions = hedged_additions(resume, jd)
    flagged = [f'verify before applying: "{x}"' for x in additions]
    if additions:
        b.skills = list(b.skills) + additions
        if "\n" in (b.skills_raw or ""):
            b.skills_raw = (b.skills_raw.rstrip() + "\nHedged (verify): " + ", ".join(additions)).strip()
        else:
            b.skills_raw = ", ".join(b.skills)
        notes.append(
            "Version (b) adds hedged skills only. Submit version (a) unless Susmitha approved (b)."
        )

    return TailorResult(
        version_a=a,
        version_b=b,
        additions_flagged=flagged,
        summary_a=a.summary,
        summary_b=b.summary,
        notes=notes,
    )
