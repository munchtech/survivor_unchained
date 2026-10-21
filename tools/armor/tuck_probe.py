"""THE BOUNDED TUCK's proof on one outfit (armor 7, 20 Oct): her skin's tuck under the outfit's channel and one slot,
by the old rule (TUCK_SMOOTH off) and the new, with a pose check of the slot's pieces, into a scratch dir only.

    blender -b <heroine_built.blend> --python tools/armor/tuck_probe.py -- <scratch dir> [outfit] [slot]

Runs tools/assets/heroine_outfits.py's body preparation, that outfit's build (--only) and the machinery up to
`if BODY_OUT:` (as piece_blender.py does, textures redirected into the scratch dir); writes <scratch>/probe.npz.
Nothing in godot/ is written.
"""
import os
import sys
import time

T0 = time.time()
ARGS = sys.argv[sys.argv.index("--") + 1:]
SCRATCH = os.path.abspath(ARGS[0])
OUTFIT = ARGS[1] if len(ARGS) > 1 else "warden"
SLOT = ARGS[2] if len(ARGS) > 2 else "top"
HERE = os.path.dirname(os.path.abspath(__file__))
HO = os.path.join(HERE, "..", "assets", "heroine_outfits.py")
os.makedirs(os.path.join(SCRATCH, "tex"), exist_ok=True)
src = open(HO, encoding="utf-8").read()
M_LOOP = ("made = []\nfor name, build in OUTFITS.items():\n    if ONLY and name != ONLY:\n        continue\n"
          "    made += [o for o in build() if o]\n")
M_BODY = "if BODY_OUT:\n    me = body.data\n"


def stamp(msg):
    print("PROBE [%6.1fs] %s" % (time.time() - T0, msg), flush=True)


def run(i, j, ns, patch=()):
    seg = src[i:j]
    for old, new in patch:
        assert seg.count(old) == 1, old
        seg = seg.replace(old, new)
    exec(compile("\n" * src.count("\n", 0, i) + seg, HO, "exec"), ns)


sys.argv = [sys.argv[0], "--", os.path.join(SCRATCH, "x"), "--only", OUTFIT]
NS = {"__name__": "heroine_outfits", "__file__": os.path.abspath(HO), "ARMOR_TEX_OUT": os.path.join(SCRATCH, "tex")}
run(0, src.index(M_BODY), NS, patch=[('out = os.path.join(TEX, f"outfit_{key}_diff.jpg")', 'out = os.path.join(ARMOR_TEX_OUT, f"outfit_{key}_diff.jpg")')])
stamp("body prepared, %s built, machinery ready" % OUTFIT)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

G = NS
body, arm, made = G["body"], G["arm"], G["made"]
me = body.data
hides = [o for o in made if o.name.startswith(OUTFIT + ".") and o.get("hides")]
shides = [o for o in hides if G["slot_entry"](o.name)["slot"] == SLOT]
stamp("%d hiding pieces, %d in slot %s: %s" % (len(hides), len(shides), SLOT, [o.name for o in shides]))
# (a slot that hides nothing, a rigid plate's (armor 8: the warden's pauldrons): its pieces all checked, her skin untucked)
spieces = shides or [o for o in made if o.name.startswith(OUTFIT + ".") and G["slot_entry"](o.name)["slot"] == SLOT]
res = {}
for mode in (0, 1):
    G["TUCK_SMOOTH"] = bool(mode)
    res[f"whole{mode}"] = G["tuck_of"](OUTFIT, hides)[0]
    res[f"whole{mode}_cos"] = G["TUCK_LAST"]["cos"]
    if shides:
        res[f"slot{mode}"] = G["tuck_of"](OUTFIT, shides, SLOT)[0]
        res[f"slot{mode}_cos"] = G["TUCK_LAST"]["cos"]
    else:
        res[f"slot{mode}"] = np.zeros(len(me.vertices))
        res[f"slot{mode}_cos"] = np.zeros(len(me.vertices))
    stamp("mode %d done" % mode)

