import sys
from PIL import Image
# pair.py A B OUT : A beside B at half size each
a,b,out=sys.argv[1:4]
A=Image.open(a).convert('RGB'); B=Image.open(b).convert('RGB')
w,h=A.size; s=0.5
A=A.resize((int(w*s),int(h*s))); B=B.resize((int(w*s),int(h*s)))
C=Image.new('RGB',(A.width*2+8,A.height),(255,255,255)); C.paste(A,(0,0)); C.paste(B,(A.width+8,0)); C.save(out,quality=88)
