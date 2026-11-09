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
RIGS = ("day", "night", "dawn", "arena")
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
    print("cards:", {k: len(v) for k, v in cards.items()})


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


SUN = "#f3d9a0"  # (rule 3: the day and dawn sun, pale gold)
BOARD_NEUTRAL = ("rock", "stone", "lb_setts")  # (the boards' grey stones: their lit sides are the boards' sun)


def day_lit_gain(cards):
    """Per channel, the gain that takes the neutral cards' day lit side to the sun's own color at its luminance (0.18 and
    0.5 cards, the geometric mean)."""
    cl = curve(cards, None, "day_play", "lit"); sun = hex_to_lin(SUN); ks = []
    for lv in (1, 2):
        lit = cl[1][lv]; k = sun / np.maximum(lit, 1e-5)
        ks.append(k * np.dot(bm.Y, lit) / np.dot(bm.Y, k * lit))
    return np.exp(np.mean(np.log(ks), 0))


NIGHT_SLOPE = 0.98  # (the night cards' slope, g18 to g50 in blue: 0.156 -> 0.424 over 0.18 -> 0.5)
SLOPE = 0.75  # (the cards' mean log-log slope of drawn over albedo, lit and shade, day and night: the refine's damping)


def solve(name="cards", night_name=None, refine=None):
    """NAME's cards for the day (and every rig), NIGHT_NAME's (when given) for the night, arena and dawn rigs."""
    cards = json.load(open(os.path.join(OUT, name, "cards.json")))
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
    # (L7 S1) the day key FROM rule 3: the neutral card's sunlit side (the key and the sky's share on it) is the sun's own
    # color, #f3d9a0; per channel the lit side's gain (its luminance held: the key's strength stays the rig's) on the 0.18
    # and 0.5 cards (the 0.8 card's lit side sits at the gamut's ceiling), the geometric mean
    k_lit = day_lit_gain(cards)
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
    # (L7 S1) the boards' own sun, read on their near-neutral stones (MB4's rock, MB3's stone, LB's setts): its chromaticity
    # (luminance 1) is a peach gold (about #ffc296, Oklab h 57) against rule 3's pale gold #f3d9a0 (h 86). Divided through
    # rule 3's sun, every warm surface came out pink (plaster h 25, setts h 1). The boards are adapted to the rule's sun
    # (per channel, von Kries; the rule wins over a board, bible): each lit side x W = rule sun / board sun; the shade side
    # follows through rho (shade/lit), so the whole board is seen under rule 3's sun.
    def chrom(v): v = np.asarray(v, float); return v / np.dot(bm.Y, v)
    bsun = np.exp(np.mean([np.log(chrom(B[m]["day_lit"])) for m in BOARD_NEUTRAL], 0))
    W = chrom(hex_to_lin(SUN)) / bsun
    rep["board_sun"] = {"from": list(BOARD_NEUTRAL), "chroma": bsun.round(4).tolist(), "hex": lin_to_hex(bsun / bsun.max()), "W": W.round(4).tolist()}
    # (3) each class's albedo: the board's day lit side through its card's day lit curve (the key's response, the grade's
    # inverse); a class two swatches give (setts: MB3 and LB; plank: MB3's beam and barrel) is their geometric mean
    alb, alb_rows = {}, {}
    for m in B:
        c = B[m]["class"]
        if c == "water": continue  # (the water is the FX helper's shader: bands of the sky, no albedo)
        cv = curve(cards, c, "day_play", "lit")
        if cv is None or "day_lit" not in B[m]: continue
        cv = (cv[0], cv[1] * k_lit)  # (L7 S1: the lit side as the solved key will draw it; under scene_color a light's gain is the drawn one)
        alb_rows.setdefault(c, []).append((m, inv(cv, np.array(B[m]["day_lit"]) * W)))
    for c, rows in alb_rows.items():
        a = np.exp(np.mean([np.log(np.maximum(r, 1e-5)) for _, r in rows], 0))
        alb[c] = {"linear": np.clip(a, 0.005, 0.9).round(4).tolist(), "hex": lin_to_hex(np.clip(a, 0.005, 0.9)),
                  "from": {m: np.round(r, 4).tolist() for m, r in rows}}
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


def apply_rigs(rep, cards, night=True):
    d = json.load(open(RIGS_JSON, encoding="utf-8")); R = d["rigs"]
    tag = "C6 (the color chain, tools/look/color_chain.py; godot/data/look/swatches.json; rules 2-4)"
    # day: the fill FROM the boards' shade/lit
    k = np.array(rep["day"]["shade_gain"])
    kk = np.array(rep["day"].get("key_gain", [1, 1, 1]))
    for name in ("day_town", "day_wild"):
        base = R["day_town"] if name == "day_wild" else {}
        # (L7 S1) the key: its color x key_gain (top channel back to 1, the energy into the intensity); the wild keeps the
        # town's color (its base) and its own intensity times the same energy
        key = R[name]["key"]; kc = key.get("color") or kc0
        if name == "day_town": kc0 = kc
        kc_new = split_energy(scale_hex(kc, kk))[0]
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
                            f"L7 S1: the key FROM rule 3, the neutral card's sunlit side the sun's own {SUN} (under scene_color, the drawn ratios are the light's): "
                            f"the lit side x{rep['day'].get('lit_gain')}, the shade's share of it {rep['day'].get('q')}, so the key x{kk.round(4).tolist()}: {kwords}. "
                            f"The grade rig_day{'_wild' if name == 'day_wild' else ''}: the highlight tint neutral (the sun's color is the key's, rule 3).")
    if not night:  # (L7 S1: `all` writes the day; the night rigs' re-solve is lead 7's and S2's, run by `apply`)
        write_json(RIGS_JSON, d); print("rigs.json written (day):", {k: {a: R[k].get(a) for a in ("key", "fill")} for k in ("day_town", "day_wild")}); return
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
    write_json(RIGS_JSON, d)
    print("rigs.json written:", {k: {a: R[k].get(a) for a in ("key", "fill")} for k in ("day_town", "day_wild", "night_play", "arena_night", "night_town", "night_wild")})


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
    Wd = np.array(rep.get("board_sun", {}).get("W", [1, 1, 1]))  # (L7 S1: by day the boards as adapted to rule 3's sun)
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
    apply_rigs(rep, json.load(open(os.path.join(OUT, name, "cards.json"))), night=False)
    apply_classes(rep)
    check("check_" + name)
    for cmd in (["ground_paint.py", "build", "all"], ["wild.py", "all", "--no-mesh"], ["town.py", "all", "--no-mesh"]):
        rc = subprocess.run([sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:]).returncode
        if rc != 0: print("FAILED", " ".join(cmd), rc); sys.exit(rc)
    subprocess.run([sys.executable, os.path.join(HERE, "ground_paint.py"), "check", "all"])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    {"all": lambda: run_all(*a[1:2]), "measure": lambda: measure(*a[1:3]), "boards": boards, "solve": lambda: solve(*a[1:4]), "check": lambda: check(*a[1:2]), "apply": lambda: (apply_rigs(json.load(open(os.path.join(OUT, "solve.json"))), json.load(open(os.path.join(OUT, a[1] if len(a) > 1 else "cards", "cards.json")))), apply_classes(json.load(open(os.path.join(OUT, "solve.json")))))}[a[0]]()