# ---- pose check (piece_blender.py's, on the slot's pieces): her skin through them, untucked and tucked
POSES = {
    "arms_overhead": [("clavicle_l", (0, 1, 0), 25, (0, 0, 1)), ("clavicle_r", (0, 1, 0), 25, (0, 0, 1)),
                      ("upperarm_l", (0, 1, 0), 110, (0, 0, 1)), ("upperarm_r", (0, 1, 0), 110, (0, 0, 1))],
    "reach_across_r": [("upperarm_r", (0, 0, 1), 80, (1, -1, 0)), ("lowerarm_r", (0, 0, 1), 60, (1, -1, 0))],
    "arms_back": [("upperarm_l", (0, 0, 1), 40, (0, 1, 0)), ("upperarm_r", (0, 0, 1), 40, (0, 1, 0))],
    "hug": [("clavicle_l", (0, 0, 1), 15, (0, -1, 0)), ("clavicle_r", (0, 0, 1), 15, (0, -1, 0)),
            ("upperarm_l", (0, 0, 1), 70, (0, -1, 0)), ("upperarm_r", (0, 0, 1), 70, (0, -1, 0))],
    "twist_bend": [("spine_02", (1, 0, 0), 20, (0, -1, 0)), ("spine_03", (0, 0, 1), 25, (1, 0, 0))],
    "arms_down": [("upperarm_l", (0, 1, 0), 40, (0, 0, -1)), ("upperarm_r", (0, 1, 0), 40, (0, 0, -1))],
    "arms_forward": [("upperarm_l", (1, 0, 0), 75, (0, -1, 0)), ("upperarm_r", (1, 0, 0), 75, (0, -1, 0))],
}


def pose(rots):
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
        pb[bone].rotation_quaternion = (R.inverted() @ Quaternion(Vector(axis), np.radians(deg)).to_matrix() @ R).to_quaternion()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg)
    m_ = be.to_mesh()
    bv = np.array([(body.matrix_world @ v.co)[:] for v in m_.vertices])
    bn = np.array([(body.matrix_world.to_3x3() @ v.normal)[:] for v in m_.vertices])
    be.to_mesh_clear()
    vs, fs = [], []
    for o in spieces:
        oe = o.evaluated_get(dg)
        mm = oe.to_mesh()
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in mm.vertices]
        fs += [[base + i for i in p_.vertices] for p_ in mm.polygons]
        oe.to_mesh_clear()
    return bv, bn, BVHTree.FromPolygons(vs, fs), np.array(vs)


BF = [list(p_.vertices) for p_ in me.polygons]
bv0, bn0, _, sv0 = pose([])
lo, hi = sv0.min(0) - 0.03, sv0.max(0) + 0.03
NEAR = np.nonzero(((bv0 > lo) & (bv0 < hi)).all(1))[0]
PC = {}
for pname, rots in [("rest", [])] + list(POSES.items()):
    bv, bn, tree, sv = pose(rots)
    row = {"piece_moved_mm": round(float(np.abs(sv - sv0).max() * 1000), 1)}
    # (how deep the slot's pieces go into her skin: its points under her surface, nearest-face signed)
    btree = BVHTree.FromPolygons([tuple(v) for v in bv], BF)
    sd_ = []
    for v in sv:
        q_, n_, _, _ = btree.find_nearest(Vector(v))
        sd_.append((Vector(v) - q_).dot(n_) if q_ is not None else 1.0)
    sd_ = np.array(sd_)
    row["piece_in_1mm"] = int((sd_ < -0.001).sum())
    row["piece_deepest_mm"] = round(float(-sd_.min() * 1000), 1)
    for mode in (0, 1):
        tk = res[f"slot{mode}"]
        thr = 0
        for i in NEAR:
            n_ = bn[i] / (np.linalg.norm(bn[i]) + 1e-12)
            p_ = bv[i] - n_ * 0.010 * (1.0 if tk[i] > 0.973 else tk[i])
            f_ = tree.ray_cast(Vector(p_ + n_ * 0.0001), Vector(n_), 0.03)
            if f_[0] is None and tree.ray_cast(Vector(p_ + n_ * 0.0001), Vector(-n_), 0.012)[0] is not None:
                thr += 1
        row[f"through_tucked_{mode}"] = thr
    PC[pname] = row
    print("POSE", pname, row, flush=True)
pose([])
ed = np.array([e.vertices[:] for e in me.edges])
np.savez_compressed(os.path.join(SCRATCH, "probe.npz"), bv0=bv0, bn0=bn0, edges=ed, co_local=np.array([v.co[:] for v in me.vertices]),
                    poses=np.array(repr(PC)), near=NEAR, **res)
stamp("written %s" % os.path.join(SCRATCH, "probe.npz"))
