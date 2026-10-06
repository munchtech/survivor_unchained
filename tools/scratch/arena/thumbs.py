"""Contact sheet of Poly Haven texture thumbnails: python thumbs.py OUT.png id id ..."""
import io, os, sys, urllib.request
from PIL import Image, ImageDraw

UA = {"User-Agent": "SurvivorUnchained-asset-fetch/1.0"}
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "thumbs")
os.makedirs(CACHE, exist_ok=True)
out, ids = sys.argv[1], sys.argv[2:]
W = 256
ims = []
for i in ids:
    p = os.path.join(CACHE, i + ".png")
    if not os.path.exists(p):
        try:
            data = urllib.request.urlopen(urllib.request.Request(f"https://cdn.polyhaven.com/asset_img/thumbs/{i}.png?width={W}&height={W}", headers=UA), timeout=60).read()
            open(p, "wb").write(data)
        except Exception as e:
            print("fail", i, e); continue
    im = Image.open(p).convert("RGB").resize((W, W))
    d = ImageDraw.Draw(im)
    d.rectangle([0, W - 16, W, W], fill=(0, 0, 0))
    d.text((3, W - 14), i, fill=(255, 255, 0))
    ims.append(im)
cols = 8
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * W, rows * W), (20, 20, 20))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * W, (k // cols) * W))
sheet.save(os.path.join(HERE, out))
print(out, sheet.size)
