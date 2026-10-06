p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_config.py"
s = open(p, encoding="utf-8").read()
old_head = s[s.index('    "sculpt": "side14'):s.index('    "head_y": -0.5,')]
new_head = '''    "sculpt": "clay33 (boar_clay side, seed 33; TRELLIS 2 seed 42)",
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
'''
s = s.replace(old_head, new_head)
open(p, "w", encoding="utf-8").write(s)
print("ok")
