"""L1 Stage C wave 2 (C6): the color chain, one command from the boards to the rigs and the classes' albedos
(docs/design/LOOK_BIBLE.md rules 1-4, 9; the boards MB1-MB4 and LB; godot/data/look/swatches.json).

The fault it fixes (wave 2's helpers): the classes were set by dividing the boards by the rigs' measured response, but the
rigs were never derived from the boards per channel, so no one albedo matched a board's lit side and its shade side at once.
The chain: (1) each board's lit and shade patches per material, by day and by night, as data (swatches.json); (2) the day
rig's fill FROM the boards' day shade/lit ratio per channel (the median across the day swatches), set so the engine's
shade/lit on a NEUTRAL grey card gives it; (3) each class's albedo = the board's day lit side through the day key's grey-card
response (per channel, the response curve's inverse: the grade is in it); (4) the night rigs' moon key and fill FROM the
night lit and shade sides over those albedos (the median across the night swatches); (5) her ember, (6) dawn and the class
marks (albedo_ctl). No frame is ever an input: the frames are the check.

    python tools/look/color_chain.py measure [NAME]   grey cards (0.18, 0.5, 0.8) on the lookdev stage, all
                                                                    rigs -> OUT/NAME/g18|g50|g80, OUT/NAME/cards.json
    python tools/look/color_chain.py boards                          the swatches' board colors -> OUT/boards.json
    python tools/look/color_chain.py solve [NAME]                    rigs + albedos from boards.json and NAME's cards
                                                                    -> OUT/solve.json (the arithmetic, per channel)
    python tools/look/color_chain.py apply                           solve.json into rigs.json, materials.json, ground.json,
                                                                    town.json (one read-modify-write each)
    python tools/look/color_chain.py wild NAME                       (L7 S1d) day_wild's key from NAME's wild and day cards
    python tools/look/color_chain.py night NAME                      (L7 S2) the night and dawn rigs from solve.json, NAME's cards
                                                                    (solve DAYCARDS NAME first: the day as it stands)
    python tools/look/color_chain.py check [NAME]     the solved albedos drawn on the stage (the relit check)
    python tools/look/color_chain.py all [NAME]                      measure, boards, solve, apply, the relit check, then the
                                                                    kits' own builds and the ground check
"""
import json, os, subprocess, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "style")); sys.path.insert(0, HERE)
import board_measure as bm  # noqa: E402
import calib  # noqa: E402

INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"
OUT = os.path.join(INPUTS, "look_l1", "c", "w2", "chain", "lookdev")
DATA = os.path.join(ROOT, "godot", "data", "look")
RIGS = ("day", "night", "dawn", "arena", "wild")  # (L7 S1d: wild, the Verge's day_wild, for wild_key)
GREYS = {"g05": 0.05, "g18": 0.18, "g50": 0.5, "g80": 0.8}  # (0.05: the dark classes, leather and road, sit under the 0.18 card)


def lin_hex(v):
    v = min(max(v, 0.0), 1.0)
    s = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return "#" + f"{round(s * 255):02x}" * 3


def shoot(out, albedo_file, extra="", rigs=RIGS):
    """The lookdev stage's swatch row in the given colors (calib.shoot's run, every rig, plus EXTRA game args)."""
    import shutil
    ex = f"--lookdev-swatches --lookdev-fire 0 --b3-cams swatches --b3-albedo {albedo_file} {extra}".strip()
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "style", "lookdev.py"), "shoot", "--out", out, "--rigs", ",".join(rigs), "--extra", ex], check=False)
    for r in rigs:
        f = os.path.join(ROOT, "godot", ".shots", f"lookdev_{r}_item_swatches_1.png")
        if os.path.exists(f): shutil.copy2(f, os.path.join(out, f"lookdev_{r}_item_swatches.png"))


# (her ember off for the cards: the swatch row stands 2.8 m from her, deep in her light's reach (11 m x LightRadius x 0.75
# x the rig's ember_reach), which lit the night cards' tops ember-red; the moon and the sun are measured alone)
CARD_EXTRA = "--ember-range 0.01"


def measure(name="cards", rigs="all", extra=CARD_EXTRA):
    """Grey cards: every class's swatch drawn at a neutral albedo (0.18, 0.5, 0.8 linear), its own cel band and roughness,
    under every rig, at the play camera and the close view, her ember off; the lit and shade faces per level."""
    rigs = RIGS if rigs == "all" else tuple(rigs.split(","))
    calib.OUT = os.path.join(OUT, name); calib.RIGS = rigs
    lib = json.load(open(calib.LIB, encoding="utf-8"))
    cards = {}
    for tag, g in GREYS.items():
        d = os.path.join(calib.OUT, tag)
        if not os.path.exists(os.path.join(d, "swatches.json")):
            os.makedirs(d, exist_ok=True)
            f = os.path.join(d, "grey.json")
            json.dump({c: f"{lin_hex(g)} {0.45 if lib['classes'][c]['cel']['spec'][2] > 0 else 1.0}" for c in lib["classes"]}, open(f, "w"))
            shoot(d, f, extra, rigs)
            calib.measure(tag)
        cards[tag] = json.load(open(os.path.join(d, "swatches.json")))
    # (L7 S1) the day's sky on the lit side: the 0.18 cards under the day rig with its key off (--air-tune key=0)
    d = os.path.join(calib.OUT, "nokey")
    if "day" in rigs and not os.path.exists(os.path.join(d, "swatches.json")):
        os.makedirs(d, exist_ok=True); f = os.path.join(d, "grey.json")
        json.dump({c: f"{lin_hex(0.18)} {0.45 if lib['classes'][c]['cel']['spec'][2] > 0 else 1.0}" for c in lib["classes"]}, open(f, "w"))
        calib.RIGS = ("day",); shoot(d, f, extra + " --air-tune key=0", ("day",)); calib.measure("nokey"); calib.RIGS = rigs
    if os.path.exists(os.path.join(d, "swatches.json")): cards["nokey"] = json.load(open(os.path.join(d, "swatches.json")))
    json.dump(cards, open(os.path.join(calib.OUT, "cards.json"), "w"), indent=0)
    open(os.path.join(calib.OUT, "day_rigs.sig"), "w").write(day_sig())
    print("cards:", {k: len(v) for k, v in cards.items()})


def day_sig():
    """(L1 l9 DAY) The day rigs' light as the cards were measured under it (day_town, day_wild, less their FROM): apply_day
    composes its gains onto the rigs as they stand, so a solve on cards measured under other rigs stepped the key again on
    every `all` (#ffbd88, #ffbd80, #ffbd78: the key drifted off the boards' sun, h 57 to 66). solve() refuses such cards."""
    import hashlib
    R = json.load(open(os.path.join(DATA, "rigs.json"), encoding="utf-8"))["rigs"]
    return hashlib.sha1(json.dumps({n: {a: b for a, b in R[n].items() if a != "from"} for n in ("day_town", "day_wild")}, sort_keys=True).encode()).hexdigest()


# ---- (1) the boards' swatches --------------------------------------------------------------------------------------
def patch(img, pt, split):
    """One patch's kept pixels (linear rows): the box, its mask, then its side's percentile."""
    L, C, h, a, b, lin = bm.pixels(img, pt)
    side = pt.get("side")
    if side == "lit": k = L >= np.percentile(L, split["lit"])
    elif side == "shade": k = L <= np.percentile(L, split["shade"])
    else: k = np.ones(len(L), bool)
    return lin[k]


