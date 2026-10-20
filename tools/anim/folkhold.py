"""A kit townsperson's held pieces against its body, from Godot (godot/tools_scenes/folk_hold.gd's JSON: the body and
outfit skinned on the CPU, the pieces as the town mounts them): per sampled time, each piece's lowest point above the
ground (a tip, a staff's foot), its clearance to the body (the holding fist and, for a shield, its forearm left out:
nearest vertex, signed by the vertex normal; negative = inside, mm), which part of the body is nearest, and each
elbow's bend.
    python tools/anim/folkhold.py dump.json [more.json ...]
"""
from __future__ import annotations

import json
import math
import re
import sys

import numpy as np
from scipy.spatial import cKDTree

# What each holding bone grips with (left out of its piece's clearance).
HOLD = {"hand_r": r"^(hand_r|(thumb|index|middle|ring|pinky)_\d+(_leaf)?_r)$",
        "hand_l": r"^(hand_l|(thumb|index|middle|ring|pinky)_\d+(_leaf)?_l)$",
        "lowerarm_l": r"^(lowerarm_l|hand_l|(thumb|index|middle|ring|pinky)_\d+(_leaf)?_l)$"}


def bend(a, b, c):
    u, v = np.subtract(b, a), np.subtract(c, b)
    return math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


def report(path):
    d = json.load(open(path))
    print(f"{path}: {d['clip']} ({d['length']:.2f} s)")
    worst = {}
    for fr in d["frames"]:
        B = fr["bones"]
        V, N = np.array(fr["body"]["v"]), np.array(fr["body"]["n"])
        names = fr["body"]["bones"]
        bone = np.array([names[i] for i in fr["body"]["bone"]])
        ground = float(V[:, 1].min())
        held = fr["held"]
        # Every hand's grip region, left out of every piece in hand (a two-handed blade lies in both fists).
        hands = "|".join(HOLD[h][1:-1] for h in held if h.startswith("hand"))
        parts = [f"t {fr['t']:.2f}  sole {ground * 1000:+.0f} mm  elbow l {bend(B['upperarm_l'], B['lowerarm_l'], B['hand_l']):.0f} "
                 f"r {bend(B['upperarm_r'], B['lowerarm_r'], B['hand_r']):.0f}"]
        for hb, pts in held.items():
            P = np.array(pts)
            skip = re.compile(f"^({hands}|{HOLD[hb][1:-1]})$")
            keep = np.array([not skip.match(b) for b in bone])
            tree = cKDTree(V[keep])
            dist, ix = tree.query(P)
            Vk, Nk, bk = V[keep], N[keep], bone[keep]
            sd = np.einsum("ij,ij->i", P - Vk[ix], Nk[ix])
            inside = (sd < 0) & (dist < 0.04)
            depth = float(-sd[inside].min()) if inside.any() else 0.0
            j = int(np.argmin(np.where(inside, sd, dist)))
            low = P[np.argmin(P[:, 1])]
            parts.append(f"{hb}: low {(low[1] - 0) * 1000:.0f} mm at ({low[0]:+.2f},{low[2]:+.2f})  clear {dist.min() * 1000:.0f} mm"
                         f"  in {depth * 1000:.0f} mm ({int(inside.sum())} pts) near {bk[ix[j]]}")
            w = worst.setdefault(hb, [1e9, 1e9, 0.0, -1e9])
            w[0] = min(w[0], low[1]); w[1] = min(w[1], dist.min()); w[2] = max(w[2], depth); w[3] = max(w[3], low[1])
        print("  " + " | ".join(parts))
    for hb, (lo, cl, dep, hi) in worst.items():
        print(f"  WORST {hb}: low {lo * 1000:.0f}..{hi * 1000:.0f} mm  clear {cl * 1000:.0f} mm  in {dep * 1000:.0f} mm")




