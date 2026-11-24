"""Two distinct original still graphics for the 26-Nov manual POST and STORY.
No generated UI or manufacturer imagery; the percentages are explicitly examples.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).parent;O=R/'output';O.mkdir(exist_ok=True)
FONT=Path('/workspace/evberegn-marketing/reels/samtale-serie-20261123/fonts/NotoSans-Bold.ttf')
BG='#080d18';TEAL='#08d1b5';WHITE='#f7fbff';MUTED='#bfced7';CARD='#102b34'
proof=[]
def render(kind,w,h):
 im=Image.new('RGB',(w,h),BG);d=ImageDraw.Draw(im);bounds=[]
 def text(s,y,size,fill=WHITE,maxwidth=900):
  f=ImageFont.truetype(str(FONT),size)
  while d.textbbox((0,0),s,font=f)[2]>maxwidth:
   size-=1;f=ImageFont.truetype(str(FONT),size)
  b=d.textbbox((0,0),s,font=f);x=w/2-(b[0]+b[2])/2;d.text((x,y-b[1]),s,font=f,fill=fill);bounds.append({'text':s,'bounds':[x+b[0],y,x+b[2],y+b[3]-b[1]],'font_size':size})
 def diagram(y):
  d.rounded_rectangle((160,y,920,y+255),radius=38,fill=CARD)
  text('VALGTE PROCENTER',y+25,30,TEAL)
  for value,label,cx in [('20 %','START',345),('80 %','SLUT',735)]:
   f=ImageFont.truetype(str(FONT),78);b=d.textbbox((0,0),value,font=f);d.text((cx-(b[0]+b[2])/2,y+100-b[1]),value,font=f,fill=WHITE)
   f=ImageFont.truetype(str(FONT),27);b=d.textbbox((0,0),label,font=f);d.text((cx-(b[0]+b[2])/2,y+202-b[1]),label,font=f,fill=MUTED)
  # A conventional directional arrow connects start to end, not a fake control.
  d.line((493,y+136,585,y+136),fill=TEAL,width=7);d.line((566,y+118,585,y+136,566,y+154),fill=TEAL,width=7)
 if kind=='POST':
  text('EV Beregner',78,42,TEAL);text('Du lader en del.',198,66);text('Regn på den del.',291,66)
  diagram(456);text('Brug din bil og din samlede elpris.',792,41);text('Tilpas start og slut, når du regner.',862,38,MUTED)
  text('evberegn.dk',1060,77,TEAL);text('Gratis · uden login',1176,35)
  text('Regneoverslag over strøm – ikke alle ejerudgifter.',1262,26,MUTED)
 else:
  text('EV Beregner',303,42,TEAL);text('En delvis opladning?',428,61)
  diagram(599);text('Brug dine egne',940,45);text('start- og slutprocenter.',1006,45)
  text('Regn på din bil på hjemmesiden',1210,35,MUTED);text('evberegn.dk',1304,74,TEAL);text('Gratis · uden login',1421,35)
  text('Valgte procenter. Et regneoverslag.',1510,27,MUTED)
 for b in bounds:
  x1,y1,x2,y2=b['bounds'];assert 55<=x1<x2<=w-55 and 45<=y1<y2<=h-45
  if kind=='STORY':assert 275<=y1 and y2<=1580
 path=O/f'2026-11-26-{kind.lower()}.jpg';im.save(path,quality=96,subsampling=0)
 with Image.open(path) as readback:assert readback.size==(w,h) and readback.format=='JPEG'
 proof.append({'type':kind,'file':str(path),'size':[w,h],'text_bounds':bounds,'photo_credits_required':False,'original_typographic_diagram':True,'website_UI':False,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
render('POST',1080,1350);render('STORY',1080,1920)
(R/'STILL-RENDER-PROOF.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps([{'type':i['type'],'size':i['size']} for i in proof]))
