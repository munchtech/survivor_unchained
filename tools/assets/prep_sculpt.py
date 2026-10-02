"""A sculpted figure made ready to bind: the body kept at full resolution
and the hair (strands are most of such a model's triangles) brought down
on its own, so the triangle budget goes to the body.

    blender -b --python tools/assets/prep_sculpt.py -- <in.glb> <out.glb> [--hair-faces 25000]

The body is the largest connected piece (seam copies joined); everything
else whose middle is above the shoulders is hair. The hair is decimated
by itself; the body is untouched.
"""
import sys

import bmesh
import bpy
import numpy as np

ARGS = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = ARGS[0], ARGS[1]
HAIR = int(ARGS[ARGS.index("--hair-faces") + 1]) if "--hair-faces" in ARGS else 25000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obj = next(o for o in bpy.data.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

me = obj.data
co = np.array([v.co[:] for v in me.vertices])
up = 2 if np.ptp(co[:, 2]) >= np.ptp(co[:, 1]) else 1
n = len(co)
h0, h1 = co[:, up].min(), co[:, up].max()
shoulder = h0 + (h1 - h0) * 0.78
# Hair by its paint: strongly saturated red above the shoulders (the hair
# is joined to the scalp, so it is not a piece of its own).
img = None
for mat in me.materials:
    for nd in (mat.node_tree.nodes if mat and mat.use_nodes else []):
        if nd.type == "TEX_IMAGE" and nd.image:
            img = nd.image
            break
px = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
uv = me.uv_layers.active.data
hair_f = np.zeros(len(me.polygons), bool)
for f in me.polygons:
    c = co[list(f.vertices)].mean(0)
    if c[up] < shoulder:
        continue
    u = np.mean([uv[l].uv[0] for l in f.loop_indices])
    v = np.mean([uv[l].uv[1] for l in f.loop_indices])
    r, g, bl = px[int(np.clip(v, 0, 0.9999) * img.size[1]), int(np.clip(u, 0, 0.9999) * img.size[0]), :3]
    if r > 0.25 and r > g * 1.7 and r > bl * 1.7:
        hair_f[f.index] = True
hair_v = np.zeros(n, bool)
for f in me.polygons:
    if hair_f[f.index]:
        hair_v[list(f.vertices)] = True
print("HAIR", int(hair_f.sum()), "faces of", len(me.polygons))

# Paint where the generator never saw skin: where the thighs touched, the
# texture was left pale. On the faces of the inner thighs and the crotch,
# texels far paler and greyer than her skin are painted over from the skin
# round them (inpainting).
import cv2
H, W_ = img.size[1], img.size[0]
mask_region = np.zeros((H, W_), np.uint8)
xs = co[:, 0]
crotch = None
mid = co[(np.abs(xs) < 0.01) & (co[:, up] > h0 + (h1 - h0) * 0.3) & (co[:, up] < h0 + (h1 - h0) * 0.6)]
crotch = mid[:, up].min() if len(mid) else h0 + (h1 - h0) * 0.45
for f in me.polygons:
    c = co[list(f.vertices)].mean(0)
    if crotch - 0.25 < c[up] < crotch + 0.08 and abs(c[0]) < 0.12:
        pts = np.array([[uv[l].uv[0] * W_, (1 - uv[l].uv[1]) * H] for l in f.loop_indices], np.int32)
        cv2.fillConvexPoly(mask_region, pts, 255)
tex = (np.clip(px[::-1, :, :3], 0, 1) * 255).astype(np.uint8)   # top-down rows
hsv = cv2.cvtColor(tex, cv2.COLOR_RGB2HSV).astype(np.float32)
skin = (mask_region > 0)
med_v, med_s = np.median(hsv[..., 2][skin]), np.median(hsv[..., 1][skin])
pale = skin & (hsv[..., 1] < med_s * 0.55) & (hsv[..., 2] > med_v * 0.9)
pale = cv2.dilate(pale.astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
print("PALE", int((pale > 0).sum()), "texels repainted of", int(skin.sum()))
fixed = cv2.inpaint(cv2.cvtColor(tex, cv2.COLOR_RGB2BGR), pale, 9, cv2.INPAINT_TELEA)
fixed = cv2.cvtColor(fixed, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
out = px.copy()
out[::-1, :, :3] = fixed
img.pixels[:] = out.ravel()
img.pack()

# Close the body's openings at the crotch (the sculpt left one): every
# hole whose edge lies within a few centimetres of the crotch is filled
# and the new surface relaxed into its surroundings.
bm2 = bmesh.new()
bm2.from_mesh(me)
bmesh.ops.remove_doubles(bm2, verts=bm2.verts, dist=1e-6)
edges = [e for e in bm2.edges if e.is_boundary and abs(e.verts[0].co[up] - crotch) < 0.06 and abs(e.verts[0].co.x) < 0.06]
filled = bmesh.ops.holes_fill(bm2, edges=edges, sides=0)
newf = filled["faces"]
if newf:
    bmesh.ops.triangulate(bm2, faces=newf)
    ring = set(v for f in newf for v in f.verts)
    for _ in range(3):
        ring |= set(e.other_vert(v) for v in list(ring) for e in v.link_edges)
    for _ in range(12):
        bmesh.ops.smooth_vert(bm2, verts=list(ring), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm2.to_mesh(me)
bm2.free()
me.update()
print("HOLES", len(edges), "edges closed with", len(newf), "faces")
# The faces are numbered afresh: the hair is found again.
co = np.array([v.co[:] for v in me.vertices])
n = len(co)
uv = me.uv_layers.active.data
hair_f = np.zeros(len(me.polygons), bool)
for f in me.polygons:
    c = co[list(f.vertices)].mean(0)
    if c[up] < shoulder:
        continue
    u = np.mean([uv[l].uv[0] for l in f.loop_indices])
    v = np.mean([uv[l].uv[1] for l in f.loop_indices])
    r, g, bl = px[int(np.clip(v, 0, 0.9999) * img.size[1]), int(np.clip(u, 0, 0.9999) * img.size[0]), :3]
    if r > 0.25 and r > g * 1.7 and r > bl * 1.7:
        hair_f[f.index] = True
hair_v = np.zeros(n, bool)
for f in me.polygons:
    if hair_f[f.index]:
        hair_v[list(f.vertices)] = True


# Split the hair into an object of its own, decimate it, join it back.
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
for v in bm.verts:
    v.select = False
for f in bm.faces:
    f.select = bool(hair_f[f.index])
bmesh.update_edit_mesh(me)
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode="OBJECT")
hair = next(o for o in bpy.data.objects if o.type == "MESH" and o != obj)
print("HAIR FACES", len(hair.data.polygons), "BODY FACES", len(obj.data.polygons))
if len(hair.data.polygons) > HAIR:
    d = hair.modifiers.new("d", "DECIMATE")
    d.ratio = HAIR / len(hair.data.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    hair.select_set(True)
    bpy.context.view_layer.objects.active = hair
    bpy.ops.object.modifier_apply(modifier="d")
bpy.ops.object.select_all(action="DESELECT")
hair.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()
print("OUT FACES", len(obj.data.polygons))
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True)
