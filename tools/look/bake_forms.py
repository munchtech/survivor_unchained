"""B3 form maps (L1 texture authoring; docs/design/look/TEXTURE_AUTHORING.md): one Blender bake of an input mesh into the
painter's inputs. Deterministic (fixed samples and seed, no AA on the ID maps, a fixed unwrap).

    blender -b --factory-startup -P tools/look/bake_forms.py -- prop  MESH.glb OUT [--node lod0] [--variant 1] [--ppm 256]
    blender -b --factory-startup -P tools/look/bake_forms.py -- setts OUT [--tile 4] [--ppm 256] [--seed 7]

prop: the mesh (one node, or one variant of a packed flora file by COLOR.a = (v + 0.5) / 8), each loose part a block
(a rock's single shell split into a few big planes by normal), each block's class from the source's own palette (the
part's vertex tint: warm = wood/plank, neutral = iron, a flora rock file = rock), a fresh unwrap at one texel density
(ppm px per metre), written as OUT/mesh.glb (one material per class, named <asset>_<class> so the material library's
assign rules give that class) and OUT/forms.npz.
setts: a laid-stone layout (courses of chunky setts, wrapped so the tile repeats), each stone a bevelled block with a
slightly tilted top (rule 9 "chunky planes"), baked top-down onto a tile of T x T m (UV = world xz / T).

forms.npz (all OUT_SIZE x OUT_SIZE, row 0 = UV v 1): mask, blk (block id, -1 none), cls (class index), pos (world m),
nrm (world normal), ao (0.35 m), cavity (1 - AO at 3 cm: concave), convex (1 - inside-AO at 3 cm: convex edges),
thick (inside-AO at 0.4 m), and for setts tnrm (tangent-space normal of the stones on the tile). forms.json: the meta.
"""
import json, math, os, sys, time

import bmesh
import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
MODE = argv.pop(0)


def opt(name, default, cast=str):
    if name in argv:
        i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return cast(v)
    return default


PPM = opt("--ppm", 256, float)
SEED = opt("--seed", 7, int)
T0 = time.time()
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LIB = os.path.join(ROOT, "godot", "data", "look", "materials.json")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.seed = SEED; cy.use_denoising = False; cy.filter_width = 0.01
    try:
        pref = bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX', 'CUDA'):
            try:
                pref.compute_device_type = t; pref.get_devices()
                if any(d.type == t for d in pref.devices):
                    for d in pref.devices: d.use = d.type == t
                    cy.device = 'GPU'; break
            except Exception: pass
    except Exception: pass
    if not sc.world: sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0, 0, 0)
    return sc


def emit_mat(name, build):
    """A material whose surface is Emission of build(nodes, links) (a socket)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs[0], out.inputs[0])
    nt.links.new(build(nt.nodes, nt.links), em.inputs[0])
    return m


def ao_socket(dist, inside, samples=16):
    def b(nodes, links):
        a = nodes.new('ShaderNodeAmbientOcclusion'); a.inputs['Distance'].default_value = dist
        a.inside = inside; a.samples = samples; a.only_local = False
        return a.outputs['AO']
    return b


def attr_socket(name):
    def b(nodes, links):
        a = nodes.new('ShaderNodeAttribute'); a.attribute_name = name; a.attribute_type = 'GEOMETRY'
        return a.outputs['Vector']
    return b


def one_socket(nodes, links):
    v = nodes.new('ShaderNodeValue'); v.outputs[0].default_value = 1.0
    return v.outputs[0]


def geo_socket(out):
    def b(nodes, links):
        return nodes.new('ShaderNodeNewGeometry').outputs[out]
    return b


def bake(obj_low, size, mats, kind='EMIT', samples=1, high=None, normal_space='TANGENT'):
    """Bakes into a float image. mats goes on the source (the high objects if given, else the low itself); the
    target image is the active node of every material on the low."""
    sc = bpy.context.scene
    sc.cycles.samples = samples
    img = bpy.data.images.new("bake", size, size, float_buffer=True, alpha=False)
    src = high or [obj_low]
    keep = {}
    for o in src:
        keep[o.name] = [m for m in o.data.materials]
        if mats is not None:
            o.data.materials.clear(); o.data.materials.append(mats)
    added = []
    for m in obj_low.data.materials:
        nt = m.node_tree
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; nt.nodes.active = tn; added.append((nt, tn))
    bpy.ops.object.select_all(action='DESELECT')
    for o in (high or []): o.select_set(True)
    obj_low.select_set(True); bpy.context.view_layer.objects.active = obj_low
    bk = sc.render.bake
    bk.use_selected_to_active = bool(high); bk.cage_extrusion = 0.25; bk.max_ray_distance = 0.5
    bk.margin = 0; bk.use_clear = True; bk.normal_space = normal_space; bk.target = 'IMAGE_TEXTURES'
    bpy.ops.object.bake(type=kind); print("B3 baked", kind, size, round(time.time() - T0, 1), flush=True)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(size, size, 4)[::-1, :, :3].copy()
    for nt, tn in added: nt.nodes.remove(tn)
    if mats is not None:
        for o in src:
            o.data.materials.clear()
            for m in keep[o.name]: o.data.materials.append(m)
    bpy.data.images.remove(img)
    return a


def target_material(obj):
    m = bpy.data.materials.new("bake_target"); m.use_nodes = True
    obj.data.materials.clear(); obj.data.materials.append(m)
    return m


# ---------------------------------------------------------------------------------------------------------------- prop
def loose_parts(bm, crease_deg=80.0):
    """The source's parts: the exporter's split vertices welded back (5e-5 m), then faces joined across edges that turn
    by less than crease_deg (a stave's bevel to its face, 55 deg) and parted at sharper ones (two staves' groove, 110;
    a head under its chime), which are marked sharp so the export keeps them hard."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=5e-5)
    bm.normal_update(); bm.faces.ensure_lookup_table(); bm.faces.index_update()
    lim = math.cos(math.radians(crease_deg))
    cut = set()
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.link_faces[0].normal.dot(e.link_faces[1].normal) < lim:
            cut.add(e.index); e.smooth = False
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen: continue
        stack, part = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); part.append(g)
            for e in g.edges:
                if e.index in cut: continue
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        parts.append(part)
    return parts


