"""Style exploration batches on the local Krea (raw results to tools/comfy/out/uiforge/<tag>/).

    python tools/uiforge/explore.py NAME [NAME ...]
"""
import os
import sys

import krea

DARK = "isolated on a pure black background, seen straight on, orthographic"
ICON = ("A single bold dark fantasy game skill icon, hand-painted with painterly brushwork, "
        "strong clean silhouette filling the frame, dramatic rim light from the upper left, glowing, "
        "on a pure black background, no frame, no border, no text: ")

GUIDES = os.path.join(krea.OUT)


def card_v2():
    p = ("An empty tall portrait card frame for a dark fantasy game: a narrow border of hand-forged blackened iron strap "
         "with hammer marks and a twisted gold wire inlaid along it, at the two top corners large forged lamp-iron brackets "
         "with curled scroll ends and a square iron coin with a quatrefoil hole glowing faintly with ember, at the two bottom "
         "corners only small square iron coins nailed on, between the top brackets a short iron chain whose middle link is "
         "pried open with molten orange ember light at the break, the inside of the card plain flat dark iron, calm and even, "
         + DARK + ". " + krea.STYLE)
    for d, sd in ((0.5, 201), (0.6, 202)):
        print(krea.i2i(os.path.join(GUIDES, "card_guide2.png"), p, denoise=d, seed=sd, n=2, tag=f"card_v2_{int(d*100)}"), flush=True)


def many1():
    jobs = [
        ("logo_a", "A dark fantasy video game title logo reading \"SURVIVOR UNCHAINED\" on two lines, the letters hand-forged "
                   "from blackened iron with bevelled edges catching warm light and a thin gold edge, a heavy iron chain running "
                   "through the letters, one link of the chain pried open between the two words with molten orange ember light "
                   "glowing at the break, a few embers drifting, on a pure black background", 301),
        ("logo_b", "A dark fantasy video game title logo reading \"SURVIVOR UNCHAINED\", tall carved Roman capitals of old gold "
                   "and blackened iron, the O of SURVIVOR is a broken chain link with ember light pouring from the break, "
                   "molten cracks of ember in the letters, on a pure black background", 302),
        ("ic_oathblade", ICON + "a sword swinging in a wide glowing arc of steel light, a hand-forged blade, sparks", 311),
        ("ic_cinder", ICON + "a heavy burning cinder falling, molten ember rock trailing fire and smoke", 312),
        ("ic_rimeshard", ICON + "a jagged shard of pale blue ice like river rime, cold mist, frost crystals", 313),
        ("ic_dawnpulse", ICON + "a ring of golden holy light bursting outward like a dawn, rays, warm gold", 314),
        ("ic_umbral", ICON + "a bolt of violet-black shadow tearing forward, wisps of darkness", 315),
        ("ic_herd", ICON + "spectral green spirit stags stampeding forward, ghostly antlers, green light", 316),
        ("medal_heart", "A round medallion of hand-forged blackened iron with a twisted gold wire round its rim, at its centre a "
                        "dark red anatomical human heart in relief bound by a small iron chain, faint ember glow, symmetrical, "
                        + DARK + ". " + krea.STYLE, 321),
        ("ring_art", "A ring made of seven forged blackened iron chain links joined in a circle, thick round links, the topmost link "
                     "pried open with molten orange ember light glowing at the break, the middle of the ring completely empty and "
                     "black, front view, " + DARK + ". " + krea.STYLE, 322),
    ]
    print(krea.t2i_many(jobs, tag="many1"), flush=True)


def corners2():
    jobs = [
        ("ford_corner", "Top-left corner piece of a blackened iron frame from a cold river ford at night: sharp pale blue rime "
                        "frost crystals growing over the iron, droplets of icy water, cold blue light, " + DARK + ". " + krea.STYLE, 71),
        ("binder_corner", "Top-left corner piece of a blackened iron frame inlaid with square-cut violet amethyst and angular "
                          "square-cut silver sigil lines with right-angled hooks like an old legion key pattern, a small square coin, "
                          "mysterious, " + DARK + ". " + krea.STYLE, 81),
        ("dawn_corner", "Top-left corner piece of a frame of burnished gold and amber over blackened iron, wrought like the flames "
                        "of a chapel lamp, rays of a rising sun, warm golden glow, holy and old, " + DARK + ". " + krea.STYLE, 91),
    ]
    print(krea.t2i_many(jobs, tag="corners2"), flush=True)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        globals()[name]()
