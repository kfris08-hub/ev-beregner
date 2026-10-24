"""Validate real calculator pages, static examples and generated car presets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json,re,subprocess
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk'
config=json.loads((ROOT/'data/calculator-pages.json').read_text())
examples=json.loads(subprocess.check_output(['node',str(ROOT/'tools/calculator_examples.cjs')],text=True))
class Markup(HTMLParser):
 def __init__(self,text):super().__init__();self.tags=[];self.feed(text)
 def handle_starttag(self,t,a):self.tags.append((t,dict(a)))
for page in config:
 text=(ROOT/'beregnere'/page['slug']/'index.html').read_text();tags=Markup(text).tags;canonical=BASE+'/beregnere/'+page['slug']+'/'
 assert [(a.get('href')) for t,a in tags if t=='link' and a.get('rel')=='canonical']==[canonical]
 assert text.count('<h1>')==1 and page['h1'] in text
 assert 'rel="canonical"' in text and 'name="robots" content="index, follow"' in text
 assert 'http-equiv="refresh"' not in text
 inputs={a['name']:a for t,a in tags if t=='input'}
 assert set(inputs)==set(page['defaults'])
 for field,expected in page['defaults'].items():assert float(inputs[field]['value'])==float(expected)
 assert examples[page['slug']]['html'] in text,'Static result must use the shared arithmetic'
 assert '<noscript>' in text and 'Gennemgået 24. oktober 2026' in text
 assert all(source['url'] in text for source in page['sources'])
 assert all('/beregnere/'+slug+'/' in text for slug in page['related'])
 assert all(f'help_{key}' in text and f'error_{key}' in text for key in inputs)
 for tag,attrs in tags:
  path=attrs.get('src') if tag=='script' else attrs.get('href') if tag=='link' and attrs.get('rel')=='stylesheet' else None
  if path and path.startswith('/'):assert (ROOT/urlsplit(path).path.lstrip('/')).is_file(),path
 graphs=[json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)]
 assert {'WebPage','WebApplication','BreadcrumbList'}=={n['@type'] for g in graphs for n in g['@graph']}
 assert not any('aggregateRating' in json.dumps(g) for g in graphs)
home=(ROOT/'index.html').read_text();cars=json.loads(re.search(r'const cars=(\[.*?\]); let selectedCar=',home,re.S)[1])
slugs=json.loads(re.search(r'const modelSlugs=(\{.*?\});',home,re.S)[1]);catalog=json.loads((ROOT/'assets/calculator-cars.json').read_text())['models']
assert len(catalog)==181
by_slug={c['slug']:c for c in catalog}
for c in cars:
 actual=by_slug[slugs[c[0]+'|||'+c[1]]]
 assert [actual[k] for k in ('price','battery','range','consumption','charging')]==c[2:]
for page in config:assert '/beregnere/'+page['slug']+'/' in home
for path in (ROOT/'elbil').glob('*/index.html'):
 text=path.read_text()
 if 'noindex, follow' in text or 'http-equiv="refresh"' in text:continue
 for slug in ['ladepris','elbil-vs-benzin','opladningstid']:assert '/beregnere/'+slug+'/#bil='+path.parent.name in text
print('PASS: five standalone HTML calculators, shared static examples, canonical metadata, structured data, sources, 181 consistent car presets and links from the homepage and all active models.')
