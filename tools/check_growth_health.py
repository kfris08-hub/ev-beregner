"""Check public freshness without measuring or manufacturing visitor traffic."""
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
import json,time
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk'
def fetch(path):
 with urlopen(Request(BASE+path+'?health='+str(time.time_ns()),headers={'User-Agent':'EVBeregnerTechnicalAudit/1.0','Cache-Control':'no-cache'}),timeout=20) as r:return json.load(r)
def age(data,field,now):
 stamp=datetime.fromisoformat(data[field].replace('Z','+00:00'))
 if stamp.tzinfo is None:raise ValueError('Timestamp without timezone')
 return (now-stamp).total_seconds()/3600
def assess(fuel,cars,now):
 errors=[];warnings=[]
 try:
  hours=age(fuel,'checked_at',now)
  if not -.17<=hours<=48:errors.append('Fuel verification is older than 48 hours or future dated')
  if fuel.get('price_type')!='pump_average':errors.append('Fuel source is not a pump-price average')
 except (KeyError,ValueError,TypeError):errors.append('Missing or invalid fuel timestamp')
 try:
  hours=age(cars,'checked_at',now)
  if not -.17<=hours<=72:errors.append('Car catalogue check is older than 72 hours or future dated')
  sources=cars.get('sources',[])
  if not any(s.get('status')=='ok' for s in sources):errors.append('No working car source')
  if any(s.get('status')!='ok' for s in sources):warnings.append('Some car sources failed; previously verified values may have been retained')
 except (KeyError,ValueError,TypeError):errors.append('Missing or invalid catalogue timestamp')
 return {'errors':errors,'warnings':warnings}
def main():
 now=datetime.now(timezone.utc);fuel=fetch('/data/fuel-prices.json');cars=fetch('/data/car-update-status.json');result=assess(fuel,cars,now)
 result.update(checked_at=now.isoformat(),fuel_checked_at=fuel.get('checked_at'),catalogue_checked_at=cars.get('checked_at'),clicks=None,impressions=None,traffic_source='No connected Search Console or Analytics access; technical checks only')
 out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'growth-health.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('GROWTH_HEALTH_RESULT '+json.dumps(result,ensure_ascii=False),flush=True)
 if result['errors']:raise SystemExit('Public data freshness check failed')
if __name__=='__main__':main()

