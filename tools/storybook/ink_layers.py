"""Split the SB00 ink picks into parallax layers in one hand (Storybook 3, phase 1).

    python tools/storybook/ink_layers.py masks  [plates]   # CPU: layer masks from depth/SAM (needs _work masks)
    python tools/storybook/ink_layers.py fills  [plates]   # GPU: Krea inpaint behind every cut (cached)
    python tools/storybook/ink_layers.py states [plates]   # GPU: drawn states, 4 seeds each (cached)
    python tools/storybook/ink_layers.py build  [plates]   # CPU: post (ink_post), cut, layers.json, sheet, checks

Everything happens at the pick's own size ("gen" px); build Lanczos-ups each layer to the
plate's target width and runs ink_post on it with the paper sampled at the layer's place.
Layers: back to front; M[i] is the part of the pick each layer owns (a partition); each layer
also extends under the nearer layers by its fill margin (the most the lens moves it against
them at the plate's camera keys, +10%), filled by Krea inpaint where an object was cut.
The lens (godot/logic/Storybook/StoryMotion.cs): a layer at depth z shows canvas point
c = R + (X - R)/z at the screen centre and appears z/(z - dolly) as large; R is the plate's
rest (the camera that sees the plate as painted). layers.json gives pos/scale in the comps'
canvas units with that rest; wiring shifts pos and keys by (1600, 900) - rest.
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_post  # noqa: E402

OUT = os.path.join(HERE, "out", "ink_layers")
WORK = os.path.join(OUT, "_work")
JOBS = {k: json.load(open(os.path.join(HERE, "ink_jobs", k + ".json"), encoding="utf-8")) for k in ("r2", "r3")}
COMPS = {p["id"]: p for p in json.load(open(os.path.join(HERE, "comps", "sb00_comps.json"), encoding="utf-8"))["plates"]}
SCREEN = (1920, 1080)
BAND = 1339 / 1800            # the 2.39:1 bars crop the 16:9 frame


def job(r, name):
    j = [x for x in JOBS[r]["jobs"] if x["name"] == name][0]
    return JOBS[r]["prefix"], j["prompt"], JOBS[r]["style"]


def full(r, prompt):
    return (JOBS[r]["prefix"] + " " + prompt + " " + JOBS[r]["style"]).strip()


def cut(text, start, end, new):
    a = text.index(start)
    b = text.index(end, a) if end else len(text)
    return text[:a] + new + text[b:]


# ---------------------------------------------------------------- plates
P5 = job("r3", "p5")[1]
P5_DROWNED_OLD = "In the ditches on both sides of the road stand many drowned dead:"
P5_CLEAN = cut(P5, P5_DROWNED_OLD, " Snow on the banks", "The ditches on both sides of the road are empty: snow, frosted reeds and dark mud, nobody there.")
P5_DROWNED = cut(P5, P5_DROWNED_OLD, " Snow on the banks",
                 "In the ditches on both sides of the road stand the drowned dead standing in the ditch along the road: gaunt corpses of peasants "
                 "in soaked ragged medieval tunics and shifts clinging to them, barefoot, no hats, pale sunken faces with dark empty eyes, long "
                 "wet hair plastered down and hanging with river weed, water dripping, arms hanging slack, every face turned toward the road, "
                 "irregular spacing, varied heights and stances, some turned, some half in shadow.")
P5_FAR = (
    "Medieval winter night, deep dark, a black starless sky. Across open snowy ground, a black river ford: a line of flat stepping "
    "stones across the shallows, ice along both edges, a low far bank with a dark line of distant trees. On the near bank of the ford "
    "stand three crude open cages of black iron bars on short black iron posts burning with a cold pale blue flame; in the middle of the "
    "river a fourth pale blue flame hangs in the empty air. No trees in front, no cart, nobody. Snow carved in dim moonlit blue-gray. "
    "The picture is mostly black.")
SKY_NIGHT = ("An empty pitch-black starless winter night sky, almost solid black ink with a few faint blue-black horizontal gouge "
             "lines, no light, no moon, no trees, nothing else.")

P6 = job("r2", "p6")[1]
P6_TRAV = ("One lone traveler in a long plain dark wool cloak with a deep hood up, seen from behind, sits on the log by the fire reading a "
           "folded letter, a small flask on a cord at the wrist; no weapon.")
ANYONE = ("a long plain dark wool cloak, deep hood up, gloved, no face, no hair, nothing that reads man or woman, no weapon")
P6_CLEAN = P6.replace(P6_TRAV, "The log by the fire is empty; nobody is there.")
P6_STATES = {
    "stand": P6.replace(P6_TRAV, f"One lone hooded traveler, {ANYONE}, stands beside the log by the fire, back to us, the letter put away, "
                                 "a small flask on a cord at the wrist."),
    "walk1": P6.replace(P6_TRAV, f"One lone hooded traveler, {ANYONE}, walks away from us toward the river at right, back to us, mid-stride, "
                                 "still lit by the fire on one side."),
    "walk2": P6.replace(P6_TRAV, f"Small in the middle distance, one lone hooded traveler, {ANYONE}, walks away from us down the slope toward "
                                 "the river at right, back to us, mid-stride, in the cold dusk shadow near the water, unlit, a dark silhouette."),
}
P6_FAR = ("Medieval dusk, the last light: a deep indigo sky over a thin dull rose band along the horizon. The far side of a wide smooth "
          "river: dark rounded trees by the water, three tiny points of cold pale blue light low among them, dark rolling hills beyond. "
          "Nobody.")
SKY_DUSK = "A deep indigo dusk sky over a thin dull rose band along the horizon, carved with long sweeping gouge lines, empty, nothing else."

P7 = job("r2", "p7")[1]
P7_BG = ("Night. A black river seen from its edge: dark water carved with short horizontal strokes and gentle rings, cold blue light "
         "glittering on it, the far bank a black band across the top. No figure, no lantern, nothing else.")
P7_HEAD = P7.replace("leaning over the water, the face entirely hidden inside the deep hood,",
                     "the hooded head lifted and turned toward the blue lamp, cold blue light washing along the hood's edge, the face entirely "
                     "hidden inside the deep hood, the body still bent over the water,")

P7U = job("r3", "p7u")[1]
P7U_BG = ("Underwater at night, looking up from below the surface of a black river: black-green murky water, carved deep green-black "
          "ink, the rippling pale underside of the surface far above. No bubbles.")

PLATES = {
    "p5": dict(src="ink_r3/p5_s707.png", r="r3", target=3600, rest=(1800, 1000),
               cams=[(1880, 700, 2.2, .15), (2000, 690, 2.5, .15), (1880, 700, 1.6, .15), (1800, 1000, 1.0, 0)],
               layers=[("sky", 12), ("far", 3.5), ("trees", 2.2), ("road", 1.4)],
               state_layer=None, glows=[("lamps", 3.5, "8ac8ff")]),     # round 3: the drowned baked into road
    "p6": dict(src="ink_r2/p6_s47.png", r="r2", target=3800, rest=(2600, 1055),
               cams=[(1650, 1050, 1.0, 0), (3550, 1060, 1.25, 0)],
               layers=[("sky", 10), ("far", 3.0), ("near", 1.0)],
               state_layer=("traveler", 1.0), glows=[("fire_glow", 1.0, "ffa04a")]),
    "p7": dict(src="ink_r2/p7_s11.png", r="r2", target=2560, rest=(1600, 1200),
               cams=[(1450, 1750, 1.3, 0), (1450, 1700, 1.3, 0), (1500, 1150, 1.15, 0)],
               layers=[("far_water", 3.0), ("water", 1.2), ("lamp", 1.1), ("traveler", 0.95)],
               state_layer=("traveler", 0.95), glows=[("lamp_glare", 1.1, "8ac8ff"), ("reflection_blue", 1.2, "8ac8ff")]),
    "p7u": dict(src="ink_r3/p7u_s47.png", r="r3", target=1920, rest=(1600, 900),
                cams=[(1600, 900, 1.0, 0)],
                layers=[("under", 1.0), ("bubbles", 0.9)], state_layer=None, glows=[("lamp_warped", 1.0, "8ac8ff")],
                light="cold"),     # ink_post's cold light step: the lights go cage blue / snow, never parchment
}

# ---------------------------------------------------------------- round 2 (ink_r2.py)
# p5 drowned: figures generated as a frieze (P5_FRIEZE, one per seed), SAM-cut, placed one per figure slot (gen px):
# (centre x, foot y, height); near ones bigger, irregular spacing, where the pick's figures stood
P5_SEEDS = (11, 23, 47, 202, 303, 505)
P5_DROWNED_DENOISE = 0.68      # img2img over a painted silhouette init (ink_r2.sketch), kept inside the slots
P5_DITCHES = {"left": (0, 400, 768, 1088), "right": (1088, 400, 2048, 1088)}
P5_SLOTS = {
    "left": [(140, 992, 300), (262, 905, 238), (358, 862, 214), (492, 968, 372), (598, 692, 188), (532, 606, 138),
             (474, 550, 98), (616, 566, 90)],
    "right": [(1196, 675, 138), (1296, 742, 206), (1385, 694, 128), (1452, 852, 246), (1560, 962, 312), (1702, 930, 286),
              (1640, 720, 150), (1918, 1042, 300), (1918, 524, 72)],
}
P5_DROWNED_LOCAL = (
    "Night, a flooded roadside ditch of black water beside a snowy rutted road, carved snow banks and frosted reeds. Standing in the "
    "ditch: drowned corpses standing upright in the flooded ditch, water to the shins; soaked torn shifts and tunics clinging to thin "
    "bodies; bare heads, long wet hair plastered flat and hanging over the face in strands, river weed; pale dead faces and hands "
    "catching the moonlight; arms hanging slack; heads tilted, every face turned toward the road; motionless. No hoods, no hats, no "
    "coats, no cloaks.")
P5_FRIEZE = (
    "Night, cold moonlight. Seven drowned dead stand far apart in a row, widely spaced with wide black gaps between them, each "
    "figure full length from head to shins, against a flat solid black background, standing in black water to the shins. Grim "
    "drowned corpses standing upright, every one different: gaunt and thin, soaked torn ragged shifts and tunics hanging in shreds "
    "and clinging to their bodies; bare heads, long wet hair plastered flat and hanging over the face in strands, river weed; "
    "pale dead faces with dark hollow eyes and slack mouths, pale dead hands catching the moonlight; arms hanging slack; heads "
    "tilted and drooping at odd angles, all turned to the left; varied heights, one stooped, one leaning; motionless. Cold blue-gray "
    "moonlight, no warm color. No hoods, no hats, no coats, no cloaks.")
P5_FRIEZE_SIZE = (1920, 1088)
P5_WATER = 0.10          # the bottom of each figure fades into the ditch water (fraction of its height)
P5_CLEAN_LOCAL = ("Night, a snowy roadside bank beside a rutted dirt road, a narrow flooded ditch of black water with frosted reeds, "
                  "snow carved in dim moonlit blue-gray. Empty: nobody, no figures, no people.")
P5_GHOST_BOX = (1100, 500, 1365, 790)      # gen px: the right ditch's far ghosts (canvas x 1930-2400, y 880-1390)
# p7 head_up retry: generous hood/head/shoulder/back mask plus room toward the lamp
P7_HEAD2 = P7.replace("leaning over the water, the face entirely hidden inside the deep hood,",
                      "the hooded head raised high and turned up toward the hanging blue lamp at the upper right, looking up at it, "
                      "the hood's edge washed in pale blue light, the face entirely hidden inside the deep hood, the body still "
                      "kneeling over the water,")
# p6 walk2: walk1's pick placed far down by the water as an unlit silhouette (canvas units: feet centre, scale vs walk1)
# p5 round 3 (ink_r3.py): the drowned baked into the road layer from this candidate's whole (_work/p5/S_drowned_r3_<tag>.png)
P5_DROWNED_R3 = "d60_s11"
P7_HEAD_ROUND = 0       # which head_up candidates the build cuts (2: ink_r2 retry; 0: none)
P7_RIM = True           # True: ship traveler_blue_rim.png (add) instead of a head_up state
# round 3: from the stand pick, scaled to round 2's walk2 height (walk1 s47's 534 px x 0.55)
# round 4: feet on the stepping stone at the water's edge, so the whole figure stands against the pale river at the last
# key (camera 3550/1060 x1.25) and still 0.5 s before it; 0.85 of round 3's height (294 px)
P6_WALK2 = dict(feet=(4201, 1461), src="stand", height_px=250, dome=False, fill="navy", fill_k=0.35, rim="slate",
                rim_side=(1.0, -0.2))


# p6 round 4: the big hill's foot right of the far mask's straight cut at 0.515 W goes to near, under a drawn
# contour (gen px) from the hill's top line past the tree's trunk base down to the river; the far layer gets a
# fill behind it (fill job far2), so neither layer has a straight edge there
P6_FOOT = [(1150, 307), (1186, 319), (1230, 333), (1265, 346), (1290, 362), (1312, 382), (1328, 400), (1342, 418),
           (1354, 434), (1368, 448), (1382, 457), (1398, 466)]


def wd(plate, *a):
    d = os.path.join(WORK, plate)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *a)


def load_mask(path):
    return np.asarray(Image.open(path).convert("L")) > 127


def save_mask(m, path):
    Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).save(path)


def pick(plate):
    return np.asarray(Image.open(os.path.join(HERE, "out", PLATES[plate]["src"])).convert("RGB")).astype(np.float32) / 255


def units(plate):
    """canvas units per gen px."""
    return COMPS[plate]["size"][0] / pick(plate).shape[1]


# ---------------------------------------------------------------- lens
def lens_point(R, cam, z, u, v):
    """Canvas point on a layer at depth z under the screen point (u, v) in [-1, 1] (band height)."""
    X, Y, zoom, dolly = cam
    f = z / max(0.05, z - dolly)
    return (R[0] + (X - R[0]) / z + u * 1600 / (zoom * f), R[1] + (Y - R[1]) / z + v * 900 * BAND / (zoom * f))


def margins(plate):
    """Per layer (by index in the full stack incl. state layer): the most it moves against any nearer layer (units)."""
    P = PLATES[plate]
    zs = [z for _, z in P["layers"]] + ([P["state_layer"][1]] if P["state_layer"] else [])
    out = []
    for i, zi in enumerate(zs):
        m = 0.0
        for zj in zs[i + 1:]:
            for cam in P["cams"]:
                for u in (-1, 0, 1):
                    for v in (-1, 0, 1):
                        a, b = lens_point(P["rest"], cam, zi, u, v), lens_point(P["rest"], cam, zj, u, v)
                        m = max(m, abs(a[0] - b[0]), abs(a[1] - b[1]))
        out.append(m)
    return out


# ---------------------------------------------------------------- masks
def clean_comps(m, min_px):
    lab, n = nd.label(m)
    if n == 0:
        return m
    sz = nd.sum(m, lab, range(1, n + 1))
    return np.isin(lab, 1 + np.where(sz >= min_px)[0])


def figures_by_depth(depth, y_min, excl, min_px=300, thresh=8):
    """Upright figures standing out of the ground in a MoGe depth map (a wide grey opening is the ground)."""
    H, W = depth.shape
    diff = depth - nd.grey_opening(depth, size=(1, 181))
    m = diff > thresh
    m[:int(y_min * H)] = 0
    m &= ~excl
    m = nd.binary_opening(m, iterations=3)
    m = nd.binary_fill_holes(nd.binary_closing(m, iterations=3))
    lab, n = nd.label(m)
    keep = np.zeros_like(m)
    for i, sl in enumerate(nd.find_objects(lab)):
        c = lab[sl] == i + 1
        y0, x0 = sl[0].start / H, sl[1].start / W
        if c.sum() < min_px or y0 <= y_min + 0.01 or c.mean() < 0.38 or (x0 > 0.88 and y0 < 0.45):
            continue
        keep[sl] |= c
    return keep


def poly_mask(shape, pts):
    H, W = shape
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon([(x * W, y * H) for x, y in pts], fill=255)
    return np.asarray(im) > 127


def make_masks(plate):
    """Writes M_<layer>.png (a partition, back to front), remove.png (figures cut from the clean plate),
    state_region.png / state masks, glow sources. Uses _work/<plate>_depth.png and SAM masks."""
    img = pick(plate)
    H, W, _ = img.shape
    w = lambda n: os.path.join(WORK, f"{plate}_{n}")
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    yy = np.arange(H)[:, None] / H * np.ones((1, W))
    M = {}
    if plate == "p5":
        d = np.asarray(Image.open(w("depth.png")).convert("L")).astype(np.float32)
        cart = load_mask(w("sam_wooden_cart.png"))
        tree = load_mask(w("t_tree.png"))
        people = figures_by_depth(d, 0.40, nd.binary_dilation(cart, iterations=4) | tree)
        tree_mid = clean_comps(tree & (d >= 55), 200)
        cartd = nd.binary_dilation(cart, iterations=2)
        sky = (d < 8) & (yy < 0.4) & ~tree_mid
        sky = nd.binary_opening(sky, iterations=2)
        far = (d < 50) & ~tree_mid & ~sky & ~cartd
        road = (d >= 95) & ~tree_mid & ~cartd
        trees = ~(sky | far | road)
        M = {"sky": sky, "far": far, "trees": trees, "road": road}
        save_mask(nd.binary_dilation(people, iterations=5), wd(plate, "remove.png"))
        save_mask(nd.binary_dilation(people, iterations=10), wd(plate, "state_region.png"))
        flame = (img[..., 2] > 0.72) & (lum > 0.55) & (yy < 0.47) & (img[..., 2] > img[..., 0] + 0.08)
        save_mask(flame, wd(plate, "glow_lamps.png"))
        save_mask(tree_mid | cartd, wd(plate, "objects_far.png"))   # cut from the far layer: Krea fills behind
    elif plate == "p6":
        sky = load_mask(w("sam_sky.png"))
        river = load_mask(w("sam_river.png"))
        person = load_mask(w("sam_person.png"))
        # the river's top edge per column; the far side is above it, right of the big hill's foot
        top = np.full(W, int(0.5 * H))
        cols = np.where(river.any(0))[0]
        top[cols] = river[:, cols].argmax(0)
        top = nd.minimum_filter1d(nd.median_filter(top, 31), 15)
        x0 = int(0.515 * W)
        far = np.zeros((H, W), bool)
        for x in range(x0, W):
            far[:top[x], x] = True
        far &= ~sky
        # round 4: the hill's foot below P6_FOOT (a smooth contour with a small drawn wobble) is near's
        cx, cy = np.array(P6_FOOT, np.float32).T
        xs_ = np.arange(W)
        line = np.interp(xs_, cx, cy, left=-1, right=H + 1)
        rng = np.random.default_rng(6)
        wob = nd.gaussian_filter1d(rng.normal(0, 1, W), 6)
        line = line + 2.5 * wob / (np.abs(wob).max() + 1e-6)
        line[(xs_ < cx[0]) | (xs_ > cx[-1])] = H + 1
        foot = far & (np.arange(H)[:, None] > line[None])
        far &= ~foot
        near = ~(sky | far)
        M = {"sky": sky, "far": far, "near": near}
        save_mask(nd.binary_dilation(foot, iterations=14) & ~sky, wd(plate, "fillmask_far_foot.png"))   # far2's fill
        save_mask(nd.binary_dilation(person, iterations=6), wd(plate, "remove.png"))
        fire = (img[..., 0] > 0.7) & (img[..., 2] < 0.45) & (img[..., 1] > 0.25) & (np.arange(W)[None] < 0.35 * W)
        save_mask(fire, wd(plate, "glow_fire_glow.png"))
        # where each state is drawn (gen px boxes, x0 y0 x1 y1 as fractions): the seated pick is "sit"
        boxes = {"stand": (0.165, 0.26, 0.275, 0.76), "walk1": (0.33, 0.30, 0.42, 0.80), "walk2": (0.545, 0.40, 0.605, 0.70)}
        for k, (a, b, c, e) in boxes.items():
            m = np.zeros((H, W), bool)
            m[int(b * H):int(e * H), int(a * W):int(c * W)] = True
            m = nd.binary_dilation(m, iterations=4)
            if k == "stand":
                m |= nd.binary_dilation(person, iterations=8)
            save_mask(m, wd(plate, f"state_{k}.png"))
    elif plate == "p7":
        far = load_mask(w("sam_sky.png"))
        lamp = load_mask(w("sam_hanging_iron_lantern.png"))
        person = load_mask(w("sam_person.png")) | load_mask(w("sam_flask.png"))   # the flask goes with the hand
        refl = load_mask(w("sam_reflection_of_the_lantern.png"))
        bank = poly_mask((H, W), [(0, 0.56), (0.07, 0.58), (0.14, 0.70), (0.22, 0.80), (0.33, 0.86), (0.46, 0.90), (0.56, 0.93),
                                  (0.60, 1.0), (0, 1.0)])
        trav = person | bank
        far &= ~trav & ~lamp
        lamp_l = lamp & ~trav
        water = ~(far | lamp_l | trav)
        M = {"far_water": far, "water": water, "lamp": lamp_l, "traveler": trav}
        save_mask(nd.binary_dilation(lamp | person, iterations=6), wd(plate, "objects_far.png"))
        flame = lamp & (lum > 0.55)
        save_mask(flame, wd(plate, "glow_lamp_glare.png"))
        save_mask(refl & (lum > 0.5), wd(plate, "glow_reflection_blue.png"))
        head = person & (yy < 0.43)
        save_mask(nd.binary_dilation(head, iterations=28), wd(plate, "state_head_up.png"))
    elif plate == "p7u":
        bub = (lum > 0.42) & (yy > 0.46)
        bub = clean_comps(nd.binary_dilation(bub, iterations=2), 25)
        under = ~bub
        M = {"under": under, "bubbles": bub}
        save_mask(clean_comps((lum > 0.5) & (yy < 0.5), 50), wd(plate, "glow_lamp_warped.png"))
    for k, m in M.items():
        save_mask(m, wd(plate, f"M_{k}.png"))
    print(plate, {k: round(float(m.mean()), 3) for k, m in M.items()}, "margins (units)", [round(x) for x in margins(plate)])


# ---------------------------------------------------------------- fills (GPU)
def fill_jobs(plate):
    """(name, init, mask, prompt): run in order; each composites back only inside its mask."""
    P = PLATES[plate]
    um = units(plate)
    mg = [int(np.ceil(1.1 * x / um)) + 4 for x in margins(plate)]
    src = os.path.join(HERE, "out", P["src"])
    jobs = []
    names = [n for n, _ in P["layers"]]
    if plate == "p5":
        jobs.append(("clean", src, wd(plate, "remove.png"), full("r3", P5_CLEAN), None))
        jobs.append(("far", "@clean", ("under", "far", mg[1]), full("r3", P5_FAR), None))
        jobs.append(("sky", "@far", ("ring", "sky", mg[0]), full("r3", SKY_NIGHT), None))
    elif plate == "p6":
        jobs.append(("clean", src, wd(plate, "remove.png"), full("r2", P6_CLEAN), None))
        jobs.append(("far", "@clean", ("under", "far", mg[1]), full("r2", P6_FAR), None))
        jobs.append(("sky", "@far", ("ring", "sky", mg[0]), full("r2", SKY_DUSK), None))
        jobs.append(("far2", "@far", wd(plate, "fillmask_far_foot.png"), full("r2", P6_FAR), None))   # round 4: behind the foot
    elif plate == "p7":
        jobs.append(("bg", src, wd(plate, "objects_far.png"), full("r2", P7_BG), None))
    elif plate == "p7u":
        jobs.append(("bg", src, ("over", "bubbles", 6), full("r3", P7U_BG), None))
    return jobs, mg


def resolve_mask(plate, spec):
    if isinstance(spec, str):
        return spec
    kind, layer, m = spec
    M = load_mask(wd(plate, f"M_{layer}.png"))
    near = nd.distance_transform_edt(~M) <= m
    r = near if kind == "over" else near & ~M   # over: the layer and m px around; ring/under: m px outside it
    dst = wd(plate, f"fillmask_{layer}_{kind}.png")
    save_mask(nd.binary_dilation(r, iterations=3), dst)
    return dst


def composite_back(init, fill, mask):
    """The fill only inside its (slightly feathered) mask: elsewhere the init exactly."""
    a = np.asarray(Image.open(init).convert("RGB")).astype(np.float32)
    b = np.asarray(Image.open(fill).convert("RGB").resize((a.shape[1], a.shape[0]), Image.LANCZOS)).astype(np.float32)
    m = np.asarray(Image.open(mask).convert("L")).astype(np.float32) / 255
    m = nd.gaussian_filter(m, 1.0) * (m > 0)
    return Image.fromarray((a * (1 - m[..., None]) + b * m[..., None] + 0.5).astype(np.uint8))


def run_fills(plate):
    import ink_comfy as C
    jobs, mg = fill_jobs(plate)
    H, W = pick(plate).shape[:2]
    for name, init, mspec, prompt, _ in jobs:
        dst = wd(plate, f"S_{name}.png")
        if os.path.exists(dst):
            continue
        if init.startswith("@"):
            init = wd(plate, f"S_{init[1:]}.png")
        mask = resolve_mask(plate, mspec)
        t0 = time.time()
        raw = wd(plate, f"raw_{name}.png")
        C.krea(prompt, W, H, 7, raw, init=init, denoise=1.0, mask=mask)
        composite_back(init, raw, mask).save(dst)
        print(plate, name, f"{time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------- states (GPU)
def state_jobs(plate):
    src = os.path.join(HERE, "out", PLATES[plate]["src"])
    if plate == "p5":
        return [("drowned", wd(plate, "S_clean.png"), wd(plate, "state_region.png"), full("r3", P5_DROWNED), 0.92)]
    if plate == "p6":
        return [(k, wd(plate, "S_clean.png"), wd(plate, f"state_{k}.png"), full("r2", p), 1.0) for k, p in P6_STATES.items()]
    if plate == "p7":
        return [("head_up", src, wd(plate, "state_head_up.png"), full("r2", P7_HEAD), 0.9)]
    return []


SEEDS = (11, 23, 47, 202)


def run_states(plate):
    import ink_comfy as C
    H, W = pick(plate).shape[:2]
    for name, init, mask, prompt, dn in state_jobs(plate):
        for s in SEEDS:
            dst = wd(plate, f"st_{name}_s{s}.png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            raw = wd(plate, f"raw_st_{name}_s{s}.png")
            C.krea(prompt, W, H, s, raw, init=init, denoise=dn, mask=mask)
            composite_back(init, raw, mask).save(dst)
            # the figure's cut: MoGe figures for p5's crowd, SAM 'person' for one traveler
            if plate == "p5":
                C.depth(dst, wd(plate, f"st_{name}_s{s}_depth.png"))
            else:
                C.sam(dst, "hooded person", wd(plate, f"st_{name}_s{s}_person.png"), 0.3)
            print(plate, name, s, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    stage = sys.argv[1]
    plates = sys.argv[2:] or list(PLATES)
    for p in plates:
        if stage == "masks":
            make_masks(p)
        elif stage == "fills":
            run_fills(p)
        elif stage == "states":
            run_states(p)
        elif stage == "build":
            import ink_build
            ink_build.build(p)
