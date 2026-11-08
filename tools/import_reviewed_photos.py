"""Import only individually reviewed Commons photographs; never search at runtime."""
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
import hashlib,io,json,time
from PIL import Image
ROOT=Path(__file__).parents[1]
def main():
 manifest=json.loads((ROOT/'data/model-photos.json').read_text());count=0
 for photo in json.loads((ROOT/'data/reviewed-photo-imports.json').read_text())['photos']:
  targets=[s for s in photo['slugs'] if manifest['models'][s]['status']=='missing']
  if not targets:continue
  if not photo.get('reviewed_at') or not photo['license'].startswith(('CC BY','CC0')):raise ValueError('Missing reviewed license')
  if not photo['source'].startswith('https://commons.wikimedia.org/wiki/File:'):raise ValueError('Unexpected image source')
  url=photo['url']
  if urlsplit(url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unexpected download host')
  for attempt in range(3):
   try:
    with urlopen(Request(url,headers={'User-Agent':'EVBeregnTechnicalReview/1.0 (+https://www.evberegn.dk)'}),timeout=30) as r:
     if urlsplit(r.url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unexpected redirect')
     body=r.read(10000001)
    if len(body)>10000000:raise ValueError('Image too large')
    break
   except Exception:
    if attempt==2:raise
    time.sleep(2*(attempt+1))
  image=Image.open(io.BytesIO(body)).convert('RGB');image.thumbnail((1200,900))
  if image.width<700:raise ValueError('Image too small')
  encoded=io.BytesIO();image.save(encoded,format='WEBP',quality=85);data=encoded.getvalue();digest=hashlib.sha256(data).hexdigest()
  src='/assets/cars/reviewed-'+photo['id']+'-'+digest[:12]+'.webp';(ROOT/src.lstrip('/')).write_bytes(data)
  for slug in targets:
   label=manifest['models'][slug]['label']
   manifest['models'][slug]={k:photo[k] for k in ('identity','file','url','original_url','source','author','license','license_url','description','original_width','original_height','reviewed_at')}
   manifest['models'][slug].update(label=label,status='verified',reviewed=True,checked_at=date.today().isoformat(),credit=photo['author'],attribution='',modifications='Nedskaleret og konverteret til WebP; ingen beskæring.',src=src,width=image.width,height=image.height,bytes=len(data),sha256=digest,caption='Modelbillede. Udstyr, farve og fælge kan afvige fra den valgte variant.')
   count+=1
  time.sleep(1)
 (ROOT/'data/model-photos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print('REVIEWED_PHOTOS_IMPORTED '+json.dumps({'model_pages':count}),flush=True)
if __name__=='__main__':main()

