"""Shrink a .gltf/.bin pair (or .glb) without changing what the game shows.

  python tools/assets/gltf_compact.py FILE.gltf [FILE2 ...] [--pos-min 1e-4] [--nor-min 0.01] [--dry]

Three things, each lossless at the game's cameras:
  1. buffer views no accessor or image points at (old targets a post step replaced) are dropped and the rest repacked;
  2. JOINTS_1/WEIGHTS_1 are dropped from primitives whose WEIGHTS_1 is all zero (the 8-weight pair only matters
     where a helper joint has weight; Godot sets 8 bone weights per surface);
  3. sparse morph-target entries below --pos-min metres (POSITION) or --nor-min (NORMAL, unit-vector delta) are
     dropped: the follow's fade writes every point it touches, most of them by a hundredth of a millimetre.
     Dense targets are left as they are.
Body 15, 27 Oct: heroine_outfit_warden.bin was 115 MB (GitHub's cap is 100 MB) after body_follow_post's 18 shapes.
"""
import json
import os
import sys

import numpy as np

# GitHub refuses files over 100 MiB; any file this writes over CAP_MIB fails loudly (main, 27 Oct: the warden outfit
# sat at 89 MiB after compaction, so the next outfit change must not slip past the cap unseen). Fallback if one goes
# over: BF_PAUL_SHAPES=0 drops the shoulder shapes on the rigid plate shells (warden: -19 MB).
CAP_MIB = float(os.environ.get("GLTF_CAP_MIB", 90))

DT = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5122: "<i2", 5121: "u1", 5120: "i1"}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _load(path):
    if path.endswith(".glb"):
        d = open(path, "rb").read()
        jl = int.from_bytes(d[12:16], "little")
        g = json.loads(d[20:20 + jl])
        bl = int.from_bytes(d[20 + jl:24 + jl], "little")
        return g, d[28 + jl:28 + jl + bl], None
    g = json.load(open(path, encoding="utf-8"))
    bp = os.path.join(os.path.dirname(path), g["buffers"][0]["uri"])
    return g, open(bp, "rb").read(), bp


def _view(g, buf, bv, dt, n, off=0):
    v = g["bufferViews"][bv]
    o = v.get("byteOffset", 0) + off
    return np.frombuffer(buf, dt, n, o)


