"""A weapon's grip thinned in its glb, nothing else touched: the grip's rings drawn in toward its axis.

    python tools/assets/grip_thin.py chevalier_sword --radius 15.0 [--dry]

Each grip ring's radius r becomes r0 + (r - r0) * k about the grip's axis, r0 the ring at the pommel end (kept, so the
grip still meets the pommel's neck as it did), k such that the widest ring comes to --radius (mm, in life: the piece as
Arms.cs scales it, Spec.Length over the mesh's length). So the barrel keeps its swell, smaller; the guard, the
ferrule (the collar under the guard), the pommel and the blade are untouched, the texture (the leather wrap is painted
in the base colour) rides on the same UVs, and the normals are carried through the same map (their radial part over
k, their part round the axis over the ring's own scale). Only the POSITION and NORMAL floats change (every other byte
stays), the accessor's min/max rewritten. Every run starts from the original as it came (git, the commit named per
piece: src), so --radius can be re-chosen.

Pieces (mesh space, as the file has it): the long axis, the grip's ring range along it, and the end ring kept.
chevalier_sword (WE-01, rubenve, CC-BY-4.0): a barrel grip 37 mm across at its widest (18.5 mm round), too thick for
her fist to close on (fistfit.py: no fit passes; a real one-handed grip is 28-32 mm across). Thinned to 15 mm,
14 October 2026, then to 13.7 mm (--radius 13.7: the staff's shaft size; the pommel-end ring is 13.68, so
the grip comes out near a cylinder) (docs/legal/ASSET_PROVENANCE.md, WE-01).
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WEAPONS = ROOT / "public" / "assets" / "weapons"

# axis: the mesh axis the piece runs along; zs: the grip's rings (mesh units along it, exclusive), r_min: rings at
# least this far out (mesh units: the ferrule's inner ring at the grip's top shares its height); life: Spec.Length
# (m) the game scales the mesh's length to.
PIECES = {"chevalier_sword": dict(axis=2, zs=(-0.8700, -0.6240), r_min=0.0300, life=1.0, src="a4df6f89")}


def read_glb(rev, path):
    b = bytearray(subprocess.run(["git", "show", f"{rev}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT,
                                 capture_output=True, check=True).stdout)
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    return b, js, 20 + jl + 8


def view(b, js, bin0, acc):
    a = js["accessors"][acc]; bv = js["bufferViews"][a["bufferView"]]
    assert a["componentType"] == 5126 and a["type"] == "VEC3" and bv.get("byteStride", 12) == 12
    off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return off, np.frombuffer(bytes(b[off:off + a["count"] * 12]), "<f4").reshape(-1, 3).astype(float)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", choices=sorted(PIECES))
    ap.add_argument("--radius", type=float, required=True, help="the widest ring's radius after (mm, in life)")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    cfg = PIECES[a.piece]; path = WEAPONS / f"{a.piece}.glb"
    b, js, bin0 = read_glb(cfg["src"], path)
    prim = js["meshes"][0]["primitives"][0]; assert len(js["meshes"]) == 1 and len(js["meshes"][0]["primitives"]) == 1
    po, V = view(b, js, bin0, prim["attributes"]["POSITION"])
    no, N = view(b, js, bin0, prim["attributes"]["NORMAL"])
    ax = cfg["axis"]; ac = [i for i in range(3) if i != ax]
    life = cfg["life"] / (V[:, ax].max() - V[:, ax].min())     # m per mesh unit
    z = V[:, ax]
    band = (z > cfg["zs"][0]) & (z < cfg["zs"][1])
    # The axis: the centre of the band's rings (least squares circle over all of them).
    P = V[band][:, ac]
    M = np.c_[2 * P, np.ones(len(P))]; sol = np.linalg.lstsq(M, (P ** 2).sum(1), rcond=None)[0]
    c = sol[:2]
    rho = V[:, ac] - c; r = np.linalg.norm(rho, axis=1)
    grip = band & (r >= cfg["r_min"])
    # The pommel end's ring (kept): the grip's band edge, just below it.
    end = (z > cfg["zs"][0] - 0.005) & (z <= cfg["zs"][0]) & (r >= 0.026)
    r0 = r[end].max(); rmax = r[grip].max()
    k = (a.radius / 1000 / life - r0) / (rmax - r0)
    assert 0 < k <= 1, k
    rn = r0 + (r - r0) * k
    s = np.where(grip, rn / r, 1.0)
    V2 = V.copy(); V2[:, ac] = c + rho * s[:, None]
    # Normals: (radial / k, round / ring scale, axial), then unit length.
    N2 = N.copy()
    rh = rho / np.maximum(r, 1e-9)[:, None]; th = np.c_[-rh[:, 1], rh[:, 0]]
    nr = (N[:, ac] * rh).sum(1); nt = (N[:, ac] * th).sum(1)
    nr2 = nr / k; nt2 = nt / s
    N2[:, ac] = np.where(grip[:, None], rh * nr2[:, None] + th * nt2[:, None], N[:, ac])
    N2[grip] /= np.linalg.norm(N2[grip], axis=1, keepdims=True)   # only the grip's: the rest stay bit for bit
    rings = sorted({round(float(v), 4) for v in z[grip]})
    print(f"{a.piece}: {life * 1000:.2f} mm per mesh unit; axis at {np.round(c, 5).tolist()}; {grip.sum()} grip vertices in "
          f"{len(rings)} rings; pommel-end ring {r0 * life * 1000:.2f} mm kept; k {k:.3f}")
    for zz in rings:
        m = grip & (np.round(z, 4) == zz)
        print(f"  ring {zz:+.4f} ({(zz - V[:, ax].min()) * life * 1000:5.1f} mm from the butt): "
              f"{r[m].max() * life * 1000:5.2f} -> {rn[m].max() * life * 1000:5.2f} mm")
    if a.dry:
        return
    b[po:po + V2.size * 4] = V2.astype("<f4").tobytes()
    b[no:no + N2.size * 4] = N2.astype("<f4").tobytes()
    acc = js["accessors"][prim["attributes"]["POSITION"]]
    acc["min"] = V2.astype("<f4").min(0).astype(float).tolist(); acc["max"] = V2.astype("<f4").max(0).astype(float).tolist()
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    out = bytearray(b[:12]) + struct.pack("<I4s", len(jb), b"JSON") + jb + b[bin0 - 8:]
    out[8:12] = struct.pack("<I", len(out))
    path.write_bytes(bytes(out))
    print(f"written {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
