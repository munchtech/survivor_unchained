import sys,os; sys.path.insert(0,os.path.dirname(__file__))
from glb import *
G_=G(sys.argv[1]); g=G_.g; N=g["nodes"]
for i in (84,86): print(i,N[i].get("name"),"skin",N[i].get("skin"),"mesh",N[i].get("mesh"))
print("skins",[(len(s["joints"])) for s in g["skins"]], "same joints", g["skins"][N[84]["skin"]]["joints"]==g["skins"][N[86]["skin"]]["joints"])
for mi in (N[84]["mesh"],N[86]["mesh"]):
  for p in g["meshes"][mi]["primitives"]:
    print(mi,g["materials"][p["material"]]["name"],list(p["attributes"].keys())[:12], g["accessors"][p["attributes"]["POSITION"]]["count"], "targets",len(p.get("targets",[])))
par={}
for i,n in enumerate(N):
  for c in n.get("children",[]): par[c]=i
hd=[i for i,n in enumerate(N) if n.get("name")=="Head"][0]
def desc(i): return [i]+[x for c in N[i].get("children",[]) for x in desc(c)]
print("Head subtree:",[N[i].get("name") for i in desc(hd)])
print("Head parent chain:",N[par[hd]]["name"],N[par[par[hd]]]["name"])
