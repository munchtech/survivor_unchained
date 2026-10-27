"""Her upper arms' LINE-LIKE GROOVES laid soft (Body 12, 26 Oct 2026; the owner on a day town close-up, front, arms
hanging: "weird vein looking things on each arm"; he likes them defined, not grooved. The precedent: Face 38's collar,
heroine_neck_relief.py SOFT, "the owner's 'vein things'").

What they were (measured in heroine_arm_tone's arm chart: s mm down from her shoulder joint's level, phi deg round the
upper arm's axis, 0 front, 90 out, -90 in toward her side):
  GEOMETRY (integration's body and round 13's alike, both arms): a lengthwise valley in her rest shape at phi ~-55
  (the front-inner arm, between the inner bulge at phi ~-85 and the biceps' front at phi ~-15), s ~40-170: 1.6-2.0 mm
  deep under the cross-section's convex hull, ~25 mm across, its stored normals swinging +-7-13 deg across it (the
  stored normals follow the geometry: 0 split normals on the arm). Round 13 adds a second, shallower one on the
  front-outer side (phi ~+40, s 80-120, ~1.1 mm). The paint is flat there (+-3 of 145 in luminance).
  TONE (round 13 only): heroine_arm_tone's bellies are plateaus with a smoothstep border band, so each border is a
  narrow ring of slope (steepest 17.7 deg at strength 1.75); the biceps' inner border runs lengthwise at phi ~-65,
  on top of the geometry's valley.

The step (after heroine_arm_tone, the last of the r13 chain): the tone is taken off, the geometry's valleys filled,
the tone laid again from its own record, softened.
  GEO: per side, her arm's radius R(s, phi) on a 2.5 mm x 2.5 deg grid (on-arm, outward-facing points, the tone's
  mask); per s row the deficit under the cross-section's convex hull; filled OUTWARD only (never thinned), LINES_GEO x
  the deficit, windowed to the front half (phi LINES_P, 15 deg fades: the pit and the back are not touched) and s
  LINES_S (20 mm fades: the shoulder top and the elbow crease are not touched), then blurred (LINES_GSS mm in s,
  LINES_GSP deg in phi) so the fill's own edge has no slope of its own. Points move radially, mirrored; normals take
  the surface's geometric change (heroine_arm_form's way); shape keys are deltas and keep their shapes.
  TONE: its height field smoothed in the arm chart (a Gaussian, LINES_TSS mm in s, LINES_TSP deg in phi, on the
  upper arm, s < 250), the forearm's left as it was; then baked as heroine_arm_tone bakes it, at its own strength.
  The broad forms keep their height (the biceps' plateau 3.2 mm, the deltoid's 4.7); their borders widen.

    LINES=1 python tools/assets/heroine_arm_lines.py <heroine.glb in> <heroine.glb out>
Gate LINES=1. Done-mark heroine_arm_lines. Needs the tone laid (heroine_arm_tone's mark); its TONE_DELT_W and
TONE_SPLIT come from the mark (or, for a body toned before the mark held them, the environment, as it was built).
Followers: rest points on her front upper arm move outward (up to ~2 mm): outfit points and armor_tuck records over
them are carried in the outfit chain, as heroine_arm_form's.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MARK = "heroine_arm_lines"
GATE = "LINES"
_E = os.environ.get
GEO = float(_E("LINES_GEO", "1.3"))                                   # share of the hull deficit filled
GEO_P = tuple(float(v) for v in _E("LINES_P", "-110,80").split(","))  # phi window (deg), 15 deg fades inside it
GEO_S = tuple(float(v) for v in _E("LINES_S", "0,215").split(","))    # s window (mm), 20 mm fades inside it
GSS, GSP = float(_E("LINES_GSS", "8")), float(_E("LINES_GSP", "6"))  # the fill's blur: mm in s, deg in phi
TSS, TSP = float(_E("LINES_TSS", "14")), float(_E("LINES_TSP", "14"))  # the tone's blur: mm in s, deg in phi
# (and, optionally, the filled radius faired: narrow crests lowered and flats rounded, a Gaussian of LP deg in phi
# (LPS mm in s), the change x LP_AMT, in the same window; 0 = off; veins b1: 10)
LP, LPS, LP_AMT = float(_E("LINES_LP", "10")), float(_E("LINES_LPS", "4")), float(_E("LINES_LP_AMT", "1"))
STEP = 2.5                                                              # grid: mm in s, deg in phi
SS = np.arange(-100, 281, STEP)
PP = np.arange(-180, 180, STEP)


def _tone():
    """heroine_arm_tone imported with its shape constants as the body was toned (they are read at import)."""
    return __import__("heroine_arm_tone")


def _ramp(x, a, b, w):
    return np.clip((x - a) / w, 0, 1) * np.clip((b - x) / w, 0, 1)


def hull_deficit(R):
    """per s row: the convex hull's radius minus R (mm, >= 0) round the full circle (phi = PP)."""
    th = np.radians(PP)
    c, s_ = np.cos(th), np.sin(th)
    out = np.zeros_like(R)
    n = R.shape[1]
    for i, r in enumerate(R):
        x, y = r * c, r * s_
        v = np.sort(ConvexHull(np.c_[x, y]).vertices)
        hv = np.r_[v, v[0] + n]
        hr = r.copy()
        for a, b in zip(hv[:-1], hv[1:]):
            if b - a < 2:
                continue
            A = np.array([x[a % n], y[a % n]])
            e = np.array([x[b % n], y[b % n]]) - A
            j = np.arange(a + 1, b) % n
            # ray t*(c, s) meets A + u*e: t = cross(A, e) / cross(d, e)
            hr[j] = (A[0] * e[1] - A[1] * e[0]) / (c[j] * e[1] - s_[j] * e[0])
        out[i] = np.maximum(hr - r, 0)
    return out


