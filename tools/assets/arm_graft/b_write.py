# Blender: put the grafted body (graft_data.npz) into Heroine and save the blend as a copy.
#   blender -b heroine_built.blend --python b_write.py -- graft_data.npz out.blend
import bpy, sys, numpy as np
a=sys.argv[sys.argv.index("--")+1:]; D=dict(np.load(a[0])); out=a[1]
obj=bpy.data.objects["Heroine"]; old=obj.data
V=D["V"]; fl=D["fl"]; fv=D["fv"]
me=bpy.data.meshes.new(old.name+"_graft")
me.vertices.add(len(V)); me.vertices.foreach_set("co",V.astype(np.float32).ravel())
me.loops.add(len(fv)); me.loops.foreach_set("vertex_index",fv.astype(np.int32))
me.polygons.add(len(fl)); ls=np.r_[0,np.cumsum(fl)[:-1]]
me.polygons.foreach_set("loop_start",ls.astype(np.int32)); me.polygons.foreach_set("loop_total",fl.astype(np.int32)) if hasattr(me.polygons[0],"loop_total") and False else None
me.update(calc_edges=True)
for m in old.materials: me.materials.append(m)
me.polygons.foreach_set("material_index",D["mat"].astype(np.int32))
me.polygons.foreach_set("use_smooth",np.ones(len(fl),bool))
uvl=me.uv_layers.new(name="Channel0"); uvl.data.foreach_set("uv",D["uv"].astype(np.float32).ravel())
ga=me.attributes.new("graft","INT","POINT"); ga.data.foreach_set("value",D["graft"].astype(np.int32))
ev=np.zeros(len(me.edges)*2,np.int32); me.edges.foreach_get("vertices",ev); ev=ev.reshape(-1,2)
emap={(min(x),max(x)):i for i,x in enumerate(ev.tolist())}
sh=np.zeros(len(me.edges),bool)
for e in D["sharp"].tolist(): sh[emap[(min(e),max(e))]]=True
sa=me.attributes.new("sharp_edge","BOOLEAN","EDGE"); sa.data.foreach_set("value",sh)
me.validate(verbose=True)
cn=D["cn"]; cn=cn/np.maximum(np.linalg.norm(cn,axis=1)[:,None],1e-12)
me.normals_split_custom_set([tuple(x) for x in cn.tolist()])
nm=old.name; old.name=nm+"_pre_graft"; me.name=nm
obj.data=me
W=D["W"]; names=[str(x) for x in D["names"]]
for n_ in names:
    if n_ not in obj.vertex_groups: obj.vertex_groups.new(name=n_)
assert [g.name for g in obj.vertex_groups]==names
for g in obj.vertex_groups:
    col=W[:,names.index(g.name)]; nz=np.nonzero(col>0)[0]
    for v in nz.tolist(): g.add([v],float(col[v]),"REPLACE")
bpy.data.meshes.remove(old)
nw=sum(len(v.groups) for v in me.vertices); print("WEIGHTS entries",nw)
print("WROTE verts",len(me.vertices),"faces",len(me.polygons),"loops",len(me.loops),"edges",len(me.edges),"sharp",int(sh.sum()))
bpy.ops.wm.save_as_mainfile(filepath=out,copy=True,compress=True)
print("SAVED",out)
