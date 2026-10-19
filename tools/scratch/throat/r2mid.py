"""r2mid.py <glb>[@W.npy] [angle]: her profile at `angle` round her neck (0 = front midline), rest, cut vs uncut: y, Head w, residual (3 cm fit)."""
from exp import *
arg=sys.argv[1]; a0=float(sys.argv[2]) if len(sys.argv)>2 else 0
path,_,wf=arg.partition("@")
G_,P,inv,U0,T,H=load(path); Wx=np.load(wf) if wf else dense(G_,inv)
names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]; hj=names.index("Head")
th,r=cyl(U0); dh=cKDTree(H).query(U0)[0]
s=np.nonzero((np.abs(th-a0)<3)&(U0[:,1]>1.46)&(U0[:,1]<1.67)&(r<0.17))[0]; s=s[np.argsort(U0[s,1])]
cols=[]
for unc in (0.03,0.0):
    Jm=skin_custom(G_,[],None,unc); U=apply(Jm,U0,Wx); S,res=mls(U,vn(U,T),s,0.072,0.03); cols.append((U,res))
for k,i in enumerate(s):
    if k%2: continue
    print("y %.3f r %.3f dh %.3f Head %.2f | uncut res %+5.1f | cut y %.3f r %.3f res %+5.1f"%(U0[i,1],r[i],dh[i],Wx[i,hj],-cols[0][1][k]*1e3,cols[1][0][i,1],np.hypot(cols[1][0][i,0],cols[1][0][i,2]+0.045),-cols[1][1][k]*1e3))
