"""Private SQLite persistence with atomic imports and observation revisions."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import csv
import os
import sqlite3
from contextlib import contextmanager
from numbers import Integral

import pandas as pd

from .monthly import aggregate_monthly


@dataclass(frozen=True)
class SeriesMetadata:
    series_id: str
    title: str
    unit: str
    source: str
    quote_semantics: str
    provenance: str


@dataclass(frozen=True)
class ImportSummary:
    series_id: str
    observations: int
    inserted: int
    revised: int
    unchanged: int


def _path(path) -> Path:
    target = Path(path).expanduser().resolve()
    checkout = Path(__file__).resolve().parents[2]
    source_checkouts = [checkout] + [ancestor for ancestor in target.parents if (ancestor / "src" / "seasonlens").is_dir()]
    if any((root / ".git").exists() and target.is_relative_to(root) for root in source_checkouts):
        raise ValueError("Private database and exports must be outside the source checkout.")
    return target


def validate_private_path(path) -> Path:
    """Resolve a private artifact path and reject this public source checkout."""
    return _path(path)


@contextmanager
def _connect(path):
    target = _path(path)
    if not target.is_file():
        raise FileNotFoundError("Private database has not been initialized.")
    connection = sqlite3.connect(target, timeout=20)
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(path) -> None:
    """Create an explicit private database path; never put it in this checkout."""
    target = _path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
    with _connect(target) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS series (
                series_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                unit TEXT NOT NULL, source TEXT NOT NULL,
                quote_semantics TEXT NOT NULL, provenance TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
                series_id TEXT NOT NULL REFERENCES series(series_id),
                observation_date TEXT NOT NULL, value REAL NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(series_id, observation_date)
            );
            CREATE TABLE IF NOT EXISTS revisions (
                revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL REFERENCES series(series_id),
                observation_date TEXT NOT NULL, old_value REAL,
                new_value REAL NOT NULL, recorded_at TEXT NOT NULL,
                source TEXT NOT NULL, provenance TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS imports (
                import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL REFERENCES series(series_id),
                recorded_at TEXT NOT NULL, observations INTEGER NOT NULL,
                inserted INTEGER NOT NULL, revised INTEGER NOT NULL,
                unchanged INTEGER NOT NULL
            );
        """)


def upsert_many(path, entries) -> tuple[ImportSummary, ...]:
    """Validate every frame, then apply all series in one transaction.

    Metadata is immutable for a series ID: different providers, quote semantics
    or provenance need a distinct ID. Existing observations are never deleted.
    Changed values and new observations receive audit entries; unchanged imports
    receive an import record but do not rewrite observation timestamps.
    """
    entries = list(entries)
    if not entries:
        raise ValueError("At least one series import is required.")
    seen = set()
    for metadata, frame in entries:
        if not isinstance(metadata, SeriesMetadata) or any(
            not isinstance(value, str) or not value.strip() for value in asdict(metadata).values()
        ):
            raise ValueError("Every series metadata field must be nonempty text.")
        if metadata.series_id in seen:
            raise ValueError("Each series ID must occur once in an atomic import.")
        seen.add(metadata.series_id)
        aggregate_monthly(frame)
        if metadata.series_id in {"EUR_PLN", "EUR_USD", "USD_PLN"}:
            # Runtime import avoids the storage/ECB metadata-definition cycle.
            from .ecb import ecb_metadata
            if metadata != ecb_metadata()[metadata.series_id]:
                raise ValueError("Direct ECB series IDs require the canonical ECB source and quote metadata.")
            if frame["value"].le(0).any():
                raise ValueError("Direct ECB rates must be strictly positive.")
        if any(isinstance(value, Integral) and int(value) != float(value) for value in frame["value"]):
            raise ValueError("Integer observations must be exactly representable in SQLite float64 storage.")
    initialize_database(path)
    recorded_at = datetime.now(timezone.utc).isoformat()
    summaries = []
    with _connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        for metadata, frame in entries:
            fields = tuple(asdict(metadata).values())
            existing_metadata = connection.execute("SELECT * FROM series WHERE series_id=?", (metadata.series_id,)).fetchone()
            if existing_metadata is None:
                connection.execute("INSERT INTO series VALUES(?,?,?,?,?,?)", fields)
            elif existing_metadata != fields:
                raise ValueError("Series metadata conflicts with stored source or quote semantics; use a distinct ID.")
            inserted = revised = unchanged = 0
            for observation in frame[["date", "value"]].itertuples(index=False, name=None):
                day, value = observation[0].date().isoformat(), float(observation[1])
                old = connection.execute("SELECT value FROM observations WHERE series_id=? AND observation_date=?", (metadata.series_id, day)).fetchone()
                if old is not None and old[0] == value:
                    unchanged += 1
                    continue
                inserted += old is None
                revised += old is not None
                connection.execute("INSERT INTO revisions(series_id,observation_date,old_value,new_value,recorded_at,source,provenance) VALUES(?,?,?,?,?,?,?)", (metadata.series_id, day, None if old is None else old[0], value, recorded_at, metadata.source, metadata.provenance))
                connection.execute("INSERT INTO observations VALUES(?,?,?,?) ON CONFLICT(series_id,observation_date) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at", (metadata.series_id, day, value, recorded_at))
            summary = ImportSummary(metadata.series_id, len(frame), inserted, revised, unchanged)
            summaries.append(summary)
            connection.execute("INSERT INTO imports(series_id,recorded_at,observations,inserted,revised,unchanged) VALUES(?,?,?,?,?,?)", (metadata.series_id, recorded_at, len(frame), inserted, revised, unchanged))
    return tuple(summaries)


