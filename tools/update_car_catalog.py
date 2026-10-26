"""Import documented Danish variants; failures never erase the last working catalogue.

The CC BY feed documents exact Danish *prices*, not variant-specific consumption.
Retail DTOs carry variant consumption in Wh/km. Ambiguous batteryMaxPower is
intentionally NOT imported as DC charging power (it may be motor power).
"""
from pathlib import Path
from datetime import date, datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse, copy, hashlib, json, math, re, time, unicodedata
from car_catalog import load_catalog
ROOT=Path(__file__).parents[1]
FIELDS=('price','battery','range','consumption','charging')
BOUNDS={'price':(10000,20000000),'battery':(1,300),'range':(40,1500),'consumption':(3,80),'charging':(0,1000)}
class SourceError(ValueError):pass

def safe_url(value):
    u=urlsplit(value or '')
    if u.scheme!='https' or not u.hostname or u.username or u.password:raise SourceError('Invalid source URL')
    return value

def normalize(value):
    value=unicodedata.normalize('NFKD',str(value).replace('+',' plus ').replace('ø','o').replace('Ø','O'))
    return re.sub(r'[^a-z0-9]+',' ',value.encode('ascii','ignore').decode().lower()).strip()

def identity_terms(value,brand):
    value=value.removeprefix(brand+' ')
    value=re.sub(r'\d+(?:[,.]\d+)?\s*kWh(?:\s*(?:netto|brutto|LFP))?','',value,flags=re.I)
    value=re.sub(r'\bEL\s*\d+\b|\d+\s*(?:hk|kW)\b','',value,flags=re.I)
    return set(normalize(value).split())

def exact_existing_variant(record,models):
    candidates=[]
    for m in models:
        if m.get('availability')=='discontinued':continue
        if normalize(m['brand'])!=normalize(record['brand']):continue
        if identity_terms(m['model'],m['brand'])!=identity_terms(record['family']+' '+record['variant'],record['brand']):continue
        battery=re.search(r'(\d+(?:[,.]\d+)?)\s*kWh',record['variant'],re.I)
        if battery and (m.get('battery') is None or abs(float(battery[1].replace(',','.'))-m['battery'])>.6):continue
        candidates.append(m)
    return candidates[0] if len(candidates)==1 else None

def slugify(value):return normalize(value).replace(' ','-')[:120]

def number(value,field):
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise SourceError('Invalid '+field)
    low,high=BOUNDS[field]
    if not low<=value<=high:raise SourceError('Out-of-range '+field)
    return value

def source_date(value,today,max_age=90):
    try:d=date.fromisoformat(value)
    except (TypeError,ValueError):raise SourceError('Missing source date')
    age=(today-d).days
    if age<0 or age>max_age:raise SourceError('Stale or future source date: '+str(value))
    return value

def download(url):
    safe_url(url)
    if urlsplit(url).hostname not in {'bil-portalen.dk','pricelists-api.cars4ever.eu'}:raise SourceError('Unexpected feed host')
    for attempt in range(2):
        try:
            req=Request(url,headers={'User-Agent':'EVBeregn-catalog/1.0 (+https://www.evberegn.dk)','Accept':'application/json'})
            with urlopen(req,timeout=25) as response:
                if urlsplit(response.url).hostname!=urlsplit(url).hostname:raise SourceError('Unexpected redirect')
                body=response.read(5000001)
            if len(body)>5000000:raise SourceError('Feed exceeds size limit')
            return json.loads(body)
        except Exception:
            if attempt:raise
            time.sleep(1)

def feed_records(data,config,today):
    if data.get('licens')!=config['license']:raise SourceError('Feed license changed')
    source_date(data.get('opdateret'),today,config['max_age_days'])
    rows=data.get('modeller')
    if not isinstance(rows,list) or len(rows)<100:raise SourceError('Incomplete feed')
    seen=set();result=[];rejected=[]
    for row in rows:
        if row.get('drivlinje')!='Elbil' or row.get('status')!='i salg':continue
        if not row.get('pris_dkk') or not row.get('variant') or not row.get('priskilde'):continue
        try:
            url=safe_url(row['url']);primary=safe_url(row['priskilde']['url'])
            if urlsplit(url).hostname!='bil-portalen.dk':raise SourceError('Unexpected model origin')
            stamp=source_date(row['priskilde'].get('dato'),today)
            brand=row['brand'].strip();family=row['model'].strip();variant=row['variant'].strip()
            if not all(isinstance(v,str) and 0<len(v)<200 and '<' not in v for v in (brand,family,variant)):raise SourceError('Invalid identity')
            key=url+'|'+variant
            if key in seen:raise SourceError('Duplicate identity')
            seen.add(key)
            # Only the exact variant price is licensed/identified by this feed.
            # Range is often a model maximum; battery in a label has no defined basis.
            result.append({'source_id':key,'family':family,'variant':variant,'brand':brand,'model':variant if normalize(variant).startswith(normalize(family.removeprefix(brand+' '))) else family.removeprefix(brand+' ')+' '+variant,
                           'values':{'price':number(row['pris_dkk'],'price')},
                           'source':{'label':config['label'],'url':url,'primary_url':primary,'source_date':stamp,'license':config['license'],'license_url':config['license_url'],'kind':'licensed-feed'}})
        except (SourceError,KeyError,AttributeError,TypeError) as exc:rejected.append({'model':str(row.get('model')),'reason':str(exc)})
    if len(result)<50:raise SourceError('Too few valid electric variant prices')
    return result,rejected

