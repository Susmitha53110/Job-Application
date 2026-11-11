# Salary expectation — NEEDS ME

Rippling/Greenhouse forms require an exact number. Min filter is **$120,000** when pay is posted, but that is not an entered expectation.

## How to unlock Curve Dental + other ATS submits
Reply in chat with one line, for example:

`Salary expectations: 120000`

or

`Salary expectations: 135000`

Agent will run:

```bash
python3 -m agent set-salary 120000
```

That writes Memory + `FORM_ANSWERS.md`, then Curve can submit in the next **08:00–12:00 America/Chicago** window via `python3 -m agent curve-gate` / computer-use.
