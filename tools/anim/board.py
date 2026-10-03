"""A board of clips side by side: each clip's sheet as one row, labelled.

    python tools/anim/board.py <out.png> <clip> [<clip> ...] [--view three] [--frames 4] [--step 30] [--size 220x330] [--weapon W] [--outfit O] [--speed S]

For comparing takes or callings at a glance; rows are written beside the
sheets in tools/anim/out/sheets.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review import sheet  # noqa: E402


def main(argv):
    out = Path(argv[0])
    clips, kw = [], {"view": "three", "frames": 4, "step": 30, "size": (220, 330)}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k, v = a[2:], argv[i + 1]
            i += 2
            if k == "size":
                w, h = v.split("x")
                kw["size"] = (int(w), int(h))
            elif k in ("frames", "step"):
                kw[k] = int(v)
            elif k in ("speed", "start", "play"):
                kw[k] = float(v)
            else:
                kw[k] = v
        else:
            clips.append(a)
            i += 1
    rows = []
    for c in clips:
        # clip@weapon@outfit: what she holds and wears for this row.
        name, *rest = c.split("@")
        k = dict(kw)
        if rest:
            k["weapon"] = rest[0]
        if len(rest) > 1:
            k["outfit"] = rest[1]
        p = sheet(name, cols=kw["frames"], **k)
        rows.append((c, Image.open(p)))
    w = max(r.width for _, r in rows)
    h = sum(r.height for _, r in rows)
    board = Image.new("RGB", (w, h), (40, 40, 44))
    y = 0
    d = ImageDraw.Draw(board)
    for name, r in rows:
        board.paste(r, (0, y))
        d.rectangle([0, y, 8 * len(name) + 10, y + 18], fill=(0, 0, 0))
        d.text((5, y + 3), name, fill=(255, 220, 120))
        y += r.height
    board.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
