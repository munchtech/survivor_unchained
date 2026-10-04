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
# weight; "X-" is both sides). Every slider moves her from here. Fitted by
# landmarks to the four AI references of her (face_fit.py: the mean of the
# four fits, depth held), then by eye toward the research
# (FACE_RESEARCH.md): eyes a touch larger, brows higher, the jaw and chin
# narrower, the lower lip the fuller.
FACE = {"head-age-decr": 0.619, "head-age-incr": 0.121, "head-diamond": 0.322, "head-fat-decr": 0.58,
        "head-scale-horiz-decr": 0.229, "head-scale-vert-incr": 0.16, "forehead-temple-decr": 0.03,
        "forehead-temple-incr": 0.133, "eyebrows-trans-up": 0.4, "X-eye-corner1-down": 0.285, "X-eye-corner2-down": 0.225,
        "X-eye-corner2-up": 0.25, "X-eye-epicanthus-in": 0.095, "X-eye-height1-decr": 0.095, "X-eye-height3-decr": 0.203,
        "X-eye-height3-incr": 0.192, "X-eye-scale-incr": 0.36, "X-eye-trans-down": 0.071, "X-eye-trans-in": 0.233,
        "X-eye-trans-out": 0.518, "nose-base-down": 0.217, "nose-hump-decr": 0.056, "nose-nostrils-width-incr": 0.104,
        "nose-point-down": 0.114, "nose-point-up": 0.2, "nose-point-width-decr": 0.3, "nose-scale-horiz-decr": 0.217,
        "nose-scale-horiz-incr": 0.178, "nose-scale-vert-incr": 0.117, "nose-trans-down": 0.372, "nose-volume-decr": 0.327,
        "nose-volume-incr": 0.068, "nose-width2-incr": 0.047, "nose-width3-incr": 0.025, "X-cheek-bones-decr": 0.031,
        "X-cheek-bones-incr": 0.044, "X-cheek-trans-down": 0.263, "X-cheek-trans-up": 0.225, "X-cheek-volume-incr": 0.114,
        "mouth-angles-up": 0.251, "mouth-cupidsbow-incr": 0.4, "mouth-lowerlip-volume-incr": 0.848,
        "mouth-lowerlip-width-incr": 0.101, "mouth-scale-horiz-decr": 0.118, "mouth-scale-horiz-incr": 0.397,
        "mouth-trans-down": 0.147, "mouth-upperlip-volume-incr": 0.729, "mouth-upperlip-width-decr": 0.024,
        "mouth-upperlip-width-incr": 0.12, "chin-bones-decr": 0.55, "chin-height-decr": 0.277, "chin-height-incr": 0.135,
        "chin-jaw-drop-decr": 0.211, "chin-width-decr": 0.4}
# Her build where her head meets her body (MakeHuman's woman is longer and
# slimmer of neck than she was made).
BUILD = {"measure-neck-height-decr": 0.9, "measure-neck-circ-incr": 0.5, "neck-back-scale-depth-incr": 0.3}

# Sculpts of our own, where MakeHuman has no target: name -> f(points, anatomy) -> moves.
SCULPTS = {}

