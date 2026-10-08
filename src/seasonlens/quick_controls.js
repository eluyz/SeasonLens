/* In-tab navigation and mirrored native selectors; no data transmission. */
(function (root) {
 'use strict';
 function initSeasonLensQuickControls(context) {
  const doc=root.document,main=doc?.querySelector('main');
  if(!main)return {refresh(){}};
  if(main._seasonLensQuickControls)return main._seasonLensQuickControls;
  const byId=id=>doc.getElementById(id);
  const make=(tag,text,className)=>{const n=doc.createElement(tag);if(text)n.textContent=text;if(className)n.className=className;return n};
  const host=make('aside',null,'quick-controls');host.id='seasonlens-quick-controls';host.setAttribute('aria-label','Current analysis and shortcuts');
  const bar=make('div',null,'quick-controls-bar'),current=make('p',null,'quick-context');current.id='quick-context';
  const contextBox=make('div',null,'quick-context-box'),cutoffLine=make('p',null,'quick-cutoff');cutoffLine.id='quick-cutoff';contextBox.append(current,cutoffLine);
  const toggle=make('button','Analysis options','secondary');toggle.type='button';toggle.id='quick-controls-toggle';toggle.setAttribute('aria-controls','quick-controls-options');toggle.setAttribute('aria-expanded','false');
  bar.append(contextBox,toggle);
  const options=make('div',null,'quick-controls-options');options.id='quick-controls-options';options.hidden=true;
  const fields=make('div',null,'quick-controls-fields');
  const instrument=make('select');instrument.id='quick-instrument';
  const currency=make('select');currency.id='quick-currency';
  for(const [text,input]of [['Instrument',instrument],['Display units',currency]]){const label=make('label',text);label.append(input);fields.append(label)}
  const provenance=make('p',null,'quick-provenance');provenance.id='quick-provenance';
  const links=make('nav',null,'quick-controls-links');links.setAttribute('aria-label','Go to an analysis');
  const hint=make('p','Tables and charts scroll sideways independently. Use the arrow keys when their frame is focused.','quick-scroll-hint');
  function expanded(open){options.hidden=!open;toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'Hide options':'Analysis options'}
  toggle.addEventListener('click',()=>expanded(options.hidden));
  host.addEventListener('keydown',event=>{if(event.key==='Escape'&&!options.hidden){expanded(false);toggle.focus();event.preventDefault()}});
  function reveal(id){
   let target=byId(id);if(!target)return false;
   if(id==='fiveyear')target=target.closest('section')||target;
   for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
   expanded(false);
   const focus=target.querySelector('h2,summary')||target;
   if(!focus.hasAttribute('tabindex')){focus.setAttribute('tabindex','-1');focus.addEventListener('blur',()=>focus.removeAttribute('tabindex'),{once:true})}
   focus.focus({preventScroll:true});
   try{root.history?.replaceState(null,'','#'+id)}catch(_){}
   target.scrollIntoView({behavior:root.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches?'auto':'smooth',block:'start'});
   return true;
  }
  for(const [id,text]of [['fiveyear','Seasonality'],['science-risk-panel','Historical risk'],['science-fx-panel','Currency effects'],['browser-import-panel','Import data'],['report-export-panel','Export report']]){
   const link=make('a',text);link.href='#'+id;link.addEventListener('click',event=>{if(reveal(id))event.preventDefault()});links.append(link);
  }
  options.append(fields,provenance,links,hint);host.append(bar,options);main.prepend(host);
  let instrumentSignature=null,currencySignature=null;
  function sync(input,base,previous){
   const choices=base?[...base.options].map(o=>[o.value,o.textContent]):[];
   const signature=JSON.stringify(choices);
   if(signature!==previous){input.replaceChildren();for(const [value,text]of choices){const option=make('option',text);option.value=value;input.append(option)}}
   input.value=base?.value||'';input.disabled=!choices.length||!!base?.disabled;
   return signature;
  }
  function refresh(){
   const baseInstrument=byId('instrument'),baseCurrency=byId('currency');
   instrumentSignature=sync(instrument,baseInstrument,instrumentSignature);currencySignature=sync(currency,baseCurrency,currencySignature);
   const selected=context.data?.[baseInstrument?.value];let view;try{view=context.view()}catch(_){}
   if(selected&&view){
    const cutoff=context.cutoff(),unit=view.unit||selected.unit||'Original input units';
    current.textContent=selected.title+' · '+unit;cutoffLine.textContent='Analysis cutoff: '+cutoff;
    provenance.textContent='Source: '+selected.source+' · '+(selected.source==='SYNTHETIC'?'Invented demonstration data.':selected.source==='USER_FILE'?'Private import in this tab only.':'Source declared by the dataset.');
   }else{current.textContent='Select or import data to begin';cutoffLine.textContent='No analysis cutoff selected';provenance.textContent='No selected data view.'}
   for(const frame of doc.querySelectorAll('.table-wrap,.science-table,.market-chart,#daily,#fiveyear,#profiles,#normalized')){
    if(!frame.hasAttribute('tabindex')){frame.setAttribute('tabindex','0');frame.setAttribute('role','region');frame.setAttribute('aria-label',frame.closest('section')?.querySelector('h2')?.textContent||'Scrollable analysis. Use arrow keys to scroll.');}
   }
  }
  instrument.addEventListener('change',()=>{
   const base=byId('instrument');if(!base||!Object.hasOwn(context.data,instrument.value)){refresh();return}
   if(base.value!==instrument.value){base.value=instrument.value;context.choose()}
   refresh();
  });
  currency.addEventListener('change',()=>{
   const base=byId('currency');if(!base||![...base.options].some(o=>o.value===currency.value)){refresh();return}
   if(base.value!==currency.value){base.value=currency.value;context.refresh()}
   refresh();
  });
  const api={refresh};main._seasonLensQuickControls=api;refresh();return api;
 }
 root.initSeasonLensQuickControls=initSeasonLensQuickControls;
 if(typeof module!=='undefined'&&module.exports)module.exports=initSeasonLensQuickControls;
})(globalThis);
