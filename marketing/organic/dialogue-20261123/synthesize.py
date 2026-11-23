"""Batch two Danish neural voices, align captions to actual provider words.
No HeyGen, paid APIs, cloning, artificial pitch effects or time-stretching.
"""
from pathlib import Path
import os,sys,json,asyncio,importlib,subprocess,wave
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/workspace/evberegn-marketing/reels/bilvalg-samtale-20261116/vendor')
import edge_tts
for name in ['edge_tts.voices','edge_tts.communicate']:importlib.import_module(name)._SSL_CTX.load_verify_locations(cafile=os.environ.get('SSL_CERT_FILE','/etc/ssl/certs/ca-certificates.crt'))
S=json.loads((ROOT/'scripts.json').read_text())
def norm(t):return ''.join(c for c in t.lower() if c.isalnum())
async def main():
 receipts=[];all_parts={};audio={}
 for role,settings in S['roles'].items():
  parts=[]
  for fi,film in enumerate(S['films']):
   for ti,turn in enumerate(film['turns']):
    if turn['speaker']==role:
     for pi,(spoken,caption) in enumerate(turn['parts']):parts.append({'film':fi,'turn':ti,'part':pi,'spoken':spoken,'caption':caption})
  if role=='A':
   sys.path.insert(0,'/workspace/evberegn-marketing/reels/bilvalg-samtale-20261116/gtts-vendor')
   from gtts import gTTS
   chunks=[];cursor=0.;row={'speaker':role,'provider':'Google Translate TTS via gTTS, Danish','status':'STARTED','change':'Female Edge voice returned no audio for both long and short inputs; use a different working provider, not the rejected Piper voice.'};receipts.append(row)
   for part in parts:
    mp3=ROOT/'voice'/f'A-{part["film"]}-{part["turn"]}-{part["part"]}.mp3'
    if not mp3.exists() or mp3.stat().st_size<1000:gTTS(part['spoken'],lang='da',tld='com',timeout=(5,12)).save(str(mp3))
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(mp3),'-ar','48000','-ac','1','-c:a','pcm_s16le','-f','s16le','pipe:1'])
    duration=len(raw)/2/48000;part.update(source_start=cursor,source_end=cursor+duration,words=[],timing='Measured complete phrase audio, not word alignment');chunks.append(raw);chunks.append(b'\0\0'*2400);cursor+=duration+.05
    print(json.dumps({'speaker':'A','film':part['film'],'turn':part['turn'],'part':part['part'],'status':'OK'}),flush=True)
   audio[role]=b''.join(chunks);all_parts[role]=parts;row.update(status='OK',phrases=len(parts));(ROOT/'SPEECH-RECEIPT.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2));continue
  text=' '.join(p['spoken'] for p in parts);mp3=ROOT/'voice'/f'{role}-batch.mp3';meta=ROOT/'voice'/f'{role}-batch.json'
  row={'speaker':role,'voice':settings['voice'],'characters':len(text),'status':'STARTED','rate':'+0%','pitch':'+0Hz','attempts':1};receipts.append(row)
  (ROOT/'SPEECH-RECEIPT.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2))
  if not mp3.exists() or mp3.stat().st_size<1000:
   try:
    c=edge_tts.Communicate(text,voice=settings['voice'],rate='+0%',proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy'),connect_timeout=6,receive_timeout=18,boundary='WordBoundary')
    await asyncio.wait_for(c.save(str(mp3),str(meta)),timeout=38)
    assert mp3.stat().st_size>1000
   except Exception as e:
    row.update(status='FAILED',error=type(e).__name__+': '+str(e)[:220]);(ROOT/'SPEECH-RECEIPT.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2));raise
  words=[json.loads(x) for x in meta.read_text().splitlines() if x.strip()];words=[x for x in words if x.get('type')=='WordBoundary']
  assert norm(text)==''.join(norm(w['text']) for w in words),'Provider words do not match input'
  ranges=[];at=0
  for w in words:
   length=len(norm(w['text']));ranges.append((at,at+length,w));at+=length
  start=0
  for part in parts:
   end=start+len(norm(part['spoken']));selected=[w for lo,hi,w in ranges if hi>start and lo<end];assert selected
   part.update(source_start=selected[0]['offset']/1e7,source_end=(selected[-1]['offset']+selected[-1]['duration'])/1e7,words=selected);start=end
  raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(mp3),'-ar','48000','-ac','1','-c:a','pcm_s16le','-f','s16le','pipe:1'])
  audio[role]=raw;all_parts[role]=parts;row.update(status='OK',bytes=mp3.stat().st_size,words=len(words));(ROOT/'SPEECH-RECEIPT.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2));print(json.dumps(row),flush=True)
 for fi,film in enumerate(S['films']):
  dest=ROOT/film['id'];dest.mkdir(exist_ok=True);clock=.12;turns=[];lines=[]
  for ti,turn in enumerate(film['turns']):
   role=turn['speaker'];parts=[p for p in all_parts[role] if p['film']==fi and p['turn']==ti];a=max(0,parts[0]['source_start']-.045);b=parts[-1]['source_end']+.14
   chunk=audio[role][round(a*48000)*2:round(b*48000)*2];duration=len(chunk)/2/48000;wav=ROOT/'voice'/f'{film["id"]}-{ti}.wav'
   if not wav.exists():
    with wave.open(str(wav),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(chunk)
   turns.append({'index':ti,'speaker':role,'spoken':' '.join(p['spoken'] for p in parts),'source':str(wav.relative_to(ROOT)),'source_in':a,'source_out':b,'start':clock,'end':clock+duration,'speed':1.0})
   for part in parts:
    lines.append({'index':len(lines),'speaker':role,'turn':ti,'spoken':part['spoken'],'caption':part['caption'],'start':clock+part['source_start']-a,'end':min(clock+duration,clock+part['source_end']-a+.10)})
   clock+=duration+.26
  for prev,nxt in zip(lines,lines[1:]):prev['end']=min(prev['end'],nxt['start'])
  timeline={'date':film['date'],'id':film['id'],'theme':film['theme'],'destination':film['destination'],'roles':S['roles'],'turns':turns,'lines':lines,'cta_start':clock,'duration':clock+3.4,'speech_speed':1.0,'listening_review':'not_performed'}
  (dest/'TIMELINE.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2));print(json.dumps({'film':film['id'],'duration':timeline['duration']}),flush=True)
 (ROOT/'WORD-ALIGNMENT.json').write_text(json.dumps(all_parts,ensure_ascii=False,indent=2))
asyncio.run(main())
