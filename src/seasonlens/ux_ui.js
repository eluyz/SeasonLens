/* Browser preferences contain display settings only, never user observations. */
(function (global) {
 'use strict';
 const KEY='seasonlens.view.v1';
 const BUILTINS=['SYNTHETIC_GRAIN','SYNTHETIC_CORN','SYNTHETIC_RAPESEED','EUR_PLN','EUR_USD','USD_PLN'];
 const VALUES={currency:['Original','PLN/t'],range:['12m','90','all'],'correlation-window':['20','60','120'],'distribution-years':['5','10'],'comparison-range':['12m','90','all'],'comparison-units':['Original','PLN/t']};
 const CHECKS=['price','sma20','sma100','sma200','bollinger_upper','bollinger_lower','baseline','current','band'];
 const DETAILS=['ux-risk','ux-relations','ux-seasonal','ux-help-percentile','ux-help-rsi','ux-help-correlation','ux-help-bollinger','ux-help-volatility','ux-help-seasonality','ux-data-notes'];
 function object(value){return value!==null&&typeof value==='object'&&!Array.isArray(value)}
 function sanitize(input){
  if(!object(input)||input.version!==1)return null;
  const out={version:1};
  if(BUILTINS.includes(input.instrument))out.instrument=input.instrument;
  for(const [id,choices] of Object.entries(VALUES))if(choices.includes(input[id]))out[id]=input[id];
  for(const id of CHECKS)if(typeof input[id]==='boolean')out[id]=input[id];
  if(Array.isArray(input.comparison))out.comparison=BUILTINS.filter(id=>input.comparison.includes(id));
  if(object(input.details)){out.details={};for(const id of DETAILS)if(typeof input.details[id]==='boolean')out.details[id]=input.details[id]}
  return out;
 }
 function read(storage){try{const raw=storage.getItem(KEY);return raw&&raw.length<=8192?sanitize(JSON.parse(raw)):null}catch(_){return null}}
 function write(storage,input){try{const safe=sanitize(input);if(!safe)return false;storage.setItem(KEY,JSON.stringify(safe));return true}catch(_){return false}}
 function technicalMessages(rows){
  const n=rows.length,last=n?rows[n-1]:null,messages=[];
  for(const [label,key,count] of [['SMA20','sma20',20],['SMA100','sma100',100],['SMA200','sma200',200],['Bollinger bands','bollinger_upper',20]]){
   if(n<count)messages.push(`${label} needs ${count} observed prices; this view has ${n}. ${count-n} more observations are needed.`);
   else if(!Number.isFinite(last[key]))messages.push(`${label} is unavailable at the last observation. Check the selected data view and its numeric range.`);
  }
  return messages;
 }
 global.SeasonLensUXPreferences=Object.freeze({key:KEY,sanitize,read,write,technicalMessages});
 global.initSeasonLensUX=function(context){
  if(document.getElementById('seasonlens-navigation'))return;
  const byId=id=>document.getElementById(id),getData=()=>context.data;
  const builtin=id=>BUILTINS.includes(id)&&getData()[id]?.source==='SYNTHETIC';
  const make=(tag,text,className)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(className)n.className=className;return n};
  const nav=make('nav',null,'ux-navigation');nav.id='seasonlens-navigation';nav.setAttribute('aria-label','Analysis sections');
  for(const [id,text] of [['market-overview','Overview'],['prices-seasonality','Prices and seasonality'],['technical-analysis','Technical analysis'],['market-comparison','Market comparisons'],['browser-import-panel','Import data']]){
   const a=make('a',text);a.href='#'+id;nav.append(a);
  }
  const top=document.querySelector('.top');if(top)top.after(nav);else document.querySelector('main').prepend(nav);
  function reveal(id,focus){const target=byId(id);if(!target)return;for(let p=target.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;target.scrollIntoView({behavior:global.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});if(focus){target.setAttribute('tabindex','-1');target.focus({preventScroll:true})}}
  nav.addEventListener('click',event=>{const a=event.target.closest('a');if(!a)return;const id=a.hash.slice(1);if(!byId(id))return;event.preventDefault();try{global.history.replaceState(null,'','#'+id)}catch(_){}reveal(id,true)});
  global.addEventListener('hashchange',()=>reveal(global.location.hash.slice(1),false));
  const help=[
   ['percentile','market-cards','What does the historical percentile mean?','A percentile places the latest price among the observed prices in the stated history. Around 90% means the price is higher than most observations; it does not mean there is a 90% chance of a fall. Equal prices receive half weight. The current price is included.'],
   ['rsi','rsi-chart','How do I read RSI?','RSI summarizes recent upward and downward price changes on a 0–100 scale. Dashed 30 and 70 lines are reference levels, not automatic trading signals. RSI14 needs 14 price changes (15 observations); flat price histories produce 50.'],
   ['correlation','correlation-chart','How do I read correlation?','Values near +1 mean the matched percentage changes moved in a similar direction; near −1 means opposite directions; near 0 means weak linear association. A full selected window of matching date intervals is required. A constant history has no defined correlation. This is not proof of causation.'],
   ['bollinger','daily','What are the six technical lines?','Price is the observed value. SMA20, SMA100 and SMA200 average the latest 20, 100 and 200 observed prices. Bollinger upper and lower are SMA20 plus or minus twice the 20-observation population standard deviation. Their width describes recent price dispersion; it is not a forecast range. Earlier history warms up the lines before the displayed period.'],
   ['volatility','volatility-chart','What does historical volatility measure?','The 20 and 60 lines measure dispersion of observed log price changes, expressed as an unannualized percentage. Higher values mean more variable changes over that window. Windows require positive prices and respectively 21 or 61 prices. Missing calendar days are not inserted.'],
   ['seasonality','distribution-chart','What does the shaded seasonal range mean?','Each available completed year contributes one monthly average with equal weight. The median is the middle value; the shaded band covers the 25th to 75th percentile of yearly monthly averages. It describes historical monthly averages, not daily extremes or a forecast. Missing years reduce the contributor count.']
  ];
  for(const [id,hostId,title,text] of help){const host=byId(hostId);if(!host)continue;const d=make('details',null,'ux-help');d.id='ux-help-'+id;d.append(make('summary',title),make('p',text));const heading=host.closest('section')?.querySelector('h2');if(heading)heading.after(d);else host.before(d)}
  for(const [id,host] of [['ux-risk','rsi-chart'],['ux-relations','correlation-chart'],['ux-seasonal','distribution-chart']]){const detail=byId(host)?.closest('details.market-advanced');if(detail)detail.id=id}
  const notes=make('details',null,'ux-help ux-data-notes');notes.id='ux-data-notes';notes.append(make('summary','Why do some values show —?'),make('p','A dash means a value is unavailable, not zero. Future months are after the selected analysis cutoff. Historical gaps mean no observations were supplied for that month. Monthly changes require the immediately preceding calendar month; technical indicators need a complete observation window. Counts measure supplied observations and do not certify a complete trading calendar. Table tooltips provide the date, count or missing-data reason where available.'));
  byId('quality')?.after(notes);
  const availability=make('div',null,'ux-availability');availability.id='technical-availability';availability.setAttribute('role','status');availability.setAttribute('aria-live','polite');byId('daily')?.before(availability);
  function updateAvailability(){let selected;try{selected=context.view()}catch(_){return}const rows=selected?.daily||[],messages=technicalMessages(rows);availability.replaceChildren();if(messages.length){availability.append(make('strong','Technical indicator coverage'));const list=make('ul');for(const message of messages)list.append(make('li',message));availability.append(list)}else if(rows.length)availability.append(make('p',`All six technical lines are available at the last observation (${rows[rows.length-1].date}). Their earlier portions may have warmup gaps.`));else availability.append(make('p','There are no observations on or before this analysis cutoff. Select another data view or import observations.'))}
  const toolbar=make('div',null,'ux-preferences');const reset=make('button','Reset view settings','secondary');reset.type='button';reset.id='reset-view-preferences';const status=make('span','Only view settings are remembered. Imported data, file details and scenario values are never saved.','muted');status.id='view-preferences-status';status.setAttribute('role','status');toolbar.append(reset,status);nav.after(toolbar);
  let storage;try{storage=global.localStorage}catch(_){}if(!storage)status.textContent='View settings are unavailable in this browser. Imported data remains in this tab only.';
  let previous=null,restoring=false;
  function capture(){const settings={version:1};const selected=byId('instrument')?.value;if(builtin(selected))settings.instrument=selected;else if(builtin(previous?.instrument))settings.instrument=previous.instrument;
   for(const id of Object.keys(VALUES)){const node=byId(id);if(node)settings[id]=node.value}
   for(const id of CHECKS){const node=byId(id);if(node)settings[id]=node.checked}
   settings.comparison=[...(byId('comparison-instruments')?.querySelectorAll('input:checked')||[])].map(n=>n.value).filter(builtin);
   settings.details={};for(const id of DETAILS){const node=byId(id);if(node)settings.details[id]=node.open}return sanitize(settings);
  }
  const defaults=capture();
  function restore(input){const settings=sanitize(input);if(!settings)return;restoring=true;try{
   if(builtin(settings.instrument)&&byId('instrument')){byId('instrument').value=settings.instrument;context.choose()}
   for(const [id,allowed] of Object.entries(VALUES)){const node=byId(id);if(!node||!allowed.includes(settings[id]))continue;if(node.tagName==='SELECT'&&![...node.options].some(o=>o.value===settings[id]))continue;node.value=settings[id]}
   for(const id of CHECKS){const node=byId(id);if(node&&typeof settings[id]==='boolean')node.checked=settings[id]}
   if(settings.comparison)for(const node of byId('comparison-instruments')?.querySelectorAll('input')||[])if(builtin(node.value))node.checked=settings.comparison.includes(node.value);
   for(const [id,open] of Object.entries(settings.details||{})){const node=byId(id);if(node)node.open=open}
   context.refresh();updateAvailability();
  }finally{restoring=false}}
  if(storage){const saved=read(storage);if(saved){previous=saved;restore(saved)}}
  function remember(){if(restoring)return;updateAvailability();previous=capture();if(storage&&!write(storage,previous))status.textContent='View settings could not be saved in this browser. Imported data remains in this tab only.'}
  const tracked=new Set(['instrument',...Object.keys(VALUES),...CHECKS]);
  document.addEventListener('change',event=>{if(tracked.has(event.target.id)||event.target.closest('#comparison-instruments'))remember()});
  for(const id of DETAILS)byId(id)?.addEventListener('toggle',remember);
  reset.addEventListener('click',()=>{try{storage?.removeItem(KEY)}catch(_){}previous=null;restore(defaults);previous=defaults;status.textContent='View settings reset. Imported data in this tab has been retained.'});
  if(global.MutationObserver&&byId('quality'))new MutationObserver(updateAvailability).observe(byId('quality'),{childList:true,subtree:true});
  updateAvailability();if(global.location.hash)reveal(global.location.hash.slice(1),false);
 };
})(globalThis);
