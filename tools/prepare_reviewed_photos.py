"""Materialize explicitly reviewed selections on the preparation branch only."""
import hashlib,io,json,re,urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).parents[1]
f=ROOT/'data/model-photos.json';data=json.loads(f.read_text());models=data['models']
pins=json.loads((ROOT/'data/reviewed-photo-pins.json').read_text())
for slug,pin in pins.items():
 old=models[slug]
 if old.get('file')==pin['file'] and old.get('src'):
  for field in ('license','license_url','author','credit','attribution','description'):old[field]=pin.get(field,'')
 else:
  request=urllib.request.Request(pin['url'],headers={'User-Agent':'EVBeregn-photo-catalog/1.0 (https://www.evberegn.dk/; credited Wikimedia photos)'})
  with urllib.request.urlopen(request,timeout=40) as response:body=response.read()
  image=Image.open(io.BytesIO(body));image.load();image=image.convert('RGB');image.thumbnail((1200,900))
  assert image.width>=700,slug
  output=io.BytesIO();image.save(output,format='WEBP',quality=82,method=6);body=output.getvalue();sha=hashlib.sha256(body).hexdigest()
  filename=slug+'-'+sha[:12]+'.webp';(ROOT/'assets/cars'/filename).write_bytes(body)
  models[slug]={**old,**pin,'src':'/assets/cars/'+filename,'width':image.width,'height':image.height,'bytes':len(body),'sha256':sha,'status':'candidate'}
for slug,p in models.items():
 if p['status']=='candidate':
  p['status']='verified';p['reviewed']=True;p['reviewed_at']='2026-10-24'
  p.pop('reason',None);p.pop('score',None);p.pop('download_error',None);p.pop('lookup_error',None)
  # Preserve the German port of CC BY-SA 3.0, not the unported license.
  if re.search(r'3\.0 de\b',p['license']):p['license_url']='https://creativecommons.org/licenses/by-sa/3.0/de/'
  else:p['license_url']=p['license_url'].replace('http://','https://').split('/deed.')[0].rstrip('/')+'/'
 else:
  p['status']='missing';p['reviewed']=True;p['reviewed_at']='2026-10-24'
  p.pop('download_error',None);p.pop('lookup_error',None)
# A shared body/market name must be disclosed, not presented as the exact trim.
models['byd-seal-u-comfort']['caption']='Modelbillede af BYD Song Plus EV, der markedsføres som Seal U i Europa. Udstyr, farve og fælge kan afvige.'
models['volvo-ec40-single-motor-core']['caption']='Modelbillede af Volvo C40 Recharge, som senere skiftede navn til EC40. Udstyr, farve og fælge kan afvige.'
models['volvo-ex40-single-motor-core']['caption']='Modelbillede af Volvo XC40 Recharge, som senere skiftede navn til EX40. Udstyr, farve og fælge kan afvige.'
models['mg-im5-long-range']['caption']='Modelbillede af IM L6, der sælges som MG IM5 på flere markeder. Udstyr, farve og fælge kan afvige.'
models['mg-im6-long-range']['caption']='Modelbillede af IM LS6, der sælges som MG IM6 på flere markeder. Udstyr, farve og fælge kan afvige.'
models['subaru-e-outback-limited-awd']['caption']='Modelbillede af Subaru Trailseeker, der markedsføres som E-Outback i Europa. Udstyr, farve og fælge kan afvige.'
models['skyworth-k-62-kwh']['caption']='Modelbillede af Skyworth EV6, som bruges til modelserien K. Markedsudgave, udstyr, farve og fælge kan afvige.'
# Remove every discarded candidate from the deployable tree.
used={p['src'].split('/')[-1] for p in models.values() if p['status']=='verified'}
for image in (ROOT/'assets/cars').glob('*.webp'):
 if image.name not in used:image.unlink()
f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verified':len(used),'missing':len(models)-len(used),'local_bytes':sum(p.get('bytes',0) for p in models.values())}))
