"""Her upper arm's LATERAL LUMP taken out of her rest shape (Body 10 round 13, 25 Oct 2026; the owner on round 11's
overhead swing, her hanging left arm: "is that lump a muscle ... I like them defined, it just seemed like that wasn't
where the bicep is", and he marked a bump in the arm's outer outline, mid upper arm).

What it was (measured on her rest skin in heroine_arm_tone's arm chart: s mm down from her shoulder joint's level,
phi deg round the upper arm's axis, 0 front, 90 out, 180 back): a ridge on the arm's outer-back side standing 5-8 mm
proud of the arm's taper at s 80-150, peak s ~110-115 (45% down), phi 90-135, bounded in front by a groove (phi 30-60)
and dropping 10-12 mm over the next 50 mm (heroine_arm_shape's inner-side draw left the outer side standing). Hanging,
her arm shows its front and outer side, so the ridge is the outer outline's bump at mid-arm and its lit flank runs down
toward the inner elbow: a muscle belly that reads diagonal and in the wrong place. It is no muscle: the deltoid tapers
to its insertion's V there (the tone map draws that V at s 112, phi 84), the biceps runs down the front, the triceps
fills the back.

The step: the arm's radius field R(s, phi) (the tone chart's grid: per cell the innermost outward-facing point the arm's
bones carry, 5 mm x 5 deg) is filled thin-plate (biharmonic, phi periodic) over the zone s FORM_S, phi FORM_P with the
grid outside it held, so the deltoid's taper runs on into the arm in one smooth convex line (C1 at the zone's edge);
each arm point (heroine_arm_tone's on-arm mask) moves radially by the fill's change there (x FORM_AMT). Left-canonical,
mirrored: her two arms match. Positions and normals (her stored normal + the surface's geometric change); shape keys are
deltas and keep their shapes, so at every sculpted key the pose moves by exactly this edit carried by the skin and
nothing else (her shoulder top, breasts, pit and fold untouched: the zone is on the arm's outer side, 0 elsewhere).

Round 13 b2, THE LOWERED-ARM ARCH (the owner on row 3, the lowered swing A~75: "is that arch too much?"; round 3:
"the indent arch from underarm to elbow ... should be a little more straight line"). Measured at the game camera on the
pose dumps of the whole swing (A 27-80, and A 90/100 turned up from it): the underside's outline from the elbow to the
pit corner stood 4.4-5.6 mm off a straight line at every A from 37 to 100 (a line fit over the outline's 5-80%), with
or without the level slot (the slot moved it 0.6 mm): the indent is the REST SHAPE's, not the sculpt, the weights or the
twist chain. On her arm's back (phi -165..-135, where the lowered arm's underside outline runs) the radius stays full
(~55 mm) to s 90, drops 13 mm over s 90-150, then runs flat to the elbow (~39 mm): a scoop where the triceps should
taper on into its tendon, and below it the flexed elbow's skin stands proud, so the line arches up from the pit's full
corner over the scoop and down to the elbow. BACK: the scoop filled outward (never in: the triceps keeps all of its
fullness), BACK_AMT mm at s BACK_S, phi BACK_P, a squared-biweight window in s and phi (half-widths BACK_SW, BACK_PW),
radially, mirrored: the back's line runs straight from the pit corner to the elbow (residual 5.3 -> 1.2 mm at A 75).
BACK_AMT=0 gives b1 (round 13's first build, the lateral fill alone).

    ARM_FORM=1 python tools/assets/heroine_arm_form.py <heroine.glb in> <heroine.glb out>
Run after shoulder_sculpt_post and BEFORE heroine_arm_tone (the tone reads the rest skin). Done-mark heroine_arm_form.
Followers: rest points on her upper arms move (up to ~7 mm in on the outer side, up to 7 mm out on the back): outfit/armor points over them and armor_tuck records
keyed by bind position must be carried/re-recorded in the outfit chain (heroine_arm_shape.py's FOLLOW pattern).
"""
import json
import os
import shutil
import sys

import numpy as np
import scipy.sparse as sps
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_arm_tone as tone  # noqa: E402

MARK = "heroine_arm_form"
GATE = "ARM_FORM"
_E = os.environ.get
FORM_S = tuple(float(v) for v in _E("FORM_S", "60,170").split(","))     # zone's s (mm)
FORM_P = tuple(float(v) for v in _E("FORM_P", "70,160").split(","))     # zone's phi (deg), from the first to the second
FORM_AMT = float(_E("FORM_AMT", "1.0"))
# (round 13 b2) the back's scoop filled: peak mm, s (mm), phi (deg), half-widths in s and phi
BACK_AMT = float(_E("BACK_AMT", "7.0"))
BACK_S, BACK_SW = float(_E("BACK_S", "155")), float(_E("BACK_SW", "65"))
BACK_P, BACK_PW = float(_E("BACK_P", "-150")), float(_E("BACK_PW", "60"))


