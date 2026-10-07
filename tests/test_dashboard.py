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
from seasonlens.dashboard import render_dashboard
from seasonlens.app import create_server
from seasonlens.storage import SeriesMetadata, upsert_series, read_series, initialize_database


def frame(values=(100.,110.,120.),dates=('2025-01-01','2025-02-01','2026-01-01')):
    return pd.DataFrame({'date':pd.to_datetime(dates),'value':values})


class DashboardTests(unittest.TestCase):
    def test_exact_date_conversion_and_escaping(self):
        price=frame((100.,110.,120.))
        fx=frame((4.,4.5),('2025-01-01','2026-01-01'))
        html=render_dashboard({'GRAIN':dict(frame=price,title='</script><img src=x>',unit='EUR/t'),
                               'EUR_PLN':dict(frame=fx,title='FX',unit='PLN per EUR',source='ECB_REFERENCE')},as_of=date(2026,1,15))
        payload=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S)[1])
        view=payload['GRAIN']['views']['PLN/t']
        self.assertEqual([r['value'] for r in view['daily']],[400.,540.])
        self.assertIn('Unmatched price dates: 1',view['conversion_note'])
        self.assertNotIn('</script><img src=x>',html)
        self.assertEqual(payload['GRAIN']['title'],'</script><img src=x>')
        self.assertIn('Same partial-month comparison',html)
        self.assertIn('first observed positive daily value',html)

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
        self.assertIn('Missing',v['heatmap'])

    def test_local_import_roundtrip_and_bad_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'data.sqlite'
            metadata=SeriesMetadata('S','Synthetic','Units','Invented','Daily synthetic','Original private provenance')
            upsert_series(db,metadata,frame())
            server=create_server(db,as_of=date(2026,1,15),port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                self.assertIn(b'Explorer v3',urlopen(base,timeout=5).read())
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
