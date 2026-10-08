/* Bounded DOM lifecycle checks; no claim of browser/device layout coverage. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
class Node {
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.listeners={};this.hidden=false;this.disabled=false;this.value='';this.checked=false;this.files=[];}
 append(...nodes){this.children.push(...nodes);if(this.tag==='select'&&!this.value&&this.children.length)this.value=this.children[0].value;}
 replaceChildren(...nodes){this.children=[];if(this.tag==='select')this.value='';this.append(...nodes);}
 setAttribute(){}
 querySelectorAll(selector){const match=node=>selector==='tbody'?node.tag==='tbody':selector==='tr[data-column]'?node.tag==='tr'&&Object.hasOwn(node.dataset,'column'):selector.startsWith('[data-field=')?node.dataset.field===selector.slice(13,-2):false;const result=[];function visit(node){for(const child of node.children){if(match(child))result.push(child);visit(child)}}visit(this);return result;}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
 addEventListener(name,f){(this.listeners[name]??=[]).push(f);}
 async emit(name,extra={}){for(const f of this.listeners[name]||[])await f({preventDefault(){},target:this,...extra});}
 scrollIntoView(){}
}
const ids=['browser-upload','browser-error','browser-review','browser-commit','browser-header-row','browser-start-row','browser-mappings','browser-excel-date-column','browser-preview','browser-preview-note','browser-file','browser-settings','browser-read','browser-asof','browser-excel-settings','browser-csv-settings','browser-formula-option','browser-mapping-panel','browser-sheet','browser-title','browser-date-column','browser-value-column','browser-unit','browser-delimiter','browser-decimal','browser-skip-blank','browser-allow-formulas','browser-validate','browser-date-format','browser-summary','browser-review-note','market-overview'];
const nodes=Object.fromEntries(ids.map(id=>[id,new Node(['browser-sheet','browser-excel-date-column'].includes(id)?'select':'div')]));
global.document={getElementById:id=>nodes[id],createElement:tag=>new Node(tag)};
for(const [id,value] of Object.entries({'browser-title':'Private test','browser-unit':'EUR/t','browser-asof':'2026-01-02','browser-header-row':'1','browser-start-row':'4','browser-date-column':'date','browser-value-column':'value','browser-delimiter':',','browser-decimal':'.','browser-date-format':'ISO'}))nodes[id].value=value;
let externalCalls=0;for(const name of ['fetch','XMLHttpRequest','WebSocket'])global[name]=()=>{externalCalls++;throw Error('Unexpected external call');};for(const name of ['localStorage','sessionStorage','indexedDB'])Object.defineProperty(global,name,{get(){externalCalls++;throw Error('Unexpected persistent storage');}});
vm.runInThisContext(fs.readFileSync(path.join(root,'src/seasonlens/browser_import.js'),'utf8'));
global.XLSX=require(path.join(root,'src/seasonlens/vendor/xlsx.mini.min.js'));
require(path.join(root,'src/seasonlens/workbook_import.js'));
global.SeasonLensMarketMath={buildMarket:()=>({})};const installed=[];
global.browserInstallEntries=entries=>installed.push(entries);
vm.runInThisContext(fs.readFileSync(path.join(root,'src/seasonlens/workbook_ui.js'),'utf8'));
SeasonLensImportUI.initialize();SeasonLensImportUI.initialize(); // initialization must be idempotent
async function readFile(name,buffer){nodes['browser-file'].files=[{name,size:buffer.byteLength,arrayBuffer:async()=>buffer}];await nodes['browser-read'].emit('click');}
function workbook(broken=false){const sheet=XLSX.utils.aoa_to_sheet([['Date','Wheat','EUR/PLN'],['Units','EUR/t','PLN per EUR'],['LIVE INVALID','bad','bad'],['2026-01-01',200,4],['2026-01-02',210,broken?'broken':4.2],['2026-01-03',999,5]]);const book=XLSX.utils.book_new();XLSX.utils.book_append_sheet(book,sheet,'Prices');return XLSX.write(book,{type:'array',bookType:'xlsx'});}
function selectMaster(){for(const row of nodes['browser-mappings'].querySelectorAll('tr[data-column]')){row.querySelector('[data-field="selected"]').checked=true;const fx=row.dataset.column==='C';row.querySelector('[data-field="role"]').value=fx?'eur_pln':'wheat';row.querySelector('[data-field="unit"]').value=fx?'PLN per EUR':'EUR/t';}}
(async()=>{
 const csvBuffer=()=>new TextEncoder().encode('date,value\n2026-01-01,100\n2026-01-02,120\n2026-01-03,999\n').buffer;
 await readFile('test.csv',csvBuffer());assert.equal(nodes['browser-settings'].hidden,false);
 await nodes['browser-upload'].emit('submit');assert.equal(installed.length,0);assert.equal(nodes['browser-review'].hidden,false);
 await nodes['browser-upload'].emit('input',{target:nodes['browser-asof']});assert.equal(nodes['browser-review'].hidden,true);assert.match(nodes['browser-error'].textContent,/Settings changed.*Validate again/);
 await nodes['browser-commit'].emit('click');assert.equal(installed.length,0);
 await nodes['browser-upload'].emit('submit');await nodes['browser-commit'].emit('click');assert.equal(installed.length,1);
 assert.equal(installed[0][0].views.Original.observations,2);assert.equal(installed[0][0].source_format,'CSV');assert.equal(installed[0][0].role,'custom');assert.equal(installed[0][0].import_summary.excluded_future_rows.length,1);
 await nodes['browser-commit'].emit('click');assert.equal(installed.length,1);
 let release;nodes['browser-file'].files=[{name:'late.csv',size:70,arrayBuffer:()=>new Promise(resolve=>release=resolve)}];const pending=nodes['browser-read'].emit('click');await nodes['browser-upload'].emit('input',{target:{id:'browser-file'}});release(csvBuffer());await pending;assert.equal(nodes['browser-settings'].hidden,true);
 await readFile('broken.xlsx',workbook(true));assert.equal(nodes['browser-settings'].hidden,false);selectMaster();await nodes['browser-upload'].emit('submit');assert.equal(nodes['browser-review'].hidden,true);assert.match(nodes['browser-error'].textContent,/Import rejected/);assert.equal(installed.length,1);
 await readFile('master.xlsx',workbook());selectMaster();await nodes['browser-upload'].emit('submit');assert.equal(installed.length,1);assert.equal(nodes['browser-review'].hidden,false);await nodes['browser-commit'].emit('click');assert.equal(installed.length,2);assert.equal(installed[1].length,2);assert.equal(installed[1][0].import_group,installed[1][1].import_group);assert.equal(installed[1][0].source_format,'XLSX');assert.equal(installed[1][1].role,'eur_pln');assert.equal(installed[1][0].views.Original.observations,2);assert.equal(installed[1][0].views.Original.daily.at(-1).value,210);assert.equal(installed[1][0].import_summary.excluded_future_rows.length,1);
 assert.equal(externalCalls,0);console.log('PASS: two-phase CSV/XLSX, invalidation, atomic invalid-master rejection, metadata, future omissions, one-shot commit, stale read and no network/storage.');
})().catch(error=>{console.error(error);process.exitCode=1;});
