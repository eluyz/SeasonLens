/* Browser-only single-series CSV preparation and analytics. No persistence. */
(() => {
'use strict';
const MAX_BYTES=12*1024*1024, MAX_ROWS=20000;
const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const technicalKeys=['value','sma20','sma100','sma200','bollinger_upper','bollinger_lower'];
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=x=>x===null||!Number.isFinite(x)?'—':String(Number(x.toPrecision(6)));
function iso(value){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))throw Error('Dates must use YYYY-MM-DD.');
 const y=+value.slice(0,4),m=+value.slice(5,7),d=+value.slice(8,10);
 if(y<1||m<1||m>12||d<1||d>monthDays(y,m))throw Error('Invalid calendar date: '+value);
 return value;
}
function monthDays(y,m){return [31,(y%4===0&&(y%100!==0||y%400===0))?29:28,31,30,31,30,31,31,30,31,30,31][m-1]}
function cutoffDate(value){iso(value);if(+value.slice(0,4)<11)throw Error('Cutoff year must be 0011 or later for ten-year analyses.');return value}
function stamp(value){const d=new Date(0);d.setUTCFullYear(+value.slice(0,4),+value.slice(5,7)-1,+value.slice(8,10));d.setUTCHours(0,0,0,0);return d.getTime()}
function dateString(d){return String(d.getUTCFullYear()).padStart(4,'0')+'-'+String(d.getUTCMonth()+1).padStart(2,'0')+'-'+String(d.getUTCDate()).padStart(2,'0')}
function priorMonths(value,n){const y=+value.slice(0,4),m=+value.slice(5,7),day=+value.slice(8,10),total=y*12+m-1-n,yy=Math.floor(total/12),mm=total%12+1;return String(yy).padStart(4,'0')+'-'+String(mm).padStart(2,'0')+'-'+String(Math.min(day,monthDays(yy,mm))).padStart(2,'0')}
function checkNumber(x){if(typeof x!=='number'||!Number.isFinite(x))throw Error('A finite real number is required.');if(Math.abs(x)>1e100||(x!==0&&Math.abs(x)<1e-100))throw Error('Browser numeric range is limited to zero or absolute values between 1e-100 and 1e100. Use the local Python app for other magnitudes.');return x}
function checked(x,purpose){if(!Number.isFinite(x))throw Error(purpose+' exceeded the browser numeric range.');return x}
function mean(xs){if(!xs.length)return null;let sum=0,c=0;const scale=xs.reduce((a,b)=>Math.max(a,Math.abs(b)),0)||1;for(const x of xs){const y=x/scale-c,t=sum+y;c=(t-sum)-y;sum=t}return checked(sum/xs.length*scale,'Average')}
function std(xs){const anchor=xs[0],center=xs.map(x=>x-anchor),scale=center.reduce((a,b)=>Math.max(a,Math.abs(b)),0);if(!scale)return 0;const ns=center.map(x=>x/scale),mu=mean(ns);return checked(Math.sqrt(mean(ns.map(x=>(x-mu)**2)))*scale,'Population deviation')}
function csvRows(text,delimiter){
 const rows=[];let cells=[],cell='',quoted=false,closed=false,started=false,line=1,startLine=1;
 function endCell(){cells.push(cell);cell='';closed=false;started=false}
 function endRow(){endCell();rows.push({cells,line:startLine});cells=[];startLine=line;if(rows.length>MAX_ROWS+1)throw Error('CSV exceeds 20,000 data rows.');}
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++}else{quoted=false;closed=true}}else{cell+=c;if(c==='\n')line++;else if(c==='\r'&&text[i+1]!=='\n')line++}continue}
  if(c==='"'){if(started||closed)throw Error('Unexpected quote at physical line '+line+'.');quoted=true;started=true;continue}
  if(c===delimiter){endCell();continue}
  if(c==='\r'||c==='\n'){if(c==='\r'&&text[i+1]==='\n')i++;line++;endRow();continue}
  if(closed)throw Error('Unexpected characters after closing quote at physical line '+line+'.');cell+=c;started=true;
 }
 if(quoted)throw Error('Unclosed quoted CSV cell.');
 if(cell!==''||cells.length||started||closed)endRow();return rows;
}
function parseCSV(text,options){
 if(typeof text!=='string')throw Error('CSV text is required.');
 if(new TextEncoder().encode(text).byteLength>MAX_BYTES)throw Error('CSV exceeds 12 MiB.');
 const opts=options||{},asOf=cutoffDate(opts.asOf),delimiter=opts.delimiter,decimal=opts.decimal;
 if(![',',';','\t'].includes(delimiter))throw Error('Choose comma, semicolon or tab delimiter.');
 if(!['.',','].includes(decimal))throw Error('Choose an explicit decimal separator.');
 if(!opts.dateColumn||!opts.valueColumn||opts.dateColumn===opts.valueColumn)throw Error('Choose distinct date and value columns.');
 const rows=csvRows(text.replace(/^\uFEFF/,''),delimiter);
 if(rows.length<2)throw Error('CSV must have a header and at least one data row.');
 const header=rows.shift().cells;
 if(new Set(header).size!==header.length)throw Error('CSV header names must be unique.');
 const di=header.indexOf(opts.dateColumn),vi=header.indexOf(opts.valueColumn);
 if(di<0||vi<0)throw Error('Selected column was not found in the CSV header.');
 // A multi-series file must be separated explicitly before this single-series importer.
 if(header.includes('instrument_id'))throw Error('This importer accepts one series. Remove the instrument_id column after selecting one instrument locally.');
 const seen=new Set(),records=[],skippedBlankRows=[],skippedFutureRows=[];let originalAllPositive=true;
 for(const row of rows){
  if(row.cells.length!==header.length)throw Error('CSV column count differs at physical line '+row.line+'.');
  const date=iso(row.cells[di].trim());
  if(seen.has(date))throw Error('Duplicate date '+date+' at physical line '+row.line+'.');seen.add(date);
  const raw=row.cells[vi].trim();
  if(raw===''){if(!opts.skipBlankRows)throw Error('Blank value at physical line '+row.line+'. Enable explicit blank skipping.');skippedBlankRows.push(row.line);continue}
  const dialect=decimal===','?/^[+-]?(?:\d+(?:,\d*)?|,\d+)(?:[eE][+-]?\d+)?$/:/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
  const normalized=decimal===','?raw.replace(',','.'):raw;
  if(!dialect.test(raw))throw Error('Invalid number at physical line '+row.line+'. Thousands separators are unsupported.');
  const value=checkNumber(Number(normalized));if(value<=0)originalAllPositive=false;
  if(date>asOf){skippedFutureRows.push(row.line);continue}records.push({date,value});
 }
 if(!records.length)throw Error('No observations remain through the selected cutoff.');
 records.sort((a,b)=>a.date.localeCompare(b.date));
 return {records,skippedBlankRows,skippedFutureRows,totalRows:rows.length,originalAllPositive};
}
function prepared(records,asOf){
 cutoffDate(asOf);if(!Array.isArray(records)||!records.length||records.length>MAX_ROWS)throw Error('Provide 1 to 20,000 observations.');
 const seen=new Set();const out=records.map(r=>{iso(r.date);checkNumber(r.value);if(seen.has(r.date))throw Error('Duplicate date '+r.date);seen.add(r.date);return {date:r.date,value:r.value}}).sort((a,b)=>a.date.localeCompare(b.date));
 const selected=out.filter(r=>r.date<=asOf);if(!selected.length)throw Error('No observations through cutoff.');return {selected,future:out.length-selected.length,positive:out.every(r=>r.value>0)};
}
function indicators(records){return records.map((r,i)=>{const result={...r};for(const n of [20,100,200])result['sma'+n]=i<n-1?null:mean(records.slice(i-n+1,i+1).map(x=>x.value));const deviation=i<19?null:std(records.slice(i-19,i+1).map(x=>x.value));result.bollinger_upper=deviation===null?null:checked(result.sma20+2*deviation,'Bollinger upper');result.bollinger_lower=deviation===null?null:checked(result.sma20-2*deviation,'Bollinger lower');return result})}
function axis(values){if(!values.length)return null;const scale=values.reduce((a,b)=>Math.max(a,Math.abs(b)),0)||1;let lo=Infinity,hi=-Infinity,minValue=Infinity,maxValue=-Infinity;for(const v of values){lo=Math.min(lo,v/scale);hi=Math.max(hi,v/scale);minValue=Math.min(minValue,v);maxValue=Math.max(maxValue,v)}const pad=lo===hi?(lo?0.01:1):Math.max((hi-lo)*.08,Number.EPSILON*Math.max(1,Math.abs(lo),Math.abs(hi)));lo-=pad;hi+=pad;if(!Number.isFinite(lo)||!Number.isFinite(hi)||lo===hi)throw Error('Chart range exceeds browser precision. Use the local Python app.');let labels;for(let p=5;p<=17;p++){labels=Array.from({length:5},(_,i)=>String(Number(((lo+(hi-lo)*i/4)*scale).toPrecision(p))));if(new Set(labels).size===5&&Number(labels[0])<=minValue&&Number(labels[4])>=maxValue)break}if(new Set(labels).size<5||Number(labels[0])>minValue||Number(labels[4])<maxValue)throw Error('Chart tick range exceeds browser precision. Use the local Python app.');return [scale,lo,hi,labels]}
function monthly(records){const groups=new Map();for(const r of records){const key=r.date.slice(0,7);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r)}const result=new Map();for(const [key,rs] of groups)result.set(key,{mean:mean(rs.map(x=>x.value)),count:rs.length,last:rs[rs.length-1]});return result}
const monthKey=(year,month)=>String(year).padStart(4,'0')+'-'+String(month).padStart(2,'0');
function item(groups,year,month){return groups.get(monthKey(year,month))||{mean:null,count:0,last:null}}
function runs(points){const out=[];let current=[];for(const p of points){if(p===null){if(current.length)out.push(current);current=[]}else current.push(p)}if(current.length)out.push(current);return out}
function chart(lines,unit,{seasonal=false,asOf=null,band=null}={}){
 const values=lines.flatMap(l=>l.values.filter(x=>x!==null));if(band)values.push(...band.flatMap(x=>x===null?[]:x));const a=axis(values);if(!a)return '<p>No observations in this window or reference year.</p>';
 const [scale,lo,hi,labels]=a,left=Math.max(80,...labels.map(x=>x.length*7+12));const x=i=>left+i*(1060-left)/11,y=v=>255-(v/scale-lo)/(hi-lo)*210;
 let svg='<svg viewBox="0 0 1120 350" role="img" aria-label="Monthly values and historical context"><title>Monthly values and historical context</title>';
 for(let i=0;i<5;i++){const yy=255-i*52.5;svg+=`<line x1="${left}" x2="1060" y1="${yy}" y2="${yy}" stroke="#dce3ed"/><text x="${left-10}" y="${yy+4}" text-anchor="end">${esc(labels[i])}</text>`}
 if(band){for(const run of runs(band.map((v,i)=>v===null?null:{v,i}))){const top=run.map(p=>x(p.i)+','+y(p.v[1])),bottom=run.slice().reverse().map(p=>x(p.i)+','+y(p.v[0]));svg+=`<polygon points="${top.concat(bottom).join(' ')}" fill="#dbeafe" opacity="0.65"/>`}}
 lines.forEach((line,index)=>{for(const run of runs(line.values.map((v,i)=>v===null?null:{v,i}))){const path=run.map((p,i)=>(i?'L':'M')+x(p.i)+','+y(p.v)).join(' ');svg+=`<path data-year-line="${index}" d="${path}" stroke="${line.color}" stroke-width="2" fill="none" ${line.dashed?'stroke-dasharray="6 4"':''}/>`;for(const p of run){const partial=asOf&&line.current&&p.i===+asOf.slice(5,7)-1&&+asOf.slice(8,10)<monthDays(+asOf.slice(0,4),p.i+1);svg+=`<circle data-year-line="${index}" cx="${x(p.i)}" cy="${y(p.v)}" r="3" stroke="${line.color}" fill="${partial?'#fff':line.color}"/>`}}});
 svg+=`<text x="${left}" y="20">${esc(unit)}</text>`;months.forEach((m,i)=>svg+=`<text x="${x(i)}" y="278" text-anchor="middle">${m}</text>`);
 lines.forEach((l,i)=>{const xx=left+(i%3)*310,yy=300+Math.floor(i/3)*24;svg+=`<g class="chart-legend"><line x1="${xx}" x2="${xx+25}" y1="${yy}" y2="${yy}" stroke="${l.color}" stroke-width="2" ${l.dashed?'stroke-dasharray="6 4"':''}/><text x="${xx+32}" y="${yy+4}">${esc(l.name)}</text></g>`});
 return svg+'</svg>';
}
function priceMatrix(groups,records,unit,asOf){const year=+asOf.slice(0,4),ref=records[records.length-1],fx=/^[A-Z]{3} per [A-Z]{3}$/.test(unit),display=v=>v===null?'—':v.toFixed(fx?3:0);let rows='';for(let m=1;m<=12;m++){rows+='<tr><th>'+months[m-1]+'</th>';for(let y=year-9;y<=year;y++){const v=item(groups,y,m),future=y===year&&m>+asOf.slice(5,7),partial=y===year&&m===+asOf.slice(5,7)&&+asOf.slice(8,10)<monthDays(year,m),color=future?'future-month':v.mean===null?'missing':v.mean<ref.value?'price-lower':v.mean>ref.value?'price-higher':'price-equal',title=future?'Month after analysis cutoff':v.mean===null?'No observations for this month':v.count+' observations; '+(v.mean<ref.value?'lower':v.mean>ref.value?'higher':'equal')+' than reference';rows+=`<td class="${color}" title="${esc(title)}">${display(v.mean)}${partial&&v.mean!==null?' *':''}</td>`}rows+='</tr>'}return `<div class="price-matrix-layout"><div class="table-wrap"><table class="price-matrix"><caption>Monthly average prices · ${esc(unit)}</caption><thead><tr><th>Month</th>${Array.from({length:10},(_,i)=>'<th>'+(year-9+i)+'</th>').join('')}</tr></thead><tbody>${rows}</tbody></table></div><aside class="matrix-reference"><span>Last available daily observation</span><strong>${display(ref.value)}</strong><span>${esc(unit)} · ${ref.date}</span><div class="matrix-key"><span class="price-higher">Higher monthly average</span><span class="price-lower">Lower monthly average</span><span class="price-equal">Equal monthly average</span><span class="missing">No observations</span></div></aside></div><p class="muted">Colors compare unrounded monthly averages with the last available daily observation. * Partial cutoff month. Counts do not certify complete sessions.</p>`}
function recent(groups,unit,asOf){const year=+asOf.slice(0,4),colors=['#2563eb','#c45d11','#7c3aed','#15803d','#dc2626'];const lines=Array.from({length:5},(_,i)=>({name:String(year-4+i),color:colors[i],current:i===4,values:months.map((_,j)=>item(groups,year-4+i,j+1).mean)}));const averages=months.map((_,j)=>mean(lines.map(l=>l.values[j]).filter(v=>v!==null)));lines.push({name:'Period average',color:'#111827',dashed:true,values:averages});let rows='';months.forEach((m,j)=>{const count=lines.slice(0,5).filter(l=>l.values[j]!==null).length,obs=Array.from({length:5},(_,i)=>item(groups,year-4+i,j+1).count).reduce((a,b)=>a+b,0);rows+='<tr><th>'+m+'</th>'+lines.map(l=>'<td>'+fmt(l.values[j])+'</td>').join('')+'<td>'+count+'/5</td><td>'+obs+'</td></tr>'});return '<div class="checks">'+lines.map((l,i)=>`<label><input type="checkbox" data-year-toggle="${i}" checked> ${esc(l.name)}</label>`).join('')+'</div>'+chart(lines,unit,{asOf})+'<div class="table-wrap"><table><thead><tr><th>Month</th>'+lines.map(l=>'<th>'+esc(l.name)+'</th>').join('')+'<th>Years used</th><th>Observations</th></tr></thead><tbody>'+rows+'</tbody></table></div>'}
function seasonal(groups,unit,asOf,n){const year=+asOf.slice(0,4),baseline=[],current=[],bands=[],coverage=[];for(let m=1;m<=12;m++){const items=Array.from({length:n},(_,i)=>item(groups,year-n+i,m)),xs=items.map(x=>x.mean).filter(x=>x!==null),now=item(groups,year,m);baseline.push(mean(xs));current.push(now.mean);bands.push(xs.length?[Math.min(...xs),Math.max(...xs)]:null);coverage.push({years:xs.length,count:items.reduce((a,b)=>a+b.count,0),current:now.count})}const lines=[{name:'Historical average',color:'#2563eb',values:baseline},{name:'Reference-year average',color:'#c45d11',values:current,current:true}];let rows='';months.forEach((m,i)=>{rows+='<tr><th>'+m+'</th><td>'+fmt(baseline[i])+'</td><td>'+fmt(bands[i]&&bands[i][0])+'</td><td>'+fmt(bands[i]&&bands[i][1])+'</td><td>'+coverage[i].years+'/'+n+'</td><td>'+coverage[i].count+'</td><td>'+fmt(current[i])+'</td><td>'+coverage[i].current+'</td><td>'+fmt(current[i]!==null&&baseline[i]!==null?current[i]-baseline[i]:null)+'</td></tr>'});return `<section><h3>${n}-year historical window · ${year-n}–${year-1}</h3>`+chart(lines,unit,{asOf,seasonal:true,band:bands})+'<p class="muted">Pale blue: historical min–max of yearly monthly averages. Hollow orange marker: partial reference month. Each available year receives equal weight.</p><div class="table-wrap"><table><thead><tr><th>Month</th><th>Average</th><th>Minimum</th><th>Maximum</th><th>Years used</th><th>Observations</th><th>Reference average</th><th>Reference observations</th><th>Difference</th></tr></thead><tbody>'+rows+'</tbody></table></div></section>'}
function partial(records,asOf){const year=+asOf.slice(0,4),month=+asOf.slice(5,7),day=+asOf.slice(8,10);return [5,10].map(n=>{const sets=Array.from({length:n},(_,i)=>records.filter(r=>+r.date.slice(0,4)===year-n+i&&+r.date.slice(5,7)===month&&+r.date.slice(8,10)<=Math.min(day,monthDays(year-n+i,month)))),now=records.filter(r=>+r.date.slice(0,4)===year&&+r.date.slice(5,7)===month),means=sets.map(rs=>mean(rs.map(r=>r.value))).filter(x=>x!==null),historical=mean(means),current=mean(now.map(r=>r.value));return '<tr>'+[n,fmt(historical),fmt(current),fmt(historical!==null&&current!==null?current-historical:null),means.length,sets.reduce((a,b)=>a+b.length,0),now.length].map(x=>'<td>'+x+'</td>').join('')+'</tr>'}).join('')}
function returnHeatmap(groups,records,asOf){const first=+records[0].date.slice(0,4),last=+asOf.slice(0,4);let rows='';for(let y=first;y<=last;y++){rows+='<tr><th>'+y+'</th>';for(let m=1;m<=12;m++){const current=item(groups,y,m),previous=item(groups,m===1?y-1:y,m===1?12:m-1),future=y===last&&m>+asOf.slice(5,7),value=current.last&&previous.last?checked(100*(current.last.value/previous.last.value-1),'Monthly change'):null,part=y===last&&m===+asOf.slice(5,7)&&+asOf.slice(8,10)<monthDays(y,m);rows+=`<td class="${future?'future-month':value===null?'missing':''}" style="${value===null?'':'background:'+(value>0?'#d1fae5':value<0?'#ede9fe':'#fff')}" title="${future?'Month after analysis cutoff':current.last?'Last observed price date: '+current.last.date:'No observations for this month'}">${fmt(value)}${value===null?'':'%'}${part?' *':''}</td>`}rows+='</tr>'}return '<div class="table-wrap"><table><thead><tr><th>Year</th>'+months.map(m=>'<th>'+m+'</th>').join('')+'</tr></thead><tbody>'+rows+'</tbody></table></div>'}
function buildView(records,{unit,asOf,futureExcluded=0,skippedBlankRows=[],originalAllPositive=true}={}){
 if(typeof unit!=='string'||!unit.trim())throw Error('Explicit units are required.');
 const {selected,future,positive}=prepared(records,asOf),daily=indicators(selected),groups=monthly(selected),asDate=new Date(stamp(asOf)),ninety=new Date(asDate.getTime()-90*86400000),range_starts={'12m':priorMonths(asOf,12),'90':dateString(ninety),'all':null},axes={};
 for(const horizon of ['12m','90','all']){const rows=daily.filter(r=>range_starts[horizon]===null||r.date>=range_starts[horizon]);for(let mask=1;mask<64;mask++){const values=[];for(const r of rows)for(let i=0;i<6;i++)if((mask&(1<<i))&&r[technicalKeys[i]]!==null)values.push(r[technicalKeys[i]]);axes[horizon+':'+mask]=axis(values)}}
 const bases=new Map();for(const r of selected)if(!bases.has(r.date.slice(0,4)))bases.set(r.date.slice(0,4),r);
 let normalized='<p>Normalized comparison unavailable: strictly positive observations are required, including excluded input rows.</p>',heatmap='<p>Monthly changes unavailable: strictly positive observations are required, including excluded input rows.</p>';
 if(positive&&originalAllPositive){const indexed=selected.map(r=>({...r,value:checked(r.value/bases.get(r.date.slice(0,4)).value*100,'Year normalization')})),ng=monthly(indexed);normalized=[5,10].map(n=>seasonal(ng,'Index: first observed value of each year = 100',asOf,n)+`<details><summary>${n}-year normalization bases</summary><div class="table-wrap"><table><thead><tr><th>Year</th><th>Base date</th><th>Base value</th></tr></thead><tbody>`+Array.from({length:n+1},(_,i)=>{const year=+asOf.slice(0,4)-n+i,b=bases.get(String(year).padStart(4,'0'));return '<tr><th>'+year+'</th><td>'+(b?b.date:'—')+'</td><td>'+fmt(b?b.value:null)+'</td></tr>'}).join('')+'</tbody></table></div></details>').join('');heatmap=returnHeatmap(groups,selected,asOf)}
 const first=selected[0],last=selected[selected.length-1],firstMonth=+first.date.slice(0,4)*12+(+first.date.slice(5,7)-1),endMonth=+asOf.slice(0,4)*12+(+asOf.slice(5,7)-1);
 return {daily,axes,range_starts,price_matrix:priceMatrix(groups,selected,unit,asOf),fiveyear:recent(groups,unit,asOf),profiles:[5,10].map(n=>seasonal(groups,unit,asOf,n)).join(''),normalized,heatmap,partial:partial(selected,asOf),unit,as_of:asOf,observations:selected.length,last_date:last.date,age_days:Math.round((stamp(asOf)-stamp(last.date))/86400000),future_excluded:future+futureExcluded,missing_months:endMonth-firstMonth+1-groups.size,import_summary:{skipped_blank_rows:skippedBlankRows.slice(),excluded_future_rows:futureExcluded},conversion_note:'User CSV stays only in this browser tab. No automatic currency conversion or provider attribution.'};
}
function buildEntry(records,options){const opts=options||{};if(typeof opts.title!=='string'||!opts.title.trim())throw Error('An explicit title is required.');if(typeof opts.unit!=='string'||opts.title.length>200||opts.unit.length>100)throw Error('Title and unit labels are too long.');return {title:opts.title,unit:opts.unit,semantics:'User-declared daily observations; '+(opts.semantics||'price / quote definition supplied by user'),source:'USER_FILE',import_summary:{skipped_blank_rows:(opts.skippedBlankRows||[]).slice(),excluded_future_rows:(opts.skippedFutureRows||[]).slice()},views:{Original:buildView(records,{...opts,futureExcluded:opts.skippedFutureRows?opts.skippedFutureRows.length:0})}}}
function inspectCSV(text,delimiter){
 if(typeof text!=='string'||new TextEncoder().encode(text).byteLength>MAX_BYTES)throw Error('CSV exceeds the 12 MiB browser limit.');
 if(![',',';','\t'].includes(delimiter))throw Error('Choose comma, semicolon or tab delimiter.');
 const rows=csvRows(text.replace(/^\uFEFF/,''),delimiter);
 if(rows.length<2)throw Error('CSV must have a header and at least one data row.');
 const header=rows[0].cells;
 if(new Set(header).size!==header.length)throw Error('CSV header names must be unique.');
 for(const row of rows)if(row.cells.length!==header.length)throw Error('CSV column count differs at physical line '+row.line+'.');
 return {header:header.slice(),preview:rows.slice(0,10).map(r=>({row:r.line,cells:r.cells.slice()})),dataRows:rows.length-1};
}
globalThis.SeasonLensBrowser=Object.freeze({parseCSV,inspectCSV,buildView,buildEntry,indicators,monthly,mean,populationStd:std,axis,validateDate:iso,cutoffDate,escapeHTML:esc,MAX_BYTES,MAX_ROWS});
})();
