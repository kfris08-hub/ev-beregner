"""Bounded daily variant of marketing/organic/render.py; original audio and UI."""
from pathlib import Path
from functools import lru_cache
import json,math,subprocess,wave,array
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'
PROOF=json.loads((OUT/'PROOF.json').read_text())
INK,WHITE,TEAL='#070c17','#ffffff','#10ddb2'
W,H,FPS,SECONDS=720,1280,24,20
SAFE=(144,232,576,832)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
@lru_cache(None)
def font(n):return ImageFont.truetype(FONT,n)
@lru_cache(None)
def screen(name):
    image=Image.open(OUT/(name+'.png')).convert('RGB')
    if name=='model':
        ratio=min(W/image.width,1030/image.height)
        image=image.resize((round(image.width*ratio),round(image.height*ratio)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGB',(W,H),INK);canvas.paste(image,((W-image.width)//2,90));return canvas
    return image.resize((W,H),Image.Resampling.LANCZOS)

def overlay(lines,y=270):
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer);yy=y;entries=[]
    for value,size,color in lines:
        f=font(size);b=d.textbbox((0,0),value,font=f)
        x=W/2-(b[0]+b[2])/2
        entries.append((value,f,x,yy-b[1],color,(x+b[0],yy,x+b[2],yy+b[3]-b[1])))
        yy+=b[3]-b[1]+16
    left=min(e[5][0] for e in entries)-12;right=max(e[5][2] for e in entries)+12
    top=y-12;bottom=max(e[5][3] for e in entries)+12
    assert SAFE[0]<=left and right<=SAFE[2] and SAFE[1]<=top and bottom<=SAFE[3],(left,top,right,bottom,lines)
    d.rounded_rectangle((left,top,right,bottom),radius=10,fill=(7,12,23,246))
    for value,f,x,y,color,_ in entries:d.text((x,y),value,font=f,fill=color)
    return layer

def music(path):
    # Original quiet plucked motif. No copyrighted recording, sample or service.
    sr=44100;pcm=array.array('h')
    for n in range(sr*SECONDS):
        t=n/sr;u=t%.625;hz=[220,277.1826,329.6276,277.1826][int(t/.625)%4]
        env=min(1,u/.02)*math.exp(-u*7)*min(1,(SECONDS-t)/.7)
        v=.07*env*(math.sin(2*math.pi*hz*t)+.2*math.sin(4*math.pi*hz*t))
        pcm.append(round(v*32767))
    with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())

def make_reel(date):
    km=date.endswith('16')
    hook=[('Din elbil.',44,WHITE),('Dine tal.',44,TEAL)] if km else [('75 km i elbil?',39,WHITE),('Regn på turen.',36,TEAL)]
    inputs=[('Brug din egen',35,WHITE),('samlede elpris',35,TEAL)] if km else [('Tilpas turen',37,WHITE),('og dit forbrug',35,TEAL)]
    result=[('Regneeksempel',26,WHITE),('32 kr. / 100 km',40,TEAL)] if km else [('Regneeksempel',26,WHITE),('33,75 kr. for turen',36,TEAL)]
    note=[('16 kWh/100 km',25,WHITE),('2,00 kr./kWh',25,WHITE),('Kun strømudgiften',23,WHITE)] if km else [('75 km · 18 kWh/100 km',21,WHITE),('2,50 kr./kWh',24,WHITE),('Kun strømudgiften',23,WHITE)]
    cta=[('EV Beregner',34,WHITE),('evberegn.dk',47,TEAL),('Gratis · uden login',22,WHITE)]
    events=[(0,4,'model',hook),(4,9,date+'-inputs',inputs),(9,15,date+'-result',result),(15,20,date+'-result',cta)]
    frames=[];sheet=[]
    for start,end,asset,copy in events:
        layer=overlay(copy,270 if start<9 else 285)
        if start==9:layer=Image.alpha_composite(layer,overlay(note,625))
        base=screen(asset).copy().convert('RGBA');settled=Image.alpha_composite(base,layer).convert('RGB')
        sheet.append(settled.resize((216,384)))
        frames.append((start,end,base,layer,settled))
    sound=OUT/(date+'-original-music.wav');music(sound)
    video=OUT/(date+'-reel.mp4')
    command=['ffmpeg','-nostdin','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(sound),'-map','0:v:0','-map','1:a:0','-af','loudnorm=I=-18:TP=-1.5:LRA=8','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(video)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for start,end,base,layer,settled in frames:
        stable=settled.tobytes()
        for f in range(round(start*FPS),round(end*FPS)):
            elapsed=f/FPS-start
            if elapsed<.25:
                a=layer.copy();a.putalpha(layer.getchannel('A').point(lambda x:round(x*min(1,elapsed/.25))))
                proc.stdin.write(Image.alpha_composite(base,a).convert('RGB').tobytes())
            else:proc.stdin.write(stable)
    proc.stdin.close();assert proc.wait()==0
    subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(video),'-f','null','-'],check=True,capture_output=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    v=next(x for x in info['streams'] if x['codec_type']=='video')
    assert (v['width'],v['height'],v['codec_name'])==(W,H,'h264')
    assert abs(float(info['format']['duration'])-20)<.1
    contact=Image.new('RGB',(864,384),INK)
    for i,img in enumerate(sheet):contact.paste(img,(i*216,0))
    contact.save(OUT/(date+'-reel-review.jpg'),quality=92)
    return {'file':video.name,'seconds':info['format']['duration'],'width':W,'height':H,'website_visible_from_second':0,'decode':'PASS','speech':False,'music':'original programmatic motif','listening_review':'not_performed','full_player_review':'not_performed','safe_area':'conservative provisional organic-Reel bounds, all essential overlay text measured'}

