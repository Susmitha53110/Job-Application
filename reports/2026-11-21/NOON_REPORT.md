# Nov 21 morning apply report (08:41 CST)

## Applied today (company ATS only; Gmail confirmed)
1. **Movement Labs — Senior Data Engineers** (Workable) — score 10.0 — confirmation email + success page
2. **Airbnb — Data Engineer Tech Foundations** (Greenhouse) — score 8.8 — confirmation email + Greenhouse confirmation page

## Discovery sources used
- `hunt_all`: Greenhouse + Ashby + Lever + Rippling + Builtin.com + Himalayas + JSON-LD career pages + Remotive/Arbeitnow
- LinkedIn guest search attempted (login wall; Easy Apply never used)
- Extra Greenhouse boards scanned (SoFi, Cloudflare, Discord, Block, Sixfold, …)
- Job alerts (Jobright First Citizens) checked → age fail (posted 2026-09-17)

## Skipped / blocked under gates
- Toast / Block Sales / Cloudflare / GUIDEcx / YesEnergy / Pocket / Life360 / Amplitude / etc. already applied
- Jobgether (standing skip), Optum (standing skip), Velosio (iCIMS needs-me)
- Air DE Analytics — U.S. citizenship required
- Anduril Product DE — security clearance required
- FloQast Sr DE — honest score 8.3 (< 8.5)
- Chorus Innovations — score 6.9
- Sixfold / Keebo / SoFi / Discord / First Citizens — first_published >10d or visa/citizen gates
- Builtin listings (PNC/Wells/GM/Rocket/bet365) — discovery only; Apply redirect needs Builtin login; no ATS URL resolved without login

## Inventory note
Fresh DE/Sr DE ≤10d + US-ok + ≥8.5 + not-already-applied was thin after Airbnb. Continue next window with expanded boards + Builtin/LinkedIn once authenticated for discovery redirects.

## Code fix
- `greenhouse_pw.match_select_option` + auth/sponsor picks: handle long "Yes, …" / "No, …" Airbnb-style options (CDP apply path).
