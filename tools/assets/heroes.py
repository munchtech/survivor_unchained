"""The survivors' bodies, built from MakeHuman's CC0 base with MPFB2 in
Blender: a woman and a man, adult (about thirty; the age is fixed here and
never below MakeHuman's 0.5, twenty-five), toned and generously shaped, with
skin, eyes, brows, lashes, hair and the game-engine rig with breast bones.

    blender -b --python tools/assets/heroes.py -- <out dir> [--render]

Writes <out>/hero_<sex>.blend and, with --render, a front and three-quarter
picture of each (<out>/hero_<sex>_*.png) to judge them by.
"""
import math
import os
import sys

import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[0] if ARGS else ".")
RENDER = "--render" in ARGS
DATA = LocationService.get_user_data()

# Adult, always: MakeHuman's age 0.5 is 25 and 0.5625 is about 30.
ADULT_AGE = 0.5625

HEROES = {
    "female": dict(
        macro=dict(gender=0.0, age=ADULT_AGE, muscle=0.68, weight=0.42, proportions=1.0, height=0.62, cupsize=0.88, firmness=0.9),
        skin="skins/toigo_light_skin_female_bronze/toigo_light_skin_female_bronze.mhmat",
        hair="hair/long01/long01.mhclo", brows="eyebrows/eyebrow010/eyebrow010.mhclo", lashes="eyelashes/eyelashes02/eyelashes02.mhclo",
        # The shape past what the macro sliders give: lifted and full at the
        # bust, a narrow waist, wide hips, a full seat, a toned stomach, long legs.
        detail={"breast/breast-trans-up": 0.55, "breast/breast-volume-vert-up": 0.45, "torso/measure-bust-circ-incr": 0.55,
                "torso/measure-underbust-circ-decr": 0.3, "torso/measure-waist-circ-decr": 0.75, "hip/hip-scale-horiz-incr": 0.35,
                "buttocks/buttocks-volume-incr": 0.75, "stomach/stomach-tone-incr": 0.6, "legs/upperlegs-height-incr": 0.3,
                "legs/l-upperleg-muscle-incr": 0.3, "legs/r-upperleg-muscle-incr": 0.3},
    ),
    "male": dict(
        macro=dict(gender=1.0, age=ADULT_AGE, muscle=1.0, weight=0.55, proportions=1.0, height=0.7, cupsize=0.5, firmness=0.5),
        skin="skins/middleage_caucasian_male/middleage_caucasian_male.mhmat",
        hair="hair/short02/short02.mhclo", brows="eyebrows/eyebrow001/eyebrow001.mhclo", lashes="eyelashes/eyelashes01/eyelashes01.mhclo",
        # A hero's build: a hard V from broad shoulders to a narrow waist, a
        # full chest, big arms, a cut stomach.
        detail={"torso/torso-vshape-incr": 0.9, "torso/torso-muscle-pectoral-incr": 0.8, "torso/torso-muscle-dorsi-incr": 0.6,
                "torso/measure-shoulder-dist-incr": 0.55, "torso/measure-waist-circ-decr": 0.45, "stomach/stomach-tone-incr": 0.9,
                "arms/l-upperarm-muscle-incr": 0.7, "arms/r-upperarm-muscle-incr": 0.7, "arms/l-upperarm-shoulder-muscle-incr": 0.6,
                "arms/r-upperarm-shoulder-muscle-incr": 0.6, "arms/l-lowerarm-muscle-incr": 0.5, "arms/r-lowerarm-muscle-incr": 0.5,
                "legs/l-upperleg-muscle-incr": 0.6, "legs/r-upperleg-muscle-incr": 0.6, "buttocks/buttocks-volume-incr": 0.3},
    ),
}


def find(rel):
    p = os.path.join(DATA, rel)
    if os.path.exists(p):
        return p
    raise FileNotFoundError(rel)


def build(sex, spec):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    macro = dict(spec["macro"])
    macro["age"] = max(0.5, macro["age"])
    macro["race"] = {"asian": 0.15, "caucasian": 0.7, "african": 0.15}
    human = HumanService.create_human(macro_detail_dict=macro)
    human.name = f"hero_{sex}"
    tdir = os.path.join(os.path.dirname(os.path.dirname(LocationService.get_mpfb_data())) if False else LocationService.get_mpfb_data(), "targets")
    for rel, w in spec.get("detail", {}).items():
        TargetService.load_target(human, os.path.join(tdir, rel + ".target.gz"), weight=w)
    HumanService.add_builtin_rig(human, "game_engine_with_breast" if sex == "female" else "game_engine")
    HumanService.set_character_skin(find(spec["skin"]), human, skin_type="ENHANCED_SSS")
    for kind, rel in (("Eyebrows", spec["brows"]), ("Eyelashes", spec["lashes"]), ("Hair", spec["hair"])):
        HumanService.add_mhclo_asset(find(rel), human, asset_type=kind, subdiv_levels=0, material_type="MAKESKIN")
    eyes = os.path.join(DATA, "eyes", "low-poly", "low-poly.mhclo")
    if os.path.exists(eyes):
        HumanService.add_mhclo_asset(eyes, human, asset_type="Eyes", subdiv_levels=0)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"hero_{sex}.blend"))
    if RENDER:
        render(sex)


def render(sex):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = 900, 1400
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world
    for name, loc, energy in (("key", (2.5, -3, 3.5), 900), ("fill", (-3, -2, 2), 300), ("rim", (0, 3, 3), 600)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.size = energy, 2
        obj = bpy.data.objects.new(name, light)
        obj.location = loc
        scene.collection.objects.link(obj)
        obj.rotation_euler = (0, 0, 0)
        c = obj.constraints.new("TRACK_TO")
        c.target = None
        direction = -__import__("mathutils").Vector(loc) + __import__("mathutils").Vector((0, 0, 1))
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 75
    for tag, ang in (("front", 0), ("three", 35), ("back", 180)):
        a = math.radians(ang)
        cam.location = (math.sin(a) * 6.2, -math.cos(a) * 6.2, 0.95)
        cam.rotation_euler = (math.radians(90), 0, a)
        scene.render.filepath = os.path.join(OUT, f"hero_{sex}_{tag}.png")
        bpy.ops.render.render(write_still=True)


for sex, spec in HEROES.items():
    build(sex, spec)
print("HEROES DONE")
