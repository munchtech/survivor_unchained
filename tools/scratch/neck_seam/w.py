import sys,os; sys.path.insert(0,os.path.dirname(__file__))
from glb import *
from scipy.spatial import cKDTree
G_=G(sys.argv[1]); g=G_.g; N=g["nodes"]; names=[n.get("name") for n in N]
sk=g["skins"][0]["joints"]
pr=lambda mi,mat:[p for p in g["meshes"][mi]["primitives"] if g["materials"][p["material"]]["name"]==mat][0]
gp=pr(0,"skin_graft"); hp=pr(2,"skin_head"); bp=pr(0,"Material_0.001")
for nm,p in (("graft",gp),("head",hp)):
  a=g["accessors"][p["attributes"]["WEIGHTS_0"]]; b=g["accessors"][p["attributes"]["JOINTS_0"]]
  print(nm,"W ct",a["componentType"],a.get("normalized"),"J ct",b["componentType"], "bv stride",g["bufferViews"][a["bufferView"]].get("byteStride"))
Pg=G_.acc(gp["attributes"]["POSITION"]).astype(float); Ph=G_.acc(hp["attributes"]["POSITION"]).astype(float); Pb=G_.acc(bp["attributes"]["POSITION"]).astype(float)
d,ix=cKDTree(Ph).query(Pg); db,_=cKDTree(Pb).query(Pg)
print("graft verts coincident with head:",(d<1e-5).sum()," with body:",(db<1e-5).sum())
print("graft y of body-coincident: %.3f..%.3f"%(Pg[db<1e-5,1].min(),Pg[db<1e-5,1].max()) if (db<1e-5).any() else "")
print("min dist head->body-coincident graft verts: %.3f"%d[db<1e-5].min() if (db<1e-5).any() else "")
for D in (0.02,0.03,0.04,0.05): print("graft verts within %.0f cm of head: %d"%(D*100,(d<D).sum()))
jg=G_.acc(gp["attributes"]["JOINTS_0"]); wg=G_.acc(gp["attributes"]["WEIGHTS_0"]).astype(float)
from collections import Counter
c=Counter(); 
for j,w in zip(jg[d<0.04].ravel(),wg[d<0.04].ravel()):
  if w>0.01: c[names[sk[j]]]+=1
print("joints on near graft:",c.most_common(12))
jh=G_.acc(hp["attributes"]["JOINTS_0"]); whh=G_.acc(hp["attributes"]["WEIGHTS_0"]).astype(float)
c=Counter()
for j,w in zip(jh[ix[d<0.04]].ravel(),whh[ix[d<0.04]].ravel()):
  if w>0.01: c[names[sk[j]]]+=1
print("joints on the head verts nearest:",c.most_common(12))
