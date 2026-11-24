"""Running queries against the flight database."""

from validator import parse_datetime

RECORD_KEYS = (
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
)
STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
NUMBER_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(RECORD_KEYS) | {"min_price", "sort_by", "order", "limit"}


def _is_number(value) -> bool:
    # bool is a subclass of int in Python, so True would otherwise count as 1.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_valid(query) -> bool:
    if not isinstance(query, dict):
        return False
    for key, value in query.items():
        if key not in ALLOWED_KEYS:
            return False
        if key in STRING_KEYS and not isinstance(value, str):
            return False
        if key in DATETIME_KEYS and parse_datetime(value) is None:
            return False
        if key in NUMBER_KEYS and not _is_number(value):
            return False
        if key == "sort_by" and value not in RECORD_KEYS:
            return False
        if key == "order" and value not in ("asc", "desc"):
            return False
        if key == "limit" and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            return False
    if "order" in query and "sort_by" not in query:
        return False
    return True


def _matches(flight: dict, query: dict) -> bool:
    for key in STRING_KEYS:
        if key in query and flight[key] != query[key]:
            return False
    # The datetime format is fixed and zero-padded, so comparing the strings
    # gives the same order as comparing the dates.
    if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and flight["price"] > query["price"]:
        return False
    if "min_price" in query and flight["price"] < query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object."""
    if not _is_valid(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [flight for flight in db if _matches(flight, query)]
    if "sort_by" in query:
        # sorted() is stable, also with reverse=True, so equal values keep database order.
        matches = sorted(
            matches,
            key=lambda flight: flight[query["sort_by"]],
            reverse=query.get("order", "asc") == "desc",
        )
    if "limit" in query:
        matches = matches[: query["limit"]]
    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list of entries."""
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, query) for query in queries]
