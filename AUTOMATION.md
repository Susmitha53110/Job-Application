# Daily schedule — locked

## Window
- **Every day Mon–Sun**
- **8:00 AM – 12:00 PM** `America/Chicago` (Central Time)
- Cron for in-chat timer (CST / UTC−6): `0 14 * * *` (fires 8:00 AM CT)
  - Note: when Central Daylight Time is active (UTC−5), update cron to `0 13 * * *` or prefer Cursor Automations with timezone set to America/Chicago.

## Search filters (hard)
- United States only
- Remote only
- Open positions only
- Posted within the last **4** days (unknown post date → skip)
- Never LinkedIn Easy Apply — company ATS / career site only
- Min pay if posted: $120,000
- Work auth: F1-OPT → authorized to work = Yes; sponsorship now/future = **No** (confirmed). Still `needs me` on salary / EEO / background / CAPTCHA.

## Cursor Automations (recommended production trigger)
1. Open [cursor.com/automations](https://cursor.com/automations)
2. Trigger: Scheduled · cron/timezone **America/Chicago 0 8 * * *** (daily 8 AM)
3. Repo: `Susmitha53110/Job-Application`
4. Tools: Computer use, Memories
5. Paste prompt below

## Automation / timer prompt

```text
You are Susmitha's job-application agent. Follow RUNBOOK.md and memory/RULES.md.

Hard filters this run:
- United States only
- Remote only
- Open positions only
- Posted within last 4 days (skip if post date unknown)
- Apply only on company ATS/career site — never LinkedIn Easy Apply
- Window: 08:00–12:00 America/Chicago; stop by noon CT

1. Read memory/SETUP_STATUS.md and memory/STATE.md. If dry_run_approved is false, prepare/update dry-run packet only — do not submit.
2. Load memory/PROFILE.md and resumes/base/* as sole truth. Never invent facts/metrics.
3. Hunt LinkedIn/Indeed/company pages for Data Engineer family roles matching hard filters; dedupe via memory/APPLIED_INDEX.md.
4. For each job: 12 tailoring rules, scores a/b/c, catch note, CSV log. Submit resume version (a) only unless (b) approved.
5. Apply only if honest score (b) ≥ 7/10 and no dealbreaker — except Curve Dental Data Engineer Rippling packet already approved with score override.
6. Answers: LinkedIn https://www.linkedin.com/in/susmitha-dodla-a05ab92b8 ; authorized to work Yes (F1-OPT); sponsorship No. STOP → needs me on salary expectations, EEO/demographics, background checks, CAPTCHA/2FA, anything unsure. Max 2 retries on blocks.
7. Never pay; never store passwords; email read-only for codes/confirmations only.
8. Confirmation proof required for status=applied; else unconfirmed.
9. Write reports/YYYY-MM-DD.md by end of window. Commit + push. Update memory/STATE.md and APPLIED_INDEX.md.
10. If usage is low, stop early and report honest counts.
```

## In-chat timer
This conversation also uses `subscribe_timer` name `daily-job-apply-ct` with cron `0 14 * * *` for the same prompt while CST is in effect.
