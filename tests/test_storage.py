"""Private SQLite persistence tests using invented observations only."""

from datetime import date
from pathlib import Path
from dataclasses import replace
import sqlite3
import tempfile
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens.storage import (
    SeriesMetadata, backup_database, export_series, freshness,
    initialize_database, list_series, read_series, upsert_many, upsert_series,
)


def metadata(identifier="SYNTHETIC"):
    return SeriesMetadata(identifier, "Invented series", "Invented units", "SYNTHETIC", "Unadjusted synthetic daily observations", "Invented for tests; no external market data")


def daily(days, values):
    return pd.DataFrame({"date": pd.to_datetime(days), "value": values})


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "private.sqlite"

    def test_exact_float_import_and_unchanged_input(self):
        data = daily(["2024-01-03", "2024-01-01"], [0.1, -2.25])
        original = data.copy(deep=True)
        summary = upsert_series(self.db, metadata(), data)
        self.assertEqual((summary.inserted, summary.revised, summary.unchanged), (2, 0, 0))
        assert_frame_equal(read_series(self.db, "SYNTHETIC"), data.sort_values("date").reset_index(drop=True))
        assert_frame_equal(data, original)
        self.assertEqual(list_series(self.db)[0]["quote_semantics"], metadata().quote_semantics)

    def test_revision_audit_and_idempotent_observations(self):
        upsert_series(self.db, metadata(), daily(["2024-01-01"], [10.]))
        unchanged = upsert_series(self.db, metadata(), daily(["2024-01-01"], [10.]))
        self.assertEqual(unchanged.unchanged, 1)
        revision = upsert_series(self.db, metadata(), daily(["2024-01-01", "2024-01-02"], [12., 0.]))
        self.assertEqual((revision.inserted, revision.revised), (1, 1))
        with sqlite3.connect(self.db) as connection:
            audit = connection.execute("SELECT old_value,new_value FROM revisions ORDER BY revision_id").fetchall()
            self.assertEqual(audit, [(None, 10.), (10., 12.), (None, 0.)])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM imports").fetchone()[0], 3)

    def test_conflicting_metadata_rolls_back_all_series_and_revisions(self):
        upsert_series(self.db, metadata(), daily(["2024-01-01"], [10.]))
        with self.assertRaisesRegex(ValueError, "metadata conflicts"):
            upsert_many(self.db, [(metadata("NEW"), daily(["2024-01-02"], [20.])), (replace(metadata(), source="OTHER_PROVIDER"), daily(["2024-01-01"], [30.]))])
        self.assertEqual([item["series_id"] for item in list_series(self.db)], ["SYNTHETIC"])
        self.assertEqual(read_series(self.db, "SYNTHETIC").loc[0, "value"], 10.)
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM revisions").fetchone()[0], 1)

    def test_invalid_frames_validated_before_import(self):
        upsert_series(self.db, metadata(), daily(["2024-01-01"], [1.]))
        with self.assertRaises(ValueError):
            upsert_many(self.db, [(metadata("NEW"), daily(["2024-01-01"], [2.])), (metadata("INVALID"), daily(["2024-01-01", "2024-01-01"], [3., 4.]))])
        self.assertEqual(len(list_series(self.db)), 1)
        with self.assertRaisesRegex(ValueError, "exactly representable"):
            upsert_series(self.db, metadata("BIG_INTEGER"), daily(["2024-01-01"], [9007199254740993]))

    def test_freshness_uses_calendar_days_and_explicit_cutoff(self):
        upsert_series(self.db, metadata(), daily(["2024-01-05", "2024-01-20"], [1., 2.]))
        recent = freshness(self.db, "SYNTHETIC", as_of=date(2024, 1, 7), max_age_days=2)
        self.assertEqual(recent["age_calendar_days"], 2)
        self.assertFalse(recent["stale"])
        self.assertTrue(freshness(self.db, "SYNTHETIC", as_of=date(2024, 1, 8), max_age_days=2)["stale"])
        self.assertIsNone(freshness(self.db, "SYNTHETIC", as_of=date(2023, 1, 1))["latest_at_cutoff"])

    def test_export_and_backup_preserve_state_without_overwrite(self):
        upsert_series(self.db, metadata(), daily(["2024-01-01"], [1.25]))
        destination = Path(self.temporary.name) / "series.csv"
        export_series(self.db, "SYNTHETIC", destination)
        self.assertEqual(pd.read_csv(destination).loc[0, "value"], 1.25)
        with self.assertRaises(FileExistsError):
            export_series(self.db, "SYNTHETIC", destination)
        backup = Path(self.temporary.name) / "backup.sqlite"
        backup_database(self.db, backup)
        assert_frame_equal(read_series(self.db, "SYNTHETIC"), read_series(backup, "SYNTHETIC"))
        with self.assertRaises(ValueError):
            backup_database(self.db, backup)
        with self.assertRaises(ValueError):
            export_series(self.db, "SYNTHETIC", self.db)

    def test_private_path_guard_and_missing_database_read(self):
        checkout = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "outside the source checkout"):
            initialize_database(checkout / "must-not-be-created.sqlite")
        with self.assertRaises(FileNotFoundError):
            read_series(self.db, "UNKNOWN")
        self.assertFalse(self.db.exists())

    def test_rejects_duplicate_batch_ids_and_bad_metadata(self):
        data = daily(["2024-01-01"], [1.])
        with self.assertRaises(ValueError):
            upsert_many(self.db, [(metadata(), data), (metadata(), data)])
        with self.assertRaises(ValueError):
            upsert_series(self.db, replace(metadata(), quote_semantics=""), data)

    def test_ecb_ids_are_reserved_before_first_write(self):
        from seasonlens.ecb import ecb_metadata
        data = daily(["2024-01-01"], [1.])
        with self.assertRaisesRegex(ValueError, "canonical ECB"):
            upsert_series(self.db, metadata("EUR_PLN"), data)
        self.assertFalse(self.db.exists())
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            upsert_series(self.db, ecb_metadata()["EUR_PLN"], daily(["2024-01-01"], [0.]))


if __name__ == "__main__":
    unittest.main()
