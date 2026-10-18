import sys
from PIL import Image
S='C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/.shots'
tags=sys.argv[2:]; F=['own','saffron','sunborn']
o=Image.new('RGB',(360*len(tags),120*3))
for j,t in enumerate(tags):
  for i,f in enumerate(F):
    import os
    p=f'{S}/f30{t}_{f}_c04a_sa5_2.png'
    if not os.path.exists(p): continue
    o.paste(Image.open(f'{S}/f30{t}_{f}_c04a_sa5_2.png').convert('RGB').crop((1030,730,1270,810)).resize((360,120),Image.LANCZOS),(360*j,120*i))
o.save(sys.argv[1])
