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
_finish, _tube = G["finish"], G["tube"]


def finish_cap(name, pos, wt, tris, mkey, thick, bevel, budget=3000, scraps=True):
    if name not in CAP["sheet"]:
        CAP["sheet"][name] = (np.array(pos, float), np.array(wt, float), np.array(tris), thick)
    return _finish(name, pos, wt, tris, mkey, thick, bevel, budget, scraps)


def tube_cap(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed=True, nv=12):
    o = _tube(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed, nv)
    CAP["tubes"][name] = dict(curve=np.array(curve, float), nrm=np.array(nrm, float), outward=np.array(outward, float),
                              width=float(np.max(width)), height=float(np.max(height)), overhang=float(np.max(overhang)),
                              thick=float(np.max(thick)), closed=closed, obj=o)
    return o


G["finish"], G["tube"] = finish_cap, tube_cap


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


def build_plate_top():
    nip = G["NIPPLE"]
    roll = PRM.get("roll", {"width": 0.005, "height": 0.0009})
    lift, thick = PRM.get("lift", 0.002), PRM.get("thick", 0.003)
    top_line = G["plunge_line"](PRM.get("over", 0.03), PRM.get("low", 0.03), PRM.get("wing", 0.022))
    cname = f"{PID}.cups"
    # (the rolled edge is the shell's: bind_edges' rolled binding, in the shell's own metal)
    cups = G["plate_cups"](cname, MKEY, top_line, lift=lift, thick=thick, trim=(MKEY, roll["width"], roll["height"], thick),
                           studs=None, gap=PRM.get("gap", 0.011), side=PRM.get("side", 0.07))
    sheet_pos, sheet_wt, sheet_tris, _ = CAP["sheet"][cname]
    CUP_PEAK, CUP_LOW = G["CUP_PEAK"], G["CUP_LOW"]
    back_z = G["UNDERBUST"] + PRM.get("back_rise", 0.035)
    arms = G["ARMW"]["l"] + G["ARMW"]["r"]
    sw = PRM.get("strap_width", 0.018)
    straps, strap_lines = [], {}
    for sd, sg in (("l", 1), ("r", -1)):
        pk = CUP_PEAK[sd]
        tp = G["front_point"](pk[0] - sg * 0.004, pk[2] - 0.012)
        cv = [tp, np.array([sg * 0.11, 0.03, 1.565]), np.array([sg * 0.1, 0.11, 1.47]), np.array([sg * 0.085, 0.125, back_z])]
        strap_lines[sd] = cv
        straps.append((sd, cv))
    strap_objs = {sd: G["ribbon"](f"{PID}.strap_{sd}", cv, sw, "darkleather", thick=0.003, centre=(0.0, 0.0, 1.33)) for sd, cv in straps}
    allstraps = [o for v_ in strap_objs.values() for o in v_]
    backstrap = G["girdle"](f"{PID}.backstrap", lambda a_: np.full_like(a_, back_z), PRM.get("back_width", 0.022), "darkleather",
                            lift=0.003, thick=0.003, arc=(1.48, 2 * np.pi - 1.48), mask=arms < 0.3)
    fix = G["studs_on"](f"{PID}.strap_rivets", allstraps + backstrap,
                        [((sg * 0.085, 0.7, back_z + 0.003), (sg * 0.085, 0.0, back_z + 0.003)) for sg in (1, -1)]
                        + [((sg * 0.7 * np.sin(1.53), -0.7 * np.cos(1.53), back_z), (0.0, 0.0, back_z)) for sg in (1, -1)], MKEY, r=0.003)
    for o in fix:
        o["rigid_part"] = True
    # Each shoulder strap's buckle, on its front run, 45% of the way from the cup to her shoulder.
    bk = PRM.get("buckle", {"t": 0.45, "w": 0.027, "h": 0.021, "r": 0.0016})
    buckles, bsock = [], {}
    for sd, cv in straps:
        m, s_ = strap_buckle(f"{PID}.buckle_{sd}", strap_objs[sd], np.asarray(cv[0]), np.asarray(cv[1]), bk["t"], bk["w"], bk["h"], bk["r"])
        buckles += m
        bsock[sd] = s_
    # The gore: a plain forged bridge plate joining the cups at their lowest inner corners, held by a rivet each side.
    gz = CUP_LOW[2] + 0.004
    gpts = np.array([[x, 0.0, gz] for x in np.linspace(-abs(CUP_LOW[0]) - 0.006, abs(CUP_LOW[0]) + 0.006, 7)])
    for i, q in enumerate(gpts):
        gpts[i] = G["front_point"](q[0], q[2])
    gore = G["ribbon"](f"{PID}.gore", list(gpts), PRM.get("gore_width", 0.016), MKEY, lift=0.0045, thick=0.0025,
                       centre=(0.0, 0.0, gz))
    gc = np.array(G["front_point"](0.0, gz))
    gn = np.array(G["SKIN_BVH"].find_nearest(Vector(gc))[1][:])
    gore_rivets = G["studs_on"](f"{PID}.gore_rivets", gore,
                                [((sg * (abs(CUP_LOW[0]) + 0.001), -0.6, gz), (sg * (abs(CUP_LOW[0]) + 0.001), 0.0, gz)) for sg in (1, -1)], MKEY, r=0.0026)
    for o in gore_rivets:
        o["rigid_part"] = True
    shell = [cups[0]]
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

    for sd in "lr":
        q = nip[sd]
        nn = np.array(G["SKIN_BVH"].find_nearest(Vector(q))[1][:])
        h = cbvh.ray_cast(Vector(q + nn * 0.0005), Vector(nn), 0.05)
        p_ = np.array(h[0][:]) if h[0] is not None else q + nn * 0.01
        n_ = np.array(h[1][:]) if h[0] is not None else nn
        if n_ @ nn < 0:
            n_ = -n_
        sock(f"cup_{sd}", p_, n_, [0, 0, 1.0], G["soft_weights"](p_[None])[0])
        pk = CUP_PEAK[sd]
        sock(f"strap_{sd}", pk, G["SKIN_BVH"].find_nearest(Vector(pk))[1][:], np.asarray(strap_lines[sd][1]) - pk, G["soft_weights"](pk[None])[0])
        bs = bsock[sd]
        sock(f"buckle_{sd}", bs["point"], bs["normal"], bs["up"], bs["weights"])
        sh = np.asarray(strap_lines[sd][1])
        sock(f"shoulder_{sd}", sh, G["SKIN_BVH"].find_nearest(Vector(sh))[1][:], [0, 1.0, 0], G["soft_weights"](sh[None])[0])
    sock("gore", gc + gn * 0.007, gn, [0, 0, 1.0], G["soft_weights"](gc[None])[0])
    bc = np.array([0.0, 0.0, back_z])
    hb = G["SKIN_BVH"].ray_cast(Vector((0.0, 0.5, back_z)), Vector((0, -1.0, 0)), 1.0)
    if hb[0] is not None:
        bc = np.array(hb[0][:]) + np.array([0, 0.006, 0])
    sock("back", bc, [0, 1.0, 0], [0, 0, 1.0], G["soft_weights"](bc[None])[0])
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
    return dict(parts=parts, shell=shell, sheet=(sheet_pos, sheet_wt, sheet_tris), thick=thick, lift=lift, sockets=socks, rims=rims,
                roll=roll)


