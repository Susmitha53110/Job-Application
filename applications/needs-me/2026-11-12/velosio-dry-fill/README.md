# Velosio — form inspect (dry, no submit)

**Date:** 2026-11-12  
**Job:** https://careers.velosio.com/jobs/3162  
**ATS:** iCIMS  

## Screenshots
- `velosio_job_page.png` — job posting
- `velosio_form_0_email.png`
- `velosio_form_1_CAPTCHA_BLOCKER.png` — hCaptcha on login step — apply lands on **Enter Your Information** (Email + Next) at  
  `https://careers-velosio.icims.com/jobs/3162/login?...`  
  Protected by **hCaptcha**.

## Blockers
1. **Candidate login / email gate** before any application fields — agent **STOP → needs-me** (never create accounts / never store passwords).
2. **hCaptcha** on the login step.
3. Salary / sponsorship / EEO fields unknown until after Susmitha signs in.
4. Never use Indeed Easy Apply (feed enabled on site config).

## Packet
Tailored resume ready (`resumes/submit/Susmitha_velosio.docx`), score **b=8.7**.  
Auto-submit queue: **excluded** until Susmitha completes iCIMS login herself.
