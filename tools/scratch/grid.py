import sys
from PIL import Image
# grid.py OUT COLS IMG... : images in a grid at 1/3 size
out,cols=sys.argv[1],int(sys.argv[2]); ims=[Image.open(p).convert('RGB') for p in sys.argv[3:]]
w,h=ims[0].size; s=1/3; tw,th=int(w*s),int(h*s); rows=(len(ims)+cols-1)//cols
G=Image.new('RGB',(cols*tw+(cols-1)*4,rows*th+(rows-1)*4),(255,255,255))
for i,im in enumerate(ims): G.paste(im.resize((tw,th)),((i%cols)*(tw+4),(i//cols)*(th+4)))
G.save(out,quality=88)
