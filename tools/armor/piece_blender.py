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
STRAP_FRAMES = {}
STRAP_ROWS = os.environ.get("PLATE_STRAP_ROWS", "1") == "1"   # (PLATE_STRAP_ROWS: see build_plate_top and tools/assets/strap_rows.py)


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
    st_ = lambda m: {"n": int(m.sum()), "max": round(float(d[m].max()), 2), "p99": round(float(np.percentile(d[m], 99)), 2),
                     "p50": round(float(np.median(d[m])), 2)} if m.any() else None
    if not sheet_name.endswith(".cups"):
        return {"all": st_(np.ones(len(d), bool)), "rim": st_(dr < rim_d)}
    ax_ = np.abs(sp[:, 0])
    nipz = G["NIPPLE"]["r"][2]
    inner = (dr < rim_d) & (ax_ < FIT["x_min"] + 0.015)
    lower = (dr < rim_d) & (sp[:, 2] < nipz - 0.015) & ~inner
    FIT["standoff_worst_at"] = {"lower_rim": nip_rel(sp[lower][np.argsort(-d[lower])[:6]]) if lower.any() else [],
                                "crown": nip_rel(sp[dr > 0.03][np.argsort(-d[dr > 0.03])[:6]])}
    return {"lower_rim": st_(lower), "inner_rim": st_(inner), "rim_all": st_(dr < rim_d), "crown": st_(dr > 0.03), "all": st_(np.ones(len(d), bool))}


def cast_sheet(c, unit, tris, front, membrane, sym=None):
    """Her filled skin (P_FILLED) seen from inside her at `c` along the directions `unit` (an icosphere's, `front`
    the ones cast): a sheet on her own surface, a `membrane` of rounds bridging every dip (never sunk into), its
    normals (facing out from c) and its curvature (convex positive, eased). fitted_cups' cast, factored out for the
    cuirass (armor 10 B2)."""
    from scipy import sparse
    fb = G["FILLED_BVH"]
    r = np.full(len(unit), np.nan)
    for i in np.nonzero(front)[0]:
        h = fb.ray_cast(Vector(c), Vector(unit[i]), 0.3)
        if h[0] is not None:
            r[i] = h[3]
    if sym is not None:
        # (`sym`: each direction's mirror (x -> -x); her left taken as her right's mirror, so the sheet is the same
        # both sides, as fitted_cups mirrors its right cup)
        r = np.where(unit[:, 0] > 1e-9, r[sym], r)
    ok = np.isfinite(r)
    tris = tris[ok[tris].all(1)]
    n = len(unit)
    A = G["adjacency"](n, tris)
    deg = np.asarray(A.sum(1)).ravel()
    Am = sparse.diags(1.0 / np.maximum(deg, 1)) @ A
    r = np.where(ok, r, 0.0)
    # (a membrane: eased, but never into her: a dip is bridged, never sunk into)
    for _ in range(membrane):
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
    return pos, nor, H, ok, tris, Am, n


def cut_sheet(f, pos, attr, tris, keep_frac):
    """A cast sheet cut to its outline field f (kept where f > 0: clip, weld, its islands under keep_frac of the
    largest dropped), renumbered; its rim points, edge loops, and each point's distance to the rim in attr's last
    column. fitted_cups' cut, factored out for the cuirass."""
    pos, at, tris = G["clip"](f, pos, attr, tris)
    pos, at, tris = G["weld"](pos, at, tris)
    tris = G["islands"](pos, tris, keep_frac=keep_frac)
    live = np.unique(tris)
    re = -np.ones(len(pos), int)
    re[live] = np.arange(len(live))
    pos, at, tris = pos[live], at[live], re[tris]
    loops = G["edge_loops"](tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops]))
    at[:, -1] = cKDTree(pos[rim]).query(pos)[0]
    return pos, at, tris, rim, loops


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
    pos, nor, H, ok, tris, Am, n = cast_sheet(c, unit, tris, front, PRM.get("membrane", 1))
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
    pos, at, tris, rim, loops = cut_sheet(f, pos, attr, tris, 0.2)
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


STRAP_EXACT = os.environ.get("STRAP_EXACT", "1") == "1"   # (the shoulder straps' edges set off their centre line, see build_plate_top)


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
              sigma=0.008, follow=True, hold=5, ease=2.0):
    """A leather band or strap that follows her skin: `cols_pts` (columns across it, each a curve of n points on her
    skin, side by side) and their skin normals; each point lifted `base_lift` off her along its own normal, or, where
    something already lies on her there (`under`, a BVH: a plate, its rolled edge, another strap), over that by `clear`,
    eased along it so it bends up over an edge and down onto her skin again. Thickened outward. Weights: her skin's
    near each row (`src_idx`: from those points only: her torso, never her arm), one set across, eased along; where it
    lies on a plate, the plate's own (`sheet`: its points and weights), so it moves with what it is riveted to.
    (r3: her skin's own weights under each point, `sigma` 8 mm, each line along it its own (`follow`): eased over 2 cm and
    one set across, with her arm's share masked off, it sank 5.6 mm into her side with her arms overhead.)
    `hold` (points) and `ease` (points, a Gaussian): how far past an edge it stays up and how softly it comes down
    (b2r3: the pauldrons' throat tab came down from the cop's edge over 4 points and stood up like a tag).)"""
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
    L = gaussian_filter1d(maximum_filter1d(lift, size=hold, mode="nearest"), ease, mode="nearest")
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


def band_and_straps(cups, sheet_pos, sheet_wt, CUP_PEAK):
    """build_plate_top's back band, shoulder straps, their rivets and buckles (proven), on any front plate: `cups` its
    parts (the band and straps lie over them), (sheet_pos, sheet_wt) its sheet, FIT["rim_r"] its rim (the band starts
    at its side seam: the rim points furthest back), CUP_PEAK its top outer corners (the straps' roots). Factored out
    for the cuirass (armor 10 B2); plate_top builds bit-identical through it."""
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
            if STRAP_EXACT:
                # (STRAP_EXACT, 21 Oct, armor 8 r4: each line along it set off its laid centre line across it, then
                # dropped onto her along her (eased) normal there, never sideways: laid by rays out from her chest,
                # each edge on its own, they wandered across her where those rays met her skin aslant)
                h_ = [skin_hit(p + b * o_ * sw + n_ * 0.03, -n_, fsk) for p, b, n_ in zip(c, bn, nr)]
                h_ = [(h[0], -h[1]) if h[0] is not None else skin_hit(centre, p + b * o_ * sw - centre, fsk) for h, p, b in zip(h_, c, bn)]
            else:
                h_ = [skin_hit(centre, p + b * o_ * sw - centre, fsk) for p, b in zip(c, bn)]
            sc.append(np.array([h[0] for h in h_]))
            sn.append(np.array([h[1] for h in h_]))
        sn = np.array(sn)
        if os.environ.get("RIB_DUMP"):
            np.savez(os.path.join(os.environ["RIB_DUMP"], f"{PID}.strap_{sd}.npz"), c=sc[1], nrm=nr, tg=tg, bn=bn,
                     pos=np.stack(sc, 1), wrow=np.full(len(c), sw), lrow=np.zeros(len(c)))
        for _ in range(3):
            sn[:, 1:-1] = (sn[:, :-2] + 2 * sn[:, 1:-1] + sn[:, 2:]) / 4
        sn /= np.linalg.norm(sn, axis=2)[:, :, None]
        # (STRAP_ROWS, armor 8 r4: one set of weights across it, eased along, so each row moves as one and its edges stay
        # parallel; each line its own (r3's `follow`, for the band under her arm), its width swung 12-19 mm in her idle
        # over the crest of her shoulder. Its rows are evened again after the graft's weight pass: strap_rows.py)
        strap_objs[sd], sinfo = skin_band(f"{PID}.strap_{sd}", sc, sn, "darkleather", PRM.get("strap_lift", 0.002), 0.003,
                                          under=under_s, sheet=(sheet_pos, sheet_wt), follow=not STRAP_ROWS)
        STRAPS[sd] = dict(sinfo, objs=strap_objs[sd])
        if STRAP_ROWS:
            import strap_rows
            STRAP_FRAMES[f"{PID}.strap_{sd}"] = strap_rows.frame(sc[1], bn, nr, sw / 2 + 0.0006, -0.001, float(sinfo["lift"].max()) + 0.0055)
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
    return dict(backstrap=backstrap, allstraps=allstraps, fix=fix, buckles=buckles, bsock=bsock, strap_lines=strap_lines,
                straps=straps, band=band)


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
    _bs = band_and_straps(cups, sheet_pos, sheet_wt, CUP_PEAK)
    backstrap, allstraps, fix, buckles = _bs["backstrap"], _bs["allstraps"], _bs["fix"], _bs["buckles"]
    bsock, strap_lines, straps = _bs["bsock"], _bs["strap_lines"], _bs["straps"]
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


# ----------------------------------------------------------- the shell: the cuirass --
# (armor 10 B2, b_design_spec.md section 2: ONE breastplate sheet cast from inside her chest as fitted_cups casts (her
# filled skin, a membrane bridging the sternum hollow and the underbust crease), cut to a shallow scoop neck, an armhole
# round each shoulder ball, a side seam, a lower rim bridging under the crease (the gore tip at her middle) and a
# lozenge window; a ridge down her middle on the bar and the gore; rolled edges; one rigid blend (her sternum's). The
# back band, shoulder straps, their rivets and buckles are build_plate_top's own (band_and_straps), the straps rooted
# at the plate's top outer corners.)
CUIR = {}


def lozenge_field(nipz, ub):
    """The window's signed distance in (x, z) (m, positive outside): a lozenge, its top point `win_top` above her
    nipple, its bottom `win_bot` above her underbust, widest `win_at` above her nipple at half-width `win_w` x her
    nipple's |x|, its sides `win_bulge` between straight (0) and elliptic (1), its four points eased by `win_round`
    (an opening: every convex corner rounded to that radius). A function of (x, z) arrays."""
    from scipy.ndimage import distance_transform_edt, map_coordinates
    nx = abs(G["NIPPLE"]["r"][0])
    zt, zb, zw = nipz + PRM.get("win_top", 0.075), ub + PRM.get("win_bot", 0.018), nipz + PRM.get("win_at", 0.01)
    w, b, rr = PRM.get("win_w", 0.42) * nx, PRM.get("win_bulge", 0.2), PRM.get("win_round", 0.008)
    st = 0.00025
    xs = np.arange(-w - 0.02, w + 0.02 + 1e-9, st)
    zs = np.arange(zb - 0.02, zt + 0.02 + 1e-9, st)
    X, Z = np.meshgrid(xs, zs)
    t = np.where(Z >= zw, (Z - zw) / (zt - zw), (zw - Z) / (zw - zb))
    tc = np.clip(t, 0, 1)
    hw = w * ((1 - b) * (1 - tc) + b * np.sqrt(np.maximum(1 - tc * tc, 0)))
    inside = (np.abs(X) < hw) & (t <= 1)
    din = distance_transform_edt(inside) * st
    ero = din > rr
    sd = (distance_transform_edt(~ero) - distance_transform_edt(ero)) * st - rr
    CUIR["window_design"] = {"top_z": round(float(zt), 4), "bottom_z": round(float(zb), 4), "widest_z": round(float(zw), 4),
                             "width_mm": round(float(2 * w * 1000), 1), "height_mm": round(float((zt - zb) * 1000), 1),
                             "area_mm2": round(float((sd < 0).sum() * st * st * 1e6), 0)}

    def f(x, z):
        ix = (np.asarray(x) - xs[0]) / st
        iz = (np.asarray(z) - zs[0]) / st
        inb = (ix >= 0) & (ix <= len(xs) - 1) & (iz >= 0) & (iz <= len(zs) - 1)
        v = map_coordinates(sd, [np.clip(iz, 0, len(zs) - 1), np.clip(ix, 0, len(xs) - 1)], order=1)
        return np.where(inb, v, 0.02)
    return f, (zt, zb, zw, w)


