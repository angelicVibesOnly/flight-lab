"""Row validation for flight schedule CSV files."""

import math
import re
from datetime import datetime

# [A-Za-z0-9] and [0-9] are written out on purpose: \w, \d, isalnum() and
# isupper() also accept non-ASCII characters such as "Ā" or Arabic digits.
FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_RE = re.compile(r"[A-Z]{3}")
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

FIELD_COUNT = 6


def parse_datetime(text: str) -> datetime | None:
    """Return a datetime if text is exactly YYYY-MM-DD HH:MM and a real date, else None."""
    # The regex enforces the exact shape (strptime alone accepts "2025-1-5 9:3"),
    # strptime then rejects impossible values such as month 13 or 25:00.
    if not isinstance(text, str) or DATETIME_RE.fullmatch(text) is None:
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file: one code per line, blank and # lines skipped."""
    airports = set()
    with open(path, encoding="utf-8-sig") as file:
        for line in file:
            code = line.strip()
            if code and not code.startswith("#"):
                airports.add(code)
    return airports


def _valid_airport(code: str, airports: set[str]) -> bool:
    return AIRPORT_RE.fullmatch(code) is not None and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Return None for a valid row, otherwise the code of the first failing check."""
    # 1. exactly 6 fields
    if len(fields) != FIELD_COUNT:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)

    # 2. no empty field
    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"
    # 3. flight id
    if FLIGHT_ID_RE.fullmatch(flight_id) is None:
        return "INVALID_FLIGHT_ID"
    # 4.-5. airports
    if not _valid_airport(origin, airports):
        return "INVALID_ORIGIN"
    if not _valid_airport(destination, airports):
        return "INVALID_DESTINATION"
    # 6.
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"
    # 7.-9. date and time
    departure_dt = parse_datetime(departure)
    if departure_dt is None:
        return "INVALID_DEPARTURE"
    arrival_dt = parse_datetime(arrival)
    if arrival_dt is None:
        return "INVALID_ARRIVAL"
    if arrival_dt <= departure_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"
    # 10.-11. price
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"
    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary."""
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }
