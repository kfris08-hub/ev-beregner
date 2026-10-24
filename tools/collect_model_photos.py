"""Collect openly licensed photo candidates on a review branch, never at page load.

The generated selections require human model/generation review before publication.
Only CC BY, CC BY-SA, CC0 and public-domain files are eligible.
"""
import base64,concurrent.futures,hashlib,html,io,json,re,time,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parents[1]
PLAN=json.loads((ROOT/'data/model-photo-plan.json').read_text())
OLD=json.loads((ROOT/'data/model-photos.json').read_text())['models'] if (ROOT/'data/model-photos.json').exists() else {}
HEADERS={'User-Agent':'EVBeregn-photo-catalog/1.0 (https://www.evberegn.dk/; Wikimedia image attribution and model review)'}
OUT=ROOT/'assets/cars';OUT.mkdir(parents=True,exist_ok=True)
REVIEW=ROOT/'test-results/photo-catalog';REVIEW.mkdir(parents=True,exist_ok=True)
def request(url,raw=False):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=35) as response:
    body=response.read()
    return body if raw else json.loads(body)
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt*2)
def api(host,**params):
 return request('https://'+host+'/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','origin':'*',**params}))
def plain(value):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',str(value or '')))).strip()
def norm(value):
 s=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()
 return re.sub('[^a-z0-9+]+',' ',s).strip()
def license_ok(meta):
 url=html.unescape(meta.get('LicenseUrl',{}).get('value',''))
 name=plain(meta.get('LicenseShortName',{}).get('value',''))
 match=re.match(r'https?://creativecommons\.org/licenses/by(?:-sa)?/[1-4]\.[05](?:/|$)',url)
 if match:return name,match[0].replace('http://','https://').rstrip('/')+'/'
 if 'creativecommons.org/publicdomain/zero/' in url:return name or 'CC0 1.0',url
 if name in ('Public domain','PD','CC0','CC0 1.0') or 'creativecommons.org/publicdomain/mark/' in url:
  return name or 'Public domain',url or 'https://creativecommons.org/publicdomain/mark/1.0/'
 return None
def candidate(page,p,lead=False):
 info=(page.get('imageinfo') or [{}])[0];meta=info.get('extmetadata',{})
 title=plain(page.get('title',''));name=norm(title)
 if title in p.get('exclude_files',[]):return None
 if not re.search(p['required'],name,re.I) or re.search(p['exclude'],name,re.I):return None
 if info.get('mime') not in ('image/jpeg','image/png','image/webp'):return None
 if info.get('width',0)<800 or info.get('width',0)/max(1,info.get('height',0))<1.1:return None
 lic=license_ok(meta)
 if not lic:return None
 author=plain(meta.get('Artist',{}).get('value',''))
 if not author:return None
 photo={'file':title,'url':info.get('thumburl') or info.get('url'),'original_url':info.get('url'),'source':info.get('descriptionurl') or 'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_')),'author':author,'license':lic[0],'license_url':lic[1],'credit':plain(meta.get('Credit',{}).get('value','')),'attribution':plain(meta.get('Attribution',{}).get('value','')),'description':plain(meta.get('ImageDescription',{}).get('value',''))[:1600],'original_width':info['width'],'original_height':info['height'],'checked_at':'2026-10-24','modifications':'Nedskaleret og konverteret til WebP; ingen beskæring.','score':30 if lead else 10}
 if re.search(r'front|side|three|quarter',name):photo['score']+=20
 if re.search(r'rear',name):photo['score']-=4
 if re.search(r'202[456]',name):photo['score']+=2
 return photo
