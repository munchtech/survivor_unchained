"""r2prof.py out.png glb... : her neck's profiles (radius from her neck's axis vs height) at 0/40/70/100 deg, the game's rest (cut) and c01, overlaid per file."""
from exp import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
out=sys.argv[1]; fs=sys.argv[2:]
poses=[("rest",[]),("c01",[("neck_01",1,6),("neck_01",2,16),("Head",1,8),("Head",2,14)])]
fig,axs=plt.subplots(2,4,figsize=(16,10)); cl="krbgm"
for fi,f in enumerate(fs):
    G_,P,inv,U0,T,H=load(f); Wx=dense(G_,inv); th,r=cyl(U0)
    for pi,(nm,op) in enumerate(poses):
        U=apply(skin_custom(G_,op,None,0),U0,Wx)
        for ai,a in enumerate((0,40,70,100)):
            s=np.nonzero((np.abs(th-a)<1.5)&(U0[:,1]>1.47)&(U0[:,1]<1.66)&(r<0.17))[0]; s=s[np.argsort(U0[s,1])]
            ax=axs[pi,ai]; rr=np.hypot(U[s,0],U[s,2]+0.045)
            ax.plot(rr*100,U[s,1]*100,cl[fi]+".-",lw=0.8,ms=2,label=f[-12:]); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title("%s th %d"%(nm,a))
axs[0,0].legend(); plt.tight_layout(); plt.savefig(out,dpi=55)
