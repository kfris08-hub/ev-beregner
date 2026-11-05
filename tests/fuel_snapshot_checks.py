"""Static HTML must agree with the shared real-price snapshot before JS runs."""
from pathlib import Path
import html,json,math,re
ROOT=Path(__file__).parents[1]
data=json.loads((ROOT/'data/fuel-prices.json').read_text())
assert data['price_type']=='pump_average' and data['source_chain']=='OK'
def kroner(n):return f'{math.floor(n+.5):,}'.replace(',','.')+' kr.'
expected={'petAnnual':kroner(20000/16*data['petrol95']),'dieselAnnual':kroner(20000/20*data['diesel']),'petPrice':f"{data['petrol95']:.2f}".replace('.',',')+' kr./l','dieselPrice':f"{data['diesel']:.2f}".replace('.',',')+' kr./l'}
checked=0
for path in (ROOT/'elbil').glob('*/index.html'):
 text=path.read_text()
 if '/assets/model-calculator.js' not in text:continue
 for identifier,value in expected.items():
  match=re.search(r'<[^>]*\bid="'+identifier+r'"[^>]*>([^<]*)<',text)
  assert match and html.unescape(match[1])==value,(path.parent.name,identifier,match[1] if match else None,value)
 for key,value in [('petrol',data['petrol95']),('diesel',data['diesel'])]:
  match=re.search(r'\bdata-'+key+r'="([^"]+)"',text);assert match and float(match[1])==value,(path.parent.name,key)
 checked+=1
assert checked==len(json.loads((ROOT/'data/cars.json').read_text())['models'])
home=(ROOT/'index.html').read_text();match=re.search(r'let energyPrices=\{electric:2,petrol:([0-9.]+),diesel:([0-9.]+)',home)
assert match and float(match[1])==data['petrol95'] and float(match[2])==data['diesel']
print(f'PASS: homepage initial prices and {checked} static model comparisons match the shared pump-price snapshot.')
