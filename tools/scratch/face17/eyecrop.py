"""eyecrop.py OUT IMG...: each image's two eyes, cropped round the irises at 3 iris radii and scaled to 120 px per
radius, one row per image."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
K = int(os.environ.get('K', '40'))
def path(s):
    for p in (s, os.path.join(S, s + '.png'), os.path.join(R, s + '.png')):
        if os.path.exists(p): return p
rows = []
for n in sys.argv[2:]:
    im = Image.open(path(n)).convert('RGB'); up = 2 if im.height < 900 else 1
    big = im.resize((im.width * up, im.height * up), Image.LANCZOS)
    L = ff.detect(np.asarray(big))[:, :2]; row = []
    for c0, ring in ((468, range(469, 473)), (473, range(474, 478))):
        c = L[c0]; r = np.mean([np.linalg.norm(L[i] - c) for i in ring])
        t = big.crop((int(c[0] - 2.2 * r), int(c[1] - 1.5 * r), int(c[0] + 2.2 * r), int(c[1] + 1.5 * r)))
        row.append(t.resize((int(4.4 * K), int(3 * K)), Image.LANCZOS))
    rows.append((n, row))
W = 2 * int(4.4 * K) + 6; H = len(rows) * (3 * K + 18)
sh = Image.new('RGB', (W, H), (15, 15, 15)); d = ImageDraw.Draw(sh)
for i, (n, row) in enumerate(rows):
    y = i * (3 * K + 18); d.text((4, y + 2), n, fill=(230, 230, 230))
    for j, t in enumerate(row): sh.paste(t, (j * (int(4.4 * K) + 6), y + 16))
sh.save(sys.argv[1], quality=90)
