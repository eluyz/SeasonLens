"""Hand fixtures for the tab-memory CSV engine and independent Python parity."""
from datetime import date, timedelta
import json
from pathlib import Path
import shutil
import subprocess
import unittest

import pandas as pd
from seasonlens.comparison import technical_analysis

ENGINE = Path(__file__).parents[1] / 'src/seasonlens/browser_import.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for browser-engine checks')
class BrowserCSVTests(unittest.TestCase):
    def node(self, expression, payload=None):
        script = "require(process.argv[1]);const api=globalThis.SeasonLensBrowser;const input=JSON.parse(require('fs').readFileSync(0,'utf8'));try {const value=("+expression+");process.stdout.write(JSON.stringify({ok:true,value}));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}"
        result = subprocess.run(['node', '-e', script, str(ENGINE)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def options(self, **kw):
        return dict(dateColumn='date', valueColumn='value', delimiter=',', decimal='.', skipBlankRows=False, asOf='2026-10-06', **kw)

    def parse(self, text, **kw):
        options=self.options(); options.update(kw)
        return self.node('api.parseCSV(input.text,input.options)',dict(text=text,options=options))

    def test_utf8_bom_quoted_multiline_and_sorted_rows(self):
        result=self.parse('\ufeffdate,value,note\r\n2026-10-06,120,"Line one\nLine ""two"""\r\n2026-10-01,100,ą\r\n')
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['value']['records'],[dict(date='2026-10-01',value=100),dict(date='2026-10-06',value=120)])

    def test_explicit_decimal_comma(self):
        result=self.parse('date;value\n2026-01-01;4,123\n',delimiter=';',decimal=',')
        self.assertEqual(result['value']['records'][0]['value'],4.123)

    def test_decimal_dialect_does_not_guess_thousands_or_wrong_separator(self):
        self.assertFalse(self.parse('date;value\n2026-01-01;1.234\n',delimiter=';',decimal=',')['ok'])
        self.assertTrue(self.parse('date;value\n2026-01-01;1,234\n',delimiter=';',decimal=',')['ok'])
        self.assertFalse(self.parse('date;value\n2026-01-01;1,234\n',delimiter=';',decimal='.')['ok'])

    def test_blank_and_future_physical_lines_are_disjoint(self):
        result=self.parse('date,value,note\n2026-10-01,100,"one\ntwo"\n2026-10-02,,blank\n2026-10-07,120,future\n',skipBlankRows=True)
        self.assertEqual(result['value']['skippedBlankRows'],[4])
        self.assertEqual(result['value']['skippedFutureRows'],[5])
        self.assertEqual(result['value']['totalRows'],3)

    def test_duplicate_and_malformed_future_rows_reject(self):
        for future in ['2026-10-07,nope','2026-10-07,Infinity','2026-10-07,NaN','2026-10-07,1e309','2026-10-07,100\n2026-10-07,','2026-02-30,100']:
            with self.subTest(future=future):
                self.assertFalse(self.parse('date,value\n2026-10-01,100\n'+future+'\n',skipBlankRows=True)['ok'])

    def test_zero_and_negative_future_rows_retain_full_input_positive_status(self):
        for value in ['0','-1']:
            result=self.parse('date,value\n2026-01-01,100\n2026-10-07,'+value+'\n')
            self.assertFalse(result['value']['originalAllPositive'])

    def test_parser_metadata_preserves_future_nonpositive_restriction_and_omissions(self):
        text='date,value\n2026-01-01,100\n2026-01-02,\n2026-10-07,0\n'
        result=self.node('(()=>{const p=api.parseCSV(input.text,input.options);return api.buildEntry(p.records,{...p,title:"Private CSV",unit:"Input units",asOf:input.options.asOf})})()',dict(text=text,options={**self.options(),'skipBlankRows':True}))
        self.assertTrue(result['ok'],result)
        entry=result['value'];self.assertEqual(entry['import_summary'],dict(skipped_blank_rows=[3],excluded_future_rows=[4]))
        self.assertEqual(entry['views']['Original']['future_excluded'],1)
        self.assertIn('strictly positive',entry['views']['Original']['normalized'])

    def test_strict_calendar_and_number_syntax(self):
        for row in ['0000-01-01,1','2025-02-29,1','2026-2-01,1','2026-01-01,1 000','2026-01-01,0x10','2026-01-01,1e101','2026-01-01,1e-101']:
            with self.subTest(row=row):self.assertFalse(self.parse('date,value\n'+row+'\n')['ok'])
        self.assertTrue(self.parse('date,value\n2024-02-29,1e2\n')['ok'])

    def test_blank_value_requires_explicit_skip_and_duplicates_still_reject(self):
        self.assertFalse(self.parse('date,value\n2026-01-01,1\n2026-01-02,\n')['ok'])
        self.assertFalse(self.parse('date,value\n2026-01-01,1\n2026-01-01,\n',skipBlankRows=True)['ok'])

    def test_structural_errors_and_multiseries_reject(self):
        for text in ['date,value\n2026-01-01,"1','date,value\n2026-01-01,"1"x\n','date,value\n2026-01-01,1,extra\n','date,date\n2026-01-01,1\n','instrument_id,date,value\nABC,2026-01-01,1\n']:
            with self.subTest(text=text):self.assertFalse(self.parse(text)['ok'])

    def test_limits(self):
        too_many='date,value\n'+'2026-01-01,1\n'*20001
        self.assertIn('20,000',self.parse(too_many)['error'])
        self.assertIn('12 MiB',self.parse('x'*(12*1024*1024+1))['error'])

    def test_view_hand_calculated_equal_year_mean_and_coverage(self):
        records=[dict(date='2024-01-01',value=100),dict(date='2024-01-03',value=120),dict(date='2025-01-01',value=200),dict(date='2026-01-01',value=155)]
        result=self.node('api.buildView(input,{unit:"EUR/t",asOf:"2026-01-15"})',records)
        self.assertTrue(result['ok'],result)
        view=result['value']
        # Jan 2024 mean110, Jan2025mean200, Jan2026mean155 -> equal-year155.
        self.assertIn('<td>110</td><td>200</td><td>155</td><td>155</td><td>3/5</td><td>4</td>',view['fiveyear'])
        self.assertIn('<td>155</td><td>110</td><td>200</td><td>2/5</td><td>3</td><td>155</td><td>1</td><td>0</td>',view['profiles'])
        self.assertEqual(view['missing_months'],22)
        self.assertEqual(view['age_days'],14)
        self.assertIn('price-lower',view['price_matrix'])
        self.assertIn('price-higher',view['price_matrix'])
        self.assertIn('price-equal',view['price_matrix'])

    def test_labels_are_escaped_and_source_is_fixed(self):
        result=self.node('api.buildEntry(input,{title:"<img onerror=evil>",unit:"<script>evil()</script>",asOf:"2026-01-02",source:"ECB_REFERENCE"})',[dict(date='2026-01-01',value=100)])
        self.assertTrue(result['ok'],result)
        entry=result['value'];self.assertEqual(entry['source'],'USER_FILE')
        html=''.join(entry['views']['Original'][k] for k in ['price_matrix','fiveyear','profiles','normalized','heatmap','partial'])
        self.assertNotIn('<script>',html);self.assertNotIn('<img',html)
        self.assertIn('&lt;script&gt;',html)

    def test_signed_and_zero_input_preserves_levels_with_clear_unavailable_views(self):
        records=[dict(date='2026-01-01',value=0),dict(date='2026-01-02',value=-1)]
        result=self.node('api.buildView(input,{unit:"Input units",asOf:"2026-01-02"})',records)
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['value']['daily'][0]['value'],0)
        self.assertIn('strictly positive',result['value']['normalized'])
        self.assertIn('strictly positive',result['value']['heatmap'])

    def test_python_indicator_parity_full_warmup(self):
        start=date(2025,1,1)
        records=[dict(date=(start+timedelta(days=i)).isoformat(),value=100+i*0.13+(i%7)*.3) for i in range(220)]
        result=self.node('api.indicators(input)',records)
        frame=pd.DataFrame(records);frame['date']=pd.to_datetime(frame['date'])
        reference=technical_analysis(frame,as_of=date.fromisoformat(records[-1]['date'])).frame
        self.assertTrue(result['ok'],result)
        for i, row in enumerate(result['value']):
            self.assertEqual(set(row),{'date','value','sma20','sma100','sma200','bollinger_upper','bollinger_lower'})
            for key in ['sma20','sma100','sma200','bollinger_upper','bollinger_lower']:
                expected=reference.iloc[i][key]
                if pd.isna(expected):self.assertIsNone(row[key])
                else:self.assertAlmostEqual(row[key],expected,places=11)

    def test_narrow_population_std_and_constant_axis(self):
        result=self.node('({std:api.populationStd([1e9,1e9+.001]),axis:api.axis([4.25,4.25])})')
        self.assertAlmostEqual(result['value']['std'],(1e9+.001-1e9)/2,places=12)
        self.assertGreater(result['value']['axis'][1]*result['value']['axis'][0],0)
        self.assertEqual(len(set(result['value']['axis'][3])),5)


if __name__=='__main__': unittest.main()