def upsert_series(path, metadata: SeriesMetadata, frame: pd.DataFrame) -> ImportSummary:
    return upsert_many(path, [(metadata, frame)])[0]


def read_series(path, series_id: str) -> pd.DataFrame:
    with _connect(path) as connection:
        if connection.execute("SELECT 1 FROM series WHERE series_id=?", (series_id,)).fetchone() is None:
            raise ValueError("Requested series does not exist.")
        rows = connection.execute("SELECT observation_date,value FROM observations WHERE series_id=? ORDER BY observation_date", (series_id,)).fetchall()
    result = pd.DataFrame(rows, columns=["date", "value"])
    result["date"] = pd.to_datetime(result["date"], format="%Y-%m-%d")
    result["value"] = result["value"].astype("float64")
    return result


def list_series(path) -> list[dict]:
    with _connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""SELECT s.*, COUNT(o.observation_date) AS observation_count,
            MIN(o.observation_date) AS first_observation_date,
            MAX(o.observation_date) AS last_observation_date,
            MAX(o.updated_at) AS last_changed_at,
            (SELECT MAX(recorded_at) FROM imports i WHERE i.series_id=s.series_id) AS last_import_at
            FROM series s LEFT JOIN observations o USING(series_id)
            GROUP BY s.series_id ORDER BY s.series_id""").fetchall()
    return [dict(row) for row in rows]


def freshness(path, series_id: str, *, as_of: date, max_age_days: int = 7) -> dict:
    """Calendar-day freshness only; no exchange-session calendar is assumed."""
    if not isinstance(as_of, date) or isinstance(as_of, datetime):
        raise ValueError("as_of must be a datetime.date.")
    if not isinstance(max_age_days, int) or isinstance(max_age_days, bool) or max_age_days < 0:
        raise ValueError("max_age_days must be a nonnegative integer.")
    records = [item for item in list_series(path) if item["series_id"] == series_id]
    if not records:
        raise ValueError("Requested series does not exist.")
    record = records[0]
    with _connect(path) as connection:
        latest = connection.execute("SELECT MAX(observation_date) FROM observations WHERE series_id=? AND observation_date<=?", (series_id, as_of.isoformat())).fetchone()[0]
    age = None if latest is None else (as_of - date.fromisoformat(latest)).days
    return {**record, "as_of": as_of.isoformat(), "latest_at_cutoff": latest, "age_calendar_days": age, "stale": age is None or age > max_age_days}


def export_series(path, series_id: str, destination) -> Path:
    target = _path(destination)
    if target == _path(path):
        raise ValueError("Export destination cannot overwrite the database.")
    frame = read_series(path, series_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "instrument_id", "value"])
        for day, value in frame.itertuples(index=False, name=None):
            writer.writerow([day.date().isoformat(), series_id, repr(value)])
    return target


def backup_database(path, destination) -> Path:
    """Snapshot via SQLite backup rather than copying a potentially active file."""
    target = _path(destination)
    if target == _path(path) or target.exists():
        raise ValueError("Backup must use a distinct, new destination.")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with _connect(path) as source, _connect(target) as backup:
            source.backup(backup)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target
