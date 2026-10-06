"""His head, made anew: heroine_head.py's way, for the hero. The sculpt's
head (tools/assets/hero_male_body.py) has its eyes and lips moulded shut into
it and painted on, so nothing about it could move. In its place a MakeHuman
man's head (CC0, made by MPFB), bald, with eyes, brows, lashes, teeth and
tongue of its own, shaped as his own (FACE) and placed on his face. His
hair and beards are made on it after (tools/assets/hero_male_hair.py).

    blender -b tools/comfy/out/heroes/hero_male_body.blend --python tools/assets/hero_male_head.py -- \
        tools/comfy/out/heroes/hero_male_built.blend godot/art/people

The scene is what hero_male_body.py saved; the scene saved is the one his
outfits are built on (hero_male_outfits.py).

He is bald and his sculpt's skin is whole, so only his head is new: above
SPLIT (under his jaw in front, under his skull behind) MakeHuman's, held to
its own shape; between SPLIT and CUT (across the middle of his neck) its
neck, fitted to his own skin, so his thick neck is his; below CUT his body
as the sculpt made it. The neck's ring is sewn to his body along CUT, and
his head, a mesh of its own for its shape keys, meets it along SPLIT, where
the two share their points.

With HEAD_CHECK=<folder> in the environment, renders of each step are
written there.
"""
import math
import os
import shutil
import sys

import bmesh
import bpy
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT_BLEND, ART = os.path.abspath(ARGS[0]), os.path.abspath(ARGS[1])
CHECK = os.environ.get("HEAD_CHECK")
TEXDIR = os.path.join(ART, "head_tex")
os.makedirs(TEXDIR, exist_ok=True)

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402

DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")

