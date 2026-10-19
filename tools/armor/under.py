"""What of a built piece another slot's piece covers, so the game leaves it undrawn while that slot is filled (armor 4
r3, F5: the plate top's shoulder strap came through the warden's pauldron in her heavy swing).

    python tools/armor/under.py <id> [<id> ...]      (build.py runs it after each piece)

For each covering slot in UNDER (today: pauldrons), its pieces are every calling outfit's meshes of that slot
(heroine_outfit_<calling>.gltf, <calling>.pauldrons.*). A vertex of the piece's leather (its straps: the plate itself
always draws) is covered when a ray out along its normal (or back along it: a strap's inner face) meets EVERY one of those pieces within REACH at rest (so the
cut holds for any pauldron), and it is hidden when it is also at least INSET in from the covered region's edge (the
strap ends 5 mm inside the pauldron's rim). The game (HerWear, Rpg.ArmorUnder) drops a triangle whose three vertices
are all hidden, in the piece's full and gameplay meshes, while that slot holds a piece.

Each covering piece its own cut (its id, <calling>.<slot>), and "*" (what all of them cover) for any other piece in
that slot. Writes godot/art/armor/armor_under/<id>.<slot>.<calling or any>.bin (u32 count, then count x i32 x, y, z: bind position, glTF Y-up
metres x 1e5 rounded, as the tuck records key her points) and the row's "under" in armor_index.json:
{slot: {piece id or "*": path under art/armor}}.
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
import heroine_lod as hl  # noqa: E402

ART = os.path.join(ROOT, "godot", "art", "armor")
PEOPLE = os.path.join(ROOT, "godot", "art", "people")
CALLINGS = ("warden", "arcanist", "ranger", "reaver")
UNDER = ("pauldrons",)
REACH = 0.04          # (m out along the strap's normal)
INSET = 0.005         # (m in from the covered region's edge)
THICK = 0.003         # (m: a strap's thickness and its rolled edge)
LEATHER = ("leather",)


def mats_kind():
    return {k: v.get("kind") for k, v in json.load(open(os.path.join(PEOPLE, "outfit_materials.json"), encoding="utf-8")).items()}


def covers(slot):
    """Each calling's piece of `slot` as triangles (n, 3, 3), bind space."""
    out = []
    for c in CALLINGS:
        f = os.path.join(PEOPLE, f"heroine_outfit_{c}.gltf")
        if not os.path.exists(f):
            continue
        g = hl.Gltf(f)
        tris = []
        for i, m in enumerate(g.js["meshes"]):
            if not m["name"].startswith(f"{c}.{slot}."):
                continue
            for _, at, T in g.prims(i):
                P = at["POSITION"][0].astype(float)
                tris.append(P[T])
        if tris:
            out.append((c, np.concatenate(tris)))
    return out


def ray_hits(O, D, tri, reach):
    """Whether each ray (O + t D, 0 < t < reach) meets any of the triangles (Moller-Trumbore, in chunks)."""
    hit = np.zeros(len(O), bool)
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    lo, hi = tri.min(1), tri.max(1)
    for a in range(0, len(O), 256):
        o, d = O[a:a + 256], D[a:a + 256]
        # (only triangles in the rays' reach box)
        bl, bh = np.minimum(o, o + d * reach).min(0) - 1e-3, np.maximum(o, o + d * reach).max(0) + 1e-3
        k = np.nonzero(((hi >= bl) & (lo <= bh)).all(1))[0]
        if not len(k):
            continue
        p = np.cross(d[:, None], e2[k][None])
        det = (e1[k][None] * p).sum(2)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = o[:, None] - v0[k][None]
        u = (s * p).sum(2) * inv
        q = np.cross(s, e1[k][None])
        v = (d[:, None] * q).sum(2) * inv
        t = (e2[k][None] * q).sum(2) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < reach)
        hit[a:a + 256] = h.any(1)
    return hit


def hidden_keys(P, N, T, slot_covers):
    """The vertices a slot's pieces all cover, INSET in from the covered region's edge: their keys and count."""
    cov = np.ones(len(P), bool)
    for _, tri in slot_covers:
        # (out along its normal, or back along it: a strap's inner face looks at her, its pauldron is behind it)
        cov &= ray_hits(P + N * 0.0003, N, tri, REACH) | ray_hits(P - N * 0.0003, -N, tri, REACH)
    # (and across the strap's thickness: its side walls look sideways, past the pauldron; a point within THICK of a
    # covered one is covered)
    if cov.any():
        cov = cKDTree(P[cov]).query(P, distance_upper_bound=THICK)[0] < np.inf
    if not cov.any() or cov.all():
        return np.zeros((0, 3), np.int64), cov, cov
    # (the edge: distance from each covered vertex to the nearest uncovered one, over this mesh's points)
    d = cKDTree(P[~cov]).query(P[cov])[0]
    hid = cov.copy()
    hid[cov] = d >= INSET
    return np.unique(np.round(P[hid].astype(np.float64) * 1e5).astype(np.int64), axis=0), cov, hid


def run(pid):
    f = os.path.join(ART, pid + ".gltf")
    g = hl.Gltf(f)
    kinds = mats_kind()
    ix_path = os.path.join(ART, "armor_index.json")
    rows = json.load(open(ix_path, encoding="utf-8"))
    row = next(r for r in rows if r["id"] == pid)
    under, nums = {}, {}
    os.makedirs(os.path.join(ART, "armor_under"), exist_ok=True)
    for slot in UNDER:
        if slot == row.get("slot"):
            continue
        sc = covers(slot)
        if not sc:
            continue
        # (each known piece of the slot its own cut, by its id (<calling>.<slot>); "*": what every one of them covers,
        # for any other piece in that slot)
        sets = [(f"{c}.{slot}", [(c, tri)]) for c, tri in sc] + [("*", sc)]
        files = {}
        for key, cs in sets:
            keys = []
            for i, m in enumerate(g.js["meshes"]):
                for mat, at, T in g.prims(i):
                    if not any(kinds.get(mat, "") == k for k in LEATHER) or "NORMAL" not in at:
                        continue
                    P, N = at["POSITION"][0].astype(float), at["NORMAL"][0].astype(float)
                    k, cov, hid = hidden_keys(P, N, T, cs)
                    nums[f"{key} {m['name']}"] = {"covered": int(cov.sum()), "hidden": int(hid.sum()), "tris_dropped": int(hid[T].all(1).sum())}
                    if len(k):
                        keys.append(k)
            keys = np.unique(np.concatenate(keys), axis=0) if keys else np.zeros((0, 3), np.int64)
            name = f"armor_under/{pid}.{slot}.{'any' if key == '*' else key.split('.')[0]}.bin"
            out = os.path.join(ART, name)
            if len(keys):
                open(out, "wb").write(struct.pack("<I", len(keys)) + keys.astype("<i4").tobytes())
                files[key] = name
            elif os.path.exists(out):
                os.remove(out)
        if files:
            under[slot] = files
    if under:
        row["under"] = under
    else:
        row.pop("under", None)
    json.dump(rows, open(ix_path, "w", encoding="utf-8"), indent=1)
    print("UNDER %s %s" % (pid, json.dumps({"under": under, **nums})))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        run(a)
