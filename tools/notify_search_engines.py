"""Notify IndexNow of real changes after verifying the publicly hosted ownership key."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import argparse,json,re,time,xml.etree.ElementTree as ET
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';ENDPOINT='https://api.indexnow.org/indexnow'
def own_url(url):
 p=urlsplit(url)
 return p.scheme=='https' and p.netloc=='www.evberegn.dk' and not p.query and not p.fragment and '..' not in p.path and p.path.startswith('/')
def snapshot(body):
 tree=ET.fromstring(body);out={}
 for node in tree:
  url=node.findtext('{*}loc');stamp=node.findtext('{*}lastmod')
  if not url or not own_url(url) or url in out:raise ValueError('Invalid or duplicate canonical URL')
  out[url]={'lastmod':stamp,'images':sorted(i.text for i in node.findall('.//{http://www.google.com/schemas/sitemap-image/1.1}loc'))}
 if not out or len(out)>10000:raise ValueError('Invalid sitemap size')
 return out
def changed(current,previous):
 if any(not own_url(u) for u in previous):raise ValueError('Unexpected host in notification state')
 return sorted([u for u,v in current.items() if previous.get(u)!=v]+[u for u in previous if u not in current])
def submit(payload,opener=urlopen,pause=time.sleep):
 data=json.dumps(payload).encode()
 for attempt in range(3):
  try:
   req=Request(ENDPOINT,data=data,method='POST',headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'EVBeregn-IndexNow/1.0'})
   with opener(req,timeout=25) as response:status=response.status;response.read(65536)
   if status not in (200,202):raise RuntimeError('Unexpected IndexNow status '+str(status))
   return status
  except HTTPError as error:
   if error.code==429:
    retry=error.headers.get('Retry-After','60') if error.headers else '60'
    seconds=float(retry) if retry.isdigit() else 60
    if seconds>60 or attempt==2:raise RuntimeError('IndexNow rate limited; previous state retained') from None
    pause(seconds)
   elif error.code in (500,502,503,504) and attempt<2:pause(3*(attempt+1))
   else:raise RuntimeError('IndexNow submission rejected (HTTP '+str(error.code)+'); previous state retained') from None
  except (URLError,TimeoutError):
   if attempt==2:raise
   pause(3*(attempt+1))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
 config=json.loads((ROOT/'data/search-notifications.json').read_text());key_file=config['key_file'];key=(ROOT/key_file).read_text().strip()
 if not re.fullmatch(r'[a-f0-9]{32}',key) or key_file!=key+'.txt':raise ValueError('Invalid ownership key file')
 current=snapshot((ROOT/'sitemap.xml').read_bytes());state_path=ROOT/'.github/state/indexnow.json';state=json.loads(state_path.read_text()) if state_path.exists() else {};previous=state.get('confirmed_snapshot',{})
 urls=changed(current,previous);out=ROOT/'test-results';out.mkdir(exist_ok=True)
 if args.dry_run:
  print('INDEXNOW_PLAN '+json.dumps({'changed_urls':len(urls),'ownership_file':key_file,'submission':False}));return
 if not urls:print('INDEXNOW_RESULT '+json.dumps({'submitted':0,'meaning':'No canonical changes since the last confirmed submission'}));return
 nonce=str(time.time_ns())
 with urlopen(Request(BASE+'/'+key_file+'?verify='+nonce,headers={'User-Agent':'EVBeregn-IndexNow/1.0','Cache-Control':'no-cache'}),timeout=20) as r:published_key=r.read(1024).decode().strip()
 if published_key!=key:raise RuntimeError('Ownership key is not public yet; no URL submitted')
 with urlopen(Request(BASE+'/sitemap.xml?verify='+nonce,headers={'User-Agent':'EVBeregn-IndexNow/1.0','Cache-Control':'no-cache'}),timeout=20) as r:published=snapshot(r.read(2000000))
 if published!=current:raise RuntimeError('Published sitemap differs; no URL submitted')
 payload={'host':'www.evberegn.dk','key':key,'keyLocation':BASE+'/'+key_file,'urlList':urls}
 status=submit(payload)
 result={'checked_at':datetime.now(timezone.utc).isoformat(),'submitted':len(urls),'http_status':status,'meaning':'Received, not a confirmation of indexing' if status==200 else 'Received; ownership validation pending','google_submission':False}
 if status==200:state['confirmed_snapshot']=current
 state['last_submission']=result;state_path.parent.mkdir(parents=True,exist_ok=True);state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
 (out/'indexnow-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('INDEXNOW_RESULT '+json.dumps(result),flush=True)
if __name__=='__main__':main()

