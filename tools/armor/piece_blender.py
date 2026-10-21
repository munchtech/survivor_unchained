"""One armor piece built on her body, inside Blender (tools/armor/build.py runs it; docs/handoff/armor.md 1.2-1.6).

    blender -b <heroine_built.blend> --python tools/armor/piece_blender.py -- <piece.json> <scratch dir>

It runs tools/assets/heroine_outfits.py's own body preparation and machinery (the source is read and run here
in three parts, unchanged but for one redirect: mat() writes its baked textures into the scratch dir, never
godot/art/outfit), builds the piece's shell from her surface with her weights, takes her body through the steps
the full build takes before it writes her tuck (chest smoothing, areolas, folds, helpers, flattened fingers), so
the tuck records and the body hash are the full build's, and writes into godot/art/armor/:
  <id>.gltf + <id>.bin       the piece, skinned on her skeleton exactly as the outfit files are
  armor_tuck/<id>.bin        her skin's tuck under it (the record format of art/people/armor_tuck)
  <id>.sockets.json          named sockets (point + frame), rims (polylines + weights), the UV surface
  armor_index.json           its row (art/people/armor_index.json's fields + file + tier)
and the numbers to <scratch>/numbers.json. The four outfit files, heroine.glb and art/outfit are never written.
"""
import json
import os
import sys
import time

T0 = time.time()
ARGS = sys.argv[sys.argv.index("--") + 1:]
PIECE_JSON = os.path.abspath(ARGS[0])
SCRATCH = os.path.abspath(ARGS[1])
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HO = os.path.join(ROOT, "tools", "assets", "heroine_outfits.py")
ART = os.path.join(ROOT, "godot", "art", "armor")
os.makedirs(SCRATCH, exist_ok=True)
SPEC_PIECE = json.load(open(PIECE_JSON, encoding="utf-8"))
PID = SPEC_PIECE["id"]
SLOT = SPEC_PIECE["slot"]


def stamp(msg):
    print("ARMOR [%6.1fs] %s" % (time.time() - T0, msg), flush=True)


# --------------------------------------------------------- her machinery --
src = open(HO, encoding="utf-8").read()


def cut(a, b=None, a_incl=True, b_incl=False):
    i = src.index(a)
    assert src.count(a) == 1, a
    if not a_incl:
        i += len(a)
    j = len(src) if b is None else src.index(b, i) + (len(b) if b_incl else 0)
    return i, j


def run(i, j, ns, patch=()):
    seg = src[i:j]
    for old, new in patch:
        assert seg.count(old) == 1, old
        seg = seg.replace(old, new)
    code = compile("\n" * src.count("\n", 0, i) + seg, HO, "exec")
    exec(code, ns)


M_LOOP = ("made = []\nfor name, build in OUTFITS.items():\n    if ONLY and name != ONLY:\n        continue\n"
          "    made += [o for o in build() if o]\n")
M_BODY = "if BODY_OUT:\n    me = body.data\n"
M_STRAYS = "# Nothing else rides along (the scene may hold strays).\n"
M_RIGID = "rigid_again(RIGID_PIECES, RIDERS)\n"
TEX_OUT = os.path.join(SCRATCH, "tex")
os.makedirs(TEX_OUT, exist_ok=True)
sys.argv = [sys.argv[0], "--", os.path.join(SCRATCH, "x")]
NS = {"__name__": "heroine_outfits", "__file__": HO, "ARMOR_TEX_OUT": TEX_OUT}
a0, a1 = 0, src.index(M_LOOP)
run(a0, a1, NS, patch=[('out = os.path.join(TEX, f"outfit_{key}_diff.jpg")', 'out = os.path.join(ARMOR_TEX_OUT, f"outfit_{key}_diff.jpg")')])
stamp("her body prepared (%d skin points)" % len(NS["P"]))

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

G = NS
P, N, W, NB, BONES, BI = G["P"], G["N"], G["W"], G["NB"], G["BONES"], G["BI"]
arm, body = G["arm"], G["body"]
PRM = SPEC_PIECE.get("params", {})
MKEY = SPEC_PIECE.get("material", "steel")
mirror = np.array([-1.0, 1.0, 1.0])


def gl(p):
    """Blender world (Z up) -> glTF / Godot (Y up), metres."""
    p = np.asarray(p, float)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], -1)


def top4(row):
    k = np.argsort(-row)[:4]
    k = [i for i in k if row[i] > 1e-4]
    s = sum(row[i] for i in k) or 1.0
    return [[BONES[i], round(float(row[i] / s), 4)] for i in k]


def set_one_blend(obj, row):
    """Every point of obj on one blend of bones (`row`: [(name, w)])."""
    idx = list(range(len(obj.data.vertices)))
    for g in list(obj.vertex_groups):
        if g.name in BI:
            obj.vertex_groups.remove(g)
    for n, w in row:
        (obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add(idx, float(w), "REPLACE")


def obj_rows(obj, names):
    gname = {g.index: g.name for g in obj.vertex_groups}
    out = []
    for v in obj.data.vertices:
        out.append({gname[g.group]: g.weight for g in v.groups if gname[g.group] in names and g.weight > 1e-5})
    return out


def rigid_parts(obj, names):
    """Each connected part of obj (a rivet, a buckle's frame) on one blend: the mean of its points' weights,
    its four largest shares (as heroine_outfits' rigid_again does a one-blend piece), so no part ever bends."""
    me = obj.data
    n = len(me.vertices)
    ev = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", ev)
    from scipy import sparse
    from scipy.sparse import csgraph
    e = ev.reshape(-1, 2)
    k, lab = csgraph.connected_components(sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    rows = obj_rows(obj, names)
    groups = {g.name: g for g in obj.vertex_groups}
    for c in range(k):
        idx = np.nonzero(lab == c)[0]
        tot = {}
        for i in idx:
            for nm, w in rows[i].items():
                tot[nm] = tot.get(nm, 0.0) + w
        keep = sorted(tot, key=tot.get, reverse=True)[:4]
        s = sum(tot[nm] for nm in keep) or 1.0
        il = [int(i) for i in idx]
        for g in obj.vertex_groups:
            if g.name in names:
                g.remove(il)
        for nm in keep:
            if nm not in groups:
                groups[nm] = obj.vertex_groups.new(name=nm)
            groups[nm].add(il, tot[nm] / s, "REPLACE")
    return k


# ------------------------------------------------------ the shell: plate --
CAP = {"sheet": {}, "tubes": {}}
SUBGRID = {}
_finish, _tube = G["finish"], G["tube"]


def finish_cap(name, pos, wt, tris, mkey, thick, bevel, budget=3000, scraps=True):
    if name not in CAP["sheet"]:
        CAP["sheet"][name] = (np.array(pos, float), np.array(wt, float), np.array(tris), thick)
    # (leather straps and the band laid out coarser: ribbon and girdle lay a grid every 1.5 mm across, ten times what a
    # flat strap's shape needs. Kept: both edges and the middle line across; along, every other row and the last)
    sg_ = SUBGRID.pop(name, None)
    if sg_ is not None:
        along, across, closed = sg_
        if len(pos) == along * across:
            pos3, wt3 = np.asarray(pos, float).reshape(along, across, 3), np.asarray(wt, float).reshape(along, across, -1)
            if closed == "open":
                # (girdle with an arc: rows across, nu along, not wrapped)
                rk = [0, along // 2, along - 1]
                pos3, wt3 = pos3[rk], wt3[rk]
                tris_n = G["grid"](3, pos3.shape[1])
            elif closed:
                # (girdle: rows across her, nu round her, wrapped)
                rk = [0, along // 2, along - 1]
                pos3, wt3 = pos3[rk], wt3[rk]
                nu_ = pos3.shape[1]
                idx_ = np.arange(3 * nu_).reshape(3, nu_)
                idx_ = np.c_[idx_, idx_[:, :1]].ravel()
                tris_n = idx_[G["grid"](3, nu_ + 1)]
            else:
                rk = list(range(0, along, 2)) + ([along - 1] if (along - 1) % 2 else [])
                ck = [0, across // 2, across - 1]
                pos3, wt3 = pos3[rk][:, ck], wt3[rk][:, ck]
                tris_n = G["grid"](len(rk), 3)
            p_n = pos3.reshape(-1, 3)
            # (facing kept as the original's)
            o_n = G["vertex_normals"](np.asarray(pos, float), np.asarray(tris)).mean(0)
            if (G["vertex_normals"](p_n, tris_n).mean(0) @ o_n) < 0:
                tris_n = tris_n[:, ::-1]
            print("SUBGRID %s: %d -> %d points" % (name, len(pos), len(p_n)))
            pos, wt, tris = p_n, wt3.reshape(len(p_n), -1), tris_n
            bevel = 0.0
    return _finish(name, pos, wt, tris, mkey, thick, bevel, budget, scraps)


def tube_cap(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed=True, nv=12):
    # (the triangle budget: a rolled edge's ring every ~3.5 mm along it, 8 round it; at the play camera it is one
    # line of light, and the sheet's edge points are ~2 mm apart)
    if name.startswith(PID) and len(curve) > 8:
        curve, nrm, outward = (np.asarray(x, float) for x in (curve, nrm, outward))
        cw = np.vstack([curve, curve[:1]]) if closed else curve
        run_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cw, axis=0), axis=1))]
        m_ = max(8, int(round(run_[-1] / PRM.get("roll_step", 0.0035))))
        ss = np.linspace(0, run_[-1], m_, endpoint=not closed)
        res = lambda a_: np.stack([np.interp(ss, run_, (np.vstack([a_, a_[:1]]) if closed else a_)[:, k]) for k in range(3)], 1)
        curve, nrm, outward = res(curve), res(nrm), res(outward)
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        outward = outward - nrm * (outward * nrm).sum(1)[:, None]
        outward /= np.linalg.norm(outward, axis=1)[:, None]
        nv = PRM.get("roll_nv", 8)
    o = _tube(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed, nv)
    CAP["tubes"][name] = dict(curve=np.array(curve, float), nrm=np.array(nrm, float), outward=np.array(outward, float),
                              width=float(np.max(width)), height=float(np.max(height)), overhang=float(np.max(overhang)),
                              thick=float(np.max(thick)), closed=closed, obj=o)
    return o


G["finish"], G["tube"] = finish_cap, tube_cap
# (no thread stitching on the straps: at the play camera it is below a pixel, and it was a third material and 20k
# triangles; the leather's look is the shader's)
_stitches = G["stitches"]
G["stitches"] = lambda *a_, **k_: []


def rim_field(pos, tris):
    loops = G["edge_loops"](tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops])) if loops else np.arange(0)
    return cKDTree(pos[rim]).query(pos)[0] if len(rim) else np.full(len(pos), 0.05), loops


def strap_buckle(name, strap_objs, a, b, t, w, h, r):
    """A buckle on a strap: a rounded frame of rod r, a bar across its middle and a tongue lying from the bar
    to its far side, at fraction t of the way a->b along the strap (its long way). All of it on one blend."""
    vs, fs = [], []
    for o in strap_objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(vs, fs)
    q = a + (b - a) * t
    hit = tree.find_nearest(Vector(q))
    at = np.array(hit[0][:])
    n = np.array(hit[1][:])
    sk = np.array(G["SKIN_BVH"].find_nearest(Vector(at))[1][:])
    if n @ sk < 0:
        n = -n
    up = (b - a) / np.linalg.norm(b - a)
    up = up - n * (up @ n)
    up /= np.linalg.norm(up)
    v = np.cross(n, up)
    c = at + n * (r + 0.0003)
    made = G["frame"](name, c, n, up, w, h, MKEY, r=r, corner=min(0.004, w / 4))
    bar = np.array([c - v * (w / 2 - r), c + v * (w / 2 - r)])
    bar = bar[0] + (bar[1] - bar[0]) * np.linspace(0, 1, 16)[:, None]
    made += G["cord"](name + "_bar", bar, MKEY, r=r * 0.8)
    tongue = np.array([c + n * r * 0.9, c + up * (h / 2 + r * 0.6) + n * r * 0.9])
    tongue = tongue[0] + (tongue[1] - tongue[0]) * np.linspace(0, 1, 14)[:, None]
    made += G["cord"](name + "_tongue", tongue, MKEY, r=r * 0.62)
    wc = G["soft_weights"](c[None], sigma=max(w, h) / 2, k=32)[0]
    for o in made:
        set_one_blend(o, top4(wc))
        o["hides"] = False
        o["rigid_part"] = True
    return made, dict(point=c, normal=n, up=up, weights=wc)


