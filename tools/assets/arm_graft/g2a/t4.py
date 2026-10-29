from proxy import *
from summ import summ
import sys
SH=SH0
Das=edit.arm_shape_field(C,SH)
def shape(fair_it=0, cap=0.0, armshape=True, **kw):
    X=C.Pg+(Das if armshape else 0)
    if fair_it:
        mk=np.maximum(edit.pit_mask(C,"r"),edit.pit_mask(C,"l"))
        X=edit.fair(C,X,mk,iters=fair_it)
    if cap:
        D=edit.cap_field(C,SH,"r",amt=cap,**kw)+edit.cap_field(C,SH,"l",amt=cap,**kw)
        X=X+C.vsmooth(D,0.012)
    return blendv(X)
import meas
meas_v=lambda P,tag: summ(variant(P,None,tag)[0],tag)
import builtins
for args in eval(sys.argv[1]):
    P=shape(**args); mv=np.linalg.norm(P-d["P"],axis=1)
    o,_=variant(P,None,str(args)) if False else (None,None)
    import io,contextlib
    with contextlib.redirect_stdout(io.StringIO()): o,_=variant(P,None,"x")
    print(args,"max move %.1f mm"%(mv.max()*1000)); summ(o,"")