def radius_grid(T, b, fr):
    """her arm's mean radius per 2.5 mm x 2.5 deg cell (on-arm, outward-facing points), holes filled, phi periodic."""
    Q = b.U * fr["mir"] + fr["off"]
    O, ax, f, l = fr["up"]
    s, phi, r = T._chart(Q, O, ax, f, l)
    N = T._vn(b.U, b.F) * fr["mir"]
    q = (Q - O) - ((Q - O) @ ax)[:, None] * ax
    outward = (N * q).sum(1) / np.maximum(np.linalg.norm(q, axis=1), 1e-9)
    R0 = T.map_coordinates(fr["Rg"], [(np.clip(s, T.RG_S[0], T.RG_S[-1]) - T.RG_S[0]) / 5, (phi - T.RG_P[0]) / 5],
                           order=1, mode="nearest")
    m = (outward > 0.3) & (r - R0 < T.ON_ARM[0]) & (Q[:, 0] > 0.06) & (s > SS[0]) & (s < SS[-1])
    i = np.clip(np.round((s[m] - SS[0]) / STEP).astype(int), 0, len(SS) - 1)
    j = np.round((phi[m] - PP[0]) / STEP).astype(int) % len(PP)
    S = np.zeros((len(SS), len(PP)))
    C = np.zeros_like(S)
    np.add.at(S, (i, j), r[m])
    np.add.at(C, (i, j), 1)
    have = C > 0
    G = np.where(have, S / np.maximum(C, 1), 0)
    _, (ii, jj) = ndimage.distance_transform_edt(~have, return_indices=True)
    G = G[ii, jj]
    return ndimage.gaussian_filter(G, 1.0, mode=("nearest", "wrap")), (s, phi, r, R0, Q)


def geo_move(T, b, FR):
    dU = np.zeros_like(b.U)
    rep = {}
    S, P = np.meshgrid(SS, PP, indexing="ij")
    win = _ramp(S, GEO_S[0], GEO_S[1], 20.0) * _ramp(P, GEO_P[0], GEO_P[1], 15.0)
    for side, fr in FR.items():
        G, (s, phi, r, R0, Q) = radius_grid(T, b, fr)
        D = hull_deficit(G)
        F = ndimage.gaussian_filter(GEO * D * win, (GSS / STEP, GSP / STEP), mode=("nearest", "wrap"))
        if LP > 0:
            Gf = G + F
            F = F + LP_AMT * win * (ndimage.gaussian_filter(Gf, (LPS / STEP, LP / STEP), mode=("nearest", "wrap")) - Gf)
        at = [(np.clip(s, SS[0], SS[-1]) - SS[0]) / STEP, (phi - PP[0]) / STEP]
        on = T._step(T.ON_ARM[1], T.ON_ARM[0], r - R0) * (Q[:, 0] > 0.06)
        d = T.map_coordinates(F, at, order=1, mode="grid-wrap") * on
        O, ax, f, l = fr["up"]
        q = (Q - O) - ((Q - O) @ ax)[:, None] * ax
        q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-9)
        dU += (d[:, None] * q * 1e-3) * fr["mir"]
        k = np.unravel_index(np.argmax(D * win), D.shape)
        rep[side] = dict(deficit_mm=round(float((D * win).max()), 2), at=[float(SS[k[0]]), float(PP[k[1]])],
                         left_mm=round(float(hull_deficit(G + F)[k]), 2), fill_mm=round(float(F.max()), 2),
                         thin_mm=round(float(-F.min()), 2))
    return dU, rep


