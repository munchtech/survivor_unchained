"""Carry morph targets from one heroine glb to another whose topology differs.

    python tools/assets/carry_targets.py SRC_GLB DST_GLB OUT_GLB [--targets elbow_point_l,elbow_point_r]

For each named target on SRC, every DST primitive whose material is also on a SRC primitive carrying
it gets the target: each DST point takes the delta (position and, if SRC has them, normal) interpolated
barycentrically at the closest point of SRC's same-material surface in bind space. Points more than
--reach (2 mm) from that surface get delta 0 and are counted. DST primitives of other materials get
an all-zero target (a mesh's primitives must share the target list). Everything else in DST is kept
byte for byte: the new data is appended to the bin; json gains only the new accessors, bufferViews,
primitive targets, mesh targetNames (and weights, if the mesh has them) and the asset mark
`carried_targets`. A target DST already has is skipped.
"""
import argparse
import json
import struct

import numpy as np
from scipy.spatial import cKDTree

CT = {5120: "i1", 5121: "u1", 5122: "i2", 5123: "u2", 5125: "u4", 5126: "<f4"}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class Glb:
    def __init__(s, path):
        d = open(path, "rb").read()
        jl = struct.unpack("<I", d[12:16])[0]
        s.g = json.loads(d[20:20 + jl])
        bl = struct.unpack("<I", d[20 + jl:24 + jl])[0]
        s.bin = bytearray(d[28 + jl:28 + jl + bl])
        assert len(d) == 28 + jl + bl, "trailing chunks"

    def get(s, ai):
        a = s.g["accessors"][ai]
        n, dt = NC[a["type"]], np.dtype(CT[a["componentType"]])
        out = np.zeros((a["count"], n), dt)
        if "bufferView" in a:
            bv = s.g["bufferViews"][a["bufferView"]]
            off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            st = bv.get("byteStride") or dt.itemsize * n
            raw = np.frombuffer(bytes(s.bin[off:off + st * (a["count"] - 1) + dt.itemsize * n]), np.uint8)
            rows = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * n), (st, 1))
            out = np.ascontiguousarray(rows).view(dt).reshape(a["count"], n).copy()
        sp = a.get("sparse")
        if sp:
            ib, vb = sp["indices"], sp["values"]
            idt = np.dtype(CT[ib["componentType"]])
            bv = s.g["bufferViews"][ib["bufferView"]]
            o = bv.get("byteOffset", 0) + ib.get("byteOffset", 0)
            idx = np.frombuffer(bytes(s.bin[o:o + idt.itemsize * sp["count"]]), idt)
            bv = s.g["bufferViews"][vb["bufferView"]]
            o = bv.get("byteOffset", 0) + vb.get("byteOffset", 0)
            val = np.frombuffer(bytes(s.bin[o:o + dt.itemsize * n * sp["count"]]), dt).reshape(-1, n)
            out[idx.astype(np.int64)] = val
        return out

    def add(s, arr, mm=False):
        """Append float32 data as a new bufferView + accessor; returns its index."""
        arr = np.ascontiguousarray(arr, "<f4")
        while len(s.bin) % 4:
            s.bin.append(0)
        s.g["bufferViews"].append({"buffer": 0, "byteOffset": len(s.bin), "byteLength": arr.nbytes})
        s.bin += arr.tobytes()
        a = {"bufferView": len(s.g["bufferViews"]) - 1, "componentType": 5126, "count": len(arr), "type": "VEC3"}
        if mm:
            a["max"], a["min"] = arr.max(0).tolist(), arr.min(0).tolist()
        s.g["accessors"].append(a)
        return len(s.g["accessors"]) - 1

    def save(s, path):
        while len(s.bin) % 4:
            s.bin.append(0)
        s.g["buffers"][0]["byteLength"] = len(s.bin)
        j = json.dumps(s.g, separators=(",", ":")).encode()
        j += b" " * (-len(j) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(s.bin)))
            f.write(struct.pack("<II", len(j), 0x4E4F534A) + j)
            f.write(struct.pack("<II", len(s.bin), 0x004E4942) + bytes(s.bin))


