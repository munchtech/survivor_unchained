"""Her lips sealed at rest, and her lower front teeth kept down and in shade, per face key, in her exported glb.

The mouth cleanup round 2 (judge a00723b7, 14 October 2026).
- At rest a glint showed in her lips' line on Moonlit (right of centre at the Look), Doe and Fey: not teeth, but the top
  of her lower lip, which on those faces rises behind its front facing up and aside (away from the camera) to meet her
  upper lip further back. The slit's turned-away band (head facing the view less than 0.5, or the inside, between her
  lips' fronts) was 1.0-2.0 mm there against 0.0-0.4 on Saffron and Highborn. SEAL holds, per face, controls at CTRL_X
  (mm off her mouth's middle; fading out over X_END): her lower lip's top (from RAMP_L_MM under her lips' line up) moved
  down by a (up where a < 0) and back by b; her upper lip's rows under her lips' line (fading out RAMP_U_MM over it)
  down by d and forward by e. They were found against that band at the Look's three views (pitch -6, yaw -17, 0, 17),
  her lips' meeting line kept within 0.15 mm where it shows. Her lips' outer border (5+ mm off the line) and their
  fronts' depth are untouched.
- Hard-won's laugh: a dark notch at her upper lip's edge over her right central incisor (her lip's underside, turned
  down and away, after the gum raise). Her upper lip's inner rows (DEEP_MM behind her lips' front, under the line) are
  dropped by k, turning that underside to the camera and laying the lip's edge on the tooth; at rest they sit behind
  her lower lip.
- JAW: her lower jaw's contents (lower teeth, lower gum, tongue) set lower in the face key: Fey's open mouth (1.0)
  showed her lower incisors' tips as bright specks over her lower lip's edge; a snarl (.8) one tip as a chip on
  Saffron, Hard-won and Sunborn. And her lower front teeth's tips are put in her lower lip's shade (TIP).
Normals of every moved head point are redone in its face key.

    python tools/assets/heroine_mouth_seal.py [GLB [OUT]]

Numpy only. In her build it runs after heroine_mouth_inner: it moves head points 0-4 mm from her lips' line, outside the
bow window of heroine_face_bow.run_keys (5.5-18 mm over it). On one already done (her head's extras say mouth_seal) it
does nothing.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_mouth as hmo  # noqa: E402
import heroine_mouth_inner as hmi  # noqa: E402

GLB = hmo.GLB
MARK = "mouth_seal"
RAMP_L_MM = 1.5                   # (her lower lip's top pressed down by a, fading to none RAMP_L_MM under her lips' line)
RAMP_U_MM = 2.0                   # (her upper lip's rows under her lips' line brought down by d, fading to none RAMP_U_MM over it)
X_END = (0.015, 0.018)            # (the controls fade out from here to here off her mouth's middle; her corners as judged)
DEEP_MM = (7.0, 10.0)             # (her upper lip's inner rows: from this deep behind her lips' front, fully that deep)
CTRL_X = np.arange(-12, 12.1, 3.0)
# (per face: (a, d) in mm at CTRL_X, found against the slit's turned-away band at the Look's views (pitch -6, yaw -17, 0, 17))
SEAL = {
    "moonlit": [[0.7, 0.4, 0.0, 0.3], [-0.4, 1.0, 0.8, 0.0], [-0.2, 1.4, 0.8, 0.0], [-0.2, 1.4, 0.8, 0.3], [-0.1, 0.6, 0.7, 0.0],
                [-0.2, 1.4, 0.8, 0.4], [0.0, 1.4, 0.8, 0.2], [-0.4, 1.1, 0.8, 0.2], [0.3, 0.2, 0.1, 0.2]],
    "doe": [[-0.3, 0.7, 0.8, 0.0], [0.2, 0.8, 0.8, 0.1], [-0.4, 0.8, 0.8, 0.6], [-0.1, 0.0, 0.4, 0.0], [0.0, 0.0, 0.0, 0.0],
            [-0.2, 0.4, 0.2, 0.2], [-0.4, 0.9, 0.8, 0.6], [0.2, 0.8, 0.8, 0.0], [-0.3, 0.7, 0.8, 0.0]],
    "fey": [[0.0, 0.4, 0.2, 0.0], [0.0, 0.5, 0.4, 0.0], [0.0, 0.4, 0.2, 0.0], [-0.3, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0], [0.0, 0.4, 0.0, 0.0], [-0.7, 1.0, 0.8, 0.4], [0.2, 0.2, 0.2, 0.0]],
    # (Hard-won's laugh (judge a00723b7): a dark notch at her upper lip's edge over her right central incisor, the
    # underside of her lip turned down and away; its inner rows dropped so the lip's edge lies on the tooth)
    "hardwon": [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 1.0], [0, 0, 0, 0, 2.0], [0, 0, 0, 0, 2.0], [0, 0, 0, 0, 2.0],
                [0, 0, 0, 0, 2.0], [0, 0, 0, 0, 2.0], [0, 0, 0, 0, 1.0]],
}
# (her lower jaw's contents (lower teeth, lower gum, tongue) set this much lower (mm) in the face key: Fey's open mouth (1.0)
# showed her lower incisors' tips as 2-3 bright specks over her lower lip's edge, a snarl (.8) one tip as a chip on
# Saffron, Hard-won and Sunborn. And her lower front teeth's tips stand in her lower lip's shade: their share (heroine_
# teethshade) falls by TIP over their top TIP_MM)
JAW = {"fey": 1.4, "saffron": 1.5, "hardwon": 1.4, "sunborn": 2.0}
TIP, TIP_MM, TIP_X = 0.35, 2.0, 0.012


def controls(face):
    c = SEAL.get(face)
    return None if c is None else np.asarray(c, dtype=np.float64).reshape(len(CTRL_X), -1)


def _vnormals(P, T, weld):
    """Area-weighted normals, copies of a point (UV seams) as one."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    acc = np.zeros((weld.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, weld[T[:, k]], fn)
    N = acc[weld]
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def seal_face(V, D, mo, mid, weld, face, lips, ctrl):
    """The face key's new deltas, its lips moved by the controls ctrl ((a, d, e, b) mm at CTRL_X: her lower lip's top
    down by a (up where less than 0), her upper lip's rows under her lips' line down by d and forward by e, her lower
    lip's top back by b; her upper lip's inner rows, DEEP_MM and more behind her lips' front, down by k)."""
    ctrl = np.pad(ctrl, ((0, 0), (0, 5 - ctrl.shape[1])))
    Df = D["face_" + face].copy()
    P = V + Df + lips * D.get("lips_lower+", 0)
    line = hmo.lips_line(P, D["mouth_open"])
    zf = P[(np.abs(P[:, 1] - line) < 0.003) & (np.abs(P[:, 0] - mid) < 0.005), 2].max()
    vx = P[:, 0] - mid
    fade = 1 - hmo._s01((np.abs(vx) - X_END[0]) / (X_END[1] - X_END[0]))
    a = np.interp(vx * 1000, CTRL_X, ctrl[:, 0]) / 1000 * fade
    d = np.interp(vx * 1000, CTRL_X, ctrl[:, 1]) / 1000 * fade
    e = np.interp(vx * 1000, CTRL_X, ctrl[:, 2]) / 1000 * fade
    b = np.interp(vx * 1000, CTRL_X, ctrl[:, 3]) / 1000 * fade
    k = np.interp(vx * 1000, CTRL_X, ctrl[:, 4]) / 1000 * fade
    zone = (np.abs(vx) < X_END[1]) & (np.abs(P[:, 1] - line) < 0.004) & (P[:, 2] > zf - 0.012)
    lower = mo > 0.002
    h = P[:, 1] - line
    wl = hmo._s01((h + RAMP_L_MM / 1000) / (RAMP_L_MM / 1000))
    wu = 1 - hmo._s01(h / (RAMP_U_MM / 1000))
    deep = hmo._s01((zf - P[:, 2] - DEEP_MM[0] / 1000) / ((DEEP_MM[1] - DEEP_MM[0]) / 1000))
    dy = np.where(lower, -a * wl, -d * wu - k * wu * deep) * zone
    dz = np.where(lower, -b * wl, e * wu) * zone
    cnt = np.bincount(weld, minlength=weld.max() + 1)
    dy = np.bincount(weld, dy, minlength=weld.max() + 1)[weld] / cnt[weld]
    dz = np.bincount(weld, dz, minlength=weld.max() + 1)[weld] / cnt[weld]
    Df[:, 1] += dy
    Df[:, 2] += dz
    return Df, (np.abs(dy) > 1e-7) | (np.abs(dz) > 1e-7)


