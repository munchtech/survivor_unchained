#!/usr/bin/env python
"""P1 E: her body's UVs BY RULE on our topology (a build step: deterministic, from the topology's own structure and
its reference surface, never a hand unwrap). The rules are L1's (tools/body/base/her_paint_regions.json, (c) inherited
from look-l1@0148089b4); every choice below names its reason.

    python tools/body/topo_uv.py [--tiers close,play]        -> tools/body/base/uv_<tier>.npz (+ printed numbers)

The layout (the left half, x >= 0; the right half is the left's MIRRORED COPY, overlapping it exactly):
  islands  TORSO  regions 4 5 6 10 (neck_decolletage, torso_front, torso_back, pelvis_glutes): one half-body sheet,
                  bounded by the neck's ring (the head's seam), the center line (the mirror line: front, crotch, back),
                  the shoulder hole's rim (trunk|shoulder parts) and the leg root (trunk/crotch|thigh parts). No cut
                  crosses the decolletage, the belly or the back: the sheet is whole (L1 seams rule).
           ARM    regions 7 8 (parts shoulder arm elbow forearm): rim -> wrist ring (forearm|hand), cut along the inner
                  arm (cut_path: the edge path that faces the torso, the side the play camera never sees).
           LEG    regions 11 12 (parts thigh knee shin): leg root -> ankle ring (shin|foot), cut along the inside leg.
           HAND_BACK, HAND_PALM  region 9 (part hand): split on the hand's sides (each quad by its normal against
                  the hand's thin axis, smoothed), so the knuckles and the palm are each whole.
           THUMB_BACK, THUMB_PALM  (E2) the hand's quads nearest our thumb's bones past thumb_02 (the opposed thumb
                  folded over the palm's sheet), each half from its side of the back | palm split.
           FOOT_TOP, FOOT_SOLE   region 13 (part foot) behind the toes: the sole (normals within 75 degrees of down)
                  apart; the top cut from the ankle's inner point (the leg's cut, continued) down to the sole's rim.
           TOES_TOP, TOES_SOLE   (E2) the toes ahead of our ball_l plane (the crease the toes bend on), split by
                  half height. Floors (checked, pieces solved alone): each toe half alone p95 1.16-1.17, the thumb's
                  pad alone 1.25: the templates' own caps; joined they read 1.18 / 1.26 / 1.22, kept joined (an island per
                  toe still misses 1.15 and seams every toe).
  triangles each quad split on its shorter diagonal, or a concave quad on its inside one (quad_diag: fixed per
                  topology; the export, the solves and the bake share it).
  mirror   overlapping copies (why: L1's "a painted half mirrors clean" holds by construction, every texel of the
           2k map serves both halves, so her body's texel density doubles; asymmetric marks are not in her look
           (clean painted skin). The center vertices are split left|right (same UV) so each half keeps its own
           tangent frame: the UVs mirror there, the handedness flips).
  solve    per island: LSCM (conformal, two pins far apart) then ARAP (local/global, cotan weights) on the reference
           surface (out/topo/<tier>.npz V: every body on our topology shares one layout, so the maps carry across
           sliders and NPCs); limbs turned so the limb runs along V (root at the top), the torso with its neck up.
  density  each island scaled to the json's texel_density (body 1.0, hands 1.5, feet 0.75) of one common scale,
           then packed (raster packer: FFT collision test, bottom-left, 0/90 degree turns so limbs stay on U or V)
           at the largest common scale that fits, with an 8 px gutter at 2k.
  play     (E2) ONE texture set for both tiers. Play's cuts (arm, leg, foot top) by the rules on play's own edges
           (play_guide), close's cuts drawn along them (cut_path guide: play's edges are twice as long, so play could
           never follow a cut drawn on close's); play's islands from close's (play_islands: each quad the close island
           most of it lies on, within its region group, so the rings stay play's own); each play UV vertex close's UV
           at its closest point on close's island, its own side of a cut (its faces' UVs pick it), clamped on close's
           triangles; then relaxed on play's surface by an ARAP held to that by a spring (arap_fit, lam 1). Checked by
           agreement(): play's UV against close's at the same body point (2k texels), and how far play reads off its
           own close island (within half the 8 px gutter it reads its own border texels).
Output per tier: corner UVs and the glb vertex split: src[k] (our topology vertex of glb vertex k; the first n are our
vertices in order, the seam/mirror copies appended), UV[k] (glTF: v down), the export's triangles over glb vertices,
the island and region of each quad, and the numbers (stretch, density, overlaps, flips, packing).
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VERSION = "uv1"
ISL = ["TORSO_FRONT", "TORSO_BACK", "ARM", "LEG", "HAND_BACK", "HAND_PALM", "FOOT_TOP", "FOOT_SOLE", "TOES_TOP", "TOES_SOLE", "THUMB_BACK", "THUMB_PALM"]
DENS_KEY = {"TORSO_FRONT": "body", "TORSO_BACK": "body", "ARM": "body", "LEG": "body", "HAND_BACK": "hands", "HAND_PALM": "hands",
            "FOOT_TOP": "feet", "FOOT_SOLE": "feet", "TOES_TOP": "feet", "TOES_SOLE": "feet",
            "THUMB_BACK": "hands", "THUMB_PALM": "hands"}
REGION_ISLAND = {4: "TORSO_FRONT", 5: "TORSO_FRONT", 6: "TORSO_FRONT", 10: "TORSO_FRONT", 7: "ARM", 8: "ARM", 11: "LEG", 12: "LEG",
                 9: "HAND", 13: "FOOT"}
TEX = 2048
GUTTER_PX = 8


def regions_json():
    with open(os.path.join(HERE, "base", "her_paint_regions.json")) as f:
        return json.load(f)


def topo_sha(z):
    return hashlib.sha256(np.ascontiguousarray(z["V"], np.float32).tobytes() +
                          np.ascontiguousarray(z["Q"], np.int32).tobytes()).hexdigest()[:16]


def U(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-20)


def quad_normals(V, Q):
    return U(np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]]))


def vertex_normals(V, Q):
    n = np.zeros_like(V)
    fn = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
    for k in range(4):
        np.add.at(n, Q[:, k], fn)
    return U(n)


def quad_diag(V, Q):
    """(E2) per quad, True where it splits along 1-3 (else 0-2). (a) A concave or folded quad (its two splits' areas
    more than 2% apart) takes the diagonal whose triangles cover the least area: the outside diagonal folds the two
    triangles over each other (the nape's thin kite at the center line flipped in UV and stretched 21x on 0-2).
    Otherwise the shorter diagonal (the better-shaped pair: the measured best of min-area, shorter, max-min-angle on
    the toes, palm and torso). Fixed per topology from its reference V, so every body on it splits the same way."""
    P = V[Q]

    def ar(a, b, c):
        return 0.5 * np.linalg.norm(np.cross(P[:, b] - P[:, a], P[:, c] - P[:, a]), axis=1)
    a02, a13 = ar(0, 1, 2) + ar(0, 2, 3), ar(1, 2, 3) + ar(1, 3, 0)
    short13 = np.linalg.norm(P[:, 3] - P[:, 1], axis=1) < np.linalg.norm(P[:, 2] - P[:, 0], axis=1)
    return np.where(np.abs(a13 - a02) > 0.02 * a02, a13 < a02, short13)


def quad_tris(C, diag):
    """The triangles of quads C [m,4] (corner indices), first triangles then second (row t and t + m: quad t)."""
    a = np.where(diag[:, None], C[:, [1, 2, 3]], C[:, [0, 1, 2]])
    b = np.where(diag[:, None], C[:, [1, 3, 0]], C[:, [0, 2, 3]])
    return np.concatenate([a, b])


def cross2(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def edge_key(a, b, n):
    a, b = np.minimum(a, b), np.maximum(a, b)
    return a.astype(np.int64) * n + b


def quad_edge_keys(Q, n):
    return np.stack([edge_key(Q[:, k], Q[:, (k + 1) % 4], n) for k in range(4)], 1)


def quad_adjacency(Q, n, sel):
    """Edge-adjacent pairs among the selected quads (index pairs into Q)."""
    qi = np.nonzero(sel)[0]
    K = quad_edge_keys(Q[qi], n).ravel()
    owner = np.repeat(qi, 4)
    o = np.argsort(K, kind="stable")
    K, owner = K[o], owner[o]
    same = K[1:] == K[:-1]
    return np.stack([owner[:-1][same], owner[1:][same]], 1), K[:-1][same]


# ----------------------------------------------------------------------------------------------- islands --
def split_two(V, Q, z, quads, axis_fn, smooth_iter=6, mid_r=0.0, mid_zone=None, cos_min=0.0):
    """Split a template part's quads in two by each quad's normal against an axis, then majority-smoothed over edge
    neighbours and each side kept as one piece (stray pieces go to the other side). Returns a bool per quad (True =
    the axis side)."""
    n = len(V)
    vs = np.unique(Q[quads])
    a = axis_fn(V[vs])
    if mid_r:
        # by height along the axis against the part's local middle there: the points within mid_r of the quad's
        # middle in the plane across the axis span the part's thickness there; the quad is on the axis side if it sits
        # above their mid height. A finger's or a toe's sides split at their half height even where the walls face
        # sideways (a normal's sign there is noise: tight toes' gaps folded inside one island)
        e1 = U(np.cross(a, [1.0, 0, 0] if abs(a[0]) < 0.9 else [0, 1.0, 0]))
        e2 = np.cross(a, e1)
        Pv = V[vs]
        tree = cKDTree(np.stack([Pv @ e1, Pv @ e2], 1))
        C = V[Q[quads]].mean(1)
        hv = Pv @ a
        nb = tree.query_ball_point(np.stack([C @ e1, C @ e2], 1), mid_r)
        mid = np.array([0.5 * (hv[j].max() + hv[j].min()) if len(j) else c_ for j, c_ in zip(nb, C @ a)])
        lab = (C @ a) > mid
    if not mid_r or mid_zone is not None:
        fn = quad_normals(V, Q[quads])
        by_n = (fn @ a) > cos_min
        lab = by_n if not mid_r else np.where(mid_zone, lab, by_n)
    return smooth_label(Q, n, quads, lab, smooth_iter)


def smooth_label(Q, n, quads, lab, smooth_iter=6):
    """A two-way label over a part's quads, majority-smoothed over edge neighbours and each side kept as one piece
    (stray pieces go to the other side). Returns the bool per quad of `quads`."""
    lab = np.asarray(lab, bool).copy()
    sel = np.zeros(len(Q), bool)
    sel[quads] = True
    pairs, _ = quad_adjacency(Q, n, sel)
    loc = -np.ones(len(Q), np.int64)
    loc[quads] = np.arange(len(quads))
    a_, b_ = loc[pairs[:, 0]], loc[pairs[:, 1]]
    A = sp.coo_matrix((np.ones(2 * len(a_)), (np.r_[a_, b_], np.r_[b_, a_])), shape=(len(quads),) * 2).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    for _ in range(smooth_iter):
        s = A @ lab.astype(float)
        lab = np.where(s * 2 > deg, True, np.where(s * 2 < deg, False, lab))
    for side in (True, False):
        m = lab == side
        sub = A[m][:, m]
        nc, cc = connected_components(sub, directed=False)
        if nc > 1:
            big = np.argmax(np.bincount(cc))
            idx = np.nonzero(m)[0][cc != big]
            lab[idx] = not side
    return lab


def principal(P):
    c = P.mean(0)
    _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
    return c, Vt


def joints(z):
    """Our skeleton's joint positions (skeleton.place_skeleton_ours on the topology's own vertices: (c) B1's
    landmarks, nothing keyed to MakeHuman), name -> world head position."""
    import skeleton as sk
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    with open(os.path.join(HERE, "base", "landmarks.json")) as f:
        lm = json.load(f)["tiers"]
    tier = str(z.get("_tier", "close"))
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        names, _, worlds, _, _ = sk.place_skeleton_ours(skel, z["V"].astype(float), lm[tier])
    return {nm: worlds[i][:3, 3].copy() for i, nm in enumerate(names)}


def ball_plane(z):
    """Our skeleton's ball_l joint and the foot's forward direction (foot_l -> ball_l, level)."""
    j = joints(z)
    b, f_ = j["ball_l"], j["foot_l"]
    d = b - f_
    d[1] = 0
    return b, U(d)


def seg_dist(X, a, b):
    """Distance of points X to the segment a-b, and the segment parameter t (unclamped)."""
    ab = b - a
    t = ((X - a) @ ab) / max(float(ab @ ab), 1e-20)
    return np.linalg.norm(X - (a + np.clip(t, 0, 1)[:, None] * ab), axis=1), t


def thumb_quads(z, hand):
    """The hand's quads nearest our thumb's bones past its first joint (thumb_02_l -> thumb_04_leaf_l) among every
    hand bone (the hand, the metacarpals, the finger chains), smoothed to one piece: the thumb's own pair of islands."""
    j = joints(z)
    V, Q = z["V"].astype(float), z["Q"]
    C = V[Q[hand]].mean(1)
    chains = {"thumb": ["thumb_02_l", "thumb_03_l", "thumb_04_leaf_l"], "thumb0": ["thumb_01_l", "thumb_02_l"]}
    for f in ("index", "middle", "ring", "pinky"):
        chains[f] = [f"{f}_metacarpal_l", f"{f}_01_l", f"{f}_02_l", f"{f}_03_l", f"{f}_04_leaf_l"]
    chains["hand"] = ["hand_l", "middle_metacarpal_l"]
    D = {}
    for k, ch in chains.items():
        D[k] = np.min([seg_dist(C, j[a], j[b])[0] for a, b in zip(ch[:-1], ch[1:])], 0)
    names = list(D)
    near = np.argmin(np.stack([D[k] for k in names]), 0)
    lab = near == names.index("thumb")
    return smooth_label(Q, len(V), hand, lab)