def lab(v):
    L, C, h = [float(x[0]) for x in bm.lin_to_lab5(np.asarray(v, float)[None])[:3]]
    return round(L, 3), round(C, 3), round(h)


def boards():
    from PIL import Image
    sw = json.load(open(os.path.join(DATA, "swatches.json"), encoding="utf-8"))
    lib = json.load(open(calib.LIB, encoding="utf-8"))
    imgs = {}
    out = {}
    for m, d in sw["materials"].items():
        img = imgs.setdefault(d["board"], Image.open(os.path.join(INPUTS, lib["boards"][d["board"]])))
        for light in ("day", "night", "dawn"):
            for side in ("lit", "shade"):
                pts = d.get(light, {}).get(side, [])
                if not pts: continue
                px = np.concatenate([patch(img, p, sw["split"]) for p in pts])
                v = px.mean(0)
                out.setdefault(m, {"class": d["class"]})[f"{light}_{side}"] = [round(float(x), 5) for x in v]
                print(f"{m:9s} {light:5s} {side:5s} n{len(px):6d} L{lab(v)[0]:.3f} C{lab(v)[1]:.3f} h{lab(v)[2]:4d}  lin {np.round(v, 4).tolist()}")
    for m, r in out.items():
        for light in ("day", "night", "dawn"):
            if f"{light}_lit" in r and f"{light}_shade" in r:
                r[f"{light}_ratio"] = [round(s / max(l, 1e-5), 4) for s, l in zip(r[f"{light}_shade"], r[f"{light}_lit"])]
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "boards.json"), "w"), indent=1)
    return out


# ---- the grey cards' response curves -------------------------------------------------------------------------------
TAGS = ("g05", "g18", "g50", "g80")
LV = np.array([GREYS[t] for t in TAGS])
METAL = ("iron", "bronze", "wrought", "gold")
DIFFUSE = ("setts", "plaster", "plank", "stone", "roof", "grass", "foliage", "rock", "road", "soil", "bark", "leather", "cloth")


def curve(cards, cls, key, side):
    """(levels, outputs[3 x 3]) of the NEUTRAL grey card under one rig and camera: the median over the diffuse classes'
    swatches (one cel model; a swatch the stage's house or a neighbour shades, as stone's top by day, is outvoted). A level
    whose channel the frame clipped (0.98+) is re-read along the unclipped green channel's slope from the level below.
    (cls is kept for the callers: every class answers to the one card.)"""
    rows = []
    for c in DIFFUSE:
        try: rows.append([cards[t][c][key][side] for t in TAGS])
        except KeyError: pass
    if not rows: return None
    Y = np.median(np.array(rows), 0)
    for i in range(1, len(LV)):
        for ch in range(3):
            if Y[i, ch] >= 0.98 and Y[i - 1, ch] < 0.98:
                g = 1 if ch != 1 else 2
                sl = np.log(max(Y[i, g], 1e-6) / max(Y[i - 1, g], 1e-6)) / np.log(LV[i] / LV[i - 1]) if Y[i, g] < 0.98 else 0.6
                Y[i, ch] = Y[i - 1, ch] * (LV[i] / LV[i - 1]) ** sl
            elif Y[i, ch] >= 0.98: Y[i, ch] = Y[i - 1, ch] * (LV[i] / LV[i - 1]) ** 0.6
    return LV, Y


def _interp(x, xs, ys):
    """Piecewise linear in log-log, the end segments extended."""
    lx, ly = np.log(np.maximum(xs, 1e-6)), np.log(np.maximum(ys, 1e-6))
    t = np.log(max(x, 1e-6))
    j = int(np.clip(np.searchsorted(lx, t) - 1, 0, len(lx) - 2))
    m = (ly[j + 1] - ly[j]) / max(lx[j + 1] - lx[j], 1e-9)
    return float(np.exp(ly[j] + m * (t - lx[j])))


def fwd(cv, a):
    """The drawn color of albedo a (per channel) on one class's curve."""
    xs, Y = cv
    return np.array([_interp(a[c], xs, Y[:, c]) for c in range(3)])


def inv(cv, o):
    """The albedo (per channel) that draws o on one class's curve (the curve's inverse: the grade is in it)."""
    xs, Y = cv
    return np.array([_interp(o[c], np.sort(Y[:, c]), xs[np.argsort(Y[:, c])]) for c in range(3)])


def med(rows):
    return np.median(np.array(rows), 0)


def lin_to_hex(v):
    v = np.clip(np.asarray(v, float), 0, 1)
    s = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)
    return "#" + "".join(f"{int(round(x * 255)):02x}" for x in s)


def hex_to_lin(h):
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def split_energy(v):
    """A linear color times an energy as (hex with its top channel at 1, the energy)."""
    v = np.asarray(v, float); e = float(v.max())
    return lin_to_hex(v / max(e, 1e-9)), e


# ---- (2)-(6) the solve ---------------------------------------------------------------------------------------------
def spread(rows, names, ref):
    """Per channel min and max, and the materials more than 2x off the median in any channel (the outliers)."""
    A = np.array(rows)
    off = [n for n, r in zip(names, A) if np.any(np.abs(np.log(np.maximum(r, 1e-4) / np.maximum(ref, 1e-4))) > np.log(2))]
    return {"min": A.min(0).round(3).tolist(), "max": A.max(0).round(3).tolist(), "outliers": off}


def shade_gain(cards, rig, rho, cam="play", lv=1, lit_gain=1.0):
    """The per-channel gain on a rig's shade light (fill, sky, ground) that gives the neutral 0.18 card shade/lit = rho
    (the 0.18 card: the day key clips a 0.5 card's red at 0.99, and dawn's grade lifts a 0.5 card's shade red past 0.99):
    per class card, the albedo whose shade draws rho x its lit (the shade curve's inverse) over 0.5; the median of the
    classes. Returns (gain, the cards' ratio now)."""
    ks, now = [], []
    for cls in DIFFUSE:
        cl, cs = curve(cards, cls, f"{rig}_{cam}", "lit"), curve(cards, cls, f"{rig}_{cam}", "shade")
        if cl is None or cs is None: continue
        lit, sh = cl[1][lv], cs[1][lv]
        now.append(sh / np.maximum(lit, 1e-5))
        ks.append(inv(cs, rho * lit * lit_gain) / LV[lv])
    return med(ks), med(now)


DAWN_SUN = "#ffa24a"  # (L1 l9 DAY, lead 8's call "the board wins": LB DAWN's sunlit setts [0.914, 0.312, 0.077] over the setts albedo #6c6977, the sun as board_sun reads it (the lit side's color over a known albedo); Oklab h 61 C 0.149; the setts draw LB's h 56. Was #f3d9a0 (L7 S2). solve() recomputes it: dawn_sun)


def dawn_sun(B, a):
    """(L1 l9 DAY) The dawn sun FROM LB DAWN: its sunlit setts over the setts albedo (linear a), luminance 1."""
    v = np.array(B["lb_setts"]["dawn_lit"]) / np.maximum(np.asarray(a, float), 1e-5)
    return lin_to_hex(v / v.max())
