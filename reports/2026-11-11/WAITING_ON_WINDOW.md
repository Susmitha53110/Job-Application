# Waiting on apply window

Updated: 2026-11-11 ~19:55 America/Chicago

## Status
- Window: **closed** until **2026-11-12 08:00 CT**
- Salary: **MISSING** (blocks Curve only)
- Clera: packet-ready (b=9.7), dry-fill proven, no salary field
- Bayesian Health: packet-ready (b=7.5), dry-fill proven, no salary field
- Curve Dental: packet-ready (b=8.1) except salary + window

## Armed timers
- `morning-prep-7am-ct` once → 07:00 CT
- `first-applies-8am-ct` once → 08:00 CT (Clera → Bayesian → Curve-if-salary)
- `daily-job-apply-ct` cron `0 14 * * *` UTC
- `overnight-job-hunt` cron `0 2,5,8,11 * * *` UTC

## Morning entrypoint
```bash
python3 -m agent handoff
python3 -m agent ready-submits
```
See `applications/needs-me/2026-11-12/FIRST_APPLIES.md` and `reports/2026-11-12/SUBMIT_HANDOFF.json`.