def assign_islands(z):
    """The island of every LEFT quad (right quads: -1; they mirror). The rules in the module docstring."""
    V, Q = z["V"].astype(float), z["Q"]
    side = z["side"]
    qside = side[Q].max(1)
    left = qside == 1
    isl = -np.ones(len(Q), np.int64)
    qreg = z["qreg"]
    for r, nm in REGION_ISLAND.items():
        m = left & (qreg == r)
        if nm in ISL:
            isl[m] = ISL.index(nm)
    hand = np.nonzero(left & (qreg == 9))[0]
    foot = np.nonzero(left & (qreg == 13))[0]

    def thin_axis(P):              # the hand's thin direction (its smallest principal axis), signed to the back (+y-ish
        _, Vt = principal(P)       # is not stable in an A pose: the back of the hand faces out, away from the body, +x)
        a = Vt[2]
        return a if a[0] >= 0 else -a
    back = split_two(V, Q, z, hand, thin_axis, mid_r=0.004)
    isl[hand[back]] = ISL.index("HAND_BACK")
    isl[hand[~back]] = ISL.index("HAND_PALM")
    # the thumb its own pair (E2): (a) in the palm's sheet the opposed thumb folded over the palm in UV (42 overlap
    # cells at 4k) and held its p95 at 1.18; cut at our thumb_02 joint's nearest-bone border, each half its side's
    th = thumb_quads(z, hand)
    isl[hand[th & back]] = ISL.index("THUMB_BACK")
    isl[hand[th & ~back]] = ISL.index("THUMB_PALM")
    # the sole: the foot's lower half (normals below its middle plane), smoothed, as the hand's palm is split from
    # its back: the toes' gaps then fall on the seam, not folded inside one island
    # the sole: the quads facing within 60 degrees of straight down; but in the toes (ahead of the ball, our skeleton's
    # ball_l placed from our vertices, less 1 cm) by half height, as the hand (a toe's walls face sideways)
    ball, fwd = ball_plane(z)
    C = V[Q[foot]].mean(1)
    # E2: the toes are their own pair of islands (TOES_TOP | TOES_SOLE), cut from the foot at our ball_l plane (the
    # quads whose middle lies ahead of it, smoothed to one clean loop): (a) one sheet of a foot and its five toes
    # cannot lie flat inside the stretch target (p95 1.24 top / 1.32 sole as one island, the toes' tubes folded over
    # its rim); the ball joint is where the toes bend, so the seam sits on the crease the toes' motion already makes
    toe = smooth_label(Q, len(V), foot, (C - ball) @ fwd > 0.0)
    rest, toes_q = foot[~toe], foot[toe]
    down = lambda P: np.array([0.0, -1.0, 0.0])         # noqa: E731
    # the sole: the quads facing within 75 degrees of straight down (60 left the foot's outer wall by the ball on the
    # top island, its p95 1.18 against 1.12 here; 85 takes the wall's top too: the sole 1.14)
    sole = split_two(V, Q, z, rest, down, cos_min=np.cos(np.radians(75)))
    isl[rest[sole]] = ISL.index("FOOT_SOLE")
    isl[rest[~sole]] = ISL.index("FOOT_TOP")
    # the toes by half height (a toe's walls face sideways: a normal's sign there is noise)
    tsole = split_two(V, Q, z, toes_q, down, mid_r=0.004)
    isl[toes_q[tsole]] = ISL.index("TOES_SOLE")
    isl[toes_q[~tsole]] = ISL.index("TOES_TOP")
    assert (isl[left] >= 0).all(), "a left quad with no island"
    return isl, left


