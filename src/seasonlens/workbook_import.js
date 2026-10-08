/* Strict browser-memory XLSX preparation. Formula caches are never recalculated. */
(() => {
'use strict';
const MAX_BYTES=12*1024*1024,MAX_EXPANDED=64*1024*1024,MAX_ROWS=20000,MAX_CELLS=250000;
const roles=new Set(['wheat','corn','rapeseed','eur_pln','eur_usd','usd_pln','custom']);
const roleUnits={eur_pln:['PLN per EUR'],eur_usd:['USD per EUR'],usd_pln:['PLN per USD'],wheat:['EUR/t','PLN/t'],corn:['EUR/t','PLN/t'],rapeseed:['EUR/t','PLN/t']};
function fail(message){throw Error(message)}
function library(){if(!globalThis.XLSX)fail('The bundled XLSX reader is unavailable.');return globalThis.XLSX}
function zipEnvelope(buffer){
 const bytes=buffer instanceof Uint8Array?buffer:new Uint8Array(buffer);
 if(!bytes.length||bytes.length>MAX_BYTES)fail('XLSX must be nonempty and no larger than 12 MiB.');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),u16=i=>v.getUint16(i,true),u32=i=>v.getUint32(i,true);
 if(bytes.length<22||u32(0)!==0x04034b50)fail('Choose an unencrypted .xlsx ZIP workbook; .xls and encrypted files are unsupported.');
 let end=-1;for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--)if(u32(i)===0x06054b50&&i+22+u16(i+20)===bytes.length){end=i;break}
 if(end<0)fail('Invalid XLSX ZIP directory.');
 const count=u16(end+10),size=u32(end+12),offset=u32(end+16);
 if(u16(end+4)||u16(end+6)||u16(end+8)!==count||count===65535||size===0xffffffff||offset===0xffffffff||!count||count>1000||offset+size!==end)fail('Unsupported or oversized XLSX ZIP directory.');
 const names=new Set();let pos=offset,expanded=0,compressed=0,readerBytes=bytes;
 const checkExtra=(start,length)=>{const stop=start+length;let i=start;while(i<stop){if(i+4>stop)fail('Malformed XLSX ZIP extra field.');const id=u16(i),length=u16(i+2);i+=4;if(i+length>stop)fail('Malformed XLSX ZIP extra field.');if(id===1)fail('ZIP64 XLSX archives are unsupported.');i+=length;}};
 for(let i=0;i<count;i++){
  if(pos+46>end||u32(pos)!==0x02014b50)fail('Malformed XLSX ZIP entry.');
  const flags=u16(pos+8),method=u16(pos+10),packed=u32(pos+20),unpacked=u32(pos+24),nameLen=u16(pos+28),extraLen=u16(pos+30),commentLen=u16(pos+32),local=u32(pos+42),next=pos+46+nameLen+extraLen+commentLen;
  if(next>end||flags&1||![0,8].includes(method)||packed===0xffffffff||unpacked===0xffffffff||local===0xffffffff||u16(pos+34))fail('Encrypted, split, ZIP64 or unsupported XLSX archives cannot be read.');
  checkExtra(pos+46+nameLen,extraLen);
  let name;try{name=new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(pos+46,pos+46+nameLen))}catch(_){fail('Invalid workbook archive filename.');}
  if(!name||name.includes('\\')||name.startsWith('/')||name.split('/').includes('..')||names.has(name))fail('Unsafe or duplicate workbook archive filename.');
  if(/(?:vbaProject|externalLinks|embeddings|activeX)/i.test(name))fail('Macro, embedded-object and external-link workbooks are unsupported. Use a values-only .xlsx file.');
  if(local+30>offset||u32(local)!==0x04034b50||u16(local+6)!==flags||u16(local+8)!==method)fail('Malformed XLSX local entry.');
  const ln=u16(local+26),le=u16(local+28),data=local+30+ln+le;
  if(data+packed>offset||ln!==nameLen||bytes.subarray(local+30,local+30+ln).some((b,j)=>b!==bytes[pos+46+j]))fail('Inconsistent XLSX archive entry.');
  checkExtra(local+30+ln,le);
  // SheetJS allocates from the LOCAL size before verifying the central directory.
  // Never allow that allocation hint to exceed the already bounded central size.
  const localPacked=u32(local+18),localUnpacked=u32(local+22),descriptor=!!(flags&8);
  if(descriptor?((localPacked!==0&&localPacked!==packed)||(localUnpacked!==0&&localUnpacked!==unpacked)):(localPacked!==packed||localUnpacked!==unpacked))fail('Inconsistent XLSX local and central sizes.');
  if(method===8&&unpacked===0)fail('Zero-length deflated XLSX entries are unsupported; save a standard .xlsx copy.');
  // A descriptor's zero local hint makes the bundled inflater grow dynamically.
  // Normalize only a private copy to the bounded directory hints before parsing.
  if(descriptor&&((localPacked===0&&packed!==0)||(localUnpacked===0&&unpacked!==0))){if(readerBytes===bytes)readerBytes=bytes.slice();const safeView=new DataView(readerBytes.buffer,readerBytes.byteOffset,readerBytes.byteLength);if(localPacked===0)safeView.setUint32(local+18,packed,true);if(localUnpacked===0)safeView.setUint32(local+22,unpacked,true);}
  expanded+=unpacked;compressed+=packed;if(expanded>MAX_EXPANDED||compressed>MAX_BYTES)fail('Expanded XLSX exceeds 64 MiB.');
  names.add(name);pos=next;
 }
 if(pos!==end||!names.has('[Content_Types].xml')||!names.has('xl/workbook.xml'))fail('This is not a supported .xlsx workbook.');
 return {bytes:readerBytes,compressedBytes:bytes.length,expandedBytes:expanded,archiveFiles:count};
}
function bounds(sheet){
 const X=library();let range;try{range=X.utils.decode_range(sheet['!ref']||'A1:A1')}catch(_){fail('Invalid worksheet dimensions.');}
 if(range.s.r<0||range.s.c<0||range.e.r<range.s.r||range.e.c<range.s.c||range.e.r>=21000||range.e.c>=16384)fail('Worksheet dimensions exceed the supported browser limits.');
 let cells=0;for(const address of Object.keys(sheet)){if(address.startsWith('!'))continue;if(!/^[A-Z]+[1-9]\d*$/.test(address))fail('Invalid worksheet cell address.');const p=X.utils.decode_cell(address);if(p.r<range.s.r||p.r>range.e.r||p.c<range.s.c||p.c>range.e.c)fail('Worksheet cells fall outside its declared dimensions.');cells++;}
 return {range,cells};
}
function readWorkbook(buffer){
 const envelope=zipEnvelope(buffer),X=library();let workbook;
 try{workbook=X.read(envelope.bytes,{type:'array',cellDates:false,cellFormula:true,cellNF:true,cellText:false,raw:true,WTF:true,bookFiles:true})}catch(_){fail('The XLSX workbook is malformed or unsupported. Save a values-only .xlsx copy and try again.');}
 // Inspect the actual decompressed package as well as the ZIP's declared sizes.
 let actualExpanded=0;for(const file of Object.values(workbook.files||{})){if(file.type!==2||!file.content)continue;actualExpanded+=file.content.length;if(actualExpanded>MAX_EXPANDED)fail('Expanded XLSX exceeds 64 MiB.');}
 const types=workbook.files&&workbook.files['[Content_Types].xml'];if(!types||!types.content)fail('Workbook content types are missing.');
 const typesXML=new TextDecoder('utf-8',{fatal:true}).decode(types.content);
 const overrides=typesXML.match(/<Override\b[^>]*>/g)||[];
 if(overrides.some(tag=>/macroEnabled|vbaProject|activeX|encrypted/i.test(tag)))fail('Only macro-free .xlsx workbooks are supported.');
 if(!overrides.some(tag=>/PartName=["']\/xl\/workbook\.xml["']/.test(tag)&&/ContentType=["']application\/vnd\.openxmlformats-officedocument\.spreadsheetml\.sheet\.main\+xml["']/.test(tag)))fail('Unsupported workbook content type. Choose a .xlsx workbook.');
 delete workbook.files;delete workbook.keys;
 if(!workbook.SheetNames||!workbook.SheetNames.length||workbook.SheetNames.length>100||new Set(workbook.SheetNames).size!==workbook.SheetNames.length)fail('Workbook has invalid or too many worksheets.');
 let cells=0;const sheets={};for(const name of workbook.SheetNames){if(!workbook.Sheets[name])fail('Worksheet is unavailable.');const b=bounds(workbook.Sheets[name]);cells+=b.cells;sheets[name]={firstRow:b.range.s.r+1,lastRow:b.range.e.r+1,firstColumn:b.range.s.c,lastColumn:b.range.e.c};}
 if(cells>MAX_CELLS)fail('Workbook exceeds 250,000 stored cells.');
 workbook.SeasonLensMeta={compressedBytes:envelope.compressedBytes,expandedBytes:envelope.expandedBytes,archiveFiles:envelope.archiveFiles,cells,sheets};return workbook;
}
function selected(workbook,name,options){
 if(!workbook||!Array.isArray(workbook.SheetNames)||!workbook.SheetNames.includes(name)||!workbook.Sheets[name])fail('Select an available worksheet.');
 const opts=options||{},headerRow=opts.headerRow===undefined?1:opts.headerRow,startRow=opts.startRow===undefined?4:opts.startRow;
 if(!Number.isInteger(headerRow)||!Number.isInteger(startRow)||headerRow<1||headerRow>1000||startRow<=headerRow||startRow>1001)fail('Header and first data rows must be positive physical row numbers; data must follow the header (maximum first data row 1001).');
 const sheet=workbook.Sheets[name],b=bounds(sheet);if(b.cells>MAX_CELLS||b.range.e.r-startRow+2>MAX_ROWS)fail('Worksheet exceeds 20,000 data rows or 250,000 stored cells.');
 if(b.range.e.c-b.range.s.c+1>250)fail('A selected worksheet may contain at most 250 columns.');
 return {sheet,range:b.range,headerRow,startRow,date1904:!!(workbook.Workbook&&workbook.Workbook.WBProps&&workbook.Workbook.WBProps.date1904)};
}
function cellAt(sheet,row,col){return sheet[library().utils.encode_cell({r:row-1,c:col})]}
function blank(cell){return !cell||(!cell.f&&(cell.t==='z'||cell.v===undefined||cell.v===null||(typeof cell.v==='string'&&!cell.v.trim())))}
function previewValue(cell){if(!cell)return '';if(cell.v instanceof Date)return Number.isFinite(cell.v.getTime())?cell.v.toISOString():'Invalid date';if(cell.v===undefined||cell.v===null)return cell.f?'[formula: no cached value]':'';return String(cell.v).slice(0,300);}
function inspectSheet(workbook,name,options){
 const s=selected(workbook,name,options),X=library(),columns=[];let formulaCells=0;
 for(let c=s.range.s.c;c<=s.range.e.c;c++)columns.push({column:X.utils.encode_col(c),header:previewValue(cellAt(s.sheet,s.headerRow,c))});
 const preview=[];for(let r=1;r<=Math.min(s.range.e.r+1,10);r++)preview.push({row:r,cells:columns.map(c=>{const cell=cellAt(s.sheet,r,X.utils.decode_col(c.column));return {column:c.column,value:previewValue(cell),type:cell?cell.t:null,formula:!!(cell&&cell.f),hasCachedValue:!!(cell&&cell.v!==undefined&&cell.v!==null)}})});
 for(const key of Object.keys(s.sheet))if(!key.startsWith('!')&&s.sheet[key].f)formulaCells++;
 return {sheetName:name,headerRow:s.headerRow,startRow:s.startRow,date1904:s.date1904,columns,preview,formulaCells,dimensions:{firstRow:s.range.s.r+1,lastRow:s.range.e.r+1,firstColumn:X.utils.encode_col(s.range.s.c),lastColumn:X.utils.encode_col(s.range.e.c)}};
}
function dateISO(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))fail('Dates must use YYYY-MM-DD.');
 const y=+value.slice(0,4),m=+value.slice(5,7),d=+value.slice(8,10),days=[31,y%4===0&&(y%100!==0||y%400===0)?29:28,31,30,31,30,31,31,30,31,30,31][m-1];
 if(y<1||y>9999||!days||d<1||d>days)fail('Invalid calendar date: '+value);return value;
}
function dateOf(value,epoch,format){
 if(value instanceof Date){if(!Number.isFinite(value.getTime())||value.getUTCHours()||value.getUTCMinutes()||value.getUTCSeconds()||value.getUTCMilliseconds())fail('Date cells must contain a valid day without a time.');return dateISO(value.toISOString().slice(0,10));}
 if(typeof value==='number'){
  if(!Number.isSafeInteger(value)||value<0||(!epoch&&value===60))fail('Excel date must be a whole valid day; fictional 1900-02-29 is unsupported.');
  const base=Date.UTC(epoch?1904:1899,epoch?0:11,epoch?1:31),day=epoch?value:value>60?value-1:value,result=new Date(base+day*86400000);
  if(!Number.isFinite(result.getTime()))fail('Excel date is out of range.');return dateISO(result.toISOString().slice(0,10));
 }
 if(typeof value!=='string')fail('Date cells must contain Excel day numbers or explicitly formatted date text.');
 const raw=value.trim();if(format==='ISO')return dateISO(raw);if(!/^\d{2}\.\d{2}\.\d{4}$/.test(raw))fail('Date text must use DD.MM.YYYY.');return dateISO(raw.slice(6,10)+'-'+raw.slice(3,5)+'-'+raw.slice(0,2));
}
function numeric(value,decimal){
 if(typeof value==='string'){const raw=value.trim(),pattern=decimal===','?/^[+-]?(?:\d+(?:,\d*)?|,\d+)(?:[eE][+-]?\d+)?$/:/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;if(!pattern.test(raw))fail('Invalid numeric text. Thousands separators are unsupported.');value=Number(decimal===','?raw.replace(',','.'):raw);}
 if(typeof value!=='number'||!Number.isFinite(value)||Math.abs(value)>1e100||(value!==0&&Math.abs(value)<1e-100))fail('Values must be finite numbers: zero or absolute magnitudes 1e-100 through 1e100.');return value;
}
function validateSheet(workbook,name,options){
 const opts=options||{},s=selected(workbook,name,opts),X=library(),asOf=dateISO(opts.asOf);
 if(+asOf.slice(0,4)<11)fail('Cutoff year must be 0011 or later for ten-year analyses.');
 const decimal=opts.decimal===undefined?'.':opts.decimal,dateFormat=opts.dateFormat===undefined?'ISO':opts.dateFormat;
 if(!['.',','].includes(decimal)||!['ISO','DD.MM.YYYY'].includes(dateFormat))fail('Choose an explicit decimal separator and date-text format.');
 const columnIndex=column=>{if(typeof column!=='string'||!/^[A-Z]{1,3}$/.test(column))fail('Columns must use Excel letters such as A or B.');const c=X.utils.decode_col(column);if(c<s.range.s.c||c>s.range.e.c)fail('Selected column '+column+' is outside the worksheet.');return c;};
 const dateCol=columnIndex(opts.dateColumn);if(!Array.isArray(opts.mappings)||!opts.mappings.length||opts.mappings.length>20)fail('Select between 1 and 20 price columns.');
 const used=new Set([dateCol]),usedRoles=new Set(),titles=new Set(),series=opts.mappings.map(m=>{
  const col=columnIndex(m.column);if(used.has(col))fail('Date and selected value columns must be distinct.');used.add(col);
  if(typeof m.title!=='string'||!m.title.trim()||m.title.length>200||typeof m.unit!=='string'||!m.unit.trim()||m.unit.length>100)fail('Each series needs a title and units (maximum 200 / 100 characters).');
  const title=m.title.trim(),unit=m.unit.trim(),role=m.role||'custom';if(titles.has(title))fail('Selected series titles must be unique.');titles.add(title);
  if(!roles.has(role))fail('Unknown declared instrument role.');if(role!=='custom'){if(usedRoles.has(role))fail('Each instrument role may be selected only once.');usedRoles.add(role);if(!roleUnits[role].includes(unit))fail('Units do not match the declared '+role+' role.');}
  return {column:m.column,col,title,unit,role,records:[],skippedBlankRows:[],skippedFutureRows:[],originalAllPositive:true};
 });
 let end=s.range.e.r+1,ignoredTrailingRows=0,cachedFormulaCells=0;
 const emptyRow=r=>{for(let c=s.range.s.c;c<=s.range.e.c;c++)if(!blank(cellAt(s.sheet,r,c)))return false;return true};
 while(end>=s.startRow&&emptyRow(end)){end--;ignoredTrailingRows++;}
 const read=(cell,row,column)=>{if(blank(cell))return null;if(cell.f){if(!opts.allowCachedFormulas)fail('Formula at '+column+row+' requires explicit consent to use saved cached values; formulas are not recalculated.');if(cell.v===undefined||cell.v===null||cell.t==='z')fail('Formula at '+column+row+' has no saved cached value.');cachedFormulaCells++;}if(['b','e'].includes(cell.t))fail('Boolean or Excel error at '+column+row+' cannot be imported.');return cell.v;};
 const seen=new Set();for(let row=s.startRow;row<=end;row++){
  let date;try{date=dateOf(read(cellAt(s.sheet,row,dateCol),row,opts.dateColumn),s.date1904,dateFormat)}catch(e){fail('Row '+row+', '+opts.dateColumn+': '+e.message)}
  if(seen.has(date))fail('Duplicate date '+date+' at physical row '+row+', including excluded or blank rows.');seen.add(date);
  for(const item of series){let value;try{const cell=cellAt(s.sheet,row,item.col);if(blank(cell)){if(!opts.skipBlankRows)fail('Blank value; enable explicit blank-value skipping.');item.skippedBlankRows.push(row);continue}value=numeric(read(cell,row,item.column),decimal)}catch(e){fail('Row '+row+', '+item.column+': '+e.message)}
   if(value<=0){item.originalAllPositive=false;if(['eur_pln','eur_usd','usd_pln'].includes(item.role))fail('Row '+row+', '+item.column+': declared FX quotes must be strictly positive, including excluded future rows.');}if(date>asOf){item.skippedFutureRows.push(row);continue}item.records.push({date,value});
  }
 }
 for(const item of series){if(!item.records.length)fail('No observations remain through the cutoff for '+item.title+'. No series has been imported.');item.records.sort((a,b)=>a.date.localeCompare(b.date));delete item.col;}
 return {series,summary:{sheetName:name,headerRow:s.headerRow,startRow:s.startRow,selectedRows:Math.max(0,end-s.startRow+1),ignoredTrailingRows,cachedFormulaCells,seriesCount:series.length,date1904:s.date1904}};
}
globalThis.SeasonLensWorkbook=Object.freeze({readWorkbook,inspectSheet,validateSheet,MAX_BYTES,MAX_EXPANDED,MAX_ROWS,MAX_CELLS});
})();
