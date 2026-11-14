from __future__ import annotations

import re
from dataclasses import dataclass, field

# Short tokens use word boundaries so "scala" ≠ "scalable", "java" ≠ "javascript", etc.
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


DEALBREAKER_PATTERNS = [
    ("sponsorship", re.compile(r"no sponsorship|must be (a )?US citizen|citizenship required|without sponsorship|visa sponsorship not|cannot sponsor|immigration-related sponsorship|authorized to work.{0,40}without sponsorship", re.I)),
    ("clearance", re.compile(r"security clearance|secret clearance|top secret|TS/SCI|must (already )?hold.*clearance|public trust|background investigation", re.I)),
    ("citizen_only", re.compile(r"US citizenship required|must be a U\.?S\.? citizen|lawful permanent resid", re.I)),
    ("on_site", re.compile(r"\bon[- ]site only\b|\bin[- ]office only\b|must (be|work) on[- ]site|no remote", re.I)),
    ("travel", re.compile(r"(\d{2,3})\s*%\s*travel|travel up to\s*(\d{2,3})\s*%", re.I)),
    ("certification", re.compile(r"required certification|must (have|hold|possess).{0,40}(certification|certified|license)", re.I)),
    ("years", re.compile(r"(?:around\s+)?(\d+)\+?\s*(?:or more\s+)?years?.{0,60}experience", re.I)),
]


EXTRA_STOP = {
    "with", "that", "this", "from", "have", "will", "your", "about", "their", "been",
    "were", "also", "into", "than", "then", "them", "they", "ability", "years", "experience",
    "work", "team", "role", "including", "using", "across", "should", "must", "preferred",
    "required", "strong", "good", "well", "etc", "and", "the", "for", "our", "you",
    "similar", "tools", "practices", "learning", "machine", "building", "anywhere",
    "bachelor", "degree", "related", "field", "professional", "support", "systems",
    "data", "engineer", "engineering", "platform", "platforms", "modern", "best",
    "what", "when", "where", "who", "how", "why", "are", "can", "more", "first",
    "through", "every", "one", "help", "time", "like", "just", "over", "into",
    "such", "each", "both", "some", "other", "than", "then", "very", "make",
    "company", "companies", "candidate", "candidates", "position", "job", "opening",
    "benefits", "equal", "opportunity", "employer", "status", "please", "apply",
}


@dataclass
class JdRequirement:
    text: str
    weight: int  # 3 hard, 2 important, 1 nice
    kind: str = "general"


@dataclass
class TieredJd:
    title: str
    company: str
    url: str
    location: str
    raw: str
    required: list[JdRequirement] = field(default_factory=list)
    preferred: list[JdRequirement] = field(default_factory=list)
    dealbreakers: list[dict] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


def _normalize_jd_text(jd_text: str) -> str:
    """Turn HTML-ish / single-line prose into line-oriented text when possible."""
    text = jd_text or ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?i)</li>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    # Common prose section markers → newlines
    text = re.sub(
        r"(?i)\s+(requirements|qualifications|what you.?ll need|you have|must have|responsibilities|"
        r"what you.?ll do|about the role|experiences?|preferred qualifications|nice to have|bonus points)\s*[:\-–—]?\s*",
        lambda m: "\n" + m.group(1).title() + "\n",
        text,
    )
    # Bullet-like separators in prose
    text = re.sub(r"\s+[•●▪︎]\s+", "\n- ", text)
    # Do NOT split every sentence — that creates noisy fake requirements for Ashby prose.
    return text


