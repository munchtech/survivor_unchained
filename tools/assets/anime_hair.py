"""Our hairstyles fitted to the woman survivor's head (anime_female.py's
body): each piece of hair keeps its height above the scalp, measured along
the ray from the middle of the Quaternius head it was made for, and stands
that far above her scalp along the same ray. (Scaled whole, a close crop
sinks into her rounder skull and shows only on top.) What hangs well clear
of the head follows the scalp it grows from, smoothly.

    python tools/assets/anime_hair.py godot/art/people/anime_female.glb \\
        ".packs/Universal Base Characters/.../Godot - UE/Superhero_Female_FullBody.gltf" \\
        ".packs/Universal Base Characters/.../Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)" \\
        godot/art/people

Writes her_<style>.glb beside her body: the hair bound to her head bone,
without its textures (the game dresses it in the Quaternius hair's own
material, People.HairOn). Needs Blender's Python module (pip install bpy)."""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

her_glb, quat_gltf, hair_dir, out_dir = sys.argv[-4:]
STYLES = ('Hair_Long', 'Hair_Buns', 'Hair_BuzzedFemale')


def imported(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    return [o for o in bpy.data.objects if o not in before]


def world(o):
    M = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in o.data.vertices])
    return V @ M[:3, :3].T + M[:3, 3]


def head(o):
    """The head's surface (the body's largest piece: not the eyes and lashes
    set into it) as a tree to cast rays at, and the middle of the head."""
    V = world(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = np.zeros(len(V), bool); best = []
    for v in bm.verts:
        if seen[v.index]: continue
        comp, todo = [], [v]
        seen[v.index] = True
        while todo:
            a = todo.pop(); comp.append(a.index)
            for e in a.link_edges:
                b = e.other_vert(a)
                if not seen[b.index]: seen[b.index] = True; todo.append(b)
        if len(comp) > len(best): best = comp
    keep = np.zeros(len(V), bool); keep[best] = True
    polys = [list(p.vertices) for p in o.data.polygons if keep[p.vertices[0]]]
    g = o.vertex_groups.get('Head').index
    inhead = np.array([any(x.group == g and x.weight > 0.5 for x in v.groups) for v in o.data.vertices]) & keep
    H = V[inhead]
    centre = (H.min(0) + H.max(0)) / 2
    bm.free()
    return BVHTree.FromPolygons([Vector(p) for p in V], polys), centre, H.max(0) - H.min(0)


bpy.ops.wm.read_factory_settings(use_empty=True)
hers = imported(her_glb)
harm = next(o for o in hers if o.type == 'ARMATURE')
her = next(o for o in hers if o.type == 'MESH')
her_tree, ch, her_size = head(her)
quat = imported(quat_gltf)
qbody = next(o for o in quat if o.type == 'MESH' and o.name.startswith('Superhero'))
q_tree, cq, q_size = head(qbody)
k = float(np.mean(her_size / q_size))
print('head centres', np.round(cq, 3), '->', np.round(ch, 3), 'sizes', np.round(q_size, 3), np.round(her_size, 3), 'k', round(k, 3))
for o in quat: bpy.data.objects.remove(o, do_unlink=True)


def cast(tree, o, u):
    hit = tree.ray_cast(Vector(o), Vector(u))
    return hit[3] if hit[0] is not None else None


for style in STYLES:
    parts = imported(os.path.join(hair_dir, f'{style}.gltf'))
    for hm in [o for o in parts if o.type == 'MESH' and o.find_armature()]:
        P = world(hm)
        n = len(P)
        base = ch + (P - cq) * k                   # the hair scaled whole, set on her head
        D = np.zeros((n, 3)); c = np.zeros(n)
        for i, p in enumerate(P):
            d = p - cq; L = np.linalg.norm(d); u = d / L
            rq, rh = cast(q_tree, cq, u), cast(her_tree, ch, u)
            if rq is None or rh is None: continue
            D[i] = ch + u * (rh + (L - rq)) - base[i]
            # Near the scalp the measure holds; hanging hair follows it.
            c[i] = np.clip((0.05 - (L - rq)) / 0.03, 0, 1)
        adj = [[] for _ in range(n)]
        for e in hm.data.edges:
            a, b = e.vertices; adj[a].append(b); adj[b].append(a)
        for _ in range(300):
            avg = np.array([D[a].mean(0) if a else D[i] for i, a in enumerate(adj)])
            D = c[:, None] * D + (1 - c[:, None]) * avg
        fit = base + D
        # Bound to her head bone alone, in her space.
        hm.parent = None
        hm.matrix_world = Matrix.Identity(4)
        for v, co in zip(hm.data.vertices, fit): v.co = co
        hm.data.update()
        hm.parent = harm
        hm.matrix_parent_inverse = harm.matrix_world.inverted()
        for m in [m for m in hm.modifiers if m.type == 'ARMATURE']: hm.modifiers.remove(m)
        hm.vertex_groups.clear()
        hm.vertex_groups.new(name='Head').add(list(range(n)), 1.0, 'REPLACE')
        hm.modifiers.new('Armature', 'ARMATURE').object = harm
        print(style, hm.name, n, 'vertices; moved', round(float(np.linalg.norm(D, axis=1).mean()) * 1000, 1), 'mm on average from the plain scale')
    bpy.ops.object.select_all(action='DESELECT')
    for hm in [o for o in parts if o.type == 'MESH' and o.find_armature()]: hm.select_set(True)
    harm.select_set(True)
    out = os.path.join(out_dir, f'her_{style}.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_animations=False,
                              export_skins=True, export_yup=True, export_image_format='NONE', export_morph=False)
    print('wrote', out)
    for o in parts:
        if o.name in bpy.data.objects: bpy.data.objects.remove(o, do_unlink=True)
