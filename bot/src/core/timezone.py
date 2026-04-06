from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()

_DEPRECATED_PREFIXES = ("US/", "Canada/", "Brazil/", "Chile/", "Mexico/", "Etc/", "SystemV/")

_TIMEZONE_LIST: list[tuple[str, str]] | None = None


def _get_timezone_list() -> list[tuple[str, str]]:
    global _TIMEZONE_LIST  # noqa: PLW0603
    if _TIMEZONE_LIST is not None:
        return _TIMEZONE_LIST

    result: list[tuple[str, str]] = []
    for tz in sorted(available_timezones()):
        if "/" not in tz or tz.startswith(_DEPRECATED_PREFIXES):
            continue
        city = tz.rsplit("/", maxsplit=1)[-1].replace("_", " ")
        result.append((city, tz))

    _TIMEZONE_LIST = result
    return _TIMEZONE_LIST


def timezone_from_location(lat: float, lon: float) -> str | None:
    return _tf.timezone_at(lng=lon, lat=lat)


def search_timezones(query: str, limit: int = 8) -> list[tuple[str, str]]:
    q = query.lower().strip()
    if not q:
        return []

    results: list[tuple[str, str]] = []
    for city, tz in _get_timezone_list():
        if q in city.lower() or q in tz.lower():
            label = format_timezone(tz)
            results.append((label, tz))
            if len(results) >= limit:
                break
    return results


def format_timezone(tz: str) -> str:
    now = datetime.now(ZoneInfo(tz))
    offset = now.strftime("%z")
    sign = offset[0]
    hours = offset[1:3]
    minutes = offset[3:5]
    city = tz.rsplit("/", maxsplit=1)[-1].replace("_", " ")
    return f"{city} (UTC{sign}{hours}:{minutes})"
