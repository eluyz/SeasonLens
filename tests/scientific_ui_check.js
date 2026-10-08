/* Real statistical modules with a bounded DOM lifecycle fixture. */
'use strict';
const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),base=path.join(root,'src/seasonlens');
for(const name of ['science_common','risk_analysis','seasonal_stats','forecast_lab','fundamentals'])require(path.join(base,name+'.js'));
class Element{
 constructor(tag='div'){this.tag=tag;this.listeners={};this.children=[];this.value='';this.textContent='';this.innerHTML='';this.open=false;this.hidden=false;this.disabled=false;this.files=[];}
 append(node){this.children.push(node);if(this.tag==='select'&&!this.value)this.value=node.value;}
 replaceChildren(){this.children=[];this.value='';}
 addEventListener(type,callback){(this.listeners[type]??=[]).push(callback);}
 async emit(type){for(const callback of this.listeners[type]||[])await callback({target:this});}
}
const nodes={},panel=fs.readFileSync(path.join(base,'scientific_panel.html'),'utf8');
for(const match of panel.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"/g))nodes[match[2]]=new Element(match[1]);
for(const id of ['instrument','currency'])nodes[id]=new Element('select');
Object.assign(nodes['instrument'],{value:'commodity'});nodes['currency'].value='Original';
for(const [id,value]of Object.entries({'science-period':'5y','science-horizon':'1','science-confidence':'0.95','science-direction':'buyer','science-quantity':'100','science-seasonal-years':'5','science-fundamental-source':'demo'}))nodes[id].value=value;
global.document={getElementById:id=>nodes[id],createElement:tag=>new Element(tag)};
let forbidden=0;for(const name of ['localStorage','sessionStorage','fetch','XMLHttpRequest','WebSocket','indexedDB'])Object.defineProperty(global,name,{configurable:true,get(){forbidden++;throw Error('Unexpected '+name);}});
const rows=[];for(let year=2010;year<=2026;year++)for(let month=1;month<=12;month++){const date=year+'-'+String(month).padStart(2,'0')+'-15';rows.push({date,value:200+(year-2010)*2+month*.7});}
for(let day=1;day<=200;day++){const date=new Date(Date.UTC(2025,11,1));date.setUTCDate(date.getUTCDate()+day);const iso=date.toISOString().slice(0,10);if(!rows.some(r=>r.date===iso))rows.push({date:iso,value:240+Math.sin(day/10)*4});}rows.sort((a,b)=>a.date.localeCompare(b.date));
let asOf='2026-10-06';const fxRows=rows.map((row,i)=>({date:row.date,value:4+Math.sin(i/13)*.02}));
const data={commodity:{title:'<Invented wheat>',source:'SYNTHETIC',unit:'EUR/t',views:{Original:{unit:'EUR/t',daily:rows}}},fx:{source:'SYNTHETIC',views:{Original:{unit:'PLN per EUR',daily:fxRows}}}};
const esc=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const fmt=(value,d=3)=>Number.isFinite(value)?value.toFixed(d):'—',chartCalls=[];
const options={data,view:()=>data[nodes.instrument.value]?.views[nodes.currency.value],cutoff:()=>asOf,chart:(...args)=>chartCalls.push(args),esc,fmt,card:(label,value,note='')=>esc(label)+' '+esc(value)+' '+esc(note),marketFXId:()=> 'fx'};
let riskCalls=0,seasonalCalls=0,forecastCalls=0;
const actualRisk=global.SeasonLensRisk,actualSeasonal=global.SeasonLensSeasonalStats,actualForecast=global.SeasonLensForecasts;
global.SeasonLensRisk={...actualRisk,historicalRisk:(...args)=>{riskCalls++;return actualRisk.historicalRisk(...args);}};
global.SeasonLensSeasonalStats={...actualSeasonal,analyze:(...args)=>{seasonalCalls++;return actualSeasonal.analyze(...args);}};
global.SeasonLensForecasts={...actualForecast,evaluate:(...args)=>{forecastCalls++;return actualForecast.evaluate(...args);}};
const initialize=require(path.join(base,'scientific_ui.js'));
(async()=>{
 const science=initialize(options);assert.equal(initialize(options),science);assert.equal(nodes['science-period'].listeners.change.length,1);assert.match(nodes['science-context'].textContent,/SYNTHETIC/);assert.equal(chartCalls.length,0);
 for(const name of ['risk','seasonal','fx','forecast','fundamental']){nodes['science-'+name+'-panel'].open=true;await nodes['science-'+name+'-panel'].emit('toggle');}
 assert.match(nodes['science-risk-status'].textContent,/valid changes/);assert.match(nodes['science-risk-cards'].innerHTML,/Historical 95% VaR/);assert.match(nodes['science-exposure'].innerHTML,/EUR/);assert.equal(nodes['science-quantity-label'].textContent,'Quantity in tonnes');
 assert.match(nodes['science-seasonal-status'].textContent,/2021–2025/);assert.match(nodes['science-seasonal-table'].innerHTML,/At least 8/);assert.match(nodes['science-seasonal-table'].innerHTML,/Positive years/);assert.match(nodes['science-forecast-table'].innerHTML,/Last observed price/);assert.match(nodes['science-fx-status'].textContent,/exact matching intervals/);assert.match(nodes['science-fundamental-status'].textContent,/SYNTHETIC.*invented/);assert.equal(nodes['science-fundamental-year'].value,'2026/27');assert.doesNotMatch(nodes['science-fundamental-table'].innerHTML,/2026-10-09/);
 // Quantity is an arithmetic scenario only and must not invalidate statistical caches.
 const counts=[riskCalls,seasonalCalls,forecastCalls];nodes['science-quantity'].value='101';await nodes['science-quantity'].emit('input');science.refresh();assert.deepEqual([riskCalls,seasonalCalls,forecastCalls],counts);
 nodes['science-confidence'].value='.99';await nodes['science-confidence'].emit('change');assert.match(nodes['science-risk-status'].textContent,/500 valid intervals/);assert.match(nodes['science-risk-cards'].innerHTML,/VaR —/);
 nodes['science-seasonal-years'].value='10';await nodes['science-seasonal-years'].emit('change');assert.match(nodes['science-seasonal-status'].textContent,/2016–2025/);const call=chartCalls.at(-1);assert(call[2].some(line=>line.name.includes('historical-mean')));assert.equal(call[3].band,undefined);
 // Panel math failure is contained; unrelated forecast and fundamentals still render.
 const badRows=[...rows,{date:'2028-99-01',value:2}];data.bad={...data.commodity,views:{Original:{unit:'EUR/t',daily:badRows}}};nodes.instrument.value='bad';science.refresh();assert.match(nodes['science-risk-status'].textContent,/unavailable.*Invalid calendar date/);assert.equal(nodes['science-risk-cards'].innerHTML,'');assert.match(nodes['science-fundamental-status'].textContent,/SYNTHETIC/);nodes.instrument.value='commodity';science.refresh();
 // Synthetic/private isolation remains enforced even if a caller supplies a wrong FX ID.
 data.commodity.source='USER_FILE';data.commodity.import_group='private1';science.refresh();assert.match(nodes['science-fx-status'].textContent,/Invented FX is never substituted/);assert.equal(nodes['science-fx-cards'].innerHTML,'');data.commodity.source='SYNTHETIC';science.refresh();
 nodes['science-confidence'].value='.95';nodes.instrument.value='fx';science.refresh();assert.equal(nodes['science-quantity-label'].textContent,'Amount in EUR');assert.match(nodes['science-exposure'].innerHTML,/PLN/);nodes.instrument.value='commodity';
 // Explicit private fundamental staging, commit, future cutoff, one-shot and stale-read invalidation.
 nodes['science-fundamental-source'].value='private';await nodes['science-fundamental-source'].emit('change');assert.match(nodes['science-fundamental-status'].textContent,/Validate and add/);
 const csv='publication_date,commodity,region,marketing_year,unit,ending_stocks,total_use\n2026-06-01,wheat,Private region,2026/27,million metric tonnes,20,100\n2026-09-01,wheat,Private region,2026/27,million metric tonnes,21,100\n2026-11-01,wheat,Private region,2026/27,million metric tonnes,999,100\n';
 nodes['science-fundamental-file'].files=[{name:'private.csv',size:csv.length,arrayBuffer:async()=>new TextEncoder().encode(csv).buffer}];await nodes['science-fundamental-read'].emit('click');assert.equal(nodes['science-fundamental-add'].hidden,false);assert.match(nodes['science-fundamental-review'].textContent,/3 releases; 2.*1 future/);assert.match(nodes['science-fundamental-status'].textContent,/Validate and add/);
 await nodes['science-fundamental-add'].emit('click');assert.match(nodes['science-fundamental-status'].textContent,/USER_FILE.*Private region/);assert.match(nodes['science-fundamental-cards'].innerHTML,/21.00%/);assert.doesNotMatch(nodes['science-fundamental-table'].innerHTML,/999/);await nodes['science-fundamental-add'].emit('click');assert.equal(nodes['science-fundamental-add'].hidden,true);
 await nodes['science-fundamental-read'].emit('click');asOf='2026-08-01';science.refresh();assert.equal(nodes['science-fundamental-add'].hidden,true);assert.match(nodes['science-fundamental-review'].textContent,/Cutoff changed/);assert.match(nodes['science-fundamental-cards'].innerHTML,/20.00%/);
 let release;nodes['science-fundamental-file'].files=[{name:'late.csv',size:csv.length,arrayBuffer:()=>new Promise(resolve=>release=resolve)}];const pending=nodes['science-fundamental-read'].emit('click');await nodes['science-fundamental-file'].emit('change');release(new TextEncoder().encode(csv).buffer);await pending;assert.equal(nodes['science-fundamental-add'].hidden,true);assert.match(nodes['science-fundamental-review'].textContent,/File changed/);
 nodes['science-fundamental-file'].files=[{name:'bad.csv',size:2,arrayBuffer:async()=>new Uint8Array([255,255]).buffer}];await nodes['science-fundamental-read'].emit('click');assert.match(nodes['science-fundamental-error'].textContent,/CSV rejected/);assert.equal(nodes['science-fundamental-add'].hidden,true);assert.match(nodes['science-fundamental-status'].textContent,/USER_FILE/);
 assert.equal(forbidden,0);console.log('PASS: lazy idempotent scientific panels, real statistics, strict isolation, cutoff, contained errors, staged fundamental lifecycle and no network/storage.');
})().catch(error=>{console.error(error);process.exitCode=1;});
