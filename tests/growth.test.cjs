const {test}=require('node:test'),assert=require('node:assert/strict');
const math=require('../assets/calculators.js'),share=require('../assets/calculation-share.js');
const defaults=id=>math.defaults(id);
test('kilometre cost has correct units and permits a free or negative electricity price',()=>{
 assert.deepEqual(math.compute(2,defaults(2)),{perKm:.32,per100:32});
 assert.equal(math.compute(2,{consumption:16,electricPrice:0}).per100,0);
 assert.equal(math.compute(2,{consumption:16,electricPrice:-.5}).per100,-8);
});
test('diesel comparison uses the entered litres and displays diesel labels',()=>{
 const r=math.compute(4,defaults(4));assert.equal(r.kwh,3200);assert.equal(r.litres,1000);assert.equal(r.fuelTotal,17000);assert.equal(r.saving,10600);
 assert.match(math.render(4,r),/Dieselbil/);assert.doesNotMatch(math.render(4,r),/Benzinbil/);
 const expensive=math.compute(4,{...defaults(4),electricPrice:8});assert.ok(expensive.saving<0);
});
test('trip energy and price are linear in distance, with a valid zero-distance case',()=>{
 const r=math.compute(6,defaults(6));assert.equal(r.energy,45);assert.equal(r.total,112.5);
 assert.equal(math.compute(6,{...defaults(6),km:500}).total,225);
 assert.equal(math.compute(6,{...defaults(6),km:0}).total,0);
});
test('range uses available kWh and cannot divide by zero',()=>{
 assert.ok(Math.abs(math.compute(7,defaults(7)).range-1000/3)<1e-9);
 assert.equal(math.compute(7,{battery:54,consumption:18}).range,300);
 assert.throws(()=>math.compute(7,{battery:60,consumption:0}),RangeError);
});
test('annual energy is a budget average, not a daily charging schedule',()=>{
 const r=math.compute(9,defaults(9));assert.equal(r.yearly,3200);assert.equal(r.monthly,3200/12);assert.equal(r.daily,3200/365);
 assert.equal(math.compute(9,{annualKm:0,consumption:16}).yearly,0);
});
test('new calculators reject missing, negative consumption, zero divisors and overflow',()=>{
 for(const id of [2,4,6,7,9])assert.throws(()=>math.compute(id,{...defaults(id),consumption:-1}),RangeError);
 assert.throws(()=>math.compute(4,{...defaults(4),fuelEconomy:0}),RangeError);
 assert.throws(()=>math.compute(6,{...defaults(6),km:1e308,consumption:1e308}),RangeError);
 assert.throws(()=>math.compute(2,{consumption:'',electricPrice:2}),RangeError);
});
test('a shared link round trips all values, model and area without a query string',()=>{
 const keys=math.definitions[3].fields.map(f=>f[0]),values={...defaults(3),electricPrice:0,annualKm:12500};
 const url=share.encode('https://www.evberegn.dk/beregnere/elbil-vs-benzin/?tracking=x',3,keys,values,'tesla-model-y-standard-rwd','DK2');
 assert.equal(new URL(url).search,'');assert.match(url,/#s=1/);
 assert.deepEqual(share.decode(new URL(url).hash,3,keys),{values,car:'tesla-model-y-standard-rwd',area:'DK2'});
});
test('ordinary existing car-selection links remain compatible',()=>{assert.equal(share.decode('#bil=kia-e-soul-64-kwh-2019',1,['battery']),null);});
test('shared links reject extra keys, duplicate values, missing values and injected markup',()=>{
 for(const hash of ['#s=1&k=2&consumption=16',' #s=1&k=2&consumption=16&electricPrice=2&__proto__=1','#s=1&k=2&consumption=16&electricPrice=2&electricPrice=3','#s=1&k=2&consumption=%3Csvg%3E&electricPrice=2','#s=1&k=2&consumption=16&electricPrice=NaN']){
  assert.equal(share.decode(hash.trim(),2,['consumption','electricPrice']).error,true,hash);
 }
});
test('shared links cannot select another calculator, area, domain or unsafe model',()=>{
 const hash='#s=1&k=2&consumption=16&electricPrice=2';
 assert.equal(share.decode(hash,4,['consumption','electricPrice']).error,true);
 assert.equal(share.decode(hash+'&area=XX',2,['consumption','electricPrice']).error,true);
 assert.equal(share.decode(hash+'&bil=%3Cscript%3E',2,['consumption','electricPrice']).error,true);
 assert.throws(()=>share.encode('https://other.example/beregnere/pris-pr-km/',2,['consumption','electricPrice'],defaults(2)),RangeError);
});
test('unbounded fragment input is rejected before parsing',()=>{assert.equal(share.decode('#s=1&'+('x'.repeat(5000)),2,['consumption','electricPrice']).error,true);});

