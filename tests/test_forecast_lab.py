"""Hand-calculated observed-step forecast fixtures. Every quote is invented."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
ENGINE = ROOT / 'src/seasonlens/forecast_lab.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for forecast checks')
class ForecastLabTests(unittest.TestCase):
    def node(self, rows, options=None, expression='api.evaluate(input.rows,input.options)'):
        script = "const api=require(process.argv[1]);const input=JSON.parse(require('fs').readFileSync(0,'utf8'));try{const value=(" + expression + ");process.stdout.write(JSON.stringify({ok:true,value}));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}"
        result = subprocess.run(['node', '-e', script, str(ENGINE)], input=json.dumps(dict(rows=rows, options=options or self.options())), text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def rows(self, values=None):
        return [dict(date=(datetime.date(2020, 1, 1)+datetime.timedelta(days=index)).isoformat(), value=value)
                for index, value in enumerate(values if values is not None else range(1, 26))]

    def options(self, **kwargs):
        result = dict(asOf='2020-01-25', horizons=[1, 5, 20], minTraining=20, maxOrigins=252)
        result.update(kwargs)
        return result

    def evaluate(self, rows=None, **kwargs):
        result = self.node(self.rows() if rows is None else rows, self.options(**kwargs))
        self.assertTrue(result['ok'], result)
        return result['value']

    def test_linear_hand_fixture_errors_and_bounds(self):
        result = self.evaluate()
        one, five, twenty = result['horizons']
        self.assertEqual(one['count'], 5)
        self.assertEqual(one['firstOriginDate'], '2020-01-20')
        self.assertEqual(one['lastOriginDate'], '2020-01-24')
        self.assertEqual(one['firstTargetDate'], '2020-01-21')
        self.assertEqual(one['lastTargetDate'], '2020-01-25')
        # Quotes 1..20 have average 10.5. At the first origin the target is
        # 21: last-price error1, drift error0, trailing-mean error10.5.
        self.assertEqual(one['rows'][0]['predictions'], dict(naive=20, drift=21, mean20=10.5))
        for metric in ['mae', 'rmse']:
            for model, expected in zip(one['models'], [1, 0, 10.5]):
                self.assertAlmostEqual(model[metric], expected)
        for model, expected in zip(one['models'], [0, 1, -9.5]):
            self.assertAlmostEqual(model['maeSkill'], expected)
        self.assertEqual(five['count'], 1)
        self.assertEqual(five['rows'][0]['predictions'], dict(naive=20, drift=25, mean20=10.5))
        for model, expected in zip(five['models'], [5, 0, 14.5]):
            self.assertAlmostEqual(model['mae'], expected)
        self.assertEqual(twenty['count'], 0)
        self.assertIsNotNone(twenty['reason'])
        self.assertTrue(all(model['mae'] is None for model in twenty['models']))

    def test_mae_and_rmse_are_different_hand_results(self):
        result = self.evaluate(self.rows([10]*20+[14, 8, 15]), horizons=[1])['horizons'][0]
        baseline = result['models'][0]
        self.assertEqual(baseline['count'], 3)
        self.assertAlmostEqual(baseline['mae'], 17/3)
        self.assertAlmostEqual(baseline['rmse'], (101/3)**0.5)
        mean20 = result['models'][2]
        self.assertAlmostEqual(mean20['mae'], (4+2.2+4.9)/3)
        self.assertAlmostEqual(mean20['rmse'], ((4**2+2.2**2+4.9**2)/3)**0.5)

    def test_future_training_shock_cannot_change_earlier_predictions(self):
        before = self.evaluate(horizons=[5])['horizons'][0]
        changed = self.rows()
        for row in changed[20:]:
            row['value'] = 10000
        after = self.evaluate(changed, horizons=[5])['horizons'][0]
        self.assertEqual(before['rows'][0]['predictions'], after['rows'][0]['predictions'])
        self.assertNotEqual(before['rows'][0]['actual'], after['rows'][0]['actual'])
        self.assertNotEqual(before['models'][0]['mae'], after['models'][0]['mae'])

    def test_valid_future_rows_have_no_influence_on_outputs(self):
        before = self.evaluate()
        after = self.evaluate(self.rows()+[dict(date='2020-02-01', value=1e100)])
        self.assertEqual(before, after)

    def test_poisoned_future_and_duplicate_inputs_reject_before_cutoff(self):
        for future in [dict(date='2020-02-01', value='bad'), dict(date='2020-02-30', value=3),
                       dict(date='2020-02-01', value=True), dict(date='2020-02-01', value=1e101),
                       dict(date='2020-02-01', value=1e-101)]:
            with self.subTest(future=future):
                self.assertFalse(self.node(self.rows()+[future])['ok'])
        rows = self.rows()+[dict(date='2020-02-01', value=3)]*2
        self.assertFalse(self.node(rows)['ok'])
        self.assertFalse(self.node(self.rows()+[dict(date='2020-02-01', value=3)],
                                   expression='(()=>{input.rows.at(-1).value=NaN;return api.evaluate(input.rows,input.options)})()')['ok'])

    def test_cutoff_target_strictly_later_and_no_guessed_calendar_steps(self):
        rows = self.rows()
        # A five-observation forecast may span a gap in the calendar.
        rows[-1]['date'] = '2020-03-01'
        before = self.evaluate(rows, horizons=[5], asOf='2020-02-29')['horizons'][0]
        after = self.evaluate(rows, horizons=[5], asOf='2020-03-01')['horizons'][0]
        self.assertEqual(before['count'], 0)
        self.assertEqual(after['count'], 1)
        self.assertEqual(after['rows'][0]['targetDate'], '2020-03-01')
        self.assertEqual(after['rows'][0]['originDate'], '2020-01-20')

    def test_selected_period_retains_expanding_and_mean_warmup(self):
        result = self.evaluate(startDate='2020-01-23', horizons=[1])['horizons'][0]
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['firstOriginDate'], '2020-01-23')
        for model, expected in dict(naive=23, drift=24, mean20=13.5).items():
            self.assertAlmostEqual(result['rows'][0]['predictions'][model], expected)
        self.assertAlmostEqual(result['models'][2]['mae'], 10.5)
        # Recutting the input to the visible period would have no warmup.
        self.assertEqual(self.evaluate(self.rows()[22:], startDate='2020-01-23', horizons=[1])['horizons'][0]['count'], 0)

    def test_nonlinear_drift_retains_first_history_quote_before_selected_period(self):
        # At Jan22 the expanding history starts at quote1, ends at quote12,
        # and spans21 intervals. Its drift is therefore 11/21; the trailing
        # twenty quotes contain eighteen10s followed by11 and12.
        result = self.evaluate(self.rows([1]+[10]*19+[11, 12, 13]),
                               startDate='2020-01-22', horizons=[1])['horizons'][0]
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['firstOriginDate'], '2020-01-22')
        self.assertEqual(result['firstTargetDate'], '2020-01-23')
        predictions = result['rows'][0]['predictions']
        self.assertEqual(predictions['naive'], 12)
        self.assertAlmostEqual(predictions['drift'], 12+11/21)
        self.assertAlmostEqual(predictions['mean20'], 10.15)
        for metric in ['mae', 'rmse']:
            for model, expected in zip(result['models'], [1, 10/21, 2.85]):
                self.assertAlmostEqual(model[metric], expected)

    def test_twenty_step_target_uses_identical_origin_for_all_models(self):
        rows = self.rows(range(1, 46))
        result = self.evaluate(rows, asOf=rows[-1]['date'], startDate='2020-01-23',
                               horizons=[20])['horizons'][0]
        self.assertEqual(result['count'], 3)
        self.assertEqual(result['firstOriginDate'], '2020-01-23')
        self.assertEqual(result['lastOriginDate'], '2020-01-25')
        self.assertEqual(result['firstTargetDate'], '2020-02-12')
        self.assertEqual(result['lastTargetDate'], '2020-02-14')
        first = result['rows'][0]
        self.assertEqual(first['actual'], 43)
        for model, expected in dict(naive=23, drift=43, mean20=13.5).items():
            self.assertAlmostEqual(first['predictions'][model], expected)
        for metric in ['mae', 'rmse']:
            for model, expected in zip(result['models'], [20, 0, 29.5]):
                self.assertAlmostEqual(model[metric], expected)

    def test_latest_origin_limit_is_explicit_and_identical_across_models(self):
        result = self.evaluate(maxOrigins=2)['horizons'][0]
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['eligibleOriginCount'], 5)
        self.assertEqual(result['limitedOriginCount'], 3)
        self.assertEqual(result['firstOriginDate'], '2020-01-23')
        self.assertEqual(result['lastOriginDate'], '2020-01-24')
        self.assertEqual([model['count'] for model in result['models']], [2, 2, 2])

    def test_constant_perfect_baseline_skill_is_undefined(self):
        result = self.evaluate(self.rows([7]*25))['horizons'][0]
        self.assertTrue(all(model['mae'] == model['rmse'] == 0 for model in result['models']))
        self.assertTrue(all(model['maeSkill'] is None and model['rmseSkill'] is None for model in result['models']))

    def test_zero_and_negative_levels_are_valid_forecast_levels(self):
        result = self.evaluate(self.rows(range(-12, 13)))['horizons'][0]
        self.assertEqual([model['mae'] for model in result['models']], [1, 0, 10.5])
        self.assertEqual(result['count'], 5)

    def test_numeric_extremes_use_finite_scale_safe_rmse(self):
        for magnitude in [1e100, 1e-100]:
            with self.subTest(magnitude=magnitude):
                result = self.evaluate(self.rows([magnitude if index % 2 else -magnitude for index in range(25)]))['horizons'][0]
                self.assertEqual(result['count'], 5)
                self.assertIsNone(result['reason'])
                self.assertAlmostEqual(result['models'][0]['mae']/magnitude, 2)
                self.assertAlmostEqual(result['models'][0]['rmse']/magnitude, 2)

    def test_sorting_is_independent_and_input_is_immutable(self):
        rows = list(reversed(self.rows()))
        result = self.node(rows, expression='(()=>{const before=JSON.stringify(input.rows);input.rows.forEach(Object.freeze);Object.freeze(input.rows);const value=api.evaluate(input.rows,input.options);return {unchanged:before===JSON.stringify(input.rows),value}})()')
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['value']['unchanged'])
        self.assertEqual(result['value']['value'], self.evaluate())

    def test_default_training_and_horizons(self):
        rows = self.rows(range(250))
        result = self.node(rows, dict(asOf=rows[-1]['date']))
        self.assertTrue(result['ok'], result)
        output = result['value']
        self.assertEqual(output['minTraining'], 200)
        self.assertEqual(output['maxOrigins'], 252)
        self.assertEqual([horizon['count'] for horizon in output['horizons']], [50, 46, 31])

    def test_empty_visible_history_has_missing_metrics(self):
        for rows in [[], self.rows()]:
            result = self.evaluate(rows, asOf='2019-12-31')
            self.assertEqual(result['visibleCount'], 0)
            self.assertTrue(all(horizon['count'] == 0 and horizon['reason'] for horizon in result['horizons']))

    def test_invalid_options_and_explicit_calendar_start_date(self):
        for kwargs in [dict(horizons=[]), dict(horizons=[1, 1]), dict(horizons=[2]), dict(horizons=[True]),
                       dict(minTraining=19), dict(minTraining=True), dict(minTraining=20001),
                       dict(maxOrigins=0), dict(maxOrigins=1001), dict(maxOrigins=1.5),
                       dict(startDate='2020-02-30'), dict(startDate='2020-01-26'),
                       dict(startDate=True), dict(asOf=None)]:
            with self.subTest(kwargs=kwargs):
                self.assertFalse(self.node(self.rows(), self.options(**kwargs))['ok'])


if __name__ == '__main__':
    unittest.main()
