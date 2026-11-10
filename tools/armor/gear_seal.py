"""THE PLATE HIDES HER (P2 gear): her skin under a rigid part that no game camera sees, in any frame of her motion, is
not drawn; and the SEAL check, that no camera ever sees the hole that leaves.

    python tools/armor/gear_seal.py hide [--gear <dir>] [--pieces id,id] [--clips <dir|list>] [--step 2]
        her points under each rigid row's rigid parts (gear_tuck.under_rigid_of) never SEEN (below) at rest or in any
        posed frame of the clips -> <gear>/armor_hidden/<id>.bin (tuck records, 1.0 = hidden) + <id>.json (the piece's
        hash: gear_tuck.write_all uses the set only while the piece is the one it was measured on). Then
        `gear_tuck.py write` makes them gone (GONE_IN from any of her not hidden).
    python tools/armor/gear_seal.py seal [--gear <dir>] [--pieces id,id] [--clips ...] [--step 1] [--json out.json]
        per clip: her gone skin under each piece that a camera sees (mm2, the frame and where). Target 0.

SEEN, for her point p in one posed frame and one view direction d (toward the camera): the camera's ray reaches p (from p
along d nothing of the piece, nor of her skin that cannot be gone, is met), and with p not drawn the camera looks into her:
from p along -d the first thing met is her own skin (the far side of her arm) or nothing, not the piece's outer face (where
her skin stands past a plate, the plate lies inside her there and the hole shows the plate). A view with d below her
tangent plane is not p's: the camera's ray entered her elsewhere first, and that point answers for it.

The views (godot/src/Game/FollowCamera.cs): the play camera 56 deg down at 23 m, the close views 15 deg / 4.2 m and
3 deg / 1.95 m, the Look / inventory front view; she turns and the camera orbits, so every azimuth, elevations from
VIEW_LOW to straight down (VIEW_N directions over the sphere, those at or above VIEW_LOW). Cameras are far against her
size: parallel rays.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gear_tuck as gt  # noqa: E402
import gear_wear as gw  # noqa: E402

VIEW_LOW = -15.0     # deg: the lowest camera (a close view under her, her arm raised over it)
VIEW_N = 240         # directions over the whole sphere (about 13 deg apart); those at or above VIEW_LOW are cast
SEAL_N = 600         # the seal check's directions (about 8 deg apart: finer than the set it checks)
VIEW_COS = 0.0       # a point seen no more squarely than this (cos of the view to her normal) counts as hidden
SEEN_CAP = 0.5       # (hide: a point seen this squarely is no longer cast)
CLAMP = 0.06         # her skin standing up to this far past a plate is put back under it (the clips: up to 51 mm)
OFF = 0.0005         # a ray's start off her surface (m)
BOX = 0.35           # blockers within this of the piece's posed box (a ray leaving it counts as seen)
SEAL_TOL = 2.0       # mm2 per clip read as zero (a ray grazing a lame's edge)


def view_dirs(n=VIEW_N, low=VIEW_LOW):
    """Unit directions toward the camera (Y up): the sphere's, at or above `low` degrees of elevation."""
    d = gt.fib_dirs(n)[:, [0, 2, 1]]
    return d[d[:, 1] >= np.sin(np.radians(low))]


def piece_hash(PB):
    return hashlib.sha1(np.round(np.asarray(PB, np.float64) * 1e5).astype(np.int64).tobytes()).hexdigest()


def clamped(O, N, pr, pm, br, back_piece):
    """Her points standing past the plate, put back under it: from 2 mm outside her point, inward (-N), the piece's outer
    face is met at or below her point and within CLAMP, and from her point inward nothing of her comes first: the point
    goes 1.5 mm under the piece's next face inward (its inner face), or 1.5 mm under the outer face (a single-sided part).
    Not drawn, such skin shows the plate where it stood: what a camera sees there is what it would see with her skin
    under the plate. pr, pm: the piece alone (intersector, mesh); br, back_piece: the piece + all of her."""
    O = O.copy()
    o1 = O + N * 0.002
    tri, ri, loc = pr.intersects_id(o1, -N, multiple_hits=False, return_locations=True)
    dep = np.linalg.norm(loc - o1[ri], axis=1) - 0.002
    ok = ((pm.face_normals[tri] * N[ri]).sum(1) > 0) & (dep >= -0.0005) & (dep <= CLAMP)
    ri, loc, dep = ri[ok], loc[ok], dep[ok]
    if not len(ri):
        return O
    o0 = O[ri] - N[ri] * OFF
    t2, r2, l2 = br.intersects_id(o0, -N[ri], multiple_hits=False, return_locations=True)
    skin_first = np.zeros(len(ri), bool)
    skin_first[r2] = ~back_piece[t2] & (np.linalg.norm(l2 - o0[r2], axis=1) < dep[r2] - OFF)
    ri, loc = ri[~skin_first], loc[~skin_first]
    O[ri] = loc - N[ri] * 0.0015
    t3, r3, l3 = pr.intersects_id(loc - N[ri] * 1e-4, -N[ri], multiple_hits=False, return_locations=True)
    ok3 = np.linalg.norm(l3 - loc[r3], axis=1) <= 0.012
    O[ri[r3[ok3]]] = l3[ok3] - N[ri[r3[ok3]]] * 0.0015
    return O


