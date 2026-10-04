"""The heroine's face, as data: the MakeHuman woman she is made from, the
targets that shape her own face, and her face's sliders (each a shape key
one way and the other, from MakeHuman's targets and sculpts of our own),
shared by heroine_head.py (which builds her), face_lab.py (which tries
faces out) and face_fit.py (which fits them to references).

Plain Python (no Blender), so the game's data and the tests can read it.
"""
import os

# MakeHuman's woman: young, slim, ideal proportions.
MACROS = {"gender": 0.0, "age": 0.5, "muscle": 0.75, "weight": 0.5, "proportions": 1.0, "height": 0.5, "cupsize": 0.5,
          "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
# Her parts, MakeHuman's own (all CC0): kind, asset.
PARTS = [("eyes", "high-poly"), ("eyebrows", "eyebrow010"), ("eyelashes", "eyelashes03"), ("teeth", "teeth_base"),
         ("tongue", "tongue01")]
EYES = "green"
SKIN = ("skins", "toigo_light_skin_female_ginger")

# Her own face: MakeHuman's woman shaped by its targets (each with its
# weight; "X-" is both sides). Every slider moves her from here.
FACE = {"head-age-decr": 0.35, "head-fat-decr": 0.2, "X-eye-scale-incr": 0.35, "X-eye-corner2-up": 0.35, "eyebrows-angle-up": 0.3,
        "nose-scale-horiz-decr": 0.65, "nose-point-up": 0.3, "nose-point-width-decr": 0.3, "nose-hump-decr": 0.45, "nose-scale-vert-decr": 0.3,
        "mouth-upperlip-volume-incr": 0.75, "mouth-lowerlip-volume-incr": 0.8, "mouth-cupidsbow-incr": 0.5, "mouth-angles-up": 0.2,
        "X-cheek-bones-incr": 0.15, "X-cheek-volume-incr": 0.5, "chin-bones-incr": 0.1, "chin-width-incr": 0.3, "chin-height-decr": 0.25,
        "chin-triangle": 0.2, "chin-prominent-incr": 0.15}
# Her build where her head meets her body (MakeHuman's woman is longer and
# slimmer of neck than she was made).
BUILD = {"measure-neck-height-decr": 0.9, "measure-neck-circ-incr": 0.5, "neck-back-scale-depth-incr": 0.3}

# Sculpts of our own, where MakeHuman has no target: name -> f(points, anatomy) -> moves.
SCULPTS = {}


def _both(stem, ends=("incr", "decr")):
    return [f"{stem}-{e}" for e in ends]


# The targets her own face is fitted from (face_fit.py, to a reference
# painting): all of MakeHuman's that shape a face seen from in front and
# from three-quarters (not her ears or neck, which the landmarks miss).
FIT_TARGETS = (
    ["head-oval", "head-round", "head-square", "head-triangular", "head-invertedtriangular", "head-diamond", "head-rectangular"]
    + _both("head-scale-horiz") + _both("head-scale-vert") + _both("head-age") + _both("head-fat")
    + _both("forehead-scale-vert") + _both("forehead-temple") + ["forehead-trans-backward", "forehead-trans-forward"]
    + ["eyebrows-trans-up", "eyebrows-trans-down", "eyebrows-angle-up", "eyebrows-angle-down", "eyebrows-trans-forward",
       "eyebrows-trans-backward"]
    + _both("X-eye-scale") + ["X-eye-trans-in", "X-eye-trans-out", "X-eye-trans-up", "X-eye-trans-down"]
    + [f"X-eye-corner{i}-{e}" for i in (1, 2) for e in ("up", "down")] + [f"X-eye-height{i}-{e}" for i in (1, 2, 3) for e in ("incr", "decr")]
    + [f"X-eye-push{i}-{e}" for i in (1, 2) for e in ("in", "out")] + ["X-eye-epicanthus-in", "X-eye-epicanthus-out"]
    + _both("nose-scale-horiz") + _both("nose-scale-vert") + _both("nose-scale-depth") + ["nose-trans-up", "nose-trans-down"]
    + ["nose-point-up", "nose-point-down"] + _both("nose-point-width") + _both("nose-hump") + _both("nose-nostrils-width")
    + _both("nose-flaring") + [f"nose-width{i}-{e}" for i in (1, 2, 3) for e in ("incr", "decr")] + ["nose-base-up", "nose-base-down"]
    + _both("nose-volume")
    + _both("mouth-scale-horiz") + _both("mouth-scale-vert") + ["mouth-trans-up", "mouth-trans-down", "mouth-trans-forward",
                                                               "mouth-trans-backward"]
    + _both("mouth-upperlip-volume") + _both("mouth-lowerlip-volume") + _both("mouth-upperlip-height") + _both("mouth-lowerlip-height")
    + _both("mouth-upperlip-width") + _both("mouth-lowerlip-width") + _both("mouth-cupidsbow") + ["mouth-angles-up", "mouth-angles-down"]
    + _both("X-cheek-bones") + _both("X-cheek-volume") + _both("X-cheek-inner") + ["X-cheek-trans-up", "X-cheek-trans-down"]
    + _both("chin-width") + _both("chin-height") + _both("chin-prominent") + _both("chin-bones") + ["chin-triangle"]
    + _both("chin-jaw-drop") + _both("chin-prognathism")
)


def sides(names):
    """Target names, "X-" ones as both sides."""
    out = []
    for n in names:
        out += [n.replace("X-", "l-", 1), n.replace("X-", "r-", 1)] if n.startswith("X-") else [n]
    return out


def weight_of(target):
    """The weight FACE or BUILD gives a target (by its own side's name)."""
    for d in (FACE, BUILD):
        for t, v in d.items():
            if target in sides([t]):
                return v
    return 0.0


def target_paths():
    """Every MakeHuman target by name (expressions as "x:name")."""
    import bpy
    tdir = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets")
    out = {}
    for root, _, files in os.walk(tdir):
        for f in files:
            if f.endswith(".target.gz") and "expression" not in root:
                out.setdefault(f[:-10], os.path.join(root, f))
    for f in os.listdir(os.path.join(tdir, "expression", "units", "caucasian")):
        out["x:" + f[:-10]] = os.path.join(tdir, "expression", "units", "caucasian", f)
    return out


def anatomy(P):
    """Where her face's parts are, from her points (in the world): filled in
    with the sculpts."""
    return {}