SUN = "#f3d9a0"  # (rule 3 of 3 Nov: the pale gold; L7 S1c: by day the boards' own sun replaces it, board_sun below; dawn keeps it)
BOARD_NEUTRAL = ("rock", "stone", "lb_setts")  # (the boards' grey stones: their lit sides are the boards' sun)


def chrom(v):
    v = np.asarray(v, float); return v / np.dot(bm.Y, v)


def board_sun(B):
    """(L7 S1c, lead 7's decision of 9 Nov: one sun, the boards') The sun the picked boards were painted under, read on their
    near-neutral grey stones (MB4's rock, MB3's stone, LB DAY's setts): the geometric mean of their day lit sides'
    chromaticities (luminance 1). About #ffc296, Oklab h 57: a peach gold. Returns (chroma, per stone chroma)."""
    per = {m: chrom(B[m]["day_lit"]) for m in BOARD_NEUTRAL}
    return np.exp(np.mean([np.log(v) for v in per.values()], 0)), per


def day_lit_gain(cards, sun):
    """Per channel, the gain that takes the neutral cards' day lit side to the sun's own color (linear, any scale) at its
    luminance (0.18 and 0.5 cards, the geometric mean; the 0.8 card's red sits at the gamut's ceiling)."""
    cl = curve(cards, None, "day_play", "lit"); ks = []
    for lv in (1, 2):
        lit = cl[1][lv]; k = sun / np.maximum(lit, 1e-5)
        ks.append(k * np.dot(bm.Y, lit) / np.dot(bm.Y, k * lit))
    return np.exp(np.mean(np.log(ks), 0))


DERIVED = {"cloth": ("plank", 0.04, 75, "MB3's plank (the beam and barrel, undyed wood's tan) lightness; C 0.04 and h 75 the middle of lead 7's undyed band (h 60-80, C 0.03-0.05); no picked board or target shows a lit undyed cloth that divides clean (G1 13's lit sacks give h 97, C 0.068)")}


def oklab_to_lin(L, C, h):
    a, b = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    l_, m_, s_ = L + 0.3963377774 * a + 0.2158037573 * b, L - 0.1055613458 * a - 0.0638541728 * b, L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                     -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])


# (L7 S2) The night's level is held (only the moon's colors come from the boards): the boards' night panels disagree on level by
# about 2x (MB3's setts ask the moon x2.49/1.38/1.42, LB NIGHT's setts x1.44/0.89/0.74), and the median (x2.3 key, x2.05 sky)
# lit the play frames to Lp50 0.46 in the arena (09, 12; rule 1's band 0.15-0.30, the picked night targets 0.20-0.27).
NIGHT_LEVEL_HOLD = True
NIGHT_SLOPE = 0.98  # (the night cards' slope, g18 to g50 in blue: 0.156 -> 0.424 over 0.18 -> 0.5)
SLOPE = 0.75  # (the cards' mean log-log slope of drawn over albedo, lit and shade, day and night: the refine's damping)


