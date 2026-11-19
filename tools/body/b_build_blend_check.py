"""Check for b_build_blend.py: re-export the made blend's body with piece_blender's base.glb call and compare to body.glb.

Run: python tools/body/b_build_blend_check.py <body.glb> <made.blend> <blender.exe> [out_dir]
(spawns blender itself for the export; then compares in plain Python with numpy).
Pass bar: joints identical (names, order), inverse binds within 1e-4, Heroine positions within 0.05 mm, UV set present.
"""
import json, os, struct, subprocess, sys
import numpy as np

EXPORT = r'''
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
body = bpy.data.objects["Heroine"]
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True); body.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_skins=True,
                          export_animations=False, export_yup=True, export_vertex_color="ACTIVE")
'''


def load(path):
    b = open(path, "rb").read()
    jl, _ = struct.unpack_from("<II", b, 12)
    j = json.loads(b[20:20 + jl])
    off = 20 + jl + 8
    return j, b[off:]


def acc(j, bin_, i):
    a = j["accessors"][i]; v = j["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
    dt = {5126: "<f4", 5123: "<u2", 5125: "<u4"}[a["componentType"]]
    o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.frombuffer(bin_, dt, a["count"] * n, o).reshape(a["count"], n)


def info(path):
    j, b = load(path)
    sk = j["skins"][0]
    names = [j["nodes"][i]["name"] for i in sk["joints"]]
    ibm = acc(j, b, sk["inverseBindMatrices"]).reshape(-1, 4, 4)
    node = next(n for n in j["nodes"] if n.get("name") == "Heroine" and "mesh" in n)
    prim = j["meshes"][node["mesh"]]["primitives"][0]
    pos = acc(j, b, prim["attributes"]["POSITION"])
    return names, ibm, pos, "TEXCOORD_0" in prim["attributes"]


if __name__ == "__main__":
    glb, blend, exe = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(blend)), ".")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "base_check.glb")
    py = os.path.join(out_dir, "_export_base.py")
    open(py, "w").write(EXPORT)
    subprocess.run([exe, "-b", blend, "--python", py, "--", out], check=True)
    n0, i0, p0, u0 = info(glb)
    n1, i1, p1, u1 = info(out)
    same = n0 == n1
    dib = float(np.abs(i0 - i1).max()) if i0.shape == i1.shape else float("inf")
    sameset = sorted(n0) == sorted(n1)
    if sameset:
        m = {n: i for i, n in enumerate(n1)}
        dib_name = float(np.abs(i0 - i1[[m[n] for n in n0]]).max())
        print("joint set equal; order differs at %d slots; ibm max abs diff matched BY NAME %.3g" % (sum(a != b for a, b in zip(n0, n1)), dib_name))
    if p0.shape == p1.shape:
        d = np.linalg.norm(p0 - p1, axis=1).max() * 1000
    else:
        d = float("inf")
    print("joints", len(n0), len(n1), "identical" if same else "DIFFER")
    print("ibm max abs diff %.3g" % dib)
    print("pos max mm %.4f (verts %d vs %d)" % (d, len(p0), len(p1)))
    print("uv", u0, u1)
    ok = same and dib < 1e-4 and d < 0.05 and u1
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
