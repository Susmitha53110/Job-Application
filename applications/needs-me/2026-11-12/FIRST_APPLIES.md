# First applies runbook — 2026-11-12 08:00 CT

Authorized real ATS work. Never Easy Apply. Do not invent salary.

## Order
1. **Clera** — Senior Data Integration Engineer (b=9.7, no salary field)
2. **Bayesian Health** — SWE Data & Analytics Platform (b=7.5, no salary field)
3. **Curve Dental** — only if `python3 -m agent curve-gate` → ok

## Commands
```bash
python3 -m agent window
python3 -m agent ready-submits
python3 -m agent daily
python3 -m agent curve-gate
```

Use computer-use prompts from `reports/<CT-day>/READY_SUBMITS.md` and `SUBMIT_NOW.md`.

## Proof paths
- `applications/applied/2026-11-12/Clera_Senior_Data_Integration_Engineer/`
- `applications/applied/2026-11-12/Bayesian_Health_Software_Engineer_Data_Analytics_Platform/`
- `applications/applied/2026-11-12/Curve_Dental_Data_Engineer/` (if salary set)

Then:
```bash
python3 -m agent proof --company "Clera" --role "Senior Data Integration Engineer" --url <url> --file <proof>...
```
