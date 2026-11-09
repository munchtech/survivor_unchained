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
lies under each piece. One row property is A's design and carried: a row whose A tuck is empty (its parts do not hide her
skin: a sheer stocking, belts, skirts, a collar) tucks nothing (a_hides). `control` compares native with A's records carried, row by row.

The cover: tools/armor/cover.py's rule (cover_of: reach 45 mm, ramp 0, deep 25 mm; a row's cover_grow) on this body.

    python tools/armor/gear_tuck.py write --body godot/art/people/body_p1 [--only id,id]   (re-writes the records alone)
    python tools/armor/gear_tuck.py control [--only id,id]   native vs A's records carried onto the gate body (B)
"""
import argparse
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


def tuck_bound(sk, t, hard=None, under=None):
    """heroine_outfits.tuck_bound on this body's welded graph (per vertex in, per vertex out)."""
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
    lw_ = np.minimum(SLOPE * l_, STEP)
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


def tuck_of(sk, PB, TB):
    """Her skin's tuck under one piece (PB points, TB triangles), per vertex of sk; and how many rays grazed it."""
    import trimesh
    t = np.zeros(len(sk.P))
    if not len(TB):
        return t, 0
    lo, hi = PB.min(0) - BOX, PB.max(0) + BOX
    cand = np.nonzero(((sk.P >= lo) & (sk.P <= hi)).all(1))[0]
    if not len(cand):
        return t, 0
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
    return tuck_bound(sk, t, None, under | (t > 0)), grazed


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


def piece_of(out_dir, row):
    """A built row's close-tier meshes on this body: points and triangles (its lod1 / shadow meshes left out)."""
    from gl import Glb
    g = Glb(os.path.join(out_dir, f"{row['id']}.gltf"))
    Ps, Ts, n = [], [], 0
    for name in row["meshes"]:
        m = g.mesh(name)
        if m is None:
            continue
        Ps.append(m.P.astype(np.float64))
        Ts.append(m.T + n)
        n += len(m.P)
    if not Ps:
        return np.zeros((0, 3)), np.zeros((0, 3), np.int64)
    return np.vstack(Ps), np.vstack(Ts)


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
        PB, TB = piece_of(out_dir, r)
        c = cover_of(close, PB, TB, r) if r["slot"] != "ink" else np.zeros(len(close.P))
        if hides.get(r["id"], True):
            tc, gz = tuck_of(close, PB, TB)
            tp = tuck_of(play, PB, TB)[0] if play is not None else np.zeros(0)
        else:
            tc, gz = np.zeros(len(close.P)), 0
            tp = np.zeros(len(play.P)) if play is not None else np.zeros(0)
        Pk = np.vstack([close.P, play.P]) if play is not None else close.P
        nt = write_records(os.path.join(out_dir, "armor_tuck", f"{r['id']}.bin"), Pk, np.r_[tc, tp])
        nc = write_records(os.path.join(out_dir, "armor_cover", f"{r['id']}.bin"), close.P, c)
        r["tuck"] = f"armor_tuck/{r['id']}.bin"
        r["tuck_count"] = nt
        r["cover_count"] = nc
        st = {"tuck_close": int(len(np.unique(np.round(close.P[tc > 0] * 1e5), axis=0))), "tuck_all": nt, "cover": nc,
              "full": int((tc >= 0.98).sum()), "gone": int((tc >= 0.995).sum()), "grazed": gz,
              "max": float(tc.max()) if len(tc) else 0.0}
        stats[r["id"]] = st
        say(f"gear tuck: {r['id']:22} tuck {nt:6d} records ({st['tuck_close']} close), max {st['max']:.2f}, "
            f"{gz} grazing rays; cover {nc:6d}")
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
