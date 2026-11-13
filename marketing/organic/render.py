"""Two original micro-demos with real website captures, controlled Danish copy.

Style: documentary interface demo, original dark/teal brand, hard cuts and
restrained overlays. No avatar, generated UI, external music or paid service.
Run: python marketing/organic/capture.py && python marketing/organic/render.py
"""
from pathlib import Path
from functools import lru_cache
import json, math, subprocess, wave, array
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / 'output'
W, H, FPS = 720, 1280, 24
INK, WHITE, TEAL = '#070c17', '#ffffff', '#10ddb2'
FONTS = Path('/usr/share/fonts/truetype/dejavu')
@lru_cache(None)
def font(size, bold=True):
    return ImageFont.truetype(str(FONTS / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')), size)
@lru_cache(None)
def screen(name):
    return Image.open(OUT / (name+'.png')).convert('RGB').resize((W,H), Image.Resampling.LANCZOS)
def label(im, lines):
    layer = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(layer)
    y=98
    for line in lines:
        f=font(37)
        assert d.textlength(line,font=f)<=602, line
        d.rounded_rectangle((35,y-8,657,y+51),radius=9,fill=(7,12,23,242))
        d.text((51,y),line,font=f,fill=WHITE)
        y+=60
    return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
def cta():
    im=Image.new('RGB',(W,H),INK);d=ImageDraw.Draw(im)
    copy=[('Din bil. Dine tal.',47,WHITE,360),('EV Beregner',52,TEAL,460),('evberegn.dk',66,TEAL,575),('20 gratis beregnere',35,WHITE,710),('Direkte i browseren',31,WHITE,772),('Uden login',31,WHITE,820)]
    for text,size,color,y in copy:
        f=font(size);tw=d.textlength(text,font=f)
        assert tw<620
        d.text(((W-tw)/2,y),text,font=f,fill=color)
    return im
VIDEOS = [
 {'file':'vaelg-din-elbil.mp4','seconds':20,'beats':[
  (0,3,'model',['Har du en elbil i tankerne?']),
  (3,7,'search',['Find din model']),
  (7,11,'selected',['Vælg bilen på hjemmesiden']),
  (11,16,'kilometer',['Regn med bilens forbrug']),
  (16,20,None,[]) ]},
 {'file':'din-bil-din-ladepris.mp4','seconds':20,'beats':[
  (0,4,'charge',['Hvad koster din opladning?']),
  (4,8,'model',['Start med din bilmodel']),
  (8,12,'charge',['Tilpas procent og elpris']),
  (12,16,'charge-result',['Se din beregnede ladepris']),
  (16,20,None,[]) ]}
]

def music(path, seconds):
    # Original quiet three-note motif; no third-party recording or composition.
    sr=44100; pcm=array.array('h')
    for n in range(sr*seconds):
        t=n/sr;beat=int(t/0.75);u=t%0.75;hz=[220.,277.1826,329.6276,277.1826][beat%4]
        envelope=min(1.,u/.025)*math.exp(-u*7)*min(1.,(seconds-t)/.6)
        value=.055*envelope*(math.sin(2*math.pi*hz*t)+.24*math.sin(4*math.pi*hz*t))
        pcm.append(int(value*32767))
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())

report={'style':'documentary interface demo, dark/teal','sources':'real evberegn.dk captures','heygen_generations':0,'videos':[]}
for number,spec in enumerate(VIDEOS,1):
    sound=OUT/f'motif-{number}.wav';music(sound,spec['seconds'])
    path=OUT/spec['file']
    cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(sound),'-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-shortest',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    contact=[]
    for start,end,asset,lines in spec['beats']:
        base=label(screen(asset).copy(),lines) if asset else cta()
        # Annotation is a conventional focus marker; no invented website control.
        for frame in range(round(start*FPS),round(end*FPS)):
            image=base.copy()
            if asset in ('search','charge'):
                t=frame/FPS-start
                if .15<t<.85:
                    d=ImageDraw.Draw(image);r=9+int(20*(t-.15)/.7)
                    x,y=(W-90,420 if asset=='search' else 750)
                    d.ellipse((x-r,y-r,x+r,y+r),outline=TEAL,width=3)
            proc.stdin.write(image.tobytes())
        thumb=base.resize((216,384))
        contact.append(thumb)
    proc.stdin.close();assert proc.wait()==0
    sheet=Image.new('RGB',(216*len(contact),384),INK)
    for i,im in enumerate(contact):sheet.paste(im,(i*216,0))
    sheet.save(OUT/f'review-{number}.jpg',quality=90)
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-print_format','json','-show_streams','-show_format',str(path)]))
    assert float(metadata['format']['duration'])>=19.9
    v=next(s for s in metadata['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['codec_name'])==(W,H,'h264')
    report['videos'].append({'file':spec['file'],'bytes':path.stat().st_size,'seconds':metadata['format']['duration'],'width':W,'height':H,'frame_rate':v['r_frame_rate'],'website_visible_from_second':0,'speech':False,'text':spec['beats']})

for number,(asset,lines) in enumerate([
 ('model',['Din næste elbil?','Se modellen. Regn videre.']),
 ('kilometer-result',['Din bil. Din elpris.','Beregn med dine egne tal.'])],1):
    im=screen(asset).copy().resize((720,1280))
    # Feed crop retains the real site with a controlled title and direct CTA.
    im=im.crop((0,0,720,900))
    im=label(im,lines)
    d=ImageDraw.Draw(im);d.rectangle((0,795,720,900),fill=INK)
    d.text((45,811),'evberegn.dk',font=font(48),fill=TEAL)
    im.save(OUT/f'opslag-{number}.png')

(OUT/'render-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
