"""Her mouth's inside seated for an open mouth and a smile, in her exported glb (heroine.glb).

The smile pass (the owner, 13 October 2026: "queue the smile pass after the face ships"). With her mouth open
(mouth_open .6, with or without smile .8) no upper teeth showed: a front ray down her mouth's middle met her upper
lip, then 7-10 mm of TONGUE (the "salmon slab" under her upper lip), then her lower teeth. The causes, all in the
MakeHuman parts as fitted to her sculpt:
- her teeth sat high: the upper incisors' edges 1-3 mm ABOVE the front edge of her upper lip (which mouth_open leaves
  where it is), so it hid them in every pose; a relaxed open mouth shows 2-4 mm of them, a smile most of the crown.
  Her faces' keys move her lips by different amounts, so the seat is each face's own (SEAT_MM);
- mouth_open moved her upper teeth too (by her upper lip's drag, 1.3 mm down): they are her skull's;
- her tongue barely followed her jaw (3 mm while her lower teeth dropped 10), so it stood up behind her upper lip;
- her smile raised her mouth's corners and not her upper lip's middle (0.1 mm), so a smile with her mouth open showed
  no more teeth than her mouth open alone.
So: her teeth and tongue seated lower (her own face's SEAT_MM in their rest shape, each other face's difference in its
face key: her closed lips cover them as before); mouth_open moves only her lower teeth and, by the lower teeth nearest
each of its points, her tongue; and a new key on her head, smile_open (her upper lip's middle raised RAISE_MM,
rolled back a little), which People.HerFace sets as smile times how far her mouth is open (her lips closed, a smile
stays closed-lipped).

    python tools/assets/heroine_mouth.py [GLB [OUT]]

On one already done (her teeth mesh's extras say mouth_seat) it does nothing. heroine_outfits.py runs it on the body
it exports, after the teeth's shade. Numpy only (it runs in Blender's Python).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_teethshade as hts  # noqa: E402

GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb")
# (mm lower, per face: each face's upper incisors 2.5 mm under her upper lip's front edge at mouth_open .6, measured by
# front rays down her mouth's middle with the teeth 4.5 mm lower: own 3.0, doe 0.8, fey 2.0, hardwon 0.4, highborn 1.2,
# moonlit 2.2, saffron 0.4, sunborn 1.2, vixen 1.6, wildling 1.8 mm shown)
SHOWN_AT_45 = {"own": 3.0, "doe": 0.8, "fey": 2.0, "hardwon": 0.4, "highborn": 1.2, "moonlit": 2.2, "saffron": 0.4,
               "sunborn": 1.2, "vixen": 1.6, "wildling": 1.8}
SHOW_MM = float(os.environ.get("MOUTH_SHOW_MM", "2.5"))
SEAT_MM = {f: 4.5 + SHOW_MM - s for f, s in SHOWN_AT_45.items()}
ROOT_Z = 0.02                  # (m: her tongue behind this depth moves as her jaw does here)
RAISE_MM = float(os.environ.get("MOUTH_RAISE_MM", "3.5"))   # (smile_open at 1: her upper lip's middle raised so far)
ROLL = 0.25                    # (and rolled back by this share of it)
UP_X, UP_X2 = 0.012, 0.020     # (m from her mouth's middle: raised fully to here, easing out to there, where her smile
#                                already lifts her mouth's corners 5-9 mm)
UP_Y1, UP_Y2 = 0.008, 0.016    # (m above her lips' line: raised fully to here, easing out to there, under her nose)
LINE_NEAR = 1.692              # (her lips' line is looked for within 2 cm of this height, m)
CAV_AXIS_Z, CAV_FRONT, CAV_SIDE, CAV_DEPTH = 0.04, 0.088, 0.6, 0.025   # (m: her mouth's axis; its opening's z at her
#                                middle, falling back CAV_SIDE per metre out; dark at CAV_DEPTH behind it)
CORNER_X, CORNER_DEPTH = (0.017, 0.023), float(os.environ.get("MOUTH_CORNER_DEPTH", "0.35"))
CREASE_X = tuple(float(v) for v in os.environ.get("MOUTH_CREASE_X", "0.015,0.018,0.023,0.026").split(","))  # (m: in, out)
CREASE_Y = tuple(float(v) for v in os.environ.get("MOUTH_CREASE_Y", "0.002,0.004").split(","))  # (m off her lips' line)
TONGUE_ROOT, TONGUE_LEN =0.12, 0.035   # (her tongue's shade at its root, so far back from its tip: at 0.3 over 50 mm its
#                                      back, unshadowed, read as a lit pink slab behind her teeth (a2))
# (at mouth_open 1, her tongue dropped and drawn back so far beyond her lower teeth's move, fully at its tip,
# at its root: following her teeth alone it filled 14 mm of her mouth's opening at .6 (a2), a slab over her lower
# teeth with no dark between it and her upper teeth; 0.6 of it at its root)
# (at mouth_open 1, her tongue's back lowered so far in its middle beyond her jaw's move (none at its sides, none at
# its tip, all of it DEPRESS_LEN behind its tip): riding her jaw alone its back stood over her upper teeth's edges)
DEPRESS_MM = float(os.environ.get("MOUTH_DEPRESS_MM", "12"))
DEPRESS_LEN = 0.03
GROOVE_X = (0.005, 0.014)      # (m off her mouth's middle: lowered fully to here, none from there out)
# (her tongue's sides against her lower side teeth (solver int2): from the Look her far side's lower premolars and
# molars, seen end-on along the line of sight, stood as a grey column through her open mouth beside the tongue's hard
# edge; of its pixels 15% were their inner (lingual) faces and 11% the gum under them, seen through a 2-3 mm gap
# between her tongue's side and the teeth, its side 1-2 mm under their inner cusps at the premolars. In a mouth the
# tongue's side lies against the teeth's inner faces and on their inner cusps. So its side is pushed out to the teeth
# (HUG_IN m into them) and up to their inner cusps' tips (HUG_UP m over them) from the first premolar back, in its
# rest shape, so it rides her jaw so at any opening; from u (its point's share of its half width) HUG_U)
HUG_IN = float(os.environ.get("MOUTH_HUG_IN_MM", "2.5")) / 1000
HUG_UP = float(os.environ.get("MOUTH_HUG_UP_MM", "3.0")) / 1000
HUG_U = (0.45, 0.95)
# (her teeth's gaps: rounded blocks 0.26-0.57 mm apart, read with open dark wedges between them along the arch (6-8%
# too wide, the face lead): each tooth widened so much along the arch about its own middle)
WIDEN = float(os.environ.get("MOUTH_WIDEN", "1.07"))
# (her tongue (solver int3): 253 points, its raised side a straight-edged light band beside her far lower row and its
# front edge a straight diagonal in her open mouth: it is subdivided once (Loop, about 950 points) before its sides
# are raised, and its normals smoothed after. Its paint is darkened where it touches her lower teeth, to TOUCH at
# them, none TOUCH_MM off; and on its whole raised side to EDGE, so that never reads lighter than its top (heroine_
# tongue.gdshader: its vertex colour's green))
TOUCH, TOUCH_MM, EDGE = 0.6, 3.0, 0.8
# (her inner cheeks beside her lower back teeth (solver int3): from the Look a saturated red-pink lit wall right of her
# far lower row (Sunborn, Saffron, Hardwon). Her head's vertex colour's green there (1 elsewhere) falls to 0 out past
# WALL_X (m off her middle, in, full) and WALL_DZ (m behind her lower canines' middles: none, full); the skin shader
# darkens and greys her mouth's colour by it (heroine_skin.gdshader's wall_*))
WALL_X, WALL_DZ = (0.017, 0.021), (-0.006, 0.006)


def _prim(js, mat):
    mats = [m.get("name") for m in js.get("materials", [])]
    hit = [(m, p) for m in js["meshes"] for p in m["primitives"] if "material" in p and mats[p["material"]] == mat]
    if len(hit) != 1:
        raise SystemExit("MOUTH: found %d %s primitives" % (len(hit), mat))
    return hit[0]


def _s01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lips_line(V, D):
    """Her lips' line (y, m) at her mouth's middle: where mouth_open's move jumps (her lower lip goes with her jaw)."""
    n = np.linalg.norm(D, axis=1)
    ys = []
    for x0 in np.arange(0, 0.0141, 0.002):
        s = (np.abs(np.abs(V[:, 0]) - x0) < 0.001) & (np.abs(V[:, 1] - LINE_NEAR) < 0.02) & (V[:, 2] > 0.05)
        i = np.where(s)[0][np.argsort(-V[s, 1])]
        k = np.argmax(np.abs(np.diff(n[i])))
        ys.append(0.5 * (V[i[k], 1] + V[i[k + 1], 1]))
    return float(np.median(ys))


