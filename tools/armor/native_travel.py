"""Her clips as the builder reads them: every clip's bones' skinning matrices (posed once by gear_wear's poser, cached
beside the clips) with her corrective shapes' weights in each frame (rig_drive.corrective_weights, the game's driver),
her skin under them (linear blend; skin(.., cw=) adds her corrective shapes in rest space before skinning, as Godot
does), and what a rigid ride does over them.
A plate that must slide under another (native_spaulder's "shell") takes its lap from this travel, measured at build
time: a new clip, a new rig or a new body re-derives it.

    S = frames()["S"]                 [frame, bone, 4, 4], every clip end to end
    ride(S, index, {"clavicle_l": 1}) [frame, 4, 4]: that rule's rigid motion
"""
import json
import os

import numpy as np

SKIP = ("Jog_Fwd",)          # (not one of hers)
FOUR = ("daggers_heavy", "run_reaver", "sword_heavy", "cast_flick")
_MEM = {}


def poses():
    """{"names": [bone ..], "clips": {clip: [F, B, 4, 4]}, "shapes": [shape ..], "cw": {clip: [F, k]} (her corrective
    shapes' weights per frame)}: read from the cache beside the clips when it answers the
    clips and the body as they are on disk (names, sizes, times), posed again (about 25 s) when not."""
    if "poses" in _MEM:
        return _MEM["poses"]
    import gear_wear as gw
    body = os.path.join(gw.REPO, "godot", "art", "people", json.load(open(os.path.join(gw.GEAR, "gear_index.json"), encoding="utf-8"))["body"])
    files = sorted(fn for fn in os.listdir(gw.CLIPS) if fn.endswith(".json"))
    stamp = lambda p: [os.path.basename(p), os.path.getsize(p), os.stat(p).st_mtime_ns]  # noqa: E731
    seen = [stamp(os.path.join(gw.CLIPS, fn)) for fn in files]
    seen += [stamp(os.path.join(body, fn)) for fn in sorted(os.listdir(body))] if os.path.isdir(body) else [stamp(body)]
    key = json.dumps(["cw1"] + seen)
    cache = os.path.join(os.path.dirname(gw.CLIPS), "clip_poses.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        if str(z["key"]) == key:
            out = _MEM["poses"] = {"names": [str(n) for n in z["names"]], "shapes": [str(n) for n in z["shapes"]],
                                   "clips": {c[5:]: z[c].astype(float) for c in z.files if c.startswith("clip_")},
                                   "cw": {c[3:]: z[c].astype(float) for c in z.files if c.startswith("cw_")}}
            return out
    sc = gw.build_scene(body, [])
    clips, ws = {}, {}
    for fn in files:
        cp = gw.ClipPoser(sc, json.load(open(os.path.join(gw.CLIPS, fn))))
        fr = [cp.frame(f) for f in range(cp.n)]
        clips[fn[:-5]] = np.stack([S for S, _ in fr])
        ws[fn[:-5]] = fr
    shapes = sorted({k for fr in ws.values() for _, w in fr for k in w})
    cw = {c: np.array([[float(w.get(k, 0.0) or 0.0) for k in shapes] for _, w in fr]).reshape(len(fr), len(shapes)) for c, fr in ws.items()}
    np.savez_compressed(cache, key=np.array(key), names=np.array(sc.poser.names), shapes=np.array(shapes, dtype=str),
                        **{"clip_" + c: v.astype(np.float32) for c, v in clips.items()}, **{"cw_" + c: v.astype(np.float32) for c, v in cw.items()})
    out = _MEM["poses"] = {"names": list(sc.poser.names), "shapes": shapes, "cw": {c: v.astype(np.float32).astype(float) for c, v in cw.items()},
                           "clips": {c: v.astype(np.float32).astype(float) for c, v in clips.items()}}
    return out


def frames(skip=SKIP, four=FOUR):
    """{"S" [F, B, 4, 4], "index" {bone: column}, "four" [F] (the frame is one of the four fight clips'), "clip" [F]
    (its clip's name), "frame" [F] (its number in it), "clips" n, "cw" {shape: [F]} (her corrective shapes' weights)}:
    every clip but `skip`, end to end."""
    k = ("frames", tuple(skip), tuple(four))
    if k not in _MEM:
        z = poses()
        names = [c for c in sorted(z["clips"]) if c not in skip]
        _MEM[k] = {"S": np.concatenate([z["clips"][c] for c in names]), "index": {n: i for i, n in enumerate(z["names"])},
                   "four": np.concatenate([np.full(len(z["clips"][c]), c in four) for c in names]),
                   "clip": np.concatenate([np.full(len(z["clips"][c]), c) for c in names]),
                   "frame": np.concatenate([np.arange(len(z["clips"][c])) for c in names]), "clips": len(names)}
        cw = np.concatenate([z["cw"][c] for c in names]) if names else np.zeros((0, len(z["shapes"])))
        _MEM[k]["cw"] = {n: cw[:, i] for i, n in enumerate(z["shapes"]) if np.abs(cw[:, i]).max() > 0}
    return _MEM[k]


def ride(S, index, rule):
    """[F, 4, 4]: a rule's {bone: share} motion over the frames (one bone: that bone's own, a rigid motion)."""
    return sum(v * S[:, index[b]] for b, v in rule.items()) / sum(rule.values())


def move(M, X):
    """[F, n, 3]: the points X under the motions M [F, 4, 4]."""
    return np.einsum("fij,nj->fni", M[:, :3, :3], X) + M[:, None, :3, 3]


def skin(ref, S, index, vs, cw=None):
    """(V [F, n, 3], N [F, n, 3]): her skin's vertices `vs` and their normals over the frames, linear blend. cw
    ({shape: [F] weights}, the frames' own: frames()["cw"] sliced like S): her corrective shapes added in rest space
    before skinning (the game's skin: LBS(V + sum_k w_k dP_k)), the normals then the deformed mesh's own (area-weighted
    face normals over every triangle touching vs, welded as ref.N is). cw None: linear blend of ref.N, as before."""
    if cw is not None:
        cw = {k: np.asarray(w, float) for k, w in cw.items() if k in ref.shapes and np.abs(w).max() > 0}
    if cw is None:
        jm = np.array([index[n] for n in ref.joint_names])
        J, W = jm[np.asarray(ref.J)[vs]], np.asarray(ref.W, float)[vs]
        Vh = np.c_[ref.V[vs], np.ones(len(vs))]
        V, N = np.zeros((len(S), len(vs), 3)), np.zeros((len(S), len(vs), 3))
        for k in range(J.shape[1]):
            Sk = S[:, J[:, k]]
            V += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :], Vh)
            N += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :3], ref.N[vs])
        return V, N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)
    vs = np.asarray(vs)
    T = np.asarray(ref.T)
    wid = np.asarray(getattr(ref, "wid", np.arange(len(ref.V))))
    inv = wid[vs]                                        # every vertex sharing a weld id with vs, and their triangles
    mates = np.flatnonzero(np.isin(wid, inv))
    tri = T[np.isin(T, mates).any(1)]
    ext = np.unique(np.r_[vs, tri.ravel()])
    at = np.full(len(ref.V), -1)
    at[ext] = np.arange(len(ext))
    R = np.broadcast_to(ref.V[ext], (len(S), len(ext), 3)).copy()
    for nm, w in cw.items():
        R += w[:, None, None] * np.asarray(ref.shapes[nm], float)[ext][None]
    jm = np.array([index[n] for n in ref.joint_names])
    J, W = jm[np.asarray(ref.J)[ext]], np.asarray(ref.W, float)[ext]
    V = np.zeros((len(S), len(ext), 3))
    for k in range(J.shape[1]):
        if not W[:, k].any():
            continue
        Sk = S[:, J[:, k]]
        V += W[None, :, k, None] * (np.einsum("fvij,fvj->fvi", Sk[:, :, :3, :3], R) + Sk[:, :, :3, 3])
    Tl = at[tri]
    fn = np.cross(V[:, Tl[:, 1]] - V[:, Tl[:, 0]], V[:, Tl[:, 2]] - V[:, Tl[:, 0]])
    ids, wl = np.unique(wid[ext], return_inverse=True)
    wl = wl.reshape(-1)
    N = np.zeros((len(S), len(ids), 3))
    for c in range(3):
        np.add.at(N, (slice(None), wl[Tl[:, c]]), fn)
    N = N[:, wl[at[vs]]]
    return V[:, at[vs]], N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)


