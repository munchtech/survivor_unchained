"""Her helper bones built into a body (hers or the hero's), and every mesh
bound to the skeleton split onto them, in Blender. What the helpers are, and
why, is tools/anim/helpers.py; the game drives them (HerJoints.cs).

    import heroine_rig
    heroine_rig.apply(armature, meshes)     # bones added once; weights split

Called by heroine_outfits.py just before it exports: her body and every
piece she wears take the same split, so cloth and skin move as one. The
split only moves weight her upper arms, forearms, collarbones, thighs and
calves already had onto the helpers that lie along them; a body without the
driver moves as it did.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "anim"))
import helpers as hp  # noqa: E402

# Her front in Blender's space (the game's +Z).
FRONT = (0.0, -1.0, 0.0)


def _active(o):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def add_bones(arm, chain=False):
    """The helper bones, if the armature lacks them: twist bones along their
    parents in their parents' frames; share bones at their joints in the
    lower bone's frame turned about its line onto the joint's hinge. The
    upper arm's twist chain (helpers SPEC "twist_chain") only with `chain`
    (hers, explicitly: never the hero's or an NPC's)."""
    have = {b.name for b in arm.data.bones}
    want = [(h, n) for h in hp.SPEC["helpers"] if chain or not h.get("chain") for n in hp.each(h["name"])]
    panels = [p for p in hp.SPEC.get("panels", []) if p["parent"] in have]
    if all(n in have for _, n in want) and all(p["name"] in have for p in panels):
        return 0
    _active(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    made = 0
    for h, n in want:
        if n in eb:
            continue
        s = n[-1]
        parent = eb[h["parent"].replace("{s}", s)]
        if h["kind"] in ("share", "point"):
            low = eb[h["bone"].replace("{s}", s)]
            above = low.parent
            g = low.matrix.to_quaternion()
            turn = hp.hinge_turn((g.x, g.y, g.z, g.w), tuple(above.head), tuple(low.head), h["way"], FRONT)
            m = low.matrix @ Matrix.Rotation(math.radians(turn), 4, "Y")
            length = low.length * 0.5
        else:
            main = eb[hp.MAIN_CHILD[parent.name.split("_")[0]] + "_" + s]
            m = parent.matrix.copy()
            m.translation = parent.head + (main.head - parent.head) * h["at"]
            length = 0.04
        b = eb.new(n)
        # (a new bone has no length, and a bone with none takes no frame)
        b.head = (0.0, 0.0, 0.0)
        b.tail = (0.0, length, 0.0)
        b.matrix = m
        b.length = length
        b.parent = parent
        b.use_connect = False
        b.use_deform = True
        made += 1
    # Panel bones (SPEC "panels"): at the parent's head + pivot (her rest
    # axes, game's +Y up / +Z front: Blender's +Z up / -Y front), pointing
    # down the panel, its +Z her front and +X her right (the game turns it
    # about that X: HerJoints, helpers.drive_panels).
    for p in panels:
        if p["name"] in eb:
            continue
        parent = eb[p["parent"]]
        gx, gy, gz = p["pivot"]
        h = parent.head + Vector((gx, -gz, gy))
        m = Matrix(((-1.0, 0.0, 0.0, h.x), (0.0, 0.0, -1.0, h.y), (0.0, -1.0, 0.0, h.z), (0.0, 0.0, 0.0, 1.0)))
        b = eb.new(p["name"])
        b.head = (0.0, 0.0, 0.0)
        b.tail = (0.0, p["length"], 0.0)
        b.matrix = m
        b.length = p["length"]
        b.parent = parent
        b.use_connect = False
        b.use_deform = True
        print(f"RIG panel {p['name']}: head {tuple(round(v, 4) for v in b.head)} tail {tuple(round(v, 4) for v in b.tail)}")
        made += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    return made


def split_mesh(arm, obj, skin=None, body=None):
    """The mesh's weights onto the helpers (helpers.split), its other vertex
    groups left as they are. With `skin` (a point to the nearest point of her
    skin, in world space), a piece she wears is split where the skin under it
    lies, not where it lies itself: the crease cut and the twist bones'
    reach are read along her skin, so cloth takes the split of the skin it
    covers (split at its own offset, cloth behind a knee was cut deeper into
    the crease than the skin under it, and the skin came through). Points
    far off her (a cape's hem) ease back to their own place."""
    bones = [b.name for b in arm.data.bones]
    index = {n: i for i, n in enumerate(bones)}
    heads = {b.name: np.array((arm.matrix_world @ b.head_local)[:]) for b in arm.data.bones}
    gname = {g.index: g.name for g in obj.vertex_groups}
    # Only points the split can touch: those with weight on a bone a helper
    # helps (collarbone, upper arm, forearm, thigh, calf).
    src = set()
    for pair in hp.SPEC["weights"]["pairs"]:
        for t in pair[:2]:
            src.update(hp.each(t))
    me = obj.data
    rows, pts = [], []
    for v in me.vertices:
        gs = [(gname.get(g.group), g.weight) for g in v.groups]
        if not any(n in src and w > 0 for n, w in gs):
            continue
        rows.append((v.index, gs))
        pts.append((obj.matrix_world @ v.co)[:])
    if not rows:
        return 0
    if skin is not None:
        own = np.array(pts)
        near = np.array([skin(p) for p in pts])
        d = np.linalg.norm(own - near, axis=1)
        t = np.clip((d - SKIN_NEAR) / SKIN_NEAR, 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        pts = near + (own - near) * t[:, None]
    W = np.zeros((len(rows), len(bones)))
    for r, (_, gs) in enumerate(rows):
        for n, w in gs:
            if n in index:
                W[r, index[n]] += w
    W2 = hp.split(W, np.array(pts), index, heads, front=(0.0, -1.0, 0.0))
    if skin is not None and body is not None:
        # Split where the skin lies is not enough: the split reads the
        # piece's own blend between the bones above and below a joint, and a
        # sleeve weighted 60/40 over skin weighted 80/20 still took another
        # share (judge 6: the mismatch's p95 stayed at 0.09, and skin came
        # through behind the knee and at the elbow). So near her, the limb's
        # weight is shared out as the skin's under it is: the piece keeps how
        # much it rides the limb, the skin says on which of its bones.
        W2 = _as_skin(W2, near, t, body, index, src)
    groups = {g.name: g for g in obj.vertex_groups}
    for n in bones:
        if n not in groups and W2[:, index[n]].any():
            groups[n] = obj.vertex_groups.new(name=n)
    bone_set = set(bones)
    for r, (vi, gs) in enumerate(rows):
        for n, _ in gs:
            if n in bone_set:
                groups[n].remove([vi])
        for j in np.nonzero(W2[r] > 1e-4)[0]:
            groups[bones[j]].add([vi], float(W2[r, j]), "REPLACE")
    return len(rows)


# Each side's limb shared out as the skin's on that side only (_as_skin).
AS_SKIN_SIDES = os.environ.get("AS_SKIN_SIDES", "1") == "1"

# A piece within this of her skin is split as the skin under it; out to twice
# this it eases to its own place.
SKIN_NEAR = 0.03


def skin_sampler(arm, body):
    """Her skin's weights (helpers included) by point: (BVH of her triangles,
    their corners [T, 3], corner points, weights [V, J] by the armature's bone
    order). A body not yet split is split here, in memory, as split_mesh
    would split it."""
    from mathutils.bvhtree import BVHTree
    bones = [b.name for b in arm.data.bones]
    index = {n: i for i, n in enumerate(bones)}
    me = body.data
    me.calc_loop_triangles()
    mw = body.matrix_world
    P = np.array([(mw @ v.co)[:] for v in me.vertices])
    T = np.array([lt.vertices[:] for lt in me.loop_triangles])
    gname = {g.index: g.name for g in body.vertex_groups}
    W = np.zeros((len(P), len(bones)))
    for v in me.vertices:
        for g in v.groups:
            n = gname.get(g.group)
            if n in index:
                W[v.index, index[n]] += g.weight
    if not any(n in gname.values() for n in hp.names()):
        heads = {b.name: np.array((arm.matrix_world @ b.head_local)[:]) for b in arm.data.bones}
        W = hp.split(W, P, index, heads, front=FRONT)
    return BVHTree.FromPolygons([tuple(p) for p in P], T.tolist()), T, P, W


def _as_skin(W2, near, t, body, index, src):
    """W2's weight on the limb's bones (those the helpers help, and the
    helpers) shared out as her skin's at `near`, eased back to W2's own as t
    goes 0 to 1."""
    bvh, T, P, W = body
    # (the hands too: at the wrist a cuff weighted more to the hand than the
    # skin under it took a different twist share; judge 8, the worst points)
    chain = sorted({index[n] for n in set(src) | set(hp.names()) | {"hand_l", "hand_r"} if n in index})
    tri = np.zeros(len(near), int)
    q = np.zeros((len(near), 3))
    for i, p in enumerate(near):
        hit = bvh.find_nearest(Vector(p))
        q[i], tri[i] = hit[0][:], hit[2]
    a, b, c = P[T[tri, 0]], P[T[tri, 1]], P[T[tri, 2]]
    # Barycentric weights of q in its triangle.
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18)
    bv = np.clip((d11 * d20 - d01 * d21) / den, 0, 1)
    bw = np.clip((d00 * d21 - d01 * d20) / den, 0, 1)
    bu = np.clip(1 - bv - bw, 0, 1)
    s = bu + bv + bw
    Ws = (W[T[tri, 0]][:, chain] * (bu / s)[:, None] + W[T[tri, 1]][:, chain] * (bv / s)[:, None]
          + W[T[tri, 2]][:, chain] * (bw / s)[:, None])
    ssum, gsum = Ws.sum(1), W2[:, chain].sum(1)
    ok = (ssum > 1e-6) & (gsum > 1e-6) & (t < 1.0)
    out = W2.copy()
    target = Ws[ok] * (gsum[ok] / ssum[ok])[:, None]
    if AS_SKIN_SIDES:
        # (each side's limb shared out on its own: the piece keeps how much
        # it rides her left limb and her right, the skin under it says only
        # on which of that side's bones. Shared out as a whole, a stocking
        # band's inner edge, nearest the other thigh where her thighs meet,
        # took that thigh's bones (up to 0.98) and stretched across the gap
        # between her legs in every clip: the owner, 13 Oct)
        names_ = {i: n for n, i in index.items()}
        # (only where the skin is the wrong leg's: at her crotch the skin
        # under a thong or a gusset is both legs', and the piece must take
        # its very blend there or it parts from her and the strip shows,
        # fin3: 11 / 6 / 4 frames. So per side only where the skin's share
        # of the piece's own leg is under 30%, fully under 10%)
        cl_ = np.array([names_[c].endswith("_l") for c in chain])
        cr_ = np.array([names_[c].endswith("_r") for c in chain])
        pl_, pr_ = W2[ok][:, np.array(chain)[cl_]].sum(1), W2[ok][:, np.array(chain)[cr_]].sum(1)
        sl_, sr_ = Ws[ok][:, cl_].sum(1), Ws[ok][:, cr_].sum(1)
        own_ = np.where(pl_ >= pr_, sl_, sr_) / np.maximum(sl_ + sr_, 1e-12)
        kx_ = np.clip((0.3 - own_) / 0.2, 0.0, 1.0)
        kx_ = (kx_ * kx_ * (3 - 2 * kx_))[:, None]
        whole_ = target
        target = np.zeros((int(ok.sum()), len(chain)))
        for suf in ("_l", "_r"):
            cs = np.array([names_[c].endswith(suf) for c in chain])
            g_ = W2[ok][:, np.array(chain)[cs]].sum(1)
            s_ = Ws[ok][:, cs].sum(1)
            has = s_ > 1e-6
            blk = np.where(has[:, None], Ws[ok][:, cs] * (g_ / np.maximum(s_, 1e-12))[:, None], W2[ok][:, np.array(chain)[cs]])
            target[:, cs] = blk
        rest_ = ~np.array([names_[c].endswith(("_l", "_r")) for c in chain])
        if rest_.any():
            target[:, rest_] = W2[ok][:, np.array(chain)[rest_]]
        target = (1 - kx_) * whole_ + kx_ * target
    tt = t[ok][:, None]
    out[np.ix_(ok.nonzero()[0], chain)] = tt * W2[ok][:, chain] + (1 - tt) * target
    return out


# ----------------------------------------------------------- correctives --
# Her corrective shapes (helpers.corrective, SPEC "correctives") as shape
# keys: made on her body from its split weights, and carried to each piece
# she wears from the skin under it. Kept by body name between apply's two
# calls (her body first, her pieces after).
_CORR = {}


def _to_game(v):
    """Blender's world (Z up, front -Y) to the game's (Y up, front +Z), as the
    glTF export turns it."""
    v = np.asarray(v, float)
    return np.stack([v[..., 0], v[..., 2], -v[..., 1]], -1)


def _to_blender(v):
    v = np.asarray(v, float)
    return np.stack([v[..., 0], -v[..., 2], v[..., 1]], -1)


def _game_skeleton(arm):
    """The game's skeleton for this armature (tools/anim/data, dumped from the
    last import), if it holds every bone and lies where the armature's do
    (within 2 mm): the corrective shapes are made in its space."""
    from rig import Skeleton
    names = {b.name for b in arm.data.bones}
    for f in ("heroine_skeleton.json", "hero_skeleton.json"):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "anim", "data", f)
        if not os.path.exists(path):
            continue
        sk = Skeleton.load(path)
        if set(sk.names) != names and not names <= set(sk.names):
            continue
        # A dump holding MORE bones than the armature (the 100-bone game dump vs a 90-bone export)
        # is kept whole (its parents and rest turns need the extra bones); only the armature's
        # bones are position-checked and re-seated, and the extras get zero weight in the callers.
        _, gpos = sk.rest_globals()
        have = [j for j, n in enumerate(sk.names) if n in names]
        heads = np.zeros_like(gpos[0])
        heads[have] = _to_game([(arm.matrix_world @ arm.data.bones[sk.names[j]].head_local)[:] for j in have])
        gpos = gpos.copy()
        gpos[0][[j for j in range(len(sk.names)) if j not in set(have)]] = 0
        err = np.abs(gpos[0] - heads).max()
        if err < 0.002:
            return sk
        # Her joints moved by translation only (the DIPs toward her knuckles, FINGER_FIX; the
        # dump made after the neck cut, whose Head rest is 30 mm short of this armature's, since
        # the cut is a glb post-step): the dump's rest turns still hold, so its rest positions are
        # re-seated on this armature's heads. Before this, a joint 2 mm off dropped every
        # corrective (elbow_point_l/r) from her body and pieces without a word in the summary.
        dev = np.abs(gpos[0] - heads).max(1)
        if err < 0.05:
            grot, _ = sk.rest_globals()
            from rig import qinv, qrot
            pos = sk.rest_pos.copy()
            hs = set(have)
            for j, p in enumerate(sk.parent):
                if j not in hs:
                    continue
                if p < 0:
                    pos[j] = heads[j]
                elif p in hs:
                    pos[j] = qrot(qinv(grot[0, p]), heads[j] - heads[p])
            sk.rest_pos = pos
            moved = [sk.names[j] for j in np.where(dev >= 0.002)[0]]
            print(f"RIG correctives: {f} was {err * 1000:.1f} mm off this armature; rest re-seated on its heads "
                  f"({len(moved)} joints: {', '.join(moved[:12])}{' ...' if len(moved) > 12 else ''})")
            return sk
        print(f"RIG correctives: {f} is {err * 1000:.1f} mm off this armature")
    return None