def _split_sections(jd_text: str) -> tuple[str, str]:
    req = []
    pref = []
    mode = "required"
    for line in jd_text.splitlines():
        low = line.strip().lower()
        if any(
            k in low
            for k in (
                "benefits",
                "compensation",
                "what we offer",
                "life at",
                "equal opportunity",
                "privacy notice",
                "how to apply",
            )
        ):
            break
        # Anti-fit / culture lists are not hard skills
        if any(k in low for k in ("you might not like", "this role is not", "you shouldn't", "red flags")):
            mode = "skip"
            continue
        if mode == "skip":
            continue
        if any(k in low for k in ("requirements", "qualifications", "you have", "must have", "what you'll need", "experiences")):
            mode = "required"
            if ":" in line:
                after = line.split(":", 1)[1].strip()
                if after and not after.lower().startswith(("first month", "first six", "first year")):
                    req.append(after)
            continue
        if any(k in low for k in ("preferred", "nice to have", "bonus", "plus if", "good to have", "nice to have")):
            mode = "preferred"
            continue
        if any(k in low for k in ("responsibilities", "what you'll do", "about the role", "the role")):
            mode = "skip"
            continue
        if line.strip().startswith(("-", "*", "•")):
            item = re.sub(r"^[-*•]\s*", "", line.strip())
            item_l = item.lower()
            if item_l.startswith(("first month", "first six", "first year", "needing ", "wanting ", "preferring ", "being ", "expecting ", "discomfort", "profit sharing", "equity", "401k", "we cover", "childcare", "gender affirming", "twenty (")):
                continue
            # Ashby compensation chrome often becomes fake bullets: "$172K", "$50K Equity"
            if re.match(r"^\$?\d", item_l) or any(
                k in item_l
                for k in (
                    "equity",
                    "profit sharing",
                    "offers bonus",
                    "per year",
                    "per month",
                    "salary",
                    "compensation",
                )
            ):
                continue
            if len(item) < 8:
                continue
            (req if mode == "required" else pref).append(item)
    return "\n".join(req), "\n".join(pref)


def _tech_requirements_from_prose(jd_text: str) -> list[JdRequirement]:
    """When no bullets exist, synthesize hard/important requirements from tech + years signals."""
    reqs: list[JdRequirement] = []
    low = jd_text.lower()

    # Prefer explicit ranges like 3-6 years; else N+ / around N or more
    years = re.search(
        r"(?:around\s+)?(\d+)\s*[–\-to]{1,3}\s*(\d+)\s*years?.{0,80}(?:experience|engineering|data)",
        low,
    )
    if years:
        reqs.append(JdRequirement(text=years.group(0), weight=3, kind="hard"))
    else:
        years = re.search(
            r"(?:around\s+)?(\d+)\+?\s*(?:or more\s+)?years?.{0,80}(?:experience|engineering|data)",
            low,
        )
        if years:
            reqs.append(JdRequirement(text=years.group(0), weight=3, kind="hard"))

    # Collect tech mentions as hard requirements
    tech_hits = []
    for pat in TECH_PATTERNS:
        if re.search(pat, low, re.I):
            tech_hits.append(pat)
    # Deduplicate overlapping labels
    labels = {
        r"\bpython\b": "Python",
        r"\bsql\b": "SQL",
        r"\bpyspark\b": "PySpark",
        r"\bspark\b": "Spark",
        r"\bscala\b": "Scala",
        r"\bdatabricks\b": "Databricks",
        r"\bsnowflake\b": "Snowflake",
        r"delta\s*lake": "Delta Lake",
        r"\badf\b|azure data factory": "Azure Data Factory",
        r"\bazure\b": "Azure",
        r"\baws\b": "AWS",
        r"\bairflow\b": "Airflow",
        r"\bdbt\b": "dbt",
        r"\bdagster\b": "Dagster",
        r"\bprefect\b": "Prefect",
        r"\bkafka\b": "Kafka",
        r"\betl\b|\belt\b": "ETL/ELT pipelines",
        r"data quality": "data quality",
        r"\blooker\b|\btableau\b|power\s*bi": "BI tools (Looker/Tableau/Power BI)",
        r"dimensional modeling|star schema|snowflake schema": "dimensional modeling",
        r"\bhipaa\b|\bphi\b": "HIPAA/PHI",
        r"\bmlops\b|machine learning": "ML/MLOps workflows",
        # Must match extract_keywords label_map — never surface raw regex as requirement text
        r"ci/?cd": "CI/CD",
        r"\bgit\b": "Git",
    }
    seen = set()
    for pat in tech_hits:
        label = labels.get(pat, pat)
        if label in seen:
            continue
        seen.add(label)
        # Core stack = hard; adjacent = important
        weight = 3 if label in {
            "Python", "SQL", "PySpark", "Spark", "Databricks", "Snowflake",
            "Azure Data Factory", "Azure", "AWS", "ETL/ELT pipelines", "dbt",
            "dimensional modeling", "data quality",
        } else 2
        # Example-only mentions (e.g. dbt) are preferred signal, not hard gates
        if label == "dbt" and re.search(
            r"(?:e\.g\.?|such as|including|like)\s+[^.],{0,80}\bdbt\b|(?:e\.g\.?|such as|including|like)\s+dbt\b",
            low,
        ):
            weight = 2
        reqs.append(JdRequirement(text=f"Experience with {label}", weight=weight, kind="hard" if weight == 3 else "important"))

    # Pipeline ownership prose
    if re.search(r"pipeline|data model|analytics engineering|production data", low):
        reqs.append(
            JdRequirement(
                text="Build and maintain production data pipelines / models",
                weight=3,
                kind="hard",
            )
        )

    # Specific tenure asks (e.g. 2 years production Snowflake)
    for m in re.finditer(
        r"(?:at least|minimum of)?\s*(\d+)\+?\s*years?.{0,40}(snowflake|databricks|dbt|python|spark|azure|aws)",
        low,
    ):
        reqs.append(
            JdRequirement(
                text=m.group(0).strip(),
                weight=3,
                kind="hard",
            )
        )
    return reqs


