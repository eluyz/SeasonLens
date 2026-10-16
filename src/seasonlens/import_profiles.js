/* Explicit local XLSX configuration files. Observation arrays are never copied. */
(() => {
'use strict';
const MAX_BYTES=65536,FORMAT='seasonlens-import-profile',VERSION=1;
const units=['EUR/t','PLN/t','USD/t','PLN per EUR','USD per EUR','PLN per USD','Input units'];
const roleUnits={custom:units,wheat:['EUR/t','PLN/t'],corn:['EUR/t','PLN/t'],rapeseed:['EUR/t','PLN/t'],eur_pln:['PLN per EUR'],eur_usd:['USD per EUR'],usd_pln:['PLN per USD']};
const fail=message=>{throw Error(message)};
function object(value,keys){if(!value||typeof value!=='object'||Array.isArray(value)||Object.getPrototypeOf(value)!==Object.prototype||Object.keys(value).length!==keys.length||!keys.every(key=>Object.hasOwn(value,key)))fail('Import profile has missing or unsupported fields.');}
function text(value,max,empty=false){if(typeof value!=='string'||value.length>max||(!empty&&!value.trim()))fail('Import profile contains invalid text fields.');return value;}
function column(value){if(typeof value!=='string'||!/^[A-Z]{1,3}$/.test(value))fail('Import profile contains an invalid column letter.');return value;}
function guard(value){object(value,['column','header']);return {column:column(value.column),header:text(value.header,4096,true)};}
function validate(value){
 object(value,['format','version','kind','worksheet','headerRow','startRow','date','mappings','decimal','dateFormat']);
 if(value.format!==FORMAT||value.version!==VERSION||value.kind!=='XLSX')fail('Unsupported import profile format or version.');
 const worksheet=text(value.worksheet,31);
 if(!Number.isInteger(value.headerRow)||!Number.isInteger(value.startRow)||value.headerRow<1||value.headerRow>1000||value.startRow<=value.headerRow||value.startRow>1001)fail('Import profile contains invalid physical row numbers.');
 if(!['.',','].includes(value.decimal)||!['ISO','DD.MM.YYYY'].includes(value.dateFormat))fail('Import profile contains unsupported number or date formats.');
 const date=guard(value.date),seenColumns=new Set([date.column]),seenTitles=new Set(),seenRoles=new Set();
 if(!Array.isArray(value.mappings)||!value.mappings.length||value.mappings.length>20)fail('Import profile must select between 1 and 20 price columns.');
 const mappings=value.mappings.map(item=>{
  object(item,['column','header','title','unit','role']);const selected={column:column(item.column),header:text(item.header,4096,true),title:text(item.title,150),unit:text(item.unit,100),role:text(item.role,20)};
  if(selected.title!==selected.title.trim()||seenTitles.has(selected.title)||seenColumns.has(selected.column))fail('Import profile contains repeated columns or titles.');
  if(!Object.hasOwn(roleUnits,selected.role)||!roleUnits[selected.role].includes(selected.unit)||selected.role!=='custom'&&seenRoles.has(selected.role))fail('Import profile contains incompatible units or repeated roles.');
  seenColumns.add(selected.column);seenTitles.add(selected.title);seenRoles.add(selected.role);return selected;
 });
 return {format:FORMAT,version:VERSION,kind:'XLSX',worksheet,headerRow:value.headerRow,startRow:value.startRow,date,mappings,decimal:value.decimal,dateFormat:value.dateFormat};
}
function size(text){if(new TextEncoder().encode(text).byteLength>MAX_BYTES)fail('Import profile exceeds the 64 KiB limit.');}
function parse(text){if(typeof text!=='string')fail('Import profile must be a JSON text file.');size(text);let value;try{value=JSON.parse(text)}catch(error){fail('Import profile is not valid JSON.');}return validate(value);}
function serialize(profile){const result=JSON.stringify(validate(profile),null,2)+'\n';size(result);return result;}
function header(workbook,worksheet,row,columnName){
 const cell=workbook.Sheets[worksheet][columnName+row],value=cell?.v;
 const result=value instanceof Date?(Number.isFinite(value.getTime())?value.toISOString():'Invalid date'):value===undefined||value===null?'':String(value);
 return text(result,4096,true);
}
function checkCompatibility(workbook,value){
 const profile=validate(value);
 if(!workbook?.SheetNames?.includes(profile.worksheet))fail('Profile worksheet is unavailable. Choose the correct workbook or configure the import manually.');
 const info=SeasonLensWorkbook.inspectSheet(workbook,profile.worksheet,profile),available=new Set(info.columns.map(item=>item.column));
 for(const selected of [profile.date,...profile.mappings])if(!available.has(selected.column)||header(workbook,profile.worksheet,profile.headerRow,selected.column)!==selected.header)fail('Profile columns or headers have changed. Review the worksheet and configure the import manually.');
 return profile;
}
function capture(workbook,worksheet,settings){
 const profile={format:FORMAT,version:VERSION,kind:'XLSX',worksheet,headerRow:settings.headerRow,startRow:settings.startRow,date:{column:settings.dateColumn,header:header(workbook,worksheet,settings.headerRow,settings.dateColumn)},mappings:settings.mappings.map(item=>({column:item.column,header:header(workbook,worksheet,settings.headerRow,item.column),title:item.title,unit:item.unit,role:item.role})),decimal:settings.decimal,dateFormat:settings.dateFormat};
 const compatible=checkCompatibility(workbook,profile);serialize(compatible);return compatible;
}
globalThis.SeasonLensImportProfiles=Object.freeze({MAX_BYTES,capture,parse,serialize,checkCompatibility});
})();
