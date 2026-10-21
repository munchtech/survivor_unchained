"""Each piece's cover of her body (armor 7, the garment tuck: docs/armor/PIECE_SCHEMA.md "Garment tuck"): where on her
body a piece lies over her, as records in the tuck format (armor_tuck/<id>.bin: u32 count, then i32 x, y, z of her
body's bind point x 1e5 rounded, f32 value), written to armor_cover/<id>.bin beside the piece's tuck.

A piece's tuck records mark only her skin that would come through it (a belt or a pauldron standing clear of her has
none), so they cannot say what a piece covers. Its cover: her body points whose outward normal ray (from 4 mm under her
skin, out to REACH) meets the piece's faces, the hit standing over that point of her (not over a nearer limb); the
value is FULL (lain all the way down, never removed: only a tuck record's 0.995 removes) over all of it (--ramp: eased
in from its edge over that many mm instead; the game spreads it out past the edge, GarmentTuck.Spread). HerWear reads max(tuck, cover) a point as the piece's footprint for the garment tuck.

    python tools/armor/cover.py [--pieces a,b,..] [--reach 45] [--ramp 0]
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wearcheck as wc  # noqa: E402

FULL = 0.98


def skin_body(rows):
    """Her body (skin), its normals, and the pieces of `rows` on her skeleton, as wearcheck loads them."""
    sk = wc.skin.Skeleton.load(wc.skin.SKELETONS / "heroine_skeleton.json")
    files = [(wc.skin.PEOPLE / "heroine.glb", lambda n: n == "Heroine", "skin")]
    owner = {}
    for path in sorted({r["path"] for r in rows}):
        names = {m: r["id"] for r in rows if r["path"] == path for m in r["meshes"]}
        owner.update(names)
        files.append((wc.skin.Path(path), lambda n, s=frozenset(names): n in s, "garment"))
    body = wc.skin.Body(sk, files, None, label="her", helpers=False)
    pid = np.array([owner.get(p, "") for p in body.piece])
    isk = np.nonzero(body.kind == "skin")[0]
    loc = np.full(len(body.P), -1)
    loc[isk] = np.arange(len(isk))
    TS = loc[body.T[(body.kind[body.T] == "skin").all(1)]]
    Ps = body.P[isk]
    Ns = wc.skin._normals(Ps, TS)
    return body, pid, Ps, Ns


def cover_of(Ps, Ns, kd_s, PB, TB, reach, ramp):
    """A piece's cover of her body points Ps (normals Ns): 0..FULL a point."""
    c = np.zeros(len(Ps))
    if not len(TB):
        return c
    d0, _ = cKDTree(PB).query(Ps, distance_upper_bound=reach + 0.01)
    cand = np.nonzero(np.isfinite(d0))[0]
    if not len(cand):
        return c
    kd_f = cKDTree(PB[TB].mean(1))
    hit = np.zeros(len(Ps), bool)
    back = 0.004
    for a in range(0, len(cand), 1500):
        ii = cand[a:a + 1500]
        O = Ps[ii] - Ns[ii] * back
        _, ci = kd_f.query(Ps[ii], k=min(wc.K0, len(TB)))
        ci = ci.reshape(len(ii), -1)
        t, _, _, _ = wc.cast(O, Ns[ii], PB[TB[ci]])
        t = np.where((t >= 0) & (t <= reach + back), t, np.inf)
        tm = t.min(1)
        ok = np.isfinite(tm)
        if not ok.any():
            continue
        # (the hit stands over this point of her, not over a nearer limb of hers)
        hp = O[ok] + Ns[ii[ok]] * tm[ok, None]
        dh, _ = kd_s.query(hp)
        h = tm[ok] - back
        hit[ii[ok]] = dh >= 0.6 * h - 0.003
    if not hit.any():
        return c
    if hit.all():
        c[:] = FULL
        return c
    din, _ = cKDTree(Ps[~hit]).query(Ps[hit])
    c[hit] = FULL * np.clip(din / ramp, 0, 1) if ramp > 0 else FULL
    return c


def write(path, Ps, c):
    q = np.round(Ps.astype(np.float64) * 1e5).astype(np.int64)
    k = np.nonzero(c > 0)[0]
    uq, inv = np.unique(q[k], axis=0, return_inverse=True)
    g = np.zeros(len(uq))
    np.maximum.at(g, np.asarray(inv).ravel(), c[k])
    rec = np.zeros(len(uq), dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    rec["x"], rec["y"], rec["z"], rec["t"] = uq[:, 0], uq[:, 1], uq[:, 2], g
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<I", len(uq)) + rec.tobytes())
    return len(uq)


def cover_path(r):
    return os.path.join(os.path.dirname(r["tuck_path"]), "..", "armor_cover", f"{r['id']}.bin")


def main(argv):
    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    only = set(opt("--pieces", "").split(",")) - {""} or None
    reach = float(opt("--reach", "45")) / 1000
    ramp = float(opt("--ramp", "0")) / 1000
    rows = [r for r in wc.catalogue(only) if r["slot"] != "ink"]
    # (the cloak too: it covers what is under it)
    for path in wc.INDEXES:
        for r in json.load(open(path, encoding="utf-8")):
            if r["slot"] in wc.SKIP_SLOTS and r["slot"] != "ink" and (not only or r["id"] in only):
                rr = dict(r)
                base = os.path.dirname(path)
                rr["path"] = os.path.join(base, rr["file"].replace("res://art/armor/", "")) if rr.get("file") else os.path.join(base, f"heroine_outfit_{rr['outfit']}.gltf")
                rr["tuck_path"] = os.path.join(base, rr["tuck"])
                rows.append(rr)
    body, pid, Ps, Ns = skin_body(rows)
    kd_s = cKDTree(Ps)
    for r in rows:
        v = np.nonzero(pid == r["id"])[0]
        T = body.T[(pid[body.T] == r["id"]).all(1)]
        c = cover_of(Ps, Ns, kd_s, body.P, T, reach, ramp)
        n = write(os.path.abspath(cover_path(r)), Ps, c)
        print(f"cover: {r['id']:20} {len(v):6d} verts, {n:6d} points ({int((c >= FULL).sum())} full)")


if __name__ == "__main__":
    main(sys.argv[1:])