def solve(name="cards", night_name=None, refine=None):
    """NAME's cards for the day (and every rig), NIGHT_NAME's (when given) for the night, arena and dawn rigs."""
    cards = json.load(open(os.path.join(OUT, name, "cards.json")))
    sig = os.path.join(OUT, name, "day_rigs.sig")
    if not os.path.exists(sig) or open(sig).read().strip() != day_sig():
        sys.exit(f"color_chain solve: {name}'s cards were not measured under today's day rigs (day_town, day_wild): measure under a new NAME first (L1 l9: stale cards drifted the day key)")
    if night_name:
        nc = json.load(open(os.path.join(OUT, night_name, "cards.json")))
        for t in cards:
            for c in cards[t]:
                cards[t][c].update({k: v for k, v in nc.get(t, {}).get(c, {}).items() if not k.startswith("day_")})
    B = json.load(open(os.path.join(OUT, "boards.json")))
    rep = {"cards": name}
    # (2) the day fill: the boards' day shade/lit per channel, the median over the non-metal day swatches
    dm = [m for m in B if "day_ratio" in B[m] and B[m]["class"] not in METAL]
    rho = med([B[m]["day_ratio"] for m in dm])
    # (L7 S1c) the day key FROM the boards' sun (board_sun): the neutral card's sunlit side (the key and the sky's share on
    # it) is the boards' sun; per channel the lit side's gain (its luminance held: the key's strength stays the rig's) on the
    # 0.18 and 0.5 cards (the 0.8 card's lit side sits at the gamut's ceiling), the geometric mean
    bsun, bper = board_sun(B)
    k_lit = day_lit_gain(cards, bsun)
    k_day, now = shade_gain(cards, "day", rho, lit_gain=k_lit)
    # the key itself: the 0.18 card's lit side less its sky (the key-off cards) is the key's part, a per channel; the key that
    # draws the sun's color = (target - sky) / a, the sky as the fill solve leaves it
    lit18 = curve(cards, None, "day_play", "lit")[1][1]
    sky18 = np.median([cards["nokey"][c]["day_play"]["lit"] for c in DIFFUSE if c in cards.get("nokey", {})], 0) * k_day
    rk = json.load(open(RIGS_JSON, encoding="utf-8"))["rigs"]["day_town"]["key"]
    key_now = hex_to_lin(rk["color"]) * rk["intensity"]
    a_key = (lit18 - sky18 / k_day) / key_now
    key_new = (lit18 * k_lit - sky18) / a_key
    kk, q = key_new / key_now, sky18 / (lit18 * k_lit)
    rep["day"] = {"rho": rho.round(4).tolist(), "spread": spread([B[m]["day_ratio"] for m in dm], dm, rho), "swatches": dm,
                  "card_ratio_now": now.round(4).tolist(), "shade_gain": k_day.round(4).tolist(),
                  "lit_gain": k_lit.round(4).tolist(), "q": q.round(4).tolist(), "key_gain": np.maximum(kk, 0.05).round(4).tolist()}
    # (6) dawn: LB DAWN's setts, the same way
    k_dawn, now_d = shade_gain(cards, "dawn", np.array(B["lb_setts"]["dawn_ratio"]))
    rep["dawn"] = {"rho": B["lb_setts"]["dawn_ratio"], "card_ratio_now": now_d.round(4).tolist(), "shade_gain": k_dawn.round(4).tolist()}
    # (L7 S1c) one sun, the boards': the game is lit by the sun the boards were painted under, so the albedos come straight
    # off the boards under their own sun (W = 1; S1's adaptation to rule 3's #f3d9a0 made grey setts and lime grass)
    W = np.ones(3)
    rep["board_sun"] = {"from": list(BOARD_NEUTRAL), "chroma": bsun.round(4).tolist(), "hex": lin_to_hex(bsun / bsun.max()), "W": W.tolist(),
                        "per": {m: lin_to_hex(v / v.max()) for m, v in bper.items()},
                        "rb_gb": [round(float(bsun[0] / bsun[2]), 3), round(float(bsun[1] / bsun[2]), 3)]}
    # (3) each class's albedo: the board's day lit side through its card's day lit curve (the key's response, the grade's
    # inverse); a class two swatches give (setts: MB3 and LB; plank: MB3's beam and barrel) is their geometric mean
    alb, alb_rows = {}, {}
    for m in B:
        c = B[m]["class"]
        if c == "water": continue  # (the water is the FX helper's shader: bands of the sky, no albedo)
        if "day_lit" not in B[m] and "day_shade" in B[m]:
            # (L7 S1c) a class only a shade side gives (cloth: G1 07's sacks in the houses' shade): the albedo through the day
            # shade card's curve as the solved fill draws it (the shade light x k_day; under scene_color a light's gain is the drawn one)
            cs = curve(cards, c, "day_play", "shade")
            if cs is not None: alb_rows.setdefault(c, []).append((m, inv((cs[0], cs[1] * k_day), np.array(B[m]["day_shade"]))))
            continue
        cv = curve(cards, c, "day_play", "lit")
        if cv is None or "day_lit" not in B[m]: continue
        cv = (cv[0], cv[1] * k_lit)  # (L7 S1: the lit side as the solved key will draw it; under scene_color a light's gain is the drawn one)
        alb_rows.setdefault(c, []).append((m, inv(cv, np.array(B[m]["day_lit"]) * W)))
    for c, rows in alb_rows.items():
        a = np.exp(np.mean([np.log(np.maximum(r, 1e-5)) for _, r in rows], 0))
        alb[c] = {"linear": np.clip(a, 0.005, 0.9).round(4).tolist(), "hex": lin_to_hex(np.clip(a, 0.005, 0.9)),
                  "from": {m: np.round(r, 4).tolist() for m, r in rows}}
    # (L7 S1c) the closed-loop calibration (godot/data/look/calibration.json): a class's in-game lit read against its reference
    # (the picked targets where they show it), per channel, the kits' painting in it
    calp = os.path.join(DATA, "calibration.json")
    for c, x in (json.load(open(calp, encoding="utf-8"))["classes"].items() if os.path.exists(calp) else ()):
        if c not in alb: continue
        L, C, h = lab(alb[c]["linear"])
        a = np.clip(oklab_to_lin(L * x["L"], C * x["C"], h + (x["dh"] if C >= 0.02 else 0)), 0.005, 0.9)
        alb[c].update({"calibrated": {k: x[k] for k in ("L", "C", "dh")}, "linear": a.round(4).tolist(), "hex": lin_to_hex(a)})
    # (L7 S1c) a class no board shows undyed (cloth: the props' canvas, linen, sacking and rope; MB2's cloth is her navy) takes a
    # named neighbour's lightness at the undyed band's chroma and hue (lead 7: tan, h 60-80, C 0.03-0.05, never rose)
    for c, (src, C, h, why) in DERIVED.items():
        if src not in alb: continue
        L = lab(alb[src]["linear"])[0]; a = np.clip(oklab_to_lin(L, C, h), 0.005, 0.9)
        alb[c] = {"linear": a.round(4).tolist(), "hex": lin_to_hex(a), "from": {f"{src} L, C {C}, h {h}": why}}
    # the refine (one round, the relit check REFINE: the solved albedos drawn under the solved rigs): each class's albedo times
    # (board / drawn)^(1/SLOPE) per channel on its day lit sides, and the night gains times the median of the same over the
    # night swatches; a class whose own card the stage shades (its 0.18 card's lit 30%+ under the neutral card's) is not refined
    if refine:
        got = json.load(open(os.path.join(OUT, refine, "swatches.json")))
        neutral = curve(cards, None, "day_play", "lit")[1][1]
        for c in (alb if os.environ.get("CHAIN_REFINE_ALBEDO") else ()):  # (r2: the day lit sides met the boards in L; the night only)
            own = cards["g18"].get(c, {}).get("day_play", {}).get("lit")
            if c not in got or "day_play" not in got[c] or own is None or np.dot(own, bm.Y) < 0.7 * np.dot(neutral, bm.Y): continue
            fs = [(np.array(B[m]["day_lit"]) / np.maximum(got[c]["day_play"]["lit"], 1e-4)) ** (1 / SLOPE) for m in B if B[m]["class"] == c and "day_lit" in B[m]]
            f = np.clip(np.exp(np.mean(np.log(fs), 0)), 0.5, 2.0)  # (damped: a channel the grade crushed reads near 0)
            a = np.clip(np.array(alb[c]["linear"]) * f, 0.005, 0.9)
            alb[c].update({"refine": f.round(4).tolist(), "linear": a.round(4).tolist(), "hex": lin_to_hex(a)})
        rep["refine"] = {}
        for side in ("lit", "shade"):
            fs = [(np.array(B[m][f"night_{side}"]) / np.maximum(got[B[m]["class"]]["night_play"][side], 1e-4)) ** (1 / NIGHT_SLOPE)
                  for m in B if f"night_{side}" in B[m] and B[m]["class"] in got and "night_play" in got[B[m]["class"]] and B[m]["class"] != "water"]
            rep["refine"][f"night_{side}"] = med(fs).round(4).tolist()
    rep["albedo"] = alb
    # (4) the night: each night swatch's sides over its class's albedo, through the night cards' curves
    for rig in ("night", "arena"):
        out = {}
        for side in ("lit", "shade"):
            ks, names = [], []
            for m in B:
                c = B[m]["class"]
                cv = curve(cards, c, f"{rig}_play", side)
                if cv is None or c not in alb or f"night_{side}" not in B[m]: continue
                ks.append(inv(cv, np.array(B[m][f"night_{side}"])) / np.array(alb[c]["linear"])); names.append(m)
            if not ks: continue
            k = med(ks)
            if refine and rig == "night": k = k * np.array(rep["refine"][f"night_{side}"])
            out[side] = {"gain": k.round(4).tolist(), "spread": spread(ks, names, k), "swatches": names,
                         "per": {n: np.round(x, 3).tolist() for n, x in zip(names, ks)}}
        rep[rig] = out
    # (6, L7 S2) dawn FROM LB DAWN's setts over the setts albedo, the night's way (under scene_color the drawn ratios are the
    # light's): the shade light so the setts' shade draws LB's (its lilac, h ~325), the lit side the dawn sun's own color
    # (L1 l9: LB DAWN's own sun, dawn_sun; it was rule 3's pale gold #f3d9a0, lead 7's call, until lead 8's "the board wins") at LB's lit luminance
    if "setts" in alb and "dawn_lit" in B.get("lb_setts", {}):
        a = np.array(alb["setts"]["linear"]); cl, cs = curve(cards, None, "dawn_play", "lit"), curve(cards, None, "dawn_play", "shade")
        if cl is not None and cs is not None:
            k_sh = inv(cs, np.array(B["lb_setts"]["dawn_shade"])) / a
            dsun = dawn_sun(B, a); sun = hex_to_lin(dsun); want = sun / np.dot(bm.Y, sun) * np.dot(bm.Y, B["lb_setts"]["dawn_lit"])
            k_lit = inv(cl, want) / a
            rep["dawn"].update({"lit": {"gain": k_lit.round(4).tolist()}, "shade": {"gain": k_sh.round(4).tolist()},
                                "albedo": alb["setts"]["hex"], "sun": dsun, "lb_lit": B["lb_setts"]["dawn_lit"], "lb_shade": B["lb_setts"]["dawn_shade"]})
    json.dump(rep, open(os.path.join(OUT, "solve.json"), "w"), indent=1)
    print(json.dumps({k: (v if k != "albedo" else {c: x["hex"] for c, x in v.items()}) for k, v in rep.items()}, indent=None)[:6000])
    return rep