def seen_of(O, N, idx, dirs, front_P, front_T, back_P, back_T, back_piece, floor=None):
    """Of the points idx (O, N their posed points and normals), how squarely each is SEEN (module doc): the largest
    cos(view, her normal) over the views of dirs that see it, -1 where none does; and that view's index. Views no more
    square than `floor` (per point: what an earlier frame already found) are not cast. front_*: what blocks the camera's
    ray (the piece + her skin that cannot be gone); back_*: the piece + all of her skin, back_piece a flag per back
    triangle (the piece's)."""
    import trimesh
    best = np.full(len(idx), -1.0) if floor is None else np.asarray(floor, float).copy()
    got = np.full(len(idx), -1)
    if not len(idx):
        return best, got
    fr = trimesh.ray.ray_pyembree.RayMeshIntersector(trimesh.Trimesh(front_P, front_T, process=False))
    bm = trimesh.Trimesh(back_P, back_T, process=False)
    br = trimesh.ray.ray_pyembree.RayMeshIntersector(bm)
    fn_b = bm.face_normals
    pm = trimesh.Trimesh(back_P, back_T[back_piece], process=False)
    pr = trimesh.ray.ray_pyembree.RayMeshIntersector(pm)
    Oi, Ni = clamped(O[idx], N[idx], pr, pm, br, back_piece), N[idx]
    cs = Ni @ dirs.T
    for k in np.argsort(-cs.max(0)):
        d = dirs[k]
        todo = np.nonzero((cs[:, k] > 0.0) & (cs[:, k] > best))[0]
        if not len(todo):
            continue
        Df = np.ascontiguousarray(np.broadcast_to(d, (len(todo), 3)))
        hit = fr.intersects_any(Oi[todo] + (Ni[todo] + d) * (OFF * 0.5), Df) if len(front_T) else np.zeros(len(todo), bool)
        c = todo[~hit]
        if not len(c):
            continue
        tri, ri = br.intersects_id(Oi[c] - Ni[c] * OFF - d * OFF * 0.4, -Df[:len(c)], multiple_hits=False)
        sealed = np.zeros(len(c), bool)
        sealed[ri] = back_piece[tri] & ((fn_b[tri] @ d) > 0)
        sn = c[~sealed]
        best[sn] = cs[sn, k]
        got[sn] = k
    return best, got


class Frames:
    """B with one piece, posed per frame (gear_wear's scene and clip poser): her skin's points (tucked as the shader
    tucks them under the piece) and normals, her triangles, the piece's points and triangles."""

    def __init__(self, gear, pid, rows=None, body_dir=None):
        ix, rows_all = gw.load_rows(gear)
        self.row = next(r for r in rows_all if r["id"] == pid)
        self.body_dir = body_dir = body_dir or os.path.join(gw.REPO, "godot", "art", "people", ix["body"])
        self.sc = sc = gw.build_scene(body_dir, [self.row], {pid})
        self.pv = np.nonzero(sc.owner == pid)[0]
        self.all = np.r_[sc.ish, self.pv]
        self.sub = sc.restrict(self.all)
        self.nsh = len(sc.ish)
        loc = np.full(len(sc.P0), -1)
        loc[self.pv] = np.arange(len(self.pv))
        self.TP = loc[sc.T[sc.tri_owner == pid]]
        self.TS = sc.TS
        recs = gw.read_records(self.row["tuck_path"]) if self.row.get("tuck_path") else {}
        depth, self.gone = gw.skin_tuck(recs, sc.keys)
        assert np.array_equal(sc.ish[:len(sc.isk)], sc.isk), "gear_seal: skin points not first among her points"
        self.depth = np.zeros(self.nsh)
        self.depth[:len(sc.isk)] = depth
        self.keys = np.round(sc.P0[sc.isk] * 1e5).astype(np.int64)

    def pose(self, S=None, w=None):
        sc = self.sc
        P = sc.rest(self.all, w or {}, self.sub)
        if S is not None:
            P = sc.lbs(S, P, sc.J[self.all], sc.W[self.all])
        Ps, Pp = P[:self.nsh], P[self.nsh:]
        Ns = sc.normals_sh(Ps)
        return Ps - Ns * self.depth[:, None], Ns, Pp

    def frames(self, clips, step):
        yield "rest", 0, None, {}
        for name, fr in gw.dump_sources(self.sc, clips, step):
            for f, S, w in fr():
                yield name, f, S, w


