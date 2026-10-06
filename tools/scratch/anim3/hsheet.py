"""Boards of clips on the hero or the heroine (anim_review.gd), one row each.

    python hsheet.py out.png clip[@weapon] ... [view=three] [frames=6] [step=4] [size=260x380] [model=hero] [speed=0] [start=0]
"""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\tools\anim")
from PIL import Image, ImageDraw  # noqa: E402

from review import sheet  # noqa: E402

out = Path(sys.argv[1])
kw = {"view": "three", "frames": "6", "step": "4", "size": "260x380", "model": "hero", "speed": "0", "start": "0", "outfit": "none",
      "hair": "none"}
clips = []
for a in sys.argv[2:]:
    if "=" in a:
        k, v = a.split("=", 1)
        kw[k] = v
    else:
        clips.append(a)
w, h = (int(x) for x in kw["size"].split("x"))
rows = []
here = Path(__file__).parent / "sh"
for c in clips:
    name, *rest = c.split("@")
    extra = {}
    if kw["model"] != "her":
        extra["MODEL"] = kw["model"]
    p = sheet(name, kw["view"], frames=int(kw["frames"]), step=int(kw["step"]), size=(w, h), cols=int(kw["frames"]),
              weapon=rest[0] if rest else "", outfit=kw["outfit"], hair=kw["hair"], speed=float(kw["speed"]),
              start=float(kw["start"]), extra=extra, out=here / f"hs_{name.replace('/', '_')}_{kw['view']}.png")
    rows.append((c, Image.open(p)))
W = max(r.width for _, r in rows)
board = Image.new("RGB", (W, sum(r.height for _, r in rows)), (40, 40, 44))
d = ImageDraw.Draw(board)
y = 0
for name, r in rows:
    board.paste(r, (0, y))
    d.rectangle([0, y, 8 * len(name) + 10, y + 18], fill=(0, 0, 0))
    d.text((5, y + 3), name, fill=(255, 220, 120))
    y += r.height
board.save(out)
print(out)
