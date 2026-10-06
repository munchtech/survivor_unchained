"""Contact sheet of shots: python cands.py OUT DIR name..."""
import os
import sys
from PIL import Image

out, S = sys.argv[1], sys.argv[2]
names = sys.argv[3:]
ims = [Image.open(os.path.join(S, n + '.png')).convert('RGB').resize((480, 270)) for n in names]
cols = 3
o = Image.new('RGB', (480 * cols, 270 * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims):
    o.paste(im, ((i % cols) * 480, (i // cols) * 270))
o.save(out)
