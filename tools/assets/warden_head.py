"""Graft a separately generated hooded bust onto a Marionette NPC package (the Ford-Warden's own head).

Marionette's NPC pipeline gives a generated man the shared base's head (skin_head, eyes, teeth, tongue, a hair crop)
and cuts his hood away. This replaces that whole head with a TRELLIS bust (hood, face, beard, the hood's skirt):

  1. the bust is placed on the body by a trimmed, symmetric similarity ICP against the full sculpt's hood and
     shoulders (the sculpt must be in the package frame: Marionette's generated/game/NAME_detail.glb or _clean.glb);
  2. cut: everything above ZCUT (the hood's skirt, overlapping the body's mantle) plus the beard below it;
  3. remeshed: decimated to ~27k tris, a fresh UV unwrap, colour / normal / roughness re-baked from the bust (4096);
     the beard darkened ~20% and glossier (roughness ~0.35, soaked), the face skin a little glossy, no metal;
  4. skinned: face, beard and the hood above the neck to Head; the hood's skirt takes the weights of the body's mantle
     under it (so the two move together), blended to Head by height; the beard's tip blends a little to neck_01;
  5. the body: the base head's meshes (Head, eyes, teeth, tongue, hair) and skin_head dropped, the neck skin under
     the hood dropped, the mantle's top tucked 7 mm under the skirt where it would poke through;
  6. lod.glb gets the same swap (a ~3k-tri head sharing the full head's UVs and material name; lod_shadow a coarse one);
  7. manifest.json renamed, hair dropped, the head and its eye sockets (Head-bone-local, metres) recorded.

The package's glTF is edited at the JSON level (nothing else of the body is round-tripped through Blender), so the
skeleton, bind poses and the clothes are byte-for-byte the package's.

Run (Blender 4.5, a blender turn):
  blender -b --python-exit-code 1 -P tools/assets/warden_head.py -- PKG_IN PKG_OUT BUST.glb SCULPT.glb
        [--name ford_warden] [--eyes "x,y;x,y"] [--work DIR]
--eyes: the eye sockets in the front check render (PKG_OUT/../_check or --work: head_front.png, 1024 px over
0.4 m centred 8 cm above the Head bone), as pixel x,y; without it the script writes that render and reports no eyes.
"""
import bpy, bmesh, json, math, os, struct, sys, shutil
import numpy as np
import mathutils
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from PIL import Image

# ---- constants (package frame, glTF: Y up, metres, front +Z) ----
ZCUT = 1.44        # the bust is kept above this (the hood's skirt down over the mantle's top)
Z0, Z1 = 1.465, 1.535   # the hood: body (mantle) weights below Z0, Head above Z1
BEARD_Z0, BEARD_Z1 = 1.40, 1.50  # the beard: Head above BEARD_Z1, a third neck_01 at its tip
TARGET_TRIS, LOD_TRIS, SHADOW_TRIS = 28000, 3000, 700
TEX = 4096
TUCK = 0.007
BEARD_DARK, BEARD_ROUGH, SKIN_ROUGH = 0.80, 0.35, 0.50
NOSE_Z = 1.648   # the beard (moustache) below this line on the face, rising 0.6 m/m toward the cheeks
HEAD_DROP = {"skin_head", "eyes", "teeth", "tongue", "hair", "hair_cap", "hair_fine"}


def log(*a):
    print("[warden_head]", *a, flush=True)


