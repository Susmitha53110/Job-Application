from __future__ import annotations

import re
from dataclasses import dataclass

from .jd_tier import TieredJd
from .resume_parse import Resume


# Keep in sync with jd_tier.TECH_PATTERNS — word boundaries avoid "scala"∈"scalable".
TECH_PATTERNS = [
    r"\bpython\b", r"\bsql\b", r"\bpyspark\b", r"\bspark\b", r"\bscala\b", r"\bjava\b", r"\bbash\b",
    r"\bdatabricks\b", r"\bsnowflake\b", r"delta\s*lake", r"\badf\b|azure data factory",
    r"\badls\b", r"\bazure\b", r"\baws\b", r"\bglue\b", r"\bs3\b", r"\bathena\b", r"\bredshift\b",
    r"\bbigquery\b", r"\bairflow\b", r"\bdbt\b", r"\bdagster\b", r"\bprefect\b", r"\bkafka\b",
    r"\bflink\b", r"\boracle\b", r"\bparquet\b", r"\bavro\b", r"ci/?cd", r"\bgit\b",
    r"dimensional modeling|star schema|snowflake schema", r"\bscd\b",
    r"\betl\b|\belt\b", r"data quality", r"\bhipaa\b|\bphi\b", r"\blooker\b|\btableau\b|power\s*bi",
    r"feature store|feature engineering", r"\bmlops\b|machine learning",
    r"\bpinecone\b|\bmilvus\b|\bweaviate\b", r"\bterraform\b|infrastructure-as-code|\biac\b",
]


@dataclass
class ScoreResult:
    raw_points: float
    max_points: float
    fit_10: float
    matched: list[str]
    missing: list[str]
    top5_missing_keywords: list[str]


def _resume_corpus(resume: Resume) -> str:
    parts = [
        resume.summary,
        resume.skills_raw,
        " ".join(resume.skills),
        resume.education,
        resume.headline,
    ]
    for exp in resume.experiences:
        parts.append(exp.title)
        parts.append(exp.employer)
        parts.extend(exp.bullets)
    return "\n".join(parts).lower()


def _tech_in_text(text: str) -> set[str]:
    found = set()
    low = text.lower()
    for pat in TECH_PATTERNS:
        if re.search(pat, low, re.I):
            found.add(pat)
    return found


def _requirement_score(item_text: str, corpus: str, my_years: int = 5) -> tuple[float, bool]:
    """Return (fraction 0-1, matched?).

    Tech-bearing requirements: fraction of JD tech terms present in resume.
    Soft requirements: keyword overlap on meaningful tokens.
    """
    low = item_text.lower()

    # Years-of-experience gates (ranges like 3-6 years, or N+/around N or more)
    m_range = re.search(r"(\d+)\s*[–\-to]{1,3}\s*(\d+)\s*years?", low)
    m = re.search(r"(?:around\s+)?(\d+)\+?\s*(?:or more\s+)?years?", low)
    if (m_range or m) and ("experience" in low or "engineering" in low or "data" in low):
        if m_range:
            lo, hi = int(m_range.group(1)), int(m_range.group(2))
            if lo <= my_years <= hi:
                return 1.0, True
            if my_years < lo:
                return max(0.0, my_years / lo), False
            # slightly over max of range — still ok for mid-level bands
            return 0.9, True
        need = int(m.group(1))
        if my_years >= need:
            if "pipeline" in low and "pipeline" in corpus:
                return 1.0, True
            if any(k in low for k in ("data engineer", "software engineer", "analytics engineer", "related field")):
                return 1.0, True
            return 0.85, True
        return max(0.0, my_years / need), False

    # Production pipeline ownership without exotic tech list
    if "pipeline" in low and any(k in low for k in ("production", "building", "maintaining", "deploy")):
        if "pipeline" in corpus and any(k in corpus for k in ("python", "sql", "spark", "etl", "elt")):
            # ML mention as one optional domain among analytics/reporting/ML
            if "machine learning" in low or "ml" in low:
                return (0.85 if "machine learning" in corpus or "ml" in corpus else 0.75), True
            return 1.0, True

    # Orchestration: treat Azure Data Factory / ADF as honest "or similar" to Airflow/Dagster/Prefect
    if re.search(r"airflow|dagster|prefect|orchestr", low) and re.search(
        r"azure data factory|\badf\b|databricks.*workflow|pipeline monitoring", corpus
    ):
        if re.search(r"or similar|preferred|e\.g\.", low):
            # Partial credit when resume has production orchestration but not named Airflow
            base = 0.7
            if "airflow" in corpus:
                base = 1.0
            return base, True

    jd_tech = _tech_in_text(item_text)
    if jd_tech:
        # Split core DE stack vs adjacent ML/tooling
        core = {t for t in jd_tech if t not in {
            r"\bmlops\b|machine learning", r"feature store|feature engineering",
            r"\bpinecone\b|\bmilvus\b|\bweaviate\b", r"\blooker\b|\btableau\b|power\s*bi",
            r"\bairflow\b", r"\bkafka\b", r"\bdbt\b", r"\bdagster\b", r"\bprefect\b", r"\bflink\b",
        }}
        adj = jd_tech - core
        core_hits = sum(1 for t in core if re.search(t, corpus, re.I)) if core else 0
        adj_hits = sum(1 for t in adj if re.search(t, corpus, re.I)) if adj else 0
        # ADF ≈ orchestration tooling when JD asks Airflow family
        if any(t in adj for t in (r"\bairflow\b", r"\bdagster\b", r"\bprefect\b")) and re.search(
            r"azure data factory|\badf\b", corpus
        ):
            adj_hits = max(adj_hits, 1)
        if core:
            frac = core_hits / len(core)
            if adj:
                frac = 0.8 * frac + 0.2 * (adj_hits / len(adj))
        else:
            frac = adj_hits / len(adj) if adj else 0.0
        if re.search(r"\bor\b", item_text, re.I) and (core_hits + adj_hits) >= 1:
            frac = max(frac, 0.7)
        return frac, frac >= 0.5

    stop = {
        "with", "that", "this", "from", "have", "will", "your", "about", "their",
        "years", "year", "experience", "using", "including", "related", "field",
        "strong", "proficiency", "professional", "working", "ability", "such",
        "technologies", "modern", "best", "practices", "understanding",
    }
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9+.#]{4,}", item_text) if t.lower() not in stop]
    if not tokens:
        return 0.5, True  # neutral soft item
    hits = sum(1 for t in tokens if t in corpus)
    frac = hits / len(tokens)
    return frac, frac >= 0.4