def planes(faces, max_deg=38.0, min_share=0.04):
    """Big planes of one shell (a rock): region growing on the region's mean normal, tiny regions merged."""
    lim = math.cos(math.radians(max_deg))
    fs = sorted(faces, key=lambda f: -f.calc_area())
    lab, regs = {}, []
    for f in fs:
        if f.index in lab: continue
        r = len(regs); acc = f.normal * f.calc_area(); stack, mem = [f], [f]; lab[f.index] = r
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index in lab: continue
                    if h.normal.dot(acc.normalized()) >= lim:
                        lab[h.index] = r; stack.append(h); mem.append(h); acc += h.normal * h.calc_area()
        regs.append(mem)
    tot = sum(f.calc_area() for f in faces)
    for _ in range(3):
        for r, mem in enumerate(regs):
            if not mem or sum(f.calc_area() for f in mem) >= min_share * tot: continue
            nb = {}
            for f in mem:
                for e in f.edges:
                    for h in e.link_faces:
                        q = lab[h.index]
                        if q != r and regs[q]: nb[q] = nb.get(q, 0) + e.calc_length()
            if not nb: continue
            q = max(nb, key=nb.get)
            for f in mem: lab[f.index] = q
            regs[q] += mem; regs[r] = []
    return [m for m in regs if m]