def compact(path, pos_min=1e-4, nor_min=0.01, dry=False):
    g, buf, bin_path = _load(path)
    assert len(g.get("buffers", [])) == 1, "one buffer only"
    A = g["accessors"]
    before = len(buf)
    new_views = []          # (bytes, extra keys)
    out = bytearray()
    remap = {}
    stats = {"w1_dropped": 0, "pos_kept": 0, "pos_all": 0, "nor_kept": 0, "nor_all": 0}
    replaced = {}           # accessor index -> new bytes for its sparse (indices, values)

    # 3. prune sparse targets
    for m in g.get("meshes", []):
        for p in m["primitives"]:
            for t in p.get("targets", []):
                for k, ai in t.items():
                    a = A[ai]
                    if "sparse" not in a or "bufferView" in a or k not in ("POSITION", "NORMAL"):
                        continue
                    s = a["sparse"]
                    n = s["count"]
                    idx = _view(g, buf, s["indices"]["bufferView"], DT[s["indices"]["componentType"]], n,
                                s["indices"].get("byteOffset", 0)).astype("<u4")
                    val = _view(g, buf, s["values"]["bufferView"], "<f4", n * 3,
                                s["values"].get("byteOffset", 0)).reshape(n, 3)
                    keep = np.linalg.norm(val, axis=1) >= (pos_min if k == "POSITION" else nor_min)
                    stats["pos_all" if k == "POSITION" else "nor_all"] += n
                    stats["pos_kept" if k == "POSITION" else "nor_kept"] += int(keep.sum())
                    idx, val = idx[keep], val[keep].astype("<f4")
                    if not len(idx):
                        idx, val = np.zeros(1, "<u4"), np.zeros((1, 3), "<f4")
                    replaced[ai] = (idx, val)
            # 2. all-zero second weight set
            at = p["attributes"]
            if "WEIGHTS_1" in at and "JOINTS_1" in at:
                a = A[at["WEIGHTS_1"]]
                if "bufferView" in a:
                    W = _view(g, buf, a["bufferView"], DT[a["componentType"]], a["count"] * 4, a.get("byteOffset", 0))
                    if not W.any():
                        del at["WEIGHTS_1"], at["JOINTS_1"]
                        stats["w1_dropped"] += 1

    # 1. repack: walk every live reference
    def add(data):
        while len(out) % 4:
            out.append(0)
        o = len(out)
        out.extend(data)
        new_views.append({"buffer": 0, "byteOffset": o, "byteLength": len(data)})
        return len(new_views) - 1

    def keep_view(bv):
        if bv not in remap:
            v = dict(g["bufferViews"][bv])
            o = v.get("byteOffset", 0)
            nv = add(buf[o:o + v["byteLength"]])
            for key in ("byteStride", "target", "name"):
                if key in v:
                    new_views[nv][key] = v[key]
            remap[bv] = nv
        return remap[bv]

    live = set()
    for m in g.get("meshes", []):
        for p in m["primitives"]:
            live.update(p["attributes"].values())
            if "indices" in p:
                live.add(p["indices"])
            for t in p.get("targets", []):
                live.update(t.values())
    for sk in g.get("skins", []):
        if "inverseBindMatrices" in sk:
            live.add(sk["inverseBindMatrices"])
    for an in g.get("animations", []):
        for sm in an.get("samplers", []):
            live.update((sm["input"], sm["output"]))
    for ai in sorted(live):
        a = A[ai]
        if ai in replaced:
            idx, val = replaced[ai]
            a["sparse"] = {"count": int(len(idx)),
                           "indices": {"bufferView": add(idx.tobytes()), "componentType": 5125},
                           "values": {"bufferView": add(val.tobytes())}}
            a["min"] = [float(x) for x in np.minimum(val.min(0), 0)]
            a["max"] = [float(x) for x in np.maximum(val.max(0), 0)]
            continue
        if "bufferView" in a:
            a["bufferView"] = keep_view(a["bufferView"])
        if "sparse" in a:
            a["sparse"]["indices"]["bufferView"] = keep_view(a["sparse"]["indices"]["bufferView"])
            a["sparse"]["values"]["bufferView"] = keep_view(a["sparse"]["values"]["bufferView"])
    for im in g.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = keep_view(im["bufferView"])
    # accessors nobody references keep their entries (indices stay stable) but lose their data
    for ai, a in enumerate(A):
        if ai not in live and ("bufferView" in a or "sparse" in a):
            a.pop("bufferView", None)
            a.pop("byteOffset", None)
            a.pop("sparse", None)
    while len(out) % 4:
        out.append(0)
    g["bufferViews"] = new_views
    g["buffers"][0]["byteLength"] = len(out)
    stats.update(before=before, after=len(out))
    if not dry:
        if bin_path:
            # (the data's checksum in the .gltf as heroine_neck._Gl writes it, so Godot reimports; the file's layout kept)
            import hashlib
            open(bin_path, "wb").write(bytes(out))
            txt = open(path, encoding="utf-8").read()
            if "data" in g["asset"].get("extras", {}):
                g["asset"]["extras"]["data"] = hashlib.md5(bytes(out)).hexdigest()
            if txt.startswith("{\n\t"):
                js = json.dumps(g, indent="\t", separators=(",", ":"), ensure_ascii=False)
            elif txt.startswith("{\n"):
                js = json.dumps(g, indent=1, ensure_ascii=False)
            else:
                js = json.dumps(g, separators=(",", ":"), ensure_ascii=False)
            open(path, "w", encoding="utf-8", newline="\n").write(js + ("\n" if txt.endswith("\n") else ""))
        else:
            js = json.dumps(g, separators=(",", ":")).encode()
            js += b" " * (-len(js) % 4)
            tot = 12 + 8 + len(js) + 8 + len(out)
            with open(path, "wb") as f:
                f.write(b"glTF" + (2).to_bytes(4, "little") + tot.to_bytes(4, "little"))
                f.write(len(js).to_bytes(4, "little") + b"JSON" + js)
                f.write(len(out).to_bytes(4, "little") + b"BIN\x00" + bytes(out))
    if len(out) > CAP_MIB * 2 ** 20:
        raise SystemExit("COMPACT FAIL %s: %.1f MiB over the %.0f MiB cap (GitHub refuses 100 MiB; see CAP_MIB's note)"
                         % (path, len(out) / 2 ** 20, CAP_MIB))
    return stats


def main(argv):
    pos_min, nor_min, dry, files = 1e-4, 0.01, False, []
    it = iter(argv)
    for a in it:
        if a == "--pos-min":
            pos_min = float(next(it))
        elif a == "--nor-min":
            nor_min = float(next(it))
        elif a == "--dry":
            dry = True
        else:
            files.append(a)
    for f in files:
        s = compact(f, pos_min, nor_min, dry)
        print("COMPACT %-40s %6.1f -> %6.1f MB; W1 dropped on %d prims; pos entries %d -> %d, normal %d -> %d"
              % (os.path.basename(f), s["before"] / 1e6, s["after"] / 1e6, s["w1_dropped"],
                 s["pos_all"], s["pos_kept"], s["nor_all"], s["nor_kept"]))


if __name__ == "__main__":
    main(sys.argv[1:])
