"""Hair vertices inside her body, head and outfit pieces at rest (bind pose), as the game builds her: each style's skin
bound by joint name onto heroine.glb's skeleton (People.HerHair). Signed distance to the nearest triangle (k nearest by
centroid, exact point-triangle), negative = behind the surface (inside the skin, or under a garment's shell)."""
import sys, numpy as np
from scipy.spatial import cKDTree
from gl import G, skinned
A = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\art\people"
STY = ["long", "ponytail", "braid", "bob", "pixie"]
OUT = ["warden", "reaver", "arcanist", "ranger"]

her = G(A + r"\heroine.glb")
HJ = {her.j["nodes"][n].get("name"): her.W(n) for n in her.j["skins"][0]["joints"]}

def surf(g, keep):
    """Skinned triangles of g's meshes whose node or material name passes keep: (tri verts (t,3,3))."""
    tris = []
    for (node, mesh, k, mat, P, J, Wt, s, I, ni) in g.meshes():
        if not keep(node, mat) or I is None: continue
        if s is not None:
            mats = np.array([HJ.get(n, g.W(g.j["skins"][s]["joints"][q])) for q, n in enumerate(g.joint_names(s))]) @ g.ibm(s)
            V = skinned(P, J, Wt, mats)
        else:
            V = (g.W(ni) @ np.c_[P, np.ones(len(P))].T).T[:, :3]
        tris.append(V[I])
    return np.concatenate(tris) if tris else np.zeros((0, 3, 3))

def closest(p, a, b, c):
    """Vectorised closest point on triangles (Ericson)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den[den == 0] = 1e-12
    v = vb / den; w = vc / den
    res = a + ab * v[:, None] + ac * w[:, None]
    m = (d1 <= 0) & (d2 <= 0); res[m] = a[m]
    m = (d3 >= 0) & (d4 <= d3); res[m] = b[m]
    m = (d6 >= 0) & (d5 <= d6); res[m] = c[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-12, d1 - d3); res[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-12, d2 - d6); res[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-12, (d4 - d3) + (d5 - d6)); res[m] = (b + (c - b) * t[:, None])[m]
    return res

class Surf:
    def __init__(self, T):
        self.T = T; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); l = np.linalg.norm(n, axis=1); ok = l > 1e-12
        self.T, self.N = T[ok], n[ok] / l[ok][:, None]; self.kd = cKDTree(self.T.mean(1))
    def sd(self, P, k=12, reach=0.015):
        d, idx = self.kd.query(P, k=k, distance_upper_bound=reach + 0.02)
        best = np.full(len(P), np.inf); sgn = np.ones(len(P))
        for c in range(k):
            ok = np.isfinite(d[:, c]); ii = idx[ok, c]
            q = closest(P[ok], self.T[ii, 0], self.T[ii, 1], self.T[ii, 2])
            dist = np.linalg.norm(P[ok] - q, axis=1)
            better = dist < best[ok]
            s = np.sign(((P[ok] - q) * self.N[ii]).sum(1))
            bo = np.where(ok)[0][better]; best[bo] = dist[better]; sgn[bo] = s[better]
        return np.where(best < reach, best * sgn, np.inf)

body = Surf(surf(her, lambda n, m: n == "Heroine"))
headS = Surf(surf(her, lambda n, m: n == "HeroineHead"))
outs = {}
for o in OUT:
    g = G(A + rf"\heroine_outfit_{o}.gltf")
    mats = sorted({m[3] for m in g.meshes()})
    outs[o] = {m: Surf(surf(g, lambda n, mm, m=m: mm == m)) for m in mats}

def region(names, J, Wt):
    top = J[np.arange(len(J)), Wt.argmax(1)]
    lab = np.array([("head" if n in ("Head",) or n.startswith("FACIAL") else "neck" if n.startswith("neck") else
                     "back" if n.startswith("spine") or n == "pelvis" else "shoulder" if n.startswith(("clavicle", "upperarm")) else "other") for n in names])
    return lab[top]

def report(tag, sd, reg, mask):
    lines = []
    for r in ("head", "neck", "back", "shoulder", "other"):
        m = mask & (reg == r)
        if not m.any(): continue
        x = sd[m]; x = x[np.isfinite(x)]
        n1, n3 = int((x < -0.001).sum()), int((x < -0.003).sum())
        if n1: lines.append(f"    {tag:22s} {r:8s} {m.sum():7d} v: inside>1mm {n1:6d} ({100*n1/m.sum():5.1f}%), >3mm {n3:6d}, worst {-x.min()*1000:6.1f} mm")
    return lines

def _main():
  for s in STY:
      g = G(A + rf"\heroine_hair_{s}.gltf")
      names = g.joint_names(0)
      mats_now = np.array([HJ[n] if n in HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(names)]) @ g.ibm(0)
      mats_then = np.array([g.W(g.j["skins"][0]["joints"][q]) for q in range(len(names))]) @ g.ibm(0)
      missing = [n for n in names if n not in HJ]
      print(f"== {s}" + (f" (joints not in heroine.glb: {missing})" if missing else ""))
      for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
          at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
          uv = g.acc(at["TEXCOORD_0"]).astype(float) if "TEXCOORD_0" in at else np.zeros((len(P), 2))
          now = skinned(P, J, Wt, mats_now); then = skinned(P, J, Wt, mats_then)
          reg = region(names, J, Wt)
          mv = np.linalg.norm(now - then, axis=1)
          print(f"  [{mat}] {len(P)} v; moved by the skeleton change: " + ", ".join(f"{r} median {np.median(mv[reg==r])*1000:.1f} max {mv[reg==r].max()*1000:.1f} mm" for r in ("head", "neck", "back", "shoulder") if (reg == r).any()))
          body_part = mat not in ("hair_cap",)
          strands = (uv[:, 1] >= 0.1) if mat != "hair_cap" else np.ones(len(P), bool)
          roots = ~strands
          L = []
          L += report("head skin (strands)", headS.sd(now), reg, strands)
          L += report("head skin (roots)", headS.sd(now), reg, roots)
          L += report("body skin (strands)", body.sd(now), reg, strands)
          for o, ms in outs.items():
              for m, S in ms.items():
                  L += report(f"{o}.{m}", S.sd(now), reg, strands)
          print("\n".join(L) if L else "    nothing inside by more than 1 mm")

if __name__ == "__main__": _main()