def prop(mesh_path, out, node, variant, asset):
    sc = reset()
    bpy.ops.import_scene.gltf(filepath=mesh_path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    ob = next((o for o in objs if node and o.name.startswith(node)), objs[0])
    for o in objs:
        if o is not ob: bpy.data.objects.remove(o)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = ob.data
    col = me.color_attributes[0] if me.color_attributes else None
    bm = bmesh.new(); bm.from_mesh(me)
    ca = bm.loops.layers.color.get(col.name) if col and col.domain == 'CORNER' else None
    cv = bm.verts.layers.color.get(col.name) if col and col.domain == 'POINT' else None
    if cv is None and col is not None and ca is None: cv = bm.verts.layers.float_color.get(col.name)
    if ca is None and col is not None and cv is None: ca = bm.loops.layers.float_color.get(col.name)

    def fcol(f):
        cs = [l[ca] for l in f.loops] if ca else [l.vert[cv] for l in f.loops] if cv else [(1, 1, 1, 1)]
        return np.mean(np.array([tuple(c) for c in cs]), axis=0)
    if variant is not None:
        want = (variant + 0.5) / 8
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(fcol(f)[3] - want) > 0.05], context='FACES')
    bm.faces.ensure_lookup_table()
    rocky = 'flora' in mesh_path.replace('\\', '/')
    classes = []
    blk_of, cls_of = {}, {}
    for part in loose_parts(bm):
        c = np.mean([fcol(f)[:3] for f in part], axis=0)
        cname = 'rock' if rocky else ('plank' if c[0] > c[2] * 1.15 else 'iron')
        if cname not in classes: classes.append(cname)
        groups = planes(part) if cname == 'rock' else [part]
        for g in groups:
            b = len(set(blk_of.values()))
            for f in g: blk_of[f.index] = b; cls_of[f.index] = classes.index(cname)
    # one material per class (assign rules: <asset>_<class>)
    me.materials.clear()
    for c in classes: me.materials.append(bpy.data.materials.new(f"{asset}_{c}"))
    for f in bm.faces: f.material_index = cls_of[f.index]
    lb = bm.faces.layers.float.new("blk"); lc = bm.faces.layers.float.new("cls")
    for f in bm.faces: f[lb] = blk_of[f.index]; f[lc] = cls_of[f.index]
    area3 = sum(f.calc_area() for f in bm.faces)
    bm.to_mesh(me); bm.free()
    # the unwrap at one texel density
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.006, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    uva = 0.0
    for p in me.polygons:
        pts = uv[p.loop_start:p.loop_start + p.loop_total]
        x, y = pts[:, 0], pts[:, 1]; uva += 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    need = math.sqrt(area3 / max(uva, 1e-6)) * PPM
    size = int(2 ** round(math.log2(max(64, need))))  # (the nearest power of two: ppm lands within x0.7-1.4)
    ppm_real = size * math.sqrt(uva / area3)
    # export the mesh (re-UV'd, per-class materials) before the bake materials go on
    keep_mats = [m for m in me.materials]
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "mesh.glb"), use_selection=True, export_format='GLB',
                              export_attributes=False, export_vertex_color='NONE', export_materials='EXPORT')
    # bakes: the low is the mesh itself (one target material across its slots)
    tm = target_material(ob)
    maps = {}
    raw = bake(ob, size, emit_mat("ids", attr_socket("blk")), samples=1)
    maps['blk'] = raw[..., 0]
    maps['cls'] = bake(ob, size, emit_mat("cls", attr_socket("cls")), samples=1)[..., 0]
    maps['mask'] = bake(ob, size, emit_mat("one", one_socket), samples=1)[..., 0]
    maps['pos'] = bake(ob, size, emit_mat("pos", geo_socket('Position')), samples=1)
    maps['nrm'] = bake(ob, size, emit_mat("nrm", geo_socket('Normal')), samples=1)
    maps['ao'] = bake(ob, size, emit_mat("ao", ao_socket(0.35, False)), samples=24)[..., 0]
    maps['cavity'] = 1 - bake(ob, size, emit_mat("cav", ao_socket(0.03, False)), samples=24)[..., 0]
    maps['convex'] = 1 - bake(ob, size, emit_mat("cvx", ao_socket(0.03, True)), samples=24)[..., 0]
    maps['thick'] = bake(ob, size, emit_mat("thk", ao_socket(0.4, True)), samples=24)[..., 0]
    return finish(out, maps, dict(kind="prop", asset=asset, source=mesh_path, node=node, variant=variant, classes=classes,
                                  size=size, ppm=round(ppm_real, 1), area_m2=round(area3, 3)))


