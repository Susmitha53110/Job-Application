# clickhouse — skipped (not US)

- URL: https://jobs.ashbyhq.com/clickhouse/6d2d05da-c1f4-4ff6-9d02-a30306940857
- Location: Netherlands / Germany / Spain / UK (EU remote)
- False positive: `usa` matched inside "reusable"/"usability" in JD text.
- Filter fixed in `agent/job_search.py` (`_explicit_us_mention` word-bounded).
- Do not submit.