def build_cuirass():
    from scipy.ndimage import gaussian_filter1d
    nip = G["NIPPLE"]
    nr = nip["r"]
    nipz, nx = float(nr[2]), abs(float(nr[0]))
    ub = float(G["UNDERBUST"])
    roll = PRM.get("roll", {"width": 0.005, "height": 0.0009})
    wroll = PRM.get("win_roll", {"width": 0.006, "height": 0.0011})
    lift, thick = PRM.get("lift", 0.0012), PRM.get("thick", 0.0028)
    cname = f"{PID}.plate"
    c = np.asarray(PRM.get("centre", [0.0, 0.0, 1.33]), float)
    if G.get("FILLED_BVH") is None:
        G["FILLED_BVH"] = BVHTree.FromPolygons([tuple(p) for p in G["P_FILLED"]], G["TRI"].tolist())
    unit, tris = ico(PRM.get("sub", 7))
    # (Blender's icosphere is the same both sides of y = 0, not of x = 0: x and y swapped, it is the same both sides of
    # her middle, so the cut sheet is too)
    unit = unit[:, [1, 0, 2]].copy()
    sym = cKDTree(unit).query(unit * mirror)[1]
    sym_err = float(np.abs(unit[sym] * mirror - unit).max())
    front = unit[:, 1] < -PRM.get("front", 0.12)
    pos, nor, H, ok, tris, Am, n = cast_sheet(c, unit, tris, front, PRM.get("membrane", 2), sym=sym)
    skin_pos = pos.copy()
    pos = pos + nor * lift
    # (params.lift_zone (c3): the upper outer quarters stood further off her, `mm` more, eased in over |x| from `x0` to `x1`
    # and over height from `z0` to `z1` above her nipple: her pectoral and armpit skin (clavicle-weighted) rise 8 mm into
    # the rigid plate in idle_warden_break's shrug and the town runs, 4.9 mm through it at the 1.2 mm lift)
    lz = PRM.get("lift_zone")
    if lz:
        nr0 = G["NIPPLE"]["r"]
        sx_ = np.clip((np.abs(pos[:, 0]) - lz["x0"]) / (lz["x1"] - lz["x0"]), 0, 1)
        sz_ = np.clip((pos[:, 2] - float(nr0[2]) - lz["z0"]) / (lz["z1"] - lz["z0"]), 0, 1)
        w_ = (sx_ * sx_ * (3 - 2 * sx_)) * (sz_ * sz_ * (3 - 2 * sz_))
        pos = pos + nor * (lz["mm"] * w_)[:, None]
    ax = np.abs(pos[:, 0])
    # The landmarks: her notch (where her sternum's front line meets her neck: the deepest point of her front at x = 0
    # between her collarbones' height and her neck), her shoulder balls.
    zz = np.arange(nipz + 0.06, nipz + 0.26, 0.002)
    fy = np.array([G["front_point"](0.0, z)[1] for z in zz])
    neck0 = G["NECK"]
    # (her notch: the deepest (furthest back) point of her front at x = 0 under her chin, 100-200 mm over her nipple)
    m_n = (zz > nipz + 0.10) & (zz < nipz + 0.20)
    notch_z = float(zz[m_n][np.argmax(fy[m_n])])
    ball = G["head"]("upperarm_l")
    z0 = nipz + PRM.get("neck", 0.12)
    nrise, nxr = PRM.get("neck_rise", 0.03), PRM.get("neck_x", 0.12)
    zneck = z0 + nrise * np.minimum(ax / nxr, 1.6) ** 2
    bxyz = np.c_[np.sign(pos[:, 0]) * abs(ball[0]), np.full(len(pos), ball[1]), np.full(len(pos), ball[2])]
    scye = np.linalg.norm(pos - bxyz, axis=1) - PRM.get("scye", 0.11)
    # The crease under each breast: in each 2 mm of |x|, the height of her most concave surface (least H) between
    # 25 and 130 mm under her nipple, on her front; eased across; held flat inside `crease_from` (between her breasts
    # there is none). The lower rim `lip` under it (it bridges below the crease, never sits in it); at her middle the
    # gore tip, `gore_drop` under the window, eased into the rim over `gore_w` of |x|.
    bins = np.arange(0.0, nx + PRM.get("side", 0.045) + 0.004, 0.002)
    zc = np.full(len(bins), np.nan)
    m_ = ok & (skin_pos[:, 2] < nipz - 0.025) & (skin_pos[:, 2] > nipz - 0.13) & (skin_pos[:, 1] < nr[1] + PRM.get("back", 0.06))
    for k, b0 in enumerate(bins):
        mm = m_ & (np.abs(skin_pos[:, 0]) >= b0) & (np.abs(skin_pos[:, 0]) < b0 + 0.002)
        if mm.sum() > 3:
            zc[k] = skin_pos[mm, 2][np.argmin(H[mm])]
    good = np.isfinite(zc)
    zc = np.interp(bins, bins[good], zc[good])
    cf = PRM.get("crease_from", 0.035)
    zc = np.where(bins < cf, np.interp(cf, bins, zc), zc)
    zc = gaussian_filter1d(zc, PRM.get("crease_ease", 4.0), mode="nearest")
    # (params.wrap (c3, judge K1): the plate carried round under each breast to her chest wall. Beyond the crease's
    # lowest point the lower rim no longer rises with it (it rose 70 mm up her side, leaving her breasts' lower outer
    # flanks bare): held at that point's height, plus `hold`.)
    wrap = PRM.get("wrap")
    if wrap:
        k_ = int(np.argmin(zc))
        zc[k_:] = np.minimum(zc[k_:], zc[k_] + wrap.get("hold", 0.0))
    lip = PRM.get("lip", 0.008)
    zt_w = ub + PRM.get("win_bot", 0.018)
    z_tip = zt_w - PRM.get("gore_drop", 0.022)
    gw = PRM.get("gore_w", 0.03)
    s_ = np.clip(bins / gw, 0, 1)
    s_ = s_ * s_ * (3 - 2 * s_)
    zlow = z_tip + (zc - lip - z_tip) * s_
    CUIR["crease_mm_under_nipple"] = {f"{int(round(b * 1000))}": round(float((nipz - z) * 1000), 1) for b, z in zip(bins[::5], zc[::5])}
    CUIR["lower_rim_z"] = {f"{int(round(b * 1000))}": round(float(z), 4) for b, z in zip(bins[::5], zlow[::5])}
    win, (wzt, wzb, wzw, ww) = lozenge_field(nipz, ub)
    # (the side seam: `back` behind her nipple below her nipple's height, letting go above it (`back_open` m a metre up),
    # where the armhole (`scye`, round her shoulder ball) takes over: held everywhere, it cut her upper chest away, which
    # recedes 60 mm behind her nipple by her collarbones)
    backlim = nr[1] + PRM.get("back", 0.06) + PRM.get("back_open", 2.0) * np.maximum(pos[:, 2] - nipz, 0.0)
    f_side = (nx + PRM.get("side", 0.045)) - ax
    f_back = backlim - pos[:, 1]
    if wrap:
        # (the wrap's side edge: round her vertical axis to `az` degrees off her front (her chest wall behind her breast's
        # outer flank, which ends near 62), from the lower rim up to `z_top` over her nipple, where the armhole takes it)
        phi_ = np.arctan2(ax, -pos[:, 1])
        waz_ = (np.radians(wrap.get("az", 66.0)) - phi_) * np.hypot(ax, pos[:, 1])
        f_side = np.maximum(np.minimum(f_side, f_back), np.minimum(waz_, (nipz + wrap.get("z_top", 0.10)) - pos[:, 2]))
        f_back = np.ones_like(f_side)
    f = np.minimum.reduce([zneck - pos[:, 2], scye, f_side, f_back,
                           pos[:, 2] - np.interp(ax, bins, zlow), win(pos[:, 0], pos[:, 2]),
                           np.where(ok, 1.0, -1.0)])
    # One blend for the whole plate: her soft weights at its sternum centre, her breast and arm bones out, its four
    # largest shares (gore_row's way).
    gc = np.array(G["front_point"](0.0, (wzt + wzb) / 2))
    row = G["soft_weights"](gc[None])[0].copy()
    for i_, bn_ in enumerate(BONES):
        if any(k in bn_.lower() for k in ("breast", "clavicle", "upperarm", "lowerarm", "hand", "shoulder")):
            row[i_] = 0.0
    row = row / row.sum()
    # (params.plate_blend (r2): the blend given, {bone: share}. Her sternum's own (spine_03 0.978) left her belly and
    # crease skin under the lower rim (spine_03 0.5 / spine_02 0.3) coming up through it in the combat swings)
    if PRM.get("plate_blend"):
        row = np.zeros_like(row)
        for n_, w_ in PRM["plate_blend"].items():
            row[BONES.index(n_)] = float(w_)
        row = row / row.sum()
    blend = top4(row)
    row4 = np.zeros(NB)
    for n_, w_ in blend:
        row4[BI[n_] if isinstance(BI, dict) else BONES.index(n_)] = w_
    attr = np.hstack([nor, np.repeat(row4[None], n, 0), np.zeros((n, 1))])
    if os.environ.get("CUIRASS_DUMP"):
        comps = np.array([zneck - pos[:, 2], scye, f_side, f_back,
                          pos[:, 2] - np.interp(ax, bins, zlow), win(pos[:, 0], pos[:, 2])])
        np.savez(os.path.join(SCRATCH, "cuirass_dump.npz"), pos=pos, ok=ok, H=H, comps=comps, bins=bins, zc=zc, zlow=zlow,
                 notch_z=notch_z, ball=ball, z0=z0, fy=fy, zz=zz, nip=nr, ub=ub, skin=skin_pos,
                 pf=np.asarray(G["P_FILLED"]), tri=np.asarray(G["TRI"]),
                 pfw=G["soft_weights"](np.asarray(G["P_FILLED"]))[:, [BONES.index(b_) for b_ in BONES if "breast" in b_.lower()]].sum(1))
        print("CUIRASS DUMP", json.dumps({k: v for k, v in CUIR.items()}), "notch", notch_z, "ball", ball.tolist())
        if os.environ.get("CUIRASS_DUMP") == "stop":
            raise SystemExit(0)
    pos, at, tris, rim, loops = cut_sheet(f, pos, attr, tris, 0.2)
    print("CUIRASS loops", len(loops), [len(lp) for lp in loops])
    # (the window's loop: the one round the window's middle)
    wc = np.array([0.0, 0.0, wzw])
    cent = [np.array(pos[lp])[:, [0, 2]].mean(0) for lp in loops]
    kw = int(np.argmin([np.hypot(ce[0], ce[1] - wzw) for ce in cent]))
    wloop = np.asarray(loops[kw])
    oloop = np.unique(np.concatenate([np.asarray(lp) for k, lp in enumerate(loops) if k != kw]))
    # The ridge down her middle, on the bar and the gore: `ridge` h high, w wide (a tent: two lit planes), out along the
    # sheet's normal, faded to nothing within `fade` of the window's rim.
    rg = PRM.get("ridge", {"h": 0.0018, "w": 0.014, "fade": 0.006})
    dwin = cKDTree(pos[wloop]).query(pos)[0]
    fade = np.clip(dwin / rg["fade"], 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    tent = np.clip(1 - np.abs(pos[:, 0]) / (rg["w"] / 2), 0, 1)
    nn_ = at[:, :3] / (np.linalg.norm(at[:, :3], axis=1)[:, None] + 1e-12)
    pos = pos + nn_ * (rg["h"] * tent * fade)[:, None]
    # (params.flare (c2): the plate's edge turned out off her, `mm` at the rim easing to none `over` m in: "low" its
    # lower rim (her belly and crease skin there, spine_03 0.5 / spine_02 0.3, came 5-7 mm through the 2 mm the rim stood
    # off her in the town runs), "scye" its armholes (her upper chest under them rises with her clavicles in the idle's
    # shrug). A cuirass's turned edge.)
    for fl in PRM.get("flare", []):
        if fl["edge"] == "low":
            hd_ = pos[:, 2] - np.interp(np.abs(pos[:, 0]), bins, zlow)
            hd_ = np.where(pos[:, 2] < nipz, hd_, np.inf)
        elif fl["edge"] == "neck":
            # ("neck": its neckline's outer reaches, from `x_from` (none) to `x_full` of |x| (all): the top outer corners,
            # where her upper chest rises with her clavicles in the idle's shrug)
            ax_ = np.abs(pos[:, 0])
            hd_ = (z0 + nrise * np.minimum(ax_ / nxr, 1.6) ** 2) - pos[:, 2]
            xs_ = np.clip((ax_ - fl.get("x_from", 0.06)) / max(fl.get("x_full", 0.09) - fl.get("x_from", 0.06), 1e-6), 0, 1)
            hd_ = np.where(xs_ > 0, hd_ / np.maximum(xs_ * xs_ * (3 - 2 * xs_), 1e-6), np.inf)
        else:
            bx_ = np.c_[np.sign(pos[:, 0]) * abs(ball[0]), np.full(len(pos), ball[1]), np.full(len(pos), ball[2])]
            hd_ = np.linalg.norm(pos - bx_, axis=1) - PRM.get("scye", 0.11)
        t_ = np.clip(1 - np.maximum(hd_, 0) / fl["over"], 0, 1)
        pos = pos + nn_ * (fl["mm"] * t_ * t_ * (3 - 2 * t_))[:, None]
        CUIR.setdefault("flare", {})[fl["edge"]] = int((t_ > 0).sum())
    # The top outer corners (the straps' roots): the highest rim points beyond 0.6 x her nipple's |x|.
    orim = oloop
    oR = orim[pos[orim, 0] < -0.6 * nx]
    G["CUP_PEAK"]["r"] = pos[oR[np.argmax(pos[oR, 2])]]
    G["CUP_PEAK"]["l"] = G["CUP_PEAK"]["r"] * mirror
    # (the band's seam: build_plate_top takes its rim's points furthest back. The cuirass's furthest back are its top
    # corners (her upper chest recedes): the band started there, at her neck, and ran 1.3 m. So only its side seams:
    # rim points beyond her nipple's |x|, below her nipple)
    # (her right side only, as fitted_cups' rim_r is: band_and_straps mirrors its anchor onto her left)
    sr_ = oloop[(pos[oloop, 0] < -nx) & (pos[oloop, 2] < nipz)]
    FIT["rim_r"] = pos[sr_ if len(sr_) > 8 else oloop]
    FIT["x_min"] = float(ww)
    FIT["window_rim"] = pos[wloop]
    G["ONE_ISLAND"].add(cname)
    G["MIRROR_BIND"].add(cname)
    G["BIND_TOP"][cname] = (wc * 0 + np.array([0.0, float(pos[wloop, 1].mean()), wzw]), (wroll["width"], wroll["height"], wroll.get("overhang", 0.0018)))
    pos, beads = G["bind_edges"](cname, pos, at, tris, MKEY, roll["width"], roll["height"], roll.get("overhang", 0.0018), thick)
    # (params.cap_density (c3): the plate's triangle floor a square metre (heroine_outfits.finish's 60000 unset): the
    # wrap's larger plate went 1.1k over the 20k budget)
    if PRM.get("cap_density"):
        NS["CAP_DENSITY"] = PRM["cap_density"]
    try:
        shell = finish_cap(cname, pos, at[:, 3:3 + NB], tris, MKEY, thick, 0.0, PRM.get("plate_budget", 9000))
    finally:
        NS.pop("CAP_DENSITY", None)
    shell["hides"] = True
    for b_ in beads:
        b_["hides"] = False
    for o_ in [shell] + beads:
        set_one_blend(o_, blend)
    sheet_pos, sheet_wt, sheet_tris, _ = CAP["sheet"][cname]
    cupl = [shell] + beads
    _bs = band_and_straps(cupl, sheet_pos, sheet_wt, G["CUP_PEAK"])
    backstrap, allstraps, fix, buckles = _bs["backstrap"], _bs["allstraps"], _bs["fix"], _bs["buckles"]
    bsock, strap_lines, straps = _bs["bsock"], _bs["strap_lines"], _bs["straps"]
    CUIR.update(blend=blend, sym_err=sym_err, notch_z=round(notch_z, 4), neck_centre_z=round(float(z0), 4),
                neck_under_notch_mm=round((notch_z - z0) * 1000, 1), neck0=np.round(neck0, 4).tolist(), ball=np.round(ball, 4).tolist(),
                gore_tip_z=round(float(z_tip), 4), corner_r=np.round(G["CUP_PEAK"]["r"], 4).tolist(),
                front_profile={f"{z:.3f}": round(float(y), 4) for z, y in zip(zz[::5], fy[::5])})
    print("CUIRASS", json.dumps(CUIR))
    parts = [shell] + beads + allstraps + backstrap + fix + buckles
    # ---- sockets
    cbvh = BVHTree.FromPolygons([tuple(shell.matrix_world @ v.co) for v in shell.data.vertices], [p.vertices[:] for p in shell.data.polygons])
    socks = {}

    def sock(name, p, n, up, wts):
        n = np.asarray(n, float) / np.linalg.norm(n)
        up = np.asarray(up, float) - n * (np.asarray(up, float) @ n)
        up /= np.linalg.norm(up)
        socks[name] = {"point": gl(p).round(5).tolist(), "normal": gl(n).round(5).tolist(), "up": gl(up).round(5).tolist(),
                       "weights": top4(np.asarray(wts, float)) if isinstance(wts, np.ndarray) else wts}

    def on_plate(q):
        """The plate's outer face over her skin point q (cast in from 30 mm out along her normal there)."""
        nn = np.array(G["SKIN_BVH"].find_nearest(Vector(q))[1][:])
        if nn[1] > 0:
            nn = -nn
        h = cbvh.ray_cast(Vector(q + nn * 0.03), Vector(-nn), 0.05)
        return (np.array(h[0][:]), nn) if h[0] is not None else (q + nn * (lift + thick), nn)

    p_, n_ = on_plate(nr)
    for sd in "lr":
        pp, pn = (p_, n_) if sd == "r" else (p_ * mirror, n_ * mirror)
        sock(f"cup_{sd}", pp, pn, [0, 0, 1.0], blend)
        pk = G["CUP_PEAK"][sd]
        sock(f"strap_{sd}", pk, G["SKIN_BVH"].find_nearest(Vector(pk))[1][:], np.asarray(strap_lines[sd][1]) - pk, blend)
        bs = bsock[sd]
        sock(f"buckle_{sd}", bs["point"], bs["normal"], bs["up"], bs["weights"])
        sh = np.asarray(strap_lines[sd][1])
        sock(f"shoulder_{sd}", sh, G["SKIN_BVH"].find_nearest(Vector(sh))[1][:], [0, 1.0, 0], top4(G["soft_weights"](sh[None])[0]))
    for nm, z in (("bar", (wzt + z0) / 2), ("gore", (wzb + z_tip) / 2)):
        q = np.array(G["front_point"](0.0, z))
        pp, pn = on_plate(q)
        sock(nm, pp, pn, [0, 0, 1.0], blend)
    bs = bsock["back"]
    sock("back", bs["point"], bs["normal"], [0, 0, 1.0], bs["weights"])
    # ---- rims: the window's (closed), and the outer loop in four runs: neck (above the corners' height, inside their
    # |x|), the side seams (beyond the corners' |x|), the lower rim (the rest)
    rims = {}
    cz, cx = float(G["CUP_PEAK"]["r"][2]), abs(float(G["CUP_PEAK"]["r"][0]))
    for tn, tb in CAP["tubes"].items():
        if not tn.startswith(cname + "_bind"):
            continue
        cur = tb["curve"]
        isw = np.ptp(cur[:, 0]) < 2.5 * ww
        rec = lambda m, closed: {"closed": closed, "points": gl(cur[m]).round(5).tolist(), "normals": gl(tb["nrm"][m]).round(4).tolist(),
                                 "outward": gl(tb["outward"][m]).round(4).tolist(), "weights": [blend] * int(m.sum()),
                                 "roll": {"width": tb["width"], "height": tb["height"], "overhang": tb["overhang"]}, "tube": tn}
        if isw:
            rims["window_rim"] = rec(np.ones(len(cur), bool), True)
            continue
        axc = np.abs(cur[:, 0])
        neck = (axc < cx - 0.002) & (cur[:, 2] > nipz + 0.03)
        side = axc >= cx - 0.002
        low = ~neck & ~side
        for nm, m in (("neck_rim", neck), ("lower_rim", low), ("side_rim_l", side & (cur[:, 0] > 0)), ("side_rim_r", side & (cur[:, 0] < 0))):
            if m.any():
                # (each run in order along the loop: rolled so it starts after a gap)
                idx = np.nonzero(m)[0]
                gaps = np.nonzero(np.diff(idx) > 1)[0]
                if len(gaps):
                    idx = np.roll(idx, -(gaps[0] + 1))
                mm = np.zeros(len(cur), bool)
                mm[idx] = True
                r_ = rec(mm, False)
                r_["points"] = gl(cur[idx]).round(5).tolist()
                r_["normals"] = gl(tb["nrm"][idx]).round(4).tolist()
                r_["outward"] = gl(tb["outward"][idx]).round(4).tolist()
                rims[nm] = r_
    CUIR["window_sheet"] = {"zs": [round(float(pos[wloop, 2].min()), 4), round(float(pos[wloop, 2].max()), 4)],
                            "half_w": round(float(np.abs(pos[wloop, 0]).max()), 4)}
    return dict(parts=parts, shell=[shell], envelope=[shell], gore=[], sheet=(sheet_pos, sheet_wt, sheet_tris), thick=thick,
                lift=lift, sockets=socks, rims=rims, roll=roll, avoid=[np.asarray(cv[0]) for _, cv in straps],
                roll_prefix=[cname + "_bind"], measure=cuirass_measure)


def cuirass_measure():
    """The cuirass's own numbers (after her tuck is final): the plate's standoff on her skin (all, its rim), the
    window (its rolled edge's line: size, and her skin seen through it at the town camera), the neckline under her
    notch, her tuck along the window rim (the step between neighbours along it, and left against right), and the
    design numbers from the build."""
    out = {"cuirass": {k: v for k, v in CUIR.items() if k != "front_profile"}}
    bb = BVHTree.FromPolygons([tuple(p) for p in bv0], [p_.vertices[:] for p_ in me.polygons])
    out["standoff_mm"] = {"plate": standoff(f"{PID}.plate", bb)}
    ev_, _, _ = mesh_world(B["envelope"])
    e_ = np.array([np.linalg.norm(np.array(filled_bvh.find_nearest(Vector(q))[0][:]) - q) for q in ev_])
    top_ = np.argsort(-e_)[:max(1, len(e_) // 100)]
    q_ = ev_[top_]
    out["envelope_top1pct"] = {"n": int(len(top_)), "min_mm": round(float(e_[top_].min() * 1000), 2),
                               "on_ridge": int((np.abs(q_[:, 0]) < 0.007).sum()),
                               "below_window": int((q_[:, 2] < CUIR["window_design"]["bottom_z"]).sum()),
                               "above_window": int((q_[:, 2] > CUIR["window_design"]["top_z"]).sum()),
                               "at": nip_rel(q_[::max(1, len(q_) // 10)])}
    wt_ = [tb for tn, tb in CAP["tubes"].items() if tn.startswith(f"{PID}.plate_bind") and
           np.ptp(tb["curve"][:, 0]) < 2.5 * FIT["x_min"]]
    if wt_:
        tb = wt_[0]
        cur = tb["curve"]
        # (the skin that shows: inside the rolled edge's inner flank (the line less its overhang, the roll's half
        # width outward is over the plate))
        inner = cur - tb["outward"] * 0.0
        w_mm = float(np.ptp(cur[:, 0]) * 1000)
        h_mm = float(np.ptp(cur[:, 2]) * 1000)
        xy = cur[:, [0, 2]]
        area = 0.5 * abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))
        ov = tb["overhang"]
        per = float(np.linalg.norm(np.diff(np.vstack([xy, xy[:1]]), axis=0), axis=1).sum())
        area_open = max(area - per * ov, 0.0)
        height_m = float(bv0[:, 2].max() - bv0[:, 2].min())
        px = height_m / 100.0          # (her ~100 px tall at the town play camera)
        out["window"] = {"line_w_mm": round(w_mm, 1), "line_h_mm": round(h_mm, 1), "line_area_mm2": round(area * 1e6, 0),
                         "open_area_mm2": round(area_open * 1e6, 0), "her_height_m": round(height_m, 3),
                         "skin_px_at_100px": round(area_open / (px * px), 1),
                         "w_px": round((w_mm / 1000 - 2 * ov) / px, 2), "h_px": round((h_mm / 1000 - 2 * ov) / px, 2)}
        # Her tuck along the window rim: her skin points within 1.5 mm of its line, in order along it.
        dense = np.vstack([cur[k] + (cur[(k + 1) % len(cur)] - cur[k]) * t for k in range(len(cur)) for t in np.linspace(0, 1, 4, endpoint=False)])
        d_, j_ = cKDTree(dense).query(bv0)
        on_ = np.zeros(len(bv0), bool)
        on_[np.array([i for p_ in me.polygons for i in p_.vertices])] = True
        smp = np.nonzero((d_ < PRM.get("rim_probe", 0.0015)) & on_)[0]
        if len(smp) > 3:
            tv = np.where(tuck > 0.973, 1.0, tuck)
            order = smp[np.argsort(j_[smp])]
            seq = tv[order]
            steps = np.abs(np.diff(np.r_[seq, seq[:1]]))
            mt = cKDTree(bv0[on_]).query(bv0[order] * mirror)
            mir = np.abs(tv[np.nonzero(on_)[0][mt[1]]] - tv[order])
            out["window_rim_tuck"] = {"samples": int(len(order)), "mark_min": round(float(seq.min()), 3), "mark_max": round(float(seq.max()), 3),
                                      "step_max": round(float(steps.max()), 3), "step_p95": round(float(np.percentile(steps, 95)), 3),
                                      "mirror_diff_max": round(float(mir[mt[0] < 0.002].max()) if (mt[0] < 0.002).any() else -1, 3),
                                      "mirror_match_mm_max": round(float(mt[0].max() * 1000), 2)}
    return out


# ------------------------------------------- the shell: lamed pauldrons --
# (armor 10, b_design_spec.md section 1: a cop over the deltoid cap and two lames a side, built on her left in her arm's
# frame (pl_limb_frame: s down her arm from the ball of her shoulder, bearing 0 up her outer arm, + to her front) and
# mirrored to her right with SWAP. Each plate is rigid, on one blend (pl_row): the cop her skin's blend under its
# neck-side third, each lame a step more of her upper arm. A leather throat tab from the cop's neck edge onto her
# trapezius, riveted to the cop.)
PAUL = {}


def _paul_mirror_name(n):
    a, b = n.split(".", 1)
    return a + "." + b.replace("_l", "_r", 1)


def _paul_mirror_obj(o):
    """Her right's copy of a part on her left: x mirrored in the world, faces turned back out, weights' sides swapped."""
    nm = _paul_mirror_name(o.name)
    me2 = o.data.copy()
    o2 = o.copy()
    o2.data = me2
    for c in o.users_collection:
        c.objects.link(o2)
    o2.name = me2.name = nm
    mw = np.array(o.matrix_world)
    inv = np.linalg.inv(mw)
    fix = lambda co: ((np.c_[co, np.ones(len(co))] @ mw.T)[:, :3] * mirror) @ inv[:3, :3].T + inv[:3, 3]
    co = np.empty(len(me2.vertices) * 3)
    me2.vertices.foreach_get("co", co)
    me2.vertices.foreach_set("co", fix(co.reshape(-1, 3)).ravel())
    for kb in (me2.shape_keys.key_blocks if me2.shape_keys else []):
        kc = np.empty(len(kb.data) * 3)
        kb.data.foreach_get("co", kc)
        kb.data.foreach_set("co", fix(kc.reshape(-1, 3)).ravel())
    me2.flip_normals()
    me2.update()
    gs = list(o2.vertex_groups)
    for g in gs:
        if g.name[-2:] in ("_l", "_r"):
            g.name = "~" + g.name
    for g in gs:
        if g.name.startswith("~"):
            n_ = g.name[1:]
            g.name = n_[:-2] + {"_l": "_r", "_r": "_l"}[n_[-2:]]
    if o.get("blend_group"):
        o2["blend_group"] = _paul_mirror_name(o["blend_group"])
    return o2


def build_pauldrons_lamed():
    cp = PRM.get("cop", {})
    TH0, TH1 = np.radians(cp.get("back", -105.0)), np.radians(cp.get("front", 95.0))
    S_MED, S_LOW, RISE, RC = cp.get("medial", -0.034), cp.get("low", 0.030), cp.get("rise", 0.014), cp.get("corner", 0.012)
    CLEAR, MOST, THK = cp.get("clear", 0.004), cp.get("most", 0.006), cp.get("thick", 0.002)
    GRID = cp.get("grid", 0.002)
    comb = PRM.get("comb", {"h": 0.0025, "w": 0.012})
    roll = PRM.get("roll", {"width": 0.0045, "height": 0.001, "overhang": 0.0015})
    lm = PRM.get("lames", {})
    tab = PRM.get("tab", {"width": 0.022, "run": 0.028, "under": 0.010, "lift": 0.0015, "thick": 0.0025})
    wp = PRM.get("weights", {})
    fsk = G["final_skin_bvh"]()

    def one_side(sd):
        F_ = G["pl_limb_frame"](sd)
        ctr, ax_, e0, e1 = F_
        PAUL.update({"F_" + sd: F_, "S_MED": S_MED, "S_LOW": S_LOW})
        s_low = lambda th: S_LOW - RISE * (th / (np.pi / 2)) ** 2
        # (b2r3: its top edge curved `dip` down her arm at the front and back, as the deltoid falls away from her side)
        DIP = cp.get("dip", 0.0)
        s_med = lambda th: S_MED + DIP * (1 - np.cos(th))

        def skin_rho(s, th):
            o = ctr + ax_ * s
            d = np.cos(th) * e0 + np.sin(th) * e1
            h = fsk.ray_cast(Vector(tuple(o)), Vector(tuple(d)), 0.25)
            return h[3] if h[0] is not None else np.nan
        R = float(np.nanmedian([skin_rho(s, t) for s in (-0.01, 0.0, 0.01) for t in np.radians([-60, -30, 0, 30, 60])]))
        # ---- the cop: a grid over its box in (u = bearing x R, s), each point cast onto her skin from her arm's axis
        gu = np.arange(np.floor((TH0 * R - 0.008) / GRID), np.ceil((TH1 * R + 0.008) / GRID) + 1) * GRID     # (a grid line on bearing 0: the comb's crest)
        gs = np.arange(S_MED - 0.008, S_LOW + 0.008, GRID)
        UU, SS = np.meshgrid(gu, gs, indexing="ij")
        uv2 = np.c_[UU.ravel(), SS.ravel()]
        ns = len(gs)
        ii = (np.arange(len(gu) - 1)[:, None] * ns + np.arange(ns - 1)[None, :]).ravel()
        tri = np.vstack([np.c_[ii, ii + ns, ii + 1], np.c_[ii + ns, ii + ns + 1, ii + 1]])
        th_g = uv2[:, 0] / R
        rho = np.array([skin_rho(s, t) for t, s in zip(th_g, uv2[:, 1])])
        bad = ~np.isfinite(rho)
        if bad.any():
            rho[bad] = rho[~bad][cKDTree(uv2[~bad]).query(uv2[bad])[1]]
        field = G["ANDR"](G["ANDR"](uv2[:, 1] - s_med(th_g), s_low(th_g) - uv2[:, 1], RC), G["ANDR"](uv2[:, 0] - TH0 * R, TH1 * R - uv2[:, 0], RC), RC)
        inside = field > -0.002
        if cp.get("surface", "hull") == "shell":
            # the fair dome: shell() (a quadric of her distance from the ball of her shoulder over the directions it covers),
            # lifted until it stands `clear` off her final skin (as the straps seat on it), at most `most`
            bvh_was = G["BVH"]
            G["BVH"] = fsk
            try:
                X = G["shell"](f"{PID}.cop_{sd}", G["pl_point"](uv2[:, 1], th_g, rho, F_), ctr, CLEAR, most=MOST)
            finally:
                G["BVH"] = bvh_was
            sX, tX, rX = G["pl_frame"](X, F_)
            rho_f = rX
        else:
            # (round 1: the quadric stood 10.9 mm off her at its worst place and was lifted its full 6 mm; the cop then stood
            # 7-12 mm off her (p50). The fair hull instead: her distance off her arm's axis eased (`sigma`, a Gaussian over
            # the grid) and never below her (the eased surface pushed back up to her and eased again, until it settles):
            # a smooth cap over the deltoid that touches its crowns and bridges its hollows, no muscle cast under 2 cm)
            from scipy.ndimage import gaussian_filter, maximum_filter
            sg_ = cp.get("sigma", 0.008) / GRID
            rho_f = gaussian_filter(rho.reshape(len(gu), ns), sg_, mode="nearest").ravel()
        from scipy.ndimage import gaussian_filter, maximum_filter
        # (round 2: a hull lifted as a whole stood 9.9 mm off her at p50: lifted until its nearest point cleared, it stood
        # off by every hollow it bridged. Now a smooth lift of its own at each place: where a point stands under `clear`
        # off her final skin, the shortfall spread (a 3x3 max, then eased `lift_sigma`) and added, rounds until all clear,
        # at most `most` anywhere)
        from scipy.ndimage import gaussian_filter, maximum_filter
        ls_ = cp.get("lift_sigma", 0.006) / GRID
        lift_ = np.zeros(len(rho_f))
        for _ in range(cp.get("lift_rounds", 8)):
            q_ = G["pl_point"](uv2[:, 1], th_g, rho_f + lift_, F_)
            dd = np.empty(len(q_))
            for i_, qq in enumerate(q_):
                h_ = fsk.find_nearest(Vector(tuple(qq)))
                dd[i_] = (qq - np.array(h_[0][:])) @ np.array(h_[1][:])
            short = np.where(inside | (field > -0.006), np.maximum(CLEAR - dd, 0.0), 0.0)
            if short.max() < 0.0002:
                break
            add = gaussian_filter(maximum_filter(short.reshape(len(gu), ns), size=3), ls_, mode="nearest").ravel()
            add *= short.max() / max(add.max(), 1e-9)
            lift_ = np.minimum(lift_ + np.maximum(add, short) * 1.1, MOST)
        up = float(lift_[inside].max())
        dd = dd[inside]
        rho_f = rho_f + lift_
        PAUL.setdefault("cop_lift_mm", {})[sd] = round(up * 1000, 2)
        PAUL.setdefault("cop_clear_mm_before_push", {})[sd] = {"min": round(float(dd.min() * 1000), 2), "p50": round(float(np.median(dd) * 1000), 2),
                                            "p99": round(float(np.percentile(dd, 99) * 1000), 2)}
        stamp(sd + " cop: lifted %.1f mm at most; off her final skin min %.1f p50 %.1f p99 %.1f mm" % (up * 1000, dd.min() * 1000, np.median(dd) * 1000, np.percentile(dd, 99) * 1000))
        up = 0.0
        # the comb: a low ridge along bearing 0, a triangle `h` high and `w` wide, out from her arm's axis; it runs out into
        # both rims (eased to nothing over `fade` inside them: at full height it kinked the rim 22.6 deg in 3 mm)
        fade = np.clip(field / comb.get("fade", 0.008), 0, 1)
        # (b2r3: higher and narrower, one highlight line down the cop's outer face; a crest grid line either side of it at
        # `w`/4 so the triangle is drawn, not one raised grid line)
        rho_c = rho_f + up + comb["h"] * np.clip(1 - np.abs(uv2[:, 0]) / (comb["w"] / 2), 0, 1) * fade * fade * (3 - 2 * fade)
        X = G["pl_point"](uv2[:, 1], th_g, rho_c, F_)

        def off_skin(Q):
            # (the true distance to her nearest point and the way to it: in the hollow at her neck rim the nearest point
            # is often on a crease of her mesh, where the distance along its face's normal reads a third of the true one)
            hn = [fsk.find_nearest(Vector(tuple(qq))) for qq in Q]
            Hp, Hn = np.array([h_[0][:] for h_ in hn]), np.array([h_[1][:] for h_ in hn])
            D = Q - Hp
            dl = np.linalg.norm(D, axis=1)
            sg = np.where((D * Hn).sum(1) < 0, -1.0, 1.0)
            return dl * sg, np.where(dl[:, None] > 1e-6, D * sg[:, None] / np.maximum(dl, 1e-9)[:, None], Hn)
        dn_, _ = off_skin(X)
        nb_ = inside & (uv2[:, 1] < s_med(th_g) + 0.012)
        ib_ = np.nonzero(inside)[0][np.argmax(dn_[inside])]
        stamp(sd + " cop surface off her final skin: max %.1f mm at s %.0f mm, bearing %.0f deg; its neck rim max %.1f p50 %.1f"
              % (dn_[ib_] * 1000, uv2[ib_, 1] * 1000, np.degrees(th_g[ib_]), dn_[nb_].max() * 1000, np.median(dn_[nb_]) * 1000))
        # (b2r3: the neck rim down onto her trapezius. The hull bridged her hollows there (and the cast from her arm's axis
        # runs slantwise to her skin above the ball of her shoulder, so the lift's casts could not bring it down): its neck
        # rim stood 8.6-9.4 mm off her final skin. Within `neck_band` of the medial edge it now stands at most `neck_off`
        # off her, moved along her own normal, the excess eased `neck_sigma` over the grid and fading out down her arm;
        # never under `clear`)
        NBAND, NOFF = cp.get("neck_band", 0.0), cp.get("neck_off", 0.0035)
        if NBAND > 0:
            wn_ = np.clip(1 - (uv2[:, 1] - s_med(th_g)) / NBAND, 0, 1)
            # (and fading out round the cop's front and back corners: sunk there and not down the edge below, the back
            # edge twisted, 21 deg in 3 mm)
            wn_ *= np.clip((np.radians(cp.get("neck_fade_to", 110.0)) - np.abs(th_g)) / np.radians(cp.get("neck_fade_over", 25.0)), 0, 1)
            wn_ = wn_ * wn_ * (3 - 2 * wn_)
            for _ in range(cp.get("neck_rounds", 6)):
                dn_, hn_ = off_skin(X)
                ex_ = np.maximum(dn_ - NOFF, 0.0) * wn_
                if ex_[inside | (field > -0.004)].max() < 0.0002:
                    break
                ex_ = gaussian_filter(ex_.reshape(len(gu), ns), cp.get("neck_sigma", 0.003) / GRID, mode="nearest").ravel()
                ex_ = np.clip(np.maximum(ex_, np.maximum(dn_ - NOFF, 0.0) * wn_ * 0.5), 0, np.maximum(dn_ - CLEAR, 0.0))
                X = X - hn_ * ex_[:, None]
            dn_, _ = off_skin(X)
            stamp(sd + " cop neck rim after the sink: max %.1f p50 %.1f mm (all inside: max %.1f, min %.1f)"
                  % (dn_[nb_].max() * 1000, np.median(dn_[nb_]) * 1000, dn_[inside].max() * 1000, dn_[inside].min() * 1000))
        # her skin's blend under the cop's neck-side third: the cop's row
        sP, tP, rP = G["pl_frame"](P, F_)
        inP = (tP > TH0) & (tP < TH1) & (sP > S_MED) & (sP < S_MED + (S_LOW - S_MED) / 3) & (rP < R + 0.03)
        base = W[inP].mean(0)
        armb = [BI[n] for n in BONES if n.endswith(f"_{sd}") and n.split("_")[0] in G["PL_LIMB"]]
        w_cop = float(wp.get("cop", base[armb].sum() / base.sum()))
        ladder = [w_cop]
        for st_ in wp.get("steps", [0.07, 0.07]):
            ladder.append(ladder[-1] + min(st_, 0.1))
        rows = [G["pl_row"](base, w, sd=sd) for w in ladder]
        PAUL.setdefault("sides", {})[sd] = dict(ladder=[round(w, 3) for w in ladder], R=R, base_arm=round(float(base[armb].sum() / base.sum()), 3), inP=int(inP.sum()))
        at = np.c_[np.zeros((len(X), 3)), np.repeat(rows[0][None], len(X), 0), field]
        pos, at, tris = G["clip"](field, X, at, tri)
        pos, at, tris = G["weld"](pos, at, tris)
        tris = G["islands"](pos, tris)
        if NBAND > 0:
            # (and once more on the cut sheet itself, its own points as they will be bound: build 2's grid read its neck
            # rim at most 4.7 mm off her after the sink while the bound sheet stood 7.7-9.3 there)
            sq_, tq_, _ = G["pl_frame"](pos, F_)
            wq_ = np.clip(1 - (sq_ - s_med(tq_)) / NBAND, 0, 1) * np.clip(
                (np.radians(cp.get("neck_fade_to", 110.0)) - np.abs(tq_)) / np.radians(cp.get("neck_fade_over", 25.0)), 0, 1)
            wq_ = wq_ * wq_ * (3 - 2 * wq_)
            Aq_ = G["adjacency"](len(pos), tris)
            nbq_ = sq_ < S_MED + 0.012
            dq_, _ = off_skin(pos)
            pre_ = dq_.copy()
            for _ in range(cp.get("neck_rounds", 6)):
                dq_, uq_ = off_skin(pos)
                exq_ = np.maximum(dq_ - NOFF, 0.0) * wq_
                if exq_.max() < 0.0002:
                    break
                es_ = exq_.copy()
                for _ in range(4):
                    es_ = 0.5 * es_ + 0.5 * (Aq_ @ es_)
                exq_ = np.clip(np.maximum(es_, 0.5 * exq_), 0, np.maximum(dq_ - CLEAR, 0.0))
                pos = pos - uq_ * exq_[:, None]
            dq_, _ = off_skin(pos)
            stamp(sd + " cop sheet (cut, unbound) neck rim off her final skin: before its sink max %.1f p50 %.1f, after max %.1f p50 %.1f mm; all max %.1f"
                  % (pre_[nbq_].max() * 1000, np.median(pre_[nbq_]) * 1000, dq_[nbq_].max() * 1000, np.median(dq_[nbq_]) * 1000, dq_.max() * 1000))
        nr = G["vertex_normals"](pos, tris)
        if (nr * (pos - ctr)).sum(1).mean() < 0:
            tris = tris[:, ::-1]
            nr = -nr
        at[:, :3] = nr
        cname = f"{PID}.cop_{sd}"
        pos, beads = G["bind_edges"](cname, pos, at, tris, MKEY, roll["width"], roll["height"], roll.get("overhang", 0.0015), THK,
                                     sigma=0.003, rmin=cp.get("rmin", 0.010))
        if NBAND > 0:
            dq_, _ = off_skin(pos)
            sq_ = G["pl_frame"](pos, F_)[0]
            nbq_ = sq_ < S_MED + 0.012
            wq_ = np.argmax(np.where(nbq_, dq_, -1))
            stamp(sd + " cop sheet bound: neck rim max %.1f p50 %.1f mm (worst at s %.0f mm, bearing %.0f deg)"
                  % (dq_[nbq_].max() * 1000, np.median(dq_[nbq_]) * 1000, sq_[wq_] * 1000, np.degrees(G["pl_frame"](pos[wq_:wq_ + 1], F_)[1][0])))
            if os.environ.get("PAUL_DUMP"):
                np.savez(os.path.join(os.environ["PAUL_DUMP"], f"cop_{sd}.npz"), X=X, field=field, uv2=uv2, pos=pos, tris=tris)
        G["RIGID_UV"][cname] = (ctr, ax_, False)
        cop = [G["finish"](cname, pos, at[:, 3:3 + NB], tris, MKEY, THK, cp.get("bevel", 0.0012), cp.get("budget", 1200))] + beads
        cop = [o for o in cop if o is not None]
        cop[0]["hides"] = True
        G["pl_one_blend"](cop, rows[0])
        cop_sheet = (pos.copy(), tris.copy())
        for o in cop:
            o["blend_group"] = cname
        left = {"cop": cop}
        # ---- the lames: pl_lame x2, each under the plate above
        lthk = lm.get("thick", 0.0018)
        rfn = lambda name, pts, nrs, rws: low_rivets(name + "_rivets", np.asarray(pts) + np.asarray(nrs) * (lthk + 0.0002),
                                                     nrs, rws, lm.get("rivet_r", 0.0026), MKEY)
        above = cop_sheet
        O_, V_ = lm.get("O", [0.014, 0.012]), lm.get("V", [0.026, 0.024])
        for k in (1, 2):
            nm = f"{PID}.lame{k}_{sd}"
            made_k, above = G["pl_lame"](nm, above, F_, rows[k], O_[k - 1], V_[k - 1], E=lm.get("E", 0.014), tuck=lm.get("tuck", 0.0035),
                                         taper=lm.get("taper", -0.04), flare=lm.get("flare", 0.003), joggle=lm.get("joggle", 0.003),
                                         rc=lm.get("rc", 0.010), thick=lthk, rv_end=lm.get("rv_end", 0.022),
                                         rv_up=lm.get("rv_up", 0.008), mkey=MKEY, rivet_key=MKEY,
                                         roll=(roll["width"], roll["height"], roll.get("overhang", 0.0015)), bevel=lm.get("bevel", 0.001),
                                         crease=(lm.get("crease", 0.0015), lm.get("crease_w", 0.010)), rv_step=lm.get("rv_step", 0.03),
                                         budget=lm.get("budget", 500), rivet_fn=rfn, h=lm.get("grid", 0.003))
            made_k = [o for o in made_k if o is not None]
            made_k[0]["hides"] = True
            for o in made_k:
                o["blend_group"] = nm
            left[f"lame{k}"] = made_k
        # ---- the throat tab: from `under` inside the cop's neck edge, over its rolled edge, `run` onto her trapezius
        tw, trun, tin = tab["width"], tab["run"], tab["under"]
        # (b2r3: five columns, its end rounded over half its width, as a strap's end: the outer columns drawn in there)
        ss = np.linspace(S_MED + tin, S_MED - trun, max(8, int(round((tin + trun) / tab.get("step", 0.003)))))
        xe_ = np.clip(((S_MED - trun + tw / 2) - ss) / (tw / 2), 0, 1)
        narrow = np.maximum(np.sqrt(np.clip(1 - xe_ ** 2, 0, 1)), tab.get("end_min", 0.3)) if tab.get("round_end") else np.ones(len(ss))
        cols, nrms = [], []
        for off in np.linspace(-tw / 2, tw / 2, tab.get("cols", 3)):
            hits = [skin_hit(ctr + ax_ * s, np.cos(off * k / R) * e0 + np.sin(off * k / R) * e1, fsk) for s, k in zip(ss, narrow)]
            cols.append(np.array([h_[0] for h_ in hits]))
            nrms.append(np.array([h_[1] for h_ in hits]))
        nrms = np.array(nrms)
        for _ in range(3):
            nrms[:, 1:-1] = (nrms[:, :-2] + 2 * nrms[:, 1:-1] + nrms[:, 2:]) / 4
        nrms /= np.linalg.norm(nrms, axis=2)[:, :, None]
        cop_bvh = bvh_of(cop)
        if tab.get("skive"):
            # (b2r3: pared to `skive[0]` of its thickness at its cut edge over `skive[1]`: its side wall caught the light as
            # a bright outline)
            G["EDGE_SKIVE"][f"{PID}.tab_{sd}"] = (float(tab["skive"][0]), float(tab["skive"][1]))
        tab_o, tinfo = skin_band(f"{PID}.tab_{sd}", cols, nrms, "darkleather", tab["lift"], tab["thick"], under=cop_bvh,
                                 sheet=(cop_sheet[0], np.repeat(rows[0][None], len(cop_sheet[0]), 0)), follow=True,
                                 hold=tab.get("hold", 5), ease=tab.get("ease", 2.0))
        op_ = np.nonzero(tinfo["on_plate"])[0]
        off_ = np.arange(len(ss)) > (op_.max() if len(op_) else -1)
        stamp(sd + " tab: top off her skin along it (mm) " + " ".join("%.1f" % ((l_ + tab["thick"]) * 1000) for l_ in tinfo["lift"])
              + "; off the plate: max %.1f, from 6 mm past it %.1f" % (((tinfo["lift"][off_] + tab["thick"]).max() * 1000) if off_.any() else -1,
                 ((tinfo["lift"][np.arange(len(ss)) > (op_.max() if len(op_) else -1) + 6e-3 / (ss[0] - ss[1])] + tab["thick"]).max() * 1000)))
        if tab.get("plain_edge"):
            # (b2r3: no painted stitching or worn edge on it: at 1:1 they drew a light outline round a 22 mm tab)
            for o in tab_o:
                if "rim" in o.keys():
                    del o["rim"]
        # (two low rivets through its riveted part, on the cop's row so they ride the plate)
        km_ = len(tinfo["cols"]) // 2
        mid = tinfo["cols"][km_]
        aims = []
        for off in (-tw * 0.25, tw * 0.25):
            q = G["pl_point"](np.array([S_MED + tin * 0.5]), np.array([off / R]), np.array([R + 0.03]), F_)[0]
            aims.append((q, ctr + ax_ * (S_MED + tin * 0.5)))
        tp_, tn_ = aim_hits(tab_o, aims)
        trv = low_rivets(f"{PID}.tab_{sd}_rivets", tp_, tn_, np.repeat(rows[0][None], len(tp_), 0), tab.get("rivet_r", 0.0024), MKEY) if tp_ else []
        for o in trv:
            o["blend_group"] = cname
        if tab.get("end_rivet"):
            # (b2r3: its end on one small rivet, on her skin's weights there as the tab is: it reads as a strap's end)
            je = len(ss) - 1 - max(1, int(round(tab["end_rivet"] / (ss[0] - ss[1]))))
            ep_ = mid[je] + tinfo["nrm"][km_][je] * (tinfo["lift"][je] + tab["thick"])
            erv = low_rivets(f"{PID}.tab_{sd}_end_rivets", [ep_], [tinfo["nrm"][km_][je]], G["soft_weights"](ep_[None]), tab.get("end_rivet_r", 0.002), MKEY)
            trv = trv + erv
        left["tab"] = tab_o + trv
        PAUL.setdefault("tab_on_plate_mm", {})[sd] = round(float(tinfo["on_plate"].sum() * (tin + trun) / len(ss) * 1000), 1)
        return dict(locals())

    S = {sd: one_side(sd) for sd in "lr"}
    parts = [o for sd in "lr" for v in S[sd]["left"].values() for o in v]
    plates = [S[sd]["left"][k][0] for sd in "lr" for k in ("cop", "lame1", "lame2")]
    # ---- sockets and rims (glTF space)
    socks, rims = {}, {}

    def sock(name, p, n, up, row):
        n = np.asarray(n, float) / np.linalg.norm(n)
        up = np.asarray(up, float) - n * (np.asarray(up, float) @ n)
        up /= np.linalg.norm(up)
        socks[name] = {"point": gl(p).round(5).tolist(), "normal": gl(n).round(5).tolist(), "up": gl(up).round(5).tolist(), "weights": top4(row)}

    def rim_of(tn, row, closed, sel=None):
        tb = CAP["tubes"][tn]
        cur, nrm_, ow = tb["curve"], tb["nrm"], tb["outward"]
        if sel is not None:
            cur, nrm_, ow = cur[sel], nrm_[sel], ow[sel]
        return {"closed": closed, "points": gl(cur).round(5).tolist(), "normals": gl(nrm_).round(4).tolist(), "outward": gl(ow).round(4).tolist(),
                "weights": [top4(row)] * len(cur), "roll": {"width": tb["width"], "height": tb["height"], "overhang": tb["overhang"]}, "tube": tn}
    for sd in "lr":
        Z = S[sd]
        F_, R, rows, left, ctr, ax_, V_ = Z["F_"], Z["R"], Z["rows"], Z["left"], Z["ctr"], Z["ax_"], Z["V_"]

        def outer_at(objs, s, th):
            q = G["pl_point"](np.array([s]), np.array([th]), np.array([R + 0.05]), F_)[0]
            p_, n_ = aim_hits(objs, [(q, ctr + ax_ * s)])
            return (p_[0], n_[0]) if p_ else (q, q - (ctr + ax_ * s))
        for key, k, s_at in (("cop", 0, (S_MED + S_LOW) / 2), ("lame1", 1, S_LOW + V_[0] / 2), ("lame2", 2, S_LOW + V_[0] + V_[1] / 2)):
            p_, n_ = outer_at([left[key][0]], s_at, 0.0)
            sock(f"{key}_{sd}", p_, n_, -ax_, rows[k])
        mid, tinfo = Z["mid"], Z["tinfo"]
        jt = len(mid) // 2
        km_ = len(tinfo["cols"]) // 2
        tq = mid[jt] + tinfo["nrm"][km_][jt] * (tinfo["lift"][jt] + tab["thick"])
        sock(f"tab_{sd}", tq, tinfo["nrm"][km_][jt], -ax_, G["soft_weights"](tq[None])[0])
        rims[f"cop_rim_{sd}"] = rim_of(f"{PID}.cop_{sd}_bind", rows[0], True)
        for k in (1, 2):
            tn = f"{PID}.lame{k}_{sd}_bind"
            sl_ = G["pl_frame"](CAP["tubes"][tn]["curve"], F_)[0]
            rims[f"lame{k}_rim_{sd}"] = rim_of(tn, rows[k], False, np.nonzero(sl_ > np.median(sl_))[0])     # (its lower edge)
        cl = [outer_at([left["cop"][0]], s, 0.0) for s in np.linspace(S_MED + 0.003, S_LOW - 0.003, 24)]
        rims[f"comb_{sd}"] = {"closed": False, "points": gl(np.array([c[0] for c in cl])).round(5).tolist(),
                              "normals": gl(np.array([c[1] for c in cl])).round(4).tolist(), "weights": [top4(rows[0])] * len(cl),
                              "ridge": {"h": comb["h"], "w": comb["w"]}}
    roll_prefix = [f"{PID}.{p}_{sd}_bind" for p in ("cop", "lame1", "lame2") for sd in "lr"]
    cname = f"{PID}.cop_l"
    sheet = CAP["sheet"][cname]
    return dict(parts=parts, shell=plates, envelope=[S["l"]["left"]["cop"][0], S["r"]["left"]["cop"][0]], sheet=(sheet[0], sheet[1], sheet[2]),
                thick=THK, lift=CLEAR, sockets=socks, rims=rims, roll=roll, avoid=[], roll_prefix=roll_prefix, measure=paul_measure)


def paul_measure():
    """The pauldrons' own numbers (b_design_spec section 1, Proof): the cop's standoff off her body (all, its neck rim),
    its neck edge from her neck_01-weighted skin at rest and in the shrug, the rim's fairness (its largest turn over
    3 mm), the weight ladder."""
    S_MED = PAUL["S_MED"]
    out = {"cop_build": {k: PAUL.get(k) for k in ("cop_lift_mm", "cop_clear_mm_before_push")}, "sides": PAUL["sides"], "tab_on_plate_mm": PAUL.get("tab_on_plate_mm"),
           "tuck_under": PAUL.get("tuck_under")}
    bb = BVHTree.FromPolygons([tuple(p) for p in bv0], [p_.vertices[:] for p_ in me.polygons])
    # (b2r2: the standoff off her FINAL skin (heroine.glb), not this scene's body, which stands up to 8 mm off it near
    # her neck; tucked by the piece's record as the game draws it: tools/armor/paul_check.py, after the install)
    bb = G["final_skin_bvh"]() or bb
    _, jp = cKDTree(P).query(bv0)
    neck_w = W[jp, BI["neck_01"]] > PRM.get("neck_w", 0.1)
    st_ = lambda d: {"n": int(len(d)), "p50": round(float(np.median(d)), 2), "p99": round(float(np.percentile(d, 99)), 2),
                     "max": round(float(d.max()), 2)} if len(d) else None
    out["standoff_cop_mm"], out["neck_edge_mm"], out["cop_rim_turn_deg_per_3mm"] = {}, {}, {}
    cops = {sd: next(o for o in made if o.name == f"{PID}.cop_{sd}") for sd in "lr"}
    for sd in "lr":
        F_ = PAUL["F_" + sd]
        sp = CAP["sheet"][f"{PID}.cop_{sd}"][0]
        d = np.array([np.linalg.norm(np.array(bb.find_nearest(Vector(q))[0][:]) - q) for q in sp]) * 1000
        s_ = G["pl_frame"](sp, F_)[0]
        out["standoff_cop_mm"][sd] = {"all": st_(d), "neck_rim": st_(d[s_ < S_MED + 0.012])}
        cur = CAP["tubes"][f"{PID}.cop_{sd}_bind"]["curve"]
        cw = np.vstack([cur, cur[:1]])
        run_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cw, axis=0), axis=1))]
        tt = np.arange(0, run_[-1], 0.003)
        q = np.stack([np.interp(tt, run_, cw[:, k]) for k in range(3)], 1)
        a_ = np.diff(np.vstack([q, q[:1]]), axis=0)
        a_ /= np.linalg.norm(a_, axis=1)[:, None]
        ang = np.degrees(np.arccos(np.clip((a_ * np.roll(a_, -1, 0)).sum(1), -1, 1)))
        out["cop_rim_turn_deg_per_3mm"][sd] = round(float(ang.max()), 1)
        im_ = int(ang.argmax())
        sq_, tq_, _ = G["pl_frame"](q[im_:im_ + 1], F_)
        out.setdefault("cop_rim_turn_at", {})[sd] = [round(float(sq_[0] * 1000), 1), round(float(np.degrees(tq_[0])), 0)]
    co_ = {sd: np.array([(cops[sd].matrix_world @ v.co)[:] for v in cops[sd].data.vertices]) for sd in "lr"}
    nk_ = {sd: G["pl_frame"](co_[sd], PAUL["F_" + sd])[0] < S_MED + 0.003 for sd in "lr"}
    for pname, rots in (("rest", []), ("shrug", POSES.get("shrug", []))):
        bv, bn, dg = pose_body(rots)
        nt = cKDTree(bv[neck_w])
        for sd in "lr":
            oe = cops[sd].evaluated_get(dg)
            m_ = oe.to_mesh()
            v = np.array([(cops[sd].matrix_world @ x.co)[:] for x in m_.vertices])
            oe.to_mesh_clear()
            out["neck_edge_mm"].setdefault(pname, {})[sd] = round(float(nt.query(v[nk_[sd]])[0].min() * 1000), 1) if nk_[sd].any() else None
    pose_rest()
    return out


# ---------------------------------------------- the shell: the g-string --
# (armor 13 g1, b_design_spec 3a: the high-rise g-string. A darkleather front panel and gusset cut from her skin (as
# warden.thong), two side strings riding high over her bare hip bones to her waist and down behind to a small leather
# triangle at her sacral dimples, a back string down the cleft flaring into the gusset, and a steel ring at each of the
# panel's top corners. Everything but the rings follows her skin; each ring is rigid on the panel's blend at its foot.)
GSTR = {}
HIP = {}


def hip_landmarks():
    """Her pelvis landmarks for hip_line (both bodies have them; cached): `c` the rays' centre (her pelvis bone's x, y),
    `asis` {sd: z} the ASIS bump (the most forward point of her front at |x| `asis_x`, between 40 and 180 mm over her
    crotch), `crest` her iliac crest's estimate (the narrowest point of her side's width between the ASIS and 120 mm
    above it would be her waist; the crest is taken as the ASIS + `crest_rise`, 35 mm, the anatomical rise of the crest's
    highest point over the ASIS), `waist` (spine_01's head), `crotch`."""
    if HIP:
        return HIP
    pel = G["head"]("pelvis")
    cr = float(G["CROTCH"])
    ax = PRM.get("asis_x", 0.09)
    asis = {}
    for sd, s in (("l", 1.0), ("r", -1.0)):
        zz = np.arange(cr + 0.04, cr + 0.18, 0.002)
        fy = np.array([G["front_point"](s * ax, z)[1] for z in zz])
        # (local most-forward point: the ASIS stands proud of the flank below and the waist above; the belly's own
        # forward bulge lies inside |x| 0.09)
        k = int(np.argmin(fy))
        asis[sd] = float(zz[k])
        sy = [float(G["side_point"](sd, float(pel[1]), z)[0]) if "side_point" in G else 0.0 for z in zz[::5]]
        print("HIP profile %s: z-crotch mm, front y mm at |x| %.3f, side |x| mm" % (sd, ax),
              [(round((z - cr) * 1000), round(y * 1000, 1), round(abs(x_) * 1000, 1)) for z, y, x_ in zip(zz[::5], fy[::5], sy)])
    HIP.update(c=np.array([0.0, float(pel[1]), 0.0]), asis=asis, waist=float(G["WAIST"]), crotch=cr,
               crest={sd: asis[sd] + PRM.get("crest_rise", 0.035) for sd in "lr"})
    return HIP


def hip_ray(sd, a, z, c=None):
    """Her skin where a level ray from her pelvis centre (at height z) at azimuth `a` meets it: a = 0 straight ahead,
    pi/2 out to side `sd` ('l' is +x), pi straight behind. (point, outward normal) or (None, None)."""
    s = 1.0 if sd == "l" else -1.0
    c = HIP["c"] if c is None else c
    d = np.array([s * np.sin(a), -np.cos(a), 0.0])
    o = np.array([c[0], c[1], z])
    h = G["SKIN_BVH"].ray_cast(Vector(tuple(o)), Vector(tuple(d)), 0.6)
    if h[0] is None:
        return None, None
    n = np.array(h[1][:])
    return np.array(h[0][:]), (n if n @ d > 0 else -n)


def _az_at_x(sd, z, x_abs, back=False):
    """The azimuth whose hit at height z lies at |x| = x_abs, on her front (or her back)."""
    lo, hi = (0.0, np.pi / 2) if not back else (np.pi / 2, np.pi)
    for _ in range(40):
        m = (lo + hi) / 2
        p, _ = hip_ray(sd, m, z)
        xa = abs(p[0]) if p is not None else 0.0
        if (xa < x_abs) != back:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def hip_line(sd, panel_top=None, panel_hw=None, cross_rise=None, side_z=None, y_z=None, y_hw=None, step=0.004):
    """The g-string's string path on side `sd` ('l' +x, 'r' -x), on her skin, laid by level rays from her pelvis centre
    (hip_landmarks()["c"]), from the front panel's top corner round to the back triangle's top corner:
      1. from the corner (|x| `panel_hw`, `panel_top` over her crotch) up over her ASIS, crossing |x| `asis_x` (0.09)
         `cross_rise` (25 mm) above the bump, so the bone shows under it;
      2. to `side_z` (WAIST, spine_01's head) at her side (azimuth 90 deg);
      3. down behind to the Y's corner (|x| `y_hw`) at `y_z` (CROTCH + 0.15, her sacral dimples).
    The height is a monotone (PCHIP) curve of the azimuth through those four keys, so it never overshoots between them.
    Defaults are the piece's params (b_design_spec 3a); every one is an offset from a landmark both bodies have.
    Returns {"points": (n, 3) on her skin, "normals": (n, 3) outward, "s": (n,) metres along it from the corner,
    "keys": {"corner", "cross", "side", "y"}: (index, point)}. The cuisses' garter (3b) ends on it, so neither piece
    needs the other built first."""
    from scipy.interpolate import PchipInterpolator
    L = hip_landmarks()
    cr = L["crotch"]
    panel_top = PRM.get("panel_top", 0.08) if panel_top is None else panel_top
    panel_hw = PRM.get("panel_hw", 0.035) if panel_hw is None else panel_hw
    cross_rise = PRM.get("cross_rise", 0.025) if cross_rise is None else cross_rise
    side_z = L["waist"] + PRM.get("side_dz", 0.0) if side_z is None else side_z
    y_z = cr + PRM.get("y_z", 0.15) if y_z is None else y_z
    y_hw = PRM.get("y_hw", 0.016) if y_hw is None else y_hw
    ax = PRM.get("asis_x", 0.09)
    z0 = cr + panel_top
    z1 = max(L["asis"][sd] + cross_rise + PRM.get("cross_margin", 0.004), z0 + 0.01)
    a0 = _az_at_x(sd, z0, panel_hw)
    a1 = _az_at_x(sd, z1, ax)
    a3 = _az_at_x(sd, y_z, y_hw, back=True)
    ka = np.array([a0, a1, np.pi / 2, a3])
    kz = np.array([z0, z1, side_z, y_z])
    zf = PchipInterpolator(ka, kz)
    aa = np.linspace(a0, a3, 1400)
    pts, nrs, az = [], [], []
    for a in aa:
        p, n = hip_ray(sd, a, float(zf(a)))
        if p is not None:
            pts.append(p), nrs.append(n), az.append(a)
    pts, nrs, az = np.array(pts), np.array(nrs), np.array(az)
    run_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    ss = np.linspace(0, run_[-1], max(8, int(round(run_[-1] / step))) + 1)
    res = lambda a_: np.stack([np.interp(ss, run_, a_[:, k]) for k in range(a_.shape[1])], 1)
    pts, nrs = res(pts), res(nrs)
    azs = np.interp(ss, run_, az)
    nrs /= np.linalg.norm(nrs, axis=1)[:, None]
    keys = {}
    for nm, a in (("corner", a0), ("cross", a1), ("side", np.pi / 2), ("y", a3)):
        k = int(np.argmin(np.abs(azs - a)))
        keys[nm] = (k, pts[k])
    return {"points": pts, "normals": nrs, "s": ss, "keys": keys, "az": azs}


def _torus(p0, n, w, R, r, nu=12, nv=6):
    """A ring (major radius R, minor r) lying flat on the point p0's tangent plane, raised r + 0.3 mm along n."""
    n = np.asarray(n, float) / np.linalg.norm(n)
    t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
    t /= np.linalg.norm(t)
    b = np.cross(n, t)
    c = p0 + n * (r + 0.0003)
    q = []
    for i in range(nu):
        u = 2 * np.pi * i / nu
        e = np.cos(u) * t + np.sin(u) * b
        for j in range(nv):
            v = 2 * np.pi * j / nv
            q.append(c + e * (R + r * np.cos(v)) + n * (r * np.sin(v)))
    q = np.array(q)
    tri = []
    for i in range(nu):
        for j in range(nv):
            a_, b_ = i * nv + j, ((i + 1) % nu) * nv + j
            c_, d_ = ((i + 1) % nu) * nv + (j + 1) % nv, i * nv + (j + 1) % nv
            tri += [(a_, b_, c_), (a_, c_, d_)]
    return q, np.repeat(np.asarray(w, float)[None], len(q), 0), np.array(tri)


def _band_along_mid(name, line, width, lift, thick, hides=False, ncol=5, sigma=None):
    """A skin_band (follow) along a line down her middle (the back string in her cleft), `width` (scalar or per point)
    across it along x: its columns found by casting in from 20 mm out along the line's own frame normal (the line's
    tangent crossed with x, facing away from her pelvis centre), never her skin's normal, which in the cleft faces a
    cheek. Returns its objects."""
    line = np.asarray(line, float)
    tng = np.gradient(line, axis=0)
    tng /= np.linalg.norm(tng, axis=1)[:, None]
    acr = np.repeat(np.array([[1.0, 0.0, 0.0]]), len(line), 0)
    nrs = np.cross(tng, acr)
    nrs /= np.linalg.norm(nrs, axis=1)[:, None]
    cc = np.c_[np.zeros(len(line)), np.full(len(line), HIP["c"][1]), np.full(len(line), HIP["crotch"] + 0.06)]
    nrs = np.where(((nrs * (line - cc)).sum(1) < 0)[:, None], -nrs, nrs)
    wid = np.broadcast_to(np.asarray(width, float), (len(line),))
    cols, cn = [], []
    for k in range(ncol):
        f_ = k / (ncol - 1) - 0.5
        cp, cq = [], []
        for p, n, a, w_ in zip(line, nrs, acr, wid):
            h, hn = skin_hit(p + a * f_ * w_ + n * 0.02, -n)
            if h is None:
                h, hn = p + a * f_ * w_, n
            cp.append(h), cq.append(-hn if hn @ n < 0 else hn)
        cols.append(cp), cn.append(cq)
    objs, info = skin_band(name, np.array(cols), np.array(cn), "darkleather", lift, thick,
                           sigma=PRM.get("string_sigma", 0.008) if sigma is None else sigma, follow=True)
    for o in objs:
        o["hides"] = bool(hides)
    return objs


def drop_strays(obj, zlo, zhi):
    """A piece's points outside the height band [zlo, zhi] (world) deleted, with their faces: the unbound gusset cut
    from her skin came out with two points at her calf (z 0.24) on a sliver joining them, as cut (g1 pv5, pv7)."""
    bm_ = bmesh.new()
    bm_.from_mesh(obj.data)
    mw_ = obj.matrix_world
    bad = [v for v in bm_.verts if not (zlo <= (mw_ @ v.co).z <= zhi)]
    if bad:
        bmesh.ops.delete(bm_, geom=bad, context="VERTS")
        bm_.to_mesh(obj.data)
        obj.data.update()
        print("STRAYS %s: %d points outside z %.3f..%.3f dropped" % (obj.name, len(bad), zlo, zhi))
    bm_.free()
    return len(bad)


def thin_to(obj, tris, sym=False):
    """A finished piece thinned to about `tris` triangles (Blender's collapse decimate, its weights carried; mirrored
    across her middle when `sym`: g1 pv5, mirrored, the gusset threw two points 70 cm down to her calf). finish() keeps every point of a piece's edge and two rows in from it, which for
    a small or narrow piece cut from her fine skin is most of it (the gusset: 5.7k triangles at a 280 budget)."""
    n0 = sum(len(p_.vertices) - 2 for p_ in obj.data.polygons)
    if n0 <= tris:
        return n0
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    am_ = [m_ for m_ in obj.modifiers if m_.type == "ARMATURE"]
    for m_ in am_:
        obj.modifiers.remove(m_)
    co0 = np.array([v.co[:] for v in obj.data.vertices])
    dc = obj.modifiers.new("thin2", "DECIMATE")
    dc.decimate_type = "COLLAPSE"
    dc.ratio = tris / n0
    dc.use_symmetry = sym
    dc.symmetry_axis = "X"
    bpy.ops.object.modifier_apply(modifier=dc.name)
    obj.data.calc_loop_triangles()
    co1 = np.array([v.co[:] for v in obj.data.vertices])
    far = cKDTree(co0).query(co1)[0]
    assert far.max() < 0.004, "THIN %s moved a point %.1f mm off the piece" % (obj.name, far.max() * 1000)
    am = obj.modifiers.new("Armature", "ARMATURE")
    am.object = arm
    n1 = len(obj.data.loop_triangles)
    print("THIN %s: %d -> %d triangles" % (obj.name, n0, n1))
    return n1


def build_gstring():
    L = hip_landmarks()
    X, Y, Z = G["X"], G["Y"], G["Z"]
    cr = L["crotch"]
    panel_top, panel_hw = PRM.get("panel_top", 0.08), PRM.get("panel_hw", 0.035)
    lift, thick = PRM.get("lift", 0.0012), PRM.get("thick", 0.0018)
    y_z = cr + PRM.get("y_z", 0.15)
    parts = []
    # (params.cap_density: the leather pieces' triangle floor a square metre (finish's 60000 unset), so each
    # piece's `*_budget` holds: the whole piece is at most 5k)
    NS["CAP_DENSITY"] = PRM.get("cap_density", 6000)
    # ---- the front panel: a piece of her skin (as warden.thong), its sides along her inguinal creases: half-width
    # `hw_bot` at her crotch widening to `panel_hw` at its top edge (`panel_top` over her crotch), into the gusset
    hb = PRM.get("hw_bot", 0.015)
    fz = np.clip((Z - cr) / panel_top, 0.0, 1.0) ** PRM.get("panel_curve", 1.0)
    hw = hb + (panel_hw - hb) * fz
    pf = G["AND"](G["FRONT"] - 0.3, hw - np.abs(X), (cr + panel_top) - Z, Z - (cr - 0.03))
    panel = G["piece"](f"{PID}.panel", pf, "darkleather", lift=lift, thick=thick, smooth=2, soften=0, budget=PRM.get("panel_budget", 500))
    if panel and panel[0]:
        thin_to(panel[0], PRM.get("panel_tris", 900))
    parts += [o for o in panel if o]
    # ---- the Y: a small leather triangle at her sacral dimples, top edge `y_hw` + 4 mm each side of her middle at
    # y_z + 4 mm, its tip `tri_h` (30 mm) below
    th = PRM.get("tri_h", 0.03)
    yhw = PRM.get("y_hw", 0.016) + 0.004
    tz = np.clip((Z - (y_z - th)) / th, 0.0, 1.0)
    xc_ = (G["head"]("glute_l")[0] + G["head"]("glute_r")[0]) / 2
    tf = G["AND"](0.003 + yhw * tz - np.abs(X - xc_ * (1 - tz)), (y_z + 0.004) - Z, Z - (y_z - th), Y - L["c"][1])
    tri_ = G["piece"](f"{PID}.y", tf, "darkleather", lift=lift, thick=thick, smooth=2, soften=0, budget=PRM.get("y_budget", 150))
    if tri_ and tri_[0]:
        thin_to(tri_[0], PRM.get("y_tris", 260))
    parts += [o for o in tri_ if o]
    # ---- the back string: down the cleft from under the triangle's tip, flaring into the gusset (as warden.thong_back,
    # a ribbon; laid here as a skin_band on 3 lines, `back_step` apart along it, for the triangle budget)
    # (back_string: midway between her glute bones (a ray down x = 0 itself passes through the slit between her
    # cheeks); the triangle's tip leans to it)
    back = G["back_string"](y_z - th + 0.008, cr + 0.012, n=24)
    bl = G["spline"](back, step=PRM.get("back_step", 0.006))
    bw0, (bw1, blen) = PRM.get("back_w", 0.014), PRM.get("back_flare", [0.03, 0.03])
    brun = np.r_[0, np.cumsum(np.linalg.norm(np.diff(bl, axis=0), axis=1))]
    bwid = bw0 + (bw1 - bw0) * np.clip((brun - (brun[-1] - blen)) / blen, 0, 1) ** 2
    parts += _band_along_mid(f"{PID}.back", bl, bwid, PRM.get("back_lift", 0.0015), PRM.get("back_thick", 0.002), hides=True,
                             ncol=PRM.get("back_cols", 5))
    # (the gusset (heroine_outfits gusset()), with a triangle budget and unbound: the binding was 1.3k triangles)
    gf = G["AND"](0.016 - np.abs(X), (0.96 - np.abs(G["N"][:, 0])) * 0.02, (bl[-1][1] + 0.015) - Y, Y - (G["GAP_F"] - 0.006),
                  Z - (cr - 0.015), (cr + 0.03) - Z)
    gus = G["piece"](f"{PID}.gusset", gf, "darkleather", lift=0.001, thick=thick, smooth=2, soften=0, slot=False, bind=False,
                     budget=PRM.get("gusset_budget", 400))
    if gus and gus[0]:
        gus[0]["tuck"] = 0.3
        drop_strays(gus[0], cr - 0.03, cr + 0.045)
        thin_to(gus[0], PRM.get("gusset_tris", 700))
    parts += [o for o in gus if o]
    # ---- the side strings: skin_bands along hip_line, `string_w` wide, from `in_corner` inside the panel's corner
    # to `in_y` inside the triangle's corner
    sw = PRM.get("string_w", 0.015)
    ncol = PRM.get("string_cols", 3)
    rows_ = {}
    for sd in "lr":
        hl = hip_line(sd, step=PRM.get("string_step", 0.008))
        pts, nrs = hl["points"], hl["normals"]
        tng = np.gradient(pts, axis=0)
        tng /= np.linalg.norm(tng, axis=1)[:, None]
        acr = np.cross(nrs, tng)
        acr /= np.linalg.norm(acr, axis=1)[:, None]
        # (overlaps: carried a few mm on past each end, along its own line, onto the panel and the triangle)
        ext = PRM.get("string_overlap", 0.006)
        pre = pts[0] - tng[0] * ext
        post = pts[-1] + tng[-1] * ext
        P_ = np.vstack([pre, pts, post])
        N_ = np.vstack([nrs[:1], nrs, nrs[-1:]])
        A_ = np.vstack([acr[:1], acr, acr[-1:]])
        cols, cn = [], []
        for k in range(ncol):
            off = (k / (ncol - 1) - 0.5) * sw
            cp, cq = [], []
            for p, n, a in zip(P_, N_, A_):
                h, hn = skin_hit(p + a * off + n * 0.02, -n)
                if h is None:
                    h, hn = p + a * off, n
                cp.append(h), cq.append(-hn if hn @ n < 0 else hn)
            cols.append(cp), cn.append(cq)
        cn = np.array(cn)
        cn = np.where(((cn * N_[None]).sum(2) < 0)[..., None], -cn, cn)
        objs, info = skin_band(f"{PID}.string_{sd}", np.array(cols), cn, "darkleather", PRM.get("string_lift", 0.0015),
                               PRM.get("string_thick", 0.0022), sigma=PRM.get("string_sigma", 0.008), follow=True)
        for o in objs:
            o["hides"] = bool(PRM.get("string_hides", False))
        parts += objs
        GSTR[sd] = dict(hl=hl, info=info)
    NS.pop("CAP_DENSITY", None)
    # ---- the rings at the panel's top corners, rigid, on the panel's blend at their foot
    rr = PRM.get("ring_r", 0.009)
    socks = {}

    def sock(name, p, n, up, row):
        n = np.asarray(n, float) / np.linalg.norm(n)
        up = np.asarray(up, float) - n * (np.asarray(up, float) @ n)
        up /= np.linalg.norm(up)
        socks[name] = {"point": gl(p).round(5).tolist(), "normal": gl(n).round(5).tolist(), "up": gl(up).round(5).tolist(),
                       "weights": top4(np.asarray(row, float))}
    rp, rw, rt = [], [], []
    for sd in "lr":
        k0, p0 = GSTR[sd]["hl"]["keys"]["corner"]
        n0 = GSTR[sd]["hl"]["normals"][k0]
        foot = p0 + n0 * (thick + lift)
        row = G["soft_weights"](p0[None], sigma=0.008)[0]
        q, w, t = _torus(foot, n0, row, rr, PRM.get("ring_wire", 0.0016), nu=PRM.get("ring_nu", 12), nv=PRM.get("ring_nv", 6))
        t = t + sum(len(x) for x in rp)
        rp.append(q), rw.append(w), rt.append(t)
        sock(f"ring_{sd}", foot, n0, [0, 0, 1.0], row)
        GSTR.setdefault("ring_at", {})[sd] = foot
    pp, ww, tt = np.vstack(rp), np.vstack(rw), np.vstack(rt)
    cen = np.vstack([np.repeat(GSTR["ring_at"][sd][None], len(q_), 0) for sd, q_ in zip("lr", rp)])
    o_ = finish_cap(f"{PID}.rings", pp, ww, tt, PRM.get("ring_mat", "steel"), 0.0, 0.0, 10 ** 7, scraps=False)
    o_["hides"] = False
    o_["rigid_part"] = True
    parts.append(o_)
    # ---- sockets: the panel's front, the rings, the Y behind
    fp = G["front_point"](0.0, cr + panel_top * 0.6)
    fn = G["SKIN_BVH"].find_nearest(Vector(fp))[1][:]
    sock("front", fp + np.array(fn) * (lift + thick), fn, [0, 0, 1.0], G["soft_weights"](fp[None], sigma=0.008)[0])
    yp, yn = hip_ray("l", np.pi, y_z - th / 2)
    sock("y_back", yp + yn * (lift + thick), yn, [0, 0, 1.0], G["soft_weights"](yp[None], sigma=0.008)[0])
    leather = [o for o in parts if o is not o_]
    sname = f"{PID}.panel"
    sh = CAP["sheet"].get(sname) or next(iter(CAP["sheet"].values()))
    GSTR["landmarks"] = {k: (v if not isinstance(v, np.ndarray) else v.tolist()) for k, v in L.items()}
    tris_ = {o.name: sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in parts}
    print("GSTRING landmarks", json.dumps(GSTR["landmarks"]), "triangles", sum(tris_.values()), json.dumps(tris_))
    return dict(parts=parts, shell=leather, envelope=leather, gore=[], sheet=(sh[0], sh[1], sh[2]), thick=thick, lift=lift,
                sockets=socks, rims={}, roll={}, avoid=[], roll_prefix=[], measure=gstring_measure)


def gstring_measure():
    """The g-string's own numbers (b_design_spec 3a, Proof): each string's standoff off her skin at rest across its
    width (p50/p99/max of its inner face's distance to her skin), the ASIS crossing's height over the bump at |x|
    asis_x, side_z over her iliac crest (estimate) and over the bump, the strings' length."""
    out = {"landmarks": GSTR.get("landmarks")}
    skin = G["SKIN_BVH"]
    for sd in "lr":
        info, hl = GSTR[sd]["info"], GSTR[sd]["hl"]
        C, Nn, lift = info["cols"], info["nrm"], info["lift"]
        # (the inner face: the band's points lifted off her, as skin_band laid them; their nearest skin)
        Q = C + Nn * lift[None, :, None]
        # (and the middle of each cell between its rows and columns: where it would bridge a hollow)
        Q = np.concatenate([Q.reshape(-1, 3), ((Q[1:, 1:] + Q[:-1, :-1] + Q[1:, :-1] + Q[:-1, 1:]) / 4).reshape(-1, 3)])[None]
        d = np.array([[np.linalg.norm(np.array(skin.find_nearest(Vector(tuple(q)))[0][:]) - q) for q in row] for row in Q]) * 1000
        k1 = hl["keys"]["cross"][0]
        ax = PRM.get("asis_x", 0.09)
        pts = hl["points"]
        # (the height where the string's centre line crosses |x| asis_x, on her front)
        fr = pts[: hl["keys"]["side"][0]]
        j = int(np.argmin(np.abs(np.abs(fr[:, 0]) - ax)))
        out[f"string_{sd}"] = {"standoff_mm": {"p50": round(float(np.median(d)), 2), "p99": round(float(np.percentile(d, 99)), 2),
                                               "max": round(float(d.max()), 2)},
                               "asis_cross_over_bump_mm": round(float((pts[j, 2] - HIP["asis"][sd]) * 1000), 1),
                               "side_z_over_crest_mm": round(float((hl["keys"]["side"][1][2] - HIP["crest"][sd]) * 1000), 1),
                               "side_z_over_asis_mm": round(float((hl["keys"]["side"][1][2] - HIP["asis"][sd]) * 1000), 1),
                               "length_mm": round(float(hl["s"][-1] * 1000), 1)}
    return {"gstring": out}


# ------------------------------------------------- the shell: a free mesh --
# (armor 9, IM1: docs/armor/PIECE_SCHEMA.md "Free meshes: the import contract". tools/armor/import_mesh.py checks the
# file first (bounds, units, materials, budget, transforms, body) and runs this build. The mesh carries shape and
# material names only: her weights, the push-out to the slot band, the tuck, LODs, sockets, rims and the row are ours.)
MESH = SPEC_PIECE.get("style") == "mesh"
# (the slot band: how far the inner face must stand off her skin at rest, by the slot's layer (slot_map.json "layers"):
# second-skin pieces 1 mm, layer 2 (belts, bracers, greaves, boots) 2 mm, layer 3 (pauldrons, cloak, head) 3 mm)
SLOT_BAND = {0: 0.0005, 1: 0.0010, 2: 0.0020, 3: 0.0030}
IMPORT = {}


def _base_name(n):
    import re
    return re.sub(r"\.\d{3}$", "", n)


def build_mesh():
    import math
    import re
    from mathutils import Matrix
    f = os.path.join(os.path.dirname(PIECE_JSON), PRM["file"])
    ext = os.path.splitext(f)[1].lower()
    before = set(bpy.data.objects)
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=f)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=f)          # (its axes converted to Blender's by the importer: Y up in, Z up here)
    elif ext == ".blend":
        with bpy.data.libraries.load(f, link=False) as (src_, dst_):
            dst_.objects = list(src_.objects)
        for o in dst_.objects:
            if o is not None:
                bpy.context.collection.objects.link(o)
    else:
        raise SystemExit("ARMOR REFUSED: %s: a free mesh is .glb, .gltf, .fbx or .blend" % f)
    new = [o for o in bpy.data.objects if o not in before]
    srcs = [o for o in new if o.type == "MESH" and len(o.data.polygons)]
    # (the file's materials named aside: the game's own of each name (heroine_outfits.mat) takes the name)
    for o in srcs:
        for m_ in o.data.materials:
            if m_ is not None and not m_.name.startswith("src~"):
                m_["key"] = _base_name(m_.name)
                m_.name = "src~" + m_.name
    keep_w = bool(PRM.get("keep_weights"))
    # (named empties: the artist's sockets, at their place, +Z out of the surface)
    empties = {_base_name(o.name): np.array(o.matrix_world) for o in new if o.type == "EMPTY" and not o.children}
    # Every transform applied (identity objects), parents and armatures let go: the mesh in her world as the file has it.
    for o in srcs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
        for m_ in list(o.modifiers):
            o.modifiers.remove(m_)
        if not keep_w:
            o.vertex_groups.clear()
        else:
            for g in list(o.vertex_groups):
                if g.name not in BI:
                    o.vertex_groups.remove(g)
    for o in new:
        if o not in srcs:
            bpy.data.objects.remove(o)
    # Mirrored, when asked: each object copied across her middle (x -> -x), _l and _r swapped in its name.
    if PRM.get("mirror"):
        for o in list(srcs):
            c = o.copy()
            c.data = o.data.copy()
            bpy.context.collection.objects.link(c)
            c.data.transform(Matrix.Scale(-1.0, 4, Vector((1, 0, 0))))
            c.data.flip_normals()
            nm = _base_name(o.name)
            sw = re.sub(r"_l(?=_|$)", "_R_", nm)
            sw = re.sub(r"_r(?=_|$)", "_l", sw).replace("_R_", "_r")
            c.name = sw if sw != nm else nm + "_mirror"
            if keep_w:
                for g in c.vertex_groups:
                    if g.name.endswith("_l") or g.name.endswith("_r"):
                        g.name = g.name[:-1] + ("r" if g.name.endswith("_l") else "l") + "~"
                for g in c.vertex_groups:
                    g.name = g.name.rstrip("~")
            srcs.append(c)
    # Each object split by material (one material a part: the export joins a slot's parts by material); the material
    # is the game's own entry of that name (outfit_materials.json), its UVs laid out at the material's true size.
    parts, rigid_of = [], {}
    for o in srcs:
        bname = _base_name(o.name)
        rigid = bname.endswith("_rigid")
        bm_ = bmesh.new()
        bm_.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm_, verts=bm_.verts, dist=0.00001)
        bmesh.ops.triangulate(bm_, faces=bm_.faces)
        bm_.to_mesh(o.data)
        bm_.free()
        o.data.update()
        # her weights at its points (soft: averaged over her skin round each point, four bones)
        co = np.array([v.co[:] for v in o.data.vertices])
        wt = G["four_bones"](G["soft_weights"](co)) if not keep_w else None
        row = None
        if rigid:
            # (a rigid part rides ONE blend from her skin at its centre: the mean of its points' blends, its four
            # largest shares, so it never bends; heroine_outfits' rigid_again keeps it on that blend after the helpers)
            if wt is None:
                wt = G["four_bones"](G["soft_weights"](co))
            m_ = wt.mean(0)
            k_ = [i for i in np.argsort(-m_)[:4] if m_[i] > 1e-4]
            row = [(BONES[i], float(m_[i] / sum(m_[j] for j in k_))) for i in k_]
            # (params.rigid_drop [bone prefix, ..] (body1 g4): bones left out of every rigid part's blend, the rest
            # renormalized. The mean of the bracers' points took 8-10% hand from her wrist under their cuff, so every
            # wrist bend swung the steel tube through her forearm: her skin through it by 2 mm over 55% of its
            # footprint in the 22-clip wearcheck; without the hand, about 8%)
            drop_ = tuple(PRM.get("rigid_drop") or ())
            if drop_:
                k_ = [i for i in np.argsort(-m_) if m_[i] > 1e-4 and not BONES[i].startswith(drop_)][:4]
                row = [(BONES[i], float(m_[i] / sum(m_[j] for j in k_))) for i in k_]
        mats = [m.get("key") if m else None for m in o.data.materials]
        used = sorted({p.material_index for p in o.data.polygons})
        for mi in used:
            mkey = _base_name(mats[mi]) if mi < len(mats) and mats[mi] else None
            if mkey not in G["SPEC"]:
                raise SystemExit("ARMOR REFUSED: %s: material %r is not in outfit_materials.json" % (bname, mkey))
            bm_ = bmesh.new()
            bm_.from_mesh(o.data)
            bmesh.ops.delete(bm_, geom=[fc for fc in bm_.faces if fc.material_index != mi], context="FACES")
            bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
            nm = f"{PID}.{bname}" + ("" if len(used) == 1 else f"_{mkey}")
            me_ = bpy.data.meshes.new(nm)
            bm_.to_mesh(me_)
            bm_.free()
            p_ = bpy.data.objects.new(nm, me_)
            bpy.context.collection.objects.link(p_)
            pc = np.array([v.co[:] for v in me_.vertices])
            if keep_w:
                # (the artist's weights, by nearest source point: same positions)
                _, jj = cKDTree(co).query(pc)
                srcg = {g.index: g.name for g in o.vertex_groups}
                for k, j in enumerate(jj):
                    for g in o.data.vertices[int(j)].groups:
                        nmg = srcg[g.group]
                        (p_.vertex_groups.get(nmg) or p_.vertex_groups.new(name=nmg)).add([k], g.weight, "REPLACE")
                if row is not None:
                    set_one_blend(p_, row)
            elif row is not None:
                set_one_blend(p_, row)
            else:
                _, jj = cKDTree(co).query(pc)
                groups = {}
                for k, j in enumerate(jj):
                    r_ = wt[int(j)]
                    top = np.argsort(-r_)[:4]
                    tot = r_[top].sum() or 1.0
                    for b_ in top:
                        if r_[b_] > 0.003:
                            if b_ not in groups:
                                groups[b_] = p_.vertex_groups.new(name=BONES[b_])
                            groups[b_].add([k], float(r_[b_] / tot), "REPLACE")
            # UVs: one smart projection, scaled to the material's metres (as heroine_outfits.finish lays a sheet)
            bpy.ops.object.select_all(action="DESELECT")
            p_.select_set(True)
            bpy.context.view_layer.objects.active = p_
            me_.uv_layers.new()
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, scale_to_bounds=False)
            bpy.ops.object.mode_set(mode="OBJECT")
            uv = me_.uv_layers.active.data
            a3 = sum(p.area for p in me_.polygons)
            a2 = 0.0
            for p in me_.polygons:
                l_ = [uv[k].uv for k in p.loop_indices]
                for k in range(1, len(l_) - 1):
                    a2 += abs((l_[k] - l_[0]).cross(l_[k + 1] - l_[0])) / 2
            sc = math.sqrt(a3 / max(a2, 1e-12)) * G["SPEC"][mkey][3]
            for d in uv:
                d.uv = d.uv * sc
            me_.materials.append(G["mat"](mkey))
            for p in me_.polygons:
                p.use_smooth = True
            me_.set_sharp_from_angle(angle=math.radians(50))
            p_.parent = arm
            am = p_.modifiers.new("Armature", "ARMATURE")
            am.object = arm
            p_["hides"] = True
            p_["source_part"] = bname
            parts.append(p_)
            rigid_of[p_.name] = bool(rigid)
        bpy.data.objects.remove(o)
    # ---- pushed out to the slot band: her skin at rest, any point of the piece nearer her than the band along her
    # normal (or inside her) is moved out by a smooth bump `push_sigma` wide, the whole piece together, so nothing parts.
    band = SLOT_BAND[json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["layers"][SLOT]]
    sig = PRM.get("band_sigma", 0.010)
    allco = [np.array([v.co[:] for v in p_.data.vertices]) for p_ in parts]
    start = np.vstack(allco)
    for rnd in range(6):
        X = np.vstack(allco)
        Q, D, A = [], [], []
        for x in X:
            h = G["SKIN_BVH"].find_nearest(Vector(x), 0.03)
            if h[0] is None:
                continue
            q, n = np.array(h[0][:]), np.array(h[1][:])
            s = (x - q) @ n
            if s < band - 0.00005:
                Q.append(x)
                D.append(n)
                A.append(band - s)
        if not Q:
            break
        Q, D, A = np.array(Q), np.array(D), np.array(A)
        out = []
        for co_ in allco:
            mv = np.zeros_like(co_)
            for a0 in range(0, len(co_), 400):
                x = co_[a0:a0 + 400]
                g = np.exp(-((x[:, None, :] - Q[None]) ** 2).sum(2) / (2 * sig ** 2)) * A[None]
                mag = g.max(1)
                dv = (g[:, :, None] * D[None]).sum(1)
                dv /= np.linalg.norm(dv, axis=1)[:, None] + 1e-12
                mv[a0:a0 + 400] = dv * mag[:, None]
            out.append(co_ + mv)
        allco = out
        IMPORT.setdefault("band_rounds", []).append({"points": int(len(Q)), "deepest_mm": round(float(A.max() * 1000), 2)})
    for p_, co_ in zip(parts, allco):
        p_.data.vertices.foreach_set("co", co_.ravel())
        p_.data.update()
    moved = np.linalg.norm(np.vstack(allco) - start, axis=1) * 1000
    IMPORT["band_mm"] = band * 1000
    IMPORT["push_to_band_mm"] = {"max": round(float(moved.max()), 2), "p99": round(float(np.percentile(moved, 99)), 2),
                                 "moved_points": int((moved > 0.01).sum()), "points": int(len(moved))}
    IMPORT["rigid_parts"] = sorted({p_["source_part"] for p_ in parts if rigid_of[p_.name]})
    IMPORT["bending_parts"] = sorted({p_["source_part"] for p_ in parts if not rigid_of[p_.name]})
    IMPORT["rigid"] = bool(parts) and all(rigid_of.values())
    # ---- sockets: the file's named empties (glTF frame); rims: each part's open boundary loops (best effort)
    socks, rims = {}, {}
    for nm, M in empties.items():
        p = M[:3, 3]
        z = M[:3, 2] / (np.linalg.norm(M[:3, 2]) + 1e-12)
        y = M[:3, 1] - z * (M[:3, 1] @ z)
        y /= np.linalg.norm(y) + 1e-12
        socks[nm] = {"point": gl(p).round(5).tolist(), "normal": gl(z).round(5).tolist(), "up": gl(y).round(5).tolist(),
                     "weights": top4(G["soft_weights"](p[None])[0])}
    for p_ in parts:
        me_ = p_.data
        co_ = np.array([v.co[:] for v in me_.vertices])
        tr_ = np.array([pl.vertices[:] for pl in me_.polygons])
        if len(tr_) < 8:
            continue
        nr_ = G["vertex_normals"](co_, tr_)
        for k, lp in enumerate(G["edge_loops"](tr_)):
            lp = np.asarray(lp)
            if len(lp) < 8:
                continue
            cur = co_[lp]
            c_ = cur.mean(0)
            nn = nr_[lp]
            ow = cur - c_
            ow -= nn * (ow * nn).sum(1)[:, None]
            ow /= np.linalg.norm(ow, axis=1)[:, None] + 1e-12
            rw = G["soft_weights"](cur)
            rims[f"{p_['source_part']}_rim{k}"] = {"closed": True, "points": gl(cur).round(5).tolist(), "normals": gl(nn).round(4).tolist(),
                                                     "outward": gl(ow).round(4).tolist(), "weights": [top4(r_) for r_ in rw]}
    IMPORT["sockets"] = sorted(socks)
    IMPORT["rims"] = len(rims)
    stamp("mesh imported: %d parts (%d rigid sources), band %.1f mm, pushed %s" % (len(parts), len(IMPORT["rigid_parts"]), band * 1000, IMPORT["push_to_band_mm"]))
    z3 = np.zeros((0, 3))
    return dict(parts=parts, shell=parts, envelope=parts, gore=[], sheet=(z3, np.zeros((0, NB)), np.zeros((0, 3), int)), thick=0.0,
                lift=band, sockets=socks, rims=rims, roll=None, avoid=[])


