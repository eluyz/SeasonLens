'use strict';
const assert=require('assert');
class Element{
 constructor(tag,id){this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.attributes={};this.listeners={};this.parentElement=null;this.open=false;this.disabled=false;this.textContent='';}
 append(child){this.children.push(child);child.parentElement=this}
 setAttribute(key,value){this.attributes[key]=String(value)}
 hasAttribute(key){return Object.hasOwn(this.attributes,key)}
 removeAttribute(key){delete this.attributes[key]}
 addEventListener(type,callback,options){(this.listeners[type]??=[]).push({callback,options})}
 async fire(type,event={}){const pending=[];for(const listener of [...this.listeners[type]||[]]){pending.push(listener.callback({preventDefault(){},...event}));if(listener.options?.once)this.listeners[type]=this.listeners[type].filter(n=>n!==listener)}await Promise.all(pending)}
 querySelector(selector){const tags=selector.split(',').map(n=>n.toUpperCase());for(const child of this.children){if(tags.includes(child.tagName))return child;const nested=child.querySelector(selector);if(nested)return nested}return null}
 closest(tag){for(let current=this;current;current=current.parentElement)if(current.tagName===tag.toUpperCase())return current;return null}
 focus(options){this.focused=options}
 scrollIntoView(options){this.scrolled=options}
}
const main=new Element('main','main');let nodes={};
function add(tag,id,parent=main){const node=new Element(tag,id);nodes[id]=node;parent.append(node);return node}
function guide(){const host=add('section','seasonlens-start');for(const name of ['explore','monthly','import','report'])add('a','start-'+name,host);add('button','start-template',host);add('p','start-template-status',host);return host}
global.document={getElementById:id=>nodes[id]||null};
let hash='',reduce=true;global.history={replaceState:(_a,_b,value)=>hash=value};global.matchMedia=()=>({matches:reduce});
let forbidden=0;for(const key of ['localStorage','sessionStorage','fetch','XMLHttpRequest','WebSocket','indexedDB'])Object.defineProperty(global,key,{configurable:true,get(){forbidden++;throw Error('Forbidden access')}});
const initialize=require('../src/seasonlens/start_ui.js');
(async()=>{
 // Empty/local builds remain valid. A missing target preserves the native anchor.
 assert.equal(initialize().navigate('missing'),false);
 const host=guide(),api=initialize();assert.equal(initialize(),api);
 assert(nodes['start-template'].disabled);assert.match(nodes['start-template-status'].textContent,/unavailable.*own XLSX or CSV/);
 let prevented=false;await nodes['start-import'].fire('click',{preventDefault(){prevented=true}});assert(!prevented);
 const outer=add('details','closed-parent'),importer=add('section','browser-import-panel',outer),heading=add('h2','import-heading',importer);
 await nodes['start-import'].fire('click',{preventDefault(){prevented=true}});assert(prevented&&outer.open);assert.deepEqual(heading.focused,{preventScroll:true});assert.equal(heading.attributes.tabindex,'-1');assert.equal(importer.scrolled.behavior,'auto');assert.equal(hash,'#browser-import-panel');await heading.fire('blur');assert(!heading.hasAttribute('tabindex'));
 const prices=add('section','year-comparison',outer),pricesHeading=add('h2','year-heading',prices);add('div','fiveyear',prices);reduce=false;await nodes['start-explore'].fire('click');assert.equal(prices.scrolled.behavior,'smooth');assert(pricesHeading.focused);assert.equal(hash,'#fiveyear');
 const monthly=add('section','prices-seasonality'),monthlyHeading=add('h2','monthly-heading',monthly);monthlyHeading.setAttribute('tabindex','0');await nodes['start-monthly'].fire('click');await monthlyHeading.fire('blur');assert.equal(monthlyHeading.attributes.tabindex,'0');
 const report=add('section','report-export-panel');add('h2','report-heading',report);await nodes['start-report'].fire('click');assert(report.scrolled);assert.equal(host.listeners.click,undefined);
 // A bundled workbook is requested only on explicit click and only once while pending.
 nodes={};const activeHost=guide();let requests=0,resolveDownload;
 const context={downloadTemplate(){requests++;return new Promise(resolve=>{resolveDownload=resolve})}};
 Object.defineProperty(context,'data',{get(){throw Error('Must not read prices')}});
 const active=initialize(context),button=nodes['start-template'],status=nodes['start-template-status'];assert(!button.disabled);assert.equal(requests,0);assert.equal(initialize(context),active);assert.equal(button.listeners.click.length,1);
 const first=button.fire('click');assert.equal(requests,1);assert(button.disabled);await button.fire('click');assert.equal(requests,1);resolveDownload();await first;assert(!button.disabled);assert.match(status.textContent,/download requested/);
 // Download errors never expose arbitrary exception strings and allow a retry.
 nodes={};guide();let attempts=0;initialize({downloadTemplate(){attempts++;if(attempts===1)throw Error('<script>private path</script>')}});
 await nodes['start-template'].fire('click');assert.match(nodes['start-template-status'].textContent,/could not be downloaded/);assert(!nodes['start-template-status'].textContent.includes('private path'));assert(!nodes['start-template'].disabled);
 await nodes['start-template'].fire('click');assert.equal(attempts,2);assert.match(nodes['start-template-status'].textContent,/download requested/);assert.equal(forbidden,0);assert(activeHost._seasonLensStartGuide);
 console.log('PASS: optional local start guide, revealed focus navigation, unavailable template fallback, explicit download and retry without data access.');
})().catch(error=>{console.error(error);process.exitCode=1});
