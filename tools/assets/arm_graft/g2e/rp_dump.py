# Body 1 g2e: an exported heroine.glb checked and posed for the textured renders (rp_render.py).
#   PYTHONPATH=tools/assets/arm_graft/g2a python rp_dump.py <people dir with heroine.glb> <out.npz> [tex dir to compare]
# Writes her posed points (reaver_show f24 right arm raised, its mirror for the left, idle_reaver_town f0), triangles,
# UVs, each triangle's material, and the glb's embedded skin images (out dir, <material>.png). With a tex dir, says whether
# the glb's body and graft images equal heroine_body_paint.png / heroine_graft.png there, pixel for pixel.
import os, sys, numpy as np, cv2
os.environ["ANIM_PEOPLE"]=os.path.abspath(sys.argv[1])
from common import *
import meas
from skin import Gltf
b=load(); meas.prep(b); out=sys.argv[2]; od=os.path.dirname(os.path.abspath(out))
g=Gltf(os.path.join(sys.argv[1],"heroine.glb")); UV=[]; MI=[]; names=[]
for n in g.js["nodes"]:
    if "mesh" in n and "skin" in n and n["name"] in ("Heroine","HeroineHead"):
        for pr in g.js["meshes"][n["mesh"]]["primitives"]:
            uv=g.accessor(pr["attributes"]["TEXCOORD_0"]).astype(float); UV.append(uv)
            mn=g.js["materials"][pr["material"]]["name"]
            if mn not in names: names.append(mn)
            MI.append(np.full(len(uv),names.index(mn)))
UV=np.concatenate(UV); MI=np.concatenate(MI); assert len(UV)==len(b.P)
import struct, json
raw=open(os.path.join(sys.argv[1],"heroine.glb"),"rb").read(); jl=struct.unpack("<I",raw[12:16])[0]; js=json.loads(raw[20:20+jl])
binst=20+jl+8
for mn in names:
    m=next(x for x in js["materials"] if x["name"]==mn); ti=m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    im=js["images"][js["textures"][ti]["source"]]; bv=js["bufferViews"][im["bufferView"]]
    data=np.frombuffer(raw[binst+bv.get("byteOffset",0):binst+bv.get("byteOffset",0)+bv["byteLength"]],np.uint8)
    px=cv2.imdecode(data,cv2.IMREAD_COLOR); cv2.imwrite(os.path.join(od,mn+".png"),px)
    print("GLB IMAGE",mn,im.get("name"),im.get("mimeType"),px.shape)
    if len(sys.argv)>3:
        ref={"Material_0.001":"heroine_body_paint.png","skin_graft":"heroine_graft.png"}.get(mn)
        if ref: r=cv2.imread(os.path.join(sys.argv[3],ref)); print("  equals",ref,":",r is not None and r.shape==px.shape and bool((r==px).all()))
G=b.globals(b.clip("reaver_show"),24)
T=b.T; tm=MI[T[:,0]]
np.savez(out,P=b.pose(G),Pl=b.pose(meas.mirrorG(b,G)),P0=b.pose(b.globals(b.clip("idle_reaver_town"),0)),T=T,UV=UV,TM=tm,names=np.array(names))
print("POSED",len(b.P),len(T),names)
