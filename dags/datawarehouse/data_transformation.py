import re
from datetime import datetime, time, timedelta


# Adjust this threshold if your project uses a different definition of "Short".
SHORT_VIDEO_MAX_SECONDS = 60


def parse_duration(value):
    """
    Parse a YouTube ISO 8601 duration, such as PT1H2M3S, into a timedelta.
    Also accepts HH:MM:SS strings and Python time/timedelta values.
    """
    if isinstance(value, timedelta):
        return value

    if isinstance(value, time):
        return timedelta(
            hours=value.hour,
            minutes=value.minute,
            seconds=value.second,
        )

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid video duration: {value!r}")

    value = value.strip()

    # Accept HH:MM:SS or MM:SS.
    if ":" in value:
        parts = value.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = parts
        else:
            raise ValueError(f"Invalid clock-formatted duration: {value!r}")

        return timedelta(
            hours=int(hours),
            minutes=int(minutes),
            seconds=float(seconds),
        )

    # Accept YouTube ISO 8601 durations, e.g. PT45S, PT5M20S, or PT1H2M3S.
    match = re.fullmatch(
        r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {value!r}")

    days, hours, minutes, seconds = match.groups()
    if not any((days, hours, minutes, seconds)):
        raise ValueError(f"Duration contains no time values: {value!r}")

    return timedelta(
        days=int(days or 0),
        hours=int(hours or 0),
        minutes=int(minutes or 0),
        seconds=float(seconds or 0),
    )


def _duration_as_time(duration):
    """Convert a duration to a time value for the PostgreSQL TIME column."""
    total_seconds = int(duration.total_seconds())

    if total_seconds < 0 or total_seconds >= 24 * 60 * 60:
        raise ValueError(
            f"Duration {duration} cannot be stored in a PostgreSQL TIME column."
        )

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours, minute=minutes, second=seconds)


def _as_int_or_none(value):
    """Convert API count values to integers while preserving nulls."""
    if value is None or value == "":
        return None
    return int(value)


def transform_data(row):
    """
    Transform an aliased staging row into the column names expected by
    insert_rows() for the core table.

    Expected input keys:
        video_id, title, publishedAt, duration,
        viewCount, likeCount, commentCount
    """
    duration_td = parse_duration(row["duration"])
    duration_value = _duration_as_time(duration_td)

    video_type = (
        "Short"
        if duration_td.total_seconds() <= SHORT_VIDEO_MAX_SECONDS
        else "Long"
    )

    published_at = row["publishedAt"]
    if isinstance(published_at, str):
        published_at = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

    return {
        "Video_ID": row["video_id"],
        "Video_Title": row["title"],
        "Upload_Date": published_at,
        "Duration": duration_value,
        "Video_Type": video_type,
        "Video_Views": _as_int_or_none(row.get("viewCount")),
        "Likes_Count": _as_int_or_none(row.get("likeCount")),
        "Comments_Count": _as_int_or_none(row.get("commentCount")),
    }