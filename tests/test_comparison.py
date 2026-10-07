"""Independent fixtures for calendar-year comparisons and technical windows."""

from datetime import date, datetime
import math
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens.comparison import recent_year_prices, technical_analysis


def daily(days, values):
    return pd.DataFrame({"date": pd.to_datetime(days), "value": values})


class ComparisonTests(unittest.TestCase):
    def test_hand_calculated_population_bands_and_full_window_minimum(self):
        data = daily(pd.date_range("2026-01-01", periods=20), [0.] * 10 + [2.] * 10)
        result = technical_analysis(data, as_of=date(2026, 1, 20)).frame
        self.assertEqual(list(result.columns), ["date", "value", "sma20", "sma100", "sma200", "bollinger_upper", "bollinger_lower"])
        self.assertTrue(result.loc[:18, ["sma20", "bollinger_upper", "bollinger_lower"]].isna().all().all())
        self.assertEqual(result.loc[19, "sma20"], 1.)
        self.assertEqual(result.loc[19, "bollinger_upper"], 3.)
        self.assertEqual(result.loc[19, "bollinger_lower"], -1.)
        self.assertTrue(result[["sma100", "sma200"]].isna().all().all())

    def test_full_history_warms_up_before_consumer_display_truncation(self):
        data = daily(pd.date_range("2024-01-01", periods=500), np.arange(1., 501.))
        result = technical_analysis(data, as_of=data.date.iloc[-1].date()).frame
        self.assertEqual(len(result), 500)
        self.assertEqual(result.loc[99, "sma100"], 50.5)
        self.assertEqual(result.loc[199, "sma200"], 100.5)
        self.assertEqual(result.loc[499, "sma200"], 400.5)
        visible = result.loc[result.date >= pd.Timestamp("2025-01-01")]
        self.assertTrue(visible.sma200.notna().all())

    def test_scaled_deviation_preserves_narrow_float_variation(self):
        level = 1e12
        data = daily(pd.date_range("2026-01-01", periods=20), [level] * 10 + [level + .125] * 10)
        result = technical_analysis(data, as_of=date(2026, 1, 20)).frame.iloc[-1]
        # Half the observations at either level: mean=level+.0625, sigma=.0625.
        self.assertEqual(result.sma20, level + .0625)
        self.assertEqual(result.bollinger_upper, level + .1875)
        self.assertEqual(result.bollinger_lower, level - .0625)

    def test_adjacent_float_levels_do_not_lose_the_band_width(self):
        low = 4.
        high = np.nextafter(low, math.inf)
        data = daily(pd.date_range("2026-01-01", periods=20), [low] * 10 + [high] * 10)
        result = technical_analysis(data, as_of=date(2026, 1, 20)).frame.iloc[-1]
        self.assertGreater(result.bollinger_upper, result.sma20)
        self.assertLess(result.bollinger_lower, result.sma20)

    def test_calendar_gaps_zero_negative_sorting_and_future_exclusions(self):
        data = daily(pd.date_range("2026-01-01", periods=21, freq="2D"), [-2.] * 10 + [0.] * 10 + [999.]).iloc[::-1]
        original = data.copy(deep=True)
        result = technical_analysis(data, as_of=date(2026, 2, 8))
        self.assertEqual(result.excluded_future_observations, 1)
        self.assertEqual(len(result.frame), 20)
        self.assertEqual(result.frame.iloc[-1].sma20, -1.)
        self.assertEqual(result.frame.iloc[-1].bollinger_upper, 1.)
        self.assertEqual(result.frame.iloc[-1].bollinger_lower, -3.)
        assert_frame_equal(data, original)

    def test_recent_year_mean_equal_weights_and_current_year_included(self):
        data = daily(["2021-01-01", "2022-01-01", "2022-01-03", "2026-01-15", "2026-01-16"], [999., 100., 120., 200., 999.])
        result = recent_year_prices(data, as_of=date(2026, 1, 15))
        self.assertEqual(result.years, (2022, 2023, 2024, 2025, 2026))
        self.assertEqual(result.monthly_means.loc[2022, 1], 110.)
        self.assertEqual(result.monthly_means.loc[2026, 1], 200.)
        self.assertEqual(result.mean_series.loc[1], 155.)
        self.assertEqual(result.year_count.loc[1], 2)
        self.assertEqual(result.observation_count.loc[1], 3)
        self.assertEqual(result.excluded_future_observations, 1)
        self.assertTrue(result.monthly_means.loc[2023].isna().all())
        self.assertTrue(result.monthly_counts.loc[2023].eq(0).all())

    def test_later_month_mean_uses_history_without_current_extrapolation(self):
        data = daily(["2022-12-01", "2025-12-01", "2026-01-01", "2026-12-01"], [100., 200., 10., 999.])
        result = recent_year_prices(data, as_of=date(2026, 1, 15))
        self.assertEqual(result.mean_series.loc[12], 150.)
        self.assertEqual(result.year_count.loc[12], 2)
        self.assertTrue(np.isnan(result.monthly_means.loc[2026, 12]))
        self.assertEqual(result.monthly_counts.loc[2026, 12], 0)
        self.assertTrue(np.isnan(result.mean_series.loc[2]))

    def test_empty_visible_series_preserves_shapes_without_filling(self):
        data = daily(["2027-01-01"], [0.])
        cutoff = date(2026, 1, 15)
        technical = technical_analysis(data, as_of=cutoff)
        recent = recent_year_prices(data, as_of=cutoff)
        self.assertTrue(technical.frame.empty)
        self.assertEqual(recent.monthly_means.shape, (5, 12))
        self.assertTrue(recent.monthly_means.isna().all().all())
        self.assertTrue(recent.year_count.eq(0).all())
        self.assertTrue(recent.observation_count.eq(0).all())
        self.assertEqual(recent.excluded_future_observations, 1)

    def test_invalid_excluded_rows_and_invalid_options_reject(self):
        cases = [daily(["2027-01-01", "2027-01-01"], [1., 2.]), daily(["2027-01-01"], [np.nan]), daily(["2027-01-01"], [np.inf])]
        for function in (technical_analysis, recent_year_prices):
            for data in cases:
                with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                    function(data, as_of=date(2026, 1, 15))
            with self.assertRaises(ValueError):
                function(daily(["2026-01-01"], [1.]), as_of=datetime(2026, 1, 15))
        with self.assertRaises(ValueError):
            recent_year_prices(daily(["2026-01-01"], [1.]), as_of=date(4, 1, 1))

    def test_recent_year_arithmetic_overflow_rejects(self):
        data = daily(["2022-01-01", "2026-01-01"], [1e308, 1e308])
        with self.assertRaisesRegex(ValueError, "Recent-year comparison mean.*numeric range"):
            recent_year_prices(data, as_of=date(2026, 1, 15))

    def test_extreme_bollinger_bound_overflow_rejects(self):
        # One observation per year avoids the monthly sum's separate limit.
        data = daily([f"{year}-01-01" for year in range(2000, 2020)], [-1e308, 1e308] * 10)
        with self.assertRaisesRegex(ValueError, "Bollinger bounds.*numeric range"):
            technical_analysis(data, as_of=date(2019, 1, 1))

    def test_result_independence_and_short_constant_series(self):
        data = daily(pd.date_range("2026-01-01", periods=20), [0.] * 20)
        original = data.copy(deep=True)
        result = technical_analysis(data, as_of=date(2026, 1, 20))
        self.assertEqual(result.frame.iloc[-1].bollinger_upper, 0.)
        self.assertEqual(result.frame.iloc[-1].bollinger_lower, 0.)
        result.frame.loc[0, "value"] = 999.
        assert_frame_equal(data, original)
        recent = recent_year_prices(data, as_of=date(2026, 1, 20))
        recent.monthly_means.loc[2026, 1] = 999.
        self.assertEqual(recent.mean_series.loc[1], 0.)
        assert_frame_equal(data, original)


if __name__ == "__main__":
    unittest.main()
