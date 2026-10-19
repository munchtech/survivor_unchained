# tuckcheck.py ART: armor_tuck/*.bin read back and set against heroine.glb's COLOR_0 channels, by position.
import json, os, sys, struct, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
from heroine_lod import Gltf

art = sys.argv[1]
CH = ["warden", "arcanist", "reaver", "ranger"]
g = Gltf(os.path.join(art, "heroine.glb"))
node = next(n for n in g.js["nodes"] if n.get("name") == "Heroine")
pos, col = [], []
for mat, attrs, tris in g.prims(node["mesh"]):
    pos.append(attrs["POSITION"][0].astype(np.float64))
    c, norm = attrs["COLOR_0"]
    col.append(c.astype(np.float64) / (np.iinfo(c.dtype).max if norm and c.dtype.kind in "ui" else 1))
pos, col = np.vstack(pos), np.vstack(col)
q = np.round(pos * 1e5).astype(np.int64)
uq, inv = np.unique(q, axis=0, return_inverse=True)
inv = np.asarray(inv).ravel()
print("body: %d glTF vertices, %d positions; hash %s" % (len(pos), len(uq), hashlib.sha1(uq.astype("<i4").tobytes()).hexdigest()))
idx = json.load(open(os.path.join(art, "armor_index.json")))
key = {tuple(r): i for i, r in enumerate(uq)}
for o in ["warden", "arcanist", "ranger", "reaver"]:
    ch = np.zeros(len(uq)); np.maximum.at(ch, inv, col[:, CH.index(o)])
    mx = np.zeros(len(uq)); miss = 0
    for r in idx:
        if r["outfit"] != o or not r["tuck"]:
            continue
        b = open(os.path.join(art, r["tuck"]), "rb").read()
        n = struct.unpack_from("<I", b)[0]
        rec = np.frombuffer(b, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
        assert n == r["tuck_count"], (r["id"], n, r["tuck_count"])
        for x, y, z, t in rec:
            i = key.get((int(x), int(y), int(z)))
            if i is None:
                miss += 1
            else:
                mx[i] = max(mx[i], t)
    full = ch > 0.973
    lost = full & (mx <= 0.973)
    d = ch - mx
    print("%s: %d positions full in the glb's channel, %d not full in any slot (largest drop %.3f, %d drops over 0.05); slot records off her body %d; rises over 1/255: %d (largest %.3f)"
          % (o, int(full.sum()), int(lost.sum()), d.max(), int((d > 0.05).sum()), miss, int((d < -1 / 255).sum()), -d.min()))
# detail: per lost or risen position, each slot's tuck
for o in ["arcanist", "ranger", "warden", "reaver"]:
    ch = np.zeros(len(uq)); np.maximum.at(ch, inv, col[:, CH.index(o)])
    per = {}
    for r in idx:
        if r["outfit"] != o or not r["tuck"]:
            continue
        b = open(os.path.join(art, r["tuck"]), "rb").read()
        n = struct.unpack_from("<I", b)[0]
        rec = np.frombuffer(b, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
        v = np.zeros(len(uq))
        for x, y, z, t in rec:
            i = key.get((int(x), int(y), int(z)))
            if i is not None: v[i] = t
        per[r["slot"]] = v
    mx = np.max(list(per.values()), 0)
    bad = np.nonzero(((ch > 0.973) & (mx <= 0.973)) | (mx - ch > 1 / 255 + 1e-3))[0]
    for i in bad[:20]:
        print("  %s at %s (m, Y-up): channel %.3f; %s" % (o, (uq[i] / 1e5).round(3), ch[i], ", ".join("%s %.3f" % (s, v[i]) for s, v in per.items() if v[i] > 0)))
