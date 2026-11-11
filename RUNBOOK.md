# Daily job-application runbook

Read `memory/SETUP_STATUS.md` first. If setup is blocked, do **not** apply — report blockers and stop.

## Every run
1. Load Memory: `memory/PROFILE.md`, `memory/RULES.md`, `memory/APPLIED_INDEX.md`, `logs/applications.csv`.
2. Confirm base resume exists in `resumes/base/` (single source of truth). Parse it; never invent facts.
3. Compute today's daily limit from ramp day count in `memory/STATE.md`.
4. Search LinkedIn, Indeed, and company career pages for target roles with hard filters: **United States only**, **Remote only**, **open positions only**, **posted within last 4 days** (skip if post date unknown). Only work inside **08:00–12:00 America/Chicago**, every day Mon–Sun.
5. Deduplicate against `memory/APPLIED_INDEX.md` and prior log rows.
6. For each candidate job, run the 12 tailoring rules in order.
7. Skip immediately on dealbreaker failure; log `skipped` + reason.
8. Build version (a) reorder-only `.docx` and version (b) hedged (do not submit b without approval).
9. Score a/b/c; apply only if honest (b) ≥ 7/10 **and** this is not a first-run dry-run waiting on approval.
10. Prefer company ATS / career site. Never LinkedIn Easy Apply.
11. On form uncertainty → `needs me` with exact action for Susmitha.
12. On submit: keep confirmation proof under `applications/applied/YYYY-MM-DD/`. No proof → `unconfirmed`.
13. Append one CSV row per job; write catch note + interview prep (8+) files.
14. By END TIME: write `reports/YYYY-MM-DD.md` daily report sections 1–7.
15. Commit artifacts to the working branch and push. Update Memory state (day count, last run).

## First run (once)
1. Select 3 jobs only.
2. Produce for each: tailored resume (a)+(b), score table, catch note, filled-form preview.
3. Status = `needs me` / awaiting approval. **Do not submit.**
4. Wait for Susmitha's explicit approval before any real submits or daily schedule activation.

## Status values
| Status | Meaning |
|--------|---------|
| `applied` | Submit confirmed with proof saved |
| `unconfirmed` | Attempted; no proof |
| `skipped` | Dealbreaker / low score / duplicate / out of scope |
| `needs me` | Requires Susmitha's action or answer |
| `dry-run` | Prepared for approval; not submitted |

## Daily report template
See `templates/daily-report.md`.
