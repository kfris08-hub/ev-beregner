"""Publish real, standard-fuel pump-price averages from OK's public station API."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import argparse,json,time
ROOT=Path(__file__).parents[1]
URL='https://mobility-prices.ok.dk/api/v1/fuel-prices'
DOCS='https://www.ok.dk/globalassets/pdfer/diverse/offentlig-api-dokumentation.pdf'
PRODUCTS={'blyfri 95':'petrol95','svovlfri diesel':'diesel'}
class FuelDataError(ValueError):pass

def timestamp(value):
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None:raise ValueError()
        return parsed.astimezone(timezone.utc)
    except (AttributeError,ValueError,TypeError):raise FuelDataError('Invalid station timestamp')

def amount(value):
    if isinstance(value,bool) or not isinstance(value,(int,float,str)):raise FuelDataError('Invalid fuel price')
    try:v=Decimal(str(value))
    except InvalidOperation:raise FuelDataError('Invalid fuel price')
    if not v.is_finite() or not Decimal('5')<=v<=Decimal('60'):raise FuelDataError('Price outside DKK/l bounds')
    return v

def snapshot(payload,now=None,previous=None,min_stations=200):
    now=now or datetime.now(timezone.utc)
    items=payload.get('items') if isinstance(payload,dict) else None
    if not isinstance(items,list) or not items:raise FuelDataError('Missing station list')
    values={'petrol95':[],'diesel':[]};seen={};included_times=[];excluded=0
    for station in items:
        if not isinstance(station,dict):raise FuelDataError('Invalid station record')
        identifier=station.get('facility_number')
        if isinstance(identifier,bool) or not isinstance(identifier,(str,int)) or not str(identifier).strip():raise FuelDataError('Missing station identity')
        identifier=str(identifier)
        if identifier in seen:
            if station!=seen[identifier]:raise FuelDataError('Conflicting duplicate station')
            continue
        seen[identifier]=station
        try:changed=timestamp(station.get('last_updated_time'))
        except FuelDataError:excluded+=1;continue
        if changed<now-timedelta(hours=72) or changed>now+timedelta(minutes=10):excluded+=1;continue
        prices=station.get('prices')
        if not isinstance(prices,list):raise FuelDataError('Missing station prices')
        selected={}
        for p in prices:
            if not isinstance(p,dict):raise FuelDataError('Invalid product')
            key=PRODUCTS.get(str(p.get('product_name','')).strip().casefold())
            if not key:continue # Oktan 100, premium and alternative fuels never enter the averages.
            price=amount(p.get('price'))
            if key in selected and selected[key]!=price:raise FuelDataError('Conflicting product prices')
            selected[key]=price
        for key,price in selected.items():values[key].append(price)
        if selected:included_times.append(changed)
    counts={key:len(v) for key,v in values.items()}
    for key,count in counts.items():
        if count<min_stations:raise FuelDataError('Too few current stations for '+key)
        if previous and previous.get('price_type')=='pump_average':
            old=previous.get('coverage',{}).get(key,0)
            if isinstance(old,(int,float)) and count<old*.75:raise FuelDataError('Station coverage dropped more than 25%')
    mean=lambda xs:float((sum(xs)/Decimal(len(xs))).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
    checked=now.isoformat(timespec='seconds')
    return {'schema_version':2,'petrol95':mean(values['petrol95']),'diesel':mean(values['diesel']),
            'currency':'DKK','unit':'DKK/l','price_type':'pump_average','source':'OK-pumpepriser · gennemsnit',
            'source_chain':'OK','source_url':URL,'documentation_url':DOCS,
            'updated':checked,'checked_at':checked,'source_date':now.astimezone(ZoneInfo('Europe/Copenhagen')).date().isoformat(),
            'coverage':counts,'range':{key:{'min':float(min(v)),'max':float(max(v))} for key,v in values.items()},
            'latest_station_update':max(included_times).isoformat(timespec='seconds'),
            'oldest_station_update':min(included_times).isoformat(timespec='seconds'),
            'station_max_age_hours':72,'excluded_stations':excluded,
            'method':'Unweighted mean: each current OK station counts once per standard product. Not a national average or a local quote.'}

def download():
    for attempt in range(2):
        try:
            req=Request(URL,headers={'User-Agent':'EVBeregn/1.0 (+https://www.evberegn.dk)','Accept':'application/json'})
            with urlopen(req,timeout=30) as response:
                if urlsplit(response.url).hostname!='mobility-prices.ok.dk':raise FuelDataError('Unexpected source redirect')
                body=response.read(5000001)
            if len(body)>5000000:raise FuelDataError('Oversized price response')
            return json.loads(body)
        except Exception:
            if attempt:raise
            time.sleep(2)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fixture',type=Path);args=parser.parse_args()
    path=ROOT/'data/fuel-prices.json'
    previous=json.loads(path.read_text()) if path.exists() else None
    raw=json.loads(args.fixture.read_text()) if args.fixture else download()
    result=snapshot(raw,previous=previous)
    path.parent.mkdir(exist_ok=True)
    # Nothing is replaced until the complete snapshot has passed validation.
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');temporary.replace(path)
    print('FUEL_PUMP_RESULT '+json.dumps(result,ensure_ascii=False))

def saved_reference(root,now=None):
    """Only verified, recent pump snapshots may seed static calculator examples."""
    now=now or datetime.now(timezone.utc)
    try:
        data=json.loads((Path(root)/'data/fuel-prices.json').read_text())
        if data.get('price_type')!='pump_average' or data.get('currency')!='DKK' or data.get('unit')!='DKK/l':return None
        checked=timestamp(data.get('checked_at',data.get('updated')))
        if checked<now-timedelta(hours=48) or checked>now+timedelta(minutes=10):return None
        for key in ('petrol95','diesel'):amount(data[key])
        return data
    except (OSError,ValueError,KeyError,TypeError):return None

if __name__=='__main__':main()
