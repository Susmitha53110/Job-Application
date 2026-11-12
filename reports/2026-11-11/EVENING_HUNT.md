# Evening hunt — 2026-11-11

Window closed (after 12:00 CT). Preparing for **2026-11-12 08:00 CT**.

## Approvals locked this evening
- LinkedIn: https://www.linkedin.com/in/susmitha-dodla-a05ab92b8
- Sponsorship answer: **No**
- Real ATS work after dry-run: **yes**
- Next filter-pass dry-run packet: **Curve Dental** approved (score override for this packet)

## API / ATS results (US · remote · open · ≤4 days)
| Company | Role | Posted | Score b | Decision |
|---------|------|--------|---------|----------|
| Curve Dental | Data Engineer | 2026-11-11 | 5.6 | **Apply when salary + window** (approved override) |
| Consumer Edge | Staff Data Engineer | 2026-11-09 | 2.5 | Skip / stretch (8+ yrs) |
| Keebo | Senior Data Engineer | 2026-11-10 | n/a | Skip (no visa support) |

## Fail-closed skips (date)
- Base Operations Data Engineer (Ashby) — published 2026-10-29
- WorkOS Data Engineer (Ashby) — published 2026-10-06
- Discord / Samsara / Cloudflare DE listings — first_published older than 4 days or not US-remote

## Tooling added
- `agent/window.py` — CT window gate
- `agent/ats_hunt.py` — Greenhouse / Ashby / Rippling hunter with fail-closed dates
- `applications/FORM_ANSWERS.md` — form bank
- `applications/needs-me/2026-11-12/MORNING_CHECKLIST.md`

## Later evening refresh (~17:20 CT)
- `python3 -m agent ready` → **0 ready** (window closed + salary missing)
- Extra Greenhouse/Lever/Rippling/Remotive scan: no new mid-level ≤4d US-remote DE hits
- PerfectServe Data Engineer first_published 2026-09-24 → skip
- Browser hunts could not verify posting dates on ATS pages; API dates remain authoritative

## Blocker for submits
Salary expectations number still unset.