# ---------------------------------------------------------------- the quick model --
# A dump's body and pieces carried rigidly by their top bones, so another clip's frames can be checked in Python in
# seconds (the same measures; joints approximate, a few mm): python tools/anim/folkhold.py --model dump.json CLIP.json
# [skeleton.json [DUMP_CLIP.json]] [--step N] (DUMP_CLIP: the clip the dump played, if not CLIP). Confirm the chosen clip with a real dump.

def load_clip(path, sk):
    d = json.load(open(path))
    T = len(next(t for t in d["tracks"])["keys"])
    rot = np.broadcast_to(sk.rest_rot, (T,) + sk.rest_rot.shape).copy()
    pos = np.broadcast_to(sk.rest_pos, (T,) + sk.rest_pos.shape).copy()
    for t in d["tracks"]:
        (rot if t["type"] == "rot" else pos)[:, sk.i(t["bone"])] = np.array(t["keys"])
    return rot, pos


def _mat(m):
    """A dump's 12 numbers (basis columns, origin) as a 4x4."""
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = m[0:3], m[3:6], m[6:9], m[9:12]
    return M


def model_check(dump, clip, skel, step=25, dump_clip=None, extra=None):
    """The dump's body (each vertex with its top bone) and pieces carried by the town's own skeleton (the dump's bone
    poses at its first time: the bone lengths and scales People.Build gave this person) through `clip`'s turns: each
    bone's local pose is the dump's with its turn swapped, R(new) R(old)^-1 (root and pelvis: the clip's positions).
    `dump_clip`: the clip the dump played (its frame 0 is the dump's first time), if not `clip`. `extra(hb, piece points,
    body points, normals, bone names, joints)`: more to print per piece and frame."""
    from rig import Skeleton, qmatrix
    sk = Skeleton.load(skel)
    d = json.load(open(dump))
    fr = d["frames"][0]
    SG = _mat(fr["skel"])
    G0 = {n: _mat(m) for n, m in fr["pose"].items()}
    rot0, pos0 = load_clip(dump_clip or clip, sk)
    rot, pos = load_clip(clip, sk)
    order = [j for j in range(len(sk)) if sk.names[j] in G0]
    par = {j: sk.parent[j] for j in order}
    L0 = {}
    for j in order:
        P = G0[sk.names[par[j]]] if par[j] >= 0 else np.eye(4)
        L0[j] = np.linalg.inv(P) @ G0[sk.names[j]]
    moved = {sk.i("root"), sk.i("pelvis")}

    def pose(f):
        G = {}
        for j in order:  # (parents first: the skeleton's order)
            L = L0[j].copy()
            L[:3, :3] = qmatrix(rot[f, j]) @ qmatrix(rot0[0, j]).T @ L0[j][:3, :3]
            if j in moved:
                L[:3, 3] = L0[j][:3, 3] + (pos[f, j] - pos0[0, j])
            G[j] = (G[par[j]] if par[j] >= 0 else np.eye(4)) @ L
        return {j: SG @ M for j, M in G.items()}

    W0 = pose_dump = {sk.i(n): SG @ M for n, M in G0.items() if n in sk.index}
    chk = pose(0) if dump_clip is None else None
    if chk is not None:
        err = max(np.abs(chk[j][:3, 3] - W0[j][:3, 3]).max() for j in order)
        print(f"  (model rebuilds the dump's own pose to {err * 1000:.2f} mm)")
    V, N = np.array(fr["body"]["v"]), np.array(fr["body"]["n"])
    bnames = fr["body"]["bones"]
    bone = np.array([bnames[i] for i in fr["body"]["bone"]])
    bix = np.array([sk.i(bnames[i]) for i in fr["body"]["bone"]])

    def to_local(X, j, normal=False):
        Mi = np.linalg.inv(W0[j])
        return X @ Mi[:3, :3].T + (0 if normal else Mi[:3, 3])
    groups = {b: bix == b for b in np.unique(bix)}
    local = np.empty_like(V); nloc = np.empty_like(N)
    for b, m in groups.items():
        local[m] = to_local(V[m], b)
        nloc[m] = to_local(N[m], b, True)
    ploc = {hb: (to_local(np.array(P), sk.i(hb)), sk.i(hb)) for hb, P in fr["held"].items()}
    print(f"model of {dump} on {clip}")
    out = []
    for f in range(0, len(rot), step):
        Wf = pose(f)
        Vw = np.empty_like(local); Nw = np.empty_like(nloc)
        for b, m in groups.items():
            Vw[m] = local[m] @ Wf[b][:3, :3].T + Wf[b][:3, 3]
            n_ = nloc[m] @ Wf[b][:3, :3].T
            Nw[m] = n_ / np.linalg.norm(n_, axis=1, keepdims=True)
        B = {n: Wf[sk.i(n)][:3, 3] for n in fr["bones"]}
        hands = "|".join(HOLD[h][1:-1] for h in ploc if h.startswith("hand"))
        parts = [f"f {f:3d}  sole {Vw[:, 1].min() * 1000:+.0f}  elbow l {bend(B['upperarm_l'], B['lowerarm_l'], B['hand_l']):.0f} "
                 f"r {bend(B['upperarm_r'], B['lowerarm_r'], B['hand_r']):.0f}"]
        for hb, (L, b) in ploc.items():
            P = L @ Wf[b][:3, :3].T + Wf[b][:3, 3]
            keep = np.array([not re.match(f"^({hands}|{HOLD[hb][1:-1]})$", x) for x in bone])
            tree = cKDTree(Vw[keep])
            dist, ix = tree.query(P)
            sd = np.einsum("ij,ij->i", P - Vw[keep][ix], Nw[keep][ix])
            inside = (sd < 0) & (dist < 0.04)
            depth = float(-sd[inside].min()) if inside.any() else 0.0
            j = int(np.argmin(np.where(inside, sd, dist)))
            low = P[np.argmin(P[:, 1])]
            parts.append(f"{hb}: low {low[1] * 1000:.0f} mm at ({low[0]:+.2f},{low[2]:+.2f})  clear {dist.min() * 1000:.0f}  in {depth * 1000:.0f} mm near {bone[keep][ix[j]]}"
                         + (extra(hb, P, Vw, Nw, bone, B) if extra else ""))
            _, _, vt = np.linalg.svd(P - P.mean(0), full_matrices=False)
            ax = vt[2] if hb == "lowerarm_l" else vt[0]
            ax = ax * (np.sign(ax[0]) if hb == "lowerarm_l" else np.sign(np.dot(ax, P[np.argmax(np.linalg.norm(P - B[hb], axis=1))] - B[hb])))
            out.append((hb, low[1], dist.min(), depth, low, ax))
        print("  " + " | ".join(parts))
    for hb in ploc:
        rows = [r for r in out if r[0] == hb]
        lows = np.array([r[4] for r in rows])
        print(f"  WORST {hb}: low {min(r[1] for r in rows) * 1000:.0f}..{max(r[1] for r in rows) * 1000:.0f} mm "
              f"(its point moves {np.ptp(lows[:, 0]) * 1000:.0f} x {np.ptp(lows[:, 2]) * 1000:.0f} mm)  "
              f"clear {min(r[2] for r in rows) * 1000:.0f} mm  in {max(r[3] for r in rows) * 1000:.0f} mm  "
              f"{'face' if hb == 'lowerarm_l' else 'line'} {np.round(np.mean([r[5] for r in rows], axis=0), 2)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--model":
        step = int(a[a.index("--step") + 1]) if "--step" in a else 25
        rest = [x for x in a[1:] if not x.startswith("--") and not x.isdigit()]
        from rig import DATA
        model_check(rest[0], rest[1], rest[2] if len(rest) > 2 else DATA / "folk_male_skeleton.json", step,
                    rest[3] if len(rest) > 3 else None)
    else:
        for p in a:
            report(p)
