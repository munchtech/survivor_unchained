"""Seam cracks: graft points within TOL of a head point at rest, their skinned gap (cut), rest + turns. python weld.py a.glb ..."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from glb import *
from motion import qmul,aq
from scipy.spatial import cKDTree
POSES=[("rest",[])]+[("Hy%+d"%d,[("Head",1,d)]) for d in (-45,45)]+[("Hx%+d"%d,[("Head",0,d)]) for d in (-20,20)]+[("Hz+15",[("Head",2,15)])]
for path in sys.argv[1:]:
    G_=G(path); g=G_.g; N=g["nodes"]; rot0={i:list(n.get("rotation",[0,0,0,1])) for i,n in enumerate(N)}
    out=[]
    for nm,ops in POSES:
        for i in range(len(N)): N[i]["rotation"]=list(rot0[i])
        for jn,ax,dg in ops:
            i=[k for k,n in enumerate(N) if n.get("name")==jn][0]; N[i]["rotation"]=qmul(N[i]["rotation"],aq(ax,dg))
        gr=skinned(G_,84)[1]; hd=skinned(G_,86)[0]
        d,ix=cKDTree(hd["rest"]).query(gr["rest"])
        out.append(nm)
        for tol in (1e-5,5e-4,2e-3):
            m=d<tol; gap=np.linalg.norm(gr["skin"][m]-hd["skin"][ix[m]],axis=1)-d[m]
            out.append("  <%.2fmm n%d gap>0.3mm %d max %.2f"%(tol*1e3,m.sum(),(gap>0.0003).sum(),gap.max()*1e3))
    print(os.path.basename(os.path.dirname(path))+"/"+os.path.basename(path)); print("\n".join("   "+x if not x.startswith("  ") else "     "+x for x in out))