STYLES = {("top", "plate"): build_plate_top}
stamp("building %s (%s/%s)" % (PID, SLOT, SPEC_PIECE["style"]))
B = STYLES[(SLOT, SPEC_PIECE["style"])]()
G["finish"], G["tube"] = _finish, _tube

# ------------------------------------------------------------ adornment --
adorn_made = []
sheet_pos, sheet_wt, sheet_tris = B["sheet"]
for ad in SPEC_PIECE.get("adorn", []):
    if ad["kind"] == "row" and ad.get("mesh", "rivet") == "rivet":
        dist, _ = rim_field(sheet_pos, sheet_tris)
        nor = G["vertex_normals"](sheet_pos, sheet_tris)
        at = np.hstack([nor, sheet_wt, dist[:, None]])
        rv = G["rivets"](f"{PID}.{ad.get('rim', 'rim')}", sheet_pos, at, sheet_tris, B["thick"], ad.get("mat", MKEY),
                         spacing=ad.get("spacing", 0.028), inset=ad.get("inset", 0.011), r=ad.get("r", 0.0032))
        for o in rv:
            o["hides"] = False
            o["rigid_part"] = True
        adorn_made += rv
    else:
        raise NotImplementedError("adornment %s (item 3b)" % ad)
made = B["parts"] + adorn_made
for o in made:
    if "hides" not in o.keys():
        o["hides"] = False