# ================= glb =================
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class Glb:
    def __init__(self, path):
        b = open(path, "rb").read()
        assert b[:4] == b"glTF"
        n = struct.unpack("<I", b[12:16])[0]
        self.j = json.loads(b[20:20 + n])
        o = 20 + n
        m = struct.unpack("<I", b[o:o + 4])[0]
        self.bin = bytearray(b[o + 8:o + 8 + m])

    def acc(self, i):
        a = self.j["accessors"][i]
        bv = self.j["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]])
        nc = NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0) or dt.itemsize * nc
        raw = np.frombuffer(self.bin, dtype=np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * nc, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, shape=(a["count"], dt.itemsize * nc), strides=(stride, 1)).copy()
        out = out.view(dt).reshape(a["count"], nc)
        if a.get("normalized") and dt != np.float32:
            out = out.astype(np.float32) / np.iinfo(dt).max
        return out if nc > 1 else out[:, 0]

    def _view(self, data, target=None):
        while len(self.bin) % 8:
            self.bin.append(0)
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            bv["target"] = target
        self.bin += data
        self.j["bufferViews"].append(bv)
        return len(self.j["bufferViews"]) - 1

    def add_acc(self, arr, kind, minmax=False, target=34962):
        arr = np.ascontiguousarray(arr)
        ct = {np.dtype(np.float32): 5126, np.dtype(np.uint32): 5125, np.dtype(np.uint16): 5123, np.dtype(np.uint8): 5121}[arr.dtype]
        a = {"bufferView": self._view(arr.tobytes(), target), "componentType": ct, "count": int(arr.shape[0]), "type": kind}
        if minmax:
            a["min"] = arr.reshape(arr.shape[0], -1).min(0).tolist()
            a["max"] = arr.reshape(arr.shape[0], -1).max(0).tolist()
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def add_image(self, data, mime, name):
        self.j.setdefault("images", []).append({"bufferView": self._view(data), "mimeType": mime, "name": name})
        self.j.setdefault("samplers", [])
        if not self.j["samplers"]:
            self.j["samplers"].append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})
        self.j.setdefault("textures", []).append({"source": len(self.j["images"]) - 1, "sampler": 0})
        return len(self.j["textures"]) - 1

    def node_index(self, name):
        return next(i for i, n in enumerate(self.j["nodes"]) if n.get("name") == name)

    def global_mats(self):
        nodes = self.j["nodes"]
        par = {}
        for i, n in enumerate(nodes):
            for c in n.get("children", []):
                par[c] = i

        def local(n):
            if "matrix" in n:
                return np.array(n["matrix"]).reshape(4, 4).T
            M = np.eye(4)
            q = n.get("rotation", [0, 0, 0, 1])
            M[:3, :3] = np.array(mathutils.Quaternion((q[3], q[0], q[1], q[2])).to_matrix())
            M[:3, :3] *= np.array(n.get("scale", [1, 1, 1]))[None, :]
            M[:3, 3] = n.get("translation", [0, 0, 0])
            return M
        out = {}

        def g(i):
            if i not in out:
                out[i] = (g(par[i]) if i in par else np.eye(4)) @ local(nodes[i])
            return out[i]
        for i in range(len(nodes)):
            g(i)
        return out

    def drop_nodes(self, drop):
        j = self.j
        keep = [i for i in range(len(j["nodes"])) if i not in drop]
        remap = {o: n for n, o in enumerate(keep)}
        j["nodes"] = [j["nodes"][i] for i in keep]
        for n in j["nodes"]:
            if "children" in n:
                n["children"] = [remap[c] for c in n["children"] if c in remap]
        for s in j["scenes"]:
            s["nodes"] = [remap[c] for c in s["nodes"] if c in remap]
        for s in j.get("skins", []):
            s["joints"] = [remap[c] for c in s["joints"]]
            if "skeleton" in s:
                s["skeleton"] = remap[s["skeleton"]]
        for an in j.get("animations", []):
            for ch in an["channels"]:
                ch["target"]["node"] = remap[ch["target"]["node"]]

    def compact(self):
        """Drop everything nothing references; rebuild the binary chunk."""
        j = self.j

        def remap_list(key, used):
            used = sorted(used)
            m = {o: n for n, o in enumerate(used)}
            j[key] = [j[key][i] for i in used]
            return m
        used_mesh = {n["mesh"] for n in j["nodes"] if "mesh" in n}
        mm = remap_list("meshes", used_mesh)
        for n in j["nodes"]:
            if "mesh" in n:
                n["mesh"] = mm[n["mesh"]]
        used_skin = {n["skin"] for n in j["nodes"] if "skin" in n}
        sm = remap_list("skins", used_skin) if j.get("skins") else {}
        for n in j["nodes"]:
            if "skin" in n:
                n["skin"] = sm[n["skin"]]
        # materials
        used_mat = {p["material"] for m in j["meshes"] for p in m["primitives"] if "material" in p}
        mtm = remap_list("materials", used_mat)
        for m in j["meshes"]:
            for p in m["primitives"]:
                if "material" in p:
                    p["material"] = mtm[p["material"]]
        # textures referenced anywhere in materials

        def tex_refs(o, out, key=""):
            if isinstance(o, dict):
                if key.endswith("Texture") and "index" in o:
                    out.append(o)
                for k, v in o.items():
                    tex_refs(v, out, k)
            elif isinstance(o, list):
                for v in o:
                    tex_refs(v, out, key)
        refs = []
        tex_refs(j["materials"], refs)
        if j.get("textures"):
            tm = remap_list("textures", {r["index"] for r in refs})
            for r in refs:
                r["index"] = tm[r["index"]]
            im = remap_list("images", {t["source"] for t in j["textures"] if "source" in t})
            for t in j["textures"]:
                t["source"] = im[t["source"]]
            if j.get("samplers"):
                spm = remap_list("samplers", {t["sampler"] for t in j["textures"] if "sampler" in t})
                for t in j["textures"]:
                    if "sampler" in t:
                        t["sampler"] = spm[t["sampler"]]
        else:
            for k in ("textures", "images", "samplers"):
                j.pop(k, None)
        # accessors
        acc_refs = []  # (dict, key)
        for m in j["meshes"]:
            for p in m["primitives"]:
                for k in p["attributes"]:
                    acc_refs.append((p["attributes"], k))
                if "indices" in p:
                    acc_refs.append((p, "indices"))
                for t in p.get("targets", []):
                    for k in t:
                        acc_refs.append((t, k))
        for s in j.get("skins", []):
            if "inverseBindMatrices" in s:
                acc_refs.append((s, "inverseBindMatrices"))
        for an in j.get("animations", []):
            for sp in an["samplers"]:
                acc_refs += [(sp, "input"), (sp, "output")]
        am = remap_list("accessors", {d[k] for d, k in acc_refs})
        for d, k in acc_refs:
            d[k] = am[d[k]]
        # buffer views
        bv_refs = [(a, "bufferView") for a in j["accessors"] if "bufferView" in a]
        bv_refs += [(i, "bufferView") for i in j.get("images", []) if "bufferView" in i]
        used_bv = sorted({d[k] for d, k in bv_refs})
        newbin = bytearray()
        bvm = {}
        views = []
        for o in used_bv:
            bv = dict(j["bufferViews"][o])
            data = self.bin[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
            while len(newbin) % 8:
                newbin.append(0)
            bv["byteOffset"] = len(newbin)
            newbin += data
            bvm[o] = len(views)
            views.append(bv)
        for d, k in bv_refs:
            d[k] = bvm[d[k]]
        j["bufferViews"] = views
        self.bin = newbin
        j["buffers"] = [{"byteLength": len(newbin)}]
        s = json.dumps({k: v for k, v in j.items() if k not in ("extensionsUsed", "extensionsRequired")})
        for k in ("extensionsUsed", "extensionsRequired"):
            if k in j:
                j[k] = [e for e in j[k] if f'"{e}"' in s]
                if not j[k]:
                    del j[k]

    def save(self, path):
        self.compact()
        js = json.dumps(self.j, separators=(",", ":")).encode()
        while len(js) % 4:
            js += b" "
        b = bytes(self.bin)
        while len(b) % 4:
            b += b"\0"
        out = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(b))
        out += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(b)) + b"BIN\0" + b
        open(path, "wb").write(out)