def smile_open(V, D):
    """smile_open's move: her upper lip (above her lips' line, and moved little by mouth_open, as her lower lip's points
    go 20-40 mm with her jaw) raised RAISE_MM in her mouth's middle and rolled back ROLL of that."""
    line = lips_line(V, D)
    n = np.linalg.norm(D, axis=1)
    w = (_s01((V[:, 1] - line + 0.004) / 0.001) * (1 - _s01((V[:, 1] - line - UP_Y1) / (UP_Y2 - UP_Y1)))
         * (1 - _s01((np.abs(V[:, 0]) - UP_X) / (UP_X2 - UP_X))) * (1 - _s01((n - 0.008) / 0.006)))
    out = np.zeros_like(V)
    out[:, 1] = RAISE_MM / 1000 * w
    out[:, 2] = -ROLL * RAISE_MM / 1000 * w
    return out, line, int((w > 0.5).sum())


def _smooth(z, v, zq, win):
    """v(z) sampled at points (z, v), as a moving max over win (m) then evened by a window as wide, at zq (m)."""
    raw = np.array([v[np.abs(z - q) < win].max() if (np.abs(z - q) < win).any() else np.nan for q in zq])
    ok = np.isfinite(raw)
    raw = np.interp(zq, zq[ok], raw[ok])
    k = max(1, int(round(win / max(zq[1] - zq[0], 1e-6))))
    pad = np.r_[np.full(k, raw[0]), raw, np.full(k, raw[-1])]
    return np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]


