"""r2top.py glb th0 th1 [pose]: the most raised points (3 cm fit) in that band, c01 (or rest), and their weights."""
from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); Wx=dense(G_,inv); a0,a1=float(sys.argv[2]),float(sys.argv[3])
names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]
th,r=cyl(U0); dh=cKDTree(H).query(U0)[0]
idx=np.nonzero((U0[:,1]>1.47)&(U0[:,1]<1.67)&(th>a0)&(th<a1)&(r<0.17)&(dh>0.002))[0]
allidx=np.nonzero((U0[:,1]>1.45)&(U0[:,1]<1.69)&(r<0.18))[0]
from r2m import POSES
op=dict(POSES)[sys.argv[4]] if len(sys.argv)>4 else dict(POSES)["c01"]
U=apply(skin_custom(G_,op,None,0),U0,Wx); S,res=mls(U,vn(U,T),idx,0.072,0.03); res=-res*1e3
for k in np.argsort(-res)[:14]:
    i=idx[k]; d={names[j]:w for j,w in enumerate(Wx[i]) if w>0.04}
    print("res %.1f th %.0f y %.3f r %.3f dh %.3f "%(res[k],th[i],U0[i,1],r[i],dh[i])+" ".join("%s:%.2f"%(a[:7],b) for a,b in sorted(d.items(),key=lambda x:-x[1])))
