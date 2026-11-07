#!/usr/bin/env python
"""P1 R1 round 10: her torso, breasts, hips and legs from A as ONE source file on our topology: the designed slider her_a
(designed/her.json, rule "target"; other bodies leave it at 0), so the one-command build reads this, not heroine.glb.

    python tools/body/her_a_target.py tools/body/specs/her_b.json [--maps] [--tiers close,play]

Writes tools/body/base/targets/her_a_{close,play}.npz: "D" [n,3] (glTF m, the move at v = 1, laid by build_topo stage 1
after the join and the stance, before seam_g1), "topology" (build_topo.topo_sha), "M" [n] (the mask), "about".
--maps also carries A's paint once onto our UVs: base/targets/her_a_maps/ (topo_bake.SOURCE_MAPS + bake.json).

The fit is the existing one: her_topo.json's sliders, stance and residual (wrap_topo.py, forms/her_topo_{tier}.npz, A posed
by her_target world=True; TIGHT p95 about 1.8 mm), the topology's hash asserted. D = M (fit - body) + (1 - M) t, where
body = this spec's stage 1 at her_a = 0 and t = spec "her_a" "arm_move_m" (dx away from the midline on each side): the
arm and deltoid keep OUR form and only ride to A's shoulder line. D is 0 on the head's ring.

M, spec "her_a" (a function of the topology's parts and rings and these numbers; no paint): 0 on "zero_parts" (default arm,
elbow, forearm and hand; round 11: the hand only, the fit's arm taken) and on the shoulder band's rings from "zero_ring" out
(null: none), 1 farther than "band_m" along the surface (reference surface, edge
lengths), biharmonic between (L^2 M = 0 on an inverse-edge-length Laplacian, the known sets thick enough that the slope
leaves them at 0), mirror-averaged. Play takes close's M through the shared reference surface. Derivation: (a) the owner,
6 Nov: A is the quality floor, B's job is one topology and sliders; (b) A; (c) the arm is ours: A's arm surface was the
fault of 27 Oct.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build_topo as bt  # noqa: E402
import headbake  # noqa: E402
from gl import Glb  # noqa: E402
from sliders import load_spec, carry_to_tier  # noqa: E402

TARGETS = os.path.join(HERE, "base", "targets")
OUT_FILE = "her_a_{tier}.npz"


def edges(Q):
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    return np.unique(np.sort(e, 1), axis=0)


def mirror(z):
    n = len(z["V"])
    pr = np.arange(n)
    mo = z["mirror_of"]
    r = np.where(mo >= 0)[0]
    pr[r] = mo[r]
    pr[mo[r]] = r
    return pr


def mask(z, cfg):
    """M on a tier's reference surface (see the module's doc); (M, zero, one) with zero and one the known sets."""
    V, Q = z["V"].astype(np.float64), z["Q"]
    parts = list(map(str, z["parts"]))
    part, ring = z["part"], z["ring"]
    arm = np.isin(part, [parts.index(p) for p in cfg.get("zero_parts", ("arm", "elbow", "forearm", "hand"))])
    zero = arm | ((part == parts.index("shoulder")) & (ring >= cfg["zero_ring"])) if cfg.get("zero_ring") is not None else arm
    e = edges(Q)
    ln = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    n = len(V)
    # the surface distance from the zero set: a virtual source joined to it
    ze = np.where(zero)[0]
    r = np.r_[e[:, 0], e[:, 1], np.full(len(ze), n)]
    c = np.r_[e[:, 1], e[:, 0], ze]
    G = sp.coo_matrix((np.r_[ln, ln, np.full(len(ze), 1e-9)], (r, c)), shape=(n + 1, n + 1)).tocsr()
    d = dijkstra(G, indices=n)[:n]
    one = (d >= cfg["band_m"]) & ~zero
    w = 1.0 / np.maximum(ln, 1e-4)
    W = sp.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    L = (sp.diags(np.asarray(W.sum(1)).ravel()) - W).tocsr()
    known = np.where(zero | one)[0]
    free = np.where(~(zero | one))[0]
    M = bt.biharmonic(L, known, one[known][:, None].astype(float), free)[:, 0]
    pr = mirror(z)
    M = np.clip(0.5 * (M + M[pr]), 0.0, 1.0)
    return M, zero, one


def bodies(spec, fit_spec, tier, A, baked):
    """(this spec's stage 1 at her_a = 0, the fit on A, z). stage_base for both (the fit through stages 2 and 2b too)."""
    pre = bt.load_tier(tier)
    z = pre[0]
    s0 = dict(spec)
    s0["sliders"] = {k: v for k, v in spec["sliders"].items() if k != "her_a"}
    _, V0 = bt.stage_base(s0, tier, {}, pre=pre)
    r = np.load(os.path.join(REPO, fit_spec["forms_topo"].format(tier=tier)))
    assert str(r["topology"]) == bt.topo_sha(z), ("the fit is for another topology", tier)
    _, Vf = bt.stage_base(fit_spec, tier, {}, pre=pre)
    Vf, ring, _ = bt.stage_place(fit_spec, z, Vf, A, baked, {})
    Vf = bt.stage_forms(fit_spec, tier, z, Vf, ring, {})
    return V0, Vf, z


def make(spec_path, tiers):
    spec = bt.with_defaults(load_spec(spec_path))
    cfg = spec["her_a"]
    fit_spec = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    A = Glb(os.path.join(REPO, spec["ref"]))
    baked = headbake.bake(A, ["HeroineHead"])
    zc = dict(np.load(os.path.join(HERE, "out", "topo", "close.npz")))
    Mc, _, _ = mask(zc, cfg)
    t = np.asarray(cfg.get("arm_move_m", [0, 0, 0]), float)
    for tier in tiers:
        V0, Vf, z = bodies(spec, fit_spec, tier, A, baked)
        ring = bt.boundary_ring(z["Q"], len(V0))
        M = Mc if tier == "close" else np.clip(carry_to_tier(Mc[:, None], "close", tier)[:, 0], 0.0, 1.0)
        M = np.where(M < 1e-3, 0.0, np.where(M > 1 - 1e-3, 1.0, M))
        ts = t[None, :] * np.stack([np.where(z["V"][:, 0] >= 0, 1.0, -1.0), np.ones(len(V0)), np.ones(len(V0))], 1)
        D = M[:, None] * (Vf - V0) + (1.0 - M[:, None]) * ts
        ring_max = float(np.abs(D[ring]).max())
        assert ring_max < 1e-4, ("the fit is not the head's on the ring", ring_max)
        D[ring] = 0.0
        about = (f"made_by: python tools/body/her_a_target.py {os.path.relpath(os.path.abspath(spec_path), REPO)}".replace("\\", "/") +
                 f" (fit {cfg['fit_spec']}, band_m {cfg['band_m']}, zero_parts {cfg.get('zero_parts', 'arm..hand')}, zero_ring {cfg.get('zero_ring')}, arm_move_m {list(t)})")
        np.savez_compressed(os.path.join(TARGETS, OUT_FILE.format(tier=tier)), D=D.astype(np.float32), M=M.astype(np.float32),
                            topology=np.array(bt.topo_sha(z)), about=np.array(about))
        print(tier, "D max mm", round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 1), "M<1", int((M < 1).sum()), "of", len(M), flush=True)


