import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

// Creates invented, static observations only. Never reads a market-data file.
const outputDir=process.argv[2];
if(!outputDir)throw Error('Pass an output directory.');
await fs.mkdir(outputDir,{recursive:true});
const wb=Workbook.create(),prices=wb.worksheets.add('Prices'),guide=wb.worksheets.add('Read me');
const dates=[],cutoff=new Date('2026-10-06T00:00:00Z');
for(let d=new Date(cutoff);dates.length<210;d.setUTCDate(d.getUTCDate()-1)){
 if(![0,6].includes(d.getUTCDay()))dates.push(new Date(d));
}
dates.reverse();
const rounded=(v,n)=>Number(v.toFixed(n));
const records=dates.map((d,i)=>{
 const eurPln=rounded(4.25+.055*Math.sin(i/18),4),eurUsd=rounded(1.12+.025*Math.cos(i/29),4);
 return [d,rounded(210+8*Math.sin(i/21)+i*.035,2),rounded(188+6*Math.sin(i/19)+i*.025,2),rounded(450+19*Math.cos(i/31)+i*.04,2),eurPln,eurUsd,eurPln/eurUsd];
});
prices.getRange('A1:G3').values=[
 ['Date','Wheat sample','Corn sample','Rapeseed sample','EUR/PLN sample','EUR/USD sample','USD/PLN sample'],
 ['Units','EUR/t','EUR/t','EUR/t','PLN per EUR','USD per EUR','PLN per USD'],
 [new Date('2026-10-07T00:00:00Z'),999,999,999,9,1,9]
];
prices.getRange('A4:G213').values=records;
prices.getRange('A1:G213').format.font={name:'Arial',size:11,color:'#172B43'};
prices.getRange('A1:G213').format.rowHeight=22;
prices.getRange('A1:G213').format.verticalAlignment='center';
prices.getRange('A1:G1').format={fill:'#193C64',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center'};
prices.getRange('A2:G2').format={fill:'#EEF3FA',font:{name:'Arial',size:11,italic:true,color:'#475569'},rowHeight:26};
prices.getRange('A3:G3').format={fill:'#FFF0C2',font:{name:'Arial',size:11,color:'#7C4D00'},rowHeight:26};
prices.getRange('A1:A213').format.columnWidthPx=125;
prices.getRange('B1:D213').format.columnWidthPx=150;
prices.getRange('E1:G213').format.columnWidthPx=162;
prices.getRange('A3:A213').setNumberFormat('yyyy-mm-dd');
prices.getRange('B3:D213').setNumberFormat('0.00');
prices.getRange('E3:G213').setNumberFormat('0.0000');
prices.getRange('B3:G213').format.horizontalAlignment='right';
prices.freezePanes.freezeRows(3);prices.freezePanes.freezeColumns(1);prices.showGridLines=false;
prices.tabColor='#193C64';
guide.showGridLines=false;guide.tabColor='#64748B';
guide.getRange('A1:D36').format.font={name:'Arial',size:11,color:'#172B43'};
guide.getRange('A1:D36').format.rowHeight=25;
guide.getRange('A1:D36').format.verticalAlignment='center';
guide.getRange('A1:A36').format.columnWidthPx=165;
guide.getRange('B1:B36').format.columnWidthPx=235;
guide.getRange('C1:C36').format.columnWidthPx=150;
guide.getRange('D1:D36').format.columnWidthPx=165;
guide.getRange('A2').values=[['SeasonLens import template']];guide.getRange('A2').format.font={name:'Arial',size:16,bold:true};guide.getRange('A2:D2').format.rowHeight=32;
guide.getRange('A4').values=[['All values are invented examples. This file contains no real exchange or bank quotes.']];
guide.getRange('A6:B14').values=[
 ['Import setting','Choose this value'],['Worksheet','Prices'],['Header row',1],['First data row',4],['Date column','A'],['Analysis cutoff','2026-10-06'],['Stored formulas','None. Leave cached-formula consent off.'],['Historical rows','4–213 (210 weekday observations)'],['Live example row','3. Excluded by first data row 4.']
];
guide.getRange('A6:B6').format={fill:'#193C64',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'}};
guide.getRange('B7:B14').format.columnWidthPx=350;
guide.getRange('A17:D23').values=[
 ['Column','Instrument title','Units','Role'],['B','Wheat sample','EUR/t','Wheat'],['C','Corn sample','EUR/t','Corn'],['D','Rapeseed sample','EUR/t','Rapeseed'],['E','EUR/PLN sample','PLN per EUR','EUR/PLN'],['F','EUR/USD sample','USD per EUR','EUR/USD'],['G','USD/PLN sample','PLN per USD','USD/PLN']
];
guide.getRange('A17:D17').format={fill:'#193C64',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'}};
guide.getRange('A26').values=[['Select all six price columns and declare each unit and role explicitly.']];
guide.getRange('A27').values=[['Choose Validate, review six instruments, then Add validated instruments to this tab.']];
guide.getRange('A29').values=[['To use your own history, replace every example row from row 4 onwards.']];
guide.getRange('A30').values=[['Keep one date per row, real Excel dates and numeric prices. Do not paste totals.']];
guide.getRange('A31').values=[['Append rows after the last observation. Missing prices need explicit skip consent.']];
guide.getRange('A32').values=[['Set your own cutoff and quote units. Do not mix different contract definitions.']];
guide.getRange('A34').values=[['The short example history cannot cover five or ten completed years. Gaps remain visible.']];
guide.getRange('A35').values=[['Imports stay in tab memory. Reload clears them. Downloaded reports contain visible results.']];
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Prices!A1:G6',include:'values,formulas',tableMaxRows:6,tableMaxCols:7,maxChars:1600})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:10},summary:'Template formula error scan',maxChars:500})).ndjson);
for(const [sheetName,range]of [['Prices','A1:G12'],['Read me','A1:D36']]){
 const blob=await wb.render({sheetName,range,scale:1.4,format:'png'});
 await fs.writeFile(`${outputDir}/${sheetName==='Prices'?'prices':'instructions'}-preview.png`,new Uint8Array(await blob.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(`${outputDir}/seasonlens-import-template.xlsx`);
console.log(JSON.stringify({rows:records.length,first:dates[0].toISOString().slice(0,10),last:dates.at(-1).toISOString().slice(0,10),output:outputDir}));
