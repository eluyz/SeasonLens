"""Completed-year monthly changes and block uncertainty, using invented quotes."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ENGINE = Path(__file__).parents[1] / 'src/seasonlens/seasonal_stats.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for seasonal-statistics checks')
class SeasonalStatisticsTests(unittest.TestCase):
    def node(self, rows, options=None, expression='api.analyze(input.rows,input.options)'):
        script = "const api=require(process.argv[1]);const input=JSON.parse(require('fs').readFileSync(0,'utf8'));try{const value=(" + expression + ");process.stdout.write(JSON.stringify({ok:true,value}));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}"
        result = subprocess.run(['node', '-e', script, str(ENGINE)],
                                input=json.dumps(dict(rows=rows, options=self.options() if options is None else options)),
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def options(self, **kwargs):
        result = dict(asOf='2026-10-06', windowYears=5, bootstrapReplicates=1000, seed=20261008)
        result.update(kwargs)
        return result

    def analyze(self, rows, **kwargs):
        result = self.node(rows, self.options(**kwargs))
        self.assertTrue(result['ok'], result)
        return result['value']

    def january_rows(self, changes, first=2021):
        rows = []
        for index, change in enumerate(changes):
            year = first + index
            rows.extend([dict(date=f'{year-1:04d}-12-31', value=100),
                         dict(date=f'{year:04d}-01-31', value=100+change)])
        return rows

    def test_hand_equal_year_statistics_and_leave_one_out(self):
        rows = self.january_rows([10, 20, 0, -10, 30])
        # Additional daily prices must not give a year more weight or replace its close.
        rows.extend([dict(date='2021-01-01', value=900), dict(date='2021-01-15', value=800)])
        result = self.analyze(rows)
        january = result['months'][0]
        self.assertAlmostEqual(january['mean'], 10)
        self.assertAlmostEqual(january['median'], 10)
        self.assertEqual(january['yearCount'], 5)
        self.assertEqual(january['positiveCount'], 3)
        self.assertEqual(january['positiveFraction'], .6)
        self.assertAlmostEqual(january['minimum'], -10)
        self.assertAlmostEqual(january['maximum'], 30)
        # Means after omitting each year are 10,7.5,12.5,15,5.
        self.assertAlmostEqual(january['leaveOneOutMinimum'], 5)
        self.assertAlmostEqual(january['leaveOneOutMaximum'], 15)
        self.assertAlmostEqual(january['earlyMean'], 15)
        self.assertAlmostEqual(january['lateMean'], 20/3)
        self.assertEqual((january['earlyCount'], january['lateCount']), (2, 3))
        self.assertIsNone(january['bootstrapLow'])
        self.assertIn('8 contributing', january['bootstrapReason'])
        self.assertEqual((result['startYear'], result['endYear'], result['yearCount'], result['splitYear']),
                         (2021, 2025, 5, 2022))

    def test_immediate_previous_calendar_month_and_actual_nonpositive_close(self):
        rows = [dict(date='2020-12-31', value=100), dict(date='2021-01-31', value=110),
                dict(date='2021-03-31', value=121),  # February is absent: March must be missing.
                dict(date='2021-04-10', value=130), dict(date='2021-04-30', value=0),
                dict(date='2021-05-31', value=140), dict(date='2021-06-30', value=-1),
                dict(date='2021-07-31', value=150)]
        result = self.analyze(rows)
        values = result['yearly'][0]['returns']
        self.assertAlmostEqual(values[0], 10)
        self.assertEqual(values[1:7], [None]*6)
        self.assertEqual(result['omissions']['missingPreviousMonth'], 1)
        self.assertEqual(result['omissions']['nonpositiveMonthEndpoints'], 4)
        self.assertTrue(all(result['months'][index]['mean'] is None for index in range(1, 7)))

    def test_preceding_december_establishes_first_january(self):
        result = self.analyze([dict(date='2020-12-31', value=80), dict(date='2021-01-31', value=100)])
        self.assertEqual(result['yearly'][0]['returns'][0], 25)
        self.assertEqual(result['months'][0]['yearCount'], 1)
        self.assertIsNone(result['months'][0]['leaveOneOutMinimum'])
        without_december = self.analyze([dict(date='2021-01-31', value=100)])
        self.assertIsNone(without_december['months'][0]['mean'])

    def test_current_calendar_year_excluded_even_when_month_completed(self):
        rows = self.january_rows([10, 20, 0, -10, 30])
        baseline = self.analyze(rows)
        extra = [dict(date='2026-01-31', value=1e100), dict(date='2026-05-31', value=1e-100),
                 dict(date='2026-12-31', value=0)]
        current = self.analyze(rows+extra)
        self.assertEqual(current['months'], baseline['months'])
        self.assertEqual(current['yearly'], baseline['yearly'])
        self.assertEqual(current['omissions']['currentYearRows'], 2)
        self.assertEqual(current['omissions']['futureRows'], 1)

    def test_gaps_do_not_move_calendar_split_or_declared_window(self):
        result = self.analyze(self.january_rows([20, 40], first=2024))
        january = result['months'][0]
        self.assertEqual([year['year'] for year in result['yearly']], list(range(2021, 2026)))
        self.assertEqual(result['earlyYears'], dict(startYear=2021, endYear=2022))
        self.assertEqual(result['lateYears'], dict(startYear=2023, endYear=2025))
        self.assertEqual(january['earlyCount'], 0)
        self.assertIsNone(january['earlyMean'])
        self.assertEqual(january['lateCount'], 2)
        self.assertAlmostEqual(january['lateMean'], 30)
        self.assertAlmostEqual(january['leaveOneOutMinimum'], 20)
        self.assertAlmostEqual(january['leaveOneOutMaximum'], 40)

    def test_empty_cutoff_visible_and_zero_contributors_are_missing(self):
        for rows in [[], [dict(date='2027-01-01', value=3)]]:
            result = self.analyze(rows)
            self.assertEqual(len(result['yearly']), 5)
            self.assertEqual(result['omissions']['missingMonthClose'], 60)
            for month in result['months']:
                self.assertEqual(month['yearCount'], 0)
                self.assertEqual(month['positiveCount'], 0)
                self.assertIsNone(month['positiveFraction'])
                self.assertIsNone(month['mean'])
                self.assertIsNone(month['median'])
                self.assertIsNone(month['leaveOneOutMinimum'])
                self.assertIsNone(month['bootstrapLow'])
        result = self.analyze([], windowYears='all')
        self.assertEqual(result['yearCount'], 0)
        self.assertEqual(result['yearly'], [])

    def test_all_window_is_calendar_bounded_not_number_of_observed_years(self):
        rows = [dict(date='1926-01-31', value=10), dict(date='2025-12-31', value=10)]
        result = self.analyze(rows, windowYears='all')
        self.assertEqual((result['startYear'], result['endYear'], result['yearCount']), (1926, 2025, 100))
        rows[0]['date'] = '1925-01-31'
        rejected = self.node(rows, self.options(windowYears='all'))
        self.assertFalse(rejected['ok'])
        self.assertIn('100 declared', rejected['error'])

    def test_windows_starting_before_calendar_year_one_reject_explicitly(self):
        for window, cutoff in [(5, '0005-12-31'), (10, '0010-12-31')]:
            result = self.node([], self.options(windowYears=window, asOf=cutoff))
            self.assertFalse(result['ok'])
            self.assertIn('year 1', result['error'])
        result = self.analyze([], asOf='0006-01-01')
        self.assertEqual((result['startYear'], result['endYear'], result['yearCount']), (1, 5, 5))
        result = self.analyze([dict(date='0001-01-31', value=10)], asOf='0002-01-01', windowYears='all')
        self.assertEqual(result['yearCount'], 1)
        self.assertIsNone(result['months'][0]['mean'])

    def test_bootstrap_constant_returns_have_constant_hand_interval(self):
        result = self.analyze(self.january_rows([25]*10, first=2016), windowYears=10)
        january = result['months'][0]
        self.assertEqual(january['yearCount'], 10)
        self.assertEqual(january['bootstrapValidReplicates'], 1000)
        self.assertIsNone(january['bootstrapReason'])
        self.assertEqual(january['bootstrapLow'], 25)
        self.assertEqual(january['bootstrapHigh'], 25)
        self.assertEqual(result['bootstrap']['blockLength'], 2)
        self.assertIn('not a future-price interval', result['bootstrap']['interpretation'])

    def test_seeded_contiguous_non_circular_vector_blocks_hand_draw(self):
        rows = self.january_rows(list(range(10)), first=2016)
        for index in range(10):
            rows.append(dict(date=f'{2016+index}-02-28', value=(100+index)*(1+2*index/100)))
        result = self.analyze(rows, windowYears=10, seed=1, bootstrapReplicates=1)
        # Seed1 selects two-year starts5,0,4,8,8 on the declared vector0..9.
        # The sampled years are5,6,0,1,4,5,8,9,8,9: average5.5. It never wraps9->0.
        january, february = result['months'][:2]
        self.assertAlmostEqual(january['bootstrapLow'], 5.5)
        self.assertAlmostEqual(january['bootstrapHigh'], 5.5)
        # Every February is twice January. Resampling the SAME whole-year blocks preserves it.
        self.assertAlmostEqual(february['bootstrapLow'], 11)
        self.assertAlmostEqual(february['bootstrapHigh'], 11)

    def test_bootstrap_is_reproducible_and_seed_sensitive(self):
        rows = self.january_rows(list(range(10)), first=2016)
        first = self.analyze(rows, windowYears=10, bootstrapReplicates=50, seed=1)
        again = self.analyze(rows, windowYears=10, bootstrapReplicates=50, seed=1)
        different = self.analyze(rows, windowYears=10, bootstrapReplicates=50, seed=2)
        self.assertEqual(first, again)
        self.assertNotEqual(first['months'][0]['bootstrapLow'], different['months'][0]['bootstrapLow'])

    def test_bootstrap_requires_eight_actual_yearly_contributors(self):
        for count in [7, 8]:
            result = self.analyze(self.january_rows([25]*count, first=2016), windowYears=10)
            january = result['months'][0]
            self.assertEqual(january['yearCount'], count)
            if count < 8:
                self.assertIsNone(january['bootstrapLow'])
                self.assertEqual(january['bootstrapValidReplicates'], 0)
            else:
                self.assertEqual(january['bootstrapLow'], 25)
                self.assertEqual(january['bootstrapValidReplicates'], 1000)
                self.assertIsNone(january['bootstrapReason'])

    def test_missing_year_vector_is_retained_and_invalid_replicates_suppress_interval(self):
        # Declared 1900..1999 contains eight January changes in1901..1908.
        rows = self.january_rows([25]*8, first=1901)+[dict(date='1999-12-31', value=100)]
        result = self.analyze(rows, asOf='2000-01-01', windowYears='all', seed=54, bootstrapReplicates=1)
        january = result['months'][0]
        self.assertEqual(result['yearCount'], 100)
        self.assertEqual(january['yearCount'], 8)
        # This seed's50 block starts all exceed8: missing years must not be discarded/resampled.
        self.assertEqual(january['bootstrapValidReplicates'], 0)
        self.assertIsNone(january['bootstrapLow'])
        self.assertIsNone(january['bootstrapHigh'])
        self.assertIn('90%', january['bootstrapReason'])

    def test_poisoned_future_and_duplicate_rows_reject_before_cutoff(self):
        rows = self.january_rows([10])
        for future in [dict(date='2027-01-01', value='bad'), dict(date='2027-02-30', value=3),
                       dict(date='2027-01-01', value=True), dict(date='2027-01-01', value=1e101),
                       dict(date='2027-01-01', value=1e-101)]:
            with self.subTest(future=future):
                self.assertFalse(self.node(rows+[future])['ok'])
        self.assertFalse(self.node(rows+[dict(date='2027-01-01', value=3)]*2)['ok'])
        self.assertFalse(self.node(rows+[dict(date='2027-01-01', value=3)],
                                   expression='(()=>{input.rows.at(-1).value=NaN;return api.analyze(input.rows,input.options)})()')['ok'])

    def test_input_is_immutable_and_sorting_independent(self):
        rows = list(reversed(self.january_rows([10, 20, 0, -10, 30])))
        result = self.node(rows, expression='(()=>{const before=JSON.stringify(input.rows);input.rows.forEach(Object.freeze);Object.freeze(input.rows);const value=api.analyze(input.rows,input.options);return {unchanged:before===JSON.stringify(input.rows),value}})()')
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['value']['unchanged'])
        self.assertEqual(result['value']['value'], self.analyze(rows))

    def test_supported_numeric_endpoints_remain_finite(self):
        result = self.analyze([dict(date='2020-12-31', value=1e-100), dict(date='2021-01-31', value=1e100)])
        self.assertAlmostEqual(result['months'][0]['mean']/1e202, 1)
        self.assertIsNone(result['months'][0]['leaveOneOutMinimum'])

    def test_invalid_options_and_dates_are_explicit(self):
        for kwargs in [dict(windowYears=7), dict(windowYears=True), dict(windowYears='5'),
                       dict(bootstrapReplicates=0), dict(bootstrapReplicates=2001),
                       dict(bootstrapReplicates=1.5), dict(bootstrapReplicates=True),
                       dict(seed=-1), dict(seed=4294967296), dict(seed=True),
                       dict(asOf='2026-02-30'), dict(asOf='today')]:
            with self.subTest(kwargs=kwargs):
                self.assertFalse(self.node([], self.options(**kwargs))['ok'])
        self.assertFalse(self.node([], {})['ok'])


if __name__ == '__main__':
    unittest.main()
