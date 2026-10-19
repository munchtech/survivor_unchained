"""r2map.py out.png sig glb... : her neck's relief (+ out, mm) over th (deg) x rest height, the game's rest and c01; dh contours."""
from exp import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
out=sys.argv[1]; sig=float(sys.argv[2]); fs=sys.argv[3:]
poses=[("rest",[]),("c01",[("neck_01",1,6),("neck_01",2,16),("Head",1,8),("Head",2,14)])]
fig,axs=plt.subplots(len(fs),2,figsize=(14,5.5*len(fs)),squeeze=False)
for fi,f in enumerate(fs):
    G_,P,inv,U0,T,H=load(f); Wx=dense(G_,inv); th,r=cyl(U0); dh=cKDTree(H).query(U0)[0]
    idx=np.nonzero((U0[:,1]>1.47)&(U0[:,1]<1.67)&(np.abs(th)<140)&(r<0.17)&(dh>0.002))[0]
    for pi,(nm,op) in enumerate(poses):
        U=apply(skin_custom(G_,op,None,0),U0,Wx); S,res=mls(U,vn(U,T),idx,2.4*sig,sig); res=-res*1e3
        ax=axs[fi,pi]; sc=ax.scatter(th[idx],U0[idx,1],c=res,cmap="RdBu_r",vmin=-4,vmax=4,s=10)
        ax.tricontour(th[idx],U0[idx,1],dh[idx],levels=[0.006,0.018,0.05,0.1],colors="g",linewidths=0.6)
        ax.set_title("%s %s max %.1f"%(f[-10:],nm,res.max())); ax.set_xlim(-140,140); ax.set_ylim(1.47,1.67); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(out,dpi=50)
