# Velosio — form inspect (dry, no submit)

**Date:** 2026-11-12  
**Job:** https://careers.velosio.com/jobs/3162  
**ATS:** iCIMS  
**Inspected by:** [Velosio ATS form inspect](bc-4825365d-76c9-5f4f-a2a2-b870aeb1f426)

## Flow observed
1. Job page loads → Apply
2. Redirect to `careers-velosio.icims.com/jobs/3162/login` — **Enter Your Information** (Email + Next)
3. After email + Next → **CAPTCHA** (“Click the TWO matching shapes”) **before any application fields**
4. Form fields (name, resume, auth, salary, EEO, …) **inaccessible** without solving CAPTCHA

## Screenshots
- `velosio_job_page.png` — job posting
- `velosio_form_0_email.png` — email gate
- `velosio_form_1_CAPTCHA_BLOCKER.png` — CAPTCHA hard stop

## Blockers (needs-me)
1. Candidate email / login gate — never create accounts or store passwords
2. **CAPTCHA** immediately after email (agent cannot solve)
3. Post-login fields unknown until Susmitha clears CAPTCHA
4. Never Indeed Easy Apply

## Dry-fill feasibility
**Not possible** for the agent. Susmitha must apply manually (or clear CAPTCHA herself) then agent can continue only if she hands off an unlocked session — prefer she completes the apply herself with the packet resume.

## Packet
`resumes/submit/Susmitha_velosio.docx` (b=8.7). Auto-submit queue: **excluded**.
