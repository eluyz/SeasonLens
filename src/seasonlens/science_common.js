/* Pure statistical helpers. Inputs and dates are explicit; nothing is retained. */
(function(root){
'use strict';
function checked(value,label){if(typeof value!=='number'||!Number.isFinite(value))throw Error((label||'Calculation')+' exceeded the finite numeric range.');return value}
function finiteNumber(value){checked(value,'Input');if(Math.abs(value)>1e100||(value!==0&&Math.abs(value)<1e-100))throw Error('Input must be zero or have absolute magnitude between 1e-100 and 1e100.');return value}
function monthDays(y,m){return [31,y%4===0&&(y%100!==0||y%400===0)?29:28,31,30,31,30,31,31,30,31,30,31][m-1]}
function validateDate(date){
 if(typeof date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('An explicit YYYY-MM-DD date is required.');
 const y=+date.slice(0,4),m=+date.slice(5,7),d=+date.slice(8,10);
 if(y<1||m<1||m>12||d<1||d>monthDays(y,m))throw Error('Invalid calendar date: '+date);
 return date;
}
function validateRows(rows,asOf){
 validateDate(asOf);if(!Array.isArray(rows))throw Error('Rows must be an array.');
 const dates=new Set(),copy=rows.map((row,i)=>{
  if(row===null||typeof row!=='object'||Array.isArray(row))throw Error('Invalid observation at row '+(i+1)+'.');
  const date=validateDate(row.date),value=finiteNumber(row.value);
  if(dates.has(date))throw Error('Duplicate observation date: '+date);dates.add(date);return {date,value};
 });
 return copy.filter(row=>row.date<=asOf).sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:0);
}
function numbers(values){if(!Array.isArray(values))throw Error('Numeric values must be an array.');for(const value of values)checked(value,'Statistic input');return values}
function mean(values){
 numbers(values);if(!values.length)return null;
 let scale=0;for(const value of values)scale=Math.max(scale,Math.abs(value));if(!scale)return 0;
 let sum=0,correction=0;for(const value of values){const next=value/scale-correction,total=sum+next;correction=(total-sum)-next;sum=total}
 return checked(sum/values.length*scale,'Mean');
}
function quantile(values,p){
 numbers(values);if(typeof p!=='number'||!Number.isFinite(p)||p<0||p>1)throw Error('Quantile probability must be between 0 and 1.');
 if(!values.length)return null;const sorted=values.slice().sort((a,b)=>a-b),position=(sorted.length-1)*p,index=Math.floor(position),fraction=position-index;
 if(!fraction)return sorted[index];return checked(sorted[index]*(1-fraction)+sorted[index+1]*fraction,'Quantile');
}
function sampleCovariance(a,b){
 numbers(a);numbers(b);if(a.length!==b.length)throw Error('Covariance arrays must have identical lengths.');if(a.length<2)return null;
 let scaleA=0,scaleB=0;for(let i=0;i<a.length;i++){scaleA=Math.max(scaleA,Math.abs(a[i]));scaleB=Math.max(scaleB,Math.abs(b[i]))}if(!scaleA||!scaleB)return 0;
 const x=a.map(v=>v/scaleA),y=b.map(v=>v/scaleB),mx=mean(x),my=mean(y);
 // Work in bounded coordinates and scale only the final covariance.
 const products=x.map((v,i)=>(v-mx)*(y[i]-my));
 return checked(checked(mean(products)*(a.length/(a.length-1))*scaleA,'Covariance')*scaleB,'Covariance');
}
function monthShift(date,months){
 validateDate(date);if(!Number.isSafeInteger(months))throw Error('Month shift must be an integer.');
 const total=(+date.slice(0,4)-1)*12+(+date.slice(5,7)-1)+months;
 if(!Number.isSafeInteger(total)||total<0||total>=9999*12)throw Error('Month shift is outside supported calendar years.');
 const y=Math.floor(total/12)+1,m=total%12+1,d=Math.min(+date.slice(8,10),monthDays(y,m));
 return String(y).padStart(4,'0')+'-'+String(m).padStart(2,'0')+'-'+String(d).padStart(2,'0');
}
function pctChange(current,previous){
 finiteNumber(current);finiteNumber(previous);if(current<=0||previous<=0)return null;
 return checked((current/previous-1)*100,'Percentage change');
}
const api=Object.freeze({validateRows,mean,quantile,sampleCovariance,monthShift,finiteNumber,pctChange,validateDate,checked});
root.SeasonLensScienceCommon=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
