"""Read public ownership responses and one pending IndexNow notification."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.robotparser import RobotFileParser
BASE='https://www.evberegn.dk';root=Path.cwd()
config=json.loads((root/'data/search-notifications.json').read_text());filename=config['key_file'];key=(root/filename).read_text().strip()
def redact(value):return str(value).replace(key,'[ownership-key]')
def request(url,method='GET',data=None,agent='EVBeregn-IndexNow/1.0'):
 headers={'User-Agent':agent,'Cache-Control':'no-cache'}
 if data is not None:headers['Content-Type']='application/json; charset=utf-8'
 req=Request(url,data=data,method=method,headers=headers)
 try:
  with urlopen(req,timeout=25) as r:return r.status,r.read(65536),r.geturl(),{k.lower():v for k,v in r.headers.items()}
 except HTTPError as e:return e.code,e.read(65536),e.geturl(),{k.lower():v for k,v in e.headers.items()}
 except (URLError,TimeoutError) as e:return 0,str(e).encode(),url,{}
records=[]
for name,url in [('key_exact',BASE+'/'+filename),('key_query',BASE+'/'+filename+'?diagnose='+str(time.time_ns())),('robots',BASE+'/robots.txt')]:
 status,body,final,headers=request(url)
 result={'probe':name,'status':status,'final':redact(final),'headers':{k:v for k,v in headers.items() if k in ['content-type','server','location','age','x-cache','retry-after','x-served-by','via','x-msedge-ref','x-azure-ref']}}
 if name.startswith('key'):result['key_matches']=body.decode('utf-8','replace').strip()==key
 elif status==200:
  robots=RobotFileParser();robots.parse(body.decode().splitlines());result['bingbot_can_fetch_key']=robots.can_fetch('bingbot',BASE+'/'+filename);result['googlebot_can_fetch_key']=robots.can_fetch('Googlebot',BASE+'/'+filename)
 if status!=200:result['response']=redact(body[:2000].decode('utf-8','replace'))
 records.append(result);print('OWNERSHIP_PROBE '+json.dumps(result),flush=True)
if records[0]['status']!=200 or not records[0].get('key_matches'):raise SystemExit('Exact ownership file unavailable; no notification sent')
payload={'host':'www.evberegn.dk','key':key,'keyLocation':BASE+'/'+filename,'urlList':[BASE+'/']}
status,body,final,headers=request('https://api.indexnow.org/indexnow',method='POST',data=json.dumps(payload).encode())
result={'probe':'one_pending_homepage_notification','urls':1,'status':status,'endpoint':final,'response':redact(body[:4000].decode('utf-8','replace')),'headers':{k:v for k,v in headers.items() if k in ['content-type','server','location','retry-after','x-msedge-ref','x-azure-ref']},'indexing_confirmed':False}
records.append(result);print('INDEXNOW_DIAGNOSTIC '+json.dumps(result),flush=True)
out=root/'test-results';out.mkdir(exist_ok=True);(out/'indexnow-diagnostic.json').write_text(json.dumps(records,indent=2))
