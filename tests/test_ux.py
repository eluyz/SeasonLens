"""Bounded browser-preference tests; no actual observation is persisted."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

MODULE = Path(__file__).parents[1] / "src/seasonlens/ux_ui.js"

DOM = r"""
const all=[], events={};
class Element {
 constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.attrs={};this.events={};this.value='';this.checked=false;this.open=false;this.id='';this.className='';this.textContent='';all.push(this)}
 append(...nodes){for(const n of nodes){n.parentElement=this;this.children.push(n)}}
 prepend(n){n.parentElement=this;this.children.unshift(n)}
 after(n){const p=this.parentElement;n.parentElement=p;p.children.splice(p.children.indexOf(this)+1,0,n)}
 before(n){const p=this.parentElement;n.parentElement=p;p.children.splice(p.children.indexOf(this),0,n)}
 replaceChildren(...nodes){this.children=[];this.append(...nodes)}
 setAttribute(k,v){this.attrs[k]=v}
 addEventListener(k,v){(this.events[k]??=[]).push(v)}
 fire(k,event={}){for(const f of this.events[k]||[])f({target:this,...event})}
 matches(s){if(s==='a')return this.tagName==='A';if(s[0]==='#')return this.id===s.slice(1);if(s[0]==='.')return this.className.split(' ').includes(s.slice(1));if(s==='input:checked')return this.tagName==='INPUT'&&this.checked;if(s==='details.market-advanced')return this.tagName==='DETAILS'&&this.className==='market-advanced';return this.tagName===s.toUpperCase()}
 querySelectorAll(s){return this.children.flatMap(n=>[...(n.matches(s)?[n]:[]),...n.querySelectorAll(s)])}
 querySelector(s){return this.querySelectorAll(s)[0]||null}
 closest(s){for(let n=this;n;n=n.parentElement)if(n.matches(s))return n;return null}
 scrollIntoView(){this.scrolled=true}
 focus(){this.focused=true}
 get options(){return this.children}
 get hash(){return this.href?.slice(this.href.indexOf('#'))||''}
}
globalThis.document={createElement:t=>new Element(t),getElementById:id=>all.find(n=>n.id===id)||null,querySelector:s=>all.find(n=>n.matches(s))||null,addEventListener:(k,v)=>(events[k]??=[]).push(v)};
globalThis.addEventListener=()=>{};globalThis.location={hash:''};globalThis.history={replaceState(...a){location.hash=a[2]}};
const store=new Map([['unrelated','keep'],['seasonlens.view.v1',JSON.stringify(input.saved||{})]]);
globalThis.localStorage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
const add=(id,tag='div',parent)=>{const n=new Element(tag);n.id=id;if(parent)parent.append(n);return n};
const main=add('main','main'),top=add('top','div',main);top.className='top';
for(const id of ['market-overview','prices-seasonality','technical-analysis','market-comparison','browser-import-panel'])add(id,'section',main).append(new Element('h2'));
const details=[];for(const [id,host] of [['risk','rsi-chart'],['relations','correlation-chart'],['seasonal','distribution-chart']]){const d=add(id,'details',main);d.className='market-advanced';d.open=id==='risk';details.push(d);const s=add(id+'-section','section',d);s.append(new Element('h2'));add(host,'div',s)}
for(const [id,parent] of [['market-cards','market-overview'],['daily','technical-analysis'],['volatility-chart','risk-section']])add(id,'div',document.getElementById(parent));
add('quality','div',main);add('comparison-instruments','div',document.getElementById('market-comparison'));
const ids=['SYNTHETIC_GRAIN','EUR_PLN','user_import_secret.csv'];
const data=Object.fromEntries(ids.map(id=>[id,{source:id.startsWith('user_')?'USER_FILE':'SYNTHETIC',title:id.startsWith('user_')?'Secret title':'Built in',views:{Original:{daily:[{date:'2026-01-01',value:123.987}],observations:1},...(id==='SYNTHETIC_GRAIN'?{'PLN/t':{daily:[]}}:{})}}]));
const select=(id,values,initial)=>{const n=add(id,'select',main);for(const value of values){const o=new Element('option');o.value=value;n.append(o)}n.value=initial||values[0];return n};
select('instrument',ids);select('currency',['Original','PLN/t']);select('range',['12m','90','all']);select('correlation-window',['60','20','120']);select('distribution-years',['5','10']);select('comparison-range',['12m','90','all']);select('comparison-units',['Original','PLN/t']);
for(const id of ['price','sma20','sma100','sma200','bollinger_upper','bollinger_lower','baseline','current','band']){const n=add(id,'input',main);n.checked=true}
for(const id of ids){const n=add('check-'+id,'input',document.getElementById('comparison-instruments'));n.value=id;n.checked=true}
let chooses=0,refreshes=0;
const context={data,view:()=>data[document.getElementById('instrument').value].views[document.getElementById('currency').value],choose(){chooses++;const n=document.getElementById('currency');n.replaceChildren();for(const value of Object.keys(data[document.getElementById('instrument').value].views)){const o=new Element('option');o.value=value;n.append(o)}n.value='Original'},refresh(){refreshes++}};
const change=id=>{const node=document.getElementById(id);for(const f of events.change||[])f({target:node})};
"""


@unittest.skipUnless(shutil.which("node"), "Node is required for browser checks")
class UXTests(unittest.TestCase):
    def run_node(self, code, payload=None, dom=False):
        script = "const input=JSON.parse(require('fs').readFileSync(0,'utf8'));" + (DOM if dom else "")
        script += "require(process.argv[1]);const api=globalThis.SeasonLensUXPreferences;" + code
        r = subprocess.run(["node", "-e", script, str(MODULE)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(r.stdout)

    def test_persistence_projects_only_approved_view_fields(self):
        candidate = dict(version=1, instrument="user_import_secret.csv", currency="PLN/t", range="90", price=False,
                         comparison=["user_import_secret.csv", "EUR_PLN", "EUR_PLN"], details={"ux-risk": True, "secret.xlsx": True},
                         title="Private company", values=[123.987], filename="secret.xlsx", scenario_price=199,
                         **{"browser-asof":"2020-01-01", "scenario-price":199, "baseline":"true"})
        result = self.run_node("let value;api.write({setItem:(k,v)=>value=v},input);console.log(value)", candidate)
        self.assertEqual(result, {"version":1,"currency":"PLN/t","range":"90","price":False,"comparison":["EUR_PLN"],"details":{"ux-risk":True}})

    def test_malformed_oversized_or_wrong_version_storage_is_ignored(self):
        result = self.run_node("console.log(JSON.stringify(input.map(raw=>api.read({getItem:()=>raw}))))", ["not json", "null", "[]", json.dumps({"version":2,"range":"90"}), " "*8193])
        self.assertEqual(result, [None]*5)

    def test_storage_denied_or_quota_failure_is_nonfatal(self):
        result = self.run_node("console.log(JSON.stringify([api.read({getItem(){throw Error('denied')}}),api.write({setItem(){throw Error('quota')}},{version:1,range:'90'})]))")
        self.assertEqual(result, [None,False])

    def test_technical_warmup_explains_actual_observation_count(self):
        result = self.run_node("console.log(JSON.stringify(api.technicalMessages(input)))", [{"date":"2026-01-01","value":0}]*17)
        self.assertEqual(len(result),4)
        self.assertIn("SMA20 needs 20 observed prices; this view has 17. 3 more", result[0])
        self.assertIn("SMA200 needs 200 observed prices; this view has 17. 183 more", result[2])
        self.assertEqual(self.run_node("console.log(JSON.stringify(api.technicalMessages(input)))", [{"sma20":0,"sma100":0,"sma200":0,"bollinger_upper":0}]*200), [])

    def test_real_initializer_restores_settings_and_excludes_active_private_import(self):
        result = self.run_node("""initSeasonLensUX(context);
