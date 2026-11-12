# Curve Dental — Rippling submit kit

**Do not submit outside 08:00–12:00 America/Chicago.**  
**Do not submit until salary expectations number is in Memory/FORM_ANSWERS.**

- Job: Data Engineer
- ATS: https://ats.rippling.com/curve-dental/jobs/81161b01-ae38-49d2-9ca8-3b618d31c394
- Posted (`createdOn`): 2026-11-11T09:43:45-08:00 · ≤4 days fail-closed
- Resume (a): `resumes/tailored/2026-11-12/Susmitha_Curve_Dental_Data_Engineer.docx`
- Scores: **8.1 / 8.1 / 10.0** (honest b ≥ 7; override kept as backup)
- Form map: `CURVE_FORM_MAP.md` (live inspect 2026-11-11; no login/CAPTCHA)
- Gaps to disclose if asked: dbt; BI tools; Snowflake prod tenure since May 2025 vs JD ~2 yrs

## Fill order (exact UI)
1. **Resume*** — upload tailored `.docx` (a)
2. **First name*** — Susmitha
3. **Last name*** — Chowdary
4. **Email*** — Susmithachowdary67@gmail.com
5. **Pronouns** — skip
6. **Current company** — Optum
7. **Phone number*** — +1 9132073787
8. **Location*** — Austin (Austin, TX if autocomplete requires)
9. **Cover letter** — skip
10. **Sponsorship now/future?*** — **No**
11. **Years of related experience?*** — **5**
12. **Home office + reliable internet?*** — **Yes**
13. **Data platform story*** — draft below
14. **Salary expectations?*** — paste Memory number only (NEEDS ME until set)
15. **How did you hear?*** — Company careers / Rippling ATS research
16–19. **EEO voluntary** — each **Choose not to disclose** (Gender, Race, Hispanic/Latino, Veteran)
20. **Text message consent*** — **No - I do not consent to receiving text messages**
21. Click **Apply** once

### Platform story (resume facts only)
At Optum I own production Azure Data Factory + Databricks ingestion into ADLS Gen2 / Delta Lake bronze-silver-gold for claims, eligibility, and provider feeds, and deliver Snowflake loads via external stages, COPY INTO, and MERGE for analytics dimensions. I cut new-source onboarding from ~2 weeks to ~4 days with a config-driven PySpark framework, reduced a claims workflow from ~2 hours to 75 minutes, and raised scheduled pipeline success from ~97% to 99.5% with dependency checks, bounded retries, and idempotent backfills. Honest gap if asked: JD prefers 2+ years production Snowflake and dbt/Fivetran; my Snowflake production ownership is since May 2025, and I do not claim production dbt/Fivetran ownership.

## Submit + proof
1. Confirm window open (`python3 -m agent window`) and salary present (`python3 -m agent curve-gate`).
2. Computer-use with `reports/<day>/CURVE_GATE.md` prompt (only when gate ok).
3. After submit, save confirmation under `applications/applied/<CT-day>/Curve_Dental_Data_Engineer/` + artifact screenshot.
4. `python3 -m agent proof --company "Curve Dental" --role "Data Engineer" --url <url> --file <proof>…`
5. CAPTCHA/login/error → `needs me` and stop this job.
