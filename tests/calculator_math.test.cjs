const {test}=require('node:test'),assert=require('node:assert/strict'),engine=require('../assets/calculators.js');
const input=(id,changes={})=>({...engine.defaults(id),...changes});
test('partial charging accounts for only the chosen percentage and declared extra energy',()=>{
 const r=engine.compute(1,input(1,{from:20,to:80,overhead:10,electricPrice:2.5}));
 assert.equal(r.batteryEnergy,36);assert.ok(Math.abs(r.paidEnergy-39.6)<1e-9);assert.ok(Math.abs(r.total-99)<1e-9);
});
test('zero charging and zero or negative prices are valid scenarios',()=>{
 assert.equal(engine.compute(1,input(1,{from:40,to:40})).total,0);
 assert.equal(engine.compute(1,input(1,{electricPrice:0,overhead:10})).total,0);
 assert.equal(engine.compute(1,input(1,{electricPrice:-.25,overhead:10})).total,-16.5);
});
test('energy comparison uses the same annual distance and is not ownership cost',()=>{
 const r=engine.compute(3,input(3));assert.equal(r.kwh,3100);assert.equal(r.litres,1250);assert.equal(r.electricTotal,6200);assert.equal(r.fuelTotal,20000);assert.equal(r.saving,13800);
 assert.equal(engine.compute(3,input(3,{electricPrice:8})).saving,-4800);
 assert.equal(engine.compute(3,input(3,{annualKm:0})).saving,0);
});
test('charging time is energy divided by average power, not car peak power',()=>{
 const r=engine.compute(8,input(8));assert.equal(r.energy,36);assert.ok(Math.abs(r.hours-3.2727272727)<1e-8);
 assert.equal(engine.compute(8,input(8,{from:80,to:80})).hours,0);
 assert.equal(engine.definitions[8].fields.find(f=>f[0]==='power')[3],'manual');
});
test('leasing compares period payments against purchase less resale, not purchase price alone',()=>{
 const r=engine.compute(12,input(12));assert.equal(r.leaseTotal,158964);assert.equal(r.buyTotal,100000);assert.equal(r.difference,58964);assert.ok(Math.abs(r.leaseMonthly-4415.6666667)<1e-6);
 const costs=engine.compute(12,input(12,{leaseOther:6000,purchaseOther:48000}));assert.equal(costs.difference,16964);
 const resale=engine.compute(12,input(12,{resaleValue:100000}));assert.equal(resale.difference,8964);
});
test('five-year cost includes depreciation and the explicitly entered running budget',()=>{
 const r=engine.compute(14,input(14));assert.equal(r.running,75000);assert.equal(r.total,225000);assert.equal(r.monthly,3750);
 assert.equal(engine.compute(14,input(14,{futureValue:75000})).total,250000);
});
for(const [id,changes] of [[1,{from:80,to:20}],[1,{to:101}],[1,{overhead:101}],[3,{fuelEconomy:0}],[8,{power:0}],[12,{months:0}],[12,{months:1.5}],[14,{price:''}],[14,{price:null}],[14,{annualRunning:-1}]])test('invalid input cannot produce a plausible result: '+id+' '+JSON.stringify(changes),()=>{
 assert.throws(()=>engine.compute(id,input(id,changes)),RangeError);
});
test('extreme finite inputs cannot overflow to infinity',()=>{assert.throws(()=>engine.compute(1,input(1,{battery:1e308,electricPrice:1e308})),RangeError)});
