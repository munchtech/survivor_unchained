"""Her skin's tuck and each piece's cover, per body, computed natively on the body the gear was built for (P2 gear).

`tools/armor/gear_fit.py build --body <dir>` calls `write_all` after it writes the pieces: for every built row it reads the
row's close-tier meshes back from <out>/<id>.gltf (the pieces as they sit on THIS body) and writes, beside the index,

    armor_tuck/<id>.bin    her skin's tuck under the piece
    armor_cover/<id>.bin   the piece's cover of her (the garment tuck's footprint, HerWear.Footprint)

in the tuck format (u32 count, then per record i32 x, y, z = the body's bind point x 1e5 rounded half to even, f32 value:
tools/armor/cover.py, HerWear.Key), and sets the row's "tuck" / "tuck_count" / "cover_count".

Keys: the body's "Heroine" mesh points (body.glb: the close tier) and, for the tuck only, also play.glb's "Heroine" points
(HerWear.TuckMap lays one map over both tiers' bodies: the play body reads its part at tuck_offset). HeroineHead is not keyed:
the game never tucks it (People.TuckBody leaves out *Head), and no built row reaches it (`control` reports it).

The tuck: tools/assets/heroine_outfits.py's general rule (tuck_of + tuck_bound, "THE BOUNDED TUCK"): each point's outward
normal ray, from 0.5 mm out, to the piece's faces within REACH (12 mm); a grazing hit (|cos| < GRAZE) is the rim seen from
outside and counts for nothing; a face-on hit marks the point under the piece and tucks it as deep as the piece lies close
(0.8 x clip((4.5 mm - gap) / 4 mm)); then, over her welded surface graph, the need smoothed within the footprint (SMOOTH_IT
rounds), raised to the envelope climbing no faster than SLOPE per metre and STEP between neighbours, capped by the same
climb in from the footprint's border. A's piece-specific rules are not carried: the nipple disc and bump (B has none), the
ranger's and warden's foot not drawn inside the boot, the arcanist's hand not drawn inside the glove and her forearm under
it tucked all the way, its glove-top and glove-edge eases, a hat's hair (the boot's deep tuck is dead code in A: no part
carries deep_zt). All of those answer clipping in MOTION (a bent ankle, a closed fist); at rest the general rule covers what
lies under each piece. In their place three general rules (P2 gear s7): skin through a piece at rest is tucked
full and held; skin under a rigid plate within RIGID_FULL is tucked full (A reached that by measuring its clips); and THE
PIECE ENCLOSES HER: in the slots that wrap a limb (ENCLOSE_SLOTS), her skin the piece encloses (every ray over her outward
hemisphere meets it, ENCLOSE_LEAK allowed out) and GONE_IN or more from any of her it does not is not drawn (1.0): a foot
in a boot, a hand in a glove, whatever the pose does inside. One row property is A's design and carried: a row whose A tuck is empty (its parts do not hide her
skin: a sheer stocking, belts, skirts, a collar) tucks nothing (a_hides). `control` compares native with A's records carried, row by row.

The cover: tools/armor/cover.py's rule (cover_of: reach 45 mm, ramp 0, deep 25 mm; a row's cover_grow) on this body.

    python tools/armor/gear_tuck.py write --body godot/art/people/body_p1 [--only id,id]   (re-writes the records alone)
    python tools/armor/gear_tuck.py control [--only id,id]   native vs A's records carried onto the gate body (B)
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "body"))
sys.path.insert(0, os.path.join(REPO, "tools", "anim"))

import cover as cv  # noqa: E402

REACH = 0.012
LIFT = 0.0005
GRAZE = 0.5
SLOPE = 30.0
SMOOTH_IT = 4
STEP = 0.15
COVER_REACH, COVER_RAMP, COVER_DEEP = 0.045, 0.0, 0.025
BOX = 0.05
FULL = 0.98            # a full tuck's mark (heroine_skin.gdshader reads 0.973 and over as all of its 10 mm)
GONE = 1.0             # her skin not drawn (the shader discards 0.995 and over)
BACK = 0.015           # through at rest: the piece's outer face met this far back along her inward normal
RIGID_FULL, RIGID_ZERO = 0.006, 0.010   # under a rigid plate: full this close, eased to none here
ENCLOSE_DIRS = 160     # rays over the sphere for the enclosure test (those within her outward hemisphere are cast)
ENCLOSE_RAY = 0.25     # a ray that runs this far clear of the piece leaves it: her point can be seen from outside
ENCLOSE_LEAK = 0.03    # share of her hemisphere's rays allowed out (grazing gaps between a piece's own parts: a sabaton's lames)
GONE_IN = 0.015        # her enclosed skin not drawn only this far (along her surface) from any of her that is not
RIGID_REACH = 0.04      # THE PLATE HIDES HER: her points whose outward ray meets a rigid face this far out (or that stand
#   through one at rest) are under it; those of them no game camera sees as she moves (gear_seal.py hide) are not drawn
ENCLOSE_SLOTS = ("boots", "gloves", "greaves", "bracers", "head")   # slots whose pieces wrap a limb (a top's arm holes
#   and neck open and close as she moves: its skin keeps the tuck)


# ---------------------------------------------------------------- the body

class Skin:
    """A body tier's Heroine points (bind space, as Godot's mesh holds them), normals, triangles, welded graph."""

    def __init__(self, glb_path):
        from gl import Glb
        m = Glb(glb_path).mesh("Heroine")
        self.P = m.P.astype(np.float64)
        self.T = m.T.astype(np.int64)
        N = m.N.astype(np.float64)
        self.N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        _, gid = np.unique(np.round(self.P / 1e-6).astype(np.int64), axis=0, return_inverse=True)
        self.gid = np.asarray(gid).ravel()
        self.ng = int(self.gid.max()) + 1
        cg = np.zeros((self.ng, 3))
        cg[self.gid] = self.P
        e = self.gid[np.vstack([self.T[:, [0, 1]], self.T[:, [1, 2]], self.T[:, [2, 0]]])]
        e = np.unique(np.sort(e[e[:, 0] != e[:, 1]], 1), axis=0)
        self.a, self.b = np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]]
        self.l = np.linalg.norm(cg[self.a] - cg[self.b], axis=1)
        self.kd = cKDTree(self.P)


def tuck_bound(sk, t, hard=None, under=None, step=None):
    """heroine_outfits.tuck_bound on this body's welded graph (per vertex in, per vertex out); `step` the most the tuck
    may rise over one edge in from the edge of the skin it covers (STEP, or a rigid slot's stand-off law)."""
    gid, ng, a_, b_, l_ = sk.gid, sk.ng, sk.a, sk.b, sk.l
    need = np.zeros(ng)
    np.maximum.at(need, gid, t)
    hd = np.zeros(ng, bool)
    if hard is not None:
        np.logical_or.at(hd, gid, hard & (t > 0))
    U = need > 0
    if under is not None:
        np.logical_or.at(U, gid, under)
    if not U.any():
        return t
    inn = U[a_] & U[b_]
    lw_ = np.minimum(SLOPE * l_, STEP if step is None else step)
    ai, bi, li = a_[inn], b_[inn], lw_[inn]
    s = need.copy()
    deg = np.bincount(bi, minlength=ng).astype(float)
    for _ in range(SMOOTH_IT):
        acc = np.bincount(bi, weights=s[ai], minlength=ng)
        s = np.where(U, (s + acc) / (1.0 + deg), 0.0)
    s[hd] = np.maximum(s[hd], need[hd])
    E = s.copy()
    for _ in range(400):
        c_ = np.full(ng, -1.0)
        np.maximum.at(c_, bi, E[ai] - li)
        En = np.maximum(E, c_)
        if np.abs(En - E).max() < 1e-7:
            break
        E = En
    bd = np.unique(a_[~U[a_] & U[b_]])
    sub = U.copy()
    sub[bd] = True
    keep = sub[a_] & sub[b_]
    gr = sparse.csr_matrix((lw_[keep], (a_[keep], b_[keep])), shape=(ng, ng))
    d_ = dijkstra(gr, directed=True, indices=bd, min_only=True, limit=1.01) if len(bd) else np.full(ng, np.inf)
    F = np.where(U, np.minimum(E, d_), 0.0)
    F[hd] = np.maximum(F[hd], need[hd])
    return np.clip(F, 0.0, 1.0)[gid]


def rigid_tuck_law(slot):
    """(full m, zero m, step) of the UNDER A RIGID PLATE rule for a slot: RIGID_FULL, RIGID_ZERO, STEP, or the slot's
    stand-off law (tools/armor/rigid_roles.json slots "standoff": "tuck_full_mm", "tuck_zero_mm", "tuck_step"): a plate
    made to stand off her where she moves keeps its full tuck that much further out."""
    import gear_fit
    law = gear_fit.standoff_law(slot) or {}
    return (law.get("tuck_full_mm", RIGID_FULL * 1000) / 1000.0, law.get("tuck_zero_mm", RIGID_ZERO * 1000) / 1000.0,
            law.get("tuck_step", STEP))


def tuck_of(sk, PB, TB, rigid=None, slot=None):
    """Her skin's tuck under one piece (PB points, TB triangles, `rigid` a flag per triangle: a plate that never bends),
    per vertex of sk; how many rays grazed it; and how many points the two rules for plates raised.

    The general rule (A's bounded tuck) tucks her as deep as the piece lies close. Two rules more, for any piece:
    - THROUGH AT REST: her skin already past the piece (its outer face met within BACK behind her along her inward
      normal, and nothing of it in front within REACH): a full tuck, held (A's "proud" rule, her skin standing out of
      the form a plate was made on, without the form).
    - UNDER A RIGID PLATE: a plate never bends, so as she moves her skin slides under it by more than a bending piece's
      clearance tracks: within RIGID_FULL a full tuck, eased to the general rule's at RIGID_ZERO. (A reached a full tuck
      under its pauldrons and cuirass by measuring its clips: tools/armor/pose_tuck.py; this is that, as a rule.)"""
    import trimesh
    t = np.zeros(len(sk.P))
    if not len(TB):
        return t, 0, 0
    lo, hi = PB.min(0) - BOX, PB.max(0) + BOX
    cand = np.nonzero(((sk.P >= lo) & (sk.P <= hi)).all(1))[0]
    if not len(cand):
        return t, 0, 0
    mesh = trimesh.Trimesh(PB, TB, process=False)
    ray = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
    O = sk.P[cand] + sk.N[cand] * LIFT
    tri, ri, loc = ray.intersects_id(O, sk.N[cand], multiple_hits=False, return_locations=True)
    d = np.linalg.norm(loc - O[ri], axis=1)
    fn = mesh.face_normals[tri]
    cos = np.abs((fn * sk.N[cand[ri]]).sum(1))
    near = d <= REACH
    face_on = near & (cos >= GRAZE)
    grazed = int((near & ~face_on).sum())
    v = cand[ri[face_on]]
    under = np.zeros(len(sk.P), bool)
    under[v] = True
    t[v] = 0.8 * np.clip((0.005 - d[face_on] - LIFT) / 0.004, 0, 1)
    raised = 0
    if rigid is not None and rigid.any():
        rg = rigid[tri[face_on]]
        rf, rz, _ = rigid_tuck_law(slot)
        tr = FULL * np.clip((rz - (d[face_on] + LIFT)) / (rz - rf), 0, 1)
        up = rg & (tr > t[v])
        t[v[up]] = tr[up]
        raised += int(up.sum())
    # (through at rest: her inward ray meets a face that looks back at it, i.e. the piece's outside, close behind her)
    infront = np.zeros(len(sk.P), bool)
    infront[cand[ri[near]]] = True
    tb, rb, lb = ray.intersects_id(sk.P[cand] + sk.N[cand] * LIFT, -sk.N[cand], multiple_hits=False, return_locations=True)
    db = np.linalg.norm(lb - (sk.P[cand[rb]] + sk.N[cand[rb]] * LIFT), axis=1)
    outer = (mesh.face_normals[tb] * sk.N[cand[rb]]).sum(1) > 0
    thr = cand[rb[(db <= BACK + LIFT) & outer]]
    thr = thr[~infront[thr]]
    hard = np.zeros(len(sk.P), bool)
    hard[thr] = True
    raised += int((t[thr] < FULL).sum())
    t[thr] = FULL
    under[thr] = True
    step = rigid_tuck_law(slot)[2] if rigid is not None and rigid.any() else None
    return tuck_bound(sk, t, hard, under | (t > 0), step), grazed, raised


def fib_dirs(n):
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    r = np.sqrt(1 - z * z)
    a = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[r * np.cos(a), r * np.sin(a), z]


def enclosed_of(sk, PB, TB, foot):
    """Her points the piece encloses: every ray from her point over her outward hemisphere (ENCLOSE_DIRS over the
    sphere, those at or above her tangent plane) meets the piece within ENCLOSE_RAY (a foot in a boot, a hand in a
    glove). Only her points in `foot` (those within the piece's box: the footprint's rays miss toes floating in a boot's
    toe box) are tried. Per vertex of sk: bool."""
    import trimesh
    out = np.zeros(len(sk.P), bool)
    cand = np.nonzero(foot)[0]
    if not len(cand) or not len(TB):
        return out
    ray = trimesh.ray.ray_pyembree.RayMeshIntersector(trimesh.Trimesh(PB, TB, process=False))
    Dd = fib_dirs(ENCLOSE_DIRS)
    for a in range(0, len(cand), 2000):
        ii = cand[a:a + 2000]
        up = (sk.N[ii] @ Dd.T) >= 0.0
        pi, di = np.nonzero(up)
        O = sk.P[ii][pi] + sk.N[ii][pi] * LIFT
        hit = np.zeros(len(pi), bool)
        _, ri, loc = ray.intersects_id(O, Dd[di], multiple_hits=False, return_locations=True)
        hit[ri] = np.linalg.norm(loc - O[ri], axis=1) <= ENCLOSE_RAY
        n_up = np.bincount(pi, minlength=len(ii))
        n_out = np.bincount(pi[~hit], minlength=len(ii))
        out[ii] = n_out <= ENCLOSE_LEAK * n_up
    return out


def under_rigid_of(sk, PB, TB, rigid):
    """Her points under the piece's rigid parts: the ray from BACK inside her, along her outward normal, first meets a
    rigid face within BACK + RIGID_REACH (a plate over her, or one she stands through at rest). Per vertex: bool."""
    import trimesh
    out = np.zeros(len(sk.P), bool)
    if not len(TB) or rigid is None or not rigid.any():
        return out
    lo, hi = PB.min(0) - BOX, PB.max(0) + BOX
    cand = np.nonzero(((sk.P >= lo) & (sk.P <= hi)).all(1))[0]
    if not len(cand):
        return out
    ray = trimesh.ray.ray_pyembree.RayMeshIntersector(trimesh.Trimesh(PB, TB, process=False))
    O = sk.P[cand] - sk.N[cand] * BACK
    tri, ri, loc = ray.intersects_id(O, sk.N[cand], multiple_hits=False, return_locations=True)
    ok = (np.linalg.norm(loc - O[ri], axis=1) <= BACK + RIGID_REACH) & rigid[tri]
    out[cand[ri[ok]]] = True
    return out


def hidden_of(out_dir, rid, sk, PB):
    """THE PLATE HIDES HER: gear_seal.py hide's set for the row (her points under its rigid parts that no game camera
    sees at rest or in any frame of her clips), while the piece is the one it was measured on. Per vertex: bool, or
    None (no set, or a stale one: said)."""
    base = os.path.join(out_dir, "armor_hidden", rid)
    if not os.path.exists(base + ".bin") or not os.path.exists(base + ".json"):
        return None
    st = json.load(open(base + ".json"))
    h = hashlib.sha1(np.round(np.asarray(PB, np.float64) * 1e5).astype(np.int64).tobytes()).hexdigest()
    if st.get("piece_hash") != h:
        print(f"gear tuck: {rid}: armor_hidden is stale (the piece changed): re-run gear_seal.py hide; no plate gone")
        return None
    k, v = read_records(base + ".bin")
    keys = {tuple(x) for x in k[v > 0]}
    return np.array([tuple(x) in keys for x in np.round(sk.P * 1e5).astype(np.int64)])


def gone_of(sk, inside, fill=True):
    """THE PIECE ENCLOSES HER: her points inside (enclosed by it), welded, holes in that set that
    touch none of her outside it filled, and only those GONE_IN or more along her surface from any of her not inside it
    (so no point that can be seen at its opening, nor one that comes into view there as she moves, is cut).
    Per vertex: bool."""
    gid, ng, a_, b_, l_ = sk.gid, sk.ng, sk.a, sk.b, sk.l
    ins = np.zeros(ng, bool)
    np.logical_or.at(ins, gid, inside)
    if not ins.any():
        return np.zeros(len(sk.P), bool)
    # (holes: her points not inside, in components that touch nothing but inside points and are small: a few of her
    # points the rays read as seen through a seam of the piece, ringed by enclosed skin)
    from scipy.sparse.csgraph import connected_components
    # (fill=False, a plate's hidden set: her skin seen through a gap between lames is seen; no hole is filled)
    if fill:
        o = ~ins
        keep = o[a_] & o[b_]
        g = sparse.csr_matrix((np.ones(int(keep.sum())), (a_[keep], b_[keep])), shape=(ng, ng))
        nc, lab = connected_components(g, directed=False)
        size = np.bincount(lab[o], minlength=nc)
        big = size.max() if len(size) else 0
        hole = o & (size[lab] < 0.01 * big)
        ins = ins | hole
    o = ~ins
    bd = np.unique(a_[o[a_] & ins[b_]])
    if not len(bd):
        return ins[gid]
    gr = sparse.csr_matrix((l_, (a_, b_)), shape=(ng, ng))
    dd = dijkstra(gr, directed=False, indices=bd, min_only=True, limit=GONE_IN * 1.01)
    return (ins & (dd >= GONE_IN))[gid]


def cover_of(sk, PB, TB, row):
    c = cv.cover_of(sk.P, sk.N, sk.kd, PB, TB, COVER_REACH, COVER_RAMP, COVER_DEEP)
    if row.get("cover_grow"):
        c = cv.grown(sk.P, sk.T, c, *[float(x) for x in row["cover_grow"]])
    return c


# ---------------------------------------------------------------- records

def write_records(path, P, v):
    """Records of v > 0 at P's keys (several points at one key: the largest); the count."""
    q = np.round(P.astype(np.float64) * 1e5).astype(np.int64)
    k = np.nonzero(v > 0)[0]
    uq, inv = np.unique(q[k], axis=0, return_inverse=True)
    g = np.zeros(len(uq))
    np.maximum.at(g, np.asarray(inv).ravel(), v[k])
    rec = np.zeros(len(uq), dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    rec["x"], rec["y"], rec["z"], rec["t"] = uq[:, 0], uq[:, 1], uq[:, 2], g
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<I", len(uq)) + rec.tobytes())
    return len(uq)


def read_records(path):
    if not os.path.exists(path):
        return np.zeros((0, 3), np.int64), np.zeros(0)
    d = open(path, "rb").read()
    n = struct.unpack_from("<I", d, 0)[0]
    rec = np.frombuffer(d, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
    return np.c_[rec["x"], rec["y"], rec["z"]].astype(np.int64), rec["t"].astype(np.float64)


def piece_of(out_dir, row, flags=False):
    """A built row's close-tier meshes on this body: points and triangles (its lod1 / shadow meshes left out); with
    `flags`, also a rigid flag per triangle (gear_fit's rule: a rigid row's metal meshes)."""
    from gl import Glb
    import gear_fit as gf
    g = Glb(os.path.join(out_dir, f"{row['id']}.gltf"))
    rigid_row = bool(row.get("rigid")) or row["id"].startswith(("plate_", "mar_her_"))
    Ps, Ts, Rs, n = [], [], [], 0
    for name in row["meshes"]:
        m = g.mesh(name)
        if m is None:
            continue
        Ps.append(m.P.astype(np.float64))
        Ts.append(m.T + n)
        Rs.append(np.full(len(m.T), gf.is_rigid_mesh(rigid_row, name)))
        n += len(m.P)
    if not Ps:
        z = (np.zeros((0, 3)), np.zeros((0, 3), np.int64))
        return z + (np.zeros(0, bool),) if flags else z
    return (np.vstack(Ps), np.vstack(Ts), np.concatenate(Rs)) if flags else (np.vstack(Ps), np.vstack(Ts))


def write_all(out_dir, close_glb, play_glb, rows, say=print):
    """Every row's tuck (close + play keys) and cover (close keys) on this body; the rows get "tuck", "tuck_count",
    "cover_count". Returns {id: {...numbers}}."""
    t0 = time.time()
    close, play = Skin(close_glb), Skin(play_glb) if play_glb and os.path.exists(play_glb) else None
    hides = a_hides()
    stats = {}
    for r in rows:
        if r.get("lod"):
            continue   # (a calling's play-tier unit: worn with its set, which tucks; its lod_shadow is no piece)
        PB, TB, RB = piece_of(out_dir, r, flags=True)
        c = cover_of(close, PB, TB, r) if r["slot"] != "ink" else np.zeros(len(close.P))
        ng = 0
        if hides.get(r["id"], True):
            tc, gz, rz = tuck_of(close, PB, TB, RB, r["slot"])
            tp = tuck_of(play, PB, TB, RB, r["slot"])[0] if play is not None else np.zeros(0)
            gc = np.zeros(len(close.P), bool)
            if r["slot"] in ENCLOSE_SLOTS:
                box = ((close.P >= PB.min(0) - BOX) & (close.P <= PB.max(0) + BOX)).all(1)
                gc |= gone_of(close, enclosed_of(close, PB, TB, box))
            hid = hidden_of(out_dir, r["id"], close, PB) if RB.any() else None
            if hid is not None:
                gc |= gone_of(close, hid & under_rigid_of(close, PB, TB, RB), fill=False)
            if gc.any():
                tc[gc] = GONE
                ng = int(gc.sum())
                if play is not None:
                    # (the play body's points take the close body's gone where they lie on it)
                    dp, ip = close.kd.query(play.P)
                    gp = gc[ip] & (dp < 0.004) & (tp > 0)
                    tp[gp] = GONE
        else:
            tc, gz, rz = np.zeros(len(close.P)), 0, 0
            tp = np.zeros(len(play.P)) if play is not None else np.zeros(0)
        Pk = np.vstack([close.P, play.P]) if play is not None else close.P
        nt = write_records(os.path.join(out_dir, "armor_tuck", f"{r['id']}.bin"), Pk, np.r_[tc, tp])
        nc = write_records(os.path.join(out_dir, "armor_cover", f"{r['id']}.bin"), close.P, c)
        r["tuck"] = f"armor_tuck/{r['id']}.bin"
        r["tuck_count"] = nt
        r["cover_count"] = nc
        st = {"tuck_close": int(len(np.unique(np.round(close.P[tc > 0] * 1e5), axis=0))), "tuck_all": nt, "cover": nc,
              "full": int((tc >= 0.98).sum()), "gone": int((tc >= 0.995).sum()), "grazed": gz, "raised": rz,
              "max": float(tc.max()) if len(tc) else 0.0}
        stats[r["id"]] = st
        say(f"gear tuck: {r['id']:22} tuck {nt:6d} records ({st['tuck_close']} close), max {st['max']:.2f}, "
            f"{gz} grazing rays, {rz} raised (plate / through), {ng} gone (enclosed); cover {nc:6d}")
    say(f"gear tuck: {len(rows)} rows in {time.time() - t0:.1f} s")
    return stats


def a_hides():
    """{id: whether the piece hides her skin}: A's row tucks something (heroine_outfits.py tucks only under a piece's parts
    marked "hides": a sheer stocking, a belt, a skirt, a collar, the warden's bracers are none, and their A tucks are empty;
    tucked under a sheer stocking her legs would sit 6-8 mm in, seen through it). Rows A does not have: True."""
    out = {}
    for path in (os.path.join(REPO, "godot", "art", "people", "armor_index.json"),
                 os.path.join(REPO, "godot", "art", "armor", "armor_index.json")):
        if os.path.exists(path):
            for r in json.load(open(path, encoding="utf-8")):
                if r.get("tuck_count") is not None:
                    out[r["id"]] = r["tuck_count"] > 0
    return out


# ---------------------------------------------------------------- control: A's records carried onto B

def a_rows():
    out = {}
    for path in (os.path.join(REPO, "godot", "art", "people", "armor_index.json"),
                 os.path.join(REPO, "godot", "art", "armor", "armor_index.json")):
        base = os.path.dirname(path)
        for r in json.load(open(path, encoding="utf-8")):
            out[r["id"]] = (os.path.join(base, r["tuck"]) if r.get("tuck") else None,
                            os.path.join(base, "armor_cover", f"{r['id']}.bin"))
    return out


def control(out_dir, only=None, radius=0.02):
    """Per built row: native (out_dir's records) vs A's records carried to B (record key -> A's Heroine vertices -> posed
    into B's rest by the maps + the field to B's surface (gear_fit.Carrier) -> each B point takes its nearest carried A
    vertex's value within `radius`). Close-tier keys only."""
    import gear_fit as gf
    from gl import Glb
    car = gf.Carrier()
    a = Glb(gf.A_PATH).mesh("Heroine")
    na = len(a.P)
    ka = np.round(a.P.astype(np.float64) * 1e5).astype(np.int64)
    ah = Glb(gf.A_PATH).mesh("HeroineHead")
    kh = {tuple(k) for k in np.round(ah.P.astype(np.float64) * 1e5).astype(np.int64)}
    lookup = {}
    for i, k in enumerate(map(tuple, ka)):
        lookup.setdefault(k, []).append(i)
    Xa = car.APb[:na] + car.e[:na]
    close = Skin(os.path.join(gf.BIND_BODY, "body.glb"))
    dB, iB = cKDTree(Xa).query(close.P)
    near = dB <= radius
    qb = np.round(close.P * 1e5).astype(np.int64)
    _, ub = np.unique(qb, axis=0, return_index=True)
    ix = json.load(open(os.path.join(out_dir, "gear_index.json")))["rows"]
    A = a_rows()
    table = []
    for r in ix:
        if (only and r["id"] not in only) or r.get("lod"):
            continue
        line = {"id": r["id"]}
        for kind, ai in (("tuck", 0), ("cover", 1)):
            apath = A.get(r["id"], (None, None))[ai]
            k, v = read_records(apath) if apath else (np.zeros((0, 3), np.int64), np.zeros(0))
            vA = np.zeros(na)
            head = 0
            for kk, vv in zip(map(tuple, k), v):
                for i in lookup.get(kk, ()):
                    vA[i] = max(vA[i], vv)
                head += kk in kh and kk not in lookup
            car_v = np.where(near, vA[iB], 0.0)[ub]
            kn, vn = read_records(os.path.join(out_dir, f"armor_{kind}", f"{r['id']}.bin"))
            nat = dict(zip(map(tuple, kn), vn))
            nat_v = np.array([nat.get(tuple(x), 0.0) for x in qb[ub]])
            m_n, m_c = nat_v > 0, car_v > 0
            union = m_n | m_c
            line[kind] = {"native": int(m_n.sum()), "carried": int(m_c.sum()), "a_records": int(len(k)), "a_head": head,
                          "only_one": float((m_n ^ m_c).sum() / max(union.sum(), 1)),
                          "mean_abs": float(np.abs(nat_v - car_v)[union].mean()) if union.any() else 0.0,
                          "native_full": int((nat_v >= 0.98).sum()), "carried_full": int((car_v >= 0.98).sum())}
        table.append(line)
        t, c = line["tuck"], line["cover"]
        print(f"{r['id']:22} tuck n {t['native']:5d} c {t['carried']:5d} (A {t['a_records']:5d}, head {t['a_head']}) "
              f"one-only {t['only_one']:.2f} |d| {t['mean_abs']:.3f} full n/c {t['native_full']}/{t['carried_full']}   "
              f"cover n {c['native']:5d} c {c['carried']:5d} one-only {c['only_one']:.2f} |d| {c['mean_abs']:.3f}")
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("write", "control"))
    ap.add_argument("--body", default=os.path.join("godot", "art", "people", "body_p1"))
    ap.add_argument("--out")
    ap.add_argument("--only")
    ap.add_argument("--json")
    a = ap.parse_args()
    body = os.path.join(REPO, a.body) if not os.path.isabs(a.body) else a.body
    out = a.out or os.path.join(REPO, "godot", "art", "gear", "out", os.path.basename(os.path.normpath(body)))
    only = set(a.only.split(",")) if a.only else None
    if a.cmd == "write":
        ip = os.path.join(out, "gear_index.json")
        ix = json.load(open(ip))
        rows = [r for r in ix["rows"] if not only or r["id"] in only]
        write_all(out, os.path.join(body, "body.glb"), os.path.join(body, "play.glb"), rows)
        with open(ip, "w") as f:
            json.dump(ix, f, indent=1)
    else:
        t = control(out, only)
        if a.json:
            json.dump(t, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
