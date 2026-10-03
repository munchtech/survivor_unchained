"""Skill, blessing, art and evolution icons (icons/glyph_color/KEY.png): painted
on the local Krea in one hand (the darkbrush LoRA), one light (upper left),
one framing (the emblem filling the middle, its glow falling off to black),
each in its school's colour. Then cut (BiRefNet for the thing, its light for
the glow), centred, graded, and checked at the sizes the game shows them
(17, 28, 67 and 68 px).

The world shows in what they are made of: steel is hand-forged and notched,
fire is the Morrow's ember (molten, cracked, rising from below), frost is the
Low Ford's rime, shadow is the barrow's, holy is the Order's dawn-gold, the
wood's things are the Verge's (bramble, antler, moss).
"""
from __future__ import annotations

import os

from PIL import Image

import krea

LOOK = ("A single bold painted emblem for a dark fantasy game skill icon, in the style of Diablo IV skill icons, hand painted, "
        "one strong clear silhouette filling the middle of the frame, dramatic light from the upper left, glowing, its glow "
        "fading to pure black at the edges, nothing touching the edges, on a pure black background, no frame, no border, no "
        "text, no letters: ")

SCHOOL = {
    "physical": "cold white steel and bone colours",
    "fire": "molten orange and gold ember colours",
    "frost": "pale icy blue colours",
    "storm": "pale electric blue-white colours",
    "nature": "vivid green colours",
    "arcane": "violet and magenta colours",
    "holy": "warm dawn gold colours",
    "shadow": "deep violet and black colours",
    "blood": "deep crimson colours",
}