def blockers(Ps, Pp, TS, TP, cand_sh, box):
    """front (piece + her triangles with no candidate point) and back (piece + all of her) meshes, within the box."""
    lo, hi = box
    inb = lambda X: ((X >= lo) & (X <= hi)).all(-1)  # noqa: E731
    ts = TS[inb(Ps[TS]).any(1)]
    tf = ts[~cand_sh[ts].any(1)]
    n = len(Pp)
    PB = np.vstack([Pp, Ps])
    front_T = np.vstack([TP, tf + n])
    back_T = np.vstack([TP, ts + n])
    back_piece = np.r_[np.ones(len(TP), bool), np.zeros(len(ts), bool)]
    return PB, front_T, back_T, back_piece


def hide(gear, pid, clips, step, log=print):
    """Her close points under the row's rigid parts never seen (rest + every frame): (hidden keys [n, 3], stats)."""
    t0 = time.time()
    fr = Frames(gear, pid)
    sc = fr.sc
    PB, TB, RB = gt.piece_of(gear, fr.row, flags=True)
    if not RB.any():
        return None, {"why": "no rigid part"}
    sk = gt.Skin(os.path.join(fr.body_dir, "body.glb"))
    under = gt.under_rigid_of(sk, PB, TB, RB)
    kk = {tuple(k): i for i, k in enumerate(np.round(sk.P * 1e5).astype(np.int64))}
    cand_isk = np.array([under[kk[tuple(k)]] if tuple(k) in kk else False for k in fr.keys])
    cand_sh = np.zeros(fr.nsh, bool)
    cand_sh[:len(cand_isk)] = cand_isk
    cidx = np.nonzero(cand_sh)[0]
    n0 = len(cidx)
    best = np.full(n0, -1.0)
    dirs = view_dirs()
    killed = {}
    nf = 0
    for name, f, S, w in fr.frames(clips, step):
        alive = np.nonzero(best < SEEN_CAP)[0]
        if not len(alive):
            break
        Ps, Ns, Pp = fr.pose(S, w)
        box = (Pp.min(0) - BOX, Pp.max(0) + BOX)
        Pall, front_T, back_T, back_piece = blockers(Ps, Pp, fr.TS, fr.TP, cand_sh, box)
        b, _ = seen_of(Ps, Ns, cidx[alive], dirs, Pall, front_T, Pall, back_T, back_piece, floor=best[alive])
        newly = (b > VIEW_COS) & (best[alive] <= VIEW_COS)
        if newly.any():
            killed[name] = killed.get(name, 0) + int(newly.sum())
        best[alive] = b
        nf += 1
    hid = np.zeros(fr.nsh, bool)
    hid[cidx[best <= VIEW_COS]] = True
    keys = fr.keys[hid[:len(fr.keys)]]
    st = {"piece": pid, "piece_hash": piece_hash(PB), "under": int(n0), "hidden": int(len(keys)), "frames": nf,
          "views": int(len(dirs)), "view_low": VIEW_LOW, "view_cos": VIEW_COS, "step": step,
          "clips": [os.path.basename(c) for c in clips], "seen_by_clip": killed, "s": round(time.time() - t0, 1),
          "_best": best, "_keys": fr.keys[cidx[cidx < len(fr.keys)]]}
    log(f"gear_seal hide: {pid}: {n0} under rigid, {len(keys)} hidden over {nf} frames ({st['s']} s)")
    return keys, st


