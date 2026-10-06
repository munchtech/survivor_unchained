"""Fetch Poly Haven thumbnails into a labelled sheet: python thumbs.py OUT id [id ...]"""
import sys, os, io, urllib.request
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
ids = sys.argv[2:]
ims = []
for i in ids:
    url = f"https://cdn.polyhaven.com/asset_img/thumbs/{i}.png?width=256&height=256"
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "survivor-unchained-assets/1.0"}), timeout=30).read()
        im = Image.open(io.BytesIO(data)).convert("RGB").resize((256, 256))
    except Exception as e:
        print("fail", i, e); continue
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 + 6 * len(i), 14], fill=(0, 0, 0))
    d.text((3, 2), i, fill=(255, 255, 0))
    ims.append(im)
cols = 6
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 256, rows * 256))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * 256, (k // cols) * 256))
sheet.save(os.path.join(HERE, out), quality=88)
print(out, len(ims))
