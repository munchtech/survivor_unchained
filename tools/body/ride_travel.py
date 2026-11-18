"""How far a skin patch travels against a RIGID ride over a pose sequence: can a rigid plate sit on it?

A rigid part (a shoulder cop) rides one rigid motion M_f per frame (a bone, a turn about a joint, anything rigid).
The skin under it does not: per patch point, per frame

    travel = | p_f - M_f x0 |                 the skin point against the place the ride carries its rest point to
    sink   = (p_f - M_f x0) . n_f             its part along the skin's posed normal: + = the skin comes UP through the
                                              plate (the plate sinks into her; the gear builder's sign), - = a gap opens
    sink_nn                                   the gear builder's own form (native_travel.on_skin / sink): the carried
                                              point's height over the NEAREST skin vertex of the moving surface along
                                              that vertex's normal, less the same at rest; the most it comes down

and per patch the FLOOR: the least-squares best rigid motion of the patch from rest, fitted per frame (Kabsch, area
weights). Its residual is what no rigid plate can remove, whatever it rides.

The core (rigid_fit, bone_ride, sphere_ride, measure, stats) takes any surface as a Track: rest and posed patch
points and normals, the skin cloud about them, and rides {name: [F, 4, 4]}. HER below is the data for her shoulder
(body B): the patch under the gear lead's spaulder cop, the four fight clips, the bones a cop could ride, and three
surface providers on the same kinematics:

    old   today's weights, bare linear blend (no corrective shapes): what the gear builder reads
    pub   today's published surface (linear blend + corrective shapes)
    new   the composed carried TARGET (carried_target.Her.target / compose): what the new fit will AIM at. No new
          weights exist yet; this is the ceiling of the fit, not a skin
    a     her old body A, posed by B's bone turns, read at the points of A's rest surface nearest B's patch points

    python tools/body/ride_travel.py                      the table (about 4 minutes), also out/ride_travel/table.json
    python tools/body/ride_travel.py --surfaces old pub   only those (seconds)
    python tools/body/ride_travel.py --sides l --clips sword_heavy cast_flick

The patch: the frame over her shoulder top, the crest line under it and the footprint are COPIED from the gear
lead's builder (gear-p2 tools/armor/native_build.py Frame / raycast / near, native_spaulder.py ShoulderFrame /
crest_line / crest_drop / footprint) so nothing is imported from that worktree; the box is the cop's of
plate_spaulders_plain/build.json (s -88..+36 mm, theta 21..172, rho < 90 mm). It is the cop's BOX, not its arched
outline, and the skin under it, not the cop's inner-face grid: comparable in kind, not point for point.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import types
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

HER = {
    "clips": ("daggers_heavy", "run_reaver", "sword_heavy", "cast_flick"),      # native_travel.FOUR: 91 frames
    "singles": (("sword_heavy", 13), ("cast_flick", 6)),                        # the gear lead's two worst frames
    "sides": ("l", "r"),
    "frame": {"from": "upperarm_{s}", "to": "lowerarm_{s}"},                    # build.json "frame"
    # the cop's box (build.json "lames" edges[0..1], theta); keep / past / ease: native_spaulder.layout's crest line
    "patch": {"s": (-0.088, 0.036), "theta": (21.0, 172.0), "rmax": 0.09, "keep": 0.036, "past": 0.008, "ease": 0.006},
    "reach": 0.07,                                                              # the skin cloud about the patch (sink_nn)
    # single bones a cop could ride (B's names; on A only the ones A has, "clavicle" = the upper arm's parent)
    "rides": {"upperarm": "upperarm_{s}", "clavicle": "clavicle_{s}", "share": "upperarm_share_{s}",
              "delt": "delt_{s}", "scap": "scap_{s}"},
    # a turn about the shoulder joint: t of the way from the clavicle's turn to the upper arm's (0 and 1 are the bones)
    "sphere": {"a": "clavicle_{s}", "b": "upperarm_{s}", "t": (0.25, 0.5, 0.75)},
    # where on the patch (the frame's s in m, theta in degrees: 0 front, 90 her outer side / top, 180 back)
    "zones": {"neck_end": lambda s, th: s < -0.045, "cap_top": lambda s, th: (s >= -0.045) & (th >= 60) & (th <= 130),
              "front": lambda s, th: (s >= -0.045) & (th < 60), "back": lambda s, th: (s >= -0.045) & (th > 130)},
    "limit_mm": 5.0,
}
KINDS = ("old", "pub", "new", "a")
HEAD = {"old": "OLD lbs", "pub": "PUB (+shapes)", "new": "NEW target", "a": "A"}


# ------------------------------------------------------------------------------------------------ the core

def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def rigid_fit(X0, X, w=None):
    """[4, 4]: the least-squares rigid motion (proper rotation + translation) taking X0 [n, 3] onto X [n, 3]."""
    w = np.ones(len(X0)) if w is None else np.asarray(w, float)
    w = w / w.sum()
    c0, c = w @ X0, w @ X
    H = ((X0 - c0) * w[:, None]).T @ (X - c)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    M = np.eye(4)
    M[:3, :3] = Vt.T @ D @ U.T
    M[:3, 3] = c - M[:3, :3] @ c0
    return M


def bone_ride(G, G0, k):
    """[F, 4, 4]: bone k's rigid motion from rest over the frames' globals G [F, bones, 4, 4]."""
    return G[:, k] @ np.linalg.inv(G0[k])


def sphere_ride(Ma, Mb, c0, c, t):
    """[F, 4, 4]: a turn about a joint (rest c0, posed c [F, 3]): t of the way from ride Ma's turn to ride Mb's."""
    Ra, Rb = Rotation.from_matrix(Ma[:, :3, :3]), Rotation.from_matrix(Mb[:, :3, :3])
    R = (Ra * Rotation.from_rotvec(t * (Ra.inv() * Rb).as_rotvec())).as_matrix()
    M = np.tile(np.eye(4), (len(R), 1, 1))
    M[:, :3, :3] = R
    M[:, :3, 3] = c - R @ c0
    return M


def carry(M, X0):
    return np.einsum("fij,nj->fni", M[:, :3, :3], X0) + M[:, None, :3, 3]


class Track:
    """One surface's patch over a pose sequence: P0 / N0 [n, 3] at rest, P / N [F, n, 3] posed, the skin cloud about it
    C0 / CN0 [m, 3], C / CN [F, m, 3], area [n] (the fit's weights), rides {name: [F, 4, 4]}."""

    def __init__(self, P0, N0, C0, CN0, area=None):
        self.P0, self.N0, self.C0, self.CN0 = P0, N0, C0, CN0
        self.area = np.ones(len(P0)) if area is None else area
        self.P, self.N, self.C, self.CN, self.rides = [], [], [], [], {}

    def add(self, P, N, C, CN):
        self.P.append(P), self.N.append(N), self.C.append(C), self.CN.append(CN)

    def close(self):
        self.P, self.N, self.C, self.CN = (np.array(x) for x in (self.P, self.N, self.C, self.CN))
        self.rides["FLOOR fit"] = np.array([rigid_fit(self.P0, p, self.area) for p in self.P])
        return self


def measure(tr, M):
    """(travel, sink, sink_nn) [F, n] in m of a Track's patch against the ride M [F, 4, 4] (see the module's head)."""
    Q = carry(M, tr.P0)
    d = tr.P - Q
    travel, sink = np.linalg.norm(d, axis=2), (d * tr.N).sum(2)
    j0 = cKDTree(tr.C0).query(tr.P0)[1]
    off0 = ((tr.P0 - tr.C0[j0]) * tr.CN0[j0]).sum(1)
    nn = np.zeros_like(sink)
    for f in range(len(Q)):
        j = cKDTree(tr.C[f]).query(Q[f])[1]
        nn[f] = off0 - ((Q[f] - tr.C[f][j]) * tr.CN[f][j]).sum(1)
    return travel, sink, nn


def stats(m, rows, sel=None):
    """Over the frames `rows` (and the patch points `sel`): each point's largest travel -> p50 / p95 / max, the largest
    sink and sink_nn, mm; "at": the row of the largest travel."""
    travel, sink, nn = (x[rows] if sel is None else x[rows][:, sel] for x in m)
    t = travel.max(0)
    return {"p50": float(np.percentile(t, 50)) * 1e3, "p95": float(np.percentile(t, 95)) * 1e3, "max": float(t.max()) * 1e3,
            "sink": float(max(sink.max(), 0.0)) * 1e3, "sink_nn": float(max(nn.max(), 0.0)) * 1e3,
            "at": int(np.asarray(rows)[travel.max(1).argmax()])}


# ------------------------------------------------- the patch (copied from gear-p2 tools/armor, see the module's head)

class ShoulderFrame:
    """native_build.Frame + native_spaulder.ShoulderFrame: c + s a + rho (cos th f + sin th o), theta 0 front, 90 her
    outer side; past the joint the centres are let down by drop(s) so they stay under her shoulder's crest."""

    def __init__(self, c, tip, hand, front=(0, 0, 1)):
        self.c, self.hand = np.asarray(c, float), hand
        a = np.asarray(tip, float) - self.c
        self.a = a / np.linalg.norm(a)
        f = np.asarray(front, float)
        self.f = unit(f - self.a * (f @ self.a))
        o = np.cross(self.a, self.f)
        self.o = o if o[0] * hand > 0 else -o
        self.ds, self.dd = np.zeros(2), np.zeros(2)

    def cyl(self, P):
        d = np.asarray(P, float) - self.c
        s = d @ self.a
        x, y = d @ self.f, d @ self.o + np.interp(s, self.ds, self.dd)
        return s, np.degrees(np.arctan2(y, x)), np.hypot(x, y)


def raycast(V, T, O, D, tmax=1.0, chunk=96):
    """native_build.raycast: first hit t of each ray O + t D on the mesh, nan where none within tmax."""
    v0 = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - v0, V[T[:, 2]] - v0
    out = np.full(len(O), np.nan)
    for a in range(0, len(O), chunk):
        o, d = O[a:a + chunk, None, :], D[a:a + chunk, None, :]
        h = np.cross(d, e2[None])
        det = (e1[None] * h).sum(-1)
        ok = np.abs(det) > 1e-14
        inv = 1.0 / np.where(ok, det, 1.0)
        sv = o - v0[None]
        u = (sv * h).sum(-1) * inv
        q = np.cross(sv, e1[None])
        v = (d * q).sum(-1) * inv
        t = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-6) & (t < tmax)
        t = np.where(hit, t, np.inf).min(1)
        out[a:a + chunk] = np.where(np.isfinite(t), t, np.nan)
    return out


