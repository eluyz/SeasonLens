"""The downloadable workbook must round-trip through the real strict importer."""
import base64
from datetime import date
from pathlib import Path
import shutil
import subprocess
import unittest
from seasonlens.dashboard import render_empty_dashboard

ROOT = Path(__file__).parents[1]


class ImportTemplateTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for XLSX checks')
    def test_workbook_rows_dates_units_and_cross_rate(self):
        source = r'''
const assert=require('node:assert/strict'),fs=require('node:fs');
global.XLSX=require('./src/seasonlens/vendor/xlsx.mini.min.js');
require('./src/seasonlens/workbook_import.js');
const bytes=Buffer.from(fs.readFileSync('./src/seasonlens/import_template.xlsx.b64','utf8').trim(),'base64');
const w=SeasonLensWorkbook.readWorkbook(bytes);
assert.deepEqual(w.SheetNames,['Prices','Read me']);
const roles=['wheat','corn','rapeseed','eur_pln','eur_usd','usd_pln'];
const units=['EUR/t','EUR/t','EUR/t','PLN per EUR','USD per EUR','PLN per USD'];
const options={headerRow:1,startRow:4,dateColumn:'A',asOf:'2026-10-08',decimal:'.',dateFormat:'ISO',skipBlankRows:false,allowCachedFormulas:false,mappings:roles.map((role,i)=>({column:'BCDEFG'[i],title:role,unit:units[i],role}))};
const v=SeasonLensWorkbook.validateSheet(w,'Prices',options);
assert.equal(v.series.length,6);assert.equal(v.summary.cachedFormulaCells,0);
for(const s of v.series){assert.equal(s.records.length,210);assert.equal(s.records[0].date,'2025-12-17');assert.equal(s.records.at(-1).date,'2026-10-06');assert.deepEqual(s.skippedFutureRows,[]);assert.deepEqual(s.skippedBlankRows,[]);assert(!s.records.some(r=>r.date==='2026-10-07'));}
for(let i=0;i<210;i++)assert.equal(v.series[5].records[i].value,v.series[3].records[i].value/v.series[4].records[i].value);
const earlier=SeasonLensWorkbook.validateSheet(w,'Prices',{...options,asOf:'2026-10-05'});
assert(earlier.series.every(s=>s.records.length===209&&s.skippedFutureRows.length===1));
console.log('PASS: six invented template series, physical live-row exclusion and exact cross-rate');
'''
        run = subprocess.run(['node', '-e', source], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node required for download checks')
    def test_download_exact_bytes_without_observation_access(self):
        source = r'''
const assert=require('node:assert/strict'),fs=require('node:fs');let blob,clicked=0,removed=0,revoked=0;
global.Blob=class{constructor(parts,options){blob={parts,options}}};global.URL={createObjectURL:()=> 'blob:template',revokeObjectURL:()=>revoked++};
global.document={body:{append(){}},createElement:()=>({click(){clicked++;assert.equal(this.download,'seasonlens-import-template.xlsx')},remove(){removed++}})};
global.setTimeout=fn=>fn();
const api=require('./src/seasonlens/template_download.js'),encoded=fs.readFileSync('./src/seasonlens/import_template.xlsx.b64','utf8').trim();
assert.equal(clicked,0);api.download(encoded);
assert.equal(clicked,1);assert.equal(removed,1);assert.equal(revoked,1);assert.equal(blob.options.type,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
assert.deepEqual(Buffer.from(blob.parts[0]),Buffer.from(encoded,'base64'));
for(const input of ['',null,'<script>','AAAA'])assert.throws(()=>api.download(input));
assert.equal(clicked,1);
'''
        run = subprocess.run(['node', '-e', source], cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_empty_dashboard_has_complete_guide_and_invented_asset(self):
        html = render_empty_dashboard(as_of=date(2026, 10, 6))
        self.assertIn('id="seasonlens-start"', html)
        self.assertIn('initSeasonLensStartGuide({downloadTemplate:', html)
        encoded = (ROOT / 'src/seasonlens/import_template.xlsx.b64').read_text().strip()
        self.assertTrue(base64.b64decode(encoded, validate=True).startswith(b'PK\x03\x04'))
        self.assertIn(encoded, html)
        self.assertNotIn('@@START_', html)
        self.assertNotIn('@@IMPORT_TEMPLATE_', html)


if __name__ == '__main__':
    unittest.main()
