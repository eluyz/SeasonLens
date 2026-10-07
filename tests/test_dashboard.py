import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import date
import pandas as pd
from seasonlens.dashboard import render_dashboard, _monthly_price_matrix
from seasonlens.app import create_server
from seasonlens.storage import SeriesMetadata, upsert_series, read_series, initialize_database


def frame(values=(100.,110.,120.),dates=('2025-01-01','2025-02-01','2026-01-01')):
    return pd.DataFrame({'date':pd.to_datetime(dates),'value':values})


class DashboardTests(unittest.TestCase):
    def test_monthly_matrix_reference_direction_cutoff_and_gaps(self):
        f=frame((999.,100.,120.,200.,155.,9999.),
                ('2016-01-01','2017-01-01','2017-01-02','2025-01-01','2026-01-10','2026-01-16'))
        matrix=_monthly_price_matrix(f,as_of=date(2026,1,15),unit='<EUR/t>')
        self.assertIn('<th scope="col">2017</th>',matrix)
        self.assertIn('<th scope="col">2026</th>',matrix)
        self.assertNotIn('<th scope="col">2016</th>',matrix)
        self.assertIn('class="price-lower" title="Monthly average lower than reference; 2 observations">110</td>',matrix)
        self.assertIn('class="price-higher" title="Monthly average higher than reference; 1 observations">200</td>',matrix)
        self.assertIn('class="price-equal"',matrix)
        self.assertIn('>155 *</td>',matrix)
        self.assertIn('<strong>155</strong>',matrix)
        self.assertIn('Observation date: 2026-01-10',matrix)
        self.assertIn('class="missing"',matrix)
        self.assertIn('&lt;EUR/t&gt;',matrix)
        self.assertNotIn('9999',matrix)
        self.assertEqual(matrix.count('<th scope="row">'),12)

    def test_monthly_matrix_no_reference_and_month_end(self):
        self.assertIn('Reference price unavailable',_monthly_price_matrix(
            frame((100.,),('2026-02-01',)),as_of=date(2026,1,31),unit='Units'))
        matrix=_monthly_price_matrix(frame((100.,),('2026-01-30',)),as_of=date(2026,1,31),unit='Units')
        self.assertNotIn('>100 *</td>',matrix)

    def test_exact_date_conversion_and_escaping(self):
        price=frame((100.,110.,120.))
        fx=frame((4.,4.5),('2025-01-01','2026-01-01'))
        html=render_dashboard({'GRAIN':dict(frame=price,title='</script><img src=x>',unit='EUR/t'),
                               'EUR_PLN':dict(frame=fx,title='FX',unit='PLN per EUR',source='ECB_REFERENCE')},as_of=date(2026,1,15))
        payload=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])
        view=payload['GRAIN']['views']['PLN/t']
        self.assertEqual([r['value'] for r in view['daily']],[400.,540.])
        self.assertIn('Unmatched price dates: 1',view['conversion_note'])
        self.assertIn('<strong>540</strong>',view['price_matrix'])
        self.assertIn('PLN/t',view['price_matrix'])
        self.assertNotIn('</script><img src=x>',html)
        self.assertEqual(payload['GRAIN']['title'],'</script><img src=x>')
        self.assertIn('Same partial-month comparison',html)
        self.assertIn('first observed positive daily value',html)

    def test_five_year_chart_and_exact_six_technical_columns(self):
        f=frame((999.,100.,120.,200.),('2021-01-01','2022-01-01','2022-01-02','2026-01-01'))
        html=render_dashboard({'S':dict(frame=f)},as_of=date(2026,1,15))
        v=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])['S']['views']['Original']
        self.assertEqual(set(v['daily'][0]),{'date','value','sma20','sma100','sma200','bollinger_upper','bollinger_lower'})
        self.assertEqual(v['fiveyear'].count('<path data-year-line='),6)
        self.assertIn('2022–2026',v['fiveyear'])
        self.assertIn('<td>155</td>',v['fiveyear'])
        self.assertNotIn('<td>999</td>',v['fiveyear'])
        self.assertIn('black dashed period average',html)
        self.assertIn('already SMA20',html)

    def test_calendar_twelve_months_and_indicator_warmup(self):
        f=pd.DataFrame({'date':pd.bdate_range('2022-01-01','2024-02-29'),'value':100.})
        html=render_dashboard({'S':dict(frame=f)},as_of=date(2024,2,29))
        v=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])['S']['views']['Original']
        self.assertEqual(v['range_starts']['12m'],'2023-02-28')
        first=next(r for r in v['daily'] if r['date']>=v['range_starts']['12m'])
        self.assertEqual(first['sma200'],100.)
        self.assertEqual(first['bollinger_upper'],100.)
        self.assertEqual(first['bollinger_lower'],100.)
        self.assertIsNotNone(v['axes']['12m:63'])

    def test_conversion_requires_explicit_quote_metadata(self):
        html=render_dashboard({'GRAIN':dict(frame=frame(),unit='EUR/t'),
                               'EUR_PLN':dict(frame=frame(),unit='EUR per PLN',source='Unrelated')},as_of=date(2026,1,15))
        payload=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])
        self.assertNotIn('PLN/t',payload['GRAIN']['views'])
        self.assertIn('conversion requires',payload['GRAIN']['views']['Original']['conversion_note'])

    def test_daily_axis_keeps_narrow_values_distinct(self):
        html=render_dashboard({'S':dict(frame=frame((4.3,4.300000000000001),('2025-01-01','2025-02-01')))},as_of=date(2026,1,15))
        payload=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])
        labels=payload['S']['views']['Original']['axes']['all:1'][3]
        self.assertEqual(len(set(labels)),5)
        self.assertTrue(all(float(v) < float('inf') for v in labels))

    def test_missing_months_do_not_depend_on_future_rows(self):
        def missing(f):
            html=render_dashboard({'S':dict(frame=f)},as_of=date(2026,10,7))
            return json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])['S']['views']['Original']['missing_months']
        self.assertEqual(missing(frame((100.,),('2025-01-01',))),21)
        self.assertEqual(missing(frame((100.,999.),('2025-01-01','2027-01-01'))),21)

    def test_empty_database_import_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'empty.sqlite';initialize_database(db)
            server=create_server(db,as_of=date(2026,1,15),port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                html=urlopen(f'http://127.0.0.1:{server.server_port}',timeout=5).read()
                self.assertIn(b'Import a local CSV',html)
                self.assertIn(b'No series imported yet',html)
                self.assertIn(b'application/json">{}',html)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)

    def test_future_exclusion_and_missing_returns(self):
        html=render_dashboard({'S':dict(frame=frame((100.,120.,999.),('2025-01-01','2025-03-01','2026-12-01')))},as_of=date(2026,1,15))
        payload=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])
        v=payload['S']['views']['Original']
        self.assertEqual(v['future_excluded'],1)
        self.assertNotIn(999,[r['value'] for r in v['daily']])
        self.assertNotIn('20%',v['heatmap'])
        self.assertIn('—',v['heatmap'])

    def test_local_import_roundtrip_and_bad_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'data.sqlite'
            metadata=SeriesMetadata('S','Synthetic','Units','Invented','Daily synthetic','Original private provenance')
            upsert_series(db,metadata,frame())
            server=create_server(db,as_of=date(2026,1,15),port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                self.assertIn(b'Explorer v6',urlopen(base,timeout=5).read())
                body=dict(series_id='S',title='Synthetic',unit='Units',source='Invented',semantics='Daily synthetic',
                          csv='date,value\n2026-01-02,130\n',date_column='date',value_column='value',
                          date_format='%Y-%m-%d',delimiter=',',decimal='.',instrument_column='',instrument_filter='',skip_missing=False,skip_rows='0')
                def request(origin):
                    return Request(base+'/import',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-SeasonLens':'local-import','Origin':origin})
                with self.assertRaises(HTTPError) as exc:urlopen(request('https://example.com'),timeout=5)
                self.assertEqual(exc.exception.code,403)
                self.assertTrue(json.load(urlopen(request(base),timeout=5))['ok'])
                self.assertEqual(list(read_series(db,'S').value),[100.,110.,120.,130.])
                body['series_id']='EUR_PLN'
                with self.assertRaises(HTTPError) as exc:urlopen(request(base),timeout=5)
                self.assertIn(b'reserved',exc.exception.read())
                body['series_id']='S'
                body['csv']='date,value\n2026-01-02,bad\n'
                with self.assertRaises(HTTPError):urlopen(request(base),timeout=5)
                self.assertEqual(list(read_series(db,'S').value),[100.,110.,120.,130.])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':unittest.main()
