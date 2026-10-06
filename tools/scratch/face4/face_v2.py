"""face_v2.py: FACE plus slider settings (as their targets) plus extra targets, printed as face_shapes source."""
import json
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\tools\assets")
import face_shapes as fs  # noqa: E402
import face_presets as fp  # noqa: E402

sliders = dict(jaw_width=-0.7, chin_width=-0.5, chin_length=-0.2, face_shape=-0.5, cheekbone_height=0.6, cheekbone_width=0.4,
               cheeks=-0.3, face_width=-0.3, eyes_open=-0.6, eyes_tilt=0.35, eyes_size=0.25, nose_length=-0.3, nose_tip=0.25,
               nose_width=-0.2, mouth_width=0.15, cupids_bow=0.5, mouth_height=0.3, mouth_corners=0.2, brows_arch=0.4,
               lips_forward=-0.4, chin_forward=0.3, nose_projection=-0.2)
extra = {"mouth-upperlip-middle-up": 0.6, "mouth-lowerlip-height-incr": 0.4, "mouth-upperlip-height-incr": 0.3,
         "mouth-scale-depth-decr": 0.3, "mouth-upperlip-volume-incr": -0.18, "mouth-lowerlip-volume-incr": -0.2}
face = dict(fs.FACE)
add = fp.to_targets(sliders)
sculpt = {t: w for t, w in add.items() if t in fs.SCULPTS}
for t, w in list(add.items()) + list(extra.items()):
    if t in fs.SCULPTS:
        continue
    face[t] = round(face.get(t, 0.0) + w, 3)
print("sculpts left out of FACE (as a slider default instead):", sculpt, file=sys.stderr)
json.dump(face, open(sys.argv[1], "w"), indent=1)
print(len(face), "targets", file=sys.stderr)