def jaw(js, binc, chunks):
    """JAW and TIP on her teeth and tongue."""
    import heroine_teethshade as hts
    out = []
    tm, tp = hmo._prim(js, "teeth")
    TV = hs._read(js, binc, tp["attributes"]["POSITION"]).astype(np.float64)
    TF = hs._read(js, binc, tp["indices"]).astype(np.int64).reshape(-1, 3)
    tn = tm["extras"]["targetNames"]
    n = np.linalg.norm(hs._read(js, binc, tp["targets"][tn.index("mouth_open")]["POSITION"]), axis=1)
    body = hts._bodies(TV, TF)
    gum = np.bincount(body).argmax()
    low = np.array([b != gum and (body == b).any() and n[body == b].mean() > 0.002 for b in range(body.max() + 1)])
    w = np.where(body == gum, hmo._s01((n - 0.001) / 0.002), low[body].astype(float))
    gm, gp = hmo._prim(js, "tongue")
    gn = gm["extras"]["targetNames"]
    for f, mm in JAW.items():
        for prim, names, wt in ((tp, tn, w), (gp, gn, None)):
            if "face_" + f not in names:
                continue
            a = prim["targets"][names.index("face_" + f)]["POSITION"]
            Df = hs._read(js, binc, a).astype(np.float64)
            Df[:, 1] -= mm / 1000 * (1.0 if wt is None else wt)
            hs._set(js, chunks, a, Df, minmax=True)
        out.append("jaw %s %.1f mm lower" % (f, mm))
    # (the tips' shade)
    ci = tp["attributes"]["COLOR_0"]
    col = hs._read(js, binc, ci).astype(np.float64)
    mid = 0.5 * (TV[:, 0].min() + TV[:, 0].max())
    front = low[body] & (np.abs(TV[:, 0] - mid) < TIP_X)
    top = np.zeros(len(TV))
    for b in np.where(low)[0]:
        m = body == b
        top[m] = TV[m, 1].max()
    f = 1 - TIP * hmo._s01((TV[:, 1] - (top - TIP_MM / 1000)) / (TIP_MM / 1000)) * front
    col[:, :3] *= f[:, None]
    hs._set_dense(js, chunks, ci, col)
    out.append("lower tips shaded on %d points" % int((f < 0.999).sum()))
    return out