# Fetch explicit article leads in batches. Article names never come from a user request.
articles={}
unique=list(dict.fromkeys(p['article'] for p in PLAN.values() if not p['skip']))
for i in range(0,len(unique),20):
 batch=unique[i:i+20]
 try:
  data=api('en.wikipedia.org',titles='|'.join(batch),redirects=1,prop='pageimages',piprop='name',pilicense='free')
  aliases={x['from']:x['to'] for x in data.get('query',{}).get('normalized',[])+data.get('query',{}).get('redirects',[])}
  pages={p['title']:p for p in data.get('query',{}).get('pages',{}).values()}
  for title in batch:
   resolved=title
   for _ in range(5):resolved=aliases.get(resolved,resolved)
   if pages.get(resolved,{}).get('pageimage'):articles[title]='File:'+pages[resolved]['pageimage']
 except Exception as e:print('ARTICLE_BATCH_ERROR',str(e),flush=True)
 print('ARTICLE_BATCH',i,len(articles),flush=True)
leads={}
files=list(set(articles.values()))
for i in range(0,len(files),20):
 try:
  data=api('commons.wikimedia.org',titles='|'.join(files[i:i+20]),prop='imageinfo',iiprop='url|extmetadata|size|mime',iiurlwidth=1200)
  for page in data.get('query',{}).get('pages',{}).values():leads[page['title']]=page
 except Exception as e:print('METADATA_BATCH_ERROR',str(e),flush=True)
 print('METADATA_BATCH',i,len(leads),flush=True)
def collect(item):
 slug,p=item
 result={'label':p['label'],'identity':p['identity'],'status':'missing','reason':p['missing_reason'] or 'Intet kontrolleret billede med en godkendt fri licens fundet.','reviewed':False}
 if p['skip']:return slug,result,[]
 if p.get('reuse') and OLD.get(slug,{}).get('src'):return slug,OLD[slug],[]
 candidates=[]
 lead=leads.get(articles.get(p['article'],''))
 if lead:
  photo=candidate(lead,p,True)
  if photo:candidates.append(photo)
 try:
  data=api('commons.wikimedia.org',generator='search',gsrnamespace=6,gsrsearch=p['query'],gsrlimit=50,prop='imageinfo',iiprop='url|extmetadata|size|mime',iiurlwidth=1200)
  for page in data.get('query',{}).get('pages',{}).values():
   photo=candidate(page,p)
   if photo and all(x['file']!=photo['file'] for x in candidates):candidates.append(photo)
 except Exception as e:result['reason']='Billedkilden svarede ikke under kontrollen.';result['lookup_error']=str(e)
 candidates.sort(key=lambda p:-p['score'])
 if not candidates:print('NO_CANDIDATE '+json.dumps({'slug':slug,'query':p['query'],'returned':len(data.get('query',{}).get('pages',{})) if 'data' in locals() else 0}),flush=True)
 if p.get('compare'):
  print('CANDIDATE_LIST '+json.dumps({'slug':slug,'files':[c['file'] for c in candidates[:6]],'sample':[{'file':pg.get('title'),'license':pg.get('imageinfo',[{}])[0].get('extmetadata',{}).get('LicenseShortName',{}).get('value'),'url':pg.get('imageinfo',[{}])[0].get('extmetadata',{}).get('LicenseUrl',{}).get('value')} for pg in list(data.get('query',{}).get('pages',{}).values())[:3]] if 'data' in locals() else []},ensure_ascii=False),flush=True)
 for photo in candidates:
  try:
   body=request(photo['url'],raw=True)
   image=Image.open(io.BytesIO(body));image.load();image=image.convert('RGB');image.thumbnail((1200,900))
   if image.width<700:continue
   raw=io.BytesIO();image.save(raw,format='WEBP',quality=82,method=6);encoded=raw.getvalue()
   filename=slug+'-'+hashlib.sha256(encoded).hexdigest()[:12]+'.webp'
   (OUT/filename).write_bytes(encoded)
   result.update(photo);result.update({'status':'candidate','src':'/assets/cars/'+filename,'width':image.width,'height':image.height,'bytes':len(encoded),'sha256':hashlib.sha256(encoded).hexdigest(),'reason':'Afventer visuel kontrol af model og generation.'})
   break
  except Exception as e:result['download_error']=str(e)
 return slug,result,candidates[:4]
