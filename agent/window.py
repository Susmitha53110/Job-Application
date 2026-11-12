from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo


TZ_CHICAGO = "America/Chicago"


@dataclass
class WindowStatus:
    now_local: datetime
    open: bool
    reason: str


def chicago_today() -> date:
    return datetime.now(ZoneInfo(TZ_CHICAGO)).date()


def check_apply_window(
    *,
    tz_name: str = TZ_CHICAGO,
    start_hour: int = 8,
    end_hour: int = 12,
) -> WindowStatus:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    open_ = start_hour <= now.hour < end_hour
    if open_:
        reason = f"Inside window {start_hour:02d}:00–{end_hour:02d}:00 {tz_name}."
    else:
        reason = (
            f"Outside window (now {now.strftime('%Y-%m-%d %H:%M %Z')}). "
            f"Applies only {start_hour:02d}:00–{end_hour:02d}:00 {tz_name}."
        )
    return WindowStatus(now_local=now, open=open_, reason=reason)


if __name__ == "__main__":
    status = check_apply_window()
    print(("OPEN" if status.open else "CLOSED"), status.reason)
