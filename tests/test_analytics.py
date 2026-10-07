"""Hand-calculated analytics definitions and strict-input boundary checks."""

from datetime import date, datetime
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from seasonlens.analytics import (convert_eur_to_pln, monthly_returns,
                                 moving_averages, normalized_seasonality,
                                 partial_month_comparison)


def daily(dates, values):
    return pd.DataFrame({"date": pd.to_datetime(dates), "value": values})


class AnalyticsTests(unittest.TestCase):
    def test_sma_counts_observations_and_waits_for_full_window(self):
        data = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=51, freq="2D"),
                             "value": list(range(1, 52))}).iloc[::-1]
        original = data.copy(deep=True)
        cutoff = data["date"].sort_values().iloc[49].date()
        result = moving_averages(data, as_of=cutoff)
        self.assertEqual(result.excluded_future_observations, 1)
        self.assertEqual(len(result.frame), 50)
        self.assertTrue(result.frame.sma20.iloc[:19].isna().all())
        self.assertEqual(result.frame.sma20.iloc[19], 10.5)
        self.assertEqual(result.frame.sma20.iloc[-1], 40.5)
        self.assertTrue(result.frame.sma50.iloc[:49].isna().all())
        self.assertEqual(result.frame.sma50.iloc[-1], 25.5)
        assert_frame_equal(data, original)

    def test_sma_allows_zero_negative_and_no_visible_observations(self):
        data = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=20), "value": [-2] * 10 + [0] * 10})
        self.assertEqual(moving_averages(data, as_of=date(2025, 1, 20)).frame.sma20.iloc[-1], -1)
        self.assertTrue(moving_averages(data, as_of=date(2024, 12, 31)).frame.empty)

    def test_monthly_returns_use_last_close_not_monthly_average(self):
        data = daily(["2024-12-31", "2025-01-01", "2025-01-30", "2025-02-04", "2025-02-05"], [100, 200, 110, 121, 999])
        result = monthly_returns(data, as_of=date(2025, 2, 4))
        january, february = result.frame.loc["2025-01"], result.frame.loc["2025-02"]
        self.assertAlmostEqual(january.return_pct, 10)
        self.assertAlmostEqual(february.return_pct, 10)
        self.assertEqual(january.close, 110)
        self.assertEqual(january.observation_count, 2)
        self.assertEqual(february.last_observation_date, pd.Timestamp("2025-02-04"))
        self.assertEqual(february.calendar_status, "month_in_progress")
        self.assertEqual(result.excluded_future_observations, 1)

    def test_missing_calendar_month_breaks_return_instead_of_skipping(self):
        result = monthly_returns(daily(["2025-01-31", "2025-03-31"], [100, 200]), as_of=date(2025, 4, 30))
        self.assertEqual(list(result.frame.index.astype(str)), ["2025-01", "2025-02", "2025-03", "2025-04"])
        self.assertTrue(result.frame.return_pct.isna().all())
        self.assertEqual(result.frame.loc["2025-02", "observation_count"], 0)
        self.assertTrue(pd.isna(result.frame.loc["2025-04", "close"]))
        self.assertEqual(result.frame.loc["2025-04", "calendar_status"], "month_ended")

    def test_normalized_first_observation_bases_and_equal_year_monthly_means(self):
        # 2024 base Jan3=10 -> Jan mean=(100+120)/2=110; Feb=150.
        # 2025 base Jan9=20 -> Jan=100; Feb=200. February baseline=175.
        data = daily(["2024-01-03", "2024-01-05", "2024-02-01", "2025-01-09", "2025-02-01", "2026-01-15", "2026-02-02", "2026-02-03"], [10, 12, 15, 20, 40, 50, 60, 999])
        original = data.copy(deep=True)
        result = normalized_seasonality(data, as_of=date(2026, 2, 2), window_years=5)
        self.assertEqual(result.seasonal.profile.loc[1, "mean"], 105)
        self.assertEqual(result.seasonal.profile.loc[2, "mean"], 175)
        self.assertEqual(result.seasonal.profile.loc[2, "minimum"], 150)
        self.assertEqual(result.seasonal.profile.loc[2, "maximum"], 200)
        self.assertEqual(result.seasonal.current.loc[2, "mean"], 120)
        self.assertEqual(result.seasonal.excluded_future_observations, 1)
        self.assertEqual(result.bases.loc[2024, "base_date"], pd.Timestamp("2024-01-03"))
        self.assertEqual(result.bases.loc[2024, "base_value"], 10)
        self.assertTrue(pd.isna(result.bases.loc[2023, "base_date"]))
        self.assertTrue(result.yearly_monthly.loc[2023].isna().all())
        self.assertTrue(result.yearly_counts.loc[2023].eq(0).all())
        assert_frame_equal(data, original)

    def test_normalized_late_base_is_exposed_and_missing_reference_is_valid(self):
        result = normalized_seasonality(daily(["2025-03-01", "2025-03-02"], [100, 120]), as_of=date(2026, 1, 15), window_years=1)
        self.assertTrue(pd.isna(result.yearly_monthly.loc[2025, 1]))
        self.assertEqual(result.yearly_monthly.loc[2025, 3], 110)
        self.assertEqual(result.bases.loc[2025, "base_date"].month, 3)
        self.assertTrue(result.seasonal.current["mean"].isna().all())
        future = normalized_seasonality(daily(["2027-01-01"], [10]), as_of=date(2026, 1, 15), window_years=1)
        self.assertEqual(future.seasonal.excluded_future_observations, 1)
        self.assertTrue(future.bases.base_value.isna().all())

    def test_partial_month_uses_same_day_not_future_days_and_equal_years(self):
        data = daily(["2024-10-01", "2024-10-06", "2024-10-07", "2025-10-04", "2025-10-30", "2026-10-01", "2026-10-06", "2026-10-07"], [100, 120, 999, 200, 999, 150, 170, 999])
        result = partial_month_comparison(data, as_of=date(2026, 10, 6), window_years=5)
        self.assertEqual((result.start_year, result.end_year), (2021, 2025))
        self.assertEqual(result.baseline_mean, 155)
        self.assertEqual((result.baseline_minimum, result.baseline_maximum), (110, 200))
        self.assertEqual((result.year_count, result.observation_count), (2, 3))
        self.assertEqual((result.current_mean, result.current_observation_count), (160, 2))
        self.assertEqual(result.difference, 5)
        self.assertEqual(result.excluded_future_observations, 1)
        self.assertEqual(result.years.loc[2025, "through_date"], date(2025, 10, 6))
        self.assertEqual(result.years.loc[2023, "observation_count"], 0)

    def test_partial_month_february29_clamps_non_leap_history(self):
        data = daily(["2022-02-28", "2022-03-01", "2023-02-28", "2024-02-29"], [100, 999, 200, 180])
        result = partial_month_comparison(data, as_of=date(2024, 2, 29), window_years=2)
        self.assertEqual(result.years.loc[2023, "through_date"], date(2023, 2, 28))
        self.assertEqual(result.baseline_mean, 150)
        self.assertEqual(result.difference, 30)

    def test_currency_conversion_matches_only_exact_dates_without_fill(self):
        prices = daily(["2025-01-03", "2025-01-01", "2025-01-02", "2025-01-05"], [30, 10, -20, 999])
        fx = daily(["2025-01-04", "2025-01-03", "2025-01-01", "2025-01-05"], [4, 5, 4, 999])
        original_price, original_fx = prices.copy(deep=True), fx.copy(deep=True)
        result = convert_eur_to_pln(prices, fx, as_of=date(2025, 1, 4))
        self.assertEqual(result.frame.pln_price.tolist(), [40, 150])
        self.assertEqual(result.frame.date.tolist(), [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-03")])
        self.assertEqual((result.unmatched_price_observations, result.unmatched_fx_observations), (1, 1))
        self.assertEqual((result.excluded_future_price_observations, result.excluded_future_fx_observations), (1, 1))
        assert_frame_equal(prices, original_price)
        assert_frame_equal(fx, original_fx)

    def test_currency_conversion_empty_match_is_auditable(self):
        result = convert_eur_to_pln(daily(["2025-01-01"], [10]), daily(["2025-01-02"], [4]), as_of=date(2025, 1, 2))
        self.assertTrue(result.frame.empty)
        self.assertEqual((result.unmatched_price_observations, result.unmatched_fx_observations), (1, 1))

    def test_invalid_future_rows_positive_rules_and_options_reject(self):
        for function in (moving_averages, monthly_returns, normalized_seasonality, partial_month_comparison):
            options = {"window_years": 5} if function in (normalized_seasonality, partial_month_comparison) else {}
            for invalid in (daily(["2027-01-01", "2027-01-01"], [1, 2]), daily(["2027-01-01"], [np.nan])):
                with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                    function(invalid, as_of=date(2026, 1, 15), **options)
            with self.assertRaises(ValueError):
                function(daily(["2025-01-01"], [1]), as_of=datetime(2026, 1, 15), **options)
        for function in (monthly_returns, normalized_seasonality):
            options = {"window_years": 5} if function == normalized_seasonality else {}
            for value in (0, -1):
                with self.assertRaises(ValueError):
                    function(daily(["2027-01-01"], [value]), as_of=date(2026, 1, 15), **options)
        with self.assertRaises(ValueError):
            convert_eur_to_pln(daily(["2025-01-01"], [1]), daily(["2027-01-01"], [0]), as_of=date(2026, 1, 15))
        for function in (normalized_seasonality, partial_month_comparison):
            with self.assertRaises(ValueError):
                function(daily(["2025-01-01"], [1]), as_of=date(2026, 1, 15), window_years=True)

    def test_numeric_overflow_never_becomes_missing_or_infinity(self):
        with self.assertRaisesRegex(ValueError, "Monthly return.*numeric range"):
            monthly_returns(daily(["2025-01-01", "2025-02-01"], [1e-308, 1e308]), as_of=date(2025, 2, 1))
        with self.assertRaisesRegex(ValueError, "Year normalization.*numeric range"):
            normalized_seasonality(daily(["2025-01-01", "2025-02-01"], [1e-308, 1e308]), as_of=date(2026, 1, 15), window_years=1)
        with self.assertRaisesRegex(ValueError, "Currency conversion.*numeric range"):
            convert_eur_to_pln(daily(["2025-01-01"], [1e308]), daily(["2025-01-01"], [10]), as_of=date(2025, 1, 1))
        with self.assertRaisesRegex(ValueError, "Partial-month baseline.*numeric range"):
            partial_month_comparison(daily(["2024-01-01", "2025-01-01"], [1e308, 1e308]), as_of=date(2026, 1, 15), window_years=2)

    def test_custom_columns_and_result_independence(self):
        data = daily(["2025-01-01", "2026-01-01"], [10, 20]).rename(columns={"date": "day", "value": "price"})
        original = data.copy(deep=True)
        result = normalized_seasonality(data, as_of=date(2026, 1, 15), window_years=1, date_column="day", value_column="price")
        result.yearly_monthly.loc[2025, 1] = 999
        self.assertEqual(result.seasonal.profile.loc[1, "mean"], 100)
        result.bases.loc[2025, "base_value"] = 999
        assert_frame_equal(data, original)


if __name__ == "__main__":
    unittest.main()