def widen(TV, body, gum, mid, lower):
    """Each tooth (not her gums) widened WIDEN times along the arch about its own middle: the move (m) per point. The
    arch's way at a tooth: from the tooth before it to the one after (each row in order round her mouth)."""
    out = np.zeros_like(TV)
    c0 = np.array([mid, 0.0, 0.04])
    for row in (False, True):
        bs = [b for b in np.unique(body) if b != gum and (lower[body == b].mean() > 0.5) == row]
        cen = {b: TV[body == b].mean(0) for b in bs}
        bs.sort(key=lambda b: np.arctan2(cen[b][0] - c0[0], cen[b][2] - c0[2]))
        for i, b in enumerate(bs):
            t = cen[bs[min(i + 1, len(bs) - 1)]] - cen[bs[max(i - 1, 0)]]
            t[1] = 0
            t /= np.linalg.norm(t)
            s = body == b
            out[s] = ((TV[s] - cen[b]) @ t)[:, None] * t * (WIDEN - 1)
    return out


def tongue_hug(GV, TV, low_teeth, mid):
    """Her tongue's side pushed out to her lower side teeth's inner faces and up to their inner cusps (HUG_IN, HUG_UP),
    from her first premolars back, in its rest shape: the move (m) per point of her tongue."""
    out = np.zeros_like(GV)
    zq = np.arange(GV[:, 2].min(), GV[:, 2].max() + 1e-4, 0.0005)
    gx = np.abs(GV[:, 0] - mid)
    hw = _smooth(GV[:, 2], gx, zq, 0.003)
    zt = TV[low_teeth, 2]
    # (from the first premolar: her lower canines' back edge, the third tooth out from her middle, to her last molars')
    tz = TV[low_teeth]
    z_canine = np.percentile(tz[np.abs(tz[:, 0] - mid) > 0.012, 2], 92)
    z_back = zt.min()
    fade = _s01((z_canine - GV[:, 2]) / 0.006) * _s01((GV[:, 2] - (z_back - 0.006)) / 0.006)
    for sg in (-1, 1):
        side = (np.sign(GV[:, 0] - mid) == sg)
        ts = low_teeth & (np.sign(TV[:, 0] - mid) == sg) & (np.abs(TV[:, 0] - mid) > 0.008)
        ax = np.abs(TV[ts, 0] - mid)
        ling = -_smooth(TV[ts, 2], -ax, zq, 0.003)          # (its inner face's distance from her middle, per z)
        near_in = ax < np.interp(TV[ts, 2], zq, ling) + 0.0025
        cusp = _smooth(TV[ts, 2][near_in], TV[ts, 1][near_in], zq, 0.003)
        u = gx / np.interp(GV[:, 2], zq, hw)
        wu = _s01((u - HUG_U[0]) / (HUG_U[1] - HUG_U[0]))
        push = np.maximum(0, np.interp(GV[:, 2], zq, ling) + HUG_IN - np.interp(GV[:, 2], zq, hw))
        # (her tongue's side's top, per z: the highest of its points out past 0.8 of its half width)
        rim = side & (u > 0.8)
        top = _smooth(GV[rim, 2], GV[rim, 1], zq, 0.003)
        lift = np.maximum(0, np.interp(GV[:, 2], zq, cusp) + HUG_UP - np.interp(GV[:, 2], zq, top))
        # (its top lifted fully, its underside a third: by its point's height in its own cross-section)
        lo = -_smooth(GV[side, 2], -GV[side, 1], zq, 0.003)
        hh = (GV[:, 1] - np.interp(GV[:, 2], zq, lo)) / np.maximum(np.interp(GV[:, 2], zq, top) - np.interp(GV[:, 2], zq, lo), 1e-4)
        wv = 0.33 + 0.67 * _s01((hh - 0.2) / 0.6)
        out[side, 0] += (sg * push * wu * fade)[side]
        out[side, 1] += (lift * wu * wv * fade)[side]
    return out


