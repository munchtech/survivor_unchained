import sys
from PIL import Image
S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab47bfdab5955dac\godot\.shots'
name, box, out = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(',')), sys.argv[3]
idx = sys.argv[4:]
ims = [Image.open(f'{S}\\{name}_{i}.png').convert('RGB').crop(box) for i in idx]
w, h = ims[0].size
o = Image.new('RGB', (w * len(ims), h))
for k, im in enumerate(ims): o.paste(im, (k * w, 0))
o.save(out)
