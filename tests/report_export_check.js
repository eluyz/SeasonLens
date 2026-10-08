/* Hand-built DOM input: adversarial serializer and report lifecycle checks. */
'use strict';
const assert=require('assert');
class TextNode{constructor(value){this.nodeType=3;this.nodeValue=String(value);this.textContent=this.nodeValue;}}
class Node{
 constructor(tag,attrs={},children=[]){this.nodeType=1;this.tagName=tag.toUpperCase();this.childNodes=[];this.attributes=Object.entries(attrs).map(([name,value])=>({name,value}));this.id=attrs.id||'';this.classList=new Set(String(attrs.class||'').split(/\s+/).filter(Boolean));this.hidden='hidden'in attrs;this.value='';this.type='';this.checked=false;this.disabled=false;this.listeners={};this.focused=false;this._html='';for(const child of children)this.append(child);}
 append(...children){for(let child of children){if(typeof child==='string')child=new TextNode(child);child.parentElement=this;this.childNodes.push(child);}}
 get textContent(){return this.childNodes.map(child=>child.textContent).join('');}set textContent(value){this.childNodes=[new TextNode(value)];}
 get innerHTML(){return this._html;}set innerHTML(value){this._html=String(value);}
 hasAttribute(name){return this.attributes.some(a=>a.name===name);}
 closest(tag){for(let node=this;node;node=node.parentElement)if(node.tagName===tag.toUpperCase())return node;return null;}
 addEventListener(name,callback){(this.listeners[name]??=[]).push(callback);}
 async emit(name){for(const callback of this.listeners[name]||[])await callback({target:this,preventDefault(){}});}
 focus(){this.focused=true;if(global.document)global.document.activeElement=this;}
 click(){this.clicked=true;this.emit('click');}
 remove(){if(this.parentElement)this.parentElement.childNodes=this.parentElement.childNodes.filter(n=>n!==this);}
}
const n=(tag,attrs={},...children)=>new Node(tag,attrs,children),text=value=>new TextNode(value);
const body=n('body'),roots=[body],events={};
function find(nodes,id){for(const node of nodes){if(node.id===id)return node;const child=find(node.childNodes||[],id);if(child)return child;}return null;}
const document={body,getElementById:id=>find(roots,id),createElement:tag=>n(tag),addEventListener:(name,callback)=>{(events[name]??=[]).push(callback);},activeElement:null};
body.classList.add=function(c){Set.prototype.add.call(this,c);};body.classList.remove=function(c){this.delete(c);};
for(const id of ['report-export-panel','report-sections','report-build','report-status','seasonlens-report-preview','seasonlens-report-content','report-close','report-print','report-download','report-snapshot-label','report-preview-status'])body.append(n('div',{id}));document.getElementById('seasonlens-report-preview').hidden=true;
global.document=document;
let printCalls=0,downloads=[],revocations=[],urlId=0;
global.print=()=>printCalls++;global.Blob=class{constructor(parts,options){this.parts=parts;this.type=options.type;downloads.push(this);}};global.URL={createObjectURL:()=> 'blob:snapshot-'+(++urlId),revokeObjectURL:url=>revocations.push(url)};global.setTimeout=callback=>{callback();return 1;};
let forbidden=0;for(const name of ['fetch','XMLHttpRequest','localStorage','sessionStorage','indexedDB'])Object.defineProperty(global,name,{configurable:true,get(){forbidden++;throw Error('Forbidden API '+name);}});
const R=require('../src/seasonlens/report_export.js');
const adversarial=n('section',{id:'adversarial',onclick:'alert(1)',style:'color:#123456;background:url(https://evil.test/pixel);--line:#2563eb;position:fixed'},
 n('h2',{},'<Private title & "source">'),
 n('script',{},'ORIGINAL_DATASET_PAYLOAD'),n('style',{},'@import "https://evil.test";'),n('img',{src:'https://evil.test/private'}),
 n('input',{value:'PRIVATE_INPUT_SECRET'}),n('label',{},'PRIVATE_FORM_LABEL',n('select',{},n('option',{},'PRIVATE_OPTIONS_SECRET'))),
 n('div',{class:'science-controls'},'PRIVATE_CONTROL_SECRET'),n('div',{id:'science-fundamental-import'},'PRIVATE_WIZARD_SECRET'),
 n('div',{hidden:''},'HIDDEN_SECRET'),n('a',{href:'javascript:alert(2)'},'LINK_SECRET'),
 n('svg',{viewBox:'0 0 650 270',onload:'alert(3)',style:'fill:#abc;stroke:url(https://evil.test)'},
  n('title',{},'Legend <text>'),n('path',{d:'M 1,2 L 3,4',stroke:'#2563eb','stroke-width':'2',fill:'none',onclick:'alert(4)'}),
  n('use',{href:'https://evil.test/asset.svg#private'}),n('image',{'xlink:href':'https://evil.test'}),n('foreignObject',{},n('div',{},'SVG_HTML_SECRET')),
  n('animate',{attributeName:'href',values:'javascript:alert(5)'}),n('g',{style:'display:none'},n('path',{d:'M999 888',stroke:'#f00'},n('title',{},'HIDDEN_YEAR_LINE_SECRET'))),n('path',{d:'M1 2',stroke:'url(#external)',fill:'javascript:alert(6)'})),
 n('details',{},n('summary',{},'Method explanation'),n('p',{},'Unavailable: insufficient warmup; — is not zero.')),
 n('table',{},n('caption',{},'Observed coverage'),n('tbody',{},n('tr',{},n('th',{scope:'row'},'2026'),n('td',{class:'missing',title:'No observations'},'—')))));
