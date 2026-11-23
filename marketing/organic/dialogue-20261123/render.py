"""Three distinct conversation Reels, using the successful illustrated reference.
python render.py elafgift | aarsforbrug | delvis-opladning
Real measured speech timing, independently posed figures, no website UI.
"""
from pathlib import Path
from functools import lru_cache
import json,sys,math,subprocess,wave,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
ROOT=Path(__file__).resolve().parent;KEY=sys.argv[1];F=ROOT/KEY;F.mkdir(exist_ok=True)
T=json.loads((F/'TIMELINE.json').read_text());LINES=T['lines'];W,H,FPS,SR=1080,1920,24,48000
FRAMES=math.ceil(T['duration']*FPS);SECONDS=FRAMES/FPS;CTA=T['cta_start']
SAFE=(216,346,864,1248);TEAL='#078d83';INK='#132631';WHITE='#ffffff'
SHEET=Image.open(ROOT/'assets/characters.png').convert('RGBA');assert SHEET.size==(1536,1024)
BG=ImageOps.fit(Image.open(ROOT/'assets/background.png').convert('RGB'),(W,H),Image.Resampling.LANCZOS)
VOICE=np.zeros(round(SECONDS*SR))
for turn in T['turns']:
 with wave.open(str(ROOT/turn['source'])) as wav:raw=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)/32768
 voiced=raw[np.abs(raw)>.004];rms=float(np.sqrt(np.mean(voiced**2))) if len(voiced) else .01
 raw*=min(.12/max(rms,.001),.65/max(np.max(np.abs(raw)),.001));at=round(turn['start']*SR)
 VOICE[at:at+len(raw)]+=raw
def energy(t):
 a=max(0,round((t-.02)*SR));b=min(len(VOICE),round((t+.02)*SR));return float(np.sqrt(np.mean(VOICE[a:b]**2))) if b>a else 0
@lru_cache(None)
def font(size):return ImageFont.truetype(str(ROOT/'fonts/NotoSans-Bold.ttf'),size)
def ease(x):x=max(0,min(1,x));return 1-(1-x)**3
@lru_cache(None)
def sprite(role,pose,closed=False):
 row=0 if role=='A' else 1;cell=SHEET.crop((pose*512,row*512,(pose+1)*512,(row+1)*512))
 # Mouth detail is a generated source patch from the same character's closed pose.
 # This is illustrative energy-driven puppet animation, not phoneme-accurate lip sync.
 if pose==1 and closed:
  ref=SHEET.crop((0,row*512,512,(row+1)*512))
  source,target=((287,56,307,71),(276,56)) if role=='A' else ((236,56,258,71),(225,56))
  patch=ref.crop(source);mask=Image.new('L',patch.size,0);ImageDraw.Draw(mask).rounded_rectangle((2,2,patch.width-2,patch.height-2),radius=4,fill=255);mask=mask.filter(ImageFilter.GaussianBlur(1));cell.paste(patch,target,mask)
 return cell
@lru_cache(maxsize=90)
def actor(role,pose,closed,tilt):
 return sprite(role,pose,closed).resize((950,950),Image.Resampling.LANCZOS).rotate(tilt,Image.Resampling.BICUBIC,expand=False)
@lru_cache(None)
def bubble(index):
 ending=index==-1
 if ending:copy=[('EV Beregner',45),('evberegn.dk',73),('Gratis · uden login',37),('Like og følg på Facebook',32)];role='B'
 else:
  row=LINES[index];role=row['speaker'];copy=[]
  for part in row['caption'].split('\n'):
   current=''
   for word in part.split():
    candidate=(current+' '+word).strip()
    if current and font(48).getlength(candidate)>596:copy.append((current,48));current=word
    else:current=candidate
   if current:copy.append((current,48))
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer);parts=[];y=398
 for word,size in copy:
  f=font(size);b=d.textbbox((0,0),word,font=f);x=W/2-(b[0]+b[2])/2;parts.append((word,f,x,y-b[1],(x+b[0],y,x+b[2],y+b[3]-b[1])));y+=b[3]-b[1]+18
 l=min(x[4][0] for x in parts)-20;r=max(x[4][2] for x in parts)+20;top=376;bottom=max(x[4][3] for x in parts)+21
 assert SAFE[0]<=l and r<=SAFE[2] and SAFE[1]<=top and bottom+24<=SAFE[3],(index,l,r,top,bottom)
 shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((l+2,top+6,r+2,bottom+6),radius=23,fill=(0,0,0,70));layer=Image.alpha_composite(layer,shadow.filter(ImageFilter.GaussianBlur(5)));d=ImageDraw.Draw(layer)
 d.rounded_rectangle((l,top,r,bottom),radius=23,fill=(255,255,255,249))
 if not ending:
  x=430 if role=='A' else 650;d.polygon([(x-15,bottom-1),(x+15,bottom-1),(x,bottom+24)],fill=(255,255,255,249))
 for word,f,x,y,b in parts:d.text((x,y),word,font=f,fill=TEAL if 'EV Beregner' in word or 'evberegn.dk' in word else INK)
 return layer,{'index':index,'text':[p[0] for p in parts],'bounds':[l,top,r,bottom+24]}
