# Nightly handoff — 2026-11-11 (~17:50 CT)

## Goal status
Agent is authorized for real ATS work. No confirmed `applied` yet.

## Gates for first submit
1. Window **08:00–12:00 America/Chicago** (currently closed)
2. Salary number in Memory / `applications/FORM_ANSWERS.md` (currently MISSING — see `applications/needs-me/SALARY.md`)
3. Curve still open + ≤4 days (API `createdOn` 2026-11-11 — currently OK)

## Morning command sequence
```bash
python3 -m agent window
python3 -m agent daily
python3 -m agent curve-gate
# if salary arrived: python3 -m agent set-salary <number>
# if curve-gate ok / SUBMIT_NOW.md exists → computer-use with that prompt
# then: python3 -m agent proof --company "Curve Dental" --role "Data Engineer" --url <url> --file <proof>
python3 -m agent watchlist
```

## Queue
- Curve Dental: submit kit ready, score override on
- Consumer Edge / Keebo: skip
- Watchlist mid-level poll (~18:00 CT): **only Curve** still passes US-remote ≤4d
