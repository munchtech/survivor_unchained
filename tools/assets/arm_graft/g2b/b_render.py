# Blender: render a posed dump (pose_dump.py) from the town close-up camera at half size, workbench, smooth.
import bpy, sys, numpy as np, mathutils
a=sys.argv[sys.argv.index("--")+1:]; D=np.load(a[0]); out=a[1]; which=a[2] if len(a)>2 else "P"
P=D[which]*1.04+np.array([0,0.182,23.0]); T=D["T"]
key=np.round(P/1e-6).astype(np.int64); _,wid,=np.unique(key,axis=0,return_inverse=True)[:2]; wid=wid.ravel()
rep=np.zeros(wid.max()+1,int); rep[wid]=np.arange(len(P)); Pw=P[rep]; Tw=wid[T]
ok=(Tw[:,0]!=Tw[:,1])&(Tw[:,1]!=Tw[:,2])&(Tw[:,0]!=Tw[:,2]); Tw=Tw[ok]
Vb=np.c_[Pw[:,0],-Pw[:,2],Pw[:,1]]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
me=bpy.data.meshes.new("pose"); me.from_pydata(Vb.tolist(),[],Tw.tolist()); me.update()
me.polygons.foreach_set("use_smooth",np.ones(len(me.polygons),bool))
ob=bpy.data.objects.new("pose",me); bpy.context.scene.collection.objects.link(ob)
def cv(v): return mathutils.Vector((v[0],-v[2],v[1]))
O=cv((0,1.9285036,25.80094)); X=cv((1,0,0)); Y=cv((0,0.9986295,-0.05233624)); Z=cv((0,0.05233624,0.9986295))
cam=bpy.data.cameras.new("c"); cam.sensor_fit="VERTICAL"; cam.angle_y=np.radians(24); co=bpy.data.objects.new("c",cam)
M=mathutils.Matrix((X,Y,Z)).transposed().to_4x4(); M.translation=O; co.matrix_world=M
bpy.context.scene.collection.objects.link(co); sc=bpy.context.scene; sc.camera=co
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="SINGLE"; sc.display.shading.single_color=(0.6,0.6,0.6)
sc.render.resolution_x=1920; sc.render.resolution_y=1080; sc.render.resolution_percentage=50; sc.render.filepath=out
bpy.ops.render.render(write_still=True); print("RENDERED",out)
