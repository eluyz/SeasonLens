import json
import math
import unittest
from datetime import date

import numpy as np
import pandas as pd

from seasonlens.market_analysis import (market_snapshot, market_indicators,
    seasonal_distribution, indexed_comparison, rolling_correlations,
    spread_series, pln_attribution, scenario_calculation)


def frame(dates, values):
    return pd.DataFrame({'date':pd.to_datetime(dates), 'value':values})


class MarketAnalysisTests(unittest.TestCase):
    def test_snapshot_dated_gapped_references_and_midrank(self):
        data=frame(['2024-12-30','2025-01-30','2025-02-27','2025-03-31','2025-04-01'],
                   [100.,110.,120.,120.,999.])
        result=market_snapshot(data,as_of=date(2025,3,31))
        self.assertEqual(result['last_date'],'2025-03-31')
        self.assertEqual(result['excluded_future_observations'],1)
        self.assertEqual(result['changes']['month']['target_date'],'2025-02-28')
        self.assertEqual(result['changes']['month']['reference_date'],'2025-02-27')
        self.assertEqual(result['changes']['month']['change_pct'],0)
        self.assertEqual(result['changes']['quarter']['reference_date'],'2024-12-30')
        self.assertAlmostEqual(result['changes']['ytd']['change_pct'],20)
        self.assertEqual(result['position']['one_year']['percentile'],75)
        self.assertIsNone(result['sma200'])
        json.dumps(result,allow_nan=False)

    def test_snapshot_negative_levels_keep_stats_not_percent(self):
        data=frame(['2025-01-01','2025-01-02'],[-2.,0.])
        result=market_snapshot(data,as_of=date(2025,1,2))
        self.assertEqual(result['last_value'],0)
        self.assertEqual(result['changes']['previous']['change'],2)
        self.assertIsNone(result['changes']['previous']['change_pct'])
        self.assertEqual(result['position']['one_year']['percentile'],75)

    def test_snapshot_empty_cutoff_and_sma200(self):
        data=frame(pd.date_range('2025-01-01',periods=200),[100.]*199+[200.])
        result=market_snapshot(data,as_of=date(2025,7,19))
        self.assertEqual(result['sma200'],100.5)
        self.assertAlmostEqual(result['distance_sma200_pct'],(200/100.5-1)*100)
        empty=market_snapshot(data,as_of=date(2024,12,31))
        self.assertIsNone(empty['last_value'])
        self.assertEqual(empty['position']['one_year']['observation_count'],0)
        json.dumps(empty,allow_nan=False)

    def test_rsi_seed_wilder_hand_reference(self):
        # Fourteen deltas: seven gains2, seven losses1 -> mean gains1/loss.5.
        values=[100.]
        for delta in [2.,-1.]*7+[0.]: values.append(values[-1]+delta)
        result=market_indicators(frame(pd.date_range('2025-01-01',periods=16),values),as_of=date(2025,1,16))
        self.assertEqual(result['rsi14'][:14],[None]*14)
        self.assertAlmostEqual(result['rsi14'][14],100*2/3)
        self.assertAlmostEqual(result['rsi14'][15],100*2/3)
        for values,expected in [([3.]*15,50), (list(range(15)),100), (list(range(15,0,-1)),0)]:
            self.assertEqual(market_indicators(frame(pd.date_range('2025-01-01',periods=15),values),as_of=date(2025,1,15))['rsi14'][14],expected)

    def test_volatility_unannualized_sample_and_invalid_window(self):
        values=[1.,2.]*10+[1.]
        result=market_indicators(frame(pd.date_range('2025-01-01',periods=21),values),as_of=date(2025,1,21))
        self.assertEqual(result['volatility20'][:20],[None]*20)
        self.assertAlmostEqual(result['volatility20'][20],100*math.log(2)*math.sqrt(20/19))
        bad=list(values);bad[0]=0
        invalid=market_indicators(frame(pd.date_range('2025-01-01',periods=21),bad),as_of=date(2025,1,21))
        self.assertIsNone(invalid['volatility20'][20])
        json.dumps(invalid,allow_nan=False)

    def test_completed_year_distribution_equal_weight(self):
        data=frame(['2023-01-01','2023-01-02','2024-01-01','2025-01-01','2025-01-02'],
                   [100.,120.,200.,999.,2000.])
        result=seasonal_distribution(data,as_of=date(2025,1,1),window_years=5)
        jan=result['months'][0]
        self.assertEqual((result['start_year'],result['end_year']),(2020,2024))
        self.assertEqual(jan,dict(month=1,mean=155.,median=155.,q25=132.5,q75=177.5,year_count=2,observation_count=3))
        self.assertIsNone(result['months'][1]['mean'])
        self.assertEqual(result['excluded_future_observations'],1)
        json.dumps(result,allow_nan=False)

    def test_base100_common_dates_no_fill_and_nonpositive(self):
        a=frame(['2025-01-01','2025-01-02','2025-01-03'],[5.,10.,20.])
        b=frame(['2025-01-02','2025-01-03','2025-01-04'],[100.,80.,999.])
        result=indexed_comparison({'a':a,'b':b},as_of=date(2025,1,3),start_date=date(2025,1,1))
        self.assertEqual(result['dates'],['2025-01-02','2025-01-03'])
        self.assertEqual(result['series']['a']['values'],[100,200])
        self.assertEqual(result['series']['b']['values'],[100,80])
        a.loc[2,'value']=-20
        result=indexed_comparison({'a':a,'b':b},as_of=date(2025,1,3),start_date=date(2025,1,1))
        self.assertEqual(result['series']['a']['values'],[None,None])
        json.dumps(result,allow_nan=False)

    def test_arbitrary_series_identifier_and_empty_interval_join(self):
        a=frame(['2025-01-01','2025-01-02'],[100.,110.])
        b=frame(['2025-01-02'],[10.])
        result=indexed_comparison({'date':a,'value':b},as_of=date(2025,1,2),start_date=date(2025,1,1))
        self.assertEqual(result['series']['date']['values'],[100.])
        result=rolling_correlations({'a':a,'b':b},as_of=date(2025,1,2),window=2)
        self.assertEqual(result['pairs'][0]['observations'],[])
        with self.assertRaises(ValueError):scenario_calculation(price=10**1000,fx=4)

    def test_return_correlation_join_exact_intervals_and_constant(self):
        a=frame(['2025-01-01','2025-01-02','2025-01-03','2025-01-04'],[100.,110.,132.,118.8])
        b=frame(['2025-01-01','2025-01-03','2025-01-04'],[10.,20.,18.])
        result=rolling_correlations({'a':a,'b':b},as_of=date(2025,1,4),window=2)
        # EndJan3 intervalJan1-Jan3 cannot match Jan2-Jan3.
        self.assertEqual(len(result['pairs'][0]['observations']),1)
        self.assertEqual(result['pairs'][0]['observations'][0]['matched_interval_count'],1)
        self.assertIsNone(result['pairs'][0]['observations'][0]['correlation'])
        result=rolling_correlations({'a':a,'b':a.copy()},as_of=date(2025,1,4),window=2,start_date=date(2025,1,3))
        self.assertEqual(len(result['pairs'][0]['observations']),2)
        self.assertAlmostEqual(result['pairs'][0]['observations'][0]['correlation'],1)
        flat=frame(pd.date_range('2025-01-01',periods=4),[10.]*4)
        result=rolling_correlations({'a':a,'flat':flat},as_of=date(2025,1,4),window=2)
        self.assertTrue(all(row['correlation'] is None for row in result['pairs'][0]['observations']))

    def test_attribution_hand_additive_and_joint_reference(self):
        p=frame(['2025-01-01','2025-01-02','2025-02-01'],[200.,999.,210.])
        fx=frame(['2025-01-01','2025-02-01'],[4.,4.2])
        result=pln_attribution(p,fx,as_of=date(2025,2,1))
        self.assertEqual(result['start_date'],'2025-01-01')
        self.assertEqual(result['end_date'],'2025-02-01')
        for key,expected in [('commodity',40),('fx',40),('interaction',2),('total',82),('commodity_pp',5),('fx_pp',5),('interaction_pp',.25),('total_pct',10.25)]:
            self.assertAlmostEqual(result[key],expected)
        self.assertEqual(result['unmatched_price_observations'],1)
        self.assertAlmostEqual(sum(result[k] for k in ['commodity','fx','interaction']),result['total'])

    def test_spread_units_exact_dates_and_scenario(self):
        a=frame(['2025-01-01','2025-01-02'],[200.,210.])
        b=frame(['2025-01-02'],[150.])
        result=spread_series(a,b,as_of=date(2025,1,2),left_unit='EUR/t',right_unit='EUR/t')
        self.assertEqual(result['values'],[60])
        self.assertEqual(result['unmatched_left_observations'],1)
        with self.assertRaises(ValueError):spread_series(a,b,as_of=date(2025,1,2),left_unit='EUR/t',right_unit='PLN/t')
        result=scenario_calculation(price=105,fx=4.08,tonnes=100,baseline_price=100,baseline_fx=4)
        self.assertAlmostEqual(result['pln_per_tonne'],428.4)
        self.assertAlmostEqual(result['change_benchmark_value_pln'],2840)
        self.assertAlmostEqual(result['change_pct'],7.1)

    def test_all_input_validation_before_future_exclusion_and_no_mutation(self):
        data=frame(['2025-01-01','2025-01-02','2025-01-03'],[1.,2.,np.inf])
        for call in [market_snapshot,market_indicators,seasonal_distribution]:
            with self.assertRaises(ValueError):call(data,as_of=date(2025,1,2))
        data.loc[2,'value']=3
        before=data.copy(deep=True)
        for call in [market_snapshot,market_indicators,seasonal_distribution]:call(data,as_of=date(2025,1,2))
        pd.testing.assert_frame_equal(data,before)
        fx=frame(['2025-01-01','2025-01-03'],[4.,0.])
        with self.assertRaises(ValueError):pln_attribution(data,fx,as_of=date(2025,1,2))
        dup=pd.concat([data,data.iloc[[2]]])
        with self.assertRaises(ValueError):market_snapshot(dup,as_of=date(2025,1,2))

    def test_finite_arithmetic_overflow_and_invalid_parameters(self):
        large=frame(['2024-12-31','2025-01-01'],[-1.7e308,1.7e308])
        with self.assertRaises(ValueError):market_snapshot(large,as_of=date(2025,1,1))
        with self.assertRaises(ValueError):market_indicators(large,as_of=date(2025,1,1))
        with self.assertRaises(ValueError):scenario_calculation(price=1.7e308,fx=4)
        small=frame(['2024-12-31','2025-01-01'],[1e-300,1e300])
        with self.assertRaises(ValueError):market_snapshot(small,as_of=date(2025,1,1))
        for window in [True,1,1.5]:
            with self.assertRaises(ValueError):rolling_correlations({'a':small},as_of=date(2025,1,1),window=window)
        with self.assertRaises(ValueError):indexed_comparison({'a':small},as_of=date(2025,1,1),start_date=date(2025,1,2))


if __name__=='__main__': unittest.main()