stamp("piece made: %d parts" % len(made))
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
stamp("tuck: %d of her vertices under it" % hid)
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


def mesh_world(objs):
    vs, fs, owner = [], [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
        owner += [o.name] * len(o.data.polygons)
    return np.array(vs), fs, owner


sv, sf, _ = mesh_world(B["shell"])
shell_bvh = BVHTree.FromPolygons([tuple(p) for p in sv], sf)
# (the shell's envelope: how far its outer face stands off her filled skin: L1 at most 6 mm)
filled_bvh = BVHTree.FromPolygons([tuple(p) for p in G["P_FILLED"]], G["TRI"].tolist())
env = np.array([np.linalg.norm(np.array(filled_bvh.find_nearest(Vector(q))[0][:]) - q) for q in sv])
NUM["envelope_mm"] = {"max": round(float(env.max() * 1000), 2), "p99": round(float(np.percentile(env, 99) * 1000), 2),
                      "p50": round(float(np.median(env) * 1000), 2)}
# Her skin against the shell, at her body's own points (the game's, after the steps above), at rest and posed.
# Covered: a ray out along her normal meets the shell's inner face within 30 mm (gap = that distance). Through:
# no ray out meets it, but one back in does within 12 mm (her skin stands outside the shell). Each counted with her
# skin as drawn (untucked) and tucked as the game draws it (10 mm times the tuck, full past 0.973).
SHELL = B["shell"]


def skin_vs_shell(bv, bn, idx, tuck_v, tree):
    out = {"covered": np.zeros(len(idx), bool), "gap": np.full(len(idx), np.nan), "through": np.zeros(len(idx), bool),
           "through_t": np.zeros(len(idx), bool), "deep_t": 0.0, "cov_t": np.zeros(len(idx), bool)}
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
            else:
                out["cov_t"][k] = f_[0] is not None
                out["through_t"][k] = f_[0] is None and b_[0] is not None
                if out["through_t"][k]:
                    out["deep_t"] = max(out["deep_t"], b_[3])
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


bv0 = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
bn0 = np.array([(body.matrix_world.to_3x3() @ v.normal)[:] for v in me.vertices])
lo, hi = sv.min(0) - 0.03, sv.max(0) + 0.03
NEAR = np.nonzero(((bv0 > lo) & (bv0 < hi)).all(1))[0]
R0 = skin_vs_shell(bv0, bn0, NEAR, tuck, shell_tree())
COV = NEAR[R0["covered"]]
g_ = R0["gap"][R0["covered"]]
NUM["rest"] = {"skin_points_near": int(len(NEAR)), "covered": int(len(COV)),
               "gap_mm": {"max": round(float(g_.max() * 1000), 2), "p99": round(float(np.percentile(g_, 99) * 1000), 2),
                          "p50": round(float(np.median(g_) * 1000), 2)},
               "through_untucked": int(R0["through"].sum()), "through_tucked": int(R0["through_t"].sum()),
               "tucked_not_covered": int(((tuck[NEAR] > 0.5) & ~R0["covered"]).sum())}
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
NUM["parts"] = len(made)


# (her skin through the shell in test poses: arms overhead, one arm across her, both arms back, a hug, a twist and bend)
def pose_check():
    pb = arm.pose.bones
    from mathutils import Quaternion
    arm.data.pose_position = "POSE"

    def rot(bone, axis, deg):
        b = arm.data.bones[bone]
        R = b.matrix_local.to_3x3()
        qw = Quaternion(Vector(axis), np.radians(deg))
        ql = (R.inverted() @ qw.to_matrix() @ R).to_quaternion()
        pb[bone].rotation_mode = "QUATERNION"
        pb[bone].rotation_quaternion = ql @ pb[bone].rotation_quaternion

    def side(bone, axis, deg, want):
        b = arm.data.bones[bone]
        d = np.array((b.tail_local - b.head_local)[:])
        d2 = np.array((Quaternion(Vector(axis), np.radians(deg)).to_matrix() @ Vector(d))[:])
        return deg if (d2 - d) @ np.asarray(want, float) > 0 else -deg

    poses = {
        "arms_overhead": [("upperarm_l", (0, 1, 0), 130, (0, 0, 1)), ("upperarm_r", (0, 1, 0), 130, (0, 0, 1))],
        "reach_across_r": [("upperarm_r", (0, 0, 1), 80, (1, -1, 0)), ("lowerarm_r", (0, 0, 1), 60, (1, -1, 0))],
        "arms_back": [("upperarm_l", (0, 0, 1), 40, (0, 1, 0)), ("upperarm_r", (0, 0, 1), 40, (0, 1, 0))],
        "hug": [("upperarm_l", (0, 0, 1), 70, (0, -1, 0)), ("upperarm_r", (0, 0, 1), 70, (0, -1, 0))],
        "twist_bend": [("spine_02", (1, 0, 0), 20, (0, -1, 0)), ("spine_03", (0, 0, 1), 25, (1, 0, 0))],
    }
    out = {}
    for pname, rots in poses.items():
        for b in pb:
            b.rotation_mode = "QUATERNION"
            b.rotation_quaternion = (1, 0, 0, 0)
        for bone, axis, deg, want in rots:
            if bone in pb:
                rot(bone, axis, side(bone, axis, deg, want))
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        be = body.evaluated_get(dg)
        m_ = be.to_mesh()
        bv = np.array([(body.matrix_world @ v.co)[:] for v in m_.vertices])
        bn = np.array([(body.matrix_world.to_3x3() @ v.normal)[:] for v in m_.vertices])
        be.to_mesh_clear()
        r_ = skin_vs_shell(bv, bn, COV, tuck, shell_tree(dg))
        moved = float(np.abs(bv[COV] - bv0[COV]).max())
        out[pname] = {"skin_moved_mm": round(moved * 1000, 1), "covered_at_rest": int(len(COV)),
                      "through_untucked": int(r_["through"].sum()), "through_tucked": int(r_["through_t"].sum()),
                      "worst_tucked_mm": round(r_["deep_t"] * 1000, 2), "no_longer_covered": int((~r_["covered"]).sum()),
                      "no_longer_covered_tucked_full": int((~r_["covered"] & (tuck[COV] > 0.973)).sum())}
    for b in pb:
        b.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    return out


try:
    NUM["poses"] = pose_check()
except Exception as ex:  # (the numbers still come; the pose check names its failure)
    import traceback
    traceback.print_exc()
    NUM["poses"] = {"error": repr(ex)}
stamp("numbers measured")

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
row = {"id": PID, "outfit": PID, "slot": SLOT, "layer": amap["layers"][SLOT], "covers": SPEC_PIECE.get("covers", [SLOT]),
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
