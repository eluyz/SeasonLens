/* Compare validated local observations without merging, rounding or filling dates. */
(() => {
'use strict';
function compare(older,newer){
 if(!Array.isArray(older?.series)||!Array.isArray(newer?.series)||!older.series.length||older.series.length!==newer.series.length)throw Error('Comparison requires matching validated instrument selections.');
 const series=older.series.map((before,index)=>{
  const after=newer.series[index];
  if(['column','title','unit','role'].some(key=>before[key]!==after[key]))throw Error('Comparison requires matching validated instrument selections.');
  const records=item=>{if(!Array.isArray(item.records)||!item.records.length)throw Error('Comparison requires nonempty validated observations.');const result=new Map();for(const record of item.records){if(typeof record.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(record.date)||typeof record.value!=='number'||!Number.isFinite(record.value)||result.has(record.date))throw Error('Comparison requires unique dates and finite validated prices.');result.set(record.date,record.value)}return result};
  const oldRecords=records(before),newRecords=records(after),counts={new:0,corrected:0,absent:0,unchanged:0},changes=[];
  for(const date of [...new Set([...oldRecords.keys(),...newRecords.keys()])].sort()){
   const hasOld=oldRecords.has(date),hasNew=newRecords.has(date),oldValue=hasOld?oldRecords.get(date):null,newValue=hasNew?newRecords.get(date):null;
   const kind=!hasOld?'new':!hasNew?'absent':oldValue===newValue?'unchanged':'corrected';counts[kind]++;
   if(kind!=='unchanged'){const difference=hasOld&&hasNew?newValue-oldValue:null;if(difference!==null&&!Number.isFinite(difference))throw Error('Comparison difference exceeds the supported numeric range.');changes.push({date,kind,older:oldValue,newer:newValue,difference});}
  }
  const oldDates=[...oldRecords.keys()].sort(),newDates=[...newRecords.keys()].sort();
  return {column:before.column,title:before.title,unit:before.unit,role:before.role,olderCount:oldRecords.size,newerCount:newRecords.size,olderFirstDate:oldDates[0],olderLastDate:oldDates.at(-1),newerFirstDate:newDates[0],newerLastDate:newDates.at(-1),counts,changes,olderBlankRows:[...before.skippedBlankRows],olderFutureRows:[...before.skippedFutureRows],newerBlankRows:[...after.skippedBlankRows],newerFutureRows:[...after.skippedFutureRows]};
 });
 return {series,olderSummary:{...older.summary},newerSummary:{...newer.summary}};
}
globalThis.SeasonLensImportComparison=Object.freeze({compare});
})();