def low_rivets(name, pts, nrms, wts, r, mkey, rise=0.42):
    """Low domed rivet heads (40 triangles each: an 8-sided dome of two rings on a thin flange) standing on the
    points' normals, each on its own blend (rigid_parts). The cheap rivet: at the play camera a rivet is a
    highlight and a shadow, never its facets."""
    nu = 8
    P2, W2, T2 = [], [], []
    for p0, n, w in zip(pts, nrms, wts):
        n = np.asarray(n, float) / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        fl = 0.08 * r
        q = [p0 + n * (fl + r * rise)]
        for rr, hh in ((r * 0.62, fl + r * rise * 0.78), (r, fl + r * rise * 0.18), (r * 1.1, -0.0004)):
            for j in range(nu):
                ph = 2 * np.pi * (j + 0.5 * (rr == r)) / nu
                q.append(p0 + (np.cos(ph) * t + np.sin(ph) * b) * rr + n * hh)
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(2):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(q))
        W2.append(np.repeat(np.asarray(w, float)[None], len(q), 0))
        T2.append(np.array(tri))
    if not P2:
        return []
    pp, ww, tt = np.vstack(P2), np.vstack(W2), np.vstack(T2)
    cen = np.repeat(np.asarray(pts, float), 1 + 3 * nu, 0)
    if (G["vertex_normals"](pp, tt) * (pp - cen)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    o_ = _finish(name, pp, ww, tt, mkey, 0.0, 0.0, 10 ** 7, scraps=False)
    o_["hides"] = False
    o_["rigid_part"] = True
    return [o_]


def aim_hits(objs, aims):
    """Where a ray from outside toward each aim (origin, target) first meets objs: (points, normals facing out)."""
    vs, fs = [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(vs, fs)
    pts, nrms = [], []
    for org, tgt in aims:
        d = Vector(tuple(np.asarray(tgt, float) - np.asarray(org, float))).normalized()
        hit = tree.ray_cast(Vector(tuple(org)), d, 2.0)
        if hit[0] is not None:
            n = np.array(hit[1][:])
            if n @ np.array(d[:]) > 0:
                n = -n
            pts.append(np.array(hit[0][:]))
            nrms.append(n)
    return pts, nrms


def ico(sub):
    bm_ = bmesh.new()
    bmesh.ops.create_icosphere(bm_, subdivisions=sub, radius=1.0)
    unit = np.array([v.co[:] for v in bm_.verts])
    tris = np.array([[v.index for v in f.verts] for f in bm_.faces])
    bm_.free()
    return unit / np.linalg.norm(unit, axis=1)[:, None], tris


FIT = {}
NUM_FIT = {}
BAND = {}
STRAPS = {}


def nip_rel(pts):
    """Points as mm from the nearer nipple (x mirrored to her right: + is toward her middle), for the log."""
    nr = G["NIPPLE"]["r"]
    q = np.asarray(pts, float).reshape(-1, 3).copy()
    q[:, 0] = -np.abs(q[:, 0])
    d = (q - nr) * 1000
    return d.round(1).tolist()


def standoff(sheet_name, skin_bvh, rim_d=0.012):
    """How far the sheet (a plate's inner face: finish thickens outward) stands off her skin, from each of its points
    to her nearest skin: by place (lower rim, inner rim, crown 30 mm in from a rim, all), in mm. The plate's own
    measure of 'floating', where the skin-ray measure also counts the open air under an overhang."""
    sp, _, st, _ = CAP["sheet"][sheet_name]
    d = np.array([np.linalg.norm(np.array(skin_bvh.find_nearest(Vector(q))[0][:]) - q) for q in sp]) * 1000
    e_ = np.sort(np.vstack([st[:, [0, 1]], st[:, [1, 2]], st[:, [2, 0]]]), 1)
    uk, cn = np.unique(e_, axis=0, return_counts=True)
    rim = np.unique(uk[cn == 1])
    dr = cKDTree(sp[rim]).query(sp)[0]
    ax_ = np.abs(sp[:, 0])
    nipz = G["NIPPLE"]["r"][2]
    inner = (dr < rim_d) & (ax_ < FIT["x_min"] + 0.015)
    lower = (dr < rim_d) & (sp[:, 2] < nipz - 0.015) & ~inner
    st_ = lambda m: {"n": int(m.sum()), "max": round(float(d[m].max()), 2), "p99": round(float(np.percentile(d[m], 99)), 2),
                     "p50": round(float(np.median(d[m])), 2)} if m.any() else None
    if not sheet_name.endswith(".cups"):
        return {"all": st_(np.ones(len(d), bool)), "rim": st_(dr < rim_d)}
    FIT["standoff_worst_at"] = {"lower_rim": nip_rel(sp[lower][np.argsort(-d[lower])[:6]]) if lower.any() else [],
                                "crown": nip_rel(sp[dr > 0.03][np.argsort(-d[dr > 0.03])[:6]])}
    return {"lower_rim": st_(lower), "inner_rim": st_(inner), "rim_all": st_(dr < rim_d), "crown": st_(dr > 0.03), "all": st_(np.ones(len(d), bool))}


def fitted_cups(cname, top, lift, thick, roll, gap, side, fold, sub=6):
    """Her right breast's own surface (her skin with the nipples filled, P_FILLED: smooth, no lumps), seen from
    inside the breast (BREAST_FORM's centre) along an even spread of directions, `lift` off her along its normal:
    a fitted cup, not a sphere. It ends where the breast ends: at the crease under and beside it (the line where
    her surface turns from convex to concave, eased; `fold` moves the cut into the crease, in 1/m of curvature),
    above at the plunge line top(|x|), inside `gap` from her middle, outside `side` past her nipple. Mirrored onto
    her left. Rolled edge (bind_edges) and thickness (finish) as the outfit cups have them."""
    from scipy import sparse
    from scipy.ndimage import gaussian_filter1d
    c, R, ax, form = G["BREAST_FORM"]
    nip = G["NIPPLE"]["r"]
    if G.get("FILLED_BVH") is None:
        G["FILLED_BVH"] = BVHTree.FromPolygons([tuple(p) for p in G["P_FILLED"]], G["TRI"].tolist())
    fb = G["FILLED_BVH"]
    un = (nip - c) / np.linalg.norm(nip - c)
    unit, tris = ico(sub)
    front = unit @ un > -0.15
    r = np.full(len(unit), np.nan)
    for i in np.nonzero(front)[0]:
        h = fb.ray_cast(Vector(c), Vector(unit[i]), 0.3)
        if h[0] is not None:
            r[i] = h[3]
    ok = np.isfinite(r)
    tris = tris[ok[tris].all(1)]
    n = len(unit)
    A = G["adjacency"](n, tris)
    deg = np.asarray(A.sum(1)).ravel()
    Am = sparse.diags(1.0 / np.maximum(deg, 1)) @ A
    r = np.where(ok, r, 0.0)
    # (a membrane: eased, but never into her: a dip is bridged, never sunk into)
    for _ in range(PRM.get("membrane", 1)):
        r = np.where(ok, np.maximum(r, Am @ r), 0.0)
    pos = c + unit * r[:, None]
    nor = G["vertex_normals"](pos, tris)
    if (nor[ok] * (pos[ok] - c)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    # Curvature, convex positive: the umbrella (her neighbours' mean less the point) against the normal, over the
    # local spacing squared, eased over the surface.
    lap = Am @ pos - pos
    e_ = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    elen = np.linalg.norm(pos[e_[:, 0]] - pos[e_[:, 1]], axis=1)
    h2 = np.bincount(e_.ravel(), np.repeat(elen, 2), n) / np.maximum(np.bincount(e_.ravel(), minlength=n), 1)
    H = -(lap * nor).sum(1) / np.maximum(h2 ** 2, 1e-8) * 4.0
    H = np.where(ok, H, 0.0)
    for _ in range(25):
        H = np.where(ok, 0.5 * H + 0.5 * (Am @ H), 0.0)
    pos = pos + nor * lift
    axs = np.abs(pos[:, 0])
    # (`below`: no lower than this under her nipple: at her outer side the breast runs into her ribs with no crease,
    # and the convex region ran 108 mm down and round her side, where her skin moves with her arm)
    f = np.minimum.reduce([top(axs) - pos[:, 2], axs - gap, abs(nip[0]) + side - axs, (H - fold) * 0.0006,
                           pos[:, 2] - (nip[2] - PRM.get("below", 0.07)),
                           # (`back`: no further back than this behind her nipple, a side seam: wrapped further round
                           # her side, her skin there pressed out past the plate under her arm, arms raised or not)
                           (nip[1] + PRM.get("back", 0.075)) - pos[:, 1],
                           unit @ un - 0.05, -pos[:, 0] - 0.001, np.where(ok, 1.0, -1.0)])
    _, j = cKDTree(P).query(pos)
    attr = np.hstack([nor, W[j].astype(float), np.zeros((n, 1))])
    pos, at, tris = G["clip"](f, pos, attr, tris)
    pos, at, tris = G["weld"](pos, at, tris)
    tris = G["islands"](pos, tris, keep_frac=0.2)
    live = np.unique(tris)
    re = -np.ones(len(pos), int)
    re[live] = np.arange(len(live))
    pos, at, tris = pos[live], at[live], re[tris]
    loops = G["edge_loops"](tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops]))
    at[:, -1] = cKDTree(pos[rim]).query(pos)[0]
    outer = rim[np.abs(pos[rim, 0]) > abs(nip[0]) * 0.85]
    G["CUP_PEAK"]["r"] = pos[outer[np.argmax(pos[outer, 2])]]
    G["CUP_PEAK"]["l"] = G["CUP_PEAK"]["r"] * mirror
    inner = rim[np.abs(pos[rim, 0]) < gap + 0.006]
    G["CUP_LOW"] = pos[inner[np.argmin(pos[inner, 2])]] if len(inner) else np.array([-gap, nip[1], G["UNDERBUST"]])
    FIT["fold_min_z"] = float(pos[rim, 2].min())
    FIT["rim_r"] = pos[rim]
    pos2 = np.vstack([pos, pos * mirror])
    at2 = np.vstack([at, np.hstack([at[:, :3] * mirror, at[:, 3:3 + NB][:, G["SWAP"]], at[:, -1:]])])
    tris2 = np.vstack([tris, tris[:, ::-1] + len(pos)])
    # (one island a cup, laid out with the least stretch: projected along their mean facing, the fitted cups' sides,
    # which turn under and beside her, were cut into smart-project islands whose seams showed as stripes)
    G["ONE_ISLAND"].add(cname)
    FIT["x_min"] = float(np.abs(pos[rim, 0]).min())
    pos2, beads = G["bind_edges"](cname, pos2, at2, tris2, MKEY, max(roll["width"], 0.005), max(roll["height"], 0.0006), 0.0018, thick)
    # (no bevel: the rolled edge wraps the cut edge, and a bevel there was 3k triangles under it)
    shell = finish_cap(cname, pos2, at2[:, 3:3 + NB], tris2, MKEY, thick, 0.0, PRM.get("cup_budget", 2600))
    shell["hides"] = True
    for b_ in beads:
        b_["hides"] = False
    print("FITTED CUPS %s: %d points a side; curvature %.0f..%.0f /m; rim lowest z %.3f" % (cname, len(pos), H[ok].min(), H[ok].max(), FIT["fold_min_z"]))
    return [shell] + beads


def gore_row(z_top, z_tip):
    """The gore's one blend: her soft weights at its centre on her sternum (its four largest shares), dense."""
    gc = np.array(G["front_point"](0.0, (z_top + z_tip) / 2))
    row = np.zeros(NB)
    for n_, w_ in top4(G["soft_weights"](gc[None])[0]):
        row[BI[n_] if isinstance(BI, dict) else BONES.index(n_)] = w_
    return row


def gore_plate(name, cup_objs, z_top, z_tip, hw_top, hw_tip, lift, thick, roll, row=None):
    """The gore: a small forged plate on her sternum between the cups, cut from her own skin (so it lies on her,
    `lift` off), its outline the cups' inner rims 1.5 mm clear above, tapering down to a rounded tip on her
    sternum. Its own rolled edge. Rigid (r2, F7): with `row`, the plate and its rolled edge all on that one blend (the
    blend at its centre), so it never bends between the cups as her breast bones move (arms in, it read as a bent
    sliver on the skin weights it took point by point)."""
    xs = np.arange(-hw_top - 0.012, hw_top + 0.012 + 1e-9, 0.0025)
    zs = np.arange(z_tip - 0.006, z_top + 0.012 + 1e-9, 0.0025)
    nx, nz = len(xs), len(zs)
    pos = np.array([G["front_point"](x, z) for z in zs for x in xs])
    i = (np.arange(nz - 1)[:, None] * nx + np.arange(nx - 1)[None, :]).ravel()
    tris = np.vstack([np.c_[i, i + nx, i + 1], np.c_[i + 1, i + nx, i + nx + 1]])
    nor = G["vertex_normals"](pos, tris)
    if nor[:, 1].mean() > 0:
        tris = tris[:, ::-1]
        nor = -nor
    # (clear of the cups: a skin point is under a cup if a ray out along her normal meets the cup within 12 mm)
    vs, fs = [], []
    for o in cup_objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + k for k in p.vertices] for p in o.data.polygons]
    ct = BVHTree.FromPolygons(vs, fs)
    under = np.array([ct.ray_cast(Vector(p), Vector(nn), 0.012)[0] is not None for p, nn in zip(pos, nor)])
    d_in = cKDTree(pos[under]).query(pos)[0] if under.any() else np.full(len(pos), 1.0)
    d_out = cKDTree(pos[~under]).query(pos)[0]
    clear = np.where(under, -d_out, d_in) - 0.0015
    x, z = pos[:, 0], pos[:, 2]
    t = np.clip((z - z_tip) / max(z_top - z_tip, 1e-6), 0, 1)
    hw = hw_tip + (hw_top - hw_tip) * np.sqrt(t)
    tipc = np.array([0.0, z_tip + hw_tip])
    f = np.minimum.reduce([clear, hw - np.abs(x), z_top - z,
                           np.where(z < tipc[1], hw_tip - np.hypot(x, z - tipc[1]), 1.0)])
    pos = pos + nor * lift
    _, j = cKDTree(P).query(pos)
    attr = np.hstack([nor, W[j].astype(float) if row is None else np.repeat(np.asarray(row, float)[None], len(pos), 0),
                      np.zeros((len(pos), 1))])
    pos, at, tris = G["clip"](f, pos, attr, tris)
    pos, at, tris = G["weld"](pos, at, tris)
    tris = G["islands"](pos, tris, keep_frac=0.3)
    live = np.unique(tris)
    re = -np.ones(len(pos), int)
    re[live] = np.arange(len(live))
    pos, at, tris = pos[live], at[live], re[tris]
    loops = G["edge_loops"](tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops]))
    at[:, -1] = cKDTree(pos[rim]).query(pos)[0]
    G["BIND_MINLOOP"][name] = 0.02
    G["ONE_ISLAND"].add(name)
    pos, beads = G["bind_edges"](name, pos, at, tris, MKEY, roll[0], roll[1], 0.0012, thick)
    plate = finish_cap(name, pos, at[:, 3:3 + NB], tris, MKEY, thick, 0.0, 400)
    plate["hides"] = True
    for b_ in beads:
        b_["hides"] = False
    return [plate] + beads, (pos, at, tris)


