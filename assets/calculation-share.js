/* URL fragments carry only the values deliberately shared by the visitor. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.EVCalculationShare=api;})(typeof window!=='undefined'?window:globalThis,function(){
 'use strict';
 const ORIGIN='https://www.evberegn.dk',slug=/^[a-z0-9-]{1,160}$/;
 function decode(hash,id,keys){
  if(String(hash).length>4096)return {error:true};
  const p=new URLSearchParams(String(hash).replace(/^#/,''));
  if(!p.has('s'))return null;
  const allowed=new Set(['s','k','bil','area',...keys]);
  if(p.get('s')!=='1'||p.get('k')!==String(id)||[...p.keys()].some(k=>!allowed.has(k)||p.getAll(k).length!==1))return {error:true};
  const values={};
  for(const key of keys){const value=p.get(key);if(value===null||value.trim()===''||value.length>64||!Number.isFinite(Number(value)))return {error:true};values[key]=Number(value);}
  const car=p.get('bil')||'',area=p.get('area')||'';
  if((car&&!slug.test(car))||(area&&!['DK1','DK2'].includes(area)))return {error:true};
  return {values,car,area};
 }
 function encode(base,id,keys,values,car='',area=''){
  const url=new URL(base);
  if(url.origin!==ORIGIN||!/^\/beregnere\/[a-z0-9-]+\/$/.test(url.pathname))throw new RangeError('Invalid calculator address');
  const p=new URLSearchParams({s:'1',k:String(id)});
  if(car)p.set('bil',car);
  if(area)p.set('area',area);
  for(const key of keys)p.set(key,String(values[key]));
  url.search='';url.hash=p.toString();
  const parsed=decode(url.hash,id,keys);if(!parsed||parsed.error)throw new RangeError('Invalid shared values');
  return url.href;
 }
 return {encode,decode};
});

