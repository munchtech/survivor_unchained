import bpy,numpy as np,sys
out=sys.argv[sys.argv.index("--")+1]
o=bpy.data.objects["Heroine"]; m=o.data; arm=bpy.data.objects["Armature"]
nv=len(m.vertices); P=np.zeros(nv*3); m.vertices.foreach_get("co",P); P=P.reshape(-1,3)
ls=np.zeros(len(m.polygons),int); m.polygons.foreach_get("loop_start",ls)
lt=np.zeros(len(m.polygons),int); m.polygons.foreach_get("loop_total",lt)
lv=np.zeros(len(m.loops),int); m.loops.foreach_get("vertex_index",lv)
mi=np.zeros(len(m.polygons),int); m.polygons.foreach_get("material_index",mi)
uv=np.zeros(len(m.loops)*2); m.uv_layers["Channel0"].data.foreach_get("uv",uv)
cn=np.zeros(len(m.loops)*3); m.corner_normals.foreach_get("vector",cn)
gr=np.zeros(nv,int); m.attributes["graft"].data.foreach_get("value",gr)
se=np.zeros(len(m.edges),bool); m.attributes["sharp_edge"].data.foreach_get("value",se)
ev=np.zeros(len(m.edges)*2,int); m.edges.foreach_get("vertices",ev)
sm=np.zeros(len(m.polygons),bool); m.polygons.foreach_get("use_smooth",sm)
VG=np.zeros((nv,len(o.vertex_groups)),np.float32)
for v in m.vertices:
    for g in v.groups: VG[v.index,g.group]=g.weight
names=[g.name for g in o.vertex_groups]
bones={b.name:(np.array(b.head_local),np.array(b.tail_local)) for b in arm.data.bones}
bn=list(bones); bh=np.array([bones[k][0] for k in bn]); bt=np.array([bones[k][1] for k in bn])
print("MW",[list(r) for r in o.matrix_world],"AW",[list(r) for r in arm.matrix_world],"parent_type",o.parent_type)
np.savez(out,P=P,ls=ls,lt=lt,lv=lv,mi=mi,uv=uv.reshape(-1,2),cn=cn.reshape(-1,3),graft=gr,sharp=se,ev=ev.reshape(-1,2),smooth=sm,VG=VG,names=np.array(names),bn=np.array(bn),bh=bh,bt=bt,mats=np.array([x.name for x in m.materials]))
print("DUMPED",nv,len(m.polygons),"lt",np.bincount(lt),"sharp",se.sum(),"graft",np.bincount(gr),"mi",np.bincount(mi),"smooth",sm.mean())
