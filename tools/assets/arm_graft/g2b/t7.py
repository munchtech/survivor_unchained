# cap hand-off: more upperarm over the deltoid top, clavicle hand-off moved medially. args: list of dicts
from proxy import *
from summ import summ
import sys, io, contextlib
Pn=np.load("P_shape1.npy"); VGa=np.load("VG_opt_a.npy")
nm=d["names"]
def capw(VG, a=1.0, t0=-0.45, t1=-0.15, t2=0.25, t3=0.45, pw=1.0, it=6, sm=0.5, sides="rl", c0=None, c1=0.3):
    V=VG.copy()
    for s in sides:
        f=C.frame(s); iC,iU=nm.index("clavicle_"+s),nm.index("upperarm_"+s)
        cu=V[:,iC]+V[:,iU]; x=np.where(cu>1e-9,V[:,iU]/np.maximum(cu,1e-9),0)
        w=edit.ss((f["t"]-t0)/(t1-t0))*edit.ss((t3-f["t"])/(t3-t2))*(((1+f["ct"])/2)**pw if c0 is None else edit.ss((f["ct"]-c0)/(c1-c0)))*f["side"]*(f["r"]<0.14)*(cu>1e-4)
        for _ in range(it): w=(1-sm)*w+sm*(C.Wn@w)
        w*= (cu>1e-4)
        xn=x+a*w*(1-x)
        V[:,iC]=cu*(1-xn); V[:,iU]=cu*xn
    return V
def run(VG,tag,verbose=False):
    if verbose: o,_=variant(Pn,VG,tag); return o
    with contextlib.redirect_stdout(io.StringIO()): o,_=variant(Pn,VG,tag)
    summ(o,tag); return o
if __name__=="__main__":
    args=eval(sys.argv[1])
    for k in args:
        if k=="base": run(VGa,"base",verbose=True); continue
        run(capw(VGa,**k),str(k)[:60],verbose=("v" in sys.argv[2:]))
def tmix(VG, ta=0.2, tb=0.4):
    """VG near the root, the dump's own weights past t (ramped ta..tb)"""
    V=VG.copy()
    for s in "rl":
        f=C.frame(s); w=(edit.ss((f["t"]-ta)/(tb-ta))*f["side"])[:,None]
        V=V*(1-w)+d["VG"]*w
    return V
