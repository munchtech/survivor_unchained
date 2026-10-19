from exp import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
G_,P,inv,U0,T,H=load(sys.argv[1]); out=sys.argv[2]; Ws=[dense(G_,inv)]+[np.load(f) for f in sys.argv[3:]]
R,sig=0.05,0.02
th,r=cyl(U0)
idx=np.nonzero((U0[:,1]>1.45)&(U0[:,1]<1.70)&(np.abs(th)<140)&(r<0.17))[0]
def ops(s1,s2): return [("neck_01",1,6*s1),("neck_01",2,16*s2),("Head",1,8*s1),("Head",2,14*s2)]
poses=(("rest",[]),("c01 ++",ops(1,1)),("c01 +-",ops(1,-1)),("c01 -+",ops(-1,1)))
fig,axs=plt.subplots(len(Ws),len(poses),figsize=(5*len(poses),5*len(Ws)))
for a,(nm,op) in enumerate(poses):
    Jm=skin_custom(G_,op,None)
    for b,Wx in enumerate(Ws):
        U=apply(Jm,U0,Wx); S,res=mls(U,vn(U,T),idx,R,sig)
        ax=axs[b,a]; ax.scatter(th[idx],U0[idx,1],c=res*1000,cmap="RdBu_r",vmin=-4,vmax=4,s=8)
        L=(th[idx]>20)&(th[idx]<110)&(U0[idx,1]<1.62); Rr=(th[idx]<-20)&(th[idx]>-110)&(U0[idx,1]<1.62)
        ax.set_title("%s W%d L %.1f R %.1f"%(nm,b,res[L].max()*1e3,res[Rr].max()*1e3)); ax.set_xlim(-140,140)
plt.tight_layout(); plt.savefig(out,dpi=45)
