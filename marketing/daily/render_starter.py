"""Create tomorrow's feed image and a separate still-image Facebook Story."""
from pathlib import Path
import json
from urllib.parse import urlparse
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright

P=Path(__file__).parent;OUT=P/'starter-output';OUT.mkdir(exist_ok=True)
BASE='https://www.evberegn.dk';SLUG='toyota-bz4x-active-57-kwh-fwd'
manifest=json.loads((Path.cwd()/'data/model-photos.json').read_text())['models'][SLUG]
assert manifest['status']=='verified' and manifest['reviewed'] and manifest['license']=='CC0'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':420,'height':748},device_scale_factor=2,is_mobile=True,has_touch=True)
    page.route('**/*',lambda route:route.continue_() if urlparse(route.request.url).hostname=='www.evberegn.dk' else route.abort())
    response=page.goto(BASE+'/elbil/'+SLUG+'/',wait_until='networkidle');assert response.status==200
    assert page.locator('#carPhoto').evaluate('(i)=>i.complete && i.naturalWidth>0')
    credit=page.locator('#photoCredit').inner_text();assert 'TTTNIS' in credit and 'CC0' in credit
    assert 'Nedskaleret' not in credit and 'konverteret' not in credit
    hero=page.locator('.hero').bounding_box();last=page.locator('#photoCredit').bounding_box()
    image=page.locator('.hero').screenshot()
    (OUT/'real-model.png').write_bytes(image)
    # Crop the real model heading, image and full credit; avoid quoting a price.
    picture=Image.open(OUT/'real-model.png').convert('RGB')
    end=round((last['y']+last['height']-hero['y']+6)*2)
    picture=picture.crop((0,0,picture.width,min(end,picture.height)))
    browser.close()

F='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def draw_text(draw,value,y,size,width=900,color='#ffffff'):
    f=ImageFont.truetype(F,size);w=draw.textlength(value,font=f)
    assert w<=width,(value,w)
    draw.text(((1080-w)/2,y),value,font=f,fill=color)
def render(height,filename,question,question2):
    im=Image.new('RGB',(1080,height),'#070c17');d=ImageDraw.Draw(im)
    top=190 if height==1920 else 75
    draw_text(d,'EV Beregner',top,36,color='#10ddb2')
    draw_text(d,question,top+70,66)
    draw_text(d,question2,top+146,66)
    y=top+245
    maxheight=880 if height==1920 else 680
    ratio=min(900/picture.width,maxheight/picture.height)
    photo=picture.resize((round(picture.width*ratio),round(picture.height*ratio)),Image.Resampling.LANCZOS)
    im.paste(photo,((1080-photo.width)//2,y))
    bottom=y+photo.height+30
    draw_text(d,'Vælg bilen. Regn med dine tal.',bottom,38)
    draw_text(d,'evberegn.dk',bottom+65,78,color='#10ddb2')
    draw_text(d,'Gratis · uden login',bottom+160,31)
    assert bottom+205<height-100,(height,bottom)
    im.save(OUT/filename,quality=94,subsampling=0)
render(1350,'2026-11-15-post.jpg','Har du en elbil','i tankerne?')
render(1920,'2026-11-15-story.jpg','Din bil – eller','den næste?')
proof={'date':'2026-11-15','source':BASE+'/elbil/'+SLUG+'/','photo_credit':credit,'rights':{'author':manifest['author'],'license':manifest['license'],'source':manifest['source']},'post':[1080,1350],'story':[1080,1920],'story_type':'STORY, single static image','new_heygen_generations':0,'real_analytics_or_ad_events':0,'website_design_changed':False}
(OUT/'PROOF.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
print('DAILY_STARTER_RESULT '+json.dumps(proof,ensure_ascii=False))
