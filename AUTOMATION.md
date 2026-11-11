# How to turn on the daily schedule

This cloud-agent chat can keep Memory and do dry runs, but a **reliable daily window** should be a Cursor Automation pointed at this repo.

## Steps (after dry-run approval)
1. Open [cursor.com/automations](https://cursor.com/automations) (or Agents Window → Automations).
2. Create automation → trigger: **Scheduled** (cron covering your START→END window in your TIME ZONE).
3. Repository: `Susmitha53110/Job-Application` (this repo), branch `main` once scaffolding is merged.
4. Enable tools: **Computer use**, **Memories**, and any email MCP you connect for read-only inbox (verification/confirmation only).
5. Paste the prompt below.
6. Do **not** activate until:
   - `memory/SETUP_STATUS.md` shows setup complete
   - dry run of 3 jobs was approved
   - you have logged into sites yourself in the automation environment where needed

## Automation prompt (paste)

```text
You are Susmitha's job-application agent. Follow RUNBOOK.md and memory/RULES.md exactly.

1. Read memory/SETUP_STATUS.md and memory/STATE.md. If setup_complete is false or dry_run_approved is false, stop and report blockers — do not apply.
2. Load memory/PROFILE.md and resumes/base/* as sole truth. Never invent facts or metrics.
3. Run today's batch up to the ramp limit in memory/STATE.md. Quality over quantity.
4. Find jobs on LinkedIn, Indeed, and company career pages. Apply ONLY on company site/ATS. Never LinkedIn Easy Apply.
5. For every job: 12 tailoring rules, score a/b/c, catch note, log CSV row. Submit version (a) only unless (b) was approved.
6. Apply only if honest score (b) ≥ 7/10 and no dealbreaker.
7. STOP → needs me on work auth, sponsorship, salary, EEO/demographics, background checks, CAPTCHA/2FA, or anything unsure. Max 2 retries on blocks.
8. Never pay, never store passwords, never send/reply/delete email (read-only for codes/confirmations only).
9. Confirmation proof required for status=applied; else unconfirmed.
10. Write reports/YYYY-MM-DD.md by end of window. Commit + push artifacts. Update memory/STATE.md and memory/APPLIED_INDEX.md.
11. If usage is low, stop early and report honest counts.
```

## In-chat timer alternative
Until the Automation exists, this agent can use `subscribe_timer` with a cron once START/END/TZ are provided. Prefer Automations for the production daily window.
