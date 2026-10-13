"""Depth of HairSway's chain points inside her body (HAIRBODY log lines, spine_03 rest space), from heroine.glb's
body and head vertices: per point, how far in front of her back surface it is (+ = inside), where her body is."""
import sys, re, numpy as np, trimesh
s = trimesh.load("C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/heroine.glb", force="scene")
V = []
for node in s.graph.nodes_geometry:
    T, g = s.graph[node]
    if g in ("Mesh_0", "HeroineHead"): V.append(trimesh.transformations.transform_points(s.geometry[g].vertices, T))
V = np.vstack(V)
def depth(q):
    m = (np.abs(V[:, 1] - q[1]) < 0.012) & (np.abs(V[:, 0] - q[0]) < 0.012)
    if not m.any(): return None
    back, front = V[m, 2].min(), V[m, 2].max()
    if q[2] <= back or q[2] >= front: return -min(back - q[2] if q[2] <= back else 9, q[2] - front if q[2] >= front else 9)
    return min(q[2] - back, front - q[2])
for line in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    if not line.startswith("HAIRBODY"): continue
    f = line.split()[1]
    pts = [np.array([float(v) for v in t.split(",")]) for t in line.split()[2:]]
    out = []
    for q in pts[1:]:
        d = depth(q)
        out.append("  .  " if d is None else ("%+.3f" % d) if d > 0 else "  -  ")
    print(f, " ".join(out), " tip", " ".join("%.2f" % c for c in pts[7]))
