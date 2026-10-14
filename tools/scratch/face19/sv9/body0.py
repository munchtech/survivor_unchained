import numpy as np, trimesh
s = trimesh.load("C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/heroine.glb", force="scene")
for node in s.graph.nodes_geometry:
    T, g = s.graph[node]
    v = trimesh.transformations.transform_points(s.geometry[g].vertices, T)
    print(node, g, len(v), np.round(v.min(0), 3), np.round(v.max(0), 3))
