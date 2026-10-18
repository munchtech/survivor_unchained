"""python strip.py OUT BOX(x0,y0,x1,y1) img... : 1:1 crops stacked, labelled."""
import sys
from PIL import Image, ImageDraw
out, box = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(","))
ims = sys.argv[3:]; w, h = box[2]-box[0], box[3]-box[1]
cols = max(1, min(len(ims), 1560 // w)); rows = (len(ims)+cols-1)//cols
S = Image.new("RGB", (cols*w, rows*(h+14)), "white"); d = ImageDraw.Draw(S)
for k, p in enumerate(ims):
    x, y = (k % cols)*w, (k//cols)*(h+14)
    S.paste(Image.open(p).convert("RGB").crop(box), (x, y+14)); d.text((x+2, y+1), p.replace("\\","/").split("/")[-1][:40], fill="black")
S.save(out)
