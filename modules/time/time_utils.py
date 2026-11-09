from typing import Any, Dict, Optional
from datetime import datetime
import zoneinfo
import dateparser
import re


def __fix_tz(text: str) -> str:
    """Overrides certain timezones with more relevant ones"""
    replacements = {
        "BST": "+0100",  # British Summer Time
        "IST": "+0530",  # Indian Standard Time
    }
    for timezone, offset in replacements.items():
        text = re.sub(rf"\b{timezone}\b", offset, text, flags=re.IGNORECASE)
    return text


def parse_date(
    date_str: Optional[str] = None,
    from_tz: Optional[str] = None,
    to_tz: Optional[str] = None,
    future: Optional[bool] = None,
    base: datetime = None,
) -> Optional[datetime]:
    """Returns datetime object for given date string
    Arguments:
    :param date_str: :class:`Optional[str]` date string to parse
    :param from_tz: :class:`Optional[str]` string representing the timezone to interpret the date as (eg. "Asia/Jerusalem")
    :param to_tz: :class:`Optional[str]` string representing the timezone to return the date in (eg. "Asia/Jerusalem")
    :param future: :class:`Optional[bool]` set to true to prefer dates from the future when parsing
    :param base: :class:`datetime` datetime representing where dates should be parsed relative to
    """
    base = datetime.now()
    if date_str is None:
        return None
    # set dateparser settings
    settings: Dict[str, Any] = {
        "RELATIVE_BASE": base.replace(tzinfo=None),
        **({"TIMEZONE": __fix_tz(from_tz)} if from_tz else {}),
        **({"TO_TIMEZONE": __fix_tz(to_tz)} if to_tz else {}),
        **({"PREFER_DATES_FROM": "future"} if future else {}),
    }
    # parse the date with dateparser
    date = dateparser.parse(__fix_tz(date_str), settings=settings)
    # return the datetime object
    return date


def format_time(time):
    """Rearrange time str. Comes in as YYYY-MM-DD HH:MM, change to MM-DD-YYYY HH:MM"""
    date = datetime.strptime(time, "%Y-%m-%d %H:%M")
    return date.strftime("%B %d, %H:%M")


def format_utc_offset(timezone_dict):
    """Find UTC offset (include dst if applicable)"""
    # Determine if DST is in effect
    current_time = datetime.strptime(timezone_dict["time"], "%Y-%m-%d %H:%M")

    # Get the timezone object
    try:
        timezone = zoneinfo.ZoneInfo(timezone_dict["timezoneId"])

        # Make datetime timezone-aware
        localized_time = current_time.replace(tzinfo=timezone)

        # Get the timezone abbreviation
        tz_abbr = localized_time.strftime("%Z")

        # Ge the actual offset at this time
        seconds_offset = localized_time.utcoffset().total_seconds()
        hours_offset = int(seconds_offset // 3600)
        minutes_offset = int((seconds_offset % 3600) // 60)

        # Format the offset string
        offset_str = (
            f"{'+' if hours_offset >= 0 else ''}{hours_offset:02d}:{minutes_offset:02d}"
        )

        return f"{tz_abbr} (UTC{offset_str})"
    except Exception:
        # Fallback in case of error
        raw_offset = timezone_dict["gmtOffset"]
        dst_offset = timezone_dict["dstOffset"]
        if raw_offset == dst_offset:
            return (
                f"{timezone_dict['timezoneId']} ("
                + ("+" if timezone_dict["gmtOffset"] > 0 else "")
                + f"{timezone_dict['gmtOffset']})"
            )
        else:
            return (
                f"{timezone_dict['timezoneId']} ("
                + ("+" if timezone_dict["dstOffset"] > 0 else "")
                + f"{timezone_dict['dstOffset']})"
            )
