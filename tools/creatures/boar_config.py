"""The boar's settings, shared by the build (in Blender) and the paint
(plain Python): how its sculpt sits, what is cut from it and remade, where
its tusks, tail and crest go, and its landmarks for the rig. Positions are
metres in Blender's axes once the sculpt is prepped: the beast faces -Y,
+Z is up, +X its left, its feet at z 0; the left side is given and the
right mirrored.

Read off the sculpt's pictures (tools/creatures/views.py) at full size.
"""

CONFIG = {
    "sculpt": "clay33 (boar_clay side, seed 33; TRELLIS 2 seed 42)",
    "yaw": -42.0,            # degrees about Z that bring its snout to -Y
    "length": 1.55,          # snout to rump along Y
    # Its body curves (the head turned to its left, the hindquarters swung
    # to its right): x shifts along its length, (y, dx), before mirroring.
    "straighten": [(-0.8, -0.055), (-0.55, -0.03), (-0.3, 0.0), (0.0, 0.025), (0.3, 0.055), (0.5, 0.08), (0.75, 0.09)],
    "mirror": "-X",          # the half kept: its right side, the one the picture showed
    "cut": {
        "tail_y": 0.665,                              # behind the rump (the tail hangs there)
        "ears": [(0.24, -0.38, 0.75, 0.12)],          # (x, y, z, radius)
        "tusks": (-0.58, 0.06, 0.40, 0.62),           # forward of y, outside |x|, between z
    },
    # The back's line under the crest: anything this far above it, near the
    # spine, is crest and is cut (the cards make it).
    "backline": {"line": [(-0.45, 0.74), (-0.3, 0.8), (-0.1, 0.83), (0.2, 0.82), (0.5, 0.8), (0.65, 0.77)], "over": 0.03, "half": 0.14},
    "head_y": -0.5,          # smoothed lightly forward of this (the face is the sculpt's own)
    "leg_z": 0.26,           # and below this (the lower legs)
    "faces": 4800,           # the low mesh's quads
    "tusks": [
        # The great lower tusks: out of the jaw at the lip's corner, out wide
        # and up past the eye, hooked back at the tip.
        {"root": (0.085, -0.70, 0.43), "length": 0.24, "r0": 0.021, "sweep": (0.55, 0.75, 0.05), "curl": 0.3},
        # The upper whetters: shorter, thick, curling up over them.
        {"root": (0.075, -0.72, 0.47), "length": 0.11, "r0": 0.016, "sweep": (0.45, 0.8, 0.2), "curl": 0.2, "rings": 7},
    ],
    "tail": {"path": [(0, 0.58, 0.76), (0, 0.66, 0.72), (0, 0.68, 0.55), (0, 0.67, 0.42)], "r0": 0.022, "r1": 0.01},
    "crest": {
        "from": -0.47, "to": 0.5, "count": 30, "fan": (-1, 0, 1), "spread": 0.03,
        # Card length along the spine (0 at the nape, 1 at the rump): tallest over the hump.
        "length": [(0.0, 0.12), (0.25, 0.2), (0.45, 0.17), (0.75, 0.11), (1.0, 0.07)],
        "lean": 40, "splay": 18, "bend": 25, "width": 0.07, "tuft": 5,
    },
    # The skeleton's joints (left side; quadruped.build_armature).
    "rig": dict(
        pelvis=(0, 0.44, 0.68), spine1=(0, 0.30, 0.70), spine2=(0, 0.08, 0.72), chest=(0, -0.18, 0.74),
        neck1=(0, -0.26, 0.73), neck2=(0, -0.35, 0.72), head=(0, -0.44, 0.70), snout=(0, -0.62, 0.52),
        snout_end=(0, -0.80, 0.40), jaw=(0, -0.50, 0.50), jaw_end=(0, -0.74, 0.38),
        ear=(0.12, -0.47, 0.82), ear_end=(0.2, -0.43, 0.92),
        tail1=(0, 0.58, 0.74), tail2=(0, 0.66, 0.70), tail3=(0, 0.68, 0.56), tail_end=(0, 0.67, 0.43),
        scapula=(0.13, -0.22, 0.80), shoulder=(0.15, -0.30, 0.55), elbow=(0.15, -0.22, 0.38),
        carpus=(0.145, -0.28, 0.20), fetlock=(0.145, -0.29, 0.09), front_toe=(0.145, -0.37, 0.01),
        hip=(0.13, 0.40, 0.64), stifle=(0.14, 0.34, 0.42), hock=(0.13, 0.52, 0.23),
        hind_fetlock=(0.13, 0.50, 0.10), hind_toe=(0.13, 0.42, 0.01),
    ),
    # The bones' height in the game (Beasts.cs's Height): what the bake
    # scales the skeleton's span of joints to.
    "game_height": 0.82,
}


def override(argv):
    """Any setting can be tried from the command line: --name value."""
    for i, a in enumerate(argv[:-1]):
        if a.startswith("--") and a[2:] not in ("work", "sculpt", "out", "tex", "maps"):
            v = argv[i + 1]
            try:
                CONFIG[a[2:]] = int(v) if v.lstrip("-").isdigit() else float(v)
            except ValueError:
                CONFIG[a[2:]] = v