# Her face's sliders, by group (FACE_RESEARCH.md 3: a portrait's order),
# each: (its name, the word for each end, the targets of its "+" key and of
# its "-" key, each with the weight its key is made at). The weight is the
# slider's reach: ±1 on the slider is the key at full, so a key is made as
# far as her face still looks well (checked in face_lab.py renders at both
# ends), and the game's slider spans all of it (REACH below).
SLIDER_GROUPS = ["Head", "Eyes", "Nose", "Cheeks", "Mouth", "Jaw", "Ears", "Neck"]
SLIDERS = {
    # Head
    "forehead_height": ("Head", "Forehead", "Low", "High", {"forehead-scale-vert-incr": 1.0}, {"forehead-scale-vert-decr": 1.0}),
    "forehead_slope": ("Head", "Brow line", "Sloped", "Upright", {"forehead-trans-forward": 1.0}, {"forehead-trans-backward": 1.0}),
    "forehead_round": ("Head", "Forehead shape", "Flat", "Rounded", {"forehead-nubian-incr": 1.0}, {"forehead-nubian-decr": 1.0}),
    "temples": ("Head", "Temples", "Narrow", "Full", {"forehead-temple-incr": 1.0}, {"forehead-temple-decr": 1.0}),
    "brow_ridge": ("Head", "Brow ridge", "Soft", "Heavy", {"eyebrows-trans-forward": 1.0}, {"eyebrows-trans-backward": 1.0}),
    "face_width": ("Head", "Face width", "Narrow", "Broad", {"head-scale-horiz-incr": 1.0}, {"head-scale-horiz-decr": 1.0}),
    "face_shape": ("Head", "Face shape", "Heart", "Oval", {"head-oval": 1.0}, {"head-invertedtriangular": 1.0}),
    # Eyes and brows
    "eyes_size": ("Eyes", "Size", "Small", "Large", {"X-eye-scale-incr": 1.0}, {"X-eye-scale-decr": 1.0}),
    "eyes_spacing": ("Eyes", "Set", "Close", "Wide", {"X-eye-trans-out": 1.0}, {"X-eye-trans-in": 1.0}),
    "eyes_height": ("Eyes", "Height", "Low", "High", {"X-eye-trans-up": 1.0}, {"X-eye-trans-down": 1.0}),
    "eyes_tilt": ("Eyes", "Tilt", "Downturned", "Upturned", {"X-eye-corner2-up": 1.0}, {"X-eye-corner2-down": 1.0}),
    "eyes_open": ("Eyes", "Lids", "Hooded", "Open", {"X-eye-height2-incr": 1.0}, {"X-eye-height2-decr": 1.0}),
    "eyes_depth": ("Eyes", "Depth", "Deep-set", "Prominent", {"X-eye-push1-out": 1.0}, {"X-eye-push1-in": 1.0}),
    "eyes_inner": ("Eyes", "Inner corners", "Round", "Almond", {"X-eye-epicanthus-in": 1.0}, {"X-eye-epicanthus-out": 1.0}),
    "brows_height": ("Eyes", "Brow height", "Low", "High", {"eyebrows-trans-up": 1.0}, {"eyebrows-trans-down": 1.0}),
    "brows_arch": ("Eyes", "Brow arch", "Straight", "Arched", {"eyebrows-angle-up": 1.0}, {"eyebrows-angle-down": 1.0}),
    # Nose
    "nose_width": ("Nose", "Width", "Narrow", "Broad", {"nose-scale-horiz-incr": 1.0}, {"nose-scale-horiz-decr": 1.0}),
    "nose_length": ("Nose", "Length", "Short", "Long", {"nose-scale-vert-incr": 1.0}, {"nose-scale-vert-decr": 1.0}),
    "nose_bridge": ("Nose", "Bridge", "Straight", "Aquiline", {"nose-hump-incr": 1.0}, {"nose-hump-decr": 1.0}),
    "nose_bridge_width": ("Nose", "Bridge width", "Fine", "Broad", {"nose-width1-incr": 1.0}, {"nose-width1-decr": 1.0}),
    "nose_tip": ("Nose", "Tip", "Down", "Upturned", {"nose-point-up": 1.0}, {"nose-point-down": 1.0}),
    "nose_tip_width": ("Nose", "Tip width", "Fine", "Round", {"nose-point-width-incr": 1.0}, {"nose-point-width-decr": 1.0}),
    "nose_projection": ("Nose", "Projection", "Flat", "Prominent", {"nose-scale-depth-incr": 1.0}, {"nose-scale-depth-decr": 1.0}),
    "nostrils": ("Nose", "Nostrils", "Fine", "Flared", {"nose-flaring-incr": 1.0}, {"nose-flaring-decr": 1.0}),
    # Cheeks
    "cheekbone_height": ("Cheeks", "Cheekbone height", "Low", "High", {"X-cheek-trans-up": 1.0}, {"X-cheek-trans-down": 1.0}),
    "cheekbone_width": ("Cheeks", "Cheekbone width", "Narrow", "Wide", {"X-cheek-bones-incr": 1.0}, {"X-cheek-bones-decr": 1.0}),
    "cheekbone_prominence": ("Cheeks", "Cheekbones", "Soft", "Sculpted", {"X-cheek-inner-incr": 1.0}, {"X-cheek-inner-decr": 1.0}),
    "cheeks": ("Cheeks", "Cheeks", "Hollow", "Full", {"X-cheek-volume-incr": 1.0}, {"X-cheek-volume-decr": 1.0}),
    # Mouth
    "lips_upper": ("Mouth", "Upper lip", "Thin", "Full", {"mouth-upperlip-volume-incr": 1.0}, {"mouth-upperlip-volume-decr": 1.0}),
    "lips_lower": ("Mouth", "Lower lip", "Thin", "Full", {"mouth-lowerlip-volume-incr": 1.0}, {"mouth-lowerlip-volume-decr": 1.0}),
    "mouth_width": ("Mouth", "Width", "Narrow", "Wide", {"mouth-scale-horiz-incr": 1.0}, {"mouth-scale-horiz-decr": 1.0}),
    "mouth_height": ("Mouth", "Height", "Low", "High", {"mouth-trans-up": 1.0}, {"mouth-trans-down": 1.0}),
    "mouth_corners": ("Mouth", "Corners", "Down", "Up", {"mouth-angles-up": 1.0}, {"mouth-angles-down": 1.0}),
    "cupids_bow": ("Mouth", "Cupid's bow", "Soft", "Sharp", {"mouth-cupidsbow-incr": 1.0}, {"mouth-cupidsbow-decr": 1.0}),
    "lips_forward": ("Mouth", "Pout", "Back", "Forward", {"mouth-trans-forward": 1.0}, {"mouth-trans-backward": 1.0}),
    # Jaw and chin
    "jaw_width": ("Jaw", "Jaw width", "Narrow", "Wide", {"chin-bones-incr": 1.0}, {"chin-bones-decr": 1.0}),
    "jaw_angle": ("Jaw", "Jaw angle", "Soft", "Sharp", {"chin-jaw-drop-incr": 1.0}, {"chin-jaw-drop-decr": 1.0}),
    "chin_width": ("Jaw", "Chin width", "Pointed", "Broad", {"chin-width-incr": 1.0}, {"sculpt-chin-narrow": 1.0, "chin-width-decr": 0.4}),
    "chin_length": ("Jaw", "Chin length", "Short", "Long", {"chin-height-incr": 1.0}, {"chin-height-decr": 1.0}),
    "chin_forward": ("Jaw", "Chin", "Back", "Forward", {"chin-prominent-incr": 1.0}, {"chin-prominent-decr": 1.0}),
    "jaw_forward": ("Jaw", "Underbite", "Back", "Forward", {"chin-prognathism-incr": 1.0}, {"chin-prognathism-decr": 1.0}),
    # Ears
    "ears_size": ("Ears", "Size", "Small", "Large", {"X-ear-scale-incr": 1.0}, {"X-ear-scale-decr": 1.0}),
    "ears_pointed": ("Ears", "Tips", "Round", "Pointed", {"X-ear-shape-pointed": 1.0}, {"X-ear-shape-round": 1.0}),
    "ears_out": ("Ears", "Set", "Flat", "Out", {"X-ear-flap-incr": 1.0}, {"X-ear-flap-decr": 1.0}),
    "ears_lobes": ("Ears", "Lobes", "Small", "Long", {"X-ear-lobe-incr": 1.0}, {"X-ear-lobe-decr": 1.0}),
    # Neck (her body's, below her head: made on her body too, and its length by her head bone: HerPose)
    "neck_width": ("Neck", "Width", "Slender", "Strong", {"neck-scale-horiz-incr": 1.0, "neck-scale-depth-incr": 0.6},
                   {"neck-scale-horiz-decr": 1.0, "neck-scale-depth-decr": 0.6}),
    "neck_length": ("Neck", "Length", "Short", "Long", {"neck-scale-vert-incr": 1.0}, {"neck-scale-vert-decr": 1.0}),
}

