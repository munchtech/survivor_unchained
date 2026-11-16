"""The kit's helm (lane D, 16 Nov 2026): kit_helm for tools/armor/kit_build.py (build.json "module": "kit_helm", its
own build as kit_upper's). Grown from kit_upper.helm (lead 1's recipe, never built), its helpers imported from there.

    python tools/armor/kit_build.py kit_helm      (or python tools/armor/kit_helm.py kit_helm)

The design (survivorsunchained_inputs/gpt_sol/kit/02_pieces.png, top left): an open-face helm. A dome over her head
and her braid's hair cap, a low crest rib front to back, a brow band round the whole helm (a V at the front over her
brows, a V at the back) with gold rims and a gold knot-work braid on it and a gold knot at the front V, a wide face
opening (rounded top corners, never over her brows, eyes, nose or mouth), straight cheek guards hanging to her jaw
with a little flare, a neck guard behind ending in a V over her nape, gold rolled rims round every edge, gold rivets.

RIGID BY CLEARANCE: the whole helm is ONE node (`helm_rigid`, a primitive a material) that rides her Head joint only
(piece params.rigid_drop: neck, spine and clavicle weights dropped from its blend; her head and hair ride Head, so
what clears at rest clears in every pose). The shell stands off the OUTERMOST of her head and her hair above
`hair_above` (rays cast from outside in: the outer hair cards, not the first card off her scalp), dilated, smoothed,
+ clear; below `wall_y` it hangs as a wall (its horizontal reach never shrinks going down, + flare), so a guard never
tucks in under her jaw or round her nape. Hair kept (no "hair": "hide"): her braid falls from under the neck guard.
Every measure is in godot/art/armor/src/kit_helm/build.json.
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_build as kb  # noqa: E402
import kit_hips as kh  # noqa: E402
from kit_upper import PEOPLE, fill_nan, icosphere, interp_table, loops_ordered, mesh_of, path_bead, ring_max, \
    smooth_scalar, write_multi  # noqa: E402
from native_build import Part, U, raycast, rivet, vertex_normals  # noqa: E402


def cast_outer(O, D, meshes, tmax):
    """Per ray from O along D the OUTERMOST surface of any mesh within tmax (cast from O + D tmax back in): t, nan none."""
    S = O + D * tmax
    T = np.full(len(D), np.nan)
    for V, F in meshes:
        t, _ = raycast(V, F, S, -D, tmax, chunk=48)
        T = np.fmax(T, tmax - t)
    return T


def smin(a, b, r):
    """A smooth minimum (corners rounded over about r)."""
    if r <= 0:
        return np.minimum(a, b)
    m = np.minimum(a, b)
    return m - r * np.log(np.exp(-(a - m) / r) + np.exp(-(b - m) / r))


class HelmDome:
    """The helm's shell over rays from O along unit directions D (an icosphere's): the outermost head/hair distance
    t, the envelope rho (dilated, smoothed, + clear, then the hanging wall below wall_y), points P = O + D rho."""

    def __init__(self, O, Vs, Fs, keep, meshes, hk):
        self.O = O = np.asarray(O, float)
        Vk = np.nonzero(keep)[0]
        remap = -np.ones(len(Vs), int)
        remap[Vk] = np.arange(len(Vk))
        self.D, self.F = D, F = Vs[Vk], remap[Fs[keep[Fs].all(1)]]
        self.t = cast_outer(O, D, meshes, hk.get("tmax", 0.3))
        t0 = fill_nan(self.t, F)
        r = ring_max(t0, F, hk["dilate"])
        r = smooth_scalar(r, F, hk["smooth"])
        base = np.maximum(r, t0) + hk["clear"]
        rho = base.copy()
        # (the keel: the dome's top drawn to a low ridge along the midline, the sheet's front view an ogive)
        kl = hk.get("keel")
        if kl:
            rho = rho + (kl["h"] * np.clip(1 - np.abs(D[:, 0]) / kl["w"], 0, 1) ** 2
                         * np.clip((D[:, 1] - kl["y0"]) / (1 - kl["y0"]), 0, 1)
                         * np.where(D[:, 2] > 0, 1.0, kl.get("back", 1.0)))
        # (the hanging wall: below wall_y each meridian's horizontal reach is at least its reach at wall_y, less wall_in
        # per metre down (the guards come in a little under the band), plus flare per metre below flare_y)
        hd = np.hypot(D[:, 0], D[:, 2])
        psi = np.degrees(np.arctan2(np.abs(D[:, 0]), D[:, 2]))
        wy = hk["wall_y"]
        w_in, fy, fl = hk.get("wall_in", 0.0), hk.get("flare_y", wy), hk.get("flare", hk.get("wall_flare", 0.0))
        P = O + D * rho[:, None]
        near = (P[:, 1] > wy - 0.004) & (P[:, 1] < wy + 0.012)
        bins = np.arange(0, 181, 5.0)
        H = np.array([np.max(np.hypot(P[near & (np.abs(psi - b) <= 6), 0], P[near & (np.abs(psi - b) <= 6), 2] - O[2]),
                             initial=0.0) for b in bins])
        H = np.where(H > 0, H, np.interp(bins, bins[H > 0], H[H > 0]))
        for _ in range(4):
            P = O + D * rho[:, None]
            low = (P[:, 1] < wy) & (hd > 0.05)
            req = np.interp(psi, bins, H) - w_in * (wy - P[:, 1]) + fl * np.maximum(fy - P[:, 1], 0.0)
            need = req / np.maximum(hd, 0.05)
            rho = np.where(low, np.maximum(rho, need), rho)
        rs = smooth_scalar(rho, F, hk.get("wall_smooth", 6))
        self.rho = np.maximum(rs, base)
        self.P = O + D * self.rho[:, None]
        self.psi, self.hd = psi, hd

    def cut(self, g):
        """The shell patch where g > 0 (g per point), cut on its edges; its outward directions."""
        V, F = kh.clip(self.P, self.F, g)
        V, F = kh.weld(V, F)
        N = vertex_normals(V, F)
        N = np.where(((N * (V - self.O)).sum(1) < 0)[:, None], -N, N)
        return V, F, U(N)


def _psi(P, O):
    return np.degrees(np.arctan2(np.abs(P[:, 0]), P[:, 2] - O[2]))


def helm(cfg, ref=None):
    gold, steel = cfg["mat"]["trim"], cfg["mat"]["plate"]
    rim, hk = cfg["rim"], cfg["helm"]
    body = os.path.join(PEOPLE, "heroine.glb")
    head = mesh_of(body, "HeroineHead")
    hv, hf = mesh_of(os.path.join(PEOPLE, f"{hk['hair']}.gltf"), hk["hair_node"])
    hc = hv[hf].mean(1)
    hair = (hv, hf[hc[:, 1] > hk["hair_above"]])
    O = np.array(hk["centre"], float)
    Vs, Fs = icosphere(hk.get("subdiv", 5))
    keep = Vs[:, 1] > hk.get("keep_dy", -0.9)
    dome = HelmDome(O, Vs, Fs, keep, [head, hair], hk)
    bd = hk["band"]
    # (the cut on the shell's own points: the face opening (its top the band's lower edge, an arch over each brow
    # meeting in a V; its sides the guards' inner edges, stepping in under the cheekbones), the bottom line)
    x, y, z = dome.P[:, 0], dome.P[:, 1], dome.P[:, 2]
    psi = dome.psi
    ybot = interp_table(hk["bottom"], psi)
    fo = hk["face"]
    top = interp_table(bd["bottom"], psi)
    half = interp_table(fo["half_w"], y)
    s_face = smin(top - y, half - np.abs(x), fo.get("corner_r", 0.0))  # > 0 inside the face opening (front only)
    s_face = np.where(z - O[2] > fo["z_min"], s_face, -1.0)
    g = np.minimum(y - ybot, -s_face)
    V, F, N = dome.cut(g)
    th = cfg["thick"]
    S, Gd = [kh.shell("helm", steel, V, F, N, th)], []
    Pout = V + N * th
    nref = kh.Normals(Pout, N)
    loops = loops_ordered(V + N * (th * 0.5), F)
    for L in loops:
        Gd.append(path_bead("helm_rim", gold, L, nref, rim, 0.0, True))
    edge = np.vstack(loops)

    def at(ps, ys, need=True):
        """The shell's outer surface at azimuths ps (deg, 0 front, + her left) and heights ys: horizontal rays from
        the helm's vertical axis (points, which hit)."""
        ps, ys = np.radians(np.atleast_1d(ps)), np.atleast_1d(ys).astype(float)
        D = np.c_[np.sin(ps), np.zeros_like(ps), np.cos(ps)]
        Oh = np.c_[np.zeros_like(ps), ys, np.full_like(ps, O[2])]
        t, _ = raycast(Pout, F, Oh, D, 0.3, chunk=48)
        ok = np.isfinite(t)
        assert ok.all() or not need, f"{np.count_nonzero(~ok)} of {len(ok)} points off the shell"
        return Oh[ok] + D[ok] * t[ok, None], ok

    # crest: a low rib front to back over the top, tallest at the front (the sheet's ridge, plain steel)
    cr = hk["crest"]
    ang = np.radians(np.linspace(cr["from"], cr["to"], 120))
    Dc = np.c_[np.zeros_like(ang), np.cos(ang), np.sin(ang)]
    t, _ = raycast(Pout, F, np.broadcast_to(O, Dc.shape).copy(), Dc, 0.3, chunk=48)
    base = O + Dc[np.isfinite(t)] * t[np.isfinite(t), None]
    n = nref.closest(base)[1]
    sfrac = np.linspace(0, 1, len(base))
    w = np.clip(np.minimum(sfrac, 1 - sfrac) / cr.get("taper", 0.12), 0, 1) ** 0.5
    hgt = cr["h_back"] + (cr["h"] - cr["h_back"]) * sfrac ** cr.get("rise", 1.0)  # (from the back up to the front)
    side = np.tile([1.0, 0, 0], (len(base), 1))
    hw = (cr["w"] / 2) * (0.55 + 0.45 * w)
    sec = [base - n * 0.0008 + side * (u * hw)[:, None] + n * (hgt * v * w)[:, None]
           for u, v in ((-1, 0.0), (-0.8, 0.8), (-0.3, 1.0), (0.3, 1.0), (0.8, 0.8), (1, 0.0))]
    S.append(kb.slab("crest", steel, np.stack(sec, 0), np.repeat(n[None], len(sec), 0), 0.0012))
    # brow band: a raised steel band round the whole helm on the shell (its lower edge the face opening's top, its
    # upper edge a chevron rising to the front; tall at the front, narrow behind), gold rims, a knot-work braid
    ps = np.linspace(-180, 180, 360, endpoint=False)
    ylo = interp_table(bd["bottom"], np.abs(ps)) + bd.get("lift", 0.0)
    yhi = interp_table(bd["top"], np.abs(ps))
    fr = np.linspace(0, 1, bd.get("rows", 9))
    rows = [at(ps, ylo + (yhi - ylo) * f)[0] for f in fr]
    nb = np.stack([nref.closest(r_)[1] for r_ in rows], 0)
    Pin = np.stack(rows, 0) + nb * 0.0003
    S.append(kb.slab("band", steel, Pin, nb, bd["thick"], closed_c=True))
    Bo = Pin + nb * bd["thick"]
    bref = kh.Normals(Bo.reshape(-1, 3), nb.reshape(-1, 3))
    brim = {**rim, "w": bd["rim_w"], "h": bd["rim_h"]}
    Gd.append(path_bead("band_rim", gold, Bo[-1], bref, brim, 0.0, True))
    lo = rows[0]
    # (the band's lower rim where the face opening's own rim is not already on that edge)
    from scipy.spatial import cKDTree
    far = cKDTree(edge).query(lo)[0] > bd.get("rim_gap", 0.007)
    if far.all():
        Gd.append(path_bead("band_rim", gold, Bo[0], bref, brim, 0.0, True))
    else:
        k0 = int(np.argmin(far))
        order = np.roll(np.arange(len(far)), -k0)
        run, runs = [], []
        for i in order:
            if far[i]:
                run.append(i)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for r_ in runs:
            if len(r_) > 2:
                Gd.append(path_bead("band_rim", gold, Bo[0][r_], bref, brim, 0.0, False))
    # (the knot-work: two gold strands crossing along the band's middle, a lane of fixed height)
    s = np.linspace(0, 1, len(ps), endpoint=False)
    ymid = ylo + (yhi - ylo) * bd.get("knot_at", 0.5)
    for ph in (0.0, np.pi):
        yk = ymid + bd["knot_amp"] * np.sin(2 * np.pi * bd["waves"] * s + ph)
        E = at(ps, yk)[0]
        E = E + nref.closest(E)[1] * (bd["thick"] + 0.0003)
        Gd.append(path_bead("band_knot", gold, E, bref, {**rim, "w": bd["knot_w"], "h": bd["knot_h"], "step": 0.0025},
                            0.0, True))
    # the gold knot at the front: a big faceted diamond on the band's centre (and any more, smaller, over it)
    kn = hk["knot"]
    y0 = interp_table(bd["bottom"], [0.0])[0] + bd.get("lift", 0.0)
    y1 = interp_table(bd["top"], [0.0])[0]
    for at_, w_, h_, d_ in [(kn.get("at", 0.5), kn["w"], kn["h"], kn["depth"])] + [tuple(m) for m in kn.get("more", [])]:
        c = at([0.0], [y0 + (y1 - y0) * at_])[0][0]
        cn = nref.closest(c[None])[1][0]
        Gd.append(kb.diamond(c + cn * (bd["thick"] + kn.get("lift", 0.0)), cn, np.array([0, 1.0, 0]), w_, h_, d_,
                             "helm_knot", gold))
    # knot-work on the guards (the sheet's back: a braid down each side of the neck guard; a short one on each cheek
    # guard): two crossing gold strands along a path on the shell through (azimuth, height) points, mirrored
    for gk in hk.get("guard_knots", []):
        cp = np.array(gk["path"], float)
        u = np.linspace(0, 1, gk.get("n", 60))
        k = np.linspace(0, 1, len(cp))
        C = at(np.interp(u, k, cp[:, 0]), np.interp(u, k, cp[:, 1]))[0]
        cn = nref.closest(C)[1]
        sd = U(np.cross(cn, np.gradient(C, axis=0)))
        env = np.sin(np.pi * u) ** 0.5
        for ph in (0.0, np.pi):
            E = C + sd * (gk["amp"] * env * np.sin(2 * np.pi * gk["waves"] * u + ph))[:, None]
            E = at(np.degrees(np.arctan2(E[:, 0], E[:, 2] - O[2])), E[:, 1])[0]  # (back on the shell)
            E = E + nref.closest(E)[1] * 0.0004
            for sg in (1, -1):
                Gd.append(path_bead("guard_knot", gold, E * [sg, 1, 1], nref,
                                    {**rim, "w": gk.get("w", 0.003), "h": gk.get("h", 0.0014), "step": 0.0025},
                                    0.0, False))
    # rivets (the cheek guards, the neck guard): (azimuth deg, height) pairs, mirrored
    for p_, yy in hk["rivets"]:
        pts, ok = at([p_], [yy])
        for p in pts:
            nn = nref.closest(p[None])[1][0]
            for sg in ((1,) if abs(p[0]) < 1e-3 else (1, -1)):
                Gd.append(rivet(p * [sg, 1, 1], nn * [sg, 1, 1], r=hk["rivet_r"], h=hk["rivet_h"], name="helm_rivet",
                                material=gold))
    by = {}
    for p in S + Gd:
        by.setdefault(p.material, []).append(p)
    return {"helm_rigid": [Part.join("helm_rigid", mm, q) for mm, q in by.items()]}, [head, hair]


