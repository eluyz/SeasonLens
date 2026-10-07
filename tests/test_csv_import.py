"""Synthetic parsing cases with independently specified rows and results."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

from seasonlens.csv_import import CSVImportError, import_csv
from seasonlens.monthly import aggregate_monthly


class CSVImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'input.csv'

    def tearDown(self):
        self.directory.cleanup()

    def read(self, text, **options):
        self.path.write_text(text, encoding='utf-8')
        defaults = dict(date_column='date', value_column='value', date_format='%Y-%m-%d')
        defaults.update(options)
        return import_csv(self.path, **defaults)

    def test_selects_one_instrument_and_preserves_zero_negative_and_source_lines(self):
        text = 'date,instrument_id,value\n2024-01-03,A,120\n2024-01-03,B,999\n2024-01-01,A,100\n2024-02-01,A,0\n2024-02-02,A,-4\n'
        result = self.read(text, instrument_column='instrument_id', instrument='A')
        self.assertEqual(result.frame.value.tolist(), [100, 120, 0, -4])
        self.assertEqual(result.source_rows, (4, 2, 5, 6))
        self.assertEqual(result.filtered_instrument_rows, (3,))
        self.assertFalse(result.report.has_errors)
        monthly = aggregate_monthly(result.frame)
        self.assertEqual(monthly.means.loc[2024, 1], 110)
        self.assertEqual(monthly.means.loc[2024, 2], -2)
        self.assertEqual(self.path.read_text(), text)

    def test_blanks_reject_by_default_and_skip_only_with_explicit_policy(self):
        text = 'date,value\n2024-01-01,100\n2024-01-02, \n2024-01-03,120\n'
        with self.assertRaises(CSVImportError) as error:
            self.read(text)
        self.assertEqual(error.exception.report.issues[0].row, 3)
        result = self.read(text, missing_values='skip')
        self.assertEqual(result.frame.value.tolist(), [100, 120])
        self.assertEqual(result.skipped_missing_rows, (3,))
        self.assertEqual(result.report.total_rows, 3)
        self.assertTrue(result.report.has_errors)  # Input report before the authorized omission.

    def test_duplicate_with_blank_is_rejected_before_missing_skip(self):
        with self.assertRaises(CSVImportError) as error:
            self.read('date,value\n2024-01-01,100\n2024-01-01,\n', missing_values='skip')
        self.assertIn('duplicate_date', [issue.code for issue in error.exception.report.issues])

    def test_explicit_semicolon_decimal_comma_and_day_first_format(self):
        result = self.read('day;price\n31/01/2024;1,25\n01/02/2024;-2,5\n', date_column='day', value_column='price', date_format='%d/%m/%Y', delimiter=';', decimal=',')
        self.assertEqual(result.frame.value.tolist(), [1.25, -2.5])
        self.assertEqual(result.frame.date.dt.month.tolist(), [1, 2])

    def test_invalid_values_never_become_skippable_missing(self):
        for value in ['NaN', 'NA', 'inf', '1e999', '1,234.5', 'abc']:
            with self.subTest(value=value), self.assertRaises(CSVImportError):
                self.read(f'date,value\n2024-01-01,{value}\n', missing_values='skip')
        with self.assertRaises(CSVImportError):
            self.read('date;value\n2024-01-01;1.25\n', delimiter=';', decimal=',')

    def test_invalid_dates_nonmidnight_and_timezone_are_rejected(self):
        for value, pattern in [('01/02/2024', '%Y-%m-%d'), ('2024-02-30', '%Y-%m-%d'), ('2024-01-01 01:00', '%Y-%m-%d %H:%M')]:
            with self.subTest(value=value), self.assertRaises(CSVImportError):
                self.read(f'date,value\n{value},100\n', date_format=pattern)

    def test_cutoff_is_explicit_and_does_not_hide_invalid_values_or_duplicates(self):
        text = 'date,value\n2024-01-03,300\n2024-01-01,100\n2024-01-02,200\n'
        result = self.read(text, max_date=date(2024, 1, 2))
        self.assertEqual(result.frame.value.tolist(), [100, 200])
        self.assertEqual(result.filtered_date_rows, (2,))
        for text in ['date,value\n2024-01-01,1\n2024-01-03,abc\n', 'date,value\n2024-01-01,1\n2024-01-03,2\n2024-01-03,\n']:
            with self.assertRaises(CSVImportError):
                self.read(text, max_date=date(2024, 1, 2), missing_values='skip')

    def test_cutoff_and_missing_counts_are_disjoint(self):
        result = self.read('date,value\n2024-01-01,1\n2024-01-02,\n2024-01-03,\n', missing_values='skip', max_date=date(2024,1,2))
        self.assertEqual(result.skipped_missing_rows, (3,))
        self.assertEqual(result.filtered_date_rows, (4,))
        self.assertEqual(result.report.total_rows, 3)

    def test_malformed_structure_is_fatal_even_for_unselected_instrument(self):
        for text in ['date,value\n2024-01-01,1,2\n', 'date,date,value\n2024-01-01,2024-01-01,1\n', 'date,\n2024-01-01,1\n', 'date,value\n"2024-01-01,1\n', 'date,value\n\n']:
            with self.subTest(text=text), self.assertRaises(CSVImportError):
                self.read(text)
        with self.assertRaises(CSVImportError):
            self.read('date,instrument_id,value\n2024-01-01,A,1\n2024-01-01,B\n', instrument_column='instrument_id', instrument='A')

    def test_multiline_other_field_and_bom_keep_physical_line_starts(self):
        result = self.read('\ufeffdate,value,note\n2024-01-02,2,"two\nlines"\n2024-01-01,1,single\n')
        self.assertEqual(result.source_rows, (4, 2))

    def test_physical_preamble_skipping(self):
        result = self.read('description\nsecond preamble\ndate,value\n2024-01-01,1\n', skip_rows=2)
        self.assertEqual(result.source_rows, (4,))

    def test_empty_missing_or_unmatched_selection_never_returns_empty_success(self):
        for text in ['', 'date,value\n', 'date,value\n2024-01-01,\n']:
            with self.subTest(text=text), self.assertRaises(CSVImportError):
                self.read(text, missing_values='skip')
        with self.assertRaises(CSVImportError):
            self.read('date,instrument_id,value\n2024-01-01,A,1\n', instrument_column='instrument_id', instrument='B')
        with self.assertRaises(CSVImportError):
            self.read('date,value\n2024-01-01,1\n', max_date=date(2023,12,31))

    def test_bad_configuration_rejected(self):
        for options in [dict(date_column='value'), dict(date_format='%m-%d'), dict(date_format='%%Y-%m-%d'), dict(date_format='%Y-%m-%d %Z'), dict(date_format='%Y-%m-%d%z'), dict(delimiter=';;'), dict(decimal=':'), dict(missing_values='fill'), dict(skip_rows=True), dict(instrument='A'), dict(instrument_column='date', instrument='A')]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.read('date,value\n2024-01-01,1\n', **options)

    def test_master_cannot_mix_instruments_without_selection(self):
        with self.assertRaises(CSVImportError) as error:
            self.read('date,instrument_id,value\n2024-01-01,A,1\n2024-01-02,B,2\n')
        self.assertEqual(error.exception.report.issues[0].code, 'missing_instrument_selection')


if __name__ == '__main__':
    unittest.main()
