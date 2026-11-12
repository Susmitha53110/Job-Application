# First applies runbook — 2026-11-12 08:00 CT

Authorized real ATS work. Never Easy Apply. Do not invent salary.

## Order
1. **Clera** — Senior Data Integration Engineer (b=9.7, no salary field)
2. **Bayesian Health** — SWE Data & Analytics Platform (b=7.5, no salary field)
3. **BetterHelp** — Senior Analytics Engineer (b=7.2; STOP if salary/EEO/CAPTCHA) — kit `BetterHelp_SUBMIT_KIT.md`
4. **Life360** — Senior Data Engineer, Ads Data (b=7.3; STOP if salary/EEO/CAPTCHA) — kit `Life360_SUBMIT_KIT.md`
5. **Curve Dental** — only if `python3 -m agent curve-gate` → ok

## Commands
```bash
python3 -m agent window
python3 -m agent handoff
python3 -m agent ready-submits
python3 -m agent daily
python3 -m agent curve-gate
```

Prefer short resumes under `resumes/submit/Susmitha_{clera,bayesian,betterhelp,life360,curve}.docx` (PDF copies also available where built).  
Use computer-use prompts from `reports/<CT-day>/SUBMIT_HANDOFF.json`, `READY_SUBMITS.md`, and `SUBMIT_NOW.md`.

## Proof paths
- `applications/applied/2026-11-12/Clera_Senior_Data_Integration_Engineer/`
- `applications/applied/2026-11-12/Bayesian_Health_Software_Engineer_Data_Analytics_Platform/`
- `applications/applied/2026-11-12/BetterHelp_Senior_Analytics_Engineer/`
- `applications/applied/2026-11-12/Life360_Senior_Data_Engineer_Ads_Data/`
- `applications/applied/2026-11-12/Curve_Dental_Data_Engineer/` (if salary set)

Then:
```bash
python3 -m agent proof --company "Clera" --role "Senior Data Integration Engineer" --url <url> --file <proof>...
```
