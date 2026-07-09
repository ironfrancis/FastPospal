from __future__ import annotations

from datetime import datetime, timedelta


def resolve_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, str]:
    today = datetime.now().date()
    default_start = (today - timedelta(days=6)).isoformat()
    default_end = today.isoformat()
    start = start_date or default_start
    end = end_date or default_end
    return f"{start} 00:00:00", f"{end} 23:59:59"


def days_ago_range(days: int) -> tuple[str, str]:
    end = datetime.now()
    begin = end - timedelta(days=max(1, days))
    return (
        begin.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
    )