def crest_line(V, T, fr, s0, s1, ds=0.002, far=0.25):
    """native_spaulder.crest_line: (s, r) her skin's height over the arm's axis along its crest (theta 90)."""
    s = np.arange(s0, s1 + 0.5 * ds, ds)
    sv, _, rho = fr.cyl(V)
    Tn = T[((sv > s0 - 0.04) & (sv < s1 + 0.04) & (rho < 2 * far))[T].any(1)]
    Tn = Tn[(V[Tn][:, :, 0] * fr.hand > -0.01).all(1)]
    t = raycast(V, Tn, fr.c + s[:, None] * fr.a + far * fr.o, np.tile(-fr.o, (len(s), 1)), 3 * far)
    ok = np.isfinite(t)
    return s, np.interp(s, s[ok], far - t[ok])


def crest_drop(s, r, keep, ease=0.006, blend=0.02):
    """native_spaulder.crest_drop: how far the centres go under the axis to stay her skin's depth at `keep` under r(s)."""
    d = ndimage.gaussian_filter1d(np.maximum(float(np.interp(keep, s, r)) - r, 0.0), ease / (s[1] - s[0]), mode="nearest")
    k = np.clip((keep - 0.004 - s) / blend, 0.0, 1.0)
    return d * k * k * (3 - 2 * k)


