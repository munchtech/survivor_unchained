"""debug: her REST mesh seen from a direction (orthographic clay), a region round a point, with loop-map cuts and marks"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
import r2lib as c
import lviz


def ortho(U, F, N, ctr, right, up, half_w, half_h, ppm=2.0, light=(-0.4, 0.5, 0.75)):
    fwd = np.cross(right, up)            # toward the viewer
    rel = U - ctr
    x = rel @ right * 1000 * ppm + half_w * 1000 * ppm
    y = -(rel @ up) * 1000 * ppm + half_h * 1000 * ppm
    z = rel @ fwd
    W, H = int(2 * half_w * 1000 * ppm), int(2 * half_h * 1000 * ppm)
    fn = np.cross(U[F[:, 1]] - U[F[:, 0]], U[F[:, 2]] - U[F[:, 0]])
    front = (fn @ fwd) > 0
    T = np.nonzero(front)[0]
    T = T[np.argsort(z[F[T]].mean(1))]
    im = Image.new("RGB", (W, H), (25, 25, 30)); d = ImageDraw.Draw(im)
    L = np.array(light); L = L / np.linalg.norm(L)
    Lw = L[0] * right + L[1] * up + L[2] * fwd
    sh_ = 0.2 + 0.8 * np.clip((N @ Lw), 0, 1)
    q = np.c_[x, y]
    for t in T:
        tri = q[F[t]]
        if tri[:, 0].max() < 0 or tri[:, 1].max() < 0 or tri[:, 0].min() > W or tri[:, 1].min() > H:
            continue
        s = sh_[F[t]].mean()
        d.polygon([tuple(p) for p in tri], fill=(int(235 * s), int(200 * s), int(175 * s)))
    return im, (lambda P: np.c_[(P - ctr) @ right * 1000 * ppm + half_w * 1000 * ppm, -((P - ctr) @ up) * 1000 * ppm + half_h * 1000 * ppm])


def view(sd, out, lm_path, marks=(), ctr=None, dirn="front", half=(0.10, 0.11), ppm=2.5, feats=None, curves=()):
    b = c.body()
    U, F = b.U, b.F
    N = b.N
    k = 1.0 if sd == "l" else -1.0
    if ctr is None:
        ctr = np.array([0.15 * k, 1.38, 0.0])
    if dirn == "front":
        right, up = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    else:   # from her side, outward
        right, up = np.array([0, 0, -1.0 * k]), np.array([0, 1.0, 0])
    im, pr = ortho(U, F, N, ctr, right, up, half[0], half[1], ppm)
    d = ImageDraw.Draw(im)
    lm = json.load(open(lm_path))
    for feat in (feats or lviz.COL):
        for ch in lviz.chains_w(lm, sd, feat):
            P = pr(U[ch])
            d.line([tuple(p) for p in P], fill=lviz.COL.get(feat, (255, 255, 255)), width=2)
    for P, col in marks:
        p = pr(np.array(P)[None])[0]
        d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], outline=col, width=2)
    for P, col in curves:
        Q = pr(np.asarray(P))
        d.line([tuple(p) for p in Q], fill=col, width=2)
    # mm grid ticks every 20 mm
    for gx in range(-100, 101, 20):
        p = pr(ctr + right * gx / 1000)[0] if False else None
    im.save(out)
    return im, pr


if __name__ == "__main__":
    sd, out = sys.argv[1:3]
    view(sd, out, os.path.join(c.B23, "loops", "loop_map.json"))