# key: (school, subject)
SUBJECTS = {
    # The callings' first skills and what they become.
    "slash_steel": ("physical", "a hand-forged notched sword sweeping through a wide bright arc of steel light"),
    "slash_holy": ("holy", "a sword throwing a glowing golden crescent of holy light"),
    "slash_blood": ("blood", "a notched blade dripping blood, a red arc of cut"),
    "slash_heavy": ("physical", "a heavy butcher's cleaver chopping in a wide arc, sparks"),
    "slash_spin": ("physical", "a cleaver whirling in a full circle, a ring of steel blur"),
    "slash_quake": ("physical", "a cleaver striking the ground, a shockwave of cracked stone bursting ahead"),
    "mote": ("arcane", "three small glowing violet motes of light curving in seeking trails"),
    "mote_cascade": ("arcane", "a cascade of many tiny violet motes splitting and multiplying"),
    "mote_star": ("arcane", "a bright violet star-mote hunting with a long curved trail"),
    "cinder": ("fire", "a heavy molten ember coal with glowing cracks falling, trailing fire"),
    "star": ("fire", "a falling star of fire plunging down, a burning tail"),
    "living_flame": ("fire", "three small living flames like seeking spirits"),
    "shard": ("frost", "a jagged shard of pale river rime ice, frost crystals"),
    "shard_deep": ("frost", "a ring of ice shards bursting outward from a frozen centre"),
    "spear_ice": ("frost", "a long enormous lance of ice"),
    "arc": ("storm", "a web of lightning leaping between three points"),
    "arc_sky": ("storm", "a bolt of lightning striking straight down from a dark cloud"),
    "arc_fork": ("storm", "a forked lightning bolt splitting into many branches"),
    "nova_holy": ("holy", "a ring of golden holy light bursting outward like a dawn"),
    "nova_dawn": ("holy", "a rising sun inside a ring of light, warm and mending"),
    "nova_sun": ("holy", "a ring of daylight burning on dark ground"),
    "zone_holy": ("holy", "a hallowed circle of golden light on the ground, runes of light"),
    "zone_sanct": ("holy", "a glowing golden shield standing on a circle of sacred ground"),
    "zone_pyre": ("fire", "a circle of holy fire burning on the ground, flames gold and orange"),
    "umbral": ("shadow", "a bolt of violet-black shadow tearing forward"),
    "ruin": ("shadow", "a jagged black bolt splitting everything, a torn wound of darkness behind it"),
    "siphon": ("shadow", "a dark violet bolt drawing a thread of red life back from a wound"),
    "dagger": ("physical", "a ring of thrown knives whirling outward"),
    "dagger_flurry": ("physical", "a storm of many knives in a whirl"),
    "dagger_blood": ("blood", "many small knives each leaving a red cut"),
    "axe": ("physical", "two hand axes circling each other"),
    "axe_storm": ("physical", "a whirling storm of axes"),
    "axe_blood": ("blood", "a spinning axe wheel trailing blood"),
    "arrow": ("physical", "a spread of three hunting arrows in flight"),
    "arrow_rain": ("physical", "a rain of arrows falling from above"),
    "arrow_mark": ("blood", "an arrow striking a red hunter's mark"),
    "moon": ("arcane", "a crescent moon of pale violet flame"),
    "moonfall": ("arcane", "moons falling from the sky trailing violet fire"),
    "moon_brand": ("arcane", "a crescent moon brand burning a glowing mark"),
    "disc": ("holy", "a round shield hurled spinning, golden light trailing"),
    "disc_reckon": ("holy", "a heavy shield ricocheting between three points of light"),
    "disc_aegis": ("holy", "a spinning shield circling to guard, a golden ward"),
    "zone_blight": ("shadow", "rotting black-green blight spreading across the ground, sickly fumes"),
    "zone_blight2": ("shadow", "a wide pool of creeping blight with grasping tendrils"),
    "zone_plague": ("nature", "a bursting plague bloom of sickly green spores"),
    "nova_blood": ("blood", "a sweeping curved graveblade carving a red arc"),
    "nova_rend": ("blood", "a curved blade drinking a red thread of blood"),
    "nova_harrow": ("shadow", "a skeletal hand rising from the earth in violet light"),
    "tether": ("shadow", "a coil of dark violet magic binding a heart"),
    "tether2": ("shadow", "two coils of dark magic, one taking, one giving back"),
    "tether_mark": ("shadow", "a coil of dark magic with a grave mark on it"),
    "palm": ("physical", "an open palm striking with a burst of force"),
    "palm_temple": ("holy", "an open palm striking a great temple bell, rings of sound"),
    "palm_storm": ("storm", "an open palm crackling with lightning"),
    "herd": ("nature", "spectral green spirit stags stampeding forward"),
    "herd_great": ("nature", "a great herd of green spirit beasts, antlers and horns"),
    "herd_hunt": ("nature", "a spirit stag running wreathed in green fire"),
    "zone_thorn": ("nature", "brambles bursting up from the ground, sharp thorns"),
    "zone_bloom": ("nature", "bramble flowers with thorns blooming"),
    "zone_root": ("nature", "gnarled roots gripping and holding"),
    "chakram": ("physical", "a bladed throwing ring spinning on the wind"),
    "chakram_razor": ("physical", "a razor-edged ring splitting the wind in two"),
    "chakram_hail": ("frost", "a spinning bladed ring through a storm of hail"),
    "beam_green": ("nature", "a straight lance of green fire"),
    "beam_gaze": ("nature", "a wide burning eye of green fire"),
    "beam_sun": ("holy", "a lance of golden holy light"),
    # The arts in hand.
    "shield": ("physical", "a battered round iron shield driven forward"),
    "aegis": ("holy", "a kite shield with a ward of golden light round it"),
    "howl": ("blood", "a snarling wolf's head howling, red breath"),
    "hourglass": ("arcane", "an hourglass with sand frozen in mid fall, violet light"),
    "mark": ("blood", "a red hunter's target mark, a crosshair of claws"),
    "smoke": ("shadow", "a burst of grey smoke with a figure vanishing"),
    "leap": ("physical", "a figure leaping high and crashing down, dust ring"),
    "blink": ("frost", "a figure stepping through a flash of blue frost"),
    "boot": ("physical", "a winged running boot, motion streaks"),
    "mirror": ("arcane", "two mirror reflections of a figure in violet light"),
    "horns": ("physical", "charging bull's horns behind a barrier of light"),
    "wraith": ("shadow", "a ghostly half-transparent hooded wraith"),
    "embers": ("fire", "a trail of burning embers on the ground"),
    "chain": ("physical", "a hooked iron chain flung out, the hook biting"),
    "echo": ("arcane", "a figure and its fading violet echo"),
    "wing": ("physical", "a single feathered wing, swift"),
    # Blessings and passives.
    "fist": ("physical", "a clenched iron gauntlet fist"),
    "magnet": ("fire", "a lodestone drawing embers and coins toward it"),
    "heart": ("blood", "a red anatomical heart, beating, glowing"),
    "crosshair": ("physical", "a hunter's sighting mark, a ring with four points"),
    "claw": ("blood", "three wolf claw marks slashed in red"),
    "expand": ("arcane", "rings of force expanding outward"),
    "triple": ("physical", "three projectiles flying side by side"),
    "coin": ("holy", "a square gold coin with a quatrefoil hole"),
    "book": ("arcane", "an old leather tome with a glowing ember on its cover"),
    "leaf": ("nature", "a green leaf with a drop of dew, healing"),
    "spear": ("physical", "a thrown spear flying fast, wind lines"),
    "perennial": ("nature", "an evergreen sprig and an hourglass of green"),
    "feint": ("physical", "a figure sidestepping a blade, a blur"),
    "thorn": ("nature", "a thorned bramble stem, sharp thorns"),
    "bleed": ("blood", "a serrated blade with drops of blood"),
    "frostaura": ("frost", "a ring of frost mist round a figure, cold"),
    "retaura": ("holy", "a searing ring of holy light round a figure"),
    "spiritwolf": ("frost", "a spirit wolf of pale blue light running"),
    "risen": ("shadow", "a ghoul's skeletal hand clawing up from a grave"),
    "command": ("shadow", "a raised dark sceptre commanding shadow servants"),
    "skull": ("physical", "a cracked human skull, grim"),
    "kindling": ("fire", "a burning branch passing its fire to two others"),
    "pyre": ("fire", "a burning figure bursting in flame"),
    "shatter": ("frost", "a frozen shape shattering into ice shards"),
    "static": ("storm", "a crackling spark leaping between two points"),
    "execute": ("blood", "a butcher's cleaver falling, a red line"),
    "scent": ("blood", "a wolf's nose and a red trail of blood scent"),
    "plague": ("nature", "a sickly green plague skull with spores"),
    "sanctify": ("holy", "a golden flame of holy fire in an open hand"),
    "consecrate": ("holy", "a glowing golden sigil on the ground where something fell"),
    "drain": ("blood", "a red stream of life flowing into an open hand"),
    "arcane": ("arcane", "a burst of violet arcane light, a many-pointed star"),
    "flame": ("fire", "a single tall flame of molten ember"),
    "hand": ("fire", "a restless open hand with ember light at the fingertips"),
    "bolt": ("storm", "a single jagged lightning bolt"),
}


