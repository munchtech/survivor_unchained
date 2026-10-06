"""Contact sheet of Poly Haven thumbnails: python thumbs.py OUT id [id ...] (cached in thumbs/)."""
import sys, urllib.request, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ids = sys.argv[2:]
out = os.path.join(HERE, sys.argv[1])
os.makedirs(os.path.join(HERE, 'thumbs'), exist_ok=True)
ims = []
for i in ids:
    p = os.path.join(HERE, 'thumbs', i + '.png')
    if not os.path.exists(p):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f'https://cdn.polyhaven.com/asset_img/thumbs/{i}.png?width=320&height=320', headers={'User-Agent': 'survivor-unchained-assets/1.0'}), timeout=60)
            open(p, 'wb').write(r.read())
        except Exception as e:
            print('fail', i, e); continue
    im = Image.open(p).convert('RGB').resize((320, 320))
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 8 + 7 * len(i), 14], fill=(0, 0, 0)); d.text((3, 1), i, fill=(255, 255, 0))
    ims.append(im)
cols = 6
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * 320, rows * 320))
for k, im in enumerate(ims): s.paste(im, ((k % cols) * 320, (k // cols) * 320))
s.save(out, quality=88)
print(out, s.size)