def shoulder_frames(V, T, heads, cfg):
    """{side: ShoulderFrame}: native_spaulder.layout's frames (one drop for her two sides, the larger)."""
    pc = cfg["patch"]
    frs = {s: ShoulderFrame(heads(cfg["frame"]["from"].replace("{s}", s)), heads(cfg["frame"]["to"].replace("{s}", s)), h)
           for s, h in (("l", 1), ("r", -1))}
    crest = {s: crest_line(V, T, fr, pc["s"][0] - pc["past"] - 0.05, pc["keep"]) for s, fr in frs.items()}
    drop = np.maximum(*(crest_drop(*crest[s], pc["keep"], pc["ease"]) for s in "lr"))
    for s, fr in frs.items():
        fr.ds, fr.dd = crest[s][0], drop
    return frs


def footprint(V, T, fr, s0, s1, t0, t1, rmax=0.09):
    """native_spaulder.footprint: the vertices of the triangles lying wholly in the box, on the frame's side of her."""
    s, th, rho = fr.cyl(V)
    ok = (V[:, 0] * fr.hand > 0) & (th >= t0) & (th <= t1) & (rho < rmax) & (s >= s0) & (s <= s1)
    return np.unique(T[ok[T].all(1)])


def vertex_area(V, T):
    ta = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 2
    A = np.zeros(len(V))
    np.add.at(A, T.reshape(-1), np.repeat(ta / 3, 3))
    return A


