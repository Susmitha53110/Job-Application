# DE discovery — 2026-11-27 (live hunt)

Ran `python3 -m agent hunt` (30 hits) plus extra Greenhouse board probes
(`selffinancial`, `onxmaps`, `codepath`, `oddball`, `sonyinteractiveentertainmentglobal`)
and Lever `bluesight`. Filters: DE / Sr DE, ≤10d, USA remote or Austin hybrid/onsite,
honest score (b) ≥8.5, not `status=applied` in APPLIED_INDEX, exclude
Citi/Optum/Jobgether/Velosio, exclude citizen/clearance/ITAR-only.

## Submit-today candidates (company ATS)

| Company | Title | Age | Loc | Score (b) | Applied? | URL | Notes |
|---------|-------|-----|-----|-----------|----------|-----|-------|
| Bluesight | Data Engineer | ~1.9d | US Remote | **10.0** | No (needs-me: Lever hCaptcha from 11-26) | https://jobs.lever.co/bluesight/8a3408a8-6909-4b66-92c1-98a5c80ba0a9 | Best fit; company Lever ATS; form previously filled |

## Blocked by citizen / clearance / ITAR (do not submit)

| Company | Title | Age | Score (b) | URL | Why |
|---------|-------|-----|-----------|-----|-----|
| SpaceX | Data Engineer, Application Software | ~1.8d | 8.5 | https://boards.greenhouse.io/spacex/jobs/8957969002?gh_jid=8957969002 | ITAR: US citizen / green card / export auth; also reCAPTCHA |
| SpaceX | Data Engineer, Hardware Reliability (Starlink) | ~3.6d | 7.9 | https://boards.greenhouse.io/spacex/jobs/8957339002?gh_jid=8957339002 | Same ITAR + below 8.5 |
| Oddball | Data Engineer | ~5.6d | 10.0 | https://job-boards.greenhouse.io/oddball/jobs/8213810003 | Clearance / background investigation dealbreaker |
| Oddball | Senior Data Engineer | ~5.6d | 10.0 | https://job-boards.greenhouse.io/oddball/jobs/8213809003 | Same |

## Near-miss (company ATS, not applied, score &lt; 8.5)

| Company | Title | Age | Loc | Score (b) | URL |
|---------|-------|-----|-----|-----------|-----|
| Clera | Senior Data Engineer | ~1.9d | remote | 8.4 | https://jobs.ashbyhq.com/Clera/acc9ce9f-1a6f-46e1-b380-bcbcd250ed74 |
| Clera | Senior Data Engineer | ~4.9d | remote | 8.4 | https://jobs.ashbyhq.com/Clera/045880a4-82bc-409e-a201-bf763806f487 |
| Self Financial | Senior Data Engineer | ~3.6d | Austin, TX | 8.3 | https://job-boards.greenhouse.io/selffinancial/jobs/6269291004 |
| CodePath | Senior Data Engineer | ~3.7d | Remote US | 7.3 | https://job-boards.greenhouse.io/codepath/jobs/5307382007 |
| onX | Senior Data Engineer | ~2.8d | Austin + multi-city | 6.9 | https://job-boards.greenhouse.io/onxmaps/jobs/4729260006 |
| PlayStation Global | Data Engineer II, JVM | ~9.4d | Austin, TX | 6.7 | https://job-boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/6252099004 |
| Bluesight | Senior Data Engineer | ~1.9d | US Remote | 2.0 | https://jobs.lever.co/bluesight/eb53be34-14ee-4bec-9edb-bcd65136c989 |

## Already applied (skip)

- EnergyHub / Senior Data Engineer, C&I — https://job-boards.greenhouse.io/energyhub/jobs/8947924002

## How daily hunt works (quick map)

- `python3 -m agent hunt` → `ats_hunt.hunt_all()` (Greenhouse boards + Ashby + Rippling + Lever + Himalayas + JSON-LD + Builtin discovery + Remotive/Arbeitnow + watchlist), age ≤10d, US remote/work-ok filter.
- `python3 -m agent overnight` → prepare-only packets; score gate ≥8.5; never submits.
- `python3 -m agent daily` → hunt + process; in-window Playwright submit for Greenhouse/Ashby/Rippling only.
- Standing skips: Citi/Optum/UHG; aggregators; staff/principal; title must be Data Engineer / Senior Data Engineer.

## Gap note

`DEFAULT_GH_BOARDS` missed `selffinancial`, `onxmaps`, `codepath`, `oddball` (found via Builtin company → board slug probe). Lever `bluesight` is not in `DEFAULT_LEVER_COMPANIES` either.
