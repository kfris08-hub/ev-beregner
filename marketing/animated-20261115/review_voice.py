"""Independent Danish speech recognition; no script prompt or paid API."""
from pathlib import Path
import json, re
from faster_whisper import WhisperModel

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'voice-v2'
model=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=2)
segments,info=model.transcribe(str(OUT/'dialogue.mp3'),language='da',beam_size=5,word_timestamps=True,vad_filter=True)
rows=[]
for s in segments:
 rows.append({'start':s.start,'end':s.end,'text':s.text,'avg_logprob':s.avg_logprob,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in (s.words or [])]})
text=' '.join(s['text'].strip() for s in rows)
normalized=''.join(c for c in text.lower() if c.isalnum())
checks={x:x in normalized for x in ['elbil','lov','registreringsafgift','år','gratis','hjemmeside','strøm']}
report={'engine':'faster-whisper medium, Danish, CPU int8, no initial prompt','transcript':text,'segments':rows,'anchor_checks':checks,'listening_review':'not_performed','warning':'Recognition is independent but not human listening or proof of naturalness. Brand/domain spellings may be uncertain.','language':info.language,'language_probability':info.language_probability}
(OUT/'ASR-REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'transcript':text,'anchor_checks':checks},ensure_ascii=False))
