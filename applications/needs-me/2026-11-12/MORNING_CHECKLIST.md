# Morning apply checklist — 2026-11-12 08:00 CT

## Gate checks (in order)
1. `python3 -m agent window` → must show `"open": true`
2. `python3 -m agent curve-gate` → `"ok": true` and non-empty computer-use prompt
3. `python3 -m agent ready` / `python3 -m agent daily`
4. Re-verify Curve `createdOn` still ≤4 days via Rippling API
5. Ramp day 1 daily limit: **10**
6. Resume version **(a)** only

## Still blocking ALL submits until answered
- **Salary expectations number** — chat `Salary expectations: <n>` or `applications/needs-me/SALARY_REPLY.md` or `python3 -m agent set-salary <n>`
- CAPTCHA / login wall → needs me, move on

## Curve-specific (form inspected 2026-11-11 — not submitted)
- Full field map: `CURVE_FORM_MAP.md`
- Submit kit: `Curve_Dental_SUBMIT_KIT.md`
- Resume: `resumes/tailored/2026-11-12/Susmitha_Curve_Dental_Data_Engineer.docx`
- Scores **8.1 / 8.1 / 10.0**
- EEO: **Choose not to disclose** on each voluntary dropdown
- Text consent: **No**
- Background-check question: **not on this form**
- After submit: `applications/applied/2026-11-12/Curve_Dental_Data_Engineer/` + `python3 -m agent proof …`

## Also hunt
- Mid-level US-remote ≤4d ATS roles via `python3 -m agent overnight` / `daily`
- Kit Senior AE (b=6.7) → skip unless override
- Keebo / Consumer Edge Staff → skip unless override
- Near-miss 5–10d watch only — do not apply

## Proof rule
Confirmation page/email proof required for `applied`; else `unconfirmed`.
