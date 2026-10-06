import bpy, sys, json, math
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures")
import importlib, quadruped as Q
importlib.reload(Q)
bpy.ops.wm.read_factory_settings(use_empty=True)
lm = dict(pelvis=(0, 0.42, 0.72), spine1=(0, 0.2, 0.76), spine2=(0, -0.05, 0.78), chest=(0, -0.3, 0.78), neck1=(0, -0.45, 0.72),
          neck2=(0, -0.58, 0.66), head=(0, -0.68, 0.62), snout=(0, -0.95, 0.45), snout_end=(0, -1.02, 0.42), jaw=(0, -0.75, 0.5),
          jaw_end=(0, -0.95, 0.38), ear=(0.07, -0.66, 0.74), ear_end=(0.12, -0.6, 0.84), tail1=(0, 0.6, 0.7), tail2=(0, 0.63, 0.6),
          tail3=(0, 0.64, 0.5), tail_end=(0, 0.64, 0.42), scapula=(0.14, -0.22, 0.8), shoulder=(0.16, -0.38, 0.55),
          elbow=(0.15, -0.3, 0.36), carpus=(0.14, -0.35, 0.16), fetlock=(0.14, -0.37, 0.05), front_toe=(0.14, -0.44, 0.0),
          hip=(0.13, 0.44, 0.6), stifle=(0.15, 0.30, 0.38), hock=(0.14, 0.45, 0.18), hind_fetlock=(0.14, 0.42, 0.05), hind_toe=(0.14, 0.35, 0.0))
arm = Q.build_armature(lm)
L = Q.legs(arm)
g = Q.Gait(period=0.36, speed=3.0, duty=0.45, phase={"FL": 0, "HR": 0.02, "FR": 0.5, "HL": 0.52})
out = []
for i in range(12):
    t = i / 12
    p = Q.Poser(arm)
    Q.pose_gait(p, g, t, L)
    out.append({n: [list(p.head(n)), list(p.tail(n))] for n in p.basis})
# check the keyed pose matches the poser: apply then read back pose bones
p = Q.Poser(arm); Q.pose_gait(p, g, 0.3, L); p.apply()
bpy.context.view_layer.update()
err = 0
for pb in arm.pose.bones:
    err = max(err, (pb.head - p.head(pb.name)).length, (pb.tail - p.tail(pb.name)).length)
print("POSE ERR", err)
json.dump(out, open(sys.argv[-1], "w"))