def centered(d,text,y,size,color=WHITE,width=920):
    f=font(size);b=d.textbbox((0,0),text,font=f);assert b[2]-b[0]<=width,text
    d.text((540-(b[0]+b[2])/2,y-b[1]),text,font=f,fill=color)

def repair_today():
    # One documented defect in the existing, not-yet-published Reel: the old
    # technical processing note in its first three seconds. Preserve the rest
    # of the edit, the original soundtrack, 20-second runtime and calendar slot.
    intro=Image.alpha_composite(screen('model').copy().convert('RGBA'),overlay([('Har du en elbil',36,WHITE),('i tankerne?',39,TEAL)],270)).convert('RGB')
    intro.save(OUT/'2026-11-15-clean-intro.png')
    original=OUT/'2026-11-15-original-QUEUED.mp4'
    result=OUT/'2026-11-15-reel-clean.mp4'
    graph='[1:v]trim=duration=3,setpts=PTS-STARTPTS,setsar=1[a];[0:v]trim=start=3:end=20,setpts=PTS-STARTPTS,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]'
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(original),'-loop','1','-framerate',str(FPS),'-i',str(OUT/'2026-11-15-clean-intro.png'),'-filter_complex',graph,'-map','[v]','-map','0:a:0','-frames:v','480','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(result)],check=True)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(result),'-f','null','-'],check=True,capture_output=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(result)]))
    assert abs(float(info['format']['duration'])-20)<.1
    return {'file':result.name,'seconds':info['format']['duration'],'fix':'Fresh opening image without technical processing note; full photographer/source/license retained','rest_of_video':'Original edit from second 3 onward','audio':'Original AAC copied unchanged','calendar_action':'Update existing UUID 8403383719013468039, preserve 15 November 10:00; never create a duplicate','decode':'PASS'}

def still(date,kind):
    story=kind=='story';height=1920 if story else 1350
    im=Image.new('RGB',(1080,height),INK);d=ImageDraw.Draw(im)
    offset=250 if story else 70
    centered(d,'EV Beregner',offset,39,TEAL)
    if date.endswith('16'):
        lines=['Hvad koster','dine 100 km?'];number='32 kr.';unit='i strøm pr. 100 km';inputs=['16 kWh/100 km','× 2,00 kr./kWh']
    else:
        lines=['Hvad koster','din tur på 75 km?'];number='33,75 kr.';unit='i strøm for turen';inputs=['75 km · 18 kWh/100 km','2,50 kr./kWh']
    for i,line in enumerate(lines):centered(d,line,offset+80+i*77,64)
    centered(d,'REGNEEKSEMPEL',offset+285,31,TEAL)
    centered(d,number,offset+350,112,TEAL)
    centered(d,unit,offset+485,38)
    for i,line in enumerate(inputs):centered(d,line,offset+585+i*50,34)
    centered(d,'Kun strømudgiften.',offset+715,31)
    centered(d,'Vælg din bil og brug dine egne tal.',offset+770,31)
    centered(d,'evberegn.dk',offset+865,76,TEAL)
    centered(d,'Gratis · uden login',offset+965,32)
    assert offset+1040<height
    path=OUT/(date+'-'+kind+'.jpg');im.save(path,quality=94,subsampling=0)
    return {'file':path.name,'width':1080,'height':height,'type':kind.upper(),'rights':'Original text/typography; no external photo or music','numeric_example_verified_in_live_calculator':True}

report={'date':'2026-11-15','style':{'direction':'Actual website with restrained kinetic type, dark/teal branding','font':'DejaVu Sans Bold','exclusions':['no fake UI','no current-price promise','no generated people or voices']},'videos':[],'stills':[],'new_heygen_jobs':0,'paid_services':0}
report['today_repair']=repair_today()
for date in ['2026-11-16','2026-11-17']:
    report['videos'].append(make_reel(date));report['stills'].append(still(date,'story'))
report['stills'].append(still('2026-11-17','post'))
(OUT/'RENDER-PROOF.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'videos':len(report['videos']),'stills':len(report['stills']),'decode':'PASS','live_inputs_and_results':'PASS'}))