STYLES = {("top", "plate"): build_plate_top, ("pauldrons", "lamed"): build_pauldrons_lamed, ("top", "cuirass"): build_cuirass,
          ("bottom", "gstring"): build_gstring}
if MESH:
    STYLES[(SLOT, "mesh")] = build_mesh
stamp("building %s (%s/%s)" % (PID, SLOT, SPEC_PIECE["style"]))
B = STYLES[(SLOT, SPEC_PIECE["style"])]()
# (armor 10: the rolled edges whose rims carry the native rivet rows, the trim strip and the rolled-edge numbers: a
# style names them by prefix (`roll_prefix`); the plate top's are its cups' binds)
ROLLS = tuple(B.get("roll_prefix", [f"{PID}.cups_bind"]))
TOP_PLATE = (SLOT, SPEC_PIECE["style"]) == ("top", "plate")
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
            if not tn.startswith(ROLLS):
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
    if not TOP_PLATE:
        # (another style: its parts' triangles and the scene, then out; its numbers come from the full build)
        for o in made:
            co_ = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
            print("PREVIEW part %s %d bbox %s %s" % (o.name, sum(len(p_.vertices) - 2 for p_ in o.data.polygons),
                                                     co_.min(0).round(3).tolist(), co_.max(0).round(3).tolist()))
        if B.get("measure"):
            print("PREVIEW measure", json.dumps(B["measure"]()))
        for o in list(bpy.data.objects):
            if o not in made and o is not body and o is not arm:
                bpy.data.objects.remove(o)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SCRATCH, "preview.blend"), copy=True)
        raise SystemExit(0)
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
    if tn.startswith(ROLLS):
        trim_uv(tb["obj"], tb, "rolled_edge")

