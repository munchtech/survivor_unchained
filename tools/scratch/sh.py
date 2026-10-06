"""Scratch: a board of one clip from several views, the camera on a bone.

    python sh.py <clip> <out.png> views=side,three frames=12 step=3 size=260x300 start=0
                 look=pelvis zoom=1.4 weapon=sword outfit=warden model= parts= looky=
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1e3002b800ee55ac")
sys.path.insert(0, str(REPO / "tools" / "anim"))
from review import sheet  # noqa: E402

clip, out = sys.argv[1], Path(sys.argv[2]).resolve()
kw = dict(a.split("=", 1) for a in sys.argv[3:])
views = kw.get("views", "side,three").split(",")
frames = int(kw.get("frames", 12))
w, h = (int(x) for x in kw.get("size", "260x300").split("x"))
extra = {}
if kw.get("look"):
    extra["LOOK"] = kw["look"]
if kw.get("zoom"):
    extra["ZOOM"] = kw["zoom"]
if kw.get("looky"):
    extra["LOOKY"] = kw["looky"]
if kw.get("model"):
    extra["MODEL"] = kw["model"]
    extra["PARTS"] = kw.get("parts", "")
if kw.get("yaw"):
    extra["YAW"] = kw["yaw"]
rows = []
for v in views:
    p = sheet(clip, v, frames=frames, step=int(kw.get("step", 3)), start=float(kw.get("start", 0)), size=(w, h),
              cols=int(kw.get("cols", frames)), weapon=kw.get("weapon", ""), outfit=kw.get("outfit", "warden"),
              speed=float(kw.get("speed", 0)), play=float(kw.get("play", 1)), extra=extra,
              out=out.with_name(f"{out.stem}_{v}.png"))
    rows.append((v, Image.open(p)))
W = max(r.width for _, r in rows)
board = Image.new("RGB", (W, sum(r.height for _, r in rows)), (40, 40, 44))
y = 0
d = ImageDraw.Draw(board)
for v, r in rows:
    board.paste(r, (0, y))
    d.rectangle([0, y, 8 * len(clip + v) + 20, y + 18], fill=(0, 0, 0))
    d.text((5, y + 3), f"{clip} {v}", fill=(255, 220, 120))
    y += r.height
board.save(out)
print(out)
