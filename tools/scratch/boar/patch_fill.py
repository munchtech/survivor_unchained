p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
a = s.index("    solid = np.zeros(dims, bool)\n    # Inside by parity along each column")
b = s.index("    bpy.data.objects.remove(shell)\n    print(\"FILLED\"")
new = '''    # Inside: everything the outside can't reach. The closed remesh is
    # marked into the voxels as a wall (densely: its corners, edges' and
    # faces' middles), the empty space flooded from the box's edge, and the
    # rest is the solid (thin double walls become slabs the opening removes).
    me = shell.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    tri = tri.reshape(-1, 3)
    ta, tb, tc = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    pts = np.concatenate([co, (ta + tb + tc) / 3, (ta + tb) / 2, (tb + tc) / 2, (tc + ta) / 2])
    ijk = np.floor((pts - np.array(lo)) / vox).astype(int)
    wall = np.zeros(dims, bool)
    wall[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
    wall = ndimage.binary_dilation(wall)
    lab, n = ndimage.label(~wall)
    outside = lab == lab[0, 0, 0]
    solid = ~outside
'''
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
