import bpy, sys
from mathutils import Vector
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, tuple(round(v,3) for v in o.location), o.parent.name if o.parent else None, len(o.data.vertices) if o.type=='MESH' else '')
arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
print("ARM", arm.name, arm.data.name, len(arm.data.bones), arm.matrix_world)
for b in arm.data.bones:
    h = arm.matrix_world @ b.head_local; t = arm.matrix_world @ b.tail_local
    m = b.matrix_local.to_3x3()
    print("BONE %-14s parent=%-12s head=(%.3f,%.3f,%.3f) tail=(%.3f,%.3f,%.3f) len=%.3f y=(%.2f,%.2f,%.2f) z=(%.2f,%.2f,%.2f)" % (b.name, b.parent.name if b.parent else '-', *h, *t, b.length, *m.col[1], *m.col[2]))
print("ACTIONS", [a.name for a in bpy.data.actions][:50], len(bpy.data.actions))
