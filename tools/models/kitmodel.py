"""Shared helpers for the game's own models, built in Blender (bpy) and
painted with the village kit's sheets so they sit beside the kit's pieces.

    <venv with bpy>/bin/python tools/models/<model>.py

Blender runs headless (the `bpy` wheel from PyPI, 4.2 LTS; a Blender install
also works: `blender -b -P tools/models/<model>.py`). A model script builds
its parts with the helpers here, each part given a kit material and a way
of laying the sheet on it:

  tile   a tiling sheet (rough stone, roof tiles) at the kit's own density
         (half a sheet per metre), projected on each face;
  band   one band of a trim sheet (a timber grain, a stone slab): along the
         part's long axis the band tiles, across a face it spans the band;
  ring   a tiling sheet wrapped round a vertical axis (a round wall).

export() writes public/assets/env/custom/<Name>.gltf (+ .bin) and puts the
kit's own materials on it: the same texture files as the village pieces
(KTX2, ../village/), so a custom piece costs no texture memory of its own
and is weathered like the rest (render/env.ts). Its bounds go into the
env manifest. Blender is Z-up; the glTF comes out Y-up, as the game wants.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ENV = os.path.join(ROOT, 'public', 'assets', 'env')
OUT = os.path.join(ENV, 'custom')

# Where each kit material's sheet bands lie, in glTF v (0 at the top of the
# image), measured on the sheets.
BANDS = {
    'MI_WoodTrim': {'grain': (0.005, 0.30), 'boards': (0.315, 0.60), 'ends': (0.625, 0.775), 'iron': (0.80, 0.94)},
    'MI_RockTrim': {'cobbles': (0.005, 0.30), 'slab': (0.32, 0.575), 'bricks': (0.59, 0.995)},
}
DENSITY = 0.5  # sheets per metre, as the kit's walls and roofs have them

# Materials that are not the kit's: plain PBR, written into the glTF as is.
PLAIN = {
    'MI_WellWater': {'baseColorFactor': [0.02, 0.035, 0.04, 1], 'metallicFactor': 0, 'roughnessFactor': 0.08},
    'MI_Rope': {'baseColorFactor': [0.17, 0.12, 0.07, 1], 'metallicFactor': 0, 'roughnessFactor': 0.95},
    'MI_Iron': {'baseColorFactor': [0.16, 0.15, 0.14, 1], 'metallicFactor': 0.7, 'roughnessFactor': 0.55},
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m


def part(name, obj, mat, lay, **opts):
    """Give a Blender object its kit material and a way of laying the sheet."""
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(material(mat))
    obj['lay'] = lay
    obj['lay_opts'] = json.dumps(opts)
    return obj


def box(name, size, at, mat, lay='band', rot=(0, 0, 0), bevel=0.0, **opts):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new('bevel', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'ANGLE'
    return part(name, o, mat, lay, **opts)


def cylinder(name, r, depth, at, mat, lay='band', rot=(0, 0, 0), sides=12, r2=None, caps=True, inward=False, **opts):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r, radius2=r if r2 is None else r2, depth=depth, location=at, rotation=rot,
                                    end_fill_type='NGON' if caps else 'NOTHING')
    o = bpy.context.active_object
    if inward:  # a wall seen from inside (a well's shaft)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(o.data); bm.free()
    return part(name, o, mat, lay, **opts)


def smooth(obj, angle=40):
    """Smooth shading, with edges sharper than `angle` kept hard."""
    obj.data.shade_smooth()
    try:
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    except AttributeError:
        pass
    return obj


# ---------------------------------------------------------------- UVs --

def _set(loop, uv_layer, u, v_gltf):
    loop[uv_layer].uv = (u, 1.0 - v_gltf)  # Blender's v runs up


def lay_uvs(obj):
    """Lay the sheet on an object (after its modifiers are applied), in world
    metres, as its 'lay' says."""
    lay = obj.get('lay', 'tile')
    opts = json.loads(obj.get('lay_opts', '{}'))
    mat = obj.data.materials[0].name if obj.data.materials else ''
    density = opts.get('density', DENSITY)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.verify()
    M = obj.matrix_world
    axis = Vector(opts.get('axis', (0, 0, 1))).normalized()
    centre = Vector(opts.get('centre', (0, 0, 0)))
    u0 = opts.get('u0', 0.0)
    for f in bm.faces:
        n = (M.to_3x3() @ f.normal).normalized()
        pts = [M @ l.vert.co for l in f.loops]
        if lay == 'ring':
            # Round a vertical axis: u runs round (in metres of arc), v up.
            r = sum(((p - centre).to_2d().length for p in pts)) / len(pts)
            angs = [math.atan2(p.y - centre.y, p.x - centre.x) for p in pts]
            base = angs[0]
            for l, p, a in zip(f.loops, pts, angs):
                a = base + math.atan2(math.sin(a - base), math.cos(a - base))  # no seam jump within a face
                _set(l, uv, u0 + a * r * density, 0.3 - p.z * density)
            continue
        # A tangent frame on the face: u along the part's axis (as near as the
        # face allows), v across.
        t = axis - n * n.dot(axis)
        if t.length < 0.3:  # the face looks along the axis: an end
            t = Vector((1, 0, 0)) - n * n.x
            if t.length < 0.3:
                t = Vector((0, 1, 0)) - n * n.y
        t.normalize()
        b = n.cross(t).normalized()
        # Roofs: the sheet's down runs down the slope, on either pitch.
        if opts.get('down') and b.z > 0:
            b = -b
        us = [p.dot(t) for p in pts]
        vs = [p.dot(b) for p in pts]
        if lay == 'tile':
            for l, u_, v_ in zip(f.loops, us, vs):
                _set(l, uv, u0 + u_ * density, v_ * density)
            continue
        # band: the part's long faces span the band; its ends take the
        # end-grain (or whatever 'end' names).
        bands = BANDS[mat]
        is_end = abs(n.dot(axis)) > 0.9
        top, bot = bands[opts.get('end', 'ends') if is_end and opts.get('end', 'ends') in bands else opts.get('band', next(iter(bands)))]
        vmin, vmax = min(vs), max(vs)
        span = max(1e-4, vmax - vmin)
        for l, u_, v_ in zip(f.loops, us, vs):
            k = (v_ - vmin) / span
            if is_end:
                uu = u0 + (u_ - min(us)) / max(1e-4, max(us) - min(us)) * (bot - top)  # a square of end grain
                _set(l, uv, uu, top + k * (bot - top))
            else:
                _set(l, uv, u0 + u_ * density * opts.get('stretch', 1.0), top + k * (bot - top))
    bm.to_mesh(obj.data)
    bm.free()


# -------------------------------------------------------------- export --

def _kit_materials():
    """Every village material's glTF definition, with its textures."""
    found = {}
    vdir = os.path.join(ENV, 'village')
    for fn in sorted(os.listdir(vdir)):
        if not fn.endswith('.gltf'):
            continue
        g = json.load(open(os.path.join(vdir, fn)))
        for m in g.get('materials', []):
            if m['name'] not in found:
                found[m['name']] = (m, g)
    return found


