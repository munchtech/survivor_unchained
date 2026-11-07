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
from surfdist import Surface  # noqa: E402

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


def quad_normals(V, Q):
    """Area-weighted vertex normals of a quad mesh (each quad as two triangles)."""
    N = np.zeros_like(V)
    for T in (Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]):
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        for c in range(3):
            np.add.at(N, T[:, c], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)


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


def kabsch(P, Q):
    """The rigid motion (R, t) taking points P onto Q (least squares)."""
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    R = Vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
    return R, qc - R @ pc


class ARest:
    """her_a "a_rest" (round 12): the chain bones that stay at A's OWN rest in the target, e.g. ["clavicle", "upperarm"].
    The fit was solved on A posed into the slider stage's rest (forms/her_topo_target_bones.json); here A is posed
    twice through her_target (the fit's pose, and the same with those bones unturned) and each fit point rides A's
    surface from the first to the second: its closest point's triangle and barycentrics, the offset turned with the
    triangle's frame. Exact on A's own surface (no weights: both poses are A's game stack). B's rest girdle and arm
    then ARE A's, so the game turns B from where A turns from, and the target needs no skinning round trip there.
    The hand (a zero part: ours) rides rigidly: onto the fit's hand in the fit's pose, then with A's hand points."""

    def __init__(self, cfg):
        import her_target as ht
        with open(os.path.join(HERE, "forms", "her_topo_target_bones.json")) as f:
            fb = {k: (np.asarray(v[0], float), np.asarray(v[1], float)) for k, v in json.load(f)["bones"].items()}
        keep = [f"{b}_{s}" for b in cfg["a_rest"] for s in "lr"]
        self.t0 = ht.target(None, world=True, want=fb)
        self.t1 = ht.target(None, world=True, want={k: (None if k in keep else v) for k, v in fb.items()})
        T = self.t0["T"]
        self.S0 = Surface(self.t0["P"], T)
        names = self.t0["names"]
        self.hand = {}
        for s in "lr":
            hb = [i for i, n in enumerate(names) if n.endswith(f"_{s}") and n.split("_")[0] in ("hand", "thumb", "index", "middle", "ring", "pinky")]
            share = (self.t0["W"] * np.isin(self.t0["J"], hb)).sum(1)
            sel = share > 0.999
            self.hand[s] = kabsch(self.t0["P"][sel], self.t1["P"][sel])
        self.turns = self.t1["turns"]

    @staticmethod
    def frames(P, T):
        e1 = P[T[:, 1]] - P[T[:, 0]]
        e2 = P[T[:, 2]] - P[T[:, 0]]
        n = np.cross(e1, e2)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-15)
        e1 = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-15)
        return np.stack([e1, np.cross(n, e1), n], 2)       # columns: edge, in-plane, normal

    def carry(self, V):
        """Points on (near) A in the fit's pose -> the same surface points on A at the a_rest pose."""
        T = self.t0["T"]
        q, _, tri, d = self.S0.closest(V, k=16)
        a, b, c = (self.t0["P"][T[tri, i]] for i in range(3))
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
        wb = (d11 * d20 - d01 * d21) / den
        wc = (d00 * d21 - d01 * d20) / den
        wa = 1.0 - wb - wc
        P1 = self.t1["P"]
        q1 = wa[:, None] * P1[T[tri, 0]] + wb[:, None] * P1[T[tri, 1]] + wc[:, None] * P1[T[tri, 2]]
        F0, F1 = self.frames(self.t0["P"], T)[tri], self.frames(P1, T)[tri]
        off = np.einsum("nji,nj->ni", F0, V - q)               # the offset in the fit-pose triangle's frame
        return q1 + np.einsum("nij,nj->ni", F1, off), d

    def tight(self, V, z, cfg):
        """her_a "a_tight" {"parts": [...], "fade_parts": [...], "lam": [...], "iters": k}: the fit's LOOSE arm (wrap_topo:
        her girth over our loops, 10-23 mm off her skin) laid ON A's skin over those parts (the shoulder and upper arm:
        the cap, the armpit and the arm's top are A's surface, as the trunk's already is), fading to the fit's own over
        fade_parts (biharmonic). Non-rigid ICP as wrap_topo's TIGHT (point-to-plane + 0.1 point-to-point + lam |L U|^2,
        lam stepped down), closest points on A at this pose whose normal agrees (> 0.5) within 40 mm, mirror-averaged."""
        import scipy.sparse.linalg as spl
        Q = z["Q"]
        parts = list(map(str, z["parts"]))
        part = z["part"]
        on = np.isin(part, [parts.index(p) for p in cfg["parts"]])
        off = ~(on | np.isin(part, [parts.index(p) for p in cfg.get("fade_parts", ())]))
        e = edges(Q)
        n = len(V)
        W = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        L = (sp.diags(np.asarray(W.sum(1)).ravel()) - W).tocsr()
        known = np.where(on | off)[0]
        w = bt.biharmonic(L, known, on[known][:, None].astype(float), np.where(~(on | off))[0])[:, 0]
        pr = mirror(z)
        w = np.clip(0.5 * (w + w[pr]), 0.0, 1.0)
        free = np.where(w > 1e-4)[0]
        Lf = L[free][:, free]
        LtL = (Lf.T @ Lf).tocsr()
        P1, T = self.t1["P"], self.t0["T"]
        S1 = Surface(P1, T)
        U = np.zeros((len(free), 3))
        X0 = V[free]
        stats = []
        n3 = 3 * len(free)
        ii = np.repeat(np.arange(len(free)) * 3, 9) + np.tile(np.repeat(np.arange(3), 3), len(free))
        jj = np.repeat(np.arange(len(free)) * 3, 9) + np.tile(np.tile(np.arange(3), 3), len(free))
        K = sp.kron(LtL, sp.eye(3)).tocsr()
        for lam in cfg["lam"]:
            for _ in range(int(cfg.get("iters", 4))):
                X = X0 + U
                q, nA, _, d = S1.closest(X, k=16)
                Vc = V.copy()
                Vc[free] = X
                ok = (d < 0.04) & ((nA * quad_normals(Vc, Q)[free]).sum(1) > 0.5)
                Bw = (w[free] * ok)[:, None, None] * (np.einsum("ni,nj->nij", nA, nA) + 0.1 * np.eye(3)[None])
                Am = sp.coo_matrix((Bw.ravel(), (ii, jj)), shape=(n3, n3)).tocsr() + lam * K
                U = spl.spsolve(Am.tocsc(), np.einsum("nij,nj->ni", Bw, q - X0).ravel()).reshape(-1, 3)
                Uf = np.zeros((n, 3))
                Uf[free] = U
                U = (0.5 * (Uf + Uf[pr] * np.array([-1.0, 1.0, 1.0])))[free]
            core = w[free] > 0.99
            stats.append((lam, round(float(np.percentile(d[core] * 1e3, 50)), 2), round(float(np.percentile(d[core] * 1e3, 95)), 2), int((~ok).sum())))
        out = V.copy()
        out[free] = X0 + U
        return out, w, stats

    def hand_field(self, V0, Vf, zero_hand, x):
        """Every point moved as our hand rides: rigidly onto the fit's hand (fit pose), then with A's hand (per side by x)."""
        out = V0.copy()
        for s, sgn in (("l", 1.0), ("r", -1.0)):
            side = x * sgn > 0
            h = zero_hand & side
            R0, t0 = kabsch(V0[h], Vf[h])
            R1, t1 = self.hand[s]
            P = V0[side] @ R0.T + t0
            out[side] = P @ R1.T + t1
        return out


