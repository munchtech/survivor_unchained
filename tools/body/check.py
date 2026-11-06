"""The body's CHECK command (docs/team/PIPELINE.md): every number a judge should not have to eyeball.

    python tools/body/check.py <body.glb> [--ref A.glb] [--rig rig.json] [--play play.glb] [--far far.glb]
                               [--poser game|lbs] [--same-head] [--topo NPZ] [--only contract,tris,weights,bends,silhouette,topology] --out DIR

Writes DIR/check.json, DIR/summary.txt and DIR/strip_<joint>.png (+ DIR/sil_*.png); exits 1 when a hard threshold
in tools/body/check_spec.json fails. See tools/body/README.md for what each number is.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bends  # noqa: E402
import ray  # noqa: E402
import topo_check  # noqa: E402
from gl import Glb, boundary_edges, dense_weights, edges, weld  # noqa: E402
from posers import HEAD_PARTS, guess_body, make_poser  # noqa: E402

HEADS = ["HeroineHead", "HeroineEyes", "HeroineLashes", "HeroineTeeth", "HeroineTongue"]


# ------------------------------------------------------------------ contract --
def contract(B: Glb, A: Glb, same_head, heads):
    def names(g):
        return {"nodes": set(g.node_names()), "meshes": {m.node for m in g.meshes}, "materials": set(g.materials),
                "skinned": {m.node for m in g.meshes if m.skin is not None}}
    nb, na = names(B), names(A)
    out = {}
    for k in nb:
        out[k] = {"only_in_body": sorted(nb[k] - na[k]), "only_in_ref": sorted(na[k] - nb[k])}
    shapes = {}
    for m in A.meshes:
        mb = B.mesh(m.node)
        if mb is None:
            continue
        sa, sb = set(m.targets), set(mb.targets)
        if sa != sb:
            shapes[m.node] = {"only_in_body": sorted(sb - sa), "only_in_ref": sorted(sa - sb)}
    out["blend_shapes"] = shapes
    out["skeleton"] = {"bones_body": len(B.skeleton().names), "bones_ref": len(A.skeleton().names),
                       "only_in_body": sorted(set(B.skeleton().names) - set(A.skeleton().names)),
                       "only_in_ref": sorted(set(A.skeleton().names) - set(B.skeleton().names))}
    if same_head:
        # (P1 B2a) the head is the ref's IN THE WORLD AT REST: each head mesh's rest world positions (every vertex
        # skinned by its file's own rest @ inverse bind: A's Head carries a 1.07 rest scale left out of its bind, ours
        # bakes it into the mesh and binds plainly) within same_head_tol_m; triangles, UVs and normals as stored, equal;
        # the blend shapes' names equal and their moves equal in the world (each POSITION move times the vertex's
        # blended rest scale, NORMAL moves as stored). The stored positions' byte equality is reported, not required.
        from headbake import rest_world
        tol = 1e-5
        skA, skB = A.skeleton(), B.skeleton()
        sh = {}
        for h in heads:
            ma, mb = A.mesh(h), B.mesh(h)
            if ma is None or mb is None:
                sh[h] = {"ok": False, "why": "missing"}
                continue
            r = {}
            for key in ("N", "UV", "T"):
                x, y = getattr(ma, key), getattr(mb, key)
                r[key] = bool(x.shape == y.shape and np.array_equal(x, y))
            r["P_bytes_equal"] = bool(ma.P.shape == mb.P.shape and np.array_equal(ma.P, mb.P))
            if ma.P.shape == mb.P.shape:
                wa, ca = rest_world(ma, skA)
                wb, cb = rest_world(mb, skB)
                # P1 R1: the head may be PLACED (the designed neck's head_move, a rigid move): the same head moved as
                # one; the move is reported (head_move_m) and the shape compared with it taken off
                off = (wb - wa).mean(0)
                r["head_move_m"] = [round(float(x), 6) for x in off]
                wb = wb - off
                r["world_rest_max_diff_m"] = float(np.linalg.norm(wa - wb, axis=1).max())
                r["world_rest"] = r["world_rest_max_diff_m"] <= tol
                tg = set(ma.targets) == set(mb.targets)
                dmax = 0.0
                if tg:
                    for k in ma.targets:
                        dmax = max(dmax, float(np.abs(ma.targets[k]["POSITION"] * ca[:, None]
                                                      - mb.targets[k]["POSITION"] * cb[:, None]).max()))
                        tg = tg and np.array_equal(ma.targets[k]["NORMAL"], mb.targets[k]["NORMAL"])
                r["targets_world_max_diff_m"] = dmax
                r["targets"] = bool(tg and dmax <= tol)
            else:
                r["world_rest"] = r["targets"] = False
            r["ok"] = all(r[k] for k in ("N", "UV", "T", "world_rest", "targets"))
            sh[h] = r
        # the body's boundary ring against the head's open boundary, both at their rest world positions
        body = B.mesh(guess_body(B))
        head = B.mesh("HeroineHead") or next((m for m in B.meshes if m.node.endswith("Head")), None)
        ring = {}
        if body is not None and head is not None:
            from scipy.spatial import cKDTree
            bw = rest_world(body, skB)[0]
            bv = np.unique(boundary_edges(np.asarray(weld(body.P, 1e-7))[body.T]))
            rep = weld(body.P, 1e-7)
            first = {}
            for i, r_ in enumerate(rep):
                first.setdefault(r_, i)
            bp = bw[[first[k] for k in bv]]
            hw = rest_world(head, skB)[0]
            hrep = weld(head.P, 1e-7)
            hfirst = {}
            for i, r_ in enumerate(hrep):
                hfirst.setdefault(r_, i)
            hv = np.unique(boundary_edges(np.asarray(hrep)[head.T]))
            hp_ = hw[[hfirst[k] for k in hv]]
            d, _ = cKDTree(hp_).query(bp)
            near = d < 0.005          # the body's ring at the neck (its other boundaries are elsewhere)
            ring = {"body_ring_points": int(near.sum()), "max_gap_m": float(d[near].max()) if near.any() else None,
                    "ok": bool(near.any() and d[near].max() <= 1e-5)}
        sh["boundary_ring"] = ring
        out["same_head"] = sh
        out["same_head_ok"] = bool(all(v.get("ok", False) for v in sh.values()))
    return out


# ---------------------------------------------------------------------- tris --
def tris(files):
    out = {}
    for tier, path in files.items():
        if not path:
            continue
        g = Glb(path)
        per = {m.node: int(len(m.T)) for m in g.meshes}
        body = guess_body(g) if any(m.J is not None for m in g.meshes) else max(per, key=per.get)
        out[tier] = {"file": str(path), "per_mesh": per, "body_only": per[body], "whole": int(sum(per.values()))}
    return out


# ------------------------------------------------------------------ topology --
def topology(files):
    """topo_check.measure on each tier's rest body mesh (its quads from the topology npz the glb names)."""
    out = {}
    for tier, (path, over) in files.items():
        if not path:
            continue
        g = Glb(path)
        tp = topo_check.topo_path(g, over)
        if tp is None or not Path(tp).exists():
            out[tier] = {"error": f"no topology npz for {path} (glb extras body_base.topology missing; pass --topo)"}
            continue
        z = dict(np.load(tp, allow_pickle=True))
        per = {m.node: m for m in g.meshes}
        body = "Heroine" if "Heroine" in per else guess_body(g)
        P = per[body].P
        if ((g.js.get("extras") or {}).get("body_base") or {}).get("split"):     # E2: UV seam copies appended
            P = P[:len(z["V"])]
        if len(P) != len(z["V"]):
            out[tier] = {"error": f"{body} has {len(P)} vertices, {tp} has {len(z['V'])}"}
            continue
        out[tier] = dict(topo_check.measure(P, z, g.skeleton()), topology=str(tp))
    return out


