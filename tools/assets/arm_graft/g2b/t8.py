# shape + cap weights together. argv1: list of (shape_kw, cap_kw)
from t7 import *
def topmask(s, T=((0.0,0.1),(0.35,0.45)), PHI=(80,110), R=(0.08,0.10)):
    f=C.frame(s); a=np.abs(f["phi"])
    return f["side"]*edit.win(f["t"],T)*edit.ss((PHI[1]-a)/(PHI[1]-PHI[0]))*edit.ss((R[1]-f["r"])/(R[1]-R[0]))
def shape(K=None, fair_it=30, top_it=0, T=((0.0,0.1),(0.35,0.45)), PHI=(80,110), sw=None):
    X=C.Pg+edit.arm_shape_field(C,SH0,K)
    mk=np.maximum(edit.pit_mask(C,"r"),edit.pit_mask(C,"l")); X=edit.fair(C,X,mk,iters=fair_it)
    if top_it:
        mt=np.maximum(topmask("r",T,PHI),topmask("l",T,PHI)); X=edit.fair(C,X,mt,iters=top_it)
    if sw:
        D=edit.cap_field(C,SH0,'r',**sw)+edit.cap_field(C,SH0,'l',**sw); X=X+C.vsmooth(D,sw.get('sigma',0.012))
    return blendv(X)
def run2(P,VG,tag,verbose=False):
    global Pn
    if verbose: o,_=variant(P,VG,tag); return o
    with contextlib.redirect_stdout(io.StringIO()): o,_=variant(P,VG,tag)
    summ(o,tag); return o
if __name__=="__main__":
    for sk,ck in eval(sys.argv[1]):
        P=shape(**sk); V0=tmix(VGa,*sk.pop("mix")) if False else VGa
        if "mix" in ck: V0=tmix(VGa,*ck.pop("mix"))
        VG=capw(V0,**ck) if ck else V0
        run2(P,VG,(str(sk)+str(ck))[:50],verbose=("v" in sys.argv[2:]))
        if "save" in sys.argv[2:]: np.save("P_%s.npy"%sys.argv[3],P); np.save("VG_%s.npy"%sys.argv[3],VG)