def run(path, out=None, faces=None):
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    hm, hp = hmo._prim(js, "skin_head")
    if MARK in hm.get("extras", {}):
        print("MOUTH_SEAL: already done in", path, "- nothing done")
        if out and out != path:
            hs._save(out, js, chunks)
        return
    names = hm["extras"]["targetNames"]
    V = hs._read(js, binc, hp["attributes"]["POSITION"]).astype(np.float64)
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    alpha = hs._read(js, binc, hp["attributes"]["COLOR_0"])[:, 3]
    D = {n: hs._read(js, binc, t["POSITION"]).astype(np.float64) for n, t in zip(names, hp["targets"])
         if n.startswith("face_") or n in ("mouth_open", "lips_lower+")}
    mo = np.linalg.norm(D["mouth_open"], axis=1)
    line = hmo.lips_line(V, D["mouth_open"])
    mid = np.median(V[(np.abs(V[:, 1] - line) < 0.004) & (V[:, 2] > 0.09), 0])
    _, weld = np.unique(np.round(V / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    weld = weld.ravel()
    lips = hmi._lips()
    done = []
    for f in (faces or SEAL):
        if not f or "face_" + f not in D or controls(f) is None:
            continue
        Df, moved = seal_face(V, D, mo, mid, weld, f, lips.get(f, 0.0), controls(f))
        t = hp["targets"][names.index("face_" + f)]
        P0, P1 = V + D["face_" + f], V + Df
        n0, n1 = _vnormals(P0, T, weld), _vnormals(P1, T, weld)
        ch = np.abs(n1 - n0).max(1) > 1e-6
        DN = hs._read(js, binc, t["NORMAL"]).astype(np.float64)
        DN[ch] += (n1 - n0)[ch]
        hs._set(js, chunks, t["POSITION"], Df, minmax=True)
        hs._set(js, chunks, t["NORMAL"], DN)
        done.append("%s %d points, most %.2f mm (normals on %d)" % (f, int(moved.sum()), 1000 * np.abs(Df - D["face_" + f]).max(), int(ch.sum())))
    done += jaw(js, binc, chunks)
    hm.setdefault("extras", {})[MARK] = {"faces": done}
    hs._save(out or path, js, chunks)
    print("MOUTH_SEAL: her lips sealed at rest: %s; written %s" % ("; ".join(done) or "none", out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0] if a else GLB, a[1] if len(a) > 1 else None)
