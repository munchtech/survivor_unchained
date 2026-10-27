# Blender: write her body's two skin images (as the ORIGINAL blend packs them) to PNG for the g2e bake.
#   blender -b heroine_built.blend --python b_img.py -- <work dir>   (old_body.png, old_graft.png; float pixels as 16-bit)
import bpy, sys, os, numpy as np
WK=sys.argv[sys.argv.index("--")+1:][0]
me=bpy.data.objects["Heroine"].data
for m,tag in zip(me.materials,("body","graft")):
    im=next(n.image for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image)
    w,h=im.size; px=np.array(im.pixels[:],np.float32).reshape(h,w,4)
    np.save(os.path.join(WK,"old_%s.npy"%tag),px)   # bottom row first, as Blender's
    print("IMG",tag,im.name,w,h,im.colorspace_settings.name)
