"""Explicit private-database commands; no provider keys or raw-value logging."""

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
import sqlite3
import sys
from urllib.error import URLError

from .csv_import import import_csv
from .ecb import update_ecb
from .storage import SeriesMetadata, backup_database, export_series, initialize_database, upsert_many


def import_master(
    db, csv_path, metadata_path, *, skip_missing=False, as_of=None,
    date_column="date", value_column="value", instrument_column="instrument_id",
    date_format="%Y-%m-%d", delimiter=",", decimal=".",
):
    """Prepare every declared instrument before writing any of them.

    Metadata JSON is a list of SeriesMetadata fields (plus optional instrument)
    or an object keyed by series_id. Provider histories keep distinct IDs from
    direct ECB reference series. Missing and cutoff policies use import_csv
    unchanged, including validation of excluded dates and duplicate blank rows.
    """
    specification = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    if isinstance(specification, dict):
        records = []
        for series_id, record in specification.items():
            if not isinstance(record, dict):
                raise ValueError("Metadata entries must be objects.")
            if "series_id" in record and record["series_id"] != series_id:
                raise ValueError("Metadata key and series_id must agree.")
            records.append({**record, "series_id": series_id})
    elif isinstance(specification, list):
        records = specification
    else:
        raise ValueError("Metadata JSON must be a nonempty list or object.")
    if not records:
        raise ValueError("Metadata JSON must declare at least one series.")
    entries, omissions = [], []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Metadata entries must be objects.")
        record = dict(record)
        instrument = record.pop("instrument", record.get("series_id"))
        try:
            metadata = SeriesMetadata(**record)
        except TypeError as exc:
            raise ValueError("Metadata must provide exactly the SeriesMetadata fields and optional instrument.") from exc
        if metadata.series_id in {"EUR_PLN", "EUR_USD", "USD_PLN"}:
            raise ValueError("Direct ECB series cannot be imported from CSV; use update-ecb.")
        result = import_csv(
            csv_path, date_column=date_column, value_column=value_column,
            date_format=date_format, delimiter=delimiter, decimal=decimal,
            instrument_column=instrument_column, instrument=instrument,
            missing_values="skip" if skip_missing else "reject", max_date=as_of,
        )
        entries.append((metadata, result.frame))
        omissions.append({
            "series_id": metadata.series_id,
            "skipped_missing_count": len(result.skipped_missing_rows),
            "excluded_future_count": len(result.filtered_date_rows),
            "skipped_missing_rows": result.skipped_missing_rows,
            "excluded_future_rows": result.filtered_date_rows,
        })
    summaries = upsert_many(db, entries)
    return summaries, tuple(omissions)


def _iso_date(text):
    try:
        parsed = date.fromisoformat(text)
        if text != parsed.isoformat():
            raise ValueError
        return parsed
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a calendar date in YYYY-MM-DD form.") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SeasonLens private SQLite data commands")
    parser.add_argument("--db", required=True, help="Explicit SQLite path outside the source checkout")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    importer = commands.add_parser("import-master")
    importer.add_argument("csv")
    importer.add_argument("--metadata", required=True)
    importer.add_argument("--skip-missing", action="store_true")
    importer.add_argument("--as-of", type=_iso_date)
    importer.add_argument("--date-column", default="date")
    importer.add_argument("--value-column", default="value")
    importer.add_argument("--instrument-column", default="instrument_id")
    importer.add_argument("--date-format", default="%Y-%m-%d")
    importer.add_argument("--delimiter", default=",")
    importer.add_argument("--decimal", default=".")
    updater = commands.add_parser("update-ecb")
    updater.add_argument("--history", action="store_true", help="Explicitly fetch the full ECB history")
    updater.add_argument("--timeout", type=float, default=20)
    updater.add_argument("--as-of", type=_iso_date, help="Explicit provider-date cutoff; default is current Europe/Warsaw date")
    exporter = commands.add_parser("export")
    exporter.add_argument("--series", required=True)
    exporter.add_argument("--output", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            initialize_database(args.db)
            print("Private database initialized.")
        elif args.command == "import-master":
            summaries, omissions = import_master(
                args.db, args.csv, args.metadata, skip_missing=args.skip_missing,
                as_of=args.as_of, date_column=args.date_column,
                value_column=args.value_column, instrument_column=args.instrument_column,
                date_format=args.date_format, delimiter=args.delimiter, decimal=args.decimal,
            )
            for summary, omitted in zip(summaries, omissions):
                print(json.dumps({**asdict(summary), "skipped_missing_count": omitted["skipped_missing_count"], "excluded_future_count": omitted["excluded_future_count"]}))
            print("Counts describe observations; live months may be incomplete. No gaps were filled.")
        elif args.command == "update-ecb":
            for summary in update_ecb(args.db, history=args.history, timeout=args.timeout, as_of=args.as_of):
                print(json.dumps(asdict(summary)))
            print("ECB reference rates and same-date derived USD/PLN were stored separately from vendor histories.")
        elif args.command == "export":
            export_series(args.db, args.series, args.output)
            print("Private series CSV exported; source restrictions still apply.")
        else:
            backup_database(args.db, args.output)
            print("Private SQLite snapshot saved.")
    except (ValueError, OSError, sqlite3.Error, URLError) as exc:
        print(f"Operation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
