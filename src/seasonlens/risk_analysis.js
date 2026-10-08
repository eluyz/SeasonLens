/* Descriptive historical benchmark risk. Observed intervals are not trading days. */
(function(root){
'use strict';
const C=root.SeasonLensScienceCommon||(typeof require==='function'?require('./science_common.js'):null);
if(!C)throw Error('SeasonLensScienceCommon must load before historical risk.');
function horizonOption(horizon){if(![1,5,20].includes(horizon))throw Error('Risk horizon must be 1, 5 or 20 observed intervals.');return horizon}
function prepare(rows,asOf,horizon){
 horizonOption(horizon);const visible=C.validateRows(rows,asOf),intervals=[],omissions=[];
 for(let i=horizon;i<visible.length;i++){
  const first=visible[i-horizon],last=visible[i],change=C.pctChange(last.value,first.value);
  if(change===null)omissions.push({start:first.date,end:last.date,reason:'nonpositive_endpoint'});
  else intervals.push({start:first.date,end:last.date,observedIntervals:horizon,change});
 }
 return {visible,intervals,omissions,counts:{observations:visible.length,candidateIntervals:Math.max(0,visible.length-horizon),validIntervals:intervals.length,nonpositiveEndpoints:omissions.length,excludedFuture:rows.length-visible.length}};
}
function histogram(changes){
 if(!changes.length)return [];let lower=changes[0],upper=changes[0];for(const v of changes){lower=Math.min(lower,v);upper=Math.max(upper,v)}
 if(lower===upper)return [{lower,upper,count:changes.length}];
 const count=Math.min(10,Math.ceil(Math.sqrt(changes.length))),bins=Array.from({length:count},(_,i)=>({lower:lower*(1-i/count)+upper*(i/count),upper:lower*(1-(i+1)/count)+upper*((i+1)/count),count:0}));
 for(const value of changes){let index=Math.floor((value-lower)/(upper-lower)*count);index=Math.min(count-1,Math.max(0,index));bins[index].count++}return bins;
}
function historicalRisk(rows,options){
 if(!options||typeof options!=='object')throw Error('Explicit risk options are required.');
 const {asOf,horizon,confidence,direction}=options;
 if(![.95,.99].includes(confidence))throw Error('Confidence must be 0.95 or 0.99.');
 if(!['buyer','seller'].includes(direction))throw Error('Direction must be buyer or seller.');
 const prepared=prepare(rows,asOf,horizon),sign=direction==='buyer'?1:-1,intervals=prepared.intervals.map(row=>({...row,loss:row.change*sign})),changes=intervals.map(row=>row.change),losses=intervals.map(row=>row.loss).sort((a,b)=>a-b);
 // Exact integer denominators avoid subtraction/product roundoff at integer
 // tail boundaries, including precisely 100/500 intervals.
 const tailMass=losses.length/(confidence===.95?20:100),available=losses.length>=(confidence===.95?100:500);
 let valueAtRisk=null,expectedShortfall=null;
 if(available){
  valueAtRisk=losses[Math.ceil(confidence*losses.length)-1];
  const whole=Math.floor(tailMass),fraction=tailMass-whole,tail=losses.slice(losses.length-whole);
  // Weighted mean with exactly the fractional boundary mass, including ties and signs.
  const scale=losses.reduce((maximum,value)=>Math.max(maximum,Math.abs(value)),0);
  if(!scale)expectedShortfall=0;
  else {const normalized=tail.map(value=>value/scale),boundary=fraction?losses[losses.length-whole-1]/scale*fraction:0;expectedShortfall=C.checked(((C.mean(normalized)||0)*whole+boundary)/tailMass*scale,'Expected shortfall')}
 }
 return {asOf,horizon,confidence,direction,counts:prepared.counts,omissions:prepared.omissions,intervals,meanChange:C.mean(changes),medianChange:C.quantile(changes,.5),var:valueAtRisk,expectedShortfall,tailMass,available,unavailableReason:available?null:'At least five observations of tail mass are required ('+(confidence===.95?100:500)+' valid intervals).',histogram:histogram(changes),overlapping:horizon>1};
}
function stressEpisodes(rows,options){
 if(!options||typeof options!=='object')throw Error('Explicit stress options are required.');
 const {asOf,horizon}=options,prepared=prepare(rows,asOf,horizon);
 let peak=null,trough=null,maxDecline=null,maxRise=null,breaks=0;
 for(let i=0;i<prepared.visible.length;i++){
  const row=prepared.visible[i];if(row.value<=0){peak=null;trough=null;breaks++;continue}
  if(peak!==null){
   const decline={start:peak.row.date,end:row.date,observedIntervals:i-peak.index,change:C.pctChange(row.value,peak.row.value)};
   const rise={start:trough.row.date,end:row.date,observedIntervals:i-trough.index,change:C.pctChange(row.value,trough.row.value)};
   if(decline.change<=0&&(maxDecline===null||decline.change<maxDecline.change))maxDecline=decline;
   if(rise.change>=0&&(maxRise===null||rise.change>maxRise.change))maxRise=rise;
  }
  if(peak===null||row.value>peak.row.value)peak={row,index:i};if(trough===null||row.value<trough.row.value)trough={row,index:i};
 }
 return {asOf,horizon,counts:prepared.counts,omissions:prepared.omissions,nonpositivePathBreaks:breaks,largestRises:prepared.intervals.filter(row=>row.change>0).sort((a,b)=>b.change-a.change).slice(0,5),largestFalls:prepared.intervals.filter(row=>row.change<0).sort((a,b)=>a.change-b.change).slice(0,5),maxDecline,maxRise};
}
function logIntervals(rows){
 const intervals=[],omissions=[];
 for(let i=1;i<rows.length;i++){
  const first=rows[i-1],last=rows[i];if(first.value<=0||last.value<=0){omissions.push({start:first.date,end:last.date,reason:'nonpositive_endpoint'});continue}
  // log ratio is accurate for nearby prices; subtraction covers extreme ratios safely.
  const relative=(last.value-first.value)/first.value;
  const change=C.checked((Math.abs(relative)<.5?Math.log1p(relative):Math.log(last.value)-Math.log(first.value))*100,'Log change');
  intervals.push({start:first.date,end:last.date,change});
 }return {intervals,omissions};
}
function fxRisk(commodityRows,fxRows,options){
 if(!options||typeof options!=='object')throw Error('Explicit FX risk options are required.');
 const {asOf}=options,commodity=C.validateRows(commodityRows,asOf),fx=C.validateRows(fxRows,asOf),c=logIntervals(commodity),f=logIntervals(fx),quotes=new Map(f.intervals.map(row=>[row.start+'|'+row.end,row])),intervals=[];
 for(const row of c.intervals){const paired=quotes.get(row.start+'|'+row.end);if(paired)intervals.push({start:row.start,end:row.end,commodityLogChange:row.change,fxLogChange:paired.change,totalLogChange:C.checked(row.change+paired.change,'Combined log change')})}
 const x=intervals.map(row=>row.commodityLogChange),y=intervals.map(row=>row.fxLogChange),z=intervals.map(row=>row.totalLogChange),varCommodity=C.sampleCovariance(x,x),varFX=C.sampleCovariance(y,y),covariance=C.sampleCovariance(x,y);
 // Equivalent var(x+y) is stable under near-perfect cancellation; never invent a positive variance.
 const totalVar=C.sampleCovariance(z,z),available=intervals.length>=2;
 // cov(x,x+y) equals var(x)+cov(x,y), but avoids subtracting two large
 // nearly equal component variances when the currency hedges the commodity.
 const commodityContribution=available?C.sampleCovariance(x,z):null,fxContribution=available?C.sampleCovariance(y,z):null;
 // Price-to-log conversion has a finite resolution. Preserve the computed
 // variance, but do not turn rounding noise in a constant combined path into
 // giant shares. Genuine small variation above this bound remains visible.
 let componentScale=100;for(let i=0;i<x.length;i++)componentScale=Math.max(componentScale,Math.abs(x[i]),Math.abs(y[i]));
 const numericalResolution=32*Number.EPSILON*componentScale;
 const sharesAvailable=available&&totalVar>numericalResolution*numericalResolution;
 const commodityShare=sharesAvailable?C.checked(commodityContribution/totalVar*100,'Commodity variance share'):null,fxShare=sharesAvailable?C.checked(fxContribution/totalVar*100,'FX variance share'):null;
 return {asOf,counts:{commodityObservations:commodity.length,fxObservations:fx.length,commodityIntervals:c.intervals.length,fxIntervals:f.intervals.length,pairedIntervals:intervals.length,commodityNonpositiveEndpoints:c.omissions.length,fxNonpositiveEndpoints:f.omissions.length,commodityExcludedFuture:commodityRows.length-commodity.length,fxExcludedFuture:fxRows.length-fx.length},intervals,omissions:{commodity:c.omissions,fx:f.omissions},varCommodity,varFX,covariance,totalVar,commodityContribution,fxContribution,commodityShare,fxShare,available,sharesAvailable,numericalResolution,unavailableReason:!available?'At least two exact matching original-source intervals are required.':totalVar===0?'Combined log changes are constant; variance shares are undefined.':!sharesAvailable?'Combined variability is below floating-point resolution; variance shares are undefined.':null};
}
const api=Object.freeze({historicalRisk,stressEpisodes,fxRisk});root.SeasonLensRisk=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
