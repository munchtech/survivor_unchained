"""Her clips as the builder reads them: every clip's bones' skinning matrices (posed once by gear_wear's poser, cached
beside the clips), her skin under them (linear blend only: no corrective shapes), and what a rigid ride does over them.
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
    """{"names": [bone ..], "clips": {clip: [F, B, 4, 4]}}: read from the cache beside the clips when it answers the
    clips and the body as they are on disk (names, sizes, times), posed again (about 25 s) when not."""
    if "poses" in _MEM:
        return _MEM["poses"]
    import gear_wear as gw
    body = os.path.join(gw.REPO, "godot", "art", "people", json.load(open(os.path.join(gw.GEAR, "gear_index.json"), encoding="utf-8"))["body"])
    files = sorted(fn for fn in os.listdir(gw.CLIPS) if fn.endswith(".json"))
    stamp = lambda p: [os.path.basename(p), os.path.getsize(p), os.stat(p).st_mtime_ns]  # noqa: E731
    seen = [stamp(os.path.join(gw.CLIPS, fn)) for fn in files]
    seen += [stamp(os.path.join(body, fn)) for fn in sorted(os.listdir(body))] if os.path.isdir(body) else [stamp(body)]
    key = json.dumps(seen)
    cache = os.path.join(os.path.dirname(gw.CLIPS), "clip_poses.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        if str(z["key"]) == key:
            out = _MEM["poses"] = {"names": [str(n) for n in z["names"]],
                                   "clips": {c[5:]: z[c].astype(float) for c in z.files if c.startswith("clip_")}}
            return out
    sc = gw.build_scene(body, [])
    clips = {}
    for fn in files:
        cp = gw.ClipPoser(sc, json.load(open(os.path.join(gw.CLIPS, fn))))
        clips[fn[:-5]] = np.stack([cp.frame(f)[0] for f in range(cp.n)])
    np.savez_compressed(cache, key=np.array(key), names=np.array(sc.poser.names), **{"clip_" + c: v.astype(np.float32) for c, v in clips.items()})
    out = _MEM["poses"] = {"names": list(sc.poser.names), "clips": {c: v.astype(np.float32).astype(float) for c, v in clips.items()}}
    return out


def frames(skip=SKIP, four=FOUR):
    """{"S" [F, B, 4, 4], "index" {bone: column}, "four" [F] (the frame is one of the four fight clips'), "clip" [F]
    (its clip's name), "frame" [F] (its number in it), "clips" n}: every clip but `skip`, end to end."""
    k = ("frames", tuple(skip), tuple(four))
    if k not in _MEM:
        z = poses()
        names = [c for c in sorted(z["clips"]) if c not in skip]
        _MEM[k] = {"S": np.concatenate([z["clips"][c] for c in names]), "index": {n: i for i, n in enumerate(z["names"])},
                   "four": np.concatenate([np.full(len(z["clips"][c]), c in four) for c in names]),
                   "clip": np.concatenate([np.full(len(z["clips"][c]), c) for c in names]),
                   "frame": np.concatenate([np.arange(len(z["clips"][c])) for c in names]), "clips": len(names)}
    return _MEM[k]


def ride(S, index, rule):
    """[F, 4, 4]: a rule's {bone: share} motion over the frames (one bone: that bone's own, a rigid motion)."""
    return sum(v * S[:, index[b]] for b, v in rule.items()) / sum(rule.values())


def move(M, X):
    """[F, n, 3]: the points X under the motions M [F, 4, 4]."""
    return np.einsum("fij,nj->fni", M[:, :3, :3], X) + M[:, None, :3, 3]


def skin(ref, S, index, vs):
    """(V [F, n, 3], N [F, n, 3]): her skin's vertices `vs` and their normals over the frames, linear blend."""
    jm = np.array([index[n] for n in ref.joint_names])
    J, W = jm[np.asarray(ref.J)[vs]], np.asarray(ref.W, float)[vs]
    Vh = np.c_[ref.V[vs], np.ones(len(vs))]
    V, N = np.zeros((len(S), len(vs), 3)), np.zeros((len(S), len(vs), 3))
    for k in range(J.shape[1]):
        Sk = S[:, J[:, k]]
        V += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :], Vh)
        N += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :3], ref.N[vs])
    return V, N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)


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
