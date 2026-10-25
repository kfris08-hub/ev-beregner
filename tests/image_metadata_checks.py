"""Regression checks for Google's two reported image metadata warnings and source accuracy."""
import json,re
from pathlib import Path
ROOT=Path(__file__).parents[1]
catalog=json.loads((ROOT/'data/model-photos.json').read_text())['models']
count=0;cc0=0;organizations=0;by_slug={}
for slug,photo in catalog.items():
    text=(ROOT/'elbil'/slug/'index.html').read_text()
    if photo['status']!='verified':
        assert 'primaryImageOfPage' not in text,slug
        continue
    data=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1])
    images=[n.get('primaryImageOfPage') for n in data.get('@graph',[]) if n.get('@type')=='WebPage']
    assert len(images)==1 and images[0]['@type']=='ImageObject',slug
    image=images[0];by_slug[slug]=image
    assert image['contentUrl']=='https://www.evberegn.dk'+photo['src'],slug
    assert image['license']==photo['license_url'] and image['acquireLicensePage']==photo['source'],slug
    assert image['creditText']==photo['author'],slug
    creator=image.get('creator')
    assert isinstance(creator,dict) and creator.get('@type') in ('Person','Organization'),slug
    name=creator.get('name');notice=image.get('copyrightNotice')
    assert isinstance(name,str) and name.strip() and len(name)<=150 and '<' not in name and '©' not in name,slug
    assert name==re.sub(r'^©\s*','',(photo.get('attribution') or photo['author']).strip()),slug
    assert isinstance(notice,str) and name in notice and 'EV Beregner' not in notice,slug
    if '/publicdomain/zero/' in photo['license_url']:
        cc0+=1
        assert 'CC0' in notice and 'public domain' in notice and '©' not in notice,slug
    if creator['@type']=='Organization':organizations+=1
    count+=1
assert count==sum(p['status']=='verified' for p in catalog.values()) and cc0==sum(p['status']=='verified' and '/publicdomain/zero/' in p['license_url'] for p in catalog.values()),(count,cc0)
assert by_slug['kia-ev4-standard-range-access']['creator']=={'@type':'Person','name':'Oleg Yunakov'}
assert by_slug['mercedes-benz-gla-with-eq-technology-200']['creator']=={'@type':'Organization','name':'Mercedes-Benz AG'}
assert by_slug['mercedes-benz-gla-with-eq-technology-200']['copyrightNotice']=='© Mercedes-Benz AG'
assert by_slug['byd-atto-2-boost']['creator']=={'@type':'Organization','name':'iMoD Official'}
assert by_slug['audi-q8-e-tron-50-quattro']['copyrightNotice']=='© M 93'
print(f'PASS: {count} source-backed creator/copyrightNotice pairs, {cc0} accurate CC0 notices, {organizations} organization credits; image URLs, licenses, credits and excluded models preserved.')
