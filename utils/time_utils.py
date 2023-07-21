from typing import Any, Dict, Optional
from datetime import datetime
import dateparser
import re


async def __fix_tz(text: str) -> str:
    """Overrides certain timezones with more relevant ones"""
    replacements = {
        "BST": "+0100",  # British Summer Time
        "IST": "+0530",  # Indian Standard Time
    }
    for timezone, offset in replacements.items():
        text = re.sub(rf"\b{timezone}\b", offset, text, flags=re.IGNORECASE)
    return text


async def parse_date(
    date_str: Optional[str] = None,
    from_tz: Optional[str] = None,
    to_tz: Optional[str] = None,
    future: Optional[bool] = None,
    base: datetime = datetime.now(),
) -> Optional[datetime]:
    """Returns datetime object for given date string
    Arguments:
    :param date_str: :class:`Optional[str]` date string to parse
    :param from_tz: :class:`Optional[str]` string representing the timezone to interpret the date as (eg. "Asia/Jerusalem")
    :param to_tz: :class:`Optional[str]` string representing the timezone to return the date in (eg. "Asia/Jerusalem")
    :param future: :class:`Optional[bool]` set to true to prefer dates from the future when parsing
    :param base: :class:`datetime` datetime representing where dates should be parsed relative to
    """
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


async def replace_offset(text: str) -> str:
    """Overrides the offset for better timezones"""
    return text.replace("UTC\+05:30", "IST").replace("UTC\+01:00", "BST")


async def format_time(time):
    """Rearrange time str. Comes in as YYYY-MM-DD HH:MM, change to MM-DD-YYYY HH:MM"""
    date = datetime.strptime(time, "%Y-%m-%d %H:%M")
    return date.strftime("%B %d, %H:%M")


async def format_gmt_offset(timezone_dict):
    """Find GMT offset (include dst if applicable)"""
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
            + ("+" if timezone_dict["gmtOffset"] > 0 else "")
            + f"{timezone_dict['gmtOffset']}/"
            + ("+" if timezone_dict["dstOffset"] > 0 else "")
            + f"{timezone_dict['dstOffset']})"
        )