def fit(src, dst, size=256, fill=1.04, lo=0.035, hi=0.20, mask=None):
    """A painted emblem on black made into an icon: alpha from its light (so its glow
    falls off softly over any backing), the solid parts from the mask when given, its
    colour un-premultiplied, cropped to what is there and centred at `fill` of the square."""
    import numpy as np
    import cv2
    import forge as F
    rgb = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255
    v = rgb.max(axis=2)
    # The painting's own black is never quite black (a haze): read it from the border
    # and start the alpha above it, so no faint square is left round the icon.
    b = max(8, v.shape[0] // 16)
    border = np.concatenate([v[:b].ravel(), v[-b:].ravel(), v[:, :b].ravel(), v[:, -b:].ravel()])
    lo = max(lo, float(np.percentile(border, 95)) + 0.02)
    hi = max(hi, lo + 0.12)
    t = np.clip((v - lo) / (hi - lo), 0, 1)
    a = t * t * (3 - 2 * t)
    if mask is not None:
        a = np.maximum(a, mask)
    else:
        # A dark thing inside its own glow (a shield against light) is solid, not a hole:
        # whatever the glow encloses, away from the edges, is filled.
        lowm = (a < 0.35).astype(np.uint8)
        n, lab = cv2.connectedComponents(lowm, connectivity=4)
        border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        enclosed = (lowm > 0) & ~np.isin(lab, border)
        a = np.where(enclosed, np.maximum(a, 0.97), a)
    # Nothing at the very edges (a painting's vignette or smoke must not frame the icon).
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    e = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (0.04 * w)
    a = a * np.clip(e, 0, 1)
    col = np.clip(rgb / np.maximum(a[..., None], 0.08), 0, 1)
    col = col * a[..., None] + rgb * (1 - a[..., None])
    ys, xs = np.nonzero(a > 0.7)
    if len(xs) == 0:
        raise ValueError("empty icon: " + src)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    side = int(max(x1 - x0, y1 - y0) / fill)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    img = np.dstack([col, a]).astype(np.float32)
    M = np.float32([[1, 0, side / 2 - cx], [0, 1, side / 2 - cy]])
    sq = cv2.warpAffine(img, M, (side, side), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out = F.downsample(sq, (size, size)) if side > size else cv2.resize(sq, (size, size), interpolation=cv2.INTER_CUBIC)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    save_small(F.to_pil(out), dst)
    return out


def save_small(img, dst):
    """A PNG of 256 colours with alpha (dithered): a sixth of the size, no visible loss on
    painted icons, and still a plain PNG the game loads by name."""
    q = img.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
    q.save(dst, optimize=True)


# Second takes, where the first read as a letter or a number, or put a figure where the
# thing itself should be (seed 950).
REDO = {
    "slash_steel": ("physical", "a single hand-forged notched longsword, blade up, inside a wide bright crescent arc of "
                                "steel light, no figure"),
    "disc": ("holy", "a round iron-rimmed shield spinning through the air, a golden trail of light behind it, no figure"),
    "mote": ("arcane", "three small round glowing violet orbs of light, each trailing a curved streak, no figure"),
    "mote_cascade": ("arcane", "a burst of many tiny glowing violet orbs of light splitting apart like sparks, no figure"),
    "tether_mark": ("shadow", "a coil of dark violet smoke wrapped round a cracked gravestone, no figure"),
    "beam_gaze": ("nature", "a single wide open eye of green fire, a beam of green flame pouring from it"),
    "consecrate": ("holy", "a glowing golden ring of light burned into dark stone ground, rays rising, no figure"),
    "bolt": ("storm", "a forked lightning bolt striking down out of a dark storm cloud"),
    "magnet": ("fire", "a black iron horseshoe lodestone drawing glowing embers and small gold coins toward it, no figure"),
}
# Third takes (seed 960): abstract, where the model kept painting a person.
REDO2 = {
    "mote": ("arcane", "an abstract magic sigil: three glowing violet spheres of light circling one another on curved "
                       "trails of light, empty black space round them"),
    "mote_cascade": ("arcane", "an abstract magic sigil: a fountain of dozens of tiny glowing violet sparks bursting "
                               "outward and splitting, empty black space round them"),
}


def prompt(key, redo=False):
    table = {False: SUBJECTS, True: REDO, 2: REDO2}[redo]
    school, subject = table[key]
    return LOOK + subject + ", " + SCHOOL[school] + "."


def generate(keys, seed=900, n=2, per=8, tag="icons"):
    """Keys in graphs of `per` prompts (one model load each)."""
    made = {}
    keys = list(keys)
    for i in range(0, len(keys), per):
        chunk = keys[i:i + per]
        jobs = [(k, prompt(k), seed) for k in chunk]
        res = krea.t2i_many(jobs, tag=tag, n=n)
        made.update(res)
        print(" ".join(chunk), flush=True)
    return made


def redo(keys=None, seed=950, n=3):
    keys = list(keys or REDO)
    jobs = [(k, prompt(k, redo=True), seed) for k in keys]
    return krea.t2i_many(jobs, tag="icons", n=n)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args and args[0] == "--redo2":
        krea.t2i_many([(k, prompt(k, redo=2), 960) for k in REDO2], tag="icons", n=3)
    elif args and args[0] == "--redo":
        redo(args[1:] or None)
    else:
        generate(args or list(SUBJECTS))
