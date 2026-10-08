"""Hand-calculated XLSX import fixtures; all data are invented."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
ENGINE = ROOT / 'src/seasonlens/workbook_import.js'
VENDOR = ROOT / 'src/seasonlens/vendor/xlsx.mini.min.js'


@unittest.skipUnless(shutil.which('node'), 'Node is required for XLSX checks')
class WorkbookImportTests(unittest.TestCase):
    def node(self, expression, payload=None):
        script = "globalThis.XLSX=require(process.argv[1]);require(process.argv[2]);const api=globalThis.SeasonLensWorkbook;const input=JSON.parse(require('fs').readFileSync(0,'utf8'));try{const value=("+expression+");process.stdout.write(JSON.stringify({ok:true,value}));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));}"
        result = subprocess.run(['node', '-e', script, str(VENDOR), str(ENGINE)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def workbook(self, rows=None, *, epoch=False, cells=None, ref='A1:C6'):
        sheet = {'!ref': ref, 'A1': {'t': 's', 'v': 'Date'}, 'B1': {'t': 's', 'v': 'Wheat'}, 'C1': {'t': 's', 'v': 'EUR/PLN'}, 'A3': {'t': 's', 'v': 'LIVE: deliberately invalid'}, 'B3': {'t': 'e', 'v': 42}}
        for i, row in enumerate(rows or [('2026-10-01', 200, 4), ('2026-10-02', 210, 4.2), ('2026-10-07', 999, 5)], 4):
            for col, value in zip('ABC', row):
                if value is not None:
                    sheet[col+str(i)] = {'t': 'n' if isinstance(value, (int, float)) else 's', 'v': value}
        if cells:
            sheet.update(cells)
        return dict(SheetNames=['Prices'], Sheets={'Prices': sheet}, Workbook={'WBProps': {'date1904': epoch}})

    def options(self, **kw):
        result = dict(headerRow=1, startRow=4, dateColumn='A', mappings=[dict(column='B', title='Wheat', unit='EUR/t', role='wheat'), dict(column='C', title='EUR/PLN', unit='PLN per EUR', role='eur_pln')], asOf='2026-10-06', decimal='.', dateFormat='ISO', skipBlankRows=False, allowCachedFormulas=False)
        result.update(kw)
        return result

    def validate(self, workbook=None, **kw):
        return self.node('api.validateSheet(input.workbook,"Prices",input.options)', dict(workbook=workbook or self.workbook(), options=self.options(**kw)))

    def test_master_physical_rows_skip_live_and_sort_independently(self):
        result = self.validate(self.workbook([('2026-10-02', 210, None), ('2026-10-01', 200, 4), ('2026-10-07', 999, 5)]), skipBlankRows=True)
        self.assertTrue(result['ok'], result)
        wheat, fx = result['value']['series']
        self.assertEqual(wheat['records'], [dict(date='2026-10-01', value=200), dict(date='2026-10-02', value=210)])
        self.assertEqual(fx['records'], [dict(date='2026-10-01', value=4)])
        self.assertEqual(fx['skippedBlankRows'], [4])
        self.assertEqual(wheat['skippedFutureRows'], [6])
        self.assertEqual(result['value']['summary']['selectedRows'], 3)

    def test_preview_plain_strings_and_formula_markers(self):
        workbook = self.workbook(cells={'B1': {'t': 's', 'v': '<img onerror=x>'}, 'B4': {'t': 'n', 'v': 200, 'f': '1+199'}})
        result = self.node('api.inspectSheet(input,"Prices",{headerRow:1,startRow:4})', workbook)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['columns'][1]['header'], '<img onerror=x>')
        self.assertTrue(result['value']['preview'][3]['cells'][1]['formula'])
        self.assertEqual(result['value']['formulaCells'], 1)

    def test_blank_policy_and_atomic_invalid_second_series(self):
        self.assertFalse(self.validate(self.workbook(cells={'C5': {'t': 's', 'v': 'broken'}}))['ok'])
        self.assertFalse(self.validate(self.workbook(cells={'B5': {'t': 'z'}}))['ok'])
        result = self.validate(self.workbook(cells={'B5': {'t': 'z'}}), skipBlankRows=True)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['series'][0]['skippedBlankRows'], [5])

    def test_invalid_and_duplicate_future_rows_cannot_be_hidden(self):
        for cells in [{'B6': {'t': 's', 'v': 'nope'}}, {'A6': {'t': 's', 'v': '2026-02-30'}}, {'A6': {'t': 's', 'v': '2026-10-01'}, 'B6': {'t': 'z'}}]:
            with self.subTest(cells=cells):
                self.assertFalse(self.validate(self.workbook(cells=cells), skipBlankRows=True)['ok'])

    def test_nonpositive_future_retains_positive_only_restriction(self):
        result = self.validate(self.workbook(cells={'B6': {'t': 'n', 'v': -10}}))
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['value']['series'][0]['originalAllPositive'])
        self.assertEqual(result['value']['series'][0]['skippedFutureRows'], [6])
        for value in [0, -1]:
            self.assertFalse(self.validate(self.workbook(cells={'C6': {'t': 'n', 'v': value}}))['ok'])

    def test_cached_formulas_require_explicit_consent_and_never_execute(self):
        workbook = self.workbook(cells={'B4': {'t': 'n', 'v': 123, 'f': '999*999'}, 'A4': {'t': 's', 'v': '2026-10-01', 'f': 'TODAY()'}})
        self.assertFalse(self.validate(workbook)['ok'])
        result = self.validate(workbook, allowCachedFormulas=True)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['series'][0]['records'][0]['value'], 123)
        self.assertEqual(result['value']['summary']['cachedFormulaCells'], 2)
        for cell in [{'t': 'n', 'f': '1+2'}, {'t': 'e', 'v': 15, 'f': '1/0'}]:
            self.assertFalse(self.validate(self.workbook(cells={'B4': cell}), allowCachedFormulas=True)['ok'])

    def test_excel_1900_and_1904_dates_hand_reference(self):
        old = self.validate(self.workbook([(1, 1, 1), (59, 2, 2), (61, 3, 3)]))
        self.assertTrue(old['ok'], old)
        self.assertEqual([r['date'] for r in old['value']['series'][0]['records']], ['1900-01-01', '1900-02-28', '1900-03-01'])
        new = self.validate(self.workbook([(0, 1, 1), (1, 2, 2), (60, 3, 3)], epoch=True))
        self.assertTrue(new['ok'], new)
        self.assertEqual([r['date'] for r in new['value']['series'][0]['records']], ['1904-01-01', '1904-01-02', '1904-03-01'])
        for serial in [60, 1.5, -1, 3000000]:
            self.assertFalse(self.validate(self.workbook(cells={'A4': {'t': 'n', 'v': serial}}))['ok'])

    def test_explicit_text_date_and_decimal_formats(self):
        workbook = self.workbook([('29.02.2024', '4,123', 4), ('01.03.2024', '4,200', 4.2), ('02.03.2024', '4,300', 4.3)])
        self.assertFalse(self.validate(workbook)['ok'])
        result = self.validate(workbook, dateFormat='DD.MM.YYYY', decimal=',')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['series'][0]['records'][0], dict(date='2024-02-29', value=4.123))
        self.assertFalse(self.validate(workbook, dateFormat='DD.MM.YYYY', decimal='.')['ok'])

    def test_typed_date_cells_reject_times_without_timezone_guessing(self):
        expression = "(()=>{input.workbook.Sheets.Prices.A4={t:'d',v:new Date(input.date)};return api.validateSheet(input.workbook,'Prices',input.options)})()"
        payload = dict(workbook=self.workbook(), options=self.options(), date='2024-02-29T00:00:00.000Z')
        result = self.node(expression, payload)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['series'][0]['records'][0]['date'], '2024-02-29')
        for date in ['2024-02-29T00:00:00.001Z', '2024-02-29T12:00:00.000Z', 'bad']:
            payload['date'] = date
            self.assertFalse(self.node(expression, payload)['ok'])

    def test_booleans_errors_and_numeric_range_reject(self):
        for cell in [{'t': 'b', 'v': True}, {'t': 'e', 'v': 7}, {'t': 's', 'v': 'NaN'}, {'t': 's', 'v': '1e101'}, {'t': 's', 'v': '1e-101'}, {'t': 's', 'v': '1 000'}]:
            with self.subTest(cell=cell):
                self.assertFalse(self.validate(self.workbook(cells={'C6': cell}))['ok'])
        self.assertTrue(self.validate(self.workbook(cells={'B4': {'t': 'n', 'v': 0}}))['ok'])

    def test_only_empty_trailing_rows_ignored_visibly(self):
        workbook = self.workbook(ref='A1:C8')
        result = self.validate(workbook)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['summary']['ignoredTrailingRows'], 2)
        self.assertFalse(self.validate(self.workbook(cells={'A5': {'t': 'z'}, 'B5': {'t': 'z'}, 'C5': {'t': 'z'}}), skipBlankRows=True)['ok'])

    def test_metadata_columns_roles_and_cutoff_validation(self):
        for options in [dict(startRow=1), dict(dateColumn='B'), dict(asOf='0001-01-01'), dict(mappings=[dict(column='B', title='Wrong', unit='USD/t', role='wheat')]), dict(mappings=[dict(column='B', title='Duplicate', unit='EUR/t', role='wheat'), dict(column='C', title='Other', unit='EUR/t', role='wheat')]), dict(mappings=[dict(column='B', title='Duplicate', unit='EUR/t', role='custom'), dict(column='C', title='Duplicate', unit='PLN per EUR', role='custom')])]:
            with self.subTest(options=options):
                self.assertFalse(self.validate(**options)['ok'])

    def test_limits_and_empty_result(self):
        self.assertFalse(self.validate(self.workbook(ref='A1:C20005'))['ok'])
        self.assertFalse(self.validate(self.workbook(ref='A1:ZZ6'))['ok'])
        self.assertFalse(self.validate(asOf='2020-01-01')['ok'])

    def test_real_xlsx_roundtrip_preserves_serial_epoch_and_cached_formula(self):
        expression = "(()=>{const bytes=XLSX.write(input.workbook,{type:'array',bookType:'xlsx',compression:true});const parsed=api.readWorkbook(bytes);return {meta:parsed.SeasonLensMeta,result:api.validateSheet(parsed,'Prices',input.options)}})()"
        workbook = self.workbook([(0, 200, 4), (1, 210, 4.2), (60, 220, 4.3)], epoch=True, cells={'B4': {'t': 'n', 'v': 200, 'f': '100+100'}})
        result = self.node(expression, dict(workbook=workbook, options=self.options(allowCachedFormulas=True)))
        self.assertTrue(result['ok'], result)
        self.assertGreater(result['value']['meta']['archiveFiles'], 0)
        self.assertEqual(result['value']['result']['series'][0]['records'][0], dict(date='1904-01-01', value=200))

    def test_nonzip_encrypted_and_macro_archives_reject(self):
        self.assertFalse(self.node('api.readWorkbook(new Uint8Array([1,2,3]))')['ok'])
        base = "const bytes=new Uint8Array(XLSX.write(input,{type:'array',bookType:'xlsx',compression:true}));"
        expression = "(()=>{"+base+"bytes[6]|=1;return api.readWorkbook(bytes)})()"
        self.assertFalse(self.node(expression, self.workbook())['ok'])
        expression = "(()=>{const w={...input,vbaraw:new Uint8Array([1,2])};return api.readWorkbook(XLSX.write(w,{type:'array',bookType:'xlsm',compression:true}))})()"
        self.assertFalse(self.node(expression, self.workbook())['ok'])
        expression = "api.readWorkbook(XLSX.write(input,{type:'array',bookType:'xlsm',compression:true}))"
        self.assertFalse(self.node(expression, self.workbook())['ok'])

    def test_declared_zip_bomb_rejected_before_parser(self):
        expression = "(()=>{const b=new Uint8Array(XLSX.write(input,{type:'array',bookType:'xlsx'}));const v=new DataView(b.buffer);for(let i=0;i<b.length-46;i++){if(v.getUint32(i,true)===0x02014b50){v.setUint32(i+24,65*1024*1024,true);v.setUint32(v.getUint32(i+42,true)+22,65*1024*1024,true);break}}return api.readWorkbook(b)})()"
        result = self.node(expression, self.workbook())
        self.assertFalse(result['ok'])
        self.assertIn('64 MiB', result['error'])

    def test_forged_local_allocation_size_rejected_before_reader(self):
        expression = "(()=>{const b=new Uint8Array(XLSX.write(input,{type:'array',bookType:'xlsx'}));const v=new DataView(b.buffer);v.setUint32(22,256*1024*1024,true);let called=false;XLSX.read=()=>{called=true;throw Error('reader must not run')};try{api.readWorkbook(b)}catch(e){return {called,error:e.message}}return {called,error:null}})()"
        result = self.node(expression, self.workbook())
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['value']['called'])
        self.assertIn('local and central sizes', result['value']['error'])

    def test_zip64_extra_size_override_rejected_before_reader(self):
        # Insert a zero-length ZIP64 extra field in the first central entry and
        # adjust the directory size; no oversized allocation is needed.
        expression = "(()=>{const original=new Uint8Array(XLSX.write(input,{type:'array',bookType:'xlsx'}));const ov=new DataView(original.buffer);let p=0;while(p<original.length-46&&ov.getUint32(p,true)!==0x02014b50)p++;const at=p+46+ov.getUint16(p+28,true),b=new Uint8Array(original.length+4);b.set(original.subarray(0,at));b.set([1,0,0,0],at);b.set(original.subarray(at),at+4);const v=new DataView(b.buffer);v.setUint16(p+30,ov.getUint16(p+30,true)+4,true);const end=b.length-22;v.setUint32(end+12,v.getUint32(end+12,true)+4,true);let called=false;XLSX.read=()=>{called=true;throw Error('reader must not run')};try{api.readWorkbook(b)}catch(e){return {called,error:e.message}}return {called,error:null}})()"
        result = self.node(expression, self.workbook())
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['value']['called'])
        self.assertIn('ZIP64', result['value']['error'])

    def test_descriptor_zero_hints_normalized_without_mutating_input(self):
        expression = """(()=>{
          const original=new Uint8Array(XLSX.write(input.workbook,{type:'array',bookType:'xlsx',compression:true}));
          const ov=new DataView(original.buffer);let first=0;
          while(first<original.length-46&&ov.getUint32(first,true)!==0x02014b50)first++;
          const local=ov.getUint32(first+42,true),packed=ov.getUint32(first+20,true),unpacked=ov.getUint32(first+24,true);
          const at=local+30+ov.getUint16(local+26,true)+ov.getUint16(local+28,true)+packed;
          const b=new Uint8Array(original.length+16);b.set(original.subarray(0,at));b.set(original.subarray(at),at+16);
          const v=new DataView(b.buffer);v.setUint32(at,0x08074b50,true);v.setUint32(at+4,ov.getUint32(first+16,true),true);v.setUint32(at+8,packed,true);v.setUint32(at+12,unpacked,true);
          for(let p=first+16;p<b.length-46;){
            if(v.getUint32(p,true)!==0x02014b50)break;
            const location=v.getUint32(p+42,true);if(location>=at)v.setUint32(p+42,location+16,true);
            p+=46+v.getUint16(p+28,true)+v.getUint16(p+30,true)+v.getUint16(p+32,true);
          }
          const end=b.length-22;v.setUint32(end+16,v.getUint32(end+16,true)+16,true);
          v.setUint16(first+16+8,v.getUint16(first+16+8,true)|8,true);v.setUint16(local+6,v.getUint16(local+6,true)|8,true);
          v.setUint32(local+18,0,true);v.setUint32(local+22,0,true);
          const originalRead=XLSX.read;let received=null;
          XLSX.read=(data,opts)=>{const dv=new DataView(data.buffer,data.byteOffset,data.byteLength);received={packed:dv.getUint32(local+18,true),unpacked:dv.getUint32(local+22,true),copied:data.buffer!==b.buffer};return originalRead(data,opts)};
          const w=api.readWorkbook(b);
          return {received,expected:{packed,unpacked,copied:true},inputUnchanged:v.getUint32(local+18,true)===0&&v.getUint32(local+22,true)===0,result:api.validateSheet(w,'Prices',input.options)};
        })()"""
        result = self.node(expression, dict(workbook=self.workbook(), options=self.options()))
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['value']['received'], result['value']['expected'])
        self.assertTrue(result['value']['inputUnchanged'])
        self.assertEqual(result['value']['result']['series'][0]['records'][0]['value'], 200)

    def test_zero_deflate_allocation_hint_is_explicitly_unsupported(self):
        expression = "(()=>{const b=new Uint8Array(XLSX.write(input,{type:'array',bookType:'xlsx',compression:true}));const v=new DataView(b.buffer);let p=0;while(p<b.length-46&&v.getUint32(p,true)!==0x02014b50)p++;const local=v.getUint32(p+42,true);v.setUint32(p+24,0,true);v.setUint32(local+22,0,true);let called=false;XLSX.read=()=>{called=true;throw Error('reader must not run')};try{api.readWorkbook(b)}catch(e){return {called,error:e.message}}return {called,error:null}})()"
        result = self.node(expression, self.workbook())
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['value']['called'])
        self.assertIn('Zero-length deflated', result['value']['error'])


if __name__ == '__main__':
    unittest.main()
