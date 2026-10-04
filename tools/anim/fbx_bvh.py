"""An FBX animation (Mixamo's, "Without Skin") as BVH for tools/anim/retarget.py.

    blender -b --python tools/anim/fbx_bvh.py -- <in.fbx> <out.bvh>

Written by hand rather than with Blender's BVH exporter so the BVH is in the
retargeter's terms: Y up, centimetres, and a rest whose joint frames are the
world's (the armature's own rest, Mixamo's T-pose), each frame's rotations
the bones' turns from that rest. Mixamo's files stay out of the repository
(its terms allow the motion in a game, not the files passed on); the BVH
and the clips made from it live in the tools' mocap folder and her library.
"""
import sys

import bpy
from mathutils import Matrix

args = sys.argv[sys.argv.index("--") + 1:]
src, dst = args[0], args[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src, automatic_bone_orientation=False)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
scene = bpy.context.scene
act = arm.animation_data.action if arm.animation_data else None
f0, f1 = (int(act.frame_range[0]), int(act.frame_range[1])) if act else (scene.frame_start, scene.frame_end)

# Blender (Z up, the figure facing -Y) to BVH (Y up, facing +Z).
C = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))

bones = list(arm.data.bones)
order = []


def walk(b):
    order.append(b)
    for c in b.children:
        walk(c)


for b in bones:
    if b.parent is None:
        walk(b)


def world_rest(b):
    m = arm.matrix_world @ b.matrix_local
    return C @ m.to_3x3().normalized(), C @ m.to_translation()


rest = {b.name: world_rest(b) for b in order}
lines = ["HIERARCHY"]


def emit(b, depth):
    ind = "  " * depth
    _, p = rest[b.name]
    off = p - rest[b.parent.name][1] if b.parent else p
    off = off * 100.0
    lines.append(f"{ind}{'ROOT' if b.parent is None else 'JOINT'} {b.name}")
    lines.append(f"{ind}{{")
    lines.append(f"{ind}  OFFSET {off.x:.5f} {off.y:.5f} {off.z:.5f}")
    lines.append(f"{ind}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation")
    for c in b.children:
        emit(c, depth + 1)
    if not b.children:
        tail = (C @ (arm.matrix_world @ b.tail_local)) - p
        tail = tail * 100.0
        lines.append(f"{ind}  End Site")
        lines.append(f"{ind}  {{")
        lines.append(f"{ind}    OFFSET {tail.x:.5f} {tail.y:.5f} {tail.z:.5f}")
        lines.append(f"{ind}  }}")
    lines.append(f"{ind}}}")


for b in order:
    if b.parent is None:
        emit(b, 0)

frames = []
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    g = {}
    row = []
    for b in order:
        pb = arm.pose.bones[b.name]
        m = arm.matrix_world @ pb.matrix
        R = C @ m.to_3x3().normalized()
        P = C @ m.to_translation()
        # The bone's turn from rest, in the world.
        d = R @ rest[b.name][0].inverted()
        g[b.name] = d
        local = (g[b.parent.name].inverted() @ d) if b.parent else d
        if b.parent:
            # Position in the parent's turned rest frame.
            pp = P - (C @ (arm.matrix_world @ arm.pose.bones[b.parent.name].matrix).to_translation())
            pos = (g[b.parent.name].inverted() @ pp) * 100.0
        else:
            pos = P * 100.0
        e = local.to_euler("YXZ")  # applied Z, then X, then Y as written
        import math
        row += [pos.x, pos.y, pos.z, math.degrees(e.z), math.degrees(e.x), math.degrees(e.y)]
    frames.append(row)

lines.append("MOTION")
lines.append(f"Frames: {len(frames)}")
lines.append(f"Frame Time: {1.0 / (scene.render.fps / scene.render.fps_base):.6f}")
for r in frames:
    lines.append(" ".join(f"{v:.5f}" for v in r))
open(dst, "w").write("\n".join(lines) + "\n")
print("BVH", dst, len(frames), "frames")
