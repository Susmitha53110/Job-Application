# Filter + schedule update — 2026-11-11

## Locked by Susmitha
- Geography: **United States only**
- Work mode: **Remote only**
- Status: **Open positions only**
- Recency: **Posted/opened within last 4 days** (unknown date → skip)
- Schedule: **Monday–Sunday, 8:00 AM – 12:00 PM America/Chicago**

## Prior dry-run re-screen (new filters)
| Company | Result | Why |
|---------|--------|-----|
| Tebra Data Engineer | **SKIP** | Greenhouse `first_published` 2026-07-27 (older than 4 days) |
| People Data Labs Data Engineer | **SKIP** | Post date not verifiable from ATS → fail closed under 4-day rule |
| Troveo AI Data Engineer | **SKIP** | Post date not verifiable from ATS → fail closed under 4-day rule |

Filled previews remain on disk for reference but must **not** be submitted unless a role is re-confirmed as open + ≤4 days + US remote.

## Fresh hunt snapshot (same evening)
Automated Remotive/Arbeitnow/Greenhouse board scan under the new filters returned **no strong US-remote Data Engineer ATS matches with verified post date ≤4 days** that also clear dealbreakers (e.g. Keebo posted ~1d ago but “visa support will not be provided”; Lyft DE posted 2026-11-10 is Toronto).

Next scheduled window (tomorrow 08:00 CT) will hunt LinkedIn/Indeed/company pages with browser + company ATS only, still no Easy Apply, and still no submits until dry-run approval + needs-me answers.

## Schedule activation
- Memory `window_start=08:00`, `window_end=12:00`, `timezone=America/Chicago`, daily Mon–Sun
- In-chat timer `daily-job-apply-ct` cron `0 14 * * *` (08:00 CT while on CST / UTC−6)
- Also documented in `AUTOMATION.md` for Cursor Automations with timezone America/Chicago
