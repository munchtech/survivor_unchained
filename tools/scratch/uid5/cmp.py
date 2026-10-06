import sys
from PIL import Image
S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab47bfdab5955dac\godot\.shots'
out, box = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(','))
names = sys.argv[3:]
ims = [Image.open(f'{S}\\{n}.png').convert('RGB').crop(box) for n in names]
w, h = ims[0].size
scale = min(1.0, 1900 / (w * len(ims)))
o = Image.new('RGB', (int(w * scale) * len(ims), int(h * scale)))
for i, im in enumerate(ims): o.paste(im.resize((int(w * scale), int(h * scale))), (i * int(w * scale), 0))
o.save(out)
