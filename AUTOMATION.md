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

1. `python3 -m agent daily` then `python3 -m agent curve-gate`.
2. If salary missing (`applications/needs-me/SALARY.md`), STOP needs-me for salary; still hunt/prepare.
3. If curve-gate ok: computer-use submit using prompt in `reports/*/CURVE_GATE.md` / submit kit; resume (a); sponsorship No; text consent No; skip voluntary EEO.
4. Hunt more ≥7 mid-level US-remote ≤4d ATS roles; tailor per RULES; dedupe APPLIED_INDEX.
5. Skip Keebo / Consumer Edge Staff unless override.
6. Proof via `python3 -m agent proof`. Commit + push. Stop by 12:00 CT.
```

## In-chat timer
This conversation also uses `subscribe_timer` name `daily-job-apply-ct` with cron `0 14 * * *` for the same prompt while CST is in effect.
