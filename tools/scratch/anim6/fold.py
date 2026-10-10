"""Her skin's folds and cracks per pose: triangles that turn over (posed
normal against the rest normal carried by the triangle's own blend of bone
turns) near the knees, elbows and armpits, and coincident points (seams)
that come apart.

    python -u fold.py before built [split]     (split: the before body split here, as helpers.split now cuts it)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import S, WT, pose, elbow, knee, wrist_turn, arm_raise  # noqa: E402
from rigtest import arm_forward, thigh_forward  # noqa: E402
from rig import Skeleton  # noqa: E402
from skin import Body  # noqa: E402


def both(fn, *a):
    return [fn("l", *a), fn("r", *a)]


POSES = {
    "knee 100": both(knee, 100), "knee 120": both(knee, 120), "knee 145": both(knee, 145),
    "hip 110 knee 135": both(thigh_forward, 110) + both(knee, 135),
    "elbow 120": both(elbow, 120), "elbow 145": both(elbow, 145),
    "e90 wrist +80": both(elbow, 90) + [wrist_turn("l", 80, 0.5), wrist_turn("r", 80, 0.5)],
    "arm raised 100": both(arm_raise, 100), "arm raised 130": both(arm_raise, 130),
    "arm fwd 90 e45": both(arm_forward, 90) + both(elbow, 45),
}
REGIONS = {"knee": ("calf_l", "calf_r"), "elbow": ("lowerarm_l", "lowerarm_r"), "armpit": ("upperarm_l", "upperarm_r")}


def load(which):
    if which == "before":
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        return Body(sk, [(S / "before/people/heroine.glb", lambda n: n == "Heroine", "skin")], None, helpers=False)
    if which == "split":
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        return Body(sk, [(S / "before/people/heroine.glb", lambda n: n == "Heroine", "skin")], None, helpers=True)
    sk = Skeleton.load(WT / "tools/anim/data/heroine_skeleton.json")
    return Body(sk, [(WT / "godot/art/people/heroine.glb", lambda n: n == "Heroine", "skin")], None, helpers=True)


def tri_n(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def run(which):
    b = load(which)
    T = b.T
    n0 = tri_n(b.P, T)
    area = 0.5 * np.linalg.norm(np.cross(b.P[T[:, 1]] - b.P[T[:, 0]], b.P[T[:, 2]] - b.P[T[:, 0]]), axis=1)
    cen = b.P[T].mean(1)
    heads = {n: b.rest[b.sk.index[n]][:3, 3] for r in REGIONS.values() for n in r}
    region = np.full(len(T), "", dtype=object)
    for name, (l, r) in REGIONS.items():
        d = np.minimum(np.linalg.norm(cen - heads[l], axis=1), np.linalg.norm(cen - heads[r], axis=1))
        region[(d < 0.10) & (region == "")] = name
    # coincident points (seams): groups by position
    key = np.round(b.P / 1e-5).astype(np.int64)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    dup = np.nonzero(cnt[inv] > 1)[0]
    print(f"== {which}: {len(T)} triangles, {len(dup)} seam points", flush=True)
    for pname, edits in POSES.items():
        G = pose(b, edits)
        Sm = b.skin_mats(G)
        P = b.pose(G)
        n = tri_n(P, T)
        # the rest normal carried by the first corner's blended turn
        L = np.zeros((len(T), 3, 3))
        v = T[:, 0]
        for k in range(4):
            L += b.W[v, k][:, None, None] * Sm[b.J[v, k], :3, :3]
        c = np.einsum("tij,tj->ti", L, n0)
        c /= np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-12)
        flip = (np.einsum("ti,ti->t", n, c) < 0) & (area > 1e-9)
        out = []
        for name in REGIONS:
            m = flip & (region == name)
            out.append(f"{name} {m.sum():4d}")
        # seams apart: the largest gap within a coincident group
        gap = 0.0
        if len(dup):
            g = inv[dup]
            order = np.argsort(g)
            gs, ps = g[order], P[dup][order]
            first = np.r_[True, gs[1:] != gs[:-1]]
            idx = np.cumsum(first) - 1
            base = ps[first][idx]
            dd = np.linalg.norm(ps - base, axis=1)
            gap = dd.max() * 1000
            worst = dup[order][np.argmax(dd)]
            wb = b.sk.names[b.J[worst, 0]]
        print(f"  {pname:18s} flipped: {'  '.join(out)}   seam gap max {gap:5.2f} mm" + (f" (at {wb})" if gap > 0.05 else ""), flush=True)


if __name__ == "__main__":
    import os
    import helpers as hp
    for w in sys.argv[1:] or ["before", "built"]:
        if ":" in w:      # split:<cut>:<reach>
            _, cut, reach = w.split(":")
            hp.SPEC["weights"]["crease"] = {"cut": float(cut), "reach": float(reach)}
            print(f"(crease cut {cut} reach {reach})")
            w = "split"
        run(w)
