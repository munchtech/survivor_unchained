# Blender, Body 1 g2e step 4: the patch's materials (plan.npz) and new UVs (newuv.npz) into Heroine, her two skin images
# swapped for the re-baked copies (packed; filepaths point at the copies; datablock names kept, so the glb's image names
# and everything that finds them by material stay the same). Saves the blend in place (heroine_built_armroot.blend only).
#   blender -b heroine_built_armroot.blend --python b_apply.py -- <work dir> <tex dir>
import bpy, sys, os, numpy as np
a=sys.argv[sys.argv.index("--")+1:]; WK,TEX=a[0],a[1]
assert os.path.basename(bpy.data.filepath)!="heroine_built.blend", "never the original"
P=np.load(os.path.join(WK,"plan.npz")); N=np.load(os.path.join(WK,"newuv.npz")); nk=int(P["nk"])
o=bpy.data.objects["Heroine"]; me=o.data; nf=len(me.polygons); assert len(P["mat"])==nf
me.polygons.foreach_set("material_index",P["mat"].astype(np.int32))
ls=np.zeros(nf,int); me.polygons.foreach_get("loop_start",ls); lt=np.zeros(nf,int); me.polygons.foreach_get("loop_total",lt)
L=np.concatenate([np.arange(ls[i],ls[i]+lt[i]) for i in range(nk,nf)]); assert len(L)==len(N["uv"])
uv=np.zeros(len(me.loops)*2); me.uv_layers["Channel0"].data.foreach_get("uv",uv); uv=uv.reshape(-1,2)
uv[L]=N["uv"]; me.uv_layers["Channel0"].data.foreach_set("uv",uv.astype(np.float32).ravel())
me.edges.foreach_set("use_seam",np.zeros(len(me.edges),bool))
for m,fn in zip(me.materials,("heroine_body_paint.png","heroine_graft.png")):
    node=next(n for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image); old=node.image; name=old.name
    im=bpy.data.images.load(os.path.join(TEX,fn)); im.colorspace_settings.name=old.colorspace_settings.name; im.pack()
    node.image=im; old.name=name+"_pre_g2e"; im.name=name
    if old.users==0: bpy.data.images.remove(old)
    print("IMAGE",m.name,im.name,im.filepath,tuple(im.size))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
print("SAVED",bpy.data.filepath,"patch loops",len(L))
