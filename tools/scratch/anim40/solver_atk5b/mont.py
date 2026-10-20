# mont.py outdir out.jpg name1 name2 ... : crop centre region of each frame, montage side by side, half size
import sys
from PIL import Image
d,out,names=sys.argv[1],sys.argv[2],sys.argv[3:]
ims=[]
for n in names:
    im=Image.open(f"{d}/{n}.png").convert("RGB")
    w,h=im.size
    im=im.crop((w*0.25,h*0.08,w*0.75,h*0.92)).resize((480,454))
    ims.append(im)
W=Image.new("RGB",(480*len(ims),454))
for i,im in enumerate(ims): W.paste(im,(480*i,0))
W.save(out,quality=85)
