# cs.py dir out.jpg name:x0:x1 ... (crop fractions of width, full height, 540 tall)
import sys
from PIL import Image
d,out=sys.argv[1],sys.argv[2]; ims=[]
for a in sys.argv[3:]:
    n,x0,x1=a.split(':'); im=Image.open(f'{d}/{n}.png'); w,h=im.size; x0,x1=float(x0),float(x1)
    c=im.crop((int(w*x0),0,int(w*x1),h)); ims.append(c.resize((int(540*c.width/h),540)))
W=Image.new('RGB',(sum(i.width for i in ims),540)); x=0
for i in ims: W.paste(i,(x,0)); x+=i.width
W.save(out,quality=85)