def on_skin(ref, S, index, M, X, reach=0.07):
    """A rigid part's points X (riding M) against her moving skin: per frame (off [F, n]: each point's height over
    the skin nearest it, along that skin's normal; slide [F, n]: how far it has moved along the skin from the skin
    point that lay under it at rest). Reads her skin within `reach` of the points."""
    from scipy.spatial import cKDTree
    vs = np.unique(np.concatenate(cKDTree(ref.V).query_ball_point(X, reach)).astype(int))
    V, N = skin(ref, S, index, vs)
    loc = cKDTree(ref.V[vs]).query(X)[1]
    P = move(M, X)
    off, slide = np.zeros(P.shape[:2]), np.zeros(P.shape[:2])
    for f in range(len(S)):
        j = cKDTree(V[f]).query(P[f])[1]
        off[f] = ((P[f] - V[f][j]) * N[f][j]).sum(1)
        d, n = P[f] - V[f][loc], N[f][loc]
        slide[f] = np.linalg.norm(d - (d * n).sum(1)[:, None] * n, axis=1)
    off0 = ((X - ref.V[vs][loc]) * ref.N[vs][loc]).sum(1)
    d0 = X - ref.V[vs][loc]
    slide0 = np.linalg.norm(d0 - (d0 * ref.N[vs][loc]).sum(1)[:, None] * ref.N[vs][loc], axis=1)
    return off - off0, np.maximum(slide - slide0, 0.0)