def write_hidden(gear, pid, keys, st):
    d = os.path.join(gear, "armor_hidden")
    os.makedirs(d, exist_ok=True)
    gt.write_records(os.path.join(d, f"{pid}.bin"), keys.astype(np.float64) / 1e5, np.ones(len(keys)))
    np.savez(os.path.join(d, f"{pid}.npz"), keys=st.pop("_keys"), best=st.pop("_best"))
    json.dump(st, open(os.path.join(d, f"{pid}.json"), "w"), indent=1)


def seal(gear, pid, clips, step, log=print):
    """Per clip: her gone skin (the piece's tuck records >= the shader's discard) seen from SEAL_N views: mm2 (max over
    frames), the frame, and the bone nearest the worst point."""
    fr = Frames(gear, pid)
    sc = fr.sc
    gone_sh = np.zeros(fr.nsh, bool)
    gone_sh[:len(fr.gone)] = fr.gone
    idx = np.nonzero(gone_sh)[0]
    T = sc.TS
    P0 = sc.P0[sc.ish]
    ta = np.linalg.norm(np.cross(P0[T[:, 1]] - P0[T[:, 0]], P0[T[:, 2]] - P0[T[:, 0]]), axis=1) / 2
    VA = np.zeros(fr.nsh)
    np.add.at(VA, T.ravel(), np.repeat(ta / 3, 3))
    names = sc.poser.names
    dom = np.array([names[j] for j in sc.J[sc.ish, sc.W[sc.ish].argmax(1)]])
    dirs = view_dirs(SEAL_N)
    res = {"piece": pid, "gone_mm2": round(float(VA[idx].sum() * 1e6), 1), "gone_n": int(len(idx)), "clips": {}}
    for name, f, S, w in fr.frames(clips, step):
        if not len(idx):
            break
        Ps, Ns, Pp = fr.pose(S, w)
        box = (Pp.min(0) - BOX, Pp.max(0) + BOX)
        Pall, front_T, back_T, back_piece = blockers(Ps, Pp, fr.TS, fr.TP, gone_sh, box)
        b, first = seen_of(Ps, Ns, idx, dirs, Pall, front_T, Pall, back_T, back_piece, floor=np.full(len(idx), VIEW_COS))
        seen = b > VIEW_COS
        a = float(VA[idx[seen]].sum() * 1e6)
        c = res["clips"].setdefault(name, {"max_mm2": 0.0, "frame": -1, "where": "", "union": np.zeros(len(idx), bool)})
        c["union"] |= seen
        if a > c["max_mm2"]:
            k = idx[seen][np.argmax(VA[idx[seen]])]
            el = float(np.degrees(np.arcsin(dirs[first[seen][np.argmax(VA[idx[seen]])]][1])))
            c.update(max_mm2=round(a, 1), frame=f, where=f"{dom[k]} (view elevation {el:.0f} deg)")
    for name, c in res["clips"].items():
        c["union_mm2"] = round(float(VA[idx[c.pop("union")]].sum() * 1e6), 1)
    worst = max(res["clips"].items(), key=lambda kv: kv[1]["max_mm2"]) if res["clips"] else ("", {"max_mm2": 0})
    res["worst"] = {"clip": worst[0], **worst[1]}
    log(f"gear_seal seal: {pid}: gone {res['gone_mm2']} mm2; worst seen {worst[1]['max_mm2']} mm2 in {worst[0]} "
        f"{worst[1].get('where', '')}")
    return res


def rigid_rows(gear):
    ix = json.load(open(os.path.join(gear, "gear_index.json")))
    return [r["id"] for r in ix["rows"] if not r.get("lod") and r.get("file")
            and (r.get("rigid") or r["id"].startswith(("plate_", "mar_her_")))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("hide", "seal"))
    ap.add_argument("--gear", default=gw.GEAR)
    ap.add_argument("--pieces", default="")
    ap.add_argument("--clips", default=gw.CLIPS)
    ap.add_argument("--step", type=int, default=None)
    ap.add_argument("--json")
    a = ap.parse_args()
    clips = gw.clip_files(a.clips)
    ids = [p for p in a.pieces.split(",") if p] or rigid_rows(a.gear)
    out = {}
    for pid in ids:
        if a.cmd == "hide":
            keys, st = hide(a.gear, pid, clips, a.step or 2)
            if keys is not None:
                write_hidden(a.gear, pid, keys, st)
            out[pid] = st
        else:
            out[pid] = seal(a.gear, pid, clips, a.step or 1)
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
