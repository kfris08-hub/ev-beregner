"""Generate a Danish dialogue revision without HeyGen or paid API credentials."""
from pathlib import Path
import asyncio,json,re,subprocess,wave
import edge_tts

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'voice-v2'
OUT.mkdir(exist_ok=True)
SR=24000
# One naturally Danish voice model. Small synthesis-time prosody differences
# distinguish the two roles; no post-production pitch shifter is used.
ROLES={'A':{'voice':'da-DK-JeppeNeural','rate':'+0%','pitch':'+4Hz'},'B':{'voice':'da-DK-JeppeNeural','rate':'-3%','pitch':'-5Hz'}}
TURNS=[
 ('A','arrival',[
  ('Jeg overvejer faktisk elbil efter den nye aftale.','Jeg overvejer faktisk elbil\nefter den nye aftale.')]),
 ('B','tax',[
  ('Ja, hvis aftalen bliver til lov,','Ja, hvis aftalen\nbliver til lov,'),
  ('udskydes stigningen i registreringsafgiften','udskydes stigningen i\nregistreringsafgiften'),
  ('med ét år.','med ét år.')]),
 ('A','cost_question',[
  ('Men hvad koster en elbil egentlig at køre i?','Men hvad koster en elbil\negentlig at køre i?')]),
 ('B','website',[
  ('Prøv E V Beregner.','Prøv EV Beregner.'),
  ('Find bilen, du overvejer,','Find bilen,\ndu overvejer,'),
  ('og regn på strømudgiften med dine egne tal.','og regn på strømudgiften\nmed dine egne tal.')]),
 ('A','app_question',[
  ('Skal jeg hente en app?','Skal jeg hente en app?')]),
 ('B','closing',[
  ('Nej, det er en gratis hjemmeside.','Nej, det er en\ngratis hjemmeside.'),
  ('Du finder linket i opslaget.','Du finder linket\ni opslaget.'),
  ('Og du behøver ikke oprette en konto.','Og du behøver ikke\noprette en konto.')]),
]
def norm(t):return ''.join(c for c in t.lower() if c.isalnum())
async def main():
 voices=await edge_tts.list_voices()
 assert any(v['ShortName']=='da-DK-JeppeNeural' for v in voices)
 timeline=[];word_report=[];chunks=[b'\0\0'*round(.25*SR)];cursor=.25
 for n,(speaker,section,parts) in enumerate(TURNS):
  text=' '.join(p[0] for p in parts)
  settings=ROLES[speaker]
  communicate=edge_tts.Communicate(text,**settings,boundary='WordBoundary',connect_timeout=12,receive_timeout=40)
  words=[];mp3=OUT/f'turn-{n}.mp3'
  with mp3.open('wb') as f:
   async for item in communicate.stream():
    if item['type']=='audio':f.write(item['data'])
    elif item['type']=='WordBoundary':words.append({k:item[k] for k in ['offset','duration','text']})
  assert mp3.stat().st_size>1000 and words
  raw=OUT/f'turn-{n}.wav'
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(mp3),'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(raw)],check=True)
  with wave.open(str(raw),'rb') as w:
   duration=w.getnframes()/SR;data=w.readframes(w.getnframes())
  if n:
   gap=.23;chunks.append(b'\0\0'*round(gap*SR));cursor+=gap
  keys=''.join(norm(w['text']) for w in words)
  assert keys==norm(text),(keys,norm(text))
  # Map canonical phrases to actual synthesis word boundaries, never estimated
  # character proportions or fabricated per-word times.
  ranges=[];at=0
  for w in words:
   size=len(norm(w['text']));ranges.append((at,at+size,w));at+=size
  startkey=0
  for spoken,caption in parts:
   endkey=startkey+len(norm(spoken))
   selected=[w for lo,hi,w in ranges if hi>startkey and lo<endkey]
   assert selected
   a=selected[0]['offset']/1e7
   b=(selected[-1]['offset']+selected[-1]['duration'])/1e7
   assert 0<=a<b<=duration+.25
   timeline.append({'index':len(timeline),'speaker':speaker,'section':section,'spoken':spoken,'caption':caption,'start':cursor+a,'end':cursor+min(b+.07,duration),'words':[{'text':w['text'],'start':cursor+w['offset']/1e7,'end':cursor+(w['offset']+w['duration'])/1e7} for w in selected]})
   startkey=endkey
  word_report.append({'turn':n,'speaker':speaker,'settings':settings,'spoken':text,'seconds':duration,'words':words})
  chunks.append(data);cursor+=duration
 chunks.append(b'\0\0'*round(1.2*SR));cursor+=1.2
 with wave.open(str(OUT/'dialogue.wav'),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(b''.join(chunks))
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'dialogue.wav'),'-c:a','libmp3lame','-b:a','128k',str(OUT/'dialogue.mp3')],check=True)
 report={'sample_rate':SR,'seconds':cursor,'lines':timeline,'speech_model':'Microsoft da-DK-JeppeNeural via edge-tts 7.3.1','roles':ROLES,'post_pitch_shifting':False,'word_alignment':'service-returned WordBoundary metadata; UTF-8 normalized source text matches','pronunciation_notes':{'brand':'E V Beregner with Danish voice locale','domain':'The address is displayed graphically; speech says the link is in the post.','legal':'conditional clause comes first; whole sentence is synthesized together'},'turns':word_report,'listening_review':'not_performed','speech_source':'https://github.com/rany2/edge-tts','generation':'Microsoft Edge online Read Aloud voice, no paid Azure API or credentials; two prosody settings of one native Danish voice','heygen_generations':0,'paid_services':0}
 (OUT/'TIMELINE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({'seconds':cursor,'phrases':len(timeline),'turns':len(TURNS),'bytes':(OUT/'dialogue.mp3').stat().st_size}))
try:asyncio.run(main())
except Exception as e:
 print('VOICE_GENERATION_BLOCKED: '+type(e).__name__+': '+str(e)[:220])
 raise SystemExit(1)
