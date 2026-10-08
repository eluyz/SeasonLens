'use strict';
const assert=require('assert');
class Element {
 constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.attributes={};this.listeners={};this.value='';this.textContent='';this.open=false;this.disabled=false;this.hidden=false;}
 append(...nodes){for(const n of nodes){n.parentElement=this;this.children.push(n);if(this.tagName==='SELECT'&&!this.value)this.value=n.value;}}
 prepend(n){n.parentElement=this;this.children.unshift(n)}
 replaceChildren(){this.children=[];this.value=''}
 get options(){return this.children}
 setAttribute(key,value){this.attributes[key]=String(value)}
 hasAttribute(key){return Object.hasOwn(this.attributes,key)}
 removeAttribute(key){delete this.attributes[key]}
 addEventListener(type,callback,options){(this.listeners[type]??=[]).push({callback,options})}
 fire(type,extra={}){for(const listener of [...this.listeners[type]||[]]){listener.callback({target:this,preventDefault(){},...extra});if(listener.options?.once)this.listeners[type]=this.listeners[type].filter(x=>x!==listener)}}
 querySelector(selector){const tags=selector.split(',').map(x=>x.toUpperCase());for(const n of this.children){if(tags.includes(n.tagName))return n;const nested=n.querySelector(selector);if(nested)return nested}return null}
 closest(tag){for(let n=this;n;n=n.parentElement)if(n.tagName===tag.toUpperCase())return n;return null}
 focus(){this.focused=true}
 scrollIntoView(options){this.scrolled=options}
}
const main=new Element('main'),nodes={};
const add=(id,tag='div',parent=main)=>{const n=new Element(tag);n.id=id;parent.append(n);nodes[id]=n;return n};
const baseInstrument=add('instrument','select'),baseCurrency=add('currency','select');
const appendOption=(select,value,text=value)=>{const option=new Element('option');option.value=value;option.textContent=text;select.append(option)};
appendOption(baseInstrument,'wheat','Invented wheat');appendOption(baseInstrument,'fx','Invented EUR/PLN');baseInstrument.value='wheat';
const data={wheat:{title:'Invented wheat',source:'SYNTHETIC',unit:'EUR/t',views:{Original:{unit:'EUR/t',as_of:'2026-10-06'},'PLN/t':{unit:'PLN/t',as_of:'2026-10-06'}}},fx:{title:'Invented EUR/PLN',source:'SYNTHETIC',unit:'PLN per EUR',views:{Original:{unit:'PLN per EUR',as_of:'2026-10-06'}}}};
let chooses=0,refreshes=0,api,cutoff='2026-10-06';
function choose(){chooses++;baseCurrency.replaceChildren();for(const key of Object.keys(data[baseInstrument.value].views))appendOption(baseCurrency,key);refresh()}
function refresh(){refreshes++;cutoff=data[baseInstrument.value].views[baseCurrency.value].as_of;api?.refresh()}
choose();chooses=refreshes=0;
const section=add('season-section','section');section.append(new Element('h2'));add('fiveyear','div',section);
const outer=add('outer','details');outer.open=false;const risk=add('science-risk-panel','details',outer);risk.append(new Element('summary'));risk.open=false;
const fx=add('science-fx-panel','details');fx.append(new Element('summary'));
const importer=add('browser-import-panel','section');importer.append(new Element('h2'));
const report=add('report-export-panel','section');report.append(new Element('h2'));
const table=add('table-frame','div',section);
function findById(id,n=main){if(n.id===id)return n;for(const child of n.children){const found=findById(id,child);if(found)return found}return null}
global.document={querySelector:s=>s==='main'?main:null,getElementById:findById,createElement:tag=>new Element(tag),querySelectorAll:()=>[table]};
let changedHash='';global.history={replaceState:(_a,_b,hash)=>changedHash=hash};global.matchMedia=()=>({matches:true});
let forbidden=0;for(const name of ['localStorage','sessionStorage','fetch','XMLHttpRequest','WebSocket','indexedDB'])Object.defineProperty(global,name,{configurable:true,get(){forbidden++;throw Error('Unexpected '+name)}});
const initialize=require('../src/seasonlens/quick_controls.js');
const context={data,view:()=>data[baseInstrument.value]?.views[baseCurrency.value],choose,refresh,cutoff:()=>cutoff};
api=initialize(context);assert.equal(initialize(context),api);assert.equal(main.children.filter(n=>n.id==='seasonlens-quick-controls').length,1);
const mirrorInstrument=findById('quick-instrument'),mirrorCurrency=findById('quick-currency'),toggle=findById('quick-controls-toggle'),options=findById('quick-controls-options');
assert.equal(mirrorInstrument.value,'wheat');assert.equal(mirrorCurrency.options.length,2);assert.match(findById('quick-context').textContent,/EUR\/t/);assert.match(findById('quick-cutoff').textContent,/2026-10-06/);assert.equal(table.attributes.tabindex,'0');assert(options.hidden);
// Mirrored changes invoke canonical callbacks once, despite their refresh recursion.
mirrorCurrency.value='PLN/t';mirrorCurrency.fire('change');assert.equal(baseCurrency.value,'PLN/t');assert.equal(refreshes,1);assert.equal(chooses,0);assert.match(findById('quick-context').textContent,/PLN\/t/);
mirrorInstrument.value='fx';mirrorInstrument.fire('change');assert.equal(baseInstrument.value,'fx');assert.equal(chooses,1);assert.equal(refreshes,2);assert.equal(mirrorCurrency.options.length,1);assert.equal(mirrorCurrency.value,'Original');
mirrorInstrument.fire('change');assert.equal(chooses,1);mirrorCurrency.value='PLN/t';mirrorCurrency.fire('change');assert.equal(refreshes,2);assert.equal(mirrorCurrency.value,'Original');
// Canonical top controls and imports synchronize back, including private cutoff/source.
baseInstrument.value='wheat';choose();assert.equal(mirrorInstrument.value,'wheat');
data.private={title:'<Private workbook>',source:'USER_FILE',unit:'EUR/t',views:{Original:{unit:'EUR/t',as_of:'2020-07-28'}}};appendOption(baseInstrument,'private','<Private workbook>');baseInstrument.value='private';choose();
assert.equal(mirrorInstrument.value,'private');assert.equal(mirrorInstrument.options.at(-1).textContent,'<Private workbook>');assert.match(findById('quick-context').textContent,/<Private workbook>/);assert.match(findById('quick-cutoff').textContent,/2020-07-28/);assert.match(findById('quick-provenance').textContent,/USER_FILE.*tab only/);
// Native links open nested details, preserve data, move focus, and honor reduced motion.
toggle.fire('click');assert(!options.hidden);assert.equal(toggle.attributes['aria-expanded'],'true');
const host=findById('seasonlens-quick-controls'),nav=host.querySelector('nav'),riskLink=nav.children.find(n=>n.href==='#science-risk-panel');let prevented=false;riskLink.fire('click',{preventDefault(){prevented=true}});
assert(prevented);assert(outer.open&&risk.open);assert(options.hidden);assert(risk.children[0].focused);assert.equal(risk.scrolled.behavior,'auto');assert.equal(changedHash,'#science-risk-panel');assert.equal(baseInstrument.value,'private');risk.children[0].fire('blur');assert(!risk.children[0].hasAttribute('tabindex'));
toggle.fire('click');host.fire('keydown',{key:'Escape'});assert(options.hidden);assert(toggle.focused);
const seasonalLink=nav.children.find(n=>n.href==='#fiveyear');seasonalLink.fire('click');assert(section.scrolled);assert(section.children[0].focused);
nav.children.find(n=>n.href==='#report-export-panel').fire('click');assert(report.scrolled);assert.equal(baseInstrument.value,'private');assert.equal(forbidden,0);
// Empty apps can initialize before first selection and become ready after import.
baseInstrument.replaceChildren();baseCurrency.replaceChildren();api.refresh();assert(mirrorInstrument.disabled);assert(mirrorCurrency.disabled);assert.match(findById('quick-context').textContent,/import data/);
appendOption(baseInstrument,'private','<Private workbook>');baseInstrument.value='private';choose();assert(!mirrorInstrument.disabled);assert.equal(mirrorInstrument.listeners.change.length,1);
console.log('PASS: synchronized local quick controls, one-shot callbacks, private import cutoff, focus navigation, empty state and no network/storage.');
