import pytest

from modules.time import time_utils


def _tz(timezone_id, time="2026-11-09 17:05", gmt=0, dst=0):
    return {
        "timezoneId": timezone_id,
        "time": time,
        "gmtOffset": gmt,
        "dstOffset": dst,
    }


def test_format_time():
    assert time_utils.format_time("2026-11-09 17:05") == "November 09, 17:05"


@pytest.mark.parametrize(
    "timezone_id, expected",
    [
        ("Australia/Perth", "AWST (UTC+08:00)"),
        ("Asia/Kolkata", "IST (UTC+05:30)"),
    ],
)
def test_format_utc_offset(timezone_id, expected):
    assert time_utils.format_utc_offset(_tz(timezone_id)) == expected


def test_format_utc_offset_unknown_zone_falls_back():
    tz = _tz("Not/AZone", gmt=5.5, dst=5.5)
    assert time_utils.format_utc_offset(tz) == "Not/AZone (+5.5)"


@pytest.mark.parametrize(
    "timezone_id, time, expected",
    [
        ("America/New_York", "2026-07-01 12:00", "EDT (UTC-04:00)"),
        ("America/St_Johns", "2026-07-01 12:00", "NDT (UTC-02:30)"),
    ],
)
def test_format_utc_offset_negative(timezone_id, time, expected):
    assert time_utils.format_utc_offset(_tz(timezone_id, time=time)) == expected
