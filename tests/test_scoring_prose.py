from agent.jd_tier import tier_jd
from agent.score import score_resume_against_jd
from agent.resume_parse import parse_markdown_resume


CURVE_PROSE = """
What you bring Required 3–6 years in data engineering, with at least 2 years running production
workloads on Snowflake Strong knowledge and skills in SQL and Python Hands-on experience with a
modern transformation framework such as dbt: modeling, testing, documentation Experience with
managed ELT tools (such as Fivetran or Airbyte) A track record of building dimensional or entity
models that business users trust
"""

KIT_PROSE = """
Experiences - Around 7 or more years in analytics engineering or data engineering where you
personally shipped production data models. Deep dbt. Advanced SQL. Python. Redshift. BI tools.
"""


def _tiny_resume():
    md = """
# SUSMITHA CHOWDARY
Data Engineer | Python · SQL · PySpark · Databricks · Snowflake · Azure · AWS
Susmithachowdary67@gmail.com | 9132073787

## Summary
Data engineer with Python, SQL, PySpark, Databricks, Snowflake, Azure Data Factory.

## Experience
### Data Engineer — Optum
May 2025 – Present
- Built production Azure Data Factory and Databricks pipelines into Delta Lake and Snowflake.

## Skills
Python, SQL, PySpark, Databricks, Snowflake, Azure Data Factory, ADF, ETL, ELT

## Education
MS Computer Science
"""
    return parse_markdown_resume(md)


def test_curve_prose_scores_at_least_seven():
    resume = _tiny_resume()
    jd = tier_jd("Data Engineer", "Curve Dental", "https://example.com", "Remote US", CURVE_PROSE)
    assert jd.required, "expected synthesized requirements"
    score = score_resume_against_jd(resume, jd, my_years=5)
    assert score.fit_10 >= 7.0, score


def test_kit_senior_below_seven_with_years_stretch():
    resume = _tiny_resume()
    jd = tier_jd("Senior Analytics Engineer", "Kit", "https://example.com", "Remote", KIT_PROSE)
    score = score_resume_against_jd(resume, jd, my_years=5)
    # 7+ years stretch + dbt-heavy should not clear 7 on reorder-only without hedges
    assert score.fit_10 < 7.0, score
