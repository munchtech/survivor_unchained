"""Stick figures of a crowd.KEYED clip (or a clip JSON): side and front views per frame.
usage: python stick.py <keyed name> [sex f|m] [step frames] [out.png]"""
import sys, json
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70")
sys.path.insert(0, str(WT / "tools" / "anim"))
import numpy as np
from PIL import Image, ImageDraw
import crowd
from keyed import Rig
from rig import DATA, Skeleton

name = sys.argv[1]
sex = sys.argv[2] if len(sys.argv) > 2 else "m"
step = int(sys.argv[3]) if len(sys.argv) > 3 else 3
out = sys.argv[4] if len(sys.argv) > 4 else str(Path(__file__).parent / f"stick_{name.replace(':', '_')}_{sex}.png")
sk = Skeleton.load(DATA / ("folk_female_skeleton.json" if sex == "f" else "folk_male_skeleton.json"))
rig = Rig(sk)
if name.startswith("warden:"):
    from clips import warden
    clip = warden.CLIPS[name[7:]](name, rig)
    name = name[7:]
elif name.startswith("take:"):
    from clips.generated import make
    prompt, t = name[5:].rsplit("_", 1)
    clip = make(rig, name, "kimodo", f"{prompt}_{t}.bvh", place="keep")
    name = name[5:]
else:
    clip = crowd.KEYED[name](f"{sex}_{name}", rig)
grot, gpos = sk.fk(clip.rot, clip.pos)
frames = list(range(0, clip.frames, step))
if frames[-1] != clip.frames - 1:
    frames.append(clip.frames - 1)
S = 150  # px per metre
cw, ch = 330, 360
COLS = 8
rows_n = (len(frames) + COLS - 1) // COLS
img = Image.new("RGB", (cw * min(COLS, len(frames)), ch * 2 * rows_n), (34, 36, 40))
d = ImageDraw.Draw(img)
skip = ("thumb", "index", "middle", "ring", "pinky", "ball", "toe")
for i, f in enumerate(frames):
    P = gpos[f]
    c, R = i % COLS, i // COLS
    for row, (ax, sign, label) in enumerate(((2, 1, "side (+z right)"), (0, -1, "front"))):
        ox, oy = c * cw + cw // 2, (R * 2 + row) * ch + ch - 30
        d.line([(c * cw, oy), (c * cw + cw, oy)], fill=(90, 90, 90))
        for j, p in enumerate(sk.parent):
            if p < 0 or any(s in sk.names[j] for s in skip):
                continue
            a, b = P[p], P[j]
            col = (230, 120, 120) if sk.names[j].endswith("_l") else (120, 170, 240) if sk.names[j].endswith("_r") else (220, 220, 220)
            d.line([(ox + sign * a[ax] * S, oy - a[1] * S), (ox + sign * b[ax] * S, oy - b[1] * S)], fill=col, width=3)
        if row == 0:
            low = min(range(len(sk)), key=lambda j: P[j][1])
            d.text((c * cw + 6, R * 2 * ch + 4), f"f{f} {f/30:.2f}s low {sk.names[low]} {P[low][1]:+.3f}", fill=(255, 255, 0))
            hl, hr = P[sk.index["hand_l"]], P[sk.index["hand_r"]]
            d.text((c * cw + 6, R * 2 * ch + 18), f"hands y {hl[1]:.2f}/{hr[1]:.2f} z {hl[2]:.2f}/{hr[2]:.2f}", fill=(200, 200, 200))
img.save(out)
print(out, clip.frames, "frames", clip.length, "s")