def frame(n,qa=False):
 t=n/FPS;line=next((l for l in LINES if l['start']<=t<l['end']),None);im=BG.copy().convert('RGBA')
 for role,cx in [('A',305),('B',775)]:
  speaking=line is not None and line['speaker']==role
  shift=(1-ease(t/.85))*(-145 if role=='A' else 145) if t<.85 else 0
  pose=1 if speaking else (2 if line and line['turn'] in [2,4] else 0)
  closed=not speaking or energy(t)<.022
  tilt=round((.65*math.sin(t*3.6) if speaking else .25*math.sin(t*1.7)),1)
  person=actor(role,pose,closed,tilt);y=650+1.5*math.sin(t*1.7+(0 if role=='A' else 1.8));im.alpha_composite(person,(round(cx+shift-person.width/2),round(y)))
 if t>=CTA:im=Image.alpha_composite(im,bubble(-1)[0])
 elif line:im=Image.alpha_composite(im,bubble(line['index'])[0])
 if qa:
  layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
  for b in [(0,0,W,346),(0,1248,W,H),(0,0,86,H),(864,0,W,H)]:d.rectangle(b,fill=(255,0,0,60))
  im=Image.alpha_composite(im,layer)
 return im.convert('RGB')
def audio():
 n=len(VOICE);t=np.arange(n)/SR;beat=60/92;phase=t%beat;freq=np.array([164.8138,195.9977,246.9417,195.9977])[(t/(beat*2)).astype(int)%4]
 bed=.018*np.minimum(phase/.025,1)*np.exp(-phase*6)*(np.sin(2*np.pi*freq*t)+.14*np.sin(4*np.pi*freq*t));bed*=np.minimum(t/.5,1)*np.clip((SECONDS-t)/.8,0,1)
 for name,x in [('dialogue',VOICE),('original-music',bed),('premaster',VOICE+bed)]:
  with wave.open(str(F/(name+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.column_stack((x,x))*32767).clip(-32767,32767).astype('<i2').tobytes())
 return F/'premaster.wav'
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(F/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(l['start'])} --> {stamp(l['end'])}\n{l['caption']}" for i,l in enumerate(LINES))+'\n')
bounds=[bubble(i)[1] for i in range(len(LINES))]+[bubble(-1)[1]];(F/'CAPTION-BOUNDS.json').write_text(json.dumps(bounds,ensure_ascii=False,indent=2))
moments=[T['lines'][0]['start']+.3,T['turns'][1]['start']+.4,T['turns'][2]['start']+.4,T['turns'][3]['start']+.4,T['turns'][5]['start']+.4,CTA+.5]
for qa,name in [(False,'REVIEW.jpg'),(True,'SAFE-AREA-QA.jpg')]:
 contact=Image.new('RGB',(1620,480))
 for i,t in enumerate(moments):contact.paste(frame(round(t*FPS),qa).resize((270,480)),(i*270,0))
 contact.save(F/name,quality=95)
if '--preview-only' in sys.argv:sys.exit(0)
dest=F/f'EV-Beregner-{KEY}-dialog.mp4';assert not dest.exists(),'Use a new export name for revisions.'
sound=audio();cmd=['ffmpeg','-nostdin','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(sound),'-map','0:v:0','-map','1:a:0','-af','loudnorm=I=-16:TP=-1.5:LRA=8','-vf','scale=out_color_matrix=bt709:in_range=full:out_range=tv,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','19','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-c:a','aac','-ar','48000','-b:a','192k','-movflags','+faststart',str(dest)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
 for n in range(FRAMES):
  p.stdin.write(frame(n).tobytes())
  if n%240==0:print(KEY,n,'/',FRAMES,flush=True)
finally:p.stdin.close()
assert p.wait()==0
subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(dest),'-f','null','-'],check=True,capture_output=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]));(F/'FFPROBE.json').write_text(json.dumps(info,indent=2))
v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio');assert (v['width'],v['height'],v['codec_name'],a['codec_name'])==(W,H,'h264','aac')
proof={'id':KEY,'date':T['date'],'duration':float(info['format']['duration']),'width':W,'height':H,'fps':FPS,'full_decode':'PASS','dialogue':True,'speakers':T['roles'],'speech_sources':'A: Google Translate TTS / Danish; B: da-DK-JeppeNeural; current receipt is authoritative','speech_speed':1.0,'website_ui':False,'domain_end_only':True,'cta_start':CTA,'copyright':'Original generated art, original music, Noto Sans SIL OFL; fictional people, no testimonials or manufacturer badge','new_heygen_jobs':0,'purchases':0,'listening_review':'not_performed','official_meta_preview':'not_performed','sha256':hashlib.sha256(dest.read_bytes()).hexdigest()};(F/'QUALITY.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps({'id':KEY,'duration':proof['duration'],'full_decode':'PASS'}),flush=True)
