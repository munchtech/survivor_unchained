"""Each share bone's Z (the bulge's axis) against her front, and her skin's
reach along it round the joint at rest (the flexor and extensor radii)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import WT  # noqa: E402
from rig import Skeleton  # noqa: E402
from skin import Body  # noqa: E402

sk = Skeleton.load(WT / "tools" / "anim" / "data" / "heroine_skeleton.json")
b = Body(sk, [(WT / "godot/art/people/heroine.glb", lambda n: n == "Heroine", "skin")], None, helpers=True)
for name in ("calf_share_l", "calf_share_r", "lowerarm_share_l", "lowerarm_share_r", "upperarm_share_l"):
    j = b.sk.index[name]
    M = b.rest[j]
    R, o = M[:3, :3], M[:3, 3]
    loc = (b.P - o) @ R            # points in the share's frame
    near = (np.abs(loc[:, 1]) < 0.02) & (np.hypot(loc[:, 0], loc[:, 2]) < 0.15)
    z = loc[near, 2]
    x = loc[near, 0]
    print(f"{name:18s} Z.front {R[:, 2] @ [0, 0, 1]:+.2f} Z.up {R[:, 2] @ [0, 1, 0]:+.2f} Y.down {R[:, 1] @ [0, -1, 0]:+.2f}  "
          f"skin within 2 cm of the joint: z {z.min()*100:+.1f}..{z.max()*100:+.1f} cm, x {x.min()*100:+.1f}..{x.max()*100:+.1f} cm (n={near.sum()})")
