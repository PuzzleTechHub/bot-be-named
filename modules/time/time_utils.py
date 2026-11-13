from datetime import datetime
import zoneinfo


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
        seconds_offset = int(localized_time.utcoffset().total_seconds())
        sign = "-" if seconds_offset < 0 else "+"
        hours_offset, remainder = divmod(abs(seconds_offset), 3600)
        minutes_offset = remainder // 60

        # Format the offset string
        offset_str = f"{sign}{hours_offset:02d}:{minutes_offset:02d}"

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
