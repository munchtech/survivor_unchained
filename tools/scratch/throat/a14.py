from exp import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
G_,P,inv,U0,T,H=load(sys.argv[1]); W2=np.load(sys.argv[2]); out=sys.argv[3]
Wd=dense(G_,inv); th,r=cyl(U0)
fig,axs=plt.subplots(1,4,figsize=(20,6))
for ax,tf in zip(axs,(0,30,60,90)):
  s=np.nonzero((np.abs(th-tf)<2.5)&(U0[:,1]>1.44)&(U0[:,1]<1.66)&(r<0.18))[0]; s=s[np.argsort(U0[s,1])]
  for pz,cl in (((0,0,0),"k"),((-40,0,0),"b"),((-50,25,0),"r"),((40,0,0),"g")):
    Jm=skin_custom(G_,pose_ops(*pz),None)
    for Wx,ls in ((Wd,"-"),(W2,"--")):
        Q=apply(Jm,U0[s],Wx[s]); hz=np.hypot(Q[:,0],Q[:,2]+0.045) if tf else Q[:,2]
        ax.plot(hz,Q[:,1],cl+ls,lw=1)
  ax.set_aspect("equal"); ax.set_title("theta %d"%tf); ax.grid(alpha=.3)
plt.savefig(out,dpi=70)
