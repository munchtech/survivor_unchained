"""pads.py: how far her right shoulder's surface (body, and each outfit) reaches from the upperarm_r joint at rest, by
direction (cm; cone of 12 deg), to size the chain's shoulder balls. Rest: she faces +Z, her right is -X."""
import json, struct, numpy as np, math, sys
P = "../../../../godot/art/people/"
def load(fn):
    if fn.endswith(".glb"):
        b = open(P + fn, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; g = json.loads(b[20:20 + n]); o = 20 + n
        bl = struct.unpack("<I", b[o:o + 4])[0]; bins = [b[o + 8:o + 8 + bl]]
    else:
        g = json.load(open(P + fn)); bins = [open(P + x["uri"], "rb").read() for x in g["buffers"]]
    def acc(i):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; buf = bins[bv.get("buffer", 0)]
        nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        dt = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}[a["componentType"]]
        st = bv.get("byteStride", 0); off = bv.get("byteOffset", 0) + a.get("byteOffset", 0); cnt = a["count"]
        isz = np.dtype(dt).itemsize * nc
        if st and st != isz:
            raw = np.frombuffer(buf, np.uint8, count=st * cnt, offset=off).reshape(cnt, st)[:, :isz].copy()
            return raw.view(dt).reshape(cnt, nc)
        return np.frombuffer(buf, dt, count=cnt * nc, offset=off).reshape(cnt, nc)
    return g, acc
def bones(g, acc):
    sk = g["skins"][0]; ibm = acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4)
    out = {}
    for j, n in enumerate(sk["joints"]):
        M = np.linalg.inv(ibm[j].T); out[g["nodes"][n]["name"]] = M
    return out
def verts(g, acc, skip=()):
    vs = []
    for mi, m in enumerate(g["meshes"]):
        if any(s in m["name"].lower() for s in skip): continue
        for p in m["primitives"]: vs.append((m["name"], acc(p["attributes"]["POSITION"]).astype(float)))
    return vs
DIRS = {"up": (0, 1, 0), "up-out": (-1, 1, 0), "out": (-1, 0, 0), "up-fwd": (0, 1, 1), "fwd": (0, 0, 1), "up-back": (0, 1, -1), "back": (0, 0, -1), "out-fwd": (-1, 0, 1), "out-back": (-1, 0, -1), "up-in": (1, 1, 0)}
def prof(vs, J):
    res = {}
    for k, d in DIRS.items():
        d = np.array(d, float); d /= np.linalg.norm(d); best = 0; who = ""
        for name, V in vs:
            r = V - J; L = np.linalg.norm(r, axis=1); c = (r @ d) / np.maximum(L, 1e-9)
            sel = (c > math.cos(math.radians(12))) & (L < 0.25)
            if sel.any() and L[sel].max() > best: best = L[sel].max(); who = name
        res[k] = (best * 100, who)
    return res
def main():
  gb, ab = load("heroine.glb"); B = bones(gb, ab)
  J = B["upperarm_r"][:3, 3]; print("upperarm_r rest", np.round(J, 4), "upperarm_l", np.round(B["upperarm_l"][:3, 3], 4), "neck_01", np.round(B["neck_01"][:3, 3], 4), "clavicle_r", np.round(B["clavicle_r"][:3, 3], 4), "lowerarm_r", np.round(B["lowerarm_r"][:3, 3], 4))
  body = prof(verts(gb, ab, ("hair", "lash", "brow", "eye", "teeth", "tongue")), J)
  print("%-9s" % "dir", "body".ljust(14), " ".join(o.ljust(28) for o in ("warden", "arcanist", "ranger", "reaver")))
  outs = {}
  for o in ("warden", "arcanist", "ranger", "reaver"):
      g, a = load("heroine_outfit_%s.gltf" % o); Bo = bones(g, a); Jo = Bo["upperarm_r"][:3, 3]
      if np.linalg.norm(Jo - J) > 1e-3: print("  (outfit %s joint differs by %.2f cm)" % (o, np.linalg.norm(Jo - J) * 100))
      outs[o] = prof(verts(g, a), Jo)
  for k in DIRS:
      print("%-9s" % k, ("%.1f" % body[k][0]).ljust(14), " ".join(("%.1f %s" % outs[o][k]).ljust(28) for o in outs))
if __name__ == "__main__": main()