# ---- apply: the rigs ------------------------------------------------------------------------------------------------
RIGS_JSON = os.path.join(DATA, "rigs.json")


def scale_hex(h, k):
    return hex_to_lin(h) * np.asarray(k, float)


def write_json(path, d):
    import re
    s = json.dumps(d, indent=2, ensure_ascii=False)
    s = re.sub(r'\[\s+([-0-9.e,\s]*?)\s+\]', lambda m: '[' + re.sub(r'\s+', ' ', m.group(1)) + ']', s)
    open(path, "w", encoding="utf-8", newline="\n").write(s + "\n")


def shade_light(rig, base, k):
    """The rig's shade light (the fill's color and strength, the sky's and the ground's colors under one hemi and env)
    times k per channel: each color's top channel back to 1, its energy into the strength (fill) or hemi and env (sky)."""
    f = {**base.get("fill", {}), **{a: b for a, b in rig.get("fill", {}).items() if b is not None}}
    out, words = {}, []
    if f.get("color"):
        c, e = split_energy(scale_hex(f["color"], k)); e /= float(hex_to_lin(f["color"]).max())
        out["color"], out["strength"] = c, round(f["strength"] * e, 4)
        words.append(f"fill {f['color']} {f['strength']} -> {c} {out['strength']}")
    if f.get("sky"):
        sky = scale_hex(f["sky"], k); m = float(sky.max()); e = m / float(hex_to_lin(f["sky"]).max())
        out["sky"] = lin_to_hex(sky / m)
        if f.get("ground"): out["ground"] = lin_to_hex(scale_hex(f["ground"], k) / m)
        if f.get("hemi") is not None: out["hemi"] = round(f["hemi"] * e, 4)
        if f.get("env") is not None: out["env"] = round(f["env"] * e, 4)
        words.append(f"sky {f['sky']} ground {f.get('ground')} hemi {f.get('hemi')} env {f.get('env')} -> {out['sky']} {out.get('ground')} {out.get('hemi')} {out.get('env')}")
    return out, "; ".join(words)


def key_gain(cards, rig, k_lit, k_sh):
    """The key's own gain: the lit side is key + shade light, so key x kk + shade x k_sh = (key + shade) x k_lit, with the
    shade's share q of the lit side's light read on the neutral 0.5 card (its shade drawn, read back through the lit curve)."""
    cl, cs = curve(cards, None, f"{rig}_play", "lit"), curve(cards, None, f"{rig}_play", "shade")
    q = inv(cl, cs[1][2]) / 0.5
    q = np.clip(q, 0, 0.9)
    return (k_lit - k_sh * q) / (1 - q), q


def wild_key(cards, face="top"):
    """(L7 S1d) day_wild's light from its own grey cards: one sun (lead 7), so the open ground's lit response in the wild is the
    town's. The neutral cards' TOP face (the ground's lie) at the play camera, under 'wild' (lookdev's wild rig, the Verge's
    day_wild) against 'day' (day_town), the 0.18 and 0.5 cards: the albedo that draws the town's luminance on the wild's curve
    over the card's own is the light the wild lacks (k). None when the cards have no wild."""
    def top(rig):
        rows = []
        for c in DIFFUSE:
            try: rows.append([np.dot(bm.Y, cards[t][c][f"{rig}_play"]["faces"][face]) for t in TAGS])
            except KeyError: pass
        return np.median(np.array(rows), 0) if rows else None
    yd, yw = top("day"), top("wild")
    if yd is None or yw is None: return None
    ks = [np.exp(np.interp(np.log(yd[i]), np.log(np.sort(yw)), np.log(LV[np.argsort(yw)]))) / LV[i] for i in (1, 2)]
    return {"k": round(float(np.exp(np.mean(np.log(ks)))), 4), "top_day": np.round(yd, 4).tolist(), "top_wild": np.round(yw, 4).tolist()}


def apply_wild(cards):
    """(L7 S1d) day_wild's key and sky x wild_key's k (rigs.json), with its FROM: the whole light, so the wild keeps its own
    shade share (its open sky, its canopy) and only its level meets the town's."""
    w = wild_key(cards)
    if w is None: print("no wild cards"); return None
    d = json.load(open(RIGS_JSON, encoding="utf-8")); r = d["rigs"]["day_wild"]; k = w["k"]; f = r.setdefault("fill", {})
    old = f"key {r['key']['intensity']}, fill {f.get('strength')}, hemi {f.get('hemi')}, env {f.get('env')}"
    r["key"]["intensity"] = round(r["key"]["intensity"] * k, 4)
    for a in ("strength", "hemi", "env"):
        if f.get(a) is not None: f[a] = round(f[a] * k, 4)
    r["from"] += (f" L7 S1d (one sun, lead 7: the open ground's lit response in the wild is the town's; color_chain.py wild_key): the neutral cards' "
                  f"top face at the play camera read {w['top_wild']} (0.05/0.18/0.5/0.8, luminance) under wild against {w['top_day']} under day_town: "
                  f"the whole light x{k} (the wild's own shade share kept): {old} -> key {r['key']['intensity']}, fill {f.get('strength')}, hemi {f.get('hemi')}, env {f.get('env')}.")
    write_json(RIGS_JSON, d); print("day_wild:", old, "->", r["key"]["intensity"], f, w); return w


def apply_rigs(rep, cards, night=True, day=True):
    d = json.load(open(RIGS_JSON, encoding="utf-8")); R = d["rigs"]
    tag = "C6 (the color chain, tools/look/color_chain.py; godot/data/look/swatches.json; rules 2-4)"
    if day: apply_day(R, rep, tag)
    if not night:  # (L7 S1: `all` wrote the day only until S2 fixed the night solve (scene_color by night))
        write_json(RIGS_JSON, d); print("rigs.json written (day):", {k: {a: R[k].get(a) for a in ("key", "fill")} for k in ("day_town", "day_wild")}); return
    apply_night(R, rep, cards, tag)
    apply_dawn(R, rep, cards, tag)
    write_json(RIGS_JSON, d)
    print("rigs.json written:", {k: {a: R[k].get(a) for a in ("key", "fill")} for k in ("day_town", "day_wild", "night_play", "arena_night", "night_town", "night_wild", "dawn")})


