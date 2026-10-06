"""Stick figures of a clip: side and front views per frame, the lowest joint and the hands.
usage: python stick.py <spec> [body her|hero|m|f] [step frames] [out.png] [from=F] [to=F]
spec: take:<prompt>_<n> | story:<name> | warden:<name> | keyed:<name> (crowd.KEYED)"""
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274")
sys.path.insert(0, str(WT / "tools" / "anim"))
from PIL import Image, ImageDraw
from keyed import Rig
from rig import DATA, Skeleton

args = [a for a in sys.argv[1:] if "=" not in a]
kw = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
spec = args[0]
body = args[1] if len(args) > 1 else "her"
step = int(args[2]) if len(args) > 2 else 6
out = args[3] if len(args) > 3 else str(Path(__file__).parent / "st" / f"st_{spec.replace(':', '_')}_{body}.png")
Path(out).parent.mkdir(exist_ok=True)
skel = {"her": "heroine_skeleton.json", "hero": "hero_skeleton.json", "m": "folk_male_skeleton.json", "f": "folk_female_skeleton.json"}[body]
sk = Skeleton.load(DATA / skel)
rig = Rig(sk, body={"her": "her", "hero": "him"}.get(body, "her"))
kind, name = spec.split(":", 1)
if kind == "warden":
    from clips import warden
    clip = warden.CLIPS[name](name, rig)
elif kind == "take":
    from clips.generated import make
    prompt, t = name.rsplit("_", 1)
    clip = make(rig, name, "kimodo", f"{prompt}_{t}.bvh", place=kw.get("place", "keep"))
elif kind == "story":
    from clips import story
    clip = dict(story.ALL)[name](rig)
elif kind == "keyed":
    import crowd
    clip = crowd.KEYED[name](name, rig)
else:
    import importlib
    clip = dict(importlib.import_module(f"clips.{kind}").ALL)[name](rig)
grot, gpos = sk.fk(clip.rot, clip.pos)
f0, f1 = int(kw.get("from", 0)), int(kw.get("to", clip.frames - 1))
frames = list(range(f0, f1 + 1, step))
if frames[-1] != f1:
    frames.append(f1)
S = 150  # px per metre
cw, ch = 300, 330
COLS = min(10, len(frames))
rows_n = (len(frames) + COLS - 1) // COLS
img = Image.new("RGB", (cw * COLS, ch * 2 * rows_n), (34, 36, 40))
d = ImageDraw.Draw(img)
skip = ("thumb", "middle", "ring", "pinky", "ball", "toe")
for i, f in enumerate(frames):
    P = gpos[f]
    c, R = i % COLS, i // COLS
    for row, (ax, sign) in enumerate(((2, 1), (0, -1))):
        ox, oy = c * cw + cw // 2, (R * 2 + row) * ch + ch - 30
        d.line([(c * cw, oy), (c * cw + cw, oy)], fill=(90, 90, 90))
        for j, p in enumerate(sk.parent):
            if p < 0 or sk.names[p] == "root" or any(s in sk.names[j] for s in skip):
                continue
            a, b = P[p], P[j]
            col = (230, 120, 120) if sk.names[j].endswith("_l") else (120, 170, 240) if sk.names[j].endswith("_r") else (220, 220, 220)
            d.line([(ox + sign * a[ax] * S, oy - a[1] * S), (ox + sign * b[ax] * S, oy - b[1] * S)], fill=col, width=2)
        if row == 0:
            low = min(range(len(sk)), key=lambda j: P[j][1])
            d.text((c * cw + 6, R * 2 * ch + 4), f"f{f} {f/30:.2f}s low {sk.names[low]} {P[low][1]:+.3f}", fill=(255, 255, 0))
            hl, hr, hd = P[sk.index["hand_l"]], P[sk.index["hand_r"]], P[sk.index["Head"]]
            d.text((c * cw + 6, R * 2 * ch + 18), f"hl {hl[0]:+.2f},{hl[1]:.2f},{hl[2]:+.2f} hr {hr[0]:+.2f},{hr[1]:.2f},{hr[2]:+.2f}", fill=(200, 200, 200))
            d.text((c * cw + 6, R * 2 * ch + 32), f"head {hd[0]:+.2f},{hd[1]:.2f},{hd[2]:+.2f}", fill=(200, 200, 200))
img.save(out)
print(out, clip.frames, "frames", round(clip.length, 2), "s", img.size)
