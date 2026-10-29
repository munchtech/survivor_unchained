from proxy import *
from summ import summ
import opt, io, contextlib, sys, time
for cn in ("warden_show","stalker_show","idle_arcanist_break"): b0._cl[cn]=b0.clip(cn)
SPEC=[("idle_reaver_town",0,None,1),("reaver_show",8,"r",1),("reaver_show",16,"r",1),("reaver_show",24,"r",2),("warden_show",18,"r",1),
      ("stalker_show",39,"r",1),("idle_arcanist_break",30,"l",1),("flask_drink",100,"r",1),("flask_drink",113,"r",1),("flask_drink",126,"r",2),("catch_breath",97,"l",2)]
Das=edit.arm_shape_field(C,SH0)
mk=np.maximum(edit.pit_mask(C,"r"),edit.pit_mask(C,"l"))
X=edit.fair(C,C.Pg+Das,mk,iters=30); Pn=blendv(X)
np.save("P_shape1.npy",Pn)
kw=eval(sys.argv[1]) if len(sys.argv)>1 else {}
VG=d["VG"].copy()
for s in "rl":
    f=C.frame(s); nm=d["names"]
    tot=VG[:,nm.index("spine_03")]+VG[:,nm.index("clavicle_"+s)]+VG[:,nm.index("upperarm_"+s)]
    zone=f["side"]&(f["t"]>kw.get("t0",-0.6))&(f["t"]<kw.get("t1",0.75))&(f["r"]<0.13)&(tot>0.02)
    o=opt.Opt(b0,d,REF,Pn,s,VG=VG,poses=opt.pose_set(b0,s,SPEC),zone=zone)
    t=time.time(); e0=o.energy(o.th)
    dmp=kw.get("damp",1.0)
    for it in range(kw.get("it",6)):
        e,en,dx,dmp=o.step(lam_s=kw.get("ls",0.3),lam_p=kw.get("lp",0.01),damp=dmp)
        print(s,it,"E %.4g -> %.4g dx %.3f damp %.3g"%(e,en,dx,dmp),flush=True); dmp=max(dmp/3,1e-3)
    print(s,"vars",len(o.vi),"E %.4g -> %.4g"%(e0,o.energy(o.th)),"%.0fs"%(time.time()-t))
    VG=o.result()
np.save("VG_opt_%s.npy"%kw.get("name","a"),VG)
with contextlib.redirect_stdout(io.StringIO()): o1,_=variant(Pn,None,"x")
summ(o1,"shape1")
with contextlib.redirect_stdout(io.StringIO()): o2,_=variant(Pn,VG,"x")
summ(o2,"shape1+opt")