def boundary_between(Q, n, quads_a, quads_b):
    """Vertices on edges shared by a quad of set a and a quad of set b."""
    ka = set(quad_edge_keys(Q[quads_a], n).ravel().tolist())
    kb = quad_edge_keys(Q[quads_b], n).ravel()
    k = np.array(sorted(ka.intersection(kb.tolist())), np.int64)
    return np.unique(np.r_[k // n, k % n]), k


def cut_path(V, Q, n, quads, starts, targets, d_in, avoid=None, k_in=12.0, guide=None):
    """The cheapest edge path inside the island from one of `starts` to one of `targets`, each edge costing its
    length times (1 + k_in * (1 - n.d_in)/2): it hugs the side facing d_in (the inner arm / inside leg). With a guide
    (a polyline from the start side to the target side: play's cut, E2), each edge costs its length times
    1 + (d / 2 mm)^2 instead (d: the farthest of its ends and middle from the guide) and the ends are the start and
    target nearest the guide's ends: close redraws play's cut on its finer edges. Returns the path's edge keys and
    its vertices."""
    Qi = Q[quads]
    vn = vertex_normals(V, Qi)
    e = np.unique(np.sort(np.concatenate([Qi[:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)
    if avoid is not None:        # never along the island's own boundary edges (the path must stay inside)
        ek = edge_key(e[:, 0], e[:, 1], n)
        e = e[~np.isin(ek, avoid)]
    L = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    if guide is None:
        din = d_in(V)
        f = 1 + k_in * (1 - 0.5 * ((vn[e[:, 0]] * din[e[:, 0]]).sum(1) + (vn[e[:, 1]] * din[e[:, 1]]).sum(1))) / 2
        s = starts[np.argmax((vn[starts] * din[starts]).sum(1))]
    else:
        t_ = np.linspace(0, 1, 9)[:, None, None]
        tree = cKDTree((guide[:-1][None] * (1 - t_) + guide[1:][None] * t_).reshape(-1, 3))
        d = np.max([tree.query(V[e[:, 0]] * (1 - a) + V[e[:, 1]] * a)[0] for a in (0.0, 0.5, 1.0)], 0)
        f = 1 + (d / 0.002) ** 2
        s = starts[np.argmin(np.linalg.norm(V[starts] - guide[0], axis=1))]
    w = L * f
    G = sp.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    dist, pred = dijkstra(G, indices=int(s), return_predecessors=True)
    if guide is None:
        t = targets[np.argmin(dist[targets])]
    else:
        t = targets[np.argmin(np.linalg.norm(V[targets] - guide[-1], axis=1))]
    assert np.isfinite(dist[t]), "no cut path"
    path = [int(t)]
    while path[-1] != s:
        path.append(int(pred[path[-1]]))
    path = np.array(path[::-1])
    return edge_key(path[:-1], path[1:], n), path


def limb_inner(P_island):
    """(c) the inner direction of a limb: toward the body's middle (-x), off the limb's own axis (its first principal
    axis): an arm's underside facing the torso, a leg's inside facing the other leg."""
    _, Vt = principal(P_island)
    ax = Vt[0]
    d = np.array([-1.0, 0, 0]) - ax * (-ax[0])
    d = U(d)
    return lambda P: np.broadcast_to(d, P.shape)


def torso_cuts(V, Q, n, z, isl, left, seam, bnd, info, tq, qi):
    """The torso half split front | back where its surface faces neither (each cut edge costs its length times
    1 + 12 |n.z|): (A) the neck ring's side -> the shoulder rim, (B) the rim's lowest point (the armpit) down the
    side -> the leg root, (C) the leg root's inner point -> the center line under the crotch. The front keeps the
    neck's front, the decolletage, the breasts, the belly and the groin whole; the back the nape, the back and the
    glutes. isl is relabelled in place (TORSO_FRONT | TORSO_BACK by the larger mean n.z)."""
    hand_q = np.r_[qi["HAND_BACK"], qi["HAND_PALM"]]
    arm_q = qi["ARM"]
    leg_q = qi["LEG"]
    rim, _ = boundary_between(Q, n, tq, arm_q)
    root, _ = boundary_between(Q, n, tq, leg_q)
    k = quad_edge_keys(Q[tq], n).ravel()
    u, c = np.unique(k, return_counts=True)
    bk = u[c == 1]
    bv = np.unique(np.r_[bk // n, bk % n])
    neck = np.setdiff1d(bv[z["side"][bv] > 0], np.r_[rim, root])
    neck = neck[np.isin(z["part"][neck], [list(z["parts"]).index("neck")])]
    center = np.nonzero(z["side"] == 0)[0]
    center = center[np.isin(center, np.unique(Q[tq]))]
    zf = lambda P: np.broadcast_to(np.array([0.0, 0, 1.0]), P.shape)       # noqa: E731

    def side_path(starts, targets, pick):
        Qi = Q[tq]
        vn = vertex_normals(V, Qi)
        e = np.unique(np.sort(np.concatenate([Qi[:, [k_, (k_ + 1) % 4]] for k_ in range(4)]), 1), axis=0)
        ek = edge_key(e[:, 0], e[:, 1], n)
        e = e[~np.isin(ek, bnd(tq))]
        L_ = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
        f = 1 + 12 * 0.5 * (np.abs(vn[e[:, 0], 2]) + np.abs(vn[e[:, 1], 2]))
        w = L_ * f
        G = sp.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        s_ = int(pick(starts))
        dist, pred = dijkstra(G, indices=s_, return_predecessors=True)
        t = targets[np.argmin(dist[targets])]
        assert np.isfinite(dist[t]), "no torso cut"
        path = [int(t)]
        while path[-1] != s_:
            path.append(int(pred[path[-1]]))
        path = np.array(path[::-1])
        return edge_key(path[:-1], path[1:], n), path
    vn_all = vertex_normals(V, Q[tq])
    kA, pA = side_path(neck, rim, lambda s_: s_[np.argmax(vn_all[s_, 0] - np.abs(vn_all[s_, 2]))])
    kB, pB = side_path(rim, root, lambda s_: s_[np.argmin(V[s_, 1])])
    kC, pC = side_path(root, center, lambda s_: s_[np.argmin(V[s_, 0])])
    for kk in (kA, kB, kC):
        seam |= set(kk.tolist())
    # the pieces
    sel = np.zeros(len(Q), bool)
    sel[tq] = True
    pairs, keys = quad_adjacency(Q, n, sel)
    ok = ~np.isin(keys, np.array(sorted(seam), np.int64))
    loc = -np.ones(len(Q), np.int64)
    loc[tq] = np.arange(len(tq))
    A = sp.coo_matrix((np.ones(ok.sum()), (loc[pairs[ok, 0]], loc[pairs[ok, 1]])), shape=(len(tq),) * 2)
    nc, cc = connected_components(A, directed=False)
    assert nc == 2, ("the torso cuts do not split it in two", nc)
    fz = quad_normals(V, Q[tq])[:, 2]
    front = int(np.argmax([fz[cc == i].mean() for i in range(2)]))
    isl[tq] = np.where(cc == front, ISL.index("TORSO_FRONT"), ISL.index("TORSO_BACK"))
    L_ = lambda p: round(float(np.linalg.norm(np.diff(V[p], axis=0), axis=1).sum()), 3)     # noqa: E731
    info["torso_cuts"] = {"A_neck_to_rim_m": L_(pA), "B_armpit_to_leg_root_m": L_(pB), "C_crotch_m": L_(pC),
                          "front_quads": int((cc == front).sum()), "back_quads": int((cc != front).sum())}


def seams(z, isl, left, guide=None):
    """Every seam edge of the left half: island borders, and the limb and foot-top cuts (guide: play's cut polylines
    by name, close redraws them; info["_paths"] the cuts' polylines)."""
    V, Q = z["V"].astype(float), z["Q"]
    n = len(V)
    K = quad_edge_keys(Q, n)
    owner = np.repeat(np.arange(len(Q)), 4)
    Kf = K.ravel()
    o = np.argsort(Kf, kind="stable")
    Ks, ow = Kf[o], owner[o]
    same = Ks[1:] == Ks[:-1]
    a, b = ow[:-1][same], ow[1:][same]
    both_left = left[a] & left[b]
    seam = set(Ks[:-1][same][both_left & (isl[a] != isl[b])].tolist())
    qi = {nm: np.nonzero(left & (isl == ISL.index(nm)))[0] for nm in ISL}
    info = {}
    # the island's own boundary (as edge keys) for each cut's avoid list
    def bnd(quads):
        k = quad_edge_keys(Q[quads], n).ravel()
        u, c = np.unique(k, return_counts=True)
        inner = set(seam)
        return np.array(sorted(set(u[c == 1].tolist()) | inner), np.int64)
    trunk_side = np.nonzero(left & np.isin(z["qreg"], [4, 5, 6, 10]))[0]
    torso_cuts(V, Q, n, z, isl, left, seam, bnd, info, trunk_side, qi)
    hand_q = np.r_[qi["HAND_BACK"], qi["HAND_PALM"]]
    foot_q = np.r_[qi["FOOT_TOP"], qi["FOOT_SOLE"]]
    # ARM: wrist ring (arm|hand) -> rim (torso|arm)
    wrist, _ = boundary_between(Q, n, qi["ARM"], hand_q)
    rim, _ = boundary_between(Q, n, qi["ARM"], trunk_side)
    din = limb_inner(V[np.unique(Q[qi["ARM"]])])
    k_arm, p_arm = cut_path(V, Q, n, qi["ARM"], wrist, rim, din, avoid=bnd(qi["ARM"]), guide=(guide or {}).get("arm"))
    seam |= set(k_arm.tolist())
    # LEG: ankle ring (leg|foot) -> leg root (torso|leg)
    ankle, _ = boundary_between(Q, n, qi["LEG"], foot_q)
    root, _ = boundary_between(Q, n, qi["LEG"], trunk_side)
    din_l = limb_inner(V[np.unique(Q[qi["LEG"]])])
    k_leg, p_leg = cut_path(V, Q, n, qi["LEG"], ankle, root, din_l, avoid=bnd(qi["LEG"]), guide=(guide or {}).get("leg"))
    seam |= set(k_leg.tolist())
    # FOOT_TOP: from the leg cut's ankle point to the sole's rim, inner side
    # (only when the top is a ring around the ankle: when the sole's half reaches the ankle ring it is a disc already)
    Qt = Q[qi["FOOT_TOP"]]
    et = np.unique(np.sort(np.concatenate([Qt[:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)
    chi = len(np.unique(Qt)) - len(et) + len(Qt)
    k_ft = np.zeros(0, np.int64)
    if chi == 0:
        solerim, _ = boundary_between(Q, n, qi["FOOT_TOP"], qi["FOOT_SOLE"])
        k_ft, p_ft = cut_path(V, Q, n, qi["FOOT_TOP"], np.array([p_leg[0]]), solerim, din_l, avoid=bnd(qi["FOOT_TOP"]),
                              guide=(guide or {}).get("foot_top"))
        seam |= set(k_ft.tolist())
    info["cuts"] = {"arm": {"from": "the wrist ring's inner point", "to": "the shoulder rim", "edges": int(len(k_arm)),
                            "length_m": round(float(np.linalg.norm(np.diff(V[p_arm], axis=0), axis=1).sum()), 3)},
                    "leg": {"from": "the ankle ring's inner point", "to": "the leg root", "edges": int(len(k_leg)),
                            "length_m": round(float(np.linalg.norm(np.diff(V[p_leg], axis=0), axis=1).sum()), 3)},
                    "foot_top": {"from": "the leg cut's ankle point", "to": "the sole's rim", "edges": int(len(k_ft))}}
    info["_paths"] = {"arm": p_arm, "leg": p_leg}
    if len(k_ft):
        info["_paths"]["foot_top"] = p_ft
    return seam, info


# ------------------------------------------------------------------------------------------------- corners --
def corner_classes(Q, n, sel, seam):
    """Union-find of the selected quads' corners across their non-seam shared edges: each class = one UV vertex.
    Returns cls [nq,4] (-1 off the selection), the class's topology vertex, and the class count."""
    nq = len(Q)
    parent = np.arange(nq * 4)

    def find(x):
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r
    qi = np.nonzero(sel)[0]
    # corner id = q*4+k; for each edge (k, k+1) of each quad: key -> list of (q, k, k+1)
    rec = {}
    for q in qi:
        for k in range(4):
            a, b = int(Q[q, k]), int(Q[q, (k + 1) % 4])
            key = (min(a, b), max(a, b))
            rec.setdefault(key, []).append((q, k, (k + 1) % 4, a, b))
    seam_s = seam
    for key, lst in rec.items():
        if len(lst) != 2 or (key[0] * n + key[1]) in seam_s:
            continue
        (q1, k1a, k1b, a1, b1), (q2, k2a, k2b, a2, b2) = lst
        c1 = {a1: q1 * 4 + k1a, b1: q1 * 4 + k1b}
        c2 = {a2: q2 * 4 + k2a, b2: q2 * 4 + k2b}
        for v in key:
            ra, rb = find(c1[v]), find(c2[v])
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    cls = -np.ones((nq, 4), np.int64)
    roots = np.array([find(q * 4 + k) for q in qi for k in range(4)])
    u, inv = np.unique(roots, return_inverse=True)
    cls[qi] = inv.reshape(-1, 4)
    cv = np.zeros(len(u), np.int64)
    cv[cls[qi].ravel()] = Q[qi].ravel()
    return cls, cv, len(u)


# ------------------------------------------------------------------------------------------- the solves --
def tri_frames(P, T):
    """Each triangle's isometric 2D coordinates (x0 = 0, x1 on the x axis) and area."""
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    e1, e2 = b - a, c - a
    l1 = np.linalg.norm(e1, axis=1)
    ex = e1 / l1[:, None]
    nrm = np.cross(e1, e2)
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    ey = U(np.cross(U(nrm), ex))
    X = np.zeros((len(T), 3, 2))
    X[:, 1, 0] = l1
    X[:, 2, 0] = (e2 * ex).sum(1)
    X[:, 2, 1] = (e2 * ey).sum(1)
    return X, area


def cot_weights(X):
    """cot of the angle opposite each edge (i, i+1), for the 2D triangles X [m,3,2]."""
    out = np.zeros((len(X), 3))
    for i in range(3):
        o = (i + 2) % 3
        u = X[:, i] - X[:, o]
        v = X[:, (i + 1) % 3] - X[:, o]
        cr = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
        out[:, i] = (u * v).sum(1) / np.maximum(np.abs(cr), 1e-20)
    return out


def lscm(P, T, nv):
    """Least squares conformal map (Levy 2002) as Dirichlet minus signed area; two pins: the pair of vertices
    farthest apart along the island's first principal axis."""
    X, area = tri_frames(P, T)
    W = cot_weights(X)
    I, J, Vv = [], [], []
    for i in range(3):
        a, b = T[:, i], T[:, (i + 1) % 3]
        w = 0.5 * W[:, i]
        I += [a, b, a, b]
        J += [b, a, a, b]
        Vv += [-w, -w, w, w]
    L = sp.coo_matrix((np.concatenate(Vv), (np.concatenate(I), np.concatenate(J))), shape=(nv, nv)).tocsr()
    # signed area 0.5 * sum over boundary edges (i -> j, the face's orientation) of (u_i v_j - u_j v_i)
    he = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    key = he[:, 0] * nv + he[:, 1]
    rkey = he[:, 1] * nv + he[:, 0]
    bd = he[~np.isin(key, rkey)]
    i, j = bd[:, 0], bd[:, 1]
    Ar = sp.coo_matrix((np.r_[0.5 * np.ones(len(i)), -0.5 * np.ones(len(i))], (np.r_[i, j], np.r_[j, i])),
                       shape=(nv, nv)).tocsr()          # u^T Ar v = area
    # E = 1/2 u'Lu + 1/2 v'Lv - u'Ar v  -> the symmetric 2n system [[L, -Ar], [-Ar', L]] (gradient)
    M = sp.bmat([[L, -Ar], [-Ar.T, L]]).tocsr()
    _, Vt = principal(P)
    s = P @ Vt[0]
    p0, p1 = int(np.argmin(s)), int(np.argmax(s))
    d = float(s[p1] - s[p0])
    fixed = np.array([p0, p1, nv + p0, nv + p1])
    val = np.array([0.0, d, 0.0, 0.0])
    free = np.setdiff1d(np.arange(2 * nv), fixed)
    Mf = M[free][:, free]
    rhs = -M[free][:, fixed] @ val
    x = np.zeros(2 * nv)
    x[fixed] = val
    x[free] = spl.spsolve((Mf + Mf.T).tocsc() * 0.5, rhs)
    return np.stack([x[:nv], x[nv:]], 1)


def arap(P, T, UV0, nv, iters=40, rounds=4, power=6.0):
    """As-rigid-as-possible (Liu et al. 2008) local/global from UV0; one vertex held (translation only). Then
    `rounds` more blocks of `iters`, each triangle's weight times its distortion^power (max(s1, 1/s2), eased): the
    worst triangles pull hardest, so the tail (the p95 the check reads) comes down, not only the mean."""
    X, area = tri_frames(P, T)
    W0 = np.maximum(cot_weights(X), 1e-4)
    mult = np.ones(len(T))
    keep = np.arange(1, nv)
    UVc = UV0.copy()
    for rnd in range(rounds + 1):
        W = W0 * mult[:, None]
        I, J, Vv = [], [], []
        for i in range(3):
            a, b = T[:, i], T[:, (i + 1) % 3]
            w = W[:, i]
            I += [a, b, a, b]
            J += [b, a, a, b]
            Vv += [-w, -w, w, w]
        L = sp.coo_matrix((np.concatenate(Vv), (np.concatenate(I), np.concatenate(J))), shape=(nv, nv)).tocsc()
        Lk = L[keep][:, keep].tocsc()
        L0 = L[keep][:, [0]]
        Lf = spl.splu(Lk)
        for _ in range(iters):
            S = np.zeros((len(T), 2, 2))
            for i in range(3):
                a, b = T[:, i], T[:, (i + 1) % 3]
                du = UVc[a] - UVc[b]
                dx = X[:, i] - X[:, (i + 1) % 3]
                S += W0[:, i, None, None] * du[:, :, None] * dx[:, None, :]
            Uu, _, Vt = np.linalg.svd(S)
            neg = np.linalg.det(Uu @ Vt) < 0
            Uu[neg, :, 1] *= -1
            R = Uu @ Vt
            rhs = np.zeros((nv, 2))
            for i in range(3):
                a, b = T[:, i], T[:, (i + 1) % 3]
                dx = X[:, i] - X[:, (i + 1) % 3]
                r = W[:, i, None] * np.einsum("tij,tj->ti", R, dx)
                np.add.at(rhs, a, r)
                np.add.at(rhs, b, -r)
            new = np.zeros((nv, 2))
            new[0] = UVc[0]
            b_ = rhs[keep] - (L0 @ UVc[[0]])
            new[keep, 0] = Lf.solve(b_[:, 0])
            new[keep, 1] = Lf.solve(b_[:, 1])
            UVc = new
        if rnd < rounds:
            sv, sa, _ = jac_sv(P, T, UVc)
            d = np.maximum(sv[:, 0], 1 / np.maximum(sv[:, 1], 1e-6))
            mult = np.sqrt(mult * np.clip(d, 1, 3) ** power)
    return UVc


def arap_fit(P, T, UVt, k, lam, iters=12):
    """(E2) ARAP on (P, T) at scale k (UV units per metre) held to target UVs UVt by a per-vertex spring lam
    (relative to the cotan weights): the target's layout kept where it is a fair map of this surface, its folds and
    slivers relaxed (play's projection of close's UVs folds where play's coarse toes and neck slivers sit a few mm
    off close's surface)."""
    X, _ = tri_frames(P, T)
    X = X * k
    W = np.maximum(cot_weights(X), 1e-4)
    nv = len(UVt)
    I, J, Vv = [], [], []
    for i in range(3):
        a, b = T[:, i], T[:, (i + 1) % 3]
        w = W[:, i]
        I += [a, b, a, b]
        J += [b, a, a, b]
        Vv += [-w, -w, w, w]
    L = sp.coo_matrix((np.concatenate(Vv), (np.concatenate(I), np.concatenate(J))), shape=(nv, nv)).tocsc()
    Lf = spl.splu((L + sp.diags(np.broadcast_to(lam, nv).astype(float))).tocsc())
    UVc = UVt.copy()
    for _ in range(iters):
        S = np.zeros((len(T), 2, 2))
        for i in range(3):
            a, b = T[:, i], T[:, (i + 1) % 3]
            S += W[:, i, None, None] * (UVc[a] - UVc[b])[:, :, None] * (X[:, i] - X[:, (i + 1) % 3])[:, None, :]
        Uu, _, Vt = np.linalg.svd(S)
        neg = np.linalg.det(Uu @ Vt) < 0
        Uu[neg, :, 1] *= -1
        R = Uu @ Vt
        rhs = np.zeros((nv, 2))
        for i in range(3):
            a, b = T[:, i], T[:, (i + 1) % 3]
            r = W[:, i, None] * np.einsum("tij,tj->ti", R, X[:, i] - X[:, (i + 1) % 3])
            np.add.at(rhs, a, r)
            np.add.at(rhs, b, -r)
        rhs += np.broadcast_to(lam, nv)[:, None] * UVt
        UVc = np.stack([Lf.solve(rhs[:, 0]), Lf.solve(rhs[:, 1])], 1)
    return UVc


def jac_sv(P, T, UV):
    """Each triangle's singular values (s1 >= s2) of the 3D -> UV map, and its UV signed area."""
    X, area = tri_frames(P, T)
    du1, du2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    Dx = np.stack([X[:, 1], X[:, 2]], 2)               # [m,2,2] columns = the two edges in 2D
    Du = np.stack([du1, du2], 2)
    Jm = Du @ np.linalg.inv(Dx)
    s = np.linalg.svd(Jm, compute_uv=False)
    sa = 0.5 * (du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0])
    return s, sa, area


# ---------------------------------------------------------------------------------------------- packing --
def outline_mask(UVs, T, res, scale, dil):
    """The island's cells at a scale (its lower-left at the origin), dilated; via a fast triangle fill."""
    from scipy import ndimage
    P = UVs * scale
    w, h = int(np.ceil(P[:, 0].max())) + 2 * dil + 2, int(np.ceil(P[:, 1].max())) + 2 * dil + 2
    g = fill_tris(P + dil + 1, T, w, h)
    if dil:
        g = ndimage.binary_dilation(g, iterations=dil)
    return g


def fill_tris(P, T, w, h, ids=None):
    """Conservative-ish triangle fill on a w x h grid: a cell is in if its centre is inside, or a vertex/edge midpoint
    falls in it (thin slivers). ids: write the triangle id + 1 instead of True (int grid)."""
    g = np.zeros((h, w), np.int64 if ids is not None else bool)
    tri = P[T]
    lo = np.floor(tri.min(1)).astype(int)
    hi = np.floor(tri.max(1)).astype(int)
    sz = (hi - lo + 1)
    # vectorised in chunks, each bbox padded to the chunk's largest (sorted by size so the padding is small)
    order = np.argsort(sz[:, 0] * sz[:, 1], kind="stable")
    m = len(T)
    chunk = 4096
    for s0 in range(0, m, chunk):
        idx = order[s0:s0 + chunk]
        bx = int(sz[idx, 0].max())
        by = int(sz[idx, 1].max())
        if bx * by * len(idx) > 6e7:
            for t in idx:
                _fill_one(g, tri[t], lo[t], sz[t], w, h, None if ids is None else t + 1)
            continue
        ox = np.arange(bx)[None, None, :]
        oy = np.arange(by)[None, :, None]
        cx = lo[idx, 0][:, None, None] + ox + 0.5
        cy = lo[idx, 1][:, None, None] + oy + 0.5
        cx = np.broadcast_to(cx, (len(idx), by, bx))
        cy = np.broadcast_to(cy, (len(idx), by, bx))
        a, b, c = tri[idx, 0], tri[idx, 1], tri[idx, 2]

        def ed(p, q):
            return ((cx - q[:, 0, None, None]) * (p[:, 1, None, None] - q[:, 1, None, None]) -
                    (p[:, 0, None, None] - q[:, 0, None, None]) * (cy - q[:, 1, None, None]))
        d1, d2, d3 = ed(a, b), ed(b, c), ed(c, a)
        ins = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
        ins &= (ox < sz[idx, 0][:, None, None]) & (oy < sz[idx, 1][:, None, None])
        X = np.broadcast_to(lo[idx, 0][:, None, None] + ox, ins.shape)
        Y = np.broadcast_to(lo[idx, 1][:, None, None] + oy, ins.shape)
        ok = ins & (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
        if ids is None:
            g[Y[ok], X[ok]] = True
        else:
            g[Y[ok], X[ok]] = np.broadcast_to(idx[:, None, None] + 1, ins.shape)[ok]
    # the vertices and edge midpoints (slivers)
    for k in range(3):
        for t_ in (0.0, 0.5):
            p = tri[:, k] * (1 - t_) + tri[:, (k + 1) % 3] * t_
            x, y = np.floor(p[:, 0]).astype(int), np.floor(p[:, 1]).astype(int)
            ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
            if ids is None:
                g[y[ok], x[ok]] = True
            else:
                empty = g[y[ok], x[ok]] == 0
                g[y[ok][empty], x[ok][empty]] = np.arange(m)[ok][empty] + 1
    return g


def _fill_one(g, tri, lo, sz, w, h, val):
    ys, xs = np.mgrid[0:sz[1], 0:sz[0]]
    cx, cy = lo[0] + xs + 0.5, lo[1] + ys + 0.5
    a, b, c = tri
    d1 = (cx - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (cy - b[1])
    d2 = (cx - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (cy - c[1])
    d3 = (cx - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (cy - a[1])
    ins = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
    X, Y = lo[0] + xs, lo[1] + ys
    ok = ins & (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
    g[Y[ok], X[ok]] = True if val is None else val


def pack(islands, res=1024, gutter_cells=4):
    """islands: list of (UV [n,2] in metres * density, T). Largest common scale at which all fit in the unit square,
    greedy (largest first), bottom-left by FFT collision, 0/90 degree turns. Returns per island (rot90 flag, offset in
    unit UV, scale) and the efficiency."""
    from scipy.signal import fftconvolve
    areas = [0.5 * np.abs(cross2(U_[T[:, 1]] - U_[T[:, 0]], U_[T[:, 2]] - U_[T[:, 0]])).sum() for U_, T in islands]
    tot = sum(areas)
    order = np.argsort(areas)[::-1]

    def attempt(s):
        occ = np.zeros((res, res), bool)
        # the square's own edge: half a gutter
        place = {}
        for i in order:
            U_, T = islands[i]
            best = None
            for rot in (0, 1):
                P = U_ if not rot else np.stack([-U_[:, 1], U_[:, 0]], 1)
                P = P - P.min(0)
                m = outline_mask(P, T, res, s, gutter_cells // 2)
                h, w = m.shape
                if h > res or w > res:
                    continue
                coll = fftconvolve(occ.astype(np.float32), m[::-1, ::-1].astype(np.float32), mode="valid") > 0.5
                ok = np.argwhere(~coll)
                if not len(ok):
                    continue
                # bottom-left: lowest y, then lowest x (in cells)
                j = np.lexsort((ok[:, 1], ok[:, 0]))[0]
                y, x = ok[j]
                key = (y + h, x + w)
                if best is None or key < best[0]:
                    best = (key, rot, y, x, m, P)
            if best is None:
                return None
            _, rot, y, x, m, P = best
            occ[y:y + m.shape[0], x:x + m.shape[1]] |= m
            place[i] = (rot, (x + gutter_cells // 2 + 1) / res, (y + gutter_cells // 2 + 1) / res, s / res)
        return place
    lo, hi = 0.0, res / np.sqrt(tot) * 1.0
    best = None
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        p = attempt(mid)
        if p is None:
            hi = mid
        else:
            lo, best = mid, p
    eff = tot * (lo / res) ** 2
    return best, float(eff)


# ------------------------------------------------------------------------------------------------- build --
def play_guide(zp):
    """Play's cuts by the rules on its own topology (the arm's, the leg's, the foot top's polylines): close redraws
    them (E2: (a) play's edges are twice as long, so a cut drawn on close's lay up to 10 mm off any play edge path,
    and play could not follow it; close follows play's within half its own quad)."""
    isl, left = assign_islands(zp)
    _, info = seams(zp, isl, left)
    return info["_paths"]           # name -> play's vertex path


def build_close(z, guide=None):
    """The close tier's layout from its topology (its cuts along play's: guide). Returns the dict saved in
    base/uv_close.npz."""
    t0 = time.time()
    V, Q = z["V"].astype(np.float64), z["Q"]
    n, nq = len(V), len(Q)
    dens = regions_json()["uv_rules"]["texel_density"]
    isl, left = assign_islands(z)
    dg = quad_diag(V, Q)
    gpts = None if guide is None else {k: guide["V"][v] for k, v in guide["paths"].items()}
    seam, info = seams(z, isl, left, gpts)
    info.pop("_paths")
    cls, cv, nc = corner_classes(Q, n, left, seam)
    # per class: island
    cisl = np.zeros(nc, np.int64)
    cisl[cls[left].ravel()] = np.repeat(isl[left], 4)
    UVc = np.zeros((nc, 2))
    rep = {"islands": {}}
    solved = []
    for ii, nm in enumerate(ISL):
        qs = np.nonzero(left & (isl == ii))[0]
        C = cls[qs]
        vs = np.unique(C)
        loc = -np.ones(nc, np.int64)
        loc[vs] = np.arange(len(vs))
        Cl = loc[C]
        T = quad_tris(Cl, dg[qs])
        P = V[cv[vs]]
        # topology of the cut island: V - E + F
        e = np.unique(np.sort(np.concatenate([Cl[:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)
        chi = len(vs) - len(e) + len(qs)
        nb, _ = connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(vs),) * 2),
                                     directed=False)
        U0 = lscm(P, T, len(vs))
        U1 = arap(P, T, U0, len(vs))
        # orientation (the limb along V, root up; the torso's neck up)
        U1 = orient(nm, U1, cv[vs], z, isl, left, Q, n)
        k = np.sqrt(np.abs(jac_sv(P, T, U1)[1]).sum() / tri_frames(P, T)[1].sum())
        U1 = U1 / k * dens[DENS_KEY[nm]]
        UVc[vs] = U1
        solved.append((nm, vs, T, P))
        rep["islands"][nm] = {"quads": int(len(qs)), "uv_vertices": int(len(vs)), "euler": int(chi),
                              "pieces": int(nb), "density": DENS_KEY[nm]}
    # pack
    place, eff = pack([(UVc[vs], T) for _, vs, T, _ in solved])
    for i, (nm, vs, T, P) in enumerate(solved):
        rot, ox, oy, s = place[i]
        Pp = UVc[vs] if not rot else np.stack([-UVc[vs][:, 1], UVc[vs][:, 0]], 1)
        Pp = Pp - Pp.min(0)
        UVc[vs] = Pp * s + [ox, oy]
        rep["islands"][nm]["turned_90"] = bool(rot)
    rep["packing_efficiency"] = round(eff, 4)
    rep["texel_m_per_unit"] = None
    out = assemble(z, cls, cv, nc, UVc, isl, left)
    out["isl"] = isl
    rep.update(info)
    rep["seam_edges_left"] = int(len(seam))
    rep["solve_s"] = round(time.time() - t0, 2)
    return out, rep


def orient(nm, UVi, verts, z, isl, left, Q, n):
    """Turn an island so its root -> end runs down V (limbs: rim/root at the top; hand/foot: wrist/ankle at the top);
    the torso: neck ring up. Then mirrored if needed so the island's winding is counter-clockwise (no flipped faces)."""
    V = z["V"]
    part = z["part"]
    P = list(z["parts"])
    pv = part[verts]
    if nm.startswith("TORSO"):
        top = np.isin(pv, [P.index("neck")])
        bot = z["vreg"][verts] == 10
    elif nm == "ARM":
        top = pv == P.index("shoulder")
        bot = pv == P.index("forearm")
    elif nm == "LEG":
        top = pv == P.index("thigh")
        bot = pv == P.index("shin")
    else:          # hand/foot: the vertices nearest the wrist/ankle vs the farthest
        X = V[verts]
        c = X.mean(0)
        _, Vt = principal(X)
        s = (X - c) @ Vt[0]
        y = X[:, 1]
        sgn = 1.0 if np.corrcoef(s, y)[0, 1] > 0 else -1.0      # the end nearer the body is the higher one
        s = s * sgn
        top = s > np.percentile(s, 90)
        bot = s < np.percentile(s, 10)
    d = UVi[top].mean(0) - UVi[bot].mean(0)
    a = np.arctan2(d[1], d[0])
    r = np.pi / 2 - a
    R = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
    return UVi @ R.T


def assemble(z, cls, cv, nc, UVc, isl, left):
    """The glb vertex list: our n topology vertices first (each its first class; a right vertex the mirror copy of
    its left's), then every other class, then the right copies of the rest (the center line's right copies too)."""
    Q = z["Q"]
    n, nq = len(z["V"]), len(Q)
    side = z["side"]
    mo = z["mirror_of"]
    mir = np.where(mo >= 0, mo, np.arange(n))          # right -> left (center, left: itself)
    # right quad -> its left mirror quad, and the corner map
    qkey = {tuple(sorted(Q[q].tolist())): q for q in np.nonzero(left)[0]}
    right = np.nonzero(~left)[0]
    lq = np.array([qkey[tuple(sorted(mir[Q[q]].tolist()))] for q in right])
    # class of each right corner: the class of the matching left corner
    rcls = np.zeros((len(right), 4), np.int64)
    for k in range(4):
        m = mir[Q[right, k]]
        hit = Q[lq] == m[:, None]
        assert (hit.sum(1) == 1).all()
        rcls[:, k] = cls[lq][hit]
    # primary class of each topology vertex
    prim = -np.ones(n, np.int64)
    for c in range(nc):                     # each class's vertex: assign the lowest class to its vertex
        v = cv[c]
        if prim[v] < 0:
            prim[v] = c
    lv_mask = side >= 0
    assert (prim[lv_mask] >= 0).all()
    # glb vertices: [0, n): left/center vertex v -> class prim[v] (left copy); right vertex v -> right copy of
    # class prim[mir[v]]. Then the left extras (classes that are no vertex's primary), then the right copies
    # of every class not already a right primary (the center classes and the extras).
    gl_left = -np.ones(nc, np.int64)       # left copy's glb index per class
    gl_right = -np.ones(nc, np.int64)      # right copy's glb index per class
    for v in np.nonzero(lv_mask)[0]:
        gl_left[prim[v]] = v
    rv = np.nonzero(side < 0)[0]
    gl_right[prim[mir[rv]]] = rv
    src = list(range(n))
    nxt = n
    extra_l = np.nonzero(gl_left < 0)[0]
    gl_left[extra_l] = np.arange(nxt, nxt + len(extra_l))
    src += cv[extra_l].tolist()
    nxt += len(extra_l)
    # the right copies still missing: mirror vertex of the class's vertex (center: itself)
    inv_mir = np.arange(n)
    inv_mir[mo[mo >= 0]] = np.nonzero(mo >= 0)[0]     # left -> right
    extra_r = np.nonzero(gl_right < 0)[0]
    gl_right[extra_r] = np.arange(nxt, nxt + len(extra_r))
    src += inv_mir[cv[extra_r]].tolist()
    nxt += len(extra_r)
    src = np.array(src, np.int64)
    UV = np.zeros((nxt, 2))
    UV[gl_left] = UVc
    UV[gl_right] = UVc
    corner = -np.ones((nq, 4), np.int64)
    corner[left] = gl_left[cls[left]]
    corner[right] = gl_right[rcls]
    assert (corner >= 0).all() and (src[corner] == Q).all(), "a corner's glb vertex is not its topology vertex"
    is_right = np.zeros(nxt, bool)
    is_right[gl_right] = True
    T = quad_tris(corner, quad_diag(z["V"].astype(float), Q))
    gUV = UV.copy()
    gUV[:, 1] = 1.0 - gUV[:, 1]                       # glTF: v down (our math frame: y up)
    return {"src": src, "UV": gUV, "uv_math": UV, "corner": corner, "T": T, "is_right": is_right,
            "class_left": gl_left, "class_right": gl_right}


# ----------------------------------------------------------------------------------------------- measure --
def measure(z, out, V=None):
    """The acceptance numbers on a surface (default: the reference topology's V)."""
    V = (z["V"] if V is None else V).astype(np.float64)
    Q, src, UV = z["Q"], out["src"], out["uv_math"]
    left = z["side"][Q].max(1) == 1
    isl = out["isl"]
    dens = regions_json()["uv_rules"]["texel_density"]
    corner = out["corner"]
    P = V[src]
    res = {"islands": {}, "regions": {}}
    Tl = quad_tris(corner[left], quad_diag(z["V"].astype(float), Q)[left])
    il = np.r_[isl[left], isl[left]]
    rg = np.r_[z["qreg"][left], z["qreg"][left]]
    s, sa, area = jac_sv(P, Tl, UV)
    k_body = None
    for ii, nm in enumerate(ISL):
        m = il == ii
        k = np.sqrt(np.abs(sa[m]).sum() / area[m].sum())
        sv = s[m] / k
        dist = np.maximum(sv[:, 0], 1 / np.maximum(sv[:, 1], 1e-9))
        res["islands"][nm] = {"stretch_p95": round(float(np.percentile(dist, 95)), 4),
                              "stretch_p99": round(float(np.percentile(dist, 99)), 4),
                              "stretch_max": round(float(dist.max()), 3),
                              "flipped": int((sa[m] <= 0).sum()), "k": float(k)}
        if nm.startswith("TORSO"):
            k_body = k
    for r in np.unique(rg):
        m = rg == r
        k = np.sqrt(np.abs(sa[m]).sum() / area[m].sum())
        name = [x["name"] for x in regions_json()["regions"] if x["id"] == r][0]
        key = {9: "hands", 13: "feet"}.get(int(r), "body")
        res["regions"][f"{r}:{name}"] = {"density_ratio": round(float(k / k_body), 4), "target": dens[key],
                                         "off_pct": round(float(abs(k / k_body / dens[key] - 1) * 100), 2)}
    # overlaps (the left half only: the right overlaps it by design) and flips on both halves
    Ta = out["T"]
    sa_all = 0.5 * cross2(UV[Ta[:, 1]] - UV[Ta[:, 0]], UV[Ta[:, 2]] - UV[Ta[:, 0]])
    rmask = out["is_right"][Ta].all(1)
    res["flipped_left"] = int((sa_all[~rmask] <= 0).sum())
    res["mirrored_right_winding"] = int((sa_all[rmask] < 0).sum())
    res["right_tris"] = int(rmask.sum())
    g = fill_tris(UV * 4096, Tl, 4096, 4096, ids=np.arange(len(Tl)))
    # an overlap: two left triangles sharing a cell centre test (count via a second fill in reverse order)
    g2 = fill_tris_rev(UV * 4096, Tl, 4096, 4096)
    ov = (g > 0) & (g2 > 0) & (g != g2)
    # neighbouring triangles share edges: a cell on a shared edge is not an overlap; count cells whose two triangles
    # share no vertex
    ys, xs = np.nonzero(ov)
    a, b = g[ys, xs] - 1, g2[ys, xs] - 1
    sharev = (Tl[a][:, :, None] == Tl[b][:, None, :]).any((1, 2))
    res["overlap_cells_4k"] = int((~sharev).sum())
    res["coverage"] = round(float((g > 0).mean()), 4)
    return res


def fill_tris_rev(P, T, w, h):
    g = fill_tris(P, T[::-1], w, h, ids=np.arange(len(T)))
    out = np.where(g > 0, len(T) - g + 1, 0)
    return out


# ---------------------------------------------------------------------------------------------- play tier --
GROUP = {4: 0, 5: 0, 6: 0, 10: 0, 7: 1, 8: 1, 11: 2, 12: 2, 9: 3, 13: 4}     # the region groups islands never cross


def close_tris(zc, oc, quads):
    """Close's triangles over its glb vertices for the given (left) quads, their positions on close's reference
    surface, and the triangle -> quad map."""
    dg = quad_diag(zc["V"].astype(np.float64), zc["Q"])
    T = quad_tris(oc["corner"][quads], dg[quads])
    return T, zc["V"].astype(np.float64)[oc["src"]], np.r_[quads, quads]


def closest_uvsafe(P, T, tree, X, k=24, uv=None, target=None, tol=None):
    """The closest point of each X on the triangles (P, T) among the k nearest by centroid: (tri, bary on the
    triangle, distance). With a target UV, only triangles whose UV centroid lies within tol of it count (a point by
    a cut takes its own side's copy); none: the one nearest in UV (distance 1e3 + its UV miss)."""
    import surfdist
    _, cand = tree.query(X, k=min(k, len(T)))
    best = np.full(len(X), np.inf)
    bt = np.zeros(len(X), np.int64)
    bq = np.zeros_like(X)
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q = surfdist.closest_on_tris(X, P[T[t, 0]], P[T[t, 1]], P[T[t, 2]])
        d = np.linalg.norm(X - q, axis=1)
        if target is not None:
            duv = np.linalg.norm(uv[T[t]].mean(1) - target, axis=1)
            d = np.where(duv <= tol, d, 1e3 + duv)
        m = d < best
        best[m], bt[m], bq[m] = d[m], t[m], q[m]
    w = np.clip(bary(bq, P[T[bt, 0]], P[T[bt, 1]], P[T[bt, 2]]), 0, None)
    w /= w.sum(1, keepdims=True)
    return bt, w, best


def play_islands(zp, zc, oc):
    """Play's islands FROM CLOSE: each left quad takes the close island most of it lies on (9 points over the quad,
    each on close's surface within the same region group: the structural rings stay play's own), stray pieces then
    joined to their neighbours. (a) Play's own rules drew its splits up to 31 mm off close's (the palm | back on its
    coarse half-height), and a texel can only serve both tiers where both put it on the same island."""
    from scipy.spatial import cKDTree
    V, Q = zp["V"].astype(np.float64), zp["Q"]
    left = zp["side"][Q].max(1) == 1
    leftc = zc["side"][zc["Q"]].max(1) == 1
    gp = np.array([GROUP.get(int(r), -1) for r in zp["qreg"]])
    gc = np.array([GROUP.get(int(r), -1) for r in zc["qreg"]])
    isl = -np.ones(len(Q), np.int64)
    C = V[Q].mean(1)
    S = [C] + [C + 0.6 * (V[Q[:, k]] - C) for k in range(4)] + \
        [C + 0.6 * (0.5 * (V[Q[:, k]] + V[Q[:, (k + 1) % 4]]) - C) for k in range(4)]
    for g in range(5):
        qc = np.nonzero(leftc & (gc == g))[0]
        T, P, tq = close_tris(zc, oc, qc)
        tree = cKDTree(P[T].mean(1))
        qp = np.nonzero(left & (gp == g))[0]
        votes = np.stack([oc["isl"][tq[closest_uvsafe(P, T, tree, s[qp])[0]]] for s in S], 1)
        lab = votes[:, 0].copy()
        for i in range(len(qp)):
            u, c = np.unique(votes[i], return_counts=True)
            if c.max() * 2 > len(S):
                lab[i] = u[np.argmax(c)]
        isl[qp] = lab
    assert (isl[left] >= 0).all(), "a play quad with no island"
    # stray pieces (each island one piece): to the label most of their neighbours carry
    n = len(V)
    pairs, _ = quad_adjacency(Q, n, left)
    for _ in range(4):
        moved = 0
        for ii in np.unique(isl[left]):
            m = left & (isl == ii)
            qi = np.nonzero(m)[0]
            loc = -np.ones(len(Q), np.int64)
            loc[qi] = np.arange(len(qi))
            pm = m[pairs[:, 0]] & m[pairs[:, 1]]
            A = sp.coo_matrix((np.ones(pm.sum()), (loc[pairs[pm, 0]], loc[pairs[pm, 1]])), shape=(len(qi),) * 2)
            nc_, cc = connected_components(A, directed=False)
            if nc_ < 2:
                continue
            big = np.argmax(np.bincount(cc))
            for c_ in range(nc_):
                if c_ == big:
                    continue
                piece = np.zeros(len(Q), bool)
                piece[qi[cc == c_]] = True
                ea = piece[pairs[:, 0]] & ~piece[pairs[:, 1]]
                eb = piece[pairs[:, 1]] & ~piece[pairs[:, 0]]
                nb = np.r_[isl[pairs[ea, 1]], isl[pairs[eb, 0]]]
                if len(nb):
                    u, c = np.unique(nb, return_counts=True)
                    isl[piece] = u[np.argmax(c)]
                    moved += 1
        if not moved:
            break
    return isl, left


def close_cuts(zc, oc):
    """Close's cuts inside an island (the arm's, the leg's, the foot top's), read from its saved layout: the edges two
    left quads of one island share whose corners take different UV vertices. Per island: the cut edges (topology
    ids) and the cut's two ends."""
    Qc, corner = zc["Q"], oc["corner"]
    n = len(zc["V"])
    leftc = zc["side"][Qc].max(1) == 1
    rec = {}
    for q in np.nonzero(leftc)[0]:
        for k in range(4):
            a, b = int(Qc[q, k]), int(Qc[q, (k + 1) % 4])
            key = (min(a, b), max(a, b))
            ga, gb = int(corner[q, k]), int(corner[q, (k + 1) % 4])
            rec.setdefault(key, []).append((q, {a: ga, b: gb}))
    out = {}
    for key, lst in rec.items():
        if len(lst) != 2:
            continue
        (q1, m1), (q2, m2) = lst
        if oc["isl"][q1] == oc["isl"][q2] and m1 != m2:
            out.setdefault(int(oc["isl"][q1]), []).append(key)
    res = {}
    for ii, e in out.items():
        e = np.array(e)
        u, c = np.unique(e, return_counts=True)
        res[ii] = {"edges": e, "ends": u[c == 1]}
    return res


def play_seams(zp, zc, oc, isl, left, paths):
    """Play's seams: its island borders, and its own cuts (paths: play_guide's, by the rules on play), which close's
    cuts were drawn along. Reported: how far each lies from close's cut (the farthest of each edge's ends and
    middle)."""
    from scipy.spatial import cKDTree
    V, Q = zp["V"].astype(np.float64), zp["Q"]
    n = len(V)
    K = quad_edge_keys(Q, n)
    Kf = K.ravel()
    owner = np.repeat(np.arange(len(Q)), 4)
    o = np.argsort(Kf, kind="stable")
    Ks, ow = Kf[o], owner[o]
    same = Ks[1:] == Ks[:-1]
    a, b = ow[:-1][same], ow[1:][same]
    both = left[a] & left[b]
    seam = set(Ks[:-1][same][both & (isl[a] != isl[b])].tolist())
    Vc = zc["V"].astype(np.float64)
    info = {"cuts": {}}
    cuts = close_cuts(zc, oc)
    for name, nm in (("arm", "ARM"), ("leg", "LEG"), ("foot_top", "FOOT_TOP")):
        if name not in paths:
            continue
        path = np.asarray(paths[name])
        seam |= set(edge_key(path[:-1], path[1:], n).tolist())
        cut = cuts.get(ISL.index(nm))
        if cut is None:
            info["cuts"][nm] = {"edges": int(len(path) - 1), "close_cut": "none"}
            continue
        t_ = np.linspace(0, 1, 9)[:, None, None]
        tree = cKDTree((Vc[cut["edges"][:, 0]][None] * (1 - t_) + Vc[cut["edges"][:, 1]][None] * t_).reshape(-1, 3))
        dd = np.max([tree.query(V[path[:-1]] * (1 - s_) + V[path[1:]] * s_)[0] for s_ in (0.0, 0.5, 1.0)], 0)
        info["cuts"][nm] = {"edges": int(len(path) - 1),
                            "off_close_cut_mm_p95": round(float(np.percentile(dd, 95)) * 1e3, 2),
                            "off_close_cut_mm_max": round(float(dd.max()) * 1e3, 2)}
    return seam, info


def build_play(zp, zc, oc, paths=None):
    """Play's layout carried from close, so ONE texture set serves both tiers: its islands from close's (play_islands),
    its cuts redrawn on close's (play_seams), and each of its UV vertices close's UV at its closest point on close's
    island, on its own side of a cut (the copy's faces' UVs pick the side), on close's triangles (clamped: a play
    seam a few mm off close's takes close's border texels, never a gutter's or a neighbour island's)."""
    from scipy.spatial import cKDTree
    t0 = time.time()
    V, Q = zp["V"].astype(np.float64), zp["Q"]
    n = len(V)
    isl, left = play_islands(zp, zc, oc)
    seam, info = play_seams(zp, zc, oc, isl, left, play_guide(zp) if paths is None else paths)
    cls, cv, nc = corner_classes(Q, n, left, seam)
    leftc = zc["side"][zc["Q"]].max(1) == 1
    UVc = np.zeros((nc, 2))
    uv = oc["uv_math"]
    rep = {"islands": {}, "carried_from": "close"}
    for ii, nm in enumerate(ISL):
        qc = np.nonzero(leftc & (oc["isl"] == ii))[0]
        qp = np.nonzero(left & (isl == ii))[0]
        if not len(qp):
            continue
        T, P, _ = close_tris(zc, oc, qc)
        tree = cKDTree(P[T].mean(1))
        k_isl = np.sqrt(np.abs(jac_sv(P, T, uv)[1]).sum() / tri_frames(P, T)[1].sum())     # UV units per metre
        # each play face's middle on close's island (a face's middle sits inside its own side of a cut)
        tf, wf, _ = closest_uvsafe(P, T, tree, V[Q[qp]].mean(1))
        uvf = (wf[:, :, None] * uv[T[tf]]).sum(1)
        acc = np.zeros((nc, 2))
        cnt = np.zeros(nc)
        for k in range(4):
            np.add.at(acc, cls[qp, k], uvf)
            np.add.at(cnt, cls[qp, k], 1)
        cs = np.unique(cls[qp])
        tgt = acc[cs] / cnt[cs, None]
        tv, wv, dv = closest_uvsafe(P, T, tree, V[cv[cs]], uv=uv, target=tgt, tol=0.02 * k_isl)
        UVc[cs] = (wv[:, :, None] * uv[T[tv]]).sum(1)
        # then relaxed on play's own surface, held to it by a spring (lam 1: 0 flips against 10 on the bare
        # projection; at 0.1 / 0.01 the layout drifts 1.6 / 2.5 px p95 from close's; the seams held harder (30)
        # kept the folds' stretch: measured)
        loc = -np.ones(nc, np.int64)
        loc[cs] = np.arange(len(cs))
        Tp = quad_tris(loc[cls[qp]], quad_diag(V, Q)[qp])
        UVc[cs] = arap_fit(V[cv[cs]], Tp, UVc[cs], k_isl, 1.0)
        rep["islands"][nm] = {"quads": int(len(qp)), "uv_vertices": int(len(cs)),
                              "off_close_mm_p95": round(float(np.percentile(np.minimum(dv, 1e3), 95)) * 1e3, 2),
                              "side_fallbacks": int((dv >= 1e3).sum())}
    out = assemble(zp, cls, cv, nc, UVc, isl, left)
    out["isl"] = isl
    rep.update(info)
    rep["solve_s"] = round(time.time() - t0, 2)
    return out, rep


def agreement(zp, op, zc, oc, size=TEX, per_tri=3, seed=3):
    """One texture set, both tiers: points on play's left triangles (random, per_tri each), play's UV there against
    close's UV at the point's closest place on close's same island (its own side: within 2 cm in UV of play's), in
    2k texels; and the share of those play UVs that fall off close's islands (into a gutter)."""
    from scipy.spatial import cKDTree
    V, Q = zp["V"].astype(np.float64), zp["Q"]
    left = zp["side"][Q].max(1) == 1
    leftc = zc["side"][zc["Q"]].max(1) == 1
    dg = quad_diag(V, Q)
    rng = np.random.default_rng(seed)
    uvp, uvq = op["uv_math"], oc["uv_math"]
    cover = fill_tris(uvq * size, quad_tris(oc["corner"][leftc], quad_diag(zc["V"].astype(np.float64), zc["Q"])[leftc]),
                      size, size)
    from scipy import ndimage
    errs, off, tot, out, offd = [], 0, 0, {}, []
    for ii, nm in enumerate(ISL):
        qp = np.nonzero(left & (op["isl"] == ii))[0]
        if not len(qp):
            continue
        Tp = quad_tris(op["corner"][qp], dg[qp])
        Pp = V[op["src"]]
        r = rng.random((len(Tp), per_tri, 2))
        r = np.where(r.sum(2, keepdims=True) > 1, 1 - r, r)
        wb = np.stack([1 - r[..., 0] - r[..., 1], r[..., 0], r[..., 1]], 2)
        X = np.einsum("tsk,tkd->tsd", wb, Pp[Tp]).reshape(-1, 3)
        Up = np.einsum("tsk,tkd->tsd", wb, uvp[Tp]).reshape(-1, 2)
        qc = np.nonzero(leftc & (oc["isl"] == ii))[0]
        T, P, _ = close_tris(zc, oc, qc)
        tree = cKDTree(P[T].mean(1))
        k_isl = np.sqrt(np.abs(jac_sv(P, T, uvq)[1]).sum() / tri_frames(P, T)[1].sum())
        t, w, _ = closest_uvsafe(P, T, tree, X, uv=uvq, target=Up, tol=0.02 * k_isl)
        Uc = (w[:, :, None] * uvq[T[t]]).sum(1)
        e = np.linalg.norm(Up - Uc, axis=1) * size
        px = np.clip((Up * size).astype(int), 0, size - 1)
        o = ~cover[px[:, 1], px[:, 0]]
        # how far off its own island (texels): the gutter takes the nearest island texel, so within half a gutter
        # (4 px at 2k) a play texel still reads its own island's border
        lo = np.maximum(px.min(0) - 16, 0)
        hi = np.minimum(px.max(0) + 17, size)
        own = fill_tris(uvq * size - lo, T, int(hi[0] - lo[0]), int(hi[1] - lo[1]))
        dist = ndimage.distance_transform_edt(~own)
        od = dist[px[:, 1] - lo[1], px[:, 0] - lo[0]]
        out[nm] = {"px_p95": round(float(np.percentile(e, 95)), 2), "px_max": round(float(e.max()), 2),
                   "off_islands_pct": round(float(o.mean() * 100), 3), "off_own_px_max": round(float(od.max()), 2)}
        offd.append(od)
        errs.append(e)
        off += int(o.sum())
        tot += len(e)
    e = np.concatenate(errs)
    return {"px_p50": round(float(np.percentile(e, 50)), 3), "px_p95": round(float(np.percentile(e, 95)), 2),
            "px_p99": round(float(np.percentile(e, 99)), 2), "px_max": round(float(e.max()), 2),
            "off_islands_pct": round(off / tot * 100, 3),
            "off_own_px_p99": round(float(np.percentile(np.concatenate(offd), 99)), 2),
            "off_own_px_max": round(float(np.concatenate(offd).max()), 2), "islands": out}


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.stack([1 - v - w, v, w], 1)


def region_of_quads(z, isl):
    """The region id map's table (L1's 'covers'), per quad, from our topology's qreg: (1) the neck's quads on the
    back island are the nape: torso_back (6); (2) the front island's trunk quads at or above the breast hole's top
    row (the highest trunk row touching a breast-part quad) are the decolletage: neck_decolletage (4). The right half
    takes its mirror's."""
    Q = z["Q"]
    r = z["qreg"].copy()
    P = list(z["parts"])
    left = z["side"][Q].max(1) == 1
    part_q = z["qpart"]
    back = left & (isl == ISL.index("TORSO_BACK")) & (part_q == P.index("neck"))
    r[back] = 6
    tr = z["part"] == P.index("trunk")
    bq = np.isin(np.arange(len(Q)), np.nonzero(part_q == P.index("breast"))[0])
    touch = np.unique(Q[bq])
    top = z["ring"][touch[tr[touch]]].max()
    front = left & (isl == ISL.index("TORSO_FRONT")) & (part_q == P.index("trunk")) & (z["ring"][Q].min(1) >= top)
    r[front] = 4
    mo = z["mirror_of"]
    mir = np.where(mo >= 0, mo, np.arange(len(mo)))
    key = {tuple(sorted(Q[q].tolist())): q for q in np.nonzero(left)[0]}
    for q in np.nonzero(~left)[0]:
        r[q] = r[key[tuple(sorted(mir[Q[q]].tolist()))]]
    return r


# ------------------------------------------------------------------------------------------------- files --
KEYS = ["src", "UV", "uv_math", "corner", "T", "is_right", "isl"]


def path(tier):
    return os.path.join(HERE, "base", f"uv_{tier}.npz")


def save(tier, z, out, rep):
    np.savez_compressed(path(tier), topology=topo_sha(z), version=VERSION, report=json.dumps(rep, default=float),
                        **{k: out[k] for k in KEYS})


def load(tier, z):
    """The tier's layout (base/uv_<tier>.npz), asserted to be for this topology."""
    r = np.load(path(tier))
    assert str(r["topology"]) == topo_sha(z), ("UVs for another topology: run tools/body/topo_uv.py", tier)
    return {k: r[k] for k in KEYS}, json.loads(str(r["report"]))


def run(tiers=("close", "play")):
    zc = dict(np.load(os.path.join(HERE, "out", "topo", "close.npz")), _tier="close")
    allrep = {}
    zp = dict(np.load(os.path.join(HERE, "out", "topo", "play.npz")), _tier="play")
    if "close" in tiers:
        oc, rc = build_close(zc, {"V": zp["V"].astype(np.float64), "paths": play_guide(zp)})
        rc["measure"] = measure(zc, oc)
        save("close", zc, oc, rc)
        allrep["close"] = rc
    else:                       # play alone: carried from the saved close layout
        oc, _ = load("close", zc)
    if "play" in tiers:
        op, rp = build_play(zp, zc, oc)
        rp["measure"] = measure(zp, op)
        rp["agreement"] = agreement(zp, op, zc, oc)
        save("play", zp, op, rp)
        allrep["play"] = rp
    return allrep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", default="close,play")
    a = ap.parse_args()
    rep = run(tuple(a.tiers.split(",")))
    print(json.dumps(rep, indent=1, default=float))


if __name__ == "__main__":
    main()