def _normals(V, F, old):
    """Smooth normals (area-weighted, points welded by position), turned to agree with the old ones."""
    _, w = np.unique(np.round(V * 1e6).astype(np.int64), axis=0, return_inverse=True)
    w = w.ravel()
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    acc = np.zeros((w.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, w[F[:, k]], fn)
    N = acc[w]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    if (N * old).sum(1).mean() < 0:
        N = -N
    return N


def _loop(V, F):
    """One Loop subdivision of the mesh (V, F) by its index topology (points split at a seam take the boundary rule,
    alike on both sides, so it stays closed): (S, L, F2), S the smoothing operator (new points x old) for positions and
    shape keys, L the plain one (each edge's middle) for UVs and weights, F2 the new triangles (each in four, same turn)."""
    n = len(V)
    E = np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], axis=1)
    opp = np.r_[F[:, 2], F[:, 0], F[:, 1]]
    ue, inv = np.unique(E, axis=0, return_inverse=True)
    inv = inv.ravel()
    ne = len(ue)
    cnt = np.bincount(inv, minlength=ne)
    S = np.zeros((n + ne, n))
    L = np.zeros((n + ne, n))
    L[np.arange(n), np.arange(n)] = 1
    L[n + np.arange(ne), ue[:, 0]] = 0.5
    L[n + np.arange(ne), ue[:, 1]] = 0.5
    inner = cnt == 2
    S[n + np.arange(ne), ue[:, 0]] = np.where(inner, 3 / 8, 0.5)
    S[n + np.arange(ne), ue[:, 1]] = np.where(inner, 3 / 8, 0.5)
    for k in range(len(inv)):
        if inner[inv[k]]:
            S[n + inv[k], opp[k]] += 1 / 8
    bd = ue[~inner]
    for v in range(n):
        nb = np.unique(ue[(ue == v).any(1)])
        nb = nb[nb != v]
        bn = np.unique(bd[(bd == v).any(1)])
        bn = bn[bn != v]
        if len(bn):
            if len(bn) == 2:
                S[v, v] = 0.75
                S[v, bn] = 0.125
            else:
                S[v, v] = 1.0
        elif len(nb):
            b = 3 / 16 if len(nb) == 3 else 3 / (8 * len(nb))
            S[v, v] = 1 - len(nb) * b
            S[v, nb] = b
        else:
            S[v, v] = 1.0
    m = n + inv.reshape(3, -1).T          # (each triangle's edges: 01, 12, 20)
    a, b, c = F[:, 0], F[:, 1], F[:, 2]
    F2 = np.r_[np.c_[a, m[:, 0], m[:, 2]], np.c_[m[:, 0], b, m[:, 1]], np.c_[m[:, 2], m[:, 1], c], np.c_[m[:, 0], m[:, 1], m[:, 2]]]
    return S, L, F2