def extract_keywords(jd_text: str, limit: int = 40) -> list[str]:
    # Prefer concrete tech labels first. Keys must match TECH_PATTERNS exactly.
    label_map = {
        r"\bpython\b": "Python",
        r"\bsql\b": "SQL",
        r"\bpyspark\b": "PySpark",
        r"\bspark\b": "Spark",
        r"\bscala\b": "Scala",
        r"\bjava\b": "Java",
        r"\bbash\b": "Bash",
        r"\bdatabricks\b": "Databricks",
        r"\bsnowflake\b": "Snowflake",
        r"delta\s*lake": "Delta Lake",
        r"\badf\b|azure data factory": "Azure Data Factory",
        r"\badls\b": "ADLS",
        r"\bazure\b": "Azure",
        r"\baws\b": "AWS",
        r"\bglue\b": "Glue",
        r"\bs3\b": "S3",
        r"\bathena\b": "Athena",
        r"\bredshift\b": "Redshift",
        r"\bbigquery\b": "BigQuery",
        r"\bairflow\b": "Airflow",
        r"\bdbt\b": "dbt",
        r"\bdagster\b": "Dagster",
        r"\bprefect\b": "Prefect",
        r"\bkafka\b": "Kafka",
        r"\bflink\b": "Flink",
        r"\boracle\b": "Oracle",
        r"\bparquet\b": "Parquet",
        r"\bavro\b": "Avro",
        r"ci/?cd": "CI/CD",
        r"\bgit\b": "Git",
        r"dimensional modeling|star schema|snowflake schema": "dimensional modeling",
        r"\bscd\b": "SCD",
        r"\betl\b|\belt\b": "ETL/ELT",
        r"data quality": "data quality",
        r"\bhipaa\b|\bphi\b": "HIPAA/PHI",
        r"\blooker\b|\btableau\b|power\s*bi": "BI tools",
        r"feature store|feature engineering": "feature engineering",
        r"\bmlops\b|machine learning": "ML/MLOps",
        r"\bpinecone\b|\bmilvus\b|\bweaviate\b": "vector DBs",
        r"\bterraform\b|infrastructure-as-code|\biac\b": "Terraform/IaC",
    }
    ranked_tech = []
    seen = set()
    for pat in TECH_PATTERNS:
        if not re.search(pat, jd_text, re.I):
            continue
        lab = label_map.get(pat, pat)
        if lab.startswith("\\b") or "|" in lab or "\\" in lab:
            # Never surface raw regex as a keyword label
            continue
        if lab not in seen:
            seen.add(lab)
            ranked_tech.append(lab)

    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+.#/-]{1,}\b", jd_text)
    counts: dict[str, int] = {}
    for w in words:
        key = w if w.isupper() or any(c in w for c in "+#.") else w.lower()
        if key.lower() in EXTRA_STOP or len(key) < 4:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    out = list(ranked_tech)
    for k, _ in ranked:
        if k in out or k.lower() in {x.lower() for x in out}:
            continue
        out.append(k)
        if len(out) >= limit:
            break
    return out[:limit]