def apply_day(R, rep, tag):
    # day: the fill FROM the boards' shade/lit
    k = np.array(rep["day"]["shade_gain"])
    kk = np.array(rep["day"].get("key_gain", [1, 1, 1]))
    for name in ("day_town", "day_wild"):
        base = R["day_town"] if name == "day_wild" else {}
        # (L7 S1) the key: its color x key_gain (top channel back to 1, the energy into the intensity); the wild keeps the
        # town's color (its base) and its own intensity times the same energy
        key = R[name]["key"]; kc = key.get("color") or kc0
        if name == "day_town": kc0 = kc
        # (L1 l9 DAY, judge 1 fix 2: the key's color IS the boards' sun, rule 3; the solve gives its energy only. The sky's
        # violet on the lit side stays: it is the boards' painted look, and solving it out warmed the key to h 66.)
        kc_new = rep["board_sun"]["hex"]
        e = float(np.dot(bm.Y, scale_hex(kc, kk))) / float(np.dot(bm.Y, hex_to_lin(kc_new)))  # (the key's luminance x the solve's)
        kwords = f"key {kc} {key.get('intensity')} -> {kc_new} {round(key['intensity'] * e, 4)}"
        if name == "day_town": key["color"] = kc_new
        key["intensity"] = round(key["intensity"] * e, 4)
        new, words = shade_light(R[name], base, k)
        if name == "day_wild": new = {a: b for a, b in new.items() if a in R[name].get("fill", {})}
        R[name].setdefault("fill", {}).update(new)
        R[name]["from"] += (f" {tag}: the shade FROM the boards: the median day shade/lit per channel over {len(rep['day']['swatches'])} day swatches "
                            f"{rep['day']['rho']} (spread {rep['day']['spread']['min']}-{rep['day']['spread']['max']}; outliers {', '.join(rep['day']['spread']['outliers'])}); "
                            f"the neutral 0.18 card's shade/lit was {rep['day']['card_ratio_now']}: the shade light x{rep['day']['shade_gain']} per channel: {words}. "
                            f"L7 S1c: the key FROM the boards' sun {rep['board_sun']['hex']} (read on {', '.join(rep['board_sun']['from'])}; lead 7, one sun), the neutral card's sunlit side that sun's color (under scene_color, the drawn ratios are the light's): "
                            f"the lit side x{rep['day'].get('lit_gain')}, the shade's share of it {rep['day'].get('q')}, so the key x{kk.round(4).tolist()}: {kwords}. "
                            f"The grade rig_day{'_wild' if name == 'day_wild' else ''}: the highlight tint neutral (the sun's color is the key's, rule 3).")


def apply_night(R, rep, cards, tag):
    # night: the moon FROM the boards over the classes' albedos, solved on night_play (the lookdev stage's play night)
    n = rep["night"]; k_lit, k_sh = np.array(n["lit"]["gain"]), np.array(n["shade"]["gain"])
    kk, q = key_gain(cards, "night", k_lit, k_sh); kk = np.maximum(kk, 0.05)
    r = R["night_play"]; key = r["key"]
    c, e = split_energy(scale_hex(key["color"], kk) * key["intensity"]); e /= float(hex_to_lin(key["color"]).max())
    old = f"{key['color']} {key['intensity']}"
    e_key = e / key["intensity"]
    key["color"], key["intensity"] = c, round(e, 4)
    new, words = shade_light(r, {}, k_sh)
    e_sky = new["hemi"] / r["fill"]["hemi"]
    if NIGHT_LEVEL_HOLD:  # (L7 S2) the boards give the night's colors, not its level: each light's energy kept
        key["intensity"] = round(e / e_key, 4); e_key = e_sky = 1.0
        for a_ in ("strength", "hemi", "env"):
            if r["fill"].get(a_) is not None: new[a_] = r["fill"][a_]
        words += " (energies held: NIGHT_LEVEL_HOLD)"
    r["fill"].update(new)
    n["key_gain"] = kk.round(4).tolist(); n["q"] = q.round(4).tolist(); n["key_energy"] = round(e_key, 4); n["sky_energy"] = round(e_sky, 4)
    a_ = rep.get("arena", {})
    r["from"] += (f" {tag}: the moon FROM the boards' night sides over the classes' albedos (one albedo serves day and night): the median gain "
                  f"lit {n['lit']['gain']} over {len(n['lit']['swatches'])} swatches (far off: {', '.join(n['lit']['spread']['outliers'])}), shade "
                  f"{n['shade']['gain']} over {len(n['shade']['swatches'])} (far off: {', '.join(n['shade']['spread']['outliers'])}); the shade's share of the "
                  f"lit side's light {n['q']} (the neutral 0.5 card), so the key x{n['key_gain']}: {old} -> {c} {key['intensity']}; "
                  f"the shade light x{n['shade']['gain']}: {words}. (The arena's own cards gave lit {a_.get('lit', {}).get('gain')}, shade "
                  f"{a_.get('shade', {}).get('gain')}: the red channel sits in the night grade's toe, 0.006-0.06 on the cards, where a gain is noise.)")
    # the arena, the town and the wild: the boards draw one moon, so night_play's derived colors, each rig's own energies
    # times night_play's energy gains (key x e_key, sky x e_sky); the arena's places keep their own moon strengths
    for name in ("arena_night", "night_town", "night_wild"):
        r = R[name]; old = f"{r['key'].get('color')} {r['key'].get('intensity')} sky {r['fill'].get('sky')} hemi {r['fill'].get('hemi')}"
        r["key"]["color"] = key["color"]
        if r["key"].get("intensity") is not None: r["key"]["intensity"] = round(r["key"]["intensity"] * e_key, 4)
        if r["fill"].get("sky") is not None: r["fill"]["sky"] = R["night_play"]["fill"]["sky"]
        if r["fill"].get("ground") is not None: r["fill"]["ground"] = lin_to_hex(scale_hex(r["fill"]["ground"], k_sh) / max(float(scale_hex(r["fill"]["ground"], k_sh).max()) / max(float(hex_to_lin(r["fill"]["ground"]).max()), 1e-6), 1))
        for f_ in ("hemi", "env"):
            if r["fill"].get(f_) is not None: r["fill"][f_] = round(r["fill"][f_] * e_sky, 4)
        r["from"] += (f" {tag}: the boards' one moon: night_play's derived key and sky colors, this rig's own energies x{n['key_energy']} (key) "
                      f"and x{n['sky_energy']} (sky): {old} -> {r['key']['color']} {r['key'].get('intensity')} sky {r['fill'].get('sky')} hemi {r['fill'].get('hemi')}"
                      + (" (the places keep their own moon strengths)" if name == "arena_night" else "") + ".")


