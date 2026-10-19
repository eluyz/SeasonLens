import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

// Static invented examples, using the same wheat construction as the import template.
// Run with the bundled artifact-tool runtime, then normalize_template_package.py on each XLSX.
const output = process.argv[2];
if (!output) throw Error('Pass an output directory.');
await fs.mkdir(output, {recursive: true});
const dates = [];
for (let day = new Date('2026-10-06T00:00:00Z'); dates.length < 210; day.setUTCDate(day.getUTCDate()-1)) {
  if (![0, 6].includes(day.getUTCDay())) dates.push(new Date(day));
}
dates.reverse();
const older = dates.map((day, i) => [day, Number((210+8*Math.sin(i/21)+i*.035).toFixed(2))]);
const newer = older.slice(1).map(([day, value]) => [new Date(day), value]);
newer.at(-1)[1] = 218.29;
newer.push([new Date('2026-10-07T00:00:00Z'), 215]);
for (const [name, rows] of [['older', older], ['newer', newer]]) {
  const wb = Workbook.create(), sheet = wb.worksheets.add('Prices');
  sheet.getRange('A1:B3').values = [
    ['Date', 'Wheat sample'], ['SYNTHETIC units', 'EUR/t'],
    [new Date('2026-10-08T00:00:00Z'), 999]
  ];
  sheet.getRange('A4:B213').values = rows;
  sheet.showGridLines = false;
  sheet.getRange('A1:B213').format = {font: {name:'Arial',size:11,color:'#18283F'},rowHeight:23,verticalAlignment:'center'};
  sheet.getRange('A1:A213').format.columnWidthPx = 180;
  sheet.getRange('B1:B213').format.columnWidthPx = 160;
  sheet.getRange('A1:B1').format = {fill:'#193C64',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center'};
  sheet.getRange('A2:B2').format.fill = '#EEF3FA';
  sheet.getRange('A3:B3').format.fill = '#FFF0C2';
  sheet.getRange('A3:A213').setNumberFormat('yyyy-mm-dd');
  sheet.getRange('B3:B213').setNumberFormat('0.00');
  sheet.freezePanes.freezeRows(3);
  wb.recalculate();
  console.log((await wb.inspect({kind:'table',range:'Prices!A210:B213',include:'values,formulas',tableMaxRows:4,tableMaxCols:2,maxChars:900})).ndjson);
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:5},maxChars:300})).ndjson);
  const preview = await wb.render({sheetName:'Prices',range:'A1:B9',scale:1.5,format:'png'});
  await fs.writeFile(`${output}/${name}-preview.png`,new Uint8Array(await preview.arrayBuffer()));
  await (await SpreadsheetFile.exportXlsx(wb)).save(`${output}/seasonlens-${name}.xlsx`);
}
console.log('Invented pair: 210 rows each, 1 new / 1 corrected (+5) / 1 absent / 208 unchanged.');
