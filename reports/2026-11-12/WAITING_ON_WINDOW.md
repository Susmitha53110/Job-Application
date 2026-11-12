# Waiting on window — 2026-11-11 20:28 CST

- Window open: **False** (applies only 08:00–12:00 America/Chicago)
- Next open: **2026-11-12 08:00 CT**
- Salary: **MISSING** (Curve only)
- Hard go/no-go: **GO** (soft: salary)

## Auto-submit when window opens
1. **Clera** — Senior Data Integration Engineer (b=9.7) — packet ready except window
2. **Bayesian Health** — SWE Data & Analytics Platform (b=7.5) — packet ready except window
3. **Life360** — Senior DE Ads (b=7.3) — packet ready except window; sponsorship **No**
4. **Curve Dental** — only if salary set + `curve-gate` ok

## needs-me / excluded from auto-submit
- **Velosio** (b=8.7) — iCIMS email + CAPTCHA before form
- **BetterHelp** (b=7.2) — required 5-year no-sponsorship question

## Hunt snapshot
10 filter-pass board hits; no new mid-level ≥7 beyond the queue above (Keebo/Consumer Edge Staff skipped).

## Commands at 08:00 CT
```bash
python3 -m agent window
python3 -m agent go-nogo
python3 -m agent handoff
python3 -m agent ready-submits
python3 -m agent daily
```
Use computer-use prompts from `SUBMIT_HANDOFF.json` / `READY_SUBMITS.md` / `SUBMIT_NOW.md`. Proof under `applications/applied/2026-11-12/…`.
