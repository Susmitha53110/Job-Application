# Curve Dental Rippling form map (inspect-only 2026-11-11 evening)

Source: live browser inspection + Rippling API `activeJobApplication`.  
**Not submitted.** Screenshots: `curve-form-screenshots/`.

## Page status
- Open, no login, no CAPTCHA
- Single-page form; final control is **Apply**
- EEOC questionnaire enabled (voluntary)

## Field order → Memory answer

| # | Label | Required | Type | Answer |
|---|-------|----------|------|--------|
| 1 | Resume | yes | file .doc/.docx/.pdf | `resumes/tailored/2026-11-12/Susmitha_Curve_Dental_Data_Engineer.docx` |
| 2 | First name | yes | text | Susmitha |
| 3 | Last name | yes | text | Chowdary |
| 4 | Email | yes | email | Susmithachowdary67@gmail.com |
| 5 | Pronouns | no | select | skip |
| 6 | Current company | no | text | Optum |
| 7 | Phone number | yes | phone (+1) | 9132073787 |
| 8 | Location (city only) | yes | autocomplete | Austin (or Austin, TX if required) |
| 9 | Cover letter | no | file | skip |
| 10 | Will you now or in the future require sponsorship to work in the US? | yes | select Yes/No | **No** |
| 11 | How many years of related experience do you have? | yes | text | **5** |
| 12 | Do you have a home office, with reliable internet, that you can work from? | yes | select Yes/No | **Yes** |
| 13 | Describe a data platform you built or significantly improved… | yes | textarea | Platform story in submit kit |
| 14 | What are your salary expectations for this role? | yes | text | **NEEDS ME** until Memory set |
| 15 | How did you hear about, or where did you find, this job posting? | yes | text | Company careers / Rippling ATS research |
| 16 | Gender | no | select | Choose not to disclose |
| 17 | Please identify your race | no | select | Choose not to disclose |
| 18 | Are you Hispanic/Latino? | no | select | Choose not to disclose |
| 19 | Veteran Status | no | select | Choose not to disclose |
| 20 | Text message consent… | yes (pick one) | radio | **No - I do not consent to receiving text messages** |

## Not on this form
- LinkedIn URL field
- Background-check Yes/No
- Work-authorization Yes/No (only sponsorship knockout)

## Blockers for submit
1. Salary number missing
2. Outside 08:00–12:00 America/Chicago until 2026-11-12 08:00 CT