# ---------------------------------------------------------------- the reach rule: a rigid part against her moving skin

def clip_frames(clips="all"):
    """The frames of `clips` ("all", "four", or names): a bool per frame of frames()."""
    z = frames()
    if clips in (None, "all"):
        return np.ones(len(z["S"]), bool)
    names = FOUR if clips == "four" else tuple(clips)
    missing = [c for c in names if c not in set(z["clip"])]
    if missing:
        raise SystemExit(f"native_travel: no clip {missing} among her clips")
    return np.isin(z["clip"], names)


def sink(ref, X, rule, clips="all", reach=0.07, chunk=120):
    """(sink [n], where [n]): the most each point X of a RIGID part riding `rule` ({bone: share}) comes down toward
    her moving skin over the clips' frames (m, 0 = never lower than at rest), and the frame (an index of frames())
    where it does. A plate reaches only as far as this stays under a limit (the reach rule: any part, any recipe)."""
    z = frames()
    on = np.flatnonzero(clip_frames(clips))
    X = np.asarray(X, float).reshape(-1, 3)
    out, where = np.zeros(len(X)), np.full(len(X), on[0] if len(on) else 0)
    for a in range(0, len(on), chunk):
        f = on[a:a + chunk]
        off, _ = on_skin(ref, z["S"][f], z["index"], ride(z["S"][f], z["index"], rule), X, reach)
        m, k = -off.min(0), f[off.argmin(0)]
        where, out = np.where(m > out, k, where), np.maximum(out, m)
    return out, where


def past(ref, X, rule, limit, clips="all"):
    """The reach rule on a part's points: {"sink_mm" (its most), "past" (points over `limit`), "worst" [clip, frame]}."""
    z = frames()
    s, w = sink(ref, X, rule, clips)
    k = int(np.argmax(s))
    return {"sink_mm": round(float(s[k]) / 0.001, 2), "past": int((s > limit).sum()), "worst": [str(z["clip"][w[k]]), int(z["frame"][w[k]])]}
