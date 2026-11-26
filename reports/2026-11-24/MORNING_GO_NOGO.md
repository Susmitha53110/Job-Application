# Morning go/no-go — 2026-11-24

- GO (hard checks): **False**
- Window open: **True**
- Salary: **120000**

## Hard failures
- packet_mongodb: blockers=['MongoDB verification failed: age fail-closed: first_published=2026-11-05T14:17:34-05:00']; url=https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433
- packet_mux: blockers=['mux verification failed: age fail-closed: publishedAt=2026-11-03T21:57:56.538+00:00']; url=https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe
- live_mux: https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe
- packet_machinify: blockers=['Machinify verification failed: age fail-closed: first_published=2026-11-03T18:23:56-05:00']; url=https://job-boards.greenhouse.io/machinifyinc/jobs/4478208009
- curve_age_le_4d: HTTP Error 404: Not Found
- curve_packet_except_salary_window: blockers=['Curve job verification failed: HTTP Error 404: Not Found']

## Soft failures (expected until answered / window)
- (none)

## All checks
- PASS `resume_short_clera` — /workspace/resumes/submit/Susmitha_clera.docx
- PASS `resume_short_bayesian` — /workspace/resumes/submit/Susmitha_bayesian.docx
- PASS `resume_short_betterhelp` — /workspace/resumes/submit/Susmitha_betterhelp.docx
- PASS `resume_short_life360` — /workspace/resumes/submit/Susmitha_life360.docx
- PASS `resume_short_velosio` — /workspace/resumes/submit/Susmitha_velosio.docx
- PASS `resume_short_curve` — /workspace/resumes/submit/Susmitha_curve.docx
- PASS `kit_clera` — /workspace/applications/needs-me/2026-11-12/Clera_SUBMIT_KIT.md
- PASS `kit_bayesian` — /workspace/applications/needs-me/2026-11-12/Bayesian_Health_SUBMIT_KIT.md
- PASS `kit_betterhelp` — /workspace/applications/needs-me/2026-11-12/BetterHelp_SUBMIT_KIT.md
- PASS `kit_life360` — /workspace/applications/needs-me/2026-11-12/Life360_SUBMIT_KIT.md
- PASS `kit_velosio` — /workspace/applications/needs-me/2026-11-12/Velosio_SUBMIT_KIT.md
- PASS `kit_curve` — /workspace/applications/needs-me/2026-11-12/Curve_Dental_SUBMIT_KIT.md
- PASS `kit_first_applies` — /workspace/applications/needs-me/2026-11-12/FIRST_APPLIES.md
- PASS `kit_form_map` — /workspace/applications/needs-me/2026-11-12/CURVE_FORM_MAP.md
- FAIL `packet_mongodb` — blockers=['MongoDB verification failed: age fail-closed: first_published=2026-11-05T14:17:34-05:00']; url=https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433
- PASS `live_mongodb` — https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433
- FAIL `packet_mux` — blockers=['mux verification failed: age fail-closed: publishedAt=2026-11-03T21:57:56.538+00:00']; url=https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe
- FAIL `live_mux` — https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe
- FAIL `packet_machinify` — blockers=['Machinify verification failed: age fail-closed: first_published=2026-11-03T18:23:56-05:00']; url=https://job-boards.greenhouse.io/machinifyinc/jobs/4478208009
- PASS `live_machinify` — https://job-boards.greenhouse.io/machinifyinc/jobs/4478208009
- FAIL `curve_age_le_4d` — HTTP Error 404: Not Found
- PASS `salary_set_for_curve` — 120000
- FAIL `curve_packet_except_salary_window` — blockers=['Curve job verification failed: HTTP Error 404: Not Found']
- PASS `real_applies_authorized` — memory/STATE.md
- PASS `dry_run_approved` — memory/STATE.md