def _weights(obj, names):
    """[V, J] weights by `names`, as the glTF export keeps them: the four
    largest, made to sum to one."""
    index = {n: i for i, n in enumerate(names)}
    gname = {g.index: g.name for g in obj.vertex_groups}
    W = np.zeros((len(obj.data.vertices), len(names)))
    for v in obj.data.vertices:
        for g in v.groups:
            n = gname.get(g.group)
            if n in index:
                W[v.index, index[n]] += g.weight
    top = np.argsort(-W, axis=1)[:, :4]
    keep = np.zeros_like(W)
    rows = np.arange(len(W))[:, None]
    keep[rows, top] = W[rows, top]
    return keep / np.maximum(keep.sum(1, keepdims=True), 1e-12)


def _shape_keys(obj, moves):
    """`moves` {name: [V, 3] world moves} as shape keys on obj (a basis first)."""
    if not moves:
        return
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    inv = np.array(obj.matrix_world.inverted().to_3x3())
    base = np.array([v.co[:] for v in obj.data.vertices])
    for name, mv in moves.items():
        kb = obj.data.shape_keys.key_blocks.get(name) or obj.shape_key_add(name=name, from_mix=False)
        kb.data.foreach_set("co", (base + mv @ inv.T).astype(np.float32).ravel())
        kb.value = 0.0


