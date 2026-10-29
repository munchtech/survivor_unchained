# Blender: write positions P (.npy, blend coords, dump order) and weights VG (.npy, dump group order) into Heroine; moved
# points' corners (and their 1-ring) take the skin's own normal, the rest keep their custom normals. Saves a copy.
#   blender -b src.blend --python w_write.py -- P.npy VG.npy names.npy out.blend
import bpy, sys, numpy as np
a=sys.argv[sys.argv.index("--")+1:]
P=np.load(a[0]); VG=np.load(a[1]); names=[str(x) for x in np.load(a[2])]; out=a[3]
obj=bpy.data.objects["Heroine"]; me=obj.data; nv=len(me.vertices); assert P.shape==(nv,3) and VG.shape[0]==nv
assert [g.name for g in obj.vertex_groups]==names, "group order differs"
nl=len(me.loops)
c_old=np.empty(nl*3,np.float32); me.corner_normals.foreach_get("vector",c_old); c_old=c_old.reshape(-1,3)
P0=np.empty(nv*3); me.vertices.foreach_get("co",P0); P0=P0.reshape(-1,3)
mv=np.abs(P-P0).max(1)>1e-7
ev=np.empty(len(me.edges)*2,np.int64); me.edges.foreach_get("vertices",ev); ev=ev.reshape(-1,2)
ring=mv.copy(); ring[ev[mv[ev[:,0]],1]]=True; ring[ev[mv[ev[:,1]],0]]=True
me.vertices.foreach_set("co",P.astype(np.float32).ravel()); me.update()
# auto normals from a copy without custom normals
tmp=me.copy(); to=bpy.data.objects.new("tmpN",tmp); bpy.context.scene.collection.objects.link(to)
with bpy.context.temp_override(object=to,active_object=to,selected_objects=[to]):
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
c_auto=np.empty(nl*3,np.float32); tmp.corner_normals.foreach_get("vector",c_auto); c_auto=c_auto.reshape(-1,3)
bpy.data.objects.remove(to); bpy.data.meshes.remove(tmp)
lv=np.empty(nl,np.int64); me.loops.foreach_get("vertex_index",lv)
use=ring[lv]; cn=np.where(use[:,None],c_auto,c_old)
me.normals_split_custom_set([tuple(x) for x in cn.tolist()])
print("MOVED",int(mv.sum()),"RING",int(ring.sum()),"corners renormaled",int(use.sum()))
nW=0
for gi,g in enumerate(obj.vertex_groups):
    g.remove(list(range(nv)))
    col=VG[:,gi]; nz=np.nonzero(col>1e-6)[0]
    for v in nz.tolist(): g.add([v],float(col[v]),"REPLACE")
    nW+=len(nz)
print("WEIGHTS entries",nW)
bpy.ops.wm.save_as_mainfile(filepath=out,copy=True,compress=True)
print("SAVED",out)
