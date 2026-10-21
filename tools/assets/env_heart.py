"""The Warden's heart (E7c): a fist-sized stone cut in a few broad, chipped faces, sculpted as env_rocks.py's
stones are (an icosphere pushed out to an ellipsoid, cut by soft planes and hard fracture faces, lumps and grit).

    blender -b -P tools/assets/env_heart.py
    then  Godot_console --headless --path godot --import

Out: godot/art/world/props/heart.gltf (+ .bin): meshes lod0 (close-ups) and lod1 (the play camera), about unit size
(OrbView measures it and scales its longest half-length to the orb's size: c03's size 0.05 is a 10 cm stone). Vertex colour
as env_rocks' bake: r edge wear, g cavity, b broad occlusion (the shader darkens the cavities, lifts the rims). Its
glowing veins are drawn in the shader (heart.gdshader), in the stone's own space, so they stay sharp at any lens.
Blender is z up here; glTF is y up (the exporter turns it).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import env_rocks as R  # noqa: E402

R.OUT = os.path.join(R.ROOT, 'godot', 'art', 'world', 'props')
# One variant: a chunky, slightly long stone (1 : 0.84 : 0.9), seven near-hard cuts for its broad faces, five hard
# fracture faces round it (the chips: 'fk' a 1% bevel), leaning any way ('fup' -0.5..0.6: faces below too, it is
# held and turned, not lying on the ground), its faces near flat, fine grit; no foot, nothing cut away.
R.PRESETS = {
    'heart': dict(lods=(9000, 2400, 2400), shadow=False, variants=[
        dict(seed=731, ax=(1.0, 0.84, 0.9), cz=0.0, planes=7, k=0.022, tilt=1.0, amp=0.02, freq=1.3, fine=0.004,
             foot=-40.0, fract=5, fk=0.01, fdepth=(0.78, 0.86), fup=(-0.5, 0.6)),
    ]),
}

if __name__ == '__main__':
    R.mesh('heart')
