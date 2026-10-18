import sys, os; sys.path.insert(0,os.path.dirname(__file__))
from sd import *
names=[n.get("name") for n in G(path).g["nodes"]]
def wof(p,jn):
    k=[k for k,j in enumerate(p["joints"]) if names[j]==jn][0]
    return (p["w"]*(p["j"]==k)).sum(1)
for uncut in (0.03,0.0):
    body,head=load(uncut); gr=body[1]
    T=cKDTree(head["skin"]); d,ix=T.query(gr["skin"])
    s=np.einsum("ij,ij->i",gr["skin"]-head["skin"][ix],head["n"][ix])
    bad=(d<0.02)&(s>0.001)
    print("uncut" if uncut else "NOW", "graft verts out of head >1mm:",bad.sum())
    wg=wof(gr,"Head"); wh=wof(head,"Head")
    for v in np.where(bad)[0][np.argsort(-s[bad])][:25]:
        x,y,z=gr["skin"][v]
        print("  v%5d x%+.3f y%.3f z%+.3f out %.1fmm  graftHeadW %.2f headHeadW %.2f  restgap %.1fmm"%(v,x,y,z,s[v]*1e3,wg[v],wh[ix[v]],1e3*np.linalg.norm(gr["rest"][v]-head["rest"][ix[v]])))