const restored={instrument:document.getElementById('instrument').value,range:document.getElementById('range').value,currency:document.getElementById('currency').value,price:document.getElementById('price').checked,chooses,refreshes};
document.getElementById('instrument').value='user_import_secret.csv';context.choose();change('instrument');
document.getElementById('range').value='all';change('range');
console.log(JSON.stringify({restored,saved:JSON.parse(store.get(api.key)),stored:[...store.values()]}));""", {"saved":{"version":1,"instrument":"SYNTHETIC_GRAIN","currency":"PLN/t","range":"90","price":False,"scenario-price":555}}, dom=True)
        self.assertEqual(result["restored"],dict(instrument="SYNTHETIC_GRAIN",range="90",currency="PLN/t",price=False,chooses=1,refreshes=1))
        self.assertEqual(result["saved"]["instrument"],"SYNTHETIC_GRAIN")
        self.assertEqual(result["saved"]["range"],"all")
        saved = json.dumps(result["stored"])
        for secret in ["secret.csv","Secret title","123.987","555","USER_FILE"]:
            self.assertNotIn(secret,saved)

    def test_navigation_opens_collapsed_ancestor_and_reset_preserves_unrelated_storage(self):
        result=self.run_node("""initSeasonLensUX(context);
const target=document.getElementById('market-comparison'),detail=new Element('details');detail.open=false;main.append(detail);detail.append(target);
const nav=document.getElementById('seasonlens-navigation'),link=nav.querySelectorAll('a').find(a=>a.hash==='#market-comparison');nav.fire('click',{target:link,preventDefault(){}});
document.getElementById('range').value='90';change('range');document.getElementById('reset-view-preferences').fire('click');
console.log(JSON.stringify({opened:detail.open,focused:target.focused,scrolled:target.scrolled,range:document.getElementById('range').value,other:store.get('unrelated'),keyPresent:store.has(api.key),privatePresent:!!data['user_import_secret.csv']}));""", {}, dom=True)
        self.assertEqual(result,dict(opened=True,focused=True,scrolled=True,range="12m",other="keep",keyPresent=False,privatePresent=True))


if __name__ == "__main__":
    unittest.main()
