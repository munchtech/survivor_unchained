"""The Long Cut's thrown rock: 12 broken chunks (0.08-0.4 m, slabs and shards with flat faces where they broke), each
its own object under ~250 tris, exported to godot/art/fx/longcut/chunks.glb (no vertex colours: Blender 4.5 writes
an all-white COLOR_0 otherwise). Two materials: rock_dark (the weathered outside) and rock_broken (the fresh broken
faces, a shade warmer and lighter).

    blender -b -P tools/fxsim/longcut_chunks.py -- [--seed 5] [--out godot/art/fx/longcut/chunks.glb] [--preview OUT.png]
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector, noise


def opt(k, d, t=str):
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return t(a[a.index(k) + 1]) if k in a else d


def mat(name, rgb, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,)
    b.inputs["Roughness"].default_value = rough
    return m


def chunk(i, rng, size, kind, m_out, m_broken):
    """A hull of jittered points in a slab or shard's proportions, then cut by 2-4 planes (the broken faces)."""
    if kind == "slab":
        sx, sy, sz = 1.0, rng.uniform(0.55, 0.9), rng.uniform(0.18, 0.32)
    elif kind == "shard":
        sx, sy, sz = 1.0, rng.uniform(0.25, 0.45), rng.uniform(0.2, 0.35)
    else:  # block
        sx, sy, sz = 1.0, rng.uniform(0.6, 0.85), rng.uniform(0.45, 0.7)
    bm = bmesh.new()
    pts = []
    for _ in range(26):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized() * rng.uniform(0.75, 1.0)
        pts.append(bm.verts.new((v.x * sx * 0.5, v.y * sy * 0.5, v.z * sz * 0.5)))
    bmesh.ops.convex_hull(bm, input=pts)
    for f in bm.faces:
        f.material_index = 0
    # the breaks: planes through the body, each cutting a flat face
    ncut = rng.randint(2, 4)
    for c in range(ncut):
        n = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 0.6))).normalized()
        d = rng.uniform(0.12, 0.32) * min(sx, sy * 1.6)
        before = set(bm.faces)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=n * d, plane_no=n, clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            fill = bmesh.ops.edgeloop_fill(bm, edges=edges)
            for f in fill["faces"]:
                f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # a little roughness on the broken faces (they are never glass-flat): nudge their verts along the normal
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.co += v.normal * 0.025 * noise.noise(v.co * 7.0 + Vector((i * 3.1, 0, 0)))
    me = bpy.data.meshes.new(f"chunk_{i:02d}")
    bm.to_mesh(me); bm.free()
    me.materials.append(m_out); me.materials.append(m_broken)
    ob = bpy.data.objects.new(f"chunk_{i:02d}", me)
    bpy.context.scene.collection.objects.link(ob)
    # scale so its longest side is `size`, origin at its centre of mass
    dims = ob.dimensions
    k = size / max(dims)
    ob.scale = (k, k, k)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_VOLUME")
    ob.location = (0, 0, 0)
    for p in me.polygons:
        p.use_smooth = False
    ob.select_set(False)
    return ob


def main():
    seed = opt("--seed", 5, int)
    out = os.path.abspath(opt("--out", "godot/art/fx/longcut/chunks.glb"))
    rng = random.Random(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m_out = mat("rock_dark", (0.045, 0.040, 0.035), 0.9)
    m_broken = mat("rock_broken", (0.11, 0.085, 0.065), 0.8)
    sizes = [0.08, 0.10, 0.12, 0.14, 0.16, 0.19, 0.22, 0.25, 0.28, 0.32, 0.36, 0.40]
    kinds = ["block", "shard", "slab", "block", "shard", "slab", "slab", "shard", "block", "slab", "shard", "slab"]
    obs = [chunk(i, rng, s, k, m_out, m_broken) for i, (s, k) in enumerate(zip(sizes, kinds))]
    for ob in obs:
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        print("CHUNK", ob.name, "tris", tris, "dims %.2f %.2f %.2f" % tuple(ob.dimensions))
    for ob in obs:
        ob.select_set(True)
    kw = dict(filepath=out, export_format="GLB", use_selection=True, export_apply=True, export_normals=True,
              export_texcoords=False, export_materials="EXPORT")
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color="NONE")
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_colors=False)
    print("EXPORTED", out)

    pv = opt("--preview", "")
    if pv:
        # the twelve in a row, lit by a low key, for the sheet
        x = 0.0
        for ob in obs:
            ob.location = (x + ob.dimensions.x / 2, 0, 0)
            ob.rotation_euler = (0.4, 0.3, 0.6)
            x += max(ob.dimensions.x, 0.12) + 0.08
        sc = bpy.context.scene
        cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = x + 0.1
        cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam)
        cam.location = (x / 2, -4, 2.2); cam.rotation_euler = (math.radians(62), 0, 0); sc.camera = cam
        ld = bpy.data.lights.new("key", "SUN"); ld.energy = 4.0
        lo = bpy.data.objects.new("key", ld); sc.collection.objects.link(lo); lo.rotation_euler = (0.7, 0.2, 0.9)
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.33, 0.3, 1)
        sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
        sc.render.resolution_x, sc.render.resolution_y = 1600, 300
        sc.render.filepath = os.path.abspath(pv)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", pv)


main()
