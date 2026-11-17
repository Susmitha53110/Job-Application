# Submit kit — Block / Sales Compensation Systems & Data Engineer
- URL (embed): `https://job-boards.greenhouse.io/embed/job_app?for=block&token=5485151008`
- URL (careers): `http://block.xyz/careers/jobs/5485151008?gh_jid=5485151008`
- ATS: greenhouse
- Age: posted 2026-11-17 (≤10d OK as of prep)
- Resume: `resumes/tailored/2026-11-17/Susmitha_Block_Sales_Compensation_Systems_Data_Engineer.docx`
- Fill-only proof: `applications/ready/2026-11-18/Block_Sales_Comp_DE/fill_only.png` + `FILL_ONLY.json`
- Standing answers: work auth Yes · sponsorship **No** · salary 120000 · relocate Yes · EEO Female/Asian · prior Block No · contract No · certify Yes
- Quirks: set **Country = United States** before phone; Location City typeahead Austin; Legal First/Last required; CAPTCHA/OTP possible
- **Submit only 08:00–12:00 CT**. Outside window = fill_only.

## Automation
- `python3 -c` / `submit_greenhouse_basic(..., fill_only=True)` smoke passed 2026-11-17
- Proof: `applications/ready/2026-11-18/Block_Sales_Comp_DE/gh_pw_fill_only/`
- At 08:00 CT: same helper with `fill_only=False` (window gated) or CDP submit
