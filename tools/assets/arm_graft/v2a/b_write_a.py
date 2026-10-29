# Blender, Body 2 A step 5: positions, weights, the patch's own material + UVs into Heroine; saves a COPY under a new name.
#   blender -b heroine_built_armroot.blend --python b_write_a.py -- <P.npy> <VG.npy> <work dir> <out.blend>
# Positions/weights as g2b/w_write.py (moved points' corners and their 1-ring take the skin's own normal). The patch's
# faces (>= nk) take material skin_arm (a copy of Material_0.001's node tree; its base-colour image swapped for
# heroine_arm_paint, packed) and their loops the UVs of arm_uv.npz (bake_a.py).
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
P = np.load(a[0]); VG = np.load(a[1]); WK = a[2]; out = a[3]
assert os.path.basename(out) not in ("heroine_built.blend", "heroine_built_armroot.blend"), "never the sources"
names = [str(x) for x in np.load(os.path.join(WK, "wts.npz"))["names"]]
obj = bpy.data.objects["Heroine"]; me = obj.data; nv = len(me.vertices); assert P.shape == (nv, 3) and VG.shape[0] == nv
assert [g.name for g in obj.vertex_groups] == names, "group order differs"
nl = len(me.loops)
c_old = np.empty(nl * 3, np.float32); me.corner_normals.foreach_get("vector", c_old); c_old = c_old.reshape(-1, 3)
P0 = np.empty(nv * 3); me.vertices.foreach_get("co", P0); P0 = P0.reshape(-1, 3)
mv = np.abs(P - P0).max(1) > 1e-7
ev = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
ring = mv.copy(); ring[ev[mv[ev[:, 0]], 1]] = True; ring[ev[mv[ev[:, 1]], 0]] = True
me.vertices.foreach_set("co", P.astype(np.float32).ravel()); me.update()
tmp = me.copy(); to = bpy.data.objects.new("tmpN", tmp); bpy.context.scene.collection.objects.link(to)
with bpy.context.temp_override(object=to, active_object=to, selected_objects=[to]):
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
c_auto = np.empty(nl * 3, np.float32); tmp.corner_normals.foreach_get("vector", c_auto); c_auto = c_auto.reshape(-1, 3)
bpy.data.objects.remove(to); bpy.data.meshes.remove(tmp)
lv = np.empty(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
use = ring[lv]; cn = np.where(use[:, None], c_auto, c_old)
me.normals_split_custom_set([tuple(x) for x in cn.tolist()])
print("MOVED", int(mv.sum()), "RING", int(ring.sum()), "corners renormaled", int(use.sum()))
nW = 0
for gi, g in enumerate(obj.vertex_groups):
    g.remove(list(range(nv)))
    col = VG[:, gi]; nz = np.nonzero(col > 1e-6)[0]
    for v in nz.tolist(): g.add([v], float(col[v]), "REPLACE")
    nW += len(nz)
print("WEIGHTS entries", nW)
# --- the patch's material and UVs
U = np.load(os.path.join(WK, "arm_uv.npz")); nk = int(U["nk"]); nf = len(me.polygons)
ls = np.zeros(nf, int); me.polygons.foreach_get("loop_start", ls); lt = np.zeros(nf, int); me.polygons.foreach_get("loop_total", lt)
L = np.concatenate([np.arange(ls[i], ls[i] + lt[i]) for i in range(nk, nf)]); assert len(L) == len(U["uv"])
uv = np.zeros(nl * 2); me.uv_layers["Channel0"].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
uv[L] = U["uv"]; me.uv_layers["Channel0"].data.foreach_set("uv", uv.astype(np.float32).ravel())
m0 = bpy.data.materials["Material_0.001"]; m2 = bpy.data.materials.get("skin_arm") or m0.copy(); m2.name = "skin_arm"
im = bpy.data.images.load(os.path.join(WK, "arm_paint.png")); im.name = "heroine_arm_paint"
base = None
for nd in m2.node_tree.nodes:
    if nd.type == "TEX_IMAGE" and nd.image: print("TEXNODE", nd.name, nd.image.name, tuple(nd.image.size), [l.to_socket.name for o in nd.outputs for l in o.links])
for nd in m2.node_tree.nodes:
    if nd.type == "TEX_IMAGE" and nd.image and any(l.to_socket.name == "Base Color" for o in nd.outputs for l in o.links): base = nd
base = base or next(nd for nd in m2.node_tree.nodes if nd.type == "TEX_IMAGE" and nd.image)
im.colorspace_settings.name = base.image.colorspace_settings.name; im.pack(); base.image = im
if "skin_arm" not in [m.name for m in me.materials]: me.materials.append(m2)
mi = [m.name for m in me.materials].index("skin_arm")
mat = np.zeros(nf, np.int32); me.polygons.foreach_get("material_index", mat); mat[nk:] = mi; me.polygons.foreach_set("material_index", mat)
me.update()
print("MATERIAL skin_arm index", mi, "faces", nf - nk, "image", im.name, tuple(im.size), "packed", bool(im.packed_file))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=True, compress=True)
print("SAVED", out)
