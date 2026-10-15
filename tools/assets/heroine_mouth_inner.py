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
    hm.setdefault("extras", {})[MARK] = {"margin_mm": MARGIN_MM, "gum_h_mm": GUM_H_MM, "faces": done}
    hs._save(out or path, js, chunks)
    print("MOUTH_INNER: her mouth's inside pushed back behind her skin: %s; written %s" % ("; ".join(done) or "none needed", out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0] if a else GLB, a[1] if len(a) > 1 else None)
