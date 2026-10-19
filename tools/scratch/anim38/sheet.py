# sheet.py OUT.png BOX COLS name1 name2 ...  (from dir given by env D): native 1:1 crops, labelled, never scaled.
# BOX = x0,y0,x1,y1 in the 1920x1080 frame.
import sys, os
from PIL import Image, ImageDraw
out, box, cols = sys.argv[1], [int(v) for v in sys.argv[2].split(',')], int(sys.argv[3])
names = sys.argv[4:]; D = os.environ.get('D', '.')
w, h = box[2]-box[0], box[3]-box[1]; lab = 18
rows = (len(names)+cols-1)//cols
s = Image.new('RGB', (cols*(w+4), rows*(h+lab+4)), (20,20,20)); d = ImageDraw.Draw(s)
for k, n in enumerate(names):
    x, y = (k % cols)*(w+4), (k//cols)*(h+lab+4)
    s.paste(Image.open(os.path.join(D, n+'.png')).convert('RGB').crop(box), (x, y+lab))
    d.text((x+3, y+3), n, fill=(230,230,230))
s.save(out); print(out, s.size)
