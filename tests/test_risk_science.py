"""Independent hand fixtures for descriptive risk, FX Euler shares and helpers."""
import datetime
import json
import math
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
ENGINE = ROOT / 'src/seasonlens/risk_analysis.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for scientific risk checks')
class RiskScienceTests(unittest.TestCase):
    def node(self, payload=None, expression='R.historicalRisk(input.rows,input.options)'):
        script = "const R=require(process.argv[1]);const C=require(process.argv[2]);const input=JSON.parse(require('fs').readFileSync(0,'utf8'));try{const value=(" + expression + ");process.stdout.write(JSON.stringify({ok:true,value}));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}"
        result = subprocess.run(['node', '-e', script, str(ENGINE), str(ENGINE.with_name('science_common.js'))],
                                input=json.dumps(payload or {}), text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def rows(self, values):
        return [dict(date=(datetime.date(2020, 1, 1)+datetime.timedelta(days=i)).isoformat(), value=value)
                for i, value in enumerate(values)]

    def change_rows(self, changes, log=False):
        values = [100.]
        for change in changes:
            values.append(values[-1]*(math.exp(change/100) if log else 1+change/100))
        return self.rows(values)

    def options(self, **kwargs):
        result = dict(asOf='2025-01-01', horizon=1, confidence=.95, direction='buyer')
        result.update(kwargs)
        return result

    def risk(self, rows, **kwargs):
        result = self.node(dict(rows=rows, options=self.options(**kwargs)))
        self.assertTrue(result['ok'], result)
        return result['value']

    def fx(self, commodity, currency, asOf='2025-01-01'):
        result = self.node(dict(commodity=commodity, currency=currency, asOf=asOf),
                           'R.fxRisk(input.commodity,input.currency,{asOf:input.asOf})')
        self.assertTrue(result['ok'], result)
        return result['value']

    def test_integer_and_fractional_empirical_tail_hand_calculations(self):
        for changes, var, es in [(range(100), 94, 97), (range(101), 95, 97.97029702970298)]:
            with self.subTest(n=len(changes)):
                result = self.risk(self.change_rows(changes))
                self.assertTrue(result['available'])
                self.assertAlmostEqual(result['var'], var)
                self.assertAlmostEqual(result['expectedShortfall'], es)
                self.assertEqual(result['counts']['validIntervals'], len(changes))

    def test_ties_include_fractional_tail_mass_instead_of_strict_exceedances(self):
        result = self.risk(self.change_rows([0]*99+[100]))
        self.assertEqual(result['var'], 0)
        self.assertEqual(result['expectedShortfall'], 20)
        self.assertEqual(result['tailMass'], 5)
        # All zero losses still have a five-observation ES of zero.
        zero = self.risk(self.rows([100]*101))
        self.assertEqual((zero['var'], zero['expectedShortfall']), (0, 0))

    def test_exact_required_sample_thresholds(self):
        for confidence, minimum in [(.95, 100), (.99, 500)]:
            for n in [minimum-1, minimum]:
                with self.subTest(confidence=confidence, n=n):
                    result = self.risk(self.rows([100]*(n+1)), confidence=confidence)
                    self.assertEqual(result['available'], n == minimum)
                    self.assertEqual(result['tailMass'], n/(20 if confidence == .95 else 100))
                    if n == minimum:
                        self.assertEqual((result['var'], result['expectedShortfall']), (0, 0))
                    else:
                        self.assertIsNone(result['var'])
                        self.assertIsNone(result['expectedShortfall'])
                        self.assertIn(str(minimum), result['unavailableReason'])

    def test_direction_and_negative_losses_are_not_clamped(self):
        rows = self.change_rows([1]*100)
        buyer, seller = self.risk(rows), self.risk(rows, direction='seller')
        self.assertAlmostEqual(buyer['expectedShortfall'], 1)
        self.assertAlmostEqual(seller['expectedShortfall'], -1)
        self.assertAlmostEqual(seller['var'], -1)
        self.assertEqual(buyer['histogram'], seller['histogram'])
        self.assertAlmostEqual(seller['meanChange'], 1)

    def test_observed_horizons_gaps_and_nonpositive_endpoint_omissions(self):
        rows = self.rows([100, 0, 102, 103, 104, 105, 106])
        rows[-1]['date'] = '2021-06-01'
        result = self.risk(rows, horizon=5)
        self.assertEqual(result['counts']['candidateIntervals'], 2)
        self.assertEqual(result['counts']['validIntervals'], 1)
        self.assertEqual(result['counts']['nonpositiveEndpoints'], 1)
        self.assertTrue(result['overlapping'])
        self.assertAlmostEqual(result['intervals'][0]['change'], 5)
        self.assertEqual(result['intervals'][0]['observedIntervals'], 5)
        one = self.risk(rows)
        self.assertEqual(one['counts']['nonpositiveEndpoints'], 2)
        self.assertEqual(one['intervals'][-1]['end'], '2021-06-01')

    def test_future_rows_excluded_but_invalid_future_rows_reject(self):
        rows = self.rows([100]*101)
        base = self.risk(rows, asOf='2020-05-01')
        future = dict(date='2021-01-01', value=1e100)
        after = self.risk(rows+[future], asOf='2020-05-01')
        self.assertEqual(after['counts']['excludedFuture'], 1)
        after['counts']['excludedFuture'] = 0
        self.assertEqual(base, after)
        for value in [True, '123', None, 1e101, 1e-101]:
            self.assertFalse(self.node(dict(rows=rows+[dict(date='2021-01-01', value=value)], options=self.options()))['ok'])
        self.assertFalse(self.node(dict(rows=rows+[future, future], options=self.options()))['ok'])
        self.assertFalse(self.node(dict(rows=rows+[dict(date='2021-02-29', value=1)], options=self.options()))['ok'])

    def test_empty_cutoff_is_missing_and_input_is_immutable(self):
        rows = list(reversed(self.rows([100, 101, 99])))
        result = self.node(dict(rows=rows, options=self.options()),
                           '(()=>{const before=JSON.stringify(input.rows);input.rows.forEach(Object.freeze);Object.freeze(input.rows);const result=R.historicalRisk(input.rows,input.options);return {unchanged:before===JSON.stringify(input.rows),result}})()')
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['value']['unchanged'])
        self.assertEqual(result['value']['result'], self.risk(list(reversed(rows))))
        empty = self.risk(rows, asOf='2019-12-31')
        self.assertIsNone(empty['meanChange'])
        self.assertIsNone(empty['medianChange'])
        self.assertEqual(empty['histogram'], [])
        self.assertEqual(empty['counts']['excludedFuture'], 3)

    def test_stress_paths_break_at_nonpositive_levels_and_keep_dates(self):
        rows = self.rows([100, 120, 60, 90, 0, 10, 25])
        result = self.node(dict(rows=rows, options=self.options()), 'R.stressEpisodes(input.rows,input.options)')
        self.assertTrue(result['ok'], result)
        value = result['value']
        self.assertEqual(value['nonpositivePathBreaks'], 1)
        self.assertEqual(value['maxDecline'], dict(start='2020-01-02', end='2020-01-03', observedIntervals=1, change=-50))
        self.assertEqual(value['maxRise'], dict(start='2020-01-06', end='2020-01-07', observedIntervals=1, change=150))
        self.assertEqual(value['largestFalls'][0]['change'], -50)
        self.assertEqual(value['largestRises'][0]['change'], 150)

    def test_histogram_and_median_preserve_all_interval_counts(self):
        result = self.risk(self.change_rows([0, 10, 20, 30]))
        self.assertAlmostEqual(result['meanChange'], 15)
        self.assertAlmostEqual(result['medianChange'], 15)
        self.assertEqual(sum(row['count'] for row in result['histogram']), 4)
        self.assertEqual(result['histogram'][0]['lower'], 0)
        self.assertAlmostEqual(result['histogram'][-1]['upper'], 30)

    def test_fx_hand_sample_variance_and_negative_euler_shares(self):
        result = self.fx(self.change_rows([1, 2, 3], log=True), self.change_rows([-.5, -1, -1.5], log=True))
        for name, expected in dict(varCommodity=1, varFX=.25, covariance=-.5,
                                   totalVar=.25, commodityContribution=.5, fxContribution=-.25,
                                   commodityShare=200, fxShare=-100).items():
            self.assertAlmostEqual(result[name], expected)
        self.assertTrue(result['sharesAvailable'])
        self.assertEqual(result['counts']['pairedIntervals'], 3)

    def test_fx_constant_combined_path_does_not_report_roundoff_shares(self):
        result = self.fx(self.change_rows([1, 2, 3], log=True), self.change_rows([-2, -3, -4], log=True))
        self.assertTrue(result['available'])
        self.assertLess(result['totalVar'], 1e-24)
        self.assertFalse(result['sharesAvailable'])
        self.assertIsNone(result['commodityShare'])
        self.assertIsNone(result['fxShare'])
        self.assertIn('resolution', result['unavailableReason'])
        zero = self.fx(self.rows([100]*4), self.rows([4]*4))
        self.assertEqual(zero['totalVar'], 0)
        self.assertIsNone(zero['commodityShare'])
        self.assertIn('constant', zero['unavailableReason'])

    def test_fx_genuine_near_cancellation_keeps_stable_euler_contributions(self):
        result = self.fx(self.change_rows([1, 2, 3], log=True),
                         self.change_rows([-1.0000000001, -2.0000000002, -3.0000000003], log=True))
        self.assertTrue(result['sharesAvailable'])
        self.assertAlmostEqual(result['totalVar']/1e-20, 1, delta=.001)
        self.assertAlmostEqual(result['commodityContribution']/-1e-10, 1, delta=.001)
        self.assertAlmostEqual(result['fxContribution']/1e-10, 1, delta=.001)
        self.assertAlmostEqual((result['commodityContribution']+result['fxContribution'])/result['totalVar'], 1, delta=.0001)
        self.assertLess(result['commodityShare'], -1e11)
        self.assertGreater(result['fxShare'], 1e11)

    def test_fx_matches_original_intervals_not_inner_joined_grid(self):
        commodity = [dict(date='2020-01-0'+str(day), value=value) for day, value in [(1, 100), (2, 110), (4, 121), (5, 130)]]
        currency = [dict(date='2020-01-0'+str(day), value=value) for day, value in [(1, 4), (3, 4.1), (4, 4.2), (5, 4.3)]]
        result = self.fx(commodity, currency)
        self.assertEqual(result['counts']['pairedIntervals'], 1)
        self.assertEqual([(row['start'], row['end']) for row in result['intervals']], [('2020-01-04', '2020-01-05')])
        self.assertFalse(result['available'])
        self.assertIsNone(result['varCommodity'])
        self.assertIsNone(result['commodityShare'])

    def test_fx_invalid_future_validation_and_nonpositive_omissions(self):
        rows = self.rows([100, 0, 101, 102])
        result = self.fx(rows, self.rows([4, 4.1, 4.2, 4.3]))
        self.assertEqual(result['counts']['commodityNonpositiveEndpoints'], 2)
        self.assertEqual(result['counts']['pairedIntervals'], 1)
        future = self.rows([4, 4.1, 4.2, 4.3])+[dict(date='2026-01-01', value='bad')]
        self.assertFalse(self.node(dict(commodity=rows, currency=future),
                                   "R.fxRisk(input.commodity,input.currency,{asOf:'2020-01-04'})")['ok'])

    def test_common_sample_covariance_has_sample_not_population_denominator(self):
        result = self.node(expression='({v:C.sampleCovariance([1,2,3],[1,2,3]),c:C.sampleCovariance([1,2,3],[-.5,-1,-1.5]),constant:C.sampleCovariance([7,7],[1,3]),missing:C.sampleCovariance([1],[2])})')
        self.assertEqual(result['value'], dict(v=1, c=-.5, constant=0, missing=None))

    def test_common_statistics_scale_safely_or_reject_explicit_overflow(self):
        result = self.node(expression='({mean:C.mean([1e308,1e308]),cancel:C.mean([1e308,-1e308]),q:C.quantile([-1e308,1e308],.5),cov:C.sampleCovariance([-1e100,1e100],[-1e100,1e100])})')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['mean'], 1e308)
        self.assertEqual(result['value']['cancel'], 0)
        self.assertEqual(result['value']['q'], 0)
        self.assertAlmostEqual(result['value']['cov']/1e200, 2)
        overflow = self.node(expression='C.sampleCovariance([-1e200,1e200],[-1e200,1e200])')
        self.assertFalse(overflow['ok'])
        self.assertIn('finite numeric range', overflow['error'])

    def test_common_real_types_dates_and_month_shifts(self):
        for expression in ['C.mean([true])', 'C.quantile([1],true)', 'C.sampleCovariance([1],[1,2])',
                           "C.validateRows([{date:'2024-02-30',value:1}],'2024-02-29')",
                           "C.validateRows([{date:'0000-01-01',value:1}],'2024-02-29')",
                           "C.monthShift('0001-01-01',-1)", "C.monthShift('9999-12-01',1)"]:
            self.assertFalse(self.node(expression=expression)['ok'], expression)
        result = self.node(expression="[C.monthShift('2024-03-31',-1),C.monthShift('2023-03-31',-1),C.mean([]),C.quantile([],0.5)]")
        self.assertEqual(result['value'], ['2024-02-29','2023-02-28',None,None])

    def test_risk_options_reject_unsupported_parameters(self):
        for kwargs in [dict(horizon=2), dict(horizon=True), dict(confidence=.9), dict(direction='unknown'), dict(asOf='2024-02-30')]:
            self.assertFalse(self.node(dict(rows=self.rows([1,2]), options=self.options(**kwargs)))['ok'])

    def test_risk_extreme_valid_prices_remain_finite(self):
        result = self.risk(self.rows([1e-100,1e100]*51))
        self.assertTrue(result['available'])
        self.assertTrue(math.isfinite(result['expectedShortfall']))
        self.assertTrue(math.isfinite(result['meanChange']))
        self.assertEqual(sum(bin['count'] for bin in result['histogram']), 101)
        fx = self.fx(self.rows([1e-100,1e100,1e-100]), self.rows([1e100,1e-100,1e100]))
        self.assertIsNone(fx['commodityShare'])
        self.assertLess(fx['totalVar'], 1e-15)


if __name__ == '__main__':
    unittest.main()