# ------------------------------------------------------------------------------------- her: the providers, the table

def her_tracks(cfg, sides, kinds, clips, log=print):
    """({(kind, side): Track}, frames [(clip, frame)], patches {side: {"ids", "s", "th"}})."""
    import carried_target as ct
    import deform_audit as da
    import region_shape as rs
    import region_target as rt
    from surfdist import Surface
    h = ct.Her(verbose=False)
    B, A, p = h.bd, h.Ab, h.bd.p
    I, AI = p.index, A.p.index
    T, AT = np.asarray(B.T, np.int64), np.asarray(A.T, np.int64)
    N0, AN0 = B._normals(B.V0), A._normals(A.V0)
    frs = shoulder_frames(B.V0, T, B.head, cfg)
    pc, area = cfg["patch"], vertex_area(B.V0, T)
    tree, atree = cKDTree(B.V0), cKDTree(A.V0)
    pat, out = {}, {}
    for s in sides:
        ids = footprint(B.V0, T, frs[s], *pc["s"], *pc["theta"], pc["rmax"])
        cl = np.unique(np.concatenate(tree.query_ball_point(B.V0[ids], cfg["reach"])).astype(int))
        sv, th, _ = frs[s].cyl(B.V0[ids])
        pat[s] = {"ids": ids, "cloud": cl, "s": sv, "th": th}
        for k in kinds:
            if k != "a":
                out[k, s] = Track(B.V0[ids], N0[ids], B.V0[cl], N0[cl], area[ids])
        if "a" in kinds:        # A's material points under B's patch: the nearest points of A's rest surface
            q, _, tri, d = Surface(A.V0, AT).closest(B.V0[ids], k=16)
            tv = AT[tri]
            w = _bary(q, A.V0[tv])
            acl = np.unique(np.concatenate(atree.query_ball_point(q, cfg["reach"])).astype(int))
            pat[s].update({"a_tv": tv, "a_w": w, "a_cloud": acl, "a_d_mm": [float(np.percentile(d, 50)) * 1e3, float(d.max()) * 1e3]})
            out["a", s] = Track(q, unit((AN0[tv] * w[:, :, None]).sum(1)), A.V0[acl], AN0[acl], area[ids])
            log(f"side {s}: patch {len(ids)} vertices (cloud {len(cl)}); A's rest surface lies {pat[s]['a_d_mm'][0]:.1f} mm (p50) /"
                f" {pat[s]['a_d_mm'][1]:.1f} mm (max) off B's patch points at rest")
        else:
            log(f"side {s}: patch {len(ids)} vertices (cloud {len(cl)})")
    frames, Gs, AGs, t0 = [], [], [], time.time()
    a_pose = types.SimpleNamespace(B=B, A=A)
    for c in clips:
        for f, _, G in B.clip_frames(da.load_clip(c), 1):
            frames.append((c, int(f)))
            Gs.append(np.array(G))
            Vp = rt.published(B, G)
            surf = {"pub": Vp}
            if "old" in kinds:
                surf["old"] = p._skin(G, {})
            if "new" in kinds:                      # carried_target.cmd_target's order: one side's target, then the whole
                h.target(G, "l", Vp)                # composed surface (both sides' regions and the neck) on every vertex
                surf["new"] = h.compose(G, Vp)
            for k in kinds:
                if k == "a":
                    continue
                Nv = B._normals(surf[k])
                for s in sides:
                    out[k, s].add(surf[k][pat[s]["ids"]], Nv[pat[s]["ids"]], surf[k][pat[s]["cloud"]], Nv[pat[s]["cloud"]])
            if "a" in kinds:
                Va, Ga = rs.Ctx.a_from_B(a_pose, G)     # A posed by B's bone turns of this frame
                AGs.append(np.array(Ga))
                Na = A._normals(Va)
                for s in sides:
                    q = pat[s]
                    out["a", s].add((Va[q["a_tv"]] * q["a_w"][:, :, None]).sum(1), unit((Na[q["a_tv"]] * q["a_w"][:, :, None]).sum(1)),
                                    Va[q["a_cloud"]], Na[q["a_cloud"]])
        log(f"  {c}: {sum(1 for x in frames if x[0] == c)} frames ({time.time() - t0:.0f} s)")
    Gs, AGs = np.array(Gs), np.array(AGs)
    for (k, s), tr in out.items():
        tr.close()
        nm = lambda x: x.replace("{s}", s)  # noqa: E731
        if k == "a":        # A's own bones, by role: the upper arm, its parent (the clavicle); A has none of B's helpers
            up = AI[A.role("upperarm", s)]
            idx, G, G0 = {"upperarm": up, "clavicle": A.p.parent[up]}, AGs, A.G0
            sa, sb = idx["clavicle"], up
        else:
            idx, G, G0 = {r: I[nm(b)] for r, b in cfg["rides"].items() if nm(b) in I}, Gs, B.G0
            sa, sb = I[nm(cfg["sphere"]["a"])], I[nm(cfg["sphere"]["b"])]
        fit = tr.rides.pop("FLOOR fit")
        for r, b in idx.items():
            tr.rides[r] = bone_ride(G, G0, b)
        for t in cfg["sphere"]["t"]:
            tr.rides[f"sphere {t:g}"] = sphere_ride(bone_ride(G, G0, sa), bone_ride(G, G0, sb), G0[sb][:3, 3], G[:, sb, :3, 3], t)
        tr.rides["FLOOR fit"] = fit
    return out, frames, pat


