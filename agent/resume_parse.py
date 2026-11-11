from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Experience:
    title: str
    employer: str
    dates: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class Resume:
    name: str = ""
    contact_lines: list[str] = field(default_factory=list)
    headline: str = ""
    summary: str = ""
    experiences: list[Experience] = field(default_factory=list)
    skills_raw: str = ""
    skills: list[str] = field(default_factory=list)
    education: str = ""
    other_sections: dict[str, str] = field(default_factory=dict)
    source_path: str = ""
    plain_text: str = ""


SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "skills": {"skills", "technical skills", "core skills", "technologies"},
    "education": {"education", "academic background"},
}


def _norm_heading(line: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", line.strip().lower())


def _classify_heading(line: str) -> str | None:
    h = _norm_heading(line)
    if not h or len(h) > 40:
        return None
    for key, aliases in SECTION_ALIASES.items():
        if h in aliases:
            return key
    return None


def parse_markdown_resume(text: str, source: Path | None = None) -> Resume:
    resume = Resume(source_path=str(source) if source else "", plain_text=text)
    lines = [ln.rstrip() for ln in text.splitlines()]
    # Name: first non-empty non-heading-ish line
    for ln in lines:
        s = ln.strip().lstrip("#").strip()
        if s:
            resume.name = s
            break

    current: str | None = None
    buf: list[str] = []
    exp: Experience | None = None

    def flush_buf():
        nonlocal buf
        if current and buf:
            block = "\n".join(buf).strip()
            if current == "summary":
                resume.summary = block
            elif current == "skills":
                resume.skills_raw = block
                parts = re.split(r"[,|\n•]+", block)
                resume.skills = [p.strip() for p in parts if p.strip()]
            elif current == "education":
                resume.education = block
            elif current not in {"experience"}:
                resume.other_sections[current] = block
        buf = []

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        heading = None
        if stripped.startswith("#"):
            heading = _classify_heading(stripped.lstrip("#").strip())
        elif stripped.isupper() and 2 <= len(stripped) <= 40:
            heading = _classify_heading(stripped)
        elif re.match(r"^[A-Za-z ].{0,38}$", stripped) and stripped.endswith(":") is False:
            # markdown bold headings **Experience**
            m = re.match(r"^\*\*(.+)\*\*$", stripped)
            if m:
                heading = _classify_heading(m.group(1))

        if heading:
            flush_buf()
            if exp and current == "experience":
                resume.experiences.append(exp)
                exp = None
            current = heading
            i += 1
            continue

        if current == "experience":
            # New job header heuristics: "Title — Company | Dates" or "Company | Title | Dates"
            if stripped and not stripped.startswith(("-", "*", "•")):
                maybe_header = stripped.lstrip("#").strip()
                if exp:
                    resume.experiences.append(exp)
                # crude split
                dates = ""
                title = maybe_header
                employer = ""
                date_match = re.search(
                    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})\s*[-–—]\s*"
                    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current)",
                    maybe_header,
                    re.I,
                )
                if date_match:
                    dates = date_match.group(0)
                    maybe_header = (maybe_header[: date_match.start()] + maybe_header[date_match.end() :]).strip(" |-–—,")
                if " at " in maybe_header.lower():
                    title, _, employer = re.split(r"\s+at\s+", maybe_header, maxsplit=1, flags=re.I)
                elif "—" in maybe_header or " - " in maybe_header:
                    parts = re.split(r"\s+[—\-]\s+", maybe_header, maxsplit=1)
                    title = parts[0].strip()
                    employer = parts[1].strip() if len(parts) > 1 else ""
                elif "|" in maybe_header:
                    parts = [p.strip() for p in maybe_header.split("|")]
                    if len(parts) >= 2:
                        title, employer = parts[0], parts[1]
                exp = Experience(title=title.strip(), employer=employer.strip(), dates=dates.strip())
            elif stripped.startswith(("-", "*", "•")) and exp:
                exp.bullets.append(re.sub(r"^[-*•]\s*", "", stripped))
        elif current is None:
            if stripped and stripped != resume.name:
                resume.contact_lines.append(stripped)
        else:
            buf.append(raw)
        i += 1

    flush_buf()
    if exp:
        resume.experiences.append(exp)

    if not resume.headline and resume.experiences:
        resume.headline = resume.experiences[0].title
    return resume


def parse_docx_resume(path: Path) -> Resume:
    from docx import Document

    doc = Document(str(path))
    paras = [p.text for p in doc.paragraphs if p.text is not None]
    text = "\n".join(paras)
    return parse_markdown_resume(text, source=path)


def load_base_resume(path: Path) -> Resume:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return parse_docx_resume(path)
    if suffix in {".md", ".txt"}:
        return parse_markdown_resume(path.read_text(encoding="utf-8"), source=path)
    if suffix == ".pdf":
        # Best-effort: try pdftotext if present
        import shutil
        import subprocess

        if shutil.which("pdftotext"):
            out = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)
            return parse_markdown_resume(out, source=path)
        raise ValueError(
            f"Cannot extract text from PDF {path.name} without pdftotext. Provide .docx or .md."
        )
    raise ValueError(f"Unsupported resume type: {path.suffix}")
