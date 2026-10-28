"""debug: arm_loops_post's pit band (as configured by LOOPS_BAND) drawn on v1's GAME frames without a rebuild: its field
on v1's mesh, iso-lines by marching triangles, posed by the dump (edge lerp), over the game crop"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
import r2lib as c, lviz
import arm_loops_post as L
from heroine_neck import _Gl

_M = [None]


def mesh():
    if _M[0] is None:
        m = L.Mesh(_Gl(c.V1[0]))
        kd = cKDTree(c.body().U)
        _, idx = kd.query(m.U)
        m.to_b = idx
        _M[0] = m
    return _M[0]


def iso(U, F, g, mask):
    """segments of g = 0 over faces whose 3 points are in mask: list of ((a,b,t),(a,b,t))"""
    segs = []
    for f in F[mask[F].all(1)]:
        pts = []
        for k in range(3):
            a, b = int(f[k]), int(f[(k + 1) % 3])
            if (g[a] < 0) != (g[b] < 0):
                t = g[a] / (g[a] - g[b])
                pts.append((a, b, t))
        if len(pts) == 2:
            segs.append(pts)
    return segs


def band_lines(sd):
    m = mesh()
    sdo = L.Side(m, sd)
    ops, info = L.plan_band(m, sdo, lambda *a: None)
    Uc = sdo.c(m.U)
    F = m.faces()
    out = []
    for kind, name, f, cval, reg in ops:
        g = f(Uc) - cval
        r = reg(Uc)
        out.append((name, iso(Uc, F, g, r)))
    return out, info


def draw(fname, sd, out_png, half=75, zoom=3, extra=("front_fold", "delt_groove")):
    fr = c.frame(fname)
    g = fr.geom(c.MemBody())
    X, XY = lviz.welded_posed(fr, g)
    m = mesh()
    J = c.jscreen(fr, "upperarm_" + sd)
    box = (int(J[0] - half), int(J[1] - 40), int(J[0] + half), int(J[1] + 110))
    im = Image.open(os.path.join(c.DUMP, fname + ".png")).convert("RGB").crop(box)
    im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    lm = json.load(open(os.path.join(c.B23, "loops", "loop_map.json")))
    for feat in extra:
        for ch in lviz.chains_w(lm, sd, feat):
            P = (XY[ch] - [box[0], box[1]]) * zoom
            d.line([tuple(p) for p in P if np.isfinite(p).all()], fill=lviz.COL[feat], width=1)
    lines, info = band_lines(sd)
    for name, segs in lines:
        col = (0, 255, 80) if name.endswith("+0") else (200, 255, 0)
        for (a1, b1, t1), (a2, b2, t2) in segs:
            p = [(1 - t) * XY[m.to_b[a]] + t * XY[m.to_b[b]] for a, b, t in ((a1, b1, t1), (a2, b2, t2))]
            p = [(q - [box[0], box[1]]) * zoom for q in p]
            d.line([tuple(p[0]), tuple(p[1])], fill=col, width=2)
    im.save(out_png)
    return im, info


if __name__ == "__main__":
    out = sys.argv[1]
    ims = []
    for f, sd in (("look_f", "r"), ("w_p45", "r"), ("w_m45", "l")):
        im, info = draw(f, sd, out + "_%s.png" % f)
        ims.append(im)
        print(f, sd, info["p1"], info["p2"], info["len_hang_mm"])
    W = sum(i.width for i in ims) + 16
    s = Image.new("RGB", (W, max(i.height for i in ims))); x = 0
    for i in ims:
        s.paste(i, (x, 0)); x += i.width + 8
    s.save(out + ".png")