def apply_dawn(R, rep, cards, tag):
    """(L7 S2) dawn FROM LB DAWN (solve's rep["dawn"]): one lilac shade light (the fill and the sky take LB's shade over the setts albedo as their color: under scene_color the drawn ratios are the light's) at the
    luminance that draws LB's shade, and the key rule 3's dawn sun (#f3d9a0) at the luminance that draws LB's lit side.
    dawn_morning's own key and fill colors follow (dawn_waystation is dawn's). Per channel gains on a purple fill and a
    blue sky made a mint sky and a pink fill that only summed to lilac on a card's side face (S2's first solve)."""
    n = rep.get("dawn", {})
    if "lit" not in n: print("no dawn solve"); return
    DAWN_SUN = n.get("sun", globals()["DAWN_SUN"])
    k_lit, k_sh = np.array(n["lit"]["gain"]), np.array(n["shade"]["gain"])
    cl, cs = curve(cards, None, "dawn_play", "lit"), curve(cards, None, "dawn_play", "shade")
    sh_now, lit_now = cs[1][1], cl[1][1]
    e_sh = float(np.dot(bm.Y, k_sh * sh_now) / np.dot(bm.Y, sh_now)); e_lit = float(np.dot(bm.Y, k_lit * lit_now) / np.dot(bm.Y, lit_now))
    q = float(np.clip(np.dot(bm.Y, sh_now) / np.dot(bm.Y, lit_now), 0, 0.9))  # (the shade light's luminance share of the lit side)
    e_key = max((e_lit - e_sh * q) / (1 - q), 0.05)
    shade_c = np.array(n["lb_shade"]) / hex_to_lin(n["albedo"]); shade_hex = lin_to_hex(shade_c / shade_c.max())
    words = []
    for name in ("dawn", "dawn_morning"):
        r = R[name]; key = r["key"]; f = r.setdefault("fill", {})
        if key.get("color"):
            old = f"{key['color']} {key['intensity']}"; Y0 = float(np.dot(bm.Y, hex_to_lin(key["color"]))); Y1 = float(np.dot(bm.Y, hex_to_lin(DAWN_SUN)))
            key["color"], key["intensity"] = DAWN_SUN, round(key["intensity"] * e_key * Y0 / Y1, 4); words.append(f"{name} key {old} -> {DAWN_SUN} {key['intensity']}")
        if f.get("color"):
            Y0 = float(np.dot(bm.Y, hex_to_lin(f["color"]))); Y1 = float(np.dot(bm.Y, hex_to_lin(shade_hex)))
            old = f"{f['color']} {f.get('strength')}"; f["color"] = shade_hex
            if f.get("strength") is not None: f["strength"] = round(f["strength"] * e_sh * Y0 / Y1, 4)
            words.append(f"{name} fill {old} -> {shade_hex} {f.get('strength')}")
        if f.get("sky"):
            Y0 = float(np.dot(bm.Y, hex_to_lin(f["sky"]))); Y1 = float(np.dot(bm.Y, hex_to_lin(shade_hex)))
            old = f"sky {f['sky']} ground {f.get('ground')} hemi {f.get('hemi')} env {f.get('env')}"; f["sky"] = shade_hex
            for a_ in ("hemi", "env"):
                if f.get(a_) is not None: f[a_] = round(f[a_] * e_sh * Y0 / Y1, 4)
            # (the hemisphere's ground side keeps its own bounce color, at the hemi's new energy)
            words.append(f"{name} {old} -> sky {f['sky']} ground {f.get('ground')} hemi {f.get('hemi')} env {f.get('env')}")
    n.update({"e_key": round(e_key, 4), "e_shade": round(e_sh, 4), "q": round(q, 4), "shade_light": shade_hex})
    R["dawn"]["from"] += (f" L7 S2 (color_chain.py apply_dawn, dawn FROM LB DAWN, chain step 6; under scene_color the drawn ratios are the light's): LB DAWN's setts "
                          f"lit {n['lb_lit']} and shade {n['lb_shade']} (linear; the shade lilac, Oklab h ~325) over the setts albedo {n['albedo']}: one lilac shade light "
                          f"{shade_hex} (fill and sky; the ground side its own bounce) x{n['e_shade']} in luminance; the key rule 3's dawn sun {n['sun']} x{n['e_key']} (the shade's share of the lit side {n['q']}): "
                          + "; ".join(words) + ".")


# ---- check: the solved albedos drawn on the stage (the relit check) -------------------------------------------------
def check(name="check_r1"):
    rep = json.load(open(os.path.join(OUT, "solve.json")))
    B = json.load(open(os.path.join(OUT, "boards.json")))
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    lib = json.load(open(calib.LIB, encoding="utf-8"))
    if not os.path.exists(os.path.join(d, "swatches.json")):
        f = os.path.join(d, "albedo.json")
        json.dump({c: f"{a['hex']} {0.45 if lib['classes'][c]['cel']['spec'][2] > 0 else 1.0}" for c, a in rep["albedo"].items()}, open(f, "w"))
        calib.OUT = OUT; calib.RIGS = ("day", "night")
        shoot(d, f, CARD_EXTRA, ("day", "night"))
        calib.measure(name)
    got = json.load(open(os.path.join(d, "swatches.json")))
    rows, out = [], {}
    Wd = np.array(rep.get("board_sun", {}).get("W", [1, 1, 1]))  # (L7 S1c: W = 1, the boards under their own sun)
    for m, r in B.items():
        c = r["class"]
        if c not in got: continue
        for light, rig in (("day", "day_play"), ("night", "night_play")):
            for side in ("lit", "shade"):
                if f"{light}_{side}" not in r or rig not in got[c]: continue
                ref = np.array(r[f"{light}_{side}"]) * (Wd if light == "day" else 1)
                g, b = lab(got[c][rig][side]), lab(ref)
                dE = float(np.hypot(g[0] - b[0], 2 * np.hypot(*(np.array(bm.lin_to_lab5(np.array([got[c][rig][side]]))[3:5]).ravel() - np.array(bm.lin_to_lab5(np.array([ref]))[3:5]).ravel()))))
                out.setdefault(m, {})[f"{light}_{side}"] = {"drawn": g, "board": b, "dE": round(dE, 3)}
                rows.append(dE)
                print(f"{m:9s} {light:5s} {side:5s} drawn L{g[0]:.2f} C{g[1]:.3f} h{g[2]:4d} | board L{b[0]:.2f} C{b[1]:.3f} h{b[2]:4d} | dE {dE:.3f}")
    print("median dE", round(float(np.median(rows)), 3))
    json.dump(out, open(os.path.join(d, "relit.json"), "w"), indent=1)


# ---- apply: the classes (materials.json), the ground (ground.json) -----------------------------------------------------
WORLD = ("setts", "plaster", "plank", "stone", "roof", "grass", "foliage", "rock", "road", "leather", "cloth")
CTL = {  # (6) the class marks, through albedo_ctl (cel.gdshaderinc cel_alb: L = min(mix(L, target, pull), cap), ab x chroma)
    "crowd_fur": ({"target": 0.30, "pull": 0.7, "cap": 0.40, "chroma": 1.0}, "rule 7: the pack mid-dark, never pale silver (it read pale silver in 09 and 12)"),
    "folk_cloth": ({"target": 0.0, "pull": 0.0, "cap": 0.75, "chroma": 1.0}, "the brief: the folk's white cloth capped at L 0.75"),
}
# (L7 S1) dropped: their cuts answered the day grade's chroma push (cloth drawn C 0.121 against MB2's 0.075; plaster's albedo
# pink through the too-warm key). Under scene_color the drawn color is the albedo's under the light, so a cut would dull them.
CTL_DROP = ("cloth", "plaster")