def retail_records(data,config,today):
    name=data.get('name','')
    if normalize(config['brand']) not in normalize(name) or normalize(config['family']) not in normalize(name):raise SourceError('Retail model identity mismatch')
    if not isinstance(data.get('variants'),list) or not isinstance(data.get('trims'),list) or not isinstance(data.get('engines'),list):raise SourceError('Retail schema changed')
    engines={e['id']:e for e in data['engines']};trims={t['id']:t for t in data['trims']};result=[];rejected=[];seen=set()
    for v in data['variants']:
        try:
            engine=engines[v['engineId']];trim=trims[v['trimId']]
            if engine.get('fuelType')!='el':continue
            variant=trim['name']+'|'+engine['name']
            key=config['url']+'|'+variant
            if key in seen:raise SourceError('Duplicate retail variant')
            seen.add(key)
            values={'price':number(v.get('price'),'price')}
            wh=v.get('consumption')
            if wh is not None:
                if isinstance(wh,bool) or not isinstance(wh,(int,float)) or not 30<=wh<=800:raise SourceError('Expected consumption in Wh/km')
                values['consumption']=number(round(wh/10,3),'consumption')
            if v.get('drivingRange') is not None:values['range']=number(v['drivingRange'],'range')
            # batteryCapacity has a unit but the API does not declare gross/net.
            if engine.get('batteryCapacity') is not None:values['battery']=number(engine['batteryCapacity'],'battery')
            result.append({'source_id':key,'family':config['brand']+' '+config['family'],'brand':config['brand'],'variant':variant,
                           'model':config['family']+' '+trim['name']+' '+engine['name'],'values':values,
                           'bound_slug':config.get('bindings',{}).get(variant),
                           'source':{'label':name+' · dansk prisliste','url':config['url'],'primary_url':safe_url(config['official_url']),'source_date':today.isoformat(),'kind':'retail-api'},
                           'price_note':'Vejledende pris. Udstyr og eventuelle kampagnevilkår fremgår af producentens prisliste.'})
        except (SourceError,KeyError,TypeError) as exc:rejected.append({'model':str(v.get('code')),'reason':str(exc)})
    if not result:raise SourceError('No valid battery-electric variants')
    return result,rejected

