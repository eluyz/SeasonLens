/* Private normalized fundamental vintages; invented examples are not official data. */
(() => {
'use strict';
const schema=Object.freeze(['publication_date','commodity','region','marketing_year','unit','ending_stocks','total_use']);
const commodities=Object.freeze(['wheat','corn','rapeseed']);
const units=Object.freeze(['metric tonnes','thousand metric tonnes','million metric tonnes','bushels','thousand bushels','million bushels']);
const MAX_BYTES=12*1024*1024,MAX_ROWS=20000;
function date(value,label='Publication date') {
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw Error(label+' must use YYYY-MM-DD.');
 const y=Number(value.slice(0,4)),m=Number(value.slice(5,7)),d=Number(value.slice(8,10));
 const days=[31,y%4===0&&(y%100!==0||y%400===0)?29:28,31,30,31,30,31,31,30,31,30,31];
 if(y<1||m<1||m>12||d<1||d>days[m-1]) throw Error(label+' is not a valid calendar date: '+value);
 return value;
}
function number(value,label) {
 if(typeof value!=='number'||!Number.isFinite(value)||Math.abs(value)>1e100||(value!==0&&Math.abs(value)<1e-100)) throw Error(label+' must be a finite number, zero or magnitude 1e-100 through 1e100.');
 return value;
}
function text(value,label) {
 if(typeof value!=='string'||!value.length||value.length>80||value!==value.trim()||/[\x00-\x1f\x7f]/.test(value)) throw Error(label+' must be nonempty, trimmed text of at most 80 characters without control characters.');
 return value;
}
function year(value) {
 if(typeof value!=='string'||!/^\d{4}\/\d{2}$/.test(value)) throw Error('Marketing year must use YYYY/YY, for example 2025/26.');
 const y=Number(value.slice(0,4));
 if(y<1||y>9998||Number(value.slice(5))!==(y+1)%100) throw Error('Marketing year must name consecutive years.');
 return value;
}
function checked(value,label) {
 if(!Number.isFinite(value)) throw Error(label+' exceeds the supported arithmetic range.');
 return value;
}
function validate(rows) {
 if(!Array.isArray(rows)||!rows.length||rows.length>MAX_ROWS) throw Error('Fundamental data must contain 1 through 20,000 rows.');
 const seen=new Set(),groupUnits=new Map();
 const output=rows.map((r,i)=>{
  const label='Fundamental row '+(i+1)+': ';
  if(!r||typeof r!=='object'||Array.isArray(r)||Object.keys(r).length!==schema.length||schema.some(k=>!Object.hasOwn(r,k))) throw Error(label+'requires exactly the seven normalized fields; source/provider claims are unsupported.');
  const clean={publication_date:date(r.publication_date),commodity:text(r.commodity,'Commodity'),region:text(r.region,'Region'),marketing_year:year(r.marketing_year),unit:text(r.unit,'Unit'),ending_stocks:number(r.ending_stocks,'Ending stocks'),total_use:number(r.total_use,'Total use')};
  if(!commodities.includes(clean.commodity)) throw Error(label+'commodity must be wheat, corn or rapeseed; aggregate oilseeds/coarse grains are not interchangeable.');
  if(!units.includes(clean.unit)) throw Error(label+'unsupported quantity unit. Choose an explicit normalized mass or bushel unit.');
  if(clean.ending_stocks<0||clean.total_use<=0) throw Error(label+'ending stocks must be nonnegative and total use must be positive.');
  const group=JSON.stringify([clean.commodity,clean.region,clean.marketing_year]),key=JSON.stringify([clean.publication_date,clean.commodity,clean.region,clean.marketing_year]);
  if(seen.has(key)) throw Error(label+'duplicate publication/commodity/region/marketing-year vintage.');
  seen.add(key);
  if(groupUnits.has(group)&&groupUnits.get(group)!==clean.unit) throw Error(label+'units differ across releases of the same commodity, region and marketing year. Normalize units explicitly before importing.');
  groupUnits.set(group,clean.unit);
  checked(clean.ending_stocks/clean.total_use*100,'Stock-to-use ratio');
  return clean;
 });
 return output.sort((a,b)=>a.publication_date.localeCompare(b.publication_date)||a.commodity.localeCompare(b.commodity)||a.region.localeCompare(b.region)||a.marketing_year.localeCompare(b.marketing_year));
}
function csvRows(input) {
 const rows=[];let cells=[],cell='',quoted=false,closed=false,started=false,line=1,start=1;
 function endCell(){cells.push(cell);cell='';closed=false;started=false;}
 function endRow(){endCell();rows.push({cells,line:start});cells=[];start=line;if(rows.length>MAX_ROWS+1)throw Error('Fundamental CSV exceeds 20,000 data rows.');}
 for(let i=0;i<input.length;i++) {
  const c=input[i];
  if(quoted){if(c==='"'){if(input[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else{cell+=c;if(c==='\n'||(c==='\r'&&input[i+1]!=='\n'))line++;}continue;}
  if(c==='"'){if(started||closed)throw Error('Unexpected CSV quote at physical line '+line+'.');quoted=true;started=true;continue;}
  if(c===','){endCell();continue;}
  if(c==='\r'||c==='\n'){if(c==='\r'&&input[i+1]==='\n')i++;line++;endRow();continue;}
  if(closed)throw Error('Unexpected characters after CSV closing quote at physical line '+line+'.');
  cell+=c;started=true;
 }
 if(quoted)throw Error('Unclosed quoted fundamental CSV field.');
 if(cell!==''||cells.length||started||closed)endRow();
 return rows;
}
function parseCSV(input) {
 if(typeof input!=='string')throw Error('Fundamental CSV text is required.');
 if(new TextEncoder().encode(input).byteLength>MAX_BYTES)throw Error('Fundamental CSV exceeds 12 MiB.');
 const rows=csvRows(input.replace(/^\uFEFF/,''));
 if(rows.length<2)throw Error('Fundamental CSV requires a header and at least one data row.');
 const header=rows.shift().cells;
 if(header.length!==schema.length||header.some((x,i)=>x!==schema[i]))throw Error('Use exactly the normalized CSV header: '+schema.join(',')+'. Provider/source columns and raw official schemas are unsupported.');
 const converted=rows.map(r=>{
  if(r.cells.length!==schema.length)throw Error('Fundamental CSV column count differs at physical line '+r.line+'.');
  const record=Object.fromEntries(schema.map((k,i)=>[k,r.cells[i]]));
  for(const k of ['ending_stocks','total_use']){
   const raw=record[k].trim();
   if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(raw))throw Error('Invalid '+k+' at physical line '+r.line+'. Use decimal points without thousands separators or blanks.');
   record[k]=Number(raw);
  }
  return record;
 });
 return validate(converted);
}
function analyze(rows,options) {
 const opts=options||{},asOf=date(opts.asOf,'Analysis cutoff'),commodity=text(opts.commodity,'Selected commodity'),region=text(opts.region,'Selected region');
 const source=opts.source===undefined?'USER_FILE':opts.source;
 if(source!=='USER_FILE'&&source!=='SYNTHETIC')throw Error('Fundamental provenance must be USER_FILE or SYNTHETIC; official-source claims require a separately validated adapter.');
 if(!commodities.includes(commodity))throw Error('Selected commodity must be wheat, corn or rapeseed.');
 if(opts.marketingYear!==undefined&&opts.marketingYear!==null&&opts.marketingYear!=='')year(opts.marketingYear);
 const all=validate(rows),visible=all.filter(r=>r.publication_date<=asOf),matching=visible.filter(r=>r.commodity===commodity&&r.region===region);
 const marketingYears=[...new Set(matching.map(r=>r.marketing_year))].sort();
 const marketingYear=opts.marketingYear||marketingYears.at(-1)||null;
 const selected=matching.filter(r=>r.marketing_year===marketingYear);
 const revisions=selected.map((r,i)=>{
  const previous=selected[i-1],ratio=checked(r.ending_stocks/r.total_use*100,'Stock-to-use ratio');
  return {...r,stocks_to_use_percent:ratio,previous_publication_date:previous?.publication_date||null,ending_stocks_change:previous?checked(r.ending_stocks-previous.ending_stocks,'Stocks revision'):null,total_use_change:previous?checked(r.total_use-previous.total_use,'Use revision'):null,stocks_to_use_change_pp:previous?checked(ratio-previous.ending_stocks/previous.total_use*100,'Ratio revision'):null};
 });
 return {source,as_of:asOf,selection:{commodity,region,marketing_year:marketingYear},available:revisions.length>0,reason:revisions.length?null:'No publication for the explicitly selected commodity, region and marketing year on or before the cutoff.',counts:{input:all.length,after_cutoff:all.length-visible.length,visible:visible.length,matching:matching.length,selected:revisions.length},marketing_years:marketingYears,units:[...new Set(selected.map(r=>r.unit))],latest:revisions.at(-1)||null,previous:revisions.at(-2)||null,revisions};
}
function demoRows() {
 const rows=[];
 const dates=['2025-06-12','2025-09-12','2026-06-12','2026-09-14','2026-10-09'];
 for(const [commodity,stock,use] of [['wheat',25,100],['corn',30,200],['rapeseed',8,40]]){
  dates.forEach((publication_date,i)=>rows.push({publication_date,commodity,region:'Invented region',marketing_year:i<2?'2025/26':'2026/27',unit:'million metric tonnes',ending_stocks:stock+[0,-1,2,1,4][i],total_use:use+[0,2,5,6,7][i]}));
 }
 return rows;
}
const api=Object.freeze({schema,commodities,units,MAX_BYTES,MAX_ROWS,validateRows:validate,parseCSV,analyze,demoRows});
globalThis.SeasonLensFundamentals=api;
if(typeof module!=='undefined'&&module.exports)module.exports=api;
})();