def bvh_of(objs):
    vs, fs = [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(vs, fs)


def skin_hit(o, d, bvh=None):
    """Her skin where a ray from o along d first meets it, and its normal facing along d (None if it misses). `bvh`:
    that skin instead of the scene's (final_skin_bvh, STRAP_FINAL)."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    h = (bvh or G["SKIN_BVH"]).ray_cast(Vector(tuple(o)), Vector(tuple(d)), 0.6)
    if h[0] is None:
        return None, None
    n = np.array(h[1][:])
    return np.array(h[0][:]), (n if n @ d > 0 else -n)


def skin_band(name, cols_pts, cols_nrm, mkey, base_lift, thick, under=None, src_idx=None, sheet=None, clear=0.0004,
              sigma=0.008, follow=True):
    """A leather band or strap that follows her skin: `cols_pts` (columns across it, each a curve of n points on her
    skin, side by side) and their skin normals; each point lifted `base_lift` off her along its own normal, or, where
    something already lies on her there (`under`, a BVH: a plate, its rolled edge, another strap), over that by `clear`,
    eased along it so it bends up over an edge and down onto her skin again. Thickened outward. Weights: her skin's
    near each row (`src_idx`: from those points only: her torso, never her arm), one set across, eased along; where it
    lies on a plate, the plate's own (`sheet`: its points and weights), so it moves with what it is riveted to.
    (r3: her skin's own weights under each point, `sigma` 8 mm, each line along it its own (`follow`): eased over 2 cm and
    one set across, with her arm's share masked off, it sank 5.6 mm into her side with her arms overhead.)"""
    from scipy.ndimage import gaussian_filter1d, maximum_filter1d
    C = np.asarray(cols_pts, float)          # (cols, n, 3)
    Nn = np.asarray(cols_nrm, float)
    k_, n = C.shape[0], C.shape[1]
    need = np.zeros(n)
    if under is not None:
        for j in range(k_):
            for i in range(n):
                o = C[j, i] + Nn[j, i] * 0.03
                h = under.ray_cast(Vector(tuple(o)), Vector(tuple(-Nn[j, i])), 0.04)
                if h[0] is not None and 0.03 - h[3] > -0.002:
                    need[i] = max(need[i], 0.03 - h[3] + clear)
    lift = np.maximum(base_lift, need)
    L = gaussian_filter1d(maximum_filter1d(lift, size=5, mode="nearest"), 2.0, mode="nearest")
    lift = np.maximum(L, lift)
    pos = (C + Nn * lift[None, :, None]).transpose(1, 0, 2).reshape(-1, 3)     # (row-major: along, then across)
    tris = G["grid"](n, k_)
    nor = G["vertex_normals"](pos, tris)
    if (nor * Nn.transpose(1, 0, 2).reshape(-1, 3)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    wt = G["soft_weights"](pos, src_idx, sigma=sigma, k=8).reshape(n, k_, -1)
    if not follow:
        wt[:] = wt.mean(1, keepdims=True)
    on_plate = gaussian_filter1d((need > 0).astype(float), 1.5, mode="nearest")
    if sheet is not None and (need > 0).any():
        s_pos, s_wt = sheet
        d_, j_ = cKDTree(s_pos).query(C[k_ // 2], k=8)
        g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
        swt = (s_wt[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
        wt = wt * (1 - on_plate[:, None, None]) + swt[:, None, :] * on_plate[:, None, None]
    for _ in range(6):
        wt[1:-1] = (wt[:-2] + 2 * wt[1:-1] + wt[2:]) / 4
    wt = wt.reshape(n * k_, -1)
    o_ = G["finish"](name, pos, wt, tris, mkey, thick, 0.0, 10 ** 7)
    o_["hides"] = False
    return [o_], dict(cols=C, nrm=Nn, lift=lift, on_plate=need > 0)


def build_plate_top():
    nip = G["NIPPLE"]
    roll = PRM.get("roll", {"width": 0.005, "height": 0.0009})
    lift, thick = PRM.get("lift", 0.0015), PRM.get("thick", 0.003)
    top_line = G["plunge_line"](PRM.get("over", 0.03), PRM.get("low", 0.03), PRM.get("wing", 0.022))
    cname = f"{PID}.cups"
    cups = fitted_cups(cname, top_line, lift, thick, roll, PRM.get("gap", 0.011), PRM.get("side", 0.07), PRM.get("fold", 0.0))
    sheet_pos, sheet_wt, sheet_tris, _ = CAP["sheet"][cname]
    CUP_PEAK = G["CUP_PEAK"]
    arms = G["ARMW"]["l"] + G["ARMW"]["r"]
    # (no underbust band: tried (18 Oct, r2) and dropped. The cups now lie on her own surface, so nothing has to hold
    # them visually; a band at the ribs is a second horizontal line across her midriff that reads as a belt and
    # covers skin the look wants bare. The back strap, as round 1, closes it behind.)
    back_z = G["UNDERBUST"] + PRM.get("back_rise", 0.035)
    sw = PRM.get("strap_width", 0.016)
    bw = PRM.get("back_width", 0.02)
    cup_parts = cups
    cup_bvh = bvh_of(cup_parts)
    # ---- the back band (r3): a fitted band, as a bra's. It starts on each cup's outer side, a tab riveted on the plate
    # `tab` in from its side seam, bends down over the rolled edge onto her skin and follows her ribs `band_lift` off
    # her (each of its edges and its middle laid on her by a level ray from her middle out, so it lies on her across
    # its width too), under her arm, round to her spine, where a buckle closes it. Weights her skin's under it (it lies
    # on her: skin_band), the plate's own on the tab.
    rr = FIT["rim_r"]
    seam = rr[rr[:, 1] > rr[:, 1].max() - 0.004]
    zlo, zhi = float(seam[:, 2].min()), float(seam[:, 2].max())
    z_anc = float(np.clip(zlo + PRM.get("band_seam", 0.35) * (zhi - zlo), zlo + bw / 2 + 0.004, zhi - bw / 2 - 0.004)) if zhi - zlo > bw + 0.008 else (zlo + zhi) / 2
    fr = G["front_point"](0.0, back_z)
    bk_ = skin_hit((0.0, 0.6, back_z), (0, -1.0, 0))[0]
    cxy = np.array([0.0, (fr[1] + (bk_[1] if bk_ is not None else 0.12)) / 2])
    anc = seam[np.argmin(np.abs(seam[:, 2] - z_anc))] * mirror        # (her left: x > 0)
    ang = lambda p: float(np.arctan2(p[0] - cxy[0], -(p[1] - cxy[1])))
    a_seam = ang(anc)
    r_seam = float(np.hypot(anc[0] - cxy[0], anc[1] - cxy[1]))
    a_start = a_seam - PRM.get("tab", 0.02) / r_seam
    def band_z(a):
        s = np.clip(np.abs(a - np.pi) / (np.pi - a_seam), 0, 1)
        return back_z + (z_anc - back_z) * (s * s * (3 - 2 * s))
    def band_ray(a, dz):
        z = band_z(a) + dz
        return skin_hit((cxy[0], cxy[1], z), (np.sin(a), -np.cos(a), 0.0))
    af = np.linspace(a_start, 2 * np.pi - a_start, 1600)
    mid = np.array([band_ray(a, 0.0)[0] for a in af])
    run_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
    nb = max(40, int(round(run_[-1] / PRM.get("band_step", 0.004))))
    aa = np.interp(np.linspace(0, run_[-1], nb), run_, af)
    cols, nrms = [], []
    for dz in (-bw / 2, 0.0, bw / 2):
        h_ = [band_ray(a, dz) for a in aa]
        cols.append(np.array([h[0] for h in h_]))
        nrms.append(np.array([h[1] for h in h_]))
    nrms = np.array(nrms)
    for _ in range(3):
        nrms[:, 1:-1] = (nrms[:, :-2] + 2 * nrms[:, 1:-1] + nrms[:, 2:]) / 4
    nrms /= np.linalg.norm(nrms, axis=2)[:, :, None]
    band_lift, band_thick = PRM.get("band_lift", 0.0015), PRM.get("band_thick", 0.0025)
    band, binfo = skin_band(f"{PID}.backstrap", cols, nrms, "darkleather", band_lift, band_thick, under=cup_bvh,
                            sheet=(sheet_pos, sheet_wt))
    BAND.update(binfo, aa=aa, a_seam=a_seam, z_anc=z_anc, seam_z=(zlo, zhi), cxy=cxy, thick=band_thick, objs=band)
    backstrap = band
    # The shoulder straps: from each cup's top outer corner over her shoulder, down her back onto the band, riveted
    # there. Laid as before (rays out from inside her chest), now lifted off her the same way: `strap_lift` off her
    # skin, over the cup at its foot and over the band at its end.
    mc = cols[1]
    straps, strap_lines = [], {}
    for sd, sg in (("l", 1), ("r", -1)):
        pk = CUP_PEAK[sd]
        tp = G["front_point"](pk[0] - sg * 0.004, pk[2] - 0.012)
        back_half = mc[(mc[:, 1] > cxy[1]) & (np.sign(mc[:, 0]) == sg)]
        bp = back_half[np.argmin(np.abs(back_half[:, 0] - sg * 0.085))]
        cv = [tp, np.array([sg * 0.11, 0.03, 1.565]), np.array([sg * 0.1, 0.11, 1.47]), np.array([bp[0], bp[1] + 0.005, bp[2] - 0.004])]
        strap_lines[sd] = cv
        straps.append((sd, cv))
    under_s = bvh_of(cup_parts + band)
    centre = np.array([0.0, 0.0, 1.33])
    strap_objs = {}
    # (STRAP_FINAL, 21 Oct, armor 8 r3: laid on her skin as her body build leaves it, not the scene's: over the crest
    # of her shoulder the scene's skin stands up to 8 mm above hers, so the strap stood 7-13 mm off her there and
    # flicked up beside her neck over a pauldron at the play camera)
    fsk = G["final_skin_bvh"]() if os.environ.get("STRAP_FINAL", "1") == "1" else None
    for sd, cv in straps:
        c = G["spline"](cv, step=0.004)
        lay = lambda pts: np.array([skin_hit(centre, p - centre, fsk)[0] for p in pts])
        c = lay(c)
        for _ in range(3):
            c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
            c = lay(c)
        nr = np.array([skin_hit(centre, p - centre, fsk)[1] for p in c])
        for _ in range(4):
            nr[1:-1] = (nr[:-2] + 2 * nr[1:-1] + nr[2:]) / 4
        nr /= np.linalg.norm(nr, axis=1)[:, None]
        tg = np.gradient(c, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        bn = np.cross(nr, tg)
        bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
        sc, sn = [], []
        for o_ in (-0.5, 0.0, 0.5):
            h_ = [skin_hit(centre, p + b * o_ * sw - centre, fsk) for p, b in zip(c, bn)]
            sc.append(np.array([h[0] for h in h_]))
            sn.append(np.array([h[1] for h in h_]))
        sn = np.array(sn)
        for _ in range(3):
            sn[:, 1:-1] = (sn[:, :-2] + 2 * sn[:, 1:-1] + sn[:, 2:]) / 4
        sn /= np.linalg.norm(sn, axis=2)[:, :, None]
        strap_objs[sd], sinfo = skin_band(f"{PID}.strap_{sd}", sc, sn, "darkleather", PRM.get("strap_lift", 0.002), 0.003,
                                          under=under_s, sheet=(sheet_pos, sheet_wt))
        STRAPS[sd] = dict(sinfo, objs=strap_objs[sd])
    allstraps = [o for v_ in strap_objs.values() for o in v_]
    # The fixings: a rivet where each shoulder strap meets the band, two through each tab of the band on its cup, one
    # through each shoulder strap's foot on its cup.
    aims = []
    for sd, cv in straps:
        e_ = STRAPS[sd]["cols"][1][-3]
        en = STRAPS[sd]["nrm"][1][-3]
        aims.append((e_ + en * 0.05, e_))
    bc_, bn_ = BAND["cols"][1], BAND["nrm"][1]
    brun = np.r_[0, np.cumsum(np.linalg.norm(np.diff(bc_, axis=0), axis=1))]
    for at_ in (0.006, 0.0145):
        for i_ in (int(np.argmin(np.abs(brun - at_))), int(np.argmin(np.abs(brun - (brun[-1] - at_))))):
            aims.append((bc_[i_] + bn_[i_] * 0.05, bc_[i_]))
    fpts, fn = aim_hits(allstraps + backstrap, aims)
    for sd, cv in straps:
        q = STRAPS[sd]["cols"][1][2]
        p_, n_ = aim_hits(strap_objs[sd], [(q + STRAPS[sd]["nrm"][1][2] * 0.05, q)])
        fpts += p_
        fn += n_
    fix = low_rivets(f"{PID}.strap_rivets", fpts, fn, G["soft_weights"](np.array(fpts)), 0.0028, MKEY) if fpts else []
    bk = PRM.get("buckle", {"t": 0.45, "w": 0.024, "h": 0.019, "r": 0.0014})
    buckles, bsock = [], {}
    for sd, cv in straps:
        m, s_ = strap_buckle(f"{PID}.buckle_{sd}", strap_objs[sd], np.asarray(cv[0]), np.asarray(cv[1]), bk["t"], bk["w"], bk["h"], bk["r"])
        buckles += m
        bsock[sd] = s_
    # (the band's closure at her spine: a buckle, its frame across the band)
    ib = int(np.argmin(np.abs(BAND["aa"] - np.pi)))
    lifted = BAND["cols"][1] + BAND["nrm"][1] * 0.02
    bkb = PRM.get("back_buckle", {"w": bw + 0.007, "h": 0.022, "r": 0.0015})
    m, s_ = strap_buckle(f"{PID}.buckle_back", band, lifted[ib - 3], lifted[ib + 3], 0.5, bkb["w"], bkb["h"], bkb["r"])
    buckles += m
    bsock["back"] = s_
    # The gore: between the cups' lower inner corners (the lowest point of each inner rim), from `top` above them to
    # `drop` below, on her sternum.
    gp = PRM.get("gore", {"top": 0.014, "drop": 0.02, "hw_tip": 0.005, "lift": 0.001, "thick": 0.0025, "roll": [0.0035, 0.0006]})
    rr = FIT["rim_r"]
    x_min = np.abs(rr[:, 0]).min()
    near_in = rr[np.abs(rr[:, 0]) < x_min + 0.012]
    z_corner = near_in[:, 2].min()
    gz_top, gz_tip = z_corner + gp["top"], z_corner - gp["drop"]
    grow = gore_row(gz_top, gz_tip) if gp.get("rigid", True) else None
    gore, gsheet = gore_plate(f"{PID}.gore", [cups[0]], gz_top, gz_tip, x_min + 0.012, gp["hw_tip"], gp["lift"], gp["thick"], gp["roll"], grow)
    if grow is not None:
        for o_ in gore:
            set_one_blend(o_, top4(grow))
    gs = gsheet[0]
    gc = np.array(G["front_point"](0.0, (gz_top + gz_tip) / 2))
    zr = gz_top - 0.007
    band_ = gs[np.abs(gs[:, 2] - zr) < 0.002]
    xr = (np.abs(band_[:, 0]).max() - 0.0055) if len(band_) else 0.008
    zt = gs[:, 2].min() + 0.0075
    gpts_, gn_ = aim_hits(gore, [((0.0, -0.6, zt), (0.0, 0.0, zt))] + [((sg * xr, -0.6, zr), (sg * xr, 0.0, zr)) for sg in (1, -1)])
    gwt_ = np.repeat(grow[None], len(gpts_), 0) if grow is not None else (G["soft_weights"](np.array(gpts_)) if gpts_ else None)
    gore_rivets = low_rivets(f"{PID}.gore_rivets", gpts_, gn_, gwt_, 0.0024, MKEY) if gpts_ else []
    FIT["gore"] = {"top_z": round(float(gz_top), 4), "tip_z": round(float(gz_tip), 4), "cups_apart_mm": round(float(2 * x_min * 1000), 1),
                   "rigid_blend": top4(grow) if grow is not None else None}
    shell = [cups[0], gore[0]]
    parts = cups + allstraps + backstrap + fix + buckles + gore + gore_rivets
    # ---- sockets
    cup_obj = cups[0]
    cbvh = BVHTree.FromPolygons([tuple(cup_obj.matrix_world @ v.co) for v in cup_obj.data.vertices], [p.vertices[:] for p in cup_obj.data.polygons])
    socks = {}

    def sock(name, p, n, up, row):
        n = np.asarray(n, float) / np.linalg.norm(n)
        up = np.asarray(up, float) - n * (np.asarray(up, float) @ n)
        up /= np.linalg.norm(up)
        socks[name] = {"point": gl(p).round(5).tolist(), "normal": gl(n).round(5).tolist(), "up": gl(up).round(5).tolist(),
                       "weights": top4(row)}

    # (the cup point: cast out from her right nipple onto the cup's outer face; her left is its mirror, as the shell
    # is (fitted_cups mirrors the right cup). A cast from each side missed on the left and fell back 12 mm off the plate.)
    q = nip["r"]
    nn = np.array(G["SKIN_BVH"].find_nearest(Vector(q))[1][:])
    cp_, cn_ = q + nn * 0.01, nn
    for t_ in (0.03, 0.0005):     # (from outside first: the outer face, where adornment sits)
        h = cbvh.ray_cast(Vector(q + nn * t_), Vector(-nn if t_ > 0.01 else nn), 0.05)
        if h[0] is not None:
            cp_, cn_ = np.array(h[0][:]), np.array(h[1][:])
            break
    assert np.linalg.norm(cp_ - q) < 0.02, "cup socket: no cup face over her right nipple"
    if cn_ @ nn < 0:
        cn_ = -cn_
    for sd in "lr":
        p_, n_ = (cp_, cn_) if sd == "r" else (cp_ * mirror, cn_ * mirror)
        sock(f"cup_{sd}", p_, n_, [0, 0, 1.0], G["soft_weights"](p_[None])[0])
        pk = CUP_PEAK[sd]
        sock(f"strap_{sd}", pk, G["SKIN_BVH"].find_nearest(Vector(pk))[1][:], np.asarray(strap_lines[sd][1]) - pk, G["soft_weights"](pk[None])[0])
        bs = bsock[sd]
        sock(f"buckle_{sd}", bs["point"], bs["normal"], bs["up"], bs["weights"])
        sh = np.asarray(strap_lines[sd][1])
        sock(f"shoulder_{sd}", sh, G["SKIN_BVH"].find_nearest(Vector(sh))[1][:], [0, 1.0, 0], G["soft_weights"](sh[None])[0])
    gn = np.array(G["SKIN_BVH"].find_nearest(Vector(gc))[1][:])
    sock("gore", gc + gn * (gp["lift"] + gp["thick"]), gn, [0, 0, 1.0], grow if grow is not None else G["soft_weights"](gc[None])[0])
    NUM_FIT.update(FIT.get("gore", {}))
    bs = bsock["back"]
    sock("back", bs["point"], bs["normal"], [0, 0, 1.0], bs["weights"])
    # ---- rims: the rolled edges' lines (the cut outline made fair), each with its weights
    rims = {}
    for tn, tb in CAP["tubes"].items():
        if not tn.startswith(cname + "_bind"):
            continue
        cur = tb["curve"]
        sd = "l" if cur[:, 0].mean() > 0 else "r"
        nm = f"cup_rim_{sd}"
        d_, j_ = cKDTree(sheet_pos).query(cur, k=8)
        g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
        ring = (sheet_wt[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
        rims[nm] = {"closed": True, "points": gl(cur).round(5).tolist(), "normals": gl(tb["nrm"]).round(4).tolist(),
                    "outward": gl(tb["outward"]).round(4).tolist(), "weights": [top4(r_) for r_ in ring],
                    "roll": {"width": tb["width"], "height": tb["height"], "overhang": tb["overhang"]}, "tube": tn}
    return dict(parts=parts, shell=shell, envelope=[cups[0]], gore=[gore[0]], sheet=(sheet_pos, sheet_wt, sheet_tris), thick=thick,
                lift=lift, sockets=socks, rims=rims, roll=roll, avoid=[np.asarray(cv[0]) for _, cv in straps])


STYLES = {("top", "plate"): build_plate_top}
stamp("building %s (%s/%s)" % (PID, SLOT, SPEC_PIECE["style"]))
B = STYLES[(SLOT, SPEC_PIECE["style"])]()
G["finish"], G["tube"], G["stitches"] = _finish, _tube, _stitches

# ------------------------------------------------------------ adornment --
adorn_made = []
RIVET_ROWS = {}
# (each native row's elements, recorded in <id>.sockets.json "adorn": a tier variant (tools/armor/adorn.py) finds them
# in the built mesh by these feet to drop or regild them; pushed with the piece below)
ADORN_REC = []
sheet_pos, sheet_wt, sheet_tris = B["sheet"]
for ad in SPEC_PIECE.get("adorn", []):
    if ad["kind"] == "row" and ad.get("mesh", "rivet") == "rivet":
        # Evenly along each rolled edge: n rivets to a rim, n the nearest whole number to its length / spacing,
        # `inset` in from the rim line, on the sheet's outer face; none under a strap's foot (its own fixing is there).
        sb = BVHTree.FromPolygons([tuple(p) for p in sheet_pos], sheet_tris.tolist())
        snor = G["vertex_normals"](sheet_pos, sheet_tris)
        stree = cKDTree(sheet_pos)
        pts, nrs, spc = [], [], {}
        for tn, tb in CAP["tubes"].items():
            if not tn.startswith(f"{PID}.cups_bind"):
                continue
            cur, ow = tb["curve"], tb["outward"]
            cw = np.vstack([cur, cur[:1]])
            run_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cw, axis=0), axis=1))]
            n_ = max(3, int(round(run_[-1] / ad.get("spacing", 0.021))))
            ss = (np.arange(n_) + 0.5) * run_[-1] / n_
            at_ = lambda a_: np.stack([np.interp(ss, run_, np.vstack([a_, a_[:1]])[:, k]) for k in range(3)], 1)
            q, o_ = at_(cur), at_(ow)
            q = q - o_ / np.linalg.norm(o_, axis=1)[:, None] * ad.get("inset", 0.0075)
            kept = []
            for k, qq in enumerate(q):
                if any(np.linalg.norm(qq - a_) < ad.get("avoid", 0.014) for a_ in B.get("avoid", [])):
                    continue
                h_ = sb.find_nearest(Vector(qq))
                hp, hn = np.array(h_[0][:]), np.array(h_[1][:])
                if hn @ snor[stree.query(hp)[1]] < 0:
                    hn = -hn
                pts.append(hp + hn * (B["thick"] + 0.0002))
                nrs.append(hn)
                kept.append(ss[k])
            spc[tn] = {"rim_mm": round(run_[-1] * 1000, 1), "count": n_, "kept": len(kept), "spacing_mm": round(run_[-1] / n_ * 1000, 1)}
        d_, j_ = stree.query(np.array(pts), k=8)
        g_ = np.exp(-0.5 * (d_ / 0.004) ** 2) + 1e-12
        wts = (sheet_wt[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
        rv = low_rivets(f"{PID}.{ad.get('rim', 'rim')}_rivets", pts, nrs, wts, ad.get("r", 0.0028), ad.get("mat", MKEY))
        RIVET_ROWS = spc
        adorn_made += rv
        ADORN_REC.append({"kind": "row", "rim": ad.get("rim", "cup_rim"), "mesh": "rivet", "mat": ad.get("mat", MKEY),
                          "spacing": ad.get("spacing", 0.021), "inset": ad.get("inset", 0.0075), "r": ad.get("r", 0.0028),
                          "avoid": ad.get("avoid", 0.014), "points": np.array(pts), "normals": np.array(nrs)})
    elif ad["kind"] in ("row", "mesh", "trim", "paint"):
        pass   # (built on the exported piece by tools/armor/adorn.py, after its LODs)
    else:
        raise NotImplementedError("adornment %s (item 3b)" % ad)
made = B["parts"] + adorn_made
for o in made:
    if "hides" not in o.keys():
        o["hides"] = False
stamp("piece made: %d parts" % len(made))
if os.environ.get("ARMOR_PREVIEW") == "1":
    # (a quick look while shaping: her skin as built on (P, N), not the game's; the full build measures that)
    def _qgap(objs):
        vs_, fs_ = [], []
        for o in objs:
            b0 = len(vs_)
            vs_ += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            fs_ += [[b0 + k for k in p_.vertices] for p_ in o.data.polygons]
        tr_ = BVHTree.FromPolygons(vs_, fs_)
        lo_, hi_ = np.min(vs_, 0) - 0.01, np.max(vs_, 0) + 0.01
        idx_ = np.nonzero(((P > lo_) & (P < hi_)).all(1))[0]
        res = []
        for i in idx_:
            n_ = N[i] / (np.linalg.norm(N[i]) + 1e-12)
            h_ = tr_.ray_cast(Vector(P[i] + n_ * 0.0001), Vector(n_), 0.03)
            if h_[0] is not None:
                res.append((i, h_[3], np.array(h_[0][:])))
            elif tr_.ray_cast(Vector(P[i] + n_ * 0.0001), Vector(-n_), 0.012)[0] is not None:
                res.append((i, -1.0, P[i]))
        return res
    rimp_ = np.vstack([tb["curve"] for tn, tb in CAP["tubes"].items() if tn.startswith(f"{PID}.cups_bind")])
    q_ = _qgap(B["envelope"])
    g_ = np.array([r_[1] for r_ in q_]) * 1000
    hp_ = np.array([r_[2] for r_ in q_])
    dr_ = cKDTree(rimp_).query(hp_)[0]
    ax_ = np.abs(hp_[:, 0])
    inner_ = (dr_ < 0.012) & (ax_ < FIT["x_min"] + 0.015) & (g_ >= 0)
    under_ = (dr_ < 0.012) & (hp_[:, 2] < G["NIPPLE"]["r"][2] - 0.015) & ~inner_ & (g_ >= 0)
    crown_ = (dr_ > 0.03) & (g_ >= 0)
    pr = lambda nm, m: print("PREVIEW %s: n %d p50 %.1f p99 %.1f max %.1f" % (nm, m.sum(), np.median(g_[m]), np.percentile(g_[m], 99), g_[m].max()) if m.any() else "PREVIEW %s: none" % nm)
    pr("underbust", under_); pr("inner", inner_); pr("crown", crown_); pr("all", g_ >= 0)
    print("PREVIEW through (skin outside the cups):", int((g_ < 0).sum()))
    print("PREVIEW standoff cups", standoff(f"{PID}.cups", G["BVH"]))
    print("PREVIEW standoff gore", standoff(f"{PID}.gore", G["BVH"]))
    np.savez(os.path.join(SCRATCH, "preview.npz"), skin=np.array([P[r_[0]] for r_ in q_]), gap=g_, hit=hp_, dr=dr_,
             nip=G["NIPPLE"]["r"], rim=rimp_, filled=np.array([G["P_FILLED"][r_[0]] for r_ in q_]))
    qg = _qgap(B["gore"])
    gg = np.array([r_[1] for r_ in qg if r_[1] >= 0]) * 1000
    print("PREVIEW gore: n %d p50 %.1f p99 %.1f max %.1f; through %d" % (len(gg), np.median(gg), np.percentile(gg, 99), gg.max(), sum(r_[1] < 0 for r_ in qg)) if len(gg) else "PREVIEW gore none")
    tris_ = {}
    for o in made:
        k_ = o.data.materials[0].name if o.data.materials else "-"
        tris_[k_] = tris_.get(k_, 0) + sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
    print("PREVIEW triangles", sum(tris_.values()), tris_, "rivet rows", RIVET_ROWS)
    for o in made:
        print("PREVIEW part %s %d" % (o.name, sum(len(p_.vertices) - 2 for p_ in o.data.polygons)))
    for o in list(bpy.data.objects):
        if o not in made and o is not body and o is not arm:
            bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SCRATCH, "preview.blend"), copy=True)
    raise SystemExit(0)
G["made"] = made
# (her machinery's second part: what must be covered, the tuck rule, the slots, the tuck writer)
run(src.index(M_LOOP) + len(M_LOOP), src.index(M_BODY), NS)
stamp("cover regions and tuck rule ready")

# --------------------------------------------- the trim strip's UVs (rims) --
TRIM = json.load(open(os.path.join(ART, "trim_strip.json"), encoding="utf-8"))


def trim_uv(obj, tb, band):
    """A rolled edge's 'trim' UVs: u along its line in metres / the strip's metres_u, v round its profile
    into the band (both faces of the roll: 0 at its outer lip, 1 back under the plate)."""
    me = obj.data
    co = np.array([v.co[:] for v in me.vertices])
    cur = tb["curve"]
    seg = np.linalg.norm(np.diff(np.vstack([cur, cur[:1]]), axis=0), axis=1)
    run = np.r_[0, np.cumsum(seg)][:-1]
    _, j = cKDTree(cur).query(co)
    d = co - cur[j]
    c0 = cur + tb["outward"] * (tb["overhang"] - tb["width"] / 2) + tb["nrm"] * (tb["thick"] / 2)
    d = co - c0[j]
    ang = np.arctan2((d * tb["nrm"][j]).sum(1), (d * tb["outward"][j]).sum(1))     # (0 at the lip, +pi/2 on top)
    f = np.abs(ang) / np.pi
    b = TRIM["bands"][band]
    uvs = np.c_[run[j] / TRIM["metres_u"], b["v0"] + f * (b["v1"] - b["v0"])]
    lay = me.uv_layers.new(name="trim")
    li = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", li)
    lay.data.foreach_set("uv", uvs[li].astype(np.float32).ravel())
    me.uv_layers.active_index = 0


for tn, tb in CAP["tubes"].items():
    if tn.startswith(f"{PID}.cups_bind"):
        trim_uv(tb["obj"], tb, "rolled_edge")

# ------------------------------------------------ her skin's tuck under it --
me = body.data
hides = [o for o in made if o.get("hides")]
tuck, hid = G["tuck_of"](PID, hides, SLOT)
tuck_of_out = tuck.copy()
stamp("tuck: %d of her vertices under it" % hid)
# (r3, F7: her skin under the gore's footprint sunk at least 3 mm (a mark of 0.3: 10 mm times it), all of it in the
# middle, so the gore stands clear of her in every calling's idle. The footprint: her points whose ray out along her
# normal meets the gore's inner face within 20 mm, plus those within 2 mm of it across her skin (its margin). Over
# it the mark ramps from 0.3 at its edge to full (0.98) 8 mm in. Nowhere else changes.)
if f"{PID}.gore" in CAP["sheet"]:
    gsp_, _, gst_, _ = CAP["sheet"][f"{PID}.gore"]
    gtree_ = BVHTree.FromPolygons([tuple(p) for p in gsp_], gst_.tolist())
    bw_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
    nm_ = body.matrix_world.to_3x3().inverted().transposed()
    bn_ = np.array([(nm_ @ v.normal).normalized()[:] for v in me.vertices])
    cand_ = np.nonzero(cKDTree(gsp_).query(bw_, distance_upper_bound=0.04)[0] < 0.04)[0]
    inF_, marg_ = [], []
    for i in cand_:
        p_, n_ = Vector(bw_[i]), Vector(bn_[i])
        h_ = gtree_.ray_cast(p_ - n_ * 0.003, n_, 0.023)
        if h_[0] is not None:
            inF_.append(i)
            continue
        q_ = gtree_.find_nearest(p_)[0]
        if q_ is not None:
            d_ = np.array((q_ - p_)[:])
            tang_ = d_ - bn_[i] * d_.dot(bn_[i])
            if np.linalg.norm(tang_) <= 0.002 and abs(d_.dot(bn_[i])) < 0.02:
                marg_.append(i)
    inF_, marg_ = np.array(inF_, int), np.array(marg_, int)
    if len(inF_):
        out_ = np.setdiff1d(cand_, inF_)
        din_ = cKDTree(bw_[out_]).query(bw_[inF_])[0] if len(out_) else np.full(len(inF_), 1.0)
        want_ = 0.3 + 0.68 * np.clip((din_ - 0.002) / 0.006, 0.0, 1.0)
        tuck[inF_] = np.maximum(tuck[inF_], want_)
    if len(marg_):
        tuck[marg_] = np.maximum(tuck[marg_], 0.3)
    stamp("tuck under the gore: %d footprint points (%d full), %d margin" % (len(inF_), int((tuck[inF_] > 0.973).sum()) if len(inF_) else 0, len(marg_)))
    # (armor 7, THE BOUNDED TUCK (heroine_outfits.py, tuck_bound): the gore's footprint taken through the same rule,
    # so its 0.3 margin and 8 mm climb slope in from the border like every other piece's; ARMOR_GORE_BOUND=0: as it was)
    if G.get("TUCK_SMOOTH") and os.environ.get("ARMOR_GORE_BOUND", "1") == "1":
        tuck_pre_bound = tuck.copy()
        tuck = G["tuck_bound"](tuck, G["TUCK_LAST"]["hard"], G["TUCK_LAST"]["under"] | (tuck > 0), label=PID + " with the gore")
# (her coverage at rest, her skin tucked as the game draws it: 10 mm times the tuck)
_, jb = cKDTree(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])).query(P)
G["cover_report"](PID, made, 0.010 * np.where(tuck[jb] > 0.973, 1.0, tuck[jb]))
TUCK_P = 0.010 * np.where(tuck[jb] > 0.973, 1.0, tuck[jb])
# Her body taken as the full build takes it before it writes her tuck (heroine_outfits.py, `if BODY_OUT:`), so
# her points, and the records and hash made from them, are the game's.
# (her breast weights eased into her body's groups, as the full build does first: chest_smooth and the helpers'
# split read them)
_, jw = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
changed = np.abs(W - G["W_AUTHORED"]).sum(1) > 1e-4
groups = {vg.name: vg for vg in body.vertex_groups}
n_eased = 0
for v in me.vertices:
    j = jw[v.index]
    if not changed[j]:
        continue
    for e in list(v.groups):
        body.vertex_groups[e.group].remove([v.index])
    row_ = W[j]
    top_ = np.argsort(-row_)[:4]
    tot_ = row_[top_].sum() or 1.0
    for b_ in top_:
        if row_[b_] > 0.003:
            vg = groups.get(BONES[b_]) or body.vertex_groups.new(name=BONES[b_])
            groups[BONES[b_]] = vg
            vg.add([v.index], float(row_[b_] / tot_), "REPLACE")
    n_eased += 1
print("BODY breast weights eased at", n_eased, "of her vertices")
if os.environ.get("CHEST_SMOOTH", "1") == "1":
    from heroine_chest import chest_smooth
    chest_smooth(body, G["mend_folds"])
if os.environ.get("AREOLA_OUT", "1") == "1":
    import heroine_areola
    heroine_areola.apply(body, [G["NIPPLE"]["l"], G["NIPPLE"]["r"]])
G["mend_folds"](me, body)
G["rig_helpers"].apply(arm, [body])
keep = None
if G["HAND_PIVOTS"] and G["FINGER_FIX"]:
    keep = [np.empty(len(me.vertices) * 3)]
    me.vertices.foreach_get("co", keep[0])
    for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
        keep.append(np.empty(len(kb.data) * 3))
        kb.data.foreach_get("co", keep[-1])
    G["finger_flattened"](body)
def mesh_world(objs):
    vs, fs, owner = [], [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
        owner += [o.name] * len(o.data.polygons)
    return np.array(vs), fs, owner




def skin_vs_shell(bv, bn, idx, tuck_v, tree):
    out = {"covered": np.zeros(len(idx), bool), "gap": np.full(len(idx), np.nan), "through": np.zeros(len(idx), bool),
           "through_t": np.zeros(len(idx), bool), "deep_t": 0.0, "cov_t": np.zeros(len(idx), bool),
           "deep_t_k": np.zeros(len(idx))}
    for k, i in enumerate(idx):
        n_ = bn[i] / (np.linalg.norm(bn[i]) + 1e-12)
        for tucked in (False, True):
            p_ = bv[i] - n_ * (0.010 * (1.0 if tuck_v[i] > 0.973 else tuck_v[i]) if tucked else 0.0)
            f_ = tree.ray_cast(Vector(p_ + n_ * 0.0001), Vector(n_), 0.03)
            b_ = tree.ray_cast(Vector(p_ + n_ * 0.0001), Vector(-n_), 0.012) if f_[0] is None else (None,)
            if not tucked:
                out["covered"][k] = f_[0] is not None
                out["gap"][k] = f_[3] if f_[0] is not None else np.nan
                out["through"][k] = f_[0] is None and b_[0] is not None
                if out["through"][k]:
                    out.setdefault("deep_u", np.zeros(len(idx)))[k] = b_[3]
            else:
                out["cov_t"][k] = f_[0] is not None
                out["through_t"][k] = f_[0] is None and b_[0] is not None
                if out["through_t"][k]:
                    out["deep_t"] = max(out["deep_t"], b_[3])
                    out["deep_t_k"][k] = b_[3]
    return out


def shell_tree(dg=None):
    vs, fs = [], []
    for o in SHELL:
        oe = o.evaluated_get(dg) if dg is not None else o
        m_ = oe.to_mesh() if dg is not None else o.data
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in m_.vertices]
        fs += [[base + i for i in p_.vertices] for p_ in m_.polygons]
        if dg is not None:
            oe.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)


# ------------------------------------- poses, and the shell pushed out where her skin comes through --
POSES = {
    "arms_overhead": [("clavicle_l", (0, 1, 0), 25, (0, 0, 1)), ("clavicle_r", (0, 1, 0), 25, (0, 0, 1)),
                      ("upperarm_l", (0, 1, 0), 110, (0, 0, 1)), ("upperarm_r", (0, 1, 0), 110, (0, 0, 1))],
    "reach_across_r": [("upperarm_r", (0, 0, 1), 80, (1, -1, 0)), ("lowerarm_r", (0, 0, 1), 60, (1, -1, 0))],
    "arms_back": [("upperarm_l", (0, 0, 1), 40, (0, 1, 0)), ("upperarm_r", (0, 0, 1), 40, (0, 1, 0))],
    "hug": [("clavicle_l", (0, 0, 1), 15, (0, -1, 0)), ("clavicle_r", (0, 0, 1), 15, (0, -1, 0)),
            ("upperarm_l", (0, 0, 1), 70, (0, -1, 0)), ("upperarm_r", (0, 0, 1), 70, (0, -1, 0))],
    "twist_bend": [("spine_02", (1, 0, 0), 20, (0, -1, 0)), ("spine_03", (0, 0, 1), 25, (1, 0, 0))],
    # (r3: arms down at her sides, along her ribs over the band; both arms forward, a two-handed swing's start)
    "arms_down": [("upperarm_l", (0, 1, 0), 40, (0, 0, -1)), ("upperarm_r", (0, 1, 0), 40, (0, 0, -1))],
    "arms_forward": [("upperarm_l", (1, 0, 0), 75, (0, -1, 0)), ("upperarm_r", (1, 0, 0), 75, (0, -1, 0))],
}


def pose_body(rots):
    """Her body posed by `rots` (rest if empty): her points and normals, world, and the depsgraph."""
    from mathutils import Quaternion
    pb = arm.pose.bones
    arm.data.pose_position = "POSE"
    for b in pb:
        b.rotation_mode = "QUATERNION"
        b.rotation_quaternion = (1, 0, 0, 0)
    for bone, axis, deg, want in rots:
        if bone not in pb:
            continue
        b = arm.data.bones[bone]
        d = np.array((b.tail_local - b.head_local)[:])
        d2 = np.array((Quaternion(Vector(axis), np.radians(deg)).to_matrix() @ Vector(d))[:])
        deg = deg if (d2 - d) @ np.asarray(want, float) > 0 else -deg
        R = b.matrix_local.to_3x3()
        qw = Quaternion(Vector(axis), np.radians(deg))
        pb[bone].rotation_quaternion = (R.inverted() @ qw.to_matrix() @ R).to_quaternion() @ pb[bone].rotation_quaternion
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg)
    m_ = be.to_mesh()
    bv = np.array([(body.matrix_world @ v.co)[:] for v in m_.vertices])
    bn = np.array([(body.matrix_world.to_3x3() @ v.normal)[:] for v in m_.vertices])
    be.to_mesh_clear()
    return bv, bn, dg


def pose_rest():
    for b in arm.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()


def push_field(Q, D, A, X, sigma):
    """The push-out at points X: from each deficit (point Q, direction D, amount A) a Gaussian bump `sigma` wide; the
    largest bump's size, along the bumps' weighted direction."""
    X = np.asarray(X, float)
    out = np.zeros_like(X)
    for a0 in range(0, len(X), 4000):
        x = X[a0:a0 + 4000]
        g = np.exp(-((x[:, None, :] - Q[None]) ** 2).sum(2) / (2 * sigma ** 2)) * A[None]
        mag = g.max(1)
        dv = (g[:, :, None] * D[None]).sum(1)
        dv /= np.linalg.norm(dv, axis=1)[:, None] + 1e-12
        out[a0:a0 + 4000] = dv * mag[:, None]
    return out


def push_apply(Q, D, A, sigma):
    """Every part of the piece moved by the push field (a plate, its rolled edge, its rivets and the band's tab all
    together, so nothing parts), and the sheet, sockets and rims with it."""
    for o in made:
        me_ = o.data
        mw = np.array(o.matrix_world)
        inv3 = np.linalg.inv(mw[:3, :3])
        co = np.empty(len(me_.vertices) * 3)
        me_.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        dw = push_field(Q, D, A, co @ mw[:3, :3].T + mw[:3, 3], sigma)
        if not np.abs(dw).max() > 1e-7:
            continue
        dl = dw @ inv3.T
        me_.vertices.foreach_set("co", (co + dl).ravel())
        for kb in (me_.shape_keys.key_blocks if me_.shape_keys else []):
            kc = np.empty(len(kb.data) * 3)
            kb.data.foreach_get("co", kc)
            kb.data.foreach_set("co", (kc.reshape(-1, 3) + dl).ravel())
        me_.update()
    for nm, (sp_, sw_, st_, th_) in list(CAP["sheet"].items()):
        CAP["sheet"][nm] = (sp_ + push_field(Q, D, A, sp_, sigma), sw_, st_, th_)
    blend = lambda g: np.stack([g[..., 0], -g[..., 2], g[..., 1]], -1)
    for s_ in B["sockets"].values():
        p_ = blend(np.array(s_["point"]))
        s_["point"] = gl(p_ + push_field(Q, D, A, p_[None], sigma)[0]).round(5).tolist()
    for r_ in B["rims"].values():
        p_ = blend(np.array(r_["points"]))
        r_["points"] = gl(p_ + push_field(Q, D, A, p_, sigma)).round(5).tolist()
    for a_ in ADORN_REC:
        a_["points"] = a_["points"] + push_field(Q, D, A, a_["points"], sigma)
    B["avoid"] = [p_ + push_field(Q, D, A, np.asarray(p_)[None], sigma)[0] for p_ in B.get("avoid", [])]


SHELL = B["shell"]
bv0 = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
bn0 = np.array([(body.matrix_world.to_3x3() @ v.normal)[:] for v in me.vertices])
sv, sf, _ = mesh_world(B["shell"])
lo, hi = sv.min(0) - 0.03, sv.max(0) + 0.03
NEAR = np.nonzero(((bv0 > lo) & (bv0 < hi)).all(1))[0]
# Pushed out where her skin comes through it, at rest or in any pose (untucked or tucked): a bump of the whole piece
# there, `push_sigma` wide, as deep as she came through plus `push_clear`, at most `push_cap` in all. Rounds until none
# comes through (a push can bring another point near). Never a cut: a cut bared her (r2).
PUSH = {"rounds": []}
PUSH_SIGMA, PUSH_CLEAR, PUSH_CAP = PRM.get("push_sigma", 0.012), PRM.get("push_clear", 0.0008), PRM.get("push_cap", 0.006)
pushed = {}
for rnd in range(PRM.get("push_rounds", 4)):
    defs = {}
    for pname, rots in [("rest", [])] + list(POSES.items()):
        bv, bn, dg = pose_body(rots)
        r_ = skin_vs_shell(bv, bn, NEAR, tuck, shell_tree(dg))
        du = r_.get("deep_u", np.zeros(len(NEAR)))
        if rnd == 0:
            PUSH.setdefault("first_round_by_pose", {})[pname] = {
                "untucked": int(r_["through"].sum()), "tucked": int(r_["through_t"].sum()),
                "deepest_untucked_mm": round(float(du.max() * 1000), 2) if r_["through"].any() else 0.0,
                "deepest_tucked_mm": round(r_["deep_t"] * 1000, 2)}
        for k in np.nonzero(r_["through"] | r_["through_t"])[0]:
            i = int(NEAR[k])
            defs[i] = max(defs.get(i, 0.0), float(max(du[k], r_["deep_t_k"][k])))
    pose_rest()
    PUSH["rounds"].append({"points": len(defs), "max_mm": round(max(defs.values(), default=0) * 1000, 2)})
    if not defs:
        break
    ii = np.array(sorted(defs))
    A = np.array([defs[i] for i in ii]) + PUSH_CLEAR
    A = np.minimum(A, np.maximum(PUSH_CAP - np.array([pushed.get(int(i), 0.0) for i in ii]), 0.0))
    if A.max() <= 1e-6:
        break
    for i, a_ in zip(ii, A):
        pushed[int(i)] = pushed.get(int(i), 0.0) + float(a_)
    D = bn0[ii] / np.linalg.norm(bn0[ii], axis=1)[:, None]
    push_apply(bv0[ii], D, A, PUSH_SIGMA)
    sv, sf, _ = mesh_world(B["shell"])
PUSH["at"] = nip_rel(bv0[sorted(pushed)])[:12] if pushed else []
PUSH["total_mm"] = round(max(pushed.values(), default=0) * 1000, 2)
stamp("push-out: %s" % json.dumps(PUSH))

TUCKDIR = os.path.join(SCRATCH, "tuck")
G["ARMOR_TUCK"].clear()
G["ARMOR_TUCK"][(PID, SLOT)] = tuck
G["armor_tuck_write"](body, TUCKDIR)
BODY_HASH = G["ARMOR_BODY_HASH"]
TUCK_N = G["ARMOR_TUCK_N"][(PID, SLOT)]
if keep is not None:
    me.vertices.foreach_set("co", keep[0])
    for kb, c in zip(me.shape_keys.key_blocks if me.shape_keys else [], keep[1:]):
        kb.data.foreach_set("co", c)
    me.update()
stamp("body hash %s, %d tuck records" % (BODY_HASH, TUCK_N))

# --------------------------------------- the post steps every piece takes --
i0, _ = cut(M_STRAYS)
i1 = src.index(M_RIGID) + len(M_RIGID)
run(i0, i1, NS)
names = set(G["BONE_NAMES"])
n_parts = 0
PARTS_OF = {}
for o in made:
    if o.get("rigid_part"):
        PARTS_OF[o.name] = rigid_parts(o, names)
        n_parts += PARTS_OF[o.name]
stamp("helpers split; %d rigid parts each on one blend" % n_parts)

# ------------------------------------------------------------- numbers --
NUM = {"id": PID, "body_hash": BODY_HASH, "tuck_records": TUCK_N, "tuck_vertices": int(hid)}


sv, sf, _ = mesh_world(B["shell"])
shell_bvh = BVHTree.FromPolygons([tuple(p) for p in sv], sf)
# (the shell's envelope: how far its outer face stands off her filled skin: L1 at most 6 mm)
filled_bvh = BVHTree.FromPolygons([tuple(p) for p in G["P_FILLED"]], G["TRI"].tolist())
def envelope(objs):
    ev, _, _ = mesh_world(objs)
    e_ = np.array([np.linalg.norm(np.array(filled_bvh.find_nearest(Vector(q))[0][:]) - q) for q in ev])
    return {"max": round(float(e_.max() * 1000), 2), "p99": round(float(np.percentile(e_, 99) * 1000), 2), "p50": round(float(np.median(e_) * 1000), 2)}


# (the cups' shell, the gore excepted (item 1.3); and with the cups' rolled edges)
NUM["envelope_mm"] = envelope(B.get("envelope", B["shell"]))
NUM["envelope_with_rolled_edge_mm"] = envelope(B.get("envelope", B["shell"]) + [tb["obj"] for tn, tb in CAP["tubes"].items() if tn.startswith(f"{PID}.cups_bind")])
# Her skin against the shell, at her body's own points (the game's, after the steps above), at rest and posed.
# Covered: a ray out along her normal meets the shell's inner face within 30 mm (gap = that distance). Through:
# no ray out meets it, but one back in does within 12 mm (her skin stands outside the shell). Each counted with her
# skin as drawn (untucked) and tucked as the game draws it (10 mm times the tuck, full past 0.973).
R0 = skin_vs_shell(bv0, bn0, NEAR, tuck, shell_tree())
COV = NEAR[R0["covered"]]
g_ = R0["gap"][R0["covered"]]
NUM["rest"] = {"skin_points_near": int(len(NEAR)), "covered": int(len(COV)),
               "gap_mm": {"max": round(float(g_.max() * 1000), 2), "p99": round(float(np.percentile(g_, 99) * 1000), 2),
                          "p50": round(float(np.median(g_) * 1000), 2)},
               "through_untucked": int(R0["through"].sum()), "through_tucked": int(R0["through_t"].sum()),
               "tucked_not_covered": int(((tuck[NEAR] > 0.5) & ~R0["covered"]).sum())}
# (by place: under the cups' lower rims, along their inner rims, under the gore, the crown (over 30 mm in from a rim))
def region_gaps():
    nipz = G["NIPPLE"]["r"][2]
    gap_in = PRM.get("gap", 0.011)
    rimp = np.vstack([tb["curve"] for tn, tb in CAP["tubes"].items() if tn.startswith(f"{PID}.cups_bind")])
    rt = cKDTree(rimp)
    out = {}
    for key, objs in (("cups", B.get("envelope", B["shell"])), ("gore", B.get("gore", []))):
        if not objs:
            continue
        vs, fs, _ = mesh_world(objs)
        tr = BVHTree.FromPolygons([tuple(p) for p in vs], fs)
        rows = []
        for i in NEAR:
            n_ = bn0[i] / (np.linalg.norm(bn0[i]) + 1e-12)
            h_ = tr.ray_cast(Vector(bv0[i] + n_ * 0.0001), Vector(n_), 0.03)
            if h_[0] is not None:
                rows.append((np.array(h_[0][:]), h_[3]))
        if not rows:
            continue
        hp = np.array([r_[0] for r_ in rows])
        gg = np.array([r_[1] for r_ in rows]) * 1000
        st = lambda m: {"n": int(m.sum()), "max": round(float(gg[m].max()), 2), "p99": round(float(np.percentile(gg[m], 99)), 2),
                        "p50": round(float(np.median(gg[m])), 2)} if m.any() else None
        if key == "gore":
            out["gore"] = st(np.ones(len(gg), bool))
            continue
        dr = rt.query(hp)[0]
        ax_ = np.abs(hp[:, 0])
        inner = (dr < 0.012) & (ax_ < FIT["x_min"] + 0.015)
        under = (dr < 0.012) & (hp[:, 2] < nipz - 0.015) & ~inner
        out["underbust_rim"] = st(under)
        out["inner_rim"] = st(inner)
        out["rim_all"] = st(dr < 0.012)
        out["crown"] = st(dr > 0.03)
    return out


NUM["gaps_by_place_mm"] = region_gaps()
_body_bvh = BVHTree.FromPolygons([tuple(p) for p in bv0], [p_.vertices[:] for p_ in me.polygons])
NUM["standoff_mm"] = {"cups": standoff(f"{PID}.cups", _body_bvh), "gore": standoff(f"{PID}.gore", _body_bvh)}
NUM["standoff_worst_at"] = FIT.get("standoff_worst_at")
NUM["cup_extent_mm"] = {"nipple_x": round(float(abs(G["NIPPLE"]["r"][0]) * 1000), 1), "rim_max_abs_x": round(float(np.abs(FIT["rim_r"][:, 0]).max() * 1000), 1),
                        "rim_min_z_below_nipple": round(float((G["NIPPLE"]["r"][2] - FIT["rim_r"][:, 2].min()) * 1000), 1)}
NUM["rivet_rows"] = RIVET_ROWS
NUM["gore_shape"] = NUM_FIT
NUM["rest"]["through_untucked_at"] = nip_rel(bv0[NEAR[R0["through"]]])
NUM["rest"]["through_untucked_depth_mm"] = (R0["deep_u"][R0["through"]] * 1000).round(2).tolist() if "deep_u" in R0 else []
_gw = COV[np.argsort(-g_)[:5]]
NUM["rest"]["largest_gaps_at"] = gl(bv0[_gw]).round(3).tolist()
# (rolled edges: the widths each rim was given and the width each roll measures across)
rw = {}
for tn, tb in CAP["tubes"].items():
    if tn.startswith(f"{PID}.cups_bind"):
        o = tb["obj"]
        co = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
        cur = tb["curve"]
        _, j = cKDTree(cur).query(co)
        acr = ((co - cur[j]) * tb["outward"][j]).sum(1)
        wid = []
        for k in range(0, len(cur), max(1, len(cur) // 40)):
            m = j == k
            if m.sum() > 4:
                wid.append(acr[m].max() - acr[m].min())
        rw[tn] = {"given_mm": round(tb["width"] * 1000, 2), "measured_mm": [round(float(np.min(wid) * 1000), 2), round(float(np.max(wid) * 1000), 2)],
                  "proud_mm": round((tb["thick"] + tb["height"]) * 1000, 2), "length_mm": round(float(np.linalg.norm(np.diff(cur, axis=0), axis=1).sum() * 1000), 1)}
NUM["rolled_edges"] = rw
NUM["rivets_cup_rims"] = sum(PARTS_OF.get(o.name, 0) for o in adorn_made if o.name.endswith("_rivets"))
NUM["rivets_fixings"] = sum(PARTS_OF.get(o.name, 0) for o in made if o.name.endswith("strap_rivets") or o.name.endswith("gore_rivets"))
NUM["rigid_parts"] = PARTS_OF
NUM["triangles"] = int(sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in made))
NUM["materials"] = sorted({o.data.materials[0].name for o in made if o.data.materials})
NUM["triangles_by"] = {}
for o in made:
    k_ = o.name.split(".", 1)[1].split("_bind")[0]
    k_ = {"strap_l": "straps", "strap_r": "straps", "buckle_l": "buckles", "buckle_r": "buckles", "buckle_l_bar": "buckles", "buckle_r_bar": "buckles",
          "buckle_l_tongue": "buckles", "buckle_r_tongue": "buckles", "buckle_back": "buckles", "buckle_back_bar": "buckles",
          "buckle_back_tongue": "buckles"}.get(k_, k_)
    NUM["triangles_by"][k_] = NUM["triangles_by"].get(k_, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
NUM["triangles_by"]["cups_rolled_edge"] = sum(sum(len(p.vertices) - 2 for p in tb["obj"].data.polygons) for tn, tb in CAP["tubes"].items() if tn.startswith(f"{PID}.cups_bind"))
NUM["parts"] = len(made)
NUM["push_out"] = PUSH
NUM["band"] = {"seam_z": [round(BAND["seam_z"][0], 4), round(BAND["seam_z"][1], 4)], "anchor_z": round(BAND["z_anc"], 4),
               "length_mm": round(float(np.linalg.norm(np.diff(BAND["cols"][1], axis=0), axis=1).sum() * 1000), 1),
               "on_plate_mm": round(float(BAND["on_plate"].sum() * PRM.get("band_step", 0.004) * 1000), 1),
               "lift_on_skin_mm": [round(float(BAND["lift"][~BAND["on_plate"]].min() * 1000), 2), round(float(BAND["lift"][~BAND["on_plate"]].max() * 1000), 2)]}


# (her skin through the shell in test poses: arms overhead, one arm across her, both arms back, a hug, a twist and
# bend, arms down at her sides, both arms forward; and the band and straps on her: how far they stand off her torso,
# whether they go into her, and how near her arm comes to them, at rest and in each pose)
_, _jP = cKDTree(P).query(bv0)
ARM_B = (G["ARMW"]["l"] + G["ARMW"]["r"])[_jP] > 0.5
TORSO_B = (G["ARMW"]["l"] + G["ARMW"]["r"])[_jP] < 0.3
BODY_F = np.array([p_.vertices[:] for p_ in me.polygons if len(p_.vertices) == 3] +
                  [p_.vertices[:3] for p_ in me.polygons if len(p_.vertices) == 4] +
                  [(p_.vertices[0], p_.vertices[2], p_.vertices[3]) for p_ in me.polygons if len(p_.vertices) == 4])


def strap_sets():
    """Each band or strap: its object, and per vertex its section along it (the rest centre line's nearest), whether it
    lies on her skin there (not on a plate or another strap) and whether it is its inner face (its rest distance to her
    skin under its lift plus half its thickness)."""
    out = []
    for nm, info, th in [("band", BAND, BAND["thick"])] + [(f"strap_{sd}", STRAPS[sd], 0.003) for sd in sorted(STRAPS)]:
        o = info["objs"][0]
        v = np.array([(o.matrix_world @ x.co)[:] for x in o.data.vertices])
        sec = cKDTree(info["cols"][1]).query(v)[1]
        d = np.array([np.linalg.norm(np.array(G["SKIN_BVH"].find_nearest(Vector(q))[0][:]) - q) for q in v])
        inner = d < info["lift"][sec] + th / 2
        # (on her skin: not on a plate, nor on the ramp down off it (lifted over its base lift))
        base_ = info["lift"][~info["on_plate"]].min()
        skin = (~info["on_plate"] & (info["lift"] < base_ + 0.0003))[sec]
        # (a strap's end over the band: over the band, not her skin)
        if nm != "band":
            bt = bvh_of(BAND["objs"])
            near_band = np.array([bt.find_nearest(Vector(q), 0.012)[0] is not None for q in info["cols"][1]])
            skin = skin & ~near_band[sec]
        out.append((nm, o, sec, inner, skin))
    return out


STRAP_SETS = strap_sets()


def arm_in_torso(bv, tbvh, arm_i):
    """Her arm's points inside her torso (her own skinning, nothing of the piece's), within the band's height: count and
    the deepest, mm."""
    zb = BAND["cols"][:, :, 2]
    sel = arm_i[(bv[arm_i, 2] > zb.min() - 0.02) & (bv[arm_i, 2] < zb.max() + 0.02)]
    deep = []
    for i in sel:
        h = tbvh.find_nearest(Vector(bv[i]), 0.03)
        if h[0] is not None and (bv[i] - np.array(h[0][:])) @ np.array(h[1][:]) < 0:
            deep.append(np.linalg.norm(bv[i] - np.array(h[0][:])))
    return {"n": len(deep), "deepest_mm": round(float(max(deep, default=0) * 1000), 1)}


def o_cols(nm):
    return BAND["cols"][1] if nm == "band" else STRAPS[nm[-1]]["cols"][1]


def strap_check(bv, bn, dg):
    """Standoff of each band's inner face over her torso skin (per section, the worst point across it; max and p50
    along it), points of it inside her (depth), and her arm's nearest approach (and points of it inside her arm)."""
    lo_, hi_ = bv[TORSO_B].min(0), bv[TORSO_B].max(0)
    res = {}
    tor_f = BODY_F[TORSO_B[BODY_F].all(1)]
    tbvh = BVHTree.FromPolygons([tuple(p) for p in bv], tor_f.tolist())
    arm_i = np.nonzero(ARM_B)[0]
    atree = cKDTree(bv[arm_i])
    for nm, o, sec, inner, skin in STRAP_SETS:
        oe = o.evaluated_get(dg)
        m_ = oe.to_mesh()
        v = np.array([(o.matrix_world @ x.co)[:] for x in m_.vertices])
        oe.to_mesh_clear()
        sd_ = np.full(len(v), np.nan)
        for k in np.nonzero(inner & skin)[0]:
            h = tbvh.find_nearest(Vector(v[k]))
            if h[0] is None:
                continue
            dvec = v[k] - np.array(h[0][:])
            sd_[k] = np.linalg.norm(dvec) * (1 if dvec @ np.array(h[1][:]) >= 0 else -1)
        per = {}
        for k in np.nonzero(np.isfinite(sd_))[0]:
            per[sec[k]] = max(per.get(sec[k], -1), sd_[k])
        pv = np.array(list(per.values())) if per else np.zeros(1)
        da, ja = atree.query(v)
        an = bn[arm_i[ja]]
        inside_arm = int(((da < 0.02) & (((v - bv[arm_i[ja]]) * an).sum(1) < 0)).sum())
        neg = sd_[np.isfinite(sd_) & (sd_ < 0)]
        kmax = max(per, key=per.get) if per else 0
        res.setdefault("arm_in_torso", arm_in_torso(bv, tbvh, arm_i))
        res[nm] = {"standoff_max_at": nip_rel(o_cols(nm)[kmax])[0], "standoff_max_mm": round(float(pv.max() * 1000), 2), "standoff_p50_mm": round(float(np.median(pv) * 1000), 2),
                   "in_her": int(len(neg)), "in_her_deepest_mm": round(float(-neg.min() * 1000), 2) if len(neg) else 0.0,
                   "arm_nearest_mm": round(float(da.min() * 1000), 1), "inside_arm": inside_arm}
    return res


POSE_DUMP = {}


def pose_dump(pname, bv, bn, dg):
    """For tools/armor/adorn.py's check of adornment on her in the test poses: her skin near the piece, posed, and
    every bone's skinning matrix, all in glTF space (Y up), and the posed shell's points to check its own skinning by."""
    C = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1.0]])
    aw = np.array(arm.matrix_world)
    mats = {}
    for pb_ in arm.pose.bones:
        S = aw @ np.array(pb_.matrix) @ np.linalg.inv(np.array(pb_.bone.matrix_local)) @ np.linalg.inv(aw)
        mats[pb_.name] = C @ S @ np.linalg.inv(C)
    sh = []
    for o in SHELL:
        oe = o.evaluated_get(dg)
        m_ = oe.to_mesh()
        sh += [tuple(o.matrix_world @ v.co) for v in m_.vertices]
        oe.to_mesh_clear()
    POSE_DUMP[pname] = {"skin": gl(bv[NEAR]), "skin_n": gl(bn[NEAR]), "bones": sorted(mats), "mats": np.array([mats[k] for k in sorted(mats)]),
                        "shell": gl(np.array(sh)), "tuck": np.asarray(tuck[NEAR], np.float32)}


def gore_in_pose(bv, dg, rest_q=None):
    """The gore plate posed (r2, F7): its standoff off her posed skin (each of its points to her nearest skin, mm: the
    inner face's min and p50, the points nearer her than the plate's thickness) and its bend (the largest distance of a
    posed point from the best rigid fit of its rest points, mm: 0 for a plate that never bends)."""
    objs = B.get("gore", [])
    if not objs:
        return None
    o = objs[0]
    oe = o.evaluated_get(dg)
    m_ = oe.to_mesh()
    q = np.array([(o.matrix_world @ v.co)[:] for v in m_.vertices])
    oe.to_mesh_clear()
    if not hasattr(gore_in_pose, "polys"):
        gore_in_pose.polys = [p_.vertices[:] for p_ in body.data.polygons]
    bt = BVHTree.FromPolygons([tuple(x) for x in bv], gore_in_pose.polys)
    d = np.array([np.linalg.norm(np.array(bt.find_nearest(Vector(x))[0][:]) - x) for x in q]) * 1000
    inner = d < np.median(d)
    r = {"standoff_min_mm": round(float(d.min()), 2), "standoff_inner_p50_mm": round(float(np.median(d[inner])), 2),
         "standoff_inner_max_mm": round(float(d[inner].max()), 2)}
    if rest_q is not None and len(rest_q) == len(q):
        a_, b_ = rest_q - rest_q.mean(0), q - q.mean(0)
        U, _, Vt = np.linalg.svd(a_.T @ b_)
        D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ D @ Vt
        r["bend_mm"] = round(float(np.linalg.norm(a_ @ R - b_, axis=1).max() * 1000), 3)
    return r, q


def pose_check():
    out = {}
    gore_rest = None
    for pname, rots in [("rest", [])] + list(POSES.items()):
        bv, bn, dg = pose_body(rots)
        try:
            pose_dump(pname, bv, bn, dg)
        except Exception as ex:
            print("POSE DUMP failed", pname, repr(ex))
        straps_ = strap_check(bv, bn, dg)
        try:
            g_ = gore_in_pose(bv, dg, gore_rest)
        except Exception as ex:
            print("GORE POSE failed", pname, repr(ex))
            g_ = None
        if pname == "rest":
            out["rest"] = {"straps": straps_}
            if g_ is not None:
                gore_rest = g_[1]
                out["rest"]["gore"] = g_[0]
            continue
        r_ = skin_vs_shell(bv, bn, NEAR, tuck, shell_tree(dg))
        moved = float(np.abs(bv[NEAR] - bv0[NEAR]).max())
        inC = R0["covered"]
        out[pname] = {"skin_moved_mm": round(moved * 1000, 1), "near_points": int(len(NEAR)), "covered_at_rest": int(len(COV)),
                      "through_untucked": int(r_["through"].sum()), "through_tucked": int(r_["through_t"].sum()),
                      "worst_tucked_mm": round(r_["deep_t"] * 1000, 2), "no_longer_covered": int((inC & ~r_["covered"]).sum()),
                      "no_longer_covered_tucked_full": int((inC & ~r_["covered"] & (tuck[NEAR] > 0.973)).sum()),
                      "through_tucked_at": nip_rel(bv0[NEAR[r_["through_t"]]])[:6],
                      "through_untucked_at": nip_rel(bv0[NEAR[r_["through"]]])[:6], "straps": straps_}
        if g_ is not None:
            out[pname]["gore"] = g_[0]
    pose_rest()
    return out


try:
    NUM["poses"] = pose_check()
except Exception as ex:  # (the numbers still come; the pose check names its failure)
    import traceback
    traceback.print_exc()
    NUM["poses"] = {"error": repr(ex)}
if POSE_DUMP:
    np.savez_compressed(os.path.join(SCRATCH, "poses.npz"), names=np.array(sorted(POSE_DUMP)),
                        **{f"{k}__{f}": np.asarray(v[f]) for k, v in POSE_DUMP.items() for f in ("skin", "skin_n", "bones", "mats", "shell", "tuck")})
stamp("numbers measured")
# (armor 7: ARMOR_SCRATCH_ONLY=1, a proof run: the numbers and her tuck into the scratch dir, nothing into godot/art)
if os.environ.get("ARMOR_SCRATCH_ONLY") == "1":
    NUM["push"] = PUSH
    json.dump(NUM, open(os.path.join(SCRATCH, "numbers.json"), "w", encoding="utf-8"), indent=1)
    _ed = np.array([e.vertices[:] for e in me.edges])
    np.savez_compressed(os.path.join(SCRATCH, "tuck_probe.npz"), tuck=tuck, tuck_of=tuck_of_out, need=G["TUCK_LAST"]["need"], cos=G["TUCK_LAST"]["cos"], under=G["TUCK_LAST"]["under"],
                        hard=G["TUCK_LAST"]["hard"], bv0=bv0, bn0=bn0, edges=_ed, co_local=np.array([v.co[:] for v in me.vertices]))
    stamp("scratch only: numbers and tuck in %s; nothing written to godot/art" % SCRATCH)
    raise SystemExit(0)

# --------------------------------------------------------------- export --
mine = made
G["detail"](mine)
by_mat = {}
for o in mine:
    by_mat.setdefault(o.data.materials[0].name if o.data.materials else "none", []).append(o)
joined, ranks = [], {}
rig_helpers = G["rig_helpers"]
for rank, (key, objs) in enumerate(sorted(by_mat.items())):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    order = [objs[0]] + [o for o in bpy.context.view_layer.objects if o.select_get() and o is not objs[0]]
    pieces_ = [[order.index(o), sum(len(f_.vertices) - 2 for f_ in o.data.polygons)] for o in objs]
    if len(objs) > 1:
        rig_helpers.share_keys(objs)
        bpy.ops.object.join()
    objs[0].name = objs[0].data.name = f"{PID}.{SLOT}.{key}"
    joined.append(objs[0])
    ranks[objs[0].name] = {"outfit": PID, "slot": SLOT, "material": key, "rank": 0, "pieces": pieces_, "tier": SPEC_PIECE.get("tier")}
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in joined:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
EXP = os.path.join(SCRATCH, "export")
os.makedirs(EXP, exist_ok=True)
path = os.path.join(EXP, f"{PID}.gltf")
bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="tex", use_selection=True,
                          export_skins=True, export_animations=False, export_yup=True, export_vertex_color="ACTIVE")
