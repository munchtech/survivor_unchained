"""Her mouth's inside kept behind her skin, each face its own, in her exported glb (heroine.glb).

The mouth cleanup (judge a05fb157, 14 October 2026). With Fey's face key and her mouth open (.6, and her laugh: open .6
and smile .8) a dark-red drop showed on her chin just under her lower lip's middle: the inside of her lower lip (its
sulcus, 4-10 mm under her lips' line and 15-20 mm behind their front) came 0.7-0.8 mm out in front of her chin's skin,
where her face key thins the lip and mouth_open swings it forward. Doe's did the same at mouth_open 1.

So, per face key: each point of her mouth's inside (the head's vertex colour alpha under ALPHA, heroine_mouth.seat's
mouth_in) near her mouth's middle (|x| < X_MAX) and off her lips' contact (more than CONTACT_MM from their line) that
any of the POSES, seen from any of the VIEWS, puts less than MARGIN_MM behind her outer skin is pushed back (-z) in
that face's key by what it lacks, spread to the inside points round it (falling to none at SPREAD_MM) and the same on
every copy of a point (her UV seams), so the inside stays smooth. Her outer skin, her own face and every other key are
untouched; at rest the pushed points sit deeper in her mouth, where nothing sees them.

    python tools/assets/heroine_mouth_inner.py [GLB [OUT]]

On one already done (her head's extras say mouth_inner) it does nothing. Numpy only. In her build it runs after
heroine_face_bow.run_keys (her mouth's last step): it moves only inside points, which no earlier step's normals use.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_mouth as hmo  # noqa: E402
import heroine_teethshade as hts  # noqa: E402

GLB = hmo.GLB
LOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "data", "content", "looks.json")
MARK = "mouth_inner"
ALPHA = 0.9                       # (a point whose mouth_in alpha is under this is her mouth's inside)
X_MAX = 0.015                     # (m off her mouth's middle; her corners are left as judged)
CONTACT_MM = 2.0                  # (her lips' contact, left as it is)
MARGIN_MM = float(os.environ.get("MOUTH_INNER_MARGIN_MM", "0.8"))
SPREAD_MM = 3.0
# (her upper gum (judge a05fb157, Hard-won's laugh): its papillae between her front teeth hang 5.4-6.8 mm over her central
# incisors' edges, where her laugh's upper lip stops (5-6.5 mm of tooth shows), so gum showed in spots under it: a lit
# pink fleck over one incisor and a dark sliver along others. Her front gum's lowest points (within GUM_FRONT_MM of her
# front teeth's faces, |x| < GUM_X) are raised to GUM_H_MM over those edges (the band up to GUM_EASE_MM above
# that squeezed into it, so the margin's scallop is kept), so her laugh's lip sits on tooth. Her own seat, so every face alike)
GUM_H_MM = float(os.environ.get("MOUTH_GUM_H_MM", "7.2"))
GUM_EASE_MM = 2.0
GUM_FRONT_MM = 6.0
GUM_X = 0.016
FAR_MM = 5.0                      # (skin further than this behind a point is another part of her (her throat), not its cover)
VIEWS = ((-17, -6), (0, -6), (17, -6), (0, 0), (-30, -6), (30, -6))   # (yaw, pitch in degrees: the Look is (-17, -6))
POSES = ({"mouth_open": 0.3}, {"mouth_open": 0.6}, {"mouth_open": 1.0}, {"mouth_open": 0.6, "smile": 0.8},
         {"mouth_open": 1.0, "smile": 1.0}, {"mouth_open": 0.3, "smile": 0.8}, {"mouth_open": 0.6, "frown": 0.8},
         {"mouth_open": 0.6, "snarl": 0.8}, {})


def _lips():
    """Each face's own lower-lip fullness (looks.json's lips: People.HerFaceKey sets lips_lower+ to it)."""
    try:
        out, todo = {}, [json.load(open(LOOKS, encoding="utf-8"))]
        while todo:
            d = todo.pop()
            if isinstance(d, dict):
                if "lips" in d and "id" in d and "lid" in d:
                    out[d["id"]] = float(d["lips"])
                todo += list(d.values())
            elif isinstance(d, list):
                todo += d
        return out
    except (OSError, ValueError):
        return {}


def _rot(yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    ry = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return rx @ ry


def _cover(Q, T, pts):
    """For each point (view coords, looking down -z), the nearest-to-camera z of the triangles T over it (-inf: none)."""
    tri = Q[T]
    lo, hi = tri[:, :, :2].min(1), tri[:, :, :2].max(1)
    out = np.full(len(pts), -np.inf)
    for k, p in enumerate(pts):
        s = np.where((lo[:, 0] <= p[0]) & (hi[:, 0] >= p[0]) & (lo[:, 1] <= p[1]) & (hi[:, 1] >= p[1]))[0]
        if not len(s):
            continue
        a, b, c = tri[s, 0], tri[s, 1], tri[s, 2]
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        ok = np.abs(d) > 1e-16
        d = np.where(ok, d, 1)
        l1 = ((b[:, 1] - c[:, 1]) * (p[0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (p[1] - c[:, 1])) / d
        l2 = ((c[:, 1] - a[:, 1]) * (p[0] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (p[1] - c[:, 1])) / d
        l3 = 1 - l1 - l2
        h = ok & (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if h.any():
            out[k] = (l1 * a[:, 2] + l2 * b[:, 2] + l3 * c[:, 2])[h].max()
    return out


def need(V, T, D, alpha, face, lips, cand, outer):
    """How far (m, world -z) each candidate point must go back so every pose and view leaves it MARGIN_MM behind her skin."""
    Pf = V + (D["face_" + face] if face != "own" else 0) + lips * D.get("lips_lower+", 0)
    w = np.zeros(len(cand))
    for kv in POSES:
        kv = dict(kv)
        mo, sm = kv.get("mouth_open", 0), kv.get("smile", 0)
        if sm and mo:
            o = min(mo / 0.3, 1)
            kv["smile_open"], kv["smile_hold"] = sm * o * o * (3 - 2 * o), sm * mo
        P = Pf + sum(v * D[k] for k, v in kv.items() if k in D)
        for yaw, pitch in VIEWS:
            R = _rot(yaw, pitch)
            Q = P @ R.T
            fz = np.cross(Q[outer[:, 1]] - Q[outer[:, 0]], Q[outer[:, 2]] - Q[outer[:, 0]])[:, 2]
            z = _cover(Q, outer[fz > 0], Q[cand])
            m = z - Q[cand, 2]
            lack = np.where((z > -np.inf) & (m > -FAR_MM / 1000) & (m < MARGIN_MM / 1000), MARGIN_MM / 1000 - m, 0)
            w = np.maximum(w, lack / max(R[2, 2], 0.5))
    return w


def gum_lift(js, binc, chunks):
    """Her upper front gum's lowest points raised (GUM_*), in her teeth's rest shape: (points moved, most mm)."""
    tm, tp = hmo._prim(js, "teeth")
    tn = tm["extras"]["targetNames"]
    TV = hs._read(js, binc, tp["attributes"]["POSITION"]).astype(np.float64)
    TF = hs._read(js, binc, tp["indices"]).astype(np.int64).reshape(-1, 3)
    n = np.linalg.norm(hs._read(js, binc, tp["targets"][tn.index("mouth_open")]["POSITION"]), axis=1)
    body = hts._bodies(TV, TF)
    gum = np.bincount(body).argmax()
    up = n < 0.002
    mid = 0.5 * (TV[:, 0].min() + TV[:, 0].max())
    ids = [b for b in np.unique(body) if b != gum and up[body == b].all()]
    ct = sorted(ids, key=lambda b: abs(TV[body == b, 0].mean() - mid))[:2]
    edge = min(TV[body == b, 1].min() for b in ct)
    zfront = max(TV[body == b, 2].max() for b in ct)
    h = TV[:, 1] - edge
    w = ((body == gum) & up & (np.abs(TV[:, 0] - mid) < GUM_X)) * (1 - hmo._s01((zfront - TV[:, 2]) / (GUM_FRONT_MM / 1000)))
    want, top = GUM_H_MM / 1000, (GUM_H_MM + GUM_EASE_MM) / 1000
    lo = h[w > 0].min() if (w > 0).any() else want
    # (the band from her gum's lowest point to GUM_H_MM + GUM_EASE_MM is squeezed into GUM_EASE_MM over GUM_H_MM: the
    # scallop of its margin kept, in order, the points over the band unmoved)
    sq = want + (h - lo) / max(top - lo, 1e-6) * (top - want)
    lift = w * np.where((h < top) & (lo < want), np.maximum(sq - h, 0), 0)
    if not (lift > 0).any():
        return 0, 0.0
    TV2 = TV.copy()
    TV2[:, 1] += lift
    hs._set(js, chunks, tp["attributes"]["POSITION"], TV2, minmax=True)
    return int((lift > 0).sum()), 1000 * lift.max()


GUMLOW_MM = float(os.environ.get("MOUTH_GUMLOW_MM", "2.0"))
GUMLOW_POSES = ({"mouth_open": 0.6}, {"mouth_open": 0.8}, {"mouth_open": 1.0}, {"mouth_open": 0.8, "smile": 0.8},
                {"mouth_open": 1.0, "smile": 1.0}, {"mouth_open": 0.6, "snarl": 0.8}, {"mouth_open": 0.6, "frown": 0.8})
GUMLOW_SLIDERS = (None, "jaw_forward+", "jaw_forward-", "mouth_height+", "mouth_height-")


def gum_low(js, binc, chunks):
    """Her lower gum kept GUMLOW_MM behind her chin's skin as her mouth opens (face 27's triage judge, 16 Oct: own's chin
    showed a dark-red dot at open 1.0, the lower gum's front 0.85 mm through her chin). The push goes back (-z) into the
    teeth's mouth_open key only, so her rest is unmoved and it grows with the opening. Every face, the jaw/mouth sliders at
    their ends, the poses above, the views of VIEWS. Returns (points moved, most mm at mouth_open 1)."""
    tm, tp = hmo._prim(js, "teeth")
    if "gum_low" in tm.get("extras", {}):
        return 0, 0.0
    hm, hp = hmo._prim(js, "skin_head")
    names, tn = hm["extras"]["targetNames"], tm["extras"]["targetNames"]
    keep = lambda n: n.startswith("face_") or n in ("smile", "mouth_open", "smile_open", "smile_hold", "frown", "snarl", "lips_lower+") or n in GUMLOW_SLIDERS
    V = hs._read(js, binc, hp["attributes"]["POSITION"]).astype(np.float64)
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    alpha = hs._read(js, binc, hp["attributes"]["COLOR_0"])[:, 3]
    D = {n: hs._read(js, binc, t["POSITION"]).astype(np.float64) for n, t in zip(names, hp["targets"]) if keep(n)}
    TV = hs._read(js, binc, tp["attributes"]["POSITION"]).astype(np.float64)
    TD = {n: hs._read(js, binc, t["POSITION"]).astype(np.float64) for n, t in zip(tn, tp["targets"]) if keep(n)}
    line = hmo.lips_line(V, D["mouth_open"])
    mid = np.median(V[(np.abs(V[:, 1] - line) < 0.004) & (V[:, 2] > 0.09), 0])
    zf = V[(np.abs(V[:, 1] - line) < 0.003) & (np.abs(V[:, 0] - mid) < 0.005), 2].max()
    near = (np.abs(V[:, 0] - mid) < 0.045) & (np.abs(V[:, 1] - line) < 0.07)
    inside = alpha < ALPHA
    tin = inside[T].any(1) | ((V[T, 2].mean(1) < zf - 0.025) & (np.abs(V[T, 0].mean(1) - mid) < 0.025))
    outer = T[~tin & near[T].all(1)]
    mo_n = np.linalg.norm(TD["mouth_open"], axis=1)
    # (the mouth height slider moved all her teeth as one, 9.5 mm at Low, while her chin's skin under 25 mm below her lips
    # stays put, so at Low her lower gum's foot sat 7-9 mm through her chin when she opened. Each tooth point now takes the
    # share of the slider her skin takes at its height: her skin's move on her face's middle line, over the lips' full move)
    prof_y = np.arange(-0.06, 0.03, 0.0025)
    for sl in ("mouth_height-", "mouth_height+"):
        if sl not in TD or sl not in D:
            continue
        full = np.median(D[sl][(np.abs(V[:, 0] - mid) < 0.004) & (np.abs(V[:, 1] - line) < 0.002), 1])
        if abs(full) < 1e-5:
            continue
        share = []
        for y in prof_y:
            s = (np.abs(V[:, 0] - mid) < 0.004) & (np.abs(V[:, 1] - (line + y)) < 0.0015) & ~inside
            share.append(np.clip(D[sl][np.where(s)[0][np.argmax(V[s, 2])], 1] / full, 0, 1) if s.any() else np.nan)
        share = np.array(share)
        ok = ~np.isnan(share)
        f = np.interp(TV[:, 1] - line, prof_y[ok], share[ok])
        f = np.where(mo_n > 0.002, f, 1.0)          # (her upper teeth and gum go with her lips, as before)
        TD[sl] = TD[sl] * f[:, None]
        hs._set(js, chunks, tp["targets"][tn.index(sl)]["POSITION"], TD[sl], minmax=True)
    cand =np.where((mo_n > 0.002) & (np.abs(TV[:, 0] - mid) < 0.025) & (TV[:, 1] < line - 0.006))[0]
    faces = [None] + [n[5:] for n in names if n.startswith("face_") and not n.endswith(("+", "-"))]
    lips = _lips()
    w = np.zeros(len(cand))
    for f in faces:
        Pf = V + (D["face_" + f] if f else 0) + lips.get(f or "own", 0.0) * D.get("lips_lower+", 0)
        Tf = TV + (TD["face_" + f] if f and "face_" + f in TD else 0)
        for sl in GUMLOW_SLIDERS:
            Ps = Pf + (D[sl] if sl and sl in D else 0)
            Ts = Tf + (TD[sl] if sl and sl in TD else 0)
            for kv in GUMLOW_POSES:
                kv = dict(kv)
                mo, sm = kv.get("mouth_open", 0), kv.get("smile", 0)
                if sm and mo:
                    o = min(mo / 0.3, 1)
                    kv["smile_open"], kv["smile_hold"] = sm * o * o * (3 - 2 * o), sm * mo
                P = Ps + sum(v * D[k] for k, v in kv.items() if k in D)
                PT = Ts + sum(v * TD[k] for k, v in kv.items() if k in TD)
                for yaw, pitch in VIEWS:
                    R = _rot(yaw, pitch)
                    Q, QT = P @ R.T, PT[cand] @ R.T
                    fz = np.cross(Q[outer[:, 1]] - Q[outer[:, 0]], Q[outer[:, 2]] - Q[outer[:, 0]])[:, 2]
                    z = _cover(Q, outer[fz > 0], QT)
                    m = z - QT[:, 2]
                    lack = np.where((z > -np.inf) & (m > -FAR_MM / 1000) & (m < GUMLOW_MM / 1000), GUMLOW_MM / 1000 - m, 0)
                    need_ = lack / max(R[2, 2], 0.5) / mo
                    if os.environ.get("GUMLOW_DEBUG") and need_.max() > 0:
                        print("  gum_low need %.2f mm/open: %s %s %s view %s (pts %d)" % (1000 * need_.max(), f or "own", sl, kv, (yaw, pitch), int((need_ > 0).sum())))
                    w = np.maximum(w, need_)
    if not (w > 0).any():
        tm.setdefault("extras", {})["gum_low"] = {"mm": GUMLOW_MM, "points": 0}
        return 0, 0.0
    # (spread over the moving lower teeth's points, falling linearly to none at SPREAD_MM; copies at UV seams move as one)
    mov = np.where(mo_n > 0.002)[0]
    src = cand[w > 0]
    dist = np.linalg.norm(TV[mov][:, None] - TV[src][None], axis=2)
    p = np.zeros(len(TV))
    p[mov] = (w[w > 0][None] * np.clip(1 - dist / (SPREAD_MM / 1000), 0, 1)).max(1)
    _, weld = np.unique(np.round(TV / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    weld = weld.ravel()
    p = np.bincount(weld, p, minlength=weld.max() + 1)[weld] / np.bincount(weld, minlength=weld.max() + 1)[weld]
    Dm = hs._read(js, binc, tp["targets"][tn.index("mouth_open")]["POSITION"]).astype(np.float64)
    Dm[:, 2] -= p
    hs._set(js, chunks, tp["targets"][tn.index("mouth_open")]["POSITION"], Dm, minmax=True)
    tm.setdefault("extras", {})["gum_low"] = {"mm": GUMLOW_MM, "points": int((p > 0).sum()), "most_mm": round(1000 * p.max(), 3)}
    return int((p > 0).sum()), 1000 * p.max()


def gum_low_file(path, out=None):
    """gum_low alone on a built glb (one whose mouth_inner already ran)."""
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    n, mm = gum_low(js, binc, chunks)
    hs._save(out or path, js, chunks)
    print("GUM_LOW: %d points pushed back, most %.2f mm at mouth_open 1; written %s" % (n, mm, out or path))


def run(path, out=None):
    js, binc = hs._load(path)
    hm, hp = hmo._prim(js, "skin_head")
    if MARK in hm.get("extras", {}):
        print("MOUTH_INNER: already done in", path, "- nothing done")
        if out and out != path:
            hs._save(out, js, {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])})
        return
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    names = hm["extras"]["targetNames"]
    V = hs._read(js, binc, hp["attributes"]["POSITION"]).astype(np.float64)
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    alpha = hs._read(js, binc, hp["attributes"]["COLOR_0"])[:, 3]
    D = {n: hs._read(js, binc, t["POSITION"]).astype(np.float64) for n, t in zip(names, hp["targets"])
         if n.startswith("face_") or n in ("smile", "mouth_open", "smile_open", "smile_hold", "frown", "snarl", "lips_lower+")}
    line = hmo.lips_line(V, D["mouth_open"])
    mid = np.median(V[(np.abs(V[:, 1] - line) < 0.004) & (V[:, 2] > 0.09), 0])
    zf = V[(np.abs(V[:, 1] - line) < 0.003) & (np.abs(V[:, 0] - mid) < 0.005), 2].max()
    near = (np.abs(V[:, 0] - mid) < 0.04) & (np.abs(V[:, 1] - line) < 0.05)
    inside = alpha < ALPHA
    cand = np.where(inside & near & (np.abs(V[:, 0] - mid) < X_MAX) & (np.abs(V[:, 1] - line) > CONTACT_MM / 1000))[0]
    # (her outer skin: no inside point, nor her throat's back wall)
    tin = inside[T].any(1) | ((V[T, 2].mean(1) < zf - 0.025) & (np.abs(V[T, 0].mean(1) - mid) < 0.025))
    outer = T[~tin & near[T].all(1)]
    # (copies of one point, at her UV seams, move as one)
    _, weld = np.unique(np.round(V / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    weld = weld.ravel()
    lips = _lips()
    ins = np.where(inside & near)[0]
    done = []
    for f in [n[5:] for n in names if n.startswith("face_") and not n.endswith(("+", "-"))]:
        w = need(V, T, D, alpha, f, lips.get(f, 0.0), cand, outer)
        if not (w > 0).any():
            continue
        # (spread: each inside point takes the most of its pushed neighbours', falling linearly to none at SPREAD_MM)
        src = cand[w > 0]
        dist = np.linalg.norm(V[ins][:, None] - V[src][None], axis=2)
        push = (w[w > 0][None] * np.clip(1 - dist / (SPREAD_MM / 1000), 0, 1)).max(1)
        p = np.zeros(len(V))
        p[ins] = push
        p = np.bincount(weld, p, minlength=weld.max() + 1)[weld] / np.bincount(weld, minlength=weld.max() + 1)[weld]
        p = np.where(inside, np.maximum(p, 0), 0)
        a = hp["targets"][names.index("face_" + f)]["POSITION"]
        Df = D["face_" + f].copy()
        Df[:, 2] -= p
        hs._set(js, chunks, a, Df, minmax=True)
        done.append("%s %d points, most %.2f mm" % (f, int((p > 0).sum()), 1000 * p.max()))
    ng, mg = gum_lift(js, binc, chunks)
    done.append("gum: %d points raised, most %.2f mm" % (ng, mg))
    # (gum_low is NOT hooked (face 28, 17 Oct): what it fixes shows only at mouth_open 0.6+, which no scene uses; run it
    # alone with gum_low_file when a scene first opens her mouth that far. Unjudged; its push reaches 7.6 mm at open 1)
    hm.setdefault("extras", {})[MARK] = {"margin_mm": MARGIN_MM, "gum_h_mm": GUM_H_MM, "faces": done}
    hs._save(out or path, js, chunks)
    print("MOUTH_INNER: her mouth's inside pushed back behind her skin: %s; written %s" % ("; ".join(done) or "none needed", out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0] if a else GLB, a[1] if len(a) > 1 else None)