# --------------------------------------------------------------------------------------------------------------- setts
def setts(out, T):
    sc = reset()
    rng = np.random.default_rng(SEED)
    # courses of uneven height (summing to T, so the tile repeats), stones l_lo-l_hi courses long (materials.json classes.setts.paint.layout)
    lay = json.load(open(LIB, encoding="utf-8"))["classes"]["setts"]["paint"]["layout"]
    c_lo, c_hi = lay["course_m"]; l_lo, l_hi = lay["length_courses"]; joint = float(lay["joint_m"])
    hs = rng.uniform(c_lo, c_hi, 64); hs = hs[:max(1, int(np.searchsorted(np.cumsum(hs), T)))]; hs *= T / hs.sum()
    stones = []
    y0 = 0.0
    for rh in hs:
        x = rng.uniform(0, 0.5); xs = [x]
        while True:
            L = rh * rng.uniform(l_lo, l_hi)
            if xs[-1] + L > x + T - 0.25: break
            xs.append(xs[-1] + L)
        xs.append(x + T)  # the last one closes the course (wraps onto the first)
        for a, b in zip(xs[:-1], xs[1:]):
            stones.append((a, b, y0, y0 + rh))
        y0 += rh
    row_h = float(hs.mean())
    idx = 0
    high = []
    for (a, b, y0, y1) in stones:
        idx += 1
        j = joint * rng.uniform(0.7, 1.4)
        w, d = (b - a) - j, (y1 - y0) - j
        h = 0.08 + rng.uniform(-0.012, 0.012)
        tx, ty, yaw = rng.normal(0, math.radians(3.5)), rng.normal(0, math.radians(3.5)), rng.normal(0, math.radians(2.5))
        for ox in (-T, 0, T):
            for oy in (-T, 0, T):
                cx, cy = (a + b) / 2 + ox, (y0 + y1) / 2 + oy
                if not (-0.6 < cx < T + 0.6 and -0.6 < cy < T + 0.6): continue
                bm = bmesh.new()
                bmesh.ops.create_cube(bm, size=1.0)
                for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * d, (v.co.z + 0.5) * h - 0.04))
                bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.045, segments=4, profile=0.62, affect='EDGES')
                me = bpy.data.meshes.new("s"); bm.to_mesh(me); bm.free()
                o = bpy.data.objects.new(f"s{idx}", me); bpy.context.scene.collection.objects.link(o)
                o.location = (cx, cy, 0); o.rotation_euler = (tx, ty, yaw)
                o.pass_index = idx
                me.attributes.new("blk", 'FLOAT', 'FACE').data.foreach_set("value", [float(idx)] * len(me.polygons))
                for p in me.polygons: p.use_smooth = True
                high.append(o)
    # the bed between the stones (the joints' floor), block 0
    bpy.ops.mesh.primitive_plane_add(size=T + 1.5, location=(T / 2, T / 2, -0.02))
    bed = bpy.context.object; bed.data.attributes.new("blk", 'FLOAT', 'FACE').data.foreach_set("value", [0.0])
    high.append(bed)
    # (one high object: a bake against hundreds of selected objects is many times slower)
    bpy.ops.object.select_all(action='DESELECT')
    for o in high: o.select_set(True)
    bpy.context.view_layer.objects.active = high[0]
    bpy.ops.object.convert(target='MESH'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    high = [bpy.context.view_layer.objects.active]
    bpy.ops.mesh.primitive_plane_add(size=T, location=(T / 2, T / 2, 0.12))
    low = bpy.context.object
    target_material(low)
    size = int(2 ** math.ceil(math.log2(T * PPM)))
    maps = {}
    maps['blk'] = bake(low, size, emit_mat("ids", attr_socket("blk")), high=high, samples=1)[..., 0]
    maps['pos'] = bake(low, size, emit_mat("pos", geo_socket('Position')), high=high, samples=1)
    maps['nrm'] = bake(low, size, emit_mat("nrm", geo_socket('Normal')), high=high, samples=1)
    maps['tnrm'] = bake(low, size, None, kind='NORMAL', high=high, samples=4)
    maps['ao'] = bake(low, size, emit_mat("ao", ao_socket(0.35, False)), high=high, samples=24)[..., 0]
    maps['cavity'] = 1 - bake(low, size, emit_mat("cav", ao_socket(0.03, False)), high=high, samples=24)[..., 0]
    maps['convex'] = 1 - bake(low, size, emit_mat("cvx", ao_socket(0.03, True)), high=high, samples=24)[..., 0]
    maps['thick'] = np.ones((size, size), np.float32)
    maps['mask'] = np.ones((size, size), np.float32)
    maps['cls'] = np.zeros((size, size), np.float32)
    return finish(out, maps, dict(kind="setts", asset="setts", classes=["setts"], size=size, ppm=round(size / T, 1),
                                  tile_m=T, stones=len(stones), layout=dict(course_m=[c_lo, c_hi], length_courses=[l_lo, l_hi], row_h=round(row_h, 3), joint=joint, h=0.08, bevel=0.045, tilt_deg=3.5, yaw_deg=2.5)))


def save_npz(path, arrays):
    """np.savez_compressed with a fixed zip date (it stamps each entry with the clock: two runs would differ)."""
    import io, zipfile
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in arrays.items():
            b = io.BytesIO(); np.lib.format.write_array(b, np.asanyarray(v), allow_pickle=False)
            zi = zipfile.ZipInfo(k + ".npy", date_time=(1980, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, b.getvalue())


def finish(out, maps, meta):
    m = maps['mask'] > 0.5
    blk = np.where(m, np.round(maps['blk']), -1).astype(np.int32)
    save_npz(os.path.join(out, "forms.npz"), dict(mask=m, blk=blk, cls=np.round(maps['cls']).astype(np.int8),
                        **{k: v.astype(np.float16) for k, v in maps.items() if k not in ('mask', 'blk', 'cls')}))
    meta.update(seed=SEED, blender=bpy.app.version_string, blocks=int(blk.max()) + 1)
    if "source" in meta:  # (repo-relative with forward slashes: no absolute paths in the outputs)
        meta["source"] = os.path.relpath(meta["source"], ROOT).replace(os.sep, "/")
    json.dump({"seconds": round(time.time() - T0, 1)}, open(os.path.join(out, "timing.json"), "w"))
    json.dump(meta, open(os.path.join(out, "forms.json"), "w"), indent=1)
    print("B3 forms:", json.dumps(meta))


if MODE == "prop":
    mesh, out = argv.pop(0), argv.pop(0)
    node, var = opt("--node", None), opt("--variant", None, int)
    asset = opt("--asset", os.path.splitext(os.path.basename(mesh))[0])
    os.makedirs(out, exist_ok=True); prop(os.path.abspath(mesh), out, node, var, asset)
elif MODE == "setts":
    out = argv.pop(0); os.makedirs(out, exist_ok=True); setts(out, opt("--tile", 4.0, float))