# MakeHuman's man: thirty or so, hard-muscled, lean in the face; his face
# shaped after (FACE).
MACROS = {"gender": 1.0, "age": 0.56, "muscle": 0.95, "weight": 0.55, "proportions": 1.0, "height": 0.6, "cupsize": 0.5,
          "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
# His parts, MakeHuman's own (all CC0): kind, asset. (His brows are painted
# into his face by hero_male_face.py, and then not written for the game.)
PARTS = [("eyes", "high-poly"), ("eyebrows", "eyebrow001"), ("eyelashes", "eyelashes01"), ("teeth", "teeth_base"),
         ("tongue", "tongue01")]
EYES = "brown"
SKIN = ("skins", "young_caucasian_male")
# (His hair and beards are tools/assets/hero_male_hair.py's, made on this head.)

# His face: a soldier's, handsome and hard used. A square jaw, wide at its
# angles, a strong chin with a faint cleft; high cheekbones over lean cheeks;
# a heavy brow, low over deep-set, narrowed eyes; a straight nose with a
# break in its bridge; a wide mouth, the lower lip the fuller.
FACE = {"head-square": 0.45, "head-scale-vert-decr": 0.25, "forehead-scale-vert-decr": 0.3, "head-fat-decr": 0.4,
        "head-back-scale-depth-incr": 0.15,
        "chin-width-incr": 0.45, "chin-bones-incr": 0.9, "chin-prominent-incr": 0.35, "chin-height-incr": 0.05, "chin-cleft-incr": 0.25,
        "X-cheek-bones-incr": 0.65, "X-cheek-volume-decr": 0.6, "forehead-nubian-incr": 0.3,
        "eyebrows-trans-down": 0.35, "eyebrows-trans-forward": 0.5, "eyebrows-angle-down": 0.15,
        "X-eye-height2-decr": 0.3, "X-eye-push1-in": 0.25, "X-eye-scale-decr": 0.05,
        "nose-hump-incr": 0.2, "nose-width1-incr": 0.25, "nose-point-width-decr": 0.1, "nose-scale-depth-incr": 0.1,
        "mouth-scale-horiz-incr": 0.18, "mouth-lowerlip-volume-incr": 0.3, "mouth-upperlip-volume-incr": 0.05}
# His sliders, for the game to shape his face with: each a shape key one
# way (name+) and the other (name-), from MakeHuman's targets. (The
# heroine's, with a beard's jaw in place of her pointed ears.)
SLIDERS = {
    "eyes_size": ("X-eye-scale-incr", "X-eye-scale-decr"), "eyes_spacing": ("X-eye-trans-out", "X-eye-trans-in"),
    "eyes_height": ("X-eye-trans-up", "X-eye-trans-down"), "eyes_tilt": ("X-eye-corner2-up", "X-eye-corner2-down"),
    "eyes_open": ("X-eye-height2-incr", "X-eye-height2-decr"), "brows_height": ("eyebrows-trans-up", "eyebrows-trans-down"),
    "brows_arch": ("eyebrows-angle-up", "eyebrows-angle-down"), "nose_width": ("nose-scale-horiz-incr", "nose-scale-horiz-decr"),
    "nose_length": ("nose-scale-vert-incr", "nose-scale-vert-decr"), "nose_tip": ("nose-point-up", "nose-point-down"),
    "nose_bridge": ("nose-hump-incr", "nose-hump-decr"), "nostrils": ("nose-flaring-incr", "nose-flaring-decr"),
    "lips_upper": ("mouth-upperlip-volume-incr", "mouth-upperlip-volume-decr"),
    "lips_lower": ("mouth-lowerlip-volume-incr", "mouth-lowerlip-volume-decr"),
    "mouth_width": ("mouth-scale-horiz-incr", "mouth-scale-horiz-decr"), "mouth_corners": ("mouth-angles-up", "mouth-angles-down"),
    "cupids_bow": ("mouth-cupidsbow-incr", "mouth-cupidsbow-decr"), "cheekbones": ("X-cheek-bones-incr", "X-cheek-bones-decr"),
    "cheeks": ("X-cheek-volume-incr", "X-cheek-volume-decr"), "jaw": ("chin-bones-incr", "chin-bones-decr"),
    "chin_width": ("chin-width-incr", "chin-width-decr"), "chin_length": ("chin-height-incr", "chin-height-decr"),
    "chin_forward": ("chin-prominent-incr", "chin-prominent-decr"), "chin_cleft": ("chin-cleft-incr", "chin-cleft-decr"),
    "brow_ridge": ("forehead-nubian-incr", "forehead-nubian-decr"), "ears_size": ("X-ear-scale-incr", "X-ear-scale-decr"),
}
# His expressions (MakeHuman's expression units), for blinking, speaking and
# his scenes: each a shape key from nothing to full. (Hers, and a jaw set
# hard for a fight.)
EXPRESSIONS = {
    "blink_l": ["eye-left-closure"], "blink_r": ["eye-right-closure"], "eyes_wide": ["eye-left-opened-up", "eye-right-opened-up"],
    "squint": ["eye-left-slit", "eye-right-slit"], "brows_up": ["eyebrows-left-up", "eyebrows-right-up"],
    "brows_sad": ["eyebrows-left-inner-up", "eyebrows-right-inner-up"], "brows_angry": ["eyebrows-left-down", "eyebrows-right-down"],
    "smile": ["mouth-corner-puller"], "mouth_open": ["mouth-open"], "pucker": ["mouth-pursing"], "snarl": ["mouth-upward-retraction"],
    "frown": ["mouth-depression"], "nose_wrinkle": ["nose-compression"],
}

# His SPLIT and CUT, from his own profile (hero_male_body.py: 1.98 m): the
# corner under his jaw at 1.70 m, the hollow of his nape at 1.76 m. Both
# lean as his neck does (rising behind, 0.54 m a metre).
SPLIT_Z, CUT_Z, LEAN = 1.696, 1.662, 0.54


def cut_z(P):
    """Height of CUT under a point: across the middle of his neck, a few
    centimetres under SPLIT and parallel to it."""
    return CUT_Z + LEAN * P[:, 1]


def g_cut(P):
    return P[:, 2] - cut_z(P)


def s_split(P):
    """Above SPLIT is his head: under his jaw in front, under his skull behind."""
    return P[:, 2] - (SPLIT_Z + LEAN * P[:, 1])
