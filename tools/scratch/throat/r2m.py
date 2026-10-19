"""r2m.py <glb>[@weights.npy] ... : her throat's relief over a 3 cm fit (MLS, sigma 3 cm), posed: midline bump/dip,
side relief (max outward, mm) at three heights each side; plus clavicle+arm weight left in her neck column."""
from exp import *
import os
def ops2(back=0,turn=0,tilt=0): return [(j,a,d/2) for j in ("neck_01","Head") for a,d in ((0,-back),(1,turn),(2,tilt)) if d]
POSES=[("rest",[]),("back40",ops2(40)),("bk40 t+25",ops2(40,25,0)),("t+25 r+25",ops2(0,25,25)),("t+25 r-25",ops2(0,25,-25)),("t-25 r+25",ops2(0,-25,25)),("t-25 r-25",ops2(0,-25,-25)),
       ("c01",[("neck_01",1,6),("neck_01",2,16),("Head",1,8),("Head",2,14)]),("c01 mirror",[("neck_01",1,-6),("neck_01",2,-16),("Head",1,-8),("Head",2,-14)])]
SIG=float(os.environ.get("SIG","0.03"))
def run(arg):
    path,_,wf=arg.partition("@")
    G_,P,inv,U0,T,H=load(path); Wx=np.load(wf) if wf else dense(G_,inv)
    names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]
    th,r=cyl(U0); dh=cKDTree(H).query(U0)[0]
    idx=np.nonzero((U0[:,1]>1.47)&(U0[:,1]<1.67)&(np.abs(th)<135)&(r<0.17)&(dh>0.004))[0]
    arm=[j for j,n in enumerate(names) if n.startswith(("clavicle","upperarm"))]
    core=(np.abs(th)>40)&(np.abs(th)<130)&(r<0.10)&(U0[:,1]>1.55)&(U0[:,1]<1.66)
    print("== %s  clav+arm in neck column: max %.2f mean %.2f"%(os.path.basename(arg),Wx[core][:,arm].sum(1).max(),Wx[core][:,arm].sum(1).mean()))
    print("%-11s %6s %6s | %5s %5s %5s | %5s %5s %5s"%("pose","mid+","mid-","L1.55","L1.58","L1.61","R1.55","R1.58","R1.61"))
    out={}
    for nm,op in POSES:
        Jm=skin_custom(G_,op,None,float(os.environ.get("UNCUT","0"))); U=apply(Jm,U0,Wx); S,res=mls(U,vn(U,T),idx,2.4*SIG,SIG)
        res=-res  # + = outward
        ti,yi=th[idx],U0[idx,1]
        mid=(np.abs(ti)<12)&(yi>1.50)&(yi<1.64)
        row=[res[mid].max()*1e3,res[mid].min()*1e3]
        for s in (1,-1):
            for y in (1.55,1.58,1.61):
                m=(s*ti>40)&(s*ti<125)&(np.abs(yi-y)<0.012); row.append(res[m].max()*1e3 if m.any() else 0)
        print("%-11s %6.1f %6.1f | %5.1f %5.1f %5.1f | %5.1f %5.1f %5.1f"%((nm,)+tuple(row))); out[nm]=(res,idx)
    return out
if __name__=="__main__":
    for a in sys.argv[1:]: run(a)
