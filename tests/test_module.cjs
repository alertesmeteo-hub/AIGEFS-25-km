const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(){this.children=[];this.value='';this.dataset={};this.events={};this.disabled=true;this.style={};}
 append(e){this.children.push(e);if(!this.value)this.value=String(e.value);}
 replaceChildren(){this.children=[];this.value='';}
 setAttribute(){}
 addEventListener(name,fn){this.events[name]=fn;}
 get selectedOptions(){return [{textContent:'Moyenne'}];}
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
async function setup(){
 const els={};for(const key of ['status','region','product','stat','step','zoom','map','period','city','show','locate','city-status','head','body'])els['[data-'+key+']']=new Element();els.datalist=new Element();
 els['[data-region]'].value='france';els['[data-stat]'].value='mean';
 const root={dataset:{source:'https://example.test/data',places:'/local-places.json'},querySelector:s=>els[s]};let success,failure,calls=0;const urls=[];
 const manifest={members:31,status:'ok',run:'2026-09-27T18:00:00Z',commune_count:2,steps:[0,24],products:{precipitation:{label:'Pluie',unit:'mm',column:12,period:'run'}}};
 const cities=[['75056','Paris','75'],['66136','Perpignan','66']];
 const ctx={document:{querySelectorAll:()=>[root],createElement:()=>new Element()},window:{isSecureContext:true},navigator:{geolocation:{getCurrentPosition:(a,b)=>{calls++;success=a;failure=b;}}},fetch:async url=>{urls.push(url);return {ok:true,json:async()=>url.endsWith('index.json')?manifest:url.endsWith('communes.json')?cities:url==='/local-places.json'?[['75056',48.8566,2.3122],['66136',42.699,2.9045]]:{communes:[[url.includes('/75.')?'75056':'66136',null,null,null,null,null,0]],forecast:[['2026-09-28T18:00:00Z',[[...Array(12).fill(null),2.5]]]]}};},Intl,Date,Set,Math,Number};
 vm.runInNewContext(fs.readFileSync('wordpress/aigefs-25-km/assets/module.js','utf8'),ctx);await settle();
 return {els,urls,click:()=>els['[data-locate]'].events.click(),position:coords=>success({coords}),fail:code=>failure({code}),calls:()=>calls};
}
(async()=>{
 let t=await setup();assert.equal(t.calls(),0,'No automatic location request');assert.equal(t.els['[data-locate]'].disabled,false);
 t.click();assert.equal(t.calls(),1);await t.position({latitude:48.857,longitude:2.31});assert.equal(t.els['[data-city]'].value,'Paris (75056)');assert.equal(t.els['[data-body]'].children.length,1);assert.ok(t.urls.every(u=>!u.includes('48.857')&&!u.includes('2.31')),'Coordinates not transmitted');
 t=await setup();t.click();t.fail(1);assert.match(t.els['[data-city-status]'].textContent,/refusée/);assert.equal(t.els['[data-locate]'].disabled,false);
 t=await setup();t.click();await t.position({latitude:40.7,longitude:-74});assert.match(t.els['[data-city-status]'].textContent,/hors de la zone/);assert.equal(t.els['[data-body]'].children.length,0);
 t=await setup();t.els['[data-city]'].value='Paris';t.els['[data-show]'].events.click();await settle();assert.equal(t.els['[data-body]'].children.length,1);
 t=await setup();t.click();t.els['[data-city]'].value='Perpignan';t.els['[data-show]'].events.click();await settle();await t.position({latitude:48.857,longitude:2.31});assert.equal(t.els['[data-city]'].value,'Perpignan','Late geolocation must not override manual choice');
 console.log('5 interface scenarios passed: opt-in location, denial, out-of-area, manual lookup, concurrent choice.');
})().catch(error=>{console.error(error);process.exitCode=1;});
