import sys; sys.argv=["x","../../../godot/art/people/heroine.glb","NUL"]
from sd import *
body,head=load(0.0); gr=body[1]
T=cKDTree(head["skin"]); d,ix=T.query(gr["skin"])
for v in (1289,1313,2690,944):
  h=ix[v]; print("v",v,"graft rest",np.round(gr["rest"][v],3),"skin",np.round(gr["skin"][v],3)," head pt rest",np.round(head["rest"][h],3),"skin",np.round(head["skin"][h],3))
# head rest points within 1cm laterally (xz) of v1289 and above it
for v in (1289,1313):
  P=head["rest"]; g=gr["rest"][v]; m=(np.hypot(P[:,0]-g[0],P[:,2]-g[2])<0.006)
  print(v,"head pts in 6mm column: ys",np.round(np.sort(P[m,1]),3)[:12], "graft y",round(g[1],3))
