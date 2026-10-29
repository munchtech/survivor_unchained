# Blender: a posed, textured dump (rp_dump.py) rendered lit (Eevee, a warm key, a cool fill, a soft world) from the town
# close-up camera (24 deg, 2.80 m; ~9.4 px/cm at 100%). Diagnosis only (seams, breaks, stretch), not the game's shader.
#   blender -b --python rp_render.py -- <pose.npz> <out.png> <P|Pl|P0> <percent>
# Prints CAP_PX x y: the image pixel of the raised arm's shoulder cap (for a 1:1 crop).
import bpy, sys, os, numpy as np, mathutils
from bpy_extras.object_utils import world_to_camera_view
a=sys.argv[sys.argv.index("--")+1:]; D=np.load(a[0]); out=a[1]; which=a[2]; pct=int(a[3]); td=os.path.dirname(os.path.abspath(a[0]))
P=D[which]*1.04+np.array([0,0.182,23.0]); T=D["T"]; UV=D["UV"]; TM=D["TM"]; names=[str(x) for x in D["names"]]
Vb=np.c_[P[:,0],-P[:,2],P[:,1]]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
me=bpy.data.meshes.new("pose"); me.from_pydata(Vb.tolist(),[],T.tolist()); me.update()
uvl=me.uv_layers.new(name="UV"); uvl.data.foreach_set("uv",np.c_[UV[T.ravel(),0],1-UV[T.ravel(),1]].astype(np.float32).ravel())
for n in names:
    m=bpy.data.materials.new(n); m.use_nodes=True; nt=m.node_tree; bs=nt.nodes["Principled BSDF"]
    tx=nt.nodes.new("ShaderNodeTexImage"); tx.image=bpy.data.images.load(os.path.join(td,n+".png")); nt.links.new(tx.outputs["Color"],bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value=0.55
    try: bs.inputs["Subsurface Weight"].default_value=0.15; bs.inputs["Subsurface Radius"].default_value=(0.01,0.004,0.002)
    except Exception: pass
    me.materials.append(m)
me.polygons.foreach_set("material_index",TM.astype(np.int32)); me.polygons.foreach_set("use_smooth",np.ones(len(T),bool))
ob=bpy.data.objects.new("pose",me); bpy.context.scene.collection.objects.link(ob)
def cv(v): return mathutils.Vector((v[0],-v[2],v[1]))
O=cv((0,1.9285036,25.80094)); X=cv((1,0,0)); Y=cv((0,0.9986295,-0.05233624)); Z=cv((0,0.05233624,0.9986295))
cam=bpy.data.cameras.new("c"); cam.sensor_fit="VERTICAL"; cam.angle_y=np.radians(24); co=bpy.data.objects.new("c",cam)
M=mathutils.Matrix((X,Y,Z)).transposed().to_4x4(); M.translation=O; co.matrix_world=M
sc=bpy.context.scene; sc.collection.objects.link(co); sc.camera=co
for nm,rot,en,col in (("key",(55,0,35),3.2,(1,0.93,0.85)),("fill",(70,0,-60),1.0,(0.8,0.88,1)),("rim",(110,0,180),1.5,(1,1,1))):
    L=bpy.data.lights.new(nm,"SUN"); L.energy=en; L.color=col; L.angle=np.radians(8); lo=bpy.data.objects.new(nm,L)
    lo.rotation_euler=[np.radians(x) for x in rot]; sc.collection.objects.link(lo)
w=bpy.data.worlds.new("w"); w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.18,0.19,0.22,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.6; sc.world=w
for eng in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE"):
    try: sc.render.engine=eng; break
    except Exception: pass
sc.view_settings.view_transform="AgX" if "AgX" in [x.identifier for x in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.resolution_x=1920; sc.render.resolution_y=1080; sc.render.resolution_percentage=pct; sc.render.filepath=out
sc.render.film_transparent=False
# the raised arm's cap: graft-material points farthest out on that side, above the shoulder line
gm=names.index("skin_graft"); vs=np.unique(T[TM==gm]); sd=-1 if which=="P" else 1
cand=vs[(np.sign(P[vs,0])==sd)&(np.abs(P[vs,0])>0.12)]; c=Vb[cand].mean(0)
p=world_to_camera_view(sc,co,mathutils.Vector(c)); print("CAP_PX %d %d"%(round(p.x*1920),round((1-p.y)*1080)))
bpy.ops.render.render(write_still=True); print("RENDERED",out)
