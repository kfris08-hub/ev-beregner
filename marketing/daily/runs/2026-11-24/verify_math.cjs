const assert=require('node:assert/strict');
const fs=require('node:fs');
const c=require('./reference/calculators.js');
const s=require('./reference/calculation-share.js');
const a=c.compute(9,{annualKm:20000,consumption:16});assert.equal(a.yearly,3200);assert.equal(Math.round(a.monthly),267);
const low=c.compute(2,{consumption:16,electricPrice:2}),high=c.compute(2,{consumption:16,electricPrice:4});assert.equal(low.perKm,.32);assert.equal(high.perKm,.64);
const partial=c.compute(1,{battery:60,electricPrice:2,from:20,to:80,overhead:0});assert.deepEqual(partial,{batteryEnergy:36,paidEnergy:36,total:72});
const plan=JSON.parse(fs.readFileSync('/workspace/evberegn-marketing/daily/DAILY-PLAN.json','utf8'));
const links=[];
for(const d of plan.days.filter(d=>d.date>='2026-11-24'&&d.date<='2026-11-26'))for(const i of d.items){
 const u=new URL(i.destination);assert.equal(u.hostname,'www.evberegn.dk');assert.equal(u.searchParams.get('utm_source'),'facebook');assert.equal(u.searchParams.get('utm_medium'),'organic_social');
 if(u.hash.startsWith('#s=')){
  const id=d.date==='2026-11-24'?9:2;const fields=id===9?['annualKm','consumption']:['consumption','electricPrice'];const decoded=s.decode(u.hash,id,fields);assert.ok(decoded&&decoded.values);assert.equal(decoded.values.consumption,16);
 }
 links.push({date:d.date,type:i.type,destination:i.destination,utm_and_shared_fragment:'PASS'});
}
const p={source:'Current GitHub main arithmetic, retrieved via connector after direct HTTP sandbox block',annual:a,price_per_km:{low,high},charging_feature_example:partial,links,advertised_math:'PASS'};
fs.writeFileSync(__dirname+'/MATH-AND-LINK-PROOF.json',JSON.stringify(p,null,2));console.log(JSON.stringify({advertised_math:'PASS',links:links.length,yearly:a.yearly,perKm:[low.perKm,high.perKm]}));
