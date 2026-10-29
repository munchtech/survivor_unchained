# blender -b --factory-startup -P tools/assets/smith_hammer.py -- <out.glb>
# NPC 18 (Brannoc): a smith's cross-peen hammer, hand-modeled in code, our own model (no source asset).
# Head 11 x 4 x 4 cm dark forged steel: a chamfered square face at +X, a wedge peen at -X whose edge runs across the
# handle (cross-peen); an ash handle 38 cm, oval (long across the head's line), swelling at the butt, waisted under the
# head, its top showing through the eye with a steel wedge line. About 300 tris, two matte materials, no texture.
# anchor_grip (Arms.Make): on the handle 7 cm up from the butt; its -Y runs up the haft to the head, its +Z is the
# face's direction (as an axe's edge), so the chop leads with the face.
import bpy, bmesh, sys, math
from mathutils import Matrix, Vector

out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, rgb, metal, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    return m

STEEL = mat('steel', (0.055, 0.058, 0.062), 0.75, 0.58)
ASH = mat('ash', (0.42, 0.29, 0.17), 0.0, 0.78)

def octo(hy, hz, c):
    """An octagon in the YZ plane: half extents hy, hz with chamfer c (corners cut)."""
    return [(hy, -hz + c), (hy, hz - c), (hy - c, hz), (-hy + c, hz), (-hy, hz - c), (-hy, -hz + c), (-hy + c, -hz), (hy - c, -hz)]

def loft(bm, rings, close_a=True, close_b=True):
    vs = [[bm.verts.new(p) for p in r] for r in rings]; n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if close_a: bm.faces.new(list(reversed(vs[0])))
    if close_b: bm.faces.new(vs[-1])
    return vs

HZ = 0.375  # the head's centre height on the handle (Blender Z up; the handle along +Z, the butt at 0)

# head: sections along X (face at +X, peen at -X); (x, half y, half z, chamfer)
H = [(0.056, 0.0165, 0.0165, 0.0055), (0.0515, 0.0195, 0.0195, 0.0045), (0.030, 0.0190, 0.0190, 0.0040),
     (0.016, 0.0175, 0.0200, 0.0035), (-0.016, 0.0175, 0.0200, 0.0035), (-0.026, 0.0185, 0.0185, 0.0040),
     (-0.044, 0.0185, 0.0095, 0.0030), (-0.0545, 0.0180, 0.0025, 0.0012)]
bm = bmesh.new()
rings = [[(x, y, HZ + z) for (y, z) in octo(hy, hz, c)] for (x, hy, hz, c) in reversed(H)]
loft(bm, rings)
me = bpy.data.meshes.new('head'); bm.to_mesh(me); bm.free()
head = bpy.data.objects.new('head', me); bpy.context.scene.collection.objects.link(head); me.materials.append(STEEL)

# handle: oval rings up +Z; (z, half x, half y)
N = 10
Hd = [(0.0, 0.0150, 0.0110), (0.006, 0.0168, 0.0124), (0.030, 0.0162, 0.0120), (0.120, 0.0148, 0.0110),
      (0.250, 0.0128, 0.0095), (0.330, 0.0120, 0.0090), (0.352, 0.0135, 0.0098), (HZ + 0.0205, 0.0135, 0.0098)]
bm = bmesh.new()
rings = [[(rx * math.cos(2 * math.pi * k / N), ry * math.sin(2 * math.pi * k / N), z) for k in range(N)] for (z, rx, ry) in Hd]
loft(bm, rings)
me = bpy.data.meshes.new('handle'); bm.to_mesh(me); bm.free()
handle = bpy.data.objects.new('handle', me); bpy.context.scene.collection.objects.link(handle); me.materials.append(ASH)

# the steel wedge across the handle's top (a thin bar in the eye)
bm = bmesh.new()
rings = [[(x, y, HZ + 0.0207) for (y, x) in [(-0.0015, -0.012), (0.0015, -0.012), (0.0015, 0.012), (-0.0015, 0.012)]],
         [(x, y, HZ + 0.0215) for (y, x) in [(-0.0012, -0.011), (0.0012, -0.011), (0.0012, 0.011), (-0.0012, 0.011)]]]
loft(bm, rings)
me = bpy.data.meshes.new('wedge'); bm.to_mesh(me); bm.free()
wedge = bpy.data.objects.new('wedge', me); bpy.context.scene.collection.objects.link(wedge); me.materials.append(STEEL)

# one mesh, flat-ish shading on the head (crisp forged facets), smooth on the handle
for o in (head, handle, wedge):
    for p in o.data.polygons: p.use_smooth = (o is handle)
bpy.ops.object.select_all(action='DESELECT')
for o in (head, handle, wedge): o.select_set(True)
bpy.context.view_layer.objects.active = handle; bpy.ops.object.join(); ham = bpy.context.active_object; ham.name = 'smith_hammer'
ham.data.name = 'smith_hammer'
ham['kind'] = 'blunt'

# anchor_grip: local Z = -world Z (so glTF -Y runs up the haft to the head), local -Y = +X (glTF +Z = the face's way)
a = bpy.data.objects.new('anchor_grip', None); bpy.context.scene.collection.objects.link(a)
a.matrix_world = Matrix(((0, -1, 0, 0), (-1, 0, 0, 0), (0, 0, -1, 0.07), (0, 0, 0, 1)))
a.parent = ham; a.matrix_parent_inverse = ham.matrix_world.inverted()

tris = sum(len(p.vertices) - 2 for p in ham.data.polygons)
print('smith_hammer tris', tris)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_extras=True, export_apply=True, export_yup=True)
print('wrote', out)
if len(sys.argv) > sys.argv.index('--') + 2:   # a preview png (workbench, three-quarter)
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = sc.render.resolution_y = 600
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
    t = Vector((0, 0, 0.21)); cam.location = t + Vector((0.45, -0.55, 0.25)); cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50; sc.render.filepath = sys.argv[sys.argv.index('--') + 2]; bpy.ops.render.render(write_still=True)
