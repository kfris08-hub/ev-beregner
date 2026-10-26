"""Shared current and historical models; historical data never inherit new-car prices."""
from pathlib import Path
import copy,json,re

def merge_historical(catalog,history):
    result=copy.deepcopy(catalog)
    if history.get('schema_version')!=1:raise ValueError('Invalid historical catalogue version')
    by_slug={m['slug']:i for i,m in enumerate(result['models'])};seen=set()
    for original in history['models']:
        m=copy.deepcopy(original);slug=m['slug']
        if slug in seen or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):raise ValueError('Duplicate/invalid historical identity')
        seen.add(slug)
        if m.get('availability')!='discontinued' or m.get('origin')!='historical' or m.get('status')!='active':raise ValueError('Invalid historical availability')
        if m.get('price') is not None:raise ValueError('Historical list price must not become a current purchase price')
        if not isinstance(m.get('model_year'),int) or not 1990<=m['model_year']<=2100:raise ValueError('Historical model year required')
        if m.get('range') is not None and m.get('range_standard')!='WLTP':raise ValueError('NEDC/unknown range cannot enter the WLTP field')
        if slug in by_slug:
            old=result['models'][by_slug[slug]]
            if old.get('origin')!='historical':raise ValueError('Historical entry conflicts with an existing model')
            result['models'][by_slug[slug]]=m
        else:by_slug[slug]=len(result['models']);result['models'].append(m)
    return result

def load_catalog(root):
    root=Path(root);catalog=json.loads((root/'data/cars.json').read_text())
    archive=root/'data/historical-cars.json'
    return merge_historical(catalog,json.loads(archive.read_text())) if archive.exists() else catalog
