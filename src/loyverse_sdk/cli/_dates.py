from datetime import UTC, datetime, timedelta

import typer

from loyverse_sdk.utils import standardize_datetime_str

_DATE_ALIASES: dict[str, tuple[int, object]] = {
    "today": (0, None),
    "yesterday": (1, None),
}


def normalize_date(value: str, *, end_of_day: bool = False) -> str:
    """Normalize a user-facing date string to an ISO-8601 UTC datetime.

    Accepted inputs:

        today             — today's date in UTC
        yesterday         — yesterday's date in UTC
        2025-05-31        — bare date (midnight or 23:59:59 UTC)
        2025-05-31T12:00Z — full ISO-8601 (passed through unchanged)
    """
    if value in _DATE_ALIASES:
        days_back, _ = _DATE_ALIASES[value]
        dt = datetime.now(UTC) - timedelta(days=days_back)
    elif "T" not in value:
        try:
            dt = datetime.strptime(value.strip(), "%Y-%m-%d")
        except ValueError as e:
            raise typer.BadParameter(
                f"Invalid date: '{value}' (expected YYYY-MM-DD)"
            ) from e
        dt = dt.replace(tzinfo=UTC)
    else:
        return value

    hour = 23 if end_of_day else 0
    minute = 59 if end_of_day else 0
    second = 59 if end_of_day else 0
    dt = dt.replace(hour=hour, minute=minute, second=second, microsecond=0)

    return standardize_datetime_str(dt.replace(tzinfo=None))
