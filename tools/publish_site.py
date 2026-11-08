"""Request Pages with retries and confirm the actual public data before success."""
import argparse, json, os, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).parents[1]
BASE='https://www.evberegn.dk/'
RETRYABLE={408,429,500,502,503,504}

def request_build(repository,token):
    req=Request('https://api.github.com/repos/'+repository+'/pages/builds',data=b'{}',method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'EVBeregn-Pages/1.0'})
    try:
        with urlopen(req,timeout=20) as r:r.read(65536)
        return 'requested'
    except HTTPError as e:
        if e.code==409:return 'already-pending'
        if e.code in RETRYABLE:return 'temporary-error'
        raise RuntimeError('Pages afviste udgivelsen (HTTP '+str(e.code)+')') from None
    except (URLError,TimeoutError):return 'temporary-error'

def public_matches(relative,expected,field,attempt):
    # No authorization header is ever sent to the public website.
    url=BASE+relative+'?publication='+str(time.time_ns())+'-'+str(attempt)
    try:
        req=Request(url,headers={'User-Agent':'EVBeregn-publication-check/1.0','Cache-Control':'no-cache'})
        with urlopen(req,timeout=12) as r:
            body=r.read(1000001)
            if len(body)>1000000:return False
            actual=json.loads(body)
        return actual.get(field)==expected[field] and (relative!='data/fuel-prices.json' or actual.get('price_type')=='pump_average')
    except (HTTPError,URLError,TimeoutError,ValueError,AttributeError):return False

def publish(relative,expected,repository,token,field='checked_at',max_wait=480,request=None,check=None,pause=time.sleep,clock=time.monotonic):
    if relative not in {'data/fuel-prices.json','data/car-update-status.json'}:raise ValueError('Unsupported publication target')
    if not expected.get(field):raise ValueError('Missing publication identifier')
    if not repository or not token:raise ValueError('Missing GitHub publication credentials')
    request=request or request_build;check=check or public_matches
    deadline=clock()+max_wait;attempt=0;requests=0;next_request=clock()
    while clock()<deadline:
        if check(relative,expected,field,attempt):
            print('PUBLICATION_CONFIRMED '+json.dumps({'path':relative,'checked_at':expected[field],'build_requests':requests}),flush=True)
            return
        if clock()>=next_request:
            outcome=request(repository,token);requests+=1
            print('PUBLICATION_REQUEST '+json.dumps({'attempt':requests,'outcome':outcome}),flush=True)
            # A 502 can still mean GitHub queued the build. Verify before retrying.
            delay=min(60,5*2**min(requests-1,4)) if outcome=='temporary-error' else 120
            next_request=clock()+delay
        pause(5);attempt+=1
    raise RuntimeError('Udgivelsen kunne ikke bekræftes på den offentlige hjemmeside; tidligere offentlig version kan stadig være aktiv')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',required=True,choices=['data/fuel-prices.json','data/car-update-status.json']);parser.add_argument('--max-wait',type=int,default=480);args=parser.parse_args()
    expected=json.loads((ROOT/args.verify).read_text())
    publish(args.verify,expected,os.environ.get('GITHUB_REPOSITORY'),os.environ.get('GH_TOKEN'),max_wait=args.max_wait)

if __name__=='__main__':main()
