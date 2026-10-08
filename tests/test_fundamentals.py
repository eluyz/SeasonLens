"""Independent, invented balance and publication-vintage hand fixtures."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
ENGINE = ROOT / 'src/seasonlens/fundamentals.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for fundamental checks')
class FundamentalTests(unittest.TestCase):
    def row(self, **values):
        result = dict(publication_date='2025-06-12', commodity='wheat',
                      region='Invented region', marketing_year='2025/26',
                      unit='million metric tonnes', ending_stocks=25, total_use=100)
        result.update(values)
        return result

    def options(self, **values):
        result = dict(asOf='2025-09-12', commodity='wheat', region='Invented region')
        result.update(values)
        return result

    def node(self, rows=None, options=None, expression='api.analyze(input.rows,input.options)', **extra):
        script = ("const api=require(process.argv[1]);const input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                  "try{const value=(" + expression + ");process.stdout.write(JSON.stringify({ok:true,value}));}"
                  "catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}")
        data = dict(rows=rows if rows is not None else [self.row()], options=options or self.options(), **extra)
        result = subprocess.run(['node', '-e', script, str(ENGINE)], input=json.dumps(data),
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def analyze(self, rows=None, **options):
        result = self.node(rows, self.options(**options))
        self.assertTrue(result['ok'], result)
        return result['value']

    def csv(self, rows=None):
        records = [self.row()] if rows is None else rows
        header = ['publication_date', 'commodity', 'region', 'marketing_year', 'unit', 'ending_stocks', 'total_use']
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header, lineterminator='\r\n')
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()

    def parse(self, csv_text):
        return self.node(expression='api.parseCSV(input.csv)', csv=csv_text)

    def test_ratio_and_same_year_revisions_hand_example(self):
        rows = [self.row(publication_date='2025-09-12', ending_stocks=24, total_use=102), self.row()]
        value = self.analyze(rows)
        self.assertEqual(value['source'], 'USER_FILE')
        self.assertEqual(value['previous']['stocks_to_use_percent'], 25)
        self.assertAlmostEqual(value['latest']['stocks_to_use_percent'], 400/17)
        self.assertAlmostEqual(value['latest']['stocks_to_use_change_pp'], -25/17)
        self.assertEqual(value['latest']['ending_stocks_change'], -1)
        self.assertEqual(value['latest']['total_use_change'], 2)
        self.assertEqual(value['latest']['previous_publication_date'], '2025-06-12')
        self.assertIsNone(value['previous']['stocks_to_use_change_pp'])

    def test_cutoff_inclusive_and_future_revision_never_leaks(self):
        rows = [self.row(), self.row(publication_date='2025-09-12', ending_stocks=24, total_use=102),
                self.row(publication_date='2025-10-09', ending_stocks=90)]
        early = self.analyze(rows, asOf='2025-09-11')
        self.assertEqual(early['latest']['ending_stocks'], 25)
        self.assertIsNone(early['previous'])
        exact = self.analyze(rows)
        self.assertEqual(exact['latest']['ending_stocks'], 24)
        self.assertEqual(exact['counts'], dict(input=3, visible=2, after_cutoff=1, matching=2, selected=2))
        self.assertEqual(exact['latest']['publication_date'], '2025-09-12')

    def test_no_publication_is_explicit_missing_even_before_first_release(self):
        result = self.analyze(asOf='2025-01-01')
        self.assertFalse(result['available'])
        self.assertIsNone(result['latest'])
        self.assertIsNone(result['selection']['marketing_year'])
        self.assertEqual(result['marketing_years'], [])
        self.assertIsNotNone(result['reason'])

    def test_new_marketing_year_has_separate_revision_sequence(self):
        rows = [self.row(), self.row(publication_date='2025-09-12', marketing_year='2026/27', ending_stocks=9),
                self.row(publication_date='2026-10-09', marketing_year='2027/28', ending_stocks=80)]
        latest = self.analyze(rows)
        self.assertEqual(latest['selection']['marketing_year'], '2026/27')
        self.assertIsNone(latest['previous'])
        self.assertIsNone(latest['latest']['ending_stocks_change'])
        selected = self.analyze(rows, marketingYear='2025/26')
        self.assertEqual(selected['latest']['ending_stocks'], 25)
        missing = self.analyze(rows, marketingYear='2027/28')
        self.assertFalse(missing['available'])
        self.assertEqual(missing['marketing_years'], ['2025/26', '2026/27'])

    def test_commodity_and_geography_selection_never_aggregate(self):
        rows = [self.row(), self.row(commodity='corn', ending_stocks=80),
                self.row(region='Other invented region', ending_stocks=90)]
        result = self.analyze(rows)
        self.assertEqual(result['counts']['matching'], 1)
        self.assertEqual(result['latest']['stocks_to_use_percent'], 25)
        self.assertFalse(self.analyze(rows, region='invented region')['available'])

    def test_bad_future_rows_and_duplicates_reject_before_cutoff(self):
        changes = [dict(ending_stocks=-1), dict(total_use=0), dict(total_use=True),
                   dict(ending_stocks='25'), dict(publication_date='2026-02-30'),
                   dict(marketing_year='2025/27'), dict(unit='tonnes'),
                   dict(region=' Invented region'), dict(commodity='oilseeds'),
                   dict(total_use=1e-101), dict(ending_stocks=1e101)]
        for changeset in changes:
            future = self.row(publication_date='2026-10-09', **{key: value for key, value in changeset.items() if key != 'publication_date'})
            if 'publication_date' in changeset:
                future['publication_date'] = changeset['publication_date']
            with self.subTest(changes=changeset):
                self.assertFalse(self.node([self.row(), future])['ok'])
        future = self.row(publication_date='2026-10-09')
        self.assertFalse(self.node([self.row(), future, dict(future)])['ok'])
        for value in ['NaN', 'Infinity', '-Infinity']:
            expr = f'(()=>{{input.rows[1].total_use={value};return api.analyze(input.rows,input.options)}})()'
            self.assertFalse(self.node([self.row(), future], expression=expr)['ok'])

    def test_unit_mismatch_even_in_future_revision_rejects(self):
        result = self.node([self.row(), self.row(publication_date='2026-10-09', unit='metric tonnes')])
        self.assertFalse(result['ok'])
        self.assertIn('units differ', result['error'])
        # A different year is its own balance; its revisions are not compared.
        self.assertTrue(self.node([self.row(), self.row(marketing_year='2026/27', unit='metric tonnes')])['ok'])

    def test_zero_stocks_and_supported_numeric_boundaries(self):
        zero = self.analyze([self.row(ending_stocks=0)])
        self.assertEqual(zero['latest']['stocks_to_use_percent'], 0)
        tiny = self.analyze([self.row(ending_stocks=1e-100, total_use=1e-100)])
        self.assertEqual(tiny['latest']['stocks_to_use_percent'], 100)
        large = self.analyze([self.row(ending_stocks=1e100, total_use=1e100)])
        self.assertEqual(large['latest']['stocks_to_use_percent'], 100)

    def test_input_unchanged_independent_results(self):
        rows = [self.row(publication_date='2025-09-12'), self.row()]
        expression = '''(()=>{const before=JSON.stringify(input.rows);
            input.rows.forEach(Object.freeze);Object.freeze(input.rows);
            const result=api.analyze(input.rows,input.options);
            result.revisions[0].ending_stocks=999;
            return {unchanged:before===JSON.stringify(input.rows),first:input.rows[0].publication_date,
                    value:input.rows[1].ending_stocks};})()'''
        value = self.node(rows, expression=expression)['value']
        self.assertEqual(value, dict(unchanged=True, first='2025-09-12', value=25))

    def test_csv_bom_quotes_exponents_and_public_fixture(self):
        quoted = self.csv([self.row(region='Invented, "region"')])
        result = self.parse('\ufeff'+quoted.replace(',25,100', ',2.5e1,1e2'))
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value'][0]['region'], 'Invented, "region"')
        self.assertEqual(result['value'][0]['ending_stocks'], 25)
        fixture = (ROOT/'examples/data/synthetic_fundamentals.csv').read_text()
        parsed = self.parse(fixture)
        self.assertTrue(parsed['ok'], parsed)
        self.assertEqual(len(parsed['value']), 15)
        demo = self.node(expression='api.validateRows(api.demoRows())')['value']
        self.assertEqual(parsed['value'], demo)
        self.assertTrue(all(row['region'] == 'Invented region' for row in demo))

    def test_csv_ambiguous_source_headers_and_structural_errors_reject(self):
        csv = self.csv()
        invalid = [csv.replace('publication_date', 'release_date'), csv.replace('total_use\r\n', 'total_use,source\r\n'),
                   csv.replace('publication_date,commodity', 'commodity,publication_date'),
                   csv.replace(',25,100', ',,100'), csv.replace(',25,100', ',25,NaN'),
                   csv+'\r\n', csv.replace('Invented region', '"Invented region'),
                   csv.replace('Invented region', '"Invented region"x'),
                   csv.replace(',25,100', ',"1,000",100')]
        for text in invalid:
            with self.subTest(csv=text):
                self.assertFalse(self.parse(text)['ok'])

    def test_source_and_complete_record_contract(self):
        self.assertEqual(self.analyze(source='SYNTHETIC')['source'], 'SYNTHETIC')
        for source in ['USDA', 'MATIF', '', None, True]:
            self.assertFalse(self.node(options=self.options(source=source))['ok'])
        extra = self.row(source='USDA')
        self.assertFalse(self.node([extra])['ok'])
        missing = self.row()
        del missing['unit']
        self.assertFalse(self.node([missing])['ok'])
        self.assertFalse(self.node([])['ok'])
        self.assertFalse(self.node(options=self.options(asOf='2026-02-30'))['ok'])
        self.assertFalse(self.node(options=self.options(marketingYear='2025'))['ok'])


if __name__ == '__main__':
    unittest.main()