# Each slider's reach either way (its "+" key's targets and its "-" key's
# made at so many times SLIDERS's weights), from the calibration sheets
# (face_lab.py renders of each at ±1 and ±2 over her fitted face, 2026-10-04):
# as far as her face still looked well. Where MakeHuman's target broke
# early the reach is short, and a sculpt of our own is wanted (SCULPT_WANTED).
REACH = {
    "forehead_height": (1.3, 1.3), "forehead_slope": (1.0, 1.5), "forehead_round": (1.5, 0.8), "temples": (1.0, 1.0),
    "brow_ridge": (0.5, 1.5), "face_width": (0.8, 0.8), "face_shape": (1.0, 1.0),
    "eyes_size": (1.5, 1.5), "eyes_spacing": (1.0, 1.0), "eyes_height": (1.0, 1.0), "eyes_tilt": (2.0, 2.0), "eyes_open": (1.5, 1.5),
    "eyes_depth": (2.0, 2.0), "eyes_inner": (1.5, 0.8), "brows_height": (1.5, 1.0), "brows_arch": (1.5, 0.8),
    "nose_width": (1.3, 1.0), "nose_length": (1.2, 0.8), "nose_bridge": (1.0, 1.3), "nose_bridge_width": (1.5, 1.5),
    "nose_tip": (1.2, 0.6), "nose_tip_width": (1.5, 1.5), "nose_projection": (0.7, 1.2), "nostrils": (0.8, 1.5),
    "cheekbone_height": (0.8, 0.8), "cheekbone_width": (0.9, 1.5), "cheekbone_prominence": (0.8, 1.5), "cheeks": (0.8, 1.5),
    "lips_upper": (1.1, 1.5), "lips_lower": (1.2, 1.5), "mouth_width": (1.3, 0.9), "mouth_height": (1.0, 1.0),
    "mouth_corners": (0.7, 0.7), "cupids_bow": (1.5, 1.5), "lips_forward": (0.7, 0.8),
    "jaw_width": (2.0, 2.0), "jaw_angle": (1.0, 1.0), "chin_width": (1.0, 1.5), "chin_length": (1.2, 0.8), "chin_forward": (1.0, 1.0),
    "jaw_forward": (1.0, 0.6),
    # (not yet checked in renders)
    "ears_size": (1.0, 1.0), "ears_pointed": (1.0, 1.0), "ears_out": (1.0, 1.0), "ears_lobes": (1.0, 1.0),
    "neck_width": (1.0, 1.0), "neck_length": (1.0, 1.0),
}
# Where MakeHuman's targets fall short, by the calibration: sculpt these in
# SCULPTS (smooth fields over her points) and use them in the slider instead.
# (Done: the narrow chin, sculpt-chin-narrow: MakeHuman's chin-triangle and chin-width-decr past
# about 1 crease her chin down its middle; the sculpt narrows it as a soft V, smooth at 1.5.)
SCULPT_WANTED = {
    "brow_ridge": "a heavier brow: eyebrows-trans-forward moves her brows off her face; raise the bone over the eyes, "
                  "the brows riding on it",
    "eyes_depth": "deep-set or prominent eyes: eye-push1 barely shows; move each eye and the skin round its socket in "
                  "and out along her face's normal",
    "face_width": "MakeHuman's head-scale-horiz leaves the eyeballs behind: the eyes must follow it (heroine_head.py EYE_FOLLOW)",
}


