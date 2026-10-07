"""Independent expected-value and input-contract checks using unittest."""

import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens import MonthlyResult, aggregate_monthly


def daily_frame(dates, values):
    return pd.DataFrame({"date": pd.to_datetime(dates), "value": values})


class MonthlyAggregationTests(unittest.TestCase):
    def test_manual_means_counts_gaps_and_unsorted_input(self):
        # January 2020: (10 + 20 + 0) / 3 = 10. February: -6.
        # All of 2021 is absent. January 2022: (4 + 8) / 2 = 6.
        frame = daily_frame(
            ["2022-01-07", "2020-01-09", "2020-02-01", "2020-01-01", "2022-01-01", "2020-01-20"],
            [8, 20, -6, 10, 4, 0],
        )
        result = aggregate_monthly(frame)
        self.assertIsInstance(result, MonthlyResult)
        years = pd.Index([2020, 2021, 2022], name="year")
        months = pd.Index(range(1, 13), name="month")
        expected_means = pd.DataFrame(np.nan, index=years, columns=months)
        expected_means.loc[2020, 1] = 10.0
        expected_means.loc[2020, 2] = -6.0
        expected_means.loc[2022, 1] = 6.0
        expected_counts = pd.DataFrame(0, index=years, columns=months, dtype="int64")
        expected_counts.loc[2020, 1] = 3
        expected_counts.loc[2020, 2] = 1
        expected_counts.loc[2022, 1] = 2
        assert_frame_equal(result.means, expected_means)
        assert_frame_equal(result.counts, expected_counts)
        ordered = aggregate_monthly(frame.sort_values("date"))
        assert_frame_equal(result.means, ordered.means)
        assert_frame_equal(result.counts, ordered.counts)

    def test_input_is_unchanged_and_repeated_indexes_are_valid(self):
        frame = daily_frame(["2020-02-29", "2020-02-01"], [2.5, 1.5])
        frame.index = [7, 7]
        frame["annotation"] = ["leap day", "month start"]
        original = frame.copy(deep=True)
        result = aggregate_monthly(frame)
        assert_frame_equal(frame, original)
        self.assertEqual(result.means.loc[2020, 2], 2.0)
        self.assertEqual(result.counts.loc[2020, 2], 2)

    def test_custom_columns_and_nullable_numeric_dtype(self):
        frame = pd.DataFrame(
            {"observation": pd.to_datetime(["2025-12-31"]), "price": pd.Series([0], dtype="Int64")}
        )
        result = aggregate_monthly(frame, date_column="observation", value_column="price")
        self.assertEqual(result.means.loc[2025, 12], 0.0)
        self.assertEqual(result.counts.loc[2025, 12], 1)
        self.assertEqual(result.means.shape, (1, 12))

    def test_rejects_invalid_dates(self):
        cases = [
            (pd.DataFrame({"date": ["2020-01-01"], "value": [1]}), "datetime dtype"),
            (daily_frame([None], [1]), "missing"),
            (daily_frame(["2020-01-01 01:00"], [1]), "midnight"),
            (daily_frame(["2020-01-01", "2020-01-01"], [1, 2]), "Duplicate dates"),
            (pd.DataFrame({"date": pd.to_datetime(["2020-01-01"], utc=True), "value": [1]}), "timezone-naive"),
        ]
        for frame, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                aggregate_monthly(frame)

    def test_rejects_invalid_values(self):
        cases = [
            ([np.nan], "missing"),
            ([np.inf], "finite"),
            ([-np.inf], "finite"),
            ([True], "numeric dtype"),
            ([1 + 2j], "numeric dtype"),
            (["1"], "numeric dtype"),
            (pd.Series([pd.NA], dtype="Float64"), "missing"),
            (pd.Series([True], dtype="boolean"), "numeric dtype"),
        ]
        for values, message in cases:
            frame = daily_frame(["2020-01-01"], values)
            with self.subTest(values=str(values)), self.assertRaisesRegex(ValueError, message):
                aggregate_monthly(frame)

    def test_rejects_empty_data_and_non_dataframe(self):
        empty = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "value": pd.Series(dtype="float64")})
        with self.assertRaisesRegex(ValueError, "At least one"):
            aggregate_monthly(empty)
        with self.assertRaisesRegex(ValueError, "DataFrame"):
            aggregate_monthly([])

    def test_rejects_aggregation_overflow_from_finite_values(self):
        frame = daily_frame(["2020-01-01", "2020-01-02"], [1e308, 1e308])
        with self.assertRaisesRegex(ValueError, "numeric range.*overflow"):
            aggregate_monthly(frame)

    @unittest.skipIf(np.dtype(np.longdouble).itemsize <= 8, "Platform has no float wider than 64 bits")
    def test_rejects_float_dtype_wider_than_64_bits(self):
        frame = daily_frame(["2020-01-01"], np.array([1.0], dtype=np.longdouble))
        with self.assertRaisesRegex(ValueError, "up to 64 bits"):
            aggregate_monthly(frame)

    def test_rejects_invalid_column_choices(self):
        frame = daily_frame(["2020-01-01"], [1])
        cases = [
            ({"date_column": "missing"}, "missing"),
            ({"value_column": "missing"}, "missing"),
            ({"value_column": "date"}, "different"),
            ({"date_column": ""}, "nonempty strings"),
            ({"date_column": None}, "nonempty strings"),
            ({"value_column": 0}, "nonempty strings"),
        ]
        for options, message in cases:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, message):
                aggregate_monthly(frame, **options)
        duplicate_columns = pd.concat([frame, frame[["value"]]], axis=1)
        with self.assertRaisesRegex(ValueError, "unique"):
            aggregate_monthly(duplicate_columns)


if __name__ == "__main__":
    unittest.main()
