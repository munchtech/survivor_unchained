"""Her body's outfit tuck channels (COLOR_0 r g b a = warden arcanist reaver ranger, People.OutfitChannels) written
from the outfits' tuck records (Body 15, 27 October 2026).

When a calling's whole set is worn and it has an _lod file, the game does not build a tuck map from the records
(HerWear.TuckMap): her skin reads the calling's channel of her body's vertex colours (HerWear.Apply, tuck_channel =
People.OutfitChannel). heroine_outfits.py writes those channels with the export; a body of record made by post-steps
on another body (the G3 chain's BODY, s4) kept that body's old colours, re-numbered under it: on Body 15's body the
arcanist and ranger channels were empty and the warden and reaver ones half there, so under a full arcanist set her
forearm skin was drawn untucked and came out through the opera glove (the glove-poke frame, c_arcanist_f).

Each channel here = the largest of
  - the outfit's tuck records at her points (people/armor_index.json rows of that outfit, their armor_tuck/*.bin:
    the same values TuckMap lays for a part set, pose_tuck's raises included), and
  - with --base BASE_GLB: BASE's own channel carried to BODY as body_follow_post carries the records (paint twins:
    the largest of the twins; BODY's new points the mean of BASE's three nearest within 8 mm), which keeps the
    export's own marks the records lack (the reaver wrap's, worn_reaver_post),
eight bits. Her other primitives' colours, the other attributes and the file's layout are left as they are. Run after
the records' last change (the chain: after s5c pose_tuck, before s6 LODs, whose bodies take these colours).
Idempotent (no mark: the same inputs write the same bytes).

--lod: the outfits' LOD bodies already built (PEOPLE_DIR/heroine_outfit_*_lod.gltf, mesh lod_body: her body's own
points, none moved) given the same colours by place, so they need no rebuild.

    python tools/assets/body_channels_post.py BODY_GLB PEOPLE_DIR [--base BASE_GLB] [--lod] [--dry]

Prints CHANNELS lines: each channel's marked points before and after, and how many changed.
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body_follow_post import Body, Field, _rkey  # noqa: E402

CHANNELS = ("warden", "arcanist", "reaver", "ranger")   # (People.OutfitChannels)


def _records(path):
    if not os.path.isfile(path):
        return {}
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    rec = np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4)
    return {tuple(int(x) for x in r["k"]): float(r["v"]) for r in rec}


def _colors(B):
    """BODY's COLOR_0 over its welded points' copies (Pc order) as 0..1 floats, and each primitive's raw array."""
    raw = [B.G.get(p["attributes"]["COLOR_0"]) for p in B.prims]
    return raw, np.vstack([r.astype(np.float64) / 65535.0 if r.dtype == np.uint16 else
                           r.astype(np.float64) / 255.0 if r.dtype == np.uint8 else r.astype(np.float64) for r in raw])


def channels(body, people, base=None):
    B = Body(body)
    raw, C = _colors(B)
    idx = json.load(open(os.path.join(people, "armor_index.json"), encoding="utf-8"))
    key = [tuple(k) for k in _rkey(B.U)]
    val = np.zeros((len(B.U), 4))
    for k, outfit in enumerate(CHANNELS):
        at = {}
        for r in idx:
            if r.get("outfit") != outfit or not r.get("tuck"):
                continue
            for q, t in _records(os.path.join(people, r["tuck"])).items():
                if t > at.get(q, 0.0):
                    at[q] = t
        val[:, k] = [at.get(q, 0.0) for q in key]
    if base:
        A = Body(base)
        _, CA = _colors(A)
        a = np.zeros((len(A.U), 4))
        np.maximum.at(a, A.wid, CA[:, :4])
        fld = Field(A, B)
        ok = fld.twin >= 0
        car = np.zeros((len(B.U), 4))
        np.maximum.at(car, fld.twin[ok], a[ok])
        if len(fld.new):
            d, j = cKDTree(fld.X1).query(B.U[fld.new], k=3)
            for q, dd, jj in zip(fld.new, d, j):
                near = jj[dd < 0.008]
                if len(near):
                    car[q] = a[near].mean(0)
        val = np.maximum(val, car)
    val = np.round(np.clip(val, 0, 1) * 255) / 255
    return B, raw, C, val


