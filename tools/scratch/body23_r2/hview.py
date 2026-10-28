"""debug: her mesh HANGING as arm_loops_post's pit band sees it (front, orthographic clay) with the loop map's cuts"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
import r2lib as c, rview, lviz
import arm_loops_post as L
from heroine_neck import _Gl


def hang_body(glb):
    m = L.Mesh(_Gl(glb))
    U = m.U.copy()
    out = U.copy()
    for side in "lr":
        sd = L.Side(m, side)
        names = [n for n in m.names if n.endswith("_" + side) and n.split("_")[0] in L.ARMB]
        w = m.weights(names)
        R = L._rot([1.0, 0, 0], L.BAND["extend"]) @ L._rot([0, 0, 1.0], -L.BAND["adduct"])
        Js = sd.Jn["upperarm"]
        Xc = sd.c(U)
        H = Xc + w[:, None] * ((Xc - Js) @ R.T + Js - Xc)
        on = w > 1e-6
        out[on] = sd.c(H)[on]
    return m, out


if __name__ == "__main__":
    glb, lm_path, out, sd = sys.argv[1:5]
    m, H = hang_body(glb)
    b = c.body()
    k = 1.0 if sd == "l" else -1.0
    F = m.faces()
    import pit_hollow_post as ph
    N = ph.vn(H, F)
    ctr = np.array([0.15 * k, 1.38, 0.0])
    im, pr = rview.ortho(H, F, N, ctr, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 0.09, 0.10, 2.5)
    d = ImageDraw.Draw(im)
    lm = json.load(open(lm_path))
    for feat in ("front_fold", "delt_groove", "delt_front", "pit_band"):
        for ch in lviz.chains_w(lm, sd, feat):
            P = pr(H[ch])
            d.line([tuple(p) for p in P], fill=lviz.COL.get(feat), width=2)
    im.save(out)