const safe=R.serialize(adversarial);
const scroll=n('div',{class:'table-wrap untrusted',tabindex:'0',role:'region'},n('table',{},'Readable result'));
assert.match(R.serialize(scroll),/class="table-wrap" tabindex="0" role="region"/);
assert(!R.serialize(n('div',{class:'table-wrap',tabindex:'-1'})).includes('tabindex'));
assert(!R.serialize(n('div',{class:'untrusted',tabindex:'0'})).includes('tabindex'));
assert.match(R.serialize(n('svg',{viewBox:'0 0 100 100'},n('path',{d:'M0 0 L100 100'}))),/^<div class="report-chart" tabindex="0" role="region"/);
assert.match(safe,/&lt;Private title &amp; &quot;source&quot;&gt;/);assert.match(safe,/viewBox="0 0 650 270"/);assert.match(safe,/stroke="#2563eb"/);assert.match(safe,/--line:#2563eb/);assert.match(safe,/Method explanation/);assert.match(safe,/Unavailable: insufficient warmup/);assert.match(safe,/title="No observations"/);assert.match(safe,/<h3>Method explanation<\/h3>/);
for(const token of ['onclick','onload','evil.test','javascript:','ORIGINAL_DATASET','PRIVATE_INPUT','PRIVATE_FORM','PRIVATE_CONTROL','PRIVATE_WIZARD','PRIVATE_OPTIONS','HIDDEN_SECRET','LINK_SECRET','SVG_HTML_SECRET','position:','HIDDEN_YEAR_LINE_SECRET','M999 888','href=','xlink','<animate','<style','<script','<select','<input'])assert(!safe.includes(token),'Leaked '+token);
const hiddenLine=n('path',{d:'M100 200'});hiddenLine.style={display:'none'};assert.equal(R.serialize(hiddenLine,true),'');
const weird=n('svg',{},n('path',{d:'M0 0',style:'fill:expression(alert(1));stroke:#fff;--line:url(data:text/html,evil)',transform:'translate(10 20) rotate(30)',width:'10;evil',id:'conflicting-id'}));const weirdSafe=R.serialize(weird);assert.match(weirdSafe,/transform="translate\(10 20\) rotate\(30\)"/);assert(!/expression|url\(|id=|width=/.test(weirdSafe));
body.append(n('section',{id:'selected-overview'},n('div',{class:'card'},'LAST_PRICE_ONLY'),n('p',{},'Counts 219 · 1 blank skipped · 1 future excluded')));
body.append(n('section',{id:'unselected-private'},'UNSELECTED_PRIVATE_GROUP_SECRET'));body.append(n('script',{id:'dataset'},'RAW_OBSERVATIONS_SECRET'));
body.append(n('details',{id:'science-risk-panel'},n('summary',{},'Historical risk'),n('p',{id:'risk-result'},'')));
const range=n('select',{id:'range'});range.value='90';range.selectedOptions=[{textContent:'Last 90 days'}];body.append(n('label',{},'Daily chart range',range));
const sma=n('input',{id:'sma200'});sma.type='checkbox';sma.checked=false;body.append(n('label',{},sma,n('span',{},'SMA200')));
const context={title:'<My imported wheat>',unit:'EUR/t',asOf:'2020-11-03',source:'USER_FILE',provenance:'Private in this tab',semantics:'Daily close; roll rule unknown'};
const sections=[{id:'overview',label:'Overview',targets:['selected-overview'],default:true,settings:['range','sma200']},{id:'risk',label:'Historical risk',targets:['science-risk-panel'],default:true},{id:'private',label:'Other private group',targets:['unselected-private'],default:false}];
let preparation=[],pending=null,resolvePending;
const initialize={context:()=>context,sections,prepareScience:async names=>{preparation.push(names.slice());document.getElementById('risk-result').textContent='219 changes · 95% VaR unavailable: fewer than five tail observations';if(pending)await pending;}};
(async()=>{
 const report=R.initSeasonLensReport(initialize);assert.strictEqual(R.initSeasonLensReport(initialize),report);assert.equal(document.getElementById('report-build').listeners.click.length,1);
 document.activeElement=document.getElementById('report-build');await document.getElementById('report-build').emit('click');assert.deepEqual(preparation[0],['overview','risk']);assert.equal(document.getElementById('science-risk-panel').open,undefined);
 const preview=document.getElementById('seasonlens-report-content').innerHTML;assert.match(preview,/USER_FILE/);assert.match(preview,/2020-11-03/);assert.match(preview,/&lt;My imported wheat&gt;/);assert.match(preview,/Daily chart range: Last 90 days/);assert.match(preview,/SMA200: Hidden/);assert.match(preview,/95% VaR unavailable/);assert.match(preview,/1 blank skipped/);assert(!preview.includes('UNSELECTED_PRIVATE_GROUP_SECRET'));assert(!preview.includes('RAW_OBSERVATIONS_SECRET'));assert(!preview.includes('<input'));assert(body.classList.has('seasonlens-report-open'));assert.equal(document.getElementById('seasonlens-report-preview').hidden,false);
 document.getElementById('selected-overview').textContent='CHANGED_RESULT';context.title='Changed later title';range.selectedOptions[0].textContent='All available history';assert.equal(document.getElementById('seasonlens-report-content').innerHTML,preview);
 await document.getElementById('report-print').emit('click');assert.equal(printCalls,1);await document.getElementById('report-download').emit('click');assert.equal(downloads.length,1);assert.equal(downloads[0].type,'text/html;charset=utf-8');const exported=downloads[0].parts.join('');assert(exported.includes(preview));assert(!exported.includes('CHANGED_RESULT'));assert(!exported.includes('Changed later title'));assert(!exported.includes('<script'));assert(!exported.includes('RAW_OBSERVATIONS_SECRET'));assert.match(exported,/default-src &#?|'none'/);assert.match(exported,/@page\{size:A4 landscape/);assert.match(exported,/width:100%/);assert.equal(revocations.length,1);
 const nativePrint=global.print;global.print=undefined;await document.getElementById('report-print').emit('click');assert.match(document.getElementById('report-preview-status').textContent,/Download HTML/);global.print=()=>{throw Error('blocked');};await document.getElementById('report-print').emit('click');assert.match(document.getElementById('report-preview-status').textContent,/could not open/);global.print=nativePrint;
 await document.getElementById('report-close').emit('click');assert.equal(document.getElementById('seasonlens-report-preview').hidden,true);assert(!body.classList.has('seasonlens-report-open'));assert.equal(document.activeElement,document.getElementById('report-build'));
 await report.build();assert.match(document.getElementById('seasonlens-report-content').innerHTML,/Changed later title/);assert.match(document.getElementById('seasonlens-report-content').innerHTML,/CHANGED_RESULT/);assert.equal(document.getElementById('report-preview-status').textContent,'');for(const listener of events.keydown)listener({key:'Escape',preventDefault(){}});assert.equal(document.getElementById('seasonlens-report-preview').hidden,true);
 // A change during async preparation must not produce a report for mixed settings.
 const last=document.getElementById('seasonlens-report-content').innerHTML;pending=new Promise(resolve=>resolvePending=resolve);const task=report.build();context.asOf='2020-11-02';resolvePending();await task;pending=null;assert.match(document.getElementById('report-status').textContent,/changed during preparation/);assert.equal(document.getElementById('seasonlens-report-content').innerHTML,last);assert.equal(document.getElementById('report-build').disabled,false);
 // Changing a displayed label during lazy render is legitimate; changing its raw value is not.
 const priorPrepare=initialize.prepareScience;initialize.prepareScience=async names=>{await priorPrepare(names);range.selectedOptions[0].textContent='Label refreshed by rendering';};await report.build();assert.match(document.getElementById('report-status').textContent,/Report ready/);initialize.prepareScience=priorPrepare;report.close();
 for(const section of sections)document.getElementById('report-include-'+section.id).checked=false;await report.build();assert.match(document.getElementById('report-status').textContent,/at least one/);
 assert.throws(()=>R.metadata({...context,asOf:'2026-02-30'}),/valid calendar date/);assert.throws(()=>R.metadata({...context,asOf:'0000-01-01'}),/valid calendar date/);assert.throws(()=>R.buildSnapshot(document,{...context,source:''},[sections[0]],'2026-10-08'),/missing source/);const missing=R.buildSnapshot(document,context,[{id:'missing',label:'No data',targets:['does-not-exist']}],'2026-10-08');assert.match(missing.body,/Unavailable: no rendered result/);assert(Object.isFrozen(missing));assert.equal(forbidden,0);
 console.log('PASS: report sanitizer, selected privacy, unavailable values, immutable print/download, repeated build, settings and async consistency.');
})().catch(error=>{console.error(error);process.exitCode=1;});
