"""Hand-calculated fixtures for equal-year weighting and cutoff behavior."""

import unittest
from datetime import date, datetime
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens.seasonal import SeasonalResult, analyze_seasonality


def daily(dates, values):
    return pd.DataFrame({"date": pd.to_datetime(dates, format="ISO8601"), "value": values})


class SeasonalTests(unittest.TestCase):
    def test_hand_calculated_equal_year_mean_extrema_and_counts(self):
        data = daily(["2024-01-01", "2024-01-03", "2025-01-01", "2026-01-15"], [100, 120, 200, 155])
        result = analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=5)
        self.assertIsInstance(result, SeasonalResult)
        self.assertEqual((result.start_year, result.end_year, result.window_years), (2021, 2025, 5))
        months = pd.Index(range(1, 13), name="month")
        expected = pd.DataFrame({"mean": np.nan, "minimum": np.nan, "maximum": np.nan, "year_count": 0, "observation_count": 0}, index=months)
        expected.loc[1, ["mean", "minimum", "maximum"]] = [155., 110., 200.]
        expected.loc[1, ["year_count", "observation_count"]] = [2, 3]
        assert_frame_equal(result.profile, expected)
        current = pd.DataFrame({"mean": np.nan, "observation_count": 0, "difference": np.nan, "calendar_status": ["month_in_progress"] + ["after_cutoff"] * 11}, index=months)
        current.loc[1, ["mean", "difference"]] = [155., 0.]
        current.loc[1, "observation_count"] = 1
        assert_frame_equal(result.current, current)

    def test_exact_window_does_not_extend_to_available_old_years(self):
        data = daily(["2019-01-01", "2020-01-01", "2024-01-01", "2026-01-01"], [999, 999, 10, 20])
        result = analyze_seasonality(data, as_of=date(2026, 1, 5), window_years=5)
        self.assertEqual(result.profile.loc[1, "mean"], 10.)
        self.assertEqual(result.profile.loc[1, "year_count"], 1)
        self.assertEqual(result.profile.loc[1, "observation_count"], 1)

    def test_no_future_leak_and_cutoff_is_inclusive(self):
        data = daily(["2025-01-01", "2026-01-01", "2026-01-15", "2026-01-16", "2026-02-01", "2027-01-01"], [10, 10, 30, 999, 999, 999])
        result = analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=1)
        self.assertEqual(result.excluded_future_observations, 3)
        self.assertEqual(result.current.loc[1, "mean"], 20.)
        self.assertEqual(result.current.loc[1, "difference"], 10.)
        self.assertEqual(result.current.loc[1, "observation_count"], 2)
        self.assertTrue(result.current.loc[2:, "mean"].isna().all())
        self.assertTrue(result.current.loc[2:, "observation_count"].eq(0).all())

    def test_partial_reference_year_uses_all_past_baseline_months(self):
        data = daily(["2025-12-31", "2026-01-01"], [50, 25])
        result = analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=1)
        self.assertEqual(result.profile.loc[12, "mean"], 50.)
        self.assertTrue(np.isnan(result.current.loc[12, "mean"]))
        self.assertTrue(np.isnan(result.current.loc[1, "difference"]))

    def test_missing_baseline_never_uses_current_year(self):
        result = analyze_seasonality(daily(["2026-01-01"], [0]), as_of=date(2026, 1, 15), window_years=5)
        self.assertTrue(result.profile[["mean", "minimum", "maximum"]].isna().all().all())
        self.assertTrue(result.profile[["year_count", "observation_count"]].eq(0).all().all())
        self.assertEqual(result.current.loc[1, "mean"], 0.)
        self.assertTrue(result.current["difference"].isna().all())

    def test_empty_visible_selection_is_valid_with_explicit_exclusions(self):
        result = analyze_seasonality(daily(["2027-01-01"], [10]), as_of=date(2026, 1, 15), window_years=5)
        self.assertEqual(result.excluded_future_observations, 1)
        self.assertTrue(result.profile["mean"].isna().all())
        self.assertTrue(result.current["mean"].isna().all())
        self.assertTrue(result.current["observation_count"].eq(0).all())

    def test_zero_negative_values_and_absent_current_year(self):
        result = analyze_seasonality(daily(["2024-01-01", "2025-01-01"], [-20, 0]), as_of=date(2026, 1, 15), window_years=2)
        self.assertEqual(result.profile.loc[1, "mean"], -10.)
        self.assertEqual(result.profile.loc[1, "minimum"], -20.)
        self.assertEqual(result.profile.loc[1, "maximum"], 0.)
        self.assertTrue(result.current["mean"].isna().all())

    def test_calendar_status_is_independent_of_observations(self):
        data = daily(["2023-01-01"], [10])
        partial = analyze_seasonality(data, as_of=date(2024, 2, 28), window_years=1)
        self.assertEqual(partial.current.loc[1, "calendar_status"], "month_ended")
        self.assertEqual(partial.current.loc[2, "calendar_status"], "month_in_progress")
        self.assertEqual(partial.current.loc[3, "calendar_status"], "after_cutoff")
        ended = analyze_seasonality(data, as_of=date(2024, 2, 29), window_years=1)
        self.assertEqual(ended.current.loc[2, "calendar_status"], "month_ended")

    def test_invalid_excluded_rows_remain_fatal(self):
        cases = [
            daily(["2026-01-01", "2027-01-01"], [1, np.nan]),
            daily(["2027-01-01", "2027-01-01"], [1, 2]),
            daily(["2010-01-01", "2010-01-01"], [1, 2]),
            daily(["2027-01-01 00:01"], [1]),
            daily(["2027-01-01", "2027-01-02"], [1e308, 1e308]),
        ]
        for data in cases:
            with self.subTest(rows=len(data)), self.assertRaises(ValueError):
                analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=5)

    def test_options_reject_implicit_or_invalid_cutoff_and_window(self):
        data = daily(["2025-01-01"], [1])
        for cutoff in (None, "2026-01-15", datetime(2026, 1, 15), pd.Timestamp("2026-01-15")):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                analyze_seasonality(data, as_of=cutoff, window_years=5)
        for window in (True, np.bool_(True), 0, -1, 1.5, "5", None, 2026):
            with self.subTest(window=window), self.assertRaises(ValueError):
                analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=window)
        self.assertEqual(analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=np.int64(1)).window_years, 1)
        with self.assertRaises(ValueError):
            analyze_seasonality(data.iloc[:0], as_of=date(2026, 1, 15), window_years=1)

    def test_custom_columns_and_input_output_independence(self):
        data = daily(["2025-01-01", "2026-01-01"], [10, 20]).rename(columns={"date": "day", "value": "price"})
        data.index = [5, 5]
        original = data.copy(deep=True)
        result = analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=1, date_column="day", value_column="price")
        assert_frame_equal(data, original)
        result.profile.loc[1, "mean"] = 1000
        self.assertEqual(result.current.loc[1, "mean"], 20.)
        assert_frame_equal(data, original)
        with self.assertRaises(FrozenInstanceError):
            result.start_year = 2000

    def test_profile_overflow_is_explicit(self):
        data = daily(["2024-01-01", "2025-01-01"], [1e308, 1e308])
        with self.assertRaisesRegex(ValueError, "profile.*numeric range"):
            analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=2)

    def test_difference_overflow_is_explicit(self):
        data = daily(["2025-01-01", "2026-01-01"], [-1e308, 1e308])
        with self.assertRaisesRegex(ValueError, "difference.*numeric range"):
            analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=1)


if __name__ == "__main__":
    unittest.main()
