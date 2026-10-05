"""Item icons (icons/item/KEY.png): the game's own photographs of its item
models (ItemPhotos, run the game with --icons), painted over on the local
Krea so each keeps the real thing's shape and colours and gains the hand of
the rest of the interface; then cut, centred to fill about four fifths of the
square, lit from the upper left, graded.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

import krea

PHOTOS = os.path.join(os.environ.get("APPDATA", ""), "Godot", "app_userdata", "Survivor Unchained", "icons")
GUIDES = os.path.join(krea.OUT, "item_guides")

LOOK = ("A single dark fantasy game item icon, hand-painted with painterly brushwork, the object alone, "
        "three-quarter view, soft warm light from the upper left, a crisp clear silhouette, on a pure black background, "
        "no frame, no text: ")

ITEMS = {
    "antidote": "a small stoppered glass bottle of cloudy green antidote, a wax-sealed cork",
    "armor": "a shirt of riveted iron chain mail",
    "armor_heavy": "a heavy blackened plate cuirass with gold rivets and pauldrons",
    "armor_light": "a quilted padded linen jerkin, laced",
    "axe": "a pair of crossed hand axes with leather-wrapped hafts",
    "bandage": "a roll of clean linen bandages",
    "bomb": "a small keg of blasting ember with a lit fuse, bound in iron",
    "bone": "a knucklebone charm hung on a fine gold chain",
    "book": "an old leather-bound manual with brass corners",
    "bow": "a hunter's crossbow of dark wood and iron",
    "censer": "a gilded censer on chains, smoke curling from it",
    "chest": "an iron-bound wooden strongbox with a brass lock",
    "circlet": "a thin circlet of moonsilver set with a pale pearl",
    "cleaver": "a heavy butcher's cleaver with a worn wooden handle",
    "cloak": "a long dark traveller's cloak with a hood and a clasp",
    "dagger": "a pair of crossed throwing knives",
    "dust": "a small sack of grey barrow dust spilling at the top",
    "ember": "a glowing orange ember shard crystal on a lump of black rock",
    "fang": "a wolf's fang hung on a gold chain",
    "flower": "a pale moonpetal flower with a long green stem",
    "helm": "an iron nasal helm, dented",
    "helm_light": "a round leather cap",
    "hide": "a rough boar hide",
    "journal": "a red leather-bound journal with a gold sigil on its cover",
    "kerchief": "a red cloth kerchief tied in a knot",
    "key": "an old iron key with a ring bow",
    "lamp": "a miner's brass lamp with a candle inside",
    "lantern": "a forged iron lamp-iron lantern with a candle burning inside",
    "lens": "a cracked magnifying lens in a gold rim",
    "map": "a torn parchment map with a red ink route",
    "mask": "a leather plague mask with a long beak and brass goggles",
    "moon": "a charm of a pale silver crescent moon on a gold chain",
    "pelt": "a grey wolf pelt",
    "picks": "a ring of iron lockpicks",
    "potion": "a round flask of glowing red health draught with a cork",
    "ring": "a gold ring set with a red stone",
    "root": "a twisted pale bitterroot with a green sprout",
    "scroll": "a rolled parchment scroll with a red wax seal",
    "seed": "a leather pouch of thornseeds with green shoots",
    "shield": "a round wooden shield with an iron boss and rim",
    "sigil": "a shard of black stone cut with a glowing violet sigil",
    "staff": "a twisted wooden staff with a glowing violet crystal at its head",
    "sword": "a long straight sword with a crossguard",
    "totem": "a carved wooden storm totem bound with iron and blue cloth",
    "vial": "a stoppered glass vial of murky green stream water",
    "vial_orange": "a stoppered glass vial of glowing orange ember slurry",
    "wand": "a short wooden wand with a pale crystal tip",
    "wand_dark": "a dark wand of twisted black wood wrapped in violet light",
}


def guide(key, size=1024):
    os.makedirs(GUIDES, exist_ok=True)
    dst = os.path.join(GUIDES, key + ".png")
    if os.path.exists(dst):
        return dst
    im = Image.open(os.path.join(PHOTOS, key + ".v1.png")).convert("RGBA")
    # The object at about four fifths of the square, on black.
    bb = im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    obj = im.crop(bb)
    k = size * 0.78 / max(obj.size)
    obj = obj.resize((max(1, int(obj.width * k)), max(1, int(obj.height * k))), Image.LANCZOS)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    bg.alpha_composite(obj, ((size - obj.width) // 2, (size - obj.height) // 2))
    bg.convert("RGB").save(dst)
    return dst


def generate(keys=None, denoise=0.5, seed=1000, n=2):
    for k in keys or list(ITEMS):
        krea.i2i(guide(k), LOOK + ITEMS[k] + ".", denoise=denoise, seed=seed, n=n, tag="items", out=os.path.join(krea.OUT, "items", k))
        print("item", k, flush=True)


# Second takes painted from words alone (seed 1100), where the game's photograph was a poor
# start: the pelts read as the same flat skin, the root as a little man, the seeds as an onion.
T2I = {
    # Seed 1110: the wolf's head painted a living wolf (a summon, not a skin); now headless.
    "pelt": "a thick tanned grey wolf fur pelt folded in a heap and tied with a leather thong, long shaggy grey and "
            "silver fur, the pale tanned leather of its underside showing at the folded edge, a bushy tail hanging "
            "down, no head, no face, no eyes",
    "hide": "a rolled boar hide, tied with twine, coarse dark brown bristles standing up along its back, the pale raw "
            "underside showing at the roll's end",
    "root": "a gnarled forked bitterroot, pale and knotted with fine hair roots, dark wet soil clinging to it, a single "
            "small green sprout at its crown",
    "seed": "a small leather drawstring pouch spilling hard black thornseeds, each seed spiked with tiny thorns, one "
            "seed split with a green bramble shoot curling out",
    "dust": "a small stoppered clay jar tipped over, fine grey-white barrow dust spilling out of it with tiny bone "
            "fragments and a cracked finger bone in the heap",
    "bomb": "a small iron-bound wooden crate charge, orange ember light glowing through the gaps between its slats, a "
            "short lit fuse sparking on top",
    # The crafting lead's Marks (design 20.3): what each people's map ruler leaves, carrying how it fought.
    # The story lead's Tally-Bone, Bent Barrow-Nail and Muster-Cord (seed 1110: the first takes missed the notches,
    # the bend and the knots).
    "hunt_bone": "a straight pale bone tally stick lying diagonally, its whole length cut with dozens of deep dark "
                 "parallel notches in a neat row like a ladder, tooth-gnawed ends, a few grey wolf hairs",
    "lamp_glass": "a cracked curved shard of thick amber lamp glass with a blackened brass rim, a tiny ember-orange "
                  "flame still burning inside the crack, soot streaks",
    "gate_nail": "a long square iron door nail bent double into a tight U shape, its square head and point side by "
                 "side, flecked with grave soil and rust, a faint pale light along the bend",
    "red_cord": "a length of faded red cord lying in a loose S curve with a long row of small tight knots tied along "
                "it at even intervals, frayed ends, nothing else",
    # The crafting lead's (design 20.5): what a deep scar leaves past the hour once the stream is clean.
    # Its lore (the story lead's): "the blue of the ford lamps, and it is never quite cold".
    "scar_glass": "a jagged shard of dark smoky glass, nearly black, a cold pale blue glow like a lamp flame trapped "
                  "deep inside it, a thin crust of scorched earth and ash on one edge",
    # The crafting lead's (design 9): Snib's jar of the Dig's slurry. No photograph (it has no model).
    "slurry_jar": "a squat grimy grey stoneware crock, its lid lashed down with twine, a crude X scratched deep into its "
                  "belly, sickly bright green light leaking out through the scratch and a crack under the lid, thick "
                  "green-black sludge oozing from under the lid and dripping down one side",
}

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "godot", "art", "ui", "icons", "item")

# Which candidate each item uses: KEY -> place in the batch of seed 1000, or (seed, place).
PICKS: dict = {
    # Painted from words (T2I), where the photograph was a poor start.
    "hide": (1100, 1), "root": (1100, 2), "seed": (1100, 3), "dust": (1100, 0), "bomb": (1100, 1), "pelt": (1110, 2),
    # The crafting lead's: Snib's jar, and the four rulers' things that carry a Mark.
    "slurry_jar": (1100, 0), "lamp_glass": (1100, 1), "hunt_bone": (1120, 2), "gate_nail": (1110, 0), "red_cord": (1110, 1),
}


def t2i(keys=None, seed=1100, n=4):
    keys = list(keys or T2I)
    jobs = [(k, LOOK + T2I[k] + ".", seed) for k in keys]
    return krea.t2i_many(jobs, tag="items_t2i", n=n)


def fit(key, j=None, size=256, fill=0.84):
    """A painted item cut out (BiRefNet for the thing, its light for any glow), centred at
    `fill` of the square, the house grade, saved small."""
    import cv2
    import cut as C
    import forge as F
    import icons
    j = PICKS.get(key, 0) if j is None else j
    seed, j = j if isinstance(j, tuple) else (1000, j)
    src = os.path.join(krea.OUT, "items", key, f"items_1000_{j}.png") if seed == 1000 else \
        os.path.join(krea.OUT, "items_t2i", f"{key}_{seed}_{j}.png")
    rgba = C.cutout(src, mode="mask+glow")
    # Keep only the solid thing and light near it: the mask's own region, a little grown.
    a = rgba[..., 3]
    x0, y0, x1, y1 = C.bbox(rgba, thr=0.35, pad=6)
    crop = C.grade(rgba[y0:y1, x0:x1], sat=0.95, shadows=1.18)
    h, w = crop.shape[:2]
    side = int(max(w, h) / fill)
    M = np.float32([[1, 0, (side - w) / 2], [0, 1, (side - h) / 2]])
    sq = cv2.warpAffine(crop, M, (side, side), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out = F.downsample(sq, (size, size)) if side > size else cv2.resize(sq, (size, size), interpolation=cv2.INTER_CUBIC)
    os.makedirs(OUT, exist_ok=True)
    icons.save_small(F.to_pil(out), os.path.join(OUT, key + ".png"))


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--fit"]:
        for k in sys.argv[2:] or list(ITEMS):
            fit(k)
            print("fit", k, flush=True)
    else:
        generate(sys.argv[1:] or None)
