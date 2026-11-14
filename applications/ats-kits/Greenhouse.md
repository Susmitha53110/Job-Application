# Greenhouse ATS kit

Standing answers: `applications/FORM_ANSWERS.md`  
Email: **dsusmitha55@gmail.com**

## Typical fields
- First/Last, Email, Phone, Country, City, Resume
- LinkedIn blank / N/A / URL placeholder if required
- Auth Yes · Sponsorship No · Prior employee No · Privacy Yes when shown
- EEO per FORM_ANSWERS · Salary 120000 if asked · How heard: Company website
- Multi-year “without sponsorship” → Yes
- Non-compete → **No**

## Email security code / reCAPTCHA
Many boards now send an **8-character code** to email (“confirm you're a human”) into `#security-input-0`…`7`.
- Gmail MCP declined → Susmitha must **paste the code in chat** while the form session is live
- Do not re-click Submit before entering the code (invalidates prior codes)
- Helper: `agent/greenhouse_pw.py` (`submit_greenhouse_basic`)

## Prefer direct job-board / embed URLs
Example MongoDB: `https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433`  
(company career-site wrappers often hide the form in iframes)

## Known boards
- BetterHelp, Life360, MongoDB, Machinify, Natera, Constant Contact, Consumer Edge, Keebo

Prefer Greenhouse job-board HTML/API over screenshots when possible.