# ================= Blender helpers =================
def b2g(a):  # Blender (Z up, front -Y) -> glTF (Y up, front +Z)
    return np.stack([a[:, 0], a[:, 2], -a[:, 1]], 1)


def g2b(a):
    return np.stack([a[:, 0], -a[:, 2], a[:, 1]], 1)


def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def world_pts(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return a @ M[:3, :3].T + M[:3, 3]


def kd(a):
    t = KDTree(len(a))
    for i, p in enumerate(a):
        t.insert(p, i)
    t.balance()
    return t


def umeyama(A, B):
    ma, mb = A.mean(0), B.mean(0)
    a, b = A - ma, B - mb
    U, D, Vt = np.linalg.svd(b.T @ a / len(A))
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    s = np.trace(np.diag(D) @ S) / (a ** 2).sum(1).mean()
    return s, R, mb - s * R @ ma


def align(bust_pts, sculpt_pts, zc=1.40):
    """Bust -> package frame (Blender coordinates): trimmed symmetric similarity ICP on the hood and shoulders."""
    D = sculpt_pts[sculpt_pts[:, 2] > zc]
    rng = np.random.default_rng(0)
    b = bust_pts[rng.choice(len(bust_pts), min(30000, len(bust_pts)), replace=False)]
    td = kd(D)
    top_b, top_d = b[:, 2].max(), D[:, 2].max()
    hb = top_b - b[:, 2].min()
    s = 0.57 * (0.88 / hb)
    R, t = np.eye(3), np.array([0, 0, top_d - s * top_b])
    for it in range(40):
        B = s * b @ R.T + t
        m = B[:, 2] > zc
        Bm, bm = B[m], b[m]
        j1 = np.array([td.find(p)[1] for p in Bm])
        e1 = np.linalg.norm(D[j1] - Bm, axis=1)
        tb = kd(Bm)
        k = np.array([tb.find(p)[1] for p in D])
        e2 = np.linalg.norm(Bm[k] - D, axis=1)
        A = np.vstack([bm, bm[k]])
        T = np.vstack([D[j1], D])
        e = np.concatenate([e1, e2])
        keep = e < np.quantile(e, 0.8)
        s, R, t = umeyama(A[keep], T[keep])
    log(f"align: scale {s:.4f}, move {np.round(t, 4).tolist()}, turn {np.round(np.degrees(mathutils.Matrix(R.tolist()).to_euler()[:]), 2).tolist()} deg, err {e1.mean()*1e3:.1f}/{e2.mean()*1e3:.1f} mm")
    M = np.eye(4)
    M[:3, :3] = s * R
    M[:3, 3] = t
    return M


def tex_array(img):
    w, h = img.size
    a = np.zeros(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)  # row 0 = bottom (v = 0)


def sample(arr, uv):
    h, w = arr.shape[:2]
    x = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(int)
    y = np.clip((uv[:, 1] % 1.0) * h, 0, h - 1).astype(int)
    return arr[y, x]


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def simplified(o, tris, name, size):
    """A new object: o's surface reduced to ~tris triangles (pyfqmr quadric collapse: Blender's decimator stalls on
    TRELLIS meshes), smooth shaded, a fresh xatlas unwrap packed for a size^2 map.
    (pyfqmr and xatlas: pip-installed into Blender's own python.)"""
    import pyfqmr
    me = o.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    me.calc_loop_triangles()
    F = np.zeros(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", F)
    s = pyfqmr.Simplify()
    s.setMesh(V.reshape(-1, 3), F.reshape(-1, 3))
    s.simplify_mesh(target_count=tris, aggressiveness=5, preserve_border=True, verbose=0)
    v, f, _ = s.getMesh()
    vmap, idx, uvs, charts = unwrap(v, f, size)
    faces = vmap[idx]
    nm = bpy.data.meshes.new(name)
    nm.from_pydata(v.tolist(), [], faces.tolist())
    for p in nm.polygons:
        p.use_smooth = True
    uvl = nm.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", uvs[idx].astype(np.float32).ravel())
    ob = bpy.data.objects.new(name, nm)
    bpy.context.scene.collection.objects.link(ob)
    log(f"{name}: {len(faces)} tris, {charts} UV charts")
    return ob


XATLAS = """
import sys, numpy as np, xatlas
d = np.load(sys.argv[1])
a = xatlas.Atlas()
a.add_mesh(d["v"].astype(np.float32), d["f"].astype(np.uint32))
po = xatlas.PackOptions()
po.resolution = int(d["size"])
po.padding = max(2, int(d["size"]) // 512)
po.bilinear = True
co = xatlas.ChartOptions()
co.max_cost = 8.0
co.normal_deviation_weight = 1.0
a.generate(chart_options=co, pack_options=po)
vm, ix, uv = a[0]
np.savez(sys.argv[2], vmap=vm, idx=ix, uvs=uv, charts=a.chart_count)
"""


def unwrap(v, f, size):
    """xatlas, in a child process (in Blender's own process its threads crash on the C++ runtime)."""
    import subprocess, tempfile
    py = os.path.join(sys.prefix, "bin", "python.exe")
    with tempfile.TemporaryDirectory() as t:
        a, b, c = (os.path.join(t, n) for n in ("in.npz", "out.npz", "xa.py"))
        np.savez(a, v=v, f=f, size=size)
        open(c, "w").write(XATLAS)
        subprocess.run([py, "-I", c, a, b], check=True)
        with np.load(b) as d:
            return d["vmap"].copy(), d["idx"].copy(), d["uvs"].copy(), int(d["charts"])


def select_only(*obs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def bake(hi, lo, size, matname):
    """Colour, normal and roughness of hi onto lo's UVs (Cycles, selected to active); arrays, row 0 = top."""
    sc = bpy.context.scene
    lmat = bpy.data.materials.new(matname)
    lmat.use_nodes = True
    lo.data.materials.clear()
    lo.data.materials.append(lmat)
    tn = lmat.node_tree.nodes.new("ShaderNodeTexImage")
    lmat.node_tree.nodes.active = tn
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 4
    bk = sc.render.bake
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.012
    bk.max_ray_distance = 0.04
    bk.margin = max(4, size // 256)
    bk.use_pass_direct = False
    bk.use_pass_indirect = False
    bk.use_pass_color = True
    out = {}
    for kind, cs in (("DIFFUSE", "sRGB"), ("NORMAL", "Non-Color"), ("ROUGHNESS", "Non-Color")):
        img = bpy.data.images.new(f"{matname}_{kind}", size, size, alpha=False, float_buffer=False)
        img.colorspace_settings.name = cs
        tn.image = img
        select_only(hi, lo)
        bpy.ops.object.bake(type=kind)
        out[kind] = tex_array(img)[::-1][..., :3].copy()
    log(f"baked {matname} at {size}")
    return out


# ================= the head =================
def build_head(bust_path, sculpt_path, work):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sculpt = imp(sculpt_path)
    sp = np.vstack([world_pts(o) for o in sculpt])
    if sp[:, 2].max() < 1.2:
        raise SystemExit("the sculpt is not in the package frame (use Marionette's generated/game/NAME_detail.glb)")
    bust = imp(bust_path)
    assert len(bust) == 1
    hi = bust[0]
    for o in sculpt:
        bpy.data.objects.remove(o)
    M = align(world_pts(hi), sp)
    hi.matrix_world = mathutils.Matrix(M.tolist())
    select_only(hi)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = hi.data
    bm = bmesh.new()
    bm.from_mesh(me)
    nv0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # (glTF splits vertices at UV seams: weld; UVs stay per corner)
    bm.verts.ensure_lookup_table()
    log(f"bust welded: {nv0} -> {len(bm.verts)} vertices")
    # the beard (pale, front and centre) is kept below the cut
    mat = me.materials[0]
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    carr = tex_array(bsdf.inputs["Base Color"].links[0].from_node.image)
    uvl = bm.loops.layers.uv.active
    vuv = np.zeros((len(bm.verts), 2))
    for f in bm.faces:
        for l in f.loops:
            vuv[l.vert.index] = l[uvl].uv
    co = np.array([v.co[:] for v in bm.verts])
    pale = sample(carr, vuv)[:, :3].max(1) > 0.35  # (sRGB)
    beardish = pale & (np.abs(co[:, 0]) < 0.11) & (co[:, 1] < -0.02)
    keepv = (co[:, 2] > ZCUT) | (beardish & (co[:, 2] > ZCUT - 0.09))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(keepv[v.index] for v in f.verts)], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    # loose specks (under 0.2% of the main piece) go
    bm.faces.ensure_lookup_table()
    seen, islands = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    small = [f for isl in islands[1:] if len(isl) < 0.002 * len(islands[0]) for f in isl]
    bmesh.ops.delete(bm, geom=small, context="FACES")
    bm.to_mesh(me)
    bm.free()
    log(f"bust cut: {len(me.polygons)} faces kept, {len(islands)} pieces ({len(small)} faces of specks dropped)")
    # the bake source: no metal
    if bsdf.inputs["Metallic"].links:
        mat.node_tree.links.remove(bsdf.inputs["Metallic"].links[0])
    bsdf.inputs["Metallic"].default_value = 0.0

    lo = simplified(hi, TARGET_TRIS, "warden_head", TEX)
    lod = simplified(hi, LOD_TRIS, "warden_head_lod", 1024)
    shadow = simplified(hi, SHADOW_TRIS, "warden_head_shadow", 256)
    log(f"head {tri_count(lo)} tris, lod {tri_count(lod)}, shadow {tri_count(shadow)}")
    out = bake(hi, lo, TEX, "warden_head")
    outl = bake(hi, lod, 1024, "warden_head_lod")
    for k in out:
        Image.fromarray((np.clip(out[k], 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(work, f"bake_{k}.png"))
        Image.fromarray((np.clip(outl[k], 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(work, f"lodbake_{k}.png"))
    bpy.data.objects.remove(hi)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, "head_low.blend"))
    return lo, lod, shadow, out, outl


def load_head(work):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(work, "head_low.blend"))
    rd = lambda p: np.asarray(Image.open(os.path.join(work, p)), np.float32)[..., :3] / 255
    out = {k: rd(f"bake_{k}.png") for k in ("DIFFUSE", "NORMAL", "ROUGHNESS")}
    outl = {k: rd(f"lodbake_{k}.png") for k in ("DIFFUSE", "NORMAL", "ROUGHNESS")}
    o = bpy.data.objects
    return o["warden_head"], o["warden_head_lod"], o["warden_head_shadow"], out, outl


def classes(o, colour):
    """Per vertex of o: (face, beard, skin) in 0..1. Face = pale, front and centre (face and beard, all on Head);
    beard = the face below the nose line (rising toward the cheeks); skin = the rest of the face."""
    me = o.data
    nv = len(me.vertices)
    co = world_pts(o)
    luv = np.zeros(len(me.loops) * 2)
    me.uv_layers[0].data.foreach_get("uv", luv)
    luv = luv.reshape(-1, 2)
    lvi = np.zeros(len(me.loops), int)
    me.loops.foreach_get("vertex_index", lvi)
    pal = np.zeros(nv)
    np.maximum.at(pal, lvi, smoothstep(0.28, 0.40, sample(colour[::-1], luv).max(1)))
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    front = smoothstep(0.125, 0.10, np.abs(x)) * smoothstep(0.0, -0.03, y)
    face = pal * front
    ev = np.zeros(len(me.edges) * 2, int)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)

    def smooth(f, n):
        for _ in range(n):
            acc = np.zeros(nv)
            cnt = np.zeros(nv)
            np.add.at(acc, ev[:, 0], f[ev[:, 1]])
            np.add.at(acc, ev[:, 1], f[ev[:, 0]])
            np.add.at(cnt, ev[:, 0], 1)
            np.add.at(cnt, ev[:, 1], 1)
            f = 0.5 * f + 0.5 * acc / np.maximum(cnt, 1)
        return f
    face = smooth(face, 4)
    line = NOSE_Z + 0.6 * np.maximum(np.abs(x) - 0.025, 0)
    below = smoothstep(line + 0.006, line - 0.006, z)
    return np.clip(face, 0, 1), smooth(face * below, 2), smooth(face * (1 - below), 2)


def raster(o, values, size):
    """Per-vertex values painted into o's UV layout (size^2, row 0 = top), bled a few texels past the islands."""
    from PIL import ImageDraw, ImageFilter
    me = o.data
    me.calc_loop_triangles()
    luv = np.zeros(len(me.loops) * 2)
    me.uv_layers[0].data.foreach_get("uv", luv)
    luv = luv.reshape(-1, 2)
    lvi = np.zeros(len(me.loops), int)
    me.loops.foreach_get("vertex_index", lvi)
    tl = np.zeros(len(me.loop_triangles) * 3, int)
    me.loop_triangles.foreach_get("loops", tl)
    tl = tl.reshape(-1, 3)
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    for t in tl:
        val = int(255 * values[lvi[t]].mean() + 0.5)
        if val:
            d.polygon([(luv[k, 0] * size, (1 - luv[k, 1]) * size) for k in t], fill=val)
    im = im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(size / 1024))
    return np.asarray(im, np.float32) / 255


def look(o, out, size):
    """The baked maps with the beard darkened and glossy (soaked), the face skin a little glossy, no metal."""
    face, beard, skin = classes(o, out["DIFFUSE"])
    mb, ms = raster(o, beard, size), raster(o, skin, size)
    col = out["DIFFUSE"] * (1 - (1 - BEARD_DARK) * mb)[..., None]
    rough = out["ROUGHNESS"][..., 0]
    rough = rough * (1 - mb - ms).clip(0, 1) + BEARD_ROUGH * mb + SKIN_ROUGH * ms
    log(f"look {size}: beard {mb.mean()*100:.2f}% of texels, skin {ms.mean()*100:.2f}%")
    z = np.zeros_like(rough)
    return face, {"color": Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)),
                  "normal": Image.fromarray((np.clip(out["NORMAL"], 0, 1) * 255 + 0.5).astype(np.uint8)),
                  "mr": Image.fromarray((np.stack([z, np.clip(rough, 0, 1), z], -1) * 255 + 0.5).astype(np.uint8))}


