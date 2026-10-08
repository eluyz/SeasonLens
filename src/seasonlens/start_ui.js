/* Optional onboarding. Navigation and template downloads never read observations. */
(function(root){
 'use strict';
 function initSeasonLensStartGuide(context={}){
  const doc=root.document,host=doc?.getElementById('seasonlens-start');
  if(!host)return {navigate(){return false}};
  if(host._seasonLensStartGuide)return host._seasonLensStartGuide;
  const byId=id=>doc.getElementById(id);
  function navigate(id){
   const destination=byId(id);if(!destination)return false;
   const target=id==='fiveyear'?(destination.closest('section')||destination):destination;
   for(let node=target;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
   const heading=target.querySelector('h2,summary')||target;
   if(!heading.hasAttribute('tabindex')){heading.setAttribute('tabindex','-1');heading.addEventListener('blur',()=>heading.removeAttribute('tabindex'),{once:true})}
   heading.focus({preventScroll:true});
   try{root.history?.replaceState(null,'','#'+id)}catch(_){}
   target.scrollIntoView({behavior:root.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches?'auto':'smooth',block:'start'});
   return true;
  }
  for(const [button,id]of [['start-explore','fiveyear'],['start-monthly','prices-seasonality'],['start-import','browser-import-panel'],['start-report','report-export-panel']]){
   byId(button)?.addEventListener('click',event=>{if(navigate(id))event.preventDefault()});
  }
  const template=byId('start-template'),status=byId('start-template-status');
  if(template&&status){
   const available=typeof context.downloadTemplate==='function';template.disabled=!available;
   status.textContent=available?'Includes six invented example series and a mapping guide.':'Template unavailable in this build. You can still import your own XLSX or CSV.';
   let pending=false;
   template.addEventListener('click',async()=>{
    if(!available||pending)return;pending=true;template.disabled=true;
    try{
     await context.downloadTemplate();
     status.textContent='Template download requested. Open the workbook instructions, then preview and validate it before adding.';
    }catch(_){status.textContent='The template could not be downloaded. Try again, or import your own XLSX or CSV.'}
    finally{pending=false;template.disabled=false}
   });
  }
  const api={navigate};host._seasonLensStartGuide=api;return api;
 }
 root.initSeasonLensStartGuide=initSeasonLensStartGuide;
 if(typeof module!=='undefined'&&module.exports)module.exports=initSeasonLensStartGuide;
})(globalThis);
