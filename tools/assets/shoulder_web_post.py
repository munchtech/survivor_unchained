"""Her deltoid and front armpit web (Body 22, 27 Oct 2026: the owner's one last in-team loop on her shoulder and armpit;
judge 5 on the anatomy resculpt: both deltoids ball caps ending in a ledge over a slimmer tube, the hanging arm plugged
in behind the breast through a dark gap with no front armpit fold). Runs after arm_anatomy_post, before elbow_psd_post.
Shaped IN CAMERA (scratch body22/shoulder: the Body 20 harness poses the body exactly as the game does at look_f,
w_p45, w_m45 and s_p45, and the outlines are fitted to a reference outline per camera), not by volumes unioned on her
skin (arm_anatomy_post FORM "fold_tried": a fin or a nub).

THE DELTOID (fix 5): a radial move delta(s, phi) (mm, + out) on the upper arm's chart (heroine_arm_tone frames: s mm
down the humerus line from the shoulder joint, phi 0 front, 90 out, 180 back, -90 in), bilinear on a 15 mm x 30 deg
grid, both sides from the same grid (mirrored by the chart). Fitted (Gauss-Newton on the outer outline, 3 rounds) to
a reference outline per camera: the cap's max 3 px in (1.2 px at the Look, its cap-to-cap width held), then one smooth
Hermite taper from the cap into the V (45% down the upper arm, + 25 px) with no ledge, notches under it filled; plus a
fairing pull on the outer face (phi 30-150, s 30-135: the radius a smooth taper, no ball over a step). Then a light
Taubin fairing of the deltoid's surface (the crease on its front, a dent and a lump at the Look). Feathered by her
arm's skinning share and to nothing by s 150 (the biceps' middle: the elbow and forearm are not this step's).

THE WEB (fix 6): the front armpit's notch bridged. At the hanging arm's pose (w_p45, her right), her posed surface's
rolling-ball closing (R 24 mm) gives the bridge over the slot's mouth; its move on the camera-visible rim (in a band
0-75 mm below the shoulder joint, in front of it) is the handle of a biharmonic field on her posed surface (zero 85 mm
out), taken to rest by each vertex's blended skin matrix and mirrored to her left. (A second field built at w_m45's
bent left arm, merged per side, opened the pit wider at s_p45, r132 and rL90: not used.) It fills the notch; it does
not yet build the fold's convex rounded edge.
Baked per welded vertex (shoulder_web_post.json, with each vertex's rest position as a guard: same topology only).
No skin-weight change.

Her shoulder pose-space shapes (shoulder_*) kept as approved (arm_contour_post.psd_keep); the rest ride on the shape.

    python tools/assets/shoulder_web_post.py <in heroine.glb> <out heroine.glb>
Idempotent: done-mark shoulder_web (a marked body is copied unchanged).
"""
import json
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MARK = "shoulder_web"
DATA = os.path.join(HERE, "shoulder_web_post.json")


def _ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def charts(b):
    """per welded vertex: the upper arm chart's s (mm), phi (deg) of its side, and the feather F"""
    import heroine_arm_tone as tone
    import arm_contour_post as ac
    FR = tone.frames(b)
    S, P = np.full(len(b.U), np.nan), np.full(len(b.U), np.nan)
    F = np.zeros(len(b.U))
    for sd in "lr":
        f = FR[sd]
        O, ax, fv, l = f["up"]
        s, phi, _ = tone._chart(b.U * f["mir"] + f["off"], O, ax, fv, l)
        side = (b.U[:, 0] > 0.001) if sd == "l" else (b.U[:, 0] < 0.001)
        fe = _ss((ac._armw(b, sd) - 0.15) / 0.45) * _ss(np.clip((s + 50) / 22, 0, 1) * np.clip((150 - s) / 28, 0, 1))
        S[side], P[side], F[side] = s[side], phi[side], fe[side]
    return S, P, F


