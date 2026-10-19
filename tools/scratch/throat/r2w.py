"""r2w.py <glb>: her weights by angle round her neck and height (rest), the bones that matter."""
from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); X=dense(G_,inv)
names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]
th,r=cyl(U0); dh=cKDTree(H).query(U0)[0]
nz=np.nonzero(X[(U0[:,1]>1.45)&(U0[:,1]<1.70)&(r<0.17)&(np.abs(th)<140)].sum(0)>0.5)[0]
print("bones:", [names[j] for j in nz])
for a in (0,30,50,70,90,110,130):
  print("theta",a)
  for y in np.arange(1.48,1.66,0.01):
    s=np.nonzero((np.abs(th-a)<4)&(np.abs(U0[:,1]-y)<0.004)&(r<0.17))[0]
    if len(s)==0: continue
    m=X[s].mean(0); print("  y %.2f r %.3f dh %.3f "%(y,r[s].mean(),dh[s].min())+" ".join("%s:%.2f"%(names[j][:6],m[j]) for j in np.argsort(-m)[:4] if m[j]>0.02))