def export(name):
    """Apply modifiers, lay UVs, export, then give it the kit's materials."""
    os.makedirs(OUT, exist_ok=True)
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH':
            continue
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
        lay_uvs(o)
        # Positions in the model's own frame: no node transforms left over.
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # One object per material keeps the draw calls down.
    by_mat = {}
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            by_mat.setdefault(o.data.materials[0].name, []).append(o)
    for mat, objs in by_mat.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        bpy.context.active_object.name = f'{name}_{mat}'
    path = os.path.join(OUT, f'{name}.gltf')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_image_format='NONE',
                              export_apply=True, export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', use_selection=False)
    _inject(path, name)


def _inject(path, name):
    g = json.load(open(path))
    kit = _kit_materials()
    g.setdefault('textures', []); g.setdefault('images', []); g.setdefault('samplers', [])
    tex_map = {}
    for i, m in enumerate(g.get('materials', [])):
        nm = m['name']
        if nm in PLAIN:
            g['materials'][i] = {'name': nm, 'pbrMetallicRoughness': PLAIN[nm]}
            continue
        if nm not in kit:
            raise SystemExit(f'{nm}: not a village material, and not in PLAIN')
        src, sg = kit[nm]
        new = json.loads(json.dumps(src))

        def take(ref):
            ti = ref['index']
            if (id(sg), ti) in tex_map:
                ref['index'] = tex_map[(id(sg), ti)]
                return
            t = json.loads(json.dumps(sg['textures'][ti]))
            srcidx = t.get('source', t.get('extensions', {}).get('KHR_texture_basisu', {}).get('source'))
            img = dict(sg['images'][srcidx])
            img['uri'] = '../village/' + img['uri']
            if 'extras' in img:
                del img['extras']
            g['images'].append(img)
            ii = len(g['images']) - 1
            if 'extensions' in t and 'KHR_texture_basisu' in t['extensions']:
                t['extensions']['KHR_texture_basisu']['source'] = ii
            else:
                t['source'] = ii
            if 'sampler' in t:
                g['samplers'].append(sg['samplers'][t['sampler']])
                t['sampler'] = len(g['samplers']) - 1
            g['textures'].append(t)
            tex_map[(id(sg), ti)] = len(g['textures']) - 1
            ref['index'] = tex_map[(id(sg), ti)]
        pbr = new.get('pbrMetallicRoughness', {})
        for k in ('baseColorTexture', 'metallicRoughnessTexture'):
            if k in pbr:
                take(pbr[k])
        for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if k in new:
                take(new[k])
        g['materials'][i] = new
    for k in ('textures', 'images', 'samplers'):
        if not g[k]:
            del g[k]
    if 'textures' in g:
        for key in ('extensionsUsed', 'extensionsRequired'):
            ext = set(g.get(key, []))
            ext.add('KHR_texture_basisu')
            g[key] = sorted(ext)
    json.dump(g, open(path, 'w'), separators=(',', ':'))
    # Bounds, for the manifest (from the positions' min/max).
    lo, hi = [1e9] * 3, [-1e9] * 3
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            a = g['accessors'][p['attributes']['POSITION']]
            lo = [min(x, y) for x, y in zip(lo, a['min'])]
            hi = [max(x, y) for x, y in zip(hi, a['max'])]
    mpath = os.path.join(ENV, 'manifest.json')
    man = json.load(open(mpath))
    man.setdefault('custom', {})[name] = {'min': [round(v, 3) for v in lo], 'max': [round(v, 3) for v in hi]}
    json.dump(man, open(mpath, 'w'), separators=(',', ':'))
    tris = sum(g['accessors'][p['indices']]['count'] // 3 for mesh in g['meshes'] for p in mesh['primitives'])
    print(f'{name}: {tris} triangles, {len(g["materials"])} materials, bounds {lo} .. {hi}')
