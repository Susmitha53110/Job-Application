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
    """Rewrite summary in JD vocabulary; claims must trace to resume (no new facts)."""
    base = resume.summary.strip() or (
        f"{resume.experiences[0].title} with experience across "
        f"{', '.join(resume.skills[:6])}."
        if resume.experiences and resume.skills
        else resume.headline
    )
    # Lead with JD title terms if they already appear in resume corpus
    lead_bits = []
    corpus = (base + " " + " ".join(resume.skills) + " " + " ".join(
        b for e in resume.experiences for b in e.bullets
    )).lower()
    for kw in jd.keywords[:8]:
        if kw.lower() in corpus and kw not in lead_bits:
            lead_bits.append(kw)
    if not lead_bits:
        return base
    lead = f"Candidate aligned to {jd.title} priorities including {', '.join(lead_bits[:5])}."
    # Keep original summary body (facts unchanged)
    if base:
        return f"{lead} {base}"
    return lead


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
    a.skills = reorder_skills(list(resume.skills), jd)
    a.skills_raw = ", ".join(a.skills)

    b = copy.deepcopy(a)
    additions = hedged_additions(resume, jd)
    flagged = [f'verify before applying: "{x}"' for x in additions]
    if additions:
        b.skills = list(b.skills) + additions
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
