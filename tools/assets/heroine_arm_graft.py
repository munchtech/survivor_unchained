"""Her arm root grafted from the Marionette shared base's quad arm (Body 1, armor 18 g1, 22 October 2026).

Her arm root (shoulder top, deltoid, pit, upper arm to the elbow crease) was a decimated triangle mesh with no loops
(median edge ~1 cm, slivers to 6.2 cm). This replaces it, both sides, with the MakeHuman CC0 base's arm patch
(C:/Users/munch/Desktop/Marionette/public/base/base.json/.bin, read only): aligned from her joints, rigid+scale ICP,
a Laplacian-regularised non-rigid fit (normal-compatible closest points) to her Taubin-smoothed sculpt, two
Catmull-Clark levels (median edge ~0.4 cm), refit, folds in the pinched pit faired. It is trimmed 6 mm inside her
patch's ring, the ring left as it was (her torso and forearm vertices keep their indices; the old patch's vertex
slots are reused, the rest appended), and stitched to it by an optimal zipper (DP over the two loops) with diagonal
flips. Weights (top 4, normalised), the graft attribute, UVs (per face from her old UV island under it, corners
projected into that island), materials, sharp edges and smooth custom normals across the seam are carried.

    blender -b heroine_built.blend --python tools/assets/arm_graft/b_dump.py -- <work>/her.npz
    python tools/assets/heroine_arm_graft.py            # fit, build, carry, check (env ARM_GRAFT_WORK = <work>)
    blender -b heroine_built.blend --python tools/assets/arm_graft/b_write.py -- <work>/graft_data.npz <out.blend>

Never overwrite heroine_built.blend; write heroine_built_armroot.blend. Steps: fit.py (fit.npz), build.py
(graft_geom.npz; env GAP, default 6 mm), carry.py (graft_data.npz), check.py (cracks, folds, seam angles).
"""
import os, subprocess, sys
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arm_graft")
for step in ("fit.py", "build.py", "carry.py", "check.py"):
    print("==", step, flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, step)], cwd=HERE)
    if r.returncode:
        sys.exit(r.returncode)
