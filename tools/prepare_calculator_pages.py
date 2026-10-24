"""Share calculator arithmetic and site CSS while preserving the homepage UI."""
from pathlib import Path
import json,re,subprocess
ROOT=Path(__file__).parents[1]
p=ROOT/'index.html';text=p.read_text()
styles=re.search(r'<style>(.*?)</style>',text,re.S)
assert styles and len(styles[1])>1000
td=re.search(r'\.answer-table td\{([^}]+)\}',styles[1])
extra='\n.answer-table th{'+(td[1] if td else 'padding:10px;border-bottom:1px solid #29374d;')+'text-align:left;font-weight:400;}\n'
(ROOT/'assets/site.css').write_text(styles[1]+extra)
text=text[:styles.start()]+'<link rel="stylesheet" href="/assets/site.css?v=20261024-calculators">'+text[styles.end():]
old=re.search(r'const calculators=(\{.*?\});',text,re.S)
original=json.loads(subprocess.check_output(['node','-e',"const vm=require('node:vm');process.stdout.write(JSON.stringify(vm.runInNewContext('('+process.argv[1]+')')));",old[1]],text=True))
shared={1,3,8,12,14}
expression='{'+','.join(str(n)+':'+('EVCalculators.definitions['+str(n)+']' if n in shared else json.dumps(original[str(n)],ensure_ascii=False,separators=(',',':'))) for n in range(1,21))+'}'
text=text[:old.start(1)]+expression+text[old.end(1):]
for n in shared:
 pattern=r'case '+str(n)+r':\{.*?;break\}'
 body='case '+str(n)+':{const inputs=Object.fromEntries(calculators[currentCalculator].fields.map(field=>[field[0],value(field[0])]));h=EVCalculators.run(currentCalculator,inputs);break}'
 text,count=re.subn(pattern,lambda m:body,text,count=1,flags=re.S)
 assert count==1,n
# Use the same per-field validation on the five shared tools.
needle=" let first=null,message='';\n for(const field"
replacement=" let first=null,message='';\n const sharedErrors=EVCalculators.definitions[currentCalculator]?EVCalculators.validate(currentCalculator,Object.fromEntries(calc.fields.map(f=>[f[0],document.getElementById('calc_'+f[0]).value]))):{};\n for(const field"
assert needle in text;text=text.replace(needle,replacement,1)
text=text.replace("  input.setCustomValidity(error);", "  if(sharedErrors[field[0]])error=sharedErrors[field[0]];\n  input.setCustomValidity(error);",1)
needle='<script src="/assets/ev-core.js?v=20261024"></script>'
assert needle in text;text=text.replace(needle,needle+'<script src="/assets/calculators.js?v=20261024-pages1"></script>',1)
text=text.replace('id="calculator-title"','id="beregnere"',1)
text=text.replace('aria-labelledby="calculator-title"','aria-labelledby="beregnere"')
# The original 20 cards remain unchanged; this is additional ordinary navigation.
links=[('ladepris','Ladepris på elbil'),('elbil-vs-benzin','Elbil eller benzin?'),('opladningstid','Hvor lang tid tager opladning?'),('leasing-vs-koeb','Leasing eller køb?'),('samlet-biloekonomi','Bilens samlede økonomi')]
section='<section class="all-cars-seo" style="margin:26px 16px;padding:20px;border:1px solid #29374d;border-radius:18px;background:#0e1727"><div class="section-label">BEREGNERE MED EKSEMPLER</div><h2 style="margin:0 0 8px">Find beregningen til dit spørgsmål</h2><p class="muted">Beregn med egne tal, og se metode, forudsætninger og et gennemregnet eksempel.</p><div class="compare-grid">'+''.join('<a class="model-link" href="/beregnere/'+slug+'/">'+label+' →</a>' for slug,label in links)+'</div></section>'
needle='<section class="all-cars-seo"';pos=text.index(needle)
text=text[:pos]+section+text[pos:]
p.write_text(text)
# Models link to the relevant real calculator paths; the fragment only preselects a car.
for model in (ROOT/'elbil').glob('*/index.html'):
 s=model.read_text()
 if 'noindex, follow' in s or 'http-equiv="refresh"' in s:continue
 slug=model.parent.name
 box='<section class="box"><div class="label">BEREGN MERE</div><h2>Regn videre med bilen</h2><div class="alts">'+''.join('<a class="alt" href="/beregnere/'+path+'/#bil='+slug+'"><b>'+label+'</b><span>'+desc+'</span></a>' for path,label,desc in [('ladepris','Ladepris','Hel eller delvis opladning'),('elbil-vs-benzin','Elbil vs. benzin','Sammenlign energiudgiften'),('opladningstid','Opladningstid','Regn med gennemsnitlig effekt')])+'</div></section>\n'
 needle='<section class="box moneybox">';assert needle in s
 model.write_text(s.replace(needle,box+needle,1))
print('Shared five calculators; original 20 homepage cards preserved; links added to 181 model pages.')
