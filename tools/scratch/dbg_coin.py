import sys, math
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import bpy
import blender_frames as B
B.reset()
W, H = 200, 200
x, y, s = 100, 100, 80
sq = []
for k in range(4):
    a = math.radians(45) + k * math.pi / 2 + math.pi / 4
    sq.append((x + math.cos(a) * s / 2 * 1.41, y + math.sin(a) * s / 2 * 1.41))
hole = [(x + math.cos(a) * 14, y + math.sin(a) * 14) for a in [2 * math.pi * j / 32 for j in range(32)]][::-1]
ob = B.curve_object("coin", [B.densify(sq, 4), hole], W, H, extrude=5, bevel=2, z=10)
dg = bpy.context.evaluated_depsgraph_get()
me = ob.evaluated_get(dg).to_mesh()
import mathutils
# Is there geometry at the coin's centre (top face)?
c = B.P(x, y, W, H)
hit = 0
for p in me.polygons:
    v = [me.vertices[i].co for i in p.vertices]
    pass
print("polys", len(me.polygons), "verts", len(me.vertices))
# Ray cast straight down through the centre.
bpy.context.view_layer.update()
res = bpy.context.scene.ray_cast(dg, mathutils.Vector((c.x, c.y, 5)), mathutils.Vector((0, 0, -1)))
print("ray centre hit:", res[0], res[1])
res = bpy.context.scene.ray_cast(dg, mathutils.Vector((c.x + 0.25, c.y, 5)), mathutils.Vector((0, 0, -1)))
print("ray off-centre hit:", res[0], res[1])
