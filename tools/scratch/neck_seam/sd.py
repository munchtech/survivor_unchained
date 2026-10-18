import sys, os; sys.path.insert(0,os.path.dirname(__file__))
from glb import *
from scipy.spatial import cKDTree
path=sys.argv[1]
def load(uncut):
    G_=G(path); g=G_.g
    if uncut:
        h=[n for n in g["nodes"] if n.get("name")=="Head"][0]; t=np.array(h["translation"]); L=np.linalg.norm(t)
        h["translation"]=list(t*(L+uncut)/L)
    body=skinned(G_,84); head=skinned(G_,86)[0]
    for p in body+[head]:
        p["n"]=G_.acc(p["prim"]["attributes"]["NORMAL"]).astype(float)
    return body,head
def sdist(A,B,mask):
    # signed distance of A's verts (mask) to B's surface, via nearest B vert and its normal
    T=cKDTree(B["skin"]); d,ix=T.query(A["skin"][mask])
    s=np.einsum("ij,ij->i",A["skin"][mask]-B["skin"][ix],B["n"][ix])
    return d,s
def main():
  for uncut in (0.03,0.0):
      body,head=load(uncut); gr=body[1]; bm=body[0]
      print("=== uncut" if uncut else "=== NOW (cut 30mm)")
      hy=head["skin"][:,1]; gy=gr["skin"][:,1]
      print("graft skinned y %.3f..%.3f  head skinned y min %.3f"%(gy.min(),gy.max(),hy.min()))
      m=hy<gy.max()+0.01
      d,s=sdist(head,gr,m)
      close=d<0.02
      print("head verts in graft band: %d; within 2cm of graft: %d; outside graft surface by >0.5mm: %d, >2mm: %d; max out %.1f mm"%(m.sum(),close.sum(),(close&(s>0.0005)).sum(),(close&(s>0.002)).sum(),s[close].max()*1e3))
      P=head["skin"][m][close&(s>0.0005)]
      if len(P): print("   out verts x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"%(P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),P[:,2].min(),P[:,2].max()))
      m2=gy>hy.min()-0.01
      d,s=sdist(gr,head,m2); close=d<0.02
      print("graft verts in head band: %d; within 2cm: %d; outside head surface by >0.5mm: %d, >2mm: %d; max %.1f"%(m2.sum(),close.sum(),(close&(s>0.0005)).sum(),(close&(s>0.002)).sum(),s[close].max()*1e3))
      # body main neck vs head
      by=bm["skin"][:,1]; m3=by>hy.min()-0.005
      d,s=sdist(bm,head,m3); close=d<0.03
      print("body-main verts above head-bottom: %d; outside head by >0.5mm: %d >2mm: %d max %.1f mm"%(m3.sum(),(close&(s>0.0005)).sum(),(close&(s>0.002)).sum(),(s[close].max()*1e3 if close.any() else 0)))
      P=bm["skin"][m3][close&(s>0.0005)]
      if len(P): print("   out verts x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"%(P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),P[:,2].min(),P[:,2].max()))
      m4=by>gy.min()
      d,s=sdist(bm,gr,m4); close=d<0.03
      print("body-main verts vs graft: %d; outside graft by >0.5mm: %d >2mm: %d max %.1f"%(m4.sum(),(close&(s>0.0005)).sum(),(close&(s>0.002)).sum(),(s[close].max()*1e3 if close.any() else 0)))

if __name__=="__main__": main()
