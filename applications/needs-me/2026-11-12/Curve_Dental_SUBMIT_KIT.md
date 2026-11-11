# Curve Dental — Rippling submit kit

**Do not submit outside 08:00–12:00 America/Chicago.**  
**Do not submit until salary expectations number is in Memory/FORM_ANSWERS.**

- Job: Data Engineer
- ATS: https://ats.rippling.com/curve-dental/jobs/81161b01-ae38-49d2-9ca8-3b618d31c394
- Posted (`createdOn`): 2026-11-11 · still ≤4 days as of kit write
- Resume (a): `resumes/tailored/2026-11-11/Susmitha_Curve_Dental_Data_Engineer.docx`
- Score override: authorized (`curve_dental_score_override: true`)
- EEO questionnaire enabled on this post → Prefer not to disclose / needs me if forced

## Basic fields
| Field | Value |
|-------|-------|
| First name | Susmitha |
| Last name | Chowdary |
| Email | Susmithachowdary67@gmail.com |
| Pronouns | Skip |
| Current company | Optum |
| Phone number | 9132073787 |
| Location (city only) | Austin |
| Resume | Upload tailored (a) `.docx` |
| Cover letter | Skip |

## Questionnaire (from Rippling API)
| Question | Answer |
|----------|--------|
| Will you now or in the future require sponsorship to work in the US? | **No** |
| How many years of related experience do you have? | **5** |
| Do you have a home office, with reliable internet, that you can work from? | **Yes** |
| Describe a data platform you built or significantly improved… | See draft below |
| What are your salary expectations for this role? | **NEEDS ME — paste exact number from Memory** |
| How did you hear about, or where did you find, this job posting? | Company careers / Rippling ATS research |

### Platform story (resume facts only)
At Optum I own production Azure Data Factory + Databricks ingestion into ADLS Gen2 / Delta Lake bronze-silver-gold for claims, eligibility, and provider feeds, and deliver Snowflake loads via external stages, COPY INTO, and MERGE for analytics dimensions. I cut new-source onboarding from ~2 weeks to ~4 days with a config-driven PySpark framework, reduced a claims workflow from ~2 hours to 75 minutes, and raised scheduled pipeline success from ~97% to 99.5% with dependency checks, bounded retries, and idempotent backfills. Honest gap if asked: JD prefers 2+ years production Snowflake and dbt/Fivetran; my Snowflake production ownership is since May 2025, and I do not claim production dbt/Fivetran ownership.

## Submit + proof
1. Confirm window open (`python3 -m agent window`) and salary present (`python3 -m agent ready`).
2. Fill Rippling form from this kit; never Easy Apply.
3. After submit, save confirmation page screenshot/HTML + any email confirmation under:
   `applications/applied/2026-11-12/Curve_Dental_Data_Engineer/`
4. Append CSV + APPLIED_INDEX with status `applied` only if proof exists; else `unconfirmed`.
5. If CAPTCHA/login wall → `needs me` and stop this job.
