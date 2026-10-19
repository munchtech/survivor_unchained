# tuck_fix.py: a one-off post-process of the committed per-slot tucks (armor_tuck/<outfit>.<slot>.bin),
# so that for each calling the max over its slots' tucks is at least its outfit channel in heroine.glb
# (COLOR_0, OutfitChannels order warden, arcanist, reaver, ranger) at every position of her body.
# The rule (the same one heroine_outfits.py's build applies after its per-slot tuck_of, "TUCK DEFICIT"):
# where the channel exceeds the max over slots, the slot whose garment's surface lies nearest that point
# takes the channel's value there. Candidates are the slots that tuck anything (the build: the slots with
# hiding pieces). The garments are read from heroine_outfit_<calling>.gltf, meshes <outfit>.<slot>.<mat>,
# bind positions (glTF Y-up metres, the frame her body's records are in).
#   python tools/armor/tuck_fix.py godot/art/people [--dry]
import json, os, sys, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
from heroine_lod import Gltf

CH = ["warden", "arcanist", "reaver", "ranger"]
REC = [("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")]
FULL = 0.973
EPS = 1 / 255  # (a deficit within a byte step is the channel's own rounding: its bytes round up as well as down)


def tri_dist(p, a, b, c):
    """Distance from point p (3,) to each triangle (a, b, c: (n, 3)); Ericson's closest point, vectorized."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v, w = vb / den, vc / den
    q = a + ab * v[:, None] + ac * w[:, None]  # (inside the face)
    with np.errstate(divide="ignore", invalid="ignore"):
        e_ab = np.clip(np.nan_to_num(d1 / (d1 - d3)), 0, 1)
        e_ac = np.clip(np.nan_to_num(d2 / (d2 - d6)), 0, 1)
        e_bc = np.clip(np.nan_to_num((d4 - d3) / ((d4 - d3) + (d5 - d6))), 0, 1)
    cands = [q, a, b, c, a + ab * e_ab[:, None], a + ac * e_ac[:, None], b + (c - b) * e_bc[:, None]]
    inside = (va >= 0) & (vb >= 0) & (vc >= 0)
    dist = np.min([np.linalg.norm(x - p, axis=1) for x in cands[1:]], 0)
    return np.where(inside, np.linalg.norm(q - p, axis=1), dist)


def main(art, dry):
    g = Gltf(os.path.join(art, "heroine.glb"))
    node = next(n for n in g.js["nodes"] if n.get("name") == "Heroine")
    pos, col = [], []
    for _, attrs, _ in g.prims(node["mesh"]):
        pos.append(attrs["POSITION"][0].astype(np.float64))
        c, norm = attrs["COLOR_0"]
        col.append(c.astype(np.float64) / (np.iinfo(c.dtype).max if norm and c.dtype.kind in "ui" else 1))
    pos, col = np.vstack(pos), np.vstack(col)
    uq, inv = np.unique(np.round(pos * 1e5).astype(np.int64), axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    key = {tuple(r): i for i, r in enumerate(uq)}
    ipath = os.path.join(art, "armor_index.json")
    idx = json.load(open(ipath, encoding="utf-8"))
    for o in CH:
        ch = np.zeros(len(uq))
        np.maximum.at(ch, inv, col[:, CH.index(o)])
        rows = [r for r in idx if r["outfit"] == o and r["tuck"]]
        per = {}
        for r in rows:
            b = open(os.path.join(art, r["tuck"]), "rb").read()
            n = struct.unpack_from("<I", b)[0]
            v = np.zeros(len(uq))
            for x, y, z, t in np.frombuffer(b, dtype=REC, count=n, offset=4):
                v[key[(int(x), int(y), int(z))]] = t
            per[r["slot"]] = v
        cand = [s for s, v in per.items() if (v > 0).any()]
        og = Gltf(os.path.join(art, "heroine_outfit_%s.gltf" % o))
        tris = {}
        for mi, m in enumerate(og.js["meshes"]):
            s = m["name"].split(".")[1] if m["name"].startswith(o + ".") else None
            if s not in cand:
                continue
            for _, attrs, tr in og.prims(mi):
                p = attrs["POSITION"][0].astype(np.float64)
                tris.setdefault(s, []).append(p[tr])
        tris = {s: np.vstack(t) for s, t in tris.items()}
        # (each slot's triangles found near a point by their centres: the nearest 64, then exactly)
        trees = {s: cKDTree(t.mean(1)) for s, t in tris.items()}

        def sdist(p, s):
            _, j = trees[s].query(p, k=min(64, len(tris[s])))
            t = tris[s][np.atleast_1d(j)]
            return tri_dist(p, t[:, 0], t[:, 1], t[:, 2]).min()
        mx = np.max([per[s] for s in cand], 0)
        # (and where the channel is full, heroine_skin.gdshader's 0.973 and over, and no slot is: a byte's step there is
        # the difference between her skin drawn 10 mm in and not drawn at all)
        bad = np.nonzero((ch - mx > EPS) | ((ch > FULL) & (mx <= FULL)))[0]
        given = {}
        for i in bad:
            p = uq[i] / 1e5
            d = {s: sdist(p, s) for s in tris}
            s = min(d, key=d.get)
            given.setdefault(s, []).append((ch[i] - mx[i], d[s]))
            per[s][i] = ch[i]
        for s, lst in sorted(given.items()):
            a = np.array(lst)
            print("%s.%s: %d positions given the channel (deficit max %.3f, mean %.3f; slot surface %.1f mm max, %.1f mm mean)"
                  % (o, s, len(a), a[:, 0].max(), a[:, 0].mean(), a[:, 1].max() * 1000, a[:, 1].mean() * 1000))
        mx = np.max([per[s] for s in cand], 0)
        # (rises: deeper than the channel, each with the slot that does it and that slot's surface distance)
        for i in np.nonzero(mx - ch > 1 / 255)[0]:
            p = uq[i] / 1e5
            for s in cand:
                if per[s][i] - ch[i] > 1 / 255:
                    print("  rise %s.%s at %s: slot %.3f, channel %.3f, slot surface %.1f mm"
                          % (o, s, p.round(3), per[s][i], ch[i], sdist(p, s) * 1000))
        if dry:
            continue
        for r in rows:
            v = per[r["slot"]]
            k = np.nonzero(v > 0)[0]
            rec = np.zeros(len(k), dtype=REC)
            rec["x"], rec["y"], rec["z"], rec["t"] = uq[k, 0], uq[k, 1], uq[k, 2], v[k]
            with open(os.path.join(art, r["tuck"]), "wb") as f:
                f.write(struct.pack("<I", len(k)) + rec.tobytes())
            r["tuck_count"] = int(len(k))
    if not dry:
        json.dump(idx, open(ipath, "w", encoding="utf-8"), indent=1)
        print("written:", ipath)


if __name__ == "__main__":
    main(sys.argv[1], "--dry" in sys.argv)
