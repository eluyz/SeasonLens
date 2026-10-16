/* Independent profile contracts with invented worksheet data only. */
const assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
global.XLSX=require(path.join(root,'src/seasonlens/vendor/xlsx.mini.min.js'));
require(path.join(root,'src/seasonlens/workbook_import.js'));
require(path.join(root,'src/seasonlens/import_profiles.js'));
const api=SeasonLensImportProfiles;
function workbook(value=200,header='Wheat'){return {SheetNames:['Prices'],Sheets:{Prices:XLSX.utils.aoa_to_sheet([['Date',header,'FX'],['units','EUR/t','PLN per EUR'],['LIVE',999,9],['2026-01-01',value,4]])}};}
const settings={headerRow:1,startRow:4,dateColumn:'A',mappings:[{column:'B',title:'Declared Wheat',unit:'EUR/t',role:'wheat'},{column:'C',title:'My EUR/PLN',unit:'PLN per EUR',role:'eur_pln'}],decimal:'.',dateFormat:'ISO',asOf:'2026-01-01',skipBlankRows:true,allowCachedFormulas:true,filename:'private-company.xlsx',records:[{date:'2026-01-01',value:200}]};
const profile=api.capture(workbook(),'Prices',settings),json=api.serialize(profile),copy=api.parse(json);
assert.deepEqual(copy,profile);assert.equal(profile.date.header,'Date');assert.equal(profile.mappings[1].header,'FX');
for(const omitted of ['asOf','skipBlankRows','allowCachedFormulas','filename','records','2026-01-01','private-company','200'])assert.equal(json.includes(omitted),false,omitted);
assert.deepEqual(api.checkCompatibility(workbook(765),copy),profile);
const options={headerRow:copy.headerRow,startRow:copy.startRow,dateColumn:copy.date.column,mappings:copy.mappings,decimal:copy.decimal,dateFormat:copy.dateFormat,asOf:'2026-01-01'};
assert.equal(SeasonLensWorkbook.validateSheet(workbook(765),'Prices',options).series[0].records[0].value,765);
assert.throws(()=>api.checkCompatibility(workbook(200,'Other wheat'),copy),/columns or headers have changed/);
const removed=workbook();removed.SheetNames=['Other'];assert.throws(()=>api.checkCompatibility(removed,copy),/worksheet is unavailable/);
const missing=workbook();delete missing.Sheets.Prices.C1;assert.throws(()=>api.checkCompatibility(missing,copy),/columns or headers have changed/);
const moved=workbook();moved.Sheets.Prices=XLSX.utils.aoa_to_sheet([['Date','Extra','Wheat','FX']]);assert.throws(()=>api.checkCompatibility(moved,copy),/columns or headers have changed/);
const long='x'.repeat(300),longProfile=api.capture(workbook(1,long+'tail1'),'Prices',settings);assert.throws(()=>api.checkCompatibility(workbook(1,long+'tail2'),longProfile),/columns or headers have changed/);
assert.throws(()=>api.parse('not JSON'),/not valid JSON/);assert.throws(()=>api.parse(' '.repeat(api.MAX_BYTES+1)),/64 KiB/);
assert.throws(()=>api.parse('"'+'ą'.repeat(40000)+'"'),/64 KiB/);
for(const mutate of [p=>p.version=2,p=>p.observations=[],p=>p.filename='private.xlsx',p=>p.headerRow=0,p=>p.startRow=p.headerRow,p=>p.date.column='a',p=>p.date.raw=[1,2],p=>p.mappings=[],p=>p.mappings[0].price=123,p=>p.mappings[1].column='A',p=>p.mappings[1].title=p.mappings[0].title,p=>p.mappings[1].role='wheat',p=>p.mappings[1].unit='EUR/t',p=>p.decimal=';',p=>p.dateFormat='guess',p=>p.mappings[0].role='__proto__',p=>p.mappings[0].header='x'.repeat(4097),p=>Object.defineProperty(p,'__proto__',{value:{polluted:true},enumerable:true})]){
 const invalid=JSON.parse(json);mutate(invalid);assert.throws(()=>api.parse(JSON.stringify(invalid)));
}
copy.mappings[0].title='Changed copy';assert.equal(profile.mappings[0].title,'Declared Wheat');assert.equal({}.polluted,undefined);
console.log('PASS: bounded strict configuration profiles, no observations/consents/cutoff, changed prices, exact layout guards and independent copies.');
