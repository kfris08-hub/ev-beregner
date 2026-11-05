"""Sitemap dates must follow real catalogue changes and stay put on a rebuild."""
from pathlib import Path
from datetime import date
import importlib.util,json,shutil,sys,tempfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('catalog_builder',ROOT/'tools/build_car_catalog.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
NS='http://www.sitemaps.org/schemas/sitemap/0.9';BASE='https://www.evberegn.dk'
class ChangedDay(date):
    @classmethod
    def today(cls):return date(2026,11,5)
class NextDay(date):
    @classmethod
    def today(cls):return date(2026,11,6)
def dates(root):
    return {n.find('{'+NS+'}loc').text:n.findtext('{'+NS+'}lastmod') for n in ET.parse(root/'sitemap.xml').getroot()}
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    for name in ['index.html','sitemap.xml']:
        shutil.copyfile(ROOT/name,root/name)
    for name in ['elbil','data','templates']:
        shutil.copytree(ROOT/name,root/name)
    (root/'assets').mkdir()
    tree=ET.parse(root/'sitemap.xml')
    for n in tree.getroot():
        if n.findtext('{'+NS+'}loc') in (BASE+'/',BASE+'/elbil/'):
            n.find('{'+NS+'}lastmod').text='2001-01-01'
    tree.write(root/'sitemap.xml',encoding='unicode')
    catalog=json.loads((root/'data/cars.json').read_text())
    model=next(m for m in catalog['models'] if m['origin']=='existing' and m['price'] is not None)
    model['price']+=1
    (root/'data/cars.json').write_text(json.dumps(catalog,ensure_ascii=False))
    builder.ROOT=root;builder.date=ChangedDay;builder.build()
    first=dates(root)
    assert first[BASE+'/']==first[BASE+'/elbil/']=='2026-11-05',first
    builder.date=NextDay;builder.build()
    second=dates(root)
    assert second[BASE+'/']==second[BASE+'/elbil/']=='2026-11-05','Unchanged daily builds must not claim a new modification date'
print('PASS: homepage and model overview lastmod follow real changes; unchanged next-day builds retain the previous date.')