def maps(spec_path):
    """A's paint carried once: topo_bake on the carrier (the fit's build, on A) into base/targets/her_a_maps."""
    import topo_bake
    spec = load_spec(spec_path)
    cfg = spec["her_a"]
    fit = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    work = os.path.join(HERE, "out", "her_a_maps_work")
    r, _ = topo_bake.run(os.path.join(REPO, cfg["carrier"]), work, size=int(fit["bake"].get("size", 2048)), pose=fit["bake"].get("pose"))
    dest = os.path.join(TARGETS, "her_a_maps")
    os.makedirs(dest, exist_ok=True)
    for k in topo_bake.SOURCE_MAPS:
        shutil.copy2(os.path.join(work, f"{k}.png"), os.path.join(dest, f"{k}.png"))
    r = {k: r[k] for k in ("version", "size", "covered", "projection", "normal_inverted_texels", "normal_form", "gates") if k in r}
    r["made_by"] = "tools/body/her_a_target.py --maps, from " + cfg["carrier"]
    with open(os.path.join(dest, "bake.json"), "w") as f:
        json.dump(r, f, indent=1, default=float)
    print("maps", r["gates"]["pass"], r["projection"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--maps", action="store_true")
    ap.add_argument("--tiers", default="close,play")
    a = ap.parse_args()
    make(a.spec, a.tiers.split(","))
    if a.maps:
        maps(a.spec)


if __name__ == "__main__":
    main()
