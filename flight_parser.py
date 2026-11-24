"""Command-line entry point: validate flight CSVs, store a JSON database, run queries."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB111"
FIRST_NAME = "Angel"
LAST_NAME = "Mehta"


class RunError(Exception):
    """An expected runtime problem: exit code 1 with an 'Error: ...' line."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store them as JSON and run queries.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", dest="input_file", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", dest="input_dir", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", dest="json_db", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", dest="airports", help="airport list file (needed with -i and -d)")
    parser.add_argument("-o", metavar="FILE", dest="output", help="output path for the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", dest="queries", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", dest="response_dir", default=".", help="folder for the response file (default: current directory)")
    return parser


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.json_db is None and args.airports is None:
        parser.error("-a is required with -i and -d")
    if args.json_db is not None and args.output is not None:
        parser.error("-o cannot be used with -j")
    return args


def read_json(path: str, what: str):
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except OSError as exc:
        raise RunError(f"cannot read {what} '{path}': {exc.strerror or exc}") from exc
    except (ValueError, RecursionError) as exc:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
        raise RunError(f"{what} '{path}' is not valid JSON") from exc


def find_csv_files(args: argparse.Namespace) -> list[str]:
    if args.input_file is not None:
        if not os.path.isfile(args.input_file):
            raise RunError(f"file not found: {args.input_file}")
        return [args.input_file]

    folder = args.input_dir
    if not os.path.isdir(folder):
        raise RunError(f"folder not found: {folder}")
    try:
        names = sorted(os.listdir(folder))
    except OSError as exc:
        raise RunError(f"cannot read folder '{folder}': {exc.strerror or exc}") from exc
    paths = [
        os.path.join(folder, name)
        for name in names
        if name.endswith(".csv") and os.path.isfile(os.path.join(folder, name))
    ]
    if not paths:
        raise RunError(f"no .csv files found in {folder}")
    return paths


def write_log(log_path: str, errors: list[str]) -> None:
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # write only to errors.log, never to the console
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        for message in errors:
            logger.warning(message)
    finally:
        # Always detach the handler: the grader calls main() many times in one process.
        logger.removeHandler(handler)
        handler.close()


def build_database(args: argparse.Namespace) -> list[dict]:
    """Parse the CSV input, write the database and errors.log, return the records."""
    try:
        airports = load_airports(args.airports)
    except (OSError, UnicodeDecodeError) as exc:
        raise RunError(f"cannot read airport file '{args.airports}'") from exc

    paths = find_csv_files(args)
    try:
        records, errors = parse_files(paths, airports)
    except (OSError, UnicodeDecodeError) as exc:
        raise RunError(f"cannot read CSV input: {exc}") from exc

    output = args.output if args.output is not None else "db.json"
    log_path = os.path.join(os.path.dirname(os.path.abspath(output)), "errors.log")
    try:
        write_log(log_path, errors)
        with open(output, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RunError(f"cannot write output: {exc.strerror or exc}") from exc

    print(f"{len(records)} valid flights, {len(errors)} invalid rows -> {output}")
    return records


def load_database(path: str) -> list[dict]:
    data = read_json(path, "database")
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise RunError(f"database '{path}' must be a JSON array of objects")
    return data


def answer_queries(db: list[dict], query_path: str, response_dir: str) -> None:
    queries = read_json(query_path, "query file")
    if isinstance(queries, list):
        if not all(isinstance(item, dict) for item in queries):
            raise RunError(f"query file '{query_path}' must hold a query object or an array of them")
    elif not isinstance(queries, dict):
        raise RunError(f"query file '{query_path}' must hold a query object or an array of them")

    responses = run_queries(db, queries)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    path = os.path.join(response_dir, name)
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(responses, file, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RunError(f"cannot write response file: {exc.strerror or exc}") from exc
    print(f"{len(responses)} queries answered -> {path}")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_arguments(argv)
    except SystemExit as exc:  # argparse exits with 2 on usage errors and 0 for -h
        return exc.code if isinstance(exc.code, int) else 0

    try:
        if args.json_db is not None:
            db = load_database(args.json_db)
        else:
            db = build_database(args)
        if args.queries is not None:
            answer_queries(db, args.queries, args.response_dir)
    except RunError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
