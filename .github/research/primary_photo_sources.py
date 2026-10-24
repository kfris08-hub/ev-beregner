import base64,html,io,json,re,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).parents[2];OUT=ROOT/'.github/research/primary';OUT.mkdir(parents=True,exist_ok=True)
UA='Mozilla/5.0 (compatible; EVBeregn-source-check/1.0; +https://www.evberegn.dk/)'
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=30) as r:return r.read(),r.headers.get('content-type','')
records={};photos=[]
urls={
'elveon':'https://elveon.dk',
'mercedes-photo-metadata':'https://api.media.mercedes-benz.com/jsonapi/image/222b49fc-2617-42d2-8b7f-695a1e6c076e',
'mercedes-photo-568':'https://api.media.mercedes-benz.com/jsonapi/image/deliver/222b49fc-2617-42d2-8b7f-695a1e6c076e/3_2_568',
'mercedes-photo-1200':'https://api.media.mercedes-benz.com/jsonapi/image/deliver/222b49fc-2617-42d2-8b7f-695a1e6c076e/3_2_1200',
'mercedes-photo-1920':'https://api.media.mercedes-benz.com/jsonapi/image/deliver/222b49fc-2617-42d2-8b7f-695a1e6c076e/3_2_1920',
}
for key,url in urls.items():
 try:
  body,mime=fetch(url)
  if mime.startswith('image/'):
   image=Image.open(io.BytesIO(body));image.load();records[key]={'url':url,'mime':mime,'width':image.width,'height':image.height,'bytes':len(body)}
   im=image.convert('RGB');im.thumbnail((600,370));photos.append((key,im))
  elif 'json' in mime:
   data=json.loads(body);records[key]={'url':url,'metadata':data};print('IMAGE_METADATA '+json.dumps(data,ensure_ascii=False)[:22000],flush=True)
  else:
   text=body.decode('utf-8','replace')
   links=re.findall(r'(?:href|src)=["\']([^"\']+)',text)
   records[key]={'url':url,'title':re.search(r'<title[^>]*>(.*?)</title>',text,re.S)[1] if '<title' in text else '', 'links':[html.unescape(l) for l in links if re.search(r'min|sedan|photo|image|\.jpg|\.png|\.webp',l,re.I)],'text':re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',text)))[:20000]}
   if key=='elveon':
    print('IMPORTER_PRIMARY '+json.dumps(records[key],ensure_ascii=False)[:16000],flush=True)
    for link in records[key]['links']:
     link=link if link.startswith('https://') else 'https://elveon.dk'+link if link.startswith('/') else ''
     if not re.search(r'\.(jpg|png|webp)(\?|$)',link,re.I):continue
     try:
      raw,_=fetch(link);im=Image.open(io.BytesIO(raw));im.load()
      if im.width<500 or im.height<250:continue
      im=im.convert('RGB');im.thumbnail((600,370));photos.append(('elveon-primary '+link[-70:],im))
      if len(photos)>=5:break
     except Exception:pass
 except Exception as e:records[key]={'url':url,'error':str(e)}
 print('SOURCE_RESULT '+json.dumps({key:records[key]},ensure_ascii=False)[:1600],flush=True)
(OUT/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
if photos:
 sheet=Image.new('RGB',(1200,((len(photos)+1)//2)*410),'#eeeeee');d=ImageDraw.Draw(sheet)
 for n,(name,im) in enumerate(photos):
  x=n%2*600;y=n//2*410;sheet.paste(im,(x+(600-im.width)//2,y));d.text((x+4,y+375),name[:85],fill='black')
 out=io.BytesIO();sheet.save(out,format='JPEG',quality=70)
 print('PRIMARY_SHEET '+base64.b64encode(out.getvalue()).decode(),flush=True)
