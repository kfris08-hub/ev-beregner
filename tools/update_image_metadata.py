"""Update only the two recommended ImageObject fields and affected sitemap dates."""
from pathlib import Path
import argparse,json,re,xml.etree.ElementTree as ET
from photo_rights import image_rights

ROOT=Path(__file__).parents[1]
ORIGIN='https://www.evberegn.dk'
DATE='2026-10-25'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check',action='store_true',help='Fail if the generated metadata is out of date')
args=parser.parse_args()
catalog=json.loads((ROOT/'data/model-photos.json').read_text())['models']
affected=set();changed=[]
for slug,photo in catalog.items():
    if photo['status']!='verified':continue
    path=ROOT/'elbil'/slug/'index.html';text=path.read_text()
    match=re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
    assert match,slug
    graph=json.loads(match[1])
    page=next(node for node in graph['@graph'] if node['@type']=='WebPage')
    image=page['primaryImageOfPage']
    assert image['contentUrl']==ORIGIN+photo['src'],slug
    rights=image_rights(photo)
    affected.add(ORIGIN+'/elbil/'+slug+'/')
    if all(image.get(k)==v for k,v in rights.items()):continue
    image.update(rights)
    updated=text[:match.start(1)]+json.dumps(graph,ensure_ascii=False)+text[match.end(1):]
    changed.append(slug)
    if not args.check:path.write_text(updated)
if args.check:
    assert not changed,'Outdated image metadata: '+', '.join(changed)
else:
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns);ET.register_namespace('image','http://www.google.com/schemas/sitemap-image/1.1')
    sitemap=ET.parse(ROOT/'sitemap.xml')
    for node in sitemap.getroot():
        if node.find('{'+ns+'}loc').text not in affected:continue
        modified=node.find('{'+ns+'}lastmod')
        if modified is None:modified=ET.SubElement(node,'{'+ns+'}lastmod')
        if not modified.text or modified.text<DATE:modified.text=DATE
    ET.indent(sitemap,space='  ');sitemap.write(ROOT/'sitemap.xml',encoding='unicode',xml_declaration=True)
print(f'PASS: creator and copyrightNotice checked on {len(affected)} images; {len(changed)} model pages updated.')