def make(spec_path, tiers, out_dir=TARGETS):
    spec = bt.with_defaults(load_spec(spec_path))
    cfg = spec["her_a"]
    fit_spec = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    A = Glb(os.path.join(REPO, spec["ref"]))
    baked = headbake.bake(A, ["HeroineHead"])
    zc = dict(np.load(os.path.join(HERE, "out", "topo", "close.npz")))
    Mc, _, _ = mask(zc, cfg)
    t = np.asarray(cfg.get("arm_move_m", [0, 0, 0]), float)
    ar = ARest(cfg) if cfg.get("a_rest") else None
    tight_d = None
    if ar is not None:
        assert list(cfg.get("zero_parts", ())) == ["hand"] and cfg.get("zero_ring") is None and not np.any(t), \
            "a_rest: the arm and shoulder are the fit's (zero_parts [hand], zero_ring null, no arm_move_m)"
        print("a_rest", cfg["a_rest"], "A's turns", {k: v for k, v in ar.turns.items() if "arm" in k or "clav" in k or "hand" in k}, flush=True)
    for tier in tiers:
        V0, Vf, z = bodies(spec, fit_spec, tier, A, baked)
        ring = bt.boundary_ring(z["Q"], len(V0))
        M = Mc if tier == "close" else np.clip(carry_to_tier(Mc[:, None], "close", tier)[:, 0], 0.0, 1.0)
        M = np.where(M < 1e-3, 0.0, np.where(M > 1 - 1e-3, 1.0, M))
        if ar is None:
            ts = t[None, :] * np.stack([np.where(z["V"][:, 0] >= 0, 1.0, -1.0), np.ones(len(V0)), np.ones(len(V0))], 1)
        else:
            parts = list(map(str, z["parts"]))
            Vh = ar.hand_field(V0, Vf, z["part"] == parts.index("hand"), z["V"][:, 0])
            Vf, dist = ar.carry(Vf)
            ts = Vh - V0
            print(tier, "a_rest carry: fit to A p50/p95/max mm", np.round(np.percentile(dist, [50, 95, 100]) * 1e3, 2).tolist(), flush=True)
            if cfg.get("a_tight"):
                if tier == "close":
                    Vt, wt, stats = ar.tight(Vf, z, cfg["a_tight"])
                    tight_d = Vt - Vf
                    print(tier, "a_tight (lam, core p50, p95 mm, rejected):", stats, "points", int((wt > 1e-4).sum()), flush=True)
                else:
                    assert tight_d is not None, "a_tight: close first (play takes close's move)"
                    tight_d = carry_to_tier(tight_d, "close", tier)
                Vf = Vf + tight_d
        D = M[:, None] * (Vf - V0) + (1.0 - M[:, None]) * ts
        ring_max = float(np.abs(D[ring]).max())
        assert ring_max < 1e-4, ("the fit is not the head's on the ring", ring_max)
        D[ring] = 0.0
        about = (f"made_by: python tools/body/her_a_target.py {os.path.relpath(os.path.abspath(spec_path), REPO)}".replace("\\", "/") +
                 f" (fit {cfg['fit_spec']}, band_m {cfg['band_m']}, zero_parts {cfg.get('zero_parts', 'arm..hand')}, zero_ring {cfg.get('zero_ring')}, arm_move_m {list(t)}, a_rest {cfg.get('a_rest')})")
        extra = {}
        if ar is not None:
            # A's own joints at this pose (her left; the skeleton mirrors): the girdle and arm skin are A's, so are they
            extra["joints"] = np.array(json.dumps({c: [round(float(x), 6) for x in ar.t1["bones"][b][0]] for c, b in (
                ("joint-l-clavicle", "clavicle_l"), ("joint-l-shoulder", "upperarm_l"), ("joint-l-elbow", "lowerarm_l"), ("joint-l-hand", "hand_l"))}))
        np.savez_compressed(os.path.join(out_dir, OUT_FILE.format(tier=tier)), D=D.astype(np.float32), M=M.astype(np.float32),
                            topology=np.array(bt.topo_sha(z)), about=np.array(about), **extra)
        print(tier, "D max mm", round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 1), "M<1", int((M < 1).sum()), "of", len(M), flush=True)


