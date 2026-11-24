"""Reading flight CSV files into records and error messages."""

import csv
import os

from validator import to_record, validate_row


def _physical_lines(path: str) -> list[str]:
    """Return the file's lines without their \\n or \\r\\n endings.

    str.splitlines() is not used because it also splits on characters such as
    \\x0c or \\u2028, which would make the line numbers wrong.
    """
    # utf-8-sig also accepts a file that starts with a byte order mark.
    with open(path, encoding="utf-8-sig", newline="") as file:
        text = file.read()
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # the file ended with a newline
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def _split(line: str) -> list[str] | None:
    try:
        return next(csv.reader([line]))
    except (csv.Error, StopIteration):
        return None


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Validate every row of the files, in order.

    Returns (valid records, error messages). The duplicate check covers all
    files of the run. This function does not write the log file.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        name = os.path.basename(path)
        for number, line in enumerate(_physical_lines(path), start=1):
            if number == 1:  # header, never validated
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue  # blank or comment line, not logged

            fields = _split(line)
            code = "WRONG_FIELD_COUNT" if fields is None else validate_row(fields, airports)
            if code is None:
                record = to_record(fields)
                key = (record["flight_id"], record["departure_datetime"])
                if key in seen:
                    code = "DUPLICATE_FLIGHT"
                else:
                    seen.add(key)
                    records.append(record)
            if code is not None:
                errors.append(f"{name}:{number}: {code} | {line}")

    return records, errors