def score_resume_against_jd(resume: Resume, jd: TieredJd, my_years: int = 5) -> ScoreResult:
    corpus = _resume_corpus(resume)
    items = list(jd.required) + list(jd.preferred)
    if not items:
        # keyword fallback using tech patterns + jd keywords
        kws = [k for k in jd.keywords if len(k) > 3][:20]
        max_points = float(len(kws) or 1)
        raw = 0.0
        matched, missing = [], []
        for kw in kws:
            if kw.lower() in corpus:
                raw += 1
                matched.append(kw)
            else:
                missing.append(kw)
        fit = round(10 * raw / max_points, 1)
        return ScoreResult(raw, max_points, fit, matched, missing, missing[:5])

    max_points = float(sum(i.weight for i in items))
    raw = 0.0
    matched, missing = [], []
    for item in items:
        frac, ok = _requirement_score(item.text, corpus, my_years=my_years)
        raw += item.weight * frac
        (matched if ok else missing).append(item.text)

    # Top missing tech keywords
    jd_tech = _tech_in_text(jd.raw)
    resume_tech = _tech_in_text(corpus)
    missing_tech = sorted(jd_tech - resume_tech)
    # human labels
    label = {
        r"\bairflow\b": "Airflow",
        r"\bkafka\b": "Kafka",
        r"\bdbt\b": "dbt",
        r"\bdagster\b": "Dagster",
        r"\bprefect\b": "Prefect",
        r"\bbigquery\b": "BigQuery",
        r"\blooker\b|\btableau\b|power\s*bi": "BI tools (Looker/Tableau/Power BI)",
        r"feature store|feature engineering": "feature engineering / feature store",
        r"\bmlops\b|machine learning": "ML/MLOps workflows",
        r"\bpinecone\b|\bmilvus\b|\bweaviate\b": "vector databases",
        r"\bflink\b": "Flink",
        r"\bavro\b": "Avro",
        r"\bterraform\b|infrastructure-as-code|\biac\b": "IaC / Terraform",
        r"\bscala\b": "Scala",
        r"\bhipaa\b|\bphi\b": "HIPAA/PHI",
    }
    top5 = []
    for pat in missing_tech:
        top5.append(label.get(pat, pat))
        if len(top5) >= 5:
            break
    if len(top5) < 5:
        junk = {
            "such", "patterns", "storage", "working", "closely", "technologies", "e.g",
            "what", "when", "where", "who", "how", "why", "are", "can", "more", "first",
            "through", "sales", "help", "time", "product", "business", "company",
            "creators", "creator", "omni", "paid", "questions", "commerce", "kit",
            "dental", "curve", "finance", "billing", "payments", "customer",
            "core", "management", "model", "report", "reliable", "bring", "build",
        }
        for kw in jd.keywords:
            if kw.lower() not in corpus and kw not in top5 and len(kw) > 3:
                if kw.lower() in junk:
                    continue
                # Never treat raw regex patterns as human keywords
                if "\\" in kw or kw.startswith("\\b") or "|" in kw:
                    continue
                # Prefer tech-looking tokens
                if not re.search(r"[A-Z]|sql|dbt|spark|python|azure|aws|snow|data|pipeline|model", kw, re.I):
                    continue
                top5.append(kw)
            if len(top5) >= 5:
                break

    fit = round(10 * (raw / max_points), 1) if max_points else 0.0
    return ScoreResult(raw, max_points, fit, matched, missing, top5[:5])


def keyword_coverage(resume: Resume, keywords: list[str]) -> tuple[list[str], list[str]]:
    corpus = _resume_corpus(resume)
    covered = [k for k in keywords if k.lower() in corpus]
    gaps = [k for k in keywords if k.lower() not in corpus]
    return covered, gaps
