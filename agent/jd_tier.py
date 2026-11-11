from __future__ import annotations

import re
from dataclasses import dataclass, field


DEALBREAKER_PATTERNS = [
    ("sponsorship", re.compile(r"no sponsorship|must be (a )?US citizen|citizenship required|without sponsorship|visa sponsorship not|cannot sponsor", re.I)),
    ("clearance", re.compile(r"security clearance|secret clearance|top secret|TS/SCI|must (already )?hold.*clearance", re.I)),
    ("citizen_only", re.compile(r"US citizenship required|must be a U\.?S\.? citizen", re.I)),
    ("on_site", re.compile(r"\bon[- ]site only\b|\bin[- ]office only\b|must (be|work) on[- ]site|no remote", re.I)),
    ("travel", re.compile(r"(\d{2,3})\s*%\s*travel|travel up to\s*(\d{2,3})\s*%", re.I)),
    ("certification", re.compile(r"required certification|must (have|hold|possess).{0,40}(certification|certified|license)", re.I)),
    ("years", re.compile(r"(\d+)\+?\s*\+?\s*years?.{0,40}experience", re.I)),
]


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


def _split_sections(jd_text: str) -> tuple[str, str]:
    req = []
    pref = []
    mode = "required"
    for line in jd_text.splitlines():
        low = line.strip().lower()
        if any(k in low for k in ("requirements", "qualifications", "you have", "must have", "what you'll need")):
            mode = "required"
            continue
        if any(k in low for k in ("preferred", "nice to have", "bonus", "plus if", "good to have")):
            mode = "preferred"
            continue
        if line.strip().startswith(("-", "*", "•")):
            (req if mode == "required" else pref).append(re.sub(r"^[-*•]\s*", "", line.strip()))
    return "\n".join(req), "\n".join(pref)


def extract_keywords(jd_text: str, limit: int = 40) -> list[str]:
    # Keep multi-word tech-ish tokens and CapWords
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+.#/-]{1,}\b", jd_text)
    stop = {
        "with", "that", "this", "from", "have", "will", "your", "about", "their", "been",
        "were", "also", "into", "than", "then", "them", "they", "ability", "years", "experience",
        "work", "team", "role", "including", "using", "across", "should", "must", "preferred",
        "required", "strong", "good", "well", "etc", "and", "the", "for", "our", "you",
        "similar", "tools", "practices", "learning", "machine", "building", "anywhere",
        "bachelor", "degree", "related", "field", "professional", "support", "systems",
        "data", "engineer", "engineering", "platform", "platforms", "modern", "best",
    }
    counts: dict[str, int] = {}
    for w in words:
        key = w if w.isupper() or any(c in w for c in "+#.") else w.lower()
        if key.lower() in stop or len(key) < 3:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    return [k for k, _ in ranked[:limit]]


def tier_jd(title: str, company: str, url: str, location: str, jd_text: str) -> TieredJd:
    req_block, pref_block = _split_sections(jd_text)
    required = [JdRequirement(text=t, weight=3, kind="hard") for t in req_block.splitlines() if t.strip()]
    preferred = [JdRequirement(text=t, weight=1, kind="nice") for t in pref_block.splitlines() if t.strip()]
    # Mid-weight: lines mentioning "important" or longer required items already 3
    if not required:
        # fallback: treat bullet-like lines as important
        for line in jd_text.splitlines():
            if line.strip().startswith(("-", "*", "•")):
                required.append(JdRequirement(text=re.sub(r"^[-*•]\s*", "", line.strip()), weight=2, kind="important"))

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