def tier_jd(title: str, company: str, url: str, location: str, jd_text: str) -> TieredJd:
    normalized = _normalize_jd_text(jd_text)
    req_block, pref_block = _split_sections(normalized)
    required = [JdRequirement(text=t, weight=3, kind="hard") for t in req_block.splitlines() if t.strip()]
    preferred = [JdRequirement(text=t, weight=1, kind="nice") for t in pref_block.splitlines() if t.strip()]

    if not required:
        # fallback: treat bullet-like lines as important (skip benefits/comp chrome)
        in_benefits = False
        for line in normalized.splitlines():
            low_line = line.strip().lower()
            if any(
                k in low_line
                for k in (
                    "benefits",
                    "compensation",
                    "what we offer",
                    "perks",
                    "our values",
                    "equal opportunity",
                    "life at",
                )
            ):
                in_benefits = True
                continue
            if in_benefits:
                continue
            if line.strip().startswith(("-", "*", "•")):
                item = re.sub(r"^[-*•]\s*", "", line.strip())
                low = item.lower()
                if re.match(r"^\$?\d", low) or any(
                    k in low
                    for k in (
                        "equity",
                        "profit sharing",
                        "offers bonus",
                        "compensation",
                        "per month",
                        "401k",
                        "medical",
                        "dental",
                        "vision",
                        "stipend",
                        "tuition",
                        "paid vacation",
                        "pto",
                        "401(k)",
                    )
                ):
                    continue
                if len(item) < 8:
                    continue
                required.append(JdRequirement(text=item, weight=2, kind="important"))

    def _looks_like_comp_noise(items: list[JdRequirement]) -> bool:
        if not items:
            return False
        hits = 0
        for it in items:
            low = (it.text or "").lower()
            if re.match(r"^\$?\d", low) or any(
                k in low for k in ("equity", "profit sharing", "offers bonus", "compensation", "per month")
            ):
                hits += 1
        return hits >= max(1, len(items) // 2)

    if not required:
        # Prose ATS descriptions (Ashby/Rippling) — synthesize tech/years requirements
        required = _tech_requirements_from_prose(jd_text)
    elif len(required) > 15 or _looks_like_comp_noise(required):
        # Noisy section split (culture/timeline/comp chrome) — prefer tech/years synthesis
        required = _tech_requirements_from_prose(jd_text)

    dealbreakers = []
    for name, pat in DEALBREAKER_PATTERNS:
        m = pat.search(jd_text)
        if m:
            dealbreakers.append({"name": name, "snippet": m.group(0), "span": m.group(0)})

    return TieredJd(
        title=title,
        company=company,
        url=url,
        location=location,
        raw=jd_text,
        required=required,
        preferred=preferred,
        dealbreakers=dealbreakers,
        keywords=extract_keywords(jd_text),
    )
