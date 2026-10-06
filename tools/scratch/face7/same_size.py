"""same_size.py out.png img[@crop] ...: faces side by side, each scaled so brow-top to chin is FACE_PX, cropped to its
face's box (a little round it): judged at one size."""
import sys
import numpy as np
from PIL import Image, ImageDraw
import skin_sample as ss

FACE_PX = 380
out = sys.argv[1]
tiles = []
for p in sys.argv[2:]:
    crop = None
    if "@" in p:
        p, c = p.split("@")
        crop = [int(v) for v in c.split(",")]
    img = Image.open(p).convert("RGB")
    if crop:
        img = img.crop(crop)
    up = 2 if img.height < 900 else 1
    L = ss.ff.detect(np.asarray(img.resize((img.width * up, img.height * up), Image.LANCZOS)))
    if L is None:
        continue
    L = L[:, :2] / up
    k = FACE_PX / np.linalg.norm(L[152] - L[10])
    im = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    c = (L[[10, 152]].mean(0)) * k
    box = (int(c[0] - 230), int(c[1] - 250), int(c[0] + 230), int(c[1] + 250))
    t = im.crop(box)
    ImageDraw.Draw(t).text((6, 6), p.replace("\\", "/").split("/")[-1], fill=(255, 255, 0))
    tiles.append(t)
W = Image.new("RGB", (460 * len(tiles), 500))
for i, t in enumerate(tiles):
    W.paste(t, (460 * i, 0))
W.save(out)
print(W.size)
