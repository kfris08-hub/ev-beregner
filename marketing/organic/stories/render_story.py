"""Single static Facebook Story, 1080x1920. Not a Reel or video.

Actual website screenshot retained. Hyundai model photo by TTTNIS / CC0.
Source: https://commons.wikimedia.org/wiki/File:Hyundai_Ioniq_5.jpg
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).parent
W, H = 1080, 1920
im = Image.new('RGB', (W, H), '#070c17')
d = ImageDraw.Draw(im)
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def text(value, y, size, color='#ffffff'):
    f = ImageFont.truetype(font_path, size)
    box = d.textbbox((0, 0), value, font=f)
    width = d.textlength(value, font=f)
    assert width <= 900, (value, width)
    d.text(((W-width)/2, y), value, fill=color, font=f)

text('EV Beregner', 200, 38, '#10ddb2')
text('Din elbil –', 276, 78)
text('eller din næste?', 365, 78)
# Crop only the website's model heading, photograph and full photo credit.
# No invented controls, replaced numbers, altered car or AI-generated interface.
source_path = P / 'story-model-source.png'
if not source_path.exists():
    source_path = P.parent / 'output' / 'model.png'
source = Image.open(source_path).convert('RGB')
picture = source.crop((0, 145, 840, 1035)).resize((900, 954), Image.Resampling.LANCZOS)
im.paste(picture, (90, 470))
text('Find bilen. Regn videre.', 1460, 46)
text('evberegn.dk', 1530, 82, '#10ddb2')
text('Gratis · uden login', 1632, 32)
im.save(P / 'facebook-story-bilvalg-20261114.jpg', quality=94, subsampling=0)
assert Image.open(P / 'facebook-story-bilvalg-20261114.jpg').size == (1080, 1920)
print('Created one static 1080x1920 Facebook Story image.')