# ------------------------------------------------ her skin's tuck under it --
me = body.data
hides = [o for o in made if o.get("hides")]
tuck, hid = G["tuck_of"](PID, hides, SLOT)
tuck_of_out = tuck.copy()
stamp("tuck: %d of her vertices under it" % hid)
# (armor 10 b2r2, params.tuck_under: her skin under named plates (`plates`: name prefixes after "<id>.") sunk as the
# gore's is, its mark `edge` at the footprint's border climbing to `full` `in` m inside, so a rigid plate over a
# moving joint (the pauldrons' cop and lames over her deltoid) never has her skin come up through it, and what shows
# at its rim sinks least. The footprint: her points whose ray out along her normal (from 3 mm under her) meets one
# of the plates within `reach`; split copies of a point one point; holes up to `close` m closed across her skin.
# The standard rule tucks only skin a piece lies within 4.5 mm of: the pauldrons stand 3-6 mm off, so it marked 154
# points under the cop and her deltoid came up 10.6 mm through it in the swings.)
TU = PRM.get("tuck_under")
if TU:
    # (tuck_under.extra (c2): more footprints, each its own plates and marks (the cuirass's straps, shallow))
    for TU_ in [TU] + list(TU.get("extra", [])):
        pl_objs = [o for o in made if o.type == "MESH" and o.name.split(".", 1)[-1].startswith(tuple(TU_.get("plates", ["cop", "lame"])))]
        vs_, fs_ = [], []
        for o in pl_objs:
            b_ = len(vs_)
            vs_ += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            fs_ += [[b_ + i for i in p_.vertices] for p_ in o.data.polygons]
        ttree_ = BVHTree.FromPolygons(vs_, fs_)
        bw_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
        nm_ = body.matrix_world.to_3x3().inverted().transposed()
        bn_ = np.array([(nm_ @ v.normal).normalized()[:] for v in me.vertices])
        reach_ = TU_.get("reach", 0.025)
        pv_ = np.array(vs_)
        near_ = np.nonzero(cKDTree(pv_).query(bw_, distance_upper_bound=reach_ + 0.01)[0] < reach_ + 0.01)[0]
        hit_ = np.zeros(len(bw_), bool)
        # (tuck_under.horiz (the cuirass, c2): also cast along the level part of her normal. In the underbust crease and on
        # the belly's top under the lower rim her normal points up or down along the plate and the ray missed it, so that
        # skin was never tucked and came up 5-7 mm through the lower rim in the town runs)
        hz_ = TU_.get("horiz", 0.0)
        # (tuck_under.from (Body 13, 26 Oct): the ray's start under her skin, m (default 3 mm). A plate laid by its own
        # law, never on her skin (the lames, under the plate above), can sink deeper into a fuller arm than 3 mm: from
        # 3 mm its skin's ray started outside it and missed, and that skin came through it untucked at rest)
        fr_ = TU_.get("from", 0.003)
        for i in near_:
            h_ = ttree_.ray_cast(Vector(bw_[i] - bn_[i] * fr_), Vector(bn_[i]), reach_ + fr_)
            hit_[i] = h_[0] is not None
            if not hit_[i] and hz_:
                nh_ = np.array([bn_[i][0], bn_[i][1], 0.0])
                ln_ = float(np.linalg.norm(nh_))
                if ln_ > hz_:
                    nh_ /= ln_
                    h_ = ttree_.ray_cast(Vector(bw_[i] - nh_ * fr_), Vector(nh_), reach_ + fr_)
                    hit_[i] = h_[0] is not None
        _, gid_ = np.unique(np.round(bw_ / 1e-6).astype(np.int64), axis=0, return_inverse=True)
        gid_ = np.asarray(gid_).ravel()
        gh_ = np.zeros(gid_.max() + 1, bool)
        np.logical_or.at(gh_, gid_, hit_)
        inm_ = gh_[gid_]
        on_ = np.zeros(len(bw_), bool)
        on_[np.array([i for p_ in me.polygons for i in p_.vertices])] = True
        cl_ = TU_.get("close", 0.004)
        if cl_ > 0:
            dil_ = on_ & (inm_ | (cKDTree(bw_[inm_]).query(bw_)[0] <= cl_))
            ero_ = dil_ & (cKDTree(bw_[on_ & ~dil_]).query(bw_)[0] > cl_)
            inm_ = inm_ | ero_
        inF_ = np.nonzero(inm_ & on_)[0]
        din_ = cKDTree(bw_[on_ & ~inm_]).query(bw_[inF_])[0]
        e_, f_, w_ = TU_.get("edge", 0.3), TU_.get("full", 0.98), TU_.get("in", 0.008)
        want_ = e_ + (f_ - e_) * np.clip((din_ - 0.002) / max(w_ - 0.002, 1e-6), 0.0, 1.0)
        tuck[inF_] = np.maximum(tuck[inF_], want_)
        if TU_ is TU:
            PAUL["tuck_under"] = {"footprint": int(len(inF_)), "full": int((want_ > 0.973).sum()), "plates": len(pl_objs)}
        else:
            PAUL.setdefault("tuck_under_extra", []).append({"plates": TU_.get("plates"), "footprint": int(len(inF_)), "max": round(float(want_.max()), 3) if len(want_) else 0})
    # (tuck_under.bound (the cuirass): the footprint taken through the bounded tuck (tuck_bound), as the gore's is, so its
    # border slopes in like every other piece's: the window's rim is where a dimple would sit)
    if TU.get("bound") and G.get("TUCK_SMOOTH"):
        tuck = G["tuck_bound"](tuck, G["TUCK_LAST"]["hard"], G["TUCK_LAST"]["under"] | (tuck > 0), label=PID + " under its plates")
    stamp("tuck under the plates: %d footprint points (%d full), %d plates" % (len(inF_), int((want_ > 0.973).sum()), len(pl_objs)))
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
POSES_ARMS = {
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
# (armor 10, b_design_spec "Machinery" (a): the poses per slot, so the push-out and the pose check see the moves that
# load each piece. Pauldrons: the arm poses + a shrug (both collarbones 20 deg up). Legs: a stride (her left thigh 55 deg
# forward, her right 25 back), a lunge (thigh 80, calf 95), a crouch (thighs 105, calves 120), a spread (thighs 35 out).
# Head: a look up 35, down 40, a turn 70 (each 2/5 her neck's, 3/5 her head's, as HeadTurn shares a look).)
POSES_LEGS = {
    "stride": [("thigh_l", (1, 0, 0), 55, (0, -1, 0)), ("thigh_r", (1, 0, 0), 25, (0, 1, 0))],
    "lunge": [("thigh_l", (1, 0, 0), 80, (0, -1, 0)), ("calf_l", (1, 0, 0), 95, (0, 1, 0))],
    "crouch": [("thigh_l", (1, 0, 0), 105, (0, -1, 0)), ("thigh_r", (1, 0, 0), 105, (0, -1, 0)),
               ("calf_l", (1, 0, 0), 120, (0, 1, 0)), ("calf_r", (1, 0, 0), 120, (0, 1, 0))],
    "spread": [("thigh_l", (0, 1, 0), 35, (1, 0, 0)), ("thigh_r", (0, 1, 0), 35, (-1, 0, 0))],
}
POSES_HEAD = {
    "look_up": [("neck_01", (1, 0, 0), 14, (0, 1, 0)), ("Head", (1, 0, 0), 21, (0, 1, 0))],
    "look_down": [("neck_01", (1, 0, 0), 16, (0, -1, 0)), ("Head", (1, 0, 0), 24, (0, -1, 0))],
    "turn": [("neck_01", (0, 0, 1), 28, (1, 0, 0)), ("Head", (0, 0, 1), 42, (1, 0, 0))],
}
POSES_BY_SLOT = {
    "top": POSES_ARMS,
    "pauldrons": dict(POSES_ARMS, shrug=[("clavicle_l", (0, 1, 0), 20, (0, 0, 1)), ("clavicle_r", (0, 1, 0), 20, (0, 0, 1))]),
    "bottom": POSES_LEGS, "legwear": POSES_LEGS, "greaves": POSES_LEGS, "boots": POSES_LEGS,
    "head": POSES_HEAD,
}
POSES = POSES_BY_SLOT.get(SLOT, POSES_ARMS)


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


PUSH_ACC = {}


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
        # no shell vertex moves more than push_cap in all rounds (her skin points flag differently each round)
        acc = PUSH_ACC.setdefault(o.name, np.zeros(len(co)))
        mag = np.linalg.norm(dw, axis=1)
        sc = np.minimum(1.0, np.maximum(PUSH_CAP - acc, 0.0) / np.maximum(mag, 1e-12))
        dw = dw * sc[:, None]
        acc += mag * sc
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
# (a free mesh: at rest only unless params.pose_push. Its rigid plates don't bend in a pose, so her skin coming
# through one there is her own skin folding (an elbow, a shoulder): a rest-pose bump for it only dents the plate;
# the pose check below still counts it)
for rnd in range(PRM.get("push_rounds", 4)):
    defs = {}
    for pname, rots in [("rest", [])] + ([] if MESH and not PRM.get("pose_push") else list(POSES.items())):
        bv, bn, dg = pose_body(rots)
        r_ = skin_vs_shell(bv, bn, NEAR, tuck, shell_tree(dg))
        du = r_.get("deep_u", np.zeros(len(NEAR)))
        if rnd == 0:
            PUSH.setdefault("first_round_by_pose", {})[pname] = {
                "untucked": int(r_["through"].sum()), "tucked": int(r_["through_t"].sum()),
                "deepest_untucked_mm": round(float(du.max() * 1000), 2) if r_["through"].any() else 0.0,
                "deepest_tucked_mm": round(r_["deep_t"] * 1000, 2)}
        # (params.push_tucked_only: her skin as the game draws it, tucked, is what must stay under it: the untucked
        # skin under a deep tuck (tuck_under) is never drawn)
        if PRM.get("push_tucked_only"):
            for k in np.nonzero(r_["through_t"])[0]:
                i = int(NEAR[k])
                defs[i] = max(defs.get(i, 0.0), float(r_["deep_t_k"][k]))
            continue
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
PUSH["total_mm"] = round(max([a.max() for a in PUSH_ACC.values()], default=0) * 1000, 2)
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
# (params.rigid_drop, after the helpers' split too: the split eases her wrist's weights onto the hand, and rigid_again's
# mean put it back on the bracers (9%); each `_rigid` source's points lose those bones, the rest renormalized)
DROP_ = tuple(PRM.get("rigid_drop") or ())
if DROP_:
    nd_ = 0
    for o in made:
        if o.type != "MESH" or not o.get("source_part", "").endswith("_rigid"):
            continue
        gname_ = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            ws_ = [(gname_[g.group], g.weight) for g in v.groups if gname_[g.group] in names]
            keep_ = [(n_, w_) for n_, w_ in ws_ if not n_.startswith(DROP_)]
            t_ = sum(w_ for _, w_ in keep_)
            if len(keep_) == len(ws_) or t_ <= 1e-6:
                continue
            for n_, _ in ws_:
                o.vertex_groups[n_].remove([v.index])
            for n_, w_ in keep_:
                o.vertex_groups[n_].add([v.index], w_ / t_, "REPLACE")
            nd_ += 1
    stamp("rigid_drop %s: %d points of the rigid parts reweighted" % (list(DROP_), nd_))
# (armor 10: a style's rigid plates (`blend_group` on each part: a plate, its rolled edge, its rivets) back on ONE common
# blend after the helpers' split, the mean of all their points', so a plate and what is on it never part)
BLEND_GROUPS = {}
for o in made:
    if o.get("blend_group"):
        BLEND_GROUPS.setdefault(o["blend_group"], []).append(o)
for bg_, objs_ in BLEND_GROUPS.items():
    tot = {}
    for o in objs_:
        gname = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            for g in v.groups:
                if gname[g.group] in names:
                    tot[gname[g.group]] = tot.get(gname[g.group], 0.0) + g.weight
    keep_ = sorted(tot, key=tot.get, reverse=True)[:4]
    s_ = sum(tot[k] for k in keep_) or 1.0
    for o in objs_:
        for g in list(o.vertex_groups):
            if g.name in names and g.name not in keep_:
                o.vertex_groups.remove(g)
        set_one_blend(o, [(k, tot[k] / s_) for k in keep_])
if MESH:
    # (each `_rigid` source after the helpers' split: how many distinct blends its points carry (1: it never bends))
    # (a source's parts (its plate and its rivets, split by material) back on ONE common blend after the split, the
    # mean of all their points', so the rivets never drift off the plate)
    by_src = {}
    for o in made:
        if o.get("source_part", "").endswith("_rigid"):
            by_src.setdefault(o["source_part"], []).append(o)
    for sp_, objs_ in by_src.items():
        tot = {}
        for o in objs_:
            gname = {g.index: g.name for g in o.vertex_groups}
            for v in o.data.vertices:
                for g in v.groups:
                    if gname[g.group] in names:
                        tot[gname[g.group]] = tot.get(gname[g.group], 0.0) + g.weight
        keep_ = sorted(tot, key=tot.get, reverse=True)[:4]
        s_ = sum(tot[k] for k in keep_) or 1.0
        for o in objs_:
            set_one_blend(o, [(k, tot[k] / s_) for k in keep_])
            for g in list(o.vertex_groups):
                if g.name in names and g.name not in keep_:
                    o.vertex_groups.remove(g)
    bl_ = {}
    for o in made:
        if o.get("source_part", "").endswith("_rigid"):
            gname = {g.index: g.name for g in o.vertex_groups}
            for v in o.data.vertices:
                bl_.setdefault(o["source_part"], set()).add(tuple(sorted((gname[g.group], round(g.weight, 4)) for g in v.groups
                                                                         if g.weight > 1e-4 and gname[g.group] in names)))
    IMPORT["blends_per_rigid_part"] = {k: len(v) for k, v in sorted(bl_.items())}

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
NUM["envelope_with_rolled_edge_mm"] = envelope(B.get("envelope", B["shell"]) + [tb["obj"] for tn, tb in CAP["tubes"].items() if tn.startswith(ROLLS)])
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


if MESH:
    NUM["import"] = IMPORT       # (a free mesh: no cups, gore, band or straps to measure; its import numbers instead)
elif not TOP_PLATE:
    NUM.update(B["measure"]() if B.get("measure") else {})     # (another style measures its own places)
else:
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
    if tn.startswith(ROLLS):
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
NUM["triangles_by"]["cups_rolled_edge" if TOP_PLATE else "rolled_edges"] = sum(sum(len(p.vertices) - 2 for p in tb["obj"].data.polygons) for tn, tb in CAP["tubes"].items() if tn.startswith(ROLLS))
NUM["parts"] = len(made)
NUM["push_out"] = PUSH
NUM["band"] = None if not BAND else {"seam_z": [round(BAND["seam_z"][0], 4), round(BAND["seam_z"][1], 4)], "anchor_z": round(BAND["z_anc"], 4),
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


STRAP_SETS = strap_sets() if BAND else []     # (the plate top's band and straps only: b_design_spec (b))


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
        straps_ = strap_check(bv, bn, dg) if STRAP_SETS else None
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
# (params.graft false (the cuirass): no graft match. It adds her neck graft's weight change to whatever lies near her
# neck, and a rigid plate on one blend took it at 5512 points, bending at its neckline)
# (params.graft "leather" (the cuirass, r2): the graft on its leather meshes only (straps and band, which lie on her
# skin and took her skin's weights): without it the strap tops stood 8-14 mm off her shoulders in the combat clips)
_gr = PRM.get("graft", True)
if float(os.environ.get("NECK_CUT", "0.03")) and _gr:
    if _gr is True:
        heroine_neck.match_pieces(path, heroine_neck.field())
    else:
        heroine_neck.match_pieces(path, heroine_neck.field(), only=lambda n, k=str(_gr): k in n)
if STRAP_FRAMES:
    import strap_rows  # noqa: E402
    strap_rows.even(path, STRAP_FRAMES)
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


def tuck_rekey_shipped(fp):
    """(armor 10 c2: the body build's steps after her export (throat soften, nape, seam fair) move her neck's points in
    the shipped glb, and the outfit build rekeys its tucks to them (heroine_outfits.armor_tuck_rekey); a piece built
    here keyed its records on the blend's points, so the cuirass's 98 at her neck's base were on none of her vertices
    in the game. Each record whose point is not in her shipped glb goes to the nearest shipped point no blend point
    sits on (a moved point's new place), within 8 mm; else dropped.)"""
    import struct
    import heroine_neck as hn_
    G_ = hn_._Gl(os.path.join(ROOT, "godot", "art", "people", "heroine.glb"))
    post = np.unique(np.concatenate([np.round(G_.get(p_["attributes"]["POSITION"]).astype(np.float64) * 1e5).astype(np.int64)
                                     for m_ in G_.g["meshes"] for p_ in m_["primitives"]]), axis=0)
    me_ = body.data
    bp_ = np.empty(len(me_.vertices) * 3, np.float32)
    me_.vertices.foreach_get("co", bp_)
    bp_ = bp_.reshape(-1, 3)
    pre = np.unique(np.round(np.stack([bp_[:, 0], bp_[:, 2], -bp_[:, 1]], 1).astype(np.float64) * 1e5).astype(np.int64), axis=0)
    pset = set(map(tuple, post.tolist()))
    pre_set = set(map(tuple, pre.tolist()))
    newk = np.array([k for k in post.tolist() if tuple(k) not in pre_set], np.int64)
    d = open(fp, "rb").read()
    n = struct.unpack_from("<I", d, 0)[0]
    rec = np.frombuffer(d, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
    got, moved, dropped = {}, 0, 0
    tree_ = cKDTree(newk) if len(newk) else None
    for x, y, z, t in rec:
        k = (int(x), int(y), int(z))
        if k not in pset:
            dd, j = tree_.query(k) if tree_ is not None else (np.inf, -1)
            if dd > 800:
                dropped += 1
                continue
            k = tuple(int(v) for v in newk[j])
            moved += 1
        got[k] = max(got.get(k, 0.0), float(t))
    ks = sorted(got)
    new = np.zeros(len(ks), dtype=rec.dtype)
    if ks:
        arr = np.array(ks, np.int64)
        new["x"], new["y"], new["z"] = arr[:, 0], arr[:, 1], arr[:, 2]
        new["t"] = [got[k] for k in ks]
    with open(fp, "wb") as f_:
        f_.write(struct.pack("<I", len(ks)) + new.tobytes())
    global TUCK_N
    TUCK_N = len(ks)
    NUM["tuck_rekey"] = {"records": int(n), "moved": moved, "dropped": dropped, "written": len(ks)}
    print("TUCK REKEY %s: %d records, %d off her shipped points moved to them, %d dropped, %d written" % (PID, n, moved, dropped, len(ks)))


tuck_rekey_shipped(os.path.join(ART, "armor_tuck", f"{PID}.bin"))
NUM["meshes"] = sorted(ranks)

# sockets, rims, the UV surface
sockets = {"id": PID, "slot": SLOT, "body_hash": BODY_HASH, "space": "glTF / Godot: Y up, metres, her bind pose",
           "sockets": B["sockets"], "rims": B["rims"],
           "fixings": [gl(p_).round(5).tolist() for p_ in B.get("avoid", [])],
           "adorn": [dict({k: v for k, v in a_.items() if k not in ("points", "normals")}, points=gl(a_["points"]).round(5).tolist(),
                          normals=gl(a_["normals"]).round(4).tolist()) for a_ in ADORN_REC],
           "uv_surface": {"mesh": f"{PID}.{SLOT}.{MKEY}", "layer": "UVMap (TEXCOORD_0)",
                          "units": "metres x the material's repeats (outfit_materials.json), one projection along the cup's facing"},
           "trim_uv": {"layer": "trim (TEXCOORD_2)", "atlas": "res://art/armor/trim_strip.png", "on": sorted(t for t in CAP["tubes"] if t.startswith(ROLLS)),
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
# (armor 9, the rigid-piece rule: a rigid piece is never bent by the garment tuck (Rpg/GarmentTuck.cs Over, HerWear,
# wearcheck --garment-tuck). A plate style is rigid; a free mesh is when every part of it is `_rigid`.)
# (rigid only when the piece says so, piece.json "rigid": true (B's cuirass, cuisses), or a free mesh made only of
# _rigid parts: the plate tops are cups on leather straps that must still lie under the pauldrons, armor 9)
if SPEC_PIECE.get("rigid") is True or (MESH and IMPORT.get("rigid")):
    row["rigid"] = True
if SPEC_PIECE.get("replaces"):
    row["replaces"] = SPEC_PIECE["replaces"]         # (a calling row id: ArmorIndex.Calling wears this piece in its place)
if SPEC_PIECE.get("cover_grow"):
    row["cover_grow"] = SPEC_PIECE["cover_grow"]     # (tools/armor/cover.py: the cover carried on past its edge, b2r3)
if MESH:
    row["source"] = "mesh"
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
