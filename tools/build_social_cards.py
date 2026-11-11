"""Create deterministic social previews in the existing EV Beregner colours."""
from pathlib import Path
import hashlib,json,io
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parents[1]
def font(size,bold=False):
 paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans'+('-Bold' if bold else '-Regular')+'.ttf']
 for path in paths:
  if Path(path).is_file():return ImageFont.truetype(path,size)
 return ImageFont.load_default(size=size)
def render(title):
 im=Image.new('RGB',(1200,630));draw=ImageDraw.Draw(im)
 for y in range(630):
  t=y/630;draw.line((0,y,1200,y),fill=(int(7+5*t),int(12+22*t),int(23+24*t)))
 draw.rounded_rectangle((65,55,1135,575),radius=28,outline='#29374d',width=2)
 draw.text((100,85),'EV BEREGNER',font=font(29,True),fill='#10ddb2')
 draw.rounded_rectangle((875,85,1095,127),radius=16,fill='#0b3937');draw.text((899,92),'GRATIS',font=font(23,True),fill='#10ddb2')
 f=font(59,True);words=title.split();lines=[];line=''
 for word in words:
  candidate=(line+' '+word).strip()
  if draw.textlength(candidate,font=f)>990 and line:lines.append(line);line=word
  else:line=candidate
 if line:lines.append(line)
 if len(lines)>3:raise ValueError('Social title is too long')
 for n,line in enumerate(lines):draw.text((100,190+n*78),line,font=f,fill='#ffffff')
 draw.line((100,457,1100,457),fill='#10ddb2',width=3)
 draw.text((100,485),'20 beregnere · egne tal · uden login',font=font(27),fill='#b9c5d6')
 draw.text((100,535),'evberegn.dk',font=font(23,True),fill='#10ddb2')
 return im
def main():
 pages=json.loads((ROOT/'data/calculator-pages.json').read_text())
 targets=[('ev-beregner','Hvad koster din elbil?')]+[(p['slug'],p['h1']) for p in pages]
 out=ROOT/'assets/social';out.mkdir(parents=True,exist_ok=True)
 for slug,title in targets:
  raw=io.BytesIO();render(title).save(raw,format='PNG',optimize=True)
  path=out/(slug+'.png');data=raw.getvalue()
  if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
 print('SOCIAL_CARDS_RESULT '+json.dumps({'cards':len(targets),'width':1200,'height':630}))
if __name__=='__main__':main()

