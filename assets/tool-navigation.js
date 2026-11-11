(function(){
 'use strict';
 const requested=new URLSearchParams(location.hash.slice(1)).get('bil')||new URLSearchParams(location.search).get('car')||'';
 if(/^[a-z0-9-]{1,160}$/.test(requested))document.querySelectorAll('[data-carry-car]').forEach(link=>{
  const url=new URL(link.href);if(url.origin!==location.origin)return;
  if(url.pathname==='/'&&/^#beregner-\d+$/.test(url.hash))url.searchParams.set('car',requested);
  else url.hash='bil='+encodeURIComponent(requested);
  link.href=url.href;
 });
 const input=document.getElementById('toolSearch');if(!input)return;
 document.querySelectorAll('[data-nav-js]').forEach(node=>{node.hidden=false;});
 const normalize=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/æ/g,'ae').replace(/ø/g,'o');
 input.addEventListener('input',()=>{
  const query=normalize(input.value).trim();let shown=0;
  document.querySelectorAll('[data-tool]').forEach(link=>{link.hidden=!normalize(link.dataset.tool).includes(query);if(!link.hidden)shown++;});
  document.querySelectorAll('.tool-group').forEach(group=>{group.hidden=![...group.querySelectorAll('[data-tool]')].some(link=>!link.hidden);});
  document.getElementById('noTools').hidden=shown>0;
 });
})();