import heroine_neck  # noqa: E402
if float(os.environ.get("NECK_CUT", "0.03")):
    heroine_neck.match_pieces(path, heroine_neck.field())
g_ = json.load(open(path, encoding="utf-8"))
# (the steel's metal map (Metal038, shared with the outfits) drops to non-metal in specks, which lit as white paint
# spatter on the cups: this piece's steel is metal all over at the map's mean roughness. Wear is the touch-up shader's,
# never painted here.)
for m_ in g_.get("materials", []):
    if m_.get("name") == MKEY:
        pb_ = m_.setdefault("pbrMetallicRoughness", {})
        pb_.pop("metallicRoughnessTexture", None)
        pb_["metallicFactor"] = 1.0
        pb_["roughnessFactor"] = PRM.get("steel_roughness", 0.37)
for m_ in g_["meshes"]:
    if m_["name"] in ranks:
        m_["extras"] = dict(m_.get("extras", {}), **ranks[m_["name"]])
# (the shared outfit textures, never copies: art/people/outfit_tex holds every one the outfits use)
PEOPLE_TEX = os.path.join(ROOT, "godot", "art", "people", "outfit_tex")
missing = []
for im in g_.get("images", []):
    bn_ = os.path.basename(im["uri"])
    if os.path.exists(os.path.join(PEOPLE_TEX, bn_)):
        im["uri"] = "../people/outfit_tex/" + bn_
    else:
        missing.append(bn_)
