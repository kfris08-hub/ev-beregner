const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const test=require('node:test'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
const homeSource=fs.readFileSync(path.join(root,'index.html'),'utf8');
const modelSource=fs.readFileSync(path.join(root,'elbil/tesla-model-y-standard-rwd/index.html'),'utf8');
const fuel=JSON.parse(fs.readFileSync(path.join(root,'data/fuel-prices.json'),'utf8'));
function setup(kind,options={}){
 const markup=kind==='home'?homeSource:modelSource;
 const elements=new Map(),listeners=new Map(),requests=[],storage=options.storage||new Map(),timers=new Set();
 let location=new URL(options.url||'https://www.evberegn.dk/');
 function parse(html){for(const m of String(html).matchAll(/<[^>]+\bid=["']([^"']+)["'][^>]*>/g)){const node=element(m[1]),v=m[0].match(/\bvalue=["']([^"']*)["']/);if(v)node.value=v[1];}}
 function element(id=''){
  if(id&&elements.has(id))return elements.get(id);
  let text='',html='';
  const el={id,value:'',style:{},className:'',children:[],offsetTop:0,dataset:{},events:new Map(),validityMessage:'',classList:{add(){},remove(){},toggle(){}},
   addEventListener(type,fn){this.events.set(type,fn)},appendChild(child){this.children.push(child)},remove(){elements.delete(id)},
   insertAdjacentHTML(_,value){html+=value;parse(value)},setAttribute(k,v){this[k]=v},getAttribute(k){return this[k]||null},setCustomValidity(m){this.validityMessage=m},reportValidity(){return !this.validityMessage},
   get src(){return this._src||''},set src(value){this._src=value;this.complete=false;queueMicrotask(()=>{if(String(value).includes('broken-image')){this.naturalWidth=0;this.onerror?.();}else{this.complete=true;this.naturalWidth=1600;this.naturalHeight=1000;this.onload?.();}})},
   get innerHTML(){return html},set innerHTML(v){html=String(v);text=html.replace(/<[^>]*>/g,'');parse(html)},get textContent(){return text},set textContent(v){text=String(v)},get innerText(){return text},set innerText(v){text=String(v)}};
  if(id)elements.set(id,el);return el;
 }
 parse(markup);
 for(const m of markup.matchAll(/<[^>]+\bid=["']([^"']+)["'][^>]*>([^<]*)/g))element(m[1]).textContent=m[2];
 const history={state:null,pushState(s,_,url){this.state=s;location=new URL(url,location)},replaceState(s,_,url){this.state=s;location=new URL(url,location)},back(){}};
 const context={console,Intl,Number,Math,Object,Array,String,Boolean,Date,JSON,Promise,URL,URLSearchParams,AbortController,encodeURIComponent,history,get location(){return location},
  localStorage:{getItem(k){if(options.storageBlocked)throw Error('blocked');return storage.get(k)||null},setItem(k,v){if(options.storageBlocked)throw Error('blocked');storage.set(k,v)}},
  document:{currentScript:{dataset:{}},getElementById(id){return elements.get(id)||null},createElement(){return element()},createTextNode(text){return {textContent:text}},addEventListener(){},querySelectorAll(){return []}},
  setTimeout(fn,delay){const timer=setTimeout(fn,options.fastTimeout?Math.min(delay,20):delay);timers.add(timer);return timer},clearTimeout(timer){timers.delete(timer);clearTimeout(timer)},
  async fetch(url){requests.push(url);if(options.pending)return new Promise(()=>{});if(options.offline)throw Error('offline');if(options.fetch)return options.fetch(url);
   const data=String(url).includes('fuel-prices')?fuel:String(url).includes('elpriser.org')?{price:options.price??2.5}:{query:{pages:{}}};return {ok:true,status:200,async json(){return data}};
  },scrollTo(){},addEventListener(name,fn){listeners.set(name,fn)}};
 context.window=context;vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(root,'assets/ev-core.js'),'utf8'),context);
 if(kind==='home')for(const s of [...homeSource.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)].filter(x=>!x[1].includes('type=')&&!x[1].includes('src=')))vm.runInContext(s[2],context);
 else{context.document.currentScript.dataset={consumption:'15.5'};vm.runInContext(fs.readFileSync(path.join(root,'assets/model-calculator.js'),'utf8'),context);}
 return {context,elements,requests,storage,listeners,run(code){return vm.runInContext(code,context)},cleanup(){for(const timer of timers)clearTimeout(timer)}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('all 20 calculators return finite default results',async()=>{const h=setup('home');await settle();assert.equal(h.run('Object.keys(calculators).length'),20);for(let id=1;id<=20;id++){h.run(`openCalculator(${id});calculate()`);const answer=h.elements.get('answer').innerText;assert.ok(answer.length>0,'calculator '+id);assert.doesNotMatch(answer,/NaN|Infinity|∞/,'calculator '+id);}h.cleanup();});
test('model selection survives the link to the homepage',()=>{const h=setup('home',{url:'https://www.evberegn.dk/?car=tesla-model-y-standard-rwd'});assert.equal(h.run('selectedCar[0]+" "+selectedCar[1]'),'Tesla Model Y Standard RWD');h.run('openCalculator(2)');assert.equal(h.elements.get('calc_consumption').value,'15.5');h.cleanup();});
test('unknown slug remains a general calculation',()=>{const h=setup('home',{url:'https://www.evberegn.dk/?car=missing'});assert.equal(h.run('selectedCar'),null);h.cleanup();});
test('calculator deep link opens the requested calculator',()=>{const h=setup('home',{url:'https://www.evberegn.dk/?car=tesla-model-y-standard-rwd#beregner-8'});assert.equal(h.run('currentCalculator'),8);assert.equal(h.elements.get('calculator').style.display,'block');h.cleanup();});
for(const price of [0,-0.25,2.5])test('price '+price+' is consistent in homepage, calculator and model',async()=>{const h=setup('home',{price}),m=setup('model',{price});await settle();await settle();h.run('openCalculator(2);calculate()');assert.equal(Number(h.elements.get('calc_electricPrice').value),price);assert.equal(Number(m.elements.get('ep').value),price);assert.equal(m.elements.get('r100').textContent,(15.5*price).toFixed(2).replace('.',',')+' kr.');h.cleanup();m.cleanup();});
test('manual zero price stays zero',async()=>{const m=setup('model');await settle();m.elements.get('ep').value='0';m.run('calculate()');assert.equal(m.elements.get('r100').textContent,'0,00 kr.');m.cleanup();});
test('results exist before either price service responds',()=>{const m=setup('model',{pending:true});assert.equal(m.elements.get('r100').textContent,'31,00 kr.');m.cleanup();});
test('timeouts keep useful results and finish status',async()=>{const m=setup('model',{pending:true,fastTimeout:true});await new Promise(resolve=>setTimeout(resolve,40));assert.equal(m.elements.get('r100').textContent,'31,00 kr.');assert.match(m.elements.get('liveNote').textContent,/kunne ikke opdateres/);m.cleanup();});
test('failed requests have explicit fallback status',async()=>{const m=setup('model',{offline:true});await settle();assert.equal(m.elements.get('r100').textContent,'31,00 kr.');assert.match(m.elements.get('liveNote').textContent,/kunne ikke opdateres/);m.cleanup();});
for(const [calc,field] of [[3,'fuelEconomy'],[4,'fuelEconomy'],[7,'consumption'],[8,'power'],[15,'annualKm']])test('calculator '+calc+' rejects zero divisor',()=>{const h=setup('home');h.run(`openCalculator(${calc})`);h.elements.get('calc_'+field).value='0';h.run('calculate()');assert.match(h.elements.get('answer').textContent,/større end 0/);assert.doesNotMatch(h.elements.get('answer').textContent,/NaN|Infinity|∞/);h.cleanup();});
test('charging percentages are ordered and within 0–100',()=>{const h=setup('home');h.run('openCalculator(8)');h.elements.get('calc_from').value='80';h.elements.get('calc_to').value='20';h.run('calculate()');assert.match(h.elements.get('answer').textContent,/Slutprocent/);h.elements.get('calc_to').value='110';h.run('calculate()');assert.match(h.elements.get('answer').textContent,/højst være 100/);h.cleanup();});
test('zero kilometres gives zero annual cost',async()=>{const m=setup('model');await settle();m.elements.get('km').value='0';m.run('calculate()');assert.equal(m.elements.get('ryear').textContent,'0 kr.');m.cleanup();});
test('blocked browser storage does not disable calculators',async()=>{const h=setup('home',{storageBlocked:true}),m=setup('model',{storageBlocked:true});await settle();h.run('openCalculator(1);calculate()');assert.doesNotMatch(h.elements.get('answer').textContent,/NaN|Infinity/);assert.match(m.elements.get('r100').textContent,/kr\./);h.cleanup();m.cleanup();});
test('invalid manual price does not silently use 2 kr.',async()=>{const m=setup('model');await settle();m.elements.get('ep').value='';m.run('calculate()');assert.equal(m.elements.get('r100').textContent,'–');m.cleanup();});
test('late price response cannot overwrite manual price',async()=>{let resolvePrice;const m=setup('model',{fetch:async url=>String(url).includes('elpriser.org')?new Promise(resolve=>{resolvePrice=resolve}):({ok:true,json:async()=>fuel})});m.elements.get('ep').value='0';m.elements.get('ep').events.get('input')();resolvePrice({ok:true,json:async()=>({price:3})});await settle();assert.equal(m.elements.get('ep').value,'0');assert.equal(m.elements.get('r100').textContent,'0,00 kr.');m.cleanup();});
test('fixed photos never start an image search or require storage',async()=>{
 const m=setup('model',{storageBlocked:true});await settle();
 const photo=m.elements.get('carPhoto');photo.src='/assets/cars/reviewed-model.webp';await settle();
 const requests=m.requests.length;
 m.run(fs.readFileSync(path.join(root,'assets/car-images.js'),'utf8'));
 assert.equal(photo.src,'/assets/cars/reviewed-model.webp');assert.equal(m.requests.length,requests);
 assert.equal(photo.style.display,undefined);m.cleanup();
});
test('a failed local photo reveals an explicit retry message',async()=>{
 const m=setup('model');await settle();
 const photo=m.elements.get('carPhoto');photo.src='/assets/cars/reviewed-model.webp';await settle();
 m.run(fs.readFileSync(path.join(root,'assets/car-images.js'),'utf8'));
 photo.events.get('error')();
 assert.equal(photo.style.display,'none');assert.equal(m.elements.get('photoLoading').style.display,'block');
 assert.match(m.elements.get('photoLoading').textContent,/genindlæse/);m.cleanup();
});
test('withdrawn model variants cannot populate a calculator',()=>{
 for(const slug of ['kia-ev1-standard-range','kia-sportage-ev-standard','volvo-ex50-single-motor-rwd','volvo-ex70-single-motor']){
  const h=setup('home',{url:'https://www.evberegn.dk/?car='+slug});assert.equal(h.run('selectedCar'),null);h.cleanup();
 }
});
test('old IONIQ 7 car links select the current IONIQ 9',()=>{
 const h=setup('home',{url:'https://www.evberegn.dk/?car=hyundai-ioniq-7-standard'});assert.equal(h.run('selectedCar[1]'),'IONIQ 9 RWD Advanced');h.cleanup();
});
test('unknown model data use editable examples in all 20 calculators',()=>{
 const h=setup('home',{url:'https://www.evberegn.dk/?car=elveon-motors-min-e-sedan-base'});
 assert.equal(h.run('selectedCar[1]'),'Min-E Sedan');
 for(const type of ['price','battery','range','consumption','charging'])assert.equal(h.run('autoValue('+JSON.stringify(type)+')'),null);
 assert.equal(h.run('money(null)'),'Ikke oplyst');
 for(let n=1;n<=20;n++){h.run('openCalculator('+n+');calculate()');assert.doesNotMatch(h.elements.get('answer').textContent,/NaN|Infinity|∞|undefined/);assert.match(h.elements.get('dataBadge').textContent,/eksempelværdier/);}
 h.cleanup();
});
test('comparison never treats missing specifications as zero or a winning value',async()=>{
 const h=setup('home');await settle();h.run('compareCars[0]=cars.find(c=>c[0]==="Elveon Motors");compareCars[1]=cars.find(c=>c[0]==="Tesla"&&c[1].startsWith("Model Y"));renderCompare()');
 const result=h.elements.get('compareOutput').innerHTML;assert.match(result,/Ikke oplyst/);assert.doesNotMatch(result,/null|undefined|NaN/);assert.doesNotMatch(result,/<td class="winner">Ikke oplyst/);h.cleanup();
});
