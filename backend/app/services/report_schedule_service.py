from datetime import datetime, time, timedelta, timezone


def calculate_next_run_at(
    *,
    report_type: str,
    run_time_utc: str,
    now: datetime | None = None,
    day_of_week: int = 0,
    day_of_month: int = 1,
) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    hour, minute = (int(part) for part in run_time_utc.split(":"))
    candidate_time = time(hour=hour, minute=minute, tzinfo=timezone.utc)
    candidate = datetime.combine(current.date(), candidate_time)

    if report_type in {"daily", "custom"}:
        return candidate if candidate > current else candidate + timedelta(days=1)

    if report_type == "weekly":
        days_ahead = (day_of_week - current.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        return candidate if candidate > current else candidate + timedelta(days=7)

    if report_type == "monthly":
        candidate = candidate.replace(day=day_of_month)
        if candidate > current:
            return candidate
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        return candidate.replace(year=year, month=month)

    raise ValueError(f"Unsupported report schedule type: {report_type}")