def _write(G, ai, r, v):
    """COLOR_0 accessor ai (raw r) given v [n, 4] in 0..1, a channel kept where it already holds the value to eight
    bits; the copies changed per channel."""
    new = r.copy()
    ch = np.zeros(4, int)
    for k in range(4):
        if r.dtype == np.uint16:
            q = np.round(v[:, k] * 65535).astype(np.uint16)
            keep = np.abs(r[:, k].astype(int) - q.astype(int)) <= 65535 // 255 // 2
        elif r.dtype == np.uint8:
            q = np.round(v[:, k] * 255).astype(np.uint8)
            keep = r[:, k] == q
        else:
            q = v[:, k].astype(r.dtype)
            keep = np.abs(r[:, k] - q) < 0.5 / 255
        new[:, k] = np.where(keep, r[:, k], q)
        ch[k] = int((~keep).sum())
    if G is not None:
        G.put(ai, new)
    return ch


def lod_bodies(people, B, val, dry):
    import glob
    from heroine_neck import _Gl
    at = {tuple(k): i for i, k in enumerate(_rkey(B.U))}
    for f in sorted(glob.glob(os.path.join(people, "heroine_outfit_*_lod.gltf"))):
        G = _Gl(f)
        ch, miss, n = np.zeros(4, int), 0, 0
        for m in G.g["meshes"]:
            if m["name"] != "lod_body":
                continue
            for p in m["primitives"]:
                if "COLOR_0" not in p["attributes"]:
                    continue
                ai = p["attributes"]["COLOR_0"]
                r = G.get(ai)
                ix = np.array([at.get(tuple(k), -1) for k in _rkey(G.get(p["attributes"]["POSITION"]))])
                miss += int((ix < 0).sum())
                n += len(ix)
                v = np.where((ix >= 0)[:, None], val[np.maximum(ix, 0)], r.astype(np.float64) / (65535.0 if r.dtype == np.uint16 else 255.0 if r.dtype == np.uint8 else 1.0))
                ch += _write(None if dry else G, ai, r, v)
        print("CHANNELS lod %-34s %6d body points (%d not on BODY, kept), copies changed %s" % (os.path.basename(f), n, miss, ch.tolist()))
        if not dry and ch.any():
            G.save()


def main(argv):
    a = [x for x in argv if not x.startswith("--")]
    body, people = a[0], a[1]
    base = argv[argv.index("--base") + 1] if "--base" in argv else None
    if base in a:
        a.remove(base)
    lod = "--lod" in argv
    dry = "--dry" in argv
    B, raw, C, val = channels(body, people, base)
    per = val[B.wid]                       # (each copy its welded point's value)
    o = 0
    changed = np.zeros(4, int)
    for p, r in zip(B.prims, raw):
        n = len(r)
        changed += _write(None if dry else B.G, p["attributes"]["COLOR_0"], r, per[o:o + n])
        o += n
    for k, outfit in enumerate(CHANNELS):
        print("CHANNELS %-8s marked %6d -> %6d (hidden %5d -> %5d), %6d copies changed" % (
            outfit, int((C[:, k] > 0.002).sum()), int((per[:, k] > 0.002).sum()), int((C[:, k] >= 0.995).sum()),
            int((per[:, k] >= 0.995).sum()), changed[k]))
    if not dry and changed.any():
        B.G.save()
        print("CHANNELS written:", body)
    if lod:
        lod_bodies(people, B, val, dry)


if __name__ == "__main__":
    main(sys.argv[1:])