# ------------------------------------------------------------------- weights --
MIRROR = [(r"_l$", "_r"), (r"_r$", "_l"), (r"\.L$", ".R"), (r"\.R$", ".L"), (r"_L$", "_R"), (r"_R$", "_L"),
          (r"Left", "Right"), (r"Right", "Left")]


def mirror_name(n):
    for a, b in MIRROR:
        if re.search(a, n):
            return re.sub(a, b, n)
    return n


def weights(g: Glb, spec):
    sk = g.skeleton()
    nb = len(sk.names)
    out = {"meshes": {}}
    for m in g.meshes:
        if m.W is None:
            continue
        W = m.W
        nz = (W > 1e-6).sum(1)
        out["meshes"][m.node] = {"influences_max": int(nz.max()),
                                 "influences_hist": {int(k): int((nz == k).sum()) for k in np.unique(nz)},
                                 "sum_err_max": float(np.abs(1 - W.sum(1)).max()),
                                 "nan": int(np.isnan(W).sum()), "negative": int((W < 0).sum())}
    body = g.mesh(guess_body(g))
    rep = weld(body.P.astype(float), 1e-6)
    first = np.zeros(rep.max() + 1, int)
    first[rep[::-1]] = np.arange(len(rep))[::-1]
    P = body.P[first].astype(float)
    D = dense_weights(body.J, body.W, nb)[first]
    E = np.unique(np.sort(rep[edges(body.T)], 1), axis=0)
    E = E[E[:, 0] != E[:, 1]]
    # L/R mirror: across her midline (x = 0 in her bind space, her left +X), mirrored bone names
    from scipy.spatial import cKDTree
    mi, md = cKDTree(P).query(P * [-1, 1, 1])[1], cKDTree(P).query(P * [-1, 1, 1])[0]
    ok = md < spec.get("mirror_tol_m", 0.001)
    perm = np.array([sk.index.get(mirror_name(n), j) for j, n in enumerate(sk.names)])
    diff = np.abs(D[ok] - D[mi[ok]][:, perm]).max(1)
    out["mirror"] = {"matched_share": round(float(ok.mean()), 4), "p95": round(float(np.percentile(diff, 95)), 4),
                     "max": round(float(diff.max()), 4), "over_0.05": int((diff > 0.05).sum())}
    # far weights: > 0.05 on a bone whose segment (head to tail) is more than far_m away
    far_m = spec.get("far_m", 0.18)
    rows = []
    for j in range(nb):
        v = np.nonzero(D[:, j] > 0.05)[0]
        if not len(v):
            continue
        a, b = sk.head(j), sk.tail(j)
        ab = b - a
        t = np.clip(((P[v] - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.linalg.norm(P[v] - (a + t[:, None] * ab), axis=1)
        if (d > far_m).any():
            rows.append((sk.names[j], int((d > far_m).sum()), round(float(d.max() * 100), 1)))
    rows.sort(key=lambda r: -r[1])
    out["far"] = {"far_m": far_m, "pairs": int(sum(r[1] for r in rows)), "bones": [{"bone": a, "points": b, "max_cm": c} for a, b, c in rows[:12]]}
    # islands per bone and the max weight step across an edge
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    thr = spec.get("island_weight", 0.02)
    isl, steps = [], []
    for j in range(nb):
        on = D[:, j] > thr
        if on.sum() < 2:
            continue
        e = E[on[E[:, 0]] & on[E[:, 1]]]
        idx = np.nonzero(on)[0]
        loc = -np.ones(len(P), int)
        loc[idx] = np.arange(len(idx))
        gph = sp.coo_matrix((np.ones(len(e)), (loc[e[:, 0]], loc[e[:, 1]])), shape=(len(idx), len(idx)))
        n, lab = connected_components(gph, directed=False)
        if n > 1:
            sizes = sorted(np.bincount(lab).tolist(), reverse=True)
            isl.append({"bone": sk.names[j], "islands": int(n), "stray_points": int(sum(sizes[1:]))})
        st = np.abs(D[E[:, 0], j] - D[E[:, 1], j])
        steps.append((sk.names[j], round(float(st.max()), 4)))
    isl.sort(key=lambda r: -r["stray_points"])
    steps.sort(key=lambda r: -r[1])
    out["islands"] = {"bones_with_islands": len(isl), "worst": isl[:12]}
    out["step"] = {"max": steps[0][1] if steps else 0.0, "worst": [{"bone": a, "max_step": b} for a, b in steps[:12]]}
    return out


# ---------------------------------------------------------------- silhouette --
def rest_points(g: Glb):
    """Every mesh at rest (skinned ones through their own skin at the rest pose), one surface."""
    sk = g.skeleton()
    S = sk.rest @ sk.ibm
    Ps, Ts, base = [], [], 0
    for m in g.meshes:
        P = m.P.astype(float)
        if m.J is not None:
            Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
            W = m.W / np.maximum(m.W.sum(1, keepdims=True), 1e-12)
            P = sum(W[:, k:k + 1] * np.einsum("nij,nj->ni", S[m.J[:, k]][:, :3, :], Ph) for k in range(m.J.shape[1]))
        Ps.append(P)
        Ts.append(m.T + base)
        base += len(P)
    return np.concatenate(Ps), np.concatenate(Ts)


def silhouette(B: Glb, A: Glb, scales, out_dir):
    from scipy.ndimage import distance_transform_edt
    from PIL import Image
    PB, TB = rest_points(B)
    PA, TA = rest_points(A)
    lo = np.minimum(PA.min(0), PB.min(0)) - 0.02
    hi = np.maximum(PA.max(0), PB.max(0)) + 0.02
    views = {"front": ([1, 0, 0], [0, 1, 0], [0, 0, 1]), "side": ([0, 0, -1], [0, 1, 0], [1, 0, 0]),
             "back": ([-1, 0, 0], [0, 1, 0], [0, 0, -1])}
    res = {}
    for sname, px in scales.items():
        for v, (ex, ey, cam) in views.items():
            ex, ey, cam = (np.array(a, float) for a in (ex, ey, cam))
            xs = sorted([lo @ ex, hi @ ex])
            vw = ray.View(np.zeros(3), ex, ey, cam, px, xs[0], xs[1], lo[1], hi[1])
            mb, ma = ray.mask(PB, TB, vw), ray.mask(PA, TA, vw)
            eb, ea = ray.boundary(mb), ray.boundary(ma)
            if eb.any() and ea.any():
                db, da = distance_transform_edt(~eb), distance_transform_edt(~ea)
                dmax = float(max(db[ea].max(), da[eb].max()))
            else:
                dmax = float("nan")
            res[f"{sname}_{v}"] = {"px_per_cm": px / 100, "size": [vw.w, vw.h], "xor_px": int((ma ^ mb).sum()),
                                   "max_outline_px": round(dmax, 2)}
            if sname == "close":
                img = np.full(ma.shape + (3,), 255, np.uint8)
                img[ma] = (170, 170, 170)
                img[ma ^ mb] = (220, 60, 40)
                Image.fromarray(img).save(Path(out_dir) / f"sil_{v}.png")
    return res


# ---------------------------------------------------------------------- main --
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--ref")
    ap.add_argument("--rig")
    ap.add_argument("--play")
    ap.add_argument("--far")
    ap.add_argument("--poser", choices=["game", "lbs"])
    ap.add_argument("--same-head", action="store_true", help="the head meshes must be the ref's in the world at rest (see contract())")
    ap.add_argument("--topo", help="the topology npz of --body (default: its glb extras body_base.topology); play: --play-topo")
    ap.add_argument("--play-topo")
    ap.add_argument("--hide-far", action="store_true", help="also draw strip_hip_flex_nofar.png: her own side of the midline only")
    ap.add_argument("--only", default="contract,tris,weights,bends,silhouette,topology")
    ap.add_argument("--spec", default=str(HERE / "check_spec.json"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(a.spec).read_text())
    rig = json.loads(Path(a.rig).read_text()) if a.rig else {}
    only = set(a.only.split(","))
    B = Glb(a.body)
    A = Glb(a.ref) if a.ref else None
    res = {"body": a.body, "ref": a.ref, "rig": a.rig}
    if "contract" in only and A is not None:
        res["contract"] = contract(B, A, a.same_head, spec.get("same_head_meshes", HEADS))
    if "tris" in only:
        res["tris"] = tris({"close": a.body, "play": a.play, "far": a.far})
    if "weights" in only:
        res["weights"] = weights(B, spec.get("weights", {}))
    if "bends" in only:
        kind = a.poser
        if kind is None:
            sys.path.insert(0, str(HERE.parents[1] / "tools" / "anim"))
            from rig import Skeleton
            import skin
            game = set(Skeleton.load(skin.SKELETONS / "heroine_skeleton.json").names)
            kind = "game" if not a.rig and set(B.skeleton().names) <= game else "lbs"
        poser = make_poser(kind, a.body, rig)
        fr = bends.Frame(poser, rig)
        res["bends"] = {"poser": kind, "frame": {"up": fr.up.round(4).tolist(), "left": fr.lat.round(4).tolist(),
                                                 "front": fr.front.round(4).tolist()}, "strips": {}}
        for mo in bends.MOTIONS:
            draws = []
            for s in "lr":
                st = bends.Strip(poser, rig, fr, mo, s)
                r, d = bends.run_strip(st)
                res["bends"]["strips"][f"{mo}_{s}"] = r
                draws.append((st, d))
            # both sides in one sheet when they fit under 700 px, else her left
            h = int(round(2 * draws[0][0].half * bends.PX_CLOSE))
            size = bends.sheet(draws if 2 * h + 20 <= 700 else draws[:1], out / f"strip_{mo}.png",
                               f"{mo} | {kind} poser | rest, " + ", ".join(str(x) for x in bends.ANGLES_OF.get(mo, bends.ANGLES)[1:])
                               + " | 9.4 px/cm | orange: outline, cyan: reference")
            res["bends"]["strips"][f"{mo}_l"]["sheet"] = str(out / f"strip_{mo}.png")
            res["bends"]["strips"][f"{mo}_l"]["sheet_size"] = list(size)
            if a.hide_far and mo == "hip_flex":
                bends.sheet(draws if 2 * h + 20 <= 700 else draws[:1], out / f"strip_{mo}_nofar.png",
                            f"{mo} | far side hidden | rest, 90, 135 | 9.4 px/cm", hide_far=True)
        if "hip_flex" in bends.MOTIONS:
            res["bends"]["both_hips"] = bends.both_hips(poser, rig, fr)
    if "silhouette" in only and A is not None:
        sc = spec.get("silhouette", {})
        res["silhouette"] = silhouette(B, A, {"close": bends.PX_CLOSE, "look": sc.get("look_px_per_cm", 30.0) * 100}, out)
    if "topology" in only:
        res["topology"] = topology({"close": (a.body, a.topo), "play": (a.play, a.play_topo)})
    fails = gate(res, spec)
    res["fails"] = fails
    (out / "check.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "summary.txt").write_text(summary(res, spec))
    print((out / "summary.txt").read_text())
    return 1 if fails else 0


def gate(res, spec):
    """The hard failures (check_spec.json "hard"); everything else reports against its target."""
    f = []
    hard = spec.get("hard", {})
    c = res.get("contract", {})
    if "same_head_ok" in c and not c["same_head_ok"]:
        f.append("same_head")
    for nm, m in res.get("weights", {}).get("meshes", {}).items():
        if m["nan"] or m["negative"]:
            f.append(f"weights_nan_or_negative:{nm}")
        if m["sum_err_max"] > hard.get("weight_sum_err_max", 1e-3):
            f.append(f"weight_sum:{nm}")
        if m["influences_max"] > hard.get("influences_max", 8):
            f.append(f"influences:{nm}")
    return f


def summary(res, spec):
    L = [f"body {res['body']}  ref {res['ref']}", f"HARD FAILS: {', '.join(res['fails']) or 'none'}"]
    c = res.get("contract")
    if c:
        diff = {k: v for k, v in c.items() if isinstance(v, dict) and (v.get("only_in_body") or v.get("only_in_ref"))}
        L.append(f"contract: {len(diff)} name groups differ ({', '.join(diff) or 'none'}); blend-shape diffs on "
                 f"{len(c.get('blend_shapes', {}))} meshes; same head: {c.get('same_head_ok', 'not asked')}")
    for tier, t in res.get("tris", {}).items():
        L.append(f"tris {tier}: body {t['body_only']}  whole {t['whole']}")
    w = res.get("weights")
    if w:
        bm = max(w["meshes"].items(), key=lambda kv: sum(kv[1]["influences_hist"].values()))
        L.append(f"weights ({bm[0]}): influences max {bm[1]['influences_max']}, sum err {bm[1]['sum_err_max']:.2e}; "
                 f"mirror p95 {w['mirror']['p95']} max {w['mirror']['max']} (matched {w['mirror']['matched_share']}); "
                 f"far pairs {w['far']['pairs']}; bones with islands {w['islands']['bones_with_islands']}; "
                 f"max edge step {w['step']['max']}")
    b = res.get("bends")
    if b:
        L.append(f"bends ({b['poser']} poser): girth ratio min..max | area ratio min..max | inside pts, depth max mm | "
                 f"outline vs ref mean/max mm")
        for k, s in b["strips"].items():
            for deg, r in s["angles"].items():
                if deg == "0":
                    continue
                g = [x for x in r["girth_ratio"].values() if x]
                ar = [x for x in r["area_ratio"].values() if x]
                o = r["outline_vs_ref"] or {}
                ot = " ".join(f"{cn} {v['ref_to_model_mean_mm']}/{v['max_mm']}" for cn, v in o.items())
                pen = r["penetration"]
                L.append(f"  {k:16s} {deg:>3s}: g {min(g):.3f}..{max(g):.3f} | a {min(ar, default=float('nan')):.3f}.."
                         f"{max(ar, default=float('nan')):.3f} | in {pen['count']} ({s['angles']['0']['penetration']['count']} at rest), "
                         f"{pen['depth_max_mm']} | {ot}"
                         + (" | pit " + " ".join(f"{g[0].upper()}{v}" for g, v in r["pit"]["by_region_mm"].items())
                            if r.get("pit") else "")
                         + (f" | true>2mm {pen['true_over_2mm']} (max {pen['true_max_mm']})" if "true_max_mm" in pen else "")
                         + (f" | end out {r['crease_end'].get('out', {}).get('gain_mm')} in "
                            f"{r['crease_end'].get('in', {}).get('gain_mm')} (<{r['crease_end']['limit_mm']})"
                            if r.get("crease_end") else "")
                         + (f" | slit {r['slit'].get('slit_mm')}" if r.get("slit") else "")
                         + (" | joint drop {joint_drop_mm} top drop {top_drop_mm} (ratio {top_ratio}) dome {d} "
                            "(rest {d0}) neck {neck_base_mm} delt out {delt_out_mm} down {delt_down_mm}".format(
                                d=r["shoulder"]["dome"]["dome_mm"], d0=r["shoulder"]["dome_rest"]["dome_mm"],
                                **r["shoulder"]) if r.get("shoulder") else "")
                         + (" | kink " + " ".join(f"{k} {v['turn_deg']}@{v['at_mm']} (rest {v['rest_deg']})"
                                                  for k, v in r["kink"].items()) if r.get("kink") else ""))
    for deg, r in res.get("bends", {}).get("both_hips", {}).items():
        L.append(f"  both hips {deg:>3s}: " + " | ".join(
            f"{s} in {r[s]['penetration']['count']}, {r[s]['penetration']['depth_max_mm']} true>2mm "
            f"{r[s]['penetration'].get('true_over_2mm')} (max {r[s]['penetration'].get('true_max_mm')}) pit "
            + " ".join(f"{g[0].upper()}{v}" for g, v in r[s]["pit"].items()) for s in "lr"))
    for tier, t in res.get("topology", {}).items():
        if "error" in t:
            L.append(f"topology {tier}: {t['error']}")
            continue
        cp = t["crease_plane_vs_bisector"]
        L.append(f"topology {tier}: fold>60 {t['fold_over_60']} (+{t['fold_over_60_crotch_exception']} crotch exception; "
                 f"max {t['fold_max_deg_off_floor']} deg), aspect>4 {t['aspect_over_4']} (max {t['aspect_max']}), "
                 f"edges<2mm {t['edges_under_2mm']} (min {t['edge_min_mm']} mm), poles in bend zone {t['poles_in_bend_zone_40mm']}"
                 f"/{t['poles_total']} {t['poles_in_bend_zone_by_zone'] or ''}, crease plane vs bisector "
                 + " ".join(f"{k} {v['deg'] if v else None} deg" for k, v in cp.items()))
    sl = res.get("silhouette")
    if sl:
        L.append("silhouette (xor px / max outline px): " + "  ".join(f"{k} {v['xor_px']}/{v['max_outline_px']}" for k, v in sl.items()))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
