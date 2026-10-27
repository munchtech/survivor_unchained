"""The heroine's outfits, one for each calling, cut from her own body.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- <out dir>/x [--body <heroine.glb>] [--only warden]

Each outfit is written as <out dir>/heroine_outfit_<name>.gltf (and .bin), the
textures in <out dir>/outfit_tex.

With --body her body is written again, marked where each outfit hides her.

The scene is the one heroine_head.py saved, so every piece is exported
from the very skeleton her body was and binds to hers exactly.

A piece is a region of her skin, bounded by a smooth curve: each region is
a field over her surface (positive inside, roughly in metres), and the
surface is cut where the field crosses zero, between vertices, so an edge
runs clean across the triangles instead of stepping along them. The piece
is then lifted off the skin, given a thickness and a rounded edge, and
keeps her weights (her springs included), so it moves as she does. Plate
is smoothed first, so it bridges the grooves of her muscles as metal would,
and then held clear of the skin everywhere.

The front of the crotch is always covered; how much of the seat is bare is
each outfit's own.
"""
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy import sparse
import scipy.sparse.csgraph
from scipy.spatial import cKDTree

# (s28, the owner's glove pick: ARC_GLOVE names the Arcanist glove's knobs as a set, each only a default
# (an explicit env still wins). G3 = the owner's pick (14 Oct): B1's ivory fingerless satin, a plum-piped top
# with a soft point over the back of her elbow and a dip at her inner elbow, a piped knuckle V; G3L/G3L2 its
# louder tops (a deeper point, a wider plum binding at the top only); B1 = plain white satin, as before s24.)
_G3 = {"GLOVE_STYLE": "G1", "GLOVE_LOOP": "0,0,0,0", "GLOVE_POINTS": "0,0,0,0,0", "FL_DORS": "0.006,0.014",
       "FL_THUMB_BLEND": "0.3,0.7", "GLOVE_IVORY": "1.789,1.470,1.142,223", "GLOVE_PIPE_MAT": "0.75,0.44,0.72,70,0.25",
       "GLOVE_EDGE_EASE": "0.010,0.005,0.003,0.010", "GLOVE_EDGE_EASE_IDX": "0.005,0.1,0.4"}
ARC_GLOVE_SETS = {"B1": {}, "G3": _G3,
                  "G3L": dict(_G3, ARC_GLOVE_POINT="0.034", ARC_GLOVE_POINT_W="46", GLOVE_PIPE_TOP="0.005,0.001,0.0022"),
                  "G3L2": dict(_G3, ARC_GLOVE_POINT="0.044", ARC_GLOVE_POINT_W="52", GLOVE_CROOK="0.012", GLOVE_PIPE_TOP="0.007,0.0014,0.003")}
ARC_GLOVE = os.environ.get("ARC_GLOVE", "G3L2")
for k_, v_ in ARC_GLOVE_SETS[ARC_GLOVE].items():
    os.environ.setdefault(k_, v_)

# Progress shown as it happens (Blender holds output back otherwise).
sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
ONLY = ARGS[ARGS.index("--only") + 1] if "--only" in ARGS else None
BODY_OUT = ARGS[ARGS.index("--body") + 1] if "--body" in ARGS else None
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit")
# Her boots, made as a bootmaker makes them (heroine_boots.py, on this
# script's helpers: it reads them from here when it is called).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_boots as BOOTS
BOOTS.bind(globals())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_rig as rig_helpers  # noqa: E402  (her helper bones, added just before export)
# Her upper arm's twist chain (tools/anim/helpers.py SPEC "twist_chain", Body 5 A2): upperarm_twist_02-_04 built into
# her and split onto her body and every piece. Off by default until the chain's rebuild (correctives and post steps
# re-solved on its weights) is judged; TWIST_CHAIN=1 builds it.
TWIST_CHAIN = os.environ.get("TWIST_CHAIN", "0") == "1"

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = bpy.data.objects["Heroine"]
# Her head is a mesh of its own (heroine_head.py), with its parts and her
# hairstyles beside it.
HEAD = bpy.data.objects.get("HeroineHead")
HEAD_PARTS = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm and o.name.startswith("Heroine") and o != body]
# (her brows are in her face's paint once heroine_face.py has painted it: their
# cards, kept for that painting, are not the game's, as heroine_head.py has it)
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "face_paint.png")):
    HEAD_PARTS = [o for o in HEAD_PARTS if o.name != "HeroineBrows"]
HAIR_DEFAULT = bpy.data.objects.get("hair_long")
BONES = [b.name for b in arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}

# ------------------------------------------------------------ her mending --
# Three flaws in the body heroine_head.py saves, mended before anything reads
# her (her vertices stay as they are, so every map by vertex still holds):
# a fin, a sliver standing off an edge three faces share (under her left
# breast, at the back of her pelvis), and a pocket, a sliver lying back to
# back with half of a graft quad at her left armpit (the speck there). Found
# by position, her seams splitting her vertices.
def mend_body(me):
    import collections
    import itertools
    mb = bmesh.new()
    mb.from_mesh(me)
    mb.faces.ensure_lookup_table()
    mb.normal_update()
    key = [tuple(round(c, 5) for c in v.co) for v in mb.verts]
    use = collections.Counter()
    for f in mb.faces:
        ks = [key[v.index] for v in f.verts]
        use.update(frozenset(e) for e in zip(ks, ks[1:] + ks[:1]))
    fins, pockets, mends = [], [], []
    for f in mb.faces:
        ks = [key[v.index] for v in f.verts]
        n = [use[frozenset(e)] for e in zip(ks, ks[1:] + ks[:1])]
        if len(ks) == 3 and n.count(1) >= 2 and max(n) > 2:
            fins.append(f)
    by3 = collections.defaultdict(list)
    for f in mb.faces:
        for c in itertools.combinations([key[v.index] for v in f.verts], 3):
            by3[frozenset(c)].append(f)
    for f in mb.faces:
        if len(f.verts) != 3:
            continue
        for g in by3[frozenset(key[v.index] for v in f.verts)]:
            if g is not f and len(g.verts) == 4 and f.normal.dot(g.normal) < 0:
                tri = set(key[v.index] for v in f.verts)
                inner = [l for l in g.loops if all(key[v.index] in tri for v in (l.link_loop_prev.vert, l.vert, l.link_loop_next.vert))]
                if len(inner) == 1:
                    pockets.append(f)
                    mends.append((g, inner[0]))
    uv = mb.loops.layers.uv
    for g, drop in mends:
        keep = [l for l in g.loops if l is not drop]
        h = mb.faces.new([l.vert for l in keep], g)
        for lo, li in zip(h.loops, keep):
            for lay in uv.values():
                lo[lay].uv = li[lay].uv
    bmesh.ops.delete(mb, geom=fins + pockets + [g for g, _ in mends], context="FACES_ONLY")
    mb.to_mesh(me)
    me.update()
    mb.free()
    print("MEND her body: %d fins, %d pockets" % (len(fins), len(pockets)))



# A hole in her right inner thigh just under the crotch, on her midline: a
# ring of 7 open edges (4.4 x 2.8 cm) round a loose triangle. build_heroine's
# crotch step gave three points of her right thigh's inner face, 0.1 mm past
# the midline, to her left leg by the sign of x, and its web cut then took
# the 10 triangles joining them to the right leg. At rest her left thigh hid
# it; with her legs apart the inside of her thigh showed through (the grey
# spots from below in the vault and death: animation, judge 10, found by a
# solver's ray cast). Filled (faces only, so every map by vertex still holds),
# facing out as the rim does, the loose points given the rim's weights.
def mend_hole(obj):
    import collections
    me = obj.data
    mb = bmesh.new()
    mb.from_mesh(me)
    mb.verts.ensure_lookup_table()
    key = [tuple(round(c, 5) for c in v.co) for v in mb.verts]
    use = collections.Counter()
    for f in mb.faces:
        ks = [key[v.index] for v in f.verts]
        use.update(frozenset(e) for e in zip(ks, ks[1:] + ks[:1]))
    at = Vector((0.0, 0.009, 0.866))
    edges = [e for e in mb.edges if use[frozenset((key[e.verts[0].index], key[e.verts[1].index]))] == 1
             and abs((e.verts[0].co + e.verts[1].co).x / 2) < 0.01 and ((e.verts[0].co + e.verts[1].co) / 2 - at).length < 0.05]
    if len(edges) != 10:
        print("MEND her thigh hole: NOT FOUND (%d open edges there, 10 wanted); left as it is" % len(edges))
        mb.free()
        return
    island = {v for e in edges for v in e.verts if len(e.link_faces) == 1 and len(e.link_faces[0].verts) == 3
              and all(len(x.link_faces) == 1 for x in e.link_faces[0].edges)}
    rim = {v for e in edges for v in e.verts} - island
    made = bmesh.ops.triangle_fill(mb, use_beauty=True, use_dissolve=False, edges=edges)["geom"]
    new = [g for g in made if isinstance(g, bmesh.types.BMFace)]
    # (the loose triangle is a face already: a fill over it is dropped)
    dup = [f for f in new if set(f.verts) <= island]
    if dup:
        bmesh.ops.delete(mb, geom=dup, context="FACES_ONLY")
        new = [f for f in new if f not in dup]
    mb.normal_update()
    turn = [f for f in new if f.normal.x < 0]
    if turn:
        bmesh.ops.reverse_faces(mb, faces=turn)
    uv = mb.loops.layers.uv
    old = next(f for v in rim for f in v.link_faces if f not in new)
    for f in new:
        f.material_index = old.material_index
        f.smooth = old.smooth
        for lo in f.loops:
            src = next((l for l in lo.vert.link_loops if l.face not in new), None)
            if src is not None:
                for lay in uv.values():
                    lo[lay].uv = src[lay].uv
    dl = mb.verts.layers.deform.verify()
    mean = collections.Counter()
    for v in rim:
        for g, w in v[dl].items():
            mean[g] += w / len(rim)
    for v in island:
        v[dl].clear()
        for g, w in mean.items():
            if w > 0.01:
                v[dl][g] = w
    mb.to_mesh(me)
    me.update()
    mb.free()
    names = {g.index: g.name for g in obj.vertex_groups}
    print("MEND her thigh hole: %d faces filled (%d turned), %d loose points given %s"
          % (len(new), len(turn), len(island), {names[g]: round(w, 3) for g, w in mean.items() if w > 0.01}))


mend_body(body.data)
mend_hole(body)


# Faces of hers folded over at rest (a corner pushed past the edge across
# from it, so the face lies turned against every face round it: 46 on her
# body, 2.7 cm2, the largest 0.36 cm2 on her right inner thigh), and corners
# whose normal is turned away from the skin round them. Mended on her body
# only, just before it is written (after every outfit has read her, so no
# piece cut from her moves: mended first, the warden's cups took 76 rivets
# for 34 and the build broke). Each folded face's corners are drawn to the
# middle of the points round them (her seams moved as one) until no face is
# folded; turning the faces round instead left them lying over their
# neighbours, dark marks at her left flank and breast (animation, judge 10).
# Then every corner moved, and every corner more than 60 degrees from the
# skin round it, takes the mean of its neighbours' own normals: the normals
# drawn round it, so no mark (an average of face normals was up to 70
# degrees off where the faces are slivers). Her hands are never moved: their
# folds are the creases between the fingers and the thumb's tip, and drawn
# in they left a glint on the thumb tip and a speck in the palm (judge 11);
# their corners still take their neighbours' normals.
HAND_BONES = ("hand_", "thumb_", "index_", "middle_", "ring_", "pinky_")


def _folded(mb, weld, nw):
    A = np.zeros((nw, 3))
    fn = [f.normal * f.calc_area() for f in mb.faces]
    for f, n in zip(mb.faces, fn):
        for v in f.verts:
            A[weld[v.index]] += n
    out = []
    for f, n in zip(mb.faces, fn):
        a = n.length
        if a < 1e-14:
            continue
        ds = []
        for v in f.verts:
            o = A[weld[v.index]] - np.array(n)
            lo = np.linalg.norm(o)
            if lo > 1e-14:
                ds.append(float(o @ np.array(n)) / (lo * a))
        if ds and np.mean(ds) < -0.5:
            out.append(f)
    return out


def mend_folds(me, obj=None, free=None, normals=True):
    nl = len(me.loops)
    cn = np.empty(nl * 3, np.float32)
    me.corner_normals.foreach_get("vector", cn)
    cn = cn.reshape(-1, 3).astype(float)
    # (s26: her chest's fitted normals, heroine_chest.py, enter here as this pass's own, so the fold check
    # below still mends any corner of theirs that turned over, and every corner is stored once, as in F0:
    # set twice, the rounding changed and the export welded 2 copies)
    _hc = sys.modules.get("heroine_chest")
    if normals and obj is not None and _hc is not None and getattr(_hc, "CN_OVERRIDE", None) is not None:
        _sel, _nv = _hc.CN_OVERRIDE
        if len(cn) == nl:
            cn[_sel] = _nv
        _hc.CN_OVERRIDE = None
    lv = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", lv)
    mb = bmesh.new()
    mb.from_mesh(me)
    mb.verts.ensure_lookup_table()
    key = {}
    weld = np.array([key.setdefault(tuple(round(c, 5) for c in v.co), len(key)) for v in mb.verts])
    copies = [[] for _ in key]
    for v in mb.verts:
        copies[weld[v.index]].append(v)
    ring = [set() for _ in key]
    for e in mb.edges:
        a, b = weld[e.verts[0].index], weld[e.verts[1].index]
        if a != b:
            ring[a].add(b)
            ring[b].add(a)
    still = set()
    if obj is not None:
        hand = {g.index for g in obj.vertex_groups if g.name.startswith(HAND_BONES)}
        for v in me.vertices:
            if sum(g.weight for g in v.groups if g.group in hand) > 0.3:
                still.add(weld[v.index])
    moved, first = set(), None
    for it in range(12):
        mb.normal_update()
        bad = _folded(mb, weld, len(key))
        if first is None:
            first = len(bad)
        move = {weld[v.index] for f in bad for v in f.verts if free is None or free(v.co)} - still
        if not move:
            break
        new = {k: sum((copies[r][0].co for r in ring[k]), Vector()) / max(len(ring[k]), 1) for k in move}
        for k, p in new.items():
            for v in copies[k]:
                v.co = p
        moved |= move
    mb.normal_update()
    left = len(_folded(mb, weld, len(key)))
    mb.to_mesh(me)
    me.update()
    mb.free()
    if not normals:
        print("MEND her folds (before cutting): %d folded, %d left, %d points moved" % (first, left, len(moved)))
        return
    # each corner against the mean normal of the corners at the places round it
    lw = weld[lv]
    S = np.zeros((len(key), 3))
    np.add.at(S, lw, cn)
    R = np.zeros((len(key), 3))
    for k, rk in enumerate(ring):
        for r in rk:
            R[k] += S[r]
    Rn = R / np.maximum(np.linalg.norm(R, axis=1, keepdims=True), 1e-12)
    target = np.isin(lw, list(moved)) | ((cn * Rn[lw]).sum(1) < 0.5)
    S2 = np.zeros((len(key), 3))
    np.add.at(S2, lw[~target], cn[~target])
    R2 = S2.copy()
    for k, rk in enumerate(ring):
        for r in rk:
            R2[k] += S2[r]
    out = cn.copy()
    ok = np.linalg.norm(R2[lw], axis=1) > 1e-9
    out[target & ok] = R2[lw[target & ok]] / np.linalg.norm(R2[lw[target & ok]], axis=1, keepdims=True)
    me.normals_split_custom_set([tuple(v) for v in out])
    print("MEND her folds: %d folded, %d left after %d passes (%d hand points kept), %d points moved; %d corners given their neighbours' normal"
          % (first, left, it + 1, len(still), len(moved), int((target & ok).sum())))

# Her folds mended before her pieces are cut from her (and again at export,
# for her normals): cut from the unmended surface, the Arcanist's suit kept
# the pinched fold at her upper-outer left breast that the mend took out of
# her skin (animation's judge 11, B2; judge 6).
# OFF by default (MEND_PRECUT=1): it broke the Warden's plate cups (they ran
# together across her cleavage and lost a binding, h4), and still did with
# only positions off her cleavage mended. B2 wants another way.
if os.environ.get("MEND_PRECUT", "0") == "1":
    mend_folds(body.data, body, free=lambda co: abs(co.x) > 0.05, normals=False)

# (s20, the owner 14 Oct: "they definitely aren't sexy female hands ... more
# delicate hands". Her bare hand ran 226 mm wrist to fingertip (12.1% of her
# 1.865 m; a woman's is 10-11%), its palm 100 mm across and its fingers 19-24 mm
# thick at the middle joint (a woman's 15-17). HAND_SLIM=k: each finger drawn
# in toward its bones by k (tapering a further HAND_TAPER to the tip), her palm
# by HAND_PALM across and through, nothing at her wrist; lengths and bones as
# they were, so every clip and grip still holds. Off at 1.0.)
# (s21, the owner 14 Oct: "we should fix it now". On by default: HAND_SCALE
# shortens her whole hand about her wrist, bones and skin together, to 11% of
# her height (227 mm -> 205); clips key her fingers' rotations only, so every
# clip still plays, and grips re-fit. Her forearm is untouched (it eases in by
# her hand's own weights at her wrist).)
# (the owner, on 0.90: "the hands went slightly too small": 0.93, about 211 mm,
# 11.3% of her height, slimmed a touch softer, the tips not pointed)
HAND_SLIM = float(os.environ.get("HAND_SLIM", "0.88"))
HAND_TAPER = float(os.environ.get("HAND_TAPER", "0.03"))
HAND_PALM = float(os.environ.get("HAND_PALM", "0.97"))
HAND_SCALE = float(os.environ.get("HAND_SCALE", "0.93"))
HEAD_SCALE = float(os.environ.get("HEAD_SCALE", "1.07"))   # (heroine_headscale.py: the last step of her export)
# (s21, the owner 14 Oct, the audit: her forearm ran 215 mm elbow to wrist,
# 0.116 of her height (a woman's 0.146): FOREARM_ADD lengthens it, her hand
# carried out along it and her forearm's skin stretched evenly from her elbow
# (nothing at her elbow, all of it at her wrist), its bones with it.)
FOREARM_ADD = float(os.environ.get("FOREARM_ADD", "0.05"))


def forearm_bones(sd):
    """Her forearm's bone and every bone under it (her hand, fingers, twists)."""
    root = arm.data.bones.get(f"lowerarm_{sd}")
    if root is None:
        return []
    return [root.name] + [c.name for c in root.children_recursive]


def hand_slimmed(obj):
    me = obj.data
    inv = obj.matrix_world.inverted()
    loc = lambda v: np.array((inv @ (arm.matrix_world @ v))[:])
    bh = lambda n: loc(arm.data.bones[n].head_local)
    bt = lambda n: loc(arm.data.bones[n].tail_local)
    co = np.array([v.co[:] for v in me.vertices])
    gi = {g.name: g.index for g in obj.vertex_groups}
    def wts(names):
        idx = {gi[n] for n in names if n in gi}
        w = np.zeros(len(co))
        for v in me.vertices:
            for g in v.groups:
                if g.group in idx:
                    w[v.index] += g.weight
        return np.clip(w, 0, 1)
    out = co.copy()
    moved = 0.0
    for sd in "lr":
        if f"hand_{sd}" not in arm.data.bones:
            continue
        for fg in ("thumb", "index", "middle", "ring", "pinky"):
            bs = [f"{fg}_0{i}_{sd}" for i in (1, 2, 3) if f"{fg}_0{i}_{sd}" in arm.data.bones]
            if len(bs) < 3:
                continue
            # (the thumb's first bone is its root in her palm: drawn in as her palm is)
            chain = bs[1:] if fg == "thumb" else bs
            pts = [bh(n) for n in chain] + [bt(chain[-1])]
            wf = wts(chain)
            m = wf > 1e-3
            if not m.any():
                continue
            q = co[m]
            best, bestd, bests = None, None, None
            L = np.cumsum([0] + [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)])
            for i in range(len(pts) - 1):
                a, e = pts[i], pts[i + 1]
                t_ = e - a
                u = ((q - a) @ t_) / (t_ @ t_)
                # (unclamped past its first and last bone: a fingertip is not drawn back)
                u = np.clip(u, -np.inf if i == 0 else 0.0, np.inf if i == len(pts) - 2 else 1.0)
                c = a + np.outer(u, t_)
                d = np.linalg.norm(q - c, axis=1)
                s = (L[i] + u * np.linalg.norm(t_)) / L[-1]
                if best is None:
                    best, bestd, bests = c, d, s
                else:
                    k = d < bestd
                    best[k], bestd[k], bests[k] = c[k], d[k], s[k]
            k = HAND_SLIM - HAND_TAPER * np.clip(bests, 0, 1)
            f = 1 - (1 - k) * wf[m]
            out[m] = best + (q - best) * f[:, None]
        # her palm: across (index to pinky) and through (back to palm), about the
        # line from her wrist to the root of her middle finger, eased in from her wrist
        hw = wts([f"hand_{sd}", f"thumb_01_{sd}"])
        a, e = bh(f"hand_{sd}"), bh(f"middle_01_{sd}")
        ax = (e - a) / np.linalg.norm(e - a)
        m = hw > 1e-3
        q = out[m]
        u = (q - a) @ ax
        ease = np.clip(u / 0.035, 0, 1)
        ease = ease * ease * (3 - 2 * ease)
        c = a + np.outer(u, ax)
        f = 1 - (1 - HAND_PALM) * hw[m] * ease
        out[m] = c + (q - c) * f[:, None]
    # her whole hand shortened about her wrist (HAND_SCALE), by her hand's weights
    if HAND_SCALE != 1.0:
        for sd in "lr":
            if f"hand_{sd}" not in arm.data.bones:
                continue
            a = bh(f"hand_{sd}")
            names = [f"hand_{sd}"] + [f"{fg}_0{i}_{sd}" for fg in ("thumb", "index", "middle", "ring", "pinky") for i in (1, 2, 3)]
            w = wts(names)
            m = w > 1e-4
            f = 1 - (1 - HAND_SCALE) * w[m]
            out[m] = a + (out[m] - a) * f[:, None]
    # her forearm lengthened (FOREARM_ADD): stretched evenly from her elbow, her hand carried out
    if FOREARM_ADD != 0.0:
        for sd in "lr":
            if f"lowerarm_{sd}" not in arm.data.bones:
                continue
            e, a = bh(f"lowerarm_{sd}"), bh(f"hand_{sd}")
            L = np.linalg.norm(a - e); ax = (a - e) / L
            w = wts(forearm_bones(sd))
            u = np.clip(((out - e) @ ax) / L, 0, 1)
            out += np.outer(FOREARM_ADD * u * w, ax)
    moved = np.linalg.norm(out - co, axis=1)
    for i in np.where(moved > 0)[0]:
        me.vertices[i].co = out[i].tolist()
    # (her shape keys moved with her, by the same amount: each keeps its own offset)
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            kc = np.array([d.co[:] for d in kb.data])
            kc += out - co
            for i in np.where(moved > 0)[0]:
                kb.data[i].co = kc[i].tolist()
    me.update()
    print("HAND_SLIM %.2f (taper %.2f, palm %.2f, scale %.2f): %d points moved, up to %.1f mm"
          % (HAND_SLIM, HAND_TAPER, HAND_PALM, HAND_SCALE, int((moved > 1e-6).sum()), moved.max() * 1000))


def hand_bones_scaled():
    """Her hand's bones shortened about her wrist by HAND_SCALE (the hand
    bone's head stays; every bone under it moves in, roll kept)."""
    import mathutils
    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    n = 0
    for sd in "lr":
        hb, lb = eb.get(f"hand_{sd}"), eb.get(f"lowerarm_{sd}")
        if hb is None or lb is None:
            continue
        a = hb.head.copy()
        e0 = lb.head.copy()
        L = (a - e0).length
        ax = (a - e0) / L
        under = set()
        todo = [hb]
        while todo:
            x = todo.pop(); under.add(x.name); todo.extend(x.children)
        def to(v, in_hand):
            if in_hand:
                v = a + (v - a) * HAND_SCALE
            u = min(max((v - e0).dot(ax) / L, 0.0), 1.0)
            return v + ax * (FOREARM_ADD * u)
        bones_ = [eb[nm] for nm in forearm_bones(sd) if nm in eb]
        new = {x.name: (to(x.head.copy(), x.name in under), to(x.tail.copy(), x.name in under), x.roll) for x in bones_}
        for x in bones_:
            h, t, roll = new[x.name]
            x.head = h
            x.tail = t
            x.roll = roll
            n += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = prev
    print("HAND_SCALE %.3f, FOREARM_ADD %.3f: %d bones moved (hands shortened about her wrists, forearms lengthened)" % (HAND_SCALE, FOREARM_ADD, n))


if HAND_SLIM < 1.0 or HAND_SCALE != 1.0 or FOREARM_ADD != 0.0:
    hand_slimmed(body)
    if HAND_SCALE != 1.0 or FOREARM_ADD != 0.0:
        hand_bones_scaled()

# (s24, the one body build, 14 Oct: her knuckles where a hand's are. F1's finger
# 01 joints sat at her webs (P1 21-27 mm, a woman's 40-50), so her fingers bent
# from her webs and no grip closed. Animation's solver (handpivots.json, fistfit
# set_hand): every finger's 01 joint drawn toward her wrist's pivot by one factor,
# till the middle one is HPIV_MCP of her hand's length from it; each 03 joint
# moved along its finger till the middle bone is HPIV_P2 of the first; her thumb's
# MCP (thumb_02) back along her metacarpal to HPIV_THUMB from her CMC (her right
# thumb; her CMC and IP stay). Her right hand is the table's (L = HPIV_L); her
# left by the same rule on its own skin, its length and thumb scaled by its own
# (her sculpt is 3.6 mm asymmetric: never a mirror). Every bone keeps its rest
# orientation (only pivots move, as the solver modelled), and the skin a pivot
# passes is handed over: palm skin to its finger's 01 bone in HPIV_LANE lanes by
# a smoothstep HPIV_RAMP either side of the new knuckle, end skin to the middle
# bone over HPIV_DIP_RAMP, thumb skin past its new MCP to thumb_02 over
# HPIV_RAMP. Her skin is not moved here. Off: HAND_PIVOTS=0.)
HAND_PIVOTS = os.environ.get("HAND_PIVOTS", "1") == "1"
HPIV_MCP = float(os.environ.get("HPIV_MCP", "0.48"))
HPIV_P2 = float(os.environ.get("HPIV_P2", "0.65"))
HPIV_L = float(os.environ.get("HPIV_L", "0.2115"))
HPIV_THUMB = float(os.environ.get("HPIV_THUMB", "0.0533"))
HPIV_RAMP, HPIV_DIP_RAMP, HPIV_LANE = 0.010, 0.005, 0.014
# (s24, the coordinator: her left PIPs on her own skin. Each left finger's skin registered
# (ICP) onto her right's mirror, her right's 02 joint carried onto it sits this far toward the
# tip, toward her index and toward her palm from her left's rigged 02 (mm per finger as
# along/across/palmward; index, middle, ring, pinky; s24 scratch pipreg4.py on P1, multi-start ICP):
# the rig had them short (6.4 mm at the pinky, so her left fingers bent mid-bone) and 2.5-3.3 mm
# toward the back of her index, middle and ring (her right's sit mid-finger). The skin short
# of a moved 02 goes to the 01 bone over HPIV_PIP_RAMP either side.)
HPIV_L02 = [[float(v) / 1000 for v in x.split("/")] for x in
            os.environ.get("HPIV_L02", "6.6/-1.0/2.9,2.2/-0.1/3.3,3.8/-0.2/2.6,6.4/2.1/-0.7").split(",")]
# (and her left DIPs likewise, from where the 0.65 rule puts them: pipreg4.py on P4)
HPIV_L03 = [[float(v) / 1000 for v in x.split("/")] for x in
            os.environ.get("HPIV_L03", "-2.8/0.1/-0.1,-0.4/0.2/-1.8,0.8/-0.5/-2.1,-1.0/-0.9/1.4").split(",")]
HPIV_PIP_RAMP = 0.006
# (FINGER_FIX=1, the owner 14-18 Oct, her fingers: (1) her end bones were stubby, the 0.65 rule put
# her index, ring and pinky DIPs 14.3/18.3/10.5 mm from their tips (D/finger 0.12-0.19, a hand's
# 0.21-0.25). Each 03 joint goes along its finger till the end segment (DIP to her skin's tip along
# the end bone) is FF_D of her finger (MCP to tip), per finger index, middle, ring, pinky (0: the
# 0.65 rule as before; her middle was already 0.23); her left's L03 offsets keep their across and
# palmward parts. Her skin has no DIP crease to sit on (its bumps and its paint are flat to 0.2 mm
# and 4/255), so the ratio places it. (2) Her proximal sections were taller than wide (mid-P1 t/w
# 1.13-1.20): finger_flattened draws each P1's palmar pad toward her bone's axis till the section's
# thickness is FF_TW of its width, the back of her finger kept, eased in past her web and out
# before her PIP; her two hands on their own skin.)
FINGER_FIX = os.environ.get("FINGER_FIX", "1") == "1"
FF_D = [float(v) for v in os.environ.get("FF_D", "0.23,0,0.23,0.23").split(",")]
FF_TW = float(os.environ.get("FF_TW", "1.0"))
# (her hand's bones as F1 built them: the fingerless glove's cut is drawn from these)
F1_HEADS = {b.name: np.array((arm.matrix_world @ b.head_local)[:]) for b in arm.data.bones}
# (the outfits' arm chains read her hand to F1's middle knuckle, so no garment moves with the pivots)
MID01_BUILT = {sd: np.array((arm.matrix_world @ arm.data.bones[f"middle_01_{sd}"].head_local)[:])
               for sd in "lr" if f"middle_01_{sd}" in arm.data.bones}
HPIV = {}


def hand_pivots(obj):
    me = obj.data
    A2B = obj.matrix_world.inverted() @ arm.matrix_world   # armature space -> her mesh's
    B2A = A2B.inverted()
    loc = lambda v: np.array((A2B @ v)[:])
    co = np.array([v.co[:] for v in me.vertices])
    gi = {g.name: g.index for g in obj.vertex_groups}
    nv = len(co)
    Wg = {}

    def read(n):
        w = np.zeros(nv)
        if n in gi:
            k = gi[n]
            for v in me.vertices:
                for g in v.groups:
                    if g.group == k:
                        w[v.index] = g.weight
        return w

    def wt(n):
        if n not in Wg:
            Wg[n] = read(n)
        return Wg[n]
    F4 = ("index", "middle", "ring", "pinky")
    bl = arm.data.bones
    old = {b.name: loc(b.head_local) for b in bl}
    new = {}
    lens = {}
    for sd in "lr":
        if f"hand_{sd}" not in bl or any(f"{f}_0{i}_{sd}" not in bl for f in F4 + ("thumb",) for i in (1, 2, 3)):
            continue
        # her hand's length on her own skin: wrist pivot to her middle fingertip
        m3 = wt(f"middle_03_{sd}") > 0.5
        lens[sd] = float(np.linalg.norm(co[m3] - old[f"hand_{sd}"], axis=1).max())
    if set(lens) != {"l", "r"}:
        print("HAND_PIVOTS: no hands found")
        return
    chain_r = (np.linalg.norm(old["thumb_02_r"] - old["thumb_01_r"])
               + np.linalg.norm(old["thumb_03_r"] - old["thumb_02_r"]))
    for sd in "lr":
        a = old[f"hand_{sd}"]
        L = HPIV_L * lens[sd] / lens["r"]
        s = HPIV_MCP * L / np.linalg.norm(old[f"middle_01_{sd}"] - a)
        for kf, f in enumerate(F4):
            p1 = a + (old[f"{f}_01_{sd}"] - a) * s
            new[f"{f}_01_{sd}"] = p1
            p2, p3 = old[f"{f}_02_{sd}"], old[f"{f}_03_{sd}"]
            e = (p3 - p2) / np.linalg.norm(p3 - p2)
            lat_ = old[f"index_02_{sd}"] - old[f"pinky_02_{sd}"]
            lat_ -= e * (lat_ @ e)
            lat_ /= np.linalg.norm(lat_)
            palm_ = np.cross(e, lat_)
            palm_ *= np.sign((old[f"thumb_03_{sd}"] - old[f"index_02_{sd}"]) @ palm_)
            if sd == "l" and any(HPIV_L02[kf]):
                p2 = p2 + e * HPIV_L02[kf][0] + lat_ * HPIV_L02[kf][1] + palm_ * HPIV_L02[kf][2]
                new[f"{f}_02_{sd}"] = p2
            new[f"{f}_03_{sd}"] = p2 + e * HPIV_P2 * np.linalg.norm(p2 - p1)
            if sd == "l" and any(HPIV_L03[kf]):
                new[f"{f}_03_{sd}"] = new[f"{f}_03_{sd}"] + e * HPIV_L03[kf][0] + lat_ * HPIV_L03[kf][1] + palm_ * HPIV_L03[kf][2]
            if FINGER_FIX and FF_D[kf] > 0:
                # (end segment = FF_D of the finger: tip is her skin's furthest point along the end bone)
                q = co[(wt(f"{f}_01_{sd}") + wt(f"{f}_02_{sd}") + wt(f"{f}_03_{sd}")) > 0.5]
                p3 = new[f"{f}_03_{sd}"]
                d0 = float(((q - p2) @ ((p3 - p2) / np.linalg.norm(p3 - p2))).max() - np.linalg.norm(p3 - p2))
                for _ in range(4):
                    e3 = (p3 - p2) / np.linalg.norm(p3 - p2)
                    t0 = float(((q - p2) @ e3).max())
                    p3 = p2 + e3 * (t0 - FF_D[kf] * (np.linalg.norm(p2 - p1) + t0))
                new[f"{f}_03_{sd}"] = p3
                d1 = t0 - float(np.linalg.norm(p3 - p2))
                print("FINGER_FIX %s %s: DIP %.1f mm toward her knuckle, end segment %.1f -> %.1f mm (D/finger %.3f)"
                      % (f, sd, (d1 - d0) * 1000, d0 * 1000, d1 * 1000, d1 / (np.linalg.norm(p2 - p1) + t0)))
        c0, m0, i0 = (old[f"thumb_0{k}_{sd}"] for k in (1, 2, 3))
        chain = np.linalg.norm(m0 - c0) + np.linalg.norm(i0 - m0)
        new[f"thumb_02_{sd}"] = c0 + (m0 - c0) / np.linalg.norm(m0 - c0) * HPIV_THUMB * chain / chain_r
        print("HAND_PIVOTS %s: hand %.1f mm on her skin (L %.1f), knuckles x%.4f: MCP %s mm from her wrist; P1 %s, P2 %s mm; "
              "thumb MCP %.1f mm back (metacarpal %.1f, proximal %.1f)"
              % (sd, lens[sd] * 1000, L * 1000, s,
                 " ".join("%.1f" % (np.linalg.norm(new[f"{f}_01_{sd}"] - a) * 1000) for f in F4),
                 " ".join("%.1f" % (np.linalg.norm(new.get(f"{f}_02_{sd}", old[f"{f}_02_{sd}"]) - new[f"{f}_01_{sd}"]) * 1000) for f in F4),
                 " ".join("%.1f" % (np.linalg.norm(new[f"{f}_03_{sd}"] - new.get(f"{f}_02_{sd}", old[f"{f}_02_{sd}"])) * 1000) for f in F4),
                 np.linalg.norm(new[f"thumb_02_{sd}"] - m0) * 1000, np.linalg.norm(new[f"thumb_02_{sd}"] - c0) * 1000,
                 np.linalg.norm(i0 - new[f"thumb_02_{sd}"]) * 1000))

    # ---- the skin each pivot passes, handed over (fistfit _model_body, _model_dips, _model_thumb)
    def share(sel, wc, kc, kp, more):
        """kc's share of the pair (kc, kp) on the vertices sel: at least (more)
        or at most (not more) the pair's total x wc."""
        wc_, wp_ = wt(kc)[sel], wt(kp)[sel]
        tot = wc_ + wp_
        nc = np.maximum(wc_, tot * wc) if more else np.minimum(wc_, tot * wc)
        Wg[kc][sel], Wg[kp][sel] = nc, tot - nc

    def smooth(x):
        u = np.clip(x, 0, 1)
        return u * u * (3 - 2 * u)
    for sd in "lr":
        hn = f"hand_{sd}"
        ax = old[f"middle_01_{sd}"] - old[hn]
        ax /= np.linalg.norm(ax)
        side = old[f"index_01_{sd}"] - old[f"pinky_01_{sd}"]
        side -= ax * (side @ ax)
        side /= np.linalg.norm(side)
        cand = np.nonzero(wt(hn) > 0)[0]
        lat = np.stack([(co[cand] - new[f"{f}_01_{sd}"]) @ side for f in F4], 1)
        lane = np.argmin(np.abs(lat), 1)
        for li, f in enumerate(F4):
            n1 = f"{f}_01_{sd}"
            m = old[n1] - new[n1]
            m /= np.linalg.norm(m)
            sel = cand[(lane == li) & (np.abs(lat[:, li]) < HPIV_LANE)]
            want = smooth(((co[sel] - new[n1]) @ m + HPIV_RAMP) / (2 * HPIV_RAMP))
            k = want > 0
            wt(n1)
            share(sel[k], want[k], n1, hn, True)
        for f in F4:
            n2, n3 = f"{f}_02_{sd}", f"{f}_03_{sd}"
            if n2 in new:
                n1 = f"{f}_01_{sd}"
                m2 = old[n3] - old[n2]   # (handed over along her finger; every left 02 moved toward the tip)
                m2 /= np.linalg.norm(m2)
                sel = np.nonzero(wt(n2) > 0)[0]
                wt(n1)
                share(sel, smooth(((co[sel] - new[n2]) @ m2 + HPIV_PIP_RAMP) / (2 * HPIV_PIP_RAMP)), n2, n1, False)
            # (along her finger: moved toward the tip, the end bone gives up the skin short of
            # its new pivot; toward the wrist, it takes the skin past it)
            m = old[n3] - old[n2]
            m /= np.linalg.norm(m)
            along = (new[n3] - old[n3]) @ m
            if abs(along) < 1e-6:
                continue
            sel = np.nonzero((wt(n3) > 0) | ((wt(n2) > 0) & (along < 0)))[0]
            want = smooth(((co[sel] - new[n3]) @ m + HPIV_DIP_RAMP) / (2 * HPIV_DIP_RAMP))
            share(sel, want, n3, n2, along < 0)
        n1, n2, n3 = f"thumb_01_{sd}", f"thumb_02_{sd}", f"thumb_03_{sd}"
        e = old[n3] - old[n1]
        e /= np.linalg.norm(e)
        sel = np.nonzero((wt(n2) > 0) | (wt(n1) > 0))[0]
        want = smooth(((co[sel] - new[n2]) @ e + HPIV_RAMP) / (2 * HPIV_RAMP))
        k = (want > 0) & (wt(n1)[sel] > 0)
        share(sel[k], want[k], n2, n1, True)
    changed = 0
    for n, w in Wg.items():
        w0 = read(n)
        if n not in gi:
            obj.vertex_groups.new(name=n)
            gi[n] = obj.vertex_groups[n].index
        vg = obj.vertex_groups[n]
        for i in np.nonzero(np.abs(w - w0) > 1e-7)[0]:
            if w[i] > 1e-7:
                vg.add([int(i)], float(w[i]), "REPLACE")
            else:
                vg.remove([int(i)])
            changed += 1

    # ---- the bones: each moved pivot's bone keeps its rest orientation; the bones under it stay where they are
    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    for n in new:
        for c in eb[n].children:
            c.use_connect = False
        eb[n].use_connect = False
    worst = 0.0
    for n, p in new.items():
        x = eb[n]
        M0 = x.matrix.copy()
        kids = list(x.children)
        tip = kids[0].head.copy() if kids else x.tail.copy()
        M = M0.copy()
        M.translation = B2A @ Vector(p.tolist())
        x.matrix = M
        x.length = max((tip - x.head).dot(M0.col[1].to_3d().normalized()), 0.004)
        worst = max(worst, max(abs(x.matrix[i][j] - M0[i][j]) for i in range(3) for j in range(3)))
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = prev
    HPIV.update(new=new, old=old, lens=lens)
    print("HAND_PIVOTS: %d pivots moved (orientation kept to %.1e), %d skin weights handed over" % (len(new), worst, changed))


def finger_flattened(obj):
    """FINGER_FIX (2): each finger's proximal section, from her web to her PIP, drawn in
    front to back toward t/w = FF_TW, from her palmar pad only (her finger's back and sides kept),
    about the bone's axis (the new 01 -> 02 line), by her finger's own weights; a plane slice of
    her skin every 0.5 mm reads w and t, twice (the second pass takes up the smoothing's shortfall)."""
    me = obj.data
    co = np.array([v.co[:] for v in me.vertices])
    nv = len(co)
    F4 = ("index", "middle", "ring", "pinky")
    gi = {g.name: g.index for g in obj.vertex_groups}
    want = {gi[f"{f}_0{i}_{sd}"]: f"{f}_0{i}_{sd}" for sd in "lr" for f in F4 for i in (1, 2, 3)
            if f"{f}_0{i}_{sd}" in gi}
    W = {n: np.zeros(nv) for n in want.values()}
    for v in me.vertices:
        for g in v.groups:
            n = want.get(g.group)
            if n:
                W[n][v.index] = g.weight
    me.calc_loop_triangles()
    tri = np.zeros(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", tri)
    tri = tri.reshape(-1, 3)
    new, old = HPIV["new"], HPIV["old"]
    hd = lambda n: new.get(n, old[n])

    def smooth(x):
        u = np.clip(x, 0, 1)
        return u * u * (3 - 2 * u)

    def sections(X, tris, p1, u, l2, d2, S, rad=0.015):
        d = (X - p1) @ u
        rows = []
        for s in S:
            dt = d[tris] - s
            pts = []
            for a_, b_ in ((0, 1), (1, 2), (2, 0)):
                da, db = dt[:, a_], dt[:, b_]
                m = (da * db) < 0
                t = da[m] / (da[m] - db[m])
                pa, pb = X[tris[m, a_]], X[tris[m, b_]]
                pts.append(pa + (pb - pa) * t[:, None])
            R = np.concatenate(pts) - (p1 + u * s)
            R = R[np.linalg.norm(R, axis=1) < rad]
            if len(R) < 4:
                rows.append((np.nan, np.nan, np.nan))
                continue
            y = R @ d2
            rows.append((np.ptp(R @ l2), y.max(), -y.min()))
        return np.array(rows)
    out = co.copy()
    for sd in "lr":
        if f"index_01_{sd}" not in new:
            continue
        for f in F4:
            n1, n2, n3 = (f"{f}_0{i}_{sd}" for i in (1, 2, 3))
            p1, p2 = hd(n1), hd(n2)
            P = float(np.linalg.norm(p2 - p1))
            u = (p2 - p1) / P
            l2 = hd(f"index_02_{sd}") - hd(f"pinky_02_{sd}")
            l2 = l2 - u * (l2 @ u)
            l2 /= np.linalg.norm(l2)
            d2 = np.cross(u, l2)
            if (hd(f"thumb_03_{sd}") - hd(f"index_02_{sd}")) @ d2 > 0:
                d2 = -d2                                   # (d2: toward the back of her finger)
            fw = np.clip(W[n1] + W[n2] + W[n3], 0, 1)
            tris = tri[(fw[tri] > 0.6).all(1)]
            trisw = tri[(fw[tri] > 0.3).all(1)]
            S = np.arange(0.001, P, 0.0005)
            mv = np.nonzero(fw > 0)[0]
            log = []
            for ps in range(3):
                sec = sections(out, tris, p1, u, l2, d2, S)
                w, dors, palm = sec[:, 0], sec[:, 1], sec[:, 2]
                mid = int(np.argmin(np.abs(S - 0.6 * P)))
                log.append((w[mid], dors[mid] + palm[mid]))
                if ps == 2:
                    break
                if ps == 0:
                    # (her web: the last section, short of 0.65 P, still 15% wider than her free finger,
                    # on her finger's own skin, else with the skin it shares; never short of 0.45 P)
                    s_w = 0.0
                    for tt in (tris, trisw):
                        ww = sections(out, tt, p1, u, l2, d2, S, 0.022)[:, 0]
                        ref = np.nanmedian(ww[(S > 0.7 * P) & (S < 0.95 * P)])
                        wide = np.nonzero((ww > 1.15 * ref) & (S < 0.65 * P))[0]
                        if len(wide):
                            s_w = S[wide.max()] + 0.0005
                            break
                    s_w = max(s_w, 0.45 * P)
                fs = np.clip((FF_TW * w - dors) / palm, 0.6, 1.0)
                fs[~np.isfinite(fs)] = 1.0
                env = smooth((S - s_w + 0.006) / 0.006) * smooth((P - 0.002 - S) / 0.008)
                g = 1 - env * (1 - fs)
                # (smoothed along her finger, sigma 2 mm: no ridge where the pad starts)
                k = np.exp(-0.5 * (np.arange(-12, 13) * 0.5 / 2.0) ** 2)
                k /= k.sum()
                g = np.convolve(np.pad(g, 12, constant_values=1.0), k, "valid")
                X = out[mv]
                sv = (X - p1) @ u
                y = (X - p1) @ d2
                gv = np.interp(sv, S, g, left=1.0, right=1.0)
                fac = 1 - (1 - gv) * smooth(-y / 0.002) * fw[mv]
                out[mv] = X + np.outer(y * fac - y, d2)
            mvd = np.linalg.norm(out[mv] - co[mv], axis=1)
            print("FINGER_FIX %s %s: web %.1f mm from MCP (P %.1f); mid-P1 w %.1f t %.1f -> w %.1f t %.1f (t/w %.2f -> %.2f); "
                  "pad drawn in up to %.1f mm" % (f, sd, s_w * 1000, P * 1000, log[0][0] * 1000, log[0][1] * 1000,
                                                  log[2][0] * 1000, log[2][1] * 1000, log[0][1] / log[0][0],
                                                  log[2][1] / log[2][0], mvd.max() * 1000))
    moved = np.linalg.norm(out - co, axis=1)
    for i in np.where(moved > 0)[0]:
        me.vertices[i].co = out[i].tolist()
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            kc = np.array([d.co[:] for d in kb.data])
            kc += out - co
            for i in np.where(moved > 0)[0]:
                kb.data[i].co = kc[i].tolist()
    me.update()
    print("FINGER_FIX: %d points moved, up to %.1f mm" % (int((moved > 1e-7).sum()), moved.max() * 1000))


if HAND_PIVOTS:
    hand_pivots(body)
# (finger_flattened is applied to her body only, just before her body is exported, and taken
# back after: her whole skin feeds every piece (BVH.find_nearest's tie-breaks between two faces
# at an edge shift with any point of her, held_edges -> a corset's bind -> its decimate), so a
# flatten here moved every outfit 3-7 mm; her gloves sit on the un-flattened pad.)

# ---- her back of hand (BACKHAND=1): her skin's knuckle drop moved onto her new knuckles.
# hand_pivots moved her finger pivots ~20 mm toward her wrist; her back-of-hand skin still fell
# off into her fingers at her old knuckles. Per finger and per hand (her two hands are her own,
# never mirrored), on her back's skin only: the drop is redrawn (her back's line, her finger's
# line stretched back, joined by a logistic as steep as her own drop) and moved till its
# steepest point is at the new pivot (BH_AT past it), after a short slide (at most BH_SLIDE)
# toward her wrist so her old drop's edge rows reach the new knuckle; a soft rise of BH_A
# BH_BACK behind each pivot (her knuckle). Weighted to her top surface, nothing on her palm
# side, her thin webs kept (BH_WEB), eased in by distance from all skin that stays (BH_EASE_R).
BACKHAND = os.environ.get("BACKHAND", "0") == "1"   # (off: judge bh1 FAILED it 14 Oct, hard facets at the ease-in on a ~7 mm mesh; detail belongs in the normal map)
_bhf = lambda k, d: float(os.environ.get(k, d))
BH_A = _bhf("BH_A", "0.0025")
BH_SIG = (_bhf("BH_SIG_T", "0.0045"), _bhf("BH_SIG_U", "0.0045"))
BH_BACK = _bhf("BH_BACK", "0.004")
BH_KW = (0.0025, 0.0045)
BH_ITERS = 8
BH_SLIDE = _bhf("BH_SLIDE", "0.004")
BH_WEB = (0.007, 0.006)
BH_EASE_R = _bhf("BH_EASE_R", "0.012")
BH_AT = _bhf("BH_AT", "0.0")


def _bh_smooth(x):
    u = np.clip(x, 0, 1)
    return u * u * (3 - 2 * u)


def _bh_side(co, T, hw, hv, J):
    """co (n,3) metres, T (m,3) tris, hw (n,) this side's hand+finger weight,
    J name->head for this side ('hand', 'index_01', ..., 'thumb_02').
    Returns (offsets (n,3), report)."""
    F4 = ("index", "middle", "ring", "pinky")
    h = J["hand"]
    ax = J["tip"] - h; ax /= np.linalg.norm(ax)
    lat = J["index_01"] - J["pinky_01"]; lat -= ax * (lat @ ax); lat /= np.linalg.norm(lat)
    nrm = np.cross(ax, lat)
    nrm *= -np.sign((J["thumb_02"] - h) @ nrm)
    tf = lambda x: (x - h) @ ax
    uf = lambda x: (x - h) @ lat
    piv = {f: [J[f"{f}_0{k}"] for k in (1, 2, 3)] for f in F4}
    t1 = {f: tf(piv[f][0]) for f in F4}
    TS = T[hv[T].any(1)]
    T = T[(hw[T] > 0.3).any(1)]
    bc = [(k / 8, l / 8) for k in range(9) for l in range(9 - k)]

    def lane_u(f, t):
        ts = [tf(p) for p in piv[f]]; us = [uf(p) for p in piv[f]]
        return np.interp(t, ts, us)
    ST = 0.001
    tg = np.arange(0.060, 0.160, ST)
    kx = np.arange(-4, 5) * ST; kk = np.exp(-kx ** 2 / (2 * 0.0015 ** 2)); kk /= kk.sum()

    def profiles(P):
        S = np.concatenate([P[TS[:, 0]] * (1 - a - b) + P[TS[:, 1]] * a + P[TS[:, 2]] * b for a, b in bc])
        q = S - h; t, u, v = q @ ax, q @ lat, q @ nrm
        out = {}
        for f in F4:
            top, bot = np.full(len(tg), np.nan), np.full(len(tg), np.nan)
            ul = lane_u(f, tg)
            for i, tt in enumerate(tg):
                m = (np.abs(t - tt) < 0.001) & (np.abs(u - ul[i]) < 0.003)
                if m.sum() > 1:
                    top[i], bot[i] = v[m].max(), v[m].min()
            res = []
            for y in (top, bot):
                ok = ~np.isnan(y); y = np.interp(tg, tg[ok], y[ok])
                res.append(np.convolve(np.pad(y, 4, mode="edge"), kk, "valid"))
            g = np.gradient(res[0], ST)
            sel = (tg > t1[f] - 0.020) & (tg < tf(piv[f][1]) - 0.010)
            i = np.nanargmin(np.where(sel, g, np.nan))
            tc = tg[i]
            y0, y1, y2 = g[i - 1], g[i], g[i + 1]; den = y0 - 2 * y1 + y2
            if den != 0:
                tc += 0.5 * (y0 - y2) / den * ST
            out[f] = (res[0], res[1], tc)
        return out
    q = co - h
    t, u, v = q @ ax, q @ lat, q @ nrm
    sel = np.nonzero((hw > 0.01) & (t > 0.060) & (t < 0.160))[0]
    ts, us, vs = t[sel], u[sel], v[sel]
    pr0 = profiles(co)
    c_old = {f: pr0[f][2] for f in F4}
    c_new = {f: t1[f] + BH_AT for f in F4}
    lanes = np.stack([lane_u(f, ts) for f in F4], 1)               # (k,4)
    lam = np.exp(-(us[:, None] - lanes) ** 2 / (2 * 0.006 ** 2)) + 1e-12
    lam /= lam.sum(1, keepdims=True)
    # (out past her outer lanes: faded over 10 mm)
    side = _bh_smooth((us - lanes[:, 3] + 0.014) / 0.010) * _bh_smooth((lanes[:, 0] + 0.014 - us) / 0.010)
    # her top (dorsal) surface as it was, rastered at 0.5 mm in (t, u)
    G = 0.0005
    gt = np.arange(0.050, 0.175, G); gu = np.arange(-0.070, 0.070, G)
    Htop = np.full((len(gt), len(gu)), -np.inf); Hbot = np.full((len(gt), len(gu)), np.inf)
    Q = co - h
    Pt, Pu, Pv = Q @ ax, Q @ lat, Q @ nrm
    for tri in T:
        x, y, z = Pt[tri], Pu[tri], Pv[tri]
        if x.min() > gt[-1] or x.max() < gt[0]:
            continue
        i0, i1 = np.searchsorted(gt, x.min()), np.searchsorted(gt, x.max(), "right")
        j0, j1 = np.searchsorted(gu, y.min()), np.searchsorted(gu, y.max(), "right")
        if i1 <= i0 or j1 <= j0:
            continue
        X, Y = np.meshgrid(gt[i0:i1], gu[j0:j1], indexing="ij")
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        l0 = ((y[1] - y[2]) * (X - x[2]) + (x[2] - x[1]) * (Y - y[2])) / d
        l1 = ((y[2] - y[0]) * (X - x[2]) + (x[0] - x[2]) * (Y - y[2])) / d
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9)
        zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
        Htop[i0:i1, j0:j1] = np.maximum(Htop[i0:i1, j0:j1], np.where(m, zz, -np.inf))
        Hbot[i0:i1, j0:j1] = np.minimum(Hbot[i0:i1, j0:j1], np.where(m, zz, np.inf))

    def hget(Hm, t_, u_):
        fi = np.clip((t_ - gt[0]) / G, 0, len(gt) - 1.001); fj = np.clip((u_ - gu[0]) / G, 0, len(gu) - 1.001)
        i, j = fi.astype(int), fj.astype(int); a_, b_ = fi - i, fj - j
        c = [Hm[i, j], Hm[i + 1, j], Hm[i, j + 1], Hm[i + 1, j + 1]]
        ok = np.isfinite(c).all(0)
        c = [np.where(ok, x, 0) for x in c]
        return (c[0] * (1 - a_) * (1 - b_) + c[1] * a_ * (1 - b_) + c[2] * (1 - a_) * b_ + c[3] * a_ * b_), ok

    # her back's skin only: full on her top surface, nothing below the middle of her hand there
    top_l, ok_t = hget(Htop, ts, us); bot_l, ok_b = hget(Hbot, ts, us)
    ok = ok_t & ok_b & (top_l - bot_l > 0.002)
    mid = 0.5 * (top_l + bot_l)
    wd = np.where(ok, _bh_smooth(((vs - mid) / np.maximum(top_l - mid, 1e-4) - 0.2) / 0.5), 0.0)
    # (her webs, thin, kept as they are)
    W = wd * side * _bh_smooth((top_l - bot_l - BH_WEB[0]) / BH_WEB[1])
    # (and eased in by distance from all her skin that stays, so no small triangle of her
    # webs or sides is pulled against its neighbour)
    still = co[sel][W < 0.02]
    dmin = np.full(len(sel), np.inf)
    for i0 in range(0, len(still), 512):
        dmin = np.minimum(dmin, np.linalg.norm(co[sel][:, None] - still[None, i0:i0 + 512], axis=2).min(1))
    W = W * _bh_smooth(dmin / BH_EASE_R)
    # each lane's drop redrawn: her back's line before it, her finger's line after it (stretched
    # back from her old drop to the new one, held at tfar short of her PIP), joined by a logistic
    # as steep as her own drop; eased into her own profile 15-21 mm before it and at tfar
    lines = {}
    for f in F4:
        y = pr0[f][0]; co_ = c_old[f]
        tfar = max(tf(piv[f][1]) - 0.008, co_ + 0.014)
        mh = (tg > co_ - 0.030) & (tg < co_ - 0.009); ml = (tg > co_ + 0.006) & (tg < tfar)
        hi = np.polyfit(tg[mh], y[mh], 1); lo = np.polyfit(tg[ml], y[ml], 1)
        g = np.gradient(y, ST); smax = -g[(tg > co_ - 0.003) & (tg < co_ + 0.003)].min()
        dlt = np.polyval(hi, co_) - np.polyval(lo, co_)
        lines[f] = (hi, lo, float(np.clip(dlt / (4 * max(smax, 1e-3)), BH_KW[0], BH_KW[1])), tfar)

    def build(c_new):
        # (a short slide first, toward her wrist, so her old drop's rows reach the new knuckle:
        # BH_SLIDE at most, nothing at the knuckle's top, back to nothing by tfar)
        sv = np.zeros((len(sel), 4))
        for k, f in enumerate(F4):
            hi, lo, kw, tfar = lines[f]
            c = c_new[f]
            sv[:, k] = BH_SLIDE * _bh_smooth((ts - (c - 0.004)) / 0.012) * (1 - _bh_smooth((ts - (c_old[f] + 0.002)) / max(tfar - c_old[f] - 0.002, 0.004)))
        dt = -(lam * sv).sum(1) * W
        tn = ts + dt
        D = np.zeros((len(sel), 4)); B = np.zeros(len(sel))
        for k, f in enumerate(F4):
            hi, lo, kw, tfar = lines[f]
            c = c_new[f]
            r = (tfar - c_old[f]) / (tfar - c)
            lw = np.polyval(lo, np.where(tn < c, c_old[f] + (tn - c), c_old[f] + (tn - c) * r))
            Hd = lw + (np.polyval(hi, tn) - lw) / (1 + np.exp(np.clip((tn - c) / kw, -50, 50)))
            e = _bh_smooth((tn - (c - 0.021)) / 0.006) * (1 - _bh_smooth((tn - (tfar - 0.006)) / 0.006))
            own = np.interp(tn, tg, pr0[f][0])
            D[:, k] = (Hd - own) * e + own - np.interp(ts, tg, pr0[f][0])
            B += BH_A * np.exp(-(tn - (t1[f] - BH_BACK)) ** 2 / (2 * BH_SIG[0] ** 2)) * np.exp(-(us - lanes[:, k]) ** 2 / (2 * BH_SIG[1] ** 2))
        dv = ((lam * D).sum(1) + B) * W
        # (never more than half way down to her palm side)
        room = 0.5 * np.maximum(vs - bot_l, 0)
        dv = np.where(dv < 0, -room * np.tanh(-dv / np.maximum(room, 1e-5)), dv)
        off = np.zeros_like(co)
        off[sel] = np.outer(dt, ax) + np.outer(dv, nrm)
        return off
    best = {f: (1e9, c_new[f]) for f in F4}
    for it in range(BH_ITERS):
        off = build(c_new)
        pr = profiles(co + off)
        err = {f: pr[f][2] - (t1[f] + BH_AT) for f in F4}
        for f in F4:
            if abs(err[f]) < best[f][0]:
                best[f] = (abs(err[f]), c_new[f])
        if max(abs(e) for e in err.values()) < 0.0003:
            break
        for f in F4:
            c_new[f] -= 0.6 * err[f]
    if any(best[f][1] != c_new[f] for f in F4):
        c_new = {f: best[f][1] for f in F4}
        off = build(c_new)
        pr = profiles(co + off)
    rep = {f: dict(t1=t1[f], old=c_old[f], new=pr[f][2], shift=c_old[f] - pr[f][2], c=c_new[f]) for f in F4}
    return off, rep

def back_of_hand(obj):
    me = obj.data
    A2B = obj.matrix_world.inverted() @ arm.matrix_world
    co = np.array([v.co[:] for v in me.vertices])
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int64)
    gname = {g.index: g.name for g in obj.vertex_groups}
    keys = ("hand", "thumb", "index", "middle", "ring", "pinky")
    hw = {sd: np.zeros(len(co)) for sd in "lr"}
    hmx = {sd: np.zeros(len(co)) for sd in "lr"}
    for v in me.vertices:
        for g in v.groups:
            n = gname.get(g.group, "")
            sd = n[-1:]
            if n[-2:-1] == "_" and sd in hw and any(k in n for k in keys):
                hw[sd][v.index] += g.weight
                hmx[sd][v.index] = max(hmx[sd][v.index], g.weight)
    bl = arm.data.bones
    out = np.zeros_like(co)
    for sd in "lr":
        need = [f"hand_{sd}", f"thumb_02_{sd}"] + [f"{f}_0{k}_{sd}" for f in ("index", "middle", "ring", "pinky") for k in (1, 2, 3)]
        if any(n not in bl for n in need):
            continue
        J = {n[:-2]: np.array((A2B @ bl[n].head_local)[:]) for n in need}
        lf = bl.get(f"middle_04_leaf_{sd}")
        J["tip"] = np.array((A2B @ (lf.head_local if lf else bl[f"middle_03_{sd}"].tail_local))[:])
        off, rep = _bh_side(co, T, hw[sd], hmx[sd] > 0.3, J)
        out += off
        print("BACKHAND %s: " % sd + "; ".join("%s pivot %.1f, drop %.1f -> %.1f mm" % (f, r["t1"] * 1000, r["old"] * 1000, r["new"] * 1000)
                                               for f, r in rep.items()))
    moved = np.linalg.norm(out, axis=1) > 0
    new = co + out
    for i in np.nonzero(moved)[0]:
        me.vertices[i].co = new[i].tolist()
    # (her shape keys moved with her, by the same amount: each keeps its own offset)
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            for i in np.nonzero(moved)[0]:
                kb.data[i].co = (np.array(kb.data[i].co[:]) + out[i]).tolist()
    me.update()
    print("BACKHAND: %d points moved, up to %.1f mm" % (int(moved.sum()), np.linalg.norm(out, axis=1).max() * 1000))


if BACKHAND:
    back_of_hand(body)

# (s24, the one body build, face lead 25's throat line (judge APPROVED, prototype proto_b.py):
# her neck graft runs upright to 1.565 m and her chest leans out at once, an up-facing lip at
# 1.545-1.56 m that catches the sheen as a level line across her throat. A biharmonic fill of
# the graft's front, whole within THROAT_IN of THROAT_C, eased out by THROAT_OUT, the graft's
# own edges held; her shape keys take the same offsets. Off: THROAT_FILL=0.)
THROAT_FILL = os.environ.get("THROAT_FILL", "1") == "1"
THROAT_C = float(os.environ.get("THROAT_C", "1.56"))
THROAT_IN = float(os.environ.get("THROAT_IN", "0.035"))
THROAT_OUT = float(os.environ.get("THROAT_OUT", "0.045"))


def throat_fill(obj):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    me = obj.data
    ga = me.attributes.get("graft")
    if ga is None:
        print("THROAT: no graft attribute")
        return
    gv = np.zeros(len(me.vertices), int)
    ga.data.foreach_get("value", gv)
    mw = obj.matrix_world
    co = np.array([v.co[:] for v in me.vertices])
    Pw = np.array([(mw @ v.co)[:] for v in me.vertices])
    key = np.round(Pw / 1e-5).astype(np.int64)
    _, w_, = np.unique(key, axis=0, return_inverse=True)[:2]
    w_ = w_.ravel()
    nw = w_.max() + 1
    P0 = np.zeros((nw, 3))
    P0[w_] = Pw
    faces = [p.vertices[:] for p in me.polygons if all(gv[i] for i in p.vertices)]
    tris = np.array([(f[0], f[k], f[k + 1]) for f in faces for k in range(1, len(f) - 1)])
    F = w_[tris]
    # (edges of the graft's own faces: a polygon's sides, not its triangulation's diagonals)
    pe = np.array([(w_[f[k]], w_[f[(k + 1) % len(f)]]) for f in faces for k in range(len(f))])
    es = np.sort(pe, 1)
    u, ec = np.unique(es, axis=0, return_counts=True)
    ing = np.zeros(nw, bool)
    ing[F.ravel()] = True
    bnd = np.zeros(nw, bool)
    bnd[u[ec == 1].ravel()] = True
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    ue = np.unique(np.sort(e, 1), axis=0)
    A = sp.coo_matrix((np.ones(len(ue) * 2), (np.r_[ue[:, 0], ue[:, 1]], np.r_[ue[:, 1], ue[:, 0]])), shape=(nw, nw)).tocsr()
    A = sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A

    def sm(x):
        x = np.clip(x, 0, 1)
        return x * x * (3 - 2 * x)
    # (the band level round her throat's front and sides: her front is -Y here, glTF's +Z)
    d = np.abs(P0[:, 2] - THROAT_C)
    wt = 1 - sm((d - THROAT_IN) / (THROAT_OUT - THROAT_IN))
    wt *= sm((-P0[:, 1] + 0.02) / 0.04)
    wt[bnd | ~ing] = 0
    free = wt > 0.999
    Lm = sp.identity(nw) - A
    Q = (Lm.T @ Lm).tocsr()
    fi, fx = np.where(free)[0], np.where(~free)[0]
    if not len(fi):
        print("THROAT: nothing in the band")
        return
    solve = spl.factorized(Q[fi][:, fi].tocsc())
    rhs = -(Q[fi][:, fx] @ P0[fx])
    Pb = P0.copy()
    Pb[fi] = np.stack([solve(rhs[:, k]) for k in range(3)], 1)
    Pn = P0 + (Pb - P0) * wt[:, None]
    mv = np.linalg.norm(Pn - P0, axis=1)
    dw = (Pn - P0)[w_]
    dl = dw @ np.array(mw.inverted().to_3x3()).T
    moved = np.nonzero(np.linalg.norm(dl, axis=1) > 1e-9)[0]
    for i in moved:
        me.vertices[i].co = (co[i] + dl[i]).tolist()
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            for i in moved:
                kb.data[i].co = (np.array(kb.data[i].co[:]) + dl[i]).tolist()
    me.update()
    print("THROAT: %d points moved (welded %d), %.2f mm at most, %.2f mm mean; z %.3f..%.3f"
          % (len(moved), int((mv > 1e-5).sum()), mv.max() * 1000, mv[mv > 1e-5].mean() * 1000,
             P0[mv > 1e-5, 2].min(), P0[mv > 1e-5, 2].max()))


if THROAT_FILL:
    throat_fill(body)

# ------------------------------------------------------------ her surface --
# Welded (the paint's seams split her vertices) and in triangles.
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table()
bm.normal_update()
mw = body.matrix_world
P = np.array([(mw @ v.co)[:] for v in bm.verts])
N = np.array([(mw.to_3x3() @ v.normal).normalized()[:] for v in bm.verts])
TRI = np.array([[v.index for v in f.verts] for f in bm.faces])
dl = bm.verts.layers.deform.active
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(P), len(BONES)), np.float32)
for v in bm.verts:
    for g, w in v[dl].items():
        n = gname.get(g)
        if n in BI:
            W[v.index, BI[n]] = w
bm.free()
# Her head's surface joined on (it shares her points along her neck), so
# collars and hats are fitted to her as she is.
if HEAD:
    hb = bmesh.new()
    hb.from_mesh(HEAD.data)
    bmesh.ops.triangulate(hb, faces=hb.faces)
    hb.verts.ensure_lookup_table()
    hb.normal_update()
    hP = np.array([(HEAD.matrix_world @ v.co)[:] for v in hb.verts])
    hN = np.array([(HEAD.matrix_world.to_3x3() @ v.normal).normalized()[:] for v in hb.verts])
    hT = np.array([[v.index for v in f.verts] for f in hb.faces])
    hW = np.zeros((len(hP), len(BONES)), np.float32)
    hl = hb.verts.layers.deform.active
    hname = {g.index: g.name for g in HEAD.vertex_groups}
    for v in hb.verts:
        for g, w in v[hl].items():
            if hname.get(g) in BI:
                hW[v.index, BI[hname[g]]] = w
    hb.free()
    d, j = cKDTree(P).query(hP)
    shared = d < 1e-5
    idx = np.where(shared, j, len(P) + np.cumsum(~shared) - 1)
    P, N, W = np.vstack([P, hP[~shared]]), np.vstack([N, hN[~shared]]), np.vstack([W, hW[~shared]])
    TRI = np.vstack([TRI, idx[hT]])
    print("HEAD joined on:", int(shared.sum()), "points shared,", int((~shared).sum()), "of its own")


def subdivide(P, N, W, TRI):
    """Each triangle made four (a point at the middle of every edge), so a
    strap narrower than her triangles still finds skin to be cut from."""
    e = np.sort(np.vstack([TRI[:, [0, 1]], TRI[:, [1, 2]], TRI[:, [2, 0]]]), 1)
    uk, inv = np.unique(e, axis=0, return_inverse=True)
    inv = inv.ravel()
    m = len(P) + np.arange(len(uk))
    P2 = np.vstack([P, (P[uk[:, 0]] + P[uk[:, 1]]) / 2])
    N2 = np.vstack([N, N[uk[:, 0]] + N[uk[:, 1]]])
    N2 /= np.linalg.norm(N2, axis=1)[:, None] + 1e-12
    W2 = np.vstack([W, (W[uk[:, 0]] + W[uk[:, 1]]) / 2])
    t = len(TRI)
    ab, bc, ca = m[inv[:t]], m[inv[t:2 * t]], m[inv[2 * t:]]
    a, b, c = TRI[:, 0], TRI[:, 1], TRI[:, 2]
    T2 = np.vstack([np.c_[a, ab, ca], np.c_[ab, b, bc], np.c_[ca, bc, c], np.c_[ab, bc, ca]])
    return P2, N2, W2, T2


P, N, W, TRI = subdivide(P, N, W, TRI)
BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI.tolist())
# Her hair, by its paint (it is part of her mesh, and some strands are
# weighted to her neck and back, not her head): red, above her shoulders.
def _hair():
    me = body.data
    img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    uv = np.zeros((len(me.vertices), 2))
    cnt = np.zeros(len(me.vertices))
    for l in me.loops:
        uv[l.vertex_index] += me.uv_layers.active.data[l.index].uv
        cnt[l.vertex_index] += 1
    uv /= np.maximum(cnt, 1)[:, None]
    col = px[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]
    co = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
    red = (col[:, 0] > 0.25) & (col[:, 0] > col[:, 1] * 1.7) & (col[:, 0] > col[:, 2] * 1.7) & (co[:, 2] > 1.4)
    _, j = cKDTree(co).query(P)
    return red[j].astype(float)


# (With a head of her own her hair is apart from her body: none of it on her.)
HAIR = np.zeros(len(P)) if HEAD else _hair()
print("HAIR", int(HAIR.sum()), "surface points")
# Her skin without her hair, for laying curves on.
_hair = (W[:, [BI[n] for n in ("Head", "neck_01") if n in BI]].sum(1) > 0.5)
_skin = ~_hair[TRI].any(1)
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI[_skin].tolist())
# Curves are laid on her skin, never on her hair.
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI[_skin & ~(HAIR[TRI] > 0.5).any(1)].tolist())
print("SURFACE", len(P), "vertices", len(TRI), "triangles")


def head(b):
    return np.array((arm.matrix_world @ arm.data.bones[b].head_local)[:])


def wsum(*names):
    return sum(W[:, BI[n]] for n in names if n in BI)


# ------------------------------------------------------------- landmarks --
X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
mid = (np.abs(X) < 0.008) & (Z > 0.8) & (Z < 1.15) & (np.abs(Y) < 0.12)
# The crotch: down the middle from the pelvis until the skin first breaks
# off (below it the middle is the gap between her thighs, or where they
# touch further down).
zs = np.sort(Z[mid])[::-1]
zs = zs[zs < head("pelvis")[2]]
gap = np.where(np.diff(zs) < -0.012)[0]
CROTCH = zs[gap[0]] if len(gap) else zs[-1]
CROTCH_Y = Y[mid][np.argmin(np.abs(Z[mid] - CROTCH))]
if "crotch" in body.keys():
    _cr = mw @ Vector(body["crotch"])
    CROTCH, CROTCH_Y = _cr.z, _cr.y
NIP = {}
for s, sd in ((1, "l"), (-1, "r")):
    m = (Z > 1.25) & (Z < 1.5) & (X * s > 0.03) & (X * s < 0.2)
    NIP[sd] = P[np.where(m)[0][np.argmin(Y[m])]]
UNDERBUST = (NIP["l"][2] + NIP["r"][2]) / 2 - 0.056
WAIST = head("spine_01")[2]
NECK = head("neck_01")
LEG = {sd: [head(f"thigh_{sd}"), head(f"calf_{sd}"), head(f"foot_{sd}"), head(f"ball_{sd}")] for sd in "lr"}
ARM = {sd: [head(f"upperarm_{sd}"), head(f"lowerarm_{sd}"), head(f"hand_{sd}"), MID01_BUILT.get(sd, head(f"middle_01_{sd}"))] for sd in "lr"}
print("LANDMARKS crotch %.3f underbust %.3f waist %.3f" % (CROTCH, UNDERBUST, WAIST))


def ramp(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def chain(pts):
    """Each vertex's place along a limb: arc length from the chain's start
    to the nearest point on it, and the distance off it."""
    best_d = np.full(len(P), 1e9)
    best_s = np.zeros(len(P))
    run = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        L = np.linalg.norm(ab)
        t = np.clip(((P - a) @ ab) / (L * L), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        better = d < best_d
        best_d[better] = d[better]
        best_s[better] = run + t[better] * L
        run += L
    return best_s, best_d


LEG_S = {}
ARM_S = {}
for sd, s in (("l", 1), ("r", -1)):
    LEG_S[sd] = chain(LEG[sd])[0]
    ARM_S[sd] = chain([head(f"clavicle_{sd}")] + ARM[sd])[0]
LEGW = {sd: wsum(f"thigh_{sd}", f"calf_{sd}", f"foot_{sd}", f"ball_{sd}") for sd in "lr"}
ARMW = {sd: wsum(*[n for n in BONES if n.endswith(f"_{sd}") and n.split("_")[0] in
                   ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")]) for sd in "lr"}
KNEE_S = np.linalg.norm(LEG["l"][1] - LEG["l"][0])
ANKLE_S = KNEE_S + np.linalg.norm(LEG["l"][2] - LEG["l"][1])
ELBOW_S = np.linalg.norm(ARM["l"][0] - head("clavicle_l")) + np.linalg.norm(ARM["l"][1] - ARM["l"][0])
WRIST_S = ELBOW_S + np.linalg.norm(ARM["l"][2] - ARM["l"][1])
FRONT = ramp(-(Y - CROTCH_Y), -0.03, 0.03)
# The slot between her thighs under the crotch (they press together there):
# its two walls face each other across a gap of a centimetre or two.
# Garments span it, as cloth does, and never dive in; below the stocking
# tops it is just her inner thighs.
SLOT = ((np.abs(X) < 0.022) & (Z < CROTCH - 0.004) & (Z > CROTCH - 0.06) & (np.abs(Y - CROTCH_Y) < 0.07)
        & (N[:, 0] * np.sign(X + 1e-9) < -0.55))
print("SLOT", int(SLOT.sum()), "points of her inner thighs under the crotch")
# The box a crossing garment is cut out of: from in front of the slot to
# behind it, below just over the crotch.
GAP_F, GAP_B, GAP_Z = CROTCH_Y - 0.03, CROTCH_Y + 0.04, CROTCH + 0.012


def thong_path(z_top, y_front=None):
    """A thong's line: down the cleft behind from z_top, then forward
    under her along the top of the slot, to tuck under the front."""
    back = back_string(z_top, CROTCH + 0.012)
    y0 = back[-1][1] - 0.004
    y1 = (GAP_F - 0.006) if y_front is None else y_front
    return back + roof_path(y0, y1, 10)


def roof_z(x, y):
    """Height of her skin straight above a point under her crotch (the top
    of the slot between her thighs), seen from below."""
    hit = BVH.ray_cast(Vector((x, y, CROTCH - 0.3)), Vector((0, 0, 1)), 0.6)
    return hit[0].z if hit[0] is not None else CROTCH


def roof_path(y0, y1, n=12, x=0.0, lift=0.003):
    """Points along the top of the slot, under her, from y0 to y1."""
    return [np.array([x, y, roof_z(x, y) - lift]) for y in np.linspace(y0, y1, n)]


def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift):
    """What carries a garment under her crotch, where it was cut away
    either side of the slot between her thighs: a gusset of even width laid
    straight along the roof of the slot, overlapping the garment's bound
    edges in front and behind."""
    # (close under her, her skin tucked under it, and each line of it moving
    # with the skin under that line, as the thongs' gussets)
    # (cut from her own skin, as the thongs' gussets: see gusset())
    # (on back under the string's foot by 1.5 cm: stopped at GAP_B, short of
    # the string, the strip between them showed as she vaulted)
    foot = back_string(CROTCH + 0.155, CROTCH + 0.012)[-1][1]
    # (LEO_GW: wider by LEO_GW[0] in front of GAP_F + LEO_GW[1], eased out
    # by GAP_F + LEO_GW[2], under the U's rounded corners)
    # (judge fin1: the gusset showed below and beside the U as a second stitched
    # lobe, a flap and a dark wedge: its own binding and stitches, its 21 mm flare
    # past the U's corners and its sides down the slot's walls (to |N_x| 0.96),
    # 4 mm off her. Now unbound, LEO_GHALF wide, up the walls only to LEO_GSTEEP,
    # LEO_GLIFT off her and LEO_GTHICK thick: on the roof of the slot, its edges in
    # the slot, the U's binding the one edge seen.)
    half = LEO_GHALF + LEO_GW[0] * ramp(-Y, -(GAP_F + LEO_GW[2]), -(GAP_F + LEO_GW[1]))
    return gusset(name + "_gusset", mkey, GAP_F - LEO_GUSSET_F, max(GAP_B + 0.014, foot + 0.015), half=half,
                  thick=LEO_GTHICK if LEO_GTHICK > 0 else thick, steep=LEO_GSTEEP, lift=LEO_GLIFT, bind=LEO_GBIND)


def gusset(name, mkey, y_front, y_back, half=0.016, steep=0.96, thick=0.0018, lift=0.001, bind=True):
    """A gusset cut from her own skin under her crotch, skin-tight (1 mm off
    her), its edges bound and her skin tucked under it: from y_front to
    y_back, |x| under `half`, and up the walls of the slot between her thighs
    only as far as they face down (|N_x| under `steep`). (A flat strip 1 mm
    under the midline crossed the walls 6 mm out, the top of the slot being
    only 4 to 8 mm wide, and left their rounded shoulders bare; hung lower,
    her skin came through it as her thighs parted.)"""
    field = AND(half - np.abs(X), (steep - np.abs(N[:, 0])) * 0.02, y_back - Y, Y - y_front,
                Z - (CROTCH - 0.015), (CROTCH + 0.03) - Z)
    made = piece(name, field, mkey, lift=lift, thick=thick, smooth=2, soften=0, slot=False, bind=bind)
    # (her skin tucked under it only 3 mm: it moves with the skin under it,
    # so it needs no more, and tucked 7 mm, as close pieces are, the walls of
    # the slot showed a gully along each of its edges as her thighs parted)
    made[0]["tuck"] = 0.3
    return made


def spline(pts, step=0.004):
    """A smooth curve through control points (Catmull-Rom, centripetal: no
    loops or overshoot where they bunch), sampled every `step` or so."""
    p = [np.array(q, float) for q in pts]
    if len(p) < 3:
        n = max(2, int(np.linalg.norm(p[-1] - p[0]) / step))
        return np.array([p[0] + (p[-1] - p[0]) * t for t in np.linspace(0, 1, n)])
    p = [2 * p[0] - p[1]] + p + [2 * p[-1] - p[-2]]
    out = []
    for k in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[k - 1], p[k], p[k + 1], p[k + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5 + 1e-9
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5 + 1e-9
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5 + 1e-9
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for t in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(p[-2])
    return np.array(out)


def on_surface(pts, step=0.004):
    """A curve through control points, sampled and laid on her skin."""
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a), np.array(b)
        n = max(2, int(np.linalg.norm(b - a) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(a + (b - a) * t)
    out.append(np.array(pts[-1]))
    return np.array([SKIN_BVH.find_nearest(Vector(p))[0][:] for p in out])


def strap(pts, width):
    """Within half the width of a curve laid on her skin."""
    d, _ = cKDTree(on_surface(pts, step=0.0015)).query(P)
    return width / 2 - d


def front_point(x, z):
    """Her skin straight in front at (x, z), as a ray from ahead finds it."""
    hit = BVH.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)), 1.2)
    return np.array(hit[0][:]) if hit[0] is not None else np.array([x, -0.1, z])


def front_poly(pts, width, n=30):
    """A line through (x, z) points down her front, on her skin as seen
    from ahead (a lacing's zigzag, a boot's laces)."""
    on = []
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        on += [front_point(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, n)]
    d, _ = cKDTree(np.array(on)).query(P)
    return width / 2 - d


def side_point(sd, y, z):
    """Her skin on her side at (y, z), as a ray from beside her finds it."""
    s_ = 1 if sd == "l" else -1
    hit = BVH.ray_cast(Vector((0.6 * s_, y, z)), Vector((-s_, 0, 0)), 1.2)
    return np.array(hit[0][:]) if hit[0] is not None else np.array([0.18 * s_, y, z])


def pouch(name, sd, y, z, size, mkey):
    """A leather pouch on her hip: a rounded box (a superellipsoid), its
    back against her skin, moving as her skin there does."""
    s_ = 1 if sd == "l" else -1
    at = side_point(sd, y, z)
    a, b, c = size
    nu, nv = 18, 32
    th = np.linspace(0.02, np.pi - 0.02, nu)[:, None]
    ph = np.linspace(0, 2 * np.pi, nv, endpoint=False)[None, :]
    e = 0.3

    def sp(v):
        return np.sign(v) * np.abs(v) ** e

    lx = a * sp(np.sin(th) * np.cos(ph))
    ly = b * sp(np.sin(th) * np.sin(ph))
    lz = c * sp(np.cos(th) * np.ones_like(ph))
    pos = np.stack([at[0] + s_ * (a + 0.004) + s_ * lx, at[1] + ly, at[2] + lz], -1).reshape(-1, 3)
    idx = np.arange(nu * nv).reshape(nu, nv)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(nu, nv + 1)]
    n = vertex_normals(pos, tris)
    if ((pos - pos.mean(0)) * n).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    _, j = cKDTree(P).query(at)
    wt = np.repeat(W[j][None, :], len(pos), 0)
    return [finish(name, pos, wt, tris, mkey, 0.002, 0.0)]


def front_line(x0, z0, x1, z1, width, n=80):
    """A line down her front from (x0, z0) to (x1, z1), on her skin as seen
    from ahead (not wandering onto her breasts, as the nearest skin would)."""
    pts = np.array([front_point(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, n)])
    d, _ = cKDTree(pts).query(P)
    return width / 2 - d


def skin_point(p):
    return np.array(SKIN_BVH.find_nearest(Vector(p))[0][:])


def AND(*f):
    return np.minimum.reduce(f)


def ANDR(a, b, r=0.01):
    """Two fields' overlap (metres, positive inside) with its corners
    rounded `r`, where AND leaves them sharp."""
    qa, qb = np.maximum(r - a, 0.0), np.maximum(r - b, 0.0)
    return r - np.hypot(qa, qb) - np.minimum(np.maximum(r - a, r - b), 0.0)


def OR(*f):
    return np.maximum.reduce(f)


# ------------------------------------------------------------- the cut --
def adjacency(n, tris):
    """Each vertex's neighbours, as a row-normalised sparse matrix."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    e = np.vstack([e, e[:, ::-1]])
    m = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    m.data[:] = 1
    deg = np.asarray(m.sum(1)).ravel()
    deg[deg == 0] = 1
    return sparse.diags(1 / deg) @ m


# (mend_body leaves each fin's tip a point in no triangle, kept so her points
# stay as many as the game's: its normal is Blender's stand-in, its own place,
# and with no neighbours the smoothing that finds bumps read the tip under her
# left breast 1.3 m proud and took it for her nipple, which moved the reaver's
# band under her breasts. Each such point takes its nearest real point's
# normal and is smoothed as that point, and is never sought as a nipple or lump.)
LOOSE = np.ones(len(P), bool)
LOOSE[TRI.ravel()] = False
LOOSE_TO = np.arange(len(P))
if LOOSE.any():
    LOOSE_TO[LOOSE] = np.where(~LOOSE)[0][cKDTree(P[~LOOSE]).query(P[LOOSE])[1]]
    N[LOOSE] = N[LOOSE_TO[LOOSE]]
    print("LOOSE points in her surface (fin tips mended away):", int(LOOSE.sum()))
ADJ = adjacency(len(P), TRI)
if LOOSE.any():
    ADJ = (ADJ + sparse.coo_matrix((np.ones(int(LOOSE.sum())), (np.where(LOOSE)[0], LOOSE_TO[LOOSE])),
                                   shape=ADJ.shape)).tocsr()
# Her breasts' weights eased up their upper slope. As authored they fell from
# most to nothing within two centimetres at the top of each breast, so in a
# swing the flesh above stayed put while the breast (and whatever she wears
# on it) moved: a hinge across her chest. Spread over about six centimetres,
# the slope moves with the breast; the rest of each point's weight makes room.
W_AUTHORED = W.copy()
_armw = W[:, [BI[n] for n in BONES if n.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "hand")]].sum(1)
for _b in ("breast_l", "breast_r"):
    if _b not in BI:
        continue
    _bi = BI[_b]
    _h = np.array((arm.matrix_world @ arm.data.bones[_b].head_local)[:])
    _wb = W[:, _bi].astype(float)
    _near = (np.linalg.norm(P - _h, axis=1) < 0.16) & (P[:, 1] < _h[1] + 0.04) & (_armw < 0.3) & (P[:, 2] > _h[2] - 0.02)
    _sm = _wb.copy()
    for _ in range(160):
        _sm = np.where(_near, ADJ @ _sm, _wb)
    _new = np.where(_near, np.maximum(_wb, 0.9 * _sm), _wb)
    _rest = 1.0 - _wb
    _scale = np.where(_rest > 1e-6, (1.0 - _new) / np.maximum(_rest, 1e-6), 1.0)
    _others = np.ones(W.shape[1], bool)
    _others[_bi] = False
    W[:, _others] = (W[:, _others] * _scale[:, None]).astype(W.dtype)
    W[:, _bi] = _new.astype(W.dtype)
print("BREAST WEIGHTS eased at", int((np.abs(W - W_AUTHORED).sum(1) > 1e-4).sum()), "points")
# All her skin's weights eased over about 1.5 cm (but her hands' and head's,
# which shape fingers and a face), and cut to four bones smoothly: her
# skin's weights jump from point to point, and where a garment's eased
# edge lay on them, her skin moved by another rule and came through the
# edge in steps when she moved. Garments take these, so the two agree.
# (armor 18 g3: her wrists eased too. Kept at a hand share over 0.05, the wrist's points just under it took the eased
# hand share (up to 0.4) beside kept points at 0.06-0.1 nearer the hand: weights out of order along her arm, and a bent
# hand folded her inner wrist (a dark speck at the town close-up). Now the authored rows come back in smoothly between a
# hand share of 0.05 and WRIST_KEEP (0.6), so the wrist is one 1.5 cm blend and her palm and fingers keep theirs. Her
# head's rule is as it was. WRIST_KEEP=0 restores the old cut.)
_hs = wsum(*[n for n in BONES if n.split("_")[0] in ("hand", "index", "middle", "ring", "pinky", "thumb")])
_keep = (_hs > 0.05) | (wsum(*[n for n in BONES if n.split("_")[0] == "Head"]) > 0.05)
_wk1 = float(os.environ.get("WRIST_KEEP", "0.6"))
_el = np.linalg.norm(P[TRI[:, 0]] - P[TRI[:, 1]], axis=1)
_rounds = int(np.clip((0.015 / float(np.median(_el))) ** 2, 0, 80))
_W = W.copy()
for _ in range(_rounds):
    _W = ADJ @ _W
if _wk1 > 0.05:
    _kh = np.clip((_hs - 0.05) / (_wk1 - 0.05), 0, 1)
    _kh = _kh * _kh * (3 - 2 * _kh)
    _kf = np.where(wsum(*[n for n in BONES if n.split("_")[0] == "Head"]) > 0.05, 1.0, _kh)
    W = _kf[:, None] * W + (1 - _kf[:, None]) * _W
    print("WRIST_KEEP %.2f: %d points of her wrists blend authored and eased weights" % (_wk1, int(((_kf > 0) & (_kf < 1)).sum())))
else:
    W = np.where(_keep[:, None], W, _W)
_fifth = -np.partition(-W, 4, axis=1)[:, 4]
W = np.maximum(W - _fifth[:, None], 0)
W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
print("SKIN WEIGHTS eased over", _rounds, "rounds, all but", int(_keep.sum()), "points of her hands and head")


# Within 4 cm of the skin heroine_head.py made anew over her shoulders
# (where her own skin meets coarser, the smoothing that finds bumps finds
# them all along the join): no nipple sought there, no lump filled.
_ga = body.data.attributes.get("graft")
if _ga:
    _gv = np.zeros(len(body.data.vertices), int)
    _ga.data.foreach_get("value", _gv)
    _gp = np.array([(body.matrix_world @ body.data.vertices[i].co)[:] for i in np.nonzero(_gv)[0]])
    NEAR_GRAFT = cKDTree(_gp).query(P)[0] < 0.04
else:
    NEAR_GRAFT = np.zeros(len(P), bool)


def nipples():
    """Each nipple: the most proud small bump on the breast (proud of her
    skin smoothed over a centimetre or so, so the breast's own curve does
    not count), away from the cleavage. Hers sit high and to the outside,
    not at the breast's most forward point."""
    S = P.copy()
    for _ in range(12):
        S = ADJ @ S
    proud = ((P - S) * N).sum(1)
    # The strongest such bump on either breast; the other nipple is sought
    # near its mirror image (they are level), so a lump elsewhere on one
    # breast cannot be taken for it.
    m = (np.abs(P[:, 0]) > 0.07) & (P[:, 2] > 1.3) & (P[:, 2] < 1.5) & (P[:, 1] < -0.05) & ~NEAR_GRAFT & ~LOOSE
    first = P[np.where(m)[0][np.argmax(proud[m])]]
    out = {}
    for s, sd in ((1, "l"), (-1, "r")):
        guess = np.array([abs(first[0]) * s, first[1], first[2]])
        near = np.where((np.linalg.norm(P - guess, axis=1) < 0.02) & ~NEAR_GRAFT & ~LOOSE)[0]
        out[sd] = P[near[np.argmax(proud[near])]]
        print("NIPPLE", sd, out[sd].round(3), "proud %.4f" % proud[near].max())
    return out


NIPPLE = nipples()


def filled_nipples(radius=0.03, rounds=4000):
    """Her skin with only each nipple and its raised areola filled in, all else
    untouched: armour cut from this is exactly her shape, without the point.
    The fill carries the breast's own curvature across the patch (the
    surface whose bending is least, not the flattest one, which would leave
    a dent where the nipple was)."""
    out = P.copy()
    inside = np.zeros(len(P), bool)
    for n in NIPPLE.values():
        inside |= np.linalg.norm(P - n, axis=1) < radius
    # Any other small lump or dent on the breasts (the sculpt has a lump low
    # on her left), so a cup copies her shape and not its flaws.
    S = P.copy()
    for _ in range(12):
        S = ADJ @ S
    proud = ((P - S) * N).sum(1)
    breast = (np.abs(P[:, 0]) > 0.03) & (P[:, 2] > 1.28) & (P[:, 2] < 1.5) & (P[:, 1] < -0.05)
    # Dents as well as lumps (a crease at the top of her left breast).
    lumps = P[breast & (np.abs(proud) > 0.0018) & ~NEAR_GRAFT & ~LOOSE]
    if len(lumps):
        d, _ = cKDTree(lumps).query(P)
        inside |= breast & (d < 0.02)
    # And her crotch, where the sculpt's skin between her thighs is
    # crumpled: a garment lies on it smooth.
    crotch = np.array([0.0, CROTCH_Y, CROTCH])
    inside |= (np.linalg.norm(P - crotch, axis=1) < 0.045) & (np.abs(X) < 0.04)
    print("FILLED", int(inside.sum()), "vertices of skin under cups")
    for _ in range(60):
        out = np.where(inside[:, None], ADJ @ out, out)
    for _ in range(rounds):
        lap = ADJ @ out - out
        out = np.where(inside[:, None], out - 0.15 * (ADJ @ lap - lap), out)
    return out


P_FILLED = filled_nipples()


def breast_ellipsoid():
    """An ellipsoid fitted to the front of both her breasts (her left
    mirrored onto her right, so the pair is one shape): the frame her cups'
    form is measured in. Its centre, axes (rows of R) and radii, on her
    right; and its radii grown to hold all of both breasts, nipples and all
    (the line the stalker's corset follows round their undersides)."""
    mirror = np.array([-1.0, 1.0, 1.0])
    front, whole = [], []
    for side_, sg in (("r", -1), ("l", 1)):
        q = NIPPLE[side_]
        near = (np.linalg.norm(P - q, axis=1) < 0.075) & (N[:, 1] < -0.3) & (P[:, 0] * sg > 0.01)
        held = (W_AUTHORED[:, BI[f"breast_{side_}"]] > 0.15) & (P[:, 0] * sg > 0.005) & (N[:, 1] < 0.0)
        flip = mirror if sg > 0 else np.ones(3)
        front.append(P_FILLED[near] * flip)
        whole.append(P[held] * flip)
    q0 = np.vstack(front)
    m = q0.mean(0)
    _, _, R = np.linalg.svd(q0 - m)
    loc = (q0 - m) @ R.T
    k, *_ = np.linalg.lstsq(np.c_[loc ** 2, loc], np.ones(len(loc)), rcond=None)
    A, B, C, D, E, F = k
    cl = -np.array([D / (2 * A), E / (2 * B), F / (2 * C)])
    g = 1 + A * cl[0] ** 2 + B * cl[1] ** 2 + C * cl[2] ** 2
    ax = np.sqrt(g / np.array([A, B, C]))
    c = m + cl @ R
    held = (np.vstack(whole) - c) @ R.T
    hold = np.sqrt(((held / ax) ** 2).sum(1)).max()
    return c, R, ax, ax * hold


def breast_form(c, R, ax):
    """Her breasts' own form, smooth: how far out it is in each direction
    from the ellipsoid's centre (as a part of the ellipsoid's radius there),
    hugging her breasts with the nipples filled (both, her left mirrored
    onto her right, so the pair is one shape). A membrane laid over them (it bridges a dip, never sinks into one),
    eased over about a centimetre, and lifted only where some of her stands
    proud of the eased one, by as much: it holds all of her, a few
    millimetres off at most. (An ellipsoid grown to hold all of her stood a
    centimetre off her breasts: the cups looked a size too big and showed
    her through the gap.) Returns a function of unit directions (in the
    ellipsoid's scaled frame)."""
    mirror = np.array([-1.0, 1.0, 1.0])
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=5, radius=1.0)
    U = np.array([v.co[:] for v in ico.verts])
    ico.free()
    U /= np.linalg.norm(U, axis=1)[:, None]
    tree = cKDTree(U)

    def kernel(sig):
        rows, cols, vals = [], [], []
        for i, nb in enumerate(tree.query_ball_point(U, 3 * sig)):
            w = np.exp(-0.5 * (np.linalg.norm(U[nb] - U[i], axis=1) / sig) ** 2)
            rows += [i] * len(nb)
            cols += nb
            vals += list(w / w.sum())
        return sparse.csr_matrix((vals, (rows, cols)), shape=(len(U), len(U)))

    # Her breasts themselves (not her ribs below them, so the form turns into
    # her at the crease under each, where a cup ends), as her skin is, but
    # for each nipple and its areola, filled. (The fill elsewhere sinks into
    # the curve under them, and a form fitted to it went into her there.)
    pts = []
    for side_, sg in (("r", -1), ("l", 1)):
        d = np.linalg.norm(P - NIPPLE[side_], axis=1)
        m = (W_AUTHORED[:, BI[f"breast_{side_}"]] > 0.15) & (d < 0.11) & (P[:, 0] * sg > 0.0) & (N[:, 1] < 0.3)
        pts.append(np.where((d < 0.03)[:, None], P_FILLED, P)[m] * (mirror if sg > 0 else np.ones(3)))
    v = ((np.vstack(pts) - c) @ R.T) / ax
    rho = np.linalg.norm(v, axis=1)
    _, i = tree.query(v / rho[:, None])
    t = np.full(len(U), -np.inf)
    np.maximum.at(t, i, rho)
    has = np.isfinite(t)
    f = t.copy()
    f[~has] = t[has][cKDTree(U[has]).query(U[~has])[1]]
    small, big = kernel(0.04), kernel(0.07)
    for _ in range(60):
        f = np.where(has, np.maximum(t, small @ f), small @ f)
    f = big @ (big @ f)
    proud = np.where(has, np.maximum(t - f, 0), 0)
    f = f + big @ np.array([proud[nb].max() for nb in tree.query_ball_point(U, 0.18)])
    f = f + max(0.0, (t[has] - f[has]).max())

    def at(dirs):
        d, j = tree.query(dirs, 6)
        w = np.exp(-0.5 * (d / 0.02) ** 2) + 1e-12
        return (f[j] * w).sum(1) / w.sum(1)
    fr = at(v / rho[:, None])
    gap = (fr - rho) / fr * np.linalg.norm(np.vstack(pts) - c, axis=1)
    print("BREAST FORM off her by %.1f mm (median), %.1f (most), %.1f (least)" % (np.median(gap) * 1e3, gap.max() * 1e3, gap.min() * 1e3))
    return at


_c, _R, _ax, _ax_hold = breast_ellipsoid()
BREAST_FORM = (_c, _R, _ax, breast_form(_c, _R, _ax))
BREAST_HOLD = (_c, _R, _ax_hold)


def ideal_breasts(surface, full=0.05, fade=0.09):
    """A surface with her breasts made the perfect form: each point of each
    breast sent out along its normal to the form (only out, never in, and
    only where the form is near her), fully within `full` of her nipple,
    fading to her own
    shape by `fade`, so whatever is cut from it is uniform over her breasts
    (no lumps, no nipples) and still meets her skin at its edges."""
    c, R, ax, form = BREAST_FORM
    out = surface.copy()
    for sd, sg in (("r", -1), ("l", 1)):
        flip = np.array([sg * -1.0, 1.0, 1.0])            # (her left onto her right and back)
        q = surface * flip
        loc = (q - c) @ R.T
        r_e = np.sqrt(((loc / ax) ** 2).sum(1))
        reach = form(loc / ax / np.maximum(r_e, 1e-9)[:, None])
        r_ell = r_e / reach                               # (1 on the form)
        on = c + (loc / np.maximum(r_ell, 1e-9)[:, None]) @ R
        d = np.linalg.norm(surface - NIPPLE[sd], axis=1)
        w = np.clip((fade - d) / (fade - full), 0, 1)
        w = w * w * (3 - 2 * w)
        mine = (surface[:, 0] * sg > 0.0) & (r_ell < 1.0) & (w > 0)
        # Out along her skin's own normal, and only where the form is a few
        # millimetres off her: past where it was fitted (toward her arms) it
        # only carries on from its edge, and her skin sent out to it there,
        # sideways along the line from its centre, folded over itself.
        n_q = N * flip
        g = np.maximum(((on - q) * n_q).sum(1), 0)
        k = np.clip((0.008 - g) / 0.004, 0, 1)
        out[mine] = (q[mine] + n_q[mine] * (g * w * k)[mine, None]) * flip
    return out


# Garments over her breasts are cut from the perfect form, and never lie
# inside her own skin there (the fill that eases her breasts' lumps sinks
# up to centimetres into the curve under them; skin would show through).
P_FILLED = ideal_breasts(P_FILLED)
# (but for her nipples and areolae, which stay filled: kept out to her skin
# there, her nipples came back into everything cut over them, and through
# a plate cup)
_on_breast = (wsum("breast_l", "breast_r") > 0.01) & (np.minimum(*[np.linalg.norm(P - q, axis=1) for q in NIPPLE.values()]) > 0.03)
_out = ((P_FILLED - P) * N).sum(1)
P_FILLED = np.where((_on_breast & (_out < 0))[:, None], P_FILLED - N * _out[:, None], P_FILLED)
print("BREAST FILL kept out of her at", int((_on_breast & (_out < 0)).sum()), "points")


def untangled(S, rounds=300):
    """A surface made from her skin with no triangle turned over: sent out
    to her breasts' form, the skin at their sides toward her arms folded
    over itself, and a garment cut there showed the fold as a black notch.
    Each folded triangle and two rings round it are eased toward their
    neighbours, and kept out of her, until none is left."""
    def normals(Q):
        return np.cross(Q[TRI[:, 1]] - Q[TRI[:, 0]], Q[TRI[:, 2]] - Q[TRI[:, 0]])
    n0 = normals(P)
    first = None
    for k in range(rounds):
        flip = (normals(S) * n0).sum(1) <= 0
        if first is None:
            first = int(flip.sum())
        if not flip.any():
            break
        bad = np.zeros(len(S))
        bad[TRI[flip].ravel()] = 1
        for _ in range(2):
            bad = np.maximum(bad, (ADJ @ bad > 0).astype(float))
        S = np.where(bad[:, None] > 0, 0.5 * S + 0.5 * (ADJ @ S), S)
        o = ((S - P) * N).sum(1)
        S = np.where((bad > 0)[:, None] & (o < 0)[:, None], S - N * o[:, None], S)
    print("UNTANGLED", first, "folded triangles, left", int(((normals(S) * n0).sum(1) <= 0).sum()), "after", k + 1, "rounds")
    return S


P_FILLED = untangled(P_FILLED)


def smooth_field(f, k=3):
    """A field eased over her surface, so its zero line has no kinks from
    the triangles or the weights it was made from."""
    for _ in range(k):
        f = 0.5 * f + 0.5 * (ADJ @ f)
    return f


def clip(f, pos, attr, tris):
    """The part of a surface where f >= 0, cut along f = 0 between vertices:
    positions, attributes (interpolated) and triangles."""
    f = np.where(np.abs(f) < 1e-6, 1e-6, f)
    inside = f >= 0
    keep_tri = inside[tris].all(1)
    mixed = inside[tris].any(1) & ~keep_tri
    used = np.where(inside)[0]
    idx = -np.ones(len(pos), int)
    idx[used] = np.arange(len(used))
    out_p, out_a = [pos[used]], [attr[used]]
    out_t = [idx[tris[keep_tri]]]
    cut, extra = {}, []

    def edge(a, b):
        k = (min(a, b), max(a, b))
        if k not in cut:
            t = f[a] / (f[a] - f[b])
            cut[k] = len(used) + len(extra)
            extra.append((pos[a] * (1 - t) + pos[b] * t, attr[a] * (1 - t) + attr[b] * t))
        return cut[k]

    more = []
    for tri in tris[mixed]:
        poly = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if inside[a]:
                poly.append(idx[a])
            if inside[a] != inside[b]:
                poly.append(edge(a, b))
        for i in range(1, len(poly) - 1):
            more.append((poly[0], poly[i], poly[i + 1]))
    if extra:
        out_p.append(np.array([e[0] for e in extra]))
        out_a.append(np.array([e[1] for e in extra]))
    if more:
        out_t.append(np.array(more))
    p2, a2, t2 = np.concatenate(out_p), np.concatenate(out_a), np.concatenate(out_t).astype(int)
    if len(t2) == 0:
        return p2[:0], a2[:0], t2
    # Only the vertices some triangle uses.
    live = np.unique(t2)
    re = -np.ones(len(p2), int)
    re[live] = np.arange(len(live))
    return p2[live], a2[live], re[t2]


def weld(pos, attr, tris, r=0.0007, joined=False):
    """Points closer than r made one (the cut leaves slivers by the vertices
    it passes close to); triangles that collapse are dropped. `joined`: only
    points an edge of the sheet joins (her skin folds back on itself at a
    nail's edge and in the creases of her fingers, and a weld by distance
    alone zipped a glove shut across those folds; thickened and bevelled,
    the zips tore open, judge 14)."""
    if os.environ.get("WELDDUMP"):  # SOLVER1 TEMP
        global _WELD_N
        _WELD_N = globals().get("_WELD_N", 0) + 1
        _nm = sys._getframe(1).f_locals.get("name", sys._getframe(1).f_code.co_name)
        np.savez(os.path.join(os.environ["WELDDUMP"], "weld_%04d_%s.npz" % (_WELD_N, _nm)), pos=pos, tris=tris, r=r,
                 caller=sys._getframe(1).f_code.co_name, line=sys._getframe(1).f_lineno)
    parent = np.arange(len(pos))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    pairs = cKDTree(pos).query_pairs(r, output_type="ndarray")
    if joined and len(pairs):
        e_ = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
        k_ = np.unique(e_[:, 0].astype(np.int64) * len(pos) + e_[:, 1])
        ps_ = np.sort(pairs, 1)
        pairs = pairs[np.isin(ps_[:, 0].astype(np.int64) * len(pos) + ps_[:, 1], k_)]
    for i, j in pairs:
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    root = np.array([find(i) for i in range(len(pos))])
    keys, inv = np.unique(root, return_inverse=True)
    cnt = np.bincount(inv)
    p2 = np.zeros((len(keys), 3))
    np.add.at(p2, inv, pos)
    a2 = np.zeros((len(keys), attr.shape[1]))
    np.add.at(a2, inv, attr)
    p2 /= cnt[:, None]
    a2 /= cnt[:, None]
    t2 = inv[tris]
    ok = (t2[:, 0] != t2[:, 1]) & (t2[:, 1] != t2[:, 2]) & (t2[:, 2] != t2[:, 0])
    t2 = t2[ok]
    area = np.linalg.norm(np.cross(p2[t2[:, 1]] - p2[t2[:, 0]], p2[t2[:, 2]] - p2[t2[:, 0]]), axis=1)
    return p2, a2, cancelled(t2[area > 1e-10])


def cancelled(tris):
    """Triangles on the same three points (a sliver the weld folded flat)
    cancelled by their winding, as a fold of no area: left in, three or four
    triangles met at an edge, the walk round the sheet's rim broke there, and
    the piece's edge was left as cut (the warden's left pauldron, unbound)."""
    st = np.sort(tris, 1)
    _, inv, cnt = np.unique(st, axis=0, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).ravel()
    dup = cnt[inv] > 1
    if not dup.any():
        return tris
    # (+1 where a triangle runs round its sorted points, -1 the other way)
    r = np.argmin(tris, 1)
    par = np.where(tris[np.arange(len(tris)), (r + 1) % 3] == st[:, 1], 1, -1)
    keep = ~dup
    for g in np.unique(inv[dup]):
        ids = np.where(inv == g)[0]
        net = int(par[ids].sum())
        keep[ids[par[ids] == np.sign(net)][:abs(net)]] = True
    return tris[keep]


def vertex_normals(pos, tris):
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    vn = np.zeros_like(pos)
    for k in range(3):
        np.add.at(vn, tris[:, k], fn)
    return vn / (np.linalg.norm(vn, axis=1)[:, None] + 1e-12)


def relax(pos, tris, interior=0, edge=12):
    """Smoothing: the inside (plate spanning hollows) and, along itself
    only, the edge, so a cut runs as one clean curve."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    be = uk[c == 1]
    n = len(pos)
    onb = np.zeros(n, bool)
    onb[be.ravel()] = True
    B = sparse.coo_matrix((np.ones(2 * len(be)), (np.r_[be[:, 0], be[:, 1]], np.r_[be[:, 1], be[:, 0]])), shape=(n, n)).tocsr()
    db = np.asarray(B.sum(1)).ravel()
    B = sparse.diags(1 / np.maximum(db, 1)) @ B
    A = adjacency(n, tris)
    for _ in range(interior):
        pos = np.where(onb[:, None], pos, 0.5 * pos + 0.5 * (A @ pos))
    # Along the edge only where it is a simple line (two edge neighbours).
    line = (onb & (db == 2))[:, None]
    for _ in range(max(edge, interior)):
        pos = np.where(line, 0.5 * pos + 0.5 * (B @ pos), pos)
    return pos


# ------------------------------------------------------------- materials --
# Each material: its scan, a tint, the mean brightness its colour is brought
# to (None keeps the scan's), how many times it repeats in a metre, and its
# metalness and roughness where the scan has no map of them. The colour is
# baked into a texture of the material's own (outfit_<key>_diff.jpg), so the
# game gets exactly what was made here.
# (s27 glove round 2: GLOVE_IVORY "r,g,b,mean" the glove an ivory under 255 so its highlight has room
# (judge gl r1: paper-white by day); GLOVE_PIPE_MAT "r,g,b,mean,rough" the piping matched to the
# leotard's plum (it read navy-black); GLOVE_THREAD_MAT likewise for the back-of-hand points)
_GIV = [float(v) for v in os.environ.get("GLOVE_IVORY", "").split(",") if v]
_GPM = [float(v) for v in os.environ.get("GLOVE_PIPE_MAT", "0.60,0.42,0.72,58,0.30").split(",")]
_GTM = [float(v) for v in os.environ.get("GLOVE_THREAD_MAT", "1.652,1.379,1.12,240,0.22").split(",")]
# (s29 judge tri, 17 Oct: the stockings a cool flat white beside the glove's ivory and plum piping, "two unrelated
# whites". STOCK_IVORY=1 tints the sheer and its top band to the glove's ivory (GLOVE_IVORY) and pipes the band's edges in
# the glove's plum, STOCK_WELT "width,lift,thick" (m); the game's sheer shader takes the stocking's mean colour from
# outfit_materials.json "tint", written only then, so the default stays as it was.)
STOCK_IVORY = os.environ.get("STOCK_IVORY", "") == "1" and bool(_GIV) and bool(os.environ.get("GLOVE_STYLE"))
STOCK_WELT = tuple(float(v) for v in os.environ.get("STOCK_WELT", "0.006,0.0008,0.0015").split(","))
# (s29 judge tri: the Arcanist's boots "flat, soleless, paddle-shaped black feet ... rubber socks" at the mid zoom.
# ARC_BOOT=made lofts them as the Ranger's boot is (heroine_boots.boot: toe box, welted sole, heel block), black, the
# front of the top ARC_BOOT_LIFT higher than the back as before; ARC_BOOT_ST "toe,toe_point,heel" (m) its toe and heel.)
ARC_BOOT = os.environ.get("ARC_BOOT", "made")   # (judge b1, 17 Oct: PASS at 1:1, "made black knee boots"; "" the old fitted sock)
ARC_BOOT_LIFT = float(os.environ.get("ARC_BOOT_LIFT", "0.03"))
ARC_BOOT_SOLE = os.environ.get("ARC_BOOT_SOLE", "darkleather")
_ABS = [float(v) for v in os.environ.get("ARC_BOOT_ST", "0.010,0.022,0.012").split(",")]
ARC_BOOT_ST = dict(BOOTS.RANGER, toe=_ABS[0], toe_point=_ABS[1], heel=_ABS[2])
ARC_BOOT_ST.update({k_: float(v_) for k_, v_ in (kv.split("=") for kv in os.environ.get("ARC_BOOT_KV", "w_ankle=0.015,w_shaft=0.022,c_shaft=0.003,c_ankle=0.003").split(",") if kv)})   # (any other key of BOOTS.RANGER, "k=v,...")
SPEC = {
    "steel": ("Metal038", (1.0, 1.0, 1.02), 175, 2.5, 1.0, None),
    "darksteel": ("Metal046B", (1.0, 1.0, 1.05), 95, 2.5, 1.0, None),
    "iron": ("Metal046B", (0.92, 0.84, 0.74), 88, 2.5, 1.0, 0.5),
    "rivetbronze": ("Metal046B", (1.0, 0.8, 0.6), 100, 2.5, 1.0, 0.48),   # (the spaulder's rivets dark bronze, not black dots, judge 7)   # (rivets: warm dark iron, an even sheen; at 72 they read as black dots beside the plate, judge 6)
    "gold": ("Metal048C", (1.0, 0.88, 0.7), None, 3, 1.0, None),   # (warmer: it read olive, judge 8)
    "claspgold": ("Metal048C", (252, 194, 108), None, 3, 1.0, 0.22),   # (the arcanist's clasp: a warm yellow gold, about sRGB 255,200,125 lit, polished; the scan's grain kept and its colour set, judge 9)
    "rust": ("Metal053C", (1, 1, 1), None, 2.5, 0.8, None),
    "leather": ("Leather037", (1, 1, 1), None, 4, 0.0, None),
    "darkleather": ("Leather026", (1.0, 0.8, 0.65), 30, 3, 0.0, None),
    "redleather": ("Leather024", (1, 1, 1), None, 4, 0.0, None),
    "oldleather": ("Leather014", (1, 0.96, 0.62), None, 4, 0.0, None),   # (Body 17: the scan is rose-grey, hue 8: the reaver's gear read dusty mauve on deep skin and her boots grey; hue 26, sat 0.6, same value, judge PASS)
    # (Body 18, the reaver's hide turnshoes (judge at 1:1: "shaft one smooth tone ... higher thong contrast"): "hide" the
    # oldleather's scan and tint, its grain a third coarser, with broad tonal patches and pale scuffs baked in (HIDE_MOTTLE
    # "patch,scuff" strengths; 0,0 = oldleather's look); "rawhide" the pale thongs crossing it)
    "hide": ("Leather014", (1, 0.96, 0.62), None, 3, 0.0, None),
    # (Body 18, judge: "salmon-pink ... reads as ballet/gladiator ribbons, not rawhide": desaturated toward yellow-cream,
    # the scan's own R:G:B 1.46:1:0.93 tinted to ~1.12:1:0.74, mean 122 -> 108 (frame about #736349, luma ~90);
    # was (1.0, 0.9, 0.72), 122)
    # (Body 18 r4, judge: "they read blue-grey cord in frame (R/G 1.04-1.09, luma 33-47)": the leather's sheen of the sky
    # on a dark cord; now 1.11:1:0.6 at a mean 195, its grain evened to 0.55 (RAWHIDE_EVEN) so the light end doesn't clip
    # flat, and its roughness floor 0.85 (outfit_materials.json): in frame sunlit R/G 1.18-1.19, G/B 1.6, luma 80-85)
    "rawhide": ("Leather014", (0.76, 1.0, 0.644), 195, 3, 0.0, None),
    # (Body 18, judge on the panel: "a burnished edge, a 4-6 mm band ~35% lighter on both long edges and the hem":
    # oldleather's scan and tint at a mean 35% over its own 54, a little glossier where hands and wear polish it)
    "burnished": ("Leather014", (1, 0.96, 0.62), 73, 4, 0.0, 0.62),
    "velvet": ("velour_velvet", (0.32, 0.1, 0.45), None, 5, 0.0, None),
    "linen": ("rough_linen", (0.3, 0.4, 0.25), None, 5, 0.0, None),
    "fur": ("curly_teddy_natural", (0.55, 0.42, 0.32), 70, 4, 0.0, 0.9),
    "arcvelvet": ("velour_velvet", (0.3, 0.3, 1.0), 66, 5, 0.0, None),
    "plumleather": ("Leather026", (0.5, 0.4, 0.75), 44, 3, 0.0, None),
    "blackleather": ("Leather026", (1, 1, 1), 26, 3, 0.0, None),
    "brownleather": ("Leather037", (1, 0.8, 0.68), 30, 3, 0.0, None),
    "lace": ("rough_linen", (1.652, 1.379, 1.12), 235, 14, 0.0, 0.5, 0.85),
    "darkpurple": ("Leather026", (0.55, 0.2, 0.9), 26, 3, 0.0, 0.35),
    "satin": ("rough_linen", (1.652, 1.379, 1.12), 235, 10, 0.0, 0.3),
    # (s21, her gloves: the stockings' bands' white, a finer weave and a softer sheen over a forearm's length)
    "glovesatin": ("rough_linen", (1.652, 1.379, 1.12), 228, 40, 0.0, 0.3) if not os.environ.get("GLOVE_STYLE") else
                  (("rough_linen", tuple(_GIV[:3]), _GIV[3], 40, 0.0, 0.25) if _GIV else ("rough_linen", (1.652, 1.379, 1.12), 212, 40, 0.0, 0.25)),   # (s23 judge gl1: 0.45 read matte cotton; a satin sheen. s24 GLOVE_STYLE S1: 212/0.25, headroom for its highlight)
    # (s24 GLOVE_STYLE S2: the gloves' plum piping (the leotard's plum, a touch lighter than plumleather),
    # a less mirror-like gold for small parts, an ivory silk thread a shade over the glove)
    **({"glovepipe": ("rough_linen", tuple(_GPM[:3]), _GPM[3], 40, 0.0, _GPM[4]),
        "wiregold": ("Metal048C", (252, 194, 108), None, 3, 1.0, 0.34),
        "glovethread": ("rough_linen", tuple(_GTM[:3]), _GTM[3], 60, 0.0, _GTM[4])} if os.environ.get("GLOVE_STYLE") else {}),
    "gloveblack": ("rough_linen", (0.3, 0.3, 0.34), 24, 40, 0.0, 0.46),   # (s23 judge gl1: 0.4 near wet-look in the fist close)
    "amethyst": ("rough_linen", (0.62, 0.18, 0.64), 100, 10, 0.0, 0.12),   # (the clasp's violet stone: deep and glossy)
    "greenleather": ("Leather026", (0.42, 0.85, 0.45), 52, 3, 0.0, None),
    "bronze": ("Brushed", (0.72, 0.58, 0.46), 95, 3, 1.0, 0.42),  # (our own brushing, along u: tools/assets/brushed_metal.py)
    "ink": ("rough_linen", (0.22, 0.26, 0.34), 22, 10, 0.0, 0.65),
    "stocking": ("rough_linen", tuple(_GIV[:3]), _GIV[3], 14, 0.0, 0.45, 0.42) if STOCK_IVORY else ("rough_linen", (1.624, 1.356, 1.11), 232, 14, 0.0, 0.45, 0.42),
    # (the linen scan is blue, about (145, 171, 205): these two are tinted from
    # it to a colour, warm ivory and a light saddle brown)
    # (the arcanist's feathery trim: soft white, drawn as fur shells, finer and longer)
    "down": ("rough_linen", (1.45, 1.24, 1.03), 228, 3, 0.0, 0.9),
    "bone": ("rough_linen", (1.376, 1.099, 0.779), 183, 12, 0.0, 0.5),
    "browncloth": ("rough_linen", (0.75, 0.55, 0.36), 78, 18, 0.0, 0.8),  # (a light brown: the old tint read olive)
    "forestleather": ("Leather026", (0.42, 0.66, 0.42), 40, 3, 0.0, None),
    # (her boots and their cuffs: a darker, greyer green, matte as worn
    # leather is, its grain finer so it does not mottle; judge 2)
    "bootleather": ("Leather026", (0.5, 0.6, 0.46), 32, 7, 0.0, 0.62),
    "thread": ("rough_linen", (1.349, 1.034, 0.682), 170, 60, 0.0, 0.5),
}
MATS = {}
HIDE_MOTTLE = [float(v) for v in os.environ.get("HIDE_MOTTLE", "1,1").split(",")]


def _hide_mottle(col, seed=18):
    """(Body 18) A worn hide's broad unevenness, tileable (the texture repeats): tonal patches a few cm across
    (2-7 cycles a tile, about +-14%), finer mottling, a few darker stains, and pale scuffs (short abraded
    streaks, mostly across the leg, lighter and a touch greyer). Its mean kept."""
    h, w = col.shape[:2]
    rng = np.random.default_rng(seed)
    fy, fx = np.fft.fftfreq(h) * h, np.fft.rfftfreq(w) * w
    kk = np.hypot(fy[:, None], fx[None, :])

    def band(k0, k1, p):
        spec = (rng.normal(size=kk.shape) + 1j * rng.normal(size=kk.shape)) * ((kk >= k0) & (kk <= k1)) / np.maximum(kk, 1) ** p
        f = np.fft.irfft2(spec, s=(h, w))
        return f / (f.std() + 1e-9)
    pa, sc = HIDE_MOTTLE
    m = 1 + pa * (0.16 * band(2, 7, 0.5) + 0.05 * band(8, 24, 0.3))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lift = np.zeros((h, w), np.float32)
    for k in range(28):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        th = rng.normal(0, 0.5)
        ln, wd = rng.uniform(22, 60), rng.uniform(9, 20)
        dy, dx = (yy - cy + h / 2) % h - h / 2, (xx - cx + w / 2) % w - w / 2
        u, v = dx * np.cos(th) + dy * np.sin(th), -dx * np.sin(th) + dy * np.cos(th)
        lift = np.maximum(lift, rng.uniform(0.5, 1) * np.exp(-(u / ln) ** 2 - (v / wd) ** 2))
    lift = lift * np.clip(0.55 + 0.45 * band(30, 90, 0.0), 0, 1)   # (abraded patchily, not a clean stroke)
    stain = np.zeros((h, w), np.float32)
    for k in range(6):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        dy, dx = (yy - cy + h / 2) % h - h / 2, (xx - cx + w / 2) % w - w / 2
        r_ = rng.uniform(40, 110)
        stain = np.maximum(stain, np.exp(-(dx * dx + dy * dy) / (r_ * r_)))
    m = m * (1 - 0.2 * pa * stain)
    mean0 = col.mean((0, 1))
    c = col * np.clip(m, 0.55, 1.5)[..., None]
    grey = c.mean(2, keepdims=True)
    scuff = sc * lift[..., None]
    c = c * (1 + 0.45 * scuff) * (1 - 0.25 * scuff) + grey * 1.45 * 0.25 * scuff
    return c * (mean0 / c.mean((0, 1)))


RAWHIDE_EVEN = float(os.environ.get("RAWHIDE_EVEN", "0.55"))   # (Body 18 r4: the thongs' grain contrast about its mean)


def mat(key):
    if key in MATS:
        return MATS[key]
    src, tint, mean, _, metal, rough = SPEC[key][:6]
    alpha = SPEC[key][6] if len(SPEC[key]) > 6 else 1.0
    from PIL import Image
    col = np.asarray(Image.open(os.path.join(TEX, f"{src}_diff.jpg")).convert("RGB"), np.float32)
    col = col * np.array(tint)
    if key in ("claspgold", "wiregold"):
        lum = col.mean(2, keepdims=True)
        col = np.clip(lum / lum.mean(), 0.92, 1.08) * np.array(tint)
    if mean:
        col = col * (mean / col.mean())
    if key in ("steel", "darksteel", "iron", "gold", "bronze", "rivetbronze"):
        # Scratches and flecks in the scan read as white specks at this scale.
        med = np.median(col.reshape(-1, 3), 0)
        col = np.clip(col, med * 0.8, med * 1.18)
    if key == "hide":
        col = _hide_mottle(col)
    if key == "rawhide":
        mu = col.reshape(-1, 3).mean(0)
        col = mu + RAWHIDE_EVEN * (col - mu)
    out = os.path.join(TEX, f"outfit_{key}_diff.jpg")
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(out, quality=92)
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def img(path, non_color=False):
        if not os.path.exists(path):
            return None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        return n

    d = img(out)
    nt.links.new(d.outputs["Color"], bsdf.inputs["Base Color"])
    r = img(os.path.join(TEX, f"{src}_rough.jpg"), True)
    if r and rough is None:
        nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = rough if rough is not None else 0.55
    mm = img(os.path.join(TEX, f"{src}_metal.jpg"), True)
    if mm and key not in ("claspgold", "wiregold"):
        nt.links.new(mm.outputs["Color"], bsdf.inputs["Metallic"])
    else:
        bsdf.inputs["Metallic"].default_value = metal
    n = img(os.path.join(TEX, f"{src}_nor.jpg"), True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    MATS[key] = m
    return m


# ------------------------------------------------------------- bindings --
def smooth_closed(curve, sigma, step=0.002):
    """A closed line resampled evenly (every `step`) and eased with a
    Gaussian `sigma` long, so it runs as one fair curve."""
    c = np.vstack([curve, curve[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    n = max(24, int(d[-1] / step))
    t = np.linspace(0, d[-1], n, endpoint=False)
    r = np.stack([np.interp(t, d, c[:, k]) for k in range(3)], 1)
    sg = sigma / (d[-1] / n)
    if sg > 0.3:
        k = int(np.ceil(3 * sg))
        g = np.exp(-0.5 * (np.arange(-k, k + 1) / sg) ** 2)
        g /= g.sum()
        r = sum(np.roll(r, -i, 0) * g[i + k] for i in range(-k, k + 1))
    return r


# (s18 ranger solver 2, RING_ONE: rolls (tube names) each of whose rings goes back on one blend after the
# helpers' split, see rings_one; RING_BAND: the sheet under the roll shares its rings' blend, eased back to its
# own over this far in from the roll's inner reach)
RING_ONE = {k_ for k_ in os.environ.get("RING_ONE", "ranger.corset_bind1,ranger.corset_bind3").split(",") if k_}
RING_BAND = float(os.environ.get("RING_BAND", "0.004"))
# (s18 ranger solver 2, BIND_CLAMP: sheet name -> how far past its bound line its thickened edge may stand, m. Where
# the edge points were moved onto the fair line some edge triangles fell into slivers standing across the sheet (an
# ear of three edge points, ranger.corset bind1 rings 221 and 223, its one triangle's normal along the roll's outward),
# and thickened along such normals the sheet's outer edge stood up to 1.2 mm out past its roll: judge fin2 item 6's knob,
# r_leo_f (830-840,677-692), and right end, bind3 rings 55-65. Pulled back, inside the roll. Rolls named in RING_ONE.)
BIND_CLAMP = {k_: float(v_) for k_, v_ in (e_.split("=", 1) for e_ in os.environ.get("BIND_CLAMP", "ranger.corset=0.0003").split(",") if e_)}


# (s18 ranger solver 2, BIND_REACH: how far in from a roll's line (RING_ONE rolls) a sheet's loose edge is brought out
# onto it. Under her crotch the ranger's right leg line had a pinch in its cut edge that edge_loops left out of the
# bound loop (a sub-loop of 8 points or fewer): its points stayed up to 6.7 mm in from the line, the sheet's edge ran
# up to 3.8 mm short of its roll over 8 mm (bind1 rings 247-251), and skin showed through between them: judge fin2
# item 6's slit, r_leo_f (865,714). 0 = off.)
BIND_REACH = float(os.environ.get("BIND_REACH", "0.008"))


def reached_to_rolls(name, pos, tris, rolls):
    """(s18 BIND_REACH) The sheet's edge points not on any bound line but
    within BIND_REACH in from one (beside its roll, in the sheet's plane)
    moved straight out onto it."""
    e_ = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    uk_, c_ = np.unique(e_, axis=0, return_counts=True)
    bv = np.unique(uk_[c_ == 1])
    lines = []
    for roll in rolls:
        if "ring_line" in roll:
            nv = int(roll["ring_nv"])
            rp = np.array(roll["ring_pts"], float).reshape(-1, nv, 3)
            c0 = rp.mean(1)
            out = rp[:, 0] - c0
            out /= np.linalg.norm(out, axis=1)[:, None] + 1e-12
            up = rp[:, nv // 4] - c0
            up /= np.linalg.norm(up, axis=1)[:, None] + 1e-12
            lines.append((np.array(roll["ring_line"], float).reshape(-1, 3), out, up))
    if not lines or BIND_REACH <= 0:
        return pos
    on = np.zeros(len(bv), bool)
    for cur, _, _ in lines:
        on |= cKDTree(cur).query(pos[bv])[0] < 0.0005
    pos = pos.copy()
    n_, mx = 0, 0.0
    for cur, out, up in lines:
        q = pos[bv]
        dn, jn = cKDTree(cur).query(q)
        s_ = ((q - cur[jn]) * out[jn]).sum(1)
        h_ = ((q - cur[jn]) * up[jn]).sum(1)
        m_ = ~on & (s_ < -0.0003) & (s_ > -BIND_REACH) & (np.abs(h_) < 0.002) & (dn < BIND_REACH + 0.001)
        pos[bv[m_]] -= out[jn[m_]] * s_[m_][:, None]
        n_ += int(m_.sum())
        mx = max(mx, float(-s_[m_].min()) if m_.any() else 0.0)
    if n_:
        print("BIND_REACH %s: %d loose edge points brought out onto their roll's line (up to %.1f mm)" % (name, n_, mx * 1000))
    return pos


def clamped_to_rolls(sheet, rolls, past):
    """(s18 BIND_CLAMP) The thickened sheet's points that stand more than
    `past` out beyond the line its edge was bound on, beside the roll, pulled
    straight back in (along the roll's outward) to `past`."""
    me = sheet.data
    # (the sheet's own space, the space its rolls' rings were made in)
    co = np.array([v.co[:] for v in me.vertices]).reshape(-1, 3)
    P = co.copy()
    D = np.zeros_like(P)
    n_ = 0
    for roll in rolls:
        if "ring_line" not in roll:
            continue
        nv = int(roll["ring_nv"])
        rp = np.array(roll["ring_pts"], float).reshape(-1, nv, 3)
        cur = np.array(roll["ring_line"], float).reshape(-1, 3)
        c0 = rp.mean(1)
        out = rp[:, 0] - c0
        rw = np.linalg.norm(out, axis=1)
        out /= rw[:, None] + 1e-12
        up = rp[:, nv // 4] - c0
        rh = np.linalg.norm(up, axis=1)
        up /= rh[:, None] + 1e-12
        dn, jn = cKDTree(cur).query(P + D)
        s_ = ((P + D - cur[jn]) * out[jn]).sum(1)
        h_ = ((P + D - c0[jn]) * up[jn]).sum(1)
        m_ = (dn < 2 * rw[jn]) & (s_ > past) & (np.abs(h_) < rh[jn] + 0.001)
        D[m_] -= out[jn[m_]] * (s_[m_] - past)[:, None]
        n_ += int(m_.sum())
    if not n_:
        return
    idx = np.nonzero(np.abs(D).sum(1) > 0)[0]
    dl = D
    for i in idx:
        me.vertices[int(i)].co = Vector(co[i] + dl[i])
    if me.shape_keys is not None:
        for kb in me.shape_keys.key_blocks:
            for i in idx:
                kb.data[int(i)].co = Vector(np.array(kb.data[int(i)].co[:]) + dl[i])
    me.update()
    print("BIND_CLAMP %s: %d points of its edge standing past the bound line pulled back to %.1f mm past it (moved up to %.2f mm)"
          % (sheet.name, len(idx), past * 1000, np.linalg.norm(D, axis=1).max() * 1000))


def tube(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed=True, nv=12):
    """A rolled edge along a line: a flattened tube `width` across, centred
    so it reaches `overhang` past the line on its `outward` side, and stands
    `height` proud of a sheet `thick` thick lying under it (half its
    height above the sheet, wrapping its cut edge). Weights from the sheet
    it binds, one set to each ring."""
    n = len(curve)
    th = np.linspace(0, 2 * np.pi, nv, endpoint=False)
    if np.ndim(width) or np.ndim(height) or np.ndim(overhang) or np.ndim(thick):
        # (s18 BIND_SLIM: its profile ring by ring)
        w_, h_, o_, t_ = (np.broadcast_to(np.asarray(v_, float), (n,)) for v_ in (width, height, overhang, thick))
        c0 = curve + outward * (o_ - w_ / 2)[:, None] + nrm * (t_ / 2)[:, None]
        pts = (c0[:, None, :] + outward[:, None, :] * ((w_ / 2)[:, None] * np.cos(th)[None, :])[:, :, None]
               + nrm[:, None, :] * ((t_ / 2 + h_)[:, None] * np.sin(th)[None, :])[:, :, None]).reshape(-1, 3)
    else:
        c0 = curve + outward * (overhang - width / 2) + nrm * (thick / 2)
        rw, rh = width / 2, thick / 2 + height
        pts = (c0[:, None, :] + outward[:, None, :] * (rw * np.cos(th))[None, :, None]
               + nrm[:, None, :] * (rh * np.sin(th))[None, :, None]).reshape(-1, 3)
    rows = n + (0 if closed else -1)
    tris = []
    for i in range(rows):
        i1 = (i + 1) % n
        for j in range(nv):
            j1 = (j + 1) % nv
            a, b, c, d = i * nv + j, i * nv + j1, i1 * nv + j, i1 * nv + j1
            tris += [(a, c, b), (b, c, d)]
    tris = np.array(tris)
    if not closed:
        # Ends closed with a fan.
        caps = []
        for i in (0, n - 1):
            ci = len(pts) + len(caps)
            caps.append(c0[i])
            for j in range(nv):
                j1 = (j + 1) % nv
                tris = np.vstack([tris, [(ci, i * nv + j1, i * nv + j)] if i == 0 else [(ci, i * nv + j, i * nv + j1)]])
        pts = np.vstack([pts, np.array(caps)])
    cen = np.vstack([np.repeat(c0, nv, 0), c0[[0, -1]]]) if not closed else np.repeat(c0, nv, 0)
    vn = vertex_normals(pts, tris)
    if ((pts - cen) * vn).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    # One set of weights to each ring of it, from the sheet within about a
    # centimetre of the ring (weighed by nearness), eased along it: each
    # point taking its nearest point of the sheet's, it kinked where that
    # point changed, as she moved.
    kk = min(24, len(src_pos))
    d_, j_ = cKDTree(src_pos).query(c0, k=kk)
    d_, j_ = np.reshape(d_, (len(c0), kk)), np.reshape(j_, (len(c0), kk))
    g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
    ring = (np.asarray(src_wt, float)[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
    for _ in range(8):
        ring = (np.roll(ring, 1, 0) + 2 * ring + np.roll(ring, -1, 0)) / 4 if closed else             np.vstack([ring[:1], (ring[:-2] + 2 * ring[1:-1] + ring[2:]) / 4, ring[-1:]])
    wt = np.repeat(ring, nv, 0)
    if not closed:
        wt = np.vstack([wt, ring[[0, -1]]])
    obj = finish(name, pts, wt, tris, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = False
    if name in RING_ONE:
        # (s18 RING_ONE: its rings as made, for rings_one at export)
        obj["ring_nv"] = nv
        obj["ring_pts"] = np.asarray(pts[:n * nv], np.float32).ravel().tolist()
        obj["ring_line"] = np.asarray(curve, np.float32).ravel().tolist()
    return obj


def edge_loops(tris):
    """A sheet's edge as loops, found in one pass: each edge of a triangle
    whose reverse no triangle has is on the rim, and following those edges
    the way the triangles wind brings each walk home, pinched corners and
    all, with no searching. Edges are counted by direction, and an edge is
    on the rim as many times as it runs one way more than the other: so the
    rim is always closed, even where the weld left three or four triangles
    on one edge (counted as present or not, such an edge dropped out of the
    rim and the walk stopped short: the ranger's left glove, a loop's last
    step 27 mm back to its start)."""
    from collections import Counter, defaultdict
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).tolist()
    count = Counter(map(tuple, e))
    out = defaultdict(list)
    for (a, b), n in count.items():
        out[a].extend([b] * max(n - count.get((b, a), 0), 0))
    out = defaultdict(list, {a: v for a, v in out.items() if v})
    loops = []
    while out:
        start = next(iter(out))
        loop, v = [start], start
        while v in out:
            nxt = out[v].pop()
            if not out[v]:
                del out[v]
            if nxt == start:
                break
            loop.append(nxt)
            v = nxt
        if len(loop) > 8:
            loops.append(loop)
    return loops


def rounded(cur, rmin, rounds=400):
    """A closed line with no bend tighter than `rmin`: each point bent
    tighter than that (its circle through it and its neighbours smaller)
    eased toward its neighbours with them, until none is. (Eased by a
    Gaussian alone, a plate's corner kept a bend tighter than its rolled
    edge was round, and the edge's rings crossed there in a knot, with a
    hole and a spike; and the arcanist's plunge came to a V.)"""
    cur = cur.copy()
    for _ in range(rounds):
        a, b = np.roll(cur, 1, 0), np.roll(cur, -1, 0)
        twice = np.linalg.norm(np.cross(cur - a, b - a), axis=1)
        r = (np.linalg.norm(b - a, axis=1) * np.linalg.norm(cur - a, axis=1) * np.linalg.norm(b - cur, axis=1)
             / (2 * twice + 1e-15))
        tight = r < rmin
        if not tight.any():
            break
        m = tight | np.roll(tight, 1) | np.roll(tight, -1)
        cur = np.where(m[:, None], 0.5 * cur + 0.25 * (a + b), cur)
    return cur


MIRROR_BIND = {"arcanist.corset"}   # (bound edges made the same both sides: the arcanist's plunge, cut on a mesh that is not, stood 0.63 mm apart at its foot, solver 11 October)


def mirror_line(cur):
    """A closed line made the same both sides of her middle (x = 0): each
    point taken halfway to the mirror of the line's nearest place to its own
    mirror, wherever the line is within 3 mm of symmetric already."""
    flip = np.array([-1.0, 1.0, 1.0])
    m = cur * flip
    a, e = cur, np.roll(cur, -1, 0) - cur
    j = cKDTree(cur).query(m)[1]
    best, bd = None, None
    for jj in ((j - 1) % len(cur), j):
        t = np.clip(((m - a[jj]) * e[jj]).sum(1) / ((e[jj] * e[jj]).sum(1) + 1e-30), 0, 1)
        q = a[jj] + e[jj] * t[:, None]
        d = np.linalg.norm(q - m, axis=1)
        if best is None:
            best, bd = q, d
        else:
            best, bd = np.where((d < bd)[:, None], q, best), np.minimum(d, bd)
    w = np.clip((0.003 - bd) / 0.001, 0, 1)[:, None]
    return cur + w * 0.5 * (best * flip - cur)


BIND_RMIN = {}   # (a piece's name: no bend of its binding tighter than this)
# (s24 glove styles, by piece name: its binding's line eased this much (not 12 mm), loops this short still
# bound (a thumb's), its binding (key, width, height, overhang) as given, not widened to 5 mm; and the
# glove's top cut for her skin's tuck under it)
BIND_SIGMA, BIND_MINLOOP, BIND_SPEC, GLOVE_TOP_D = {}, {}, {}, {}
# (s28, the owner's louder G3 top: a piece's name: (a point, (width, height, overhang)): its bound edge loop
# nearest that point (the glove's top, by her elbow) bound to that instead of BIND_SPEC's; the rest as given)
BIND_TOP = {}
# (s17 spike2: a piece's name: its binding faces the sheet's faces within 3 mm of
# the line, weighed by their area, not the one nearest face: at the arcanist's left
# hip one folded sliver at the edge (0.18 mm2) was the nearest face of four line
# points, its facing turned over; eased along the line it swung the roll's frame
# 100 deg over 4 mm and the roll crumpled into a spur, judge fin1)
BIND_AREA_N = {k_ for k_ in os.environ.get("BIND_AREA_N", "arcanist.corset").split(",") if k_}
# (a piece's name: its binding faces the sheet as fitted across the roll's width, see bind_edges)
BIND_FIT = {"ranger.corset"}
# (s18, judge fin2: a piece's name: its binding slimmed round and under her crotch, to width : height : overhang :
# centre-thick (the roll centred half that off the sheet's inside, as the sheet's thickness centres it elsewhere). The
# one-piece's leg-line roll, 8 mm by 4.2 mm, centred on the full 3 mm sheet, stood 2.7 mm proud of its skived 0.9 mm
# edge; where it turned under her crotch it showed past the sheet as a knob (a_leo_f, a_full_f's foot) and a ragged
# end (a_leo_qr). Slim: 7 by 2.4 mm, 0.9 mm proud of the skived edge. Full below CROTCH + 4 mm, none above + 20 mm.)
BIND_SLIM_STITCH = float(os.environ.get("BIND_SLIM_STITCH", "0.05"))   # (s18 leo2: 0.45 = as built in s18leo)
BIND_SLIM = {k_: tuple(float(v_) for v_ in r_.split(":")) for k_, r_ in (e_.split("=", 1) for e_ in os.environ.get(
    "BIND_SLIM", "arcanist.corset=0.007:0.0004:0.0015:0.0016").split(",") if e_)}
# (armor 17 N3: a piece's name -> (a field on its edge line, 0..1; (width, height, overhang, thickness)): its binding
# eased to that size where the field is 1. The arcanist's caps: a roll sized for the full 3 mm sheet stood ~4 mm proud
# over the skived 2 mm cap, a lip at its hem (max judge OJ1: "a flush bound edge, no rolled lip"). Set by the outfit.)
BIND_ZONE = {}


def sheet_untangled(name, pos, ref, tris, zone, rounds=400):
    """A sheet with no triangle turned over against `ref` (the same sheet
    before a shaping), as untangled() does her skin: each folded triangle
    and two rings round it eased toward their neighbours, the edge kept,
    within `zone` (a mask of points) only, until none is left."""
    def normals(Q):
        return np.cross(Q[tris[:, 1]] - Q[tris[:, 0]], Q[tris[:, 2]] - Q[tris[:, 0]])
    n0 = normals(ref)
    A = adjacency(len(pos), tris)
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    free = np.asarray(zone, bool).copy()
    free[uk[c == 1].ravel()] = False
    S, first, k = pos.copy(), None, 0
    for k in range(rounds):
        flip = ((normals(S) * n0).sum(1) <= 0) & free[tris].any(1)
        if first is None:
            first = int(flip.sum())
        if not flip.any():
            break
        bad = np.zeros(len(S))
        bad[tris[flip].ravel()] = 1
        for _ in range(2):
            bad = np.maximum(bad, (A @ bad > 0).astype(float))
        m = (bad > 0) & free
        S = np.where(m[:, None], 0.5 * S + 0.5 * (A @ S), S)
    left = int((((normals(S) * n0).sum(1) <= 0) & free[tris].any(1)).sum())
    print("UNTANGLED %s: %d folded triangles, left %d after %d rounds; moved up to %.1f mm"
          % (name, first, left, k + 1, np.linalg.norm(S - pos, axis=1).max() * 1000))
    return S


def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.012, stitch=False, rmin=None):
    """A sheet's cut outline made fair and bound: each edge loop eased into
    one smooth curve, the sheet's own edge points moved onto it, and a
    rolled edge laid along it that covers the cut, as a garment's edges are
    bound or a plate's are rolled."""
    loops = edge_loops(tris)
    if not loops:
        return pos, []
    nor = vertex_normals(pos, tris)
    tree = cKDTree(pos)
    sheet_bvh = BVHTree.FromPolygons([tuple(p) for p in pos], tris.tolist())
    beads = []
    pos = pos.copy()
    moved = np.zeros(len(pos), bool)
    bound = 0
    planes = []
    top_k = -1
    if name in BIND_TOP:
        a_ = np.asarray(BIND_TOP[name][0], float)
        top_k = int(np.argmin([np.linalg.norm(pos[l_].mean(0) - a_) for l_ in loops]))
    for k, loop in enumerate(loops):
        lp = pos[loop]
        seg = np.linalg.norm(np.diff(np.vstack([lp, lp[:1]]), axis=0), axis=1)
        # A walk that jumped across the sheet, or a hole too small to bind
        # (a finger's), is left as cut.
        if seg.max() > 0.015 or seg.sum() < BIND_MINLOOP.get(name, 0.07):
            print("UNBOUND %s: an edge loop of %d points left as cut (longest step %.1f mm, %.1f cm round)"
                  % (name, len(loop), seg.max() * 1000, seg.sum() * 100))
            continue
        bound += 1
        cur = smooth_closed(lp, BIND_SIGMA.get(name, sigma))
        # (no bend tighter than twice the rolled edge's radius: see rounded())
        cur = rounded(cur, rmin or BIND_RMIN.get(name) or (BIND_TOP[name][1][0] if k == top_k else width))
        # Back onto the sheet (its surface, not the plane of the nearest
        # point: that changed from point to point and stepped the line in
        # depth, unseen face-on, kinked at a glancing view), the move eased
        # along the line; and the sheet's normal there.
        # (the sheet's facing, from its surface, eased well along the line:
        # taken from the nearest point's normal it swung near the cut edge,
        # and the rolled edge, set off sideways by it, folded into a Z)
        hits = [sheet_bvh.find_nearest(Vector(q)) for q in cur]
        on = np.array([h[0][:] for h in hits])
        nrm = np.array([h[1][:] for h in hits])
        _, j = tree.query(cur)
        nrm = np.where(((nrm * nor[j]).sum(1) < 0)[:, None], -nrm, nrm)
        if name in BIND_AREA_N:
            fcr_ = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
            an_ = nrm.copy()
            for i_, nb_ in enumerate(cKDTree(pos[tris].mean(1)).query_ball_point(on, 0.003)):
                s_ = fcr_[nb_].sum(0) if nb_ else np.zeros(3)
                if np.linalg.norm(s_) > 1e-12:
                    an_[i_] = s_ / np.linalg.norm(s_)
            # (one sign for the whole line, the winding being the sheet's own: the
            # nearest point's normal, which set it point by point, was the sliver's)
            nrm = an_ * (1.0 if (an_ * nor[j]).sum() >= 0 else -1.0)
        for _ in range(12):
            nrm = (np.roll(nrm, 1, 0) + 2 * nrm + np.roll(nrm, -1, 0)) / 4
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        mv = on - cur
        for _ in range(6):
            mv = (np.roll(mv, 1, 0) + 2 * mv + np.roll(mv, -1, 0)) / 4
        cur = cur + mv
        if name in MIRROR_BIND:
            cur = mirror_line(cur)
        if name in BIND_FIT:
            # (its facing from the sheet itself under the roll: a plane fitted
            # to the sheet within 6 mm of each point of the line. From the
            # nearest face, eased along the line, it lagged 17-28 deg where the
            # ranger's cup edge turns down under her arm, and the leather rose
            # 1-2 mm over the roll's inner flank there: a torn edge, judge 9)
            fit = nrm.copy()
            for i, nb in enumerate(tree.query_ball_point(cur, 0.006)):
                if len(nb) < 4:
                    continue
                q = pos[nb]
                g = np.exp(-0.5 * (np.linalg.norm(q - cur[i], axis=1) / 0.003) ** 2)[:, None]
                m = (q * g).sum(0) / g.sum()
                f = np.linalg.eigh(((q - m) * g).T @ (q - m))[1][:, 0]
                fit[i] = f if f @ nrm[i] > 0 else -f
            for _ in range(3):
                fit = (np.roll(fit, 1, 0) + 2 * fit + np.roll(fit, -1, 0)) / 4
            nrm = fit / (np.linalg.norm(fit, axis=1)[:, None] + 1e-12)
        tg = np.roll(cur, -1, 0) - np.roll(cur, 1, 0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        bn = np.cross(nrm, tg)
        for _ in range(8):
            bn = (np.roll(bn, 1, 0) + 2 * bn + np.roll(bn, -1, 0)) / 4
        bn = bn - tg * (bn * tg).sum(1)[:, None]
        if name in BIND_FIT:
            # (and square to that facing: eased along a tight turn it tilted out of the sheet's plane)
            bn = bn - nrm * (bn * nrm).sum(1)[:, None]
        bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
        # Outward: away from the sheet's points near the line.
        votes = []
        for i in range(0, len(cur), 4):
            near = tree.query_ball_point(cur[i], 0.02)
            if near:
                votes.append(((pos[near].mean(0) - cur[i]) @ bn[i]))
        sgn = -1.0 if np.median(votes) > 0 else 1.0
        outward = bn * sgn
        # The sheet's edge points onto the fair line, and anything of the
        # sheet still standing out past it (scraps, pinched corners) pulled
        # back inside it.
        # (each edge point to its own place on the line, the line being its
        # loop eased: sent to the nearest place instead, neighbours landed
        # on one spot, their triangles fell flat, and thickened they stood
        # out as spikes and steps along her neckline)
        lt = cKDTree(cur)
        run = np.r_[0, np.cumsum(seg)]                     # (each point's way along its loop)
        tt = np.linspace(0, run[-1], len(cur), endpoint=False)
        cw = np.vstack([cur, cur[:1]])
        tw = np.r_[tt, run[-1]]
        pos[loop] = np.stack([np.interp(run[:-1], tw, cw[:, k]) for k in range(3)], 1)
        moved[loop] = True
        dn, jn = lt.query(pos)
        near_ = dn < 0.025
        out_ = ((pos - cur[jn]) * outward[jn]).sum(1)
        fix = near_ & (out_ > -0.0003)
        fix[loop] = False
        pos[fix] -= outward[jn[fix]] * (out_[fix] + 0.0003)[:, None]
        moved |= fix
        w_r, h_r, o_r, t_r = width, height, overhang, thick
        if k == top_k:
            w_r, h_r, o_r = BIND_TOP[name][1]
            print("BIND_TOP %s_bind%d: %.1f mm wide, %.1f mm over the sheet, %.1f mm overhang" % (name, k, w_r * 1000, h_r * 1000, o_r * 1000))
        if name in BIND_SLIM:
            # (s18 BIND_SLIM: slimmer round and under her crotch, eased along the line)
            sl_ = ramp(-cur[:, 2], -(CROTCH + 0.02), -(CROTCH + 0.004)) * ramp(-np.abs(cur[:, 0]), -0.06, -0.05)
            for _ in range(8):
                sl_ = (np.roll(sl_, 1) + 2 * sl_ + np.roll(sl_, -1)) / 4
            if sl_.max() > 0.01:
                ws_, hs_, os_, ts_ = BIND_SLIM[name]
                w_r, h_r, o_r, t_r = (v_ + sl_ * (s_ - v_) for v_, s_ in ((width, ws_), (height, hs_), (overhang, os_), (thick, ts_)))
                print("BIND_SLIM %s_bind%d: %d of %d rings slimmed (to %.1f by %.1f mm)" % (name, k, int((sl_ > 0.5).sum()), len(cur), ws_ * 1000, (ts_ + 2 * hs_) * 1000))
        if name in BIND_ZONE:
            zf_, zs_ = BIND_ZONE[name]
            z_ = np.clip(np.asarray(zf_(cur), float), 0, 1)
            for _ in range(8):
                z_ = (np.roll(z_, 1) + 2 * z_ + np.roll(z_, -1)) / 4
            if z_.max() > 0.01:
                w_r, h_r, o_r, t_r = (v_ + z_ * (s_ - v_) for v_, s_ in ((w_r, zs_[0]), (h_r, zs_[1]), (o_r, zs_[2]), (t_r, zs_[3])))
                if name not in BIND_SLIM:
                    sl_ = np.zeros(len(cur))
                print("BIND_ZONE %s_bind%d: %d of %d rings eased (to %.1f by %.1f mm)" % (name, k, int((z_ > 0.5).sum()), len(cur), zs_[0] * 1000, (zs_[3] + 2 * zs_[1]) * 1000))
        if os.environ.get("RIB_DUMP"):
            np.savez(os.path.join(os.environ["RIB_DUMP"], f"{name}_bind{k}.npz"), cur=cur, nrm=nrm, outward=outward)
        beads.append(tube(f"{name}_bind{k}" if k else f"{name}_bind", cur, nrm, outward, key, w_r, h_r, o_r, t_r,
                          pos, at[:, 3:3 + NB]))
        if name in BIND_FIT:
            planes.append((cur.copy(), nrm.copy(), outward.copy()))
        if stitch:
            # (sewn through the binding, along its inner shoulder)
            if np.ndim(w_r):
                c0 = cur + outward * (o_r - w_r / 2)[:, None] + nrm * (t_r / 2)[:, None]
                # (s18 leo2, judge fin2 regression: on the slimmed rings the inner shoulder lay ~0.4 mm under the
                # skived sheet's face and the row was lost; there it moves out toward the roll's crown, BIND_SLIM_STITCH
                # of its half-width in, on the roll's own surface + 0.1 mm)
                u_ = 0.45 + (BIND_SLIM_STITCH - 0.45) * sl_
                line = c0 - outward * (w_r / 2 * u_)[:, None] + nrm * ((t_r / 2 + h_r) * np.sqrt(1 - u_ * u_) + 0.0001)[:, None]
            else:
                c0 = cur + outward * (overhang - width / 2) + nrm * (thick / 2)
                line = c0 - outward * (width / 2) * 0.45 + nrm * ((thick / 2 + height) * 0.893 + 0.0001)
            beads += stitches(f"{name}_stitch{k}", line, nrm, tg, pos, at[:, 3:3 + NB], closed=True)
    # The points next to the edge eased, so the sheet meets its new edge
    # without a crease.
    A = adjacency(len(pos), tris)
    near = (A @ moved.astype(float)) > 0
    near &= ~moved
    nor_e = vertex_normals(pos, tris)
    for _ in range(6):
        d_ = 0.5 * (A @ pos - pos)
        d_ -= nor_e * (d_ * nor_e).sum(1)[:, None]
        pos = np.where(near[:, None], pos + d_, pos)
    # (BIND_FIT: the sheet under and just inside its roll laid in the roll's
    # own plane, fully to BF_IN in from the edge and faded out by BF_OUT: the
    # leather rose 17 deg from 2.5 mm in and lay over the roll's inner flank,
    # so the roll showed 0.5 mm and the edge read torn, judge 9, solver E)
    BF_IN, BF_OUT = (float(v) for v in os.environ.get("BIND_FLAT", "0.004,0.008").split(","))
    BF_MAX = float(os.environ.get("BIND_FLATMAX", "0.0008"))   # (pulled at most this far: unbounded, 6-12 mm, it folded the cup's turn under her arm, e1)
    for cur, nrm, outward in planes:
        dn, jn = cKDTree(cur).query(pos)
        inw = -((pos - cur[jn]) * outward[jn]).sum(1)       # (how far in from the edge)
        sel = (dn < BF_OUT + 0.002) & (inw > -0.001)
        t_ = np.clip((inw[sel] - BF_IN) / (BF_OUT - BF_IN), 0, 1)
        w_ = 1 - t_ * t_ * (3 - 2 * t_)
        h_ = ((pos[sel] - cur[jn[sel]]) * nrm[jn[sel]]).sum(1)
        pos[sel] -= nrm[jn[sel]] * np.clip(w_ * h_, -BF_MAX, BF_MAX)[:, None]
        if len(h_):
            print("BINDFLAT %s: %d points laid in the roll's plane, off it by up to %.2f mm before" % (name, sel.sum(), np.abs(h_).max() * 1000))
    print("BOUND", name, bound, "of", len(loops), "edge loops")
    return pos, beads


def domes(name, pts, nrms, mkey, r=0.0028, src=None, rise=0.7):
    """Small domed studs (eyelets, rivets) at points, standing on normals."""
    P2, T2 = [], []
    nu, nv = 12, 4
    for p0, n in zip(pts, nrms):
        n = n / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        q = [p0 + n * r * rise]
        for k in range(1, nv + 1):
            th = (np.pi / 2) * k / nv
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                q.append(p0 + (np.cos(ph) * t + np.sin(ph) * b) * r * np.sin(th) + n * r * rise * np.cos(th))
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv - 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(q))
        T2.append(np.array(tri))
    pp, tt = np.vstack(P2), np.vstack(T2)
    cen = np.repeat(np.array(pts), nu * nv + 1, 0)
    if ((pp - cen) * vertex_normals(pp, tt)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    # (each moves as one piece: its centre's weights for all of it)
    cen_ = np.array(pts, float)
    if src is None:
        wc = soft_weights(cen_)
    else:
        _, jc = cKDTree(src[0]).query(cen_)
        wc = np.asarray(src[1], float)[jc]
    obj = finish(name, pp, np.repeat(wc, nu * nv + 1, 0), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return [obj]


def grommets(name, pts, nrms, mkey, r_out=0.0036, r_in=0.0018, height=0.0014, hole="blackleather"):
    """Eyelets as a corsetier sets them: a rolled metal ring at each point,
    standing on its normal, with the dark of the hole inside it (a dome
    reads as a stud, not as a hole a lace goes through)."""
    nu, nv = 20, 8
    R0, rw, rh = (r_out + r_in) / 2, (r_out - r_in) / 2, height / 2
    P2, T2, C2, H2, HT = [], [], [], [], []
    for p0, n in zip(pts, nrms):
        n = n / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        q, cen = [], []
        for i in range(nu):
            radial = np.cos(2 * np.pi * i / nu) * t + np.sin(2 * np.pi * i / nu) * b
            for j in range(nv):
                th = 2 * np.pi * j / nv
                q.append(p0 + n * rh + radial * (R0 + rw * np.cos(th)) + n * rh * np.sin(th))
                cen.append(p0 + n * rh + radial * R0)
        tri = []
        for i in range(nu):
            i1 = (i + 1) % nu
            for j in range(nv):
                j1 = (j + 1) % nv
                a_, b_, c_, d_ = o + i * nv + j, o + i * nv + j1, o + i1 * nv + j, o + i1 * nv + j1
                tri += [(a_, c_, b_), (b_, c_, d_)]
        P2.append(np.array(q))
        T2.append(np.array(tri))
        C2.append(np.array(cen))
        ho = sum(len(x) for x in H2)
        H2.append(np.array([p0 + n * rh * 0.5] + [p0 + n * rh * 0.5 + (np.cos(2 * np.pi * i / nu) * t + np.sin(2 * np.pi * i / nu) * b)
                                                  * (r_in + rw * 0.5) for i in range(nu)]))
        tr = np.array([(ho, ho + 1 + i, ho + 1 + (i + 1) % nu) for i in range(nu)])
        if (vertex_normals(H2[-1], tr - ho) @ n).mean() < 0:
            tr = tr[:, ::-1]
        HT.append(tr)
    pp, tt, cc = np.vstack(P2), np.vstack(T2), np.vstack(C2)
    if ((pp - cc) * vertex_normals(pp, tt)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    hp, ht = np.vstack(H2), np.vstack(HT)
    made = []
    wc = soft_weights(np.array(pts, float))
    for nm, q, tr, key, per in ((name, pp, tt, mkey, nu * nv), (name + "_holes", hp, ht, hole, nu + 1)):
        made.append(finish(nm, q, np.repeat(wc, per, 0), tr, key, 0.0, 0.0, 10 ** 7))
    for o_ in made:
        o_["hides"] = False
    return made


def cord(name, pts, mkey, r=0.0014, nv=10, closed=False, src=None):
    """A round cord (a lace, a bow) along points given densely, as they are
    (taut, not laid on her). It hides nothing of her: what shows between
    the laces is her skin."""
    c = np.asarray(pts, float)
    nrm = np.array([SKIN_BVH.find_nearest(Vector(p))[1][:] for p in c])
    tg = (np.roll(c, -1, 0) - np.roll(c, 1, 0)) if closed else np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
    obj = tube(name, c, nrm, np.cross(nrm, tg), mkey, 2 * r, r, r, 0.0, *(src if src is not None else (P, W.astype(float))), closed=closed, nv=nv)
    obj["hides"] = False
    return [obj]


def bezier(p0, p1, p2, step=0.0012):
    """Points along a quadratic curve from p0 to p2 drawn toward p1."""
    n = max(4, int((np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)) / step))
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def stitches(name, line, nrm, tg, src_pos, src_wt, step=0.004, length=0.0026, width=0.00065, height=0.0004, closed=False,
             mkey="thread"):
    """Saddle stitching along a line laid on a surface (`nrm` its normal,
    `tg` the line's way): a dash of waxed thread every `step`, its ends sunk
    into the leather, every one exactly in line and evenly spaced, as a
    careful hand sews. (Painted stitches, laid out from screen derivatives,
    wandered and broke at the texture's seams.)"""
    line, nrm, tg = (np.asarray(x, float) for x in (line, nrm, tg))
    if closed:
        line, nrm, tg = np.vstack([line, line[:1]]), np.vstack([nrm, nrm[:1]]), np.vstack([tg, tg[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
    if len(line) < 2 or d[-1] < 3 * step:
        return []
    n_ = int(d[-1] / step)
    ss = (np.arange(n_) + 0.5) * d[-1] / n_
    c = np.stack([np.interp(ss, d, line[:, k]) for k in range(3)], 1)
    nn = np.stack([np.interp(ss, d, nrm[:, k]) for k in range(3)], 1)
    nn /= np.linalg.norm(nn, axis=1)[:, None] + 1e-12
    tt = np.stack([np.interp(ss, d, tg[:, k]) for k in range(3)], 1)
    tt -= nn * (tt * nn).sum(1)[:, None]
    tt /= np.linalg.norm(tt, axis=1)[:, None] + 1e-12
    bb = np.cross(nn, tt)
    nu, nv = 4, 4
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False) + np.pi / 4
    tv = np.linspace(-1, 1, nv + 1)[1:-1]
    ring = np.sqrt(1 - tv ** 2)
    base = c - nn * height * 0.35
    # (per stitch: an end, nv-1 rings of nu, the other end)
    ends0 = base - tt * length / 2
    ends1 = base + tt * length / 2
    rings = (base[:, None, None, :] + tt[:, None, None, :] * (tv * length / 2)[None, :, None, None]
             + (np.cos(ph)[None, None, :, None] * bb[:, None, None, :] * width / 2
                + np.sin(ph)[None, None, :, None] * nn[:, None, None, :] * height) * ring[None, :, None, None])
    per = 2 + (nv - 1) * nu
    pts = np.concatenate([ends0[:, None], rings.reshape(len(c), -1, 3), ends1[:, None]], 1).reshape(-1, 3)
    tri = [(0, 1 + (j + 1) % nu, 1 + j) for j in range(nu)]
    for k in range(nv - 2):
        a0, b0 = 1 + k * nu, 1 + (k + 1) * nu
        tri += [t for j in range(nu) for t in ((a0 + j, a0 + (j + 1) % nu, b0 + j), (b0 + j, a0 + (j + 1) % nu, b0 + (j + 1) % nu))]
    last = 1 + (nv - 2) * nu
    tri += [(per - 1, last + j, last + (j + 1) % nu) for j in range(nu)]
    tri = np.array(tri)
    tris = (tri[None] + (np.arange(len(c)) * per)[:, None, None]).reshape(-1, 3)
    cen = np.repeat(base, per, 0)
    if ((pts - cen) * vertex_normals(pts, tris)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    # (each stitch weighed as the binding's rings are, so it stays on them)
    kk = min(24, len(src_pos))
    d_, j_ = cKDTree(src_pos).query(base, k=kk)
    d_, j_ = np.reshape(d_, (len(base), kk)), np.reshape(j_, (len(base), kk))
    g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
    w_ = (np.asarray(src_wt, float)[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
    obj = finish(name, pts, np.repeat(w_, per, 0), tris, mkey, 0.0, 0.0, 10 ** 7, scraps=False)
    obj["hides"] = False
    return [obj]


def studs_on(name, objs, aims, mkey, r=0.0026):
    """Rivets set on the outer face of pieces already made (a belt, a strap),
    where a ray from outside toward each aim (origin, target) first meets
    them: the visible fixing of one piece to another."""
    vs, fs = [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(vs, fs)
    pts, nrms = [], []
    for org, tgt in aims:
        d = Vector(tuple(np.asarray(tgt) - np.asarray(org))).normalized()
        hit = tree.ray_cast(Vector(tuple(org)), d, 2.0)
        if hit[0] is not None:
            n = np.array(hit[1][:])
            if n @ np.array(d[:]) > 0:
                n = -n
            pts.append(np.array(hit[0][:]) + n * 0.0002)
            nrms.append(n)
    if not pts:
        return []
    # (judge 4: rivets read as black plastic beads: dark iron, lower and
    # flatter headed, an even sheen in place of the scan's blotched one)
    made = domes(name, pts, nrms, "iron" if mkey == "darksteel" else mkey, r=r, rise=0.42)
    for o_ in made:
        o_["hides"] = False
    return made


def sunburst(name, centre, nrm, up, radius, mkey, rays=12, thick=0.0035, boss=None):
    """The sun of the Order of the Morning Light, as a smith would cut it:
    a disc ringed by `rays` rays, long and short by turns, the long ones
    tapering to points, `thick` deep with rounded edges, a domed boss in its
    middle (of `boss`, or of its own metal). Standing at `centre` on a
    surface whose normal is `nrm` (`up` its long way); weighted as her skin
    nearest it."""
    n = nrm / np.linalg.norm(nrm)
    u = up - n * (up @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    # The outline: between each pair of rays a notch at the disc's rim.
    ang = np.linspace(0, 2 * np.pi, 4 * rays, endpoint=False) + np.pi / 2
    rr = []
    for i in range(4 * rays):
        ray = i // 2
        if i % 2 == 0:
            rr.append(radius * (1.0 if ray % 2 == 0 else 0.78))       # a ray's point
        else:
            rr.append(radius * 0.56)                                  # the notch between rays
    rr = np.array(rr)
    rings = 6
    pts = [centre]
    for kk in range(1, rings + 1):
        for a_, r_ in zip(ang, rr * kk / rings):
            pts.append(centre + (np.cos(a_) * u + np.sin(a_) * v) * r_)
    pts = np.array(pts)
    m = len(ang)
    tris = [(0, 1 + j, 1 + (j + 1) % m) for j in range(m)]
    for kk in range(rings - 1):
        a0, b0 = 1 + kk * m, 1 + (kk + 1) * m
        for j in range(m):
            j1 = (j + 1) % m
            tris += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
    tris = np.array(tris)
    if (vertex_normals(pts, tris) @ n).mean() < 0:
        tris = tris[:, ::-1]
    wc = soft_weights(np.array([centre]), sigma=radius, k=32)
    made = [finish(name, pts, np.repeat(wc, len(pts), 0), tris, mkey, thick, thick * 0.4, 10 ** 7)]
    made += domes(name + "_boss", [centre + n * thick], [n], boss or mkey, r=radius * 0.38)
    for o_ in made:
        o_["hides"] = False
    return made


def fangs(name, pts, outs, downs, mkey, length=0.026, base=0.0045, curl=0.35, rng=None):
    """Wolf fangs strung on a cord: at each point a tooth, its root a little
    off the cord along `out`, curving down (`down`) and out to a point,
    round and tapering, each a little longer or shorter than the next."""
    rng = rng or np.random.default_rng(3)
    P2, T2 = [], []
    nu, nv = 10, 12
    for p0, o, dn in zip(pts, outs, downs):
        o = o / np.linalg.norm(o)
        dn = dn - o * (dn @ o)
        dn /= np.linalg.norm(dn)
        side = np.cross(o, dn)
        L = length * rng.uniform(0.75, 1.1)
        off = len(sum([list(x) for x in P2], []))
        ring_pts = []
        for k in range(nv + 1):
            t = k / nv
            # the tooth's middle line: down, curling out toward its point
            c = p0 + o * 0.003 + dn * L * t + o * L * curl * t * t
            tang = dn + o * 2 * L * curl * t / max(L, 1e-6)
            tang /= np.linalg.norm(tang)
            a1 = np.cross(tang, side)
            a1 /= np.linalg.norm(a1)
            r = base * (1 - t) ** 0.8 + 0.0002
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                ring_pts.append(c + (np.cos(ph) * side + np.sin(ph) * a1) * r * (1.0 if np.sin(ph) > 0 else 0.8))
        ring_pts.append(p0 + o * 0.003 + dn * L + o * L * curl + dn * 0.0006)
        tri = []
        for k in range(nv):
            a0_, b0_ = off + k * nu, off + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0_ + j, b0_ + j, b0_ + j1), (a0_ + j, b0_ + j1, a0_ + j1)]
        tip = off + (nv + 1) * nu
        tri += [(off + nv * nu + j, tip, off + nv * nu + (j + 1) % nu) for j in range(nu)]
        # its root closed
        tri += [(off, off + (j + 1) % nu, off + j) for j in range(1, nu - 1)]
        P2.append(np.array(ring_pts))
        T2.append(np.array(tri))
    pp, tt = np.vstack(P2), np.vstack(T2)
    if (vertex_normals(pp, tt) * (pp - np.repeat(np.array(pts), (nv + 1) * nu + 1, 0))).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    wc = soft_weights(np.array(pts, float))
    obj = finish(name, pp, np.repeat(wc, (nv + 1) * nu + 1, 0), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = False
    return [obj]


def frame(name, centre, nrm, up, w, h, mkey, r=0.002, corner=0.004, lift=0.0):
    """A buckle frame: a rounded rectangle of rod `r` thick, `w` by `h`,
    standing on a surface at `centre` (normal `nrm`, `up` its long way)."""
    n = nrm / np.linalg.norm(nrm)
    u = up - n * (up @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pts = []
    hw, hh = w / 2 - corner, h / 2 - corner
    for cx, cy, a0 in ((hw, hh, 0), (-hw, hh, np.pi / 2), (-hw, -hh, np.pi), (hw, -hh, 3 * np.pi / 2)):
        for a in np.linspace(a0, a0 + np.pi / 2, 8, endpoint=False):
            pts.append(centre + n * lift + v * (cx + corner * np.cos(a)) + u * (cy + corner * np.sin(a)))
    pts = np.array(pts)
    nr = np.repeat(n[None], len(pts), 0)
    tg = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    out = np.cross(nr, tg)
    if ((pts - pts.mean(0)) * out).sum(1).mean() < 0:
        out = -out
    c_ = pts.mean(0)
    wc = soft_weights(c_[None], sigma=max(w, h) / 2, k=32)
    return [tube(name, pts, nr, out, mkey, 2 * r, 0.0, r, 2 * r, c_[None], wc)]


# ----------------------------------------------------------------- pieces --
NB = len(BONES)


def hulled(pos, where, tris, blend=0.02, fill=0):
    """Where `where` > 0 (a boot's foot), the piece laid on the convex hull
    of itself there: toes become one rounded toe box, as leather over them
    is; it eases back to its own shape over `blend` of `where`. `fill` (Body
    17, the reaver's turnshoe): the sheet first smoothed that many rounds
    there (the hull taken before), so the gaps between her toes fill before
    each point goes to the hull's nearest point: low between her toes that
    was the hull's floor, and the gap between her big toe and the next
    stayed, a notch in the outline and a crease above it."""
    from scipy.spatial import ConvexHull
    m = where > -blend
    if m.sum() < 10:
        return pos
    h = ConvexHull(pos[m])
    hv = pos[m]
    bvh = BVHTree.FromPolygons([tuple(p) for p in hv], h.simplices.tolist())
    out = pos.copy()
    t = np.clip((where + blend) / blend, 0, 1)
    src = pos
    if fill:
        import scipy.sparse as sp_
        e_ = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        A_ = sp_.coo_matrix((np.ones(2 * len(e_)), (np.r_[e_[:, 0], e_[:, 1]], np.r_[e_[:, 1], e_[:, 0]])), shape=(len(pos), len(pos))).tocsr()
        A_.data[:] = 1.0
        deg_ = np.asarray(A_.sum(1)).ravel() + 1e-12
        src = pos.copy()
        # (the foot past the blend only: the ankle's blend as before, the walk's ankle crease came out through it)
        mf = where > 0.005
        for _ in range(fill):
            src = np.where(mf[:, None], (A_ @ src) / deg_[:, None], pos)
    for i in np.where(m)[0]:
        q = bvh.find_nearest(Vector(src[i]))[0]
        if q is not None:
            out[i] = pos[i] * (1 - t[i]) + np.array(q[:]) * t[i]
    if fill and HULL_PAD > 0:
        # (and the filled foot HULL_PAD further out, eased in over the blend: her toes flexing in the walk)
        vn_ = vertex_normals(out, tris)
        if ((vn_[m] * (out[m] - out[m].mean(0))).sum(1) < 0).mean() > 0.5:
            vn_ = -vn_
        out = out + vn_ * (HULL_PAD * np.clip(where / 0.02, 0, 1))[:, None]
    return out


def rim_loops(pos, tris):
    """The edge of a sheet as closed loops, in order. Spurs (where the cut
    left a stray edge) are pruned; at a branch the walk takes the
    straightest way on, and backs up from a dead end, until it is home."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    nbr = {}
    # An edge on the rim is used by an odd number of triangles (once, or
    # three times where the cut pinched the sheet).
    for a, b in uk[c % 2 == 1]:
        nbr.setdefault(int(a), set()).add(int(b))
        nbr.setdefault(int(b), set()).add(int(a))
    changed = True
    while changed:
        changed = False
        for v in [v for v, n in nbr.items() if len(n) < 2]:
            for w in nbr.pop(v):
                nbr.get(w, set()).discard(v)
            changed = True
    left = set(nbr)
    loops = []
    while left:
        start = max(left, key=lambda v: (len(nbr[v]) == 2, -v))
        path, onpath = [start], {start}
        tried = {start: set()}
        found = False
        while path and not found:
            v = path[-1]
            prev = path[-2] if len(path) > 1 else None
            d0 = pos[v] - pos[prev] if prev is not None else None
            cands = [w for w in nbr[v] if w != prev and w not in tried[v] and (w not in onpath or (w == start and len(path) > 8))]
            if not cands:
                path.pop()
                onpath.discard(v)
                continue
            if d0 is not None:
                cands.sort(key=lambda w: -np.dot(d0, pos[w] - pos[v]) / (np.linalg.norm(pos[w] - pos[v]) + 1e-12))
            w = cands[0]
            tried[v].add(w)
            if w == start:
                found = True
                break
            path.append(w)
            onpath.add(w)
            tried[w] = set()
        if found and len(path) > 20:
            loops.append(path)
        left -= set(path) | {start}
        left -= {v for v in list(left) if not (nbr[v] & left)}
    return loops


ROUND_RIM = 20      # rounds of smoothing a cup's outline gets
FILLED_BVH = None


def bra_cup(pos, tris, edge, skin, skin_n, lift, blend=0.0):
    """A cup shaped as a bra's is: an ellipsoid (a sphere stretched along
    the breast's own axes) fitted to the front of her breast under it (not
    the fold beneath, which faces down), as large as her breast and `lift`
    more, the even grid laid on it straight out from its centre; only its
    last `blend` toward the edge eases onto the edge itself. Her skin under
    it is not drawn, so it need not clear any bump of hers."""
    out = pos.copy()
    for side in (pos[:, 0] < 0, pos[:, 0] >= 0):
        sk = skin[(skin[:, 0] < 0) == (side[0] if False else bool(pos[side][0, 0] < 0))] if side.any() else None
        if sk is None:
            continue
        sn = skin_n[(skin[:, 0] < 0) == bool(pos[side][0, 0] < 0)]
        front = sk[(sn[:, 1] < -0.25)]
        if len(front) < 30:
            continue
        m = front.mean(0)
        _, _, R = np.linalg.svd(front - m)
        q = (front - m) @ R.T
        k, *_ = np.linalg.lstsq(np.c_[q ** 2, q], np.ones(len(q)), rcond=None)
        A, B, C, D, E, F = k
        if min(A, B, C) <= 0:
            print("BRA CUP fit not an ellipsoid", (A, B, C))
            continue
        cl = -np.array([D / (2 * A), E / (2 * B), F / (2 * C)])
        g = 1 + A * cl[0] ** 2 + B * cl[1] ** 2 + C * cl[2] ** 2
        ax = np.sqrt(g / np.array([A, B, C])) + lift
        c = m + cl @ R
        v = pos[side]
        loc = (v - c) @ R.T
        on = c + (loc / np.sqrt(((loc / ax) ** 2).sum(1))[:, None]) @ R
        t = np.clip(edge[side] / blend, 0, 1)[:, None] if blend > 0 else np.ones((side.sum(), 1))
        t = t * t * (3 - 2 * t)
        out[side] = v * (1 - t) + on * t
        print("BRA CUP axes", (ax * 100).round(1), "cm")
    return out


def onto_breast(pos, tris, lift, rounds=150):
    """A cup's even grid laid on her breast as it is (the areola filled in,
    nothing else changed): each point sent straight in or out to her skin,
    lifted, then ironed smooth without shrinking, so the cup has her own
    round shape, close-fitting, with no crease or bump in it."""
    global FILLED_BVH
    if FILLED_BVH is None:
        FILLED_BVH = BVHTree.FromPolygons([tuple(p) for p in P_FILLED], TRI.tolist())
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    rim = np.zeros(len(pos), bool)
    rim[uk[c == 1].ravel()] = True
    out = pos.copy()
    for side in (pos[:, 0] < 0, pos[:, 0] >= 0):
        q = pos[side & rim]
        if len(q) < 10:
            continue
        _, _, R = np.linalg.svd(q - q.mean(0))
        n = R[2]
        if n[1] > 0:
            n = -n            # out of her front
        for i in np.where(side & ~rim)[0]:
            best = None
            for d in (n, -n):
                hit = FILLED_BVH.ray_cast(Vector(pos[i] - d * 0.002), Vector(d), 0.2)
                if hit[0] is not None and (best is None or hit[3] < best[1]):
                    best = (np.array(hit[0][:]), hit[3], np.array(hit[1][:]))
            if best is not None:
                out[i] = best[0] + best[2] * lift
    out = taubin(out, tris, rounds=rounds)
    return out
FULLER = 0.005      # how far a cup stands off her skin


def even_cup(pos, at, tris, h=0.004):
    """Each cup's sheet made again on an even grid of triangles spanning
    its rim (the cut leaves slivers and the filled areola is crumpled, and
    a membrane solved on uneven triangles folds where their size changes).
    The rim is kept exactly; inside, points on a grid in the rim's own
    plane, the membrane then solved from the rim alone; everything else
    (weights, the field) from the nearest old point."""
    from matplotlib.path import Path as MPath
    from scipy.spatial import Delaunay
    tree = cKDTree(pos)
    P2, A2, T2 = [], [], []
    # (Twice-made triangles out, which would hide an edge.)
    _, first = np.unique(np.sort(tris, 1), axis=0, return_index=True)
    tris = tris[np.sort(first)]
    loops = rim_loops(pos, tris)
    print("CUP RIMS", [len(l) for l in loops])
    for loop in sorted(loops, key=len, reverse=True)[:2]:
        # The outline itself made a smooth curve (it follows her skin's cut
        # exactly, corners and all, and the bowl takes its shape from it).
        rimp = pos[loop].copy()
        for _ in range(ROUND_RIM):
            rimp = 0.5 * rimp + 0.25 * (np.roll(rimp, 1, 0) + np.roll(rimp, -1, 0))
        m = rimp.mean(0)
        _, _, R = np.linalg.svd(rimp - m)
        u, v = R[0], R[1]
        r2 = np.c_[(rimp - m) @ u, (rimp - m) @ v]
        path = MPath(r2)
        lo, hi = r2.min(0), r2.max(0)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
        gx[1::2] += h / 2
        g = np.c_[gx.ravel(), gy.ravel()]
        g = g[path.contains_points(g)]
        if len(g):
            d, _ = cKDTree(r2).query(g)
            g = g[d > 0.6 * h]
        pts2 = np.vstack([r2, g])
        tri = Delaunay(pts2).simplices
        tri = tri[path.contains_points(pts2[tri].mean(1))]
        p3 = np.vstack([rimp, m + g[:, :1] * u + g[:, 1:] * v])
        _, j = tree.query(p3)
        a3 = at[j].copy()
        # How far in from the edge (what the trim follows), measured across
        # the rim's plane.
        a3[:, -1] = np.r_[np.zeros(len(rimp)), cKDTree(r2).query(g)[0] if len(g) else []]
        base = sum(len(x) for x in P2)
        P2.append(p3)
        A2.append(a3)
        T2.append(tri + base)
    return np.vstack(P2), np.vstack(A2), np.vstack(T2)


def bubble(pos, tris, clear, out, ref=None):
    """A cup as a soap bubble blown in its rim, like a bra cup: nothing of
    her skin is kept but the rim, where the cup meets her. Across it, a
    membrane under even pressure: each point at its neighbours' middle,
    less the pressure along its normal (solved directly, the normals
    updated a few times), which settles perfectly smooth and round. The
    pressure is set, by halving, so the cup stands as high as her breast."""
    from scipy.sparse.linalg import splu
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    rim = np.zeros(len(pos), bool)
    rim[uk[c == 1].ravel()] = True
    inner = np.where(~rim)[0]
    A = adjacency(len(pos), tris).tocsr()
    L = (sparse.identity(len(pos)) - A).tocsr()
    Lii = splu(L[inner][:, inner].tocsc())
    Lib = L[inner][:, np.where(rim)[0]]
    xb = pos[rim]
    h = np.linalg.norm(pos[uk[:, 0]] - pos[uk[:, 1]], axis=1).mean()
    sign = 1.0 if (vertex_normals(pos, tris) * out).sum(1).mean() > 0 else -1.0

    def blow(p):
        x = pos.copy()
        for _ in range(12):
            n = sign * vertex_normals(x, tris)
            rhs = -(Lib @ xb) + p * h * h * n[inner]
            x[inner] = np.column_stack([Lii.solve(rhs[:, k]) for k in range(3)])
        return x

    # Sized to her: the cup stands as high off its rim as her breast does
    # under it, and a few millimetres more (her skin under a cup is not
    # drawn, so no small bump of hers needs clearing).
    right = (pos[:, 0] < 0) & ~rim
    up = out[right].mean(0)
    up /= np.linalg.norm(up)
    base = pos[rim & (pos[:, 0] < 0)].mean(0)

    def height(x):
        return ((x[right] - base) @ up).max()

    # Her breast's own height, from the sheet as it was cut from her.
    target = (((ref[ref[:, 0] < 0] - base) @ up).max() if ref is not None else height(pos)) + FULLER
    lo, hi = 0.0, 0.05
    while height(blow(hi)) < target and hi < 1e4:
        lo, hi = hi, hi * 2
    for _ in range(14):
        mid = (lo + hi) / 2
        if height(blow(mid)) < target:
            lo = mid
        else:
            hi = mid
    x = blow(hi)
    print("BUBBLE pressure %.3f, height %.4f (her breast %.4f)" % (hi, height(x), target - FULLER))
    return x


def taubin(pos, tris, rounds=40, w=None):
    """Creases, lumps and uneven patches taken out of a sheet without
    shrinking it (Taubin's smoothing: a step in, a slightly larger step back
    out); the more rounds, the larger the unevenness ironed out, while the
    size and fit stay. The edge stays put. `w` (0 to 1 a point) irons only
    where it is asked, easing out round it."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    onb = np.zeros(len(pos), bool)
    onb[uk[c == 1].ravel()] = True
    A = adjacency(len(pos), tris)
    for _ in range(rounds):
        for k in (0.5, -0.53):
            pos = np.where(onb[:, None], pos, pos + k * (1.0 if w is None else w[:, None]) * (A @ pos - pos))
    return pos


def fuller(pos, f, tris, most=0.004, reach=0.03):
    """A cup filled out where it runs toward the cleavage (her skin goes a
    little flat there, which in plate reads as pinched): lifted along its
    normal by up to `most`, nothing at its edge, the full amount `reach`
    inside it, and more toward the middle of her chest than the outside."""
    inward = np.clip(1 - np.abs(pos[:, 0]) / 0.14, 0, 1)
    t = np.clip(f / reach, 0, 1)
    lift = most * (t * t * (3 - 2 * t)) * (0.35 + 0.65 * inward)
    return pos + vertex_normals(pos, tris) * lift[:, None]


# Each bone's opposite number, for mirroring a piece's weights.
SWAP = np.array([BI.get(n[:-2] + {"_l": "_r", "_r": "_l"}[n[-2:]], i) if n[-2:] in ("_l", "_r") else i
                 for i, n in enumerate(BONES)])


def mirrored(pos, at, tris):
    """A pair made of its right half and that half's mirror image (her
    breasts are not quite each other's; the cups should be)."""
    keep = (pos[tris][:, :, 0] < 0).all(1)
    t = tris[keep]
    used = np.unique(t)
    re = -np.ones(len(pos), int)
    re[used] = np.arange(len(used))
    p, a, t = pos[used], at[used], re[t]
    mp = p * np.array([-1, 1, 1])
    ma = a.copy()
    ma[:, 0] *= -1                                   # the normal
    ma[:, 3:3 + NB] = a[:, 3:3 + NB][:, SWAP]        # the weights
    return np.vstack([p, mp]), np.vstack([a, ma]), np.vstack([t, t[:, ::-1] + len(p)])


def pushes_off_skin(pos, lift):
    """How far, and which way, each point must move to stand `lift` off her skin
    (one distance, or one to each point)."""
    push = np.zeros_like(pos)
    lift = np.broadcast_to(np.asarray(lift, float), (len(pos),))
    for i in range(len(pos)):
        q, n, _, _ = BVH.find_nearest(Vector(pos[i]))
        if q is None:
            continue
        d = (Vector(pos[i]) - q).dot(n)
        if d < lift[i]:
            push[i] = (n * (lift[i] - d))[:]
    return push


def clear_of_skin(pos, lift, tris=None, spread=0.003, rounds=20, fall=0.9):
    """At least `lift` off her skin everywhere. With `tris`, the part of any
    push over `spread` is smoothed over the sheet, its way averaged with its
    neighbours' and its size never less than the point's own need, nor less
    than `fall` of theirs (so it fades out round the pushed patch): a plate
    lifted off a hollow moves as one piece. (Pushed point by point, each
    along its own nearest normal, the neck side of the ranger's second
    pauldron, 19 mm off her over the rise of her neck, was torn from 5 mm
    steps to 24 mm and its rim could not be bound.) Pushes under `spread`
    (every skin-tight piece's) are left exactly as they were."""
    push = pushes_off_skin(pos, lift)
    size = np.linalg.norm(push, axis=1)
    if tris is not None and len(tris) and size.max() > spread:
        over = push * (np.maximum(size - spread, 0) / np.maximum(size, 1e-12))[:, None]
        need = np.linalg.norm(over, axis=1)
        A = adjacency(len(pos), tris)
        eased = over.copy()
        for _ in range(rounds):
            m = A @ eased
            ml = np.linalg.norm(m, axis=1)
            mag = np.maximum(ml * fall, need)
            eased = np.where((ml > 1e-12)[:, None], m / np.maximum(ml, 1e-12)[:, None] * mag[:, None], eased)
        pos = pos + (push - over) + eased
        # (an eased push can lean off a point's own normal: made up here)
        push = pushes_off_skin(pos, lift)
        size = np.linalg.norm(push, axis=1)
        print("CLEAR eased pushes over %.0f mm (largest %.1f mm) out over the sheet" % (spread * 1000, np.linalg.norm(over, axis=1).max() * 1000 + spread * 1000))
    pos = pos + push
    if (size > 0).any():
        print("CLEAR pushed", int((size > 0).sum()), "of", len(pos))
    return pos


# (20 Oct, armor 8, a face judge's whole-frame FAIL at creation's Look: the warden's pauldron, a fair dome stood 12 mm
# off her everywhere, rose off the top of her shoulder like a hoop with the forest behind it (turn -40), and its neck
# side ran along her top's strap, so the strap's edge showed ragged under its gold binding (front). Now its neck side
# is cut back clear of the strap (PAUL_STRAP_CLEAR from the strap's laid centre line, corners rounded) and its rim is
# seated onto her where her skin faces up, the top of her shoulder, PAUL_SEAT_GAP off her, eased in over
# PAUL_SEAT_BAND from the rim: a plate resting on her shoulder, flaring off her arm below. Off: PAUL_SEAT=0)
PAUL_SEAT = os.environ.get("PAUL_SEAT", "1") == "1"
STRAP_FINAL = os.environ.get("STRAP_FINAL", "1") == "1"
RIB_TRIM = os.environ.get("RIB_TRIM", "warden.strap").split(",")   # (the ribbons whose gold is laid from their own line, by name prefix, see ribbon; "": all cut from their sheet as before)
PAUL_BESIDE = tuple(float(v) for v in os.environ.get("PAUL_BESIDE", "0.019,0.006").split(","))   # (its rim beside the strap: metres from the strap's line, and the reach; 0 = off; see seated)   # (the warden's shoulder straps laid on final_skin_bvh, see warden())
PAUL_SEAT_GAP, PAUL_SEAT_BAND, PAUL_STRAP_CLEAR = (float(v) for v in os.environ.get("PAUL_SEAT_K", "0.003,0.035,0.019").split(","))
PAUL_SEAT_IN = tuple(float(v) for v in os.environ.get("PAUL_SEAT_IN", "0.0,0.03").split(","))   # (its neck side: metres in from the ball of her shoulder)
PAUL_SEAT_UP = tuple(float(v) for v in os.environ.get("PAUL_SEAT_UP", "0.2,0.5").split(","))


def strap_clear(name, clear):
    """A field on her skin (metres, positive allowed): out of the ribbon `name`'s way on the far side of it from her
    middle, at least `clear` from its laid centre line."""
    line = RIBBON_LINE[name]
    d, j = cKDTree(line).query(P)
    lateral = np.abs(X) > np.abs(line[j, 0])
    return np.where(lateral, d - clear, -d - clear)


_FINAL_SKIN = []


def final_skin_bvh():
    """(once per run, see _final_skin_bvh)"""
    if not _FINAL_SKIN:
        _FINAL_SKIN.append(_final_skin_bvh())
    return _FINAL_SKIN[0]


def _final_skin_bvh():
    """Her skin as her last body build left it (PAUL_SEAT_BODY, default godot/art/people/heroine.glb), in this scene's
    axes: the build's own skin stands up to 8 mm above it on top of her shoulder near her neck (the neck cut and nape
    ease move it after the pieces are cut), so a piece seated within millimetres of her is seated on this. None if
    there is no such file."""
    import json as json_
    import struct as struct_
    path = os.environ.get("PAUL_SEAT_BODY", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb"))
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    jl = struct_.unpack_from("<I", b, 12)[0]
    g = json_.loads(b[20:20 + jl])
    bn = b[20 + jl + 8:]

    def acc(i):
        a = g["accessors"][i]
        v = g["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a["componentType"]]
        nc = {"SCALAR": 1, "VEC3": 3}[a["type"]]
        return np.frombuffer(bn, dt, a["count"] * nc, v.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, nc)
    mi = next(n["mesh"] for n in g["nodes"] if n.get("name") == "Heroine" and "mesh" in n)
    vs, fs, off = [], [], 0
    for pr in g["meshes"][mi]["primitives"]:
        q = acc(pr["attributes"]["POSITION"]).astype(float)
        vs.append(np.stack([q[:, 0], -q[:, 2], q[:, 1]], 1))
        fs.append(acc(pr["indices"]).reshape(-1, 3).astype(np.int64) + off)
        off += len(q)
    return BVHTree.FromPolygons([tuple(p_) for p_ in np.vstack(vs)], np.vstack(fs).tolist())


def seated(name, pos, tris, edge, gap_to, band, up, where=None, beside=None):
    """A plate's rim brought down onto her: each point within `band` of its edge, where her skin under it faces up
    (its normal's height, ramped over `up`), moved in along her (smoothed) normal until it stands `gap_to` off her
    at the rim, eased to nothing `band` in, so the plate turns down onto her as a rolled flange does. `where`, a
    weight by place (the pauldron's neck side only: its far end rides her arm). `beside` (a ribbon's name, distance,
    reach): its rim where it runs beside that strap set that far from the strap's laid centre line, across her
    (PAUL_BESIDE)."""
    skin_ = final_skin_bvh() or BVH

    def near(p_):
        q_, n_ = np.zeros_like(p_), np.zeros_like(p_)
        for i in range(len(p_)):
            h = skin_.find_nearest(Vector(p_[i]))
            q_[i], n_[i] = h[0][:], h[1][:]
        return q_, n_
    A = adjacency(len(pos), tris)
    q, n = near(pos)
    g0 = ((pos - q) * n).sum(1)
    for _ in range(6):
        n = A @ n
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    w = (1 - ramp(edge, 0.0, band)) * ramp(n[:, 2], *up) * (where(pos) if where is not None else 1.0)
    for _ in range(4):
        w = 0.5 * w + 0.5 * (A @ w)
    if name in os.environ.get("DUMP", "").split(","):
        # (its sheet as it comes to be seated, with the seat's weight and normals, for study)
        np.savez(os.path.join(os.environ.get("TEMP", "."), f"dump_{name}_3seat.npz"), pos=pos, tris=tris, w=w, n=n, edge=edge)
    for it in range(3):
        q, _ = near(pos)
        g = ((pos - q) * n).sum(1)
        pos = pos - n * (w * np.maximum(g - gap_to, 0.0))[:, None]
    if beside is not None:
        # (21 Oct, armor 8 r3, a max judge on the seated pauldron: where the top's strap runs beside its cut neck side
        # the gap between them pinched to a busy double gold line at the top (4.0 to 8.8 mm, gold to strap). The cut
        # is made on this scene's skin and the plate is then shelled and seated, so its rim wanders across her from
        # the cut. Now each rim point beside the strap is set `dist` from the strap's laid centre line, measured
        # across her (in her skin's plane, square to the strap), fully within `reach` of that and fading out over
        # the next `reach`; the sheet in from the rim follows, eased to nothing over the seat's band)
        lname, dist, reach = beside
        line = RIBBON_LINE[lname]
        tl = np.gradient(line, axis=0)
        tl /= np.linalg.norm(tl, axis=1)[:, None] + 1e-12
        e_ = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
        u_, c_ = np.unique(e_, axis=0, return_counts=True)
        rim_ = np.zeros(len(pos), bool)
        rim_[u_[c_ == 1].ravel()] = True

        def across(p_):
            _, j_ = cKDTree(line).query(p_)
            r_ = p_ - line[j_]
            r_ = r_ - tl[j_] * (r_ * tl[j_]).sum(1)[:, None]
            r_ = r_ - n_s * (r_ * n_s).sum(1)[:, None]
            return r_
        _, n_s = near(pos)
        r0 = across(pos)
        d0 = np.linalg.norm(r0, axis=1)
        k_ = rim_ & (d0 < dist + 2 * reach)
        wk = (1 - ramp(d0, dist + reach, dist + 2 * reach)) * k_
        D = np.zeros_like(pos)
        D[k_] = (r0[k_] / (d0[k_, None] + 1e-12)) * ((dist - d0[k_]) * wk[k_])[:, None]
        Dr = D.copy()
        fall = 1 - ramp(edge, 0.0, band)
        for _ in range(40):
            D = A @ D
            D[rim_] = Dr[rim_]
            D *= fall[:, None]
            D[rim_] = Dr[rim_]
        pos = pos + D
        d1 = np.linalg.norm(across(pos), axis=1)
        full = k_ & (wk > 0.99)
        if full.any():
            print("BESIDE %s: %d rim points set %.1f mm from %s's line (were %.1f..%.1f, now %.1f..%.1f), %d fading out; most moved %.1f mm"
                  % (name, full.sum(), dist * 1000, lname, d0[full].min() * 1000, d0[full].max() * 1000, d1[full].min() * 1000,
                     d1[full].max() * 1000, int((k_ & ~full & (wk > 0)).sum()), np.linalg.norm(D, axis=1).max() * 1000))
    q, _ = near(pos)
    g = ((pos - q) * n).sum(1)
    pos = pos + n * (np.maximum(gap_to - g, 0.0) * (w > 0.01))[:, None]
    e = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    fi = np.tile(np.arange(len(tris)), 3)
    o = np.lexsort((e[:, 1], e[:, 0]))
    e, fi = e[o], fi[o]
    same = np.nonzero((e[1:] == e[:-1]).all(1))[0]
    fa, fb, ed2 = fi[same], fi[same + 1], e[same]
    band_f = (w[tris] > 0.05).any(1)

    def flipped(p_):
        fn = np.cross(p_[tris[:, 1]] - p_[tris[:, 0]], p_[tris[:, 2]] - p_[tris[:, 0]])
        fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-15
        return ((fn[fa] * fn[fb]).sum(1) < 0) & (band_f[fa] | band_f[fb])
    # (a sliver at its rim folded back under its neighbour (the left pauldron kept one, 0.15 mm2, its tip 0.4 mm into
    # her): the smaller face's free corner laid out flat in its neighbour's plane on the far side of their shared
    # edge, so the seated rim is clean)
    for _ in range(5):
        flip = flipped(pos)
        if not flip.any():
            break
        for i in np.nonzero(flip)[0]:
            ea, eb = pos[ed2[i, 0]], pos[ed2[i, 1]]
            ar = [np.linalg.norm(np.cross(pos[tris[f, 1]] - pos[tris[f, 0]], pos[tris[f, 2]] - pos[tris[f, 0]])) for f in (fa[i], fb[i])]
            small, big = (fa[i], fb[i]) if ar[0] <= ar[1] else (fb[i], fa[i])
            tip = [v for v in tris[small] if v not in ed2[i]][0]
            far = [v for v in tris[big] if v not in ed2[i]][0]
            u = (eb - ea) / (np.linalg.norm(eb - ea) + 1e-15)

            def off(v_):
                r_ = pos[v_] - ea
                return r_ - u * (r_ @ u)
            o_far = off(far)
            side = -o_far / (np.linalg.norm(o_far) + 1e-15)
            r_tip = pos[tip] - ea
            pos[tip] = ea + u * (r_tip @ u) + side * np.linalg.norm(off(tip))
    flip = flipped(pos)
    q, _ = near(pos)
    g = ((pos - q) * n).sum(1)
    rim = (edge < 0.004) & (w > 0.5)
    print("SEAT %s: %d rim points seated (gap before %.1f..%.1f mm), now %.1f mm median, %.1f max; %d points eased in; "
          "%d flipped face pairs in the band" % (name, rim.sum(), g0[rim].min() * 1000 if rim.any() else 0, g0[rim].max() * 1000 if rim.any() else 0,
                                                 np.median(g[rim]) * 1000 if rim.any() else 0, g[rim].max() * 1000 if rim.any() else 0,
                                                 int((w > 0.01).sum()), int(flip.sum())))
    return pos


NEST = {}   # (plates nested in a set: their directions and radii so far)


def shell(name, pos, centre, clear, most=0.006, nest=None):
    """A rigid plate's surface: its distance from `centre` (the ball of her
    shoulder) fitted, over the directions it covers, by a smooth quadric in
    them, so the plate is one fair dome and no longer a cast of the muscle
    under it (judge 2: the pauldrons were lumpy); then lifted as a whole,
    up to `most`, until it stands `clear` off her everywhere (any rest left
    to clear_of_skin)."""
    d = pos - centre
    r = np.linalg.norm(d, axis=1)
    u = d / r[:, None]
    x, y, z = u.T
    B = np.stack([np.ones_like(x), x, y, z, x * x, y * y, x * y, y * z, z * x], 1)
    # (fitted again without the points far off it, a scrap or a fold, which
    # then keep their own distance within 4 mm of the dome's)
    keep = np.ones(len(r), bool)
    # (ridged: a plate covering a narrow spread of directions left the fit
    # ill-posed, and it ran off by a metre at its fringe)
    for _ in range(4):
        Bk = B[keep]
        coef = np.linalg.solve(Bk.T @ Bk + 1e-4 * len(Bk) * np.diag([0] + [1] * (B.shape[1] - 1)), Bk.T @ r[keep])
        rf = B @ coef
        res = np.abs(rf - r)
        keep = res < max(3 * np.sqrt((res[keep] ** 2).mean()), 0.004)
    # (and no point moved more than 12 mm from where it was cast)
    if nest is None:
        rf = np.clip(np.where(keep, rf, np.clip(r, rf - 0.004, rf + 0.004)), r - 0.012, r + 0.012)
    # (a set's plate is the dome exactly: points left off it within 4 mm
    # dented lame 2 and waved its rim, judge 5)
    print("SHELL %s: %d of %d points off the dome, eased to within 4 mm of it" % (name, (~keep).sum(), len(r)))
    up = 0.0
    for _ in range(6):
        q = centre + u * (rf + up)[:, None]
        need = np.linalg.norm(pushes_off_skin(q, clear), axis=1).max()
        if need < 0.0002 or up >= most:
            break
        up = min(most, up + need * 1.15)
    print("SHELL %s: fair dome, %.1f mm rms off the cast (largest %.1f), lifted %.1f mm" %
          (name, np.sqrt(((rf - r) ** 2).mean()) * 1000, np.abs(rf - r).max() * 1000, up * 1000))
    rf = rf + up
    if nest is not None:
        # (lames, built from the lowest up: each lifted as a whole until it
        # stands `step` outside every plate under it wherever it overlaps
        # them, so one never cuts through another; fitted alone, they did)
        # (compared in the world, along this plate's own rays: each plate
        # has its own centre, on her arm at its height)
        group, step = nest
        if group in NEST:
            q = NEST[group]
            here = centre + u * rf[:, None]
            dist, j = cKDTree(q).query(here, distance_upper_bound=0.03)
            ok = np.isfinite(dist)
            dd = here[ok] - q[j[ok]]
            radial = (dd * u[ok]).sum(1)
            lateral = np.linalg.norm(dd - radial[:, None] * u[ok], axis=1)
            over = lateral < 0.004
            need = max(0.0, float((step - radial[over]).max())) if over.any() else 0.0
            rf = rf + need
            print("SHELL %s: nested %.1f mm out over the %d points it overlaps" % (name, need * 1000, over.sum()))
            NEST[group] = np.vstack([q, centre + u * rf[:, None]])
        else:
            NEST[group] = centre + u * rf[:, None]
    return centre + u * rf[:, None]


def dump(name, stage, pos, tris, field):
    """A piece's sheet at a stage of its making, saved for study (DUMP=its
    name in the environment)."""
    if name in os.environ.get("DUMP", "").split(","):
        np.savez(os.path.join(os.environ.get("TEMP", "."), f"dump_{name}_{stage}.npz"), pos=pos, tris=tris, field=field)


def mls_flat(pos, w, n, sigma):
    """A sheet's points moved, along `n`, onto a local quadric fitted to
    the sheet round each (moving least squares, Gaussian `sigma`): what is
    smaller than about `sigma` (muscle, a nipple's cone) is gone and the
    sheet's own curve stays, as a stiffened panel or a cup moulded over a
    form would lie. Moved by `w` (0 to 1) a point; only points within
    `sigma` of its height are fitted, so the far side of a fold never pulls
    on it."""
    n = np.asarray(n, float) / np.linalg.norm(n)
    a = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    a /= np.linalg.norm(a)
    b = np.cross(n, a)
    u, v, h = pos @ a, pos @ b, pos @ n
    tree = cKDTree(np.c_[u, v])
    out = pos.copy()
    for i in np.where(w > 1e-3)[0]:
        j = np.asarray(tree.query_ball_point([u[i], v[i]], 2.5 * sigma), int)
        j = j[np.abs(h[j] - h[i]) < sigma]  # (this layer of the sheet only)
        if len(j) < 12:
            continue
        du, dv = u[j] - u[i], v[j] - v[i]
        g = np.exp(-(du * du + dv * dv) / (2 * sigma * sigma))
        M = np.c_[np.ones(len(j)), du, dv, du * du, du * dv, dv * dv] * np.sqrt(g)[:, None]
        c = np.linalg.lstsq(M, h[j] * np.sqrt(g), rcond=None)[0]
        out[i] = pos[i] + n * (w[i] * (c[0] - h[i]))
    return out


def over_nipples(pos, tris, least=float(os.environ.get("NIP_RISE", "0.0015")), s=0.008, dome=0.065, rim_reach=0.02, fit=0.02):
    """A garment cut over her filled breasts drawn over each nipple as a
    low, soft rise (`least` high, `s` its spread), so her nipples show
    through it as shapes; the tip of her nipple, through it, is hidden
    under it (the owner: hide the tip, leave the nipple visible). (Raised
    to clear all of her nipple, it was a cone; 3 mm high and 9 mm across,
    the owner wanted less poke, the same on both: 1.5 mm and 11 mm, her
    skin's own tip tucked under it, and each rise set on the two nipples'
    mirrored mean, so neither sits higher or further out. Still a point:
    the cup followed her breast's own cone to its tip, so first it is eased
    into a dome within `dome` of each tip, along its normals only, and the
    rise is 0.7 mm over about 16 mm. Judge 9: at 0.7 mm it can't be seen
    from either side, and the owner asked for it on the Arcanist and the
    Ranger: back to the owner's own 1.5 mm, NIP_RISE.)"""
    mean = (NIPPLE["l"] * np.array([-1, 1, 1]) + NIPPLE["r"]) / 2
    tips = [mean * np.array([-1 if sd == "l" else 1, 1, 1]) for sd in ("l", "r")]
    dist = np.min([np.linalg.norm(pos - t, axis=1) for t in tips], axis=0)
    # (judge 3: eased within 35 mm on a smoothstep, the dome's own rim was a
    # bump in the highlight. Now 65 mm on a smootherstep (curvature-continuous
    # at its rim), and eased off over `rim_reach` toward the cut edge rather
    # than pinned there: a sweetheart or plunge line can pass within reach.)
    w = np.clip(1 - dist / dome, 0, 1)
    w = w ** 3 * (w * (6 * w - 15) + 10)
    rim = np.array([v for loop in edge_loops(tris) for v in loop], int)
    if len(rim):
        rd = cKDTree(pos[rim]).query(pos)[0]
        t = np.clip(rd / rim_reach, 0, 1)
        w = w * t ** 3 * (t * (6 * t - 15) + 10)
    # (and the cone taken out by a fit, not by smoothing: smoothed along its
    # normals over so wide a reach, her breast itself would shrink. A local
    # quadric of the sheet over each breast, `fit` wide, keeps her breast's
    # curve and drops anything smaller, her nipple's cone with it.)
    for sd, t in zip(("l", "r"), tips):
        near = np.linalg.norm(pos - t, axis=1) < dome
        if near.sum() < 30:
            continue
        nrm = vertex_normals(pos, tris)[near].mean(0)
        pos = mls_flat(pos, w * near, nrm / np.linalg.norm(nrm), fit)
    nor = vertex_normals(pos, tris)
    out = pos.copy()
    for sd in ("l", "r"):
        tip = mean * np.array([-1 if sd == "l" else 1, 1, 1])
        near = np.where(np.linalg.norm(pos - tip, axis=1) < 0.05)[0]
        if len(near) < 10:
            continue
        centre = pos[near[cKDTree(pos[near]).query(tip)[1]]]
        h = least
        d = np.linalg.norm(pos[near] - centre, axis=1)
        out[near] += nor[near] * (h * np.exp(-(d / s) ** 2))[:, None]
        print("NIPPLE RISE %s %.1f mm" % (sd, h * 1e3))
    return out


SHEET = {}   # (each piece's sheet as finished: points, triangles, weights, thickness)


# (judge fin1 c: two steel spikes stood out past the gold roll down the back of each
# Warden greave, over her heel: a sliver of the cut 0.02-0.04 mm high, or a triangle
# folded back over its neighbour, at the sheet's edge, thickened along its skewed
# facing. GREAVE_RIM=1: such triangles at the edge dropped before the plate is made
# (the roll already lies along the edge and covers the notch they leave); 0: as before.)
GREAVE_RIM = os.environ.get("GREAVE_RIM", "1") == "1"


def rim_cleaned(name, pos, at, tris, least=0.0002, fold=0.3, rounds=6):
    """A sheet's edge cleared of slivers and folds: each triangle on its edge
    lower than `least` (its smallest height) or folded against a neighbour
    (their facings' dot under `fold`) dropped, again as the edge moves in;
    the points left without a triangle dropped with them."""
    tris = np.asarray(tris)
    gone = 0
    for _ in range(rounds):
        nf = len(tris)
        e = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
        _, iv, cnt = np.unique(e, axis=0, return_inverse=True, return_counts=True)
        iv = iv.ravel()
        on_edge = (cnt[iv].reshape(3, -1) == 1).any(0)
        a, b, c = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
        fn = np.cross(b - a, c - a)
        ar = np.linalg.norm(fn, axis=1)
        fu = fn / (ar[:, None] + 1e-15)
        longest = np.maximum.reduce([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)])
        height = ar / (longest + 1e-15)
        o = np.argsort(iv, kind="stable")
        s = iv[o]
        k = np.where(s[1:] == s[:-1])[0]
        f1, f2 = o[k] % nf, o[k + 1] % nf
        d = (fu[f1] * fu[f2]).sum(1)
        worst = np.ones(nf)
        np.minimum.at(worst, f1, d)
        np.minimum.at(worst, f2, d)
        bad = on_edge & ((height < least) | (worst < fold))
        if not bad.any():
            break
        gone += int(bad.sum())
        tris = tris[~bad]
    if gone:
        used = np.unique(tris)
        remap = np.full(len(pos), -1, dtype=np.int64)
        remap[used] = np.arange(len(used))
        pos, at, tris = pos[used], at[used], remap[tris]
    print("RIMCLEAN %s: %d slivers or folds dropped from its edge" % (name, gone))
    return pos, at, tris


# A lining under part of a piece's edge (GREAVE_LINE, s17 lead; the
# coordinator's ruling on fin1's dark slit over her heel): dark leather from
# just inside the edge (spec[3] in, under the plate) down toward her skin,
# spec[0] short of it and at most spec[1] of the way, eased in over spec[2]
# where a run of the chosen edge ends. `sel(pos, loop)` picks the loops.
# Like the Warden cups' CUP_LINE: closed from the inside, the plate's own
# form and edge are as judged; the lining rides with the plate's weights.
GREAVE_LINE = [float(v) for v in os.environ.get("GREAVE_LINE", "0.0012,0.9,0.006,0.0015").split(",")]


def edge_lining(name, pos, at, tris, spec, sel):
    if spec[0] <= 0:
        return None
    loops = [np.array(lp) for lp in edge_loops(tris) if sel(pos, lp)]
    tree_ = cKDTree(pos)
    LP, LW, LT = [], [], []
    for run in loops:
        k_ = len(run)
        if k_ < 4:
            continue
        q = pos[run]
        qq = np.vstack([q[-1:], q, q[:1]])
        tg = (qq[2:] - qq[:-2])
        tg /= np.maximum(np.linalg.norm(tg, axis=1), 1e-9)[:, None]
        n_ = at[run, :3] / np.maximum(np.linalg.norm(at[run, :3], axis=1), 1e-9)[:, None]
        inn = np.cross(n_, tg)
        inn /= np.maximum(np.linalg.norm(inn, axis=1), 1e-9)[:, None]
        m_ = k_ // 2
        if at[tree_.query(q[m_] + inn[m_] * 0.004)[1], -1] < at[tree_.query(q[m_] - inn[m_] * 0.004)[1], -1]:
            inn = -inn
        a_ = q + inn * spec[3] - n_ * 0.0003
        sk_ = np.array([SKIN_BVH.find_nearest(Vector(v))[0][:] for v in a_])
        L_ = np.linalg.norm(sk_ - a_, axis=1)
        f_ = np.clip((L_ - spec[0]) / np.maximum(L_, 1e-6), 0, spec[1])
        b_ = a_ + (sk_ - a_) * f_[:, None]
        o_ = sum(len(x) for x in LP)
        nx = [(i + 1) % k_ for i in range(k_)]
        LP.append(np.vstack([a_, b_]))
        LW.append(np.vstack([at[run, 3:3 + NB]] * 2))
        LT += [[o_ + i, o_ + nx[i], o_ + k_ + nx[i]] for i in range(k_)] + [[o_ + i, o_ + k_ + nx[i], o_ + k_ + i] for i in range(k_)]
        print("EDGE LINING %s: %d points round its edge; the plate %.1f-%.1f mm off her there, the lining %.1f mm deep at most"
              % (name, k_, L_.min() * 1000, L_.max() * 1000, (L_ * f_).max() * 1000))
    if not LP:
        return None
    return np.vstack(LP), np.vstack(LW), np.array(LT)


# (armor 17 N3: pieces whose keep_off weights (her Head's) are made the same both sides before the cut: her Head
# weight sits higher on her right side of the neck, so the arcanist's high collar was cut up to 2.5 cm lower on her
# right, a notch where it met the plunge (max judge OJ1). Each point takes the lower of its own weight and its
# mirror's, so her right's collar comes up to her left's, left = right.)
KEEP_SYM = {k_ for k_ in os.environ.get("KEEP_SYM", "arcanist.corset").split(",") if k_}
_MIRROR_P = []


def keep_sym(w):
    if not _MIRROR_P:
        _MIRROR_P.append(cKDTree(P).query(P * np.array([-1.0, 1.0, 1.0]))[1])
    return np.minimum(w, w[_MIRROR_P[0]])


def piece(name, field, mkey, lift=0.003, thick=0.003, smooth=0, bevel=0.0012, trim=None, clear=None, soften=3, dome=False, keep_off=("Head", "neck_01"), cut=None, iron=0, hull=None, studs=None, budget=None, filled=False, edge=30, slot=True, bridge=False, bind=True, rigid=None, stiff=None, studs_off=None, weigh=None, hold=None, crotch=None, rim_clean=False, line=None, seat=None, blend_from=None):
    """A region of her skin made into a piece of her outfit. `rigid`, a
    centre, makes it a rigid plate: a fair dome round that centre (shell())
    on one blend of bones throughout, so it moves as one piece. `trim`, as
    (material, width, height, thickness), edges it with a band laid on the
    piece itself, so the two can never part. `clear` is how close to the
    skin it may come once smoothed (the lift unless said): plate lifted well
    off and allowed close only at a peak keeps the peak as a hint, not a
    cast of it. `soften` eases the field first; a strap, narrower than
    some of her triangles, is not eased (easing would wear it through)."""
    # Never her head or hair (the hair is part of her mesh).
    slot_m = SLOT if slot is True else (SLOT & (X < 0) if slot == "right" else (SLOT & (X > 0) if slot == "left" else np.zeros(len(P), bool)))
    wk_ = wsum(*keep_off)
    if name in KEEP_SYM and not np.isscalar(wk_):
        wk_ = keep_sym(wk_)
    f = smooth_field(np.minimum.reduce([field, (0.3 - wk_) * 0.1, (0.5 - HAIR) * 0.1,
                                        np.where(slot_m, -0.004, 1.0)]), soften)
    # `cut`, a second field, trims the piece after it is shaped: a cup
    # keeps the shape of the full cup however low it is cut.
    attr = np.hstack([N, W, (hull if hull is not None else -np.ones(len(P)))[:, None],
                      (cut if (cut is not None and not callable(cut)) else np.ones(len(P)))[:, None], f[:, None]])
    # A garment crossing her crotch is cut off just in front of and just
    # behind the slot between her thighs (`gap` is how far a point is out
    # of that box), and the two cut edges joined by a strip under her.
    gap = np.maximum.reduce([GAP_F - Y, Y - GAP_B, Z - GAP_Z, np.abs(X) - 0.07]) if bridge else np.ones(len(P))
    # (`crotch`, a field on her skin taken as it is, not eased: what a one-piece
    # keeps of her under the crotch, its own sheet carried on there, no gusset)
    clipf = np.minimum(f, gap) if crotch is None else np.maximum(np.minimum(f, gap), crotch)
    if crotch is not None:
        attr[:, -1] = clipf
    dump(name, "0skin", P_FILLED if (dome or filled) else P, TRI, clipf)  # SOLVER1 TEMP
    pos, at, tris = clip(clipf, P_FILLED if (dome or filled) else P, np.hstack([attr, gap[:, None]]), TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris, joined=name in FOLD_SAFE)
    dump(name, "1clip", pos, tris, at[:, -2])
    skin_at = pos.copy()   # (her skin as cut, for SHEER_UNTANGLE)
    gap_at, at = at[:, -1], at[:, :-1]
    nor = at[:, :3] / (np.linalg.norm(at[:, :3], axis=1)[:, None] + 1e-12)
    if crotch is not None:
        PIECE_SRC[name] = (pos.copy(), nor.copy())
    if callable(lift):
        # (a lift by place, read on her skin: the full glove's top eased in to the fingerless
        # glove's, see glove_a_lift; its largest after for whatever else reads the lift)
        lv_ = np.asarray(lift(pos), float)
        pos = pos + nor * lv_[:, None]
        lift = float(lv_.max())
    else:
        pos = pos + nor * lift
    if hull is not None:
        pos = hulled(pos, at[:, -3], tris, fill=HULL_FILL.get(name, 0))
        if HULL_FILL.get(name):
            # (filled, a point over her toes may come from between them: its weights from her skin nearest where it
            # now is (her leg's), not where it was cut; as cut, her toes came out through it in the walk, 122 samples)
            sel_ = np.where(LEGW[name[-1]] > 0.5)[0]
            d_, j_ = cKDTree(P[sel_]).query(pos, k=6)
            iw_ = 1.0 / np.maximum(d_, 1e-4)
            nw_ = (W[sel_][j_] * iw_[:, :, None]).sum(1) / iw_.sum(1)[:, None]
            t_ = np.clip((at[:, -3] - 0.005) / 0.015, 0, 1)[:, None]   # (the filled foot only: the ankle's bridge as cut)
            at[:, 3:3 + NB] = at[:, 3:3 + NB] * (1 - t_) + nw_ * t_
    pos = relax(pos, tris, interior=smooth, edge=edge)
    if iron:
        pos = taubin(pos, tris, rounds=iron)
    if stiff is not None:
        # (a stiffened panel: ironed far more where `stiff` asks, then held
        # off her skin below, so it bridges what it no longer follows)
        # (judge 3: Taubin's smoothing keeps every wave longer than a few
        # edges, so her abs stayed; a quadric fit `stiff[0]` wide drops them.)
        # (several zones, each fitted and lifted on its own: (width, field))
        for st in (stiff if isinstance(stiff, list) else [stiff]):
            if callable(st):
                # (or a piece's own shaping, handed its sheet: the arcanist's
                # taut gore)
                pos = st(pos, tris)
                continue
            wide, zone = st[:2]
            sw = zone(pos)
            if len(st) > 2 and st[2] > 0:
                # (faded to nothing over the last `st[2]` before its edge: fitted
                # up to the edge, the plunge's foot stood 7 mm off her and its
                # bound edge came out toothed, judge 6; the distance to the
                # edge is the exact cut's where one is given: the field the
                # sheet was cut from stands 20 mm past the plunge, so it
                # never faded there)
                sw = sw * ramp(np.minimum(at[:, -1], cut(pos)) if callable(cut) else at[:, -1], 0.0, st[2])
            pos = mls_flat(pos, sw, (0.0, -1.0, 0.0), wide)
            # (lifted as a whole, where stiff, onto what it now bridges: pushed
            # off point by point it took the shape back)
            need = np.linalg.norm(pushes_off_skin(pos, lift), axis=1)
            up = np.percentile(need[sw > 0.5], 95) if (sw > 0.5).any() else 0.0
            pos = pos + vertex_normals(pos, tris) * (sw * up)[:, None]
            print("STIFF %s: fitted %.0f mm wide, lifted %.1f mm" % (name, wide * 1000, up * 1000))
    dump(name, "2shaped", pos, tris, at[:, -1])
    if filled and not dome:
        pos = over_nipples(pos, tris)
    if dome:
        cut_from, cut_at = pos.copy(), at.copy()
        pos, at, tris = even_cup(pos, at, tris)
        pos = bra_cup(pos, tris, at[:, -1], cut_from, cut_at[:, :3], FULLER)
        # Weights, normals and any cut, from where each point of the bowl
        # now stands over the sheet it replaced.
        _, j = cKDTree(cut_from).query(pos)
        edge = at[:, -1].copy()
        at = cut_at[j].copy()
        at[:, -1] = edge
        pos, at, tris = mirrored(pos, at, tris)
    if cut is not None:
        if callable(cut):
            at[:, -2] = cut(pos)
        at[:, -1] = np.minimum(at[:, -1], at[:, -2])
        cut_done = True
        pos, at, tris = clip(at[:, -2], pos, at, tris)
        pos, at, tris = weld(pos, at, tris)
        pos = relax(pos, tris, interior=0)
        if crotch is not None and LEO_LIP > 0:
            # (the one-piece's edge round the V's foot: no lip up a crease's far wall, see LEO_LIP)
            pos, at, tris = lip_trimmed(name, pos, at, tris, LEO_LIP)
        dump(name, "3cut", pos, tris, at[:, -1])
    if hold is not None:
        # (`hold`: chosen edges held down onto her skin, see held_edges)
        pos, held = held_edges(name, pos, tris, *hold)
    if rigid is not None:
        if isinstance(rigid, tuple):
            pos = shell(name, pos, np.asarray(rigid[0], float), lift if clear is None else clear, nest=rigid[1:])
        else:
            pos = shell(name, pos, np.asarray(rigid, float), lift if clear is None else clear)
        # (one blend for the whole plate, its skin's mean: it moves rigidly)
        blend_ = at[:, 3:3 + NB].mean(0, keepdims=True)
        if blend_from is not None:
            # (`blend_from`: the blend of the plate as cut from that field instead, made exactly as above, so a plate
            # cut back (PAUL_SEAT) swings as it did)
            fb_ = smooth_field(np.minimum.reduce([blend_from, (0.3 - wsum(*keep_off)) * 0.1, (0.5 - HAIR) * 0.1,
                                                  np.where(slot_m, -0.004, 1.0)]), soften)
            ab_ = np.hstack([N, W, -np.ones((len(P), 1)), np.ones((len(P), 1)), fb_[:, None], np.ones((len(P), 1))])
            pb_, ab_, tb_ = clip(fb_, P, ab_, TRI)
            pb_, ab_, tb_ = weld(pb_, ab_, tb_, joined=name in FOLD_SAFE)
            blend_ = ab_[:, 3:3 + NB].mean(0, keepdims=True)
        at[:, 3:3 + NB] = four_bones(blend_)
        print("RIGID %s: %s" % (name, ", ".join("%s %.4f" % (BONES[k_], at[0, 3 + k_]) for k_ in np.nonzero(at[0, 3:3 + NB] > 0)[0])))
    if not dome and not filled:
        pos = clear_of_skin(pos, lift if clear is None else (clear(pos) if callable(clear) else clear), tris)
    if seat is not None:
        # (`seat`: its rim brought down onto her where `seat` asks, see seated)
        pos = seated(name, pos, tris, at[:, -1], *seat)
    dump(name, "3pre", pos, tris, at[:, -1])  # SOLVER1 TEMP
    # Every edge bound: in the trim's colour where one is asked, else in the
    # piece's own (a rolled hem). Sheer and painted pieces are left as cut.
    beads = []
    # (eased before its edge is bound, so the binding moves as the edge does)
    at[:, 3:3 + NB] = four_bones(eased_weights(pos, tris, at[:, 3:3 + NB]))
    # (`weigh`: the piece's own weights over its skin's; the spaulder's
    # leather takes each plate's blend where riveted under it)
    if weigh is not None:
        at[:, 3:3 + NB] = four_bones(weigh(pos, at[:, 3:3 + NB]))
    if bind and len(SPEC[mkey]) < 7 and mkey != "ink":
        if trim:
            tkey, w, h, tt = trim
            bspec = BIND_SPEC.get(name) or (tkey, max(w, 0.005), max(h, 0.0006), 0.0018)
        else:
            bspec = (mkey, 0.0045, 0.0005, 0.0015)
        pos, beads = bind_edges(name, pos, at, tris, bspec[0], bspec[1], bspec[2], bspec[3], thick,
                                stitch=kind(mkey) == "leather")
        if name in BIND_CLAMP:
            # (s18 BIND_REACH: its loose edge brought out onto its rolls)
            pos = reached_to_rolls(name, pos, tris, beads)
        dump(name, "4bound", pos, tris, at[:, -1])
        trim = None
    if rim_clean:
        # (`rim_clean`: slivers and folds at its edge dropped, see rim_cleaned)
        pos, at, tris = rim_cleaned(name, pos, at, tris)
    if name in SHEER_UNTANGLE and len(skin_at) == len(pos):
        # (s20: the stocking had 126 triangles turned over against her skin,
        # 2-3 cm folds 3-11 cm in from its edges on her inner front thighs:
        # sheer, its alpha rises where it faces away, so each read as a white
        # or lavender streak, animation judge 5. Untangled against her skin
        # as cut, then held off her again.)
        dump(name, "5folded", pos, tris, at[:, -1])
        pos = sheet_untangled(name, pos, skin_at, tris, np.ones(len(pos), bool))
        pos = clear_of_skin(pos, lift, None)
        n_ = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
        n0_ = np.cross(skin_at[tris[:, 1]] - skin_at[tris[:, 0]], skin_at[tris[:, 2]] - skin_at[tris[:, 0]])
        print("SHEER_UNTANGLE %s: %d turned over after the clearance" % (name, int(((n_ * n0_).sum(1) <= 0).sum())))
    SHEET[name] = (pos.copy(), tris.copy(), at[:, 3:3 + NB].copy(), thick)
    lining = edge_lining(name, pos, at, tris, line[0], line[1]) if line is not None else None
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))] + beads
    if name in BIND_CLAMP:
        # (s18 BIND_CLAMP: its thickened edge kept inside its rolls)
        clamped_to_rolls(made[0], beads, BIND_CLAMP[name])
    if lining is not None:
        # (`line`: a dark leather lining under the chosen edge, see edge_lining)
        made.append(finish(name + "_lining", lining[0], lining[1], lining[2], "darkleather", 0.0012, 0.0004, 10 ** 6))
    if hold is not None and len(held):
        # (the held edge as built, for her skin's tuck under it: BODY_OUT)
        made[0]["hold_line"] = pos[held].ravel().tolist()
    if any("_stitch" in o.name for o in beads):
        made[0]["geo_stitch"] = True
    if bridge and crotch is None:
        made += crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift)
    if studs:
        made += rivets(name, pos, at, tris, thick, studs, off=studs_off)
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr, edge=30)
            if os.environ.get("RIB_DUMP"):
                np.savez(os.path.join(os.environ["RIB_DUMP"], name + "_trim.npz"), tp=tp, tr=tr, sp=pos, st=tris, edge=at[:, -1])
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel, 1500))
    # Only the piece itself hides her skin: its binding, trim, studs and
    # stitches overhang its edge, and skin hidden under them showed as holes
    # in her just past it.
    # (A rigid plate tucks nothing: it moves apart from her skin, and the
    # skin tucked under it showed in its shadow as it swung.)
    for o in made:
        o["hides"] = o is made[0] and len(SPEC[mkey]) < 7 and rigid is None
    return made


HOLD_OFF, HOLD_FULL, HOLD_SLOPE = (float(v) for v in os.environ.get("HOLD", "0.001,0.012,0.25").split(","))
HOLD_BAND, HOLD_GROOVE, HOLD_SOFT = (float(v) for v in os.environ.get("HOLD_TUCK", "0.05,0.0015,0.030").split(","))
# (the leotard leg lines held onto her, 419ede90, down to their foot at the crotch
# (LEO_HOLD_Z: select above, fade from/to, metres over CROTCH): seen from the game camera
# at her front quarter, the strip showed by a pixel under the foot of the leg line, which
# stood 2-4 mm off her there; LEO_FOOT widens the foot (eased out over 3.5 cm up) and
# LEO_GUSSET_F carries the gusset further forward under it, the bare corner between them
# 3.9 mm from the strip. HOLD_CAP: under a held edge her tuck is eased in from the edge
# for every rule, not only the hold's (the standard rule tucked 7 mm right at the held edge,
# seen as cyan slivers when the cloth lifted in motion).)
LEO_HOLD = os.environ.get("LEO_HOLD", "1") == "1"
LEO_HOLD_Z = tuple(float(v) for v in os.environ.get("LEO_HOLD_Z", "0.002,-0.02,-0.01").split(","))
HOLD_CAP = os.environ.get("HOLD_CAP", "1") == "1"
LEO_FOOT = float(os.environ.get("LEO_FOOT", "0.004"))
LEO_GUSSET_F = float(os.environ.get("LEO_GUSSET_F", "0.026"))
LEO_U = tuple(float(v) for v in os.environ.get("LEO_U", "0.016,0.004").split(","))
# (LEO_GW: the gusset LEO_GW[0] wider in front of GAP_F + LEO_GW[1], eased out by
# GAP_F + LEO_GW[2], under the U's rounded corners; LEO_UG: where the gusset is
# under the U's edge, from LEO_UG[0] inside its edge to LEO_UG[1] outside; LEO_UH:
# there the edge is held onto the gusset's top, LEO_UH * 30 mm higher, not off it)
LEO_UG = tuple(float(v) for v in os.environ.get("LEO_UG", "0.001,0.005").split(","))
LEO_GW = tuple(float(v) for v in os.environ.get("LEO_GW", "0.005,0,0.015").split(","))
# (the arcanist's gusset, judge fin1: LEO_GHALF its half-width, LEO_GSTEEP how far up the
# slot's walls (|N_x|), LEO_GLIFT off her, LEO_GTHICK thick (0: the corset's), LEO_GBIND=1
# binds and stitches its edges. Defaults as built before (s17: unbound, narrowed or kept off
# the walls, the strip under her showed from the game cameras: vis5 game 0 -> 50 to 312))
LEO_GHALF = float(os.environ.get("LEO_GHALF", "0.016"))
LEO_GSTEEP = float(os.environ.get("LEO_GSTEEP", "0.96"))
LEO_GLIFT = float(os.environ.get("LEO_GLIFT", "0.001"))
LEO_GTHICK = float(os.environ.get("LEO_GTHICK", "0"))
LEO_GBIND = os.environ.get("LEO_GBIND", "1") == "1"
LEO_UH = float(os.environ.get("LEO_UH", "0.07"))
# (judge fin1, route (a): LEO_ONE=1 makes the arcanist's leotard one piece, as a real one is
# made: the corset's own sheet carried on under her crotch to the thong's foot, one leg-line
# binding a side from front to back and one stitch row, no U across the foot, no gusset.
# Under her its leg lines stand LEO_ONE_W[0] (front) to LEO_ONE_W[1] (back) out from her
# middle, its back end rounded LEO_ONE_W[2]; it goes up the slot's walls while |N_x| is
# under LEO_ONE_STEEP, laid LEO_ONE_LIFT off her (as the gusset was) below LEO_ONE_Z[0]
# over the crotch and behind it; the back's thong cut from LEO_ONE_Z[1] up.)
LEO_ONE = os.environ.get("LEO_ONE", "1") == "1"
LEO_ONE_W = tuple(float(v) for v in os.environ.get("LEO_ONE_W", "0.0185,0.016,0.012").split(","))
LEO_ONE_STEEP = float(os.environ.get("LEO_ONE_STEEP", "0.96"))
LEO_ONE_LIFT = float(os.environ.get("LEO_ONE_LIFT", "0.001"))
LEO_ONE_Z = tuple(float(v) for v in os.environ.get("LEO_ONE_Z", "0.02,0.03").split(","))
# (LEO_ONE_LAY: the laid sheet eased in from LEO_ONE_LAY[0] down to LEO_ONE_LAY[1] over the crotch)
LEO_ONE_LAY = tuple(float(v) for v in os.environ.get("LEO_ONE_LAY", "0.012,0.002").split(","))
PIECE_SRC = {}   # (a piece cut with `crotch`: its sheet's skin points and normals, before lifting)
# (LEO_ONE_TUCK: her skin under the one-piece's crotch tucked no deeper than this. The
# built gusset tucked her not at all (its 'hides' was cleared as it joined the corset's
# pieces), and lying 1 mm off untucked skin is what kept the strip unseen: tucked all the
# way under the held leg lines (s17 dry one1) or 3 mm (one2), a tunnel opened under the
# sheet and the strip showed through it (vis5 game 5 / 120, low 1115 / 483; at 0: 0 / 0).
# LEO_ONE_DEPTH (0 off): in front of the slot the leg lines go no lower than this under
# its roof, easing 12 mm deeper from 2 cm in front of the crotch point to 2 cm behind it,
# so they don't drop below the V's foot seen from the front as two fangs (one3); at 4 mm
# the strip's bare edge came within 5.8 mm and showed low from the front quarter (one4).)
LEO_ONE_TUCK = float(os.environ.get("LEO_ONE_TUCK", "0"))
LEO_ONE_DEPTH = float(os.environ.get("LEO_ONE_DEPTH", "0.007"))
# (s18 leo2, judge fin2 1a, LEO_SLOT_CAP (0 off): the knob below the U's right end (a_leo_f, a_half_f, a_full_f's foot)
# was the leg-line roll under her crotch point (posed y -0.008 to 0), down the slot's wall ~9 mm under its roof (cut there
# by |N_x| 0.96, below LEO_ONE_DEPTH's eased floor), seen through the gap between her thighs below the U's bottom. Round
# the crotch point (CROTCH_Y -2 cm to +2 cm, full from -8 mm to +8 mm) the walls go no deeper than this: below ~4 mm
# they are steeper than |N_x| 0.86 there, left out of the strip.)
# (dry t1/t2: at 5 mm the knob rose ~3 mm (leo_f eye at rest: foot rows 203 -> 181-187, centre 161) but vis5 low went
# 8 -> 82, mid 0 -> 1: the walls' band 5-9 mm under the roof hides the strip from the low cameras. Off.)
LEO_SLOT_CAP = float(os.environ.get("LEO_SLOT_CAP", "0"))
LEO_SLOT_BACK = float(os.environ.get("LEO_SLOT_BACK", "0.008"))   # (full to CROTCH_Y + this, eased out over 12 mm more)
# (s18 leo3, judge fin2 1a, LEO_BRIDGE (0 off): the knob is the slot's own arch. Seen from the front the sheet lining the slot
# shows the arch between her thighs: its middle 5-6 mm above the leg-line rolls 9 mm down each wall (rest, a_leo_f eye: the
# outline over the gap 32 rows concave). LEO_BRIDGE: round the crotch point the laid sheet spans the slot instead, its height
# over the walls' edge squashed to this, its middle LEO_BRIDGE_SAG lower; LEO_BRIDGE_Y (from CROTCH_Y): eased in, full, full,
# eased out. Never under the line exact() cuts the walls at.)
# (dry b2/b3: concave 32 -> 7 rows (a 1 mm notch left at the middle), COVER 10.6 kept, but the pocket under the span lets vis5
# see the strip: game/mid/low 0/0/7 -> 0/1/11 (b3, zone -0.022,-0.012,0.006,0.016), 0/5/12 (b2, -0.030,-0.014,0.008,0.024). Off.)
LEO_BRIDGE = float(os.environ.get("LEO_BRIDGE", "0"))
LEO_BRIDGE_SAG = float(os.environ.get("LEO_BRIDGE_SAG", "0.0008"))
LEO_BRIDGE_Y = tuple(float(v) for v in os.environ.get("LEO_BRIDGE_Y", "-0.030,-0.014,0.008,0.024").split(","))
# (LEO_ROOF_FIX: roof_zs cast again from the slot where the cast from below hit her thighs; the floor was deeper than the walls' cut there anyway)
LEO_ROOF_FIX = os.environ.get("LEO_ROOF_FIX", "1") == "1"
# (LEO_LIP (0 off): s17 leo3, the flecks at the V's foot. Her right groin crease runs just inside the leg line there
# (her left one 4-6 mm outside it), so the cut left the sheet's last 2-3 mm turned up the thigh's wall; its roll,
# faced by that lip, stood on its side and the 3 mm sheet came out through it as ragged flecks (dry one4-7, base:
# sections across the line). Round the V's foot, in front of the slot, the edge strip is trimmed where it
# stands more than LEO_LIP off the plane of the sheet 3-8 mm in from its edge, so the roll sits on a flat edge.)
LEO_LIP = float(os.environ.get("LEO_LIP", "0"))   # (0.0008 in dry lip2: flecks 0 px, but vis5 mid 0->5, low 7->22: off until the trim keeps the strip covered)


def lip_trimmed(name, pos, at, tris, h_max):
    """A cut sheet's edge strip (the last 3 mm) trimmed where it stands more than
    h_max off the plane of the sheet 3-8 mm in from the edge (a lip turned up a
    crease's far wall), round the V's foot only (in front of the slot: trimmed under
    the crotch too, the strip showed, s17 leo3 lip1)."""
    e = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    uk, c = np.unique(e, axis=0, return_counts=True)
    bv = np.unique(uk[c == 1])
    bv = bv[(pos[bv, 2] < CROTCH + 0.035) & (pos[bv, 2] > CROTCH - 0.005) & (np.abs(pos[bv, 0]) < 0.05) & (pos[bv, 1] < CROTCH_Y - 0.02) & (pos[bv, 1] > CROTCH_Y - 0.09)]
    if not len(bv):
        return pos, at, tris
    nor = vertex_normals(pos, tris)
    tree = cKDTree(pos)
    de = cKDTree(pos[np.unique(uk[c == 1])]).query(pos)[0]
    f = np.full(len(pos), 1.0)
    for i in bv:
        nb = np.array(tree.query_ball_point(pos[i], 0.009))
        nb = nb[(de[nb] > 0.003) & (de[nb] < 0.008)]
        if len(nb) < 6:
            continue
        q = pos[nb]
        m = q.mean(0)
        n = np.linalg.eigh((q - m).T @ (q - m))[1][:, 0]
        st = np.array(tree.query_ball_point(pos[i], 0.004))
        st = st[de[st] < 0.003]
        f[st] = np.minimum(f[st], h_max - np.abs((pos[st] - m) @ n))
    if (f > 0).all():
        print("LIP %s: no lip over %.1f mm round the V's foot (%d edge points)" % (name, h_max * 1000, len(bv)))
        return pos, at, tris
    n0 = int((f <= 0).sum())
    at = at.copy()
    at[:, -2] = np.minimum(at[:, -2], f)
    at[:, -1] = np.minimum(at[:, -1], at[:, -2])
    pos, at, tris = clip(at[:, -2], pos, at, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris, interior=0)
    print("LIP %s: %d points of the edge strip stood over %.1f mm off the sheet round the V's foot: trimmed (%d edge points)" % (name, n0, h_max * 1000, len(bv)))
    return pos, at, tris
TUCK_ZONES = {}  # (an outfit: [(cap, zone of her skin 0 to 1)], tucked no deeper there)
RBOOT_GONE = float(os.environ.get("RBOOT_GONE", "0.005"))


def held_edges(name, pos, tris, sel, fade=None):
    """A skin-tight piece's chosen edges held down onto her skin, as an
    elastic edge is: within HOLD_FULL of the edge the sheet lies HOLD_OFF off
    her, and from there it rises back to its own lie no steeper than
    HOLD_SLOPE (one smooth line, no step or ridge; a stiff panel keeps its
    look away from the edge). Only ever pulled toward her, along her normal,
    so the cut stays where it was on her. (The arcanist's leg lines stood 5-7
    mm off her: looked in at a glance under the edge, her untucked belly
    showed as a skin wedge, judge 14.) `sel` picks the held edge points,
    `fade` (0 to 1 a point) eases the hold out where it is not wanted."""
    e = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    uk, c = np.unique(e, axis=0, return_counts=True)
    be = uk[c == 1]
    bv = np.unique(be)
    held = bv[sel(pos[bv])]
    if not len(held):
        return pos, held
    hb = be[np.isin(be[:, 0], held) & np.isin(be[:, 1], held)]
    smp = np.concatenate([pos[hb[:, 0]] * (1 - t) + pos[hb[:, 1]] * t for t in np.linspace(0, 1, 5)])
    d, _ = cKDTree(smp).query(pos)
    rw = 0.004
    r = np.where(d < HOLD_FULL - rw, 0.0, np.where(d > HOLD_FULL + rw, d - HOLD_FULL, (d - HOLD_FULL + rw) ** 2 / (4 * rw)))
    cap = HOLD_OFF + HOLD_SLOPE * r + (0.0 if fade is None else (1 - fade(pos)) * 0.03)
    out = pos.copy()
    k, drop, at_edge = 0.001, [], []
    for i in np.nonzero(cap < 0.02)[0]:
        q, n, _, _ = BVH.find_nearest(Vector(pos[i]))
        if q is None:
            continue
        s_ = (Vector(pos[i]) - q).dot(n)
        h = min(max(0.5 + 0.5 * (cap[i] - s_) / k, 0.0), 1.0)
        s2 = cap[i] * (1 - h) + s_ * h - k * h * (1 - h)
        if d[i] < 0.0015:
            at_edge.append((s_, min(s_, s2)))
        if s2 < s_:
            out[i] = pos[i] + np.array(n[:]) * (s2 - s_)
            drop.append(s_ - s2)
    ae = np.array(at_edge) * 1000 if at_edge else np.zeros((1, 2))
    print("HOLD %s: %d edge points; at the edge %.1f-%.1f mm off her (median %.1f) now %.1f-%.1f (median %.1f); %d points pulled in, up to %.1f mm"
          % (name, len(held), ae[:, 0].min(), ae[:, 0].max(), np.median(ae[:, 0]), ae[:, 1].min(), ae[:, 1].max(), np.median(ae[:, 1]),
             len(drop), max(drop, default=0) * 1000))
    return out, held


def rivets(name, pos, at, tris, thick, mkey, spacing=0.028, inset=0.011, r=0.0032, off=None, spots=None):
    """Domed rivets set in from a piece's edge every `spacing`, on its
    outer face: the detail that makes a plate read as made. `spots`, as
    (points on the sheet, their normals, their weights), sets them where a
    piece has laid out its own rows instead."""
    if spots is None:
        f = at[:, -1]
        cand = np.where(np.abs(f - inset) < 0.0025)[0]
        if off is not None and len(cand):
            # (none under or within 4 mm of the plate over this one: the plate's
            # rim sliced them, judge 5)
            cand = cand[off[cKDTree(P).query(pos[cand])[1]] < -0.004]
        if len(cand) == 0:
            return []
        picked = []
        tree_p = []
        for i in cand[np.argsort(pos[cand, 2])]:
            if all(np.linalg.norm(pos[i] - q) >= spacing for q in tree_p):
                picked.append(i)
                tree_p.append(pos[i])
        nor = vertex_normals(pos, tris)
        spots = (pos[picked], nor[picked], at[picked, 3:3 + NB])
    spot_p, spot_n, spot_w = (np.asarray(x, float) for x in spots)
    if len(spot_p) == 0:
        return []
    P2, W2, T2 = [], [], []
    nu, nv = 12, 4
    for i in range(len(spot_p)):
        n = spot_n[i] / np.linalg.norm(spot_n[i])
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        base = spot_p[i] + n * (thick + 0.0003)
        # (judge 5: near half-spheres read as beads: a dome 30% of its
        # width high, on a thin flange)
        fl = 0.08 * r
        pts = [base + n * (fl + r * 0.52)]
        rings = [(r * np.sin((np.pi / 2) * k / nv), fl + r * 0.52 * np.cos((np.pi / 2) * k / nv)) for k in range(1, nv + 1)]
        # (the flange just past the head: 1.3 r wide it caught the light as a pale
        # washer, a halo, and edge-on round a dark head it read as a hole, judge 7)
        rings += [(r * 1.12, fl), (r * 1.12, 0.0)]
        for rr, hh in rings:
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                pts.append(base + (np.cos(ph) * t + np.sin(ph) * b) * rr + n * hh)
        o = sum(len(x) for x in P2)
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv + 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(pts))
        W2.append(np.repeat(spot_w[i:i + 1], len(pts), 0))
        T2.append(np.array(tri))
    if not P2:
        return []
    pp, ww, tt = np.vstack(P2), np.vstack(W2), np.vstack(T2)
    if (vertex_normals(pp, tt) * (pp - np.repeat(spot_p, ((nv + 2) * nu + 1), 0))).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    print("RIVETS", name, len(spot_p))
    return [finish(name + "_rivets", pp, ww, tt, "iron" if mkey == "darksteel" else mkey, 0.0002, 0.0, 10 ** 7, scraps=False)]  # (each rivet is a part: scraps dropped them all past 50, animation)


def islands(pos, tris, keep_frac=0.02):
    """Triangles of a sheet in pieces too small to be meant (scraps a cut
    leaves): only pieces with at least keep_frac of the sheet are kept."""
    n = len(pos)
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]]])
    g = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    k, lab = sparse.csgraph.connected_components(g, directed=False)
    if k == 1:
        return tris
    size = np.bincount(lab[tris[:, 0]], minlength=k)
    good = size >= keep_frac * len(tris)
    return tris[good[lab[tris[:, 0]]]]


ARM_BONES = [BI[n] for n in BONES if n.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "hand")]
BREAST_BONES = [BI[n] for n in ("breast_l", "breast_r") if n in BI]


UNSTEADIED = set()  # pieces that keep her skin's own weights over her breasts (bandeau)


def steady_on_breasts(wt, least=0.01, full=0.1):
    """Weights with her arms' share taken off where her breasts have any:
    none at `least` of her breasts' weight, all of it by `full` (that share
    given to the rest, in proportion; her upper chest's bone if nothing else
    is left). (Taken off all at once at a line, the line stepped the
    arcanist's neckline when she moved.)"""
    wt = np.array(wt, float)
    b = wt[:, BREAST_BONES].sum(1)
    on = b > least
    if not on.any():
        return wt
    k = np.clip((b[on] - least) / (full - least), 0, 1)
    k = k * k * (3 - 2 * k)
    w = wt[on].copy()
    w[:, ARM_BONES] *= (1 - k)[:, None]
    tot = w.sum(1)
    empty = tot < 1e-6
    w[empty, BI["spine_03"]] = 1
    tot[empty] = 1
    wt[on] = w / tot[:, None]
    return wt


def four_bones(wt):
    """At most four bones to a point, as the game takes them, cut smoothly:
    every weight less the point's fifth largest. (Left to the exporter,
    which keeps each point's four largest, neighbours kept different fours
    where a fourth and a fifth crossed, and an edge stepped there when she
    moved.)"""
    wt = np.array(wt, float)
    if wt.shape[1] <= 4:
        return wt
    fifth = -np.partition(-wt, 4, axis=1)[:, 4]
    wt = np.maximum(wt - fifth[:, None], 0)
    return wt / np.maximum(wt.sum(1, keepdims=True), 1e-9)


def eased_weights(pos, tris, wt, over=0.008):
    """Weights eased over about `over` of a sheet: her skin's weights are
    uneven from point to point, and an edge that took them as they are was
    pulled into steps and tears when she moved (her belts were, before
    theirs were eased too)."""
    if not len(tris):
        return wt
    el = np.linalg.norm(pos[tris[:, 0]] - pos[tris[:, 1]], axis=1)
    rounds = int(np.clip((over / max(float(np.median(el)), 1e-4)) ** 2, 0, 80))
    if not rounds:
        return wt
    A_ = adjacency(len(pos), tris)
    wt = np.array(wt, float)
    for _ in range(rounds):
        wt = A_ @ wt
    return wt / np.maximum(wt.sum(1, keepdims=True), 1e-9)


def pinholes_filled(name, pos, wt, tris, most=0.03):
    """Any small hole inside a sheet (a pocket where the field it was cut
    by dipped below nothing: it showed as a black notch in her suit) closed
    with a fan of triangles, wound as its neighbours are. Its edges proper,
    however short, are each at least a quarter of its longest."""
    from collections import defaultdict
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).tolist()
    have = set(map(tuple, e))
    nxt = defaultdict(list)
    for a, b in e:
        if (b, a) not in have:
            nxt[a].append(b)
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, v = [start], start
        while v in nxt:
            w = nxt[v].pop()
            if not nxt[v]:
                del nxt[v]
            if w == start:
                break
            loop.append(w)
            v = w
        loops.append(loop)
    if len(loops) < 2:
        return pos, wt, tris
    per = [float(np.linalg.norm(pos[lp] - pos[np.roll(lp, 1)], axis=1).sum()) for lp in loops]
    big = max(per)
    nrm = vertex_normals(pos, tris)
    add_p, add_w, add_t = [], [], []
    for lp, pr in zip(loops, per):
        if len(lp) < 3 or len(set(lp)) < len(lp) or pr >= most or pr >= big * 0.25:
            continue
        # A hole's fill faces the way the sheet round it does; a loop round
        # a small piece of its own (a fringe's tongue, a strip of trim)
        # would be filled facing against it, over the piece: never that.
        cen = pos[lp].mean(0)
        a_, b_ = pos[lp], pos[np.roll(lp, -1)]
        fan = np.cross(a_ - b_, cen - b_)
        if (fan * nrm[lp]).sum() <= 0:
            continue
        k = len(pos) + len(add_p)
        add_p.append(cen)
        add_w.append(wt[lp].mean(0))
        add_t += [[b, a, k] for a, b in zip(lp, np.roll(lp, -1))]
    if not add_p:
        return pos, wt, tris
    print("PINHOLES closed in %s: %d" % (name, len(add_p)))
    return np.vstack([pos, add_p]), np.vstack([wt, add_w]), np.vstack([tris, np.array(add_t, int)])


RIGID_UV = {}   # (a plate's name: (centre, arm axis, unrolled round the arm?))
ONE_ISLAND = set()   # (sheets laid out whole, one island with no seams)
SHEER_UNTANGLE = {k_ for k_ in os.environ.get("SHEER_UNTANGLE", "arcanist.stocking_l,arcanist.stocking_r").split(",") if k_}   # (s20, see piece)
ARC_HANDS = os.environ.get("ARC_HANDS", "fingerless")   # (s20: set again in arcanist(), see there)
FOLD_SAFE = {"arcanist.glove_l", "arcanist.glove_r"}   # (welded only along their own edges: weld(joined))


KEEP_FINE = {}   # (piece name prefix -> f(pos): points finish() never thins)
KEEP_SUB = {}    # (piece name prefix -> f(pos, wt, tris) -> (pos, wt, tris): zones finish() divides finer first)
# A skived edge (s17 lead; judge fin1's spikes at the Arcanist's skin edges):
# leather is pared thin where it goes under its binding, as a leatherworker
# skives an edge before it is bound. The corset's 3 mm sheet filled its roll
# with 0.25 mm to spare, and where the sheet tilted against the roll's facing
# its edge came out through the roll (the plunge's tooth and bump, the leg
# line's thorn and spurs; s17_spike's posed measure, 0.7-3.85 mm). Exact piece
# name -> (thickness at the cut as a share of the sheet's, eased to full over
# this many metres in). EDGE_SKIVE="" turns it off.
# The Arcanist's boning channels end flush over this many metres at the
# hip (judge fin1's tab and thorn were their square lower ends). 0 = off.
BONING_TAPER = float(os.environ.get("BONING_TAPER", "0.008"))
# (s18: a channel laid on a piece (`onto`) ends this far inside the piece's edge, its taper there. Its control
# line ran on past the leg line at her hips, where lay() missed the sheet and left its points at the control
# line's own depth, 10 cm inside her: the channel dived into her at the leg line, and the side of that dive was
# judge fin1/fin2's tab (r_hand_outer_rest) and thorn (a_leo_qr); the taper was on its end, inside her. 0 = off.)
BONING_CLIP = float(os.environ.get("BONING_CLIP", "0.008"))
# (touch-up 2, 18 Oct, the owner's C01 frames: the Reaver's cord is laid from inside the base of her neck and taut
# over the hollow between her collarbones and her neck, not snapped to the skin nearest each point, which jumped
# across that crease and hooked; ribbon(taut=). TAUT_ITERS: the passes of its pull. 0 = off.)
TAUT_CORD = int(os.environ.get("TAUT_CORD", "1"))
TAUT_ITERS = int(os.environ.get("TAUT_ITERS", "40"))
# (touch-up 3, 18 Oct, the C01 s10 firelight close-up: the cord showed at the back of her neck as a dark bracket and
# went missing down the side of her neck. Two causes, measured on the built rig with her head turned 40-60 degrees:
# the band of skin at her nape from 1 to 4 cm above neck_01 folds over itself in a turn (the skin's own weights; a
# point 3.5 mm off it, weighted exactly as it is, still goes 2-4 mm under), and the cord's back ran in that band
# with a 2 cm wobble (laid from inside, rising and dipping) and a V where its two ends met. So the cord is a closed
# loop (smoothed across its join) and its back is free to slide along her: eased straight, without shrinking up
# her neck (Taubin), no higher than NAPE_CORD below neck_01 at the back, taut over hollows as before. Its front,
# with the fangs, does not move. NAPE_CORD: metres below neck_01's head; < 0 = off.)
NAPE_CORD = float(os.environ.get("NAPE_CORD", "0.01"))
NAPE_ITERS = int(os.environ.get("NAPE_ITERS", "150"))
# (NAPE_SIDE: at her neck's sides it rides this much higher than behind, where her neck meets her shoulders: any
# lower and it lay out on top of her shoulders, 16 cm from her neck's axis. Her skin there holds in a turn up to
# 1.5 cm above neck_01.)
NAPE_SIDE = float(os.environ.get("NAPE_SIDE", "0.011"))
EDGE_SKIVE = {k_: (float(f_), float(o_)) for k_, f_, o_ in
              (e_.split(":") for e_ in os.environ.get("EDGE_SKIVE", "arcanist.corset:0.3:0.006").split(",") if e_)}
# (armor 17 N3: a piece's name -> a field on its points, the share of its thickness kept there (1 = all): the
# arcanist's shoulder caps a 2 mm leather hugging her, not a 3 mm pad, max judge OJ1. Set by the outfit.)
THIN_ZONE = {}


def loop_divided(pos, attr, tris, red, sw):
    """One Loop step on the faces `red`, closed red-green so it stays one
    sheet (a face with two or three of its edges split is divided whole, one
    with one is halved). New points by Loop's rules, every point's move from
    the plain midpoint (or its old place) scaled by `sw`, 0 to 1 per point;
    `attr` (weights) carried linearly."""
    nf = len(tris)
    fe = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, inv = np.unique(np.sort(fe, 1), axis=0, return_inverse=True)
    inv = inv.ravel().reshape(3, nf).T
    red = red.copy()
    while True:
        split = np.zeros(len(uk), bool)
        split[inv[red].ravel()] = True
        more = (~red) & (split[inv].sum(1) >= 2)
        if not more.any():
            break
        red |= more
    split = np.zeros(len(uk), bool)
    split[inv[red].ravel()] = True
    green = (~red) & (split[inv].sum(1) == 1)
    ef = np.full((len(uk), 2), -1)
    opp = np.full((len(uk), 2), -1)
    idx = np.arange(nf)
    for c in range(3):
        e, o = inv[:, c], tris[:, (c + 2) % 3]
        a = ef[e, 0] < 0
        ef[e[a], 0] = idx[a]
        opp[e[a], 0] = o[a]
    for c in range(3):
        e, o = inv[:, c], tris[:, (c + 2) % 3]
        b = ef[e, 0] != idx
        ef[e[b], 1] = idx[b]
        opp[e[b], 1] = o[b]
    sp = np.where(split)[0]
    a, b = uk[sp, 0], uk[sp, 1]
    lin = (pos[a] + pos[b]) / 2
    lp = lin.copy()
    inner = opp[sp, 1] >= 0
    lp[inner] = 3 / 8 * (pos[a[inner]] + pos[b[inner]]) + 1 / 8 * (pos[opp[sp[inner], 0]] + pos[opp[sp[inner], 1]])
    newp = lin + (lp - lin) * np.minimum(sw[a], sw[b])[:, None]
    newa = (attr[a] + attr[b]) / 2
    n = len(pos)
    bnd = np.zeros(n, bool)
    bnd[uk[ef[:, 1] < 0].ravel()] = True
    allred = np.ones(n, bool)
    allred[tris[~red].ravel()] = False
    A = sparse.coo_matrix((np.ones(2 * len(uk)), (np.r_[uk[:, 0], uk[:, 1]], np.r_[uk[:, 1], uk[:, 0]])), shape=(n, n)).tocsr()
    val = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    beta = (5 / 8 - (3 / 8 + np.cos(2 * np.pi / val) / 4) ** 2) / val
    sm = (1 - val * beta)[:, None] * pos + beta[:, None] * (A @ pos)
    p2 = pos + (sm - pos) * (sw * (allred & ~bnd))[:, None]
    mid = np.full(len(uk), -1)
    mid[sp] = n + np.arange(len(sp))
    out = [tris[~red & ~green]]
    r = np.where(red)[0]
    A_, B_, C_ = tris[r, 0], tris[r, 1], tris[r, 2]
    ab, bc, ca = mid[inv[r, 0]], mid[inv[r, 1]], mid[inv[r, 2]]
    out += [np.c_[A_, ab, ca], np.c_[ab, B_, bc], np.c_[ca, bc, C_], np.c_[ab, bc, ca]]
    g = np.where(green)[0]
    for c in range(3):
        gg = g[split[inv[g, c]]]
        if len(gg):
            m = mid[inv[gg, c]]
            v0, v1, v2 = tris[gg, c], tris[gg, (c + 1) % 3], tris[gg, (c + 2) % 3]
            out += [np.c_[v0, m, v2], np.c_[m, v1, v2]]
    return np.vstack([p2, newp]), np.vstack([attr, newa]), np.vstack(out)


def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000, scraps=True):
    """A sheet made a piece: her weights, its texture laid out at true size,
    a thickness and a rounded edge, bound to her skeleton. The sheet is
    first thinned to `budget` triangles (cut from a finely divided skin,
    it carries far more than its shape needs)."""
    # Any point that came out of the shaping as no number at all is dropped,
    # with the triangles it was part of.
    okp = np.isfinite(pos).all(1)
    if not okp.all():
        print("DROPPED", int((~okp).sum()), "broken points of", name)
        tris = tris[okp[tris].all(1)]
        pos = np.where(okp[:, None], pos, 0.0)
    # (scraps a cut leaves are dropped; a piece made of many small parts
    # on purpose, stitches, keeps them all)
    if scraps:
        # (points on top of each other made one, and the flat triangles
        # between them dropped: they have no facing, and thickened, stood
        # out as spikes)
        pos, wt, tris = weld(pos, np.asarray(wt, float), tris, r=0.0002, joined=name in FOLD_SAFE)
        tris = islands(pos, tris)
        pos, wt, tris = pinholes_filled(name, pos, wt, tris)
    # (zones a piece asks to have divided finer, KEEP_SUB: the glove's
    # fingertip caps, their outlines polygonal at 2x with 2 mm edges)
    sub = next((f for k_, f in KEEP_SUB.items() if name.startswith(k_)), None)
    if sub is not None:
        pos, wt, tris = sub(pos, np.asarray(wt, float), tris)
    # Its true edge, the sheet's border before it is thickened (both faces of
    # it): the shader's stitching and worn edges are measured from this. A
    # guess from its shape took any crease for an edge, and stitched rings
    # round them in the middle of a panel.
    e_ = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    uk_, cnt_ = np.unique(e_, axis=0, return_counts=True)
    be = uk_[cnt_ == 1]
    rim = None
    if len(be):
        t_ = np.linspace(0, 1, 4, endpoint=False)
        a_, b_ = pos[be[:, 0]], pos[be[:, 1]]
        rim = (a_[:, None] + (b_ - a_)[:, None] * t_[None, :, None]).reshape(-1, 3)
        rn = vertex_normals(pos, tris)[np.repeat(be[:, 0], len(t_))]
        rim = np.vstack([rim, rim + rn * thick])
        rim = rim[np.isfinite(rim).all(1)]
    # Over her breasts a piece moves with her body and breasts, never her
    # arms: her skin at the outer curve of each breast is partly her arm's,
    # and a garment taking that from it is dragged out of shape when her arm
    # moves (the skin under it is hidden). But at its edges it keeps her
    # skin's own weights, eased in over 3 cm: there her skin is seen, and
    # with her arm's share gone from the edge alone, her skin drew away from
    # under a plate cup's top as she ran, and you saw down into the cup.
    steady = np.asarray(wt, float) if any(name.startswith(n) for n in UNSTEADIED) else steady_on_breasts(wt)
    if len(be):
        d_ = cKDTree(pos[np.unique(be)]).query(pos)[0]
        s_ = np.clip((d_ - 0.005) / 0.025, 0, 1)
        s_ = (s_ * s_ * (3 - 2 * s_))[:, None]
        wt = steady * s_ + np.asarray(wt, float) * (1 - s_)
    else:
        wt = steady
    if scraps:
        wt = eased_weights(pos, tris, wt)
    # No point left without a bone (it would stay behind when she moves):
    # those take the weights of her skin nearest them.
    tot = wt.sum(1)
    if (tot < 0.01).any():
        _, jz = cKDTree(P).query(pos[tot < 0.01])
        wt = wt.copy()
        wt[tot < 0.01] = W[jz]
    wt = four_bones(wt)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pos], [], tris.tolist())
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if rim is not None and len(rim):
        obj["rim"] = rim.astype(np.float32).ravel().tolist()
    groups = {}
    for i in range(len(wt)):
        top = np.argsort(-wt[i])[:4]
        tot = wt[i, top].sum() or 1
        for j in top:
            if wt[i, j] > 0.003:
                if j not in groups:
                    groups[j] = obj.vertex_groups.new(name=BONES[j])
                groups[j].add([i], float(wt[i, j] / tot), "REPLACE")
    me.validate(clean_customdata=False)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # A piece that faces mostly one way (a cup, a plate, a knee) is laid out
    # in one projection along that way: no seams for the texture to break at.
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    ax = fn.sum(0)
    ax /= np.linalg.norm(ax) + 1e-12
    facing = (fn / (np.linalg.norm(fn, axis=1)[:, None] + 1e-12)) @ ax
    uv = me.uv_layers.new().data
    if name in RIGID_UV:
        # (a plate round a joint, laid out round it, one island: a lame
        # unrolled round her arm, a dome flattened about its middle;
        # projected flat, its sides stretched and the brushing went blocky)
        c_, ax_, ring = RIGID_UV[name]
        d_ = np.array([v.co[:] for v in me.vertices]) - c_
        mid = d_.mean(0) - ax_ * (d_.mean(0) @ ax_)
        e1 = mid / np.linalg.norm(mid)
        e2 = np.cross(ax_, e1)
        R_ = np.linalg.norm(d_, axis=1).mean()
        if ring:
            phi = np.arctan2(d_ @ e2, d_ @ e1)
            rad = np.linalg.norm(d_ - np.outer(d_ @ ax_, ax_), axis=1).mean()
            uvv = np.c_[phi * rad, d_ @ ax_]
        else:
            # (judge 5: flattened about the top of her arm, the brushing's
            # blocks turned with the bearing, rotated patches. Now laid out as
            # the lames are: u round her arm, v down the meridians from its
            # axis (the angle from it, times the dome's radius))
            th = np.arccos(np.clip((d_ / np.linalg.norm(d_, axis=1)[:, None]) @ -ax_, -1, 1))
            phi = np.arctan2(d_ @ e2, d_ @ e1)
            rho_ = np.linalg.norm(d_ - np.outer(d_ @ ax_, ax_), axis=1)
            uvv = np.c_[phi * np.median(rho_), th * R_]
        for poly in me.polygons:
            for li in poly.loop_indices:
                uv[li].uv = tuple(float(t) for t in uvv[me.loops[li].vertex_index])
    elif name in ONE_ISLAND:
        # (a sheet wrapped round a joint every way, laid out whole with no
        # seams, as little stretched as can be)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.mark_seam(clear=True)
        try:
            bpy.ops.uv.unwrap(method="MINIMUM_STRETCH", margin=0.0)
        except TypeError:
            bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.0)
        bpy.ops.object.mode_set(mode="OBJECT")
    elif np.percentile(facing, 2) > 0.15:
        u = np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        for poly in me.polygons:
            for li in poly.loop_indices:
                co = np.array(me.vertices[me.loops[li].vertex_index].co[:])
                uv[li].uv = (float(co @ u), float(co @ v))
    else:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    uv = me.uv_layers.active.data
    a3 = sum(p.area for p in me.polygons)
    a2 = 0.0
    for p in me.polygons:
        l = [uv[k].uv for k in p.loop_indices]
        for k in range(1, len(l) - 1):
            a2 += abs((l[k] - l[0]).cross(l[k + 1] - l[0])) / 2
    k = math.sqrt(a3 / max(a2, 1e-12)) * SPEC[mkey][3]
    for d in uv:
        d.uv = d.uv * k
    me.materials.append(mat(mkey))
    for p in me.polygons:
        p.use_smooth = True
    # A large piece keeps enough triangles to hold her curves (thinned too
    # far, it flattens and her skin pokes through between its points).
    area = sum(p.area for p in me.polygons)
    # (CAP_DENSITY: a piece build's own floor, triangles a square metre; tools/armor sets it for one part (the cuirass's
    # plate, armor 12 c3); unset, 60000 as always)
    budget = max(budget, int(area * globals().get("CAP_DENSITY", 60000)))
    if len(me.polygons) > budget:
        # Only the inside is thinned: the edge and two rows in from it keep
        # every point, so a cut line stays the smooth curve it was made.
        e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
        keep = np.zeros(len(pos))
        keep[uk[c == 1].ravel()] = 1
        A = adjacency(len(pos), tris)
        for _ in range(2):
            keep = np.maximum(keep, (A @ keep > 0).astype(float))
        # (and any zone a piece asks to keep whole, KEEP_FINE: the glove's
        # fingertip caps, polygonal at 2x when thinned; the budget grows by it)
        fine = next((f for k_, f in KEEP_FINE.items() if name.startswith(k_)), None)
        nfine = 0
        if fine is not None:
            kf = np.asarray(fine(pos)) > 0
            keep = np.maximum(keep, kf.astype(float))
            nfine = int(kf[tris].all(1).sum())
            budget += nfine
            print("KEEP_FINE %s: %d points, %d faces kept whole" % (name, int(kf.sum()), nfine))
        inner = obj.vertex_groups.new(name="_thin")
        inner.add([int(i) for i in np.where(keep == 0)[0]], 1.0, "REPLACE")
        dc = obj.modifiers.new("thin", "DECIMATE")
        dc.decimate_type = "COLLAPSE"
        dc.vertex_group = "_thin"
        dc.vertex_group_factor = 1000.0
        dc.ratio = budget / len(me.polygons)
        dc.use_symmetry = bool(abs(pos[:, 0].mean()) < 0.02)
        dc.symmetry_axis = "X"
    # (A sheer piece is one sheet: layered, it would not be sheer.)
    so = obj.modifiers.new("thick", "SOLIDIFY") if thick > 0 else None
    if so:
        so.thickness = thick
        so.offset = 1
        so.use_even_offset = False
        so.use_quality_normals = True
        so.use_rim = True
        # (EDGE_SKIVE: the sheet pared thin toward its bound edge)
        if name in EDGE_SKIVE and len(be):
            sf_, so_ = EDGE_SKIVE[name]
            ds_ = cKDTree(pos[np.unique(be)]).query(pos)[0]
            ws_ = np.clip(ds_ / so_, 0, 1)
            ws_ = ws_ * ws_ * (3 - 2 * ws_)
            if name in THIN_ZONE:
                # (THIN_ZONE: the share kept there, on top of the skive's; Solidify takes sf_ + (1 - sf_) * w)
                zf_ = np.clip(np.asarray(THIN_ZONE[name](pos), float), sf_, 1.0)
                ws_ = np.clip(((sf_ + (1 - sf_) * ws_) * zf_ - sf_) / (1 - sf_), 0, 1)
                print("THIN_ZONE %s: %d points at under %.0f%% of the sheet's thickness" % (name, int((zf_ < 0.99).sum()), zf_.min() * 100))
            gs_ = obj.vertex_groups.new(name="_skive")
            for i_ in range(len(pos)):
                gs_.add([i_], float(ws_[i_]), "REPLACE")
            so.vertex_group = "_skive"
            so.thickness_vertex_group = sf_
            print("EDGE SKIVE %s: %.1f mm at the cut, full %.1f mm from %.0f mm in; %d points pared"
                  % (name, thick * sf_ * 1000, thick * 1000, so_ * 1000, int((ws_ < 1).sum())))
    if bevel > 0:
        bv = obj.modifiers.new("edge", "BEVEL")
        bv.width = min(bevel, thick * 0.45)
        bv.segments = 2
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(50)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if "_thin" in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups["_thin"])
    if "_skive" in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups["_skive"])
    # After thickening and bevelling, any point left without a bone takes
    # the weights of the nearest point that has some.
    vs = obj.data.vertices
    tot = np.array([sum(g.weight for g in v.groups) for v in vs])
    fin = np.array([all(math.isfinite(c) for c in v.co) for v in vs])
    bare = np.where((tot < 0.01) & fin)[0]
    if len(bare):
        good = np.where((tot >= 0.01) & fin)[0]
        gco = np.array([vs[i].co[:] for i in good])
        _, jn = cKDTree(gco).query(np.array([vs[i].co[:] for i in bare]))
        for i, j in zip(bare, good[jn]):
            for g in vs[j].groups:
                obj.vertex_groups[g.group].add([int(i)], g.weight, "REPLACE")
        print("WEIGHTS given to", len(bare), "bare points of", name)
    # (r3: a wrap takes her final skin's weights again here, after the easing above: eased, its sides lost part of
    # her arms' share and her skin slid out past them as she ran, 22 mm)
    wk = [k for k in WRAP_SKINW if name.startswith(k)]
    if wk:
        Qs, Ws = WRAP_SKINW[wk[0]]
        co = np.array([v.co[:] for v in vs])
        dq, jq = cKDTree(Qs).query(co, k=4)
        iw = 1.0 / np.maximum(dq, 1e-4)
        ws = four_bones((Ws[jq] * iw[:, :, None]).sum(1) / iw.sum(1)[:, None])
        for vg in list(obj.vertex_groups):
            obj.vertex_groups.remove(vg)
        groups = {}
        for i in range(len(ws)):
            for j in np.nonzero(ws[i] > 0.003)[0]:
                if j not in groups:
                    groups[j] = obj.vertex_groups.new(name=BONES[j])
                groups[j].add([i], float(ws[i, j] / ws[i, ws[i] > 0.003].sum()), "REPLACE")
        print("WRAP weights: %s takes her skin's again (%d points)" % (name, len(ws)))
    me.set_sharp_from_angle(angle=math.radians(50))
    obj.parent = arm
    am = obj.modifiers.new("Armature", "ARMATURE")
    am.object = arm
    print("PIECE", name, len(me.polygons), "faces")
    return obj


# ------------------------------------------------------------- the cuts --
def bottom(style, top=0.075, side_rise=0.05, gusset=0.022):
    """Briefs: the front a panel from the crotch widening to the hips, the
    top edge low in front and rising over the hip bones; `style` shapes the
    seat: 'full', 'cheeky' (the lower cheeks bare) or 'thong'."""
    ax = np.abs(X)
    top_line = CROTCH + top + side_rise * np.clip(ax / 0.15, 0, 1) ** 2 + 0.035
    rise = np.maximum(Z - CROTCH, 0)
    front_w = gusset + rise * 1.9
    if style == "thong":
        back_w = 0.008 + ramp(Z, CROTCH + 0.1, top_line - 0.01) * 0.16 + rise * 0.05
    elif style == "cheeky":
        back_w = gusset + rise * 1.1
    else:
        back_w = gusset + rise * 2.2
    w = front_w * FRONT + back_w * (1 - FRONT)
    panel = AND(w - ax, top_line - Z, Z - (CROTCH - 0.02))
    band = AND(top_line - Z, Z - (top_line - 0.022), 0.25 - ax, 0.5 - LEGW["l"] - LEGW["r"])
    return OR(panel, band)


# Nothing but a cup on her breasts (a band or corset running up under one
# would stand off it as a shelf): positive off them, in metres-ish.
# Off her breasts and out from under them (where a breast hangs over her
# ribs, a band or corset would stand off it as a shelf), so torso pieces
# end flush on her ribs, short of the breast.
def _off_breast():
    wb = wsum("breast_l", "breast_r")
    bp = P[wb > 0.02]
    tree = cKDTree(bp[:, :2])
    under = np.zeros(len(P), bool)
    for i, nb in enumerate(tree.query_ball_point(P[:, :2], 0.015)):
        if nb:
            dz = bp[nb, 2] - P[i, 2]
            under[i] = ((dz > 0.002) & (dz < 0.009)).any()
    # In or out, eased over her surface into a smooth slope, so the line
    # where a piece ends is one even curve, not the triangles' steps.
    f = np.where(under | (wb > 0.003), -1.0, 1.0)
    for _ in range(60):
        f = 0.5 * f + 0.5 * (ADJ @ f)
    return np.where(f > 0.6, 1.0, f * 0.03)


OFF_BREAST = _off_breast()


def hero_briefs(top=0.125, cut=0.95):
    """Briefs as a superhero wears them over her suit: broad across the
    front and seat up to a waistband `top` above the crotch, the leg holes
    cut high, rising toward the hips at slope `cut`."""
    ax = np.abs(X)
    legs = (Z - CROTCH + 0.02) - cut * np.maximum(ax - 0.03, 0) * (0.75 + 0.25 * FRONT)
    return AND((CROTCH + top) - Z, Z - (CROTCH - 0.03), legs, 0.3 - ARMW["l"] - ARMW["r"])


def cups(cover=0.62, plunge=0.02, band=0.03, over=0.022, reach=0.088):
    """A half-cup under each breast and the band under them: the cup holds
    the breast from below, its top edge `over` above the nipple and dipping
    toward the middle, so the upper breast shows; `reach` is how far round
    the breast it comes; its inner edge leaves `plunge` of the cleavage
    bare. (`cover` is kept for callers; the nipple sets the line.)"""
    parts = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        nip = NIPPLE[sd]
        c = n + np.array([0, 0.035, -0.012])
        r = np.linalg.norm(P - c, axis=1)
        top = nip[2] + over - 0.45 * np.maximum(0, abs(nip[0]) - np.abs(X)) - 0.3 * np.maximum(0, np.abs(X) - abs(nip[0]) - 0.02)
        parts.append(AND(reach - r, top - Z, X * s - plunge, -(Y - 0.02)))
    ub = AND(Z - (UNDERBUST - band - 0.03), UNDERBUST + 0.006 - Z, 0.4 - ARMW["l"] - ARMW["r"], OFF_BREAST)
    return OR(*parts), ub


RIBBON_LINE = {}   # (each ribbon's centre line as laid on her)
RIBBON_FRAME = {}   # (STRAP_ROWS: the frames of the straps whose rows are evened after export)
STRAP_ROWS = os.environ.get("STRAP_ROWS", "warden.strap").split(",")


def ribbon(name, ctrl, width, mkey, lift=0.0035, thick=0.0025, cols=5, trim=None, snap=True, centre=None,
           hides=False, follow=False, flare=None, onto=None, taper=None, taut=0, closed=False, nape=None, skin=None):
    """A strap as a strap is made: a ribbon of even width laid along a
    smooth curve on her skin, so its edges are two clean parallel lines.
    It moves with the skin under each point of it. With `centre` (a point
    inside her), it is laid on her by looking out from there through each
    point of it: the skin nearest a point inside her can jump from one
    curve of her to another (from her breast to her chest), and kinked it.
    `hides`: her skin under it is tucked in, as under a fitted piece (a
    gusset or a thong's string, which she must never show through).
    `follow`: each line along it moves with the skin under that line, as
    stretched cloth does, rather than the whole width as one strap (a
    gusset: her thighs part the skin under its edges, and a strap's edges,
    staying put, let it out from under them). `flare` (width, length): the
    ribbon widens to that width over that length at its end, as a thong's
    string opens into its gusset. `onto`, a piece made before it: laid on
    that piece's outside as seen from ahead, `lift` off it, moving with it
    (a boning channel on a suit). `taper`, a length: over that much of its
    end it eases down into the piece it lies on and narrows, so it ends
    flush, not in a square tab (a boning channel ending on a panel).
    `closed`: its first and last control points are one, and it is eased
    across that join as along the rest (a cord round her neck). `nape`
    (height, y): with `taut`, its points behind y slide along her, eased
    straight and no higher than that height (NAPE_CORD). `skin`, a BVH: laid on that and not this scene's skin
    (final_skin_bvh: her skin as her body build leaves it, STRAP_FINAL)."""
    SKIN_BVH = skin if skin is not None else globals()["SKIN_BVH"]

    def sm3(a):
        # (one [1 2 1]/4 pass along it; round the join when closed)
        a = a.copy()
        if closed:
            r = a[:-1]
            r = (np.roll(r, 1, 0) + 2 * r + np.roll(r, -1, 0)) / 4
            return np.concatenate([r, r[:1]])
        a[1:-1] = (a[:-2] + 2 * a[1:-1] + a[2:]) / 4
        return a
    if onto is not None:
        s_pos, s_tris, s_wt, s_thick = SHEET[onto]
        s_bvh = BVHTree.FromPolygons([tuple(p) for p in s_pos], s_tris.tolist())
        s_nrm = vertex_normals(s_pos, s_tris)
        lift = lift + s_thick

    def lay(pts):
        if onto is not None:
            out_ = []
            for p in pts:
                hit = s_bvh.ray_cast(Vector((p[0], -0.6, p[2])), Vector((0, 1, 0)), 1.2)
                out_.append(np.array(hit[0][:]) if hit[0] is not None else np.asarray(p, float))
            return np.array(out_)
        if centre is None:
            return np.array([SKIN_BVH.find_nearest(Vector(p))[0][:] for p in pts])
        o = np.asarray(centre, float)
        out_ = []
        for p in pts:
            d = np.asarray(p) - o
            hit = SKIN_BVH.ray_cast(Vector(o), Vector(d / np.linalg.norm(d)), 1.0)
            out_.append(np.array(hit[0][:]) if hit[0] is not None else np.array(SKIN_BVH.find_nearest(Vector(p))[0][:]))
        return np.array(out_)
    # (columns fine enough that a trim along its edges is a clean line)
    cols = max(cols, int(np.ceil(max(width, flare[0] if flare else 0.0) / 0.0015)) + 1)
    # (a smooth curve through its points, not straight runs between them:
    # those met at corners, and a strap kinked at each)
    c = spline(ctrl, step=0.003)
    if snap:
        c = lay(c)
    # (not snapped, it is taut, as given: it bridges a hollow rather than
    # sinking into it)
    for _ in range(3):
        c = sm3(c)
        if snap:
            c = lay(c)
    if taut and snap and onto is None:
        # (taut, the Reaver's cord (touch-up 2, 18 Oct; the owner's C01 frames): laid on her skin it sank into the
        # hollow between her collarbones and her neck and hooked at its edges. A cord over a hollow is held up by
        # its own pull: each point is only ever lifted off her along her skin's normal, by as much as its
        # neighbours' pull would carry it, never moved along her (so the fangs stay on it) and never pushed in.
        # `taut` is the most it may stand off her, in metres)
        for _ in range(TAUT_ITERS):
            sm = sm3(c)
            hit = [SKIN_BVH.find_nearest(Vector(p)) for p in c]
            q = np.array([h[0][:] for h in hit])
            n = np.array([h[1][:] for h in hit])
            up = np.maximum(((sm - c) * n).sum(1), 0.0)
            c = c + n * up[:, None]
            h_ = ((c - q) * n).sum(1)
            c = c - n * (np.maximum(h_, 0.0) - np.clip(h_, 0.0, taut))[:, None] - n * np.minimum(h_, 0.0)[:, None]
        if nape is not None and closed:
            # (NAPE_CORD, see the knob: the back slides, Taubin-eased (a pass in, a pass out: wobbles go, the loop
            # does not shrink up her neck), held under the height, then back onto her within `taut`)
            zcap, y0, ay = nape
            r = c[:-1].copy()
            r0_ = r.copy()
            w_ = ramp(r[:, 1], y0, y0 + 0.03)
            # (its back laid afresh: laid by rays from inside the base of her neck, it doubled back on itself behind
            # her shoulders (an 8 cm jump). So: its front, from the fangs out to where it turns behind her, kept;
            # behind, an arc round her neck, each point cast level out from her neck's axis, rising from where
            # the front ends to the height behind)
            fr = np.nonzero(w_ < 0.3)[0]
            fr = fr[fr.argsort()]
            assert (np.diff(fr) == 1).all(), "nape: the cord's front is not one run"
            pa, pb = r[fr[0]], r[fr[-1]]
            fa = np.arctan2(pa[0], pa[1] - ay)
            fb = np.arctan2(pb[0], pb[1] - ay)
            if fa < fb:
                fa += 2 * np.pi
            n_ = max(8, int((fa - fb) * 0.065 / 0.003))
            u_ = np.linspace(0, 1, n_ + 2)[1:-1]
            ph = fb + (fa - fb) * u_
            fa_, fb_ = fa - 2 * np.pi * (fa > np.pi), fb

            def prof(f_):
                # (its height round her: zcap behind, NAPE_SIDE higher at her sides, down to the front's ends)
                f_ = (f_ + np.pi) % (2 * np.pi) - np.pi
                z_ = zcap + NAPE_SIDE * np.sin(np.minimum(np.abs(f_), np.pi / 2)) ** 2
                ze = np.where(f_ > 0, pa[2], pb[2])
                fe = np.where(f_ > 0, abs(fa_), abs(fb_))
                return z_ + (ze - zcap - NAPE_SIDE) * ramp(np.abs(f_), np.pi / 2, fe)
            zz = prof(ph)
            arc = []
            for f_, z_ in zip(ph, zz):
                d_ = Vector((np.sin(f_), np.cos(f_), 0.0))
                hit_ = SKIN_BVH.ray_cast(Vector((0.0, ay, z_)), d_, 0.3)
                arc.append(np.array(hit_[0][:]) if hit_[0] is not None else np.array(SKIN_BVH.find_nearest(Vector((0.08 * d_[0], ay + 0.08 * d_[1], z_)))[0][:]))
            r = np.concatenate([r[fr], np.array(arc)])
            w_ = np.concatenate([w_[fr], np.ones(len(arc))])[:, None]
            for _ in range(NAPE_ITERS):
                for f_ in (0.5, -0.53):
                    # (across the cord only, never along it: points eased along it bunched and spread, 1 to 27 mm)
                    t_ = np.roll(r, -1, 0) - np.roll(r, 1, 0)
                    t_ /= np.linalg.norm(t_, axis=1)[:, None] + 1e-12
                    L_ = (np.roll(r, 1, 0) + np.roll(r, -1, 0)) / 2 - r
                    r = r + f_ * w_ * (L_ - (L_ * t_).sum(1)[:, None] * t_)
                r[:, 2] -= w_[:, 0] * np.maximum(r[:, 2] - prof(np.arctan2(r[:, 0], r[:, 1] - ay)) - 0.001, 0.0)
                hit = [SKIN_BVH.find_nearest(Vector(p)) for p in r]
                q = np.array([h[0][:] for h in hit])
                n = np.array([h[1][:] for h in hit])
                h_ = ((r - q) * n).sum(1)
                # (out of her at once; in toward her only softly: pulled straight in, points over the crease
                # where her neck meets her shoulders all went to the same point of it)
                r = r - n * (np.minimum(h_, 0.0) + 0.2 * np.maximum(h_ - taut, 0.0))[:, None]
                # (and the arc behind her kept evenly spaced along itself, its ends on the front's)
                nf_ = len(fr)
                pl = np.concatenate([r[nf_ - 1:], r[:1]])
                sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pl, axis=0), axis=1))]
                tq = np.linspace(0, sl[-1], len(pl))[1:-1]
                r[nf_:] = np.stack([np.interp(tq, sl, pl[:, k]) for k in range(3)], 1)
            c = np.concatenate([r, r[:1]])
            if os.environ.get("CORD_DUMP"):
                np.savez(os.environ["CORD_DUMP"], before=r0_, after=r, w=w_[:, 0])
            tg_ = np.diff(np.concatenate([r, r[:2]]), axis=0)
            tg_ /= np.linalg.norm(tg_, axis=1)[:, None] + 1e-12
            ang = np.degrees(np.arccos(np.clip((tg_[1:] * tg_[:-1]).sum(1), -1, 1)))
            ln_ = np.linalg.norm(np.diff(np.concatenate([r, r[:2]]), axis=0)[1:], axis=1)
            bk_ = np.roll(w_[:, 0], -1) > 0.5
            print("NAPE %s: back at %.1f..%.1f mm below the cap, its sharpest bend %.0f deg/cm (front %.0f), its steps %.1f..%.1f mm"
                  % (name, (zcap - np.roll(r[:, 2], -1)[bk_].max()) * 1000, (zcap - np.roll(r[:, 2], -1)[bk_].min()) * 1000,
                     (ang / (ln_ * 100))[bk_].max(), (ang / (ln_ * 100))[~bk_].max(), ln_.min() * 1000, ln_.max() * 1000))
        hit = [SKIN_BVH.find_nearest(Vector(p)) for p in c]
        h_ = (((c - np.array([h[0][:] for h in hit])) * np.array([h[1][:] for h in hit])).sum(1))
        print("TAUT %s: stands off her up to %.1f mm (mean %.1f) over %d points" % (name, h_.max() * 1000, h_.mean() * 1000, len(c)))
    if onto is not None and BONING_CLIP > 0:
        # (s18, BONING_CLIP: no further than its piece goes, see the knob)
        hit_ = np.array([s_bvh.ray_cast(Vector((p[0], -0.6, p[2])), Vector((0, 1, 0)), 1.2)[0] is not None for p in c])
        e_ = np.sort(np.vstack([s_tris[:, [0, 1]], s_tris[:, [1, 2]], s_tris[:, [2, 0]]]), 1)
        uk_, cn_ = np.unique(e_, axis=0, return_counts=True)
        be_ = uk_[cn_ == 1]
        smp_ = np.concatenate([s_pos[be_[:, 0]] * (1 - t_) + s_pos[be_[:, 1]] * t_ for t_ in np.linspace(0, 1, 6)])
        bad_ = np.nonzero(~(hit_ & (cKDTree(smp_).query(c)[0] > BONING_CLIP)))[0]
        bad_ = bad_[bad_ > len(c) // 2]
        if len(bad_):
            print("BONING %s: ends %.0f mm inside %s's edge, %d of %d points past it dropped" % (name, BONING_CLIP * 1000, onto, len(c) - bad_[0], len(c)))
            c = c[:bad_[0]]
    RIBBON_LINE[name] = c.copy()   # (its laid centre line, for pieces kept clear of it: PAUL_SEAT)
    if onto is not None:
        # (its normal the sheet's own, outward as it was lifted)
        nrm = s_nrm[cKDTree(s_pos).query(c)[1]]
    else:
        nrm = np.array([SKIN_BVH.find_nearest(Vector(p))[1][:] for p in c])
    for _ in range(4):
        nrm = sm3(nrm)
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    tg = np.gradient(c, axis=0)
    if closed:
        tg[0] = tg[-1] = c[1] - c[-2]
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    bn = np.cross(nrm, tg)
    bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
    off = np.linspace(-0.5, 0.5, cols)
    wrow = np.full(len(c), width)
    if flare:
        run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        wrow = width + (flare[0] - width) * ramp(run, run[-1] - flare[1], run[-1])
    lrow = np.full(len(c), lift)
    if taper:
        # (BONING_TAPER: down to the sheet's own surface, the last fifth
        # under it, even where the sheet is skived thin; narrowed by half)
        run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        k_ = ramp(run, run[-1] - taper, run[-1])
        lrow = lift - (lift - (s_thick - thick - 0.0002 if onto is not None else 0.0)) * ramp(run, run[-1] - taper, run[-1] - 0.2 * taper)
        lrow = lrow - np.maximum(lrow, 0) * ramp(run, run[-1] - 0.2 * taper, run[-1])
        wrow = wrow * (1 - 0.5 * k_)
    pos = (c[:, None, :] + nrm[:, None, :] * lrow[:, None, None] + bn[:, None, :] * (off[None, :] * wrow[:, None])[:, :, None]).reshape(-1, 3)
    tris = grid(len(c), cols)
    nor = vertex_normals(pos, tris)
    if (nor * np.repeat(nrm, cols, 0)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    # (one set of weights across its width, eased along it: it moves as a
    # strap; or, following, each line along it its own)
    if onto is not None:
        # (the sheet's own weights under each point: it moves as the sheet does)
        dq, jq = cKDTree(s_pos).query(pos, k=4)
        wq = 1.0 / np.maximum(dq, 1e-5)
        wt = ((s_wt[jq] * wq[:, :, None]).sum(1) / wq.sum(1)[:, None]).reshape(len(c), cols, -1)
    else:
        wt = soft_weights(pos).reshape(len(c), cols, -1)
    if not follow:
        wt[:] = wt.mean(1, keepdims=True)
    for _ in range(6):
        wt = sm3(wt)
    edge = (wrow[:, None] / 2 - np.abs(off[None, :] * wrow[:, None])).ravel()
    at = np.hstack([nor, wt.reshape(len(pos), -1), edge[:, None]])
    if os.environ.get("RIB_DUMP"):
        # (RIB_DUMP, a folder: each ribbon's laid line, frame and sheet, for measuring its edges)
        np.savez(os.path.join(os.environ["RIB_DUMP"], name + ".npz"), c=c, nrm=nrm, tg=tg, bn=bn, pos=pos.reshape(len(c), cols, 3),
                 wrow=wrow, lrow=lrow)
    if not follow and onto is None and any(name.startswith(k_) for k_ in STRAP_ROWS if k_):
        # (STRAP_ROWS: its frame, so its rows are evened again after the export's weight passes; tools/assets/strap_rows.py)
        import strap_rows
        RIBBON_FRAME[name] = strap_rows.frame(c, bn, nrm, wrow.max() / 2 + 0.0006, lrow.min() - 0.001,
                                              lrow.max() + thick + (trim[2] + trim[3] if trim else 0.0) + 0.0025)
    if trim and any(name.startswith(k_) for k_ in RIB_TRIM if k_):
        # (RIB_TRIM, 21 Oct, armor 8 r4: its gold laid as the strap is, from its own line: each edge's band offset from
        # the laid centre line across it and lifted along its eased normal. Cut from the sheet, lifted by that thin
        # band's own normals and its two edges eased along themselves (relax), over the crest of her shoulder its
        # edges drew in toward the bend's centre, 1.5-2.5 mm down into the leather and 0.5-1 mm across, unevenly:
        # the gold piping wavered like a hand-drawn line at the creation Look and broke up on the skyline)
        made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, None, budget=10 ** 7)
        tkey, tw_, th_, tt_ = trim
        kc = max(3, int(np.ceil(tw_ / 0.0015)) + 1)
        fr_ = np.linspace(0.0, 1.0, kc)
        tps, trs, tws = [], [], []
        for sg_ in (-1.0, 1.0):
            uu = sg_ * (wrow[:, None] / 2 - tw_ * (1 - fr_)[None, :])
            p_ = c[:, None, :] + nrm[:, None, :] * (lrow + thick + th_)[:, None, None] + bn[:, None, :] * uu[:, :, None]
            ci = np.clip(np.rint((uu / wrow[:, None] + 0.5) * (cols - 1)).astype(int), 0, cols - 1)
            tws.append(np.take_along_axis(wt, ci[:, :, None], 1).reshape(len(c) * kc, -1))
            g_ = grid(len(c), kc)
            if sg_ > 0:
                g_ = g_[:, ::-1]
            trs.append(g_ + sum(len(t_) for t_ in tps))
            tps.append(p_.reshape(-1, 3))
        tp_, tr_ = np.vstack(tps), np.vstack(trs)
        if (vertex_normals(tp_, tr_) * np.repeat(nrm, kc, 0)[np.r_[np.arange(len(c) * kc), np.arange(len(c) * kc)]]).sum(1).mean() < 0:
            tr_ = tr_[:, ::-1]
        if os.environ.get("RIB_DUMP"):
            np.savez(os.path.join(os.environ["RIB_DUMP"], name + "_trim.npz"), tp=tp_, tr=tr_, edge=np.zeros(len(tp_)))
        made.append(finish(name + "_trim", tp_, np.vstack(tws), tr_, tkey, tt_, 0.0008))
    else:
        made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = hides and o is made[0]
    if kind(mkey) == "leather" and width >= 0.012:
        inset = 0.0028
        for k, sgn in enumerate((1, -1)):
            ln = c + nrm * (lrow[:, None] + thick + 0.0001) + bn[:] * (sgn * (wrow[:, None] / 2 - inset))
            made += stitches(f"{name}_stitch{k}", ln, nrm, tg, pos, at[:, 3:3 + NB])
        made[0]["geo_stitch"] = True
    return made


def shoulder_strap_curves():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        out.append([n + np.array([0.012 * s, 0, 0.065]), np.array([0.105 * s, -0.04, 1.52]), np.array([0.11 * s, 0.03, 1.565]),
                    np.array([0.1 * s, 0.11, 1.47]), np.array([0.085 * s, 0.12, UNDERBUST - 0.02])])
    return out


def shoulder_straps(width=0.016):
    f = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        pts = [n + np.array([0.012 * s, 0, 0.065]), np.array([0.105 * s, -0.04, 1.52]), np.array([0.11 * s, 0.03, 1.565]),
               np.array([0.1 * s, 0.11, 1.47]), np.array([0.085 * s, 0.12, UNDERBUST - 0.02])]
        f.append(strap(pts, width))
    return OR(*f)


def limb(sd, s0, s1, legs=True, front_dip=0.0):
    """A sleeve of a limb from s0 to s1 along it (metres from the hip or the
    collarbone); its top edge dips at the back by front_dip."""
    S = LEG_S[sd] if legs else ARM_S[sd]
    Wm = LEGW[sd] if legs else ARMW[sd]
    top = s0 - front_dip * (1 - FRONT)
    return AND(S - top, s1 - S, Wm - 0.5)


def cap(center, radius):
    c = skin_point(center)
    return radius - np.linalg.norm(P - c, axis=1)


def shoulder(sd):
    return head(f"upperarm_{sd}") + np.array([0.02 * (1 if sd == "l" else -1), 0, 0.06])


# Where the last cups made hold their straps (their peaks, outside) and meet
# (their inner rims' lowest point), for the pieces fixed to them.
CUP_PEAK = {}
CUP_LOW = None


def plate_cups(name, mkey, top, lift=0.003, thick=0.003, trim=None, studs=None, gap=0.011, side=0.07, only=None):
    """A pair of plate cups, each a smooth form rather than a cast of her:
    her breasts' form (breast_form: both, her left mirrored onto her right,
    so the pair is one shape and holds either; a few millimetres off her at
    most), `lift` more. Nothing of her skin's own lumps reaches it; her
    nipples, filled under it, are hidden where they would show through it.
    Below and at
    the side it ends where it meets her (it goes into her chest there, as a
    breast does), a clean seam; above, it is cut to the line `top(|x|)` (a
    height for each distance from her middle: a plunge falls toward her
    middle); inside, `gap` from her middle; outside, `side` past her nipple.
    Made on her right and mirrored onto her left (with `only`, that side
    alone), its weights from her skin nearest it (it moves, and swings, with
    her)."""
    sd, s_ = "r", -1
    nip = NIPPLE[sd]
    mirror = np.array([-1.0, 1.0, 1.0])
    c, R, ax, form = BREAST_FORM
    # The form as an even mesh of triangles (a geodesic sphere, ~2 mm apart
    # over it): no poles. (A grid by angles has one at the front of each
    # breast, where its lines crowd together, were welded into a flat disc,
    # and showed as a dent at the nipple.) Then `lift` off it.
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=6, radius=1.0)
    unit = np.array([v.co[:] for v in ico.verts])
    tris = np.array([[v.index for v in f.verts] for f in ico.faces])
    ico.free()
    unit /= np.linalg.norm(unit, axis=1)[:, None]
    pos = c + (unit * ax * form(unit)[:, None]) @ R
    nor = vertex_normals(pos, tris)
    if (nor * (pos - c)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    pos = pos + nor * lift
    # Where it meets her, as a drawn line: round the axis through her
    # nipple, at each bearing, how far out from it the plate still stands
    # clear of her (of her skin with the nipples filled; which side of her
    # it is, by the plate's own normal: her filled nipple's folded
    # triangles face every way, and cut a ring round it), never past the
    # first place it goes into her, and eased round. (Cut where it met her
    # skin, a snug plate met it so shallowly that the edge wandered.)
    global FILLED_BVH
    if FILLED_BVH is None:
        FILLED_BVH = BVHTree.FromPolygons([tuple(p) for p in P_FILLED], TRI.tolist())
    out_of = np.zeros(len(pos))
    for i, q in enumerate(pos):
        v_ = np.array(q) - np.array(FILLED_BVH.find_nearest(Vector(q))[0][:])
        out_of[i] = np.linalg.norm(v_) * np.sign(v_ @ nor[i])
    un = ((nip - c) @ R.T) / ax
    un /= np.linalg.norm(un)
    e1 = np.cross(un, [0.0, 0.0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(un, e1)
    theta = np.arccos(np.clip(unit @ un, -1, 1))
    bins = 120
    phi_f = (np.arctan2(unit @ e2, unit @ e1) + np.pi) / (2 * np.pi) * bins
    phi = phi_f.astype(int) % bins
    reach = np.full(bins, np.pi)
    inside = (out_of < lift * 0.5) & (theta > 0.25)
    np.minimum.at(reach, phi[inside], theta[inside])
    from scipy.ndimage import gaussian_filter1d, minimum_filter1d
    reach = gaussian_filter1d(minimum_filter1d(reach, 9, mode="wrap"), 4, mode="wrap") - 0.01
    reach_at = np.interp(phi_f - 0.5, np.arange(-1, bins + 1), np.r_[reach[-1], reach, reach[0]])
    axs = np.abs(pos[:, 0])
    f = np.minimum.reduce([top(axs) - pos[:, 2], axs - gap, abs(nip[0]) + side - axs, (reach_at - theta) * 0.08,
                           # (her right side only: the left is its mirror)
                           -pos[:, 0] - 0.001])
    _, j = cKDTree(P).query(pos)
    attr = np.hstack([nor, W[j].astype(float), np.zeros((len(pos), 1))])
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    tris = islands(pos, tris, keep_frac=0.2)
    loops = edge_loops(tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops])) if loops else np.arange(0)
    at[:, -1] = cKDTree(pos[rim]).query(pos)[0] if len(rim) else 0.05
    # Its peak at the outside, where a strap holds it (for the outfit's straps).
    outer = rim[np.abs(pos[rim, 0]) > abs(nip[0]) * 0.85]
    CUP_PEAK["r"] = pos[outer[np.argmax(pos[outer, 2])]]
    CUP_PEAK["l"] = CUP_PEAK["r"] * mirror
    inner = rim[np.abs(pos[rim, 0]) < gap + 0.006]
    global CUP_LOW
    CUP_LOW = pos[inner[np.argmin(pos[inner, 2])]] if len(inner) else np.array([0.0, nip[1], UNDERBUST])
    # A lining under its top edge, from her middle to past her nipple: dark
    # leather from just under the plate's edge down toward her, CUP_LINE[0]
    # short of her skin (at most CUP_LINE[1] of the way, eased in over
    # CUP_LINE[2] at each end). The plate stands off her by up to a
    # centimetre under the plunge, and bent over (chain_haul, the motion
    # check's left view, s16_sab2) a look in under that edge met the inner
    # rim of her right areola (-0.17 cm). Closed from the inside, the plate's
    # own form and edge are as judged. (Tucking her deeper there only let the
    # look go deeper: offline, 1.6 cm became 0.7.)
    line_ = [float(v) for v in os.environ.get("CUP_LINE", "0.0025,0.85,0.01,0.0015").split(",")]
    lining = None
    if line_[0] > 0 and loops:
        ax_ = np.abs(pos[:, 0])
        on_top = (np.abs(top(ax_) - pos[:, 2]) < 0.0015) & (ax_ < abs(nip[0]) + 0.025)
        tree_ = cKDTree(pos)
        LP, LW, LT = [], [], []
        for lp in loops:
            lp = np.array(lp)
            if not on_top[lp].any():
                continue
            if not on_top[lp].all():
                lp = np.roll(lp, -int(np.argmin(on_top[lp])))
            runs, cur = [], []
            for v_ in lp:
                if on_top[v_]:
                    cur.append(v_)
                elif cur:
                    runs.append(cur)
                    cur = []
            if cur:
                runs.append(cur)
            for run in runs:
                run = np.array(run)
                if len(run) < 4:
                    continue
                q = pos[run]
                arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
                tp_ = np.clip(np.minimum(arc, arc[-1] - arc) / line_[2], 0, 1)
                tp_ = tp_ * tp_ * (3 - 2 * tp_)
                n_ = at[run, :3] / np.linalg.norm(at[run, :3], axis=1)[:, None]
                tg = np.gradient(q, axis=0)
                tg /= np.maximum(np.linalg.norm(tg, axis=1), 1e-9)[:, None]
                inn = np.cross(n_, tg)
                inn /= np.maximum(np.linalg.norm(inn, axis=1), 1e-9)[:, None]
                m_ = len(run) // 2
                if at[tree_.query(q[m_] + inn[m_] * 0.004)[1], -1] < at[tree_.query(q[m_] - inn[m_] * 0.004)[1], -1]:
                    inn = -inn
                a_ = q + inn * line_[3] - n_ * 0.0003
                sk_ = np.array([SKIN_BVH.find_nearest(Vector(v))[0][:] for v in a_])
                L_ = np.linalg.norm(sk_ - a_, axis=1)
                f_ = np.clip((L_ - line_[0]) / np.maximum(L_, 1e-6), 0, line_[1]) * tp_
                b_ = a_ + (sk_ - a_) * f_[:, None]
                o_ = sum(len(x) for x in LP)
                k_ = len(run)
                LP.append(np.vstack([a_, b_]))
                LW.append(np.vstack([at[run, 3:3 + NB]] * 2))
                LT += [[o_ + i, o_ + i + 1, o_ + k_ + i + 1] for i in range(k_ - 1)] + [[o_ + i, o_ + k_ + i + 1, o_ + k_ + i] for i in range(k_ - 1)]
                print("CUP LINING %s: %d points along its top edge, %.0f mm long; the plate %.1f-%.1f mm off her there, the lining %.1f mm deep at most"
                      % (name, k_, arc[-1] * 1000, L_.min() * 1000, L_.max() * 1000, (L_ * f_).max() * 1000))
        if LP:
            lining = (np.vstack(LP), np.vstack(LW), np.array(LT))
    pos2 = np.vstack([pos, pos * mirror])
    at2 = np.vstack([at, np.hstack([at[:, :3] * mirror, at[:, 3:3 + NB][:, SWAP], at[:, -1:]])])
    tris2 = np.vstack([tris, tris[:, ::-1] + len(pos)])
    if only == "r":
        pos2, at2, tris2 = pos, at, tris
    elif only == "l":
        pos2, at2, tris2 = pos2[len(pos):], at2[len(pos):], tris[:, ::-1]
    beads = []
    if trim:
        tkey, w, h, tt = trim
        pos2, beads = bind_edges(name, pos2, at2, tris2, tkey, max(w, 0.005), max(h, 0.0006), 0.0018, thick)
    made = [finish(name, pos2, at2[:, 3:3 + NB], tris2, mkey, thick, 0.0006, 10 ** 7)] + beads
    if studs:
        made += rivets(name, pos2, at2, tris2, thick, studs)
    if lining is not None:
        lp2, lw2, lt2 = lining
        if only != "r":
            lp2, lw2, lt2 = np.vstack([lp2, lp2 * mirror]), np.vstack([lw2, lw2[:, SWAP]]), np.vstack([lt2, lt2[:, ::-1] + len(lp2)])
            if only == "l":
                lp2, lw2, lt2 = lp2[len(lining[0]):], lw2[len(lining[0]):], lining[2][:, ::-1]
        made.append(finish(name + "_lining", lp2, lw2, lt2, "darkleather", 0.0012, 0.0004, 10 ** 6))
    for o_ in made:
        o_["hides"] = o_ is made[0]
    print("PLATE CUP %s: %d points" % (name, len(pos2)))
    return made


def trimmed(name, pos, at, tris, mkey, thick, bevel, trim, budget=3000):
    """A sheet and, if asked, the gold along its edge (the field in `at`'s
    last column is the distance in from the edge)."""
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget)]
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr, edge=30)
            if os.environ.get("RIB_DUMP"):
                np.savez(os.path.join(os.environ["RIB_DUMP"], name + "_trim.npz"), tp=tp, tr=tr, sp=pos, st=tris, edge=at[:, -1])
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel))
    return made


def grid(nu, nv):
    i = np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :]
    i = i.ravel()
    return np.vstack([np.c_[i, i + nv, i + 1], np.c_[i + 1, i + nv, i + nv + 1]])


# (FRINGE_RIGID: a hanging piece cut into tongues weights each tongue as one; see hanging())
FRINGE_RIGID = os.environ.get("FRINGE_RIGID", "1") == "1"
# (REAVER_PANEL / REAVER_BOOT: the reaver's front panel and boots as Body 17 remade them; "old": as before)
REAVER_PANEL = os.environ.get("REAVER_PANEL", "new")
# (Body 18, judge: "side-on it reads as a cord": the taper eased, the hem ~20% wider)
# (its tongues fanned a little more: hem 98 -> ~120 mm, its top as it was; Body 17's PANEL_TAPER=0.03 PANEL_SPLAY=0.05)
PANEL_TAPER = float(os.environ.get("PANEL_TAPER", "0.0"))
# (Body 18 r2, judge: "side-on still a thin straight strap ... fix the shape, not the width": PANEL_WRAP its sides swept
# back (m, see hanging()), a burnished edge PANEL_EDGE_W wide in PANEL_EDGE (round 1: darkleather 0.01), the tongues
# fanned 10-15 deg (splay 0.08 -> 0.12: the outer ~13)
PANEL_SPLAY = float(os.environ.get("PANEL_SPLAY", "0.12"))
PANEL_WRAP = float(os.environ.get("PANEL_WRAP", "0.021"))
PANEL_EDGE = os.environ.get("PANEL_EDGE", "burnished")
PANEL_EDGE_W = float(os.environ.get("PANEL_EDGE_W", "0.005"))
REAVER_BOOT = os.environ.get("REAVER_BOOT", "hide")
# (FRINGE_ONE: a front panel given `one_piece` moves as one piece below its top; see hanging())
FRINGE_ONE = os.environ.get("FRINGE_ONE", "1") == "1"


def fringe(hem, strips, depth, notch=0.18):
    """A hem cut into `strips` strips: between each, a V-notch `depth` deep
    and `notch` of a strip wide, so the leather hangs in tongues."""
    def f(u):
        ph = ((u + 1) / 2 * strips) % 1.0
        v = max(0.0, 1 - abs(ph - 1.0 if ph > 0.5 else ph) / (notch / 2))
        return hem(u) + depth * v
    return f


def hanging(name, a0, a1, z_top, hem, mkey, flare=0.15, lift=0.01, gap=0.012, thick=0.0025, trim=None, nu=56, snug=None,
            strips=None, one_piece=None, taper=0.0, crease=None, splay=0.0, notch_depth=0.0, wrap=0.0):
    """Cloth hanging from her hips, all round her between the angles a0 and
    a1 (radians; 0 her front, rising toward her left): at each angle it
    falls from the hips, flaring out by `flare` a metre of fall, and never
    nearer her than `gap` (so it goes over her thighs, not into them). Its
    hem is `hem(u)`, u from -1 at a0 to 1 at a1. It is weighted to the
    pelvis at the top and more and more to the thigh on its side below the
    hip, so it swings with her stride.
    `z_top` may be a function of the angle (a plate hung from under a belt
    follows the belt's line). With `snug` it is tucked: only `snug` off her at
    its top, easing to `gap` over its first 5 cm, and its top edge (hidden
    under what it hangs from) is not trimmed.
    (Body 17, the reaver's panel) `taper`: its sides cut in by that much (m) a metre of fall, so it narrows to
    its hem; `crease` (angle, width rad, depth m): one soft fold down it from 6 cm below its top, a valley
    with a low ridge beside it; `splay` (rad): a fringe's tongues fan out from their notches' roots (`strips`
    and `notch_depth` the fringe's), the outer ones most, each lifted or laid a little in turn."""
    a = np.linspace(a0, a1, nu)
    top = np.asarray(z_top(a), float) if callable(z_top) else np.full(nu, float(z_top))
    zmax = float(top.max())
    ring = (np.abs(Z - zmax) < 0.008) & (ARMW["l"] + ARMW["r"] < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    zs = np.arange(zmax, min(hem(u) for u in np.linspace(-1, 1, 41)) - 0.03, -0.006)
    body = (ARMW["l"] + ARMW["r"] < 0.3) & (wsum("Head") < 0.3)
    ang = np.arctan2(X, -(Y - cy))
    rad = np.hypot(X, Y - cy)
    R = np.full((len(zs), nu), np.nan)
    for k, z in enumerate(zs):
        m = body & (np.abs(Z - z) < 0.006)
        if not m.any():
            continue
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi)
            w = d < 0.12
            if w.any():
                R[k, j] = rad[m][w].max()
    R[0] = np.where(np.isnan(R[0]), np.nanmax(R[0]), R[0])
    # (her radius at each angle's own top, from the levels measured there)
    R_top = np.array([np.interp(top[j], zs[::-1], np.where(np.isnan(R[::-1, j]), R[0, j], R[::-1, j])) for j in range(nu)])
    for k in range(1, len(zs)):
        R[k] = np.where(np.isnan(R[k]), 0, R[k])
    fall = np.maximum(top[None, :] - zs[:, None], 0)
    clear = gap if snug is None else snug + (gap - snug) * ramp(fall, 0.0, 0.05)
    hang = (R_top + lift)[None, :] + flare * fall
    r = np.maximum(hang, R + clear)
    r = np.maximum.accumulate(r, axis=0)
    for _ in range(6):
        r[1:-1] = (r[:-2] + 2 * r[1:-1] + r[2:]) / 4
        r[:, 1:-1] = (r[:, :-2] + 2 * r[:, 1:-1] + r[:, 2:]) / 4
        r = np.maximum(r, R + clear)
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], len(zs), 0)
    fall_ = np.maximum(top[None, :] - zz, 0)
    if crease is not None:
        ca, cw, cd = crease
        g_ = lambda x: np.exp(-(x / cw) ** 2)
        r = r - cd * ramp(fall_, 0.06, 0.16) * (g_(aa - ca) - 0.35 * g_(aa - ca - 1.6 * cw))
    if wrap:
        # (Body 18, the reaver's panel side-on "a thin straight strap": its cross-section curved round her thighs, the
        # sides swept back by up to `wrap` (m, at its edges, quadratic across it) from 2 cm below its top to 22 cm,
        # never nearer her than its clearance)
        un_ = (aa - (a0 + a1) / 2) / ((a1 - a0) / 2)
        r = np.maximum(r - wrap * un_ ** 2 * ramp(fall_, 0.02, 0.22), R + clear)
    a_pos = aa
    if splay and strips:
        u0_ = (aa - a0) / (a1 - a0) * 2 - 1
        k0_ = np.clip(np.floor((u0_ + 1) / 2 * strips), 0, strips - 1)
        uc_ = (k0_ + 0.5) / strips * 2 - 1
        root_ = np.vectorize(hem)(uc_) + notch_depth
        t_ = ramp(root_ - zz, 0.0, max(notch_depth, 1e-3) * 1.5)
        a_pos = aa + splay * uc_ * t_
        r = r + 0.004 * np.where(k0_ % 2 == 0, 1.0, -0.4) * t_
    pos = np.stack([r * np.sin(a_pos), cy - r * np.cos(a_pos), zz], -1).reshape(-1, 3)
    tris = grid(len(zs), nu)
    nor = vertex_normals(pos, tris)
    out = np.c_[np.sin(aa).ravel(), -np.cos(aa).ravel()]
    if ((nor[:, :2] * out).sum(1)).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    u = (aa.ravel() - a0) / (a1 - a0) * 2 - 1
    zb = np.array([hem(x) for x in u])
    arc = np.minimum(aa.ravel() - a0, a1 - aa.ravel()) * r.ravel()
    top_at = np.repeat(top[None, :], len(zs), 0).ravel()
    if taper:
        arc = arc - taper * np.maximum(top_at - pos[:, 2], 0)
    f = np.minimum.reduce([pos[:, 2] - zb, top_at - pos[:, 2] + 0.002, arc])
    # (a tucked top is hidden: its trim would only stand into what hides it)
    f_trim = np.minimum(pos[:, 2] - zb, arc) if snug is not None else f
    hip = head("thigh_l")[2]
    leg = 0.85 * ramp(hip - pos[:, 2], 0.0, 0.45)
    side = 1 / (1 + np.exp(-pos[:, 0] / 0.035))
    wt = np.zeros((len(pos), NB))
    wt[:, BI["pelvis"]] = 1 - leg
    wt[:, BI["thigh_l"]] = leg * side
    wt[:, BI["thigh_r"]] = leg * (1 - side)
    # Where it lies close over her (her seat, her hips) it moves exactly as
    # her skin there does, springs and all, so she cannot slide through it.
    d, j = cKDTree(P[body]).query(pos)
    near = 1 - ramp(d, gap + 0.004, 0.06)
    wt = wt * (1 - near[:, None]) + soft_weights(pos, np.where(body)[0], sigma=0.02) * near[:, None]
    # A hem cut into `strips` tongues (fringe()): each tongue moves as one,
    # from 3 cm above its notches' roots, all of it 3 cm below them (each row
    # of it its row's mean): weighted column by column, a tongue near her
    # middle took one thigh at one edge and the other at its other, and with
    # her thighs spread (sit_log) its tip stretched across her thigh in a
    # sawtooth shard (judge r2). Between tongues the notches part instead.
    if strips and FRINGE_RIGID:
        u_ = (aa.ravel() - a0) / (a1 - a0) * 2 - 1
        ks = np.clip(np.floor((u_ + 1) / 2 * strips), 0, strips - 1).astype(int)
        zr = np.array([max(hem(x) for x in np.linspace(2 * k / strips - 1, 2 * (k + 1) / strips - 1, 9)) for k in range(strips)])
        rows = np.repeat(np.arange(len(zs)), nu)
        grp = rows * strips + ks
        cnt = np.bincount(grp, minlength=len(zs) * strips)[:, None]
        mean = np.stack([np.bincount(grp, wt[:, b], minlength=len(zs) * strips) for b in range(wt.shape[1])], 1) / np.maximum(cnt, 1)
        t_ = ramp(zr[ks] + 0.03 - pos[:, 2], 0.0, 0.06)[:, None]
        wt = wt * (1 - t_) + mean[grp] * t_
    # A narrow front panel (`one_piece`, its thigh share at the hem) moves as
    # one piece below its top: pelvis, and both thighs alike, more and more
    # from 5 cm below the hip joint to 25 cm. Each side after its own thigh,
    # with her thighs raised and spread (sit_log) the panel spread with them,
    # stretched and streaked across her thigh (judge r2); and in a stride it
    # tore between a thigh forward and a thigh back, and went into the one
    # forward no less (measured over run and sprint: the leading thigh in it
    # a third as often this way). Near the belt, her skin's weights as above.
    if one_piece is not None and FRINGE_ONE:
        leg1 = one_piece * ramp(hip - pos[:, 2], 0.05, 0.25)
        w1 = np.zeros_like(wt)
        w1[:, BI["pelvis"]] = 1 - leg1
        w1[:, BI["thigh_l"]] = w1[:, BI["thigh_r"]] = leg1 / 2
        k_ = ramp(pos[:, 2], CROTCH - 0.04, CROTCH + 0.06)[:, None]
        wt = wt * k_ + w1 * (1 - k_)
    attr = np.hstack([nor, wt, f_trim[:, None]])
    if os.environ.get("HANGDEBUG"):
        print("HANGDEBUG", name, "grid z %.3f..%.3f" % (pos[:, 2].min(), pos[:, 2].max()), "kept pts", int((f >= 0).sum()), "of", len(f),
              "zb %.3f..%.3f" % (zb.min(), zb.max()), "kept z %.3f..%.3f" % (pos[f >= 0, 2].min(), pos[f >= 0, 2].max()) if (f >= 0).any() else "")
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris)
    if os.environ.get("HANGDEBUG"):
        print("HANGDEBUG", name, "after clip", len(pos), "pts z %.3f..%.3f" % (pos[:, 2].min(), pos[:, 2].max()), len(tris), "tris")
    return trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim)


def witch_hat(name, mkey, band_key, brim=0.21, height=0.34, droop=0.09, bald=False):
    """A wide-brimmed hat with a tall crown that bends back and droops at
    the tip, set on her hair: its crown is as wide as her hair at the brim
    and never nearer it than a centimetre above. All of it is her head's."""
    hd = (wsum("Head") > 0.5) & ((HAIR < 0.5) if bald else True)
    # Her head, and her own hairstyle over it (a mesh apart).
    pts = np.c_[X[hd], Y[hd], Z[hd]]
    if HAIR_DEFAULT and not bald:
        pts = np.vstack([pts, [(HAIR_DEFAULT.matrix_world @ v.co)[:] for v in HAIR_DEFAULT.data.vertices]])
    hx, hy, hz = pts.T
    top = hz.max()
    upper = hz > top - 0.1
    cx, cy = hx[upper].mean(), hy[upper].mean()
    zb = top - 0.07
    ang = np.arctan2(hx - cx, -(hy - cy))
    rad = np.hypot(hx - cx, hy - cy)
    nu = 64
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)

    def hair_r(z, dz=0.008):
        m = np.abs(hz - z) < dz
        out = np.zeros(nu)
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi) < 0.15
            if d.any():
                out[j] = rad[m][d].max()
        return out

    base = hair_r(zb) + 0.012
    base = np.maximum(base, np.percentile(base, 60) * 0.92)
    for _ in range(4):
        base = (np.roll(base, 1) + 2 * base + np.roll(base, -1)) / 4
    # The crown, ring by ring.
    K = 36
    rings = []
    for k in range(K + 1):
        t = k / K
        z = zb + height * t
        bend = max(0.0, t - 0.45) / 0.55
        ccy = cy + 0.13 * bend ** 2
        cz = z - droop * bend ** 3
        scale = (1 - t) ** 1.15
        rr = base * scale + 0.004 * (1 - t)
        need = hair_r(z) + 0.01
        rr = np.maximum(rr, need * (need > 0.01))
        rings.append(np.stack([cx + rr * np.sin(a), ccy - rr * np.cos(a), np.full(nu, cz)], -1))
    crown = np.array(rings).reshape(-1, 3)
    ct = grid(K + 1, nu + 1)
    # Close the seam: wrap the angle.
    idx = np.arange((K + 1) * nu).reshape(K + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    ct = idx[ct]
    # The brim: from the crown's base out, sagging a little, its sides
    # turned up and front and back down (the witch's wave).
    M = 14
    br = []
    for k in range(M + 1):
        t = k / M
        rr = base + brim * t
        z = zb - 0.012 * t * t + 0.03 * t * t * (np.cos(2 * a) * -1 + 1) / 2 - 0.015 * t * t
        br.append(np.stack([cx + rr * np.sin(a), cy - rr * np.cos(a), z], -1))
    brimp = np.array(br).reshape(-1, 3)
    idx = np.arange((M + 1) * nu).reshape(M + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    bt = idx[grid(M + 1, nu + 1)]
    # A band round the crown's foot.
    # The crown closed underneath (seen from below, it was open).
    capc = rings[0].mean(0)
    capp = np.vstack([rings[0], capc[None]])
    capt = np.array([(j, (j + 1) % nu, nu) for j in range(nu)])
    bandp = np.array(rings[:4]).reshape(-1, 3)
    bandp[:, :2] = (bandp[:, :2] - [cx, cy]) * 1.03 + [cx, cy]
    bandt = np.arange(4 * nu).reshape(4, nu)
    bandt = np.c_[bandt, bandt[:, :1]].ravel()[grid(4, nu + 1)]
    out = []
    for nm, pp, tt, key, th in ((name + "_crown", crown, ct, mkey, 0.003), (name + "_brim", brimp, bt, mkey, 0.004),
                                (name + "_band", bandp, bandt, band_key, 0.002), (name + "_cap", capp, capt, mkey, 0.002)):
        n = vertex_normals(pp, tt)
        rad_out = pp[:, :2] - [cx, cy]
        if (n[:, :2] * rad_out).sum(1).mean() < 0 and nm.endswith(("crown", "band")):
            tt = tt[:, ::-1]
        if nm.endswith("brim") and n[:, 2].mean() < 0:
            tt = tt[:, ::-1]
        wt = np.zeros((len(pp), NB))
        wt[:, BI["Head"]] = 1
        out.append(finish(nm, pp, wt, tt, key, th, 0.001))
    print("HAT brim at %.3f, crown base %.3f-%.3f m" % (zb, base.min(), base.max()))
    return out


# ---------------------------------------------------------------- outfits --
def plunge_line(over=0.03, low=0.03, wing=0.022):
    """The top edge of a plunging cup, as a height for each distance from her
    middle: from `low` over her underbust at her middle, rising in a curve
    to `over` above her nipple, highest a little past it where a strap
    would hold it (`wing` higher), then down the side of her breast toward
    her arm."""
    from scipy.interpolate import PchipInterpolator
    nx = abs(NIPPLE["r"][0])
    nz = NIPPLE["r"][2]
    xs = np.array([0.0, 0.012, nx * 0.45, nx * 0.8, nx, nx + 0.025, nx + 0.05, nx + 0.09])
    zs = np.array([UNDERBUST + low - 0.005, UNDERBUST + low, nz - 0.01, nz + over * 0.8, nz + over, nz + over + wing,
                   nz + over + 0.005, nz - 0.02])
    return PchipInterpolator(xs, zs, extrapolate=True)


def warden():
    """The oath-knight, sworn to the Order of the Morning Light: formed
    plate cups, plunging deep between her breasts, gold-bound and riveted,
    held by straps over her shoulders and a strap round her back; a war belt
    slung low on her hips, a skirt of steel plates hung from it, and
    beneath it only a thong; plate at her shoulders, forearms, knees and
    shins."""
    arms = ARMW["l"] + ARMW["r"]
    nx, nz = abs(NIPPLE["r"][0]), NIPPLE["r"][2]

    def gold(w=0.007):
        return ("gold", w, 0.0004, 0.0015)

    # The belt: slung low, where a brief's waistband would run, rising over
    # her hip bones and behind.
    bz0 = CROTCH + 0.13

    def belt_z(a):
        return bz0 + 0.05 * np.clip(np.abs(0.17 * np.sin(a)) / 0.15, 0, 1) ** 2 + 0.06 * ramp(-np.cos(a), -0.15, 0.35)
    under_belt = bz0 - 0.022
    thong_back = back_string(under_belt + 0.06, CROTCH + 0.012)
    # The straps: from each cup's peak, over her shoulder, down her back to
    # the strap round it.
    back_z = UNDERBUST + 0.035
    cups = plate_cups("warden.cups", "steel", plunge_line(), lift=0.002, thick=0.003, trim=gold(0.007), studs="gold")
    # Where her cups meet below her cleavage: the sun of her Order joins them.
    gore_at = np.array([0.0, CUP_LOW[1] - 0.004, CUP_LOW[2] - 0.004])
    buckle_at = front_point(0.0, bz0)
    buckle_n = np.array(SKIN_BVH.find_nearest(Vector(buckle_at))[1][:])
    straps = []
    for sd, sg in (("l", 1), ("r", -1)):
        # (from just under the cup's rim at its peak: it runs up from behind the plate)
        pk = CUP_PEAK[sd]
        top = front_point(pk[0] - sg * 0.004, pk[2] - 0.012)
        # (straight up from the cup to her shoulder: a point between them
        # put a kink in it)
        straps.append([top, np.array([sg * 0.11, 0.03, 1.565]),
                       np.array([sg * 0.1, 0.11, 1.47]), np.array([sg * 0.085, 0.125, back_z])])
    # (STRAP_FINAL, 21 Oct, armor 8 r3: laid on her skin as her body build leaves it (final_skin_bvh), not this scene's:
    # over the crest of her shoulder the scene's skin stands up to 8 mm above hers, so the strap stood 9-14 mm off her
    # there, its dark underside a notch beside her neck at the play camera and a crumpled crest from the front)
    skin_ = final_skin_bvh() if STRAP_FINAL else None
    strap_objs = [o for k, cv in enumerate(straps) for o in ribbon(f"warden.strap{k}", cv, 0.018, "darkleather", thick=0.003,
                                                                  trim=gold(0.003), centre=(0.0, 0.0, 1.33), skin=skin_)]
    backstrap = girdle("warden.backstrap", lambda a_: np.full_like(a_, back_z), 0.022, "darkleather", lift=0.003, thick=0.003,
                       trim=gold(0.003), arc=(1.48, 2 * np.pi - 1.48), mask=arms < 0.3)
    belt = girdle("warden.belt", belt_z, 0.05, "darkleather", lift=0.006, thick=0.005, trim=gold(0.005))
    out = [
        *cups,
        *strap_objs,
        *backstrap,
        *belt,
        # Each strap riveted where it meets the strap round her back.
        *studs_on("warden.strap_rivets", strap_objs + backstrap,
                  [((sg * 0.085, 0.7, back_z + 0.003), (sg * 0.085, 0.0, back_z + 0.003)) for sg in (1, -1)]
                  + [((sg * 0.7 * np.sin(1.53), -0.7 * np.cos(1.53), back_z), (0.0, 0.0, back_z)) for sg in (1, -1)], "gold", r=0.003),
        *sunburst("warden.buckle", buckle_at + buckle_n * 0.009, buckle_n, np.array([0, 0, 1.0]), 0.034, "gold",
                  boss="steel"),
        *sunburst("warden.gore", gore_at, np.array([0, -1.0, 0.25]), np.array([0, 0, 1.0]), 0.019, "gold", rays=8,
                  thick=0.003, boss="steel"),

        # Beneath, a thong: a narrow front (under the fauld) and a string
        # down the back from the belt.
        # (its front starts well under the plates' tucked tops, and lies
        # close, so they hang clear of it)
        *piece("warden.thong", AND(FRONT - 0.3, np.minimum(0.015 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X),
                                   (bz0 - 0.04) - Z, Z - (CROTCH - 0.03)), "darkleather", lift=0.0012, thick=0.0018, smooth=2,
               soften=0),
        # (opening into the gusset over its last 3 cm, as a thong's string
        # does: 2 cm wide all the way, her skin beside it slipped out as her
        # cheeks parted in a vault)
        *ribbon("warden.thong_back", thong_back, 0.02, "darkleather", lift=0.003, thick=0.003, snap=False, hides=True,
                flare=(0.034, 0.03)),
        # (under her, a gusset wider than the string, as a thong's is: the
        # string alone left her bare either side there as she lay on her back)
        # (close under her, 1 mm, her skin tucked in under it and each line of
        # it moving with the skin under that line: hung 6 mm under her and
        # moving as one strap, her skin came through it as her thighs parted)
        # (1.5 cm up into her cleft, under the string's foot: begun 4 mm
        # short of it, the turn between them was bare, and 6 mm under it, the
        # strip beside the hand-over showed as she vaulted)
        *gusset("warden.thong_gusset", "darkleather", GAP_F - 0.006, thong_back[-1][1] + 0.015),
    ]
    # A skirt of steel plates hung all round from the belt, each its own (her
    # legs move freely between them; each swings with the thigh it is over),
    # gold-edged and rounded at its foot: longest in front, over her crotch,
    # shorter behind (the lower curve of her cheeks glimpsed below them); a
    # second row behind the gaps, a little shorter and darker, so nothing
    # shows through them.
    # Each plate's top is tucked up under the belt all along the belt's own
    # line (it rises over her hips and behind), snug there, so the plate
    # comes out from under the belt's edge as if part of it, then flares
    # clear of her thighs. Two gold rivets on the belt fix each plate of
    # the front row.
    plates = 12
    step = 2 * np.pi / plates
    ring = (np.abs(Z - bz0) < 0.01) & (arms < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    aims = []
    for row, (snug, drop, key, w_, th_) in enumerate(((0.003, 0.0, "steel", 0.47, 0.0025), (0.0008, 0.02, "darksteel", 0.4, 0.002))):
        for k in range(plates):
            ac = (k + 0.5 * row) * step
            fr_ = (1 + np.cos(ac)) / 2
            hem = CROTCH - 0.06 * fr_ + 0.035 * (1 - fr_) + drop
            out += hanging(f"warden.skirt{row}_{k}", ac - step * w_, ac + step * w_, lambda a_: belt_z(a_) - 0.018,
                           lambda u, h=hem: h + 0.022 * u * u, key, flare=0.14, lift=snug, gap=0.016 - 0.004 * row, thick=th_,
                           trim=gold(0.006) if row == 0 else None, snug=snug)
            if row == 0:
                for da in (-0.5, 0.5):
                    a_ = ac + da * step * w_
                    z_ = float(belt_z(a_)) - 0.013
                    aims.append(((0.7 * np.sin(a_), cy - 0.7 * np.cos(a_), z_), (0.0, cy, z_)))
    out += studs_on("warden.skirt_rivets", belt, aims, "gold", r=0.0028)
    for sd, sg in (("l", 1), ("r", -1)):
        out += [
            *piece(f"warden.pauldron_{sd}", ANDR(cap(shoulder(sd), 0.11), strap_clear(f"warden.strap{0 if sd == 'l' else 1}", PAUL_STRAP_CLEAR), 0.015)
                   if PAUL_SEAT else cap(shoulder(sd), 0.11), "steel", lift=0.012, thick=0.004, smooth=14, trim=gold(0.01), studs="gold",
                   rigid=head(f"upperarm_{sd}"), seat=(PAUL_SEAT_GAP, PAUL_SEAT_BAND, PAUL_SEAT_UP,
                                                                   lambda q_, c_=abs(shoulder(sd)[0]): ramp(c_ - np.abs(q_[:, 0]), *PAUL_SEAT_IN),
                                                                   (f"warden.strap{0 if sd == 'l' else 1}", *PAUL_BESIDE) if PAUL_BESIDE[0] > 0 else None) if PAUL_SEAT else None,
                   blend_from=cap(shoulder(sd), 0.11) if PAUL_SEAT else None),
            *piece(f"warden.vambrace_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.01, legs=False), "steel", lift=0.006, smooth=8, trim=gold(), studs="gold"),
            *piece(f"warden.greave_{sd}", limb(sd, KNEE_S + 0.03, ANKLE_S + 0.01, front_dip=0.04), "steel", lift=0.008, smooth=12, trim=gold(), studs="gold", rim_clean=GREAVE_RIM,
                   line=(GREAVE_LINE, lambda p_, lp_: p_[lp_, 2].mean() < p_[:, 2].mean())),
            *piece(f"warden.knee_{sd}", cap(LEG[sd][1] + np.array([0, -0.06, 0]), 0.06), "steel", lift=0.016, thick=0.004, smooth=12, trim=gold(0.006)),
            # (the sabaton a made shoe, lofted as the Ranger's boot is, toe box,
            # welted sole and heel, its top under the greave: laid on her foot it
            # showed each toe in steel, animation's judge 49, and laid on her
            # foot's hull the toes still showed as creases; cut 3.5 cm lower behind,
            # its back came through the greave over her heel; judge h, still a patent loafer:
            # now plate, heroine_boots.sabaton: the greave's steel, gold-edged lames, rivets, toe cap, heel cup)
            *BOOTS.sabaton(f"warden.sabaton_{sd}", sd, ANKLE_S - 0.06, 0.035, BOOTS.SABATON, "steel", under=f"warden.greave_{sd}"),
        ]
    return out


PLUNGE_FOOT = float(os.environ.get("PLUNGE_FOOT", 0.022))   # (the round foot's radius)
PLUNGE_FLARE = float(os.environ.get("PLUNGE_FLARE", 1.8))   # (how late its sides ease out: 1 straight)
PLUNGE_FOLD = float(os.environ.get("PLUNGE_FOLD", 0.04))    # (how wide the cloth is fitted over the fold beside its foot)
PLUNGE_FADE = float(os.environ.get("PLUNGE_FADE", 0.0))    # (the fit faded to nothing over this, before its edge; off: at 15 mm, on the U's true distance, the crease came back, 72-80 deg, and the sheet stood 6 mm up through the binding)
PLUNGE_TAUT = float(os.environ.get("PLUNGE_TAUT", 0.06))    # (the gore at its foot: the round its cloth spans her folds by)
PLUNGE_RIM = float(os.environ.get("PLUNGE_RIM", 0.0015))    # (the U's rim, its lower part, this far off her: on a taut string along it)
PLUNGE_STRING = float(os.environ.get("PLUNGE_STRING", 0.035))  # (that string's least round, both ways: it spans her folds, never kinks)
PLUNGE_BAND = float(os.environ.get("PLUNGE_BAND", 0.028))   # (how far from the rim the cloth eases back into the fitted sheet)
PLUNGE_TRIM = os.environ.get("PLUNGE_TRIM", "")   # ("down": the owner's option, a white feathery trim along the plunge, for the side-by-side)
PLUNGE_UNTANGLE = os.environ.get("PLUNGE_UNTANGLE", "1") == "1"   # (s17 spike2: the fold's fit untangled, see plunge_fold)
PLUNGE_CLASP = os.environ.get("PLUNGE_CLASP", "1") == "1"   # (a small gold crescent clasp with a violet stone at the plunge's foot: the fallback, judge 7)
CLASP_TH, CLASP_W = (float(v) for v in os.environ.get("CLASP", "100,0.0085").split(","))   # (the clasp's horns' reach round the foot, degrees; its width at its foot)
# (route D, the coordinator after routes RIDE/S/A failed: a small clasp at the foot only. The horns end
# CLASP_D_TH degrees round (50, was 100), tapered to their own tips, each drawn CLASP_D_IN in toward the
# opening so it ends free over her skin, clear of the binding; no seat, the cut only under its foot.
# CLASP_D=0 gives g0 back)
CLASP_D = os.environ.get("CLASP_D", "1") == "1"
CLASP_D_IN = float(os.environ.get("CLASP_D_IN", "0.0"))   # (D2, clasp6: no pull-in; the tips seated on the binding's outer part, CLASP_D_ON
# onto it from its inner edge, ball CLASP_D_SEAT off it: in her carriage the binding slides 2.0 mm radially and 0.9 mm along
# relative to the rigid clasp at 25 deg (3.1 / 3.7 at 50) but only 0.1 mm in depth, so the balls stay on it, 0.2-0.3 mm off)
CLASP_D_ON = float(os.environ.get("CLASP_D_ON", "0.0037"))
CLASP_D_SEAT = float(os.environ.get("CLASP_D_SEAT", "0.0002"))
CLASP_D_ROUND = os.environ.get("CLASP_D_ROUND", "1") == "1"   # (D2: a half-round section, no flat ledge on its foot from above, judge h)
DOWN_IN, DOWN_OUT = 0.004, 0.012   # (how far the trim reaches over her skin, and over the corset, from the cut)


def arcanist():
    """The arcanist: a velvet capelet and sleeves, a plum leather corset
    with gold boning under low velvet half-cups, an open coat that bares
    her thighs, sheer stockings, thigh boots and a witch's hat."""
    def gold(w=0.006):
        return ("darkpurple", w, 0.0004, 0.0013)

    # The warden's cups (their shape is the one), cut lower toward the
    # middle so the inner and upper breast show; at the outside the cut is
    # above the nipple, so the full cup's edge stands there.
    cup, _ = cups(cover=0.6, plunge=0.012)
    low = np.min([NIPPLE[sd][2] + 0.035 - 0.5 * np.maximum(0, abs(NIPPLE[sd][0]) - np.abs(X)) for sd in "lr"], axis=0) - Z
    for sd in "lr":
        print("NIPPLE COVER arcanist", sd, "cup field %.4f" % cup[np.argmin(np.linalg.norm(P - NIPPLE[sd], axis=1))])
    arms = ARMW["l"] + ARMW["r"]
    ctop = UNDERBUST + 0.012 + 0.07 * (1 - FRONT)
    cbot = 1.012 - 0.04 * np.exp(-(X / 0.04) ** 2) * FRONT
    # A skin-tight one-piece: from under her cups down over her hips to a
    # leotard's high-cut legs.
    ax = np.abs(X)
    # Cut as high as it goes: the leg line rises from the crotch almost to
    # her waist at the sides, front and back.
    # A narrow V in front rising steeply to her hip bones; a thong behind
    # widening into a V above her cheeks.
    # (2.9 cm across at its foot: what must be covered there is 2.4 cm, and
    # at 1.9 cm her skin showed either side of it in a lunge)
    w = (0.0145 + 0.42 * np.maximum(Z - CROTCH, 0) + LEO_FOOT * np.exp(-(np.maximum(Z - CROTCH, 0) / 0.035) ** 2)) * FRONT + (-0.01 + 1.5 * np.maximum(Z - CROTCH - 0.13, 0)) * (1 - FRONT)
    leotard = AND(Z - (CROTCH - 0.03), w - ax)
    # A bodysuit: over her breasts and up to a high neck.
    neck_top = head("neck_01")[2] + 0.07 - 0.035 * (1 - FRONT)
    # Clean armholes: round each shoulder, at a set distance along the
    # arm from the collarbone.
    def sleeve(sd):
        # Sleeves to the gloves: on her arm, down to just inside the glove;
        # her torso always.
        torso = smooth_field(0.5 - ARMW[sd], 40) * 0.1
        side = X * (1 if sd == "l" else -1) > 0
        arm = WRIST_S - float(os.environ.get("ARC_SLEEVE_END", "0.012" if os.environ.get("ARC_HANDS") == "bare" else "0.06")) - ARM_S[sd]
        if ARC_CAPS:
            # (her skin's field a little past the cap: the exact line decides)
            arm = cap_len(P, sd) + 0.02
        return np.where(side, np.maximum(arm, torso), 1.0)
    # (s21, the owner 14 Oct: "sheer off the arm of her leotard leaving just
    # the shoulders". ARC_CAPS: shoulder caps, CAP_TOP down her arm from her
    # shoulder joint over the top of her shoulder, easing (CAP_POW) to
    # CAP_UNDER under her arm, where the armhole follows her torso's own
    # line; cut exactly (`exact`), bound in the suit's gold.)
    ARC_CAPS = os.environ.get("ARC_CAPS", "1") == "1"
    # (armor 17 N3, max judge OJ1: at 7 cm the caps ran past the widest bulge of her deltoid, "a linebacker's
    # shoulders". Now each ends above it, about 3.5 cm below her shoulder point on the outside, tapering to nothing
    # at her armpit; the lower deltoid shows as bare shoulder. Over the cap (her skin's arm weight CAP_W) the
    # leather is laid CAP_LIFT off her, not the suit's 3.5 mm, and CAP_THICK of its thickness (a 2 mm leather
    # hugging her, its bound edge flush), so arc_fit_post's caps step is retired.)
    # (its taper as before, CAP_TOP 7 cm on the line; the cap only cut off at CAP_MAX along her arm, a soft
    # minimum CAP_SOFT round: cut short everywhere, the armhole's back moved into her armpit's fold, where the
    # suit lay 2 mm inside her at rest)
    CAP_TOP = float(os.environ.get("CAP_TOP", "0.07"))
    CAP_MAX = float(os.environ.get("CAP_MAX", "0.04"))
    CAP_SOFT = float(os.environ.get("CAP_SOFT", "0.008"))
    CAP_W = tuple(float(v_) for v_ in os.environ.get("CAP_W", "0.20,0.50").split(","))
    CAP_C = tuple(float(v_) for v_ in os.environ.get("CAP_C", "-0.1,0.5").split(","))
    # (the cap's binding: (width, height, overhang, thickness) over the cap, by her arm weight CAP_BW: about the
    # skived edge's own thickness, so it lies flush, not a 4 mm roll)
    CAP_BW = tuple(float(v_) for v_ in os.environ.get("CAP_BW", "0.15,0.40").split(","))
    CAP_BIND = tuple(float(v_) for v_ in os.environ.get("CAP_BIND", "0.006,0.00025,0.0012,0.0010").split(","))
    CAP_LIFT = float(os.environ.get("CAP_LIFT", "0.0010"))
    CAP_THICK = float(os.environ.get("CAP_THICK", "0.67"))
    CAP_UNDER = float(os.environ.get("CAP_UNDER", "0.0"))
    CAP_POW = float(os.environ.get("CAP_POW", "1.5"))
    def cap_len(q, sd):
        """How far the cap still has to run down her arm at q (metres; < 0 past its edge)."""
        a0, a1 = ARM[sd][0], ARM[sd][1]
        ax_ = (a1 - a0) / np.linalg.norm(a1 - a0)
        t_ = (q - a0) @ ax_
        r_ = q - a0 - np.outer(t_, ax_)
        r_ = r_ / np.maximum(np.linalg.norm(r_, axis=1, keepdims=True), 1e-9)
        up_ = np.array([0.0, 0.0, 1.0]) - ax_[2] * ax_
        up_ /= np.linalg.norm(up_)
        c_ = np.clip(r_ @ up_, -1, 1)
        l_ = CAP_UNDER + (CAP_TOP - CAP_UNDER) * ((1 + c_) / 2) ** CAP_POW
        if CAP_MAX > 0:
            l_ = 0.5 * (l_ + CAP_MAX - np.sqrt((l_ - CAP_MAX) ** 2 + CAP_SOFT ** 2))
        return l_ - t_
    cap_torso = {sd: smooth_field(0.5 - ARMW[sd], 40) * 0.1 for sd in "lr"}
    cap_kd = cKDTree(P)
    def cap_upper(q):
        """Over the top of her arm (1), not its front, back or underside (0): the armhole's front and back, at her
        armpit, keep the suit's lift (laid 1 mm off there, her skin came through it as an arm rose)."""
        out_ = np.zeros(len(q))
        for sd, s_ in (("l", 1), ("r", -1)):
            a0, a1 = ARM[sd][0], ARM[sd][1]
            ax_ = (a1 - a0) / np.linalg.norm(a1 - a0)
            r_ = q - a0 - np.outer((q - a0) @ ax_, ax_)
            r_ = r_ / np.maximum(np.linalg.norm(r_, axis=1, keepdims=True), 1e-9)
            up_ = np.array([0.0, 0.0, 1.0]) - ax_[2] * ax_
            up_ /= np.linalg.norm(up_)
            out_ = np.where(q[:, 0] * s_ > 0, ramp(r_ @ up_, CAP_C[0], CAP_C[1]), out_)
        return out_
    def cap_share(q):
        return ramp((ARMW["l"] + ARMW["r"])[cap_kd.query(q)[1]], CAP_W[0], CAP_W[1]) * cap_upper(q)
    def corset_lift(q):
        return 0.0035 - (0.0035 - CAP_LIFT) * cap_share(q)
    if ARC_CAPS:
        THIN_ZONE["arcanist.corset"] = lambda q: 1 - (1 - CAP_THICK) * cap_share(q)
        BIND_ZONE["arcanist.corset"] = (lambda q: ramp((ARMW["l"] + ARMW["r"])[cap_kd.query(q)[1]], CAP_BW[0], CAP_BW[1]) * cap_upper(q), CAP_BIND)
    def caps_exact(q):
        d_, j_ = cap_kd.query(q, k=6)
        w_ = 1.0 / np.maximum(d_, 1e-5)
        w_ /= w_.sum(1, keepdims=True)
        out_ = np.ones(len(q))
        for sd, s_ in (("l", 1), ("r", -1)):
            side_ = q[:, 0] * s_ > 0
            torso_ = (cap_torso[sd][j_] * w_).sum(1)
            out_ = np.where(side_, np.minimum(out_, np.maximum(cap_len(q, sd), torso_)), out_)
        return out_
    # A plunge: a deep V from her collar to below where her breasts meet,
    # its sides crossing the inner curve of each breast well inside her
    # nipples (her cleavage bare, her breasts held), the high collar kept
    # round the sides and back of her neck.
    v_lo, v_hi = UNDERBUST + 0.004, head("neck_01")[2] + 0.02
    nx_ = abs(NIPPLE["r"][0])
    # (one U, judge 2: drawn piecewise straight it came out with a flat
    # bottom, a hump and a corner. A parabola from its foot, round there,
    # through the upper breast, then eased up to the collar.)
    from scipy.interpolate import PchipInterpolator
    zt, wt_ = NIPPLE["r"][2] + 0.03, nx_ * 0.62
    # (judge 3: the parabola kept widening, so its sides ran out across the
    # fold under her breasts in a corner, its foot a flat strip. Now a true
    # round foot, `R_u`, its sides upright where it ends, rising up her
    # cleavage before they ease out over her breasts.)
    R_u = PLUNGE_FOOT
    a = np.linspace(0, np.pi / 2, 10)
    zf, xf = v_lo + R_u * (1 - np.cos(a)), R_u * np.sin(a)
    t = np.linspace(0, 1, 9)[1:]
    zr = v_lo + R_u + (zt - v_lo - R_u) * t
    xr = R_u + (wt_ - R_u) * t ** PLUNGE_FLARE
    zk = np.r_[zf, zr, zt + (v_hi - zt) * np.array([0.35, 0.7]), v_hi]
    xk = np.r_[xf, xr, wt_ + (0.05 - wt_) * 0.3, wt_ + (0.05 - wt_) * 0.7, 0.05]
    _vh = PchipInterpolator(zk, xk, extrapolate=False)
    def vhalf(z):
        return np.nan_to_num(_vh(np.clip(z, v_lo, v_hi)))
    print("PLUNGE U: foot round %.1f mm, %.1f cm across at %.1f cm above its foot" % (R_u * 1000, 2 * wt_ * 100, (zt - v_lo) * 100))
    # The U cut by its signed distance, front on, from one line mirrored, its
    # foot a true circle (cut by |x| - vhalf, which jumped where its foot
    # began, the clip set the foot flat on a row of her points).
    def uhalf(z):
        r_ = np.clip(z - v_lo, 0.0, R_u)
        return np.where(z < v_lo + R_u, np.sqrt(np.maximum(R_u * R_u - (R_u - r_) ** 2, 0.0)), vhalf(z))
    zz_ = np.r_[v_lo + R_u * (1 - np.cos(np.linspace(0, np.pi / 2, 400))), np.arange(v_lo + R_u + 0.0002, v_hi + 0.15, 0.0002)]
    xx_ = uhalf(zz_)
    u_tree = cKDTree(np.r_[np.c_[-xx_[::-1], zz_[::-1]], np.c_[xx_, zz_]])
    def u_dist(qx, qz):
        d = u_tree.query(np.c_[qx, qz])[0]
        return np.where((qz >= v_lo) & (np.abs(qx) < uhalf(qz)), -d, d)
    v_half = vhalf(Z)
    plunge = np.where(FRONT > 0.5, np.abs(X) - v_half, 1.0)
    plunge = np.where(Z < v_lo, 1.0, plunge)
    # Its leg lines and plunge are cut exactly once it is shaped (cut on her
    # skin and then smoothed, they wandered); her skin's field is left a
    # little wider there, so the exact lines decide.
    corset = AND(neck_top - Z, OR(Z - 1.13, leotard + 0.02), sleeve("l"), sleeve("r"), plunge + 0.02)

    # (judge h: the V's foot was a knot, the two leg lines meeting the bridge's
    # straight cut in two corners, their binding folded and crossed by the
    # gusset's. Now ONE U across the foot: the leg lines rounded into one curve
    # LEO_U[0] round, in a chart tilted 45 degrees (t, up the front of her mound
    # and forward under it alike), its bottom LEO_U[1] in front of the bridge's
    # cut so this exact line, not the cut, decides; the gusset lies under it.)
    y_ub = GAP_F - LEO_U[1]
    t_ub = ((roof_z(0.0, y_ub) - 0.0035) - y_ub) / np.sqrt(2)
    # (LEO_ONE: the one-piece's back end, where the gusset's was, under the thong's foot)
    y_end1 = max(GAP_B + 0.014, back_string(CROTCH + 0.155, CROTCH + 0.012)[-1][1] + 0.015)
    roof_ys = np.linspace(GAP_F - 0.03, y_end1 + 0.01, 80)
    roof_zs = np.array([roof_z(0.0, y) for y in roof_ys])
    if LEO_ROOF_FIX:
        # (s18 leo3: where her thighs meet under the slot, y 0.006-0.016 at rest, the cast from 30 cm below hit them, not the roof)
        bad_ = roof_zs < CROTCH - 0.02
        for i_ in np.nonzero(bad_)[0]:
            hit_ = BVH.ray_cast(Vector((0.0, float(roof_ys[i_]), CROTCH - 0.02)), Vector((0, 0, 1)), 0.1)
            roof_zs[i_] = hit_[0].z if hit_[0] is not None else np.interp(roof_ys[i_], roof_ys[~bad_], roof_zs[~bad_])
        print("LEO_ROOF_FIX: %d roof samples (under where her thighs meet) cast again from the slot" % int(bad_.sum()))

    def exact(q):
        qx, qy, qz = q[:, 0], q[:, 1], q[:, 2]
        fr = ramp(-(qy - CROTCH_Y), -0.03, 0.03)
        r = qz - CROTCH
        wq = (0.0145 + 0.42 * np.maximum(r, 0) + LEO_FOOT * np.exp(-(np.maximum(r, 0) / 0.035) ** 2)) * fr + (-0.01 + 1.5 * np.maximum(r - 0.13, 0)) * (1 - fr)
        if LEO_ONE:
            # (one piece: under her crotch the leg lines carry on back to the thong's foot)
            u_ = ramp(-qz, -(CROTCH + LEO_ONE_Z[1]), -(CROTCH + LEO_ONE_Z[0]))
            wf_ = 0.0145 + 0.42 * np.maximum(r, 0) + LEO_FOOT * np.exp(-(np.maximum(r, 0) / 0.035) ** 2)
            wq = wf_ * fr + (1 - fr) * (u_ * LEO_ONE_W[1] + (1 - u_) * (-0.01 + 1.5 * np.maximum(r - 0.13, 0)))
        legs = np.maximum(qz - 1.13, wq - np.abs(qx))
        if LEO_ONE:
            a_, b_, ru = wq - np.abs(qx), y_end1 - qy, LEO_ONE_W[2]
            end_ = np.where((a_ < ru) & (b_ < ru), ru - np.hypot(ru - a_, ru - b_), np.minimum(a_, b_))
            legs = np.where((qy > CROTCH_Y) & (u_ > 0), np.minimum(legs, end_), legs)
            if LEO_ONE_DEPTH > 0:
                floor_ = np.interp(qy, roof_ys, roof_zs) - LEO_ONE_DEPTH - 0.012 * ramp(qy, CROTCH_Y - 0.02, CROTCH_Y + 0.02)
                if LEO_SLOT_CAP > 0:
                    # (s18 leo2, LEO_SLOT_CAP: round her crotch point no deeper than this under the roof)
                    w_ = ramp(qy, CROTCH_Y - 0.02, CROTCH_Y - 0.008) * (1 - ramp(qy, CROTCH_Y + LEO_SLOT_BACK, CROTCH_Y + LEO_SLOT_BACK + 0.012))
                    floor_ = floor_ + w_ * np.maximum(np.interp(qy, roof_ys, roof_zs) - LEO_SLOT_CAP - floor_, 0.0)
                legs = np.where((qy > GAP_F - 0.025) & (qz < CROTCH + 0.005), np.minimum(legs, qz - floor_), legs)
        if LEO_U[0] > 0 and not LEO_ONE:
            a_, b_, ru = wq - np.abs(qx), (qz - qy) / np.sqrt(2) - t_ub, LEO_U[0]
            foot = np.where((a_ < ru) & (b_ < ru), ru - np.hypot(ru - a_, ru - b_), np.minimum(a_, b_))
            legs = np.where((qy < CROTCH_Y) & (qz < CROTCH + 0.06), foot, legs)
        pl = np.where(fr > 0.5, u_dist(qx, qz), 1.0)
        if ARC_CAPS:
            return np.minimum(np.minimum(legs, pl), caps_exact(q))
        return np.minimum(legs, pl)
    # A boned front from her underbust to below her navel: stiff, so it no
    # longer shows every muscle of her stomach (judge 2), the rest still
    # skin-tight.
    # (judge 4: a small round blister over each collarbone: fitted as the
    # stomach is, the bone's knob no longer cast in the leather)
    nz0 = head("neck_01")[2]
    def collar(q):
        return (ramp(q[:, 2], NIPPLE["l"][2] + 0.05, NIPPLE["l"][2] + 0.08) * ramp(-q[:, 2], -(nz0 + 0.012), -(nz0 - 0.008))
                * ramp(-np.abs(q[:, 0]), -0.17, -0.14) * ramp(-q[:, 1], -(q[:, 1].mean() + 0.02), -q[:, 1].mean()))
    # (the plunge's foot: the fold under each breast ran into the U's sides
    # as a crease, which the gore lifted but kept (a solver, 11 October).
    # Fitted wide there, the cloth spans the fold as it would.)
    def fold(q):
        return (ramp(-np.abs(q[:, 0]), -0.09, -0.065) * ramp(q[:, 2], v_lo - 0.03, v_lo - 0.012)
                * ramp(-q[:, 2], -(v_lo + 0.075), -(v_lo + 0.05)) * ramp(-q[:, 1], -(q[:, 1].mean() + 0.02), -q[:, 1].mean()))
    def front_panel(q):
        return (ramp(q[:, 2], WAIST - 0.11, WAIST - 0.08) * ramp(-q[:, 2], -(UNDERBUST - 0.005), -(UNDERBUST - 0.025))
                * ramp(-np.abs(q[:, 0]), -0.12, -0.09) * ramp(-q[:, 1], -(q[:, 1].mean() + 0.02), -q[:, 1].mean()))
    # The plunge's foot on a taut gore, as cloth spans there: not down into
    # the fold under her breasts, where any line crossing it kinked (judge 3:
    # a flat strip across her sternum, a corner at each side; fitted locally,
    # a notch and a step seen from above, the fold kept). Her sheet, front
    # on, is closed by a disc `PLUNGE_TAUT` round rolled up and down it (the
    # fold spanned; her cleavage, which the U opens, not bridged), and across
    # it below the foot (the groove of her sternum spanned); that lift, the
    # same both sides, is laid on her sheet round the foot. It only lifts.
    def taut_gore(pos, tris):
        from scipy.ndimage import grey_closing, gaussian_filter
        from scipy.interpolate import RegularGridInterpolator
        g, R = 0.001, PLUNGE_TAUT
        gx = np.linspace(-0.1, 0.1, 201)
        gz = np.arange(v_lo - 0.07, v_lo + 0.12 + 1e-9, g)
        def front_depth(pp, tt):
            box = (np.abs(pp[:, 0]) < 0.13) & (np.abs(pp[:, 2] - v_lo - 0.025) < 0.13) & (pp[:, 1] < pp[:, 1].mean())
            bvh = BVHTree.FromPolygons([tuple(p) for p in pp], tt[box[tt].all(1)].tolist())
            y0 = pp[:, 1].min() - 0.3
            d = np.full((len(gz), len(gx)), np.nan)
            for i, j in np.ndindex(d.shape):
                hit = bvh.ray_cast(Vector((gx[j], y0, gz[i])), Vector((0.0, 1.0, 0.0)))[0]
                if hit is not None:
                    d[i, j] = -hit[1]
            return d
        hs, hk = front_depth(pos, tris), front_depth(P_FILLED, TRI)
        both = ~np.isnan(hs) & ~np.isnan(hk)
        h = np.where(np.isnan(hs), hk + np.median(hs[both] - hk[both]), hs)
        h = np.where(np.isnan(h), np.nanmin(h), h)
        k = int(round(R / g))
        s = np.sqrt(np.maximum(R * R - (np.arange(-k, k + 1) * g) ** 2, 0.0))
        up = grey_closing(h, structure=s[:, None], mode="nearest")
        across = grey_closing(h, structure=s[None, :], mode="nearest")
        def sstep(t):
            t = np.clip(t, 0.0, 1.0)
            return t ** 3 * (t * (6 * t - 15) + 10)
        below = sstep((v_lo + 0.012 - gz) / 0.012)[:, None]
        # (not within 20 mm of the U: the rim is pinned there, plunge_rim)
        mx, mz = np.meshgrid(gx, gz)
        below = below * sstep((u_dist(mx.ravel(), mz.ravel()).reshape(mx.shape) - 0.01) / 0.01)
        c = np.maximum(up, h + below * (across - h))
        c = np.maximum(c, c[:, ::-1])
        lift_ = gaussian_filter(c - h, 2.0)
        lf = RegularGridInterpolator((gz, gx), lift_, bounds_error=False, fill_value=0.0)
        w = (sstep((0.085 - np.abs(pos[:, 0])) / 0.035) * sstep((pos[:, 2] - (v_lo - 0.065)) / 0.03)
             * sstep((v_lo + 0.115 - pos[:, 2]) / 0.04) * ramp(-pos[:, 1], -(pos[:, 1].mean() + 0.02), -pos[:, 1].mean()))
        lv = lf(np.c_[pos[:, 2], pos[:, 0]]) * w
        probe = lambda x_, dz: float(lf([[v_lo + dz, x_]])[0]) * 1000
        print("TAUT GORE: disc %.0f mm; lifted up to %.1f mm; at its foot %.1f, 15 mm below %.1f, beside it (25 mm out, 15 up) %.1f / %.1f, (35 out, 15 up) %.1f / %.1f"
              % (R * 1000, lv.max() * 1000, probe(0, 0), probe(0, -0.015), probe(-0.025, 0.015), probe(0.025, 0.015), probe(-0.035, 0.015), probe(0.035, 0.015)))
        out = pos.copy()
        out[:, 1] -= lv
        return out
    # (the fold beside the plunge's foot fitted `PLUNGE_FOLD` wide as before,
    # but lifted off her by a smooth field of what each place needs: lifted
    # as one by the most any place needed, 7.4 mm, its foot stood 16 mm in
    # front of her sternum, a flat shelf; solver, 11 October)
    def plunge_fold(pos, tris):
        pos0_ = pos.copy()
        sw = fold(pos)
        pos = mls_flat(pos, sw, (0.0, -1.0, 0.0), PLUNGE_FOLD)
        on = np.where(sw > 1e-3)[0]
        need = np.linalg.norm(pushes_off_skin(pos[on], 0.0035), axis=1)
        tr = cKDTree(pos[on])
        env = np.array([need[j].max() for j in tr.query_ball_point(pos[on], 0.015)])
        sm = np.empty(len(on))
        for i, j in enumerate(tr.query_ball_point(pos[on], 0.018)):
            g_ = np.exp(-0.5 * (np.linalg.norm(pos[on][j] - pos[on][i], axis=1) / 0.006) ** 2)
            sm[i] = (env[j] * g_).sum() / g_.sum()
        lv = np.zeros(len(pos))
        lv[on] = sm * sw[on]
        print("PLUNGE FOLD: fitted %.0f mm wide, lifted %.1f to %.1f mm (median %.1f)"
              % (PLUNGE_FOLD * 1000, sm.min() * 1000, sm.max() * 1000, np.median(sm) * 1000))
        out_ = pos + vertex_normals(pos, tris) * lv[:, None]
        if PLUNGE_UNTANGLE:
            # (s17 spike2: the fit along her depth laid the steep wall of the fold
            # under each breast flat into a crease of turned-over triangles, which
            # the U's cut met at each corner of its foot: a flap of the sheet 2 mm
            # under its roll, the tooth left of the clasp and the speck right of it)
            out_ = sheet_untangled("arcanist.corset", out_, pos0_, tris, fold(pos0_) > 1e-3)
        return out_
    # The U's rim, its lower part, pinned onto her as a bound edge lies: on a
    # taut string along the U (her skin's depth along it closed and opened by
    # a round `PLUNGE_STRING`: it spans the fold under each breast without
    # dipping into it, and never kinks) `PLUNGE_RIM` off her. From it to the
    # fitted sheet the cloth is a membrane over her (it spans, never goes
    # through her), eased back into the sheet by `PLUNGE_BAND` from the rim;
    # the same both sides. (The fit faded before the rim instead, its crease
    # came back, solver 11 October.)
    def rim_depth(pp, tt, gx, gz):
        box = (np.abs(pp[:, 0]) < 0.13) & (np.abs(pp[:, 2] - v_lo - 0.025) < 0.13) & (pp[:, 1] < pp[:, 1].mean())
        bvh = BVHTree.FromPolygons([tuple(p) for p in pp], tt[box[tt].all(1)].tolist())
        y0 = pp[:, 1].min() - 0.3
        d = np.full((len(gz), len(gx)), np.nan)
        for i, j in np.ndindex(d.shape):
            hit = bvh.ray_cast(Vector((gx[j], y0, gz[i])), Vector((0.0, 1.0, 0.0)))[0]
            if hit is not None:
                d[i, j] = -hit[1]
        return d
    def plunge_rim(pos, tris):
        from scipy.ndimage import grey_closing, grey_opening
        from scipy.interpolate import RegularGridInterpolator
        def sstep(t):
            t = np.clip(t, 0.0, 1.0)
            return t ** 3 * (t * (6 * t - 15) + 10)
        g = 0.001
        gx = np.linspace(-0.09, 0.09, 181)
        gz = np.arange(v_lo - 0.05, v_lo + 0.1 + 1e-9, g)
        GX, GZ = np.meshgrid(gx, gz)
        hs, hk = rim_depth(pos, tris, gx, gz), rim_depth(P_FILLED, TRI, gx, gz)
        hk = np.where(np.isnan(hk), np.nanmin(hk), hk)
        hs = np.where(np.isnan(hs), hk + 0.0035, hs)
        hs_m, hk_m = (hs + hs[:, ::-1]) / 2, (hk + hk[:, ::-1]) / 2
        # (the string, along the U from its foot, in mm)
        sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.c_[xx_, zz_], axis=0), axis=1))]
        s = np.arange(0, sl[-1], g)
        xu, zu = np.interp(s, sl, xx_), np.interp(s, sl, zz_)
        keep = zu < gz[-1] - 0.002
        xu, zu = xu[keep], zu[keep]
        f = RegularGridInterpolator((gz, gx), hk_m)(np.c_[zu, xu]) * 1000
        sh = RegularGridInterpolator((gz, gx), hs_m)(np.c_[zu, xu]) * 1000
        R = PLUNGE_STRING * 1000
        k = int(R)
        ball = np.sqrt(np.maximum(R * R - np.arange(-k, k + 1) ** 2, 0.0))
        full = np.r_[f[:0:-1], f]
        T = grey_opening(grey_closing(full, structure=ball, mode="nearest"), structure=ball, mode="nearest")[len(f) - 1:] + PLUNGE_RIM * 1000
        a = sstep((v_lo + 0.08 - zu) / 0.03)
        Tr = (a * T + (1 - a) * sh) / 1000
        # (each place: its way from the rim, front on, and the rim's place nearest it)
        ud = u_dist(GX.ravel(), GZ.ravel()).reshape(GX.shape)
        near = cKDTree(np.c_[xu, zu]).query(np.c_[np.abs(GX.ravel()), GZ.ravel()])[1].reshape(GX.shape)
        fixed = (ud <= 0) | (ud >= PLUNGE_BAND)
        fixed[[0, -1], :] = True
        fixed[:, [0, -1]] = True
        D = np.where(ud <= 0, Tr[near], hs_m)
        floor_ = hk_m + PLUNGE_RIM * 0.8
        for _ in range(3000):
            av = 0.25 * (np.roll(D, 1, 0) + np.roll(D, -1, 0) + np.roll(D, 1, 1) + np.roll(D, -1, 1))
            D = np.where(fixed, D, np.maximum(av, floor_))
        w = np.where(ud < 0, sstep((ud + 0.012) / 0.006), 1 - sstep((ud - 0.01) / (PLUNGE_BAND - 0.01))) * a[near]
        lf = RegularGridInterpolator((gz, gx), w * (D - hs), bounds_error=False, fill_value=0.0)
        lv = lf(np.c_[pos[:, 2], pos[:, 0]]) * ramp(-pos[:, 1], -(pos[:, 1].mean() + 0.02), -pos[:, 1].mean())
        print("PLUNGE RIM: string %.0f mm round, rim %.1f mm off her (at its foot the string %.1f over her, the sheet was %.1f); moved %.1f to %.1f mm"
              % (R, PLUNGE_RIM * 1000, T[0] - f[0], sh[0] - f[0], lv.min() * 1000, lv.max() * 1000))
        out = pos.copy()
        out[:, 1] -= lv
        return out
    belt_z = 1.0 + 0.035 * X / 0.18
    belt = AND(0.016 - np.abs(Z - belt_z), 0.3 - arms)
    bones = OR(*[front_line(x, UNDERBUST - 0.022, x * 0.8, 1.025 - 0.025 * (abs(x) < 0.05), 0.009)
                 for x in (-0.085, -0.04, 0.04, 0.085)])
    bones = AND(bones, corset - 0.004)
    nz = head("neck_01")[2]
    choker = AND(0.009 - np.abs(Z - (nz + 0.035)), wsum("neck_01", "Head") - 0.4, 0.3 - wsum("Head") + wsum("neck_01") * 0, 0.3 - arms)
    mantle = OR(cap(shoulder("l"), 0.14), cap(shoulder("r"), 0.14),
                AND(Z - 1.43, (Y - 0.0), 0.3 - arms))
    # The owner's option (11 October): a white feathery trim along the plunge,
    # "only increase the skin we cover slightly". A soft roll swept along the
    # corset's own bound edge (smoothed), DOWN_IN over her skin and DOWN_OUT
    # over the corset, flat beneath, fur shells grown on it (tuned as down),
    # tapered to nothing at her neck. (Cut from her skin as a band, it came
    # out as torn paper ribbons, h4.)
    def plunge_clasp():
        """The plunge's foot closed by a small clasp (PLUNGE_CLASP=1; the
        coordinator's fallback after judge 7: a fair U at the foot would not
        come clean at 1:1 after two solvers and one more try). A crescent of
        the corset's gold lying on the binding round the foot, its horns rising
        up the U's sides past where its kinks were (about 23 mm out), a violet
        cabochon in a gold bezel at its foot. It covers the binding and at most
        1 mm of her skin inside it. Its back follows the cloth and binding
        under it (their front-most surface, eased), 0.6 mm off; each point
        skinned as the corset point nearest it, so it never parts from them."""
        cp, ct, cw, cth = SHEET["arcanist.corset"]
        obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("arcanist.corset")]
        dg = bpy.context.evaluated_depsgraph_get()
        bvhs = [(BVHTree.FromObject(o.evaluated_get(dg), dg), o.matrix_world.copy()) for o in obs]
        cz = v_lo + R_u
        TH0, W0, R_IN = np.radians(CLASP_TH), CLASP_W, R_u - 0.001

        def front(x, z):
            best = None
            for bv, mw in bvhs:
                inv = mw.inverted()
                h = bv.ray_cast(inv @ Vector((x, -1.0, z)), (inv.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized(), 2.0)
                if h[0] is not None:
                    y = (mw @ h[0])[1]
                    best = y if best is None else min(best, y)
            return np.nan if best is None else best

        # (front on: columns round the foot, rows across the crescent)
        nth, nr = 61, 15
        uu = 0.5 - 0.5 * np.cos(np.pi * np.linspace(0, 1, nr))   # (across it, closer at its rims)
        th = np.linspace(-TH0, TH0, nth)
        # (a boss under the stone tapering to 2.5 mm at its tips, judge 8; the
        # horns follow the binding's own inner edge on each side, found by
        # walking out from the foot's centre until the cloth begins, so both
        # tips lie on it: a round of one radius ran one under the cup and left
        # the other on her skin)
        y_ft = front(0.0, v_lo - 0.004)   # (the cloth just below the foot: the front layer's depth)

        def edge(t0):
            # (the binding's inner edge on the ray at t0 round the foot)
            for r_ in np.arange(0.5 * R_u, 3.0 * R_u, 0.00025):
                if front(r_ * np.sin(t0), cz - r_ * np.cos(t0)) < y_ft + 0.04:   # (nan is never less: the opening; her back's cloth is far behind)
                    return r_
            return np.nan

        def taper(s_):
            return (0.0025 + 0.0085 * (1 - s_) ** 1.5) * np.sqrt(np.clip(1 - s_ ** 12, 0.25, 1.0))

        # (judge 8 asked to keep h5's 58 mm span so it reaches past the U's
        # kinks, where its round foot meets its sides. Once the horns
        # followed the binding's inner edge, 78 degrees came to 38 mm and
        # stopped short of them; held at 58 mm the horns climbed 145 degrees
        # up the sides and it read as a gold lining, no longer a clasp. So
        # the horns go 100 degrees round, just past the kinks; CLASP_SPAN, in
        # metres, solves the reach for a span instead)
        SPAN = float(os.environ.get("CLASP_SPAN", "0"))
        if SPAN > 0:
            tg = np.radians(np.arange(0.0, 160.01, 1.0))
            eg = np.array([edge(t0) for t0 in tg])
            ok_ = ~np.isnan(eg)
            top = tg[ok_ & (np.cumsum(~ok_) == 0)].max()   # (as far round as the edge runs unbroken)

            def reach(T):
                t_ = np.linspace(-T, T, nth)
                x_ = (np.interp(np.abs(t_), tg[ok_], eg[ok_]) - 0.001 + taper(np.abs(t_) / T)) * np.sin(t_)
                return x_.max() - x_.min()
            lo_, hi_ = np.radians(30.0), top
            for _ in range(30):
                mid = 0.5 * (lo_ + hi_)
                lo_, hi_ = (mid, hi_) if reach(mid) < SPAN else (lo_, mid)
            TH0 = 0.5 * (lo_ + hi_)
            if reach(TH0) < SPAN - 0.001:
                print("CLASP: WARNING the binding's edge runs out at %.0f deg; span only %.0f mm" % (np.degrees(top), reach(TH0) * 1000))
        if CLASP_D:
            TH0 = np.radians(float(os.environ.get("CLASP_D_TH", "25")))
        th = np.linspace(-TH0, TH0, nth)
        s_ = np.abs(th) / TH0
        wid = taper(s_)
        r_e = np.array([edge(t0) for t0 in th])
        r_e = np.where(np.isnan(r_e), np.nanmax(r_e), r_e)
        for _ in range(6):
            r_e[1:-1] = 0.25 * r_e[:-2] + 0.5 * r_e[1:-1] + 0.25 * r_e[2:]
        # (its inner rim 1 mm onto her skin at the foot, meeting it there; out
        # along the horns it moves onto the binding, 1 mm in from the
        # binding's inner edge at the tips, and each horn narrows about its
        # own middle line: narrowed from the outside only, the tips lay
        # inside the binding's edge, on her skin, as points, judge 8)
        wfull = 0.0025 + 0.0085 * (1 - s_) ** 1.5
        # (each tip on its cup's binding, judge 9: the binding's own edges found
        # front on along each tip's ray, where it is the corset's front-most
        # piece, and the horn's outer rim CLASP_TIPIN, 1.5 mm, inside its outer
        # edge. A fixed 5 mm out from the cloth's edge put the right tip under
        # its cup and left the left one on her skin, n1)
        bvb = [(BVHTree.FromObject(o.evaluated_get(dg), dg), o.matrix_world.copy()) for o in obs if "_bind" in o.name or o.name.endswith("_trim")]   # (the binding is `<piece>_bind<k>`, tube(); "_trim" alone found none, c1)

        def on_bind(x, z):
            yb = None
            for bv, mw in bvb:
                inv = mw.inverted()
                h = bv.ray_cast(inv @ Vector((x, -1.0, z)), (inv.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized(), 2.0)
                if h[0] is not None:
                    yb = (mw @ h[0])[1] if yb is None else min(yb, (mw @ h[0])[1])
            return yb is not None and yb <= front(x, z) + 1e-5
        TIPIN = float(os.environ.get("CLASP_TIPIN", "0.0015"))
        outs = {}
        for a in (0, nth - 1):
            rs = np.arange(r_e[a] - 0.003, r_e[a] + 0.02, 0.0001)
            hit = np.array([on_bind(r * np.sin(th[a]), cz - r * np.cos(th[a])) for r in rs])
            base = r_e[a] - 0.001 + 0.5 * wfull[a]
            if not hit.any():
                print("CLASP: WARNING no binding on the tip's ray at %.0f deg" % np.degrees(th[a]))
                outs[a] = 0.005
                continue
            i0 = int(np.argmax(hit))
            i1 = i0 + int(np.argmin(np.r_[hit[i0:], False]))
            rb0, rb1 = rs[i0], rs[i1 - 1]
            want = rb0 + CLASP_D_ON if CLASP_D else max(rb1 - TIPIN - 0.0012, rb0 + 0.0012)
            outs[a] = want - base
            print("CLASP: tip at %+.0f deg: binding %.1f to %.1f mm out from the foot's centre (cloth's edge %.1f); horn's middle %.1f, %.1f mm inside its outer edge"
                  % (np.degrees(th[a]), rb0 * 1000, rb1 * 1000, r_e[a] * 1000, want * 1000, (rb1 - want) * 1000))
        mid_ = r_e - 0.001 + (np.where(th < 0, outs[0], outs[nth - 1]) - (CLASP_D_IN if CLASP_D else 0.0)) * s_ ** 2 + 0.5 * wfull
        R_IN = mid_ - 0.5 * wid
        if CLASP_D and CLASP_D_ROUND:
            # (D2, judge h: from above its foot stood as a pale ledge (h3), or half-round
            # as a tall hood, behind the stone: its inner rim lay 1 mm over her skin, so
            # its back's rim dropped 4.8 mm to her skin there. Now the inner rim lies at
            # least CLASP_D_RIN onto the binding all along (a smooth max), its outer rim
            # out by half as much, so the binding's own inner edge, uncut, runs down to
            # her skin above it as all round the U; the tips stay where they were)
            d_ = r_e + float(os.environ.get("CLASP_D_RIN", "0.0008")) - R_IN
            sh = 0.5 * (d_ + np.sqrt(d_ * d_ + 0.0004 ** 2))
            f_ = np.clip((s_ - 0.8) / 0.2, 0, 1)
            sh = sh * (1 - f_ * f_ * (3 - 2 * f_))
            wid = wid - 0.5 * sh
            R_IN = R_IN + sh
            print("CLASP: inner rim onto the binding: moved out %.1f mm at the foot, %.1f at 50%% out, %.2f at the tips"
                  % (sh[nth // 2] * 1000, np.interp(0.5, s_[nth // 2:], sh[nth // 2:]) * 1000, sh[0] * 1000))
        rr = R_IN[:, None] + wid[:, None] * uu[None, :]
        X = rr * np.sin(th)[:, None]
        Zc = cz - rr * np.cos(th)[:, None]
        Y = np.array([[front(X[a, b], Zc[a, b]) for b in range(nr)] for a in range(nth)])
        Y[Y > y_ft + 0.04] = np.nan   # (her back's cloth, seen through the opening)
        Yraw = Y.copy()
        # (inside the opening the ray finds no cloth: the row's own front-most)
        for a in range(nth):
            ok = ~np.isnan(Y[a])
            Y[a] = np.where(ok, Y[a], np.nanmin(Y[a]) if ok.any() else np.nanmin(Y))
        Y = np.minimum.accumulate(Y[:, ::-1], axis=1)[:, ::-1]   # (never behind what lies outside it)
        if CLASP_D and CLASP_D_ROUND and os.environ.get("CLASP_D_LIE", "1") == "1":
            # (D2: across its foot the back follows the cloth and binding as they are,
            # not held to the front-most outside each point: there the corset recedes
            # about 17 deg as it rises and its binding lies flush with it, so held
            # square the crescent stood 3.4 mm off the binding at its top, its stone
            # square to her, and from above its foot read as a ledge or hood, judge h.
            # Laid on them it is seen nearly face on from above; the horns as before)
            w_ = np.clip((0.7 - s_) / 0.3, 0, 1)
            Y = Y + (w_ * w_ * (3 - 2 * w_))[:, None] * (np.where(np.isnan(Yraw), Y, Yraw) - Y)
        # (a rigid piece of metal, not a foil: its back is one smooth surface,
        # a cubic in x and z hugging the front-most of the cloth and binding
        # under it (refitted to the lower envelope), then set CLASP_OFF, 3 mm,
        # in front of every sample. At 0.4 mm the cloth came through it in her
        # idle (her chest rises under it) and the strip read as crumpled foil
        # with its horns buried; at 3 mm it lies clean.)
        Y0 = Y.copy()
        xs, zs = X.ravel() / 0.03, (Zc.ravel() - cz) / 0.03
        A = np.stack([xs ** i * zs ** j for i in range(4) for j in range(4 - i)], 1)
        tgt = Y0.ravel().copy()
        for _ in range(40):
            fit = A @ np.linalg.lstsq(A, tgt, rcond=None)[0]
            tgt = np.minimum(Y0.ravel(), fit)
        Y = fit.reshape(Y0.shape)
        Y = Y + min(0.0, float((Y0 - Y).min())) - float(os.environ.get("CLASP_OFF", 0.001))
        # (the horns laid down onto the binding toward their tips, 0.4 mm off
        # it: held in front of all the crescent's samples they stood off it)
        k_ = np.clip((s_ - 0.55) / 0.45, 0, 1)
        Y = Y + (0.0 if CLASP_D and CLASP_D_IN > 0 else 1.0) * (k_ * k_ * (3 - 2 * k_) * np.maximum((Y0 - Y).min(1) - 0.0004, 0))[:, None]
        gap = (Y0 - Y) * 1000
        print(f"CLASP: back off the cloth {gap.min():.2f} to {gap.max():.2f} mm (median {np.median(gap):.2f}; its rim {np.median(np.r_[gap[:, 0], gap[:, -1]]):.2f})")
        t = uu[None, :]
        # (a 0.7 mm round at each rim under a polished crown: a thin bright
        # line along both edges, judge 9)
        dd = np.minimum(t, 1 - t) * wid[:, None]
        bump = (0.0006 + 0.0006 * np.sqrt(1 - (1 - np.clip(dd / 0.0007, 0, 1)) ** 2)
                + 0.0011 * np.sqrt(np.clip(np.sin(np.pi * t), 0, 1)) * (wid[:, None] / W0) ** 0.5)
        # (its back's rim drawn down onto what lies under it, 0.3 mm off: her
        # skin where its inner rim is over the opening, else the cloth or
        # binding. From above a slot showed between its back and her skin,
        # and the motion check saw her tucked skin through it, judge 9)
        bsel = (np.abs(P_FILLED[:, 0]) < 0.07) & (np.abs(P_FILLED[:, 2] - cz) < 0.07) & (P_FILLED[:, 1] < y_ft + 0.03)
        sbv = BVHTree.FromPolygons([tuple(p) for p in P_FILLED], TRI[bsel[TRI].all(1)].tolist())

        def skin_y(x, z):
            h = sbv.ray_cast(Vector((x, -1.0, z)), Vector((0.0, 1.0, 0.0)))[0]
            return np.inf if h is None else h[1]
        under = np.minimum(np.where(np.isnan(Yraw), np.inf, Yraw), np.array([[skin_y(X[a, b], Zc[a, b]) for b in range(nr)] for a in range(nth)]))
        per = np.zeros((nth, nr), bool)
        per[:, 0] = per[:, -1] = per[0, :] = per[-1, :] = True
        if CLASP_D:
            per &= (s_ < 0.6)[:, None]   # (D: the horns end free over her skin, no skirt drawn down to it)
        Yb = np.where(per & np.isfinite(under), np.maximum(Y, np.minimum(under - 0.0003, Y + float(os.environ.get("CLASP_PULL", "0.006")))), Y)   # (at most 6 mm: 12 mm reached her skin behind the cup, c1)
        print("CLASP: back's rim drawn down %.1f to %.1f mm onto what lies under it (inner rim median %.1f)"
              % (((Yb - Y)[per]).min() * 1000, ((Yb - Y)[per]).max() * 1000, np.median((Yb - Y)[:, 0]) * 1000))
        Yf = Y - bump
        if CLASP_D and CLASP_D_ROUND:
            # (D2's foot read as a pale flat ledge from above, a top hat's brim:
            # the back's inner rim drawn 4.8 mm down to her skin left a flat wall
            # under a flat-topped bar, judge h. Now a half-round section all
            # along: the front rolls from its crown down to the back's rim on both
            # sides; the drawn-down rim eases out toward the horns (none past 60%
            # out); the front never nearer the cloth under it than 0.4 mm)
            fall = np.clip((0.6 - s_) / 0.2, 0, 1)
            Yb = Y + (Yb - Y) * (fall * fall * (3 - 2 * fall))[:, None]
            L_ = Y + (1 - t) * (Yb[:, :1] - Y[:, :1]) + t * (Yb[:, -1:] - Y[:, -1:])
            crown = Y - bump[:, nr // 2][:, None]
            Yf = L_ - (L_ - crown) * np.sqrt(np.clip(1 - (2 * t - 1) ** 2, 0, 1))
            Yf = np.minimum(Yf, np.where(np.isnan(Yraw), np.inf, Yraw - 0.0004))
            Yb = np.maximum(Yb, Yf + 0.0003)
            print("CLASP: half-round section; at the foot its crown %.1f mm proud of its inner rim, %.1f of its outer; %.1f mm proud at the tips"
                  % ((L_[nth // 2, 0] - crown[nth // 2, 0]) * 1000, (L_[nth // 2, -1] - crown[nth // 2, 0]) * 1000, (L_[0, 0] - crown[0, 0]) * 1000))
        back = np.stack([X, Yb, Zc], -1)
        frnt = np.stack([X, Yf, Zc], -1)
        P2, T2 = [], []

        def grid(G, flip):
            o = sum(len(q) for q in P2)
            P2.append(G.reshape(-1, 3))
            for a in range(nth - 1):
                for b in range(nr - 1):
                    q = [o + a * nr + b, o + (a + 1) * nr + b, o + (a + 1) * nr + b + 1, o + a * nr + b + 1]
                    T2.extend([(q[0], q[1], q[2]), (q[0], q[2], q[3])] if not flip else [(q[0], q[2], q[1]), (q[0], q[3], q[2])])
        grid(frnt, False)
        grid(back, True)
        n0 = nth * nr
        rim = ([(a, 0) for a in range(nth)] + [(nth - 1, b) for b in range(nr)]
               + [(a, nr - 1) for a in range(nth - 1, -1, -1)] + [(0, b) for b in range(nr - 1, -1, -1)])
        for (a0, b0), (a1, b1) in zip(rim, rim[1:]):
            i0, i1 = a0 * nr + b0, a1 * nr + b1
            T2.extend([(i0, n0 + i0, n0 + i1), (i0, n0 + i1, i1)])
        pp, tt = np.vstack(P2), np.array(T2)
        if (vertex_normals(pp, tt)[:n0, 1] > 0).mean() > 0.5:
            tt = tt[:, ::-1]
        c_foot = back[nth // 2, nr // 2]
        def sk(pts):
            # (metal moves as one rigid piece: every point of the crescent, its
            # bezel and stone takes one row, the cloth's weights averaged over
            # 12 mm round the foot. Per-point weights mixed her breasts' and
            # spine's bones differently from point to point, and the four-bone
            # cut crumpled the strip into zigzags in her idle.)
            d, j = cKDTree(cp).query(c_foot, k=96)
            g = np.exp(-(d / 0.012) ** 2)
            w = (cw[j] * g[:, None]).sum(0) / g.sum()
            return np.repeat((w / w.sum())[None], len(pts), 0)
        # (the horns ride their cups: each station takes the cloth's own weights
        # under its middle (6 mm round it), blended in from the rigid row over
        # the first 30% out from the foot (there the two nearly agree), so the
        # crescent bends as the binding under it does and the tips and balls move
        # with the cups' rolls. Rigid, the rolls slid 9 mm off the balls in her
        # carriage (rest + HerPose), both over her skin; blended in from 30% to
        # 85% the horns rode their rolls but folded at a kink, c1. At rest the
        # balls were within 0.4 mm of the binding, judge 10)
        w_r = sk(pp[:1])[0]
        mids = np.stack([X[:, nr // 2], Y[:, nr // 2], Zc[:, nr // 2]], 1)
        d_w, j_w = cKDTree(cp).query(mids, k=48)
        g_w = np.exp(-0.5 * (d_w / 0.006) ** 2) + 1e-12
        w_b = (cw[j_w] * g_w[:, :, None]).sum(1) / g_w.sum(1)[:, None]
        for _ in range(4):
            w_b[1:-1] = 0.25 * w_b[:-2] + 0.5 * w_b[1:-1] + 0.25 * w_b[2:]
        k_w = np.clip((s_ - float(os.environ.get("CLASP_RIDE0", "0.0"))) / 0.3, 0, 1)
        k_w = k_w * k_w * k_w * (k_w * (6 * k_w - 15) + 10)
        w_st = (1 - k_w)[:, None] * w_r[None] + k_w[:, None] * w_b
        w_st = w_st / w_st.sum(1, keepdims=True)
        print("CLASP: horns ride their cups from %.0f%% out (full by +30%%); tip rows %s | %s" % (100 * float(os.environ.get("CLASP_RIDE0", "0.3")),
              {BONES[j]: round(float(w_st[0, j]), 3) for j in np.argsort(-w_st[0])[:4]}, {BONES[j]: round(float(w_st[-1, j]), 3) for j in np.argsort(-w_st[-1])[:4]}))
        RIDE = os.environ.get("CLASP_RIDE", "0") == "1"   # (off: c2 rode the rolls but the crescent came out a flattened, dented bar in her carriage)
        # (CLASP_SHEAR=1, route S, unjudged: each half's rows blend from the rigid row at the
        # stone to the cloth's own row under its tip, along ((1 - cos th) / (1 - cos TH0)) ** 0.8,
        # the binding's own profile round the U (offline: it leads the cosine by 0.03-0.07). Its
        # U flattens in her carriage (spine_03 pitched 31 deg on spine_02): the tips then ride
        # the binding as at rest; a tip shift of 0.20 left the balls beside the tube or inside it)
        if os.environ.get("CLASP_SHEAR", "0") == "1":
            f_ = ((1 - np.cos(th)) / (1 - np.cos(TH0))) ** float(os.environ.get("CLASP_SHEAR_P", "0.8"))
            w_st = (1 - f_)[:, None] * w_r[None] + f_[:, None] * np.where((th < 0)[:, None], w_b[0][None], w_b[-1][None])
            w_st = w_st / w_st.sum(1, keepdims=True)
            RIDE = True
            print("CLASP: SHEAR on: tip rows %s | %s" % ({BONES[j]: round(float(w_st[0, j]), 3) for j in np.argsort(-w_st[0])[:4]},
                  {BONES[j]: round(float(w_st[-1, j]), 3) for j in np.argsort(-w_st[-1])[:4]}))
        # (CLASP_A=1, route A, unjudged, failed offline: the whole clasp (crescent, bezel, stone, balls)
        # one rigid row, the mean of the corset's own rows under its two tips, so it keeps its shape and
        # its balls stay seated in her carriage (0.8 / 0.5 mm off their rest seats). Her U flattens there
        # (its sides drop 14 mm on its foot), so the clasp's foot lands 14 mm below the U's foot and 4.5 mm
        # in: the cloth below covers the stone and foot and the cut under the clasp opens, 77 of 78 mm^2)
        if os.environ.get("CLASP_A", "0") == "1":
            w_a = 0.5 * (w_b[0] + w_b[-1])
            w_a = w_a / w_a.sum()
            sk = lambda pts, w_a=w_a: np.repeat(w_a[None], len(pts), 0)
            RIDE = False
            print("CLASP: A on: one row %s" % {BONES[j]: round(float(w_a[j]), 3) for j in np.argsort(-w_a)[:5]})
        made = [finish("arcanist.clasp", pp, w_st[(np.arange(len(pp)) % (nth * nr)) // nr] if RIDE else sk(pp), tt, "claspgold", 0.0, 0.0, 10 ** 6, scraps=False)]
        # (the stone: an oval cabochon at the foot, 10 x 8 mm, 3.2 mm high, in
        # a gold bezel ring 1 mm proud of the crescent)
        c0 = frnt[nth // 2, nr // 2]
        nu, nv = 24, 6
        # (D2: the stone and bezel laid on the crescent's back at the foot, not square
        # to her: the cloth there recedes as it rises, so a square bezel's top stood
        # off the crescent and its bottom sank into it; CLASP_D_TILT=0 squares it)
        m_ = float(np.polyfit(Zc[nth // 2], Y[nth // 2], 1)[0]) if CLASP_D and CLASP_D_ROUND and os.environ.get("CLASP_D_TILT", "1") == "1" else 0.0
        nh_, vh_ = np.array([0.0, -1.0, m_]) / math.hypot(1.0, m_), np.array([0.0, m_, 1.0]) / math.hypot(1.0, m_)

        def jw(dx, dy, dz):
            # (a point of the jewel: dx across, dy behind its seat (- in front), dz up its face)
            return c0 + np.array([dx, 0.0, 0.0]) - dy * nh_ + dz * vh_
        sp = [jw(0.005 * np.cos(2 * np.pi * j / nu) * np.cos(k / nv * np.pi / 2), -0.0032 * np.sin(k / nv * np.pi / 2),
                 0.004 * np.sin(2 * np.pi * j / nu) * np.cos(k / nv * np.pi / 2)) for k in range(nv + 1) for j in range(nu)]
        st = [t_ for k in range(nv) for j in range(nu) for t_ in ((k * nu + j, k * nu + (j + 1) % nu, (k + 1) * nu + (j + 1) % nu),
                                                                   (k * nu + j, (k + 1) * nu + (j + 1) % nu, (k + 1) * nu + j))]
        sp, st = np.array(sp), np.array(st)
        if (vertex_normals(sp, st)[:, 1] > 0).mean() > 0.5:
            st = st[:, ::-1]
        _, jn = cKDTree(cp).query(sp)
        made.append(finish("arcanist.clasp_stone", sp, sk(sp), st, "amethyst", 0.0, 0.0, 10 ** 6, scraps=False))
        # (under a half-round crescent the bezel's ring stood off it at its top and
        # bottom: its outer wall flares back 3.5 mm into the crescent, a bezel cup)
        BEZ = ((1.0, 0.0), (1.0, -0.001), (1.2, -0.001), (1.2, 0.0)) if not (CLASP_D and CLASP_D_ROUND) else               ((1.0, 0.0), (1.0, -0.001), (1.2, -0.001), (1.25, -0.0002), (1.3, 0.0035))
        cup = [BEZ[-1][1]] * nu
        if CLASP_D and CLASP_D_ROUND:
            # (D2: the cup's last row reaches back to what lies behind it, 0.3 mm
            # into it: the crescent's front where it lies under it, else the binding
            # or cloth, else her skin; at most 6 mm. A fixed 3.5 mm stood off the
            # binding at its top and sank into the crescent at its sides)
            def behind(x, z):
                r_, t_ = math.hypot(x, cz - z), math.atan2(x, cz - z)
                if abs(t_) <= TH0:
                    ri, wi = np.interp(t_, th, R_IN), np.interp(t_, th, wid)
                    u_ = (r_ - ri) / wi
                    if -0.001 / wi <= u_ <= 1.0 + 0.001 / wi:   # (within 1 mm of it: onto its rim)
                        u_ = min(max(u_, 0.0), 1.0)
                        fa = np.interp(t_, th, np.arange(nth))
                        a0 = min(int(fa), nth - 2)
                        fb = np.arccos(np.clip(1 - 2 * u_, -1, 1)) / np.pi * (nr - 1)
                        b0 = min(int(fb), nr - 2)
                        wa, wb = fa - a0, fb - b0
                        return float((1 - wa) * ((1 - wb) * Yf[a0, b0] + wb * Yf[a0, b0 + 1]) + wa * ((1 - wb) * Yf[a0 + 1, b0] + wb * Yf[a0 + 1, b0 + 1])), True
                y_ = front(x, z)
                return (skin_y(x, z) if np.isnan(y_) or y_ > y_ft + 0.04 else y_), False
            ra_ = BEZ[-1][0]
            for j in range(nu):
                dx_, dz_, D_ = 0.005 * ra_ * np.cos(2 * np.pi * j / nu), 0.004 * ra_ * np.sin(2 * np.pi * j / nu), 0.001
                for _ in range(6):
                    q_ = jw(dx_, D_, dz_)
                    ys_, in_ = behind(q_[0], q_[2])
                    D_ = float(np.clip(D_ + ((ys_ if np.isfinite(ys_) else q_[1] + 0.01) + 0.0003 - q_[1]) * math.hypot(1.0, m_), 0.0005, 0.006))
                # (only its upper half reaches back, where a slot behind it shows from
                # above; elsewhere, over the cloth beside and below the boss or over the
                # crescent's lower half, the cup stays shallow, CLASP_D_CUPOUT: reaching
                # 4.8 mm to the cloth it stood as a drum round the stone (clasp16a), 3.2
                # mm to the crescent below it a thick double rim front on (clasp16b))
                cup[j] = D_ if in_ and dz_ > 0 else min(D_, float(os.environ.get("CLASP_D_CUPOUT", "0.0012")))
            print("CLASP: jewel laid %.0f deg back on the crescent; bezel cup reaches back %.1f mm at its top, %.1f at its sides, %.1f at its bottom"
                  % (np.degrees(np.arctan(m_)), cup[nu // 4] * 1000, 0.5 * (cup[0] + cup[nu // 2]) * 1000, cup[3 * nu // 4] * 1000))
        bp = [jw(0.005 * ra * np.cos(2 * np.pi * j / nu), cup[j] if k_ == len(BEZ) - 1 else dy, 0.004 * ra * np.sin(2 * np.pi * j / nu))
              for k_, (ra, dy) in enumerate(BEZ) for j in range(nu)]
        bt = [t_ for k in range(len(BEZ) - 1) for j in range(nu) for t_ in ((k * nu + j, (k + 1) * nu + (j + 1) % nu, k * nu + (j + 1) % nu),
                                                                  (k * nu + j, (k + 1) * nu + j, (k + 1) * nu + (j + 1) % nu))]
        bp, bt = np.array(bp), np.array(bt)
        _, jn = cKDTree(cp).query(bp)
        made.append(finish("arcanist.clasp_bezel", bp, sk(bp), bt, "claspgold", 0.0, 0.0, 10 ** 6, scraps=False))
        # (a small gold ball at each horn's tip, 3.2 mm across, seated on the
        # binding: the narrowed tips read as sharp points, judge 8)
        tp, tt_ = [], []
        for a in (0, nth - 1):
            # (centred on the horn's front at its middle line, over the binding:
            # set 1.2 mm in front of its back, the horn's front buried it, j1)
            q0 = frnt[a, nr // 2].copy()
            if CLASP_D and CLASP_D_IN == 0:   # (D2: seated on the binding under it, CLASP_D_SEAT off it)
                q0[1] = front(q0[0], q0[2]) - float(os.environ.get("CLASP_D_BALL", "0.0011")) - CLASP_D_SEAT
            o_ = len(tp)
            tp += [q0 + (float(os.environ.get("CLASP_D_BALL", "0.0011")) if CLASP_D else 0.0009) * np.array([np.cos(2 * np.pi * j / nu) * np.cos(0.98 * np.pi * (k / nv - 0.5)), np.sin(0.98 * np.pi * (k / nv - 0.5)),
                                            np.sin(2 * np.pi * j / nu) * np.cos(0.98 * np.pi * (k / nv - 0.5))]) for k in range(nv + 1) for j in range(nu)]
            tt_ += [(o_ + t0, o_ + t1, o_ + t2) for k in range(nv) for j in range(nu)
                    for t0, t1, t2 in ((k * nu + j, k * nu + (j + 1) % nu, (k + 1) * nu + (j + 1) % nu),
                                       (k * nu + j, (k + 1) * nu + (j + 1) % nu, (k + 1) * nu + j))]
        tp, tt_ = np.array(tp), np.array(tt_)
        if (vertex_normals(tp, tt_)[:len(tp) // 2] * (tp[:len(tp) // 2] - tp[:len(tp) // 2].mean(0))).sum(1).mean() < 0:
            tt_ = tt_[:, ::-1]
        made.append(finish("arcanist.clasp_tips", tp, np.repeat(w_st[[0, nth - 1]], len(tp) // 2, 0) if RIDE else sk(tp), tt_, "claspgold", 0.0, 0.0, 10 ** 6, scraps=False))
        print("CLASP: crescent %.0f mm across, horns %.0f deg round the foot, %.1f mm wide at its foot; stone at z %.3f"
              % ((X.max() - X.min()) * 1000, np.degrees(TH0), wid[nth // 2] * 1000, c0[2]))
        # (the cloth, binding and stitches under it cut away 1 mm inside its
        # edge: lumps of the cloth came through a rigid clasp seated close in
        # her idle, and 3 mm off it showed a dark slot round it, judge 8)
        yb, ncut = float(Y.max()) + 0.012, 0
        for o in obs:
            mw = o.matrix_world
            bm = bmesh.new()
            bm.from_mesh(o.data)
            gone = []
            for f in bm.faces:
                ins = True
                for v in f.verts:
                    q = mw @ v.co
                    r_, t_ = math.hypot(q.x, cz - q.z), math.atan2(q.x, cz - q.z)
                    ri, wi = np.interp(t_, th, R_IN), np.interp(t_, th, wid)
                    if abs(t_) >= TH0 * (float(os.environ.get("CLASP_D_CUT", "0.6")) if CLASP_D else 0.97) or q.y > yb or not (ri + 0.001 < r_ < ri + wi - 0.001):
                        ins = False
                        break
                if ins:
                    gone.append(f)
            if gone:
                bmesh.ops.delete(bm, geom=gone, context="FACES")
                bm.to_mesh(o.data)
            bm.free()
            ncut += len(gone)
        print("CLASP: %d faces of cloth, binding and stitches cut away under it" % ncut)
        return made

    def down_tube():
        cp, ct, cw, cth = SHEET["arcanist.corset"]
        cn = vertex_normals(cp, ct)
        best = None
        for lp in edge_loops(ct):
            lp = np.array(lp)
            q = cp[lp]
            on = (np.abs(u_dist(q[:, 0], q[:, 2])) < 0.008) & (q[:, 2] > v_lo - 0.02) & (q[:, 2] < head("neck_01")[2] + 0.05) & (q[:, 1] < 0)
            if on.sum() > (0 if best is None else best[1].sum()):
                best = (lp, on)
        lp, on = best
        # (the longest run round the loop that is on the plunge)
        k0 = int(np.argmin(on))
        lp, on = np.roll(lp, -k0), np.roll(on, -k0)
        runs, s0 = [], None
        for k, v in enumerate(np.r_[on, False]):
            if v and s0 is None:
                s0 = k
            if not v and s0 is not None:
                runs.append((s0, k))
                s0 = None
        a0, a1 = max(runs, key=lambda r: r[1] - r[0])
        C = cp[lp[a0:a1]]
        C = C[C[:, 2] <= min(C[0, 2], C[-1, 2]) + 1e-6]   # (both ends as high, so it mirrors onto itself)
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
        t = np.arange(0, L[-1], 0.0015)
        C = np.stack([np.interp(t, L, C[:, k]) for k in range(3)], 1)
        # (made the same both sides, its mirror's average, and eased over about
        # 15 mm: along the edge as bound, the foot's kinks came through, h4)
        C = 0.5 * (C + C[::-1] * np.array([-1.0, 1.0, 1.0]))
        for _ in range(200):
            C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
        _, jn = cKDTree(cp).query(C)
        n_ = cn[jn]
        T_ = np.gradient(C, axis=0)
        T_ /= np.linalg.norm(T_, axis=1)[:, None]
        b_ = np.cross(T_, n_)
        b_ /= np.linalg.norm(b_, axis=1)[:, None]
        # (b toward the corset: the side its sheet lies on)
        mid = cp[cKDTree(cp).query(C + b_ * 0.006)[1]] - C
        if ((mid * b_).sum(1) < 0).mean() > 0.5:
            b_ = -b_
        n_ = np.cross(b_, T_)
        w_ = (DOWN_IN + DOWN_OUT) / 2
        off = (DOWN_OUT - DOWN_IN) / 2
        s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
        taper = np.clip(np.minimum(s_, s_[-1] - s_) / 0.015, 0.03, 1.0)
        taper = taper * taper * (3 - 2 * taper)
        nseg = 18
        ph = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
        cx, cy = np.cos(ph), np.maximum(np.sin(ph), -0.25)
        cen = C + n_ * (cth + 0.0022) + b_ * off * taper[:, None]
        pos = (cen[:, None, :] + (b_[:, None, :] * cx[None, :, None] * w_ + n_[:, None, :] * cy[None, :, None] * 0.0042) * taper[:, None, None]).reshape(-1, 3)
        rows = len(C)
        tris = []
        for r in range(rows - 1):
            for k in range(nseg):
                a, b2, c2, d = r * nseg + k, r * nseg + (k + 1) % nseg, (r + 1) * nseg + k, (r + 1) * nseg + (k + 1) % nseg
                tris += [(a, c2, b2), (b2, c2, d)]
        tris = np.array(tris)
        nr_ = vertex_normals(pos, tris)
        if ((nr_.reshape(rows, nseg, 3) * (pos.reshape(rows, nseg, 3) - cen[:, None, :])).sum(2).mean() < 0):
            tris = tris[:, ::-1]
        # (its weights the corset's under it, eased along it)
        wt = cw[jn].astype(float)
        for _ in range(30):
            wt[1:-1] = 0.25 * wt[:-2] + 0.5 * wt[1:-1] + 0.25 * wt[2:]
        wt = four_bones(np.repeat(wt, nseg, 0))
        print("DOWN arcanist.down: %.0f mm along the plunge, %d rings" % (s_[-1] * 1000, rows))
        return [finish("arcanist.down", pos, wt, tris, "down", 0.0, 0.0, 10 ** 6, scraps=False)]

    global GARTER_Z
    GARTER_Z = CROTCH + 0.2
    # (the gloves' cuffs 4 cm up under the sleeves, which end 6 cm short of her
    # wrists: at 2 cm a notch at the sleeve's hem showed her skin, judge 14)
    GLOVE_TOP = float(os.environ.get("GLOVE_TOP", 0.10))
    # (s21, the owner 14 Oct: "lets make the gloves elbow length": with her
    # shoulder caps (ARC_CAPS) the glove's top is ARC_GLOVE_ELBOW below her
    # elbow joint, her upper arm bare between)
    if os.environ.get("ARC_CAPS", "1") == "1" and "GLOVE_TOP" not in os.environ:
        GLOVE_TOP = WRIST_S - ELBOW_S - float(os.environ.get("ARC_GLOVE_ELBOW", "0.04"))
    # (s20, the owner 14 Oct, her hands: ARC_HANDS glove (as before) | fingerless
    # | bare (no gloves; the sleeves to her wrists, ARC_SLEEVE_END short of it);
    # a fingerless glove in ARC_GLOVE_MAT ("satin": the white of her stockings'
    # bands), second-skin: FL_LIFT off her, FL_THICK thick)
    global ARC_HANDS
    ARC_HANDS = os.environ.get("ARC_HANDS", "fingerless")
    ARC_GLOVE_MAT = os.environ.get("ARC_GLOVE_MAT", "glovesatin")
    FL_LIFT = float(os.environ.get("FL_LIFT", "0.0005"))
    FL_THICK = float(os.environ.get("FL_THICK", "0.0006"))
    FL_CUT = float(os.environ.get("FL_CUT", "0.012"))
    FL_CUT_THUMB = float(os.environ.get("FL_CUT_THUMB", "0.008"))
    FL_POINT = float(os.environ.get("FL_POINT", "0.016"))
    FL_POINT_W = float(os.environ.get("FL_POINT_W", "0.009"))
    # (the U's foot lies on the gusset, not held down through it: where the gusset
    # is under it, 0 to 1, held onto its top; LEO_U, LEO_UG, LEO_UH. Released
    # there instead, the held leg line stepped 2 mm up within 2 mm, a bump.)
    def on_gusset(q):
        hf = LEO_GHALF + LEO_GW[0] * ramp(-q[:, 1], -(GAP_F + LEO_GW[2]), -(GAP_F + LEO_GW[1]))
        return (float(LEO_U[0] > 0 and not LEO_ONE) * ramp(hf + LEO_UG[1] - np.abs(q[:, 0]), 0.0, LEO_UG[0] + LEO_UG[1]) * ramp(q[:, 1], GAP_F - LEO_GUSSET_F - 0.002, GAP_F - LEO_GUSSET_F + 0.004)
                * ramp(-q[:, 2], -(CROTCH + 0.035), -(CROTCH + 0.028)))
    # (judge h: the glove copied the nail's free edge at the thumb tip, an
    # overhang with a dark wedge under it, and a pale lip at the thumb and
    # index tips. Dark flecks at the sleeve's hem over the glove's top: its
    # top 15 mm sunk GLOVE_SINK deeper, under the sleeve.)
    # (The sheet copies her nail: it folds back under the nail's free edge and
    # into the grooves round it. Laid point by point on the tip's convex hull,
    # the fold was only flattened onto it, its triangles still turned over, and
    # thickened along their turned normals they showed as the wedge. So each
    # fingertip, over its last GLOVE_TIP_R[0] (the whole nail; the thumb's
    # GLOVE_TIP_THUMB times as far), eased out by GLOVE_TIP_R[1], is relaxed
    # over the hull, GLOVE_TIP_ROUNDS times each point toward its neighbours'
    # mean and back onto the hull: one taut round cap, nothing turned over. The
    # hull holds her own fingertip lifted as far as the rest of the glove
    # (1.2 mm), so the cap is never nearer her than that; clear_of_skin pushes
    # only under GLOVE_TIP_CLEAR there, as its push along the nearest face's
    # normal at the nail's edge is what folded the sheet again.)
    GLOVE_TIP_R = tuple(float(v) for v in os.environ.get("GLOVE_TIP_R", "0.011,0.017").split(","))
    GLOVE_TIP_THUMB = float(os.environ.get("GLOVE_TIP_THUMB", "1.25"))
    GLOVE_TIP_ROUNDS = int(os.environ.get("GLOVE_TIP_ROUNDS", "40"))
    GLOVE_TIP_RELAX = float(os.environ.get("GLOVE_TIP_RELAX", "0.85"))
    GLOVE_TIP_CLEAR = float(os.environ.get("GLOVE_TIP_CLEAR", "0.0005"))
    GLOVE_SINK = float(os.environ.get("GLOVE_SINK", "0.001"))
    # (s17: each cap ends GLOVE_TIP_DIP short of where her skin starts to bend
    # with the finger's middle bone (its last bone's weight under
    # GLOVE_TIP_BEND), eased over at least GLOVE_TIP_EASE, its hull taken
    # GLOVE_TIP_HULL past it; rounded by GLOVE_TIP_TAUBIN rounds and held
    # GLOVE_TIP_FLOOR off her; Loop-divided GLOVE_TIP_SUB times in finish())
    # (GLOVE_TIP_BEND off (0) by default: her skin's weights fade from the last
    # bone from 5 to 19 mm short of the tip, unevenly between her hands)
    GLOVE_TIP_BEND = float(os.environ.get("GLOVE_TIP_BEND", "0"))
    GLOVE_TIP_FAIR = int(os.environ.get("GLOVE_TIP_FAIR", "4"))
    GLOVE_TIP_DIP = float(os.environ.get("GLOVE_TIP_DIP", "0.002"))
    GLOVE_TIP_EASE = float(os.environ.get("GLOVE_TIP_EASE", "0.004"))
    GLOVE_TIP_HULL = float(os.environ.get("GLOVE_TIP_HULL", "0.002"))
    GLOVE_TIP_TAUBIN = int(os.environ.get("GLOVE_TIP_TAUBIN", "20"))
    GLOVE_TIP_FLOOR = float(os.environ.get("GLOVE_TIP_FLOOR", "0.001"))
    GLOVE_TIP_SUB = int(os.environ.get("GLOVE_TIP_SUB", "1"))
    skin_kd = cKDTree(P)
    glove_tips_ = {}

    def glove_tips(sd):
        # (each finger: its bones, the tip of its skin, its two radii)
        if sd not in glove_tips_:
            glove_tips_[sd] = []
            for fg in ("thumb", "index", "middle", "ring", "pinky"):
                bs = [BI[f"{fg}_0{i}_{sd}"] for i in (1, 2, 3) if f"{fg}_0{i}_{sd}" in BI]
                if len(bs) < 3:
                    continue
                sel = W[:, bs[2]] > 0.5
                if sel.sum() < 5:
                    continue
                base = P[W[:, bs[1]] > 0.5].mean(0)
                tip = P[sel][np.argmax(np.linalg.norm(P[sel] - base, axis=1))]
                sc = GLOVE_TIP_THUMB if fg == "thumb" else 1.0
                r0, r1 = GLOVE_TIP_R[0] * sc, GLOVE_TIP_R[1] * sc
                # (fin1's 17 mm reached over the pinky's last joint: curled
                # (idle), the leather bridged over its crease folded into a
                # ragged patch with pale glints)
                bend = (W[:, bs].sum(1) > 0.5) & (W[:, bs[2]] < GLOVE_TIP_BEND)
                if bend.any():
                    r1 = min(r1, float(np.linalg.norm(P[bend] - tip, axis=1).min()) - GLOVE_TIP_DIP)
                    r0 = min(r0, r1 - GLOVE_TIP_EASE)
                glove_tips_[sd].append((fg, bs, tip, r0, r1))
        return glove_tips_[sd]

    def glove_tip_k(pos, sd):
        # (1 over each fingertip's cap, eased to 0 at its edge; its own finger only)
        nb = skin_kd.query(pos)[1]
        k = np.zeros(len(pos))
        for fg, bs, tip, r0, r1 in glove_tips(sd):
            kk = np.clip((r1 - np.linalg.norm(pos - tip, axis=1)) / (r1 - r0), 0, 1)
            k = np.maximum(k, np.where(W[nb][:, bs].sum(1) > 0.5, kk * kk * (3 - 2 * kk), 0.0))
        return k

    for sd_ in "lr":
        KEEP_FINE[f"arcanist.glove_{sd_}"] = lambda q, sd_=sd_: glove_tip_k(q, sd_)

    def glove_sub(pos, wt, tris, sd):
        # (the caps Loop-divided GLOVE_TIP_SUB times: every face with a point
        # on a cap, the move eased by the cap)
        n0 = len(tris)
        for _ in range(GLOVE_TIP_SUB):
            k = glove_tip_k(pos, sd)
            pos, wt, tris = loop_divided(pos, wt, tris, (k[tris] > 0).any(1), k)
        print("GLOVE %s: caps Loop-divided %d times, %d faces -> %d" % (sd, GLOVE_TIP_SUB, n0, len(tris)))
        return pos, wt, tris
    for sd_ in "lr":
        KEEP_SUB[f"arcanist.glove_{sd_}"] = lambda q, w_, t_, sd_=sd_: glove_sub(q, w_, t_, sd_)

    F1h = lambda n_: F1_HEADS.get(n_, head(n_))   # (s24: the glove's cut as drawn on F1's hand)
    # (s24, the owner picked B1 and said "give them style": GLOVE_STYLE G1 "sorceress points" | G2 "laced
    # plunge" (glove_style_spec.md); "" is B1 as it was. Any style: the satin at 212/0.25 (S1, its SPEC row),
    # the top dipped GLOVE_CROOK at her inner elbow over +-GLOVE_CROOK_W deg (S3, clear of her biceps at the
    # brim); G1 and G2 bound in plum, GLOVE_PIPE (width, height over the sheet, overhang) round every edge,
    # the thumb's too, the line eased GLOVE_BIND_SIGMA (B1's 12 mm took the points off))
    GLOVE_STYLE = os.environ.get("GLOVE_STYLE", "")
    _g1, _g2 = GLOVE_STYLE == "G1", GLOVE_STYLE == "G2"
    GLOVE_CROOK = float(os.environ.get("GLOVE_CROOK", "0.006" if GLOVE_STYLE else "0"))
    GLOVE_CROOK_W = np.radians(float(os.environ.get("GLOVE_CROOK_W", "70")))
    GLOVE_PIPE = tuple(float(v) for v in os.environ.get("GLOVE_PIPE", "0.003,0.0006,0.0014").split(","))
    GLOVE_BIND_SIGMA = float(os.environ.get("GLOVE_BIND_SIGMA", "0.003"))
    # (s28: the top's binding alone as (width, height over the sheet, overhang), the louder G3; 0 = GLOVE_PIPE's)
    GLOVE_PIPE_TOP = tuple(float(v) for v in os.environ.get("GLOVE_PIPE_TOP", "0,0,0").split(","))
    # (G1: the top's lancet ARC_GLOVE_POINT up toward her elbow, ARC_GLOVE_POINT_W deg each side at its root,
    # its tip ARC_GLOVE_POINT_TIP deg round, centred ARC_GLOVE_POINT_ROT deg round from the back of her hand
    # toward her pinky (her ulna's ridge, the line to her elbow's tip); on her hand a tongue FL_TONGUE onto
    # her middle finger, FL_TONGUE_W wide, its tip FL_TONGUE_R round; a plum ring round that finger through
    # the tongue's tip, GLOVE_LOOP (wire r, lift off her on the palm side, over the tongue, back from the tip)
    # and three ivory points down the back of her hand, GLOVE_POINTS (spacing at the knuckles, at the wrist
    # end, length, gap behind the line, thread r))
    ARC_GLOVE_POINT = float(os.environ.get("ARC_GLOVE_POINT", "0.024" if _g1 else "0"))
    ARC_GLOVE_POINT_W = np.radians(float(os.environ.get("ARC_GLOVE_POINT_W", "42")))
    ARC_GLOVE_POINT_TIP = np.radians(float(os.environ.get("ARC_GLOVE_POINT_TIP", "4")))
    ARC_GLOVE_POINT_ROT = np.radians(float(os.environ.get("ARC_GLOVE_POINT_ROT", "45")))
    ARC_GLOVE_POINT_AT = os.environ.get("ARC_GLOVE_POINT_AT", "bend")   # (bend: the back of her elbow's bend; hand: ARC_GLOVE_POINT_ROT from the back of her hand)
    FL_TONGUE = float(os.environ.get("FL_TONGUE", "0.016" if _g1 else "0"))
    FL_TONGUE_W = float(os.environ.get("FL_TONGUE_W", "0.009"))   # (spec 0.011: a soft U on her curled finger, gsG1a)
    FL_TONGUE_R = float(os.environ.get("FL_TONGUE_R", "0.0025"))
    FL_V_R = float(os.environ.get("FL_V_R", "0.0025"))
    GLOVE_LOOP = tuple(float(v) for v in os.environ.get("GLOVE_LOOP", "0.0008,0.001,0.0023,0.0012" if _g1 else "0,0,0,0").split(","))
    GLOVE_POINTS = tuple(float(v) for v in os.environ.get("GLOVE_POINTS", "0.008,0.006,0.042,0.0055,0.0005" if _g1 else "0,0,0,0,0").split(","))
    # (G2: a laced V on the back of her forearm under the back of her hand, GLOVE_V (width at the top, where
    # its sides would meet, its foot's radius); eyelet rows GLOVE_EYES (m from the top) in wiregold rings
    # GLOVE_EYE (radius, wire r, in from the cut); laced in plum GLOVE_LACE_R, tied in a bow at the top,
    # GLOVE_BOW (loop length, loop height, tail length, aglet length, aglet r))
    GLOVE_V = tuple(float(v) for v in os.environ.get("GLOVE_V", "0.022,0.13,0.003" if _g2 else "0,0,0").split(","))
    # (where round her forearm: side, square to her elbow's hinge on the side the back of her hand faces
    # (the face seen with her elbow bent: gsG2a, laid on the back of her hand's line, it lay 30 deg from her
    # crook, edge-on in the fist); hand: on that line)
    GLOVE_V_AT = os.environ.get("GLOVE_V_AT", "hand")   # (gsG2b-d: side, far and face never faced the camera in the fist; hand showed best, in the idle)
    GLOVE_V_ROT = np.radians(float(os.environ.get("GLOVE_V_ROT", "60")))
    GLOVE_EYES = [float(v) for v in os.environ.get("GLOVE_EYES", "0.008,0.028,0.048,0.068,0.086").split(",")]
    GLOVE_EYE = tuple(float(v) for v in os.environ.get("GLOVE_EYE", "0.0015,0.00045,0.0026").split(","))
    GLOVE_LACE_R = float(os.environ.get("GLOVE_LACE_R", "0.0009"))
    GLOVE_LACE_CLEAR = float(os.environ.get("GLOVE_LACE_CLEAR", "0.0006"))   # (s25 gs2: a lace's surface off the built binding and sheet; at 0.4 mm two points stood 0.27 mm off, G2h)
    GLOVE_KNOT_SEAT = float(os.environ.get("GLOVE_KNOT_SEAT", "0.00075"))   # (s25 gs2: the knot's base off what is under it)
    GLOVE_BOW = tuple(float(v) for v in os.environ.get("GLOVE_BOW", "0.009,0.004,0.014,0.0035,0.0011").split(","))
    GLOVE_STYLE_FRAME, GLOVE_HAND = {}, {}

    def glove_arm_frame(sd):
        """(s24) Her forearm's frame for the styles: her elbow, the axis to her wrist, the back of her
        hand round it (d0), her pinky's side (pk) and her elbow's tip (el, ARC_GLOVE_POINT_ROT from d0)."""
        if sd in GLOVE_STYLE_FRAME:
            return GLOVE_STYLE_FRAME[sd]
        e_, w_ = ARM[sd][1], ARM[sd][2]
        ax_ = (w_ - e_) / np.linalg.norm(w_ - e_)
        hx = F1h(f"middle_02_{sd}") - F1h(f"hand_{sd}")
        hx /= np.linalg.norm(hx)
        sd_ = F1h(f"pinky_02_{sd}") - F1h(f"index_02_{sd}")
        sd_ -= hx * (sd_ @ hx)
        up = np.cross(hx, sd_)
        up *= -np.sign((F1h(f"thumb_03_{sd}") - F1h(f"index_02_{sd}")) @ up)
        d0 = up - ax_ * (up @ ax_)
        d0 /= np.linalg.norm(d0)
        pk = sd_ - ax_ * (sd_ @ ax_)
        pk -= d0 * (pk @ d0)
        pk /= np.linalg.norm(pk)
        el = np.cos(ARC_GLOVE_POINT_ROT) * d0 + np.sin(ARC_GLOVE_POINT_ROT) * pk
        bk = -(ARM[sd][0] - e_)
        bk -= ax_ * (bk @ ax_)
        bent_ = np.degrees(np.arccos(np.clip((e_ - ARM[sd][0]) @ ax_ / np.linalg.norm(e_ - ARM[sd][0]), -1, 1)))
        if ARC_GLOVE_POINT_AT == "bend" and bent_ > 8:
            # (s24 build gsG1a: the spec's line, 45 deg from the back of her hand toward her pinky, lay 105 deg
            # from the back of her elbow's bend (17 deg in the rest pose: a hinge, so its convex side is her
            # elbow's tip). The point and the crook taken from the bend itself.)
            el0_ = el
            el = bk / np.linalg.norm(bk)
            print("GLOVE %s style frame: the elbow's tip from her bend, %.0f deg round from the back of her hand (toward her pinky +)"
                  % (sd, np.degrees(np.arctan2(el @ pk, el @ d0))))
        print("GLOVE %s style frame: the point's line %.0f deg round from the back of her elbow's bend (her arm bent %.0f deg in the rest pose)"
              % (sd, np.degrees(np.arctan2(np.cross(el, bk) @ ax_, el @ bk)),
                 np.degrees(np.arccos(np.clip((e_ - ARM[sd][0]) @ ax_ / np.linalg.norm(e_ - ARM[sd][0]), -1, 1)))))
        GLOVE_STYLE_FRAME[sd] = (e_, ax_, d0, pk, el)
        return GLOVE_STYLE_FRAME[sd]

    def round_phi(q, e_, ax_, ref):
        r_ = q - e_
        r_ = r_ - np.outer(r_ @ ax_, ax_)
        return np.arctan2(r_ @ np.cross(ax_, ref), r_ @ ref), np.linalg.norm(r_, axis=1)

    def glove_v(q, sd, s):
        """(G2) The V's cut, positive in the cloth: its sides straight from GLOVE_V[0] wide at the top toward
        a point GLOVE_V[1] down, round at the foot (GLOVE_V[2]) where they touch its circle."""
        ph, rr = round_phi(q, *v_frame(sd))
        x = np.abs(ph) * rr
        hw0, L, ra = GLOVE_V
        al = np.arctan2(0.5 * hw0, L)
        yc = L - ra / np.sin(al)
        yt = yc - ra * np.sin(al)
        side = (x - 0.5 * hw0 * (1 - s / L)) * np.cos(al)
        circ = np.sqrt(x ** 2 + (s - yc) ** 2) - ra
        return np.where(s > yt, circ, side)

    def v_frame(sd):
        e_, ax_, d0, pk, el = glove_arm_frame(sd)
        if GLOVE_V_AT == "face":
            # (gsG2a-c: at 150, 90 and 270 deg round from her elbow's tip it lay at the top edge, the far
            # face and the top edge in the fist: the face the camera sees is about 300, GLOVE_V_ROT from
            # her elbow's tip toward "side")
            sf_ = -(d0 - el * (d0 @ el))
            sf_ = sf_ / np.linalg.norm(sf_)
            d0 = np.cos(GLOVE_V_ROT) * el + np.sin(GLOVE_V_ROT) * sf_
        elif GLOVE_V_AT in ("side", "far"):
            # (gsG2b: square to the hinge on the back of her hand's side it lay on the far face in the fist;
            # side: the other face, the one the camera sees with her elbow bent)
            d0 = (d0 - el * (d0 @ el)) * (-1.0 if GLOVE_V_AT == "side" else 1.0)
            d0 = d0 / np.linalg.norm(d0)
        return e_, ax_, d0

    def glove_style_cut(sd, off_):
        e_, ax_, d0, pk, el = glove_arm_frame(sd)
        def f(q):
            s = (q - e_) @ ax_ - off_
            pe, _ = round_phi(q, e_, ax_, el)
            t = s - GLOVE_CROOK * np.cos(0.5 * np.pi * np.clip((np.pi - np.abs(pe)) / GLOVE_CROOK_W, 0, 1)) ** 2
            if ARC_GLOVE_POINT > 0:
                rho = np.sqrt(pe ** 2 + ARC_GLOVE_POINT_TIP ** 2) - ARC_GLOVE_POINT_TIP
                t = t + ARC_GLOVE_POINT * np.clip(1 - rho / ARC_GLOVE_POINT_W, 0, None) ** 1.4
            if GLOVE_V[0] > 0:
                t = np.minimum(t, glove_v(q, sd, s))
            return t
        return f

    def glove_style_cords(sd):
        """(s24) A style's cords, laid on the glove as built (its SHEET) and on her skin: G1's ring and
        points; G2's eyelets, lacing and bow. Each laid by its height off her skin, stacked over what
        is under it (cloth, binding, a lace already laid) and eased along its way."""
        from scipy.ndimage import gaussian_filter1d
        nm = f"arcanist.glove_{sd}"
        if nm not in SHEET:
            return []
        sp_, st_, sw_, sth = SHEET[nm]
        # (s24 gsG2f: the eyelets and G1's points weighted from the glove's sheet, so they ride with it; what
        # crosses her skin (laces, bow) from her skin, which from the sheet came through a lace. gsG2a:  (the glove's
        # weights are eased, and its top refitted): from her skin the eyelets stood 3-4 mm off the binding
        # in the idle. Named under the glove, so glove_top_weights refits them with it.)
        wsrc_ = (sp_, np.asarray(sw_, float))
        sbvh = BVHTree.FromPolygons([tuple(p_) for p_ in sp_], st_.tolist())
        lift_c = FL_LIFT + FL_THICK
        def skin_ray(o, d):
            hit = SKIN_BVH.ray_cast(Vector(o), Vector(d), 0.2)
            if hit[0] is None:
                return None, None
            n = np.array(hit[1][:])
            return np.array(hit[0][:]), (n if n @ d < 0 else -n)
        def cloth_h(p_, n):
            # (the glove's outer face off her skin at p_, along n; 0 where there is none)
            co, nn, _, dist = sbvh.find_nearest(Vector(p_ + n * 0.001))
            if co is None or dist > 0.0025:
                return 0.0
            c_ = np.array(co[:]) - p_
            return float(c_ @ n + sth) if np.linalg.norm(c_ - n * (c_ @ n)) < 0.0008 else 0.0
        def eased(h, req, sig, closed=False):
            for _ in range(6):
                h = np.maximum(gaussian_filter1d(h, sig, mode="wrap" if closed else "nearest"), req)
            return gaussian_filter1d(h, 0.6, mode="wrap" if closed else "nearest")
        made_ = []
        H = GLOVE_HAND.get(sd)
        if H is not None and GLOVE_POINTS[2] > 0:
            a_, hx, side_, up_, lmid = H["a"], H["ax"], H["side"], H["up"], H["lmid"]
            g0, g1, ln, gap, tr = GLOVE_POINTS
            hs = []
            for k, kk in enumerate((-1, 0, 1)):
                t0 = float(H["line"](np.array([lmid + kk * g0]), np.array([1.0]), tongue=False)[0]) - gap
                pts, nrs, chs = [], [], []
                for t in np.linspace(0, 1, 90):
                    p_, n = skin_ray(a_ + side_ * (lmid + kk * (g0 + (g1 - g0) * t)) + hx * (t0 - ln * t) + up_ * 0.05, -up_)
                    if p_ is None:
                        continue
                    pts.append(p_); nrs.append(n); chs.append(cloth_h(p_, n))
                pts, nrs, chs = np.array(pts), np.array(nrs), np.array(chs)
                chs = gaussian_filter1d(np.maximum(chs, lift_c), 2.0, mode="nearest")
                end = np.minimum(np.arange(len(pts)), np.arange(len(pts))[::-1]) * (ln / max(len(pts) - 1, 1))
                h = chs + tr * (1.2 * np.clip(end / 0.0025, 0, 1) - 0.6)
                hs.append(float(np.median(chs)))
                made_ += cord(f"arcanist.glove_{sd}_point{'abc'[k]}", pts + nrs * h[:, None], "glovethread", r=tr, nv=8, src=wsrc_)
            print("GLOVE %s points: three, %.0f mm long, the glove's face %s mm off her under them" % (sd, ln * 1000, " ".join("%.2f" % (v * 1000) for v in hs)))
        if H is not None and GLOVE_LOOP[0] > 0:
            a_, hx, side_, up_, lmid = H["a"], H["ax"], H["side"], H["up"], H["lmid"]
            lr_, lp0, lp1, lb = GLOVE_LOOP
            fa, fb = F1h(f"middle_01_{sd}"), F1h(f"middle_02_{sd}")
            fx = (fb - fa) / np.linalg.norm(fb - fa)
            u = up_ - fx * (up_ @ fx)
            u /= np.linalg.norm(u)
            v = np.cross(fx, u)
            # (the tongue's tip as bound: the furthest edge point of the sheet over the back of her middle
            # finger (gsG1a: from the cut's own line the ring stood 6 mm past the binding, afloat))
            bd_ = np.unique(np.concatenate([lp_ for lp_ in edge_loops(st_)]))
            rel_ = sp_[bd_] - fa
            sb_ = rel_ @ fx
            on_ = (np.abs(rel_ @ v) < 0.004) & (rel_ @ u > 0) & (sb_ > -0.01) & (sb_ < 0.04)
            if on_.any():
                s_ring = float(sb_[on_].max()) - lb
            else:
                qt_tip = float(H["line"](np.array([lmid]), np.array([1.0]))[0])
                tip, _n = skin_ray(a_ + side_ * lmid + hx * qt_tip + up_ * 0.05, -up_)
                s_ring = (tip - fa) @ fx - lb
            fw = wsum(f"middle_01_{sd}", f"middle_02_{sd}", f"middle_03_{sd}")
            sl = (P - fa) @ fx
            rad = np.linalg.norm((P - fa) - np.outer(sl, fx), axis=1)
            for wd in (0.001, 0.0015, 0.0025, 0.004):
                m = (np.abs(sl - s_ring) < wd) & (fw > 0.5) & (rad < 0.015)
                if m.sum() >= 14:
                    break
            rel = P[m] - fa - np.outer(sl[m], fx)
            uv = np.stack([rel @ u, rel @ v], 1)
            c2 = uv.mean(0)
            th = np.arctan2(uv[:, 1] - c2[1], uv[:, 0] - c2[0])
            rd = np.linalg.norm(uv - c2, axis=1)
            basis = lambda a: np.stack([np.ones_like(a), np.cos(a), np.sin(a), np.cos(2 * a), np.sin(2 * a)], 1)
            coef = np.linalg.lstsq(basis(th), rd, rcond=None)[0]
            ph = np.linspace(0, 2 * np.pi, 96, endpoint=False)
            Rr = basis(ph) @ coef + lp0 + (lp1 - lp0) * ((1 + np.cos(ph)) / 2) ** 2
            ring = (fa + fx * s_ring + u * c2[0] + v * c2[1])[None] + (np.outer(np.cos(ph), u) + np.outer(np.sin(ph), v)) * Rr[:, None]
            made_ += cord(f"arcanist.glove_{sd}_loop", ring, "glovepipe", r=lr_, nv=8, closed=True)
            print("GLOVE %s loop: round her middle finger %.1f mm past its F1 head, %d skin points, section %.1f x %.1f mm"
                  % (sd, s_ring * 1000, int(m.sum()), 2 * (coef[0] + abs(coef[3])) * 1000, 2 * (coef[0] - abs(coef[3])) * 1000))
        if GLOVE_V[0] > 0:
            e_, ax_, d0 = v_frame(sd)
            off_ = float(os.environ.get("ARC_GLOVE_ELBOW", "0.04"))
            b0 = np.cross(ax_, d0)
            hw0, L, ra = GLOVE_V
            cutf = glove_style_cut(sd, off_)
            wpipe, hpipe, opipe = GLOVE_PIPE
            def arm_pt(s, x):
                c = e_ + ax_ * (off_ + s)
                p_, n = skin_ray(c + d0 * 0.06, -d0)
                R_ = np.linalg.norm((p_ - c) - ax_ * ((p_ - c) @ ax_)) if p_ is not None else 0.035
                # (the angle by her radius on its own side, as the cut measures it: her bone's axis lies
                # off her forearm's middle, and from the middle's radius one row of eyelets stood 3-4 mm
                # off its binding, gsG2a/e)
                for _ in range(4):
                    a = x / R_
                    d = np.cos(a) * d0 + np.sin(a) * b0
                    p_, n = skin_ray(c + d * 0.06, -d)
                    if p_ is None:
                        break
                    R_ = np.linalg.norm((p_ - c) - ax_ * ((p_ - c) @ ax_))
                if p_ is None:
                    co, nn, _, _ = SKIN_BVH.find_nearest(Vector(c + d * (R_ + 0.005)))
                    p_, n = np.array(co[:]), np.array(nn[:])
                return p_, n
            # (s25 gs2: the binding as built (its tubes, BIND_SIGMA-eased off the cut), for the laces:
            # over the cut's estimate one crossing lace dipped 3 mm into it, gsG2g)
            bobs_ = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(nm + "_bind")]
            bvb_ = None
            if bobs_:
                bv_, bt_, o_ = [], [], 0
                for o in bobs_:
                    bv_ += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
                    bt_ += [tuple(i + o_ for i in pl.vertices) for pl in o.data.polygons]
                    o_ += len(o.data.vertices)
                bvb_ = BVHTree.FromPolygons(bv_, bt_)
            def built_h(p_, n):
                # (the highest built face over p_ along n, binding or sheet, off her skin)
                h = 0.0
                for bvh_, add in ((bvb_, 0.0), (sbvh, sth)):
                    if bvh_ is None:
                        continue
                    hit = bvh_.ray_cast(Vector(p_ + n * 0.02), Vector(-n), 0.025)
                    if hit[0] is not None:
                        h = max(h, float((np.array(hit[0][:]) - p_) @ n) + add)
                return h
            def under(p_, n=None):
                # (what lies under a cord at p_, off her skin: the glove's face, its binding's crown)
                dd = float(cutf(p_[None])[0])
                h = lift_c if dd > 0 else 0.0
                cb = wpipe / 2 - opipe
                if -opipe < dd < wpipe - opipe:
                    h = max(h, FL_LIFT + FL_THICK / 2 + (FL_THICK / 2 + hpipe) * np.sqrt(max(0.0, 1 - ((dd - cb) / (wpipe / 2)) ** 2)))
                return h
            laid = []   # (points of the cords laid: 3D centre, r)
            def lay(name, sx, r, key, closed=False, base=0.00015, ends=None, sig=10.0, extra=None, wsrc=None):
                sx = np.asarray(sx, float)
                if not closed:
                    dd_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sx, axis=0), axis=1))]
                    t_ = np.linspace(0, dd_[-1], max(6, int(dd_[-1] / 0.0004) + 1))
                    sx = np.stack([np.interp(t_, dd_, sx[:, 0]), np.interp(t_, dd_, sx[:, 1])], 1)
                PN = [arm_pt(s, x) for s, x in sx]
                pp = np.array([a for a, b in PN])
                nn = np.array([b for a, b in PN])
                req = np.array([max(under(a), built_h(a, b) + GLOVE_LACE_CLEAR - base) if key == "glovepipe" else under(a) for a, b in zip(pp, nn)]) + r + base
                if laid:
                    lp = np.array([a for a, b in laid])
                    lr = np.array([b for a, b in laid])
                    tree_ = cKDTree(lp)
                    for i, (a, n) in enumerate(zip(pp, nn)):
                        if ends is not None and ((ends[0] is not None and i < 7) or (ends[1] is not None and i >= len(pp) - 7)):
                            continue
                        for j in tree_.query_ball_point(a + n * req[i], r + lr.max() + 0.0012):
                            rel_ = lp[j] - a
                            hj = rel_ @ n
                            lat = np.linalg.norm(rel_ - n * hj)
                            if lat < r + lr[j]:
                                req[i] = max(req[i], hj + np.sqrt((r + lr[j]) ** 2 - lat ** 2) + 0.0001)
                if extra is not None:
                    req = np.maximum(req, extra(np.arange(len(pp)), len(pp)))
                def at_ends(h):
                    if ends is None:
                        return h
                    k_ = np.arange(len(h))
                    for e_h, kk in zip(ends, (k_, k_[::-1])):
                        if e_h is not None:
                            w_ = np.clip(1 - kk / 3.0, 0, 1)
                            h = h * (1 - w_) + e_h * w_
                    return h
                req = at_ends(req)
                h = at_ends(eased(req.copy(), req, sig, closed))
                c3 = pp + nn * h[:, None]
                laid.extend(zip(c3, np.full(len(c3), r)))
                return cord(name, c3, key, r=r, nv=8, closed=closed, src=wsrc), c3
            lay_ = lambda *a, **k: lay(*a, **k)[0]
            hw = lambda s: 0.5 * hw0 * (1 - s / L)
            er, ewr, ein = GLOVE_EYE
            xs = [hw(s) + ein for s in GLOVE_EYES]
            # eyelets
            for i, s in enumerate(GLOVE_EYES):
                for sg in (1, -1):
                    t = np.linspace(0, 2 * np.pi, 40, endpoint=False)
                    made_ += lay_(f"arcanist.glove_{sd}_eye{i}{'ab'[sg > 0]}", np.stack([s + er * np.cos(t), sg * xs[i] + er * np.sin(t)], 1),
                                 ewr, "wiregold", closed=True, base=-0.4 * ewr, sig=2.0, wsrc=wsrc_)
            laid.clear()
            eye_end = lift_c + 0.3 * GLOVE_LACE_R   # (a lace's end, into its eyelet)
            lr_ = GLOVE_LACE_R
            ne = len(GLOVE_EYES)
            # the foot bar, then each pair's crossing (the under lace first), the top laces to the knot
            made_ += lay_(f"arcanist.glove_{sd}_lace_foot", [(GLOVE_EYES[-1], xs[-1]), (GLOVE_EYES[-1], -xs[-1])], lr_, "glovepipe", ends=(eye_end, eye_end))
            for i in range(ne - 1, 0, -1):
                over = 1 if i % 2 == 0 else -1
                for sg in (-over, over):
                    made_ += lay_(f"arcanist.glove_{sd}_lace{i}{'ab'[sg > 0]}", [(GLOVE_EYES[i], sg * xs[i]), (GLOVE_EYES[i - 1], -sg * xs[i - 1])],
                                 lr_, "glovepipe", ends=(eye_end, eye_end))
            bl, bh, tl, al_, ar_ = GLOVE_BOW
            s_k = GLOVE_EYES[0] - 0.0045
            kp, kn = arm_pt(s_k, 0.0)
            # (s25 gs2: the knot seated, its base GLOVE_KNOT_SEAT off what is under it (it stood 4.4 mm off
            # her on the laces' stack, gsG2g), the top laces' ends inside it, loops and tails from its rim)
            hb_ = max(under(kp), built_h(kp, kn)) + GLOVE_KNOT_SEAT
            for sg in (1, -1):
                made_ += lay_(f"arcanist.glove_{sd}_lace_top{'ab'[sg > 0]}", [(GLOVE_EYES[0], sg * xs[0]), (s_k, sg * 0.0006)], lr_, "glovepipe", ends=(eye_end, hb_ + 0.0003))
            hk = hb_ + 0.0008   # (the knot dome's base at hk - 0.8 mm = hb_)
            for sg in (1, -1):
                t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
                lp_ = np.stack([s_k - 0.5 * bh * np.sin(t) + 0.0006 * (1 - np.cos(t)), sg * 0.5 * bl * (1 - np.cos(t))], 1)
                made_ += lay_(f"arcanist.glove_{sd}_bow{'ab'[sg > 0]}", lp_, lr_, "glovepipe", closed=True,
                             extra=lambda i, n: hk + 0.0004 * (1 - np.cos(2 * np.pi * i / n)), sig=3.0)
            for sg in (1, -1):
                t = np.linspace(0, 1, 40)
                tail = np.stack([s_k + 0.0015 + tl * t, sg * (0.0012 + 0.004 * t + 0.0006 * np.sin(6 * t))], 1)
                to_, tc3 = lay(f"arcanist.glove_{sd}_tail{'ab'[sg > 0]}", tail, lr_, "glovepipe",
                               extra=lambda i, n: hk * np.clip(1 - i / 8.0, 0, 1), sig=3.0)
                ka = int(len(tc3) * (1 - al_ / tl))
                made_ += to_ + cord(f"arcanist.glove_{sd}_aglet{'ab'[sg > 0]}", tc3[ka:], "wiregold", r=ar_, nv=10)
                tg_ = tc3[-1] - tc3[-2]
                for o_ in domes(f"arcanist.glove_{sd}_aglettip{'ab'[sg > 0]}", [tc3[-1]], [tg_ / np.linalg.norm(tg_)], "wiregold", r=ar_):
                    o_["hides"] = False
                    made_.append(o_)
            for o_ in domes(f"arcanist.glove_{sd}_knot", [kp + kn * (hk - 0.0008)], [kn], "glovepipe", r=0.0019):
                o_["hides"] = False
                made_.append(o_)
            print("GLOVE %s V: %.0f mm wide at the top, its foot %.0f mm down; %d eyelet pairs, %d crossings, the bow's knot's base %.2f mm off what is under it"
                  % (sd, hw0 * 1000, (L - ra / np.sin(np.arctan2(0.5 * hw0, L)) + ra) * 1000, ne, ne - 1, GLOVE_KNOT_SEAT * 1000))
            # (the gate: every lace point GLOVE_LACE_CLEAR off every binding tube and the sheet, bar the
            # eyelet ends, which go into their rings)
            if bvb_ is not None:
                worst_ = []
                for o in made_:
                    if "_lace" not in o.name and "_tail" not in o.name and "_bow" not in o.name:
                        continue
                    for v in o.data.vertices:
                        q_ = o.matrix_world @ v.co
                        co, nrm_, _, dist = bvb_.find_nearest(q_)
                        if co is None:
                            continue
                        e_d = min(np.linalg.norm(np.array(q_[:]) - arm_pt(s, sg_ * xs[i])[0]) for i, s in enumerate(GLOVE_EYES) for sg_ in (1, -1)) if dist < 0.0006 else 1.0
                        if e_d < er + 0.0005:
                            continue
                        worst_.append(dist if (np.array(q_[:]) - np.array(co[:])) @ np.array(nrm_[:]) > 0 else -dist)
                print("GLOVE %s laces off the built binding: nearest %.2f mm (%d lace surface points under 0.3 mm)" % (sd, min(worst_) * 1000, int((np.array(worst_) < 0.0003).sum())))
        return made_

    def knuckle_cut(sd):
        """(s20, ARC_HANDS=fingerless: the owner's "cut off at the fingers sexily")
        Her hand to FL_CUT past each knuckle (the thumb FL_CUT_THUMB past its
        middle joint), and over the back of her middle finger a point FL_POINT
        further, FL_POINT_W wide at its root. Eased by each finger's weight, so
        the line runs smoothly through the webs between them."""
        f_ = np.ones(len(P))
        a_ = F1h(f"middle_01_{sd}")
        ax_ = F1h(f"middle_02_{sd}") - a_
        ax_ /= np.linalg.norm(ax_)
        side_ = F1h(f"pinky_01_{sd}") - F1h(f"index_01_{sd}")
        side_ -= ax_ * (side_ @ ax_)
        side_ /= np.linalg.norm(side_)
        up_ = np.cross(ax_, side_)
        # (the back of her hand: away from her thumb, which lies before her palm)
        up_ *= -np.sign((F1h(f"thumb_03_{sd}") - F1h(f"index_01_{sd}")) @ up_)
        for fg in ("index", "middle", "ring", "pinky", "thumb"):
            bs = [f"{fg}_0{i}_{sd}" for i in ((2, 3) if fg == "thumb" else (1, 2, 3))]
            if not all(n in BI for n in bs):
                continue
            a = F1h(bs[0])
            ax = F1h(bs[1]) - a
            ax /= np.linalg.norm(ax)
            s = (P - a) @ ax
            cut = (FL_CUT_THUMB if fg == "thumb" else FL_CUT) + (FL_FIELD_OVER if FL_EXACT else 0.0)
            if fg == "middle" and FL_EXACT and FL_TONGUE > 0:
                cut = cut + FL_TONGUE   # (s24 G1: the field past the tongue, so the exact line decides)
            if fg == "middle" and not FL_EXACT:
                lat = np.abs((P - a) @ side_)
                cut = cut + FL_POINT * np.clip(1 - lat / FL_POINT_W, 0, 1) * ((P - a) @ up_ > 0)
            wf = np.clip(wsum(*bs), 0, 1)
            f_ = np.minimum(f_, (1 - wf) * 0.05 + wf * (cut - s))
        return f_

    # (s23, judge gl1: the knuckle cut, jagged, a tooth of cloth in every web and half
    # of each first finger covered: now cut exactly (FL_EXACT), one smooth line across
    # her hand FL_WEB_GAP short of the webs between her fingers (found on her skin, not
    # from her bones, which a later body build moves), so no cloth bridges them; over
    # the back of her hand the line falls FL_V back toward her wrist at its sides, a
    # point at her middle knuckle; her thumb cut FL_CUT_THUMB past its middle joint.
    # knuckle_cut's field then stands FL_FIELD_OVER past it, so the exact line decides.)
    FL_EXACT = os.environ.get("FL_EXACT", "1") == "1"
    FL_FIELD_OVER = float(os.environ.get("FL_FIELD_OVER", "0.008"))
    FL_WEB_GAP = float(os.environ.get("FL_WEB_GAP", "0.002"))
    FL_V = float(os.environ.get("FL_V", {"G1": "0.012", "G2": "0.011"}.get(GLOVE_STYLE, "0.008")))
    FL_P1 = [float(x) for x in os.environ.get("FL_P1", "0.0232,0.0269,0.0267,0.0211").split(",")]
    # (s27 glove round 2, judge gl r1: a white tooth where the cut met her index knuckle and the piping hooked
    # there and at the pinky end. FL_DORS "offset,width" of the band the V eases in over, back of the hand to
    # palm (was 4,8 mm); FL_THUMB_BLEND "lo,hi" her thumb's weight over which the thumb cut's field blends into
    # the knuckle cut's (was a hard switch at 0.5, a step in the field; "0,0" = as before))
    FL_DORS = [float(x) for x in os.environ.get("FL_DORS", "0.004,0.008").split(",")]
    FL_THUMB_BLEND = [float(x) for x in os.environ.get("FL_THUMB_BLEND", "0,0").split(",")]
    def knuckle_exact(sd):
        # (her frame from her wrist and her middle joints (02), which a body build's
        # knuckle move leaves where they are; each finger's knot FL_P1 (her F1 rig's first
        # bones, the right hand's, measured: their 01 heads sat at her webs) short of its
        # 02 joint, less FL_WEB_GAP)
        a_ = F1h(f"hand_{sd}")
        ax_ = F1h(f"middle_02_{sd}") - a_
        ax_ /= np.linalg.norm(ax_)
        side_ = F1h(f"pinky_02_{sd}") - F1h(f"index_02_{sd}")
        side_ -= ax_ * (side_ @ ax_)
        side_ /= np.linalg.norm(side_)
        up_ = np.cross(ax_, side_)
        up_ *= -np.sign((F1h(f"thumb_03_{sd}") - F1h(f"index_02_{sd}")) @ up_)
        F4 = ("index", "middle", "ring", "pinky")
        # (s24: across her hand by F1's knuckles, FL_P1 short of each 02 joint along its first bone)
        k1 = [F1h(f"{f}_02_{sd}") - FL_P1[k] * (F1h(f"{f}_02_{sd}") - F1h(f"{f}_01_{sd}"))
              / np.linalg.norm(F1h(f"{f}_02_{sd}") - F1h(f"{f}_01_{sd}")) for k, f in enumerate(F4)]
        fl = [(k1[k] - a_) @ side_ for k in range(4)]
        knots_t = [(F1h(f"{f}_02_{sd}") - a_) @ ax_ - FL_P1[k] - FL_WEB_GAP for k, f in enumerate(F4)]
        o = np.argsort(fl); knots_l = np.array(fl)[o]; knots_t = np.array(knots_t)[o]
        lmid, half = fl[1], 0.5 * abs(fl[3] - fl[0]) + 0.006
        print("GLOVE %s knuckle line: %s mm from her wrist" % (sd, " ".join("%.1f" % (t_ * 1000) for t_ in knots_t)))
        ta_ = F1h(f"thumb_02_{sd}")
        tx_ = F1h(f"thumb_03_{sd}") - ta_
        tx_ /= np.linalg.norm(tx_)
        wth = np.clip(wsum(f"thumb_02_{sd}", f"thumb_03_{sd}"), 0, 1)
        tree = cKDTree(P)
        if GLOVE_STYLE:
            # (s24, a style's line: through the knots eased (PCHIP, no corner at each), its V's point at her
            # middle knuckle FL_V_R round, and G1's tongue; kept in GLOVE_HAND for the style's cords)
            from scipy.interpolate import PchipInterpolator
            pch_ = PchipInterpolator(knots_l, knots_t)
            base_ = lambda ql: pch_(np.clip(ql, knots_l[0], knots_l[-1]))
        else:
            base_ = lambda ql: np.interp(ql, knots_l, knots_t)
        def line_at(ql, qu, tongue=True):
            line = base_(ql)
            dors = np.clip((qu + FL_DORS[0]) / FL_DORS[1], 0, 1)
            dors = dors * dors * (3 - 2 * dors)
            dl = np.sqrt((ql - lmid) ** 2 + FL_V_R ** 2) - FL_V_R if GLOVE_STYLE else np.abs(ql - lmid)
            line = line - FL_V * dors * np.clip(dl / half, 0, 1)
            if tongue and FL_TONGUE > 0:
                rho = np.sqrt((ql - lmid) ** 2 + FL_TONGUE_R ** 2) - FL_TONGUE_R
                line = line + FL_TONGUE * dors * np.clip(1 - rho / FL_TONGUE_W, 0, None) ** 1.6
            return line
        GLOVE_HAND[sd] = dict(a=a_, ax=ax_, side=side_, up=up_, lmid=lmid, half=half, line=line_at)
        def f(q):
            ql, qt, qu = (q - a_) @ side_, (q - a_) @ ax_, (q - a_) @ up_
            line = line_at(ql, qu)
            c = line - qt
            _, j = tree.query(q)
            th = FL_CUT_THUMB - (q - ta_) @ tx_
            if os.environ.get("FL_FDUMP"):
                # (debug: the cut's inputs, for study offline)
                np.savez(os.path.join(os.environ["FL_FDUMP"], "kx_%s.npz" % sd), q=q, ql=ql, qt=qt, qu=qu, c=c, th=th, wthj=wth[j],
                         P=P, TRI=TRI, wth=wth, a=a_, ax=ax_, side=side_, up=up_, ta=ta_, tx=tx_, kl=knots_l, kt=knots_t,
                         lmid=lmid, half=half, prm=np.array([FL_V, FL_V_R, FL_TONGUE, FL_TONGUE_R, FL_TONGUE_W, FL_CUT_THUMB] + list(FL_DORS)))
            if FL_THUMB_BLEND[1] > FL_THUMB_BLEND[0]:
                s_ = np.clip((wth[j] - FL_THUMB_BLEND[0]) / (FL_THUMB_BLEND[1] - FL_THUMB_BLEND[0]), 0, 1)
                s_ = s_ * s_ * (3 - 2 * s_)
                return c * (1 - s_) + th * s_
            return np.where(wth[j] > 0.5, th, c)
        return f

    # (s21: the elbow glove's top cut exactly, square across her forearm, ARC_GLOVE_ELBOW below her
    # elbow joint (her skin's field a little wider there, so this line decides), and hemmed: a
    # GLOVE_HEM binding in the glove's own cloth round every edge; GLOVE_SOFTEN/GLOVE_SMOOTH: the
    # second skin eased over her skin's facets)
    GLOVE_HEM = float(os.environ.get("GLOVE_HEM", "0.0035"))
    GLOVE_SOFTEN = int(os.environ.get("GLOVE_SOFTEN", "24"))
    GLOVE_SMOOTH = int(os.environ.get("GLOVE_SMOOTH", "6"))
    # (s26 solver gs5, judge hip l30: with her thumb spread (hand on hip, thumb_in 70) the thumb hole's web side
    # sank 2.2 mm into her and the knuckle edge at the web stood off as a white point: the sheet's weights, eased
    # over 8 mm (eased_weights), had carried her hand's share up the 8 mm thumb sleeve (hand 0.06, thumb_01 0.13
    # where her skin has none) and her thumb's down onto the web's knuckle edge (thumb_02 0.07 vs 0.01), and with
    # her thumb turned 70 deg at its root each point went 4-6 mm off the skin it sits on. Now the glove's hand
    # part takes her skin's own blend at its nearest point (barycentric: as smooth as her skin's), full where her
    # hand and fingers carry GLOVE_HAND_EXACT[1] of it, none under [0] (her wrist keeps the eased blend). "0": as before.)
    GLOVE_HAND_EXACT = tuple(float(v) for v in os.environ.get("GLOVE_HAND_EXACT", "0.5,0.9").split(","))
    _hand_cols = np.array([n.split("_")[0] in ("hand", "thumb", "index", "middle", "ring", "pinky") for n in BONES])
    def glove_hand_exact(pos, wt):
        if len(GLOVE_HAND_EXACT) < 2:
            return wt
        sx = np.zeros_like(wt)
        for i, q in enumerate(pos):
            co, _n, fi, _d = BVH.find_nearest(Vector(q))
            if co is None:
                sx[i] = wt[i]
                continue
            a_, b_, c_ = P[TRI[fi]]
            v0, v1, v2 = b_ - a_, c_ - a_, np.array(co[:]) - a_
            d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
            den = max(d00 * d11 - d01 * d01, 1e-18)
            bv = (d11 * d20 - d01 * d21) / den
            bw = (d00 * d21 - d01 * d20) / den
            bc = np.clip(np.array([1 - bv - bw, bv, bw]), 0, 1)
            sx[i] = bc @ W[TRI[fi]] / max(bc.sum(), 1e-9)
        k = np.clip((sx[:, _hand_cols].sum(1) - GLOVE_HAND_EXACT[0]) / (GLOVE_HAND_EXACT[1] - GLOVE_HAND_EXACT[0]), 0, 1)
        k = (k * k * (3 - 2 * k))[:, None]
        out_ = wt * (1 - k) + sx * k
        print("GLOVE hand exact: %d points on her skin's own blend, %d eased into it (moved L1 up to %.2f, mean %.3f)"
              % (int((k[:, 0] > 0.999).sum()), int(((k[:, 0] > 0) & (k[:, 0] <= 0.999)).sum()),
                 np.abs(out_ - wt).sum(1).max(), np.abs(out_ - wt).sum(1).mean()))
        return out_
    def glove_top_cut(sd):
        e_, w_ = ARM[sd][1], ARM[sd][2]
        ax_ = (w_ - e_) / np.linalg.norm(w_ - e_)
        off_ = float(os.environ.get("ARC_GLOVE_ELBOW", "0.04"))
        if GLOVE_STYLE:
            return glove_style_cut(sd, off_)
        return lambda q: (q - e_) @ ax_ - off_

    # (s23 solver: the full glove (ARC_HANDS=glove) at elbow length takes the fingerless glove's
    # top: the exact cut above, its field GLOVE_FIELD_OVER past it so only the cut decides (at 2 cm
    # her coarse arm field dipped 3-4 mm under the cut in places, a notch in the edge), and its
    # leather eased from its 1.2 mm lift down to GLOVE_A_TOP_LIFT over the last GLOVE_A_TOP_EASE,
    # so its edge sits on her as the fingerless glove's does, not 2 mm proud with her skin
    # through it)
    GLOVE_FIELD_OVER = float(os.environ.get("GLOVE_FIELD_OVER", "0.04"))
    GLOVE_A_TOP_LIFT = float(os.environ.get("GLOVE_A_TOP_LIFT", "0.0005"))
    GLOVE_A_TOP_EASE = float(os.environ.get("GLOVE_A_TOP_EASE", "0.02"))
    def glove_a_lift(q, sd):
        if not ARC_CAPS:
            return np.full(len(q), 0.0012)
        return 0.0012 - (0.0012 - GLOVE_A_TOP_LIFT) * (1 - ramp(glove_top_cut(sd)(q), 0.0, GLOVE_A_TOP_EASE))

    def glove_top_k(pos, sd):
        k = np.clip(1 - (ARM_S[sd][skin_kd.query(pos)[1]] - (WRIST_S - GLOVE_TOP)) / 0.015, 0, 1)
        return k * k * (3 - 2 * k)

    def glove_shape(pos, tris, sd):
        nb = skin_kd.query(pos)[1]
        nor = vertex_normals(pos, tris)
        sgn = 1.0 if (nor * N[nb]).sum(1).mean() > 0 else -1.0
        from scipy.spatial import ConvexHull
        A_ = adjacency(len(pos), tris)
        p0 = pos.copy()
        x = pos.copy()
        nfill = 0
        for fg, bs, tip, r0, r1 in glove_tips(sd):
            d = np.linalg.norm(p0 - tip, axis=1)
            own = W[nb][:, bs].sum(1) > 0.5
            m = own & (d < r1 + GLOVE_TIP_HULL)
            if m.sum() < 20:
                continue
            # (the hull of the sheet there and of her fingertip lifted 1.2 mm)
            sk = (W[:, bs].sum(1) > 0.5) & (np.linalg.norm(P - tip, axis=1) < r1 + GLOVE_TIP_HULL)
            hp = np.vstack([p0[m], P[sk] + N[sk] * 0.0012])
            h = ConvexHull(hp)
            hb = BVHTree.FromPolygons([tuple(q) for q in hp], h.simplices.tolist())
            k = np.clip((r1 - d) / (r1 - r0), 0, 1)
            k = np.where(own, k * k * (3 - 2 * k), 0.0)
            idx = np.where(k > 0)[0]
            # (each point held to where it first lands on the hull by 1 -
            # GLOVE_TIP_RELAX of each step: the fold opens, and the cap's
            # points slide no further than a few of their spacings)
            h0 = p0.copy()
            for i in idx:
                q = hb.find_nearest(Vector(p0[i]))[0]
                if q is not None:
                    h0[i] = np.array(q[:])
            for _ in range(GLOVE_TIP_ROUNDS):
                av = (1 - GLOVE_TIP_RELAX) * h0 + GLOVE_TIP_RELAX * (A_ @ x)
                for i in idx:
                    q = hb.find_nearest(Vector(av[i]))[0]
                    if q is not None:
                        x[i] = p0[i] * (1 - k[i]) + np.array(q[:]) * k[i]
            nfill += len(idx)
        # (then rounded: a hull is flat between its points, and its ridges,
        # up to 42 deg at the index tip (fin1), showed as corners in the
        # outline. Taubin's rounds weighted by the cap; any point that comes
        # nearer her than GLOVE_TIP_FLOOR put back out along her normal.)
        kc = glove_tip_k(p0, sd)
        # (and GLOVE_TIP_FAIR rings past it, fading: the cap's edge stood as a
        # kink, up to 59 deg at 15-21 mm from the pinky's tip, fin1)
        for _ in range(GLOVE_TIP_FAIR):
            kc = np.maximum(kc, 0.75 * (A_ @ kc))
        for _ in range(GLOVE_TIP_TAUBIN):
            for lam in (0.5, -0.53):
                x = x + (lam * kc)[:, None] * (A_ @ x - x)
        nlift = 0
        for i in np.where(kc > 0)[0]:
            co, nn, _f, _d = BVH.find_nearest(Vector(x[i]))
            if co is None:
                continue
            short = GLOVE_TIP_FLOOR - float(np.dot(x[i] - np.array(co[:]), np.array(nn[:])))
            if short > 0:
                x[i] = x[i] + np.array(nn[:]) * short
                nlift += 1
        mv = np.linalg.norm(x - p0, axis=1)
        kt = glove_top_k(x, sd)
        pos = x - sgn * vertex_normals(x, tris) * (GLOVE_SINK * kt)[:, None]
        print("GLOVE %s: fingertips relaxed over their hulls, %d points (moved up to %.2f mm, %d over 0.3 mm); top %d points sunk %.1f mm"
              % (sd, nfill, mv.max() * 1000, int((mv > 0.0003).sum()), int((kt > 0.5).sum()), GLOVE_SINK * 1000))
        print("GLOVE %s: caps (mm) %s; %d Taubin rounds, %d points held out to %.1f mm"
              % (sd, " ".join("%s %.1f-%.1f" % (fg, r0 * 1000, r1 * 1000) for fg, bs, tip, r0, r1 in glove_tips(sd)), GLOVE_TIP_TAUBIN, nlift, GLOVE_TIP_FLOOR * 1000))
        return pos
    # (LEO_ONE, route (a): what the sheet keeps of her under the crotch (taken as it is,
    # then cut by exact's leg lines and back end), and there laid LEO_ONE_LIFT off her
    # from the skin it was cut from (eased as the gusset was), not lifted 3.5 mm and
    # ironed (an arch so narrow sagged into the slot))
    def one_zone(q):
        z_ = q[:, 2]
        return (np.maximum(ramp(-z_, -(CROTCH + LEO_ONE_LAY[0]), -(CROTCH + LEO_ONE_LAY[1])), ramp(q[:, 1], CROTCH_Y, CROTCH_Y + 0.01))
                * ramp(-np.abs(q[:, 0]), -0.05, -0.04) * ramp(-z_, -(CROTCH + 0.06), -(CROTCH + 0.05)))
    # (in front of the slot, where LEO_ONE_DEPTH's line decides, kept down its walls
    # whatever their slope: cut there by |N_x| too, the walls' patches of steeper skin
    # tore the sheet at the line into flecks (dry one5); eased 3 rounds, no jag)
    one_keep = smooth_field(AND(0.03 - np.abs(X), (LEO_ONE_STEEP + (0.999 - LEO_ONE_STEEP) * float(LEO_ONE_DEPTH > 0) * (1 - ramp(Y, CROTCH_Y - 0.012, CROTCH_Y + 0.004)) - np.abs(N[:, 0])) * 0.02,
                                (y_end1 + 0.006) - Y, Z - (CROTCH - 0.015), (CROTCH + 0.04) - Z), 3) if LEO_ONE else None
    def slot_bridged(q):
        # (s18 leo3, LEO_BRIDGE: see its knob)
        if LEO_BRIDGE <= 0:
            return q
        from scipy.ndimage import gaussian_filter1d
        x_, y_, z_ = q[:, 0], q[:, 1], q[:, 2]
        a0, a1, b0, b1 = LEO_BRIDGE_Y
        wy = ramp(y_, CROTCH_Y + a0, CROTCH_Y + a1) * (1 - ramp(y_, CROTCH_Y + b0, CROTCH_Y + b1))
        inz = (wy > 0) & (np.abs(x_) < 0.03) & (z_ < CROTCH + 0.015)
        if not inz.any():
            return q
        yb = np.arange(CROTCH_Y + a0 - 0.002, CROTCH_Y + b1 + 0.0021, 0.001)
        bi = np.clip(np.round((y_ - yb[0]) / 0.001).astype(int), 0, len(yb) - 1)
        def per_bin(m_, f_):
            zb = np.full(len(yb), np.nan)
            for b_ in np.unique(bi[m_]):
                zb[b_] = f_(z_[m_ & (bi == b_)])
            ok = ~np.isnan(zb)
            return gaussian_filter1d(np.interp(np.arange(len(yb)), np.nonzero(ok)[0], zb[ok]), 2.0, mode="nearest")
        zl, zr = per_bin(inz & (x_ < -0.001), np.min), per_bin(inz & (x_ > 0.001), np.min)
        # (never under the line exact() cuts the walls at: the span laid just above it)
        fl_ = np.interp(yb, roof_ys, roof_zs) - LEO_ONE_DEPTH - 0.012 * ramp(yb, CROTCH_Y - 0.02, CROTCH_Y + 0.02)
        if LEO_SLOT_CAP > 0:
            w2_ = ramp(yb, CROTCH_Y - 0.02, CROTCH_Y - 0.008) * (1 - ramp(yb, CROTCH_Y + LEO_SLOT_BACK, CROTCH_Y + LEO_SLOT_BACK + 0.012))
            fl_ = fl_ + w2_ * np.maximum(np.interp(yb, roof_ys, roof_zs) - LEO_SLOT_CAP - fl_, 0.0)
        zl, zr = np.maximum(zl, fl_ + 0.0006), np.maximum(zr, fl_ + 0.0006)
        zc = per_bin(inz & (np.abs(x_) < 0.0015), np.max)
        zep = zl[bi] + (zr[bi] - zl[bi]) * ramp(x_, -0.004, 0.004)
        H = np.maximum(zc[bi] - zep, 1e-4)
        h = z_ - zep
        zt = zep + np.maximum(h, 0) * np.minimum(LEO_BRIDGE / H, 1.0) + np.minimum(h, 0)
        # (LEO_BRIDGE_SAG: its middle that much lower than over its leg lines, so seen from the front its foot is round, not flat)
        zt = zt - LEO_BRIDGE_SAG * np.clip(1 - (x_ / 0.008) ** 2, 0, 1) * np.clip(h / 0.003, 0, 1)
        out = q.copy()
        out[:, 2] = np.where(inz, z_ + wy * (zt - z_), z_)
        mv = np.abs(out[:, 2] - z_)
        print("LEO_BRIDGE: the slot spanned %.1f mm over its leg lines, %d points lowered up to %.1f mm" % (LEO_BRIDGE * 1000, int((mv > 0.0002).sum()), mv.max() * 1000))
        np.savez(os.path.join(os.environ.get("TEMP", "."), "bridge.npz"), yb=yb, zl=zl, zr=zr, zc=zc)
        return out
    def crotch_lay(pos, tris):
        src, ns = PIECE_SRC["arcanist.corset"]
        w_ = one_zone(src)[:, None]
        laid = slot_bridged(relax(src + ns * LEO_ONE_LIFT, tris, interior=2, edge=30))
        print("LEO_ONE: %d points laid %.1f mm off her under the crotch" % (int((w_ > 0.5).sum()), LEO_ONE_LIFT * 1000))
        return pos * (1 - w_) + laid * w_
    def one_clear(q):
        return 0.0035 - (0.0035 - LEO_ONE_LIFT) * one_zone(q)
    if LEO_ONE:
        TUCK_ZONES["arcanist"] = [(LEO_ONE_TUCK, one_zone)]
    out = [
        # (opening into the gusset at its foot, as the warden's does)
        *ribbon("arcanist.thong", back_string(CROTCH + 0.155, CROTCH + 0.012), 0.016, "plumleather", lift=0.003, thick=0.003,
               trim=gold(0.004), snap=False, hides=True, flare=(0.034, 0.03)),
        *piece("arcanist.corset", corset, "plumleather", lift=corset_lift if ARC_CAPS else 0.0035, smooth=8, iron=60, trim=gold(0.008), keep_off=("Head",), filled=True, edge=120, soften=80,
               bridge=True, cut=exact, stiff=[(0.03, front_panel), (0.03, collar), plunge_fold, taut_gore, plunge_rim] + ([crotch_lay] if LEO_ONE else []),
               crotch=one_keep, clear=one_clear if LEO_ONE else None,
               hold=None if not LEO_HOLD else (lambda q: (q[:, 2] > CROTCH + LEO_HOLD_Z[0]) & (q[:, 2] < 1.2) & (np.abs(q[:, 0]) < 0.3), lambda q: ramp(q[:, 2], CROTCH + LEO_HOLD_Z[1], CROTCH + LEO_HOLD_Z[2]) * (1 - LEO_UH * on_gusset(q)))),
        *(down_tube() if PLUNGE_TRIM == "down" else []),
        *(plunge_clasp() if PLUNGE_CLASP else []),
        # (judge 4: the front read as moulded latex. Four stitched boning
        # channels, as a corset's front is made, from under her cups to
        # her hips, raised on the suit and moving with it.)
        *[o for k, x in enumerate((-0.088, -0.044, 0.044, 0.088))
          for o in ribbon(f"arcanist.boning{'abcd'[k]}",
                          [np.array([x + (x * 0.82 - x) * t, 0.0, (UNDERBUST - 0.024) + (1.03 - UNDERBUST + 0.024) * t]) for t in np.linspace(0, 1, 7)],
                          0.012, "plumleather", lift=0.0002, thick=0.0007, onto="arcanist.corset",
                          taper=BONING_TAPER or None)],
        # (the choker is cut, armor 9, 21 Oct: its mask (neck weight over 0.4 with Head under 0.3) only ever held a
        # fragment at the back of her neck since the neck seam, which showed at the close-up as a dark comma behind her
        # right shoulder; a full ring, if wanted, is an outfits item)
        *witch_hat("arcanist.hat", "plumleather", "darkpurple"),
    ]
    for sd in "lr":
        if GLOVE_STYLE:
            GLOVE_TOP_D[sd] = glove_top_cut(sd)
            BIND_SIGMA[f"arcanist.glove_{sd}"] = GLOVE_BIND_SIGMA
            BIND_MINLOOP[f"arcanist.glove_{sd}"] = 0.03
            if GLOVE_STYLE in ("G1", "G2"):
                BIND_SPEC[f"arcanist.glove_{sd}"] = ("glovepipe",) + GLOVE_PIPE
                if GLOVE_PIPE_TOP[0] > 0:
                    BIND_TOP[f"arcanist.glove_{sd}"] = (ARM[sd][1], GLOVE_PIPE_TOP)
        out += [
            *(piece(f"arcanist.glove_{sd}", limb(sd, WRIST_S - GLOVE_TOP - (GLOVE_FIELD_OVER if ARC_CAPS else 0.0), 9.9, legs=False), "blackleather",
                    lift=(lambda q, sd=sd: glove_a_lift(q, sd)) if ARC_CAPS else 0.0012, thick=0.001, bevel=0.0004, trim=gold(0.008), edge=30, soften=12,
                    cut=glove_top_cut(sd) if ARC_CAPS else None,
                    stiff=[lambda q, t_, sd=sd: glove_shape(q, t_, sd)],
                    clear=(lambda q, sd=sd: glove_a_lift(q, sd) - (0.0012 - GLOVE_TIP_CLEAR) * glove_tip_k(q, sd)) if ARC_CAPS else
                          (lambda q, sd=sd: 0.0012 - GLOVE_SINK * glove_top_k(q, sd) - (0.0012 - GLOVE_TIP_CLEAR) * glove_tip_k(q, sd)))
              if ARC_HANDS == "glove" else
              piece(f"arcanist.glove_{sd}", AND(limb(sd, WRIST_S - GLOVE_TOP - (GLOVE_FIELD_OVER if ARC_CAPS else 0.0), 9.9, legs=False), knuckle_cut(sd)), ARC_GLOVE_MAT, lift=FL_LIFT, thick=FL_THICK, bevel=0.0003, edge=30,
                    soften=GLOVE_SOFTEN, smooth=GLOVE_SMOOTH,
                    cut=(lambda q, sd=sd, tc=glove_top_cut(sd) if ARC_CAPS else None, kc=knuckle_exact(sd) if FL_EXACT else None:
                         (np.minimum(tc(q), kc(q)) if kc is not None else tc(q)) if tc is not None else kc(q))
                        if (ARC_CAPS or FL_EXACT) else None,
                    trim=(("glovepipe", GLOVE_PIPE[0], 0.0003, 0.0008) if GLOVE_STYLE in ("G1", "G2") else (ARC_GLOVE_MAT, GLOVE_HEM, 0.0003, 0.0008)) if GLOVE_HEM > 0 else None,
                    clear=lambda q, sd=sd: FL_LIFT - (0.0 if ARC_CAPS else GLOVE_SINK) * glove_top_k(q, sd),
                    weigh=glove_hand_exact)
              if ARC_HANDS == "fingerless" else []),
            # (her leg by where it is, not by its weights: her inner thigh is
            # partly her hips', and a weight test tore a hole there; and no
            # gap kept for the slot between her thighs, which ends above it)
            *piece(f"arcanist.stocking_{sd}", AND(0.3 - ARMW["l"] - ARMW["r"], stock_top(sd) - Z, (X * (1 if sd == "l" else -1) - 0.004) * 0.3, (KNEE_S - 0.03) - LEG_S[sd]), "stocking", lift=0.0012, thick=0.0, bevel=0.0, soften=10, slot=False),
            *girdle(f"arcanist.lace_{sd}", stock_band, 0.03, "glovesatin" if STOCK_IVORY else "satin", lift=0.003, thick=0.0018,
                    trim=("glovepipe",) + STOCK_WELT if STOCK_IVORY else ("satin", 0.0035, 0.0006, 0.0012), mask=(LEGW[sd] > 0.6) & (Z < CROTCH + 0.02) & (X * (1 if sd == "l" else -1) > 0.002)),
            *(BOOTS.boot(f"arcanist.boot_{sd}", sd, KNEE_S - 0.05 - ARC_BOOT_LIFT, ARC_BOOT_LIFT, ARC_BOOT_ST, "blackleather", sole_key=ARC_BOOT_SOLE)
              if ARC_BOOT == "made" else
              piece(f"arcanist.boot_{sd}", limb(sd, KNEE_S - 0.05, 9.9, front_dip=-0.03), "blackleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03, trim=gold(0.008), edge=30)),
            *piece(f"arcanist.cuff_{sd}", limb(sd, KNEE_S - 0.065, KNEE_S - 0.015), "blackleather", lift=0.009, thick=0.003, smooth=6, trim=gold(0.005)),
        ]
        if GLOVE_STYLE and ARC_HANDS == "fingerless":
            out += glove_style_cords(sd)
    return out


def leg_z(sd, s0):
    """Height of the point `s0` along a leg (metres from the hip)."""
    pts = LEG[sd]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1))]
    return float(np.interp(s0, d, np.array(pts)[:, 2]))


PL_SPOTS = []   # (the pauldron's rivets as laid: plate, centre; for its checks)
PL_ROWS = {}    # (each pauldron plate's one blend of bones)


PL_LIMB = ("upperarm", "lowerarm", "hand", "index", "middle", "pinky", "ring", "thumb")


def pl_limb_frame(sd="l", bone="upperarm", child="lowerarm", ref=None):
    """A limb's frame for pl_frame (armor 10): the centre at `bone`'s head, the
    axis down to `child`'s head, bearing 0 toward `ref` (default: the top of
    her shoulder, as the ranger's pauldrons) and + to her front on either
    side (her right's frame is the left's mirror, so a piece built on the
    left and mirrored with SWAP has the same (s, bearing) there)."""
    ctr = head(f"{bone}_{sd}")
    ax_ = head(f"{child}_{sd}") - ctr
    ax_ /= np.linalg.norm(ax_)
    ref = shoulder(sd) if ref is None else np.asarray(ref, float)
    e0 = (ref - ctr) - ax_ * ((ref - ctr) @ ax_)
    e0 /= np.linalg.norm(e0)
    return (ctr, ax_, e0, np.cross(ax_, e0) * (1 if sd == "l" else -1))


def pl_mirror(pos, wt, tris):
    """A sheet on her left made her right's: x mirrored, its weights' sides
    swapped (SWAP, as the plate cups are), its faces turned back outward."""
    return np.asarray(pos, float) * np.array([-1.0, 1.0, 1.0]), np.asarray(wt, float)[:, SWAP], np.asarray(tris)[:, ::-1]


def pl_frame(Q, F_):
    """Points in a limb's frame (her left arm's by default: pl_limb_frame):
    `s` down the limb from its joint's ball, the bearing round it (0 up her
    outer arm, + to her front) and the distance off its axis."""
    c_, a_, e0_, e1_ = F_
    d_ = np.atleast_2d(Q) - c_
    s_ = d_ @ a_
    r_ = d_ - np.outer(s_, a_)
    return s_, np.arctan2(r_ @ e1_, r_ @ e0_), np.linalg.norm(r_, axis=1)


def pl_point(s_, th_, rho_, F_):
    c_, a_, e0_, e1_ = F_
    return c_ + np.outer(s_, a_) + np.asarray(rho_)[:, None] * (np.outer(np.cos(th_), e0_) + np.outer(np.sin(th_), e1_))


def pl_row(base, w, sd="l", bone="upperarm", limb=PL_LIMB):
    """A plate's one blend of bones: `w` of her upper arm (`bone` on side
    `sd`, the limb's bones `limb` taken out of the rest), the rest the
    shoulder's own blend under the dome (her collarbone, chest and neck)."""
    arm_l = [BI[n] for n in BONES if n.endswith(f"_{sd}") and n.split("_")[0] in limb]
    rest = np.array(base, float)
    rest[arm_l] = 0
    rest /= rest.sum()
    row = rest * (1 - w)
    row[BI[f"{bone}_{sd}"]] += w
    return four_bones(row[None])[0]


def pl_one_blend(objs, row):
    """Every point of these parts on the plate's one blend (it moves rigidly)."""
    keep = np.where(row > 0.003)[0]
    for o in objs:
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        idx = list(range(len(o.data.vertices)))
        for j in keep:
            o.vertex_groups.new(name=BONES[j]).add(idx, float(row[j] / row[keep].sum()), "REPLACE")


def pl_rim(pos, tris, F_):
    """A plate's lower rim round her arm, from its outline as built: the
    lowest crossing at each bearing (half a degree apart) and the plate's
    distance off her arm there; only the rim proper, round the lowest point
    for as long as it runs round her arm at 45 degrees or less (past that it
    is the plate's end, turning up)."""
    loop = max(edge_loops(tris), key=len)
    s_, th_, rho_ = pl_frame(pos[loop], F_)
    g_ = np.radians(np.arange(-150, 150.01, 0.5))
    lo, rr = np.full(len(g_), -np.inf), np.zeros(len(g_))
    for i in range(len(loop)):
        j = (i + 1) % len(loop)
        if min(rho_[i], rho_[j]) < 0.02 or abs(th_[j] - th_[i]) > 0.5 or th_[j] == th_[i]:
            continue
        k = np.where((g_ >= min(th_[i], th_[j])) & (g_ < max(th_[i], th_[j])))[0]
        if not len(k):
            continue
        f = (g_[k] - th_[i]) / (th_[j] - th_[i])
        sv, rv = s_[i] + f * (s_[j] - s_[i]), rho_[i] + f * (rho_[j] - rho_[i])
        up = sv > lo[k]
        lo[k[up]], rr[k[up]] = sv[up], rv[up]
    ok = np.isfinite(lo)
    mid = np.where(ok & (np.abs(g_) < np.radians(60)))[0]
    i0 = mid[np.argmax(lo[mid])]
    dg = np.radians(0.5)
    a0 = b0 = i0
    while a0 > 0 and ok[a0 - 1] and abs(lo[a0 - 1] - lo[a0]) <= rr[a0] * dg:
        a0 -= 1
    while b0 < len(g_) - 1 and ok[b0 + 1] and abs(lo[b0 + 1] - lo[b0]) <= rr[b0] * dg:
        b0 += 1
    return g_[a0:b0 + 1], lo[a0:b0 + 1], rr[a0:b0 + 1]


def pl_lame(name, above, F_, row, O, V, E=0.016, tuck=0.0045, taper=-0.04, flare=0.004, joggle=0.003,
            rc=0.010, thick=0.0015, rv_end=0.022, rv_up=0.009, cut=None, mkey="bronze", rivet_key="darksteel",
            roll=(0.0045, 0.0005, 0.0015), bevel=0.0012, crease=None, rv_r=0.0032, rv_step=0.028, budget=3000,
            rivet_fn=None, h=0.0015):
    """A lame: a band round her arm under the rim of the plate above it, built
    in her arm's frame and never drawn on her skin (an outline on her skin,
    lifted off it, slid 10 to 18 mm, and no tuck survived: judge 5). Its top
    edge follows the built rim above `O` up under it, its lower edge `V` below
    that rim, each end `E` inside the rim's own end, the corners rounded `rc`.
    Its distance off her arm is one smooth law: the plate above's, less
    `tuck`, at every bearing (a Chebyshev fit, then lowered until it is under
    that plate everywhere they overlap), narrowing down her arm by `taper`,
    the hidden top bent `joggle` further in, the lower edge flared `flare`
    out over its last 12 mm. Laid out round her arm (its brushing runs round
    it, one island), bound all round, rivets `rv_up` above its lower edge.
    (armor 10: any limb, by its frame F_ (pl_limb_frame); `mkey`, `rivet_key`,
    `roll` (the rolled edge's width, height, overhang), `bevel`, `rv_r` and
    `rv_step`, `budget` as the ranger's by default (`rivet_fn(name, points,
    normals, rows)`: other rivet heads; `h` its grid's step); `crease` (depth, half-width): a
    ridge pressed out along bearing 0, a V that rises `depth` at it.)"""
    from numpy.polynomial import chebyshev as cheb
    from scipy.interpolate import LinearNDInterpolator
    pa, ta = above
    th_r, s_r, rho_r = pl_rim(pa, ta, F_)
    rl = rho_r - tuck
    u_r = np.r_[0, np.cumsum(np.diff(th_r) * (rl[1:] + rl[:-1]) / 2)]
    u_r -= np.interp(0.0, th_r, u_r)

    def th_of(u):
        return np.where(u < u_r[0], th_r[0] + (u - u_r[0]) / rl[0],
                        np.where(u > u_r[-1], th_r[-1] + (u - u_r[-1]) / rl[-1], np.interp(u, u_r, th_r)))

    def u_of(th):
        return np.where(th < th_r[0], u_r[0] + (th - th_r[0]) * rl[0],
                        np.where(th > th_r[-1], u_r[-1] + (th - th_r[-1]) * rl[-1], np.interp(th, th_r, u_r)))
    cl = np.r_[0, np.cumsum(np.hypot(np.diff(u_r), np.diff(s_r)))]
    L = cl[-1]
    tt = np.arange(0, L, 0.0005)
    C = np.c_[np.interp(tt, cl, u_r), np.interp(tt, cl, s_r)]
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    Nn = np.c_[-T[:, 1], T[:, 0]]
    # (a grid over the band's box, each point placed along the rim and below it)
    inb = (tt >= E) & (tt <= L - E)
    box = np.vstack([C[inb] + d * Nn[inb] for d in (-O, V)])
    gu = np.arange(box[:, 0].min() - 0.004, box[:, 0].max() + 0.004, h)
    gs = np.arange(box[:, 1].min() - 0.004, box[:, 1].max() + 0.004, h)
    UU, SS = np.meshgrid(gu, gs, indexing="ij")
    uv2 = np.c_[UU.ravel(), SS.ravel()]
    ns = len(gs)
    ii = (np.arange(len(gu) - 1)[:, None] * ns + np.arange(ns - 1)[None, :]).ravel()
    tri = np.vstack([np.c_[ii, ii + ns, ii + 1], np.c_[ii + ns, ii + ns + 1, ii + 1]])
    _, jn = cKDTree(C).query(uv2)
    t_ = tt[jn]
    d_ = ((uv2 - C[jn]) * Nn[jn]).sum(1)
    # (`cut`: the hidden top lowered cut[0] at its back end, over cut[1] from
    # it, eased back over cut[2]: at her idle the back of her arm rises under
    # the dome, and lame 1's top corner came up through the dome, judge 7)
    Ot = O - (cut[0] * (1 - ramp(t_ - E, cut[1], cut[1] + cut[2])) if cut else 0.0)
    tc, hw, dc, hh = L / 2, (L - 2 * E) / 2, (V - Ot) / 2, (V + Ot) / 2
    qx, qy = np.abs(t_ - tc) - (hw - rc), np.abs(d_ - dc) - (hh - rc)
    field = -(np.minimum(np.maximum(qx, qy), 0) + np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) - rc)
    th_g = th_of(uv2[:, 0])
    # (the plate above, as built, round her arm: its distance off the axis at
    # each bearing and height)
    sa, tha, rha = pl_frame(pa, F_)
    near = (np.abs(tha) < np.radians(150)) & (rha > 0.02)
    rad_above = LinearNDInterpolator(np.c_[tha[near] * rl.mean(), sa[near]], rha[near])(th_g * rl.mean(), uv2[:, 1])
    jog = joggle * np.clip(-d_ / O, 0, 1) ** 2
    fl = flare * np.clip((d_ - (V - 0.012)) / 0.012, 0, 1) ** 2
    ov = (field > -0.003) & (d_ < 0.001) & np.isfinite(rad_above)
    bound = rad_above - tuck - taper * d_
    lo_t, hi_t = th_g[ov].min(), th_g[ov].max()

    def xb(th):
        return np.clip((th - lo_t) / (hi_t - lo_t) * 2 - 1, -1, 1)
    bins = np.round(np.degrees(th_g[ov])).astype(int)
    ub = np.unique(bins)
    cb = np.array([bound[ov][bins == b].min() for b in ub])
    xs = xb(np.radians(ub))
    tgt = cb.copy()
    for _ in range(8):
        coef = cheb.chebfit(xs, tgt, 6)
        over = cheb.chebval(xs, coef) - cb
        if over.max() < 0.0001:
            break
        tgt -= np.maximum(over, 0)
    shift = max(0.0, float((cheb.chebval(xb(th_g[ov]), coef) - bound[ov]).max())) + 0.0002

    def law(th, d):
        return (cheb.chebval(xb(th), coef) - shift + taper * d + flare * np.clip((d - (V - 0.012)) / 0.012, 0, 1) ** 2
                - joggle * np.clip(-d / O, 0, 1) ** 2
                + (crease[0] * np.clip(1 - np.abs(u_of(th)) / crease[1], 0, 1) if crease else 0.0))
    X = pl_point(uv2[:, 1], th_g, law(th_g, d_), F_)
    at = np.c_[np.zeros((len(X), 3)), np.repeat(row[None], len(X), 0), t_, d_, field]
    pos, at, tris = clip(field, X, at, tri)
    pos, at, tris = weld(pos, at, tris)
    tris = islands(pos, tris)
    nr = vertex_normals(pos, tris)
    sp, thp, _ = pl_frame(pos, F_)
    if (nr * (np.cos(thp)[:, None] * F_[2] + np.sin(thp)[:, None] * F_[3])).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nr = -nr
    at[:, :3] = nr
    pos, beads = bind_edges(name, pos, at, tris, mkey, roll[0], roll[1], roll[2], thick, sigma=0.003)
    # (how far the bound sheet stands off its own law: rigid, none)
    sp, thp, rp = pl_frame(pos, F_)
    q2 = np.c_[u_of(thp), sp]
    _, jq = cKDTree(C).query(q2)
    dev = np.abs(rp - law(thp, ((q2 - C[jq]) * Nn[jq]).sum(1)))
    print("PAULDRON %s: %.0f mm long round her arm, %d points, off its law by %.2f mm at most (%.2f mm 99%%), "
          "lowered %.1f mm" % (name, (L - 2 * E) * 1000, len(pos), dev.max() * 1000, np.percentile(dev, 99) * 1000, shift * 1000))
    SHEET[name] = (pos.copy(), tris.copy(), at[:, 3:3 + NB].copy(), thick)
    RIGID_UV[name] = (F_[0], F_[1], True)
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget)] + beads
    # (rivets in one row `rv_up` above its lower edge, `rv_end` in from its ends)
    n = max(2, int(round((L - 2 * E - 2 * rv_end) / rv_step)) + 1)
    tk = np.linspace(E + rv_end, L - E - rv_end, n)
    pk = np.c_[np.interp(tk, tt, C[:, 0]), np.interp(tk, tt, C[:, 1])] + (V - rv_up) * np.c_[np.interp(tk, tt, Nn[:, 0]), np.interp(tk, tt, Nn[:, 1])]
    thk = th_of(pk[:, 0])
    spots = pl_point(pk[:, 1], thk, law(thk, np.full(n, V - rv_up)), F_)
    _, jv = cKDTree(pos).query(spots)
    if rivet_fn is None:
        made += rivets(name, pos, at, tris, thick, rivet_key, r=rv_r, spots=(spots, vertex_normals(pos, tris)[jv], np.repeat(row[None], n, 0)))
    else:
        made += rivet_fn(name, spots, vertex_normals(pos, tris)[jv], np.repeat(row[None], n, 0))
    PL_SPOTS.extend((name, p) for p in spots)
    pl_one_blend([o for o in made if o is not None], row)
    PL_ROWS[name] = row
    return made, (pos, tris)


def pl_border_spots(pos, tris, F_, inset=0.0095, step=0.028):
    """Rivets in a row `inset` inside a plate's outline, `step` apart round
    it, one at its lowest point on her outer arm."""
    loop = max(edge_loops(tris), key=len)
    lp = np.vstack([pos[loop], pos[loop[:1]]])
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(lp, axis=0), axis=1))]
    Lp = run[-1]
    rd = np.arange(0, Lp, 0.0005)
    dense = np.stack([np.interp(rd, run, lp[:, k]) for k in range(3)], 1)
    dist, j = cKDTree(dense).query(pos)
    par = rd[j]
    # (and none nearer the edge than inset less 1.5 mm: chosen within 3 mm,
    # the cap's nearest rivet stood 7.9 mm in at an inset of 10, short of the
    # 8.2 that puts it 2 mm inside the rolled rim, judge 8)
    cand = np.where((np.abs(dist - inset) < 0.003) & (dist > inset - 0.0015))[0]
    s_, th_, _ = pl_frame(dense, F_)
    lat = np.where(np.abs(th_) < np.radians(30))[0]
    a0 = rd[lat[np.argmax(s_[lat])]]
    n = int(round(Lp / step))
    nor = vertex_normals(pos, tris)
    pts, nrs = [], []
    for k in range(n):
        tgt = (a0 + k * Lp / n) % Lp
        dp = np.abs((par[cand] - tgt + Lp / 2) % Lp - Lp / 2)
        best = np.argmin(dp + 2 * np.abs(dist[cand] - inset))
        if dp[best] < 0.005:
            pts.append(pos[cand[best]])
            nrs.append(nor[cand[best]])
        else:
            # (no point in the band near this slot: the cap had 16 of 17, a
            # gap of two steps in its row, judge 9. A wider band, never
            # nearer the edge, then the nearest along it)
            c2 = np.where((dist > inset - 0.0015) & (dist < inset + 0.006))[0]
            dp2 = np.abs((par[c2] - tgt + Lp / 2) % Lp - Lp / 2)
            b2 = np.argmin(dp2 + np.abs(dist[c2] - inset))
            if dp2[b2] < 0.008:
                pts.append(pos[c2[b2]])
                nrs.append(nor[c2[b2]])
            else:
                print("RIVETS: WARNING slot %d of %d found no point (nearest %.1f mm along)" % (k, n, dp2[b2] * 1000))
    return np.array(pts), np.array(nrs)


def ranger_pauldron():
    """Her left spaulder: a bronze dome over her shoulder and three lames down
    her arm, each a rigid plate on one blend of bones, stepping from the
    dome's (her shoulder's, seated on her trapezius) to her upper arm's."""
    out = []
    sh = shoulder("l")
    ctr = head("upperarm_l")
    ax_ = head("lowerarm_l") - ctr
    ax_ /= np.linalg.norm(ax_)
    e0 = (sh - ctr) - ax_ * ((sh - ctr) @ ax_)
    e0 /= np.linalg.norm(e0)
    F_ = (ctr, ax_, e0, np.cross(ax_, e0))
    NEST.pop("ranger.pauldron", None)
    # (her upper arm's share in each plate: the dome stays with her shoulder,
    # the lames step to her arm, by less lower down, where the same turn
    # about her shoulder's ball swings a lame further out under the one above)
    PL_W = tuple(float(x) for x in os.environ.get("PL_W", "0.05,0.42,0.60,0.72").split(","))
    PL_O = tuple(float(x) for x in os.environ.get("PL_O", "0.022,0.016,0.014").split(","))   # (how far each lame goes up under the plate above)
    PL_V = tuple(float(x) for x in os.environ.get("PL_V", "0.030,0.029,0.028").split(","))   # (and shows below it)
    PL_LIFT = float(os.environ.get("PL_LIFT", "0.026"))
    PL_TUCK = float(os.environ.get("PL_TUCK", "0.0045"))
    PL_CUT = tuple(float(x) for x in os.environ["PL_CUT"].split(",")) if os.environ.get("PL_CUT") else None   # (lame 1's hidden back top lowered; off until tuned)
    zone = ANDR(cap(sh, 0.11), Z - (sh[2] - 0.11 * 0.55), r=0.011)
    RIGID_UV["ranger.pauldron0"] = (ctr, ax_, False)
    dome = piece("ranger.pauldron0", zone, "bronze", lift=PL_LIFT, clear=0.015, thick=0.0015, smooth=14,
                 soften=10, rigid=(ctr, "ranger.pauldron", 0.0028))
    pd, td, wd, _ = SHEET["ranger.pauldron0"]
    row = pl_row(wd[0], PL_W[0])
    pts, nrs = pl_border_spots(pd, td, F_)
    dome += rivets("ranger.pauldron0", pd, None, td, 0.0015, "darksteel", spots=(pts, nrs, np.repeat(row[None], len(pts), 0)))
    PL_SPOTS.extend(("ranger.pauldron0", p) for p in pts)
    pl_one_blend([o for o in dome if o is not None], row)
    PL_ROWS["ranger.pauldron0"] = row
    SHEET["ranger.pauldron0"] = (pd, td, np.repeat(row[None], len(pd), 0), 0.0015)
    out += dome
    above = (pd, td)
    for k in (1, 2, 3):
        made, above = pl_lame(f"ranger.pauldron{k}", above, F_, pl_row(wd[0], PL_W[k]), PL_O[k - 1], PL_V[k - 1],
                              tuck=PL_TUCK, rv_end=0.022 if k < 3 else 0.012, cut=PL_CUT if k == 1 else None)
        out += made
    return out


def sp_env(k, d):
    return tuple(float(x) for x in os.environ.get(k, d).split(","))


def ranger_spaulder():
    """The simpler pauldron (PAULDRON=leather, for the owner beside the lames):
    a leather spaulder over her left shoulder, skinned as her other leathers
    are, so its neck end lies on her trapezius (the rigid dome stood 17-26 mm
    off it), with a bronze cap plate and two bronze bands riveted onto it,
    spaced and never overlapping, so no plate can rise through another (lame
    1 rose through the dome at her idle, judge 6). The leather under each
    plate takes its shape and its one blend of bones, so they move as one
    where riveted."""
    out = []
    sh = shoulder("l")
    ctr = head("upperarm_l")
    ax_ = head("lowerarm_l") - ctr
    ax_ /= np.linalg.norm(ax_)
    e0 = (sh - ctr) - ax_ * ((sh - ctr) @ ax_)
    e0 /= np.linalg.norm(e0)
    F_ = (ctr, ax_, e0, np.cross(ax_, e0))
    S0, C2 = sp_env("SP_LINE", "0.012,0.012")          # (the cap plate's lower edge: s = S0 + C2 th^2 down her arm)
    G, H = sp_env("SP_BAND", "0.011,0.0245")           # (gap between plates; band height: 7 mm closed and the plates crossed in a third of her poses, the sweep)
    THB, = sp_env("SP_THB", "1.55")                    # (bands' half-span round her arm, radians)
    S_MED, = sp_env("SP_MED", "-0.055")                # (the cap plate stops here toward her neck: short of her trapezius, judge 7)
    R_CAP, = sp_env("SP_R", "0.105")                   # (the cap plate's reach over her shoulder)
    LIFT, THK, GAP = sp_env("SP_LIFT", "0.003,0.0025,0.0012")
    W_ = sp_env("SP_W", "0.5,0.55,0.6")                # (upper arm's share in the cap and each band: close, so they turn nearly as one; 0.45-0.7 crossed them)
    LKEY = os.environ.get("SP_LEATHER", "forestleather")
    FAR, *FAR_W = sp_env("SP_FAR", "0.016,0.016,0.006")   # (past these from any plate the leather takes her skin's shape; past the cap and the bands, her skin's bones)
    CLR = LIFT + THK + GAP
    CAP_UP, = sp_env("SP_CAP_UP", "0.0045")           # (the cap stands further off: her shoulder swells under it at her idle; 4 mm left band 1 1.17 mm under it, judge 8)
    # (the hem away from the cap: how close it lies on her, the strip along
    # it on one set of weights, and the width under a band over which the
    # leather goes from the band's row to her skin's, hidden by the band)
    HEM_LIFT, STRIP, TRANS = sp_env("SP_HEM", "0.0015,0.012,0.0")
    # (how far the leather runs past band 2: 11 mm, and the change from the
    # band's row to her skin's in that strip folded it at her idle, judge 8;
    # made under the band instead, the leather on her skin's weights rose
    # 4.8 mm through it at her idle, so the leather ends just past the band
    # and moves with it, sp9)
    # (and how far round her arm it runs past the bands' ends: 11 mm, and
    # that corner, past any plate, hung off the back of her arm as a loop
    # with a void under it through two solvers, judge 8; now it ends 3 mm
    # inside the bands' ends, so all of it below the cap rides a band)
    TONGUE, TSIDE = sp_env("SP_TONGUE", "0.006,-0.003")
    s_, th_, rho_ = pl_frame(P, F_)
    line = S0 + C2 * th_ ** 2
    # (never round into her armpit; a distance, not a step: cut on a step,
    # the leather's edge followed her triangles in a stair and its binding
    # tore, judge 7. The cap stops CAP_TH round her arm behind and CAP_TH2
    # in front, on top of her shoulder: her front deltoid swells 6-8 mm
    # through a rigid plate at her idle, and the leather alone covers it)
    CAP_TH, LEAF_TH, CAP_TH2 = sp_env("SP_TH", "90,115,65")
    side = (np.radians(LEAF_TH) - np.abs(th_)) * rho_
    side_c = (np.radians(np.where(th_ < 0, CAP_TH, CAP_TH2)) - np.abs(th_)) * rho_
    capf = ANDR(ANDR(cap(sh, R_CAP), line - s_, r=0.008), s_ - S_MED, r=0.012)
    capf = ANDR(capf, side_c, r=0.008)

    def band(k):
        top = line + G + (k - 1) * (H + G)
        return ANDR(np.minimum(s_ - top, top + H - s_), (THB - np.abs(th_)) * rho_, r=0.009)
    bot = line + 2 * (H + G) + TONGUE
    # (the leather shows only toward her neck, between the bands and below
    # them; round the rest of the cap plate it ends hidden under its rim)
    tongue = ANDR(ANDR(bot - s_, (THB - np.abs(th_)) * rho_ + TSIDE, r=0.014), s_ - (line - 0.02), r=0.004)
    # (the leather runs MARGIN past the cap plate all round, so the plate
    # lies on it everywhere: ended hidden under its rim, her skin showed
    # under the rim's front as she moved, judge 7; its neck end, TRAP past
    # the cap's reach, stops short of her neck's bones, whose pull had torn
    # its edge)
    MARGIN, TRAP = sp_env("SP_MARGIN", "0.008,0.01")
    # (the neck end's corners: at 12 mm its binding turned up off her
    # trapezius in a hook, judge 8)
    NECK_R, = sp_env("SP_NECK_R", "0.024")
    # (and its hem there, past the cap's neck stop and NOFF out from under
    # the cap, lies NLIFT on her (judge 8 asked 1 mm or less; it was 1.5))
    # (NSTRIP: over how much of it the leather rises from NLIFT to LIFT: over
    # STRIP, the binding's fair line, rounded inside the hem at the front
    # corner, found the leather 2-2.5 mm up and stood off with it, solver 3)
    NOFF, NLIFT, NS, NSTRIP = sp_env("SP_NECKPIN", "0.004,0.0013,0.0,0.024")
    LOWPASS = int(os.environ.get("SP_LOWPASS", "20"))   # (Taubin rounds over the leather away from the plates)
    _ua = ANDR(cap(sh, R_CAP + MARGIN), line - s_ + MARGIN, r=0.008)
    # (SP_NECKCUT: how far past S_MED the neck end reaches, and its drop
    # below the shoulder; shorter, it stops before the top of her trapezius)
    NK_MED, NK_DROP = sp_env("SP_NECKCUT", "0.02,0.0605")
    _ub = ANDR(ANDR(cap(sh, R_CAP + TRAP), Z - (sh[2] - NK_DROP), r=NECK_R), (S_MED + NK_MED) - s_, r=NECK_R)
    # (the neck end as a soft 0-1 weight over NKW, not a hard mask: its
    # switch stepped the hem's height, the strip's width and the weights,
    # and the leather creased along it, a pale line from the binding's kink,
    # judge 9 A5)
    NKW = float(os.environ.get("SP_NECKW", "0.012"))

    def nkw(pos, own, past):
        a = np.clip(0.5 + (S_MED + NS - pl_frame(pos, F_)[0]) / NKW, 0, 1)
        b = np.clip(0.5 + (past[0] - NOFF) / NKW, 0, 1)
        sm = lambda t: t * t * (3 - 2 * t)
        return sm(a) * sm(b) * (own < 0)
    _fil = float(os.environ.get("SP_FILLET", "0.012"))
    under = -ANDR(-_ua, -_ub, r=_fil) if _fil > 0 else OR(_ua, _ub)
    # (its corners round, 16-18 mm: at 8 the neck corner's binding turned
    # tight and curled up off her trapezius, judge 8)
    leaf = ANDR(OR(under, tongue), side, r=0.016)
    # The plates first: the leather is shaped under them.
    names = ["ranger.pauldron0", "ranger.pauldron1", "ranger.pauldron2"]
    base = W[capf > 0].mean(0)
    plates = []
    for k, (nm, fld) in enumerate(zip(names, [capf, band(1), band(2)])):
        if k == 0:
            cen = ctr
            RIGID_UV[nm] = (ctr, ax_, False)
        else:
            sm = float(np.median(s_[fld > 0]))
            cen = ctr + ax_ * sm
            RIGID_UV[nm] = (ctr, ax_, True)
        cl = CLR + (CAP_UP if k == 0 else 0.0)
        made = piece(nm, fld, "bronze", lift=cl, clear=cl, thick=0.0015, smooth=14, soften=6 if k == 0 else 3, rigid=cen)
        pd, td, wd, _ = SHEET[nm]
        row = pl_row(base, W_[k])
        if k == 0:
            # (10 mm in: at 9.5 the cap's border rivets stood only 1.6 mm inside
            # its rolled rim, judge 8 asked for 2 mm or more)
            pts, nrs = pl_border_spots(pd, td, F_, inset=0.0100)
        else:
            sp_, tp_, rp_ = pl_frame(pd, F_)
            mid = float(np.median(sp_))
            lo, hi = tp_.min(), tp_.max()
            pts, nrs = [], []
            nr_ = vertex_normals(pd, td)
            arc = (hi - lo) * float(np.median(rp_)) - 0.03
            n = max(2, int(round(arc / 0.028)) + 1)
            # (each at its bearing on the band's own middle, the point there
            # farthest from the plate's rim, and none nearer it than 8.2 mm
            # (its edge 2 mm inside the rolled rim's inner edge):
            # on the band's median height overall, the end rivet sat on the
            # rolled rim where the band curves up, half off it in a ring,
            # judge 8)
            ein_ = cKDTree(pd[max(edge_loops(td), key=len)]).query(pd)[0]
            for t in np.linspace(lo + 0.018 / np.median(rp_), hi - 0.018 / np.median(rp_), n):
                near_ = np.where(np.abs(tp_ - t) * rp_ < 0.002)[0]
                j = near_[np.argmax(ein_[near_])] if len(near_) else int(np.argmin(np.abs(tp_ - t)))
                if ein_[j] < 0.0082:
                    continue
                pts.append(pd[j])
                nrs.append(nr_[j])
            pts, nrs = np.array(pts), np.array(nrs)
        made += rivets(nm, pd, None, td, 0.0015, "rivetbronze", spots=(pts, nrs, np.repeat(row[None], len(pts), 0)))
        PL_SPOTS.extend((nm, p) for p in pts)
        pl_one_blend([o for o in made if o is not None], row)
        PL_ROWS[nm] = row
        SHEET[nm] = (pd, td, np.repeat(row[None], len(pd), 0), 0.0015)
        loop = max(edge_loops(td), key=len)
        ein = cKDTree(pd[loop]).query(pd)[0]
        print("SPAULDER %s: rivet nearest its plate's edge %.1f mm" % (nm, cKDTree(pd[loop]).query(pts)[0].min() * 1000))
        plates.append((pd, vertex_normals(pd, td), ein, cKDTree(pd), row))
        out += made
        print("SPAULDER %s: %d points, rivets %d, upper arm %.2f" % (nm, len(pd), len(pts), W_[k]))

    def owned(pos):
        """Which plate each point of the leather lies under (-1: none), the
        leather's place under it, and how far each point is past the
        nearest plate's edge (0 under one)."""
        own = -np.ones(len(pos), int)
        tgt = pos.copy()
        past = np.full((len(plates), len(pos)), np.inf)
        for k, (pd, nd, ein, kd, row) in enumerate(plates):
            _, j = kd.query(pos)
            d = pos - pd[j]
            dn = (d * nd[j]).sum(1)
            tan = np.linalg.norm(d - nd[j] * dn[:, None], axis=1)
            sd = np.where(ein[j] > 0.0025, ein[j], -tan)
            near = np.abs(dn) < 0.03
            under = near & (sd >= 0)
            own[under] = k
            tgt[under] = (pos - nd[j] * (dn + GAP + THK)[:, None])[under]
            past[k] = np.where(near, np.maximum(-sd, 0), np.inf)
        return own, tgt, past

    def fill(tris, vals, known):
        """Harmonic fill: `vals` kept where `known`, eased between."""
        n = len(vals)
        e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        e = np.unique(np.sort(e, 1), axis=0)
        A = sparse.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        Lp = sparse.diags(np.asarray(A.sum(1)).ravel()) - A
        fr = np.where(~known)[0]
        kn = np.where(known)[0]
        if len(fr) == 0:
            return vals
        from scipy.sparse.linalg import spsolve
        rhs = -Lp[fr][:, kn] @ vals[kn]
        out = vals.copy()
        sol = spsolve(Lp[fr][:, fr].tocsc(), rhs)
        out[fr] = sol.reshape(len(fr), -1) if vals.ndim > 1 else sol
        return out

    # (the leather is held to each plate's underside where under it and to
    # her skin past FAR from any plate; between, in the gaps between plates
    # and up her trapezius from the cap's neck end, it is eased harmonically:
    # blending each plate's tangent plane by distance crumpled it into
    # facets and shards, judge 7)
    TRIS_L = []     # (the leather's triangles, for weigh(): piece() hands it none)

    def conform(pos, tris):
        TRIS_L[:] = [tris]
        own, tgt, past = owned(pos)
        known = (own >= 0) | (past.min(0) > FAR)
        disp = np.where((own >= 0)[:, None], tgt - pos, 0.0)
        # (its hem, past the plates, hugs her: ironed, it bridged the hollow
        # behind her armpit and flared 8-13 mm off her arm, judge 7)
        hem = np.unique(np.concatenate(edge_loops(tris)))
        hem = hem[own[hem] < 0]
        # (away from the cap it lies close on her, HEM_LIFT, as a tailored
        # edge does, rising to LIFT over the strip along it: held 3 mm off,
        # its rear corner stood off her arm as a tongue with a void under
        # it, and its neck corner curled up off her trapezius, judge 8)
        far_ = np.clip((past[0] - FAR_W[0] / 2) / (FAR_W[0] / 2), 0, 1) * np.clip((past[1:].min(0) - STRIP) / STRIP, 0, 1)
        nw_ = nkw(pos, own, past)
        far_ = far_ + (1.0 - far_) * nw_
        hl_ = HEM_LIFT + (NLIFT - HEM_LIFT) * nw_
        for i in hem:
            q, n, _, _ = BVH.find_nearest(Vector(pos[i]))
            if q is not None:
                disp[i] = np.array(n) * (LIFT - (LIFT - hl_[i]) * far_[i] - (Vector(pos[i]) - q).dot(n))
        known[hem] = True
        disp = fill(tris, disp, known)
        out_ = pos + disp
        # (and nothing of it nearer her than that: piece() clears it only by
        # HEM_LIFT now, so the rest is cleared by LIFT here, as before)
        # (and away from the plates and the hem, low-passed (Taubin, so it
        # does not shrink): it took her skin's every sub-millimetre ridge, and
        # the rim light drew the edge of her shoulders' graft across it as a
        # pale line, judge 8)
        import scipy.sparse as sps
        ed_ = np.r_[tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]
        A_ = sps.coo_matrix((np.ones(len(ed_)), (ed_[:, 0], ed_[:, 1])), shape=(len(pos), len(pos))).tocsr()
        A_ = ((A_ + A_.T) > 0).astype(float)
        deg_ = np.asarray(A_.sum(1)).ravel()
        free_ = np.setdiff1d(np.where(own < 0)[0], hem)
        for k_ in range(LOWPASS):
            lam_ = 0.5 if k_ % 2 == 0 else -0.53
            avg_ = (A_ @ out_) / np.maximum(deg_, 1)[:, None]
            out_[free_] += lam_ * (avg_[free_] - out_[free_])
        d_e, j_e = cKDTree(out_[hem]).query(out_)
        need = LIFT - (LIFT - hl_[hem][j_e]) * far_[hem][j_e] * np.clip(1 - d_e / (STRIP + (NSTRIP - STRIP) * nw_[hem][j_e]), 0, 1)
        for i in np.where(own < 0)[0]:
            q, n, _, _ = BVH.find_nearest(Vector(out_[i]))
            if q is not None:
                d = (Vector(out_[i]) - q).dot(n)
                if d < need[i] - (0.0008 if LOWPASS else 0.0):   # (a ridge under it may come 0.8 mm nearer)
                    out_[i] = out_[i] + np.array(n) * (need[i] - d)
        print("SPAULDER leather held under the plates at %d of %d points, eased at %d" % ((own >= 0).sum(), len(pos), (~known).sum()))
        return out_

    def weigh(pos, wt):
        own, _, past = owned(pos)
        # (the cap's bones reach further than a band's: her shoulder swells
        # under it at her idle, and leather just past its rim, skinned as
        # she is, rose over the rim, judge 7)
        rows = np.array([pl[4] for pl in plates])
        known = (own >= 0) | ((past[0] > FAR_W[0]) & (past[1:].min(0) > FAR_W[1]))
        vals = np.where((own >= 0)[:, None], rows[np.maximum(own, 0)], wt)
        # (its hem strip away from the cap, the last STRIP of it, binding and
        # all, on one set of weights across it: her skin's at the edge, eased
        # along it. Under band 2 it took the band's row and 7-11 mm lower her
        # skin's, and the sheet folded just inside the binding: a ragged edge
        # with her skin at its notch, judge 8. The change from a band's row to
        # her skin's is made under the band, over TRANS, hidden by it)
        tris = TRIS_L[0]
        hp, hw, hk = [], [], []
        for lp in edge_loops(tris):
            lp = np.asarray(lp)
            w_ = np.asarray(wt, float)[lp]
            for _ in range(30):
                w_ = (np.roll(w_, 1, 0) + 2 * w_ + np.roll(w_, -1, 0)) / 4
            # (soft at the neck end too: a hard stop there ended the strip
            # abruptly and the leather creased from the binding's corner, A5)
            kw_ = np.maximum((past[0][lp] > FAR_W[0]).astype(float), nkw(pos[lp], own[lp], past[:, lp])) \
                * (past[1:, lp].min(0) > STRIP + 0.004)
            keep = kw_ > 0
            hp.append(lp[keep])
            hw.append(w_[keep])
            hk.append(kw_[keep])
        hp, hw, hk = np.concatenate(hp), np.vstack(hw), np.concatenate(hk)
        if len(hp):
            d_e, j_e = cKDTree(pos[hp]).query(pos)
            strip = (d_e < STRIP) & (own < 0)   # (never under a plate: the neck's strip reaches the cap)
            k_ = hk[j_e[strip]][:, None]
            vals[strip] = (1 - k_) * vals[strip] + k_ * hw[j_e[strip]]
            known |= strip
            known &= ~((own >= 1) & ~strip & (d_e < STRIP + TRANS))
            print("SPAULDER hem strip on its edge's weights at %d points, eased from the bands' rows at %d" % (
                strip.sum(), ((own >= 1) & ~strip & (d_e < STRIP + TRANS)).sum()))
        # (the neck end, past the cap's neck stop, on the very weights of her
        # skin beneath, point by point, not eased: on weights eased over the
        # piece, its tip near her neck took less of her neck's bone and none
        # of her head's than her skin there (clavicle .58 neck .20 against
        # .45 and .25 with head .05), and it stood 5-7 mm off her trapezius
        # at her idle, 2-3 at rest: the hook of judge 8 #3, j2)
        nw_ = nkw(pos, own, past)
        nk_ = nw_ > 0
        vals[nk_] = (1 - nw_[nk_, None]) * vals[nk_] + nw_[nk_, None] * W[cKDTree(P).query(pos[nk_])[1]]
        known |= nk_
        print("SPAULDER neck end on her skin's weights at %d points (eased in at %d)" % (nk_.sum(), (nk_ & (nw_ < 1)).sum()))
        return fill(tris, vals, known)

    # (laid out whole, one island: cut into four by smart_project, it showed
    # a pale line across it near her neck, judge 8)
    ONE_ISLAND.add("ranger.spaulder")
    BIND_RMIN["ranger.spaulder"] = 0.012

    # (cleared to HEM_LIFT all over once shaped, the neck end's hem, pinned at
    # NLIFT, went back up to 1.5 mm, and its binding's underside, 0.6 mm
    # below the leather, stood 1-2.5 mm off her trapezius at rest: there it
    # keeps NLIFT, solver 3)
    def clear_(pos):
        own, _, past = owned(pos)
        return HEM_LIFT + (min(NLIFT, HEM_LIFT) - HEM_LIFT) * nkw(pos, own, past)
    lm = piece("ranger.spaulder", leaf, LKEY, lift=LIFT, thick=THK, smooth=10, soften=10, iron=20, clear=clear_,
               trim=("darkleather", 0.006, 0.0006, 0.0013), stiff=[conform], weigh=weigh)
    # (its binding and stitches on the weights the leather's edge ends with:
    # the binding took the sheet's weights before finish() eased them again,
    # and at her idle the two parted by up to 9 mm at the lower corners (26 mm
    # over the sweep): the leather rose over the binding in a ragged edge with
    # her skin showing, and the rear corner hung off as a tongue, judge 8)
    sheet = lm[0]
    vs_ = sheet.data.vertices
    sp_ = np.array([sheet.matrix_world @ v.co for v in vs_])
    sw_ = np.zeros((len(vs_), len(BONES)))
    for v in vs_:
        for gg in v.groups:
            sw_[v.index, BI[sheet.vertex_groups[gg.group].name]] = gg.weight
    kd_ = cKDTree(sp_)
    rings = {}
    # (one set to each ring of the binding, as tube() gives, from the
    # leather round the ring's centre, eased along it: each point of a ring
    # on its own nearest leather, the roll came out toothed as she moved)
    for o in sorted([o for o in lm[1:] if o is not None], key=lambda o: "_stitch" in o.name):
        op_ = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        if "_bind" in o.name and len(op_) % 12 == 0:
            rc_ = op_.reshape(-1, 12, 3).mean(1)
            d_, j_ = kd_.query(rc_, k=8)
            g_ = np.exp(-0.5 * (d_ / 0.003) ** 2) + 1e-12
            rw_ = (sw_[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
            for _ in range(3):
                rw_ = (np.roll(rw_, 1, 0) + 2 * rw_ + np.roll(rw_, -1, 0)) / 4
            rings[o.name] = (rc_, rw_)
            ow_ = four_bones(np.repeat(rw_, 12, 0))
        elif rings:
            # (stitches on the ring of the binding they are sewn through)
            rc_ = np.vstack([r[0] for r in rings.values()])
            rw_ = np.vstack([r[1] for r in rings.values()])
            ow_ = four_bones(rw_[cKDTree(rc_).query(op_)[1]])
        else:
            continue
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        for b in np.where(ow_.max(0) > 0.003)[0]:
            grp = o.vertex_groups.new(name=BONES[b])
            for i in np.where(ow_[:, b] > 0.003)[0]:
                grp.add([int(i)], float(ow_[i, b]), "REPLACE")
    print("SPAULDER binding and stitches on the leather's final weights: %d parts" % (len(lm) - 1))
    out = lm + out
    return out


# (RANGER_GUSSET "front,back,z0,z1": the ranger corset's thong made wider at her crotch, by
# `front` each side in front of it and `back` behind, in full up to z0 over her crotch and eased
# out by z1, one fair line into the leg line and the thong above. s17: as cut it was 5 mm each side
# of her middle under her crotch (the strip a garment must cover is 12), the strip 2-4 mm inside
# its roll, and it showed by a pixel past her right edge behind, seen from below in a wide stance.
# "0,0,0.02,0.07" is the cut as before.)
RG_F, RG_B, RG_Z0, RG_Z1 = (float(v) for v in os.environ.get("RANGER_GUSSET", "0.004,0.008,0.02,0.07").split(","))


def ranger():
    """The stalker: a corset that holds her. It is strapless, with a
    sweetheart line over her breasts (hugged tight, on their perfect form),
    leaving her shoulders and the top of her chest bare. It is laced up the
    front over a strip of her skin and tied in a bow, and runs on down over
    her crotch. On her right it is cut away from her waist: a straight line
    in front to just shy of her crotch, and behind a line over the top of
    her cheek into a thong, so her right hip and cheek are bare. Her left
    leg is in a light brown pant leg, tucked up under the corset and down
    into her boot. A belt slung round her hips with a bronze buckle; a buckled strap
    cinched high on her bare right thigh; bronze lames at her left
    shoulder, bronze bracers, fingerless gloves; knee boots with folded
    cuffs, the right one laced up the front. Corset, gloves and boots of
    forest-green leather; the pant leg light brown cloth."""
    from scipy.interpolate import PchipInterpolator
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.006, key="darkleather"):
        return (key, w, 0.0006, 0.0013)

    def belt_z(a):
        return CROTCH + 0.085 - 0.022 * np.sin(a)

    nx, nzn = abs(NIPPLE["r"][0]), NIPPLE["r"][2]
    ax_ = np.abs(X)

    def smin(a, b, k=0.004):
        m = np.minimum(a, b)
        return m - k * np.log(np.exp(-(a - m) / k) + np.exp(-(b - m) / k))

    # The top: a sweetheart over her breasts, well above each nipple, down to
    # a point between them; then, by the angle round her chest, down under
    # her arm (below all the skin her arm moves, so the edge is this line and
    # never the ragged edge of her arm's weights) into a straight band round
    # her back. The two met by a smooth minimum: one fair curve.
    sweet = PchipInterpolator([0.0, 0.025, nx * 0.6, nx, nx + 0.04, nx + 0.09],
                              [nzn - 0.014, nzn - 0.004, nzn + 0.026, nzn + 0.034, nzn + 0.03, nzn + 0.02])
    under_arm = PchipInterpolator([0, 50, 62, 72, 82, 92, 104, 118, 180],
                                  [1.8, 1.8, nzn + 0.05, nzn + 0.025, nzn, nzn - 0.03, UNDERBUST + 0.062, UNDERBUST + 0.06,
                                   UNDERBUST + 0.06])

    def top_at(q):
        round_ = np.degrees(np.abs(np.arctan2(q[:, 0], -(q[:, 1] + 0.03))))
        return smin(sweet(np.minimum(np.abs(q[:, 0]), nx + 0.09)), under_arm(round_))

    top_z = top_at(P)
    # Below, her right is cut away. In front the corset keeps only her abs:
    # its edge runs up from just shy of her crotch along the groove at their
    # outer edge (found on her: about 7 cm out from her middle, narrowing
    # toward her crotch), then curves out round her side at her lower ribs.
    # Behind, from there it runs level, then curves down over the top of her
    # cheek to her middle above the cleft, and a thong runs down it. Her
    # whole right hip, flank and cheek are bare. Her left is a cheeky seat
    # over the top of her pant leg.
    ang = np.abs(np.arctan2(X, -(Y - CROTCH_Y)))
    rise_ = Z - CROTCH
    hug = PchipInterpolator([-0.035, 0.0, 0.02, 0.04, 0.07, 0.1, 0.16, 0.22, 0.28, 0.33, 0.37, 0.40],
                            [0.012, 0.016, 0.026, 0.045, 0.063, 0.072, 0.075, 0.077, 0.08, 0.092, 0.13, 0.2])
    right_front = hug(np.clip(rise_, -0.035, 0.40)) + X
    u_ = np.clip(-X / 0.13, 0, 1)
    right_back = Z - (CROTCH + 0.31 + 0.095 * u_ ** 0.9)
    right = right_front * FRONT + right_back * (1 - FRONT)
    edge_l = CROTCH + PchipInterpolator([0, 0.6, 1.2, 1.57, 2.1, 2.6, np.pi], [-0.02, 0.0, 0.03, 0.05, 0.065, 0.06, 0.055])(ang)
    rise = np.maximum(Z - CROTCH, 0)
    # (between her legs a narrow strip, a little wider in front; behind, a
    # thong down her cleft)
    # (RANGER_GUSSET: wider at her crotch, eased out up the leg line and the thong)
    def gusset(z, fr_):
        return (RG_F * fr_ + RG_B * (1 - fr_)) * (1 - ramp(z - CROTCH, RG_Z0, RG_Z1))
    strip = (0.012 + 0.3 * rise) * FRONT + np.minimum(0.008 + 0.07 * rise, 0.018) * (1 - FRONT) + gusset(Z, FRONT) - ax_
    legs = OR(np.where(X < 0, right + 0.03, Z - edge_l), strip)
    # (her skin's field reaches lower under her crotch than the exact foot)
    # (her breasts always held; elsewhere never her arm, the cut eased so it
    # can never be ragged)
    # (a hard switch at the breasts' edge frayed it under her arm: the two
    # tests now meet smoothly, and the top is cut exactly, after shaping)
    not_arms = np.maximum(smooth_field(0.5 - arms, 30), (wsum("breast_l", "breast_r") - 0.03) * 10)
    body = AND(top_z + 0.02 - Z, Z - (CROTCH - 0.035), not_arms, legs)
    # Its front is laced over a strip of her skin, from under her breasts to
    # above her belt. The skin shows in a gap between bound edges, with
    # bronze eyelets either side. The lace crosses between them over her
    # skin, with a bar across the foot, and is tied at the top in a bow
    # under her breasts.
    lace_top, lace_bot = UNDERBUST - 0.008, CROTCH + 0.118
    half = 0.011
    def exact(q):
        # In front, her abs kept by one straight line from just shy of her
        # crotch up to under her breast; outside it, only her breast, the
        # edge following its underside up to her side. Behind, open from
        # beside her spine across to her side, up to a line a few
        # centimetres under the band. The thong between her legs, and her
        # lace opening's two straight sides.
        qx, qy, qz = q[:, 0], q[:, 1], q[:, 2]
        fr = ramp(-(qy - CROTCH_Y), -0.03, 0.03)
        r = qz - CROTCH
        reach = np.where(r < 0, 0.012 + 0.004 * np.clip(r / 0.035 + 1, 0, 1), 0.016 + 0.056 * np.clip(r, 0, None) / 0.24) + gusset(qz, 1.0)
        # (her breast held by its own form: inside the ellipsoid her cups are
        # built on, a little grown, so the edge runs round its underside as
        # one closed curve; a height for each width folded back on the
        # breast's curved side and left a hole there)
        c_b, R_b, ax_b = BREAST_HOLD
        r_ell = np.sqrt((((q - c_b) @ R_b.T / ax_b) ** 2).sum(1))
        front = np.maximum(qx + reach, (1.07 - r_ell) * 0.08)
        u = np.clip(-qx / 0.13, 0, 1)
        band = qz - (UNDERBUST + 0.015 + 0.01 * u)
        side = front * fr + band * (1 - fr)
        rq = np.maximum(r, 0)
        thong = (0.015 + 0.3 * rq) * fr + np.minimum(0.015 + 0.07 * rq, 0.018) * (1 - fr) + gusset(qz, fr) - np.abs(qx)
        right_q = np.where(qx < 0, np.maximum(side, thong), 1.0)
        slot = np.where((qz < lace_top + 0.018) & (qz > lace_bot - 0.045) & (fr > 0.5), np.abs(qx) - half, 1.0)
        # (and its foot under her crotch, cut with the rest, so the corner
        # where her leg line meets it is one clean turn)
        return np.minimum.reduce([right_q, slot, r + 0.024, top_at(q) - qz])

    corset = body
    lift, thick = 0.0035, 0.003
    rows = np.linspace(lace_top - 0.012, lace_bot + 0.012, 9)
    eye, enrm = {1: [], -1: []}, {1: [], -1: []}
    for sg in (1, -1):
        for z in rows:
            q = front_point(sg * (half + 0.0085), z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            eye[sg].append(q + n * (lift + thick + 0.0003))
            enrm[sg].append(n)

    def at_eye(sg, i):
        return eye[sg][i] + enrm[sg][i] * 0.0007

    laces = []
    nf = (enrm[1][-1] + enrm[-1][-1]) / 2
    laces += cord("ranger.lace_foot", bezier(at_eye(1, -1), (at_eye(1, -1) + at_eye(-1, -1)) / 2 + nf * 0.003, at_eye(-1, -1)),
                  "darkleather")
    for i in range(len(rows) - 1, 0, -1):
        for sg in (1, -1):
            # Each pair crosses at its middle, one over the other by turns
            # (a Bezier's middle is half its control's offset).
            a_, b_ = at_eye(sg, i), at_eye(-sg, i - 1)
            nm = (enrm[sg][i] + enrm[-sg][i - 1]) / 2
            up_ = 0.0044 if (sg > 0) == (i % 2 == 0) else -0.0012
            laces += cord(f"ranger.lace{i}{'ab'[sg > 0]}", bezier(a_, (a_ + b_) / 2 + nm * (0.0016 + up_), b_), "darkleather")
    # The bow: a knot just above the top eyelets, two loops, two tails.
    knot = front_point(0.0, rows[0] + 0.013)
    kn = np.array(SKIN_BVH.find_nearest(Vector(knot))[1][:])
    knot = knot + kn * (lift + thick + 0.0035)
    up_v = np.array([0, 0, 1.0]) - kn * kn[2]
    up_v /= np.linalg.norm(up_v)
    side_v = np.cross(up_v, kn)
    side_v *= np.sign(side_v[0])
    tips, tip_dirs = [], []
    for sg in (1, -1):
        a_ = at_eye(sg, 0)
        laces += cord(f"ranger.lace_top{'ab'[sg > 0]}", bezier(a_, (a_ + knot) / 2 + kn * 0.003, knot), "darkleather")
        ph = np.linspace(0, 2 * np.pi, 64)
        loop = (knot[None] + side_v[None] * (sg * 0.019 * (1 - np.cos(ph)))[:, None]
                + up_v[None] * (0.009 * np.sin(ph) - 0.005 * (1 - np.cos(ph)))[:, None]
                + kn[None] * (0.0035 * (1 - np.cos(ph)))[:, None])
        laces += cord(f"ranger.bow{'ab'[sg > 0]}", loop, "darkleather", r=0.0014)
        tail = []
        for t in np.linspace(0, 1, 40):
            z = knot[2] - 0.1 * t
            q = front_point(sg * (0.004 + 0.024 * t + 0.003 * np.sin(t * 6)), z)
            qn = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            tail.append(q + qn * (lift + thick + 0.0048 - 0.0008 * t))
        tail[0] = knot
        tail = np.array(tail)
        laces += cord(f"ranger.tail{'ab'[sg > 0]}", tail[:-3], "darkleather", r=0.0014)
        laces += cord(f"ranger.aglet{'ab'[sg > 0]}", tail[-4:], "bronze", r=0.0019)
    knot_ = domes("ranger.lace_knot", [knot - kn * 0.001], [kn], "darkleather", r=0.0042)
    for o_ in knot_:
        o_["hides"] = False
    laces += knot_

    def belt_lift(a):
        # Over the corset and pant (her left, her front) it clears them; on
        # her bare right hip and cheek it lies close to her skin.
        am = (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi
        over = np.where(am >= 0, 1 - ramp(am, 2.75, 3.05), ramp(am, -0.75, -0.45))
        return 0.0045 + 0.0065 * over

    # The belt and its buckle; the strap on her right thigh.
    bfront = front_point(0.035, float(belt_z(0.2)))
    bn_ = np.array(SKIN_BVH.find_nearest(Vector(bfront))[1][:])
    tz = leg_z("r", 0.16)
    tpt = front_point(LEG["r"][0][0] - 0.03, tz)
    tn_ = np.array(SKIN_BVH.find_nearest(Vector(tpt))[1][:])
    tz2 = leg_z("r", 0.29)
    tpt2 = front_point(LEG["r"][0][0] - 0.022, tz2)
    tn2_ = np.array(SKIN_BVH.find_nearest(Vector(tpt2))[1][:])
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    tops = {"r": KNEE_S - 0.03, "l": KNEE_S + 0.1}
    # Her left leg in light brown cloth. Its top reaches up under the
    # corset's edge all the way round, so no skin shows between them; its
    # foot goes down into her boot. Both ends are hidden, so neither is bound.
    pant = AND(X - 0.004, (edge_l + 0.03) - Z, (tops["l"] + 0.06) - LEG_S["l"], 0.3 - ARMW["l"])
    out = [
        *piece("ranger.corset", corset, "forestleather", lift=lift, thick=thick, smooth=8, iron=60, soften=20, slot="right",
               trim=("darkleather", 0.006, float(os.environ.get("CORSET_ROLL", "0.001")), 0.0013), filled=True, keep_off=("Head", "neck_01"), edge=6, cut=exact),   # (its roll 1 mm proud: at 0.6 the cup's own rise behind it covered its inner flank, judge 9)
        *grommets("ranger.eyelets", eye[1] + eye[-1], enrm[1] + enrm[-1], "bronze"),
        *laces,
        *girdle("ranger.belt", belt_z, 0.042, "brownleather", lift=belt_lift, thick=0.004),
        *frame("ranger.buckle", bfront + bn_ * 0.022, bn_, np.array([0, 0, 1.0]), 0.042, 0.052, "bronze", r=0.0028),
        *girdle("ranger.thighstrap", lambda a: np.full_like(a, tz), 0.028, "brownleather", lift=0.003, thick=0.003,
                mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz) < 0.05)),
        *frame("ranger.thighbuckle", tpt + tn_ * 0.008, tn_, np.array([0, 0, 1.0]), 0.03, 0.036, "bronze", r=0.0022),
        *girdle("ranger.thighstrap2", lambda a: np.full_like(a, tz2), 0.024, "brownleather", lift=0.003, thick=0.003,
                mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz2) < 0.05)),
        *frame("ranger.thighbuckle2", tpt2 + tn2_ * 0.008, tn2_, np.array([0, 0, 1.0]), 0.026, 0.032, "bronze", r=0.002),
        *piece("ranger.pant", pant, "browncloth", lift=0.0008, thick=0.001, smooth=6, soften=8, slot="right", bind=False),
    ]
    seam = []
    legl = LEGW["l"] > 0.6
    for z in np.linspace(CROTCH + 0.07, leg_z("l", tops["l"]) - 0.01, 40):
        m = legl & (np.abs(Z - z) < 0.004)
        if m.sum() > 3:
            seam.append(P[m][np.argmax(X[m])])
    seam = np.array(seam)
    for _ in range(4):
        seam[1:-1] = (seam[:-2] + 2 * seam[1:-1] + seam[2:]) / 4
    out += ribbon("ranger.pant_seam", list(seam), 0.005, "brownleather", lift=0.0022, thick=0.0012)
    # (two pauldrons for the owner to choose between: the lamed one, and the
    # leather spaulder with riveted plates)
    out += ranger_spaulder() if os.environ.get("PAULDRON", "leather") == "leather" else ranger_pauldron()
    for sd in "lr":
        # (the bracers satin and brushed round her forearm as the plates are
        # round her arm, judge 7)
        fa = head(f"lowerarm_{sd}")
        RIGID_UV[f"ranger.bracer_{sd}"] = (fa, (head(f"hand_{sd}") - fa) / np.linalg.norm(head(f"hand_{sd}") - fa), True)
        cz = leg_z(sd, tops[sd] + 0.02)
        # (the right boot, over her knee in front, cut 8 cm lower behind, as a
        # riding boot is, its cuff with it: cut level, the cuff stood 24 mm
        # into the back of her knee as she knelt)
        dip = {"r": 0.08, "l": 0.0}
        out += [
            *piece(f"ranger.bracer_{sd}", limb(sd, ELBOW_S + 0.04, WRIST_S - 0.015, legs=False), "bronze", lift=0.007, smooth=8,
                   soften=10, trim=edge(0.006, "brownleather"), studs="darksteel"),
            *piece(f"ranger.glove_{sd}", AND(limb(sd, WRIST_S - 0.03, 9.9, legs=False), 0.4 - fingers), "forestleather", lift=0.0015,
                   thick=0.0012, bevel=0.0004, soften=8),
            *BOOTS.boot(f"ranger.boot_{sd}", sd, tops[sd], dip[sd], BOOTS.RANGER, "bootleather"),
            *girdle(f"ranger.cuff_{sd}", lambda a, cz=cz, d=dip[sd]: cz - d * (1 - np.cos(a)) / 2, 0.06, "bootleather",
                    lift=0.01 if sd == "r" else 0.012, thick=0.003, trim=edge(0.005),
                    mask=(LEGW[sd] > 0.6) & (np.abs(Z - cz) < 0.07 + dip[sd]), flare=0.012),
        ]
    # The right boot laced up the front of her shin, below its cuff.
    kx = LEG["r"][1][0]
    ax0 = LEG["r"][2][0]
    z0, z1 = LEG["r"][2][2] + 0.07, leg_z("r", tops["r"] + 0.02) - 0.04
    lz = np.linspace(z1, z0, 9)
    bl = {}
    # (laid on the boot's shaft: 1.5 mm off its outer face)
    shell = BVHTree.FromPolygons([tuple(p) for p in BOOTS.SHELL["r"][0]], BOOTS.SHELL["r"][1].tolist())
    for sgn in (1, -1):
        e = []
        for z in lz:
            t = (LEG["r"][1][2] - z) / (LEG["r"][1][2] - LEG["r"][2][2])
            x = kx + (ax0 - kx) * t + 0.013 * sgn
            loc, n, _, _ = shell.find_nearest(Vector(front_point(x, z)))
            e.append(np.array(loc[:]) + np.array(n[:]) * (0.0025 + 0.0015))
        bl[sgn] = e
    for i in range(len(lz) - 1):
        for sg in (1, -1):
            out += ribbon(f"ranger.bootlace{i}{'ab'[sg > 0]}", [bl[sg][i], bl[-sg][i + 1]], 0.003, "darkleather", lift=0.0005,
                          thick=0.0012, snap=False)
    return out


CHANNELS = ["warden", "arcanist", "reaver", "ranger"]
BALD = set()
def hull_radius_grid(z0, z1, nu=160, step=0.004, mask=None, angles=None):
    """Her body's section (arms and hair left out) as a convex hull, its
    radius at each of `nu` angles round her (0 her front), every `step`
    in height from z0 to z1, and the centre it is measured from."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5) if mask is None else mask
    zs = np.arange(z0, z1 + step, step)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if angles is None else angles
    nu = len(a)
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    m0 = body_pts & (np.abs(Z - (z0 + z1) / 2) < 0.02)
    cxy = P[m0][:, :2].mean(0)
    R = np.zeros((len(zs), nu))
    for k, z in enumerate(zs):
        q = P[body_pts & (np.abs(Z - z) < 0.006)][:, :2]
        if len(q) < 8:
            # Past the end of what is measured: the nearest level's.
            R[k] = R[k - 1] if k else 0
            continue
        hv = q[ConvexHull(q).vertices]
        best = np.zeros(nu)
        for i in range(len(hv)):
            p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
            e = p1 - p0
            den = d[:, 0] * e[1] - d[:, 1] * e[0]
            ok = np.abs(den) > 1e-12
            t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
            u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
            best = np.where(ok & (t > 0) & (u >= 0) & (u <= 1), np.maximum(best, t), best)
        R[k] = best
    for k in range(len(zs) - 2, -1, -1):
        if not R[k].any():
            R[k] = R[k + 1]
    return zs, a, R, cxy


GARTER_Z = None


def stock_band(a):
    """The middle of a stocking's top band at angle a round her leg (0 her
    front): just under her crotch in front, dropping under her cheeks
    behind, so it frames them and never crosses them."""
    return np.full_like(np.asarray(a, float), CROTCH - 0.07)


def stock_top(sd):
    """Where a stocking's sheer part ends: inside its band, by the same
    angle round the leg (so the two always match)."""
    m = (LEGW[sd] > 0.6) & (np.abs(Z - (CROTCH - 0.05)) < 0.01)
    cx, cy = P[m][:, 0].mean(), P[m][:, 1].mean()
    a = np.arctan2(X - cx, -(Y - cy))
    return stock_band(a) + 0.004


def garters(name, sd, top_field, band_field, mkey, width=0.01):
    """Garter straps on one leg, front and back: each straight down her
    thigh from the garter belt (GARTER_Z) to the top of the stocking."""
    s_ = 1 if sd == "l" else -1
    out = []
    for k, (fy, xo) in enumerate(((-1, 0.1), (1, 0.08))):
        side = (np.sign(Y - CROTCH_Y) == fy) & (np.abs(X * s_ - xo) < 0.005)
        band = P[side & (band_field > 0)]
        if not len(band):
            continue
        z1 = band[:, 2].max() - 0.008
        ctrl = []
        for z in np.linspace(GARTER_Z, z1, 10):
            hit = BVH.ray_cast(Vector((xo * s_, 0.6 * fy, z)), Vector((0, -fy, 0)), 1.2)
            if hit[0] is not None:
                ctrl.append(np.array(hit[0][:]))
        if len(ctrl) > 2:
            out += ribbon(f"{name}{k}", ctrl, width, mkey, lift=0.004, thick=0.0015, snap=False)
    return out


def back_string(z0, z1, n=12):
    """A line down the cleft between her cheeks from z0 to z1: straight
    down the middle of her (midway between her buttock bones), each point
    where a ray from behind first meets her skin there."""
    xc = (head("glute_l")[0] + head("glute_r")[0]) / 2
    out = []
    for z in np.linspace(z0, z1, n):
        hit = BVH.ray_cast(Vector((xc, 0.6, z)), Vector((0, -1, 0)), 1.0)
        if hit[0] is not None:
            out.append(np.array(hit[0][:]))
    return out


def soft_weights(pts, src_idx=None, sigma=0.015, k=16):
    """Bone weights from her skin near each point, averaged over a couple of
    centimetres: smooth from point to point. (Taken from each point's
    nearest skin, a belt bridging her hollows took bones in jumps, and
    crumpled when she moved.)"""
    sp = P if src_idx is None else P[src_idx]
    sw = W if src_idx is None else W[src_idx]
    tree = cKDTree(sp)
    out = np.zeros((len(pts), W.shape[1]))
    for a in range(0, len(pts), 3000):
        dd, jj = tree.query(pts[a:a + 3000], k=k)
        ww = np.exp(-(dd / sigma) ** 2) + 1e-9
        ww /= ww.sum(1, keepdims=True)
        out[a:a + 3000] = np.einsum("pk,pkb->pb", ww, sw[jj].astype(float))
    return out / (out.sum(1, keepdims=True) + 1e-12)


def girdle(name, zfun, width, mkey, lift=0.004, thick=0.004, trim=None, rows=9, nu=160, mask=None, gap=None, arc=None, flare=0.0, span=None):
    """A belt round her, its middle at height zfun(angle) (angle 0 her
    front, rising toward her left), `width` tall, pulled taut over her
    (on the convex hull of her body there), so its edges are two clean
    even curves. It moves with the skin nearest each point of it."""
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if arc is None else np.linspace(arc[0], arc[1], nu)
    if span is not None:
        # From a lower to an upper line, each its own height at each angle.
        zlo, zhi = span(a)
        zc, half = (zlo + zhi) / 2, (zhi - zlo) / 2
    else:
        zc, half = zfun(a), np.full(nu, width / 2)
    zs, _, R, cxy = hull_radius_grid((zc - half).min() - 0.01, (zc + half).max() + 0.01, nu, mask=mask, angles=a)
    # The hull's corners shift from level to level, and a belt laid on them
    # creases along them (thin bright lines in its shine). So: eased round
    # her and up her, then lifted back out by however far that brought it
    # inside the hull anywhere near, eased too. Fair, and never in her.
    from scipy.ndimage import gaussian_filter, maximum_filter
    run_a = max(np.abs(np.diff(a)).mean() * float(np.mean(R)), 1e-4)
    sg_ = (0.008 / 0.004, 0.02 / run_a)
    md = ("nearest", "wrap" if arc is None else "nearest")
    R_s = gaussian_filter(R, sg_, mode=md)
    lack = maximum_filter(np.maximum(R - R_s, 0), size=(5, max(3, int(0.03 / run_a))), mode=md)
    R = R_s + gaussian_filter(lack, sg_, mode=md) * 1.1
    # (rows fine enough that a trim band cut along the edge is a clean line)
    rows = max(rows, int(np.ceil(width / 0.0016)) | 1)
    off = np.linspace(-1, 1, rows)
    pos = np.zeros((rows, nu, 3))
    # (`lift` may be a function of the angle: a belt over a garment on one
    # side and bare skin on the other stands off each by what is under it)
    lift_a = lift(a) if callable(lift) else lift
    for k, o in enumerate(off):
        z = zc + o * half
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        rl = r + lift_a + flare * k / (rows - 1)
        pos[k] = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
    for _ in range(3):
        if arc is None:
            pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
        else:
            pos[:, 1:-1] = (pos[:, :-2] + 2 * pos[:, 1:-1] + pos[:, 2:]) / 4
    seams = []
    if kind(mkey) == "leather" and width >= 0.012:
        inset = 0.003 if width < 0.03 else 0.0038
        for sgn in (1, -1):
            o_ = sgn * (1 - inset / np.maximum(half, inset * 2))
            z = zc + o_ * half
            r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
            rl = r + lift_a + flare * (o_ + 1) / 2
            ln = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
            for _ in range(3):
                if arc is None:
                    ln = (np.roll(ln, 1, 0) + 2 * ln + np.roll(ln, -1, 0)) / 4
                else:
                    ln[1:-1] = (ln[:-2] + 2 * ln[1:-1] + ln[2:]) / 4
            radial = np.stack([np.sin(a), -np.cos(a), np.zeros_like(a)], -1)
            tgl = np.gradient(ln, axis=0)
            seams.append((ln + radial * (thick + 0.0001), radial, tgl))
    pos = pos.reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    if arc is None:
        idx = np.c_[idx, idx[:, :1]].ravel()
        tris = idx[grid(rows, nu + 1)]
    else:
        tris = grid(rows, nu)
    if gap is not None:
        # Open where it would meet its twin (between her thighs, hidden).
        tris = tris[(np.abs(pos[tris][:, :, 0]) > gap).all(1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    src = np.where(mask)[0] if mask is not None else np.arange(len(P))
    # (one set of weights across its width, eased along it: it moves as a belt)
    wt = soft_weights(pos, src).reshape(rows, nu, -1)
    wt[:] = wt.mean(0, keepdims=True)
    for _ in range(12):
        if arc is None:
            wt = (np.roll(wt, 1, 1) + 2 * wt + np.roll(wt, -1, 1)) / 4
        else:
            wt[:, 1:-1] = (wt[:, :-2] + 2 * wt[:, 1:-1] + wt[:, 2:]) / 4
    wt = wt.reshape(len(pos), -1)
    edge = ((1 - np.abs(off))[:, None] * half[None, :]).ravel()
    if arc is not None:
        run = np.abs(np.diff(a)).mean() * np.mean(R)
        col = np.tile(np.arange(nu), rows)
        edge = np.minimum(edge, np.minimum(col, nu - 1 - col) * run)
    at = np.hstack([nor, wt, edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = False
    for k, (ln, rn, tgl) in enumerate(seams):
        made += stitches(f"{name}_stitch{k}", ln, rn, tgl, pos, at[:, 3:3 + NB], closed=arc is None)
    if seams:
        made[0]["geo_stitch"] = True
    print("GIRDLE", name)
    return made


def section(z, keep):
    """Her outline at height z, as points (x, y): where her triangles whose
    points are all `keep` cross that level."""
    tri = TRI[keep[TRI].all(1)]
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        p, q = P[tri[:, i]], P[tri[:, j]]
        s = (p[:, 2] - z) * (q[:, 2] - z) < 0
        t = (z - p[s, 2]) / (q[s, 2] - p[s, 2])
        out.append(p[s, :2] + t[:, None] * (q[s, :2] - p[s, :2]))
    return np.vstack(out)


def bandeau(name, mkey, zc, width, lift=0.004, thick=0.003, trim=None, rows=11, nu=120):
    """A strip of leather round her chest at height `zc`, `width` tall,
    pulled taut: each row of it lies on the convex hull of her body's
    section there (her arms left out), so it runs straight across the
    cleavage from breast to breast as a strap does, never into it. It
    moves with the skin nearest each point of it (her breasts' springs
    included)."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5)
    zs = np.linspace(zc - width / 2, zc + width / 2, rows)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    R = np.zeros((rows, nu))
    cxy = None
    for k, z in enumerate(zs):
        # Her outline at this row's own height, exactly (where her triangles
        # cross it). (The hull of her points within a centimetre of it took
        # the fuller breast below for the row above: the upper rows stood 5 to
        # 20 mm off her upper breast, and a camera at her side saw in behind
        # the band to her areola as she vaulted.)
        q = section(z, body_pts)
        if cxy is None:
            cxy = q.mean(0)
        h = ConvexHull(q)
        hv = q[h.vertices]
        d = np.stack([np.sin(a), -np.cos(a)], 1)
        best = np.zeros(nu)
        for i in range(len(hv)):
            p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
            e = p1 - p0
            den = d[:, 0] * e[1] - d[:, 1] * e[0]
            ok = np.abs(den) > 1e-12
            t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
            u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
            hit = ok & (t > 0) & (u >= 0) & (u <= 1)
            best = np.where(hit, np.maximum(best, t), best)
        R[k] = best
    for _ in range(3):
        R[1:-1] = (R[:-2] + 2 * R[1:-1] + R[2:]) / 4
        R = (np.roll(R, 1, 1) + 2 * R + np.roll(R, -1, 1)) / 4
    R = R + lift
    # Its top and bottom edges pressed onto her, as a strap's edge bites:
    # standing off by its lift, the camera above saw down behind its top.
    R[0] -= lift + 0.001
    R[-1] -= lift + 0.001
    R[1] -= (lift + 0.001) * 0.4
    R[-2] -= (lift + 0.001) * 0.4
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], rows, 0)
    pos = np.stack([cxy[0] + R * np.sin(aa), cxy[1] - R * np.cos(aa), zz], -1).reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pos)
    edge = np.minimum(pos[:, 2] - zs[0], zs[-1] - pos[:, 2])
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    # (all of it on her skin's own weights, her arms' share kept: steadied, it
    # stayed put as her arm drew the skin at her breasts' sides from under it)
    UNSTEADIED.add(name)
    # (its edges bound with a rolled binding, as every other piece's are: a
    # flat strip laid over the edge showed the sheet's own edge as a pale
    # sliver between two dark lines, and stretched at a corner, judge 5)
    beads = []
    if trim:
        tkey, w, h, tt = trim
        pos, beads = bind_edges(name, pos, at, tris, tkey, max(w, 0.005), max(h, 0.0006), 0.0018, thick,
                                stitch=kind(mkey) == "leather")
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, 0.001)] + beads
    for o in made:
        o["hides"] = o is made[0]
    # (her skin tucked under it only 3.5 mm: it moves with her skin, springs
    # and all; tucked 6 mm, as close pieces are, the gap under its taut top
    # edge showed the tuck as a dark slit, seen from above as she ran)
    made[0]["tuck"] = 0.35
    print("BANDEAU", name, "at %.3f, %.3f tall" % (zc, width))
    return made


# (armor 15 r1, 22 Oct: THE WRAP. Max judge J1 on the reaver's bandeau at 1:1: "still rigid spheres. The band is
# a straight tube that squeezes nothing, and the breasts below it are perfect half-spheres." The bandeau's rows lay
# on the convex hull of her chest, 1.5 mm off: a rigid cylinder bridging the cleavage, standing off her, pressing
# nothing, with the lower half of each breast bare below it. The wrap is leather worn tight on a soft body:
#   - its rows lie on her own outline at each height (her final skin, heroine.glb: the shape the game draws), so it
#     follows each breast's curve; between them it is drawn in toward her sternum, WRAP_DIP of the way from the
#     hull to her skin (a band can't reach the bottom of her cleavage);
#   - it is pressed into her: its inner face WRAP_PRESS[0] under her rest skin across its middle, WRAP_PRESS[1] at
#     its edges (eased over WRAP_PRESS[2]), so its outer face sits on her and its edges bite in, her skin past them
#     standing proud of it as flesh swells from under a tight edge (the skin under it is tucked: wrap_tuck_post.py
#     writes reaver.top's tuck from this shape, so no ray of the old rule decides it);
#   - it covers her breasts down to WRAP_Z[0] (about a centimetre above her underbust fold, the lower edge pressed in)
#     and up to WRAP_Z[1] over her nipples, both from the build's nipple height; at the front it is gathered at the
#     centre, the top drawn down WRAP_PINCH[0] and the bottom up WRAP_PINCH[1] over a Gaussian WRAP_PINCH[2] wide.)
WRAP_GLB = os.environ.get("WRAP_GLB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb"))
WRAP_DIP = float(os.environ.get("WRAP_DIP", "0.5"))
WRAP_TAUT = float(os.environ.get("WRAP_TAUT", "1.0"))  # (d3: how much of any hollow but the cleavage it bridges)
WRAP_PRESS = [float(v) for v in os.environ.get("WRAP_PRESS", "0.002,0.0045,0.004").split(",")]
WRAP_Z = [float(v) for v in os.environ.get("WRAP_Z", "-0.040,0.024").split(",")]
WRAP_PINCH = [float(v) for v in os.environ.get("WRAP_PINCH", "0.012,0.018,0.025").split(",")]
WRAP_ON = os.environ.get("WRAP", "1") == "1"
WRAP_BUMP = float(os.environ.get("WRAP_BUMP", "0.001"))
# (r3: its top edge drawn down WRAP_SIDE[0] at her sides and back, eased in from WRAP_SIDE[1] degrees past her
# nipples' angle round her to WRAP_SIDE[2] degrees off the front; the front from breast to breast as it was. r2's top
# ran level round her at nipple + 2.4 cm, and where her arm joins her (spine_03 + upperarm_share skin, 1.443-1.448 m)
# her skin came 15-18 mm through it at rest)
WRAP_SIDE = [float(v) for v in os.environ.get("WRAP_SIDE", "0.015,12,95").split(",")]
WRAP_SKINW = {}  # (r3: pieces whose final points take her final skin's weights again after finish()'s easing)


def _wrap_skin():
    """Her final skin (heroine.glb's body, welded), in this scene's frame, less her arms and hair."""
    import heroine_neck as hn_
    from wrap_post import skin_union
    G_ = hn_._Gl(WRAP_GLB)
    # (r3: her body AND its back graft (skin_graft, her upper back from 1.386 m): without it the wrap's back saw no
    # skin of hers and lay on the front's hull, 9-25 mm inside her back)
    Ug, Fg, J_, Wt_, _ = skin_union(G_)
    Q = np.c_[Ug[:, 0], -Ug[:, 2], Ug[:, 1]]
    j_ = cKDTree(P).query(Q)[1]
    # (r2: her arms are taken out of each outline by shape, _wrap_torso; by weight (r1: arm weight 0.25 and over) it
    # took her back and flanks too, which carry her arms' share at this height, and the band's sides and back fell
    # inside her, 14-20 mm under her skin at rest)
    keep = HAIR[j_] < 0.5
    # (and her final skin's own weights as this scene's BONES: the wrap takes the weights of the skin under it, so her
    # skin can't slide past its sides when her arms swing (r1: 30 mm through at the sides))
    g_ = G_.g
    hb_ = [n for n in g_["nodes"] if n.get("name") == "Heroine"][0]
    names_ = [g_["nodes"][k]["name"] for k in g_["skins"][hb_["skin"]]["joints"]]
    col_ = np.array([BONES.index(n) if n in BONES else -1 for n in names_])
    Wq = np.zeros((len(Q), NB))
    c_ = col_[J_]
    for k in range(J_.shape[1]):
        ok_ = c_[:, k] >= 0
        np.add.at(Wq, (np.nonzero(ok_)[0], c_[ok_, k]), Wt_[ok_, k])
    Wq /= np.maximum(Wq.sum(1, keepdims=True), 1e-9)
    return Q, Fg[keep[Fg].all(1)], Wq


def _wrap_segments(Q, F, z):
    """Her outline at height z as segments (n, 2, 2): where each of her triangles crosses it."""
    zt = Q[F, 2]
    f = F[(zt.min(1) < z) & (zt.max(1) > z)]
    pts = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        p, q = Q[f[:, i]], Q[f[:, j]]
        s = (p[:, 2] - z) * (q[:, 2] - z) < 0
        t = np.where(s, (z - p[:, 2]) / np.where(s, q[:, 2] - p[:, 2], 1), np.nan)
        pts.append(p[:, :2] + t[:, None] * (q[:, :2] - p[:, :2]))
    pts = np.stack(pts, 1)
    ok = np.isfinite(pts[:, :, 0])
    good = ok.sum(1) == 2
    o = np.argsort(~ok[good], 1, kind="stable")[:, :2]
    return np.take_along_axis(pts[good], o[:, :, None], 1)


def _wrap_torso(seg, xmax=0.168):
    """Her torso's outline alone: each loop of seg lying wholly past 12 cm off her middle (an arm) dropped, and where an
    arm joins her (the armpit) anything past xmax."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = len(seg)
    if n == 0:
        return seg
    pts = seg.reshape(-1, 2)
    pr = cKDTree(pts).query_pairs(1e-6, output_type="ndarray").reshape(-1, 2)
    i = np.r_[np.arange(n) * 2, pr[:, 0]]
    j = np.r_[np.arange(n) * 2 + 1, pr[:, 1]]
    _, lab = connected_components(coo_matrix((np.ones(len(i)), (i, j)), shape=(2 * n, 2 * n)), directed=False)
    near = np.zeros(lab.max() + 1)
    np.maximum.at(near, lab, (np.abs(pts[:, 0]) < 0.12).astype(float))
    lab = lab[0::2]
    ok = (near[lab] > 0) & (np.abs(seg[:, :, 0]).max(1) < xmax)
    return seg[ok]


def _wrap_rays(seg, c, a):
    """The farthest crossing along each ray from c at angles a (0 in front, -y), of segments seg (0: none)."""
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    p0, e = seg[:, 0] - c, seg[:, 1] - seg[:, 0]
    den = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]
    ok = np.abs(den) > 1e-12
    dn = np.where(ok, den, 1)
    t = (p0[None, :, 0] * e[None, :, 1] - p0[None, :, 1] * e[None, :, 0]) / dn
    u = (p0[None, :, 0] * d[:, None, 1] - p0[None, :, 1] * d[:, None, 0]) / dn
    hit = ok & (t > 0) & (u >= 0) & (u <= 1)
    return np.where(hit, t, 0).max(1)


def wrap(name, mkey, zb, zt, thick=0.003, trim=None, rows=41, nu=240, budget=5000):
    """THE WRAP (above): a fitted leather wrap round her breasts from zb to zt."""
    from scipy.spatial import ConvexHull
    from scipy.signal import savgol_filter
    Q, F, Wq = _wrap_skin()
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    # (its edges round her: gathered at the front centre)
    g = np.exp(-0.5 * (0.15 * np.sin(a) / WRAP_PINCH[2]) ** 2) * (np.cos(a) > 0)
    zb_a, zt_a = zb + WRAP_PINCH[1] * g, zt - WRAP_PINCH[0] * g
    _pt = _wrap_torso(_wrap_segments(Q, F, (zb + zt) / 2)).reshape(-1, 2)
    cxy = (_pt.min(0) + _pt.max(0)) / 2
    an = np.degrees(np.mean([abs(np.arctan2(NIPPLE[sd][0] - cxy[0], -(NIPPLE[sd][1] - cxy[1]))) for sd in "lr"]))
    ad = np.degrees(np.abs(np.arctan2(np.sin(a), np.cos(a))))
    sd_ = np.clip((ad - (an + WRAP_SIDE[1])) / (WRAP_SIDE[2] - an - WRAP_SIDE[1]), 0, 1)
    zt_a = zt_a - WRAP_SIDE[0] * sd_ * sd_ * (3 - 2 * sd_)
    print("WRAP side drop: nipples at %.1f deg round her; top down %.1f mm from %.1f to %.1f deg" % (
        an, 1000 * WRAP_SIDE[0], an + WRAP_SIDE[1], WRAP_SIDE[2]))
    zl = np.arange(zb - 0.004, zt + 0.0045, 0.001)
    # (r2: the centre the middle of her outline's bounding box at mid-height; the mean of the outline's points, pulled
    # forward by her breasts' dense mesh, sat in front of her sternum on the higher band, its front rays met no skin of
    # hers and the whole front fell back to the hull, a tube bridging her cleavage)
    Rr, Rh = np.zeros((len(zl), nu)), np.zeros((len(zl), nu))
    for k, z in enumerate(zl):
        seg = _wrap_torso(_wrap_segments(Q, F, z))
        Rr[k] = _wrap_rays(seg, cxy, a)
        pt = seg.reshape(-1, 2)
        hv = pt[ConvexHull(pt).vertices]
        Rh[k] = _wrap_rays(np.stack([hv, np.roll(hv, -1, 0)], 1), cxy, a)
    # (her own outline, drawn in WRAP_DIP of the way where the hull bridges a hollow; where the ray meets no skin of
    # hers (her arms left out) or the hollow is past 3.5 cm off the front, the hull)
    gap = Rh - Rr
    front = np.cos(a)[None, :] > 0.5
    bad = (Rr <= 0) | ((gap > 0.035) & ~front)
    # (d3, 22 Oct, the owner: "is this a dent in reaver". Only the cleavage is drawn in: each row's run of hollow
    # holding her front centre, out to where the hull meets her breasts. Every other hollow is bridged, the band
    # taut on the hull: the side of her chest, between each breast and her back (her skin 18-25 mm under the hull
    # at 85-100 deg round her), took the band WRAP_DIP of the way in, a 10-12 mm dent beside each cup, a dark
    # vertical patch by day and night. WRAP_TAUT of the hollow bridged there (1: the hull))
    cl = np.zeros_like(gap, bool)
    for k in range(len(zl)):
        for st in (1, -1):
            i = 0
            while abs(i) < nu // 2 and gap[k, i % nu] > 0.0005:
                cl[k, i % nu] = True
                i += st
    Rs = np.where(bad, Rh, np.where(cl, Rr + WRAP_DIP * gap, Rr + WRAP_TAUT * gap))
    # (her nipples' bumps and the hull's bridges over her arms' gaps taken out: the wrap no higher than WRAP_BUMP over
    # its own shape smoothed ~1 cm round her and ~5 mm up and down, three times; r1's first build carried each
    # nipple's 2-4 mm bump through the leather as a poke and a dark spot by day, and a step at her arm)
    # (r2: the smoothing a quadratic fit, Savitzky-Golay, ~25 mm up and down and round her: a plain blur of a breast's
    # convex outline lies inside it, and r1's clamp to it cut the band up to a centimetre into her lower poles (her skin
    # through it in ragged patches) and dimpled each apex (a soft dark spot by day); a quadratic fit keeps her curve
    # and still takes out the nipple's narrow bump)
    Rs0 = Rs.copy()
    for _ in range(3):
        G_ = savgol_filter(Rs, 25, 2, axis=0, mode="interp")
        G_ = savgol_filter(G_, 7, 2, axis=1, mode="wrap")
        Rs = np.minimum(Rs, G_ + WRAP_BUMP)
    cut = (Rs0 - Rs)[:, np.cos(a) > 0.3]
    print("WRAP bump clamp: cut max %.1f mm, p99 %.1f mm" % (1000 * cut.max(), 1000 * np.percentile(cut, 99)))
    for _ in range(10):
        Rs[1:-1] = (Rs[:-2] + 2 * Rs[1:-1] + Rs[2:]) / 4
    for _ in range(6):
        Rs = (np.roll(Rs, 1, 1) + 2 * Rs + np.roll(Rs, -1, 1)) / 4
    u = np.linspace(0, 1, rows)
    zz = zb_a[None, :] + u[:, None] * (zt_a - zb_a)[None, :]
    R = np.stack([np.interp(zz[:, i], zl, Rs[:, i]) for i in range(nu)], 1)
    edge = np.minimum(zz - zb_a[None, :], zt_a[None, :] - zz)
    R = R - (WRAP_PRESS[0] + (WRAP_PRESS[1] - WRAP_PRESS[0]) * np.exp(-edge / WRAP_PRESS[2]))
    aa = np.repeat(a[None, :], rows, 0)
    pos = np.stack([cxy[0] + R * np.sin(aa), cxy[1] - R * np.cos(aa), zz], -1).reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    used = np.unique(F)
    dq, jq = cKDTree(Q[used]).query(pos, k=4)
    iw = 1.0 / np.maximum(dq, 1e-4)
    wq = (Wq[used[jq]] * iw[:, :, None]).sum(1) / iw.sum(1)[:, None]
    at = np.hstack([nor, wq, edge.reshape(-1, 1)])
    UNSTEADIED.add(name)
    WRAP_SKINW[name] = (Q[used], Wq[used])
    beads = []
    if trim:
        tkey, w, h, tt = trim
        pos, beads = bind_edges(name, pos, at, tris, tkey, max(w, 0.005), max(h, 0.0006), 0.0018, thick,
                                stitch=kind(mkey) == "leather")
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, 0.001, budget=budget)] + beads
    for o in made:
        o["hides"] = o is made[0]
    made[0]["tuck"] = 0.8
    # (the shape the tuck post-step reads: centre, angles, rows' heights and inner radii, this scene's frame)
    np.savez(os.path.join(os.path.dirname(OUT), "wrap_%s.npz" % name), cxy=cxy, a=a, zz=zz, R=R, thick=thick)
    print("WRAP %s: %.3f to %.3f, dip %.2f, press %s; cleavage drawn in %.1f of %.1f mm" % (
        name, zb, zt, WRAP_DIP, WRAP_PRESS, 1000 * (Rs - Rr)[:, 0].mean(), 1000 * gap[:, 0].mean()))
    return made


def limb_angle(sd, legs=True):
    """Each point's angle round a limb's upper segment (radians)."""
    a, b = (LEG[sd][0], LEG[sd][1]) if legs else (ARM[sd][0], ARM[sd][1])
    ax = (b - a) / np.linalg.norm(b - a)
    ref = np.cross(ax, [1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.cross(ax, [0, 1.0, 0])
    ref /= np.linalg.norm(ref)
    sec = np.cross(ax, ref)
    d = P - a
    return np.arctan2(d @ sec, d @ ref)


def zigzag_band(sd, s0, legs=True, width=0.014, amp=0.014, teeth=6):
    """A tattooed band round a limb at `s0` along it: a zigzag line,
    `teeth` points round, `amp` high."""
    S = LEG_S[sd] if legs else ARM_S[sd]
    Wm = LEGW[sd] if legs else ARMW[sd]
    th = limb_angle(sd, legs)
    tri = np.arcsin(np.sin(teeth * th)) / (np.pi / 2)
    return AND(width / 2 - np.abs(S - s0 - amp * tri), Wm - 0.5)


def reaver():
    """The reaver: a loincloth panel in front on a belt slung low on her hips, a
    G-string beneath, a strip of leather
    across her breasts, a fur half cape over her left shoulder, fur-topped
    boots and fur cuffs at her wrists, leather bracers, and tattoos: zigzag
    bands round her right arm and left thigh."""
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.005, key="darkleather"):
        return (key, w, 0.0004, 0.0013)

    nz = (NIPPLE["l"][2] + NIPPLE["r"][2]) / 2
    # Slung low, where a brief's waistband would run: low in front and
    # behind, rising over the hip bones.
    bz0 = CROTCH + 0.12
    # Behind, it rides up over the top of her cheeks, so they stand clear
    # of it and the string shows from the belt down.
    belt_z = bz0 + 0.05 * np.clip(np.abs(X) / 0.15, 0, 1) ** 2 + 0.07 * (1 - FRONT)
    belt = AND(0.02 - np.abs(Z - belt_z), 0.3 - arms)
    # Fur over her left shoulder only (a mantle down her back clashed
    # with the strap).
    cape = cap(shoulder("l"), 0.13)
    buckle_at = front_point(0.0, bz0)
    buckle_n = np.array(SKIN_BVH.find_nearest(Vector(buckle_at))[1][:])
    # The cord: round the base of her neck behind, over her collarbones, and
    # down to a point above her cleavage; the fangs along its lowest part.
    neck_z = head("neck_01")[2]
    cord = [np.array([0.0, 0.07, neck_z + 0.02]), np.array([0.055, 0.03, neck_z]), np.array([0.07, -0.04, neck_z - 0.045]),
            front_point(0.035, nz + 0.06), front_point(0.0, nz + 0.035), front_point(-0.035, nz + 0.06),
            np.array([-0.07, -0.04, neck_z - 0.045]), np.array([-0.055, 0.03, neck_z]), np.array([0.0, 0.07, neck_z + 0.02])]
    path = on_surface(cord[2:7], step=0.003)
    if TAUT_CORD and NAPE_CORD >= 0:
        # (NAPE_CORD: its back laid under the cap from the start, so the cap only holds it, never flattens it)
        cord_t = [q.copy() for q in cord]
        for k_, dz_ in ((0, 0.004), (8, 0.004), (1, 0.012), (7, 0.012)):
            cord_t[k_][2] = neck_z - NAPE_CORD - dz_
    else:
        cord_t = cord
    for _ in range(3):
        path[1:-1] = (path[:-2] + 2 * path[1:-1] + path[2:]) / 4
    low = path[np.argsort(path[:, 2])[:len(path) // 3]]
    low = low[np.argsort(low[:, 0])]
    pick = np.linspace(0, len(low) - 1, 7).round().astype(int)
    fang_at = low[pick]
    fang_out = np.array([SKIN_BVH.find_nearest(Vector(q))[1][:] for q in fang_at])
    fang_down = np.tile([0.0, 0.0, -1.0], (len(fang_at), 1))
    out = [
        # (pulled tight: standing off her by 4 mm, the camera above saw down
        # behind its top to her areola as she ran)
        *(wrap("reaver.strap", "oldleather", nz + WRAP_Z[0], nz + WRAP_Z[1], trim=edge()) if WRAP_ON else
          bandeau("reaver.strap", "oldleather", nz - 0.01, 0.07, lift=0.0015, trim=edge())),
        *girdle("reaver.belt", lambda a: bz0 + 0.05 * np.clip(np.abs(0.17 * np.sin(a)) / 0.15, 0, 1) ** 2
               + 0.07 * ramp(-np.cos(a), -0.15, 0.35), 0.036, "oldleather", lift=0.006, thick=0.004, trim=edge(0.005)),
        *frame("reaver.buckle", buckle_at + buckle_n * 0.017, buckle_n, np.array([0, 0, 1.0]), 0.05, 0.042, "rust", r=0.0034,
               corner=0.006),
        # The panel's hem cut into a fringe: strips with V-notches between.
        # (columns ~1 mm apart: any closer and the weld merges them)
        # (Body 17, judge at the 1:1 town close-up: "a flat grey plank down to the knee". REAVER_PANEL=old: as it was.
        # Now ~30% shorter (its middle 0.53 -> 0.37 m, ending well above the knee's fur), a hem that waves, its sides
        # tapering in, one crease down it, the tongues splayed; the lower half folds over her thigh: helpers "fold")
        *(hanging("reaver.loin_front", -0.33, 0.33, bz0, fringe(lambda u: 0.52 + 0.07 * u * u, 11, 0.075, notch=0.26), "oldleather",
                  flare=0.06, lift=0.016, trim=edge(0.01), nu=120, strips=11, one_piece=0.7) if REAVER_PANEL == "old" else
          hanging("reaver.loin_front", -0.34, 0.34, bz0,
                  fringe(lambda u: bz0 - 0.37 + 0.045 * u * u + 0.007 * np.sin(5.3 * u + 0.8) + 0.004 * np.sin(11.7 * u + 2.1), 9, 0.05, notch=0.3),
                  "oldleather", flare=0.05, lift=0.016, trim=edge(PANEL_EDGE_W, PANEL_EDGE), nu=120, strips=9, one_piece=0.7,
                  taper=PANEL_TAPER, crease=(0.07, 0.035, 0.006), splay=PANEL_SPLAY, notch_depth=0.05, wrap=PANEL_WRAP)),
        # Wolf fangs on a cord round her neck, hanging into her cleavage:
        # trophies of the Verge's wolves.
        # (TAUT_CORD: laid from inside the base of her neck, so no point jumps from her collarbone to her neck
        # as the skin nearest it did, and taut over the hollow between them)
        *(ribbon("reaver.cord", cord_t, 0.004, "blackleather", lift=0.0025, thick=0.003, taut=0.008,
                 centre=np.array([0.0, 0.005, neck_z - 0.05]), closed=NAPE_CORD >= 0,
                 nape=(neck_z - NAPE_CORD, -0.02, head("neck_01")[1]) if NAPE_CORD >= 0 else None) if TAUT_CORD else
          ribbon("reaver.cord", cord, 0.004, "blackleather", lift=0.0025, thick=0.003)),
        *fangs("reaver.fangs", fang_at, fang_out, fang_down, "bone"),
        # Beneath it a G-string hung from the belt itself: a narrow front
        # (hidden by the panel) and a string down the back, both running up
        # into the belt, so belt and G-string are one piece of gear.
        *piece("reaver.gstring", OR(
            AND(FRONT - 0.3, np.minimum(0.015 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03)),
            ), "oldleather", lift=0.002, smooth=2, soften=0),
        # (opening into the gusset at its foot, as on the warden's thong)
        *ribbon("reaver.gstring_back", back_string(bz0 + 0.07, CROTCH + 0.012), 0.022, "oldleather", lift=0.003, thick=0.004,
                trim=edge(0.004, "blackleather"), snap=False, hides=True, flare=(0.028, 0.03)),
        # (under her a gusset wider than the string, close under her and
        # following her skin, as on the warden's thong)
        *gusset("reaver.gstring_gusset", "oldleather", GAP_F - 0.006, back_string(bz0 + 0.07, CROTCH + 0.012)[-1][1] + 0.015),
        *piece("reaver.cape", cape, "fur", lift=0.012, thick=0.004, smooth=12, soften=10, keep_off=("Head",)),
        *piece("reaver.tattoo_arm", OR(zigzag_band("r", ELBOW_S - 0.12, legs=False), zigzag_band("r", ELBOW_S - 0.06, legs=False, amp=0.01, width=0.012)), "ink", lift=0.0012, thick=0.0002, bevel=0.0, soften=0, budget=10 ** 7),
        *piece("reaver.tattoo_thigh", OR(zigzag_band("l", 0.15), zigzag_band("l", 0.22, amp=0.01, width=0.013)), "ink", lift=0.0012, thick=0.0002, bevel=0.0, soften=0, budget=10 ** 7),
    ]
    for sd in "lr":
        out += [
            *piece(f"reaver.bracer_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.04, legs=False), "oldleather", lift=0.004, smooth=6, trim=edge(), studs="rust"),
            *piece(f"reaver.wristfur_{sd}", limb(sd, WRIST_S - 0.05, WRIST_S + 0.005, legs=False), "fur", lift=0.012, thick=0.012, smooth=8),
            *(piece(f"reaver.boot_{sd}", limb(sd, KNEE_S - 0.01, 9.9), "oldleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03)
              if REAVER_BOOT == "old" else
              # (Body 17, judge at the 1:1 town close-up: "dark stockings over bare feet"; then the Ranger's last
              # reskinned, out of her (her toes through it at rest) and not hers: the coordinator wants rough hide
              # wrapped on her own foot. A turnshoe, see reaver_turnshoe)
              reaver_turnshoe(sd)),
            *piece(f"reaver.bootfur_{sd}", limb(sd, KNEE_S - 0.05, KNEE_S + 0.06), "fur", lift=0.016, thick=0.016, smooth=10),
        ]
    return out


# (Body 17) The reaver's boots: rough hide on her own foot, a turnshoe. Her sock as it was (her leg and foot
# lifted 5 mm, the foot on its convex hull: one rounded toe box, no toes), and on it, all cheap rolled tubes
# (tube()) moving with the sock under them:
#   - a rawhide sole edge round the foot just over its floor (TS_SOLE_UP), TS_SOLE wide and 3 mm proud, a black
#     bead under it at the ground;
#   - a moccasin seam over her toes, a U from beside the ball round the front, gathered (short ribs outside it);
#   - two rawhide thongs crossed up her shin from an ankle ring to under the fur cuff (REAVER_THONGS turns
#     each, crossing in front at every turn, rising faster in front than behind so the crosses stand up), the
#     second over the first in front and under it behind.
REAVER_THONGS = int(os.environ.get("REAVER_THONGS", "4"))
HULL_PAD = float(os.environ.get("TS_PAD", "0.002"))
HULL_FILL = {f"reaver.boot_{sd}": int(os.environ.get("TS_FILL", "150")) for sd in "lr"} if REAVER_BOOT != "old" else {}
TS_SOLE_UP = float(os.environ.get("TS_SOLE_UP", "0.007"))  # (the sole edge's middle, this far over the sock's floor)
TS_SOLE = float(os.environ.get("TS_SOLE", "0.009"))         # (its width across the corner)
TS_THONG = float(os.environ.get("TS_THONG", "0.014"))       # (each thong's width: ~7 px on a 250 px boot)
# (Body 18: the shoe's hide and thong keys (REAVER_HIDE=oldleather REAVER_THONG_KEY=darkleather: Body 17's), the puckers
# every TS_PUCKER m, TS_PUCKER_SIZE "long,short,width,proud" (m))
REAVER_HIDE = os.environ.get("REAVER_HIDE", "hide")
REAVER_THONG_KEY = os.environ.get("REAVER_THONG_KEY", "rawhide")
TS_PUCKER = float(os.environ.get("TS_PUCKER", "0.016"))
TS_GAPS = [float(v) for v in os.environ.get("TS_GAPS", "1.18,0.84,1.1,0.88").split(",")]
TS_KNOT = os.environ.get("TS_KNOT", "1") == "1"
TS_PUCKER_SIZE = [float(v) for v in os.environ.get("TS_PUCKER_SIZE", "0.015,0.010,0.0042,0.0018").split(",")]


def _ts_resample(c, step, closed):
    c = np.asarray(c, float)
    cc = np.vstack([c, c[:1]]) if closed else c
    sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]
    n = max(4, int(round(sl[-1] / step)))
    t = np.linspace(0, sl[-1], n, endpoint=not closed)
    return np.c_[[np.interp(t, sl, cc[:, k]) for k in range(3)]].T


def _ts_smooth(c, rounds, closed):
    c = np.asarray(c, float).copy()
    for _ in range(rounds):
        if closed:
            c = (np.roll(c, 1, 0) + 2 * c + np.roll(c, -1, 0)) / 4
        else:
            c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
    return c


def reaver_turnshoe(sd):
    name = f"reaver.boot_{sd}"
    out = list(piece(name, limb(sd, KNEE_S - 0.01, 9.9), REAVER_HIDE, lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03))
    s_pos, s_tris, s_wt, s_thick = SHEET[name]
    s_wt = np.asarray(s_wt, float)
    s_nrm = vertex_normals(s_pos, s_tris)
    knee, ank, ball = (np.asarray(LEG[sd][k], float) for k in (1, 2, 3))
    # (the sheet's normals outward: most of the shin's point away from her leg's line)
    shin = (s_pos[:, 2] > ank[2] + 0.05) & (s_pos[:, 2] < knee[2] - 0.05)
    ax_ = knee[None, :] + (ank - knee)[None, :] * ((knee[2] - s_pos[:, 2]) / (knee[2] - ank[2]))[:, None]
    if ((s_nrm[shin] * (s_pos[shin] - ax_[shin])).sum(1) < 0).mean() > 0.5:
        s_nrm, s_tris = -s_nrm, s_tris[:, ::-1]
    bvh = BVHTree.FromPolygons([tuple(p) for p in s_pos], s_tris.tolist())
    kd = cKDTree(s_pos)
    src = (s_pos, s_wt)

    def nrm_at(c, rounds=6, closed=False):
        _, j = kd.query(c, k=8)
        n_ = _ts_smooth(s_nrm[j].mean(1), rounds, closed)
        return n_ / (np.linalg.norm(n_, axis=1)[:, None] + 1e-12)

    def snap(c):
        return np.array([bvh.find_nearest(Vector(p))[0][:] for p in c])

    def frame(c, closed):
        tg = (np.roll(c, -1, 0) - np.roll(c, 1, 0)) if closed else np.gradient(c, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        n_ = nrm_at(c, closed=closed)
        n_ = n_ - tg * (n_ * tg).sum(1)[:, None]
        n_ /= np.linalg.norm(n_, axis=1)[:, None] + 1e-12
        return n_, np.cross(n_, tg)

    def band(nm, c, mkey, width, proud, closed, nv=8, rise=0.0):
        # (a flattened tube on the sock's outside: its inner face on it, `proud` off it, `rise` more lifted)
        n_, across = frame(c, closed)
        rise = np.broadcast_to(np.asarray(rise, float), (len(c),))
        cur = c + n_ * (s_thick + proud / 2 + rise)[:, None]
        return tube(nm, cur, n_, across, mkey, width, proud / 2, width / 2, 0.0, *src, closed=closed, nv=nv)

    # --- the sole edge: round the foot's outline in plan (the convex outline of its lowest 25 mm), each point a ray
    # in from outside at TS_SOLE_UP over the sock's floor near it (the arch's floor higher)
    from scipy.spatial import ConvexHull
    foot = s_pos[:, 2] < ank[2] - 0.035
    low = s_pos[foot]
    zf = low[:, 2].min()
    lowp = low[low[:, 2] < zf + 0.025]
    poly = lowp[ConvexHull(lowp[:, :2]).vertices]
    ol = _ts_resample(np.c_[poly[:, :2], np.zeros(len(poly))], 0.005, True)[:, :2]
    tg2 = np.roll(ol, -1, 0) - np.roll(ol, 1, 0)
    tg2 /= np.linalg.norm(tg2, axis=1)[:, None] + 1e-12
    on2 = np.c_[tg2[:, 1], -tg2[:, 0]]
    kd2 = cKDTree(low[:, :2])
    # (the floor's height along it eased over ~6 cm: the line rises gently under her arch, no kinks)
    zb = np.array([low[i_, 2].min() if len(i_) else zf for i_ in kd2.query_ball_point(ol, 0.012)])
    zb = np.clip(_ts_smooth(np.convolve(np.r_[zb[-3:], zb, zb[:3]], np.ones(7) / 7, "valid")[:, None], 30, True)[:, 0], zf, zf + 0.02)
    sole = []
    for q, o, z_ in zip(ol, on2, zb):
        st_ = q + o * 0.03
        hit = bvh.ray_cast(Vector((st_[0], st_[1], z_ + TS_SOLE_UP)), Vector((-o[0], -o[1], 0.0)), 0.1)
        if hit[0] is not None:
            sole.append(np.array(hit[0][:]))
    sole = snap(_ts_smooth(_ts_resample(_ts_smooth(np.array(sole), 4, True), 0.005, True), 4, True))
    print("TURNSHOE %s sole: floor %.3f, %d of %d rays, %.0f mm round, z %.3f..%.3f" % (
        name, zf, len(sole), len(ol), 1000 * np.linalg.norm(np.diff(np.vstack([sole, sole[:1]]), axis=0), axis=1).sum(),
        sole[:, 2].min(), sole[:, 2].max()))
    out.append(band(f"{name}_sole", sole, "darkleather", TS_SOLE, 0.003, True))
    # (the dark line at the ground: a bead under the sole edge, on its lower side)
    n_, across = frame(sole, True)
    down = np.where((across[:, 2] < 0)[:, None], across, -across)
    bead = sole + down * (TS_SOLE * 0.42) + n_ * (s_thick + 0.0012)
    out.append(tube(f"{name}_ground", bead, n_, across, "blackleather", 0.004, 0.0012, 0.002, 0.0, *src, closed=True, nv=5))

    # --- the moccasin seam: a U over her toes, from beside the ball round the front, laid from above
    f2 = (ball - ank)[:2]
    f2 /= np.linalg.norm(f2)
    pp = np.array([-f2[1], f2[0]])
    fm = foot & (s_pos[:, 2] < 0.07)
    yf = (s_pos[fm, :2] - ank[:2]) @ f2
    xf = (s_pos[fm, :2] - ank[:2]) @ pp
    ball_yf = float((ball[:2] - ank[:2]) @ f2)
    toe_yf = yf.max()
    nb = np.abs(yf - ball_yf) < 0.012
    xc, hw = (xf[nb].max() + xf[nb].min()) / 2, (xf[nb].max() - xf[nb].min()) / 2
    yc = ball_yf - 0.012
    a_ax, b_ax = toe_yf - 0.024 - yc, 0.6 * hw
    phi = np.linspace(-np.radians(95), np.radians(95), 80)
    plan = ank[:2] + np.outer(yc + a_ax * np.cos(phi), f2) + np.outer(xc + b_ax * np.sin(phi), pp)
    top = []
    for q in plan:
        hit = bvh.ray_cast(Vector((q[0], q[1], ank[2] + 0.05)), Vector((0, 0, -1)), 0.3)
        top.append(np.array(hit[0][:]) if hit[0] is not None else np.full(3, np.nan))
    top = np.array(top)
    top = top[np.isfinite(top).all(1)]
    seam = snap(_ts_smooth(_ts_resample(top, 0.003, False), 4, False))
    out.append(band(f"{name}_seam", seam, "darkleather", 0.0045, 0.0018, False, nv=6))
    # (gathered: short ribs out from the seam round its front, the sole's leather puckered into it)
    cen = ank + np.r_[f2 * yc + pp * xc, 0.0]
    sn_, _ = frame(seam, False)
    sl_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(seam, axis=0), axis=1))]
    ribs = 0
    # (Body 18, judge: "toe ribs read faintly as toe splits on a planted foot (fewer, larger puckers)": every TS_PUCKER
    # m, long and short in turn, wider and prouder; Body 17's: TS_PUCKER=0.0075 TS_PUCKER_SIZE=0.009,0.009,0.0026,0.0014)
    for s_ in np.arange(0.012, sl_[-1] - 0.012, TS_PUCKER):
        i = int(np.searchsorted(sl_, s_))
        p0, n0 = seam[i], sn_[i]
        h_ = (p0 - cen)[:2]
        if np.degrees(np.arccos(np.clip(h_ @ f2 / (np.linalg.norm(h_) + 1e-12), -1, 1))) > 75:
            continue
        r_ = p0 - cen
        r_ = r_ - n0 * (r_ @ n0)
        r_ /= np.linalg.norm(r_) + 1e-12
        rib = snap(p0[None, :] + r_[None, :] * np.linspace(0.002, TS_PUCKER_SIZE[ribs % 2], 7)[:, None])
        out.append(band(f"{name}_pucker{ribs}", rib, REAVER_HIDE, TS_PUCKER_SIZE[2], TS_PUCKER_SIZE[3], False, nv=6))
        ribs += 1

    # --- the thongs: an ankle ring, then two crossed up her shin to under the fur cuff
    z0, z1 = ank[2] + 0.045, leg_z(sd, KNEE_S + 0.045)

    def on_leg(th, z):
        pts = []
        for t_, zz in zip(th, z):
            c = knee + (ank - knee) * (knee[2] - zz) / (knee[2] - ank[2])
            d = np.array([np.sin(t_), -np.cos(t_), 0.0])
            hit = bvh.ray_cast(Vector((c[0], c[1], zz)), Vector(d), 0.3)
            pts.append(np.array(hit[0][:]) if hit[0] is not None else np.full(3, np.nan))
        pts = np.array(pts)
        return pts[np.isfinite(pts).all(1)]
    ring = on_leg(np.linspace(0, 2 * np.pi, 120, endpoint=False), np.full(120, z0 - 0.006))
    ring = snap(_ts_smooth(_ts_resample(_ts_smooth(ring, 3, True), 0.006, True), 3, True))
    nt = REAVER_THONGS
    ph = np.linspace(0, 2 * np.pi * nt, 160 * nt)
    # (Body 18, judge: "a perfectly even X-lattice reads as ballet/gladiator ribbons": the turns' heights uneven,
    # TS_GAPS each turn's share (-+15-20%), so the crossings sit irregularly as a hand wraps them; "1" = even)
    g_ = np.resize(np.array(TS_GAPS), nt)
    g_ = g_ / g_.mean()
    cum = np.r_[0, np.cumsum(g_)] / nt
    tt_ = ph / (2 * np.pi)
    gk = g_[np.clip(np.floor(tt_).astype(int), 0, nt - 1)]
    zt = z0 + (z1 - z0) * (np.interp(tt_, np.arange(nt + 1), cum) + gk * 0.75 * np.sin(ph) / (2 * np.pi * nt))
    th_a, th_b = (snap(_ts_smooth(_ts_resample(_ts_smooth(on_leg(s_ * ph, zt), 3, False), 0.006, False), 3, False)) for s_ in (1, -1))

    def over(c, others):
        # (lifted where it crosses another: the second thong over the first in front, under it behind; both over the ring)
        lift_ = np.zeros(len(c))
        ax_c = knee + (ank - knee) * ((knee[2] - c[:, 2]) / (knee[2] - ank[2]))[:, None]
        isf = (c - ax_c)[:, 1] < 0
        for o_, fr_ in others:
            d_ = cKDTree(o_).query(c)[0]
            w_ = np.clip(1 - d_ / (TS_THONG * 1.1), 0, 1)
            w_ = w_ * w_ * (3 - 2 * w_)
            if fr_ is not None:
                w_ = w_ * (isf if fr_ else ~isf)
            lift_ = np.maximum(lift_, w_ * 0.0024)
        return _ts_smooth(lift_[:, None], 4, False)[:, 0]
    out.append(band(f"{name}_thongring", ring, REAVER_THONG_KEY, TS_THONG, 0.0022, True, nv=6))
    out.append(band(f"{name}_thong0", th_a, REAVER_THONG_KEY, TS_THONG, 0.0022, False, nv=6, rise=over(th_a, [(ring, None), (th_b, False)])))
    out.append(band(f"{name}_thong1", th_b, REAVER_THONG_KEY, TS_THONG, 0.0022, False, nv=6, rise=over(th_b, [(ring, None), (th_a, True)])))
    # (Body 18, judge: "add a knot with two short tails under the fur cuff": where the two thongs end, crossed in front
    # at z1, a tight loop of thong over the crossing and two tails of unequal length hanging from it)
    if TS_KNOT:
        e_ = (th_a[-1] + th_b[-1]) / 2
        ax_e = knee + (ank - knee) * ((knee[2] - e_[2]) / (knee[2] - ank[2]))
        o_ = e_ - ax_e
        o_[2] = 0
        o_ /= np.linalg.norm(o_) + 1e-12
        sd_ = np.cross([0, 0, 1.0], o_)
        a_ = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        knot = snap(e_ + 0.0065 * (np.outer(np.cos(a_), sd_) + np.outer(np.sin(a_), [0, 0, 1.0])))
        out.append(band(f"{name}_thongknot", knot, REAVER_THONG_KEY, TS_THONG * 0.75, 0.0024, True, nv=6, rise=0.0034))
        t0_ = math.atan2(o_[0], -o_[1])
        for k_, (dt_, ln_) in enumerate(((0.22, 0.062), (-0.15, 0.045))):
            u_ = np.linspace(0, 1, 24)
            tail = on_leg(t0_ + dt_ * u_ ** 1.3, e_[2] - 0.004 - ln_ * u_)
            if len(tail) > 4:
                tail = snap(_ts_smooth(_ts_resample(_ts_smooth(tail, 2, False), 0.005, False), 2, False))
                out.append(band(f"{name}_thongtail{k_}", tail, REAVER_THONG_KEY, TS_THONG * 0.8, 0.0022, False, nv=6,
                                rise=0.0026 * (1 - np.linspace(0, 1, len(tail))) ** 2))
    print("TURNSHOE %s: seam %.0f mm, %d puckers, thongs %d turns from %.3f to %.3f m (%d, %d points), ring %d" % (
        name, 1000 * sl_[-1], ribs, nt, z0, z1, len(th_a), len(th_b), len(ring)))
    return out


OUTFITS = {"warden": warden, "arcanist": arcanist, "ranger": ranger, "reaver": reaver}

# How each material is drawn in the game (shaders/heroine_outfit.gdshader):
# leather (grain, burnished edges, stitching), metal (forged, polished at
# the edges, dark in the crevices), cloth (weave, sheen), gloss (latex,
# satin: clean). Fur and sheer stockings have shaders of their own.
KIND = {"steel": "metal", "darksteel": "metal", "iron": "metal", "rivetbronze": "metal", "gold": "metal", "claspgold": "metal", "bronze": "metal", "rust": "metal",
        "velvet": "cloth", "arcvelvet": "cloth", "linen": "cloth", "lace": "cloth", "ink": "cloth",
        "browncloth": "twill", "thread": "gloss", "satin": "gloss", "glovesatin": "satin", "gloveblack": "satin", "glovepipe": "satin", "glovethread": "satin", "wiregold": "metal", "amethyst": "gloss", "bone": "leather", "fur": "fur", "down": "fur", "stocking": "sheer"}


# Decals laid on her skin, drawn this far toward the camera so they never
# z-fight it (the Reaver's ink half sank into her skin in the full model).
PULL = {"ink": 0.0015}


def kind(key):
    return KIND.get(key, "leather")


def detail(objs, rays=20, reach=0.03):
    """What the outfit's shader needs to know of each point of each piece,
    from the pieces as made (thickened, bevelled), all of the outfit and
    her skin together:
      - how far it is from the piece's edge (its rim, where the sheet turns
        over: the faces that stand across her skin rather than along it), in
        metres: for stitching, burnished and polished edges, and wear;
      - how convex it is there (a bulge is worn, a hollow keeps its dirt);
      - how much of the sky it sees (rays out to 3 cm against everything
        else): darker and dirtier where pieces overlap or meet her;
      - a number for the piece (each its own shade).
    The first two as a second UV, the others as its vertex colours."""
    from mathutils import Vector
    import zlib
    allv, allt = [P], [TRI]
    base = len(P)
    for o in objs:
        me = o.data
        allv.append(np.array([(o.matrix_world @ v.co)[:] for v in me.vertices]))
        allt.append(np.array([[v + base for v in p.vertices[:3]] for p in me.polygons if len(p.vertices) >= 3]))
        base += len(me.vertices)
    bvh = BVHTree.FromPolygons([tuple(q) for q in np.vstack(allv)], np.vstack(allt).tolist())
    rng = np.random.default_rng(1)
    dirs = rng.normal(size=(rays, 3))
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        V = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
        Nv = np.array([(o.matrix_world.to_3x3() @ v.normal).normalized()[:] for v in me.vertices])
        # The edge: a sheet knows its own (finish() kept its border). A closed
        # piece (a cord, a rolled binding, a rivet) has none: guessed from its
        # shape, its curve read as edges and drew stitches across it.
        fin = np.isfinite(V).all(1)
        dist = np.full(len(V), 0.05)
        if "rim" in o.keys():
            M = np.array(o.matrix_world)
            rp = np.array(o["rim"].to_list() if hasattr(o["rim"], "to_list") else o["rim"], float).reshape(-1, 3)
            rp = rp @ M[:3, :3].T + M[:3, 3]
            dist[fin] = cKDTree(rp).query(V[fin])[0]
            del o["rim"]
        V = np.where(fin[:, None], V, 0.0)
        Nv = np.where(np.isfinite(Nv).all(1)[:, None], Nv, [0.0, 0.0, 1.0])
        # Convexity: how far each point stands out from the middle of its neighbours, along its normal.
        ev = np.zeros(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        A = sparse.coo_matrix((np.ones(2 * len(ev)), (np.r_[ev[:, 0], ev[:, 1]], np.r_[ev[:, 1], ev[:, 0]])),
                              shape=(len(V), len(V))).tocsr()
        deg = np.asarray(A.sum(1)).ravel()
        has = deg > 0
        mean_nb = lambda x: np.where(has if x.ndim == 1 else has[:, None], (A @ x) / np.maximum(deg, 1)[(slice(None),) + (None,) * (x.ndim - 1)], x)
        d = mean_nb(V) - V
        el = np.array([np.linalg.norm(V[A.indices[A.indptr[i]:A.indptr[i + 1]]] - V[i], axis=1).mean() if deg[i] else 1.0
                       for i in range(len(V))]) + 1e-6
        conv = np.where(has, -(d * Nv).sum(1) / el, 0.0)
        el_med = float(np.median(el)) if len(el) else 0.002
        for _ in range(int(np.clip((0.012 / max(el_med, 1e-4)) ** 2, 3, 120))):
            conv = 0.5 * conv + 0.5 * mean_nb(conv)
        conv = np.tanh(conv * 4) * 0.5 + 0.5
        ao = np.ones(len(V))
        for i in range(len(V)):
            n = Nv[i]
            hemi = dirs * np.sign(dirs @ n)[:, None]
            org = Vector(V[i] + n * 0.0008)
            seen = 0.0
            tot = 0.0
            for d in hemi:
                w = float(d @ n)
                tot += w
                if bvh.ray_cast(org, Vector(d), reach)[0] is None:
                    seen += w
            ao[i] = seen / max(tot, 1e-6)
        # (each point's few rays are noisy: eased over its neighbours, or a
        # smooth plate reads blotched)
        el_mean = float(np.median(el)) if len(el) else 0.002
        # (a rivet's eased only a little: eased 200 times over a 3 mm head, its
        # contact shadow spread over all of it, and it read as a black dot with
        # no ring where it meets the plate, judge 6)
        n_ease = 2 if o.name.endswith("_rivets") else int(np.clip((0.015 / max(el_mean, 1e-4)) ** 2, 8, 200))
        for _ in range(n_ease):
            ao = 0.5 * ao + 0.5 * mean_nb(ao)
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        du = me.uv_layers.new(name="detail")
        du.data.foreach_set("uv", np.c_[dist, conv][loops].astype(np.float32).ravel())
        me.uv_layers.active_index = 0
        me.uv_layers[0].active_render = True
        rnd = (zlib.crc32(o.name.split(".")[-1].split("_")[0].encode()) % 1000) / 1000.0
        col = me.color_attributes.new("detail", "FLOAT_COLOR", "POINT")
        painted = 0.0 if o.get("geo_stitch") else 1.0
        # (alpha, a flag for the shader: 0 a rolled binding, drawn matte if leather;
        # 0.5 a pauldron plate laid out round her arm, brushed along its UVs)
        flag = 0.0 if "_bind" in o.name else 0.5 if re.fullmatch(r"ranger\.(pauldron\d|bracer_[lr])", o.name) else 1.0
        col.data.foreach_set("color", np.c_[ao, np.full(len(V), rnd), np.full(len(V), painted), np.full(len(V), flag)].astype(np.float32).ravel())
        me.color_attributes.active_color = col
    print("DETAIL", len(objs), "pieces")


def material_table(path):
    """The outfit materials' table for the game: each one's kind and how
    many times its texture repeats in a metre (its UVs are in those units)."""
    import json
    # (entries it doesn't make, the armor pieces' own (gold trims' and gems': tools/armor/adorn.py), kept as they are)
    keep, zones, extra = {}, {}, {}
    if os.path.exists(path):
        old = json.load(open(path, encoding="utf-8"))
        keep = {k: v for k, v in old.items() if k not in SPEC}
        zones = {k: v["zone"] for k, v in old.items() if "zone" in v}   # (dye zones are data: kept across a rebuild)
        # (armor 16: a material's hand-set shading keys (the plumleather's rough_floor and clear coat, the glove satin's
        # sheen) are data too: every key this build doesn't write is kept)
        extra = {k: {kk: vv for kk, vv in v.items() if kk not in ("kind", "repeats", "pull", "tint", "zone")} for k, v in old.items() if k in SPEC}
    with open(path, "w", encoding="utf-8") as fh:
        from PIL import Image

        def tint(k):   # (STOCK_IVORY: a sheer piece's mean colour, for the game's sheer shader, which draws no texture)
            f = os.path.join(TEX, f"outfit_{k}_diff.jpg")
            if not (STOCK_IVORY and kind(k) == "sheer" and os.path.exists(f)):
                return {}
            return {"tint": [round(float(c) / 255, 4) for c in np.asarray(Image.open(f).convert("RGB"), np.float32).reshape(-1, 3).mean(0)]}
        json.dump({**{k: {"kind": kind(k), "repeats": v[3], **({"pull": PULL[k]} if k in PULL else {}), **tint(k), **({"zone": zones[k]} if k in zones else {}), **extra.get(k, {})} for k, v in SPEC.items()}, **keep}, fh, indent=1)

# (s30, for face's hair drape, 18 Oct: BODY_BLEND_OUT=<path> saves a copy of the scene here, her body after the
# F1 body pass and every body step above, before any outfit is made; object names kept: Heroine, HeroineHead,
# the armature. Not in it: what the glb's post-steps add (the face chain, the head's rest scale, her helpers).)
if os.environ.get("BODY_BLEND_OUT"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["BODY_BLEND_OUT"], copy=True)
    print("BODY_BLEND_OUT", os.environ["BODY_BLEND_OUT"])

made = []
for name, build in OUTFITS.items():
    if ONLY and name != ONLY:
        continue
    made += [o for o in build() if o]


# ---------------------------------------------------- what must be covered --
# The legal motion check's own regions (tools/legal/motioncheck/marks_section.py),
# measured here at rest after every build: the strip a garment must cover (the
# midline, 1.2 cm either side, from 2.3 cm behind the lowest point under her
# crotch forward to just below the front of her mons, skin facing sideways left
# out) and each areola (2.2 cm round the centre of its pigment). For each outfit,
# how much of each is bare at rest, and how near bare skin comes to it: the margin
# it has to move in before the check sees it. (The motion check proves it moving.)
def _cover_regions():
    mid = np.abs(X) < 0.003
    down = mid & (Z > 0.6) & (Z < 1.1) & (N[:, 2] < -0.9) & (np.abs(N[:, 0]) < 0.6)
    u = P[down][np.argmin(Z[down])]
    fwd = mid & (Y < u[1]) & (Z > u[2]) & (Z < u[2] + 0.15) & (N[:, 1] < -0.8)
    m = P[fwd][np.argmin(Z[fwd])]
    strip = (np.abs(X) < 0.012) & (np.abs(N[:, 0]) < 0.7) & (Y < u[1] + 0.023) & (Z > u[2] - 0.005) & (Z < m[2] - 0.005)
    # Her paint at each point (the darkest of a seam's sides), as the check reads it.
    me = body.data
    img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w_, h_ = img.size
    px = np.array(img.pixels[:]).reshape(h_, w_, 4)[:, :, :3]
    lum_v = np.full(len(me.vertices), 9.0)
    uvl = me.uv_layers.active.data
    for l in me.loops:
        uv_ = uvl[l.index].uv
        c_ = px[min(max(int(uv_[1] * h_), 0), h_ - 1), min(max(int(uv_[0] * w_), 0), w_ - 1)]
        lum_v[l.vertex_index] = min(lum_v[l.vertex_index], 0.3 * c_[0] + 0.59 * c_[1] + 0.11 * c_[2])
    co = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
    _, jl = cKDTree(co).query(P)
    lum = lum_v[jl]
    areolas = {}
    for sd in "lr":
        bn = arm.data.bones[f"breast_{sd}"]
        hd = np.array((arm.matrix_world @ bn.head_local)[:])
        ax_ = np.array((arm.matrix_world @ bn.tail_local)[:]) - hd
        ax_ /= np.linalg.norm(ax_)
        own = W[:, BI[f"breast_{sd}"]] > 0.5
        along = (P - hd) @ ax_
        cand = own & (along >= 0.5 * along[own].max())
        dark = cand & (lum < 0.8 * np.median(lum[cand]))
        areolas[sd] = P[dark].mean(0)
    print("COVER regions: strip %d points, from %.3f to %.3f deep and %.3f to %.3f high; areolas at %s and %s"
          % (strip.sum(), u[1] + 0.023, P[strip, 1].min(), u[2] - 0.005, m[2] - 0.005,
             areolas["l"].round(3), areolas["r"].round(3)))
    return strip, areolas


def cover_report(name, objs, tuck=None):
    """How bare her strip and areolas are under one outfit at rest (see above),
    her skin drawn tucked in as the game draws it (`tuck`: metres, each point)."""
    Pt = P - N * (tuck[:, None] if tuck is not None else 0.0)
    vs, fs = [], []
    for o in objs:
        key = o.data.materials[0].name if o.data.materials else ""
        if key in SPEC and len(SPEC[key]) >= 7:   # (seen through: stockings, lace)
            continue
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    if not fs:
        return
    tree = BVHTree.FromPolygons(vs, fs)
    near = np.zeros(len(P), bool)
    for c in [P[COVER_STRIP].mean(0)] + list(COVER_AREOLAS.values()):
        near |= np.linalg.norm(P - c, axis=1) < 0.1
    bare = np.zeros(len(P), bool)
    for i in np.where(near)[0]:
        bare[i] = tree.ray_cast(Vector(Pt[i] + N[i] * 0.0003), Vector(N[i]), 0.03)[0] is None
    # (bare skin facing sideways, the walls of the slot between her thighs, is
    # hidden in it and left out of the strip by the check too: not counted near it)
    seen = bare & (np.abs(N[:, 0]) < 0.7)
    regions = [("strip", COVER_STRIP, seen)] + [("areola %s" % sd, np.linalg.norm(P - c, axis=1) < 0.022, bare)
                                                for sd, c in COVER_AREOLAS.items()]
    for rname, reg, against in regions:
        if not reg.any():
            continue
        bt = cKDTree(P[against]) if against.any() else None
        if bt is None:
            print("COVER %s %s: all of %d points covered; no bare skin within 10 cm" % (name, rname, reg.sum()))
            continue
        d, j = bt.query(P[reg])
        k = int(np.argmin(d))
        where = P[reg][k]
        print("COVER %s %s: %d of %d points bare at rest; bare skin nearest %.1f mm away (at %s)"
              % (name, rname, int((bare & reg).sum()), int(reg.sum()), d[k] * 1000, where.round(3)))


COVER_STRIP, COVER_AREOLAS = _cover_regions()

# (a full tuck's mark, and how far inside a glove's cuff her hand goes undrawn)
TUCK_FULL = 0.98
# (the Arcanist's elbow glove's top: her skin's tuck at its line, and how far in it is full)
GLOVE_TUCK_RIM = float(os.environ.get("GLOVE_TUCK_RIM", "0.05"))
GLOVE_TUCK_IN = float(os.environ.get("GLOVE_TUCK_IN", "0.03"))
# (s26 solver gs6: the outfits whose marks are one at each point of her split skin, TUCK_WELD; and the
# fingerless glove's open edges on her hand, her skin eased in from nothing there to a full tuck GLOVE_EDGE_IN in)
TUCK_WELD = [s_ for s_ in os.environ.get("TUCK_WELD", "arcanist").split(",") if s_]
GLOVE_EDGE_IN = float(os.environ.get("GLOVE_EDGE_IN", "0.010"))
GONE_IN = 0.02
# ------------------------------------------------------------------ slots --
# (armor lead 1, 18 Oct: docs/handoff/armor.md section 1.) Each piece of hers is one slot's
# (tools/armor/slot_map.json): her outfits are exported a mesh per (slot, material), named
# <outfit>.<slot>.<material>, so the game can wear any outfit's pieces by slot and mix them; each
# (outfit, slot) carries its own tuck of her skin (armor_tuck/<outfit>.<slot>.bin) beside the four
# outfit channels, and armor_index.json lists them.
import hashlib
import json as _json
import struct as _struct
ARMOR_MAP = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "armor", "slot_map.json"), encoding="utf-8"))
ARMOR_RE = {o: [(e, [re.compile(r) for r in e["match"]]) for e in es] for o, es in ARMOR_MAP["outfits"].items()}


def slot_entry(name):
    """The slot map's entry for a built piece `<outfit>.<piece>` (None: no entry or more than one)."""
    o, _, pc = name.partition(".")
    hits = [e for e, rs in ARMOR_RE.get(o, []) if any(r.fullmatch(pc) for r in rs)]
    return hits[0] if len(hits) == 1 else None


def slot_check(objs, when):
    """The build fails naming every piece that maps to no slot, or to more than one."""
    bad = []
    for o in objs:
        out, _, pc = o.name.partition(".")
        hits = [e["slot"] for e, rs in ARMOR_RE.get(out, []) if any(r.fullmatch(pc) for r in rs)]
        if len(hits) != 1:
            bad.append("%s -> %s" % (o.name, hits or "no slot"))
    if bad:
        raise RuntimeError("SLOTS (%s): %d pieces not mapped to exactly one slot in tools/armor/slot_map.json: %s" % (when, len(bad), "; ".join(bad)))
    print("SLOTS (%s): all %d pieces mapped" % (when, len(objs)))


ARMOR_TUCK = {}      # (outfit, slot) -> her skin's tuck, a value a vertex of her body
ARMOR_TUCK_N = {}    # (outfit, slot) -> records written
ARMOR_BODY_HASH = None


def armor_tuck_write(body_obj, folder):
    """Each (outfit, slot)'s tuck, sparse: u32 count, then count records (i32 x, i32 y, i32 z: her body
    vertex's bind position, glTF Y-up metres x 1e5 rounded; f32 tuck), little-endian; only tuck > 0,
    one record a position (her split skin's copies at one point: the largest of their tucks). And
    ARMOR_BODY_HASH: sha1 of her body's bind positions so rounded, unique, sorted, as i32 little-endian."""
    global ARMOR_BODY_HASH
    me_ = body_obj.data
    # (her points as the exporter writes them, float32 in her mesh's own frame (her world frame: asserted), so
    # each rounds as the game's copy of them does)
    bp = np.empty(len(me_.vertices) * 3, np.float32)
    me_.vertices.foreach_get("co", bp)
    bp = bp.reshape(-1, 3)
    if not np.allclose(np.array(body_obj.matrix_world), np.eye(4), atol=1e-9):
        print("ARMOR TUCK: her body is not at the origin; its points taken through its matrix")
        bp = np.array([(body_obj.matrix_world @ v.co)[:] for v in me_.vertices], np.float32)
    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1).astype(np.float64) * 1e5).astype(np.int64)
    # (only her points on a face: the exporter writes no others)
    fv = np.empty(sum(len(f_.vertices) for f_ in me_.polygons), np.int64)
    me_.polygons.foreach_get("vertices", fv)
    used = np.zeros(len(me_.vertices), bool)
    used[fv] = True
    uq, inv = np.unique(q[used], axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    print("ARMOR TUCK: %d of her %d points on faces, %d places" % (int(used.sum()), len(used), len(uq)))
    ARMOR_BODY_HASH = hashlib.sha1(uq.astype("<i4").tobytes()).hexdigest()
    os.makedirs(os.path.join(folder, "armor_tuck"), exist_ok=True)
    for (out, slot), t in sorted(ARMOR_TUCK.items()):
        assert len(t) == len(me_.vertices), "her body's vertices changed after the tuck"
        g = np.zeros(len(uq))
        np.maximum.at(g, inv, t[used])
        k = np.nonzero(g > 0)[0]
        rec = np.zeros(len(k), dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
        rec["x"], rec["y"], rec["z"], rec["t"] = uq[k, 0], uq[k, 1], uq[k, 2], g[k]
        with open(os.path.join(folder, "armor_tuck", f"{out}.{slot}.bin"), "wb") as f_:
            f_.write(_struct.pack("<I", len(k)) + rec.tobytes())
        ARMOR_TUCK_N[(out, slot)] = int(len(k))
    print("ARMOR TUCK: %d (outfit, slot) tucks written, her body %s" % (len(ARMOR_TUCK), ARMOR_BODY_HASH))


def _body_keys(path):
    """Her built glb's vertex keys in file order, one array a mesh primitive (glTF positions x 1e5 rounded: HerWear's key)."""
    import heroine_neck as hn_
    G_ = hn_._Gl(path)
    return {(mi_, pi_): np.round(G_.get(p_["attributes"]["POSITION"]).astype(np.float64) * 1e5).astype(np.int64)
            for mi_, m_ in enumerate(G_.g["meshes"]) for pi_, p_ in enumerate(m_["primitives"])}


def armor_tuck_rekey(pre, path, folder):
    """(armor 4, 19 Oct: the body steps after her export (the throat soften, the neck cut, the seam...) move her points
    in the glb, so tuck records keyed at export missed them in the game: 600 of the arcanist top's. Each record at a
    point that moved goes to where that point now is; one also still on an unmoved point stays there too.)"""
    post = _body_keys(path)
    # (paired a vertex by index within each primitive that kept its vertex count: the mouth and teeth steps add
    # vertices and primitives, but no tuck lies on them)
    same = [k for k in pre if k in post and pre[k].shape == post[k].shape]
    print("ARMOR TUCK REKEY: %d of %d primitives paired (unpaired: %s)" % (len(same), len(post), sorted(set(post) - set(same))))
    A, B = np.concatenate([pre[k] for k in same]), np.concatenate([post[k] for k in same])
    mv = np.any(A != B, 1)
    to = {}
    for a, b in zip(map(tuple, A[mv]), map(tuple, B[mv])):
        to.setdefault(a, b)
    still = set(map(tuple, A[~mv]))
    moved = 0
    for (out, slot) in sorted(ARMOR_TUCK_N):
        fp = os.path.join(folder, "armor_tuck", f"{out}.{slot}.bin")
        d = open(fp, "rb").read()
        n = _struct.unpack_from("<I", d, 0)[0]
        rec = np.frombuffer(d, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
        got = {}
        for x, y, z, t in rec:
            k = (int(x), int(y), int(z))
            ks = ([to[k]] if k in to else []) + ([k] if k in still or k not in to else [])
            moved += k in to
            for k2 in ks:
                got[k2] = max(got.get(k2, 0.0), float(t))
        ks = sorted(got)
        new = np.zeros(len(ks), dtype=rec.dtype)
        if ks:
            arr = np.array(ks, np.int64)
            new["x"], new["y"], new["z"] = arr[:, 0], arr[:, 1], arr[:, 2]
            new["t"] = [got[k] for k in ks]
        with open(fp, "wb") as f_:
            f_.write(_struct.pack("<I", len(ks)) + new.tobytes())
        ARMOR_TUCK_N[(out, slot)] = int(len(ks))
    print("ARMOR TUCK REKEY: %d of her glb's points moved after export; %d tuck records followed them" % (int(mv.sum()), moved))


# (armor 7, 20 Oct: THE BOUNDED TUCK. The owner's crop, the warden's cups in town: a small round pinch on her
# left breast just outside the cup's inner rim, its mirror smooth. Her skin's tuck was each point's own, from its
# own 12 mm ray (a gap's few mm of noise became up to 8 mm of depth, neighbours 0.25 to 0.77, left and right 0.5
# apart), and a ray grazing a rolled rim from just outside the piece tucked skin the piece never covered. Now, for
# every piece and outfit: a point is under a piece only if its ray meets the piece face-on (|cos| >= TUCK_GRAZE;
# a grazing hit is the rim seen from outside), and over her welded skin the tuck is the rays' need smoothed
# (TUCK_SMOOTH_IT averaging rounds within the footprint), raised to an envelope that climbs no faster than
# TUCK_SLOPE (tuck per metre of her surface) and TUCK_STEP between neighbours, and capped by the same climb in from
# the footprint's border: no neighbour step past either, a slope in from every edge, nothing outside. The
# rules that mean to be hard (a nipple's disc and bump, a boot's deep tuck) keep their values as floors.)
TUCK_SMOOTH = os.environ.get("TUCK_SMOOTH", "1") == "1"
TUCK_GRAZE = float(os.environ.get("TUCK_GRAZE", "0.5"))
TUCK_SLOPE = float(os.environ.get("TUCK_SLOPE", "30"))
TUCK_SMOOTH_IT = int(os.environ.get("TUCK_SMOOTH_IT", "4"))
TUCK_STEP = float(os.environ.get("TUCK_STEP", "0.15"))   # (and no more than this between two neighbours, however far apart)


def _tuck_graph():
    """Her skin welded (copies at one point are one), its edges and their lengths in metres (world)."""
    if "_tuck_g" not in globals():
        me_ = body.data
        co_ = np.array([(body.matrix_world @ v.co)[:] for v in me_.vertices])
        _, gid_ = np.unique(np.round(np.array([v.co[:] for v in me_.vertices]) / 1e-6).astype(np.int64), axis=0, return_inverse=True)
        gid_ = np.asarray(gid_).ravel()
        ng_ = int(gid_.max()) + 1
        cg_ = np.zeros((ng_, 3))
        cg_[gid_] = co_
        ev_ = gid_[np.array([e.vertices[:] for e in me_.edges])]
        ev_ = np.unique(np.sort(ev_[ev_[:, 0] != ev_[:, 1]], 1), axis=0)
        a_, b_ = np.r_[ev_[:, 0], ev_[:, 1]], np.r_[ev_[:, 1], ev_[:, 0]]
        globals()["_tuck_g"] = (gid_, ng_, a_, b_, np.linalg.norm(cg_[a_] - cg_[b_], axis=1))
    return globals()["_tuck_g"]


def tuck_bound(t, hard=None, under=None, say=print, label=""):
    """THE BOUNDED TUCK (above) of a per-vertex tuck `t`; `under`: her points under the piece (its footprint, a
    loose part's zero tucks too; None: where t > 0); `hard`: points whose value is a floor."""
    gid_, ng_, a_, b_, l_ = _tuck_graph()
    need = np.zeros(ng_)
    np.maximum.at(need, gid_, t)
    hd = np.zeros(ng_, bool)
    if hard is not None:
        np.logical_or.at(hd, gid_, hard & (t > 0))
    U = need > 0
    if under is not None:
        np.logical_or.at(U, gid_, under)
    if not U.any():
        return t
    inn = U[a_] & U[b_]
    # (each edge's allowance: TUCK_SLOPE over its length, at most TUCK_STEP; her rows are 4 to 15 mm apart there)
    lw_ = np.minimum(TUCK_SLOPE * l_, TUCK_STEP)
    ai, bi, li = a_[inn], b_[inn], lw_[inn]
    # (the need smoothed over the footprint: each round, a point's mean with its neighbours under the piece)
    s = need.copy()
    deg = np.bincount(bi, minlength=ng_).astype(float)
    for _ in range(TUCK_SMOOTH_IT):
        acc = np.bincount(bi, weights=s[ai], minlength=ng_)
        s = np.where(U, (s + acc) / (1.0 + deg), 0.0)
    s[hd] = np.maximum(s[hd], need[hd])
    # (raised to the least envelope climbing no faster than TUCK_SLOPE over her surface)
    E = s.copy()
    for _ in range(400):
        c_ = np.full(ng_, -1.0)
        np.maximum.at(c_, bi, E[ai] - li)
        En = np.maximum(E, c_)
        if np.abs(En - E).max() < 1e-7:
            break
        E = En
    # (capped by the slope in from the footprint's border: distance over her skin from the nearest point outside it)
    bd = np.unique(a_[~U[a_] & U[b_]])
    sub = U.copy()
    sub[bd] = True
    keep = sub[a_] & sub[b_]
    gr = sparse.csr_matrix((lw_[keep], (a_[keep], b_[keep])), shape=(ng_, ng_))
    d_ = sparse.csgraph.dijkstra(gr, directed=True, indices=bd, min_only=True, limit=1.01) if len(bd) else np.full(ng_, np.inf)
    F = np.where(U, np.minimum(E, d_), 0.0)
    F[hd] = np.maximum(F[hd], need[hd])
    F = np.clip(F, 0.0, 1.0)
    say("TUCK BOUND %s: %d points of her welded skin under it, %d hard; mean %.3f -> %.3f, max %.2f -> %.2f"
        % (label, int(U.sum()), int(hd.sum()), need[U].mean(), F[U].mean(), need.max(), F.max()))
    return F[gid_]


def tuck_of(name, objs, slot=None):
    """Her skin's tuck (0..1 a vertex of her body, as one channel of its `hide` colours holds it) under `objs`,
    the hiding pieces of outfit `name`: all of them (slot None: that outfit's channel, as it always was), or
    one slot's (armor lead 1: the tuck a slot carries, for the game to take the max over what she wears).
    The rules tied to one piece (the arcanist glove's top, the boot's foot, a hat's hair) apply only in
    the slot that holds it."""
    me = body.data
    mw3 = body.matrix_world.to_3x3()
    t = np.zeros(len(me.vertices))
    whole = slot is None
    say = print if whole else (lambda *a, **k: None)
    skip_ = None
    if not whole:
        # (a slot's pieces reach her skin within 3 cm (the boot's ray) or 1.5 cm behind: points of hers
        # well outside the pieces' box are left untucked without their rays, as the rays would leave them)
        pw_ = np.array([(o.matrix_world @ v.co)[:] for o in objs for v in o.data.vertices])
        bw0_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
        skip_ = ((bw0_ < pw_.min(0) - 0.05) | (bw0_ > pw_.max(0) + 0.05)).any(1)
    vs, fs, cap, deep = [], [], [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
        cap += [o.get("tuck", 1.0)] * len(o.data.polygons)
        # (a boot's parts: its top edge's heights round its middle, and its leg)
        deep += [(np.array(o["deep_zt"][:]), np.array(o["deep_c"][:]), o["deep_side"]) if "deep_zt" in o else None] * len(o.data.polygons)
    tree = BVHTree.FromPolygons(vs, fs)
    reach = 0.03 if any(d is not None for d in deep) else 0.012
    hid = 0
    cos_ = np.full(len(me.vertices), np.nan)   # (each point's ray: |cos| of the angle it meets the piece at)
    hard_ = np.zeros(len(me.vertices), bool)
    under_ = np.zeros(len(me.vertices), bool)   # (its ray met a piece face-on: under it, however loose)
    grazed = 0
    # Her skin under a piece (it faces the piece, within 12 mm), and
    # where her skin stands proud of the filled form the pieces are cut
    # from (a nipple's tip under a plate cup), from behind too. Never
    # more: skin hidden past a piece's edge shows as a hole in her.
    _, jj = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
    # (and all of each nipple's disc, under whatever covers it: hidden only
    # at the tip, the skin round the tip came through a plate cup as she
    # ran, the plate and her breast swinging a little apart)
    to_tip = np.minimum(*[np.linalg.norm(P[jj] - q, axis=1) for q in NIPPLE.values()])
    disc = to_tip < 0.028
    proud = ((((P - P_FILLED) * N).sum(1)[jj] > 0.0005) & (P[jj, 2] > CROTCH + 0.12)) | disc
    # (and each nipple's bump, standing proud of the form the pieces are
    # made on, tucked all the way under whatever covers it: tucked only as
    # deep as the piece lay close, 2 to 4 mm off it, its tip came through a
    # cup's outline by a pixel as she swung; at least 2 cm inside every
    # piece's edge, so the deeper tuck can't be seen)
    bump = (((P - P_FILLED) * N).sum(1)[jj] > 0.0005) & (to_tip < 0.012)
    # Tucked as deep as the piece lies close: skin a piece stands well
    # clear of (a pauldron, a bracer) cannot come through it, and tucked
    # there it showed as a deeper gap under the piece's edge as it swung.
    for v in me.vertices:
        if skip_ is not None and skip_[v.index]:
            continue
        co = body.matrix_world @ v.co
        n = (mw3 @ v.normal).normalized()
        hit = tree.ray_cast(co + n * 0.0005, n, reach)
        # A boot (its parts keep 'deep_*') tucks her skin all the way
        # under it, through a 30 mm ray, eased in from 4 to 8 cm under its
        # top edge (the standard rule above that: tucked deep from 1 cm
        # down, it showed as a deep gap seen up into the boot's top as she
        # vaulted): it stands well off her, and her calf, ankle and toes
        # would come through it as she moved.
        # Every other piece keeps the standard rule and its 12 mm ray.
        # (how deep under the top edge both the hit and her skin are: a
        # long ray from skin just past a boot's edge grazed its wall, and
        # tucked bare skin deep there)
        dp = deep[hit[2]] if hit[0] is not None else None
        t_ = 0.0
        if dp is not None and LEGW[dp[2]][jj[v.index]] >= 0.3:
            ka_ = np.arange(len(dp[0]) + 1) * 2 * np.pi / len(dp[0])
            d_ = [np.interp(np.mod(np.arctan2(q[1] - dp[1][1], q[0] - dp[1][0]), 2 * np.pi), ka_, np.r_[dp[0], dp[0][:1]]) - q[2]
                  for q in (hit[0], co)]
            t_ = float(ramp(min(d_), 0.04, 0.08))
        if hit[0] is not None and hit[3] > 0.012 and t_ <= 0:
            hit = (None, None, None, None)
        if hit[0] is not None:
            cos_[v.index] = abs(hit[1].dot(n))
            # (THE BOUNDED TUCK: a ray grazing the piece, its rolled rim seen from outside, is no piece over her)
            if TUCK_SMOOTH and t_ <= 0 and cos_[v.index] < TUCK_GRAZE:
                hit = (None, None, None, None)
                grazed += 1
        if proud[v.index] and tree.ray_cast(co + n * 0.0005, -n, 0.015)[0] is not None:
            t[v.index] = 1
            hard_[v.index] = True
        elif hit[0] is not None:
            under_[v.index] = True
            hard_[v.index] = bool(bump[v.index]) or t_ > 0
            t[v.index] = 1.0 if bump[v.index] else min(cap[hit[2]], 0.8 * np.clip((0.005 - hit[3] - 0.0005) / 0.004, 0, 1))
            t[v.index] = t[v.index] * (1 - t_) + t_
        hid += t[v.index] > 0
    # Tucked in gradually from the border, a third, two thirds, then all
    # the way, so her skin slopes under a piece's edge as if it pressed
    # in, rather than stepping down.
    if "_body_nb" not in globals():
        ev = np.array([e.vertices[:] for e in me.edges])
        globals()["_body_nb"] = sparse.coo_matrix((np.ones(2 * len(ev)), (np.r_[ev[:, 0], ev[:, 1]], np.r_[ev[:, 1], ev[:, 0]])),
                                                  shape=(len(me.vertices), len(me.vertices))).tocsr()
    # (s26 solver gs6, TUCK_WELD: her skin is split here and there, two to four copies at one point, each
    # its own normal (her hands most: 80 such points in the Arcanist's mark), and each copy took its own
    # mark, by its own ray and its own ring from the border: 0.27, 0.53 and 0.78 at one point 3.7 mm in
    # from the left thumb hole. Drawn tucked, the copies part, a crack 5.5 mm wide under the glove's open
    # edge, seen as a dark slit and the edge over it as a white flap. In the outfits named, the copies at
    # a point are one: the deepest copy's ray, the rings counted on her skin welded, one mark for all.)
    welded = name in TUCK_WELD
    if welded:
        if "_body_cw" not in globals():
            _, gid_ = np.unique(np.round(np.array([v.co[:] for v in me.vertices]) / 1e-6).astype(np.int64), axis=0, return_inverse=True)
            gid_ = np.asarray(gid_).ravel()
            S_ = sparse.csr_matrix((np.ones(len(gid_)), (np.arange(len(gid_)), gid_)))
            C_ = (S_ @ S_.T).tocsr()
            globals()["_body_cw"] = (gid_, (C_ @ _body_nb @ C_).tocsr())
        gm_ = np.zeros(_body_cw[0].max() + 1)
        np.maximum.at(gm_, _body_cw[0], t[:])
        say("TUCK WELD %s: %d points of hers split in copies, %d of them marked unequally" % (name, int((np.bincount(_body_cw[0]) > 1).sum()), int((np.abs(gm_[_body_cw[0]] - t[:]) > 1e-6).sum())))
        t[:] = gm_[_body_cw[0]]
    globals()["TUCK_LAST"] = {"need": t.copy(), "cos": cos_, "hard": hard_.copy(), "under": under_ | (t > 0), "grazed": grazed}
    if TUCK_SMOOTH:
        say("TUCK GRAZE %s: %d rays of hers met the piece at a graze (|cos| < %.2f), left untucked" % (name, grazed, TUCK_GRAZE))
        t[:] = tuck_bound(t, hard_, under_ | (t > 0), say, name)
    else:
        under = t[:] > 0
        reached, ring = ~under, np.zeros(len(under))
        for r_ in (1, 2):
            nxt = under & ~reached & (((_body_cw[1] if welded else _body_nb) @ reached.astype(float)) > 0)
            ring[nxt], reached = r_, reached | nxt
        t[:] *= np.where(ring > 0, ring / 3, 1.0)
    # Under a held edge (held_edges: a leotard's leg lines) she is tucked
    # all the way, out to HOLD_BAND from it, so a look in under the edge
    # meets the piece's inside, not her; the last row before the edge only
    # as deep as keeps her skin just past it from dipping more than
    # HOLD_GROOVE under it (her rows are 4-20 mm apart there).
    for o in objs:
        if "hold_line" not in o:
            continue
        hl = np.array(o["hold_line"][:]).reshape(-1, 3)
        bw_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
        dl, _ = cKDTree(hl).query(bw_)
        und = np.zeros(len(dl), bool)
        for i in np.nonzero(dl < HOLD_BAND)[0]:
            v = me.vertices[i]
            co = body.matrix_world @ v.co
            n = (mw3 @ v.normal).normalized()
            und[i] = tree.ray_cast(co + n * 0.0005, n, 0.012)[0] is not None
        nb = _body_nb.tocoo()
        m_ = und[nb.row] & ~und[nb.col] & (t[nb.col] == 0)
        u_ = dl[nb.col[m_]] / np.maximum(dl[nb.col[m_]] + dl[nb.row[m_]], 1e-6)
        lim = np.ones(len(dl))
        np.minimum.at(lim, nb.row[m_], HOLD_GROOVE / 0.010 / np.maximum(u_, 1e-3))
        before = t[und].copy()
        # (eased in: a full tuck only from HOLD_SOFT inside the edge, a
        # depth of a third of the way in nearer it at 30 mm; tucked all the way
        # right up to the edge, her skin showed as cyan slivers and a sawtooth
        # along the leg line as the cloth lifted in chain_haul, daggers_fore and
        # the vaults, and eased over 10 mm it changed nothing, her rows there
        # being 4-20 mm apart)
        soft = np.clip(dl / HOLD_SOFT, 0.0, 1.0) if HOLD_SOFT > 0 else np.ones(len(dl))
        t[und] = np.minimum(soft[und], lim[und]) if HOLD_CAP else np.maximum(t[und], np.minimum(soft[und], lim[und]))
        say("HOLD TUCK %s: %d vertices of hers under it within %.0f mm of its held edge; marks %.2f -> %.2f (mean), %d at the edge row limited (mean %.2f)"
              % (o.name, und.sum(), HOLD_BAND * 1000, before.mean(), t[und].mean(), (und & (lim < 1)).sum(), lim[und & (lim < 1)].mean() if (und & (lim < 1)).any() else 0))
    if name == "arcanist":
        # (her forearm and elbow under the sleeve and glove tucked all the way,
        # from 5 cm above her elbow to 1 cm short of her wrist: with her elbow
        # shut to 145 degrees its inside came through, animation's judge 11 and
        # judge 6; her hand is left as it was, a full tuck would cross a finger)
        for sd in ("l", "r"):
            fa = (ARM_S[sd][jj] > ELBOW_S - 0.05) & (ARM_S[sd][jj] < WRIST_S - 0.01) & (ARMW[sd][jj] > 0.5)
            t[fa & (t[:] > 0)] = 1.0
        # (s22: the elbow glove's top (shoulder caps, her elbow bare): her skin under it eased in
        # from the glove's own cut, GLOVE_TUCK_RIM of a full tuck at the line, all of it
        # GLOVE_TUCK_IN inside, and none past it. Tucked by the rays and the rule above, the
        # tuck's border followed her coarse rows across the line: a sawtooth, partly past the
        # top (seen into the glove, its inside blue-grey) and partly short of it, 10 mm deep
        # one row in; with her elbow shut at the hat brim the top looked torn.)
        if ARC_HANDS in ("fingerless", "glove") and os.environ.get("ARC_CAPS", "1") == "1" and GLOVE_TUCK_IN > 0 and (whole or any(o.name.startswith("arcanist.glove_") for o in objs)):
            for sd in ("l", "r"):
                e_, w_ = ARM[sd][1], ARM[sd][2]
                d_ = GLOVE_TOP_D[sd](P[jj]) if sd in GLOVE_TOP_D else (P[jj] - e_) @ ((w_ - e_) / np.linalg.norm(w_ - e_)) - float(os.environ.get("ARC_GLOVE_ELBOW", "0.04"))
                fa = (ARMW[sd][jj] > 0.5) & (d_ > -0.05) & (d_ < GLOVE_TUCK_IN)
                t[fa] = np.where(d_[fa] > 0, GLOVE_TUCK_RIM + (1.0 - GLOVE_TUCK_RIM) * ramp(d_[fa], 0.0, GLOVE_TUCK_IN), 0.0)
                say("GLOVE TUCK %s: %d vertices of hers eased in under its top, %d past it untucked" % (sd, int((fa & (d_ > 0)).sum()), int((fa & (d_ <= 0)).sum())))
        # (s26 solver gs6, GLOVE_EDGE_IN: the fingerless glove's open edges on her hand, the thumb hole and
        # the knuckle cut (its sheet's own border, finish()'s rim, where her skin under it is her hand's):
        # her skin eased in from no tuck at the edge to a full one GLOVE_EDGE_IN inside, and none beside it.
        # Tucked by the rays and the rings, a mark of 0.78 sat 3.7 mm in from the left thumb hole, 0.3 and
        # more within 4 mm of it: her skin sank away under the open edge, a dark slit and a white flap.)
        if ARC_HANDS == "fingerless" and GLOVE_EDGE_IN > 0:
            bwc_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
            for sd in ("l", "r"):
                rim_ = [np.array(o["rim"].to_list() if hasattr(o["rim"], "to_list") else o["rim"], float).reshape(-1, 3)
                        @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                        for o in objs if o.name.startswith(f"arcanist.glove_{sd}") and "rim" in o.keys()]
                if not rim_:
                    continue
                rim_ = np.vstack(rim_)
                hc_ = [BI[n] for n in BONES if n.endswith(f"_{sd}") and n.split("_")[0] in ("hand", "thumb", "index", "middle", "ring", "pinky")]
                rim_ = rim_[W[cKDTree(P).query(rim_)[1]][:, hc_].sum(1) > 0.5]
                de_ = cKDTree(rim_).query(bwc_)[0]
                cap_ = ramp(de_, 0.0, GLOVE_EDGE_IN)
                m_ = (de_ < GLOVE_EDGE_IN) & (t[:] > cap_)
                n4_ = de_ < 0.004
                say("GLOVE EDGE %s: %d rim points on her hand; %d vertices of hers eased in from its open edges (mean %.2f -> %.2f); within 4 mm max %.2f -> %.2f"
                      % (sd, len(rim_), int(m_.sum()), t[m_].mean() if m_.any() else 0, cap_[m_].mean() if m_.any() else 0,
                         t[n4_].max(), np.minimum(t[n4_], cap_[n4_]).max()))
                t[m_] = cap_[m_]
    for cap_, zone_ in TUCK_ZONES.get(name, []):
        zw_ = zone_(P[jj])
        say("TUCK ZONE %s: %d vertices of hers capped at %.2f" % (name, int(((zw_ > 0.5) & (t[:] > cap_)).sum()), cap_))
        t[:] = t[:] * (1 - zw_) + np.minimum(t[:], cap_) * zw_
    if name in BALD and (whole or slot == "head"):
        # Her hair is part of her body: hidden under a hat that is to carry the look.
        _, j = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
        hair = HAIR.copy()
        for _ in range(6):
            hair = np.maximum(hair, (ADJ @ hair > 0.05).astype(float))
        t[(hair[j] > 0.5) & (wsum("Head", "neck_01")[j] > 0.2)] = 1
    # A full tuck is marked TUCK_FULL (heroine_skin.gdshader reads 0.973 and
    # over as all of it): a mark of 1 is her skin not drawn at all. So are
    # her hands inside the Arcanist's gloves, from her fingertips to GONE_IN
    # inside the cuff: no tuck keeps a hand in (a finger is thinner than a
    # full tuck), and the back of her wrist, bent back as she caught her
    # breath, came through the back of the glove tucked all the way (judge
    # 10). Under the cuff's own edge she is tucked as before, so no gap
    # opens there and a look into the cuff finds her.
    t[:] = np.minimum(t[:], TUCK_FULL)
    if name in TUCK_WELD and "_body_cw" in globals():
        gm_ = np.zeros(_body_cw[0].max() + 1)
        np.maximum.at(gm_, _body_cw[0], t[:])
        t[:] = gm_[_body_cw[0]]
    if name == "arcanist" and ARC_HANDS == "glove":
        for sd in ("l", "r"):
            glv = [o for o in objs if o.name.startswith(f"arcanist.glove_{sd}")]
            if not glv:
                continue
            gw = np.array([(o.matrix_world @ v.co)[:] for o in glv for v in o.data.vertices])
            jn = cKDTree(P).query(gw)[1]
            cuff = ARM_S[sd][jn[(ARMW[sd][jn] > 0.5) & (ARM_S[sd][jn] > ELBOW_S)]].min()
            inside = (ARMW[sd][jj] > 0.5) & (ARM_S[sd][jj] > cuff + GONE_IN)
            if os.environ.get("ARC_CAPS", "1") == "1":
                # (s23 solver: at elbow length her arm's coarse field runs on the slant to the
                # glove's exact top, and past it at her elbow's side her skin went undrawn
                # outside the glove, a hole onto its inside; so also GONE_IN inside the cut)
                e_, w_ = ARM[sd][1], ARM[sd][2]
                inside &= (P[jj] - e_) @ ((w_ - e_) / np.linalg.norm(w_ - e_)) - float(os.environ.get("ARC_GLOVE_ELBOW", "0.04")) > GONE_IN
            # every hand vertex past the cuff line, the fingertips and knuckles the
            # coverage mark never reached too: the weld of the glove by position shows
            # its finger ends closed, so each of them sits inside leather (judge 13)
            gone = inside
            t[gone] = 1.0
            say("HIDES arcanist glove_%s: her hand inside not drawn, %d vertices, from %.3f m down her arm (the cuff at %.3f, her wrist at %.3f); %d there unmarked, drawn"
                  % (sd, gone.sum(), cuff + GONE_IN, cuff, WRIST_S, (inside & ~gone).sum()))
    if name in ("ranger", "warden") and (whole or slot == "boots"):
        # (her foot inside each Ranger boot and Warden sabaton not drawn, from RBOOT_GONE under her
        # ankle down, where the boot rides her foot rigidly: her heel skin carries
        # calf weight and swung 43-51 mm against the rigid heel counter, out
        # through it in run_stalker; the shaft above keeps the tuck, so a look
        # down into the boot still finds her)
        for sd in ("l", "r"):
            za = BOOTS.Leg(sd).ankle[2]
            foot = (LEGW[sd][jj] > 0.5) & (P[jj, 2] < za - RBOOT_GONE)
            gone = foot & (t[:] > 0)
            t[gone] = 1.0
            say("HIDES %s boot_%s: her foot inside not drawn, %d vertices under %.3f m (ankle %.3f); %d there unmarked, drawn"
                  % (name, sd, gone.sum(), za - RBOOT_GONE, za, (foot & ~gone).sum()))
    say("HIDES", name, hid, "of", len(me.vertices), "vertices of her skin")
    return t, hid


# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (CHANNELS, as People.cs has them), for the game to draw tucked a
# few millimetres in (shaders/heroine_skin.gdshader): a smooth cup need not
# clear every bump of hers, nothing of her shows through, and since nothing
# of her is cut away no gap can open where a piece moves off her.
# Loose things (a coat, a hat) and sheer ones hide nothing.
if BODY_OUT:
    me = body.data
    col = me.color_attributes.get("hide") or me.color_attributes.new("hide", "BYTE_COLOR", "POINT")
    vals = np.zeros((len(me.vertices), 4))
    vals[:, 3] = 0
    mw3 = body.matrix_world.to_3x3()
    for name in OUTFITS:
        k = CHANNELS.index(name)
        objs = [o for o in made if o.name.startswith(name + ".") and o.get("hides")]
        if not objs or k > 3:
            continue
        vals[:, k] = tuck_of(name, objs)[0]
    # (armor lead 1: and each (outfit, slot)'s own, from its hiding pieces by the same rule)
    slot_check([o for o in made if o.name.partition(".")[0] in OUTFITS], "tuck")
    for _aout in OUTFITS:
        if ONLY and _aout != ONLY:
            # (armor 17 N3: an --only build with --body has no other outfit's pieces; their channels stay empty)
            continue
        _ahides = [o for o in made if o.name.startswith(_aout + ".") and o.get("hides")]
        for _aslot in sorted({slot_entry(o.name)["slot"] for o in made if o.name.startswith(_aout + ".")}):
            _aobjs = [o for o in _ahides if slot_entry(o.name)["slot"] == _aslot]
            ARMOR_TUCK[(_aout, _aslot)] = tuck_of(_aout, _aobjs, _aslot)[0] if _aobjs else np.zeros(len(me.vertices))
        _ak = CHANNELS.index(_aout)
        # (armor 2, TUCK DEFICIT: the max over an outfit's slots must reach its channel everywhere, or her skin is
        # drawn over where a garment hides it when the whole set is worn (each slot's tuck eases in from its own
        # border, so at a seam between two slots, and under the boots' deep rule, neither reached the channel).
        # Where the channel exceeds the max over slots, the slot whose hiding pieces' surface lies nearest that point
        # of hers takes the channel's value there. tools/armor/tuck_fix.py applied the same rule to the 18 Oct build.)
        _aslots = sorted({slot_entry(o.name)["slot"] for o in _ahides})
        if _ak <= 3 and _aslots:
            _amx = np.max([ARMOR_TUCK[(_aout, s_)] for s_ in _aslots], 0)
            _adef = np.nonzero((vals[:, _ak] - _amx > 1 / 255) | ((vals[:, _ak] > 0.973) & (_amx <= 0.973)))[0]  # (or full in the channel only: the shader reads 0.973 and over as full)
            _atr = {}
            for s_ in _aslots:
                _avs, _afs = [], []
                for o in _ahides:
                    if slot_entry(o.name)["slot"] == s_:
                        b_ = len(_avs)
                        _avs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
                        _afs += [[b_ + i for i in p_.vertices] for p_ in o.data.polygons]
                _atr[s_] = BVHTree.FromPolygons(_avs, _afs)
            _agiven = {}
            for i_ in _adef:
                co_ = body.matrix_world @ me.vertices[i_].co
                d_ = {s_: (t_.find_nearest(co_)[3] if t_.find_nearest(co_)[0] is not None else 1e9) for s_, t_ in _atr.items()}
                s_ = min(d_, key=d_.get)
                ARMOR_TUCK[(_aout, s_)][i_] = vals[i_, _ak]
                _agiven[s_] = _agiven.get(s_, 0) + 1
            print("TUCK DEFICIT %s: %d vertices short of the channel given it, by nearest slot: %s" % (_aout, len(_adef), _agiven))
        if _ak <= 3:
            _amx = np.max([t_ for (o_, s_), t_ in ARMOR_TUCK.items() if o_ == _aout], 0)
            _afull = vals[:, _ak] > 0.973
            _alost = _afull & (_amx <= 0.973)
            _adrop = vals[:, _ak] - _amx
            print("ARMOR TUCK %s: %d vertices full in its channel, %d of them not full in any slot (largest drop %.3f); "
                  "%d tucked deeper by a slot than by the channel (largest rise %.3f), %d of them full in a slot only"
                  % (_aout, int(_afull.sum()), int(_alost.sum()), float(_adrop.max()), int((_adrop < -1e-6).sum()),
                     float(-_adrop.min()), int(((_amx > 0.973) & ~_afull).sum())))
    col.data.foreach_set("color", vals.ravel())
    # Each outfit's coverage at rest, her skin tucked as the game draws it
    # (heroine_skin.gdshader: 10 mm times the outfit's channel).
    _, jb = cKDTree(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])).query(P)
    for name in OUTFITS:
        objs = [o for o in made if o.name.startswith(name + ".")]
        if objs and CHANNELS.index(name) <= 3:
            cover_report(name, objs, 0.010 * np.where(vals[jb, CHANNELS.index(name)] > 0.973, 1.0, vals[jb, CHANNELS.index(name)]))
    _, jw = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
    changed = np.abs(W - W_AUTHORED).sum(1) > 1e-4
    groups = {vg.name: vg for vg in body.vertex_groups}
    n_eased = 0
    for v in me.vertices:
        j = jw[v.index]
        if not changed[j]:
            continue
        for e in list(v.groups):
            body.vertex_groups[e.group].remove([v.index])
        row = W[j]
        top = np.argsort(-row)[:4]
        tot = row[top].sum() or 1.0
        for b in top:
            if row[b] > 0.003:
                vg = groups.get(BONES[b]) or body.vertex_groups.new(name=BONES[b])
                groups[BONES[b]] = vg
                vg.add([v.index], float(row[b] / tot), "REPLACE")
        n_eased += 1
    print("BODY breast weights eased at", n_eased, "of her vertices")
    me.color_attributes.active_color = col
    # (s25, her chest skin faired over the sculpt's irregular triangulation: heroine_chest.py; here,
    # after every piece is fitted to her as she was, so none changes. Off: CHEST_SMOOTH=0)
    if os.environ.get("CHEST_SMOOTH", "1") == "1":
        from heroine_chest import chest_smooth
        chest_smooth(body, mend_folds)
    # (18 Oct, the owner: her nipples and areolae out of the shipped body, painted out of her albedo and
    # flattened into her breasts' curve: heroine_areola.py; here, after every piece is cut from her as she
    # was, so none changes. AREOLA_OUT=0 builds the anatomical body, kept and never shipped.)
    if os.environ.get("AREOLA_OUT", "1") == "1":
        import heroine_areola
        heroine_areola.apply(body, [NIPPLE["l"], NIPPLE["r"]])
    # Her helper bones (twists at the shoulders and down the forearms, shares
    # at the shoulders, elbows and knees: tools/anim/helpers.py), her weights
    # split onto them; her pieces take the same split below.
    mend_folds(me, body)
    rig_helpers.apply(arm, [body], chain=TWIST_CHAIN)
    _ff_keep = None
    if HAND_PIVOTS and FINGER_FIX:
        _ffm = body.data
        _ff_keep = [np.empty(len(_ffm.vertices) * 3)]
        _ffm.vertices.foreach_get("co", _ff_keep[0])
        for _kb in (_ffm.shape_keys.key_blocks if _ffm.shape_keys else []):
            _ff_keep.append(np.empty(len(_kb.data) * 3))
            _kb.data.foreach_get("co", _ff_keep[-1])
        _ff_cn = np.empty(len(_ffm.loops) * 3, np.float32)
        _ffm.corner_normals.foreach_get("vector", _ff_cn)
        finger_flattened(body)
        # (her custom normals are kept relative to each corner's own frame, so points moved under them
        # turned a few round (4 corners on her left fingers over 45 deg, 3 past 90: dark specks). Her moved
        # points' corners, and the ring round them, take her skin's own normal as it now is; the rest keep theirs.)
        _ffc = np.empty(len(_ffm.vertices) * 3)
        _ffm.vertices.foreach_get("co", _ffc)
        _ffmv = np.abs(_ffc - _ff_keep[0]).reshape(-1, 3).max(1) > 1e-9
        _ffe = np.empty(len(_ffm.edges) * 2, np.int64)
        _ffm.edges.foreach_get("vertices", _ffe)
        _ffe = _ffe.reshape(-1, 2)
        _ffr = _ffmv.copy()
        _ffr[_ffe[_ffmv[_ffe[:, 0]], 1]] = True
        _ffr[_ffe[_ffmv[_ffe[:, 1]], 0]] = True
        _fflv = np.empty(len(_ffm.loops), np.int64)
        _ffm.loops.foreach_get("vertex_index", _fflv)
        _ffvn = np.empty(len(_ffm.vertices) * 3, np.float32)
        _ffm.vertex_normals.foreach_get("vector", _ffvn)
        # (as mend_folds does: welded by place, and any point whose normal turned against the mean of
        # the points round it (a pad point drawn through her skin) takes the mean of its unturned neighbours)
        _, _ffw = np.unique(np.round(_ffc.reshape(-1, 3) / 1e-5).astype(np.int64), axis=0, return_inverse=True)
        _ffw = _ffw.ravel()
        _ffnw = _ffw.max() + 1
        _ffW = np.zeros((_ffnw, 3))
        np.add.at(_ffW, _ffw, _ffvn.reshape(-1, 3))
        _ffW /= np.maximum(np.linalg.norm(_ffW, axis=1, keepdims=True), 1e-12)
        _ffa, _ffb = _ffw[_ffe[:, 0]], _ffw[_ffe[:, 1]]
        _ffk = _ffa != _ffb
        _ffa, _ffb = _ffa[_ffk], _ffb[_ffk]
        _ffM = np.zeros((_ffnw, 3))
        np.add.at(_ffM, _ffa, _ffW[_ffb])
        np.add.at(_ffM, _ffb, _ffW[_ffa])
        _ffM /= np.maximum(np.linalg.norm(_ffM, axis=1, keepdims=True), 1e-12)
        _ffrw = np.zeros(_ffnw, bool)
        _ffrw[_ffw[_ffr]] = True
        _ffbad = _ffrw & ((_ffW * _ffM).sum(1) < 0.5)
        _ffG = np.where(_ffbad[:, None], 0.0, _ffW)
        _ffM2 = np.zeros((_ffnw, 3))
        np.add.at(_ffM2, _ffa, _ffG[_ffb])
        np.add.at(_ffM2, _ffb, _ffG[_ffa])
        _ffok = _ffbad & (np.linalg.norm(_ffM2, axis=1) > 1e-9)
        _ffW[_ffok] = _ffM2[_ffok] / np.linalg.norm(_ffM2[_ffok], axis=1, keepdims=True)
        _ffo = _ff_cn.reshape(-1, 3).copy()
        _ffs = _ffr[_fflv]
        _ffo[_ffs] = _ffW[_ffw[_fflv[_ffs]]]
        _ffm.normals_split_custom_set([tuple(v) for v in _ffo])
        print("FINGER_FIX: %d corners given her skin's own normal (%d points moved, %d in the ring; %d turned points "
              "given their neighbours')" % (int(_ffs.sum()), int(_ffmv.sum()), int(_ffr.sum() - _ffmv.sum()), int(_ffok.sum())))
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in [body] + HEAD_PARTS:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=BODY_OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_vertex_color="ACTIVE")
    armor_tuck_write(body, os.path.dirname(OUT))
    _tuck_pre = _body_keys(BODY_OUT)
    if _ff_keep is not None:
        # (her flattened fingers taken back: her pieces' rigging and glove fit below read her body)
        _ffm.vertices.foreach_set("co", _ff_keep[0])
        for _kb, _c in zip(_ffm.shape_keys.key_blocks if _ffm.shape_keys else [], _ff_keep[1:]):
            _kb.data.foreach_set("co", _c)
        _ffm.update()
        _ffm.normals_split_custom_set([tuple(v) for v in _ff_cn.reshape(-1, 3)])
    # (her head's keys' normals held to her neck's at SPLIT, as the exporter does not: heroine_seam.py)
    import heroine_seam
    heroine_seam.seam(BODY_OUT)
    # (and her upper lids' creases made a soft fold, never a second brow: heroine_browfold.py; the paints'
    # partner step, heroine_browpaint.py, is done once in each paint)
    import heroine_browfold
    heroine_browfold.fold(BODY_OUT)
    # (and the bow's normals refilled in the face keys, so no dark dots sit over her upper lip's border:
    # heroine_face_bow.py run; its run_keys follows the smile's easing below)
    import heroine_face_bow
    heroine_face_bow.run(BODY_OUT)
    # (and her side teeth in the cheeks' shade: heroine_teethshade.py)
    import heroine_teethshade
    heroine_teethshade.shade(BODY_OUT)
    # (and her teeth and tongue seated for an open mouth and a smile, her mouth's inside dark by depth and the
    # smile_open key: heroine_mouth.py)
    import heroine_mouth
    heroine_mouth.seat(BODY_OUT)
    # (and her smile's and open mouth's moves eased across her upper lip's border, so no groove or fold opens
    # there: heroine_smile_lip.py)
    import heroine_smile_lip
    heroine_smile_lip.run(BODY_OUT)
    # (and the bow's normals refilled in the base and every mouth key, after the easing above recomputed them:
    # heroine_face_bow.py run_keys)
    heroine_face_bow.run_keys(BODY_OUT)
    # (and her mouth's inside pushed back behind her skin in every face key, and the upper front gum raised so the laugh
    # shows teeth, not gum: heroine_mouth_inner.py; heroine_mouth_seal.py is NOT hooked yet, judged NOT YET)
    import heroine_mouth_inner
    heroine_mouth_inner.run(BODY_OUT)
    # (her head +7%, the owner 14 Oct: the Head joint's rest scaled, her meshes as they were, so it
    # may run before or after any step that measures them (heroine_mouth.seat); keep it last)
    import heroine_headscale
    heroine_headscale.scale(BODY_OUT, HEAD_SCALE)
    # (her neck 3 cm shorter, the owner's pick B, 18 Oct: her Head joint's rest moved down her neck, as the
    # game's --neck-cm drew it for the 1:1 sheet; last, after every step that finds her face by position)
    import heroine_neck
    # (and her neck's skin under her head given her head's weights there first, so the cut drops the two as one:
    # heroine_neck.match_graft; the pieces and hair that took that skin's weights follow it, match_pieces below)
    heroine_neck.match_graft(BODY_OUT, float(os.environ.get("NECK_CUT", "0.03")))
    # (18 Oct, the owner on C01: "a giant atoms apple". Her throat's weights refilled smoothly between her chest and
    # the skin under her head, her clavicles and upper arms out of her neck's column (the pieces and hair that took her
    # neck's weights follow, match_pieces below, through match_graft's field), then her neck's front and sides faired
    # inward as the game shows her after the cut: heroine_throat_skin.py. Off: THROAT_SOFT=0)
    if os.environ.get("THROAT_SOFT", "1") == "1":
        import heroine_throat_skin
        heroine_throat_skin.ease(BODY_OUT)
        heroine_throat_skin.soften(BODY_OUT, float(os.environ.get("NECK_CUT", "0.03")))
    # (20 Oct, the owner's crop at creation's Look: a step in her neck's outline under her right ear. Her nape's weight
    # spikes refilled from the points round them, then her weights round her neck's back and sides eased between her
    # body and her head, so the cut below spreads down her nape instead of folding it: heroine_neck.nape. The pieces and
    # hair that took those weights follow, match_pieces, through the field. Off: NAPE=0)
    if os.environ.get("NAPE", "1") == "1" and float(os.environ.get("NECK_CUT", "0.03")):
        heroine_neck.nape(BODY_OUT)
    # (21 Oct, the owner's frame from play: her left neck outline jogged out below her jaw. Her graft's top and her
    # head's lowest skin round her neck's sides and back met halfway each side and faired (positions and normals
    # only): heroine_neck.fair_seam. Off: NECK_FAIR=0)
    if os.environ.get("NECK_FAIR", "1") == "1":
        heroine_neck.fair_seam(BODY_OUT)
    heroine_neck.shorten_glb(BODY_OUT, float(os.environ.get("NECK_CUT", "0.03")))
    armor_tuck_rekey(_tuck_pre, BODY_OUT, os.path.dirname(OUT))
    print("BODY", BODY_OUT)

# Nothing else rides along (the scene may hold strays).
for o in [o for o in bpy.data.objects if o not in made and o not in (arm, body)]:
    bpy.data.objects.remove(o)
material_table(os.path.join(os.path.dirname(OUT), "outfit_materials.json"))
# One file an outfit, so the game loads only what she wears.
# (each outfit's pieces listed before any are joined: a joined piece is gone)
# Every piece split onto her helper bones as her skin is, so they move as one.
BONE_NAMES = {b.name for b in arm.data.bones}


def one_blend_pieces(objs):
    """The pieces on one blend of bones: rigid plates, the clasp, rivets."""
    out = []
    for o in objs:
        if o.type != "MESH" or not len(o.data.vertices):
            continue
        gname = {g.index: g.name for g in o.vertex_groups}
        rows = {tuple(sorted((gname[g.group], round(g.weight, 4)) for g in v.groups
                             if g.weight > 1e-4 and gname[g.group] in BONE_NAMES)) for v in o.data.vertices}
        if len(rows) == 1 and rows != {()}:
            out.append(o)
    return out


def rows_of(o):
    gname = {g.index: g.name for g in o.vertex_groups}
    return [tuple(sorted((gname[g.group], round(g.weight, 4)) for g in v.groups
                         if g.weight > 1e-4 and gname[g.group] in BONE_NAMES)) for v in o.data.vertices]


def rigid_again(objs, riders):
    """Each one-blend piece back on one blend after the helpers' split, and
    its corrective shapes made a shift of the whole. The split reads each
    point's own place (the twist bones' reach, the skin under it), so a plate
    on one blend came out bent, point by point: it takes the mean of its
    points' split instead, its four largest shares."""
    for o in objs:
        gname = {g.index: g.name for g in o.vertex_groups}
        tot = {}
        for v in o.data.vertices:
            for g in v.groups:
                n = gname[g.group]
                if n in BONE_NAMES:
                    tot[n] = tot.get(n, 0.0) + g.weight
        keep = sorted(tot, key=tot.get, reverse=True)[:4]
        s = sum(tot[n] for n in keep)
        sh_ = [(n, tot[n] / s) for n in keep]
        # (the spaulder's plates go back on their blends from before the
        # split: split by their places, the cap rode the shoulder's helper
        # and band 1 the twist bone, and band 1 went through the cap in 13 of
        # 24 lying frames (death_back, get_up_back), j2; on the bones they
        # were judged on, h5, the nearest was 1.17 mm)
        if PL_RAW and o.name.startswith("ranger.pauldron"):
            sh_ = list(RIGID_ROWS[o.name])
        # (the leather spaulder's cap and band 1 on her shoulder's share bone
        # alone: on blends of her collarbone and upper arm (.50, .55) linear
        # skinning shrank each plate and turned them apart when her arm went
        # high or she lay down, and band 1 went through the cap in 11 of 64
        # Godot frames, j3. The share bone is that half turn as a true turn,
        # unshrunk, so the two move as one and keep their 5.9 mm in every
        # pose; band 2 stays on its blend (offline over the six clips: never
        # nearer band 1 than 2.8 mm), sv)
        if o.name.split("_")[0] in SP_SHARE:
            sh_ = [("upperarm_share_l", 1.0)]
        # (or all three plates on one row, SP_ROW: they move as one and can't
        # cross; the twist bone's share keeps the shrink small, so band 1
        # keeps 2.1 mm or more under the cap and band 2 under band 1 in all
        # six clips, offline; on their own blends 11 frames crossed, j3, and
        # the share bone alone slid the cap 25 mm round her arm at idle, s1)
        if SP_ROW and o.name.split("_")[0].startswith("ranger.pauldron"):
            sh_ = list(SP_ROW)
        idx = list(range(len(o.data.vertices)))
        for g in list(o.vertex_groups):
            if g.name in BONE_NAMES:
                o.vertex_groups.remove(g)
        for n, w in sh_:
            o.vertex_groups.new(name=n).add(idx, w, "REPLACE")
        keys = o.data.shape_keys
        if keys is not None:
            base = np.array([k.co[:] for k in keys.reference_key.data])
            for kb in keys.key_blocks[1:]:
                d = np.array([k.co[:] for k in kb.data]) - base
                for i, k in enumerate(kb.data):
                    k.co = Vector(base[i] + d.mean(0))
    # (what rides a plate on its very blend, the spaulder's leather riveted
    # under it, takes the plate's new blend too, so they still move as one)
    by_row = {}
    for o in objs:
        gname = {g.index: g.name for g in o.vertex_groups}
        by_row[RIGID_ROWS[o.name]] = [(gname[g.group], g.weight) for g in o.data.vertices[0].groups if gname[g.group] in BONE_NAMES]
    n_ride = 0
    for o, rows in riders:
        hit = [i for i, r in enumerate(rows) if r in _rset]
        if not hit:
            continue
        groups = {g.name: g for g in o.vertex_groups}
        for i in hit:
            for g in list(o.data.vertices[i].groups):
                if o.vertex_groups[g.group].name in BONE_NAMES:
                    o.vertex_groups[g.group].remove([i])
            for n, w in by_row[rows[i]]:
                if n not in groups:
                    groups[n] = o.vertex_groups.new(name=n)
                groups[n].add([i], w, "REPLACE")
        n_ride += len(hit)
    print("RIGID: %d points riding a plate on its blend moved with it" % n_ride)
    print("RIGID: %d one-blend pieces kept on one blend after the helpers' split" % len(objs))


PL_RAW = os.environ.get("PL_RAW", "1") == "1"
SP_SHARE = {"ranger.pauldron%d" % k for k, on in enumerate(os.environ.get("SP_SHARE", "0,0,0").split(",")) if on == "1"}     if os.environ.get("PAULDRON", "leather") == "leather" else set()
# (with her twist chain, TWIST_CHAIN=1, twist_01 carries 0.30 of the roll, not 0.50: the row's 0.27 goes to twist_02,
# which carries 0.475, so the plates keep the turn they were judged on)
SP_ROW = [(n, float(w)) for n, w in (kv.split(":") for kv in os.environ.get("SP_ROW", "clavicle_l:0.4206,spine_03:0.0494,upperarm_l:0.26," + ("upperarm_twist_02_l" if TWIST_CHAIN else "upperarm_twist_01_l") + ":0.27").split(",") if kv)] if os.environ.get("PAULDRON", "leather") == "leather" else []
RIGID_PIECES = one_blend_pieces(made)
RIGID_ROWS = {o.name: rows_of(o)[0] for o in RIGID_PIECES}
_rset = {r for r in RIGID_ROWS.values() if len(r) > 1}   # (a blend, never one bone's whole: cloth on one bone is no rider)
RIDERS = [(o, r) for o in made if o.type == "MESH" and o not in RIGID_PIECES for r in [rows_of(o)] if _rset & set(r)]
rig_helpers.apply(arm, made, skin=lambda p: SKIN_BVH.find_nearest(Vector(p))[0][:], body=body, chain=TWIST_CHAIN)
rigid_again(RIGID_PIECES, RIDERS)

# (s23 solver, the elbow glove's top edge, shoulder caps on: heroine_rig shares each point's limb
# weight out as her skin's nearest point does, and her skin's coarse rows cross the glove's cut
# on the slant, so along the cut the weights it read went up and down from row to row (and a
# fourth and a fifth bone crossed, the exporter keeping different fours): with her elbow shut
# the edge rippled 1-2 mm and the hem parted from the sheet. So the top GLOVE_WSMOOTH_BAND[0] of
# each Arcanist glove, eased out by GLOVE_WSMOOTH_BAND[1], takes weights fitted locally (linear,
# so the run of her weights down her arm is kept) over GLOVE_WSMOOTH[0] round her arm and
# GLOVE_WSMOOTH[1] along it, every layer of it (sheet, its inside, hem, trim, stitches) read
# together, so they cannot part; then four bones, cut smoothly. GLOVE_WSMOOTH=0: as rigged.)
GLOVE_WSMOOTH = tuple(float(v) for v in os.environ.get("GLOVE_WSMOOTH", "0.008,0.003").split(","))
GLOVE_WSMOOTH_BAND = tuple(float(v) for v in os.environ.get("GLOVE_WSMOOTH_BAND", "0.02,0.035").split(","))
# (s26 solver, the top in her bent elbow: her skin's weights change fast round her arm at the crook
# and the elbow's point, so the smoothed top bent on another blend than the skin under it, and her
# skin came through it there (2.2 mm at the brim, 1.7 mm casting). Now each point of the top band
# takes the four-bone blend that best keeps it where it sits on its nearest triangle of her skin
# (at its own height off it), her elbow bent 0-165 degrees, her forearm rolled -60..60 and her upper
# arm -30..30, her helpers driven and her correctives keyed as the game does (tools/anim/helpers.py);
# poses where it would sink into her skin count GLOVE_WFIT_ASYM times more. Her rest is untouched
# (any blend is exact there). GLOVE_WFIT=0, or no game skeleton for the armature: the s23 smoothing.)
GLOVE_WFIT = os.environ.get("GLOVE_WFIT", "1") == "1"
GLOVE_WFIT_LAM = float(os.environ.get("GLOVE_WFIT_LAM", "1.0"))
GLOVE_WFIT_ASYM = float(os.environ.get("GLOVE_WFIT_ASYM", "10"))
# (s26 solver gs4, the crook: with her elbow shut past 95 degrees her skin at the crook, a few mm under the
# top, came through the top band (B1 0.50 mm at the brim, G1 0.86 with its dip and 0.21 running). The band
# took the mean of her skin's upperarm share there (0.17-0.24), but one of her coarse rows carries less
# (0.11-0.15), and with less of the upper arm a point folds less into the crook: so the row stood proud
# of the band. Now, within GLOVE_CROOK_WX[1] deg of her crook (eased out by [2]) and from the top to
# [3] mm in (eased out by [4]), [0] of the glove's upperarm share goes to her forearm's (lowerarm and
# twist, their own ratio): the band folds in less than any of her rows, and her rest is untouched. Its
# flanks (40 deg off) wanted the opposite, so the window is narrow. "0" leaves the fit as it was.)
GLOVE_CROOK_WX = tuple(float(v) for v in os.environ.get("GLOVE_CROOK_WX", "0.4,12,32,20,35").split(","))


def glove_fit_poses():
    """(her game skeleton, [(skin matrices [J, 4, 4], game space, rest to posed; {corrective: weight})]), or None."""
    sk = rig_helpers._game_skeleton(arm)
    if sk is None:
        return None
    hp = rig_helpers.hp
    from rig import qaxis, qmul
    nj = len(sk.names)
    grot0, gpos0 = sk.rest_globals()
    rest_inv = np.linalg.inv(hp.mats(grot0[0], gpos0[0]))
    out = []
    for deg in range(0, 166, 15):
        for roll in (-60, -30, 0, 30, 60):
            for ur in (-30, 0, 30):
                rot = sk.rest_rot.copy()
                for s_ in "lr":
                    la, ua = sk.index["lowerarm_" + s_], sk.index["upperarm_" + s_]
                    rot[la] = qmul(hp.bent(sk, "lowerarm_" + s_, deg)[la], qaxis([0, 1.0, 0], roll))
                    rot[ua] = qmul(rot[ua], qaxis([0, 1.0, 0], ur))
                scale, shift = np.ones((nj, 3)), np.zeros((nj, 3))
                rot = hp.drive(sk, rot, scale, shift)
                grot, gpos = sk.fk(rot[None])
                out.append((hp.mats(grot[0], gpos[0], scale, shift) @ rest_inv, hp.corrective_weights(sk, rot)))
    return sk, out


def glove_keys_game(o, names):
    """{name: [V, 3] moves, game space} of o's shape keys `names` it has."""
    out = {}
    if o.data.shape_keys is None:
        return out
    n = len(o.data.vertices)
    base = np.empty(n * 3)
    o.data.shape_keys.reference_key.data.foreach_get("co", base)
    m3 = np.array(o.matrix_world.to_3x3())
    for nm in names:
        kb = o.data.shape_keys.key_blocks.get(nm)
        if kb is not None:
            co = np.empty(n * 3)
            kb.data.foreach_get("co", co)
            out[nm] = rig_helpers._to_game((co - base).reshape(-1, 3) @ m3.T)
    return out


def glove_fit_rows(fitp, gl, X, W0, sel, bones):
    """The band's rows (`sel` of X, Blender world; W0 by `bones`) fitted to follow her skin over fitp's poses."""
    from scipy.optimize import nnls
    sk, poses = fitp
    S = np.stack([m for m, _ in poses])                     # (f, J, 4, 4)
    sv = [sh for _, sh in poses]
    kn = ("elbow_point_l", "elbow_point_r")
    mw = body.matrix_world
    nbv = len(body.data.vertices)
    co = np.empty(nbv * 3)
    body.data.vertices.foreach_get("co", co)
    PB = rig_helpers._to_game(co.reshape(-1, 3) @ np.array(mw.to_3x3()).T + np.array(mw.translation))
    WB = rig_helpers._weights(body, sk.names)
    KB = glove_keys_game(body, kn)
    body.data.calc_loop_triangles()
    TB = np.empty(len(body.data.loop_triangles) * 3, np.int64)
    body.data.loop_triangles.foreach_get("vertices", TB)
    TB = TB.reshape(-1, 3)
    XG = rig_helpers._to_game(X)
    KG = {k_: [] for k_ in kn}
    for o in gl:
        kk_ = glove_keys_game(o, kn)
        for k_ in kn:
            KG[k_].append(kk_.get(k_, np.zeros((len(o.data.vertices), 3))))
    KG = {k_: np.vstack(v) for k_, v in KG.items()}
    near = cKDTree(XG[sel]).query(PB)[0] < 0.03
    TB = TB[near[TB].any(1)]
    bvh = BVHTree.FromPolygons([tuple(p) for p in PB], TB.tolist())
    T = np.array([TB[bvh.find_nearest(Vector(XG[i]))[2]] for i in sel])
    A_, B_, C_ = PB[T[:, 0]], PB[T[:, 1]], PB[T[:, 2]]
    nf = np.cross(B_ - A_, C_ - A_)
    nf /= np.linalg.norm(nf, axis=1, keepdims=True)
    d = ((XG[sel] - A_) * nf).sum(1)
    q = XG[sel] - nf * d[:, None] - A_
    e1, e2 = B_ - A_, C_ - A_
    g11, g12, g22 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1)
    r1, r2 = (q * e1).sum(1), (q * e2).sum(1)
    det = g11 * g22 - g12 * g12
    u = (g22 * r1 - g12 * r2) / det
    v = (g11 * r2 - g12 * r1) / det
    bc = np.column_stack([1 - u - v, u, v])
    Wi = (WB[T] * np.clip(bc, 0, 1)[:, :, None]).sum(1)
    Wi /= np.maximum(Wi.sum(1, keepdims=True), 1e-9)
    # her skin under the band, posed (her correctives keyed) in every pose
    U = np.unique(T)
    ui = np.searchsorted(U, T)
    PBp = []
    for f in range(len(S)):
        Pu = PB[U] + sum(sv[f].get(k_, 0.0) * KB[k_][U] for k_ in KB)
        Mu = np.einsum("uj,jab->uab", WB[U], S[f])
        PBp.append(np.einsum("uab,ub->ua", Mu[:, :3, :3], Pu) + Mu[:, :3, 3])
    PBp = np.stack(PBp, 1) * 1e3                             # (U, f, 3) mm
    bix_ = {n: i for i, n in enumerate(bones)}
    tob = np.array([bix_[n] for n in sk.names])
    fromb = {bix_[n]: j for j, n in enumerate(sk.names)}
    Wn = np.zeros((len(sel), len(bones)))
    sl = np.sqrt(GLOVE_WFIT_LAM)
    SWm = np.array([[sv[f].get(k_, 0.0) for k_ in kn] for f in range(len(S))])
    worst = 0.0
    for r, i in enumerate(sel):
        a_, b_, c_ = PBp[ui[r, 0]], PBp[ui[r, 1]], PBp[ui[r, 2]]
        n_ = np.cross(b_ - a_, c_ - a_)
        n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        tg = a_ + (b_ - a_) * u[r] + (c_ - a_) * v[r] + n_ * d[r] * 1e3
        cand = np.nonzero((WB[T[r]].max(0) > 0) | (W0[i, tob] > 0))[0]
        pf = XG[i][None, :] + SWm @ np.stack([KG[k_][i] for k_ in kn])
        Sc = S[:, cand]
        Xm = (np.einsum("fcab,fb->fca", Sc[:, :, :3, :3], pf) + Sc[:, :, :3, 3]) * 1e3   # (f, c, 3)
        Xm = Xm.transpose(0, 2, 1).reshape(-1, len(cand))
        y = tg.reshape(-1)
        Aa = np.vstack([Xm, sl * np.eye(len(cand)), 1e3 * np.ones((1, len(cand)))])
        ya = np.concatenate([y, sl * Wi[r, cand], [1e3]])
        cf = np.ones(len(S))
        for _ in range(4 if GLOVE_WFIT_ASYM > 0 else 1):
            rw = np.concatenate([np.repeat(np.sqrt(cf), 3), np.ones(len(cand) + 1)])
            w_, _ = nnls(Aa * rw[:, None], ya * rw)
            if (w_ > 1e-6).sum() > 4:
                keep = np.argsort(-w_)[:4]
                w2, _ = nnls(Aa[:, keep] * rw[:, None], ya * rw)
                w_ = np.zeros(len(cand))
                w_[keep] = w2
            en = ((Xm @ w_ - y).reshape(-1, 3) * n_).sum(1)
            cf = cf + GLOVE_WFIT_ASYM * (en < -0.1)
        worst = max(worst, -en.min())
        Wn[r, tob[cand]] = w_
    Wn = np.maximum(Wn, 0.0)
    Wn /= np.maximum(Wn.sum(1, keepdims=True), 1e-9)
    return Wn, worst


_GLOVE_FITP = []


def glove_top_weights(objs):
    if GLOVE_WSMOOTH[0] <= 0 or ARC_HANDS not in ("fingerless", "glove") or os.environ.get("ARC_CAPS", "1") != "1":
        return
    bones = [b.name for b in arm.data.bones]
    bix = {n: i for i, n in enumerate(bones)}
    off = float(os.environ.get("ARC_GLOVE_ELBOW", "0.04"))
    sc, sa = GLOVE_WSMOOTH[0], GLOVE_WSMOOTH[1]
    for sd in "lr":
        gl = [o for o in objs if o.type == "MESH" and o.name.startswith(f"arcanist.glove_{sd}")]
        if not gl:
            continue
        e_, w_ = ARM[sd][1], ARM[sd][2]
        ax = (w_ - e_) / np.linalg.norm(w_ - e_)
        X, W0, at = [], [], []
        for o in gl:
            mw = o.matrix_world
            gname = {g.index: g.name for g in o.vertex_groups}
            for v in o.data.vertices:
                row = np.zeros(len(bones))
                for g in v.groups:
                    if gname.get(g.group) in bix:
                        row[bix[gname[g.group]]] += g.weight
                X.append((mw @ v.co)[:])
                W0.append(row)
                at.append((o, v.index))
        X, W0 = np.array(X), np.array(W0)
        k = 1 - ramp((X - e_) @ ax - off, GLOVE_WSMOOTH_BAND[0], GLOVE_WSMOOTH_BAND[1])
        sel = np.nonzero(k > 0)[0]
        if not len(sel):
            continue
        # (round her arm: about the band's own middle line, not the bone's, which lies off it)
        c_ = X[sel].mean(0)
        rad = (X - c_) - np.outer((X - c_) @ ax, ax)
        rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
        tree = cKDTree(X)
        Wn = W0.copy()
        if GLOVE_WFIT and not _GLOVE_FITP:
            _GLOVE_FITP.append(glove_fit_poses())
        if GLOVE_WFIT and _GLOVE_FITP[0] is not None:
            Wn[sel], worst = glove_fit_rows(_GLOVE_FITP[0], gl, X, W0, sel, bones)
            print("GLOVE TOP FIT %s: %d points fitted over %d poses (LAM %g, ASYM %g); most a point still sinks into her skin %.2f mm"
                  % (sd, len(sel), len(_GLOVE_FITP[0][1]), GLOVE_WFIT_LAM, GLOVE_WFIT_ASYM, worst))
        for i in (sel if not (GLOVE_WFIT and _GLOVE_FITP[0] is not None) else []):
            J = np.array(tree.query_ball_point(X[i], 2.5 * max(sc, sa)))
            D = X[J] - X[i]
            da, dn, dc = D @ ax, D @ rad[i], D @ np.cross(ax, rad[i])
            g = np.exp(-0.5 * ((da / sa) ** 2 + (dc / sc) ** 2)) * (np.abs(dn) < 0.004)
            A = np.column_stack([np.ones(len(J)), da / sa, dc / sc]) * np.sqrt(g)[:, None]
            beta = np.linalg.solve(A.T @ A + np.diag([0.0, 1e-3, 1e-3]) * g.sum(), A.T @ (W0[J] * np.sqrt(g)[:, None]))
            Wn[i] = beta[0]
        Wn = np.maximum(Wn, 0.0)
        Wn /= np.maximum(Wn.sum(1, keepdims=True), 1e-9)
        Wn = four_bones(k[:, None] * Wn + (1 - k[:, None]) * W0)
        wr = sel
        if GLOVE_CROOK_WX[0] > 0 and all(f"{n}_{sd}" in bix for n in ("upperarm", "lowerarm", "lowerarm_twist_01")):
            al_, pf_, pz_, df_, dz_ = GLOVE_CROOK_WX
            bk_ = e_ - ARM[sd][0]
            bk_ = bk_ - ax * (bk_ @ ax)
            bk_ /= np.linalg.norm(bk_)
            r_ = (X - e_) - np.outer((X - e_) @ ax, ax)
            off_c = 180.0 - np.abs(np.degrees(np.arctan2(r_ @ np.cross(ax, bk_), r_ @ bk_)))
            dt_ = np.maximum(GLOVE_TOP_D[sd](X), 0.0) if sd in GLOVE_TOP_D else np.maximum((X - e_) @ ax - off, 0.0)
            kc = (1 - ramp(off_c, pf_, pz_)) * (1 - ramp(dt_ * 1000, df_, dz_))
            iu, il, it_ = bix[f"upperarm_{sd}"], bix[f"lowerarm_{sd}"], bix[f"lowerarm_twist_01_{sd}"]
            cs = np.nonzero((kc > 0) & (Wn[:, iu] > 0) & (Wn[:, il] + Wn[:, it_] > 0))[0]
            mv_ = Wn[cs, iu] * al_ * kc[cs]
            fl_ = Wn[cs, il] / (Wn[cs, il] + Wn[cs, it_])
            Wn[cs, iu] -= mv_
            Wn[cs, il] += mv_ * fl_
            Wn[cs, it_] += mv_ * (1 - fl_)
            wr = np.union1d(sel, cs)
            print("GLOVE CROOK %s: %d points' upperarm share cut (by up to %.0f%%; most %.3f, mean %.3f)"
                  % (sd, len(cs), 100 * al_, mv_.max() if len(cs) else 0, mv_.mean() if len(cs) else 0))
        groups = {o: {g.name: g for g in o.vertex_groups} for o in gl}
        moved = 0
        for i in wr:
            o, vi = at[i]
            gs = groups[o]
            for j in np.nonzero((W0[i] > 0) | (Wn[i] > 1e-4))[0]:
                n = bones[j]
                if n not in gs:
                    gs[n] = o.vertex_groups.new(name=n)
                if Wn[i, j] > 1e-4:
                    gs[n].add([vi], float(Wn[i, j]), "REPLACE")
                else:
                    gs[n].remove([vi])
            moved += int(np.abs(Wn[i] - W0[i]).max() > 1e-4)
        print("GLOVE TOP WEIGHTS %s: %d points of %d in its top %.0f mm refitted over %.0f x %.0f mm, %d changed (most %.3f)"
              % (sd, len(sel), len(X), GLOVE_WSMOOTH_BAND[1] * 1000, sc * 1000, sa * 1000, moved, np.abs(Wn[sel] - W0[sel]).max()))


glove_top_weights(made)

# (s21, animation's panel bone, 14 Oct: helpers.py SPEC "panels" and its recipe. The Reaver's front
# panel (and its trim) onto `panel_front`, a pelvis child the game swings forward with the leading
# thigh: W = (1 - k) W_built + k panel_front, k = smoothstep(0, 0.06, top - z), top the panel's top
# edge at rest; its thighs' small share kept in that top band. PANEL_W=0: as built.)
if os.environ.get("PANEL_W", "1") == "1" and "panel_front" in arm.data.bones:
    _pobjs = [o for o in made if o.type == "MESH" and o.name.startswith("reaver.loin_front")]
    _main = [o for o in _pobjs if o.name == "reaver.loin_front"]
    if _main:
        _top = max((_main[0].matrix_world @ v.co).z for v in _main[0].data.vertices)
        _n, _ks = 0, []
        for o in _pobjs:
            vg_ = o.vertex_groups.get("panel_front") or o.vertex_groups.new(name="panel_front")
            for v in o.data.vertices:
                k_ = float(ramp(_top - (o.matrix_world @ v.co).z, 0.0, 0.06))
                for g in list(v.groups):
                    if g.group != vg_.index:
                        g.weight = g.weight * (1 - k_)
                vg_.add([v.index], k_, "REPLACE")
                for g in list(v.groups):
                    if g.weight < 1e-4 and g.group != vg_.index:
                        o.vertex_groups[g.group].remove([v.index])
                _n += 1
                _ks.append(k_)
        print("PANEL reaver.loin_front: top %.3f m, %d points onto panel_front (k mean %.2f, %d at 1)"
              % (_top, _n, float(np.mean(_ks)), int(np.sum(np.array(_ks) > 0.999))))
        # (Body 17) The lower half's fold: three shape keys (helpers.py SPEC "panels" "fold", HerJoints drives
        # them): its points below the hinge turned forward about her lateral axis through the panel's middle
        # there by `step` (a), a further `step` (b, on top of a) and back by `neg` (n), eased over +-`band`.
        import helpers as _hp
        _fd = next((p_.get("fold") for p_ in _hp.SPEC.get("panels", []) if p_["name"] == "panel_front"), None)
        if _fd and REAVER_PANEL != "old":
            _yh, _bw = _fd["hinge"], _fd["band"]
            _mw = _main[0].matrix_world
            _near = [(_mw @ v.co).y for v in _main[0].data.vertices if abs((_mw @ v.co).z - _yh) < 0.01]
            _H = np.array([0.0, float(np.median(_near)), _yh])

            def _turned(Q, deg):
                a_ = math.radians(deg)
                c_, s_ = math.cos(a_), math.sin(a_)
                d_ = Q - _H
                # (forward: her front is -Y; the panel's foot toward it and up)
                return np.c_[d_[:, 0], d_[:, 1] * c_ + d_[:, 2] * s_, -d_[:, 1] * s_ + d_[:, 2] * c_] + _H
            _moved = 0
            for o in _pobjs:
                me_ = o.data
                n_ = len(me_.vertices)
                if me_.shape_keys is None:
                    o.shape_key_add(name="Basis", from_mix=False)
                base_ = np.empty(n_ * 3)
                me_.shape_keys.reference_key.data.foreach_get("co", base_)
                base_ = base_.reshape(-1, 3)
                M_ = np.array(o.matrix_world)
                Wp = base_ @ M_[:3, :3].T + M_[:3, 3]
                t_ = np.clip((_yh + _bw - Wp[:, 2]) / (2 * _bw), 0, 1)
                w_ = (t_ * t_ * (3 - 2 * t_))[:, None]
                Minv = np.linalg.inv(M_[:3, :3])
                d1 = w_ * (_turned(Wp, _fd["step"]) - Wp)
                d2 = w_ * (_turned(Wp, 2 * _fd["step"]) - Wp) - d1
                dn = w_ * (_turned(Wp, -_fd["neg"]) - Wp)
                for nm_, d_ in zip(_fd["shapes"], (d1, d2, dn)):
                    kb_ = o.shape_key_add(name=nm_, from_mix=False)
                    kb_.data.foreach_set("co", (base_ + d_ @ Minv.T).ravel())
                # (Body 18) its half over each thigh lifted along its face (her front, -Y) as that thigh swings forward
                # (helpers.py SPEC "panels" "fold" "side"; HerJoints drives them): none in its top 3 cm, all 12 cm down
                _sd = _fd.get("side")
                if _sd:
                    g2_ = np.clip((_top - Wp[:, 2] - 0.03) / 0.09, 0, 1)
                    for nm_, sg_ in zip(_sd["shapes"], (1, -1)):
                        t2_ = np.clip((sg_ * Wp[:, 0] - _sd["x"][0]) / (_sd["x"][1] - _sd["x"][0]), 0, 1)
                        d_ = np.zeros_like(Wp)
                        d_[:, 1] = -_sd["lift"] * t2_ * t2_ * (3 - 2 * t2_) * g2_
                        kb_ = o.shape_key_add(name=nm_, from_mix=False)
                        kb_.data.foreach_set("co", (base_ + d_ @ Minv.T).ravel())
                _moved += int((w_[:, 0] > 0).sum())
            print("PANEL FOLD reaver.loin_front: hinge %.3f m (middle y %.3f), %d points in its lower half, shapes %s"
                  % (_yh, _H[1], _moved, ", ".join(_fd["shapes"])))


def rings_one(objs):
    """(s18 ranger solver 2, RING_ONE) Each ring of a roll back on one blend
    after the helpers' split, as tube() made it: the blend of the sheet round
    the ring as split (24 nearest points, weighed by nearness, eased along
    the line), the roll's stitches on their ring's, and the sheet under the
    roll on it too, eased back to its own over RING_BAND in from the roll's
    inner reach, so roll, stitches and edge move as one. Split point by
    point, a ring's twelve points took the skin under each: round the
    ranger's leg-line rolls her right and left thighs' shares varied by up to
    0.29 within a ring (corset_bind1 ring 261, under her crotch), and posed
    the rings sheared up to 6 mm and the roll left its edge: judge fin2's
    slit (item 6, r_leo_f (865,714)) and much of the knob."""
    if not RING_ONE:
        return
    bones = [b.name for b in arm.data.bones]
    bi = {n: i for i, n in enumerate(bones)}
    by = {o.name: o for o in objs if o.type == "MESH"}

    def wts(o):
        gname = {g.index: g.name for g in o.vertex_groups}
        w_ = np.zeros((len(o.data.vertices), len(bones)))
        for v in o.data.vertices:
            for g in v.groups:
                if gname[g.group] in bi:
                    w_[v.index, bi[gname[g.group]]] += g.weight
        return w_

    def where(o):
        # (the pieces' own space, the space their rings were made in)
        return np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3)

    def put(o, idx, rows):
        groups = {g.name: g for g in o.vertex_groups}
        for i, r in zip(idx, rows):
            i = int(i)
            for gi in [g.group for g in o.data.vertices[i].groups]:
                if o.vertex_groups[gi].name in bi:
                    o.vertex_groups[gi].remove([i])
            for j in np.nonzero(r > 1e-4)[0]:
                if bones[j] not in groups:
                    groups[bones[j]] = o.vertex_groups.new(name=bones[j])
                groups[bones[j]].add([i], float(r[j]), "REPLACE")

    band = {}
    for rn in sorted(RING_ONE):
        roll = by.get(rn)
        if roll is None or "ring_pts" not in roll:
            continue
        base, k = rn.rsplit("_bind", 1)
        sheet = by.get(base)
        if sheet is None:
            continue
        nv = int(roll["ring_nv"])
        rp = np.array(roll["ring_pts"], float).reshape(-1, nv, 3)
        c0 = rp.mean(1)
        out = rp[:, 0] - c0
        rw = np.linalg.norm(out, axis=1)
        out /= rw[:, None] + 1e-12
        up = rp[:, nv // 4] - c0
        rh = np.linalg.norm(up, axis=1)
        up /= rh[:, None] + 1e-12
        if base not in band:
            band[base] = (where(sheet), wts(sheet), [])
        ps, ws, parts = band[base]
        kk = min(24, len(ps))
        d_, j_ = cKDTree(ps).query(c0, k=kk)
        d_, j_ = np.reshape(d_, (len(c0), kk)), np.reshape(j_, (len(c0), kk))
        g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
        ring = (ws[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
        for _ in range(8):
            ring = (np.roll(ring, 1, 0) + 2 * ring + np.roll(ring, -1, 0)) / 4
        ring = four_bones(ring)
        vr = where(roll)
        ri = np.minimum(cKDTree(rp.reshape(-1, 3)).query(vr)[1] // nv, len(c0) - 1)
        wr = wts(roll)
        spread = max((np.abs(wr[ri == i] - wr[ri == i].mean(0)).sum(1).max() for i in range(len(c0)) if (ri == i).any()), default=0.0)
        put(roll, range(len(vr)), ring[ri])
        st = by.get(base + "_stitch" + (k or "0"))
        nst = 0
        if st is not None and len(st.data.vertices):
            vs = where(st)
            put(st, range(len(vs)), ring[cKDTree(c0).query(vs)[1]])
            nst = len(vs)
        dn, jn = cKDTree(c0).query(ps)
        s_ = ((ps - c0[jn]) * out[jn]).sum(1)
        h_ = ((ps - c0[jn]) * up[jn]).sum(1)
        t_ = np.clip((-s_ - rw[jn]) / max(RING_BAND, 1e-6), 0, 1)
        f_ = np.where((dn < rw[jn] + RING_BAND + 0.002) & (np.abs(h_) < rh[jn] + 0.002), 1 - t_ * t_ * (3 - 2 * t_), 0.0)
        parts.append((f_, ring[jn]))
        print("RING_ONE %s: %d rings on one blend each (their points' shares had differed by up to %.2f); %d stitch points on theirs; %d points of %s under it shared"
              % (rn, len(c0), spread, nst, int((f_ > 1e-3).sum()), base))
    for base, (ps, ws, parts) in band.items():
        F = sum(f_ for f_, _ in parts)
        sel = np.nonzero(F > 1e-3)[0]
        if not len(sel):
            continue
        acc = sum(f_[sel, None] * r_[sel] for f_, r_ in parts)
        Fs = F[sel, None]
        new = np.where(Fs > 1, acc / np.maximum(Fs, 1e-9), acc + ws[sel] * (1 - Fs))
        put(by[base], sel, four_bones(new))


rings_one(made)

# (s25 gs2, G1: the three points down the back of her hand ride the glove's sheet as finally weighted
# (helpers split, top refitted, rings): each point of a thread takes the blend of the sheet under it,
# so thread and cuff move as one in the fist and the open hand. GLOVE_RIDERS=0: as laid.)
def glove_riders(objs):
    if os.environ.get("GLOVE_RIDERS", "1") != "1":
        return
    bones = [b.name for b in arm.data.bones]
    bi = {n: i for i, n in enumerate(bones)}
    for sd in "lr":
        sheet = [o for o in objs if o.type == "MESH" and o.name == f"arcanist.glove_{sd}"]
        riders = [o for o in objs if o.type == "MESH" and o.name.startswith(f"arcanist.glove_{sd}_point")]
        if not sheet or not riders:
            continue
        sh = sheet[0]
        mw = sh.matrix_world
        sp = np.array([(mw @ v.co)[:] for v in sh.data.vertices])
        gname = {g.index: g.name for g in sh.vertex_groups}
        sw = np.zeros((len(sp), len(bones)))
        for v in sh.data.vertices:
            for g in v.groups:
                if gname.get(g.group) in bi:
                    sw[v.index, bi[gname[g.group]]] += g.weight
        tris = [tuple(p.vertices) for p in sh.data.polygons]
        bvh = BVHTree.FromPolygons([tuple(x) for x in sp], tris)
        worst, n = 0.0, 0
        for o in riders:
            mo = o.matrix_world
            rows = []
            for v in o.data.vertices:
                q = mo @ v.co
                co, _, fi, dist = bvh.find_nearest(q)
                vs = tris[fi]
                # (the face's blend at the nearest point: weights by inverse distance to its corners)
                dd = np.linalg.norm(sp[list(vs)] - np.array(co[:]), axis=1)
                k = 1.0 / np.maximum(dd, 1e-6)
                rows.append((k[:, None] * sw[list(vs)]).sum(0) / k.sum())
                worst = max(worst, dist)
            rows = four_bones(np.array(rows))
            rows /= np.maximum(rows.sum(1, keepdims=True), 1e-9)
            for vg in list(o.vertex_groups):
                if vg.name in bi:
                    o.vertex_groups.remove(vg)
            groups = {}
            for i, r in enumerate(rows):
                for j in np.nonzero(r > 1e-4)[0]:
                    if bones[j] not in groups:
                        groups[bones[j]] = o.vertex_groups.new(name=bones[j])
                    groups[bones[j]].add([i], float(r[j]), "REPLACE")
            n += len(rows)
        print("GLOVE RIDERS %s: %d points of %d threads on the sheet's own weights (furthest %.1f mm off it)" % (sd, n, len(riders), worst * 1000))


# (s26 solver gs5: GLOVE_HAND_EXACT again, last, on her body's final weights: the sheet's blend taken at build
# time still carried 0.04 of her hand up the thumb sleeve where her exported skin has none (her rig's later
# passes), 3 mm off her with her thumb spread. So every layer of each fingerless glove (sheet, hem, piping)
# takes, in its hand part, her final skin's own blend at its nearest point, before the cords ride it.)
# (s27 solver, judge gl r2 fixes 2 and 3: GLOVE_EDGE_EASE "knuckle sigma,thumb sigma,full,none" (m). Her skin's
# weights are coarse at her hand: round her index knuckle's thumb side a ring of points half hand, half finger, which
# the knuckle edge ran along between ends on the finger (0.9), and at her thumb cut thumb_02/03 shares uneven point
# to point (0.65-0.98). The cut was smooth at rest (radius 5-8 mm), but in her fist the knuckle edge doubled back
# on itself at the index knuckle (radius 1.2 mm, 162 deg in 6 mm: the hook) and the thumb cut zig-zagged (1.4 mm,
# 135 deg: the crown), as her skin there does. So each hand opening's blend is eased along the opening (Gaussian,
# sigma of arc; the thumb hole's by its own sigma) and every layer (sheet, hem, piping) takes the change in full
# within `full` of the edge, none past `none`. "": as before.)
GLOVE_EDGE_EASE = [float(v) for v in os.environ.get("GLOVE_EDGE_EASE", "").split(",") if v]
# (s27: GLOVE_EDGE_EASE_IDX "small,lo,hi": on the knuckle opening the wide sigma only where the edge carries her
# index finger (its blend share, smoothed along the loop, eased in from lo to hi), `small` elsewhere: the wide ease
# everywhere mixed ring into pinky on the back of her hand (L knuckle edge 2.92 mm off her in cast_raise))
GLOVE_EDGE_EASE_IDX = [float(v) for v in os.environ.get("GLOVE_EDGE_EASE_IDX", "").split(",") if v]


def glove_edge_delta(sd, bp, tri, bw, bvh, handc, thumbc):
    """(GLOVE_EDGE_EASE) The hand openings' points of the glove's sheet and, at each, the change its eased blend
    makes to her skin's own blend there: (tree of the points, changes), or None."""
    sh = SHEET.get(f"arcanist.glove_{sd}")
    if len(GLOVE_EDGE_EASE) < 4 or sh is None:
        return None
    spos, stris = sh[0], sh[1]
    def blend(q):
        co, _n, fi, _d = bvh.find_nearest(Vector(q))
        if co is None:
            return np.zeros(bw.shape[1])
        a_, b_, c_ = bp[tri[fi]]
        v0, v1, v2 = b_ - a_, c_ - a_, np.array(co[:]) - a_
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = max(d00 * d11 - d01 * d01, 1e-18)
        bv = (d11 * d20 - d01 * d21) / den
        bw_ = (d00 * d21 - d01 * d20) / den
        bc = np.clip(np.array([1 - bv - bw_, bv, bw_]), 0, 1)
        return bc @ bw[tri[fi]] / max(bc.sum(), 1e-9)
    pts, dl = [], []
    for lp in edge_loops(stris):
        L = spos[np.array(lp)]
        W_ = np.array([blend(q) for q in L])
        if W_[:, handc].sum(1).mean() < 0.5:
            continue
        thumb_ = W_[:, thumbc].sum(1).mean() > 0.3
        sg = GLOVE_EDGE_EASE[1] if thumb_ else GLOVE_EDGE_EASE[0]
        seg = np.linalg.norm(np.roll(L, -1, 0) - L, axis=1)
        s = np.r_[0, np.cumsum(seg)[:-1]]
        tot = seg.sum()
        ds = (s[:, None] - s[None, :] + tot / 2) % tot - tot / 2
        K = np.exp(-0.5 * (ds / sg) ** 2)
        K /= K.sum(1, keepdims=True)
        if not thumb_ and len(GLOVE_EDGE_EASE_IDX) >= 3:
            idxc = np.array([b.name.startswith("index") for b in arm.data.bones])
            t_ = np.clip((K @ W_[:, idxc].sum(1) - GLOVE_EDGE_EASE_IDX[1]) / (GLOVE_EDGE_EASE_IDX[2] - GLOVE_EDGE_EASE_IDX[1]), 0, 1)
            sgv = GLOVE_EDGE_EASE_IDX[0] + (sg - GLOVE_EDGE_EASE_IDX[0]) * t_ * t_ * (3 - 2 * t_)
            K = np.exp(-0.5 * (ds / sgv[:, None]) ** 2)
            K /= K.sum(1, keepdims=True)
            print("GLOVE EDGE EASE %s knuckle: sigma %.0f-%.0f mm by her index share (wide at %d of %d points)"
                  % (sd, sgv.min() * 1000, sgv.max() * 1000, (t_ > 0.5).sum(), len(L)))
        d_ = K @ W_ - W_
        pts.append(L)
        dl.append(d_)
        print("GLOVE EDGE EASE %s %s: %d points, %.0f mm, sigma %.0f mm, blend moved L1 up to %.2f (mean %.2f)"
              % (sd, "thumb" if thumb_ else "knuckle", len(L), tot * 1000, sg * 1000, np.abs(d_).sum(1).max(), np.abs(d_).sum(1).mean()))
    if not pts:
        return None
    return cKDTree(np.vstack(pts)), np.vstack(dl)


def glove_hand_final(objs):
    ex = tuple(float(v) for v in os.environ.get("GLOVE_HAND_EXACT", "0.5,0.9").split(","))
    if len(ex) < 2 or ARC_HANDS != "fingerless":
        return
    bones = [b.name for b in arm.data.bones]
    bi = {n: i for i, n in enumerate(bones)}
    handc = np.array([n.split("_")[0] in ("hand", "thumb", "index", "middle", "ring", "pinky") for n in bones])
    bm_ = body.data
    bm_.calc_loop_triangles()
    mwb = body.matrix_world
    bp = np.array([(mwb @ v.co)[:] for v in bm_.vertices])
    gname = {g.index: g.name for g in body.vertex_groups}
    bt = np.array([t.vertices[:] for t in bm_.loop_triangles])
    for sd in "lr":
        gl = [o for o in objs if o.type == "MESH" and o.name.startswith(f"arcanist.glove_{sd}") and "_point" not in o.name]
        if not gl:
            continue
        gp = np.vstack([np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]) for o in gl])
        near = cKDTree(gp).query(bp, distance_upper_bound=0.03)[0] < 0.03
        tri = bt[near[bt].all(1)]
        used = np.unique(tri)
        bw = np.zeros((len(bp), len(bones)))
        for i in used:
            for g in bm_.vertices[i].groups:
                n = gname.get(g.group)
                if n in bi:
                    bw[i, bi[n]] += g.weight
        bvh = BVHTree.FromPolygons([tuple(q) for q in bp], tri.tolist())
        ed_ = glove_edge_delta(sd, bp, tri, bw, bvh, handc, np.array([n.startswith("thumb") for n in bones])) if GLOVE_EDGE_EASE else None
        nmv, worst = 0, 0.0
        for o in gl:
            ogn = {g.index: g.name for g in o.vertex_groups}
            groups = {g.name: g for g in o.vertex_groups}
            rows, ks = [], []
            for v in o.data.vertices:
                q = o.matrix_world @ v.co
                old = np.zeros(len(bones))
                for g in v.groups:
                    if ogn.get(g.group) in bi:
                        old[bi[ogn[g.group]]] += g.weight
                co, _n, fi, _d = bvh.find_nearest(q)
                if co is None:
                    rows.append(old); ks.append(0.0)
                    continue
                a_, b_, c_ = bp[tri[fi]]
                v0, v1, v2 = b_ - a_, c_ - a_, np.array(co[:]) - a_
                d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
                den = max(d00 * d11 - d01 * d01, 1e-18)
                bv = (d11 * d20 - d01 * d21) / den
                bw_ = (d00 * d21 - d01 * d20) / den
                bc = np.clip(np.array([1 - bv - bw_, bv, bw_]), 0, 1)
                sx = bc @ bw[tri[fi]] / max(bc.sum(), 1e-9)
                k = np.clip((sx[handc].sum() - ex[0]) / (ex[1] - ex[0]), 0, 1)
                k = k * k * (3 - 2 * k)
                rows.append(old * (1 - k) + sx * k); ks.append(k)
            if ed_ is not None:
                # (GLOVE_EDGE_EASE: the opening's eased blend, in full near its edge, faded out into the glove)
                gpo = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
                dd_, jj_ = ed_[0].query(gpo)
                f_ = 1 - np.clip((dd_ - GLOVE_EDGE_EASE[2]) / (GLOVE_EDGE_EASE[3] - GLOVE_EDGE_EASE[2]), 0, 1)
                f_ = f_ * f_ * (3 - 2 * f_) * np.array(ks)
                rows = list(np.maximum(np.array(rows) + f_[:, None] * ed_[1][jj_], 0))
            rows = four_bones(np.array(rows))
            rows /= np.maximum(rows.sum(1, keepdims=True), 1e-9)
            ks = np.array(ks)
            for i in np.nonzero(ks > 0)[0]:
                for g in list(o.data.vertices[i].groups):
                    if o.vertex_groups[g.group].name in bi:
                        o.vertex_groups[g.group].remove([int(i)])
                for j in np.nonzero(rows[i] > 1e-4)[0]:
                    if bones[j] not in groups:
                        groups[bones[j]] = o.vertex_groups.new(name=bones[j])
                    groups[bones[j]].add([int(i)], float(rows[i, j]), "REPLACE")
            nmv += int((ks > 0).sum())
        print("GLOVE HAND FINAL %s: %d points of %d layers on her final skin's blend" % (sd, nmv, len(gl)))


glove_hand_final(made)

glove_riders(made)
pieces_of = {name: [o for o in made if o.name.startswith(name + ".")] for name in OUTFITS}
slot_check([o for v_ in pieces_of.values() for o in v_], "export")
ARMOR_ROWS = []
for name in OUTFITS:
    mine = pieces_of[name]
    if not mine:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in mine:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    # Text and binary apart, the textures beside them in one folder that
    # every outfit shares (embedded, each file carried its own copies).
    path = os.path.join(os.path.dirname(OUT), f"heroine_outfit_{name}.gltf")
    detail(mine)
    by_mat = {}
    for o in mine:
        by_mat.setdefault(o.data.materials[0].name if o.data.materials else "none", []).append(o)
    joined = []
    ranks = {}
    for key, objs in by_mat.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        # (armor lead 1: a mesh per (slot, material), <outfit>.<slot>.<material>. Each slot's pieces are
        # joined in the order one join of the material's took them, the active piece and then the rest as
        # the view layer lists them, so the slots' meshes laid end to end in rank order are that one mesh:
        # heroine_lod.py joins them back so)
        order = [objs[0]] + [o for o in bpy.context.view_layer.objects if o.select_get() and o is not objs[0]]
        assert len(order) == len(objs)
        by_slot = {}
        for o in order:
            by_slot.setdefault(slot_entry(o.name)["slot"], []).append(o)
        seq = [slot_entry(o.name)["slot"] for o in order]
        runs = sum(1 for i_ in range(len(seq)) if i_ == 0 or seq[i_] != seq[i_ - 1])
        if runs != len(by_slot):
            print("SLOT ORDER %s.%s: its slots interleave in the join (%d runs of %d slots): heroine_lod.py lays its pieces back in order" % (name, key, runs, len(by_slot)))
        for rank, (slot, sobjs) in enumerate(by_slot.items()):
            # (each piece's place in the material's one join and its triangles, in this mesh's order)
            pieces_ = [[order.index(o), sum(len(f_.vertices) - 2 for f_ in o.data.polygons)] for o in sobjs]
            bpy.ops.object.select_all(action="DESELECT")
            for o in sobjs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = sobjs[0]
            if len(sobjs) > 1:
                # (her corrective shapes kept through the join: heroine_rig)
                rig_helpers.share_keys(sobjs)
                bpy.ops.object.join()
            sobjs[0].name = sobjs[0].data.name = f"{name}.{slot}.{key}"
            joined.append(sobjs[0])
            ranks[sobjs[0].name] = {"outfit": name, "slot": slot, "material": key, "rank": rank, "pieces": pieces_}
    print("MERGED", name, len(mine), "pieces into", len(joined), "meshes")
    mine = joined
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in mine:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="outfit_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True, export_vertex_color="ACTIVE")
    # (its points that took her neck's weights follow her neck's skin as heroine_neck.match_graft changed it)
    import heroine_neck
    if float(os.environ.get("NECK_CUT", "0.03")):
        heroine_neck.match_pieces(path, heroine_neck.field())
    # (STRAP_ROWS, armor 8 r4: the straps' rows share their weights again after that, see tools/assets/strap_rows.py)
    fr_ = {k_: v_ for k_, v_ in RIBBON_FRAME.items() if k_.startswith(name + ".")}
    if fr_:
        import strap_rows
        strap_rows.even(path, fr_)
    # (each mesh's slot, material and rank in its material's join, as glTF extras: heroine_lod.py and the game read them)
    g_ = _json.load(open(path, encoding="utf-8"))
    for m_ in g_["meshes"]:
        if m_["name"] in ranks:
            m_["extras"] = dict(m_.get("extras", {}), **ranks[m_["name"]])
    _json.dump(g_, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    slots_ = {}
    for mn_, r_ in ranks.items():
        slots_.setdefault(r_["slot"], []).append(mn_)
    for slot, meshes_ in sorted(slots_.items()):
        e_ = next(e for e in ARMOR_MAP["outfits"][name] if e["slot"] == slot)
        tk_ = (name, slot) in ARMOR_TUCK_N
        ARMOR_ROWS.append({"id": f"{name}.{slot}", "outfit": name, "slot": slot, "layer": ARMOR_MAP["layers"][slot],
                           "covers": e_.get("covers", [slot]), "meshes": sorted(meshes_),
                           "tuck": f"armor_tuck/{name}.{slot}.bin" if tk_ else None,
                           "tuck_count": ARMOR_TUCK_N.get((name, slot)), "body_hash": ARMOR_BODY_HASH,
                           **({"under": e_["under"]} if "under" in e_ else {}),
                           **({"hold": {"amount": 0.55, "squash": 0}} if (name, slot) == ("warden", "top") else {})})  # (plate holds her: HerJiggle)
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)
# (armor lead 1: one row per (outfit, slot); body_hash as armor_tuck_write has it)
_json.dump(ARMOR_ROWS, open(os.path.join(os.path.dirname(OUT), "armor_index.json"), "w", encoding="utf-8"), indent=1)
print("ARMOR INDEX: %d (outfit, slot) rows -> %s" % (len(ARMOR_ROWS), os.path.join(os.path.dirname(OUT), "armor_index.json")))