def apply_classes(rep):
    import re
    lib = json.load(open(calib.LIB, encoding="utf-8")); gains = {}
    for c in WORLD:
        if c not in rep["albedo"]: continue
        a = np.array(rep["albedo"][c]["linear"]); p = lib["classes"][c]["paint"].setdefault("albedo", {})
        old = p.get("mid"); gains[c] = a / np.maximum(hex_to_lin(old), 1e-4) if old else None
        L, C, h = lab(a)
        wL = (p["L"][2] - p["L"][0]) / 2 if "L" in p else 0.03; wC = (p["C"][2] - p["C"][0]) / 2 if "C" in p else 0.01
        p["L"] = [round(L - wL, 4), L, round(L + wL, 4)]; p["C"] = [round(max(0, C - wC), 4), C, round(C + wC, 4)]
        p["h"] = [h] + (p["h"][1:] if "h" in p else [0, 0])
        p["mid"] = rep["albedo"][c]["hex"]; p["linear"] = rep["albedo"][c]["linear"]; p["v"] = 4
        p["method"] = (f"L1 W2 C6 (tools/look/color_chain.py, the color chain): the boards' DAY lit side {rep['albedo'][c]['from']} (swatches.json; per swatch "
                       f"the neutral grey card's day lit curve inverted per channel, the grade in it; a class two swatches give is their geometric mean) "
                       f"-> {p['mid']} (lin {p['linear']}); one albedo serves day and night (the night rigs' moon is solved over it). Was {old}.")
    for c, (ctl, why) in CTL.items():
        lib["classes"][c]["albedo_ctl"] = dict(ctl, **{"from": f"L1 W2 C6: {why}"})
    for c in CTL_DROP: lib["classes"][c].pop("albedo_ctl", None)
    s = json.dumps(lib, indent=1, ensure_ascii=False)
    s = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]', lambda mm: '[' + re.sub(r'\s+', ' ', mm.group(1)) + ']', s)
    s = re.sub(r'"roles": \{\s+([^{}]*?)\s+\}', lambda mm: '"roles": {' + re.sub(r'\s+', ' ', mm.group(1)) + '}', s)
    open(calib.LIB, "w", encoding="utf-8", newline="\n").write(s + "\n")
    # the ground: each surface's colors times its class's gain (new albedo / old), so the painters' hand-set relations hold
    P = os.path.join(DATA, "ground.json"); g = json.load(open(P, encoding="utf-8"))
    gains["soil"] = gains.get("road")  # (the earth under the crowns takes the road's gain, as mark 6 did)
    for name, sf in g["surfaces"].items():
        k = gains.get(sf.get("class"))
        if k is None: continue
        def fix(x):
            if isinstance(x, str) and x.startswith("#") and len(x) == 7: return lin_to_hex(hex_to_lin(x) * k)
            if isinstance(x, list): return [fix(y) for y in x]
            if isinstance(x, dict): return {kk: (fix(v) if kk in ("colors", "under", "joint", "color", "lit", "shade") else v) for kk, v in x.items()}
            return x
        for kk in ("masses", "cells", "stamps", "patches"):
            if kk in sf: sf[kk] = fix(sf[kk])
        # (L7 S1b) the coursed setts (ground_paint.py courses; the town's setts arrays) never took the class: their colors were
        # hand-set by wave 2's town helper over the old day response (#5a4962, a purple). Now FROM the class's albedo: the first
        # stone is the class mid, the others and the joint keep their ratios to it (the painter's relations)
        cs = sf.get("courses")
        if cs and sf.get("class") in lib["classes"]:
            mid = hex_to_lin(lib["classes"][sf["class"]]["paint"]["albedo"]["mid"]); base = hex_to_lin(cs["colors"][0])
            cs["colors"] = [lin_to_hex(np.clip(mid * hex_to_lin(c) / np.maximum(base, 1e-4), 0, 0.9)) for c in cs["colors"]]
            cs["joint"] = lin_to_hex(np.clip(mid * hex_to_lin(cs["joint"]) / np.maximum(base, 1e-4), 0, 0.9))
            sf["c6"] = f"L7 S1b (the color chain): the courses FROM the {sf['class']} class's mid {lib['classes'][sf['class']]['paint']['albedo']['mid']}, the stones and joint at their ratios to the first."
    # (L7 S1d) the grass cards (grass_own.gdshader's atlas, ground_paint.py atlas; the lit grass in 04 and 07) never took the
    # class: their colors were hand-set by C1 (5 Nov). Now FROM the grass class's mid: the clump's body is the mid, the lit top
    # and the cool underside at their ratios to it (the painter's relations)
    ga = g.get("grass_atlas")
    if ga and "grass" in lib["classes"]:
        mid = hex_to_lin(lib["classes"]["grass"]["paint"]["albedo"]["mid"]); base = hex_to_lin(ga["colors"]["body"])
        ga["colors"] = {k: lin_to_hex(np.clip(mid * hex_to_lin(v) / np.maximum(base, 1e-4), 0, 0.9)) for k, v in ga["colors"].items()}
        ga["c6"] = f"L7 S1d (the color chain): the clump's body FROM the grass class's mid {lib['classes']['grass']['paint']['albedo']['mid']}, the lit top and the underside at their ratios to it."
        sf["c6"] = f"L1 W2 C6 (the color chain): x{np.round(k, 3).tolist()} per channel (linear) = the {sf['class']} class's chain albedo / its old mid (materials.json)."
    json.dump(g, open(P, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    print("classes:", {c: rep["albedo"][c]["hex"] for c in WORLD if c in rep["albedo"]}, "gains:", {c: np.round(v, 2).tolist() for c, v in gains.items() if v is not None})


def run_all(name=None):
    """(L7 S1) The chain in one command: fresh grey cards under today's rigs (NAME, default cards_<HEAD>), the boards, the
    solve, the apply, the relit check (check_NAME), then the kits' own builds (the ground's painted sets, the wild's and the
    town's paint from materials.json)."""
    if not name:
        name = "cards_" + subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    measure(name)
    boards()
    solve(name)
    rep = json.load(open(os.path.join(OUT, "solve.json")))
    apply_rigs(rep, json.load(open(os.path.join(OUT, name, "cards.json"))))
    apply_wild(json.load(open(os.path.join(OUT, name, "cards.json"))))
    apply_classes(rep)
    check("check_" + name)
    for cmd in (["ground_paint.py", "build", "all"], ["wild.py", "all", "--no-mesh"], ["town.py", "all", "--no-mesh"]):
        rc = subprocess.run([sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:]).returncode
        if rc != 0: print("FAILED", " ".join(cmd), rc); sys.exit(rc)
    subprocess.run([sys.executable, os.path.join(HERE, "ground_paint.py"), "check", "all"])
    # (L7 S1b) the rebuilt textures reach the game only through Godot's import: on 9 Nov the frames were shot with the
    # kits' old .ctex (house and roof sheets rebuilt at 01:24, imported 8 Nov 23:37), so the chain ends with one import
    turn = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
    subprocess.run([sys.executable, turn, "take", "godot", "chain import", "--wait", "30"])
    try:
        godot = os.environ.get("GODOT_CONSOLE", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
        print("import rc", subprocess.run([godot, "--headless", "--path", os.path.join(ROOT, "godot"), "--import"], capture_output=True).returncode)
    finally:
        subprocess.run([sys.executable, turn, "give", "godot", "chain import"])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    {"all": lambda: run_all(*a[1:2]), "measure": lambda: measure(*a[1:3]), "wild": lambda: apply_wild(json.load(open(os.path.join(OUT, a[1], "cards.json")))), "boards": boards, "solve": lambda: solve(*a[1:4]), "check": lambda: check(*a[1:2]), "night": lambda: apply_rigs(json.load(open(os.path.join(OUT, "solve.json"))), json.load(open(os.path.join(OUT, a[1], "cards.json"))), day=False), "apply": lambda: (apply_rigs(json.load(open(os.path.join(OUT, "solve.json"))), json.load(open(os.path.join(OUT, a[1] if len(a) > 1 else "cards", "cards.json")))), apply_classes(json.load(open(os.path.join(OUT, "solve.json")))))}[a[0]]()
