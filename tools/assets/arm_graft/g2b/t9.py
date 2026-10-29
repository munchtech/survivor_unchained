# inner elbow: smooth the upperarm/lowerarm split over the elbow's inner side
import sys; args=eval(sys.argv[1]); sys.argv=["x"]
from t8 import *
P1=np.load("P_v1.npy"); V1=np.load("VG_v1.npy")
def elb(VG, T=((0.75,0.85),(1.15,1.3)), side_c=0.0, it=20, sm=0.5, front=True, sides="rl"):
    V=VG.copy()
    for s in sides:
        f=C.frame(s); iU,iL=nm.index("upperarm_"+s),nm.index("lowerarm_"+s)
        tot=V[:,iU]+V[:,iL]; x=np.where(tot>1e-9,V[:,iL]/np.maximum(tot,1e-9),0)
        e_fr=f["e"]@f["fr"]
        m=edit.win(f["t"],T)*f["side"]*(edit.ss((e_fr-side_c+0.5)/1.0) if front else 1)*(tot>0.3)*(f["r"]<0.08)
        xs=x.copy()
        for _ in range(it): xs=(1-sm)*xs+sm*(C.Wn@xs)
        xn=x*(1-m)+xs*m
        V[:,iU]=tot*(1-xn); V[:,iL]=tot*xn
    return V
for k in args:
    o=run2(P1,elb(V1,**k) if k is not None else V1,str(k)[:40])
    for s in "rl": print("   ",s,"elbow<0.5 A82 %.0f%% flask %.0f%% catch %.0f%%"%(100*o[s]["A82_elb"],100*o[s]["flask_elb"],100*o[s]["catch_elb"]))
if "save" in sys.argv[0:0] or os.environ.get("SAVE_V2"):
    np.save("VG_v2.npy",elb(V1,it=10)); print("saved VG_v2")
