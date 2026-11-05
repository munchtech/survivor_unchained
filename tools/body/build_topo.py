#!/usr/bin/env python
"""P1 B2a: the base build on OUR topology, both tiers, no Blender, no MakeHuman at build time. docs/team/body.md P1.

    python tools/body/build_topo.py tools/body/specs/base_woman.json <out_dir> [--tiers close,play]

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
              way); "forms" (v1's residual, per MakeHuman point) is NOT applied: ours are "forms_topo" (2b);
  2 place     her shipped head, baked to its world rest (headbake.py: A's +7% Head scale and off-rest bind folded into
              the meshes); our open neck ring (94 points, one to one with the head's open ring by construction)
              snapped onto the baked head ring, the move eased harmonically into the body over `fit_ease_m` under
              SPLIT (stages.harmonic on our quads' graph Laplacian);
  2b forms    the spec's "forms_topo" (a path pattern with {tier}: wrap_topo.py's R per our vertex, 0 on the ring)
              added to the placed body; the npz names our topology's hash (stage_forms asserts it);
  3 skeleton  tools/body/skeleton.json placed from OUR vertices alone (skeleton.place_skeleton_ours,
              base/landmarks.json "tiers"[tier]) on the placed body;
  4 weights   v0 (weights_topo.py: our topology's primary weights, then weights.py's rules 2 and 4-10), and the
              head's: its ring = the body ring's weights, Head above, harmonic between;
  5 export    glbwrite.py: our skeleton (no rest scale, plain binds), the body (our quads as triangle pairs, normals
              from our faces, the ring's from the head so the seam lights as one; TEXCOORD_0 a placeholder front
              projection: UVs are a later step), the head meshes with the bake and our weights written over A's; and
              rig.json (stages.write_rig: the poser's drivers, base_drive.json).
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
from gl import Glb, weld  # noqa: E402
from sliders import OurSliders, load_spec  # noqa: E402

HEADS = ["HeroineEyes", "HeroineHead", "HeroineLashes", "HeroineTeeth", "HeroineTongue"]
HOLD_M, EASE_M = 0.015, 0.06          # forms.py's join
GLB = {"close": ("body.glb", "rig.json"), "play": ("play.glb", "play_rig.json")}


def s01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def split_depth(V):
    """How far under SPLIT (headmatch.s_split) each point is, m, positive below; V in glTF, our placed frame."""
    return -hm.s_split(hm.to_blender(V))


def boundary_ring(Q, n):
    e = np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return np.unique(u[c == 1])


# ------------------------------------------------------------------------------------------------- 1 base --
def load_tier(tier):
    """Our topology and its slider bake for a tier (stage 1's inputs; the fit, wrap_topo.py, holds them)."""
    return (dict(np.load(os.path.join(HERE, "out", "topo", f"{tier}.npz"))),
            OurSliders(os.path.join(HERE, "base", f"sliders_{tier}.npz")))


def stage_base(spec, tier, rep, pre=None):
    z, sl = pre or load_tier(tier)
    V0 = sl.V0.copy()
    assert np.abs(V0 - z["V"]).max() < 1e-6, "the sliders' reference is not this topology"
    info = {"topology": f"tools/body/out/topo/{tier}.npz", "vertices": int(len(V0)), "quads": int(len(z["Q"]))}
    V = V0.copy()
    jw = s01((split_depth(V0) - HOLD_M) / EASE_M)[:, None]
    sliders = {k: v for k, v in spec.get("sliders", {}).items() if v}
    if sliders:
        unknown = sorted(set(sliders) - set(sl.names))
        assert not unknown, ("sliders not in the bake", unknown)
        d = sl.evaluate(sliders) - V0
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
    if spec.get("forms"):
        info["forms"] = f"NOT applied ({spec['forms']}: per MakeHuman point; ours are \"forms_topo\", stage 2b)"
    rep["base"] = info
    return z, V


# ------------------------------------------------------------------------------------------------ 2 place --
def stage_place(spec, z, V, A, baked, rep):
    Q = z["Q"]
    ring = boundary_ring(Q, len(V))
    head = A.mesh("HeroineHead")
    d, hv = cKDTree(head.P.astype(float)).query(V[ring])
    assert len(ring) == 94 and d.max() < 1e-6, ("the open ring is not the head's", len(ring), d.max())
    tgt = baked["HeroineHead"]["P"][hv]
    D = tgt - V[ring]
    L = st.laplacian(Q, len(V))
    zone = split_depth(V) < spec["fit_ease_m"]
    zone[ring] = False
    V = V + st.harmonic(L, ring, D, np.where(zone)[0])
    V[ring] = tgt
    rep["place"] = {"ring_points": int(len(ring)), "ring_move_max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 2),
                    "ring_move_mean_mm": round(float(np.linalg.norm(D, axis=1).mean()) * 1e3, 2),
                    "ease_points": int(zone.sum()), "fit_ease_m": spec["fit_ease_m"],
                    "feet_lowest_m": round(float(V[:, 1].min()), 4)}
    return V, ring, hv


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
def stage_skeleton(V, tier, rep):
    import skeleton as sk
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    with open(os.path.join(HERE, "base", "landmarks.json")) as f:
        table = json.load(f)["tiers"][tier]
    names, par, worlds, ends, info = sk.place_skeleton_ours(skel, V, table)
    rep["skeleton"] = info
    return {"skel": skel, "names": names, "parents": par, "worlds": worlds, "ends": ends}


# ---------------------------------------------------------------------------------------------- 4 weights --
def stage_weights(z, V, ring, hv, sk, A, baked, rep):
    import weights_topo as wtp
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
def stage_export(spec, tier, z, V, ring, hv, sk, wts, A, baked, out, rep):
    import glbwrite
    Q = z["Q"]
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    N = st.vertex_normals(V, T)
    head = A.mesh("HeroineHead")
    N[ring] = head.N[hv]
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6)
    de = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    twice = int(len(de) - len(np.unique(de, axis=0)))        # a directed edge used twice: a flipped face
    UV = np.stack([(V[:, 0] + 0.6) / 1.2, 1.0 - V[:, 1] / 1.8], 1)      # placeholder (UVs are a later step)
    Pv = V.astype(np.float32)
    Pv[ring] = np.asarray(baked["HeroineHead"]["P"][hv], np.float32)
    body = {"node": "Heroine", "material": spec["body_material"], "P": Pv, "N": N, "UV": UV, "T": T,
            "J": np.pad(wts["J"], ((0, 0), (0, 8 - wts["J"].shape[1]))),
            "W": np.pad(wts["W"], ((0, 0), (0, 8 - wts["W"].shape[1])))}
    skel = {"names": sk["names"], "parents": sk["parents"], "worlds": sk["worlds"], "scale": {}}
    ov = {h: {"P": baked[h]["P"], "J": wts["heads"][h][0], "W": wts["heads"][h][1], "targets": baked[h]["targets"]}
          for h in HEADS}
    glb, rig = GLB[tier]
    glbwrite.write(os.path.join(out, glb), os.path.join(REPO, spec["ref"]), skel, body, HEADS,
                   np.zeros(len(A.skeleton().names), np.int64), head_override=ov,
                   extras={"body_base": {"spec": rep["spec"], "tier": tier, "topology": f"tools/body/out/topo/{tier}.npz",
                                         "skeleton": "tools/body/skeleton.json", "weights": "v0 tools/body/weights_topo.py",
                                         "head": "A's, the Head scale baked (tools/body/headbake.py)", "version": 2}})
    tmp = os.path.join(out, "stage", tier)
    os.makedirs(tmp, exist_ok=True)
    st.write_rig(sk, tmp)
    os.replace(os.path.join(tmp, "rig.json"), os.path.join(out, rig))
    ht = int(sum(len(A.mesh(h).T) for h in HEADS))
    rep["export"] = {"file": glb, "body_vertices": int(len(V)), "tris_body": int(len(T)), "head_tris": ht,
                     "tris_whole": int(len(T)) + ht, "signed_volume_l": round(vol * 1e3, 2),
                     "flipped_edges": twice}
    np.savez(os.path.join(out, "stage", f"{tier}.npz"), V=V, J=wts["J"], W=wts["W"], worlds=sk["worlds"])