def inpaint(G, free, ds=5.0, dp=5.0 * tone.R0 * np.pi / 180):
    """thin-plate (biharmonic) fill of grid G over the free cells, the rest held; phi (axis 1) periodic"""
    ns, npp = G.shape
    idx = np.arange(ns * npp).reshape(ns, npp)
    r, c, v = [], [], []
    k = 0
    for i in range(1, ns - 1):
        for j in range(npp):
            for (a, b, w) in ((i, j, -2 / ds ** 2 - 2 / dp ** 2), (i - 1, j, 1 / ds ** 2), (i + 1, j, 1 / ds ** 2),
                              (i, (j - 1) % npp, 1 / dp ** 2), (i, (j + 1) % npp, 1 / dp ** 2)):
                r.append(k)
                c.append(idx[a, b])
                v.append(w)
            k += 1
    L = sps.csr_matrix((v, (r, c)), shape=(k, ns * npp))
    f = free.ravel()
    g = G.ravel().copy()
    LF, LB = L[:, f], L[:, ~f]
    g[f] = spsolve((LF.T @ LF).tocsc(), -(LF.T @ (LB @ g[~f])))
    return g.reshape(ns, npp)


def zone():
    S, P = np.meshgrid(tone.RG_S, tone.RG_P, indexing="ij")
    return (S >= FORM_S[0]) & (S <= FORM_S[1]) & ((P - FORM_P[0]) % 360 <= (FORM_P[1] - FORM_P[0]) % 360)


def move(b, FR=None):
    """the rest move (n, 3) m, and per side the grid's change (mm)"""
    FR = FR or tone.frames(b)
    dU = np.zeros_like(b.U)
    grids = {}
    for side, fr in FR.items():
        G = fr["Rg"]
        dR = (inpaint(G, zone()) - G) * FORM_AMT
        grids[side] = dR
        Q = b.U * fr["mir"] + fr["off"]
        O, ax, f, l = fr["up"]
        s, phi, r = tone._chart(Q, O, ax, f, l)
        at = [(np.clip(s, tone.RG_S[0], tone.RG_S[-1]) - tone.RG_S[0]) / 5, (phi - tone.RG_P[0]) / 5]
        R = tone.map_coordinates(G, at, order=1, mode="nearest")
        on = tone._step(tone.ON_ARM[1], tone.ON_ARM[0], r - R) * (Q[:, 0] > 0.06)
        d = tone.map_coordinates(dR, at, order=1, mode="nearest") * on
        if BACK_AMT > 0:
            # (round 13 b2) the back's scoop filled outward (BACK): a squared biweight in s and phi
            ws = np.clip(1 - ((s - BACK_S) / BACK_SW) ** 2, 0, 1) ** 2
            wp = np.clip(1 - (((phi - BACK_P + 180) % 360 - 180) / BACK_PW) ** 2, 0, 1) ** 2
            d = d + BACK_AMT * ws * wp * on
        q = (Q - O) - ((Q - O) @ ax)[:, None] * ax
        q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-9)
        dU += (d[:, None] * q * 1e-3) * fr["mir"]
    return dU, grids


def run(src, dst):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    ex = G.g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("ARM_FORM: %s has had it" % dst)
        return
    if ex.get(tone.MARK):
        sys.exit("ARM_FORM: run before heroine_arm_tone (the tone reads the rest skin)")
    b = ph.Body(G)
    dU, grids = move(b)
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        N = G.get(ni).astype(float) + (n1 - n0)[w]
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, N.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"s": FORM_S, "phi": FORM_P, "amt": FORM_AMT, "back": [BACK_AMT, BACK_S, BACK_SW, BACK_P, BACK_PW],
                "max_mm": round(float(mv.max()), 2)}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    import struct
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("ARM_FORM: %d points moved > 0.5 mm, max %.1f mm (grid change l %.1f..%.1f mm) -> %s"
          % ((mv > 0.5).sum(), mv.max(), grids["l"].min(), grids["l"].max(), dst))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if _E(GATE) != "1":
        print("ARM_FORM: gated off (set %s=1); nothing changed" % GATE)
        if len(a) == 2 and os.path.abspath(a[0]) != os.path.abspath(a[1]):
            shutil.copyfile(a[0], a[1])
        sys.exit(0)
    run(a[0], a[1])
