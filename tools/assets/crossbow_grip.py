"""The crossbow's pistol grip (the owner, 14 October, "the crossbow hold", (a)): a wooden grip under the stock, behind
the lever trigger, raked back RAKE degrees, round to the Crossbow type's grip (data/grip_spec.json, 13.7 mm, as the
one-handed blade's), so her fist seats on it as on a sword (WeaponSockets.CrossbowAtR / CrossbowDirR, Arms.Seat's
pistol path). Modelled here in Blender (bpy, headless): a lathe, its profile below, then appended to the original
file as a second primitive of the stock's own mesh (its Wood material), so every other byte of the file stays as it
was (the stock, the bow, every other vertex, UV and texture).

    blender -b --factory-startup -P tools/assets/crossbow_grip.py -- [--src PATH] [--out PATH]

The grip, in the stock's own mesh space (file units, Y up, +Z toward the bow; 1 mm in life = 1 / MM units, the
stock's Arms.Spec length over the file's length along it):
  * its line meets the stock's underside JZ (file z) behind the lever's tail, so her forefinger sits between the two;
    from there it runs down and back, RAKE degrees off square to the stock (a pistol-grip crossbow's);
  * a round band (R mm) where the fist closes, a slight swell and a domed end below it (the pommel), a flare where
    it meets the stock (wide fore and aft, narrower across than the stock), buried BURY mm into it;
  * its UVs on a clean, uncut patch of the stock's own wood (PATCH, pixels of the 1024 albedo): the grain along the
    grip, half the round mirrored onto the other half at the grip's back and front (so the patch holds at the stock's
    own texel density), tangents as the file's (glTF: along +u, w by the +v side, checked on the stock's own: 100%);
  * an anchor_grip node (under the stock's node): its origin on the grip's line ANCHOR mm below the stock's
    underside (the fist's pocket), -Y along the stock toward the bow, +Z the stock's top. Arms.Make then lays the
    piece +Y along the stock, +Z up, the grip point at its origin; the grip's line in the piece is (0, sin RAKE,
    cos RAKE) (WeaponSockets.PistolRake).
Then fistfit (tools/anim/fistfit.py crossbow) is the numeric pass on her fist once the dump has re-read it.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "assets"))
from grip_conform import Glb, write_anchor  # noqa: E402

SRC = ROOT / "public" / "assets" / "weapons" / "crossbow.glb"
LENGTH = 0.693         # m: Arms.Spec crossbow Length, the stock's run (the size it had in the game while Arms.Make
                       # took its bow, 0.85 across, for its length: the anchor now says the stock is the shaft)
RAKE = 18.0            # deg: the grip's line off square to the stock, its foot toward the butt (WeaponSockets.PistolRake)
R = 13.7               # mm: the band's radius (grip_spec.json Crossbow, the one-handed blade's 13.7)
JZ = -0.478            # file z where the grip's line meets the stock's underside (the lever's tail ends at z -0.409)
ANCHOR = 62.0          # mm along the line below the underside: the grip point (the fist's pocket)
SHEATH = np.array([0.0, 0.02, 0.0])   # file: the sheath point, the stock's middle on its centre line
BURY = 12.0            # mm: the flare carried on into the stock
SEG = 36               # segments round
FLARE_X, FLARE_Z = 16.5, 24.0   # mm: the flare's half-width across (the stock is 19.2 each side) and fore and aft
# the albedo patch (pixels, 1024 square): clean grain, no worn edge, no lock-plate shadow
PATCH_U0, PATCH_V0 = 278.0, 70.0
DU_DY, DV_DZ = 0.82, 0.77   # the stock side's own texel density (UV per file unit: across, along; its +X island)


def profile():
    """(t mm along the line from the underside, + up into the stock; rx mm across; rz mm fore and aft)."""
    rows = []
    for k in range(7):                                  # the domed end: 10 mm tall, 14.9 round
        a = (k / 6) * (math.pi / 2)
        rows.append((-124.0 + 10.0 * (1 - math.cos(a)), 14.9 * math.sin(a)))
    for t in (-112.0, -109.0, -106.0, -103.0, -100.0):  # the pommel's swell easing into the band
        s = (t + 114.0) / 14.0
        rows.append((t, R + (14.9 - R) * 0.5 * (1 + math.cos(math.pi * s))))
    for t in np.arange(-96.0, -14.0 + 1e-6, 6.0):      # the band
        rows.append((float(t), R))
    out = [(t, r, r) for t, r in rows]
    for k in range(1, 8):                               # the flare: a fillet into the stock
        s = k / 7; t = -14.0 + 14.0 * s
        out.append((t, R + (FLARE_X - R) * s * s, R + (FLARE_Z - R) * s * s))
    out.append((BURY / 2, FLARE_X, FLARE_Z)); out.append((BURY, FLARE_X, FLARE_Z))
    return out


def stock_underside(z, V):
    """The stock's underside (file y) at z: the Wood mesh's lowest point near the middle there."""
    m = (np.abs(V[:, 2] - z) < 0.02) & (np.abs(V[:, 0]) < 0.02)
    if m.sum() < 2:   # long faces: the plane through its run (z -0.071 .. -0.68, measured)
        return -0.057 + (-0.071 - z) * (0.034 + 0.057) / (0.68 - 0.071)
    return float(V[m, 1].min())


def build(mm):
    """The lathe in Blender (bmesh): positions (file units), smooth normals, triangles, and per vertex its (t, theta)."""
    import bpy
    import bmesh
    a = math.radians(RAKE)
    g = np.array([0.0, math.cos(a), math.sin(a)])        # up the grip
    f = np.array([0.0, -math.sin(a), math.cos(a)])       # forward, square to it
    x = np.array([1.0, 0.0, 0.0])
    J = np.array([0.0, JY, JZ])
    prof = profile()
    bm = bmesh.new(); rings = []; meta = []
    bottom = bm.verts.new(tuple(J + prof[0][0] / mm * g)); meta.append((prof[0][0], 0.0))
    for t, rx, rz in prof[1:]:
        ring = []
        for k in range(SEG):
            th = 2 * math.pi * k / SEG
            d = -rz * math.cos(th)                       # mm fore (+) and aft of the line
            # the flare follows the stock's underside (it slopes 8.5 deg to the stock's run, 9.5 to the grip's
            # square): its rings tilted onto that plane, eased in from the band (else a lip shows at the front)
            w = 0.0 if t <= -14.0 else min(1.0, ((t + 14.0) / 14.0) ** 2)
            p = J + (t + w * TILT * d) / mm * g + (d * f + rx * math.sin(th) * x) / mm
            ring.append(bm.verts.new(tuple(p))); meta.append((t, th))
        rings.append(ring)
    for k in range(SEG):
        bm.faces.new((bottom, rings[0][(k + 1) % SEG], rings[0][k]))
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(SEG):
            k1 = (k + 1) % SEG
            bm.faces.new((r0[k], r0[k1], r1[k1], r1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("crossbow_grip"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new("crossbow_grip", me); bpy.context.scene.collection.objects.link(ob)
    P = np.array([v.co[:] for v in me.vertices]); N = np.array([v.normal[:] for v in me.vertices])
    me.calc_loop_triangles()
    T = np.array([[lt.vertices[0], lt.vertices[1], lt.vertices[2]] for lt in me.loop_triangles])
    # outward: the normals away from the line
    c = P - J; c -= np.outer(c @ g, g)
    assert np.mean(np.sum(c * N, 1) > 0) > 0.95, "normals not outward"
    return P, N, T, np.array(meta), g, f


def split_uv(P, N, T, meta):
    """Each vertex once per half (theta in [0, pi] and [pi, 2 pi]: the patch mirrored at the back and front), UVs
    on the patch, tangents (glTF: along +u, w = the +v side), triangles re-indexed."""
    t, th = meta[:, 0], meta[:, 1]
    tmax = max(t)
    def uv(i, half):
        a = th[i] if half == 0 else 2 * math.pi - th[i]
        a = min(max(a, 0.0), math.pi)
        if t[i] == t.min():                                        # the pole: the patch's middle
            a = math.pi / 2
        circ = math.pi * R                                         # half the band's round, mm
        u = PATCH_U0 + DU_DY * 1024 / MM * circ * a / math.pi
        v = PATCH_V0 + DV_DZ * 1024 / MM * (tmax - t[i])
        return u / 1024.0, v / 1024.0
    vmap = {}; Po, No, Uo, To = [], [], [], []
    for tri in T:
        # the triangle's half: by its vertices' mean angle (the pole: by the others)
        ths = [th[i] for i in tri if t[i] != t.min()]
        mean = math.atan2(np.mean(np.sin(ths)), np.mean(np.cos(ths))) % (2 * math.pi)
        half = 0 if mean <= math.pi else 1
        new = []
        for i in tri:
            key = (int(i), half)
            if key not in vmap:
                vmap[key] = len(Po); Po.append(P[i]); No.append(N[i]); Uo.append(uv(i, half))
            new.append(vmap[key])
        To.append(new)
    Po, No, Uo, To = np.array(Po), np.array(No), np.array(Uo), np.array(To, dtype=np.uint32)
    tan = np.zeros_like(Po); bit = np.zeros_like(Po)
    for fa in To:
        p0, p1, p2 = Po[fa]; u0, u1, u2 = Uo[fa]
        e1, e2 = p1 - p0, p2 - p0; d1, d2 = u1 - u0, u2 - u0
        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < 1e-14:
            continue
        tv = (e1 * d2[1] - e2 * d1[1]) / det; bv = (e2 * d1[0] - e1 * d2[0]) / det
        for v in fa:
            tan[v] += tv; bit[v] += bv
    tan -= No * np.sum(tan * No, 1)[:, None]
    n = np.linalg.norm(tan, axis=1)
    bad = n < 1e-9
    tan[bad] = np.cross(No[bad], [0.0, 0.0, 1.0]); n[bad] = np.linalg.norm(tan[bad], axis=1)
    tan /= n[:, None]
    w = np.where(np.sum(np.cross(No, tan) * bit, 1) >= 0, 1.0, -1.0)
    return Po, No / np.linalg.norm(No, axis=1)[:, None], Uo, np.c_[tan, w], To


def append_primitive(glb: Glb, mesh_i, material, P, N, Tg, UV, I):
    """A new primitive on mesh `mesh_i`: its data appended to the end of the BIN chunk, so every byte before stays."""
    js = glb.js
    binlen = struct.unpack("<I", glb.b[glb.bin0 - 8:glb.bin0 - 4])[0]
    assert glb.bin0 + binlen == len(glb.b), "chunks after BIN"
    data = bytearray(glb.b[glb.bin0:glb.bin0 + binlen]); data += b"\0" * (-len(data) % 4)
    attrs = {}
    def add(arr, ctype, typ, target, minmax=False):
        raw = arr.astype("<f4" if ctype == 5126 else "<u4").tobytes()
        off = len(data); data.extend(raw); data.extend(b"\0" * (-len(data) % 4))
        js["bufferViews"].append(dict(buffer=0, byteOffset=off, byteLength=len(raw), target=target))
        acc = dict(bufferView=len(js["bufferViews"]) - 1, componentType=ctype, count=int(arr.shape[0]), type=typ)
        if minmax:
            acc["min"] = [float(v) for v in arr.min(0)]; acc["max"] = [float(v) for v in arr.max(0)]
        js["accessors"].append(acc)
        return len(js["accessors"]) - 1
    attrs["POSITION"] = add(P, 5126, "VEC3", 34962, True)
    attrs["NORMAL"] = add(N, 5126, "VEC3", 34962)
    attrs["TANGENT"] = add(Tg, 5126, "VEC4", 34962)
    attrs["TEXCOORD_0"] = add(UV, 5126, "VEC2", 34962)
    ind = add(I.reshape(-1), 5125, "SCALAR", 34963)
    js["meshes"][mesh_i]["primitives"].append(dict(attributes=attrs, indices=ind, material=material, mode=4))
    js["buffers"][0]["byteLength"] = len(data)
    glb.b = bytearray(glb.b[:glb.bin0 - 8]) + struct.pack("<I4s", len(data), b"BIN\0") + data


JY = 0.0
MM = 1.0      # mm in life per file unit (main)
# the underside's plane over the line: t (mm along the line) of the plane at d mm fore of it, per mm (n.f / -n.g, the
# underside's normal (0, -0.989, -0.148), measured on the Wood mesh)
_n = np.array([0.0, -0.989, -0.148]); _a = math.radians(RAKE)
TILT = float(-(_n @ [0.0, -math.sin(_a), math.cos(_a)]) / (_n @ [0.0, math.cos(_a), math.sin(_a)]))


def main():
    global JY, MM
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    src = Path(argv[argv.index("--src") + 1]) if "--src" in argv else SRC
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else SRC
    glb = Glb.read(src)
    js = glb.js
    assert not any(p.get("name") == "crossbow_grip" for p in js["meshes"]), "already has a grip"
    wood = [i for i, m in enumerate(js["materials"]) if m.get("name") == "Wood"][0]
    mesh_i = [i for i, m in enumerate(js["meshes"]) if m["primitives"][0].get("material") == wood][0]
    assert len(js["meshes"][mesh_i]["primitives"]) == 1, "the stock already has a second primitive"
    node_i = [i for i, n in enumerate(js["nodes"]) if n.get("mesh") == mesh_i][0]
    parent = [i for i, n in enumerate(js["nodes"]) if node_i in n.get("children", [])][0]
    W, _ = glb.world()
    assert np.allclose(W[node_i], W[parent]), "the stock's node moves its mesh"
    Vw = glb.acc(js["meshes"][mesh_i]["primitives"][0]["attributes"]["POSITION"])[1]
    allz = []
    for m in js["meshes"]:
        for p in m["primitives"]:
            allz.append(glb.acc(p["attributes"]["POSITION"])[1][:, 2])
    allz = np.concatenate(allz)
    mm = LENGTH * 1000.0 / (allz.max() - allz.min())        # mm in life per file unit (Arms.Make's scale)
    JY = stock_underside(JZ, Vw); MM = mm
    P, N, T, meta, g, f = build(mm)
    Po, No, Uo, Tg, I = split_uv(P, N, T, meta)
    append_primitive(glb, mesh_i, wood, Po, No, Tg, Uo, I)
    js["meshes"][mesh_i]["primitives"][-1]["extras"] = {"name": "crossbow_grip"}
    # the anchor: the grip point on the line, -Y toward the bow (+Z file), +Z the stock's top (+Y file)
    G = np.array([0.0, JY, JZ]) - ANCHOR / mm * g
    Rl = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])   # columns X (1,0,0), Y (0,0,-1), Z (0,1,0)
    Wp = W[parent]
    Gw = (Wp @ np.r_[G, 1.0])[:3]; Rw = Wp[:3, :3] @ Rl
    write_anchor(glb, Gw, Rw / np.linalg.norm(Rw, axis=0), under=parent)
    # the sheath point (where it hangs slung, Arms.Sockets Sling): the stock's middle, on its centre line (without one
    # the grip point would be, 60 mm under the stock)
    Sw = (Wp @ np.r_[SHEATH, 1.0])[:3]
    T4 = np.eye(4); T4[:3, :3] = Rw / np.linalg.norm(Rw, axis=0); T4[:3, 3] = Sw
    L4 = np.linalg.inv(Wp) @ T4
    js["nodes"].append(dict(name="anchor_sheath", matrix=[float(v) for v in L4.T.reshape(-1)]))
    js["nodes"][parent].setdefault("children", []).append(len(js["nodes"]) - 1)
    glb.write(out)
    rep = dict(out=str(out), mm_per_unit=mm, rake=RAKE, radius=R, verts=int(len(Po)), tris=int(len(I)),
               junction=[0.0, JY, JZ], anchor_local=G.tolist(), length_below_stock=-min(p[0] for p in profile()),
               uv_min=Uo.min(0).tolist(), uv_max=Uo.max(0).tolist())
    print("CROSSBOW_GRIP " + json.dumps(rep))


if __name__ == "__main__":
    main()
