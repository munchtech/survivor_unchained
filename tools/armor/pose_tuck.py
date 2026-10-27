"""The pose-aware tuck (Body 14, 26 October 2026): a piece's armor_tuck record raised where her skin comes out
through the piece in her clips, as wearcheck measures it.

wearcheck --dump writes, for each skin test, every footprint skin point's least gap past the piece's OUTER face over
the clips (min_out; negative: her skin shows through it there), its rest gap and the tuck it already has. Here each
such point's tuck is raised to what keeps it under the piece (-min_out + MARGIN), capped at CAP (the shader's tuck is
10 mm at most, 0.98 a full mark, never 0.995 and over: that would stop drawing her there), and only where her skin is
under the piece at rest (rest gap >= 0: hidden by it), faded to nothing over FADE mm at the footprint's edge, where she
shows beside it. The raise is spread over SPREAD mm of the footprint (each point the largest of its neighbours'
values, falling off linearly), so the tucked patch has no step. A record only ever rises.

    python tools/armor/pose_tuck.py <dump dir> <art dir> [--pieces a,b,..] [--cap 0.010] [--margin 0.0015]

<art dir> is godot/art (people/ and armor/ under it, as wearcheck's WC_ART). Prints POSE_TUCK lines.
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

MARGIN = 0.0015      # m past the outer face's measure: her skin kept this far under it
SPREAD = 0.012       # m: the raise spread over the footprint
FADE = 0.010         # m: faded to 0 at the footprint's edge (her skin there shows beside the piece)
FULL, GONE_BELOW = 0.98, 0.99


def read(path):
    if not os.path.isfile(path):
        return {}
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    rec = np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4)
    return {tuple(int(x) for x in r["k"]): float(r["v"]) for r in rec}


def write(path, d):
    keys = sorted(d)
    rec = np.zeros(len(keys), np.dtype([("k", "<i4", 3), ("v", "<f4")]))
    rec["k"] = np.array(keys, np.int64).reshape(-1, 3)
    rec["v"] = [d[k] for k in keys]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(struct.pack("<I", len(rec)) + rec.tobytes())


def rows(art):
    out = {}
    for sub in ("people", "armor"):
        ix = os.path.join(art, sub, "armor_index.json")
        if os.path.isfile(ix):
            for r in json.load(open(ix, encoding="utf-8")):
                out[r["id"]] = (ix, os.path.join(art, sub, r["tuck"]))
    return out


def main(argv):
    def opt(n, d):
        return argv[argv.index(n) + 1] if n in argv else d
    a = [x for i, x in enumerate(argv) if not x.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    dump, art = a[0], a[1]
    cap = float(opt("--cap", "0.010"))
    margin = float(opt("--margin", str(MARGIN)))
    want = opt("--pieces", "")
    want = set(want.split(",")) if want else None
    R = rows(art)
    counts = {}
    for f in sorted(os.listdir(dump)):
        if not (f.startswith("skin_") and f.endswith(".npz")):
            continue
        pid = f[5:-4]
        if (want and pid not in want) or pid not in R:
            continue
        z = np.load(os.path.join(dump, f))
        rest, mo, rg, tk = z["rest"].astype(np.float64), z["min_out"], z["rest_gap"], z["tuck"]
        tree = cKDTree(rest)
        under = np.isfinite(rg) & (rg >= 0)
        # (the footprint's edge: the nearest skin point not under the piece at rest)
        if (~under).any():
            de, _ = cKDTree(rest[~under]).query(rest)
        else:
            de = np.full(len(rest), np.inf)
        fade = np.clip(de / FADE, 0, 1) * under
        need = np.where(np.isfinite(mo), np.clip(-mo + margin, 0, None) + tk, 0)      # (tk: the tuck it was measured with)
        need = np.minimum(need, cap)
        raise_ = np.zeros(len(rest))
        src = np.nonzero(need > tk + 1e-4)[0]
        for i, js in zip(src, tree.query_ball_point(rest[src], SPREAD)):
            js = np.asarray(js, int)
            fall = 1 - np.linalg.norm(rest[js] - rest[i], axis=1) / SPREAD
            raise_[js] = np.maximum(raise_[js], need[i] * fall)
        t = np.minimum(raise_ * fade / 0.010, FULL)
        ix, path = R[pid]
        d = read(path)
        keys = np.round(rest.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)
        up = 0
        for k, v in zip(map(tuple, keys), t):
            if v > d.get(k, 0.0) + 1e-3:
                d[k] = float(min(v, FULL))
                up += 1
        write(path, d)
        counts[(ix, pid)] = len(d)
        shown = int((mo < -0.002).sum())
        print("POSE_TUCK %-26s footprint %5d, through > 2 mm %5d (of them under it at rest %d), raised %5d points (max %.1f mm), record %d"
              % (pid, len(rest), shown, int(((mo < -0.002) & under).sum()), up, float(t.max() * 10) if len(t) else 0, len(d)))
    for ix in {k[0] for k in counts}:
        js = json.load(open(ix, encoding="utf-8"))
        for r in js:
            if (ix, r["id"]) in counts and "tuck_count" in r:
                r["tuck_count"] = counts[(ix, r["id"])]
        json.dump(js, open(ix, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:])
