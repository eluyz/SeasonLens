/* The packaged, invented workbook is independent of every user import. */
(function(root){
 'use strict';
 function download(encoded){
  if(typeof encoded!=='string'||!encoded.length||encoded.length>1024*1024||!/^[A-Za-z0-9+/]+={0,2}$/.test(encoded))throw Error('Import template is unavailable.');
  const binary=root.atob(encoded),bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
  if(bytes[0]!==80||bytes[1]!==75||bytes[2]!==3||bytes[3]!==4)throw Error('Import template is not an XLSX workbook.');
  const blob=new root.Blob([bytes],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
  const url=root.URL.createObjectURL(blob),anchor=root.document.createElement('a');
  try{anchor.href=url;anchor.download='seasonlens-import-template.xlsx';root.document.body.append(anchor);anchor.click();}
  finally{anchor.remove();root.setTimeout(()=>root.URL.revokeObjectURL(url),1000);}
 }
 const api=Object.freeze({download});root.SeasonLensTemplate=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(globalThis);