def closest(P, V, F, k=16):
    """Closest point on triangle soup (V, F) for each row of P: (dist, face, barycentric [n, 3])."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    cand = cKDTree((A + B + C) / 3).query(P, k=min(k, len(F)))[1]
    best_d = np.full(len(P), np.inf)
    best_f = np.zeros(len(P), np.int64)
    best_w = np.zeros((len(P), 3))
    for c in range(cand.shape[1]):
        f = cand[:, c]
        a, b, cc = A[f], B[f], C[f]
        n = np.cross(b - a, cc - a)
        nn = np.maximum((n * n).sum(1), 1e-30)
        q = P - a
        # barycentrics of the plane projection
        v = (np.cross(q, cc - a) * n).sum(1) / nn
        w = (np.cross(b - a, q) * n).sum(1) / nn
        W = np.stack([1 - v - w, v, w], 1)
        bad = (W < 0).any(1)
        if bad.any():
            Pb, Q = P[bad], [a[bad], b[bad], cc[bad]]
            bd = np.full(len(Pb), np.inf)
            bw = np.zeros((len(Pb), 3))
            for (i, j) in ((0, 1), (1, 2), (0, 2)):
                e = Q[j] - Q[i]
                t = np.clip(((Pb - Q[i]) * e).sum(1) / np.maximum((e * e).sum(1), 1e-30), 0, 1)
                d = np.linalg.norm(Pb - (Q[i] + e * t[:, None]), axis=1)
                w3 = np.zeros((len(Pb), 3))
                w3[:, i], w3[:, j] = 1 - t, t
                m = d < bd
                bd[m], bw[m] = d[m], w3[m]
            W[bad] = bw
        X = W[:, 0:1] * a + W[:, 1:2] * b + W[:, 2:3] * cc
        d = np.linalg.norm(P - X, axis=1)
        m = d < best_d
        best_d[m], best_f[m], best_w[m] = d[m], f[m], W[m]
    return best_d, best_f, best_w


def faces(g, prim):
    if "indices" in prim:
        return g.get(prim["indices"]).reshape(-1, 3).astype(np.int64)
    n = g.g["accessors"][prim["attributes"]["POSITION"]]["count"]
    return np.arange(n).reshape(-1, 3)


def nz(X):
    return int((np.linalg.norm(X, axis=1) > 1e-7).sum())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("out")
    ap.add_argument("--targets", default="elbow_point_l,elbow_point_r")
    ap.add_argument("--reach", type=float, default=0.002, help="metres")
    a = ap.parse_args(argv)
    want = [t for t in a.targets.split(",") if t]
    S, D = Glb(a.src), Glb(a.dst)

    def mat(g, p):
        return g.g["materials"][p["material"]]["name"]

    report, carried, zeros = [], [], {}
    for t in want:
        src = {}
        for m in S.g["meshes"]:
            names = m.get("extras", {}).get("targetNames", [])
            if t in names:
                for p in m["primitives"]:
                    src.setdefault(mat(S, p), (p, names.index(t)))
        if not src:
            print(f"{t}: not on SRC")
            continue
        for m in D.g["meshes"]:
            names = m.get("extras", {}).get("targetNames")
            if names is None or not any(mat(D, p) in src for p in m["primitives"]):
                continue
            if t in names:
                print(f"{t}: DST {m.get('name')} already has it, skipped")
                continue
            for p in m["primitives"]:
                mt = mat(D, p)
                n = D.g["accessors"][p["attributes"]["POSITION"]]["count"]
                if mt not in src:
                    if n not in zeros:
                        zeros[n] = D.add(np.zeros((n, 3)), mm=True)
                    p.setdefault("targets", []).append({"POSITION": zeros[n], "NORMAL": zeros[n]})
                    continue
                sp, ti = src[mt]
                st = sp["targets"][ti]
                SV = S.get(sp["attributes"]["POSITION"]).astype(float)
                SF = faces(S, sp)
                SD = S.get(st["POSITION"]).astype(float)
                SN = S.get(st["NORMAL"]).astype(float) if "NORMAL" in st else None
                P = D.get(p["attributes"]["POSITION"]).astype(float)
                dist, f, w = closest(P, SV, SF)
                ok = dist <= a.reach
                tri = SF[f]

                def lerp(X):
                    return (X[tri] * w[:, :, None]).sum(1) * ok[:, None]

                dp = lerp(SD)
                dn = lerp(SN) if SN is not None else np.zeros_like(dp)
                p.setdefault("targets", []).append({"POSITION": D.add(dp, mm=True), "NORMAL": D.add(dn)})
                mag = np.linalg.norm(dp, axis=1)
                report.append(dict(
                    target=t, mesh=m.get("name"), material=mt, points=n,
                    src_nonzero=nz(SD), out_nonzero=nz(dp),
                    src_max_mm=round(float(np.linalg.norm(SD, axis=1).max() * 1000), 3),
                    out_max_mm=round(float(mag.max() * 1000), 3),
                    match_max_mm=round(float(dist.max() * 1000), 3),
                    match_max_where_delta_mm=round(float(dist[mag > 1e-7].max() * 1000), 3) if (mag > 1e-7).any() else 0.0,
                    far=int((~ok).sum())))
            names.append(t)
            if "weights" in m:
                m["weights"].append(0.0)
            carried.append(t)
    if carried:
        ex = D.g["asset"].setdefault("extras", {})
        ex["carried_targets"] = {"targets": carried, "reach_mm": a.reach * 1000}
    D.save(a.out)
    for r in report:
        print(r)
    return report


if __name__ == "__main__":
    main()
