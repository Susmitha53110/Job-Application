# Waiting on window — 2026-11-12

Outside **08:00–12:00 America/Chicago**. Real ATS submits start at **08:00 CT**.

## Auto-submit order (computer-use)
1. **Clera** — Ashby — no salary field — prompt in `SUBMIT_HANDOFF.json` / `READY_SUBMITS.md`
2. **Bayesian Health** — Ashby — sponsorship **No** — paste why-fit from kit
3. **Life360** — Greenhouse — Country US / City Austin / auth Yes / sponsorship No
4. **Curve Dental** — only if `python3 -m agent curve-gate` ok (salary still MISSING)

## Skip / needs-me
- Talkiatry Analytics Engineer — scored **5.0** (dbt/BigQuery/BI gaps); logged skip
- BetterHelp — 5-year no-sponsorship gate
- Velosio — iCIMS login + CAPTCHA
- Instructure Senior Analytics Engineer — Ashby near-miss (published 2026-11-06; >4d)

## Commands at 08:00 CT
```bash
python3 -m agent window
python3 -m agent go-nogo
python3 -m agent handoff
python3 -m agent ready-submits
python3 -m agent daily
```
Then computer-use each `computer_use_prompt` from `reports/2026-11-12/SUBMIT_HANDOFF.json` in order.
Never Easy Apply. Never invent salary.