def _bary(q, tri):
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    v, w = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    return np.c_[1 - v - w, v, w]


def rebase(tr, rows, first, mask):
    """A Track of the frames `rows` measured from frame `first` (None: from rest) with the floor fitted on `mask` points."""
    t = Track(tr.P0, tr.N0, tr.C0, tr.CN0, tr.area)
    if first is not None:
        t.P0, t.N0, t.C0, t.CN0 = tr.P[first], tr.N[first], tr.C[first], tr.CN[first]
    t.P, t.N, t.C, t.CN = tr.P[rows], tr.N[rows], tr.C[rows], tr.CN[rows]
    for r, m in tr.rides.items():
        if r != "FLOOR fit":
            t.rides[r] = m[rows] if first is None else m[rows] @ np.linalg.inv(m[first])
    t.rides["FLOOR fit"] = np.array([rigid_fit(t.P0[mask], p[mask], t.area[mask]) for p in t.P])
    return t


def cell(st):
    return "       -                 " if st is None else f"{st['p50']:4.1f}/{st['p95']:4.1f}/{st['max']:4.1f} {st['sink']:4.1f} {st['sink_nn']:4.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--surfaces", nargs="+", default=list(KINDS), choices=KINDS)
    ap.add_argument("--sides", nargs="+", default=list(HER["sides"]), choices=["l", "r"])
    ap.add_argument("--clips", nargs="+", default=list(HER["clips"]))
    ap.add_argument("--ref", choices=["rest", "first"], default="rest", help="measure from rest, or from each clip's first frame")
    ap.add_argument("--patch", choices=["box", "cap_top", "neck_end"], default="box", help="the zone the floor is fitted on and travel reported on")
    ap.add_argument("--out", default=str(HERE / "out" / "ride_travel" / "table.json"))
    a = ap.parse_args()
    cfg, kinds = HER, [k for k in KINDS if k in a.surfaces]
    tracks, frames, pat = her_tracks(cfg, a.sides, kinds, a.clips)
    seqs = [(c, [i for i, (cc, _) in enumerate(frames) if cc == c]) for c in a.clips]
    seqs.append(("ALL", list(range(len(frames)))))
    seqs += [(f"{c}@{f}", [frames.index((c, f))]) for c, f in cfg["singles"] if (c, f) in frames]
    sel = {s: None for s in a.sides}
    if a.patch != "box":
        sel = {s: cfg["zones"][a.patch](pat[s]["s"], pat[s]["th"]) for s in a.sides}
    if a.ref == "rest" and a.patch == "box":
        M = {key: {r: measure(tr, m) for r, m in tr.rides.items()} for key, tr in tracks.items()}
    else:
        M = {}
        for (k, s), tr in tracks.items():
            mk = np.ones(len(tr.P0), bool) if sel[s] is None else sel[s]
            parts = []
            for c, rows in seqs[:len(a.clips)]:
                bt = rebase(tr, rows, rows[0] if a.ref == "first" else None, mk)
                parts.append({r: measure(bt, m) for r, m in bt.rides.items()})
            M[k, s] = {r: tuple(np.concatenate([pt[r][i] for pt in parts]) for i in range(3)) for r in parts[0]}
    rides = list(dict.fromkeys(r for key in M for r in M[key] if r != "FLOOR fit")) + ["FLOOR fit"]
    res = {"ref": a.ref, "patch": a.patch, "frames": len(frames), "limit_mm": cfg["limit_mm"], "rows": []}
    print("\ncells: travel p50/p95/max  sink  sink_nn   (mm; per patch point the largest over the frames; sink + = plate into her)")
    for s in a.sides:
        for name, rows in seqs:
            print(f"\nside {s}  {name} ({len(rows)} frame{'s' * (len(rows) != 1)})")
            print(f"  {'ride':12s}" + "".join(f" | {HEAD[k]:25s}" for k in kinds))
            for r in rides:
                st = {k: stats(M[k, s][r], rows, sel[s]) if r in M[k, s] else None for k in kinds}
                print(f"  {r:12s}" + "".join(f" | {cell(st[k])}" for k in kinds))
                for k in kinds:
                    if st[k]:
                        res["rows"].append({"side": s, "seq": name, "ride": r, "surface": k, **{x: round(y, 2) for x, y in st[k].items() if x != "at"},
                                            "at": list(frames[st[k]["at"]])})
    allr = list(range(len(frames)))
    print(f"\nwhere it sits (ALL frames; travel p95 / max mm by zone of the patch) and the {cfg['limit_mm']:g} mm line")
    for s in a.sides:
        zones = {z: fn(pat[s]["s"], pat[s]["th"]) for z, fn in cfg["zones"].items()}
        print(f"side {s}: zones " + ", ".join(f"{z} {int(m.sum())}" for z, m in zones.items()) + " points")
        for k in kinds:
            single = {r: stats(M[k, s][r], allr, sel[s]) for r in M[k, s] if r != "FLOOR fit"}
            best = min(single, key=lambda r: single[r]["max"])
            for r in (best, "FLOOR fit"):
                st = stats(M[k, s][r], allr, sel[s])
                zs = {z: stats(M[k, s][r], allr, m) for z, m in zones.items() if m.any()}
                at = frames[st["at"]]
                under = "UNDER" if st["max"] < cfg["limit_mm"] else "over"
                print(f"  {HEAD[k]:14s} {('best ride: ' + r) if r == best else r:22s} travel max {st['max']:5.1f} ({under} {cfg['limit_mm']:g}), sink {st['sink']:4.1f},"
                      f" worst at {at[0]}@{at[1]};  " + "  ".join(f"{z} {v['p95']:.1f}/{v['max']:.1f}" for z, v in zs.items()))
                res.setdefault("zones", []).append({"side": s, "surface": k, "ride": r, "best_single": r == best, "max": round(st["max"], 2), "sink": round(st["sink"], 2),
                                                    "at": list(at), **{z: [round(v["p95"], 2), round(v["max"], 2)] for z, v in zs.items()}})
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