def basis(s, phi, SN, PN):
    n = len(s)
    si = np.clip((s - SN[0]) / (SN[1] - SN[0]), 0, len(SN) - 1.0001)
    i0 = np.floor(si).astype(int)
    fs = si - i0
    dp = PN[1] - PN[0]
    pp = (phi - PN[0]) / dp % len(PN)
    j0 = np.floor(pp).astype(int) % len(PN)
    fp = pp - np.floor(pp)
    j1 = (j0 + 1) % len(PN)
    W = np.zeros((n, len(SN) * len(PN)))
    r = np.arange(n)
    for ii, ws in ((i0, 1 - fs), (np.minimum(i0 + 1, len(SN) - 1), fs)):
        for jj, wp in ((j0, 1 - fp), (j1, fp)):
            np.add.at(W, (r, ii * len(PN) + jj), ws * wp)
    return W


def fair_w(S, P, F):
    """the deltoid's surface fairing weight: s -25..125, the outer three quarters round (not the pit side)"""
    import heroine_arm_tone as tone
    ok = np.isfinite(S)
    w = np.zeros(len(S))
    s, p = S[ok], P[ok]
    ws = np.clip((s + 30) / 15, 0, 1) * np.clip((130 - s) / 20, 0, 1)
    wp = np.clip((115 - np.abs(tone._wrap(p - 75))) / 25, 0, 1)
    w[ok] = _ss(ws) * _ss(wp) * np.clip(F[ok] / 0.5, 0, 1)
    return w


def deltoid_move(b, D):
    import pit_hollow_post as ph
    S, P, F = charts(b)
    N = ph.vn(b.U, b.F)
    for _ in range(3):
        N = N + b.lap(N) * 0.5
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    SN, PN, delta = np.array(D["SN"]), np.array(D["PN"]), np.array(D["delta"])
    ok = np.isfinite(S) & (F > 1e-3)
    d = np.zeros((len(b.U), 3))
    v = basis(S[ok], P[ok], SN, PN) @ delta.ravel()
    d[ok] = (v * F[ok])[:, None] * N[ok] / 1000.0
    X = b.U + d
    w = fair_w(S, P, F)
    for _ in range(D.get("fair_it", 6)):                       # Taubin: no shrink
        for k in (0.5, -0.53):
            X = X + (k * w)[:, None] * b.lap(X)
    return X - b.U


def web_move(b, D):
    W = D["web"]
    idx = np.array(W["idx"], int)
    if idx.max() >= len(b.U) or np.abs(b.U[idx] - np.array(W["pos"])).max() > 0.002:
        sys.exit("SHOULDER_WEB: the baked web doesn't fit this body's vertices (same topology only)")
    d = np.zeros((len(b.U), 3))
    d[idx] = np.array(W["d"])
    return d


def run(src, dst, quiet=False):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    import arm_contour_post as ac
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    g = G.g
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("SHOULDER_WEB: %s has had it" % dst)
        return None
    D = json.load(open(DATA))
    b = ph.Body(G)
    dD = deltoid_move(b, D)
    dW = web_move(b, D)
    dU = dD + dW
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        Nn = G.get(ni).astype(float) + (n1 - n0)[w]
        Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, Nn.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    rep = {}
    ac.psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"deltoid_max_mm": round(float(np.linalg.norm(dD, axis=1).max() * 1000), 2),
                "web_max_mm": round(float(np.linalg.norm(dW, axis=1).max() * 1000), 2), "max_mm": round(float(mv.max()), 2)}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    if not quiet:
        print("SHOULDER_WEB: %d points moved > 0.5 mm, max %.1f mm -> %s" % ((mv > 0.5).sum(), mv.max(), dst))
        print("  " + json.dumps(ex[MARK]))
        print("  psd kept (points, max mm taken back): " + ", ".join("%s %d/%.1f" % (k, v[0], v[1]) for k, v in rep.items()))
    return ex[MARK]


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
