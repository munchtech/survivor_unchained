from lib import *
import math
def qmul(a,b):
    x1,y1,z1,w1=a; x2,y2,z2,w2=b
    return [w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2]
def aq(ax,deg):
    h=math.radians(deg)/2; v=[0,0,0]; v[ax]=math.sin(h); return v+[math.cos(h)]
def posed(G_,ops,inv,uncut=0.03):
    g=G_.g; N=g["nodes"]; keep=[dict(n) for n in N]
    if uncut:
        h=[n for n in N if n.get("name")=="Head"][0]; t=np.array(h["translation"]); L=np.linalg.norm(t); h["translation"]=list(t*(L+uncut)/L)
    for jn,ax,dg in ops:
        i=[k for k,n in enumerate(N) if n.get("name")==jn][0]; N[i]["rotation"]=qmul(N[i].get("rotation",[0,0,0,1]),aq(ax,dg))
    out=skinned(G_,84); hd=skinned(G_,86)[0]["skin"]
    S=np.concatenate([o["skin"] for o in out[:2]])
    for i in range(len(N)): N[i].clear(); N[i].update(keep[i])
    U=np.zeros((inv.max()+1,3)); U[inv]=S
    return U,hd
def pose_ops(back,turn,tilt=0):
    o=[]
    for j in ("neck_01","Head"):
        o+= [(j,0,back/2),(j,1,turn/2),(j,2,tilt/2)]
    return o