g_.setdefault("asset", {})["extras"] = {"armor_piece": PID, "slot": SLOT, "tier": SPEC_PIECE.get("tier"), "body_hash": BODY_HASH,
                                        "source": os.path.relpath(PIECE_JSON, ROOT).replace("\\", "/")}
json.dump(g_, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
if missing:
    print("ARMOR TEXTURES not in art/people/outfit_tex (copied beside the piece):", missing)
# (the piece must sit on the body the game ships: her hash as art/people/armor_index.json has it, item 1)
_pix = json.load(open(os.path.join(ROOT, "godot", "art", "people", "armor_index.json"), encoding="utf-8"))
SHIPPED_HASH = {r.get("body_hash") for r in _pix} - {None}
if SHIPPED_HASH != {BODY_HASH} and os.environ.get("ARMOR_ANY_BODY") != "1":
    json.dump(NUM, open(os.path.join(SCRATCH, "numbers.json"), "w", encoding="utf-8"), indent=1)
    raise SystemExit("ARMOR REFUSED: built on body %s, the shipped body is %s (art/people/armor_index.json); nothing written"
                     % (BODY_HASH, sorted(SHIPPED_HASH)))
import shutil  # noqa: E402
os.makedirs(os.path.join(ART, "armor_tuck"), exist_ok=True)
shutil.copyfile(path, os.path.join(ART, f"{PID}.gltf"))
shutil.copyfile(os.path.join(EXP, f"{PID}.bin"), os.path.join(ART, f"{PID}.bin"))
for bn_ in missing:
    os.makedirs(os.path.join(ART, "tex"), exist_ok=True)
    shutil.copyfile(os.path.join(EXP, "tex", bn_), os.path.join(ART, "tex", bn_))
shutil.copyfile(os.path.join(TUCKDIR, "armor_tuck", f"{PID}.{SLOT}.bin"), os.path.join(ART, "armor_tuck", f"{PID}.bin"))
NUM["meshes"] = sorted(ranks)

# sockets, rims, the UV surface
sockets = {"id": PID, "slot": SLOT, "body_hash": BODY_HASH, "space": "glTF / Godot: Y up, metres, her bind pose",
           "sockets": B["sockets"], "rims": B["rims"],
           "fixings": [gl(p_).round(5).tolist() for p_ in B.get("avoid", [])],
           "adorn": [dict({k: v for k, v in a_.items() if k not in ("points", "normals")}, points=gl(a_["points"]).round(5).tolist(),
                          normals=gl(a_["normals"]).round(4).tolist()) for a_ in ADORN_REC],
           "uv_surface": {"mesh": f"{PID}.{SLOT}.{MKEY}", "layer": "UVMap (TEXCOORD_0)",
                          "units": "metres x the material's repeats (outfit_materials.json), one projection along the cup's facing"},
           "trim_uv": {"layer": "trim (TEXCOORD_2)", "atlas": "res://art/armor/trim_strip.png", "on": sorted(t for t in CAP["tubes"] if t.startswith(f"{PID}.cups_bind")),
                       "band": "rolled_edge"}}
json.dump(sockets, open(os.path.join(ART, f"{PID}.sockets.json"), "w", encoding="utf-8"), indent=1)

# the index row
ix_path = os.path.join(ART, "armor_index.json")
rows = json.load(open(ix_path, encoding="utf-8")) if os.path.exists(ix_path) else []
rows = [r for r in rows if r.get("id") != PID]
amap = G["ARMOR_MAP"]
row = {"id": PID, "outfit": None, "slot": SLOT, "layer": amap["layers"][SLOT], "covers": SPEC_PIECE.get("covers", [SLOT]),
       "meshes": sorted(ranks), "tuck": f"armor_tuck/{PID}.bin", "tuck_count": TUCK_N, "body_hash": BODY_HASH}
if SPEC_PIECE.get("hold"):
    row["hold"] = SPEC_PIECE["hold"]
row["file"] = f"res://art/armor/{PID}.gltf"
row["tier"] = SPEC_PIECE.get("tier")
rows.append(row)
rows.sort(key=lambda r: r["id"])
json.dump(rows, open(ix_path, "w", encoding="utf-8"), indent=1)


def tuck_read(f):
    import struct
    raw = open(f, "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    return {(int(r["x"]), int(r["y"]), int(r["z"])): float(r["t"]) for r in rec}


mine_t = tuck_read(os.path.join(ART, "armor_tuck", f"{PID}.bin"))
wf = os.path.join(ROOT, "godot", "art", "people", "armor_tuck", "warden.top.bin")
if os.path.exists(wf):
    war_t = tuck_read(wf)
    both = set(mine_t) & set(war_t)
    NUM["tuck_vs_warden_top"] = {
        "mine": {"records": len(mine_t), "max": round(max(mine_t.values(), default=0), 3), "full": sum(v > 0.973 for v in mine_t.values())},
        "warden": {"records": len(war_t), "max": round(max(war_t.values(), default=0), 3), "full": sum(v > 0.973 for v in war_t.values())},
        "shared_places": len(both), "only_mine": len(set(mine_t) - set(war_t)), "only_warden": len(set(war_t) - set(mine_t)),
        "shared_mean_diff": round(float(np.mean([mine_t[k] - war_t[k] for k in both])) if both else 0.0, 4)}
NUM["wall_s"] = round(time.time() - T0, 1)
json.dump(NUM, open(os.path.join(SCRATCH, "numbers.json"), "w", encoding="utf-8"), indent=1)
stamp("DONE %s -> %s" % (PID, os.path.join(ART, PID + ".gltf")))
print("ARMOR NUMBERS", json.dumps(NUM))
