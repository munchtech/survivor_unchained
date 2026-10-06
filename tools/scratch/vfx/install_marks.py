"""Install the rise's painted marks into godot/art/fx/marks.

watch_dial: from watch_dial2, keyed from black with a floor, so only its engraved lines, hours,
stars and lantern are kept (the dial's dark stone face, kept at a third, browned the ground
and the crowd standing on it). smoulder: from smoulder2 as marks.py keyed it."""
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "marks_out")
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545"
DST = os.path.join(WT, "godot", "art", "fx", "marks")
SIZE = 512

src = Image.open(os.path.join(SRC, "watch_dial2_source.jpg")).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
c = np.asarray(src).astype(np.float32) / 255.0
hi = c.max(axis=2)
a = np.clip((hi - 0.2) / 0.45, 0, 1)
rgb = np.where(a[..., None] > 1e-3, c / np.maximum(hi[..., None], 1e-3), 0)
y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
r = np.hypot(x - SIZE / 2, y - SIZE / 2) / (SIZE / 2)
edge = np.clip((1 - r) / 0.12, 0, 1)
a = a * edge * edge * (3 - 2 * edge)
emit = c * np.clip((hi - 0.28) * 1.8, 0, 1)[..., None] * a[..., None]
Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a]) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(DST, "watch_dial.png"))
Image.fromarray((np.clip(emit, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(DST, "watch_dial_emit.png"))
# Light at the border would show the square: refuse it.
border = np.concatenate([a[:4].ravel(), a[-4:].ravel(), a[:, :4].ravel(), a[:, -4:].ravel()])
print("watch_dial border alpha max", float(border.max()), "mean alpha", float(a.mean()))

shutil.copy(os.path.join(SRC, "smoulder2.png"), os.path.join(DST, "smoulder.png"))
shutil.copy(os.path.join(SRC, "smoulder2_emit.png"), os.path.join(DST, "smoulder_emit.png"))
sa = np.asarray(Image.open(os.path.join(DST, "smoulder.png")))[..., 3].astype(np.float32) / 255
border = np.concatenate([sa[:4].ravel(), sa[-4:].ravel(), sa[:, :4].ravel(), sa[:, -4:].ravel()])
print("smoulder border alpha max", float(border.max()))
print("installed")
