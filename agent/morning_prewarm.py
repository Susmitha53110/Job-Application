"""7:55 CT pre-warm: verify ages + queue before 08:00 submits. Never submits."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .job_search import assert_url_within_max_age
from .morning_queue_submit import load_queue
from .window import check_apply_window, chicago_today


def prewarm(*, day: str | None = None) -> dict:
    day = day or chicago_today().isoformat()
    tz = ZoneInfo("America/Chicago")
    now = datetime.now(tz)
    window = check_apply_window()
    items = []
    for q in load_queue(day):
        ok, detail = assert_url_within_max_age(q.url)
        items.append(
            {
                "key": q.key,
                "company": q.company,
                "role": q.role,
                "ats": q.ats,
                "age_ok": ok,
                "age_detail": detail,
                "resume_exists": q.resume.exists(),
                "url": q.url,
            }
        )
    blocked = [i for i in items if not i["age_ok"] or not i["resume_exists"]]
    return {
        "day": day,
        "now": now.isoformat(),
        "window_open": window.open,
        "window_reason": window.reason,
        "queue_n": len(items),
        "blocked_n": len(blocked),
        "items": items,
        "blocked": blocked,
        "next": "At 08:00 CT run: python3 -m agent.morning_queue_submit",
    }


if __name__ == "__main__":
    print(json.dumps(prewarm(), indent=2))
