"""debug: the game crop (A's dump png or a shot dir) round the elbow with the measured outer contour (red) and apex"""
import sys, os, numpy as np
from PIL import Image, ImageDraw
import r2lib as c, corner as K


def tile(f, sd, body="A", png_dir=None, half=80, zoom=2):
    fr = c.frame(f)
    g = fr.geom(c.MemBody() if body == "A" else c.h.GlbBody(body))
    k = K.corner(fr, g, sd)
    E = c.jscreen(fr, "lowerarm_" + sd)
    box = (int(E[0] - half), int(E[1] - half), int(E[0] + half), int(E[1] + half))
    im = Image.open(os.path.join(png_dir or c.DUMP, f + ".png")).convert("RGB").crop(box).resize((2 * half * zoom, 2 * half * zoom), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    if k:
        Q = (k["Q"] - [box[0], box[1]]) * zoom
        d.line([tuple(p) for p in Q], fill=(255, 0, 0), width=1)
        a = (k["apex"] - [box[0], box[1]]) * zoom
        d.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], outline=(0, 255, 0))
        d.text((4, 4), "%s r%.0f f%.0f" % (f, k["r_eff"], k["flat_mm"]), fill=(255, 255, 0))
    return im


if __name__ == "__main__":
    out = sys.argv[1]; body = sys.argv[2] if len(sys.argv) > 2 else "A"; pdir = sys.argv[3] if len(sys.argv) > 3 else None
    ts = [tile(f, sd, body, pdir) for f, sd in (("w_m80", "l"), ("rL90_m45", "l"), ("s_p45", "r"))]
    W = sum(t.width for t in ts) + 8 * (len(ts) - 1)
    s = Image.new("RGB", (W, ts[0].height), (20, 20, 20)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + 8
    s.save(out)
