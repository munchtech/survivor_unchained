"""Copy shots into the review folder as full-resolution JPEGs: python review.py OUTDIR name=shot ..."""
import os
import sys
from PIL import Image

S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a4fdbc49786ba8b7f\godot\.shots'
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for pair in sys.argv[2:]:
    name, shot = pair.split('=')
    src = shot if os.path.isabs(shot) else os.path.join(S, shot + '.png')
    Image.open(src).convert('RGB').save(os.path.join(out, name + '.jpg'), quality=92)
    print('wrote', name)
