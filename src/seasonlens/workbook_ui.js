/* Private Excel/CSV wizard: explicit configuration, review, atomic commit. */
(() => {
'use strict';
const roles=[['custom','Custom series'],['wheat','Wheat'],['corn','Corn'],['rapeseed','Rapeseed'],['eur_pln','EUR/PLN'],['eur_usd','EUR/USD'],['usd_pln','USD/PLN']];
const units=['EUR/t','PLN/t','USD/t','PLN per EUR','USD per EUR','PLN per USD','Input units'];
const roleUnits={eur_pln:'PLN per EUR',eur_usd:'USD per EUR',usd_pln:'PLN per USD'};
const byId=id=>document.getElementById(id);
const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);return node};
function appendOption(select,value,text){const node=element('option',text);node.value=value;select.append(node)}
function table(headers,rows){const t=element('table'),head=element('thead'),tr=element('tr');for(const name of headers)tr.append(element('th',name));head.append(tr);t.append(head);const body=element('tbody');for(const row of rows){const r=element('tr');row.forEach((value,i)=>r.append(element(i===0?'th':'td',value)));body.append(r)}t.append(body);return t}
function omission(rows){return rows.length?rows.length+' (rows '+rows.slice(0,12).join(', ')+(rows.length>12?', …':'')+')':'0'}
function initialize(){
 const form=byId('browser-upload');if(!form||form.dataset.wizardInitialized)return;form.dataset.wizardInitialized='true';
 let revision=0,loaded=null,staged=null,busy=false;
 const status=text=>{byId('browser-error').textContent=text};
 function invalidate(){revision++;staged=null;byId('browser-review').hidden=true;byId('browser-commit').disabled=true}
 function config(){return {headerRow:Number(byId('browser-header-row').value),startRow:Number(byId('browser-start-row').value)}}
 function mappings(){return [...byId('browser-mappings').querySelectorAll('tr[data-column]')].filter(row=>row.querySelector('[data-field="selected"]').checked).map(row=>({column:row.dataset.column,title:row.querySelector('[data-field="title"]').value.trim(),unit:row.querySelector('[data-field="unit"]').value.trim(),role:row.querySelector('[data-field="role"]').value}))}
 function fillMappings(columns){
  const previous=new Map([...byId('browser-mappings').querySelectorAll('tr[data-column]')].map(row=>[row.dataset.column,{selected:row.querySelector('[data-field="selected"]').checked,title:row.querySelector('[data-field="title"]').value,unit:row.querySelector('[data-field="unit"]').value,role:row.querySelector('[data-field="role"]').value}]));
  const t=table(['Import','Column','Instrument title','Units','Role'],[]),body=t.querySelector('tbody'),dateColumn=byId('browser-excel-date-column').value;
  for(const column of columns){if(column.column===dateColumn)continue;const old=previous.get(column.column),row=element('tr');row.dataset.column=column.column;const check=element('input');check.type='checkbox';check.dataset.field='selected';check.checked=old?.selected??false;check.setAttribute('aria-label','Import column '+column.column);const title=element('input');title.dataset.field='title';title.maxLength=150;title.value=old?.title??column.header??column.column;title.setAttribute('aria-label','Title for column '+column.column);const unit=element('select');unit.dataset.field='unit';unit.setAttribute('aria-label','Units for column '+column.column);units.forEach(v=>appendOption(unit,v,v));unit.value=old?.unit??'EUR/t';const role=element('select');role.dataset.field='role';role.setAttribute('aria-label','Role for column '+column.column);roles.forEach(([v,label])=>appendOption(role,v,label));role.value=old?.role??'custom';role.addEventListener('change',()=>{if(roleUnits[role.value])unit.value=roleUnits[role.value]});for(const value of [check,column.column+' · '+column.header,title,unit,role]){const td=element('td');if(typeof value==='string')td.textContent=value;else td.append(value);row.append(td)}body.append(row)}
  byId('browser-mappings').replaceChildren(t);
 }
 function refreshPreview(){
  if(!loaded)return;
  if(loaded.kind==='XLSX'){
   const info=SeasonLensWorkbook.inspectSheet(loaded.workbook,byId('browser-sheet').value,config()),previous=byId('browser-excel-date-column').value;byId('browser-excel-date-column').replaceChildren();for(const column of info.columns)appendOption(byId('browser-excel-date-column'),column.column,column.column+' · '+column.header);if(info.columns.some(c=>c.column===previous))byId('browser-excel-date-column').value=previous;
   byId('browser-preview').replaceChildren(table(['Row',...info.columns.map(c=>c.column)],info.preview.map(row=>[row.row,...info.columns.map(col=>{const cell=row.cells.find(c=>c.column===col.column);return cell?(String(cell.value??'')+(cell.formula?' [formula'+(cell.hasCachedValue?' cached':' without result')+']':'')):''})])));
   byId('browser-preview-note').textContent='Worksheet '+info.sheetName+' · used rows '+info.dimensions.firstRow+'–'+info.dimensions.lastRow+' · header row '+info.headerRow+' · first data row '+info.startRow+' · '+info.formulaCells+' formula cells. First physical rows shown; header and live/preamble rows are visible for checking.';fillMappings(info.columns);
  }else{
   const info=SeasonLensBrowser.inspectCSV(loaded.text,byId('browser-delimiter').value);byId('browser-preview').replaceChildren(table(['Physical line',...info.header],info.preview.map(row=>[row.row,...row.cells])));byId('browser-preview-note').textContent=info.dataRows+' CSV data rows · first 10 physical row starts shown. The first row is the header.';
  }
 }
 form.addEventListener('input',event=>{invalidate();if(event.target.id==='browser-file'){loaded=null;byId('browser-settings').hidden=true;status('File changed. Open it to review its rows.')}else if(loaded)status('Settings changed. Validate again before adding.')});
 form.addEventListener('change',event=>{
  invalidate();const id=event.target.id;if(loaded)status('Settings changed. Validate again before adding.');if(['browser-sheet','browser-header-row','browser-start-row','browser-excel-date-column','browser-delimiter'].includes(id)&&loaded){try{refreshPreview()}catch(error){byId('browser-preview').replaceChildren();status('Preview rejected: '+error.message)}}
 });
 byId('browser-read').addEventListener('click',async()=>{
  invalidate();const token=revision,file=byId('browser-file').files[0];loaded=null;byId('browser-settings').hidden=true;busy=true;byId('browser-read').disabled=true;status('Reading selected file locally…');
  try{if(!file)throw Error('Select an .xlsx or .csv file.');if(file.size>SeasonLensBrowser.MAX_BYTES)throw Error('File exceeds the 12 MiB browser import limit.');const extension=file.name.split('.').at(-1).toLowerCase();if(!['xlsx','csv'].includes(extension))throw Error('Choose an .xlsx or .csv file. Old .xls and .xlsm files are unsupported.');const buffer=await file.arrayBuffer();if(token!==revision)return;
   if(extension==='xlsx'){const workbook=await SeasonLensWorkbook.readWorkbook(buffer);if(token!==revision)return;loaded={kind:'XLSX',workbook};byId('browser-sheet').replaceChildren();for(const name of workbook.SheetNames)appendOption(byId('browser-sheet'),name,name);if(!workbook.SheetNames.length)throw Error('Workbook has no worksheets.');byId('browser-mappings').replaceChildren();byId('browser-excel-date-column').replaceChildren();}
   else{loaded={kind:'CSV',text:new TextDecoder('utf-8',{fatal:true}).decode(buffer)};if(!byId('browser-title').value.trim())byId('browser-title').value=file.name.replace(/\.csv$/i,'')}
   byId('browser-excel-settings').hidden=loaded.kind!=='XLSX';byId('browser-csv-settings').hidden=loaded.kind!=='CSV';byId('browser-formula-option').hidden=loaded.kind!=='XLSX';byId('browser-mapping-panel').hidden=loaded.kind!=='XLSX';byId('browser-settings').hidden=false;refreshPreview();status('Preview ready. Choose columns and rows, then validate. No observations have been added.');
  }catch(error){if(token===revision){loaded=null;byId('browser-settings').hidden=true;status('File rejected: '+error.message)}}finally{busy=false;byId('browser-read').disabled=false}
 });
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(busy)return;invalidate();const token=revision;busy=true;byId('browser-validate').disabled=true;status('Validating all selected rows and building analyses locally…');
  try{
   if(!loaded)throw Error('Open a file and inspect its preview first.');const asOf=SeasonLensBrowser.cutoffDate(byId('browser-asof').value),group='private_'+Date.now()+'_'+token+'_'+Math.random().toString(36).slice(2),skipBlankRows=byId('browser-skip-blank').checked;
   await new Promise(resolve=>setTimeout(resolve,0));if(token!==revision)return;
   let validated;
   if(loaded.kind==='XLSX')validated=SeasonLensWorkbook.validateSheet(loaded.workbook,byId('browser-sheet').value,{...config(),dateColumn:byId('browser-excel-date-column').value,mappings:mappings(),asOf,skipBlankRows,allowCachedFormulas:byId('browser-allow-formulas').checked,decimal:byId('browser-decimal').value,dateFormat:byId('browser-date-format').value});
   else{const parsed=SeasonLensBrowser.parseCSV(loaded.text,{dateColumn:byId('browser-date-column').value,valueColumn:byId('browser-value-column').value,delimiter:byId('browser-delimiter').value,decimal:byId('browser-decimal').value,skipBlankRows,asOf});validated={series:[{...parsed,title:byId('browser-title').value.trim(),unit:byId('browser-unit').value,role:'custom'}],summary:{sheetName:'CSV',seriesCount:1,cachedFormulaCells:0}}}
   const entries=validated.series.map(series=>{const entry=SeasonLensBrowser.buildEntry(series.records,{...series,asOf,semantics:'User-declared daily observations; quote and roll rules unverified'});entry.import_group=group;entry.role=series.role;entry.source_format=loaded.kind;entry.sheet_name=validated.summary.sheetName;entry.views.Original.market=SeasonLensMarketMath.buildMarket(entry.views.Original.daily,asOf);return entry});if(token!==revision)return;
   if(!entries.length)throw Error('Select at least one instrument column.');staged={token,entries};byId('browser-summary').replaceChildren(table(['Instrument / units','Role','Observations','First date','Last date','Blank values skipped','Future rows excluded'],validated.series.map(s=>[s.title+' · '+s.unit,s.role,s.records.length,s.records[0].date,s.records.at(-1).date,omission(s.skippedBlankRows),omission(s.skippedFutureRows)])));
   byId('browser-review-note').textContent=entries.length+' instrument(s) validated through '+asOf+'. '+(validated.summary.ignoredTrailingRows?validated.summary.ignoredTrailingRows+' empty trailing worksheet row(s) ignored. ':'')+(validated.summary.cachedFormulaCells?validated.summary.cachedFormulaCells+' cached formula result(s) accepted explicitly; these may be stale. ':'')+'Nothing has been added yet.';byId('browser-review').hidden=false;byId('browser-commit').disabled=false;status('Validation passed. Review observation dates and omitted rows, then add the instruments.');
  }catch(error){if(token===revision){staged=null;byId('browser-review').hidden=true;status('Import rejected: '+error.message)}}finally{busy=false;byId('browser-validate').disabled=false}
 });
 byId('browser-commit').addEventListener('click',()=>{
  if(!staged||staged.token!==revision){status('Settings changed. Validate again before adding.');return}const pending=staged;byId('browser-commit').disabled=true;
  try{if(typeof browserInstallEntries!=='function')throw Error('Import integration is unavailable.');browserInstallEntries(pending.entries);staged=null;byId('browser-review').hidden=true;status('Added '+pending.entries.length+' instrument(s) privately in this tab. Reloading clears these imports. See each instrument’s last observation date above.');byId('market-overview').scrollIntoView({behavior:'smooth',block:'start'})}catch(error){status('Could not add validated instruments: '+error.message);byId('browser-commit').disabled=false}
 });
}
globalThis.SeasonLensImportUI=Object.freeze({initialize});
})();
