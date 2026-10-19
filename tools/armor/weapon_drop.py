"""Drop a new weapon of a known kind into the game as DATA (docs/anim/GRIP_STANDARD.md sections 2-4).

    python tools/armor/weapon_drop.py <file.glb> --id <id> [--no-copy]

Checks the .glb: an anchor_grip and an anchor_sheath node, a kind (a node extra "kind", or a node kind_<kind>) that
is a known one, the grip's section against tools/anim/data/grip_spec.json "types" for the kind (the grip point's band,
"length" mm long and "grip_from_guard" mm below the guard, less 2 mm at each end, cut into 8 rings; each ring's radius within 0.3 mm of the
spec's). Then copies it to public/assets/weapons/<id>.glb and writes godot/art/weapons/weapons.json's row
(Arms.All merges it: godot/src/Actors/ArmsData.cs). Exit 0 on a clean pass, 1 on any failure.
Units: the glb is at life size, in metres (Arms.Make scales its long extent along the anchor's Y to "length").
The anchor frame: origin the grip point, -Y down the shaft to the tip, +Z the edge/face direction. For a flat type the
width is taken along the anchor's Z (the edge), the depth along its X.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "tools" / "anim" / "data" / "grip_spec.json"
WEAPONS = ROOT / "public" / "assets" / "weapons"
ROWS = ROOT / "godot" / "art" / "weapons" / "weapons.json"
KINDS = ["blade1h", "blade2h", "blunt", "axe", "axe2h", "dagger", "wand", "staff", "shield", "crossbow"]
TOL = 0.3
MARGIN = 2.0   # mm off each end of the band (grip_conform's margin): a guard's or pommel's lip shares the band's last slice
RINGS = 8
CT = {5126: ("f", 4), 5123: ("H", 2), 5125: ("I", 4), 5121: ("B", 1), 5120: ("b", 1), 5122: ("h", 2)}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path):
    b = Path(path).read_bytes()
    if b[:4] != b"glTF":
        raise SystemExit("FAIL: not a .glb")
    pos, js, bin_ = 12, None, b""
    while pos < len(b):
        n, t = struct.unpack("<II", b[pos:pos + 8])
        chunk = b[pos + 8:pos + 8 + n]
        if t == 0x4E4F534A:
            js = json.loads(chunk)
        elif t == 0x004E4942:
            bin_ = chunk
        pos += 8 + n
    return js, bin_


def accessor(js, bin_, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    fmt, sz = CT[a["componentType"]]
    nc = NC[a["type"]]
    stride = bv.get("byteStride") or sz * nc
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    out = np.empty((a["count"], nc))
    for k in range(a["count"]):
        out[k] = struct.unpack_from("<" + fmt * nc, bin_, base + k * stride)
    return out


def local_matrix(n):
    if "matrix" in n:
        return np.array(n["matrix"], float).reshape(4, 4).T
    M = np.eye(4)
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M[:3, :3] = R * np.array(n.get("scale", [1, 1, 1]))
    M[:3, 3] = n.get("translation", [0, 0, 0])
    return M


def world(js):
    N = js["nodes"]
    W = [None] * len(N)

    def go(i, P):
        W[i] = P @ local_matrix(N[i])
        for c in N[i].get("children", []):
            go(c, W[i])
    roots = set(range(len(N))) - {c for n in N for c in n.get("children", [])}
    for s in js.get("scenes", []):
        roots |= set(s.get("nodes", []))
    for r in sorted(roots):
        if W[r] is None:
            go(r, np.eye(4))
    return W


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--id", required=True)
    ap.add_argument("--no-copy", action="store_true")
    a = ap.parse_args(argv)
    fails = []
    js, bin_ = read_glb(a.glb)
    N = js["nodes"]
    W = world(js)

    def name(i):
        return N[i].get("name", "")
    ag = [i for i in range(len(N)) if name(i).startswith("anchor_grip")]
    asx = [i for i in range(len(N)) if name(i).startswith("anchor_sheath")]
    if not ag:
        fails.append("no anchor_grip node")
    if not asx:
        fails.append("no anchor_sheath node")
    kinds = {str(n["extras"]["kind"]).lower() for n in N if isinstance(n.get("extras"), dict) and "kind" in n["extras"]}
    kinds |= {name(i).lower()[5:] for i in range(len(N)) if name(i).lower().startswith("kind_")}
    if not kinds:
        fails.append("no kind (a node extra kind, or a node kind_<kind>)")
    elif len(kinds) > 1:
        fails.append(f"kind tags disagree: {sorted(kinds)}")
    kind = sorted(kinds)[0] if kinds else None
    if kind and kind not in KINDS:
        fails.append(f"unknown kind '{kind}' (known: {' '.join(KINDS)})")
    spec = json.loads(SPEC.read_text())
    ty = next(((k, t) for k, t in spec["types"].items() if kind and any(kind == q.lower() for q in t["kinds"])), None)
    pts = []
    for i, n in enumerate(N):
        if "mesh" in n:
            for p in js["meshes"][n["mesh"]]["primitives"]:
                V = accessor(js, bin_, p["attributes"]["POSITION"])
                pts.append(V @ W[i][:3, :3].T + W[i][:3, 3])
    if not pts:
        fails.append("no mesh")
    length = grip = None
    if ag and pts:
        P = np.concatenate(pts)
        M = W[ag[0]]
        G = M[:3, 3]
        D = -M[:3, 1] / np.linalg.norm(M[:3, 1])
        X = M[:3, 0] / np.linalg.norm(M[:3, 0])
        Z = M[:3, 2] / np.linalg.norm(M[:3, 2])
        t = (P - G) @ D
        length = float(t.max() - t.min())
        grip = float(-t.min() / length)
        if ty is None:
            if kind in KINDS:
                print(f"note: no grip section in grip_spec.json for kind '{kind}': grip not measured")
        else:
            nm, T = ty
            s = T["section"]
            gl = T["length"]
            gg = T.get("grip_from_guard")
            if gg is None:
                fails.append(f"grip_spec type {nm} has no grip_from_guard")
            else:
                t0, t1 = -(gl - gg - MARGIN) / 1000, (gg - MARGIN) / 1000      # metres along D from the grip point (the guard at +t, toward the tip)
                edges = np.linspace(t0, t1, RINGS + 1)
                for r in range(RINGS):
                    sel = (t > edges[r]) & (t < edges[r + 1])
                    if sel.sum() < 3:
                        fails.append(f"ring {r + 1}: {int(sel.sum())} vertices in {1000 * edges[r]:.1f}..{1000 * edges[r + 1]:.1f} mm")
                        continue
                    Q = P[sel] - G - np.outer(t[sel], D)
                    if s["shape"] == "round":
                        rad = float(np.linalg.norm(Q, axis=1).max() * 1000)
                        bad = abs(rad - s["half_w"]) > TOL
                        want, got = f"{s['half_w']:.2f}", f"{rad:.2f}"
                    else:
                        hw = float(np.abs(Q @ Z).max() * 1000)
                        hd = float(np.abs(Q @ X).max() * 1000)
                        bad = abs(hw - s["half_w"]) > TOL or abs(hd - s["half_d"]) > TOL
                        want, got = f"{s['half_w']:.2f}x{s['half_d']:.2f}", f"{hw:.2f}x{hd:.2f}"
                    print(f"  ring {r + 1}: t {1000 * edges[r]:7.1f}..{1000 * edges[r + 1]:6.1f} mm  {got}  spec {want}  {'FAIL' if bad else 'ok'}")
                    if bad:
                        fails.append(f"ring {r + 1}: {got} vs spec {want} (> {TOL} mm)")
    if fails:
        print(f"FAIL {a.id}: " + "; ".join(fails))
        return 1
    row = {"file": a.id, "length": round(length, 3), "kind": kind, "node": None, "pistol": kind == "crossbow", "lean": None, "grip": round(grip, 3)}
    if not a.no_copy:
        WEAPONS.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a.glb, WEAPONS / f"{a.id}.glb")
        txt = ROWS.read_text() if ROWS.exists() else ""
        rows = json.loads(txt) if txt.strip() else {}
        rows[a.id] = row
        ROWS.parent.mkdir(parents=True, exist_ok=True)
        ROWS.write_text(json.dumps(rows, indent=1) + "\n")
    where = f"copied to public/assets/weapons/{a.id}.glb, row in godot/art/weapons/weapons.json" if not a.no_copy else "not copied"
    print(f"OK {a.id}: kind {kind}, length {row['length']} m, grip {row['grip']} from the butt, section type {ty[0] if ty else '-'}, {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