results={};alternatives={}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
 for slug,result,candidates in executor.map(collect,PLAN.items()):
  results[slug]=result;alternatives[slug]=candidates
  print('PHOTO '+json.dumps({'slug':slug,**{k:result.get(k) for k in ('status','file','license','author','src','reason')}} ,ensure_ascii=False),flush=True)
manifest={'version':1,'checked_at':'2026-10-24','note':'Modelspecific photo, not a guarantee of the trim, colour, wheels or equipment shown.','models':results}
(ROOT/'data/model-photos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(REVIEW/'alternatives.json').write_text(json.dumps(alternatives,ensure_ascii=False,indent=2))
(ROOT/'data/model-photo-candidates.json').write_text(json.dumps(alternatives,ensure_ascii=False,indent=2)+'\n')
# Review sheets are log output only, not published as website assets.
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(font_path,13)
selected=[(slug,p) for slug,p in results.items() if p['status']=='candidate' and (not PLAN[slug].get('reuse') or PLAN[slug].get('sheet_only'))]
for offset in range(0,len(selected),20):
 sheet=Image.new('RGB',(1280,1100),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for j,(slug,p) in enumerate(selected[offset:offset+20]):
  x=(j%4)*320;y=(j//4)*220
  image=Image.open(ROOT/p['src'].lstrip('/'));image.thumbnail((312,168));sheet.paste(image,(x+(312-image.width)//2,y))
  label=p['label']
  while len(label)>43:
   cut=label.rfind(' ',0,43);cut=cut if cut>5 else 43
   draw.text((x+3,y+170),label[:cut],font=font,fill='black');label=label[cut:].strip();y+=15
  draw.text((x+3,y+170),label,font=font,fill='black')
  draw.text((x+3,(j//4)*220+207),str(offset+j+1),font=font,fill='blue')
 buf=io.BytesIO();sheet.save(buf,format='JPEG',quality=68)
 (REVIEW/('sheet-'+str(offset//20+1)+'.jpg')).write_bytes(buf.getvalue())
 print('CONTACT_SHEET '+str(offset//20+1)+' '+base64.b64encode(buf.getvalue()).decode(),flush=True)
print('CATALOG_SUMMARY '+json.dumps({'total':len(results),'candidates':sum(p['status']=='candidate' for p in results.values()),'missing':sum(p['status']=='missing' for p in results.values()),'new_sheets':len(selected),'bytes':sum(p.get('bytes',0) for p in results.values())}),flush=True)

comparisons=[]
for slug,p in PLAN.items():
 if not p.get('compare'):continue
 for number,photo in enumerate(alternatives.get(slug,[])[:4],1):
  try:
   image=Image.open(io.BytesIO(request(photo['url'],raw=True))).convert('RGB');image.thumbnail((312,165))
   comparisons.append((slug,number,photo,image))
  except Exception:pass
for offset in range(0,len(comparisons),16):
 sheet=Image.new('RGB',(1280,920),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for j,(slug,number,photo,image) in enumerate(comparisons[offset:offset+16]):
  x=j%4*320;y=j//4*230;sheet.paste(image,(x+(312-image.width)//2,y))
  label=slug+' ['+str(number)+']'
  draw.text((x+3,y+168),label[:42],font=font,fill='blue')
  draw.text((x+3,y+183),label[42:84],font=font,fill='blue')
  label=photo['file'][5:]
  draw.text((x+3,y+198),label[:42],font=font,fill='black');draw.text((x+3,y+213),label[42:84],font=font,fill='black')
 buf=io.BytesIO();sheet.save(buf,format='JPEG',quality=62)
 print('ALTERNATIVE_SHEET '+str(offset//16+1)+' '+base64.b64encode(buf.getvalue()).decode(),flush=True)
