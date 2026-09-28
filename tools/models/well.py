"""The Waystation's well, in the village kit's stone, timber and tile.

    <venv with bpy>/bin/python tools/models/well.py

A round shaft of the town walls' rough stone, capped with dressed slabs; two
posts and a beam carrying a windlass, rope wound on it and a bucket hanging;
a little tiled roof, its tiles rounded like the kit's; dark water below.
The origin is the middle of the well at ground level; about 2.3 m across
and 3 m to the ridge.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from kitmodel import reset, box, cylinder, part, smooth, export  # noqa: E402

random.seed(7)
reset()

R_OUT, R_IN, H = 1.0, 0.72, 0.78   # the shaft: outer and inner radius, height

# The shaft, outside and in (rough stone wrapped round).
cylinder('shaft', R_OUT, H, (0, 0, H / 2), 'MI_UnevenBrick', lay='ring', sides=28, caps=False)
cylinder('shaft_in', R_IN, H, (0, 0, H / 2), 'MI_UnevenBrick', lay='ring', sides=28, caps=False, inward=True, u0=0.37)
# Dark water, a way down.
bpy.ops.mesh.primitive_circle_add(vertices=28, radius=R_IN, fill_type='NGON', location=(0, 0, 0.42))
part('water', bpy.context.active_object, 'MI_WellWater', 'tile')

# Capstones: dressed slabs round the rim, each a little off true.
N = 13
for i in range(N):
    a = (i + 0.5) / N * math.tau
    r = (R_OUT + R_IN) / 2 + 0.04
    length = 2 * math.pi * r / N - 0.03
    o = box(f'cap{i}', (length, 0.44, 0.12 + random.uniform(-0.01, 0.015)),
            (math.cos(a) * r, math.sin(a) * r, H + 0.06 + random.uniform(-0.008, 0.008)),
            'MI_RockTrim', lay='band', rot=(random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), a + math.pi / 2),
            bevel=0.025, band='slab', end='slab', axis=(-math.sin(a), math.cos(a), 0), u0=random.random())

# Posts and the beam (timber, grain along each piece).
PX = 0.98
for s in (-1, 1):
    box(f'post{s}', (0.16, 0.16, 1.9), (s * PX, 0, H + 0.1 + 0.95), 'MI_WoodTrim', bevel=0.018, band='grain', axis=(0, 0, 1))
    # A knee brace from post to beam.
    box(f'brace{s}', (0.09, 0.09, 0.55), (s * (PX - 0.2), 0, H + 1.88), 'MI_WoodTrim', rot=(0, s * math.radians(45), 0),
        bevel=0.01, band='grain', axis=(s * -0.707, 0, 0.707))
box('beam', (2.36, 0.15, 0.17), (0, 0, H + 2.08), 'MI_WoodTrim', bevel=0.018, band='grain', axis=(1, 0, 0))

# The windlass: a drum between the posts, rope wound on it, a crank outside.
WZ = H + 0.95
cylinder('drum', 0.085, 2 * PX - 0.16, (0, 0, WZ), 'MI_WoodTrim', rot=(0, math.pi / 2, 0), sides=12, band='grain', axis=(1, 0, 0))
smooth(cylinder('coil', 0.115, 0.46, (0.05, 0, WZ), 'MI_Rope', 'tile', rot=(0, math.pi / 2, 0), sides=14))
cylinder('axle', 0.03, 0.34, (PX + 0.12, 0, WZ), 'MI_Iron', 'tile', rot=(0, math.pi / 2, 0), sides=8)
box('crank', (0.04, 0.05, 0.36), (PX + 0.27, 0, WZ - 0.16), 'MI_Iron', 'tile')
cylinder('handle', 0.025, 0.2, (PX + 0.35, 0, WZ - 0.32), 'MI_Iron', 'tile', rot=(0, math.pi / 2, 0), sides=8)

# The rope down, and the bucket on it.
BZ = H + 0.22
cylinder('rope', 0.014, WZ - 0.11 - (BZ + 0.24), (0.12, 0, (WZ - 0.11 + BZ + 0.24) / 2), 'MI_Rope', 'tile', sides=6)
cylinder('bucket', 0.155, 0.28, (0.12, 0, BZ), 'MI_WoodTrim', r2=0.19, sides=14, band='boards', end='ends', axis=(0, 0, 1))
for z in (BZ - 0.08, BZ + 0.09):
    cylinder(f'hoop{z:.2f}', 0.172 if z < BZ else 0.184, 0.028, (0.12, 0, z), 'MI_Iron', 'tile', sides=14)
bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.012, major_segments=16, minor_segments=5,
                                 location=(0.12, 0, BZ + 0.16), rotation=(math.pi / 2, 0, 0))
o = bpy.context.active_object
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.02], context='VERTS')  # half a ring: the bail
bm.to_mesh(o.data); bm.free()
part('bail', o, 'MI_Iron', 'tile')

# The roof: two pitches of round tiles, ridge along the beam.
RIDGE, EAVE, HALF_W, HALF_L = H + 2.62, H + 2.06, 1.0, 1.35
for s in (-1, 1):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=36, y_subdivisions=3, size=1)
    o = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(o.data)
    slope = math.hypot(HALF_W, RIDGE - EAVE)
    for v in bm.verts:
        x, y = v.co.x * 2 * HALF_L, (v.co.y + 0.5)  # y: 0 at the ridge, 1 at the eave
        # Round tiles: a row of barrels running down the slope.
        bump = 0.045 * abs(math.sin(math.pi * x / 0.3))
        v.co.x = x
        v.co.y = s * (y * HALF_W + bump * 0.2)
        v.co.z = RIDGE - y * (RIDGE - EAVE) + bump
    bm.to_mesh(o.data); bm.free()
    if s < 0:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
    m = o.modifiers.new('thick', 'SOLIDIFY'); m.thickness = 0.05; m.offset = -1
    smooth(o, 50)
    part(f'roof{s}', o, 'MI_RoundTiles', 'tile', axis=(1, 0, 0), down=True, density=0.56)
    # Barge boards along the gable ends.
    for e in (-1, 1):
        box(f'barge{s}{e}', (0.06, slope + 0.1, 0.16), (e * (HALF_L + 0.03), s * HALF_W / 2, (RIDGE + EAVE) / 2 + 0.03), 'MI_WoodTrim',
            rot=(-s * math.atan2(RIDGE - EAVE, HALF_W), 0, 0), bevel=0.01, band='boards', axis=(0, s * HALF_W, -(RIDGE - EAVE)))
smooth(cylinder('ridge', 0.075, 2 * HALF_L + 0.12, (0, 0, RIDGE + 0.03), 'MI_RoundTiles', 'tile', rot=(0, math.pi / 2, 0), sides=10, axis=(1, 0, 0), density=0.56))

export('Well')
