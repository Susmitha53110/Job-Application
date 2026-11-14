# Morning unlock runbook — 2026-11-15

Use **after** `python3 -m agent queue-submit` finishes the 8 auto roles.
Window: 08:00–12:00 America/Chicago only. Gmail declined — paste 8-char OTP in chat (no re-auth).

Standing answers: email `dsusmitha55@gmail.com` · phone `9132073787` · LinkedIn `https://www.linkedin.com/in/susmitha-dodla-a05ab92b8` · salary `120000` · sponsorship **No** · relocate/hybrid **Yes prefer remote** · Female / Asian / not Hispanic / not veteran / no disability · how heard **Company website**.

## A. OTP (paste code → agent resumes Greenhouse submit)

| Pri | Company | URL | Age note | Kit |
|-----|---------|-----|----------|-----|
| 1 | MongoDB | `https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433` | first_published ~11-05 14:17 CT — **ages out ~14:17 CT today; unlock first** | `applications/applied/2026-11-14/MongoDB_Sr_fill/` |
| 2 | Extend | `https://job-boards.greenhouse.io/extend/jobs/6250516004` | posted 11-06 | `applications/applied/2026-11-14/Extend_Senior_Analytics_Engineer/` |
| 3 | Keebo | `https://job-boards.greenhouse.io/keebo/jobs/5470466008` | posted 11-10; sponsorship No is OK (F1-OPT) | `applications/applied/2026-11-14/Keebo_Senior_Data_Engineer/` |

**Aged — do not unlock:** Machinify (first_published 11-03).

Command once code pasted: `python3 -m agent gh-fill <mongodb|…> --submit --security-code <CODE>` (or computer-use on kit URL).

## B. CAPTCHA / Cloudflare (human solve → Submit → screenshot proof)

Priority = honest b + age + US company ATS:

| Pri | Company | Role | URL | Blocker |
|-----|---------|------|-----|---------|
| 1 | Anduril | Production Master Data Engineer | `https://boards.greenhouse.io/andurilindustries/jobs/5291892007` | GH reCAPTCHA |
| 2 | Commure | Sr SWE, Data Platform | `https://jobs.ashbyhq.com/Commure/039d70f4-a796-453c-9d8b-0926f91f1654` | submit unconfirmed — retry |
| 3 | Solvd | Knowledge Ingestion | `https://jobs.ashbyhq.com/Solvd/33ec603d-3ddf-47a4-852e-6fece64196f9` | reCAPTCHA Enterprise |
| 4 | Natera | Sr Forward Deployed DE | `https://job-boards.greenhouse.io/natera/jobs/6255111004` | CAPTCHA |
| 5 | Amplitude | Sr DE Marketing & GTM | `https://jobs.ashbyhq.com/amplitude/32a5b52c-9e3b-46e2-8c3f-a843fa21bd48` | CAPTCHA |
| 6 | Instructure | Senior Analytics Engineer | `https://jobs.ashbyhq.com/instructure/af01c88f-fb94-420b-85e8-2afbfb5b0213` | CAPTCHA |
| 7 | Mercer Advisors | Senior Analytics Engineer | `https://job-boards.greenhouse.io/merceradvisors/jobs/5462825008` | CAPTCHA |
| 8 | BookNook | Senior Analytics Engineer | `https://ats.rippling.com/booknook-inc/jobs/5d515e53-e907-4e79-81cb-b8dcf52954f5` | Cloudflare |
| 9 | Talkiatry | Analytics Engineer | `https://jobs.ashbyhq.com/talkiatry/75a5f6d7-bf9f-40a5-bde3-87e2d8ff8ad3` | CAPTCHA |
| 10 | The Knot | Lead Analytics Engineer | `https://job-boards.greenhouse.io/theknotworldwide/jobs/5474523008` | CAPTCHA (7y stretch — only if time) |

Proof dir pattern: `applications/applied/2026-11-15/<Company>_<Role>/confirmation.png` + append applied index.

## C. iCIMS (age unlocked — computer-use)

| Company | Role | URL | Note |
|---------|------|-----|------|
| Velosio | Data Engineer | `https://careers.velosio.com/jobs/3162` | datePosted 2026-11-11; not Playwright-auto |

## D. Skip forever this window

SpaceX / Rocket Lab / NinjaOne / Anduril Lead|Manager — citizen/ITAR/clearance.  
Jobgether Lever mirrors — FunCAPTCHA + often already applied (Life360 Ads).  
Citi / Optum. ClickHouse EU-only.

## E. After unlocks

One `hunt_all` → score → fill/submit any new ≤10d b≥7 company-ATS hits toward **20–25**.
