import json,numpy as np
B=r"C:\Users\munch\Desktop\Marionette\public\base"
def load_base():
    js=json.load(open(B+r"\base.json")); raw=open(B+r"\base.bin","rb").read()
    def part(n,dt,w):
        p=js["parts"][n]; return np.frombuffer(raw,dt,p["length"],p["offset"]).reshape(-1,w)
    P=part("positions",np.float32,3).astype(float); T=part("triangles",np.uint32,3).astype(int)
    UV=part("uvs",np.float32,2); TU=part("triangleUvs",np.uint32,3).astype(int); TG=part("triangleGroups",np.uint16,1).ravel()
    return js,P,T,UV,TU,TG
