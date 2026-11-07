#!/usr/bin/env python
"""P1 B2a: the base build on OUR topology, both tiers, no Blender, no MakeHuman at build time. docs/team/body.md P1.

    python tools/body/build_topo.py tools/body/specs/base_woman.json <out_dir> [--tiers close,play] [--no-correctives]

Writes <out>/body.glb + <out>/rig.json (close), <out>/play.glb + <out>/play_rig.json (play), <out>/build.json (counts,
timings, checks) and <out>/stage/<tier>.npz (each stage's arrays). Check it:
    python tools/body/check.py <out>/body.glb --ref godot/art/people/heroine.glb --rig <out>/rig.json --poser lbs
           --same-head --play <out>/play.glb --out <dir>
Why a new file and not build.py --topo: build.py's path (MakeHuman in Blender, subdivided) stays as it is because it
IS the reference topo_corr.py replays (Reference()); this one shares none of its stages but stage_export's writer.
Stages (each a function, no hand steps):
  1 base      our reference topology (out/topo/<tier>.npz, topo_build.py) with the spec's "sliders" through
              OurSliders (base/sliders_<tier>.npz): the slider body joined under the head as forms.join does (its
              mean move at the neck under SPLIT taken off; none within 1.5 cm of SPLIT, all of it 6 cm lower), then
              the spec's "stance" (forms.stance's rule: a pitch about the neck's middle and a move, eased in the same
              way); spec "join": "ring" eases both by the distance to the seam as well (join_weight: a body with no
              forms copy); "forms" (v1's residual, per MakeHuman point) is NOT applied: ours are "forms_topo" (2b);
  2 place     her shipped head, baked to its world rest (headbake.py: A's +7% Head scale and off-rest bind folded into
              the meshes); our open neck ring (94 points) IS the baked head ring by construction (topo.head_ring
              uses the same headbake.rest_world; asserted to 1e-6 m), so the snap, eased harmonically into the body
              over `fit_ease_m` under SPLIT (stages.harmonic on our quads' graph Laplacian), moves nothing (P1 N);
  2b forms    the spec's "forms_topo" (a path pattern with {tier}: wrap_topo.py's R per our vertex, 0 on the ring)
              added to the placed body; the npz names our topology's hash (stage_forms asserts it);
  3 skeleton  tools/body/skeleton.json placed from OUR vertices alone (skeleton.place_skeleton_ours,
              base/landmarks.json "tiers"["close"]) on the placed close body; the play tier takes the close tier's
              (P1 R2: one skeleton for both tiers; stage/close_skeleton.json when play is built alone; build.json
              "skeleton_play_vs_close" asserted 0, "skeleton_vs_published" the close against the published body.glb);
  4 weights   weights_topo.py (its VERSION in the glb extras; v1: seeds by rule + a bounded biharmonic fill, then
              weights.py's rules 2 and 4-10), and the head's: its ring = the body ring's weights, Head above, harmonic between;
  5 export    glbwrite.py: our skeleton (no rest scale, plain binds), the body (our quads as triangle pairs, normals
              from our faces, the ring's from the head so the seam lights as one; TEXCOORD_0 a placeholder front
              projection: UVs are a later step), the head meshes with the bake and our weights written over A's; and
              rig.json (stages.write_rig: the poser's drivers, base_drive.json).
  6 correctives  correctives.py on each tier's own export (tools/body/correctives.json: per joint and key pose a
              smooth-skin solve with the crease's contact, shapes stored before skinning, weight laws into the tier's
              rig "correctives" for rig_drive.py); solved on play's own mesh, not carried from close: the solve is
              the same command on any mesh, and play's shapes then meet play's own posed surface exactly (a carried
              shape inherits close's contacts on a coarser skin). --no-correctives skips it.
No subdivision: the topology is the tier. Derivation: (a) the game's need (one build command per tier on our own
topology, every input ours but the CC0 reference surface the topology and sliders were derived from); (c) the head
inherited from A (approved), baked.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import headbake  # noqa: E402
import headmatch as hm  # noqa: E402
import stages as st  # noqa: E402
import weights_topo as wtp  # noqa: E402
from gl import Glb, weld  # noqa: E402
from sliders import OurSliders, load_spec, head_move as sliders_head_move  # noqa: E402

HEADS = ["HeroineEyes", "HeroineHead", "HeroineLashes", "HeroineTeeth", "HeroineTongue"]
HOLD_M, EASE_M = 0.015, 0.06          # forms.py's join
GLB = {"close": ("body.glb", "rig.json"), "play": ("play.glb", "play_rig.json")}


def s01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


_SPLIT_DROP = []


def split_drop():
    """(c, P1 N) SPLIT carried with the head: headmatch.s_split was drawn on the head's stored ring; the head is built
    at its baked world rest (25 mm lower), so the plane moves down by the baked ring's mean depth under it (25.9 mm;
    the ring's points then sit -7.8..+4.4 mm about it, inside HOLD_M), and every join/hold under SPLIT keeps its
    meaning against the ring the body actually meets."""
    if not _SPLIT_DROP:
        import topo
        with open(os.path.join(HERE, "loopplan.json")) as f:
            r = json.load(f)["reference"]
        R = topo.head_ring(os.path.join(REPO, r["head"]), r["head_mesh"])
        _SPLIT_DROP.append(float(np.mean(-hm.s_split(hm.to_blender(R)))))
    return _SPLIT_DROP[0]


def split_depth(V):
    """How far under SPLIT (headmatch.s_split, carried down with the head: split_drop) each point is, m, positive
    below; V in glTF, our placed frame."""
    return -hm.s_split(hm.to_blender(V)) - split_drop()


def boundary_ring(Q, n):
    e = np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return np.unique(u[c == 1])


JOINS = ("split", "ring")


def join_weight(spec, Q, V0):
    """Stage 1's join: how much of the sliders' and the stance's move each point takes (0 at the head's seam, 1 well
    under it). "split" (the default; forms.py's join): by the depth under SPLIT, none within HOLD_M, all of it EASE_M
    lower. "ring" (spec "join": "ring"): the larger of that and the same ease on the point's distance to our open neck
    ring (the seam itself). Why: SPLIT's depth holds every point near the plane, and the plane runs level with the
    ring's high back, so the trapezius and the shoulder's top (2-12 cm out from the ring, 0.4-2.5 cm under SPLIT) kept
    the reference's shape, the shrug of MakeHuman's short neck under her head: the stance's 41 mm drop reached the arm
    but not the shoulder's top (jw 0.00-0.05 at x 6-18 cm), a 26-45 mm yoke over her ek2 body (5 Nov, arms down). A
    body with a forms copy (her_topo) was reshaped there by its residual, so "split" stays its join, byte for byte."""
    mode = spec.get("join", "split")
    assert mode in JOINS, ("join", mode)
    jw = s01((split_depth(V0) - HOLD_M) / EASE_M)
    if mode == "ring":
        ring = boundary_ring(Q, len(V0))
        dr, _ = cKDTree(V0[ring]).query(V0)
        jw = np.maximum(jw, s01((dr - HOLD_M) / EASE_M))
    return jw


# ------------------------------------------------------------------------------------------------- 1 base --
def load_tier(tier):
    """Our topology and its slider bake for a tier (stage 1's inputs; the fit, wrap_topo.py, holds them)."""
    return (dict(np.load(os.path.join(HERE, "out", "topo", f"{tier}.npz"))),
            OurSliders(os.path.join(HERE, "base", f"sliders_{tier}.npz")))


def stage_base(spec, tier, rep, pre=None):
    z, sl = pre or load_tier(tier)
    for n, f in (spec.get("target_files") or {}).items():
        # a trial's target (a scratch spec names it; the designed slider's own "file" otherwise), e.g. her_a_target.py --out-dir
        sl.designed[n] = {**sl.designed[n], "file": f}
    V0 = sl.V0.copy()
    assert np.abs(V0 - z["V"]).max() < 1e-6, "the sliders' reference is not this topology"
    info = {"topology": f"tools/body/out/topo/{tier}.npz", "vertices": int(len(V0)), "quads": int(len(z["Q"]))}
    V = V0.copy()
    jw = join_weight(spec, z["Q"], V0)[:, None]
    if spec.get("join", "split") != "split":
        info["join"] = spec["join"]
    sliders = {k: v for k, v in spec.get("sliders", {}).items() if v}
    if sliders:
        unknown = sorted(set(sliders) - set(sl.names))
        assert not unknown, ("sliders not in the bake", unknown)
        d = sl.evaluate(sliders, post=False) - V0
        dep = split_depth(V0)
        t = d[(dep > 0) & (dep < 0.04)].mean(0)
        t[0] = 0.0
        V = V0 + jw * (d - t)
        info["sliders"] = sliders
        info["neck_shift_m"] = [round(float(x), 5) for x in t]
    if spec.get("stance"):
        s_ = spec["stance"]
        dep = split_depth(V0)
        c = V0[(dep > 0) & (dep < 0.04)].mean(0)
        c[0] = 0.0
        a = np.radians(s_.get("pitch_deg", 0.0))
        # forms.stance's turn about MakeHuman's x (z up, front -y) and move, here in our placed frame's Blender axes
        # (the head's placement turn, a few degrees, is not undone: her.json's stance is v1's fit, refit in step C)
        Rb = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
        B = hm.to_blender(V)
        cb = hm.to_blender(c[None])[0]
        to = (B - cb) @ Rb.T + cb + np.asarray(s_.get("move_m", [0, 0, 0]), float)
        V = V + jw * (hm.to_gltf(to) - V)
        info["stance"] = s_
    post = sl.post_delta(sliders) if sliders else None
    if post is not None and np.abs(post).max() > 0:
        # P1 R1: the form library's post-join fields (the neck: its length lifts the ring with the head, head_move)
        V = V + post
        info["post_join"] = sorted(n for n in sliders if sl.designed.get(n, {}).get("post_join"))
        from sliders import relax
        V = relax(sl, V, sliders)
        # R1b round 3: neck_form.fair's "after_join" regions (a fairing is not a linear field, so post_delta cannot
        # carry it): the side of the neck the join holds, faired on the joined body
        import neck_form
        V = neck_form.after_join(sl, V, sliders)
        info["post_join_ring_move_mm"] = [round(float(x) * 1e3, 2) for x in post[boundary_ring(z["Q"], len(V0))].mean(0)]
    if spec.get("forms"):
        info["forms"] = f"NOT applied ({spec['forms']}: per MakeHuman point; ours are \"forms_topo\", stage 2b)"
    rep["base"] = info
    return z, V


# ------------------------------------------------------------------------------------------------ 2 place --
def stage_place(spec, z, V, A, baked, rep):
    Q = z["Q"]
    ring = boundary_ring(Q, len(V))
    # our ring IS the baked head's ring (topo.head_ring: the same headbake.rest_world), so the lookup is on the baked
    # rest; the move left is the slider/stance join's at the ring (0 for both: held over HOLD_M under SPLIT)
    d, hv = cKDTree(baked["HeroineHead"]["P"]).query(V[ring])
    assert len(ring) == 94 and d.max() < 1e-6, ("the open ring is not the head's", len(ring), d.max())
    assert len(np.unique(hv)) == 94, "the ring's head points are not one to one"
    tgt = baked["HeroineHead"]["P"][hv]
    D = tgt - V[ring]
    L = st.laplacian(Q, len(V))
    zone = split_depth(V) < spec["fit_ease_m"]
    zone[ring] = False
    V = V + st.harmonic(L, ring, D, np.where(zone)[0])
    V[ring] = tgt
    V = seam_g1(spec, Q, V, ring, hv, baked["HeroineHead"]["P"], A.mesh("HeroineHead").T, L, rep)
    rep["place"] = {"ring_points": int(len(ring)), "ring_move_max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 2),
                    "ring_move_mean_mm": round(float(np.linalg.norm(D, axis=1).mean()) * 1e3, 2),
                    "ease_points": int(zone.sum()), "fit_ease_m": spec["fit_ease_m"],
                    "feet_lowest_m": round(float(V[:, 1].min()), 4)}
    return V, ring, hv


def biharmonic(L, known, vals, free):
    """Values on `free` points biharmonic (L^2 x = 0) given `vals` on `known` and 0 on every other point (seam_g1)."""
    import scipy.sparse.linalg as spl
    M = (L @ L).tocsr()
    x = np.zeros((L.shape[0], vals.shape[1]))
    x[known] = vals
    solve = spl.factorized(M[free][:, free].tocsc())
    rhs = -(M[free] @ x)
    x[free] = np.stack([solve(np.ascontiguousarray(rhs[:, k])) for k in range(vals.shape[1])], 1)
    return x


def seam_g1(spec, Q, V, ring, hv, HP, HT, L, rep):
    """P1 R1: the throat seam as ONE surface (spec "seam": {"rows_m": d}): the body leaves the head's ring along the
    head's own surface direction (G1), so no crease line runs round the throat under a cel terminator. Each ring
    point's way out of the head (its position less the mean of its head neighbours off the ring: the head surface's
    direction across the seam) carries the body's first row (each point set at its own distance from its ring
    neighbours along that direction), and that move eases harmonically to 0 at d from the ring. Measured by the seam
    angle (each ring point's body normal against its head normal; formrules "seam"): her_sliders 36.5 deg mean,
    her_topo (A's copy) 6.8."""
    s = spec.get("seam")
    if not s:
        return V
    w = np.asarray(weld(HP, 1e-7))            # the head's UV-split copies as one point
    hs = set(int(w[h]) for h in hv)
    he = w[np.concatenate([HT[:, [0, 1]], HT[:, [1, 2]], HT[:, [2, 0]]])]
    first = {}
    for i_, r_ in enumerate(w):
        first.setdefault(int(r_), i_)
    nb = {}
    for a_, b_ in he:
        for x, y in ((int(a_), int(b_)), (int(b_), int(a_))):
            if x in hs and y not in hs:
                nb.setdefault(x, set()).add(y)
    tdir = np.zeros((len(ring), 3))
    for i, h in enumerate(hv):
        inner = [first[k] for k in sorted(nb.get(int(w[h]), ()))]
        if not inner:                         # a corner point whose triangles touch only the ring: its ring
            ring_nb = {int(y) for x, y in he if int(x) == int(w[h]) and int(y) in hs}   # neighbours' way out
            inner = [first[k] for r_ in sorted(ring_nb) for k in sorted(nb.get(r_, ()))]
        t = HP[int(h)] - HP[inner].mean(0)
        tdir[i] = t / max(np.linalg.norm(t), 1e-12)
    # the head's ring rows are uneven (corner triangles): each way out is smoothed along the ring with its two ring
    # neighbours, twice, and kept tangent to the body side (it must point away from the head: down the neck)
    rv = V[ring]
    nbr = cKDTree(rv).query(rv, k=3)[1][:, 1:]
    for _ in range(2):
        tdir = 0.5 * tdir + 0.25 * (tdir[nbr[:, 0]] + tdir[nbr[:, 1]])
        tdir /= np.maximum(np.linalg.norm(tdir, axis=1, keepdims=True), 1e-12)
    rep.setdefault("seam_dirs", {})["min_down"] = round(float(-tdir[:, 1].max()), 3)
    pos = {int(r): i for i, r in enumerate(ring)}
    be = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    rows = {}
    for a_, b_ in be:
        for x, y in ((int(a_), int(b_)), (int(b_), int(a_))):
            if x in pos and y not in pos:
                rows.setdefault(y, set()).add(x)
    F = np.array(sorted(rows))
    tgt = np.zeros((len(F), 3))
    for k, f in enumerate(F):
        tgt[k] = np.mean([V[r] + np.linalg.norm(V[f] - V[r]) * tdir[pos[r]] for r in rows[f]], 0)
    Df = (tgt - V[F]) * float(s.get("k", 1.0))
    dr, _ = cKDTree(V[ring]).query(V)
    zone = dr < float(s["rows_m"])
    zone[ring] = False
    zone[F] = False
    known = np.concatenate([ring, F])
    vals = np.concatenate([np.zeros((len(ring), 3)), Df])
    q5 = lambda u: u ** 3 * (10 - 15 * u + 6 * u * u)         # C2 quintic ramp 0 -> 1
    # R1b: the front of the ring (full within front_deg[0] deg of the front about the ring's middle, 0 past
    # front_deg[1], C2): the throat under the head's under-chin plane. The back keeps R1's seam exactly (the nape's
    # line sets the C7 joint, skeleton.cervical_joint: a moved nape moves the skeleton and needs the clip bake again)
    a0, a1 = s.get("front_deg", [55.0, 95.0])
    c = V[ring].mean(0)
    az = np.degrees(np.abs(np.arctan2(V[:, 0] - c[0], V[:, 2] - c[2])))
    front = 1 - q5(np.clip((az - a0) / (a1 - a0), 0, 1))
    X = st.harmonic(L, known, vals, np.where(zone)[0])
    if s.get("solve", "biharmonic") == "biharmonic":
        # R1b: the harmonic ease is a membrane: its slope breaks at the first row (the move falls off linearly from
        # it), so the second row sat a ledge in from the first (a 5-7 mm notch across the throat front under the
        # head's under-chin plane: the dark zigzag band of the R1 judge). The biharmonic ease (L^2 x = 0, the ring and
        # the first row known: the head's slope carried; 0 with zero slope outside the zone) bends with no kink.
        Xb = biharmonic(L, known, vals, np.where(zone)[0])
        X = X + front[:, None] * (Xb - X)
    fill = s.get("fill_m", 0.045)
    if fill:
        # the body's own surface under the ring is a groove (MakeHuman's throat sits 12-14 mm in behind the head's
        # ring at the front: 26 -> 12 mm forward over the first 2 rows): an ease of a move keeps that curvature.
        # Within fill_m of the ring the surface itself is laid biharmonic (positions: the ring and the moved first
        # row hold the head's slope, the body outside holds its own), so the throat leaves the head in one fair
        # curve; the fill fades over its outer half (C2 in the distance) and round the side (front) to no line.
        Vx = V + X
        fz = dr < float(fill)
        fz[ring] = False
        fz[F] = False
        kn = np.where(~fz)[0]
        Pf = biharmonic(L, kn, Vx[kn], np.where(fz)[0])
        k0 = float(s.get("fill_core", 0.25))
        w = (1 - q5(np.clip((dr / float(fill) - k0) / (1 - k0), 0, 1))) * front * fz
        Dfill = w[:, None] * (Pf - Vx)
        X = X + Dfill
        rep["seam_fill"] = {"fill_m": fill, "front_deg": [a0, a1],
                            "move_mm_max": round(float(np.linalg.norm(Dfill, axis=1).max()) * 1e3, 2)}
    rep["seam"] = {"rows_m": s["rows_m"], "first_row": int(len(F)), "first_row_move_mm_max": round(float(np.linalg.norm(Df, axis=1).max()) * 1e3, 2),
                   "first_row_move_mm_mean": round(float(np.linalg.norm(Df, axis=1).mean()) * 1e3, 2)}
    return V + X


# ----------------------------------------------------------------------------------------------- 2b forms --
def topo_sha(z):
    """Our topology's identity for a forms file: the reference vertices' and quads' bytes."""
    return hashlib.sha256(np.ascontiguousarray(z["V"], np.float32).tobytes() +
                          np.ascontiguousarray(z["Q"], np.int32).tobytes()).hexdigest()[:16]


def stage_forms(spec, tier, z, V, ring, rep):
    """Her residual (spec "forms_topo": a path pattern with {tier}; wrap_topo.py's npz): R per our vertex (glTF m)
    added to the placed body; R is 0 on the ring and eased in under it, so the seam stays the head's exactly."""
    f = spec.get("forms_topo")
    if not f:
        return V
    path = os.path.join(REPO, f.format(tier=tier))
    r = np.load(path)
    assert str(r["topology"]) == topo_sha(z), ("forms for another topology", path)
    R = r["R"].astype(np.float64)
    assert R.shape == V.shape and np.abs(R[ring]).max() == 0.0, "forms must be 0 on the ring"
    nr = np.linalg.norm(R, axis=1)
    rep["forms"] = {"file": f.format(tier=tier), "move_p50_mm": round(float(np.percentile(nr, 50)) * 1e3, 2),
                    "move_p95_mm": round(float(np.percentile(nr, 95)) * 1e3, 2),
                    "move_max_mm": round(float(nr.max()) * 1e3, 2)}
    return V + R


# --------------------------------------------------------------------------------------------- 3 skeleton --
def bone_body(spec, tier, z, V, A, baked, rep):
    """P1 R1b: soft tissue does not move bones. The body the skeleton's landmarks are read on: this spec's body with
    every designed slider flagged "soft": true at 0 (fat outline, glutes, breasts: their fields would drag the
    landmarks' vertex fits, e.g. the hourglass pulled the hip joint 11 mm in), stages 1, 2, 2b again. A spec may
    also set "bone_sliders" {name: value}: values used for the bones only (her specs: the retired MakeHuman soft
    targets her skeleton was fitted with). No soft slider set and no bone_sliders: V itself (byte-identical)."""
    sv = {k: v for k, v in spec.get("sliders", {}).items() if v}
    designed = {}
    for f in sorted(os.listdir(os.path.join(HERE, "designed"))):
        if f.endswith(".json"):
            with open(os.path.join(HERE, "designed", f)) as fh:
                designed.update(json.load(fh).get("sliders", {}))
    soft = sorted(k for k in sv if designed.get(k, {}).get("soft"))
    over = spec.get("bone_sliders") or {}
    if not soft and not over:
        return V
    s2 = dict(spec)
    s2["sliders"] = {**{k: v for k, v in sv.items() if k not in soft}, **over}
    r2 = {}
    _, Vb = stage_base(s2, tier, r2)
    Vb, ring, _ = stage_place(s2, z, Vb, A, baked, r2)
    Vb = stage_forms(s2, tier, z, Vb, ring, r2)
    rep["bone_body"] = {"soft_off": soft, "bone_sliders": over,
                        "max_mm": round(float(np.linalg.norm(Vb - V, axis=1).max()) * 1e3, 2)}
    return Vb


def bone_values(spec):
    """The slider values the bones are read at (bone_body's): every non-soft slider, then the spec's bone_sliders."""
    sv = {k: v for k, v in spec.get("sliders", {}).items() if v}
    designed = {}
    for f in sorted(os.listdir(os.path.join(HERE, "designed"))):
        if f.endswith(".json"):
            with open(os.path.join(HERE, "designed", f)) as fh:
                designed.update(json.load(fh).get("sliders", {}))
    return {**{k: v for k, v in sv.items() if not designed.get(k, {}).get("soft")}, **(spec.get("bone_sliders") or {})}, designed


def target_joints(spec):
    """P1 R1 round 12: a designed "target" slider's own joints ({cube: [x, y, z]} glTF m, her left, the npz's "joints"
    json; her_a_target.py's a_rest: A's clavicle head, shoulder, elbow and wrist at the pose its skin was taken in), at
    the bone body's value v: {cube: (point, v)} for stage_skeleton. The close tier's file (one skeleton for both)."""
    vals, designed = bone_values(spec)
    over = spec.get("target_files") or {}
    out = {}
    for n, v in vals.items():
        c = designed.get(n, {})
        if c.get("rule") != "target" or not v:
            continue
        z = np.load(os.path.join(REPO, over.get(n, c["file"]).format(tier="close")))
        if "joints" in z.files:
            for cube, p in json.loads(str(z["joints"])).items():
                out[cube] = (np.asarray(p, float), float(v))
    return out


def stage_skeleton(V, tier, rep, head=None, moves=None, joints=None):
    import skeleton as sk
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    with open(os.path.join(HERE, "base", "landmarks.json")) as f:
        table = json.load(f)["tiers"][tier]
    names, par, worlds, ends, info = sk.place_skeleton_ours(skel, V, table, head, moves, joints)   # head: her baked head (Head joint)
    if joints:
        info["target_joints"] = {k: [round(float(x) * 1e3, 1) for x in p] + [v] for k, (p, v) in joints.items()}
    rep["skeleton"] = info
    return {"skel": skel, "names": names, "parents": par, "worlds": worlds, "ends": ends}


# ---------------------------------------------------------------------------------------------- 4 weights --
def stage_weights(z, V, ring, hv, sk, A, baked, rep):
    J, W, info = wtp.body(V, z, sk)
    names = sk["names"]
    nb = len(names)
    D = np.zeros((len(V), nb))
    np.put_along_axis(D, J, W, 1)
    # the head: welded points, the ring's from the body's ring, one to one
    head = A.mesh("HeroineHead")
    PH = baked["HeroineHead"]["P"]
    rep_ = np.asarray(weld(head.P.astype(float), 1e-7))
    uniq, first = np.unique(rep_, return_index=True)
    remap = -np.ones(rep_.max() + 1, np.int64)
    remap[uniq] = np.arange(len(uniq))
    TH = remap[rep_[head.T]]
    ring_w = remap[rep_[hv]]
    Hd, hinfo = wtp.head(PH[first], TH, ring_w, D[ring], names)
    Hd = Hd[remap[rep_]]
    heads = {}
    for h in HEADS:
        m = A.mesh(h)
        Wh = Hd if h == "HeroineHead" else np.eye(nb)[np.full(len(m.P), names.index("Head"))]
        Jh, Wk = wt_cap(Wh)
        heads[h] = (Jh, Wk)
    # the seam: the head's ring copies hold the body's ring weights exactly
    Jr, Wr = heads["HeroineHead"]
    ring_err = 0.0
    Dh = np.zeros((len(head.P), nb))
    np.put_along_axis(Dh, Jr, Wr, 1)
    for i, r in enumerate(ring):
        cop = np.where(rep_ == rep_[hv[i]])[0]
        ring_err = max(ring_err, float(np.abs(Dh[cop] - D[r]).max()))
    info["head"] = {**hinfo, "ring_weight_step_max": ring_err,
                    "max_influences": int((Wr > 0).sum(1).max())}
    rep["weights"] = info
    return {"J": J, "W": W, "heads": heads}


def wt_cap(Wd, k=8):
    import weights as wt
    J, W = wt.cap(Wd, k)
    kk = 4 if (W > 0).sum(1).max() <= 4 else 8
    return J[:, :kk], W[:, :kk]


# ----------------------------------------------------------------------------------------------- 5 export --
def stage_uv(z, tier, rep):
    """(P1 E2) The tier's UV layout (tools/body/topo_uv.py -> base/uv_<tier>.npz), asserted to be for this topology
    (its hash). Close and play share one texture set (topo_uv's play rules)."""
    import topo_uv
    uv, urep = topo_uv.load(tier, z)
    m = urep.get("measure", {})
    rep["uv"] = {"file": f"tools/body/base/uv_{tier}.npz", "version": topo_uv.VERSION, "glb_vertices": int(len(uv["src"])),
                 "flipped": m.get("flipped_left"), "overlap_cells_4k": m.get("overlap_cells_4k"),
                 "stretch_p95": {k: v["stretch_p95"] for k, v in m.get("islands", {}).items()},
                 # (D2) the export's triangles mirror left/right: each right quad's diagonal, mirrored, its left's (1.0)
                 "tri_mirror": topo_uv.mirror_share(z, uv["T"], uv["src"])}
    assert rep["uv"]["tri_mirror"]["share"] == 1.0, ("the triangulation does not mirror: run tools/body/topo_uv.py", tier)
    return uv


def stage_bake(spec, tier, out, rep):
    """(P1 E2, stage 7; spec "bake": {"maps", "size", "pose", "carrier"}) The maps on our UVs (topo_bake.py: baked from the close
    build into <out>/maps; play shares them), gated (topo_bake.gates: albedo dE, seam step, frames; written into
    <out>/maps/bake.json), published to spec "maps" only when the gates pass (a failing bake never reaches godot/),
    then attached to every export of the tier (body / body_lbs, play / play_lbs), after the correctives.
    A stage, not a separate command: the maps are a function of this build's surface, UVs and frames (the bake reads
    stage/close.npz and the export's normals), so a rebuild that changes any of them rebakes in the same command."""
    import shutil
    import glbwrite
    import topo_bake
    b = spec["bake"]
    maps = os.path.join(out, "maps")
    pub = os.path.join(REPO, b["maps"])
    if tier == "close" or not os.path.exists(os.path.join(maps, "albedo.png")):
        r, _ = topo_bake.run(out, maps, size=int(b.get("size", 2048)), pose=b.get("pose"), carrier=b.get("carrier"), carry=b.get("carry"),
                              source_maps=b.get("source_maps"))
        r["files"] = sorted(f for f in os.listdir(maps) if f.endswith((".png", ".json")))
        with open(os.path.join(maps, "bake.json"), "w") as f:
            json.dump(r, f, indent=1, default=float)
        rep["bake"] = {k: v for k, v in r.items() if k != "files"}
        if r["gates"]["pass"] and not b.get("publish_maps", True):
            rep["bake"]["published"] = None     # (publish_p1.py copies <out>/maps with the glbs: the game's maps and bodies stay one set)
        elif r["gates"]["pass"]:
            os.makedirs(pub, exist_ok=True)
            for f in os.listdir(maps):
                shutil.copy2(os.path.join(maps, f), os.path.join(pub, f))
            rep["bake"]["published"] = b["maps"]
        else:
            rep["bake"]["published"] = None
            print("BAKE gates FAILED (not published):", r["gates"], flush=True)
    att = {"baseColor": os.path.join(maps, "albedo.png"), "normal": os.path.join(maps, "normal.png"),
           "metallicRoughness": os.path.join(maps, "roughness.png")}
    stem = os.path.splitext(GLB[tier][0])[0]
    done = []
    for f in (f"{stem}.glb", f"{stem}_lbs.glb"):
        if os.path.exists(os.path.join(out, f)):
            glbwrite.attach_maps(os.path.join(out, f), "Heroine", att)
            done.append(f)
    rep["maps"] = {"dir": spec["bake"]["maps"], "files": sorted(os.listdir(maps)), "attached_to": done}


def her_a_normals(spec, tier, V, N, rep):
    """(P1 R1 bake round 2; spec "her_a" "normals", the her_a target's "N", "NG", "NW", "P": her_a_target.a_normals)
    The export's normals where B lies on A are A's, as A's file stores them (what the game shades A with), each half
    its own: A's normal turned by however the built body's own normal stands off the target's (NG -> N: 0 where the
    build is the target, as on her trunk; the seam's rows and any other slider then carry A's normal with them), and
    weighted v(her_a) * NW * (1 within dev_mm[0] of the target's point, 0 beyond dev_mm[1]); B's own elsewhere.
    The ring is set to the head's after this. Bodies at her_a 0, or a target without "N", keep B's normals exactly."""
    v = float(spec.get("sliders", {}).get("her_a", 0.0))
    nc = (spec.get("her_a") or {}).get("normals")
    if not v or not nc:
        return N, None
    from sliders import designed
    f = (spec.get("target_files") or {}).get("her_a") or designed()["her_a"]["file"]
    zt = np.load(os.path.join(REPO, f.format(tier=tier)))
    assert "N" in zt.files, ("her_a normals: the target has no A normals (her_a_target.py with her_a \"normals\")", f)
    NA, NG, NW, P = (zt[k].astype(np.float64) for k in ("N", "NG", "NW", "P"))
    assert NA.shape == N.shape, ("her_a normals: the target is not this tier", f, NA.shape, N.shape)
    dev = np.linalg.norm(V - P, axis=1) * 1e3
    d0, d1 = nc["dev_mm"]
    x = np.clip((dev - d0) / (d1 - d0), 0.0, 1.0)
    w = v * NW * (1.0 - x * x * (3 - 2 * x))
    from bends import turn_onto
    Nt = turn_onto(NA, NG, N)
    out = w[:, None] * Nt + (1.0 - w[:, None]) * N
    out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    ang = np.degrees(np.arccos(np.clip((out * N).sum(1), -1, 1)))
    on = w > 0.99
    info = {"file": f, "a_normals_vertices": int(on.sum()), "blended": int(((w > 1e-3) & ~on).sum()), "of": int(len(N)),
            "dev_mm_p99_on": round(float(np.percentile(dev[on], 99)), 3) if on.any() else None,
            "turn_from_B_deg_p50_p90_p99_on": [round(float(q), 2) for q in np.percentile(ang[on], [50, 90, 99])] if on.any() else None}
    rep["normals"] = info
    return out, info


def stage_export(spec, tier, z, V, ring, hv, sk, wts, A, baked, out, rep, uv=None):
    import glbwrite
    Q = z["Q"]
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    N = st.vertex_normals(V, T)
    N, _ = her_a_normals(spec, tier, V, N, rep)
    head = A.mesh("HeroineHead")
    N[ring] = head.N[hv]
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6)
    de = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    twice = int(len(de) - len(np.unique(de, axis=0)))        # a directed edge used twice: a flipped face
    UV = np.stack([(V[:, 0] + 0.6) / 1.2, 1.0 - V[:, 1] / 1.8], 1)      # placeholder (UVs are a later step)
    Pv = V.astype(np.float32)
    Pv[ring] = np.asarray(baked["HeroineHead"]["P"][hv], np.float32)
    Jp = np.pad(wts["J"], ((0, 0), (0, 8 - wts["J"].shape[1])))
    Wp = np.pad(wts["W"], ((0, 0), (0, 8 - wts["W"].shape[1])))
    split = {}
    if uv is not None:
        # (E2) the glb vertices split at the UV seams and the mirror line: glb vertex k is our topology vertex src[k]
        # (the first n are ours in order); its position, normal, joints and weights are src's; the UVs and the
        # triangles the layout's; the tangent from the UVs (topo_bake.tangent_frames)
        import topo_bake
        src = uv["src"]
        Pv, N, Jp, Wp, T, UV = Pv[src], N[src], Jp[src], Wp[src], uv["T"], uv["UV"]
        tan, tw = topo_bake.tangent_frames(Pv.astype(np.float64), N, UV, T)
        split = {"Tan": np.concatenate([tan, tw[:, None]], 1).astype(np.float32)}
    body = {"node": "Heroine", "material": spec["body_material"], "P": Pv, "N": N, "UV": UV, "T": T,
            "J": Jp, "W": Wp, **split}
    skel = {"names": sk["names"], "parents": sk["parents"], "worlds": sk["worlds"], "scale": {}}
    ov = {h: {"P": baked[h]["P"], "J": wts["heads"][h][0], "W": wts["heads"][h][1], "targets": baked[h]["targets"]}
          for h in HEADS}
    glb, rig = GLB[tier]
    glbwrite.write(os.path.join(out, glb), os.path.join(REPO, spec["ref"]), skel, body, HEADS,
                   np.zeros(len(A.skeleton().names), np.int64), head_override=ov,
                   extras={"body_base": {"spec": rep["spec"], "tier": tier, "topology": f"tools/body/out/topo/{tier}.npz",
                                         "skeleton": "tools/body/skeleton.json", "weights": f"{wtp.VERSION} tools/body/weights_topo.py",
                                         "head": "A's, the Head scale baked (tools/body/headbake.py)", "version": 2,
                                         **({"split": {"n_topology": int(len(V)), "src": f"stage/{tier}.npz:src",
                                                       "uv": f"tools/body/base/uv_{tier}.npz"}} if uv is not None else {})}})
    tmp = os.path.join(out, "stage", tier)
    os.makedirs(tmp, exist_ok=True)
    st.write_rig(sk, tmp)
    os.replace(os.path.join(tmp, "rig.json"), os.path.join(out, rig))
    ht = int(sum(len(A.mesh(h).T) for h in HEADS))
    rep["export"] = {"file": glb, "body_vertices": int(len(V)), "tris_body": int(len(T)), "head_tris": ht,
                     "tris_whole": int(len(T)) + ht, "signed_volume_l": round(vol * 1e3, 2),
                     "flipped_edges": twice}
    np.savez(os.path.join(out, "stage", f"{tier}.npz"), V=V, J=wts["J"], W=wts["W"], worlds=sk["worlds"],
             **({"src": uv["src"], "T": uv["T"]} if uv is not None else {}))


def stage_shapes(spec, tier, z, V, A, baked, out, rep):
    """8 (P1 R1) form shapes: designed sliders the GAME sets at run time, written as blend shapes on the body (after
    the correctives' shapes, kept): spec "shapes" {slider: value} -> a shape "form_<slider>" = the body built with
    that slider raised by value less this body (stages 1, 2, 2b again: the same join and seam); spec "shapes_with"
    {slider: {other: value}}: that shape's body also has these others at these values (a support undoes the settle). The first use: the
    armor's support (breast_support...): each armor piece sets its shape's weight as data, so the body under a
    push-up piece is shaped by design, never per piece. Normals' deltas by correctives.normal_delta."""
    import glbwrite
    from correctives import normal_delta
    glb = os.path.join(out, GLB[tier][0])
    st_ = np.load(os.path.join(out, "stage", f"{tier}.npz"))
    src = st_["src"] if "src" in st_.files else np.arange(len(V))
    Tg = st_["T"] if "T" in st_.files else np.concatenate([z["Q"][:, [0, 1, 2]], z["Q"][:, [0, 2, 3]]])
    tg, info = {}, {}
    # (her_a normals: the shapes turn the export's own normals, correctives.normal_delta N; else the geometric delta)
    Nx = Glb(glb).mesh("Heroine").N.astype(np.float64) if rep.get("normals") else None
    for name, val in spec["shapes"].items():
        s2 = dict(spec)
        s2["sliders"] = dict(spec.get("sliders", {}))
        s2["sliders"][name] = float(s2["sliders"].get(name, 0.0)) + float(val)
        s2["sliders"].update(spec.get("shapes_with", {}).get(name, {}))    # the shape also takes these sliders to these values
        r2 = {}
        _, V2 = stage_base(s2, tier, r2)
        V2, ring, _ = stage_place(s2, z, V2, A, baked, r2)
        V2 = stage_forms(s2, tier, z, V2, ring, r2)
        D = (V2 - V)[src]
        tg["form_" + name] = (D.astype(np.float32), normal_delta(V[src], Tg, D, Nx).astype(np.float32))
        info["form_" + name] = {"value": val, "max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 2)}
    glbwrite.add_targets(glb, "Heroine", tg)
    rep["shapes"] = info


def skeleton_diff(a, b):
    """Two glbs' skeletons: names and parents equal, and the worst rest-world gap (mm, deg)."""
    sa, sb = Glb(a).skeleton(), Glb(b).skeleton()
    if list(sa.names) != list(sb.names) or list(sa.parent) != list(sb.parent):
        return {"same_names_parents": False}
    dm = float(np.abs(sa.rest[:, :3, 3] - sb.rest[:, :3, 3]).max()) * 1e3
    R = np.einsum("nji,njk->nik", sa.rest[:, :3, :3], sb.rest[:, :3, :3])
    dd = float(np.degrees(np.arccos(np.clip((np.trace(R, axis1=1, axis2=2) - 1) / 2, -1, 1))).max())
    return {"same_names_parents": True, "max_mm": round(dm, 6), "max_deg": round(dd, 6)}


def run_tier(spec, tier, A, baked, out, rep, correct=True, sk_close=None):
    t = time.time()
    tim = rep["timings_s"]
    z, V = stage_base(spec, tier, rep)
    tim["base"] = round(time.time() - t, 2)
    t = time.time()
    V, ring, hv = stage_place(spec, z, V, A, baked, rep)
    tim["place"] = round(time.time() - t, 2)
    t = time.time()
    V = stage_forms(spec, tier, z, V, ring, rep)
    tim["forms"] = round(time.time() - t, 2)
    t = time.time()
    if tier == "play":
        # P1 R2: one skeleton for both tiers. The play tier takes the close tier's placed skeleton (names, parents,
        # worlds, ends) so a clip baked on the close rest drives play identically; play's weights are computed on it
        if sk_close is None:
            with open(os.path.join(out, "stage", "close_skeleton.json")) as f:
                sk_close = json.load(f)
            sk_close["worlds"] = np.asarray(sk_close["worlds"], float)
            sk_close["ends"] = {k: tuple(np.asarray(x, float) for x in v) for k, v in sk_close["ends"].items()}
        sk = {k: sk_close[k] for k in ("skel", "names", "parents", "worlds", "ends")}
        rep["skeleton"] = {"from": "close (build_topo P1 R2: one skeleton for both tiers)"}
    else:
        sk = stage_skeleton(bone_body(spec, tier, z, V, A, baked, rep), tier, rep, baked["HeroineHead"]["P"], spec.get("joint_moves"),
                            target_joints(spec))
        with open(os.path.join(out, "stage", "close_skeleton.json"), "w") as f:
            json.dump({k: sk[k] for k in ("skel", "names", "parents", "worlds", "ends")}, f,
                      default=lambda x: np.asarray(x).tolist())
    tim["skeleton"] = round(time.time() - t, 2)
    t = time.time()
    wts = stage_weights(z, weights_body(spec, tier, z, V, A, baked, rep), ring, hv, sk, A, baked, rep)
    tim["weights"] = round(time.time() - t, 2)
    t = time.time()
    uv = stage_uv(z, tier, rep) if spec.get("uv", True) else None
    stage_export(spec, tier, z, V, ring, hv, sk, wts, A, baked, out, rep, uv)
    tim["export"] = round(time.time() - t, 2)
    if correct:
        t = time.time()
        import correctives
        rep["correctives"] = correctives.run(out, tier=tier, fresh=True, turn_normals=bool(rep.get("normals")))
        tim["correctives"] = round(time.time() - t, 2)
    if spec.get("shapes"):
        t = time.time()
        stage_shapes(spec, tier, z, V, A, baked, out, rep)
        tim["shapes"] = round(time.time() - t, 2)
    if uv is not None and spec.get("bake"):
        t = time.time()
        stage_bake(spec, tier, out, rep)
        tim["bake"] = round(time.time() - t, 2)
    with open(os.path.join(out, GLB[tier][0]), "rb") as f:
        rep["glb_sha256"] = hashlib.sha256(f.read()).hexdigest()
    pub = os.path.join(REPO, "godot", "art", "people", "body_p1", "body.glb")
    if tier == "close" and os.path.exists(pub):
        rep["skeleton_vs_published"] = skeleton_diff(os.path.join(out, "body.glb"), pub)
    if tier == "play" and os.path.exists(os.path.join(out, "body.glb")):
        d = skeleton_diff(os.path.join(out, "play.glb"), os.path.join(out, "body.glb"))
        rep["skeleton_play_vs_close"] = d
        assert d.get("same_names_parents") and d["max_mm"] < 1e-3 and d["max_deg"] < 1e-3, f"play skeleton != close: {d}"
    return sk


def weights_body(spec, tier, z, V, A, baked, rep):
    """P1 R1c: the body the skin weights are read on: this spec's body with every designed slider flagged
    "rides_skin": true at 0 (designed/armpit.json's fill: a few mm of soft tissue laid on the skin, which must move
    with the skin it sits on; read on the filled body, the girdle's bounded biharmonic fill and its distance rules
    re-solved across 3848 trunk/shoulder/arm points, up to 0.15, and the hanging arm re-opened the gap it fills).
    None set: V itself (byte-identical)."""
    sv = {k: v for k, v in spec.get("sliders", {}).items() if v}
    des = {}
    for f in sorted(os.listdir(os.path.join(HERE, "designed"))):
        if f.endswith(".json"):
            with open(os.path.join(HERE, "designed", f)) as fh:
                des.update(json.load(fh).get("sliders", {}))
    rides = sorted(k for k in sv if des.get(k, {}).get("rides_skin"))
    if not rides:
        return V
    s2 = dict(spec)
    s2["sliders"] = {k: v for k, v in sv.items() if k not in rides}
    r2 = {}
    _, Vw = stage_base(s2, tier, r2)
    Vw, ring_w, _ = stage_place(s2, z, Vw, A, baked, r2)
    Vw = stage_forms(s2, tier, z, Vw, ring_w, r2)
    rep["weights_body"] = {"rides_skin_off": rides, "max_mm": round(float(np.linalg.norm(Vw - V, axis=1).max()) * 1e3, 2)}
    return Vw


def with_defaults(spec):
    """P1 R1c: a designed slider with a "default" (designed/armpit.json's armpit_fill: the body's own armpit) is laid
    on every body at that value unless the spec names it (0 = off), so NPCs and the male body get it free. The value
    joins spec["sliders"] here, before every stage, so bone_body (its "soft" flag) and the shapes see the same body."""
    des = {}
    for f in sorted(os.listdir(os.path.join(HERE, "designed"))):
        if f.endswith(".json"):
            with open(os.path.join(HERE, "designed", f)) as fh:
                des.update(json.load(fh).get("sliders", {}))
    add = {k: c["default"] for k, c in des.items() if c.get("default") and k not in spec.get("sliders", {})}
    if not add:
        return spec
    spec = dict(spec)
    spec["sliders"] = {**spec.get("sliders", {}), **add}
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--tiers", default="close,play")
    ap.add_argument("--no-correctives", action="store_true", help="skip stage 6 (the export without shapes)")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(os.path.join(out, "stage"), exist_ok=True)
    spec = load_spec(a.spec)
    spec = with_defaults(spec)
    A = Glb(os.path.join(REPO, spec["ref"]))
    t0 = time.time()
    baked = headbake.bake(A, HEADS)
    hmove = np.asarray(sliders_head_move(spec.get("sliders", {})), float)
    if np.abs(hmove).max() > 0:
        # P1 R1: the head's placement on the new neck (the designed neck sliders' head_move): the whole baked head
        # (every head mesh; the skeleton's Head joint is placed from it) moves rigidly; the ring moves with it
        for h in baked:
            baked[h]["P"] = baked[h]["P"] + hmove[None, :]
    full = {"spec": os.path.relpath(os.path.abspath(a.spec), REPO).replace("\\", "/"), "tiers": {}}
    full["head_move_m"] = [round(float(x), 5) for x in hmove]
    sk_close = None
    for tier in a.tiers.split(","):
        rep = {"spec": full["spec"], "timings_s": {}}
        sk = run_tier(spec, tier, A, baked, out, rep, correct=not a.no_correctives, sk_close=sk_close)
        if tier == "close":
            sk_close = sk
        full["tiers"][tier] = rep
        print("BUILD", tier, os.path.join(out, GLB[tier][0]), rep["glb_sha256"][:16], rep["timings_s"])
    full["total_s"] = round(time.time() - t0, 2)
    with open(os.path.join(out, "build.json"), "w") as f:
        json.dump(full, f, indent=1, default=float)


if __name__ == "__main__":
    main()