def build(pid, cfg=None):
    from native_build import Ref
    d = os.path.join(kb.SRC, pid)
    cfg = cfg or json.load(open(os.path.join(d, "build.json"), encoding="utf-8"))
    mats = json.load(open(kb.MATS, encoding="utf-8"))
    for m in cfg["mat"].values():
        assert m in mats, f"material {m} not in outfit_materials.json"
    groups, under = helm(cfg)
    V = np.vstack([under[0][0], under[1][0]])
    T = np.vstack([under[0][1], under[1][1] + len(under[0][0])])
    cref = Ref(V, T)
    for ps in groups.values():
        for p in ps:
            p.N = vertex_normals(p.P, p.T)
    write_multi(os.path.join(d, f"{pid}.glb"), groups, {"kit_build": {"piece": pid}})
    piece = {k: v for k, v in cfg["piece"].items() if k != "layer"}
    piece = {"id": piece["id"], "name": piece["name"], "slot": piece["slot"], "style": "mesh",
             "params": {"file": f"{pid}.glb", **cfg.get("params", {})},
             **{k: v for k, v in piece.items() if k not in ("id", "name", "slot")},
             "layer": cfg["piece"].get("layer", 1), "body_sha1": hashlib.sha1(open(kb.BODY, "rb").read()).hexdigest()}
    with open(os.path.join(d, "piece.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(piece, f, indent=1)
        f.write("\n")
    rep = {"tris": int(sum(len(p.T) for ps in groups.values() for p in ps)),
           "by_node": {nm: {p.material: int(len(p.T)) for p in ps} for nm, ps in groups.items()},
           "min_clear_mm (head + hair)": {f"{nm}.{p.material}": round(float(kb.clearance(cref, p).min()) * 1000, 2)
                                          for nm, ps in groups.items() for p in ps}}
    print(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    build(sys.argv[1])
