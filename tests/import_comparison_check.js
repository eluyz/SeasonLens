/* Independent hand-calculated differences using real XLSX preparation. */
'use strict';
const assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
global.XLSX=require(path.join(root,'src/seasonlens/vendor/xlsx.mini.min.js'));
require(path.join(root,'src/seasonlens/workbook_import.js'));
require(path.join(root,'src/seasonlens/import_profiles.js'));
require(path.join(root,'src/seasonlens/import_comparison.js'));
const settings={headerRow:1,startRow:4,dateColumn:'A',mappings:[{column:'B',title:'Private <price>',unit:'Input units',role:'custom'}],decimal:'.',dateFormat:'ISO'};
const options={...settings,asOf:'2026-01-08',skipBlankRows:true,allowCachedFormulas:false};
function workbook(rows){const book=XLSX.utils.book_new();XLSX.utils.book_append_sheet(book,XLSX.utils.aoa_to_sheet([['Date','Price'],['Units','Input units'],['Live invalid','bad'],...rows]),'Prices');return SeasonLensWorkbook.readWorkbook(XLSX.write(book,{type:'array',bookType:'xlsx'}));}
function validate(book,overrides={}){return SeasonLensWorkbook.validateSheet(book,'Prices',{...options,...overrides});}
const older=workbook([['2026-01-01',100],['2026-01-02',200],['2026-01-03',-5],['2026-01-04',0],['2026-01-05',null],['2026-01-06',55],['2026-01-07',77],['2026-01-09',999]]);
const newer=workbook([['2026-01-01',105],['2026-01-02',200],['2026-01-03',-7],['2026-01-04',-0],['2026-01-05',9],['2026-01-06',null],['2026-01-09',800]]);
const profile=SeasonLensImportProfiles.capture(newer,'Prices',settings);SeasonLensImportProfiles.checkCompatibility(older,profile);
const oldValidated=validate(older),newValidated=validate(newer),oldSnapshot=structuredClone(oldValidated),newSnapshot=structuredClone(newValidated);
const comparison=SeasonLensImportComparison.compare(oldValidated,newValidated),item=comparison.series[0];
assert.deepStrictEqual(item.counts,{new:1,corrected:2,absent:2,unchanged:2});
assert.equal(item.olderCount,6);assert.equal(item.newerCount,5);assert.equal(item.olderFirstDate,'2026-01-01');assert.equal(item.olderLastDate,'2026-01-07');assert.equal(item.newerLastDate,'2026-01-05');
assert.deepStrictEqual(item.changes,[
 {date:'2026-01-01',kind:'corrected',older:100,newer:105,difference:5},
 {date:'2026-01-03',kind:'corrected',older:-5,newer:-7,difference:-2},
 {date:'2026-01-05',kind:'new',older:null,newer:9,difference:null},
 {date:'2026-01-06',kind:'absent',older:55,newer:null,difference:null},
 {date:'2026-01-07',kind:'absent',older:77,newer:null,difference:null},
]);
assert.deepStrictEqual(item.olderBlankRows,[8]);assert.deepStrictEqual(item.newerBlankRows,[9]);assert.deepStrictEqual(item.olderFutureRows,[11]);assert.deepStrictEqual(item.newerFutureRows,[10]);
assert.deepStrictEqual(oldValidated,oldSnapshot);assert.deepStrictEqual(newValidated,newSnapshot);
item.olderBlankRows.push(999);comparison.olderSummary.selectedRows=999;assert.deepStrictEqual(oldValidated,oldSnapshot);
const tinyOld=validate(workbook([['2026-01-01',1]])),tinyNew=validate(workbook([['2026-01-01',1+Number.EPSILON]]));
const tiny=SeasonLensImportComparison.compare(tinyOld,tinyNew).series[0];assert.equal(tiny.counts.corrected,1);assert.equal(tiny.changes[0].difference,Number.EPSILON);
assert.equal(SeasonLensImportComparison.compare(validate(workbook([['0011-01-01',0]])),validate(workbook([['0011-01-01',1]]))).series[0].changes[0].difference,1);
assert.throws(()=>validate(older,{skipBlankRows:false}),/Blank value/);
assert.throws(()=>validate(workbook([['2026-01-01',100],['2026-01-09','bad']])),/Invalid numeric text/);
assert.throws(()=>validate(workbook([['2026-01-01',100],['2026-01-09',9],['2026-01-09',null]])),/Duplicate date/);
assert.throws(()=>validate(workbook([['2026-01-01',100],['2026-02-30',9]])),/Invalid calendar date/);
const renamed=workbook([['2026-01-01',100]]);renamed.Sheets.Prices.B1.v='Renamed';assert.throws(()=>SeasonLensImportProfiles.checkCompatibility(renamed,profile),/headers have changed/);
const formula=workbook([['2026-01-01',100]]);formula.Sheets.Prices.B4.f='1+99';assert.throws(()=>validate(formula),/requires explicit consent/);assert.equal(validate(formula,{allowCachedFormulas:true}).summary.cachedFormulaCells,1);
const mismatch=structuredClone(tinyNew);mismatch.series[0].unit='EUR/t';assert.throws(()=>SeasonLensImportComparison.compare(tinyOld,mismatch),/matching validated/);
const duplicate=structuredClone(tinyNew);duplicate.series[0].records.push({...duplicate.series[0].records[0]});assert.throws(()=>SeasonLensImportComparison.compare(tinyOld,duplicate),/unique dates/);
console.log('PASS: hand-calculated old/new corrections, exact precision, zero/negative prices, omissions/cutoff, full-input validation, layout and formula consent.');