def run_tier(spec, tier, A, baked, out, rep):
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
    sk = stage_skeleton(V, tier, rep)
    tim["skeleton"] = round(time.time() - t, 2)
    t = time.time()
    wts = stage_weights(z, V, ring, hv, sk, A, baked, rep)
    tim["weights"] = round(time.time() - t, 2)
    t = time.time()
    stage_export(spec, tier, z, V, ring, hv, sk, wts, A, baked, out, rep)
    tim["export"] = round(time.time() - t, 2)
    with open(os.path.join(out, GLB[tier][0]), "rb") as f:
        rep["glb_sha256"] = hashlib.sha256(f.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--tiers", default="close,play")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(os.path.join(out, "stage"), exist_ok=True)
    spec = load_spec(a.spec)
    A = Glb(os.path.join(REPO, spec["ref"]))
    t0 = time.time()
    baked = headbake.bake(A, HEADS)
    full = {"spec": os.path.relpath(os.path.abspath(a.spec), REPO).replace("\\", "/"), "tiers": {}}
    for tier in a.tiers.split(","):
        rep = {"spec": full["spec"], "timings_s": {}}
        run_tier(spec, tier, A, baked, out, rep)
        full["tiers"][tier] = rep
        print("BUILD", tier, os.path.join(out, GLB[tier][0]), rep["glb_sha256"][:16], rep["timings_s"])
    full["total_s"] = round(time.time() - t0, 2)
    with open(os.path.join(out, "build.json"), "w") as f:
        json.dump(full, f, indent=1, default=float)


if __name__ == "__main__":
    main()
