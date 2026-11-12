# Job-Application agent workspace

Persistent workspace for Susmitha's Cursor job-application agent.

## Layout
- `memory/` — profile, rules, state, applied index (agent Memory)
- `resumes/base/` — **only** source-of-truth resume
- `resumes/tailored/` — per-job `.docx` outputs (`FirstName_Company_Role.docx`)
- `logs/applications.csv` — one row per job
- `reports/` — end-of-day reports
- `applications/` — proof / needs-me / skipped packets
- `interview-prep/` — Q&A for fits ≥ 8/10
- `RUNBOOK.md` — daily procedure
- `AUTOMATION.md` — how to schedule daily runs

## Current status
**Blocked on setup.** Fill `memory/PROFILE.md`, drop the base resume into `resumes/base/`, then ask the agent to run the first 3-job dry run.
