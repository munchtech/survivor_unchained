import sys,numpy as np
W=r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7"
sys.path.insert(0,W+r"\tools\anim")
from skin import Body, Gltf, PEOPLE
PXCM=1080/(2*2.80*np.tan(np.radians(12)))/100*1.04   # px per mesh-cm at the close-near (24 deg, 2.80 m), world scale 1.04
def load():
    b=Body.heroine(jiggle=False,head=True,helpers=True)
    # normals in Body order
    g=Gltf(PEOPLE/"heroine.glb"); N=[]
    for n in g.js["nodes"]:
        if "mesh" in n and "skin" in n and n["name"] in ("Heroine","HeroineHead"):
            for pr in g.js["meshes"][n["mesh"]]["primitives"]:
                N.append(g.accessor(pr["attributes"]["NORMAL"]).astype(float))
    b.N=np.concatenate(N); assert len(b.N)==len(b.P)
    # weld by position
    key=np.round(b.P/1e-5).astype(np.int64)
    _,b.wid,b.wcnt=np.unique(key,axis=0,return_inverse=True,return_counts=True)
    b.wid=b.wid.ravel()
    return b
def armframe(b,s):
    I=b.sk.index;R=b.rest
    H=R[I[f"upperarm_{s}"]][:3,3];E=R[I[f"lowerarm_{s}"]][:3,3];Hd=R[I[f"hand_{s}"]][:3,3]
    u=(E-H)/np.linalg.norm(E-H); L=np.linalg.norm(E-H)
    up=np.array([0,1.,0]); up=up-u*(up@u); up/=np.linalg.norm(up)
    fr=np.cross(u,up); 
    if fr[2]<0: fr=-fr
    return H,E,Hd,u,L,up,fr
def regions(b,s="r"):
    H,E,Hd,u,L,up,fr=armframe(b,s)
    P=b.P; d=P-H; t=(d@u)/L; rr=d-np.outer(d@u,u)
    phi=np.degrees(np.arctan2(rr@fr,rr@up))   # 0 up, 90 front, 180/-180 down (toward pit)
    rad=np.linalg.norm(rr,axis=1)
    sk=b.piece=="Heroine"; head=b.piece=="HeroineHead"
    side=(P[:,0]<0) if s=="r" else (P[:,0]>0)
    armish=sk&side&(rad<0.075)
    uf=(Hd-E)/np.linalg.norm(Hd-E); tf=((P-E)@uf)/np.linalg.norm(Hd-E); rf=np.linalg.norm((P-E)-np.outer((P-E)@uf,uf),axis=1)
    reg={
     "shoulder_top":armish&(t>-0.3)&(t<0.15)&(np.abs(phi)<45),
     "deltoid":armish&(t>=0.0)&(t<0.45)&(np.abs(phi)<75),
     "pit":armish&(t>-0.15)&(t<0.3)&(np.abs(phi)>130),
     "bicep":armish&(t>0.4)&(t<0.8)&(np.abs(phi-90)<45),
     "upperarm_under":armish&(t>0.4)&(t<0.85)&(np.abs(phi)>135),
     "inner_elbow":armish&(t>0.85)&(t<1.12)&(np.abs(phi-90)<50),
     "forearm":sk&side&(tf>0.3)&(tf<0.7)&(rf<0.06),
     "breast":sk&side&(P[:,1]>1.22)&(P[:,1]<1.40)&(np.abs(P[:,0])>0.03)&(np.abs(P[:,0])<0.17)&(P[:,2]>0.07),
     "torso_side":sk&side&(P[:,1]>1.05)&(P[:,1]<1.22)&(np.abs(P[:,0])>0.11)&(np.abs(P[:,2])<0.06),
     "face":head&(P[:,2]>0.06)&(P[:,1]>1.62),
    }
    return reg,dict(t=t,phi=phi,rad=rad,u=u,H=H,L=L)
def edges(T):
    e=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); e.sort(1); return np.unique(e,axis=0)
