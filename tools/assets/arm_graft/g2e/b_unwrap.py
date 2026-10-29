# Blender, Body 1 g2e step 2: unwrap the arm patch on plan.npz's seams (SLIM, minimum stretch); dump its corner UVs.
#   blender -b heroine_built_armroot.blend --python b_unwrap.py -- <work dir>     (writes unwrap.npz; saves nothing)
import bpy, bmesh, sys, os, numpy as np
WK=sys.argv[sys.argv.index("--")+1:][0]; P=np.load(os.path.join(WK,"plan.npz")); nk=int(P["nk"]); mat=P["mat"]
IT=int(os.environ.get("UV_IT","60"))
o=bpy.data.objects["Heroine"]; me=o.data
for ob in bpy.context.view_layer.objects: ob.select_set(False)
bpy.context.view_layer.objects.active=o; o.select_set(True)
nf=len(me.polygons); assert len(mat)==nf, (len(mat),nf)
me.polygons.foreach_set("material_index",mat.astype(np.int32))
ev=np.zeros(len(me.edges)*2,np.int64); me.edges.foreach_get("vertices",ev); ev=ev.reshape(-1,2)
emap={(min(a),max(a)):i for i,a in enumerate(ev.tolist())}
seam=np.zeros(len(me.edges),bool)
for a,b in P["seam"].tolist(): seam[emap[(min(a,b),max(a,b))]]=True
me.edges.foreach_set("use_seam",seam)
sel=np.zeros(nf,bool); sel[nk:]=True
me.polygons.foreach_set("select",sel)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_mode(type="FACE")
bm=bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
for f in bm.faces: f.select_set(f.index>=nk)
bmesh.update_edit_mesh(me)
bpy.ops.uv.unwrap(method="MINIMUM_STRETCH",fill_holes=True,correct_aspect=True,margin=0.01,iterations=IT,no_flip=True)
bpy.ops.object.mode_set(mode="OBJECT")
uv=np.zeros(len(me.loops)*2); me.uv_layers["Channel0"].data.foreach_get("uv",uv); uv=uv.reshape(-1,2)
ls=np.zeros(nf,int); me.polygons.foreach_get("loop_start",ls); lt=np.zeros(nf,int); me.polygons.foreach_get("loop_total",lt)
np.savez(os.path.join(WK,"unwrap.npz"),uv=uv,ls=ls,lt=lt,nk=nk)
print("UNWRAPPED patch faces",nf-nk,"loops",int(lt[nk:].sum()))
