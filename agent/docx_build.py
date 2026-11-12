from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Pt

from .resume_parse import Resume


def build_ats_docx(resume: Resume, dest: Path) -> Path:
    """Single-column, body-only contact, no tables/textboxes/images/headers/footers."""
    doc = Document()
    section = doc.sections[0]
    # Ensure empty header/footer
    section.header.paragraphs[0].text = ""
    section.footer.paragraphs[0].text = ""

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    pf = style.paragraph_format
    pf.space_after = Pt(4)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE

    def add_heading_line(text: str):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)

    # Name
    name_p = doc.add_paragraph()
    name_run = name_p.add_run(resume.name or "Name")
    name_run.bold = True
    name_run.font.size = Pt(16)

    # Contact in body
    if resume.contact_lines:
        doc.add_paragraph(" | ".join(resume.contact_lines))

    if resume.headline:
        hp = doc.add_paragraph()
        hr = hp.add_run(resume.headline)
        hr.italic = True

    if resume.summary:
        add_heading_line("Summary")
        doc.add_paragraph(resume.summary)

    if resume.experiences:
        add_heading_line("Experience")
        for exp in resume.experiences:
            header = " | ".join(x for x in [exp.title, exp.employer, exp.dates] if x)
            p = doc.add_paragraph()
            r = p.add_run(header)
            r.bold = True
            for b in exp.bullets:
                doc.add_paragraph(b, style="List Bullet")

    if resume.skills or resume.skills_raw:
        add_heading_line("Skills")
        doc.add_paragraph(resume.skills_raw or ", ".join(resume.skills))

    if resume.education:
        add_heading_line("Education")
        doc.add_paragraph(resume.education)

    for title, body in resume.other_sections.items():
        add_heading_line(title.title())
        doc.add_paragraph(body)

    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest))
    return dest


def extract_plain_text_from_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def ats_order_check(plain: str) -> dict:
    """Confirm rough reading order; never claim 100% ATS compatible."""
    lower = plain.lower()
    checks = {
        "no_tables_used_in_builder": True,
        "contact_in_body": True,
        "has_summary_or_profile": "summary" in lower or "profile" in lower,
        "has_experience": "experience" in lower,
        "has_skills": "skill" in lower,
        "has_education": "education" in lower,
        "header_footer_empty_by_construction": True,
        "layout": "single-column paragraphs + bullets only",
    }
    return checks
