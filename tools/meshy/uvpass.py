# blender -b -P uvpass.py -- <glb> <out_prefix> [cam dx dy dz] [ortho scale] [aim drop below the top]: a face camera (ortho, aimed at the head);
# writes <out>_uv.png (16-bit: R,G = UV, B = 1 on the mesh), <out>_n.png (geometry normal *0.5+0.5, no normal map) and
# <out>_alb.png (the unlit base colour): the screen <-> atlas map glb_patch.screen_to_uv uses
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; glb, out = a[0], a[1]
CAM = (float(a[2]), float(a[3]), float(a[4])) if len(a) > 4 else (2.0, -2.6, 0.3)
SC = float(a[5]) if len(a) > 5 else 0.26
DROP = float(a[6]) if len(a) > 6 else 0.16   # the aim, below the top
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.use_denoising = False
sc.render.filter_size = 0.01
sc.render.resolution_x = 700; sc.render.resolution_y = 700; sc.view_settings.view_transform = 'Raw'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0
ms = [o for o in bpy.data.objects if o.type == 'MESH']
P = [o.matrix_world @ v.co for o in ms for v in o.data.vertices]; z1 = max(p.z for p in P)
top = [p for p in P if p.z > z1 - 0.25]; cx = sum(p.x for p in top) / len(top)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = SC
tgt = Vector((cx, 0, z1 - DROP)); ymin = min(p.y for p in top); tgt.y = ymin + 0.08
eye = tgt + Vector(CAM); cam.location = eye; cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
base_img = None
for m0 in bpy.data.materials:
    if m0.node_tree:
        for nd in m0.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED' and nd.inputs['Base Color'].links: base_img = nd.inputs['Base Color'].links[0].from_node.image
def mk(kind):
    m = bpy.data.materials.new(kind); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); c = nt.nodes.new('ShaderNodeCombineXYZ')
    if kind == 'uv':
        u = nt.nodes.new('ShaderNodeUVMap'); s = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(u.outputs[0], s.inputs[0])
        nt.links.new(s.outputs[0], c.inputs[0]); nt.links.new(s.outputs[1], c.inputs[1]); c.inputs[2].default_value = 1
        nt.links.new(c.outputs[0], e.inputs[0])
    elif kind == 'alb':
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = base_img; t.interpolation = 'Closest'; nt.links.new(t.outputs[0], e.inputs[0])
    else:
        g = nt.nodes.new('ShaderNodeNewGeometry'); vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'MULTIPLY_ADD'; vm.inputs[1].default_value = (0.5,0.5,0.5); vm.inputs[2].default_value = (0.5,0.5,0.5); nt.links.new(g.outputs['Normal'], vm.inputs[0]); nt.links.new(vm.outputs[0], e.inputs[0])
    nt.links.new(e.outputs[0], o.inputs[0]); return m
for kind in ('uv', 'n', 'alb'):
    sc.view_settings.view_transform = 'Standard' if kind == 'alb' else 'Raw'; sc.render.image_settings.color_depth = '8' if kind == 'alb' else '16'
    m = mk(kind)
    for o in ms:
        for i in range(len(o.material_slots)): o.material_slots[i].material = m
        if not o.material_slots: o.data.materials.append(m)
    sc.render.filepath = out + '_' + kind + '.png'; bpy.ops.render.render(write_still=True)
print('IMAGES', [(i.name, i.size[:]) for i in bpy.data.images])