def _body_moves(arm, body):
    """Her corrective shapes as world moves of her body's points, from its
    split weights, or {} (none in the spec, no game skeleton for this
    armature, or a body not split)."""
    if not hp.SPEC.get("correctives"):
        return {}
    if not any(g.name in hp.names() for g in body.vertex_groups):
        return {}
    sk = _game_skeleton(arm)
    if sk is None:
        print("RIG correctives: no game skeleton matches this armature; none made")
        return {}
    mw = body.matrix_world
    P = _to_game([(mw @ v.co)[:] for v in body.data.vertices])
    W = _weights(body, sk.names)
    moves = {k: _to_blender(d) for k, d in hp.corrective(P, W, sk, front=(0.0, 0.0, 1.0)).items()}
    return {k: _relaxed(body.data, d) for k, d in moves.items() if np.abs(d).max() > 0}


def _relaxed(me, d, passes=3):
    """A shape's moves eased over her mesh (each point halfway to the mean
    of the points round it, `passes` times; her seams welded), then scaled
    back to its peak: the falloff's rim follows her own edges, not a cut
    across them (at 145 degrees a step in the patch's forearm-side rim read
    as a nub on the elbow's flank: animation, judge 10)."""
    co = np.array([v.co[:] for v in me.vertices])
    _, w = np.unique(np.round(co / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    w = w.ravel()
    ev = np.array([e.vertices[:] for e in me.edges])
    a, b = w[ev[:, 0]], w[ev[:, 1]]
    k = a != b
    a, b = a[k], b[k]
    n = w.max() + 1
    D = np.zeros((n, 3))
    np.add.at(D, w, d)
    D /= np.bincount(w, minlength=n)[:, None]
    deg = np.bincount(np.r_[a, b], minlength=n).astype(float)
    peak = np.linalg.norm(D, axis=1).max()
    for _ in range(passes):
        S = np.zeros_like(D)
        np.add.at(S, a, D[b])
        np.add.at(S, b, D[a])
        D = np.where(deg[:, None] > 0, 0.5 * D + 0.5 * S / np.maximum(deg, 1)[:, None], D)
    D *= peak / max(np.linalg.norm(D, axis=1).max(), 1e-12)
    return D[w]


def _sampler_moves(arm, sampler):
    """As _body_moves, from skin_sampler's points and split weights."""
    if not hp.SPEC.get("correctives"):
        return {}
    sk = _game_skeleton(arm)
    if sk is None:
        return {}
    _, _, Pb, Wb = sampler
    order = [b.name for b in arm.data.bones]
    W = np.stack([Wb[:, order.index(n)] if n in order else np.zeros(len(Wb)) for n in sk.names], 1)
    top = np.argsort(-W, axis=1)[:, :4]
    keep = np.zeros_like(W)
    rows = np.arange(len(W))[:, None]
    keep[rows, top] = W[rows, top]
    W = keep / np.maximum(keep.sum(1, keepdims=True), 1e-12)
    moves = {k: _to_blender(d) for k, d in hp.corrective(_to_game(Pb), W, sk, front=(0.0, 0.0, 1.0)).items()}
    return {k: d for k, d in moves.items() if np.abs(d).max() > 0}


def body_correctives(arm, body):
    """Her corrective shapes set as shape keys on her body (once split) and
    kept for her pieces."""
    moves = _body_moves(arm, body)
    _shape_keys(body, moves)
    _CORR[body.name] = moves
    for k, d in moves.items():
        n = np.linalg.norm(d, axis=1)
        print(f"RIG corrective {k}: {int((n > 1e-5).sum())} points, deepest {n.max() * 1000:.1f} mm")
    return moves


def piece_correctives(obj, body, sampler):
    """A piece's corrective shapes: the move of the skin under each point
    (barycentric on her nearest triangle), whole within garment[0] of her
    skin, easing out to none at garment[1]."""
    moves = _CORR.get(body.name)
    if not moves:
        return 0
    bvh, T, Pb, _ = sampler
    mw = obj.matrix_world
    P = np.array([(mw @ v.co)[:] for v in obj.data.vertices])
    out = {}
    for c in hp.SPEC.get("correctives", []):
        near, far = c.get("garment", (0.02, 0.04))
        for name in hp.each(c["name"]):
            mv = moves.get(name)
            if mv is None:
                continue
            # only points near the skin that moves
            moving = np.linalg.norm(mv, axis=1) > 1e-6
            lo, hi = Pb[moving].min(0) - far, Pb[moving].max(0) + far
            cand = np.nonzero(((P > lo) & (P < hi)).all(1))[0]
            if not len(cand):
                continue
            d = np.zeros((len(P), 3))
            for i in cand:
                q, _, ti, dist = bvh.find_nearest(Vector(P[i]))
                if q is None or dist >= far:
                    continue
                a, b_, c_ = (Pb[T[ti, k]] for k in range(3))
                v0, v1, v2 = b_ - a, c_ - a, np.array(q[:]) - a
                d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
                d20, d21 = v2 @ v0, v2 @ v1
                den = max(d00 * d11 - d01 * d01, 1e-18)
                bv = min(max((d11 * d20 - d01 * d21) / den, 0.0), 1.0)
                bw = min(max((d00 * d21 - d01 * d20) / den, 0.0), 1.0)
                bu = max(1.0 - bv - bw, 0.0)
                s = bu + bv + bw
                m = (mv[T[ti, 0]] * bu + mv[T[ti, 1]] * bv + mv[T[ti, 2]] * bw) / s
                t = min(max((dist - near) / (far - near), 0.0), 1.0)
                d[i] = m * (1.0 - t * t * (3 - 2 * t))
            if np.abs(d).max() > 1e-6:
                out[name] = d
    _shape_keys(obj, out)
    return len(out)


def share_keys(objs):
    """Before pieces are joined: every one given the shape keys any of them
    has (a copy of its basis where it has none), so the join keeps them all
    (Blender keeps only the active object's keys, matched by name)."""
    names = []
    for o in objs:
        if o.type == "MESH" and o.data.shape_keys:
            names += [k.name for k in o.data.shape_keys.key_blocks[1:] if k.name not in names]
    if not names:
        return
    for o in objs:
        if o.type != "MESH":
            continue
        if o.data.shape_keys is None:
            o.shape_key_add(name="Basis", from_mix=False)
        for n in names:
            if n not in o.data.shape_keys.key_blocks:
                o.shape_key_add(name=n, from_mix=False)


def apply(arm, meshes, skin=None, body=None, chain=False):
    # On: judged at 1:1 in motion (animation judges 9-11) and shipped in her
    # body and outfits since 11 October, so a build without them would
    # quietly drop them. --no-helpers after the build's "--" leaves them out
    # (for a before/after).
    if "--no-helpers" in sys.argv:
        print("RIG helpers: off (--no-helpers)")
        return
    made = add_bones(arm, chain)
    # (her skin's split, read once, for the pieces she wears to share as it)
    sampler = skin_sampler(arm, body) if (skin is not None and body is not None) else None
    total = 0
    for o in meshes:
        if o.type == "MESH":
            total += split_mesh(arm, o, skin, sampler)
    print(f"RIG helpers: {made} bones added; {total} points split onto them")
    # Her corrective shapes: on her body once split (called with her body
    # alone), then on the pieces she wears, from the skin under them.
    if sampler is None:
        for o in meshes:
            if o.type == "MESH" and o.name not in _CORR:
                body_correctives(arm, o)
    else:
        if body.name not in _CORR:
            # (her body exported in another run: its moves made again here,
            # from the sampler's split of her)
            _CORR[body.name] = _sampler_moves(arm, sampler)
        keyed = sum(1 for o in meshes if o.type == "MESH" and piece_correctives(o, body, sampler))
        print(f"RIG correctives: {keyed} pieces keyed")
