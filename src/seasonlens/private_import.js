function browserInstallEntries(entries) {
 if (!Array.isArray(entries) || !entries.length) throw Error('No validated instruments are ready.');
 const group = entries[0].import_group;
 if (!group || entries.some(s => s.source !== 'USER_FILE' || s.import_group !== group || !s.views?.Original)) throw Error('Invalid private import group.');
 const fx = entries.find(s => s.role === 'eur_pln' && s.unit === 'PLN per EUR');
 for (const entry of entries) {
  const original = entry.views.Original, asOf = original.as_of;
  original.market = SeasonLensMarketMath.buildMarket(original.daily, asOf);
  original.conversion_note = 'Private '+(entry.source_format==='XLSX'?'Excel':'CSV')+' observations stay in this tab. No provider provenance is assigned.';
  if (entry.unit === 'EUR/t' && fx) {
   const rates = new Map(fx.views.Original.daily.filter(r => r.date <= asOf).map(r => [r.date, r.value]));
   const prices = original.daily, matched = prices.filter(r => rates.has(r.date) && r.value > 0 && rates.get(r.date) > 0);
   if (matched.length) {
    const converted = matched.map(r => ({date:r.date, value:r.value*rates.get(r.date)}));
    const view = SeasonLensBrowser.buildView(converted, {unit:'PLN/t', asOf, originalAllPositive:true});
    view.market = SeasonLensMarketMath.buildMarket(view.daily, asOf);
    view.conversion_note = `Private same-workbook conversion: ${entry.title} × ${fx.title}. ${matched.length} exact-date positive pairs; ${prices.length-matched.length} commodity observations not converted. No quotes carried forward.`;
    entry.views['PLN/t'] = view;
    original.conversion_note += ' PLN/t view is available using the declared EUR/PLN column from this same workbook.';
   } else original.conversion_note = 'No positive exact-date pairs with the declared private EUR/PLN series. Original observations remain available.';
  }
 }
 const ids = entries.map((_,i) => 'USER_FILE_'+Date.now()+'_'+Object.keys(data).length+'_'+i);
 if (ids.some(id => Object.hasOwn(data,id))) throw Error('Import identifier collision. Please validate again.');
 entries.forEach((entry,i) => {
  data[ids[i]] = entry;
  const option = document.createElement('option'); option.value=ids[i];
  option.textContent=entry.title+' · private '+(entry.source_format === 'XLSX' ? 'Excel' : 'CSV'); el('instrument').append(option);
 });
 el('instrument').value=ids[0];
 for(const name of ['instrument','currency','range','export','price','sma20','sma100','sma200','bollinger_upper','bollinger_lower']) el(name).disabled=false;
 marketInitialize(); choose();
 return ids;
}
function marketFXId(s) {
 if (s.unit !== 'EUR/t') return null;
 if (s.source === 'USER_FILE') {
  if (!s.import_group) return null;
  const matches = Object.keys(data).filter(id => data[id].source==='USER_FILE' && data[id].import_group===s.import_group && data[id].role==='eur_pln' && data[id].unit==='PLN per EUR');
  return matches.length===1 ? matches[0] : null;
 }
 const f=data.EUR_PLN;
 if(f?.unit!=='PLN per EUR') return null;
 return ((f.source==='ECB_REFERENCE'&&s.source!=='SYNTHETIC')||(f.source==='SYNTHETIC'&&s.source==='SYNTHETIC')) ? 'EUR_PLN' : null;
}
