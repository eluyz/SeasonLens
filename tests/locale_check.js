'use strict';
// Small DOM harness for deterministic mutation/storage/privacy checks, no downloads.
const assert=require('assert'),vm=require('vm'),fs=require('fs');
const source=fs.readFileSync(require('path').join(__dirname,'../src/seasonlens/locale.js'),'utf8');
function environment({search='',stored,deny=false}={}){
 let doc,observer=null;const frames=[],writes=[],history=[];
 function record(change){if(observer?.connected&&change.target.isConnected&&(!change.attributeName||observer.options.attributeFilter.includes(change.attributeName)))observer.records.push(change);}
 class Node{
  constructor(type){this.nodeType=type;this.childNodes=[];this.parentNode=null;}
  get parentElement(){return this.parentNode?.nodeType===1?this.parentNode:null;}
  get isConnected(){for(let n=this;n;n=n.parentNode)if(n===doc?.documentElement)return true;return false;}
  get children(){return this.childNodes.filter(n=>n.nodeType===1);}
  append(...nodes){for(const n of nodes){n.parentNode=this;this.childNodes.push(n);}record({type:'childList',target:this,addedNodes:nodes});}
  contains(node){for(let n=node;n;n=n.parentNode)if(n===this)return true;return false;}
  get textContent(){return this.nodeType===3?this.nodeValue:this.childNodes.map(n=>n.textContent).join('');}
  set textContent(value){for(const old of this.childNodes)old.parentNode=null;this.childNodes=[];this.append(new Text(String(value)));}
 }
 class Text extends Node{
  constructor(value){super(3);this._value=value;}
  get nodeValue(){return this._value;}
  set nodeValue(value){this._value=value;record({type:'characterData',target:this});}
 }
 class Element extends Node{
  constructor(tag){super(1);this.tagName=tag.toUpperCase();this.attributes={};this.listeners={};this.classList={toggle(){}};}
  get id(){return this.attributes.id||'';}set id(v){this.attributes.id=v;}
  setAttribute(k,v){this.attributes[k]=String(v);record({type:'attributes',target:this,attributeName:k});}
  getAttribute(k){return this.attributes[k]??null;}hasAttribute(k){return Object.hasOwn(this.attributes,k);}
  get value(){return this._value??this.getAttribute('value')??(this.tagName==='OPTION'?this.textContent:'');}
  set value(v){this._value=String(v);if(this.tagName==='OPTION')this.attributes.value=String(v);}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);}click(){for(const fn of this.listeners.click||[])fn();}
 }
 const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
 function serialize(n){return n.nodeType===3?escape(n.nodeValue):n.nodeType===11?n.childNodes.map(serialize).join(''):'<'+n.tagName.toLowerCase()+Object.entries(n.attributes).map(([k,v])=>' '+k+'="'+escape(v)+'"').join('')+'>'+n.childNodes.map(serialize).join('')+'</'+n.tagName.toLowerCase()+'>';}
 class Template extends Element{
  constructor(){super('template');this.content=new Node(11);}
  get innerHTML(){return serialize(this.content);}
  set innerHTML(html){const stack=[this.content];for(const token of html.match(/<[^>]+>|[^<]+/g)||[]){if(token.startsWith('</'))stack.pop();else if(token.startsWith('<')){const name=token.match(/^<([\w-]+)/)[1],el=new Element(name);for(const attr of token.matchAll(/([\w-]+)="([^"]*)"/g))el.setAttribute(attr[1],attr[2]);stack.at(-1).append(el);stack.push(el);}else stack.at(-1).append(new Text(token));}}
 }
 class Observer{
  constructor(callback){this.callback=callback;this.records=[];this.connected=false;observer=this;}
  observe(_node,options){this.connected=true;this.options=options;}
  disconnect(){this.connected=false;}takeRecords(){const r=this.records;this.records=[];return r;}
  deliver(){const r=this.takeRecords();if(r.length)this.callback(r);}
 }
 const html=new Element('html'),body=new Element('body');html.append(body);
 function byId(id,n=html){if(n.id===id)return n;for(const child of n.children){const result=byId(id,child);if(result)return result;}return null;}
 doc={documentElement:html,body,getElementById:byId,createElement:tag=>tag==='template'?new Template():new Element(tag)};
 const context={document:doc,URL,URLSearchParams,location:{search,href:'https://example.test/app'+search+'#risk'},history:{replaceState(_a,_b,url){history.push(url);context.location.href=url;context.location.search=new URL(url).search;}},MutationObserver:Observer,requestAnimationFrame:fn=>frames.push(fn),setTimeout:fn=>frames.push(fn),module:{exports:{}}};
 Object.defineProperty(context,'localStorage',{get(){if(deny)throw Error('Access denied');return {getItem:()=>stored,setItem:(k,v)=>{writes.push([k,v]);stored=v;}};}});
 vm.runInNewContext(source,context);const api=context.module.exports;
 const make=(tag,text,parent=body)=>{const el=new Element(tag);if(text!==undefined)el.textContent=text;parent.append(el);return el;};
 function drain(){let turns=0;do{observer?.deliver();const f=frames.shift();if(f)f();if(++turns>100)throw Error('Observer did not settle');}while(frames.length||observer?.records.length);return turns;}
 return {api,body,doc,make,Text,writes,frames,history,drain,get observer(){return observer;}};
}
{
 const e=environment({search:'?lang=pl',stored:'en'}),{api,make}=e;
 const heading=make('h2','Monthly average prices'),svg=make('svg'),svgText=make('text','Jan',svg),button=make('button','Import');button.setAttribute('aria-label','Import');button.setAttribute('title','Historical average');
 const input=make('input');input.value='Wheat';input.setAttribute('placeholder','Title');
 const select=make('select'),option=make('option','Wheat',select);option.value='wheat';const implicit=make('option','Original',select);
 const user=make('option','Wheat Jan Source · private Excel',select);user.value='USER_FILE_001';
 const raw=make('span','Wheat');raw.setAttribute('data-no-translate','');const title=make('input');title.value='Mean';
 const pre=make('pre','Import');const storageBefore=e.writes.length;
 for(const lang of ['en','pl']){const tile=make('button',lang==='en'?'English':'Polski');tile.id='language-'+lang;}
 const guide=make('a','Follow the wheat + EUR/PLN walkthrough');guide.id='start-walkthrough';
 assert.strictEqual(api.init(),api);assert.strictEqual(api.language(),'pl');assert.strictEqual(e.writes.length,storageBefore);
 assert.equal(heading.textContent,'Średnie ceny miesięczne');assert.equal(svgText.textContent,'Sty');assert.equal(button.getAttribute('aria-label'),'Import');assert.equal(button.getAttribute('title'),'Średnia historyczna');assert.equal(input.getAttribute('placeholder'),'Nazwa');assert.equal(input.value,'Wheat');assert.equal(title.value,'Mean');assert.equal(raw.textContent,'Wheat');assert.equal(pre.textContent,'Import');assert.equal(option.value,'wheat');assert.equal(option.textContent,'Pszenica');assert.equal(implicit.value,'Original');assert.equal(user.textContent,'Wheat Jan Source · prywatny Excel');
 assert.equal(e.doc.getElementById('language-pl').getAttribute('aria-pressed'),'true');assert.equal(guide.getAttribute('href'),'https://eluyz.github.io/SeasonLens/walkthrough-pl.html');
 assert.strictEqual(api.init(),api);e.doc.getElementById('language-en').click();assert.equal(api.language(),'en');assert.equal(svgText.textContent,'Jan');assert.equal(input.getAttribute('placeholder'),'Title');assert.equal(option.textContent,'Wheat');assert.equal(user.textContent,'Wheat Jan Source · private Excel');assert.equal(button.getAttribute('title'),'Historical average');assert.match(e.history.at(-1),/lang=en#risk$/);
 api.setLanguage('pl');heading.childNodes[0].nodeValue='Historical average';button.setAttribute('title','Price');const added=make('p','Analysis cutoff: 2026-10-06');e.drain();assert.equal(heading.textContent,'Średnia historyczna');assert.equal(button.getAttribute('title'),'Cena');assert.equal(added.textContent,'Data graniczna analizy: 2026-10-06');assert.equal(e.observer.records.length,0);assert.equal(e.frames.length,0);
 api.setLanguage('en');assert.equal(heading.textContent,'Historical average');assert.equal(button.getAttribute('title'),'Price');assert.equal(added.textContent,'Analysis cutoff: 2026-10-06');assert.equal(user.value,'USER_FILE_001');
 const html=api.localizeHTML('<h2>Historical average</h2><span data-no-translate="true">Wheat</span>','pl');assert.equal(html,'<h2>Średnia historyczna</h2><span data-no-translate="true">Wheat</span>');assert(!html.includes('<html'));assert(!html.includes('<body'));
 assert(e.writes.every(([k,v])=>k==='seasonlens.language.v1'&&['en','pl'].includes(v)));
 assert.equal(api.setLanguage('de'),false);assert.equal(api.language(),'en');
}
for(const args of [{deny:true},{stored:'{"privatePrices":[1]}'},{search:'?lang=invalid',stored:'bad'}]){const e=environment(args);e.api.init();assert.equal(e.api.language(),'en');assert.equal(e.api.setLanguage('pl'),true);assert.equal(e.api.language(),'pl');}
{
 const e=environment({stored:'pl'});const preview=e.make('div');preview.id='browser-preview';e.make('td','Wheat',preview);
 const source=e.make('select');source.id='science-fundamental-source';source.value='private';const privateSelect=e.make('select');privateSelect.id='science-fundamental-commodity';const option=e.make('option','Wheat',privateSelect);option.value='Wheat';
 e.api.init();assert.equal(preview.textContent,'Wheat');assert.equal(option.textContent,'Wheat');
 const large=e.make('div');for(let i=0;i<4100;i++)e.make('span','Historical average',large);e.observer.deliver();assert(e.frames.length);e.frames.shift()();assert(e.frames.length,'Large changed subtree must be continued in bounded batches');e.drain();assert.equal(large.children.at(-1).textContent,'Średnia historyczna');assert.equal(e.observer.records.length,0);
}
{
 const e=environment(),t=e.api.translate;
 assert.equal(t('Analysis cutoff: 2026-10-06','pl'),'Data graniczna analizy: 2026-10-06');
 assert.equal(t('  Historical average\n','pl'),'  Średnia historyczna\n');
 assert.equal(t('Notebook containing Historical average and Wheat','pl'),'Notebook containing Historical average and Wheat');
 assert.equal(t('Analysis cutoff: named customer','pl'),'Analysis cutoff: named customer');
 assert.equal(t('Observation: 2026-10-06','pl'),'Data obserwacji: 2026-10-06');
 assert.equal(t('Reference: unavailable','pl'),'Data odniesienia: niedostępna');
 assert.equal(t('4.325 PLN per EUR','pl'),'4.325 PLN za EUR');
 assert.equal(t('262 observations · 2025-10-06–2026-10-06 · min 4.314 / max 4.424','pl'),'262 obserwacji · 2025-10-06–2026-10-06 · min 4.314 / maks. 4.424');
 assert.equal(t('— analysis report','pl'),'— raport analityczny');
 assert.equal(t('Mean Jan · EUR/t · USER_FILE — private in this tab · analysis cutoff 2026-10-06 · risk/FX/forecast window 2021-10-06–2026-10-06.','pl'),'Mean Jan · EUR/t · USER_FILE — prywatnie w tej karcie · data graniczna analizy 2026-10-06 · okno ryzyka/walut/prognoz 2021-10-06–2026-10-06.');
 assert.equal(t('Private same-workbook conversion: Wheat. Jan × Mean. 210 exact-date positive pairs; 0 commodity observations not converted. No quotes carried forward. Future observations excluded: 1','pl'),'Prywatne przeliczenie w ramach jednego skoroszytu: Wheat. Jan × Mean. 210 dodatnich par z identyczną datą; 0 obserwacji surowca nie przeliczono. Kursów nie przenoszono na kolejne dni. Wykluczone przyszłe obserwacje: 1');
 assert.equal(t('14 observations; higher than reference','pl'),'14 obserwacji; powyżej odniesienia');
 assert.equal(t('Import rejected: Customer Mean Wheat','pl'),'Import odrzucony: Customer Mean Wheat');
 assert.equal(t('2 instrument(s) validated through 2026-10-06. Nothing has been added yet.','pl'),'2 instrumentów sprawdzonych do 2026-10-06. Nie dodano jeszcze żadnych danych.');
}
console.log('PASS: reversible locale, bounded updates, private strings and denied storage');
