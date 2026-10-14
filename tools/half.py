"""Half-size copies of pictures for a lead's working looks (the owner, 14 Oct: a quarter of the tokens).

  python tools/half.py a.png [b.jpg ...]      -> a_half.jpg ... next to each; Read those
  python tools/half.py --scale 0.33 sheet.jpg  -> other scales

Working looks only (did it render, is the framing right, did the build change). Judges, and
anything going to the owner, read full size.
"""
import sys
from pathlib import Path

from PIL import Image

args = sys.argv[1:]
scale = 0.5
if args[:1] == ["--scale"]:
    scale, args = float(args[1]), args[2:]
for a in args:
    p = Path(a)
    im = Image.open(p)
    im = im.convert("RGB").resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    out = p.with_name(f"{p.stem}_half.jpg")
    im.save(out, quality=88)
    print(out)
