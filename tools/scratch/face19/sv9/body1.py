"""body1.py: her rest body (heroine.glb body+head) against the b3/b2 balls: at lateral x0, per height, the body's back surface
(most negative z) and the balls' back-most z there; + = the balls stand out behind her body (cm)."""
import numpy as np, trimesh, json
s = trimesh.load("C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/heroine.glb", force="scene")
V = []
for node in s.graph.nodes_geometry:
    T, g = s.graph[node]
    if g in ("Mesh_0", "Mesh_1", "HeroineHead"): V.append(trimesh.transformations.transform_points(s.geometry[g].vertices, T))
V = np.vstack(V)
B = json.load(open("../../../../godot/art/people/heroine_hair_braid.chain.json"))["spheres"]
def ballz(x0, y, W=0.06):
    """back-most z of the file's balls (spine ones as capsules of half-width W) at (x0, y)."""
    best = 9
    for b in B:
        at = np.array(b["at"]); r = b["r"]; w = W if b["bone"].startswith("spine") else 0
        dx = max(0, abs(x0) - w) if w else abs(x0)
        q = r * r - dx * dx - (y - at[1]) ** 2
        if q > 0: best = min(best, at[2] - np.sqrt(q))
    return best
for x0 in (0.0, 0.04, 0.06, 0.08, 0.10, 0.12):
    print("x0 %.2f" % x0)
    for y in np.arange(1.46, 1.68, 0.02):
        m = (np.abs(V[:, 0] - x0) < 0.008) & (np.abs(V[:, 1] - y) < 0.008)
        if not m.any(): print("   y %.2f body none" % y); continue
        zb = V[m, 2].min(); bz = ballz(x0, y); bz0 = ballz(x0, y, 0)
        print("   y %.2f body back z %.3f  capsules %s  spheres %s" % (y, zb, "%+.1f" % ((zb - bz) * 100) if bz < 9 else "  -", "%+.1f" % ((zb - bz0) * 100) if bz0 < 9 else "  -"))
