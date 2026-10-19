"""Round 15 (style_r15*.json): the hand made when the picture is made, from one source
(judge r2: the shared repaint kept each source's edges, and the edges carried four hands).

The method, the master in context: one canvas holds the master plate (r14's P4,
the only plate that read as paint) and the target plate, and the target is painted
from nothing (denoise 1.0) beside it. The mask is held on the latent as well as given
to the ControlNet's inpaint (gen.py "hold"), so at every step the model attends to the
exact master while it paints the target. The target's layout comes from depth only
(depth_r15.py: our block-out for P1, MoGe of our block-ins for P7/P9, of r14's P4 for
P4, edited for judge r2's content), never from a picture's edges. The words name both
as plates from one book by one painter. P4 is remade the same way, beside the master.

  V    the master's 2.39 band (1792x752) above a 16 px black gutter and the 1792x1024
       target: a 1792x1792 canvas; the target cropped out after
  H    the whole master, the gutter and the target side by side: 3600x1024
  alt  (judge r2's fallback) img2img over the r14 plate at a high denoise, the same
       hand and content words, the same depth control, no master in context

    python tools/storybook/depth.py <r14 plates and r13 block-ins> --out tools/storybook/out/style_r15/depth
    python tools/storybook/depth_r15.py
    python tools/storybook/mkjobs_style_r15.py [test|final] [--seed N --strength S --end E --canvas V]
    python tools/storybook/gen.py tools/storybook/jobs/style_r15_<test|final>.json --out tools/storybook/out/style_r15/gen
    python tools/storybook/unify.py finish <the four> --out tools/storybook/out/style_r15/fin
"""
import argparse
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "style_r15")
REL = "tools/storybook/out/style_r15/"
MASTER = os.path.join(HERE, "out", "style_r14", "fin", "p4_d60_s11.png")
MASTER_DEPTH = os.path.join(OUT, "depth", "r14p4_depth.png")
R14 = {k: f"tools/storybook/out/style_r14/fin/{k}_d60_s11.png" for k in ("p1", "p4", "p7", "p9")}
W, H = 1792, 1024
BAND = (136, 888)   # the 2.39 window's rows of a plate
GAP = 16

HAND = ("a restrained dark oil painting over a bold brush-ink drawing: thin dark transparent glazes in the shadows, thick "
        "opaque paint only where the light falls, heavy dark ink contours on the figures only, while the land, rock, snow "
        "and sky are painted in broad soft-edged masses without outlines; faces cut into a few flat planes; quiet clean "
        "shadows; a night palette of deep indigo, slate and umber with the story's lights; grim and serious, realistic "
        "proportions. ")
SHEET = {"V": "one above the other", "H": "side by side"}
FIRST = {"V": "The top plate", "H": "The left plate"}
SECOND = {"V": "The bottom plate", "H": "The right plate"}
MASTER_WORDS = ("night on a frosted field: a dead villager standing slack, lit gold from inside, and an old watchman in a "
                "slate-blue hooded cloak with a round wooden shield driving a spear into his chest. ")
FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "

CONTENT = {
    "p1": ("Night, two thousand years ago. We stand on the near rim of a great raw cut dug deep into a hillside and look "
           "across it and down into it. At the left, close to us on our rim, two soldiers of an ancient legion stand with "
           "their backs to us as dark silhouettes: dull dark rust-red wool cloaks, plain dull matte bronze helmets with "
           "crests and cheek guards; the nearer holds a small torch low in front of him, half hidden by his body. Across the "
           "cut, the far wall drops away into darkness as four great flat planes of bare slate rock, each one a single broad "
           "shape of cold dark slate with one clean edge. Down that wall a dense column of marching soldiers winds in an S "
           "from just below the far rim to the bottom of the picture, packed close together, their torches held up in their "
           "hands, so the column reads as a winding stream of small flames above dark heads going down into the depth of "
           "the cut. Above the far rim the dark empty hillside rises to a crest under a strip of deep indigo night sky. The "
           "right side of the picture sinks into deep shadow. The torchlight's orange is the only strong color; everything "
           "else is night."),
    "p4": ("Night under a dark slate-blue sky, hard frost on a field beside a pale dirt road, a few ember-gold glints in the "
           "frozen soil, a dark body lying in the frost behind. A dead villager stands upright and slack, arms hanging, head "
           "tilted, in a torn linen shirt: gray waxy skin, sunken cheeks, matted hair; his eye sockets are empty holes lit "
           "gold from inside, and gold light glows in his open mouth; his skin is lit from within like paper over a lamp. "
           "To the right an old watchman with a gray beard, a slate blue-gray hooded cloak over a shirt of mail, a round "
           "wooden shield with a dark matte iron boss on his arm, is braced with his weight forward, both hands on a single "
           "plain dark wooden spear driven into the dead man's chest; the spearhead is buried out of sight inside him, and "
           "golden light bursts out around the shaft where it enters and falls as small glowing gold stones that pile up in "
           "a little heap on the frost at the dead man's feet. A short faint puff of white breath at the watchman's lips. "
           "The golden light is the only strong color; the rest is cold night, frost and slate."),
    "p7": ("The Low Ford at night in winter: a shallow river crossing between dark snowy banks under bare trees, pale thin "
           "ice along both edges of the water, a trodden track in the snow running down to the water's edge, and a line of "
           "large flat dark stepping stones crossing the shallows. Three new square cages of crude hand-forged black iron "
           "bars stand on plain square black iron posts, each cage holding a cold pale blue flame that pools blue light on "
           "the snow at its foot; those blue pools are the only bright snow, and the far bank, the right bank and the edges "
           "of the picture lie deep in shadow. In the middle of the river, just above the water over the stones, a fourth "
           "blue light floats with nothing holding it, in a wide soft cold glare that fades gently into the dark, its light "
           "lying on the water. Nobody is there. The cold blue is the only strong color; the rest is deep night."),
    "p9": ("Dusk, a deep blue sky over a thin dull rose band above the far hills. A small camp beside a rutted dirt track: "
           "a campfire burning high; beside it a bedroll with a wool blanket folded on top, lit by the fire; a plain leather "
           "pack. A lone traveler sits on a log by the fire with their back to us, wrapped from the hood to the ground in one "
           "plain dark wool cloak that falls over the log in a single smooth cone; only the hands show, holding a folded "
           "letter to the firelight; a small leather flask hangs on a cord from one wrist. Far up the track on a low rise "
           "stands the waystation: a long low hall of stone and dark timber with a steep roof and warm orange windows, and "
           "beside it a short, squat, square stone tower with a flat roof and one warm window near its top. On the right a "
           "narrow river winds between bare trees, and low among the trees by the water three tiny cold blue lamp flames, "
           "far apart from each other at different distances, each with a short blue reflection in the water. The fire's "
           "orange is the warm color; the rest is blue dusk."),
}