def _put(js, chunks, i, vals, ctype=5126, minmax=False):
    """Accessor i given these values whole (a new count allowed), in component type ctype."""
    a = js["accessors"][i]
    dt = {5126: "<f4", 5121: "u1", 5123: "<u2", 5125: "<u4"}[ctype]
    vals = np.ascontiguousarray(vals.astype(dt))
    for k in ("bufferView", "byteOffset", "sparse", "min", "max"):
        a.pop(k, None)
    a["componentType"], a["count"] = ctype, int(len(vals) if vals.ndim > 1 or a["type"] != "SCALAR" else vals.size)
    a["bufferView"] = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0})
    chunks[a["bufferView"]] = vals.tobytes()
    if minmax:
        a["min"], a["max"] = [float(v) for v in vals.min(0)], [float(v) for v in vals.max(0)]


def _near_dist(P, V, F, per=12):
    """Each point of P's distance (m) to the surface (V, F), by points spread over its triangles (per each)."""
    rng = np.random.default_rng(1)
    w = rng.dirichlet(np.ones(3), per)
    S = np.einsum("kj,fjd->fkd", w, V[F]).reshape(-1, 3)
    S = np.r_[S, V]
    out = np.empty(len(P))
    for i in range(0, len(P), 256):
        out[i:i + 256] = np.sqrt(((P[i:i + 256, None] - S[None]) ** 2).sum(2).min(1))
    return out


def _seen(V, I, pts, dirs=((0, 0, 1), (0.3, 0, 1), (-0.3, 0, 1), (0, 0.2, 1), (0, -0.2, 1))):
    """Those of the points pts (indices into V) a ray from in front reaches (any of dirs, toward her front, meets
    none of the triangles I): numpy only (Moller-Trumbore)."""
    A, B, C = V[I[:, 0]], V[I[:, 1]], V[I[:, 2]]
    e1, e2 = B - A, C - A
    seen = []
    for p in pts:
        o = V[p]
        far = (I != p).all(1)
        hit_all = True
        for d in dirs:
            d = np.array(d, float) / np.linalg.norm(d)
            h = np.cross(d, e2)
            a = (e1 * h).sum(1)
            ok = np.abs(a) > 1e-12
            f = np.where(ok, 1 / np.where(ok, a, 1), 0)
            s = o - A
            u = f * (s * h).sum(1)
            q = np.cross(s, e1)
            v = f * (q @ d)
            t = f * (e2 * q).sum(1)
            if not (ok & far & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 2e-4)).any():
                hit_all = False
                break
        if not hit_all:
            seen.append(p)
    return np.array(seen, dtype=np.int64)


def _add_target(js, chunks, mesh, prim, name, vals):
    js["accessors"].append({"componentType": 5126, "count": len(vals), "type": "VEC3"})
    i = len(js["accessors"]) - 1
    hs._set(js, chunks, i, vals, minmax=True)
    prim.setdefault("targets", []).append({"POSITION": i})
    mesh.setdefault("extras", {}).setdefault("targetNames", []).append(name)
    if "weights" in mesh:
        mesh["weights"].append(0.0)


def _add_colour(js, chunks, prim, rgba):
    js["accessors"].append({"componentType": 5126, "count": len(rgba), "type": "VEC4"})
    i = len(js["accessors"]) - 1
    a = js["accessors"][i]
    a["bufferView"] = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0})
    chunks[a["bufferView"]] = np.ascontiguousarray(rgba.astype("<f4")).tobytes()
    prim["attributes"]["COLOR_0"] = i