def maps(spec_path):
    """A's paint carried once: topo_bake on the carrier (the fit's build, on A) into base/targets/her_a_maps."""
    import topo_bake
    spec = load_spec(spec_path)
    cfg = spec["her_a"]
    fit = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    work = os.path.join(HERE, "out", "her_a_maps_work")
    # (spec her_a "maps_bake", P1 R1 round 13: "carrier" a build whose surface is the target's (a published round: the
    # girdle and arm at A's rest are A's), "a_rest" A posed so (default her_a's a_rest), "mirror" and "form_near" as
    # topo_bake.run has them; without it the round 10 carry)
    mb = cfg.get("maps_bake", {})
    carrier = mb.get("carrier", cfg["carrier"])
    r, _ = topo_bake.run(os.path.join(REPO, carrier), work, size=int(fit["bake"].get("size", 2048)), pose=fit["bake"].get("pose"),
                         a_rest=mb.get("a_rest", cfg.get("a_rest")) if mb else None, mirror=mb.get("mirror", "avg"),
                         form_near=mb.get("form_near"), a_normals=mb.get("a_normals"))
    dest = os.path.join(TARGETS, "her_a_maps")
    os.makedirs(dest, exist_ok=True)
    for k in topo_bake.SOURCE_MAPS:
        shutil.copy2(os.path.join(work, f"{k}.png"), os.path.join(dest, f"{k}.png"))
    r = {k: r[k] for k in ("version", "size", "covered", "projection", "normal_inverted_texels", "normal_form", "mirror", "a_normals", "gates") if k in r}
    r["made_by"] = "tools/body/her_a_target.py --maps, from " + carrier + (" (her_a maps_bake " + json.dumps(mb) + ")" if mb else "")
    with open(os.path.join(dest, "bake.json"), "w") as f:
        json.dump(r, f, indent=1, default=float)
    print("maps", r["gates"]["pass"], r["projection"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--maps", action="store_true")
    ap.add_argument("--tiers", default="close,play")
    ap.add_argument("--out-dir", default=TARGETS, help="a trial's folder (the spec's \"target_files\" reads it); default the shipped base/targets")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    make(a.spec, a.tiers.split(","), a.out_dir)
    if a.maps:
        maps(a.spec)


if __name__ == "__main__":
    main()