def slider_keys(name):
    """A slider's "+" and "-" keys' targets with their weights, reach and all."""
    _g, _n, _lo, _hi, plus, minus = SLIDERS[name]
    rp, rm = REACH.get(name, (1.0, 1.0))
    return ({t: w * rp for t, w in plus.items()}, {t: w * rm for t, w in minus.items()})


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


def _smooth(x):
    import numpy as np
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def anatomy(P):
    """Where her face's parts are, from her points (MakeHuman's world: z up,
    her front toward -y): the tip of her nose, the point of her chin (from
    her profile, where it steps back under her chin) and her mouth's height."""
    import numpy as np
    top = P[:, 2].max()
    face = P[(P[:, 2] > top - 0.30) & (P[:, 1] < 0.02)]
    mid = face[np.abs(face[:, 0]) < 0.006]
    nose = mid[np.argmin(mid[:, 1])]
    prof = []
    for z in np.arange(nose[2] - 0.03, nose[2] - 0.15, -0.003):
        m = np.abs(mid[:, 2] - z) < 0.003
        if m.any():
            prof.append((z, mid[m, 1].min()))
    chin = None
    for (z0, y0), (z1, y1) in zip(prof, prof[1:]):
        if y1 - y0 > 0.015:
            chin = np.array([0.0, y0, z0])
            break
    return {"nose": nose, "chin": chin, "mouth_z": nose[2] - 0.35 * (nose[2] - chin[2])}


def _chin_narrow(P, a):
    """Her chin and the front of her jaw drawn in toward her middle: most at
    the point of her chin, easing to nothing at her mouth's corners and back
    toward the angles of her jaw, and under her chin into her throat; a soft
    V, never a crease (everything moves by a smooth field)."""
    import numpy as np
    c = a["chin"]
    up = (P[:, 2] - c[2]) / (a["mouth_z"] - c[2])                  # 0 at her chin's point, 1 at her mouth
    back = (P[:, 1] - c[1]) / 0.075                                  # 0 at her chin's front, 1 by her jaw's angles
    below = (c[2] - P[:, 2]) / 0.03                                  # under her chin
    w = (1 - _smooth(up)) * (1 - _smooth(back)) * (1 - _smooth(below)) * (np.abs(P[:, 0]) < 0.09)
    d = np.zeros_like(P)
    d[:, 0] = -P[:, 0] * 0.22 * w
    return d


SCULPTS["sculpt-chin-narrow"] = _chin_narrow
