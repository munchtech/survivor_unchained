import sys, os; sys.path.insert(0,os.path.dirname(__file__))
from glb import *
G_=G(sys.argv[1]); g=G_.g
for i,n in enumerate(g["nodes"]):
    if "mesh" in n:
        m=g["meshes"][n["mesh"]]
        print(i,n.get("name"),m.get("name"),[ (g["materials"][p["material"]].get("name"), g["accessors"][p["attributes"]["POSITION"]]["count"]) for p in m["primitives"]], "skin" in n)
for nm in ("neck_01","Head","neck_02"):
    h=[n for n in g["nodes"] if n.get("name")==nm]
    if h: print(nm,h[0].get("translation"))
