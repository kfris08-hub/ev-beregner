"""Check the useful entry pages, honest metadata and stable rebuilds."""
from pathlib import Path
from datetime import date
import contextlib,hashlib,importlib.util,io,json,re,shutil,struct,sys,tempfile
ROOT=Path(__file__).parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_calculator_pages as builder
pages=json.loads((ROOT/'data/calculator-pages.json').read_text())
assert {p['calculator'] for p in pages}=={1,2,3,4,6,7,8,9,12,14}
home=(ROOT/'index.html').read_text()
assert home.index('id="main-title"')<home.index('<!-- BEGIN AADS')
assert home.count("data-aa='2457081'")==1 and 'id="quickTools"' in home
hub=(ROOT/'beregnere/index.html').read_text()
assert hub.count('data-tool=')==20 and 'name="robots" content="index, follow' in hub
assert 'name="description"' in (ROOT/'om/index.html').read_text()
presets={m['slug']:m for m in json.loads((ROOT/'assets/calculator-cars.json').read_text())['models']}
for m in json.loads((ROOT/'data/cars.json').read_text())['models']:
 if m.get('price') is not None and not m.get('provenance',{}).get('price') and m.get('availability')!='discontinued':assert presets[m['slug']]['price_status']=='catalogue'
for slug in ['ev-beregner']+[p['slug'] for p in pages]:
 image=(ROOT/'assets/social'/(slug+'.png')).read_bytes();assert image[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',image[16:24])==(1200,630)
for p in pages:
 text=(ROOT/'beregnere'/p['slug']/'index.html').read_text()
 assert text.index('id="answer"')<text.index('<!-- BEGIN AADS')
 assert 'id="shareCalculation"' in text and 'id="printCalculation"' in text
 assert '/assets/social/'+p['slug']+'.png' in text
 assert 'FAQPage' not in text and 'aggregateRating' not in text
# A next-day rebuild must not manufacture a new date or alter an unchanged homepage.
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory)
 for name in ['index.html','sitemap.xml']:shutil.copyfile(ROOT/name,root/name)
 for name in ['data','beregnere','om']:shutil.copytree(ROOT/name,root/name)
 (root/'assets').mkdir();shutil.copyfile(ROOT/'assets/calculators.js',root/'assets/calculators.js')
 (root/'tools').mkdir();shutil.copyfile(ROOT/'tools/calculator_examples.cjs',root/'tools/calculator_examples.cjs')
 def fingerprint():
  files=[root/'index.html',root/'sitemap.xml',*root.glob('beregnere/**/index.html'),root/'om/index.html']
  return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 before=fingerprint()
 with contextlib.redirect_stdout(io.StringIO()):builder.build(root,today=date(2026,11,12))
 after=fingerprint();assert before==after,'An unchanged next-day build must retain content and sitemap dates'
print('GROWTH_CONTENT_RESULT '+json.dumps({'standalone_calculators':len(pages),'overview_tools':20,'social_cards':len(pages)+1,'unchanged_rebuild':'passed','catalogue_price_markers':'preserved'}))

