"""debug: a frame's clay crop (harness) round a pit with the loop map's cuts drawn (posed)"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
import r2lib as c

COL = {"front_fold": (255, 60, 60), "back_fold": (255, 160, 0), "delt_groove": (60, 120, 255), "delt_front": (0, 200, 255),
       "delt_back": (160, 80, 255), "pit_band": (0, 255, 80), "elbow_ring": (255, 255, 0)}


def welded_posed(fr, g):
    u = c.d2u(fr)
    n = len(c.body().U)
    X = np.full((n, 3), np.nan); XY = np.full((n, 2), np.nan)
    ok = u >= 0
    X[u[ok]] = g["X"][ok]; XY[u[ok]] = g["xy"][ok]
    return X, XY


def chains_w(lm, sd, feat):
    b = c.body()
    offs = np.cumsum([0] + [len(p["P"]) for p in c.gbA().prims if p["mat"] != "skin_head"])
    out = []
    for cut, chs in lm[sd].get(feat, {}).items():
        if cut == "_old":
            continue
        for ch in chs:
            out.append([b.wid[offs[pt[0][0]] + pt[0][1]] for pt in ch])
    return out


def view(f, sd, out, lm_path=None, half=110, zoom=3, feats=None, body=None, center=None):
    fr = c.frame(f)
    g = fr.geom(body or c.MemBody())
    import sh as SH
    J = c.jscreen(fr, "upperarm_" + sd) if center is None else center
    box = (int(J[0] - half), int(J[1] - half * 0.6), int(J[0] + half), int(J[1] + half * 1.4))
    rgb, ids = SH.clay(fr, g, box)
    im = Image.fromarray(rgb).resize(((box[2] - box[0]) * zoom, (box[3] - box[1]) * zoom), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    if lm_path:
        lm = json.load(open(lm_path))
        X, XY = welded_posed(fr, g)
        zt = g["z"]
        for feat in (feats or COL):
            for ch in chains_w(lm, sd, feat):
                P = (XY[ch] - [box[0], box[1]]) * zoom
                d.line([tuple(p) for p in P if np.isfinite(p).all()], fill=COL.get(feat, (255, 255, 255)), width=2)
    im.save(out)
    return im


if __name__ == "__main__":
    f, sd, out = sys.argv[1:4]
    lm = sys.argv[4] if len(sys.argv) > 4 else os.path.join(c.B23, "loops", "loop_map.json")
    view(f, sd, out, lm)
