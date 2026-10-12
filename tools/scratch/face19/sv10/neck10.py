"""neck10.py: her rest body (heroine.glb) around her neck: per height, the body's back and front z at a given x, against
the neck and head balls; is a point on top of neck ball b1 (p1 lodged in the throw) inside her neck?"""
import numpy as np, trimesh, json
s = trimesh.load("C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/heroine.glb", force="scene")
V = []
for node in s.graph.nodes_geometry:
    T, g = s.graph[node]
    if g in ("Mesh_0", "Mesh_1", "HeroineHead"): V.append(trimesh.transformations.transform_points(s.geometry[g].vertices, T))
V = np.vstack(V)
B = json.load(open("../../../../godot/art/people/heroine_hair_braid.chain.json"))["spheres"]
for b in B[:4]: print(b["bone"], np.round(b["at"], 4), round(b["r"], 4))
for x0 in (0.0, -0.0125, -0.03, -0.05):
    print("x0 %+.4f" % x0)
    for y in np.arange(1.60, 1.72, 0.01):
        m = (np.abs(V[:, 0] - x0) < 0.006) & (np.abs(V[:, 1] - y) < 0.006)
        if not m.any(): print("   y %.3f none" % y); continue
        z = V[m, 2]
        print("   y %.3f body z %.3f .. %.3f (back surface %.3f)" % (y, z.min(), z.max(), z.min()))
