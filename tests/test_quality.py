"""Synthetic, independently specified quality-report acceptance checks."""

import unittest
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens.quality import QualityIssue, QualityReport, inspect_series


def frame(dates, values):
    return pd.DataFrame({"date": pd.to_datetime(dates, format="ISO8601"), "value": values})


class QualityTests(unittest.TestCase):
    def test_valid_unsorted_series_with_gaps_zero_negative_and_unchanged_input(self):
        data = frame(["2026-12-31", "2024-02-29", "2024-01-01"], [0, -5, 12])
        data.index = [8, 8, 1]
        original = data.copy(deep=True)
        report = inspect_series(data)
        self.assertEqual(report, QualityReport(3, ()))
        self.assertFalse(report.has_errors)
        assert_frame_equal(data, original)

    def test_manual_issues_include_all_duplicates_despite_missing_values(self):
        data = frame(["2024-01-01", "2024-01-01", None, "2024-01-03 00:00:00.000000001"], [2, np.nan, np.inf, -np.inf])
        data.index = [4, 4, 4, 4]
        original = data.copy(deep=True)
        report = inspect_series(data, source_rows=[2, 3, 5, 8])
        self.assertEqual(report.total_rows, 4)
        self.assertTrue(report.has_errors)
        self.assertEqual(
            [(issue.row, issue.code) for issue in report.issues],
            [(5, "missing_date"), (8, "non_daily_date"), (2, "duplicate_date"), (3, "duplicate_date"), (3, "missing_value"), (5, "nonfinite_value"), (8, "nonfinite_value")],
        )
        assert_frame_equal(data, original)

    def test_default_row_numbers_are_positions(self):
        data = frame(["2024-01-01", "2024-01-02"], [np.nan, np.inf])
        data.index = [100, 200]
        self.assertEqual([(i.row, i.code) for i in inspect_series(data).issues], [(1, "missing_value"), (2, "nonfinite_value")])

    def test_timezone_reports_structural_error_and_duplicate_rows(self):
        data = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-01"], utc=True), "value": [1, 2]})
        self.assertEqual(
            [(i.row, i.code) for i in inspect_series(data).issues],
            [(None, "timezone_date"), (1, "duplicate_date"), (2, "duplicate_date")],
        )

    def test_dates_are_not_parsed(self):
        data = pd.DataFrame({"date": ["2024-01-01"], "value": [1]})
        self.assertEqual([i.code for i in inspect_series(data).issues], ["invalid_date_type"])
        self.assertEqual(data.loc[0, "date"], "2024-01-01")

    def test_empty_and_structural_columns(self):
        empty = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "value": pd.Series(dtype="float64")})
        self.assertEqual([i.code for i in inspect_series(empty).issues], ["empty_data"])
        missing = pd.DataFrame({"other": [1]})
        self.assertEqual([i.code for i in inspect_series(missing).issues], ["invalid_date_type", "invalid_value_type"])
        duplicate = pd.concat([frame(["2024-01-01"], [1]), pd.DataFrame({"value": [2]})], axis=1)
        self.assertEqual([i.code for i in inspect_series(duplicate).issues], ["duplicate_columns", "invalid_value_type"])

    def test_duplicate_auxiliary_columns_rejected_like_monthly_core(self):
        data = frame(["2024-01-01"], [1])
        data = pd.concat([data, pd.DataFrame([[2, 3]], columns=["other", "other"])], axis=1)
        self.assertEqual([i.code for i in inspect_series(data).issues], ["duplicate_columns"])

    def test_invalid_value_types_and_nullable_missing(self):
        for values in ([True], [1 + 2j], ["1"], pd.Series([True], dtype="boolean")):
            with self.subTest(dtype=str(pd.Series(values).dtype)):
                self.assertEqual([i.code for i in inspect_series(frame(["2024-01-01"], values)).issues], ["invalid_value_type"])
        nullable = frame(["2024-01-01", "2024-01-02", "2024-01-03"], pd.Series([1, pd.NA, np.inf], dtype="Float64"))
        self.assertEqual([(i.row, i.code) for i in inspect_series(nullable).issues], [(2, "missing_value"), (3, "nonfinite_value")])

    def test_supported_numeric_dtypes(self):
        for dtype in ["float16", "float32", "float64", "int64", "Float32", "Float64", "Int64"]:
            with self.subTest(dtype=dtype):
                data = frame(["2024-01-01", "2024-01-02"], pd.Series([0, -1], dtype=dtype))
                self.assertFalse(inspect_series(data).has_errors)

    @unittest.skipIf(np.dtype(np.longdouble).itemsize <= 8, "Platform has no float wider than 64 bits")
    def test_wide_float_rejected(self):
        data = frame(["2024-01-01"], np.array([1], dtype=np.longdouble))
        self.assertEqual([i.code for i in inspect_series(data).issues], ["invalid_value_type"])

    def test_bad_source_rows_rejected(self):
        data = frame(["2024-01-01"], [1])
        for mapping in ([], [1, 2], [0], [-1], [True], [np.bool_(True)], [1.5], ["2"], "2", 2):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                inspect_series(data, source_rows=mapping)
        self.assertEqual(inspect_series(data, source_rows=[np.int64(2)]), QualityReport(1, ()))

    def test_report_objects_are_frozen(self):
        issue = QualityIssue(1, "missing_value", "Value is missing.")
        report = QualityReport(1, (issue,))
        with self.assertRaises(FrozenInstanceError):
            issue.row = 2
        with self.assertRaises(FrozenInstanceError):
            report.total_rows = 2


if __name__ == "__main__":
    unittest.main()