def seat(path, out=None):
    js, binc = hs._load(path)
    tm, tp = _prim(js, "teeth")
    gm, gp = _prim(js, "tongue")
    hm, hp = _prim(js, "skin_head")
    if "mouth_seat" in tm.get("extras", {}):
        print("MOUTH: already done in", path, "- nothing done")
        return
    if len(hm["primitives"]) != 1:
        raise SystemExit("MOUTH: her head's mesh has %d primitives (one expected)" % len(hm["primitives"]))
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    rd = lambda i: hs._read(js, binc, i).astype(np.float64)  # noqa: E731
    TV, GV, HV = rd(tp["attributes"]["POSITION"]), rd(gp["attributes"]["POSITION"]), rd(hp["attributes"]["POSITION"])
    tn, gn, hn = tm["extras"]["targetNames"], gm["extras"]["targetNames"], hm["extras"]["targetNames"]
    TD = rd(tp["targets"][tn.index("mouth_open")]["POSITION"])
    HD = rd(hp["targets"][hn.index("mouth_open")]["POSITION"])
    n = np.linalg.norm(TD, axis=1)
    # (her teeth widened along the arch, each about its middle, and its normals with them; her tongue's sides hugged
    # to her lower side teeth (HUG_*), in their rest shapes)
    TF = hs._read(js, binc, tp["indices"]).astype(np.int64).reshape(-1, 3)
    body = hts._bodies(TV, TF)
    gum = np.bincount(body).argmax()
    mid = 0.5 * (TV[:, 0].min() + TV[:, 0].max())
    wd = widen(TV, body, gum, mid, n > 0.002)
    TN = rd(tp["attributes"]["NORMAL"])
    for b in np.unique(body[np.linalg.norm(wd, axis=1) > 0]):
        s = body == b
        t = wd[s][np.argmax(np.linalg.norm(wd[s], axis=1))]
        t /= np.linalg.norm(t)
        TN[s] -= (1 - 1 / WIDEN) * (TN[s] @ t)[:, None] * t
    TN /= np.linalg.norm(TN, axis=1, keepdims=True)
    TV = TV + wd
    GF = hs._read(js, binc, gp["indices"]).astype(np.int64).reshape(-1, 3)
    for o in js["meshes"]:
        for q in o["primitives"]:
            if q is not gp:
                used = set(q["attributes"].values()) | {t["POSITION"] for t in q.get("targets", [])} | {q.get("indices")}
                assert not used & (set(gp["attributes"].values()) | {gp["indices"]}), "MOUTH: the tongue shares an accessor"
    nv0 = len(GV)
    S, Lm, GF = _loop(GV, GF)
    GN0 = Lm @ rd(gp["attributes"]["NORMAL"])
    GV = S @ GV
    gt = {nm: S @ rd(t["POSITION"]) for nm, t in zip(gn, gp["targets"])}
    UV = Lm @ rd(gp["attributes"]["TEXCOORD_0"])
    J0, W0 = rd(gp["attributes"]["JOINTS_0"]), rd(gp["attributes"]["WEIGHTS_0"])
    first = np.argmax(Lm > 0, axis=1)
    last = Lm.shape[1] - 1 - np.argmax(Lm[:, ::-1] > 0, axis=1)
    same = (J0[first] == J0[last]).all(1)
    GJ = J0[first]
    GW = np.where(same[:, None], Lm @ W0, W0[first])
    hug = tongue_hug(GV, TV, (n > 0.002) & (body != gum), mid)
    GV = GV + hug
    GN = _normals(GV, GF, GN0)
    lowt = (n > 0.002) & (body != gum)
    keep = lowt[TF].all(1)
    touch = TOUCH + (1 - TOUCH) * _s01(_near_dist(GV, TV, TF[keep]) / (TOUCH_MM / 1000))
    edge = 1 - (1 - EDGE) * _s01(hug[:, 1] / 0.001)
    # (her tongue rides her jaw: her lower teeth's and gum's mouth_open is an affine map of their (y, z), rms 0.1 mm
    # (MakeHuman's jaw morph), so each point of her tongue moves as her jaw does where it is (behind ROOT_Z, as at it).
    # Following the lower teeth nearest it (inverse distance over the 16 nearest, the front teeth weighing most) and
    # dropped 7 mm more, its sides sank 4-6 mm under her lower side teeth's tops at mouth_open .6, and from the Look
    # (17 degrees to her right, 6 below) her far side's lower back teeth stood over it as a wall, a black column with a
    # hard tongue edge beside it (judge j2). Its sides now rest at her lower teeth's cusps as with her mouth closed,
    # and its middle and back are lowered (DEPRESS_MM), so a dark band of her throat shows over it)
    jaw = n > 0.002
    fit = np.linalg.lstsq(np.c_[TV[jaw][:, 1:], np.ones(jaw.sum())], TD[jaw][:, 1:], rcond=None)[0]
    rms = np.sqrt((np.linalg.norm(np.c_[TV[jaw][:, 1:], np.ones(jaw.sum())] @ fit - TD[jaw][:, 1:], axis=1) ** 2).mean())
    GD_old = gt["mouth_open"]
    GD = np.c_[np.zeros(len(GV)), np.c_[GV[:, 1], np.maximum(GV[:, 2], ROOT_Z), np.ones(len(GV))] @ fit]
    mid = 0.5 * (TV[:, 0].min() + TV[:, 0].max())
    wx = 1 - _s01((np.abs(GV[:, 0] - mid) - GROOVE_X[0]) / (GROOVE_X[1] - GROOVE_X[0]))
    GD[:, 1] -= DEPRESS_MM / 1000 * wx * _s01((GV[:, 2].max() - GV[:, 2]) / DEPRESS_LEN)
    # (her upper teeth are her skull's: mouth_open no longer moves them. They move under 0.5% of the most, her lower
    # teeth and gum 10% and more (the back of her jaw, by its hinge). An easing from 30% to 50% held back her lower
    # back molars and gum, which stretched into a wall over her tongue's side, black in the shade (the smile pass, e2))
    TD2 = TD * _s01((n / n.max() - 0.01) / 0.04)[:, None]
    SO, line, raised = smile_open(HV, HD)
    # (each accessor written anew: a shared view would move other parts too)
    gt["mouth_open"] = GD
    hs._set(js, chunks, tp["targets"][tn.index("mouth_open")]["POSITION"], TD2, minmax=True)
    dy = np.array([0, -SEAT_MM["own"] / 1000, 0])
    hs._set(js, chunks, tp["attributes"]["POSITION"], TV + dy, minmax=True)
    hs._set(js, chunks, tp["attributes"]["NORMAL"], TN)
    for f, mm in SEAT_MM.items():
        if f == "own":
            continue
        extra = np.array([0, -(mm - SEAT_MM["own"]) / 1000, 0])
        if "face_" + f in tn:
            a = tp["targets"][tn.index("face_" + f)]["POSITION"]
            hs._set(js, chunks, a, rd(a) + extra, minmax=True)
        if "face_" + f in gt:
            gt["face_" + f] = gt["face_" + f] + extra
    # (her tongue written whole, subdivided: its points, normals, UVs, weights, shape keys and triangles)
    _put(js, chunks, gp["attributes"]["POSITION"], GV + dy, minmax=True)
    _put(js, chunks, gp["attributes"]["NORMAL"], GN)
    _put(js, chunks, gp["attributes"]["TEXCOORD_0"], UV)
    _put(js, chunks, gp["attributes"]["JOINTS_0"], GJ, js["accessors"][gp["attributes"]["JOINTS_0"]]["componentType"])
    _put(js, chunks, gp["attributes"]["WEIGHTS_0"], GW)
    for nm, t in zip(gn, gp["targets"]):
        _put(js, chunks, t["POSITION"], gt[nm], minmax=True)
    _put(js, chunks, gp["indices"], GF.ravel(), 5123 if GF.max() < 65535 else 5125)
    _add_target(js, chunks, hm, hp, "smile_open", SO)
    # (the inside of her mouth, for heroine_skin.gdshader's mouth_in: her head's vertex colour's alpha, 1 outside,
    # falling to 0 with depth behind her lips, on the points facing in toward her mouth's middle; and her tongue's
    # vertex colour, its own shade, lit at its tip and dark at its root)
    HN = rd(hp["attributes"]["NORMAL"])
    c0 = np.array([0.0, line, CAV_AXIS_Z])
    inside = (((c0 - HV) * HN).sum(1) > 0) & (np.abs(HV[:, 0]) < 0.035) & (np.abs(HV[:, 1] - line) < 0.025)
    front = CAV_FRONT - CAV_SIDE * np.abs(HV[:, 0])
    depth = np.where(inside, _s01((front - HV[:, 2]) / CAV_DEPTH), 0.0)
    # (her lips' inner faces at her mouth's corners stand as far forward as her lips there, so the plane left them
    # as paint, an orange-brown wedge lit at each corner of her smile (a4): there, at least CORNER_DEPTH, a wet dark red)
    cw = _s01((np.abs(HV[:, 0]) - CORNER_X[0]) / (CORNER_X[1] - CORNER_X[0]))
    depth = np.where(inside, np.maximum(depth, CORNER_DEPTH * cw), depth)
    # (her mouth's inside pokes out through her cheek under her jaw's side (|x| 31-34 mm, 21 mm under her lips): the
    # skin shader draws the inside's back faces, so it showed as a dark red speck there, on every face (g1). Seen from
    # in front with her lips closed nothing of the inside shows, so any of it a ray from in front reaches is outside:
    # none of the mouth's shade there, nor near it)
    HI = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    # (away from her lips' line, where her closed lips leave a hairline gap a ray can pass)
    poke = _seen(HV, HI, np.where((depth > 0) & (np.abs(HV[:, 1] - line) > 0.008))[0])
    if len(poke):
        near = np.linalg.norm(HV[:, None] - HV[poke][None], axis=2).min(1) < 0.004
        depth = np.where(near, 0.0, depth)
    print("MOUTH: %d points of her mouth's inside seen from in front (poking out), cleared with %d near them"
          % (len(poke), int(near.sum()) if len(poke) else 0))
    # (her mouth's corners, the crease where her lips meet: in her smile it folds in, sideways and back, and the lamps
    # behind her lit it, an orange-brown wedge through her skin's light (the smile pass, e3: by the lamps behind her,
    # not her paint and not the mouth's red). Shadows at this scale don't reach it; red: 1, or down to 0 there, the
    # lamps' share the skin shader lets reach it (corner_shade))
    cx = np.abs(HV[:, 0])
    crease = (_s01((cx - CREASE_X[0]) / (CREASE_X[1] - CREASE_X[0])) * (1 - _s01((cx - CREASE_X[2]) / (CREASE_X[3] - CREASE_X[2])))
              * (1 - _s01((np.abs(HV[:, 1] - line) - CREASE_Y[0]) / (CREASE_Y[1] - CREASE_Y[0]))))
    can = []
    for sg in (-1, 1):
        row = sorted((b for b in np.unique(body) if b != gum and n[body == b].mean() > 0.002 and np.sign(TV[body == b, 0].mean() - mid) == sg),
                     key=lambda b: abs(TV[body == b, 0].mean() - mid))
        can.append(TV[body == row[2], 2].mean())
    zc = float(np.mean(can))
    wall = np.where(depth > 0, _s01((np.abs(HV[:, 0] - mid) - WALL_X[0]) / (WALL_X[1] - WALL_X[0]))
                    * _s01((zc - HV[:, 2] - WALL_DZ[0]) / (WALL_DZ[1] - WALL_DZ[0])), 0.0)
    _add_colour(js, chunks, hp, np.c_[1 - crease, 1 - wall, np.ones(len(HV)), 1 - depth])
    gs = 1 - (1 - TONGUE_ROOT) * _s01((GV[:, 2].max() - GV[:, 2]) / TONGUE_LEN)
    _add_colour(js, chunks, gp, np.c_[gs, touch * edge, gs, np.ones(len(GV))])
    tm.setdefault("extras", {})["mouth_seat"] = {"seat_mm": SEAT_MM, "tongue_jaw_rms_mm": round(1000 * rms, 2), "depress_mm": DEPRESS_MM, "raise_mm": RAISE_MM,
                                                 "line": round(line, 5)}
    hs._save(out or path, js, chunks)
    print("MOUTH: her inner cheeks behind her lower canines (z %.1f mm) greyed on %d points" % (1000 * zc, int((wall > 0.01).sum())))
    print("MOUTH: her tongue subdivided, %d points to %d; darkened at her lower teeth on %d, on its raised side %d" % (
        nv0, len(GV), int((touch < 0.99).sum()), int((edge < 0.99).sum())))
    print("MOUTH: teeth and tongue seated %s mm lower (own %.1f); mouth_open no longer moves her upper teeth; the tongue "
          "rides her jaw (affine fit to %d points, rms %.2f mm; its mouth_open was %.1f mm at most, now %.1f); smile_open raises %d points of "
          "her upper lip %.1f mm (lips' line y %.4f); written %s" % (
              ", ".join("%s %.1f" % kv for kv in SEAT_MM.items() if kv[0] != "own"), SEAT_MM["own"], jaw.sum(), 1000 * rms,
              1000 * np.linalg.norm(GD_old, axis=1).max(), 1000 * np.linalg.norm(GD, axis=1).max(), raised, RAISE_MM,
              line, out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    seat(a[0] if a else GLB, a[1] if len(a) > 1 else None)
