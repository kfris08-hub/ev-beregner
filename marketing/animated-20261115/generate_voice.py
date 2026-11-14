"""Free Danish dialogue, generated in a public Actions runner; no paid APIs."""
from pathlib import Path
import json, subprocess, wave, urllib.request, shutil
from piper import PiperVoice

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'voice-output'
OUT.mkdir(exist_ok=True)
MODEL='da_DK-talesyntese-medium.onnx'
BASE='https://huggingface.co/rhasspy/piper-voices/resolve/main/da/da_DK/talesyntese/medium/'
for name in [MODEL,MODEL+'.json','MODEL_CARD']:
    with urllib.request.urlopen(BASE+name, timeout=60) as r:
        (OUT/name).write_bytes(r.read())
card=(OUT/'MODEL_CARD').read_text()
assert 'CC0' in card
voice=PiperVoice.load(str(OUT/MODEL))
lines=[
 ('A','Jeg overvejer elbil efter den nye aftale.','Jeg overvejer elbil\nefter den nye aftale.'),
 ('B','Stigningen i registreringsafgiften udskydes ét år,','Stigningen i\nregistreringsafgiften\nudskydes ét år,'),
 ('B','hvis aftalen bliver til lov.','hvis aftalen\nbliver til lov.'),
 ('A','Men hvad koster en elbil at køre i?','Men hvad koster\nen elbil at køre i?'),
 ('B','Prøv E V Beregner.','Prøv EV Beregner.'),
 ('B','Find bilen, du overvejer,','Find bilen,\ndu overvejer,'),
 ('B','og beregn strømudgiften med dine egne tal.','og beregn strømudgiften\nmed dine egne tal.'),
 ('A','Er det en app?','Er det en app?'),
 ('B','Det er en gratis hjemmeside.','Det er en\ngratis hjemmeside.'),
 ('B','E V beregn punktum D K. Uden login.','evberegn.dk\nUden login.'),
]
sr=22050
timeline=[]
chunks=[b'\0\0'*round(.4*sr)]
cursor=.4
previous=None
for n,(speaker,text,caption) in enumerate(lines):
    raw=OUT/f'raw-{n}.wav'
    with wave.open(str(raw),'wb') as w:
        voice.synthesize_wav(text,w)
    target=OUT/f'line-{n}.wav'
    # Distinguish the two original fictional characters without cloning anyone.
    # Pitch is a creative voice setting; rate stays at 1.0.
    pitch=1.045 if speaker=='A' else .925
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'rubberband=tempo=1:pitch={pitch}', '-ar',str(sr),'-ac','1','-c:a','pcm_s16le',str(target)],check=True)
    with wave.open(str(target),'rb') as w:
        assert w.getframerate()==sr and w.getsampwidth()==2
        data=w.readframes(w.getnframes())
        duration=w.getnframes()/sr
    gap=.22 if previous==speaker else .32
    if n==0:gap=0
    chunks.append(b'\0\0'*round(gap*sr));cursor+=gap
    timeline.append({'index':n,'speaker':speaker,'spoken':text,'caption':caption,'start':cursor,'end':cursor+duration})
    chunks.append(data);cursor+=duration;previous=speaker
chunks.append(b'\0\0'*round(1.2*sr));cursor+=1.2
with wave.open(str(OUT/'dialogue.wav'),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(b''.join(chunks))
subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'dialogue.wav'),'-c:a','libmp3lame','-b:a','96k',str(OUT/'dialogue.mp3')],check=True)
report={'sample_rate':sr,'seconds':cursor,'lines':timeline,'speech_model':'Piper da_DK-talesyntese-medium','dataset_license':'CC0','model_card':card,'speech_source':'https://huggingface.co/rhasspy/piper-voices/blob/main/da/da_DK/talesyntese/medium/MODEL_CARD','generation':'offline neural speech with two tonal variations of one public model; no real-person clone','listening_review':'not_performed','captions_timing':'measured full utterance WAV intervals, no guessed word alignment','heygen_generations':0,'paid_services':0}
(OUT/'TIMELINE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'seconds':cursor,'lines':len(timeline),'speech_bytes':(OUT/'dialogue.mp3').stat().st_size}))