def rgb(f):
    return cv2.imread(f, cv2.IMREAD_COLOR)


def canvases(kind, k):
    """init (= inpaint image), mask and control for plate k on canvas kind; returns paths and the crop."""
    d = os.path.join(OUT, "canvas")
    os.makedirs(d, exist_ok=True)
    m, md = rgb(MASTER), rgb(MASTER_DEPTH)
    td = rgb(os.path.join(OUT, "layouts", k + "_depth.png"))
    if kind == "V":
        a, b = BAND
        cw, ch, crop = W, (b - a) + GAP + H, [0, (b - a) + GAP, W, H]
        init = np.full((ch, cw, 3), 128, np.uint8)
        ctl = np.zeros((ch, cw, 3), np.uint8)
        init[:b - a], ctl[:b - a] = m[a:b], md[a:b]
        init[b - a:b - a + GAP] = 0
        ctl[crop[1]:] = td
    else:
        cw, ch, crop = W + GAP + W, H, [W + GAP, 0, W, H]
        init = np.full((ch, cw, 3), 128, np.uint8)
        ctl = np.zeros((ch, cw, 3), np.uint8)
        init[:, :W], ctl[:, :W] = m, md
        init[:, W:W + GAP] = 0
        ctl[:, crop[0]:] = td
    mask = np.zeros((ch, cw, 3), np.uint8)
    mask[crop[1]:crop[1] + crop[3], crop[0]:crop[0] + crop[2]] = 255
    names = {}
    for tag, im in (("init", init), ("mask", mask), ("ctl", ctl)):
        names[tag] = REL + f"canvas/{kind}_{k}_{tag}.png"
        cv2.imwrite(os.path.join(d, f"{kind}_{k}_{tag}.png"), im)
    return names, crop, cw, ch


def ic_prompt(kind, k):
    return (f"One dark sheet holding two plates from the same illustrated book, {SHEET[kind]} with a thin black gap between "
            f"them, each plate full-bleed, filling its whole area edge to edge with no border, margin or paper edge. Both "
            f"plates were painted by the same painter with the same brushes, in exactly the same technique: {HAND}"
            f"{FIRST[kind]}: {MASTER_WORDS}{SECOND[kind]}, painted in exactly the same way as the first: {CONTENT[k]}")


def ic_job(kind, k, seed, strength, end, tag):
    c, crop, cw, ch = canvases(kind, k)
    return {"name": f"{k}_{tag}", "prompt": ic_prompt(kind, k), "seed": seed, "w": cw, "h": ch,
            "init": c["init"], "denoise": 1.0, "inpaint": c["init"], "mask": c["mask"], "hold": True,
            "control": c["ctl"], "strength": strength, "end": end, "crop": crop}


def alt_job(k, seed, strength, end, dn, tag):
    return {"name": f"{k}_{tag}", "prompt": FRAME + HAND[0].upper() + HAND[1:] + CONTENT[k], "seed": seed,
            "init": R14[k], "denoise": dn, "control": REL + f"layouts/{k}_depth.png", "strength": strength, "end": end}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["test", "final"])
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--strength", type=float, default=0.6)
    ap.add_argument("--end", type=float, default=0.7)
    ap.add_argument("--canvas", default="V")
    a = ap.parse_args()
    jobs = []
    if a.which == "test":
        for k in ("p9", "p1"):
            jobs.append(ic_job("V", k, [11, 23], 0.6, 0.7, "icv_s60e70"))
            jobs.append(ic_job("V", k, [11], 0.45, 0.5, "icv_s45e50"))
            jobs.append(ic_job("H", k, [11], 0.6, 0.7, "ich_s60e70"))
            jobs.append(alt_job(k, [11], 0.6, 0.7, 0.8, "alt_d80"))
        for k in ("p4", "p7"):
            jobs.append(ic_job("V", k, [11], 0.6, 0.7, "icv_s60e70"))
    else:
        tag = f"ic{a.canvas.lower()}_s{int(a.strength * 100)}e{int(a.end * 100)}"
        for k in ("p1", "p4", "p7", "p9"):
            jobs.append(ic_job(a.canvas, k, [a.seed], a.strength, a.end, tag))
    f = os.path.join(HERE, "jobs", f"style_r15_{a.which}.json")
    json.dump({"defaults": {"w": W, "h": H, "steps": 9}, "jobs": jobs}, open(f, "w"), indent=1)
    print(f, sum(len(j["seed"]) for j in jobs), "pictures")


if __name__ == "__main__":
    main()
