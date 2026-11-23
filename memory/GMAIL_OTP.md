# Gmail OTP (connected 2026-11-16)

Account: `dsusmitha55@gmail.com` via Gmail MCP.

## Agent use
When `applications/applied/YYYY-MM-DD/<Company>_OTP_wait/WAITING_FOR_OTP` exists:
1. `search_emails` query: `from:greenhouse-mail.io newer_than:1d subject:"Security code for your application to <Company>"`
2. Take the **newest** message snippet/body 8-digit code
3. Write it to `<proof_dir>/OTP_CODE.txt` (no other text)
4. Do **not** re-submit the form (that invalidates older codes)

Scope: read Greenhouse security codes only. Do not send mail or browse unrelated inbox.