def apply_records(catalog,records,config,today):
    candidate=copy.deepcopy(catalog);by_slug={m['slug']:m for m in candidate['models']};by_source={s:m for m in candidate['models'] for s in m.get('source_ids',[])}
    bindings={b['url']+'|'+b['variant']:b['slug'] for b in config['bindings']}
    changes=[];new=[];unmatched=[];rejected=[];limit=max(0,config['max_new_per_day']-sum(m.get('discovered')==today.isoformat() for m in candidate['models'] if m.get('origin')=='automatic'))
    for record in records:
        key=record['source_id'];bound=record.get('bound_slug') or bindings.get(key)
        existing=by_source.get(key) or by_slug.get(bound)
        if existing is None and record['source']['kind']=='licensed-feed':existing=exact_existing_variant(record,list(by_slug.values()))
        if existing and (existing['slug'] in config['protected_slugs'] or existing.get('availability')=='discontinued'):continue
        label=record['brand']+' '+record['model']
        if any(normalize(block) in normalize(label) for block in config['blocked_names']):continue
        if existing is None:
            # A base-model price must not silently replace another trim. For a
            # represented family only a complete retail DTO may add variants.
            family=normalize(record['family']);family_present=any(family in normalize(m['brand']+' '+m['model']) for m in by_slug.values() if m.get('availability')!='discontinued')
            if family_present and record['source']['kind']=='licensed-feed':
                unmatched.append({'family':record['family'],'variant':record['variant'],'reason':'Different or unbound existing variant; old values preserved'});continue
            if len(new)>=limit:continue
            slug=slugify(label)+'-'+hashlib.sha256(key.encode()).hexdigest()[:8]
            if slug in by_slug or slug in config['protected_slugs']:continue
            existing={'slug':slug,'brand':record['brand'],'model':record['model'],'status':'active','origin':'automatic','discovered':today.isoformat(),'indexable':False,'modified':today.isoformat(),'provenance':{},**{f:None for f in FIELDS}}
            candidate['models'].append(existing);by_slug[slug]=existing;new.append(slug)
        else:
            # Large price jumps are quarantined without harming other variants.
            old=existing.get('price');price=record['values'].get('price')
            if old and price and not .6<=price/old<=1.4:
                rejected.append({'model':existing['slug'],'reason':'Price change exceeds 40%; retained last known price'});continue
        changed=False
        for field,value in record['values'].items():
            if value is None:continue
            number(value,field)
            previous=existing.get('provenance',{}).get(field,{})
            src=record['source']
            if previous.get('kind')=='retail-api' and src['kind']=='licensed-feed' and previous.get('source_date','')>=src['source_date']:continue
            # A retrieval date may not make unchanged figures appear newly edited.
            same_source=previous.get('url')==src['url']
            if existing.get(field)!=value or not same_source or (src['kind']=='licensed-feed' and previous.get('source_date')!=src['source_date']):
                existing[field]=value;existing.setdefault('provenance',{})[field]=copy.deepcopy(src);changed=True
        if existing.get('origin')=='automatic':
            existing['indexable']=all(existing.get(f) is not None for f in ('price','range','consumption'))
        ids=existing.setdefault('source_ids',[])
        if key not in ids:ids.append(key);changed=True
        by_source[key]=existing
        if record.get('price_note') and record['price_note']!=existing.get('price_note'):
            existing['price_note']=record['price_note'];changed=True
        if changed:existing['modified']=today.isoformat();changes.append(existing['slug'])
    return candidate,{'updated_models':sorted(set(changes)),'new_models':new,'unmatched_existing_variants':unmatched,'quarantine':rejected}

def validate_catalog(data,config):
    if data.get('schema_version')!=1:raise SourceError('Catalogue schema changed')
    seen=set();labels=set()
    for m in data['models']:
        slug=m['slug'];label=m['brand']+'|||'+m['model']
        if any(not isinstance(m.get(k),str) or not m[k].strip() or len(m[k])>200 or '<' in m[k] or '>' in m[k] for k in ('brand','model')):raise SourceError('Invalid model label')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug) or slug in seen or label in labels:raise SourceError('Duplicate/invalid model identity')
        if slug in config['protected_slugs']:raise SourceError('Protected historical address')
        seen.add(slug);labels.add(label)
        for f in FIELDS:
            if m.get(f) is not None:number(m[f],f)
        for src in m.get('provenance',{}).values():safe_url(src['url'])
    if not set(config['preserved_slugs'])<=seen:raise SourceError('Existing catalogue has been truncated')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fixture-dir',type=Path);args=parser.parse_args();today=date.today()
    config=json.loads((ROOT/'data/car-sources.json').read_text());catalog=load_catalog(ROOT);validate_catalog(catalog,config)
    results=[];records=[];rejected=[]
    # Complete variant records take precedence over model-level price discovery.
    sources=[('retail-'+s['code'],s,retail_records) for s in config['retail_apis']]+[('bil-portalen',config['feed'],feed_records)]
    for identifier,source,parse in sources:
        try:
            raw=json.loads((args.fixture_dir/(identifier+'.json')).read_text()) if args.fixture_dir else download(source['url'])
            entries,bad=parse(raw,source,today);records+=entries;rejected+=bad;results.append({'id':identifier,'status':'ok','records':len(entries)})
        except Exception as exc:results.append({'id':identifier,'status':'error','error':str(exc)[:250]})
    candidate,report=apply_records(catalog,records,config,today);validate_catalog(candidate,config)
    report.update(checked_at=datetime.now(timezone.utc).isoformat(),sources=results,source_rejections=rejected,active_models=len(candidate['models']),automatically_priced_models=sum(bool(m.get('source_ids')) for m in candidate['models']),legacy_models_without_automatic_price=sum(not m.get('source_ids') and m.get('availability')!='discontinued' for m in candidate['models']),historical_models=sum(m.get('availability')=='discontinued' for m in candidate['models']),pending_indexing=sum(not m['indexable'] for m in candidate['models']))
    out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'car-update-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('CAR_UPDATE_RESULT '+json.dumps({k:v for k,v in report.items() if k not in ('unmatched_existing_variants','source_rejections')},ensure_ascii=False))
    if not any(s['status']=='ok' for s in results):raise SystemExit('All car sources failed; live catalogue unchanged')
    (ROOT/'data/cars.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/car-update-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
