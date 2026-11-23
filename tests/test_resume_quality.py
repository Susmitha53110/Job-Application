from pathlib import Path

from agent.docx_build import build_ats_docx, extract_plain_text_from_docx
from agent.jd_tier import JdRequirement, TieredJd
from agent.resume_parse import load_base_resume
from agent.tailor import rewrite_summary, tailor


BASE = Path("resumes/base/Susmitha_Chowdary_Base_Resume.md")


def _sample_jd() -> TieredJd:
    return TieredJd(
        title="Data Engineer",
        company="TestCo",
        url="https://example.com",
        location="Remote",
        raw="Python SQL AWS ETL HIPAA Data Engineer",
        required=[JdRequirement(text="Python SQL AWS ETL HIPAA", weight=3)],
        preferred=[],
        keywords=["Python", "SQL", "AWS", "ETL/ELT", "HIPAA/PHI"],
    )


def test_no_candidate_aligned_summary():
    resume = load_base_resume(BASE)
    summary = rewrite_summary(resume, _sample_jd())
    assert "Candidate aligned" not in summary
    assert "nearly 5 years" in summary.lower()


def test_header_not_duplicated_and_city_only():
    resume = load_base_resume(BASE)
    assert resume.name.upper().startswith("SUSMITHA")
    assert resume.headline.startswith("Data Engineer")
    contact = " | ".join(resume.contact_lines)
    assert "Scottsdale" not in contact
    assert "Austin" in contact
    assert "susmitha chowdary" not in contact.lower()


def test_skills_keep_categories_after_tailor(tmp_path: Path):
    resume = load_base_resume(BASE)
    result = tailor(resume, _sample_jd())
    assert "\n" in result.version_a.skills_raw
    assert "Candidate aligned" not in result.version_a.summary
    assert "Programming & Processing:" in result.version_a.skills_raw or "Python" in result.version_a.skills_raw

    out = tmp_path / "out.docx"
    build_ats_docx(result.version_a, out)
    plain = extract_plain_text_from_docx(out)
    assert "Candidate aligned" not in plain
    assert plain.lower().count("susmitha chowdary") == 1
    assert "Technical Skills" in plain
    assert "Scottsdale" not in plain