def head_arrays(o, face, cls_smooth=4):
    """Triangle arrays (glTF frame) of a Blender mesh: positions, normals, uvs, indices, and the source vertex of each."""
    me = o.data
    me.calc_loop_triangles()
    nv = len(me.vertices)
    co = np.zeros(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    vn = np.zeros(nv * 3)
    me.vertices.foreach_get("normal", vn)
    vn = vn.reshape(-1, 3)
    tl = np.zeros(len(me.loop_triangles) * 3, int)
    me.loop_triangles.foreach_get("loops", tl)
    lvi = np.zeros(len(me.loops), int)
    me.loops.foreach_get("vertex_index", lvi)
    luv = np.zeros(len(me.loops) * 2)
    me.uv_layers[0].data.foreach_get("uv", luv)
    luv = luv.reshape(-1, 2)
    key = np.round(np.c_[lvi, luv * 65536], 0)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    first = np.zeros(len(uniq), int)
    first[inv[::-1]] = np.arange(len(inv))[::-1]
    src = lvi[first]
    # face/beard class smoothed over edges
    ev = np.zeros(len(me.edges) * 2, int)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    f = face.astype(float)
    for _ in range(cls_smooth):
        acc = np.zeros(nv)
        cnt = np.zeros(nv)
        np.add.at(acc, ev[:, 0], f[ev[:, 1]])
        np.add.at(acc, ev[:, 1], f[ev[:, 0]])
        np.add.at(cnt, ev[:, 0], 1)
        np.add.at(cnt, ev[:, 1], 1)
        f = 0.5 * f + 0.5 * acc / np.maximum(cnt, 1)
    uv = luv[first].copy()
    uv[:, 1] = 1 - uv[:, 1]
    return dict(pos=b2g(co[src]).astype(np.float32), nrm=b2g(vn[src]).astype(np.float32), uv=uv.astype(np.float32),
                idx=inv[tl].astype(np.uint32), src=src, face=f[src], vpos=b2g(co), vface=f)


# ================= weights =================
def body_weights(g, prim, joint_names):
    p = g.j["meshes"][0]["primitives"][prim]
    pos = g.acc(p["attributes"]["POSITION"])
    J = g.acc(p["attributes"]["JOINTS_0"]).astype(int)
    W = g.acc(p["attributes"]["WEIGHTS_0"]).astype(np.float32)
    return pos, J, W


def head_weights(pos, face, ref_pos, ref_J, ref_W, names):
    """Head (and neck_01 at the beard's tip) for the face and beard; the hood blends from the body's mantle weights to Head by height."""
    nb = len(names)
    hi = names.index("Head")
    nk = names.index("neck_01")
    sel = ref_pos[:, 1] > 1.25
    rp, rJ, rW = ref_pos[sel], ref_J[sel], ref_W[sel]
    t = kd(rp)
    dense = np.zeros((len(pos), nb), np.float32)
    for i, q in enumerate(pos):
        hits = t.find_n(q, 4)
        ws = np.array([1 / max(h[2], 1e-4) for h in hits])
        ws /= ws.sum()
        for (c, k, dd), w in zip(hits, ws):
            np.add.at(dense[i], rJ[k], rW[k] * w)
    y = pos[:, 1]
    f = np.clip(face, 0, 1)
    wh = f + (1 - f) * smoothstep(Z0, Z1, y)
    dense *= (1 - wh)[:, None]
    dense[:, hi] += wh
    # (the beard's tip: up to a third to neck_01, taken out of Head)
    tip = f * smoothstep(BEARD_Z1, BEARD_Z0, y) * 0.35
    dense[:, hi] -= tip
    dense[:, nk] += tip
    dense = np.clip(dense, 0, None)
    order = np.argsort(-dense, 1)[:, :4]
    W = np.take_along_axis(dense, order, 1)
    W /= W.sum(1, keepdims=True)
    return order.astype(np.uint16), W.astype(np.float32)


def tuck(pos, head_pos, head_idx, zmin):
    """Body vertices that would poke through the bust: moved TUCK under it."""
    tris = head_idx.reshape(-1, 3)
    bvh = BVHTree.FromPolygons([tuple(v) for v in head_pos.astype(float)], [tuple(t) for t in tris.tolist()])
    out = pos.copy()
    moved = 0
    for i in np.nonzero(pos[:, 1] > zmin)[0]:
        q = mathutils.Vector(pos[i].tolist())
        hit = bvh.find_nearest(q, 0.06)
        if hit[0] is None:
            continue
        p, n = hit[0], hit[1]
        if (q - p).dot(n) > -TUCK:
            out[i] = np.array(p - n * TUCK)
            moved += 1
    return out, moved


# ================= package =================
def mat_index(g, name):
    return next(i for i, m in enumerate(g.j["materials"]) if m.get("name") == name)


def add_head_material(g, images, size, name="warden_head"):
    def enc(im, fmt, q=92):
        import io
        if im.size[0] != size:
            im = im.resize((size, size), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, fmt, quality=q) if fmt == "JPEG" else im.save(b, fmt, optimize=True)
        return b.getvalue()
    tc = g.add_image(enc(images["color"], "JPEG", 92), "image/jpeg", name + "_color")
    tnm = g.add_image(enc(images["normal"], "JPEG", 95), "image/jpeg", name + "_normal")
    tmr = g.add_image(enc(images["mr"].resize((size // 2, size // 2), Image.LANCZOS) if size > 512 else images["mr"], "PNG"), "image/png", name + "_mr")
    g.j["materials"].append({"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": tc}, "metallicRoughnessTexture": {"index": tmr},
                                                                      "metallicFactor": 1.0, "roughnessFactor": 1.0},
                             "normalTexture": {"index": tnm}})
    return len(g.j["materials"]) - 1


def filter_skin(g, prim, keep_tri):
    p = prim
    pos = g.acc(p["attributes"]["POSITION"])
    idx = g.acc(p["indices"]).reshape(-1, 3)
    c = pos[idx].mean(1)
    k = np.array([keep_tri(x) for x in c])
    p["indices"] = g.add_acc(idx[k].astype(np.uint32).ravel(), "SCALAR", target=34963)
    return int((~k).sum())


def neck_skin(c):  # a skin triangle under the hood (not the hands)
    return not (c[1] > 1.42 and abs(c[0]) < 0.16 and abs(c[2] + 0.03) < 0.16)


def add_prim(g, mesh, arr, J, W, mat, attrs):
    a = {"POSITION": g.add_acc(arr["pos"], "VEC3", minmax=True)}
    if "NORMAL" in attrs:
        a["NORMAL"] = g.add_acc(arr["nrm"], "VEC3")
    if "TEXCOORD_0" in attrs:
        a["TEXCOORD_0"] = g.add_acc(arr["uv"], "VEC2")
    a["JOINTS_0"] = g.add_acc(J, "VEC4")
    a["WEIGHTS_0"] = g.add_acc(W, "VEC4")
    mesh["primitives"].append({"attributes": a, "indices": g.add_acc(arr["idx"], "SCALAR", target=34963), "material": mat, "mode": 4})


def front_render(o, path, head_g, colour):
    sc = bpy.context.scene
    tn = next(n for n in o.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    tn.image = bpy.data.images.load(colour)
    for x in list(bpy.data.objects):
        if x is not o:
            x.hide_render = True
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_x = sc.render.resolution_y = 1024
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 0.4
    cx, cz = head_g[0], head_g[1] + 0.08
    cam.location = (cx, -2, cz)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return cx, cz


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    pos_args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    opt = {argv[i][2:]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    pkg_in, pkg_out, bust_path, sculpt_path = pos_args[:4]
    name = opt.get("name", "ford_warden")
    work = opt.get("work", os.path.join(pkg_out, "..", "_check_" + name))
    os.makedirs(pkg_out, exist_ok=True)
    os.makedirs(work, exist_ok=True)

    if "reuse" in opt:
        lo, mid, sh, out, outl = load_head(work)
    else:
        lo, mid, sh, out, outl = build_head(bust_path, sculpt_path, work)
    face, images = look(lo, out, TEX)
    lface, limages = look(mid, outl, 1024)
    images["color"].save(os.path.join(work, "head_color.png"))
    ga = head_arrays(lo, face, 0)
    gl = head_arrays(mid, lface, 0)
    tf = kd(ga["vpos"])
    gs = head_arrays(sh, np.array([ga["vface"][tf.find(p)[1]] for p in b2g(world_pts(sh))]), 0)

    # ---- body.glb ----
    g = Glb(os.path.join(pkg_in, "body.glb"))
    skin = g.j["skins"][0]
    names = [g.j["nodes"][n]["name"] for n in skin["joints"]]
    body_node = next(i for i, n in enumerate(g.j["nodes"]) if n.get("mesh") == 0)
    bmesh_ = g.j["meshes"][0]
    gen = next(i for i, p in enumerate(bmesh_["primitives"]) if g.j["materials"][p["material"]]["name"] == "generated")
    rp, rJ, rW = body_weights(g, gen, names)
    J, W = head_weights(ga["pos"], ga["face"], rp, rJ, rW, names)
    # drop the base head's own meshes
    drop = {i for i, n in enumerate(g.j["nodes"]) if "mesh" in n and i != body_node}
    log("dropped nodes:", [g.j["nodes"][i]["name"] for i in drop])
    newp = []
    cut_skin = 0
    for p in bmesh_["primitives"]:
        mn = g.j["materials"][p["material"]]["name"]
        if mn in HEAD_DROP:
            continue
        if mn == "skin":
            cut_skin = filter_skin(g, p, neck_skin)
        if mn == "generated":
            pos = g.acc(p["attributes"]["POSITION"])
            pos2, moved = tuck(pos, ga["pos"], ga["idx"], ZCUT - 0.03)
            p["attributes"]["POSITION"] = g.add_acc(pos2.astype(np.float32), "VEC3", minmax=True)
            log(f"mantle tucked under the hood: {moved} vertices")
        newp.append(p)
    bmesh_["primitives"] = newp
    hm = add_head_material(g, images, TEX)
    add_prim(g, bmesh_, ga, J, W, hm, ["NORMAL", "TEXCOORD_0"])
    gm = g.global_mats()
    head_node = g.node_index("Head")
    Ghead = gm[head_node]
    g.drop_nodes(drop)
    g.save(os.path.join(pkg_out, "body.glb"))
    log(f"body.glb: neck skin tris dropped {cut_skin}; head tris {len(ga['idx'])//3}")

    # ---- lod.glb ----
    gL = Glb(os.path.join(pkg_in, "lod.glb"))
    namesL = [gL.j["nodes"][n]["name"] for n in gL.j["skins"][0]["joints"]]
    lmesh_i = next(gL.j["nodes"][i]["mesh"] for i, n in enumerate(gL.j["nodes"]) if n.get("name") == "lod")
    smesh_i = next(gL.j["nodes"][i]["mesh"] for i, n in enumerate(gL.j["nodes"]) if n.get("name") == "lod_shadow")
    lm = gL.j["meshes"][lmesh_i]
    newp = []
    for p in lm["primitives"]:
        mn = gL.j["materials"][p["material"]]["name"]
        if mn in HEAD_DROP:
            continue
        if mn == "skin":
            filter_skin(gL, p, neck_skin)
        if mn == "generated":
            pos = gL.acc(p["attributes"]["POSITION"])
            pos2, moved = tuck(pos, gl["pos"], gl["idx"], ZCUT - 0.03)
            p["attributes"]["POSITION"] = gL.add_acc(pos2.astype(np.float32), "VEC3", minmax=True)
        newp.append(p)
    lm["primitives"] = newp
    attrs = list(newp[0]["attributes"].keys())
    JL, WL = head_weights(gl["pos"], gl["face"], rp, rJ, rW, names)
    remapL = np.array([namesL.index(n) for n in names], np.uint16)
    hmL = add_head_material(gL, limages, 1024, "warden_head_lod")
    add_prim(gL, lm, gl, remapL[JL], WL, hmL, attrs)
    smesh = gL.j["meshes"][smesh_i]
    sp = smesh["primitives"][0]
    filter_skin(gL, sp, lambda c: not (c[1] > 1.50 and abs(c[0]) < 0.2))
    JS, WS = head_weights(gs["pos"], gs["face"], rp, rJ, rW, names)
    add_prim(gL, smesh, gs, remapL[JS], WS, sp["material"], list(sp["attributes"].keys()))
    gL.save(os.path.join(pkg_out, "lod.glb"))
    log(f"lod.glb: head {len(gl['idx'])//3} tris, shadow head {len(gs['idx'])//3}")

    # ---- eyes ----
    hpos = Ghead[:3, 3]
    shot = os.path.join(work, "head_front.png")
    eyes = None
    cx, cz = front_render(lo, shot, hpos, os.path.join(work, "head_color.png"))
    if "eyes" in opt:
        bvh = BVHTree.FromObject(lo, bpy.context.evaluated_depsgraph_get())
        eyes = {}
        for side, pxy in zip(("r", "l"), opt["eyes"].split(";")):
            px, py = [float(v) for v in pxy.split(",")]
            x = cx + (px / 1024 - 0.5) * 0.4
            z = cz + (0.5 - py / 1024) * 0.4
            hit = bvh.ray_cast(mathutils.Vector((x, -1.0, z)), mathutils.Vector((0, 1, 0)))
            if hit[0] is None:
                raise SystemExit(f"eye {side}: no hit at {px},{py}")
            pb = np.array(hit[0]) + np.array([0, -0.004, 0])  # 4 mm in front of the socket's floor
            pg = b2g(pb[None])[0]
            loc = np.linalg.inv(Ghead) @ np.r_[pg, 1]
            eyes["l" if pg[0] > 0 else "r"] = [round(float(v), 4) for v in loc[:3]]
            log(f"eye {side}: package {np.round(pg, 4).tolist()} -> Head-local {eyes['l' if pg[0] > 0 else 'r']}")
    log("front check render:", shot)

    # ---- manifest ----
    m = json.load(open(os.path.join(pkg_in, "manifest.json")))
    m["name"] = name
    m.pop("hair", None)
    m["head"] = {
        "source": os.path.basename(bust_path) + " (TRELLIS.2 hooded bust), grafted by tools/assets/warden_head.py",
        "placedBy": os.path.basename(sculpt_path),
        "material": "warden_head", "tris": len(ga["idx"]) // 3, "lodTris": len(gl["idx"]) // 3, "shadowTris": len(gs["idx"]) // 3,
        "maps": TEX, "bones": sorted({names[j] for j in np.unique(J[W > 0.01])}),
        "dropped": sorted(HEAD_DROP), "faceRig": False,
        "eyes": eyes, "eyesFrame": "Head bone local, metres (glTF/Godot)",
    }
    if "tris" in m and isinstance(m["tris"], dict):
        s = m["tris"].get("surfaces", {})
        for k in list(s):
            if k in HEAD_DROP or k.startswith("hair"):
                s.pop(k)
        s["warden_head"] = len(ga["idx"]) // 3
        m["tris"]["note"] = "LOD0 surfaces before the head graft, plus warden_head; skin trimmed at the neck"
    json.dump(m, open(os.path.join(pkg_out, "manifest.json"), "w"), indent=1)
    log("done:", pkg_out, "bones", m["head"]["bones"])


if __name__ == "__main__":  # (warden_face.py imports the glb and bake helpers)
    main()