def soft_field(T, FR):
    """heroine_arm_tone.field with its upper-arm part smoothed in the arm chart (TSS mm x TSP deg)."""
    S, P = np.meshgrid(SS, PP, indexing="ij")
    D = {}
    for side, fr in FR.items():
        O, ax, f, l = fr["up"]
        Rg = T.map_coordinates(fr["Rg"], [(np.clip(S, T.RG_S[0], T.RG_S[-1]) - T.RG_S[0]) / 5, (P - T.RG_P[0]) / 5],
                               order=1, mode="nearest") / 1000
        th = np.radians(P)[..., None]
        Q = O + S[..., None] / 1000 * ax + Rg[..., None] * (np.cos(th) * f + np.sin(th) * l)
        H = T._side(Q.reshape(-1, 3), fr).reshape(S.shape)
        Hs = ndimage.gaussian_filter(H, (TSS / STEP, TSP / STEP), mode=("nearest", "wrap"))
        D[side] = (Hs - H) * np.clip((250 - S) / 20, 0, 1)
    orig = T.field

    def field(Pw, FR_=None):
        h = orig(Pw, FR)
        for side, fr in FR.items():
            Q = Pw * fr["mir"] + fr["off"]
            s, phi, r = T._chart(Q, *fr["up"])
            R0 = T.map_coordinates(fr["Rg"], [(np.clip(s, T.RG_S[0], T.RG_S[-1]) - T.RG_S[0]) / 5,
                                              (phi - T.RG_P[0]) / 5], order=1, mode="nearest")
            on = T._step(T.ON_ARM[1], T.ON_ARM[0], r - R0) * (Q[:, 0] > 0.06)
            h = h + on * T.map_coordinates(D[side], [(np.clip(s, SS[0], SS[-1]) - SS[0]) / STEP, (phi - PP[0]) / STEP],
                                           order=1, mode="grid-wrap")
        return h
    return field, {k: round(float(np.abs(v).max() * 1000), 2) for k, v in D.items()}


def _drop_unused(g):
    """the first tone's images (left in the file by heroine_arm_tone.remove) out of the texture and image lists, so the
    import doesn't load them (their bytes stay in the buffer)."""
    def refs(m):
        out = []
        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == "index" and isinstance(v, int):
                        out.append((x, v))
                    else:
                        walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(m)
        return out
    used = sorted({v for m in g["materials"] for _, v in refs(m)})
    tmap = {o: i for i, o in enumerate(used)}
    for m in g["materials"]:
        for d, v in refs(m):
            d["index"] = tmap[v]
    g["textures"] = [g["textures"][o] for o in used]
    iu = sorted({t["source"] for t in g["textures"]})
    imap = {o: i for i, o in enumerate(iu)}
    for t in g["textures"]:
        t["source"] = imap[t["source"]]
    g["images"] = [g["images"][o] for o in iu]


def run(src, dst):
    from heroine_neck import _Gl
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    g0 = _Gl(dst).g
    ex0 = (g0.get("asset", {}).get("extras") or {})
    if ex0.get(MARK):
        print("LINES: %s has had it" % dst)
        return
    rec = ex0.get("heroine_arm_tone")
    if not rec:
        sys.exit("LINES: no heroine_arm_tone on %s (this step follows it)" % dst)
    for k, env in (("delt_w", "TONE_DELT_W"), ("split", "TONE_SPLIT")):
        if k in rec:
            os.environ[env] = repr(rec[k])
        elif env not in os.environ:
            sys.exit("LINES: the tone's record has no %s: set %s as it was built" % (k, env))
    T = _tone()
    import pit_hollow_post as ph
    T.STRENGTH = float(rec["strength"])
    T.remove(dst)
    # GEO: the valleys filled (the rest skin the tone is then laid on)
    G = _Gl(dst)
    g = G.g
    b = ph.Body(G)
    FR = T.frames(b)
    dU, rep = geo_move(T, b, FR)
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
        N = G.get(ni).astype(float) + (n1 - n0)[w]
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, N.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    mv = np.linalg.norm(dU, axis=1) * 1000
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("LINES: geometry: %d points moved > 0.2 mm, max %.2f mm; %s" % ((mv > 0.2).sum(), mv.max(), rep))
    # TONE: laid again on the filled skin, its field smoothed
    b2 = ph.Body(_Gl(dst))
    FR2 = T.frames(b2)
    T.field, trep = soft_field(T, FR2)
    T.run(dst, dst)
    g2, binc = T._read(dst)
    g2["asset"]["extras"].pop("heroine_arm_tone_removed", None)
    _drop_unused(g2)
    g2["asset"]["extras"][MARK] = {"geo": GEO, "phi": GEO_P, "s": GEO_S, "geo_blur": [GSS, GSP], "fair": [LP, LPS, LP_AMT],
                                   "tone_blur": [TSS, TSP], "max_mm": round(float(mv.max()), 2), "geo_rep": rep,
                                   "tone_change_mm": trep}
    T._write(dst, g2, binc)
    print("LINES: tone softened (largest height change per side, mm: %s) -> %s" % (trep, dst))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if _E(GATE) != "1":
        print("LINES: gated off (set %s=1); nothing changed" % GATE)
        if len(a) == 2 and os.path.abspath(a[0]) != os.path.abspath(a[1]):
            shutil.copyfile(a[0], a[1])
        sys.exit(0)
    run(a[0], a[1])
