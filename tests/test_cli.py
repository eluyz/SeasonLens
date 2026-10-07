"""Synthetic private master workflow and command-line output checks."""

from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
from datetime import date
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from seasonlens.cli import import_master, main
from seasonlens.csv_import import CSVImportError
from seasonlens.storage import SeriesMetadata, list_series, read_series


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.db = self.folder / 'private.sqlite'
        self.csv = self.folder / 'master.csv'
        self.meta = self.folder / 'metadata.json'
        self.metadata = SeriesMetadata('SYNTH_A', 'Invented A', 'Invented units', 'SYNTHETIC', 'Invented daily level', 'Synthetic test fixture')
        self.meta.write_text(json.dumps([asdict(self.metadata)]))

    def test_missing_policy_and_cutoff_preserve_import_csv_validation(self):
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,100\n2024-01-02,SYNTH_A,\n2024-01-03,SYNTH_A,120\n2024-02-01,SYNTH_A,999\n')
        with self.assertRaises(CSVImportError):
            import_master(self.db, self.csv, self.meta, as_of=date(2024, 1, 31))
        summaries, omissions = import_master(self.db, self.csv, self.meta, skip_missing=True, as_of=date(2024, 1, 31))
        self.assertEqual(summaries[0].inserted, 2)
        self.assertEqual(omissions[0]['skipped_missing_rows'], (3,))
        self.assertEqual(omissions[0]['excluded_future_rows'], (5,))
        self.assertEqual(read_series(self.db, 'SYNTH_A')['value'].tolist(), [100., 120.])

    def test_duplicate_missing_beyond_cutoff_does_not_escape(self):
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,100\n2025-01-01,SYNTH_A,\n2025-01-01,SYNTH_A,120\n')
        with self.assertRaises(CSVImportError):
            import_master(self.db, self.csv, self.meta, skip_missing=True, as_of=date(2024, 1, 31))
        self.assertFalse(self.db.exists())

    def test_multiple_series_are_prepared_before_atomic_write(self):
        second = SeriesMetadata('SYNTH_B', 'Invented B', 'Invented units', 'SYNTHETIC', 'Invented daily level', 'Synthetic test fixture')
        self.meta.write_text(json.dumps([asdict(self.metadata), asdict(second)]))
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,100\n2024-01-01,SYNTH_B,malformed\n')
        with self.assertRaises(CSVImportError):
            import_master(self.db, self.csv, self.meta)
        self.assertFalse(self.db.exists())
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,100\n2024-01-01,SYNTH_B,200\n')
        self.assertEqual(len(import_master(self.db, self.csv, self.meta)[0]), 2)
        self.assertEqual(len(list_series(self.db)), 2)

    def test_keyed_metadata_and_explicit_instrument_mapping(self):
        record = asdict(self.metadata)
        record.pop('series_id')
        record['instrument'] = 'INPUT_A'
        self.meta.write_text(json.dumps({'SYNTH_A': record}))
        self.csv.write_text('date,instrument_id,value\n2024-01-01,INPUT_A,100\n')
        self.assertEqual(import_master(self.db, self.csv, self.meta)[0][0].series_id, 'SYNTH_A')

    def test_csv_cannot_masquerade_as_direct_ecb_even_with_canonical_metadata(self):
        from seasonlens.ecb import ecb_metadata
        self.meta.write_text(json.dumps([asdict(ecb_metadata()['EUR_PLN'])]))
        self.csv.write_text('date,instrument_id,value\n2024-01-01,EUR_PLN,999\n')
        with self.assertRaisesRegex(ValueError, 'cannot be imported from CSV'):
            import_master(self.db, self.csv, self.meta)
        self.assertFalse(self.db.exists())

    def test_cli_reports_counts_without_raw_values_and_refuses_overwrite(self):
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,123.456789\n')
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(main(['--db', str(self.db), 'import-master', str(self.csv), '--metadata', str(self.meta)]), 0)
            self.assertEqual(main(['--db', str(self.db), 'export', '--series', 'SYNTH_A', '--output', str(self.folder / 'output.csv')]), 0)
            self.assertEqual(main(['--db', str(self.db), 'export', '--series', 'SYNTH_A', '--output', str(self.folder / 'output.csv')]), 1)
        self.assertNotIn('123.456789', output.getvalue() + errors.getvalue())
        self.assertIn('live months may be incomplete', output.getvalue())

    def test_cli_provider_failure_returns_error(self):
        with patch('seasonlens.cli.update_ecb', side_effect=ValueError('ECB rate is invalid.')), redirect_stdout(StringIO()), redirect_stderr(StringIO()) as errors:
            self.assertEqual(main(['--db', str(self.db), 'update-ecb']), 1)
        self.assertIn('ECB rate is invalid', errors.getvalue())

    def test_cli_backup_creates_independent_snapshot(self):
        self.csv.write_text('date,instrument_id,value\n2024-01-01,SYNTH_A,10\n')
        import_master(self.db, self.csv, self.meta)
        destination = self.folder / 'snapshot.sqlite'
        with redirect_stdout(StringIO()):
            self.assertEqual(main(['--db', str(self.db), 'backup', '--output', str(destination)]), 0)
        self.assertEqual(read_series(destination, 'SYNTH_A').loc[0, 'value'], 10.)


if __name__ == '__main__':
    unittest.main()
