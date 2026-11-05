"""B3 round 3: each class's albedo AND the one day fill (its color and strength), solved together (L1 texture authoring;
docs/design/look/TEXTURE_AUTHORING.md "Round 3"). Round 2 matched only the lit side: the day fill (#6a5ce0 at 0.12) turned
the shade sides lilac at about 0.35 of white where the boards paint them at about 0.2, mauve to violet-blue.

The model, from the shader (cel.gdshaderinc cel_fill_add): the fill adds cel_fill * lum(key) * strength in the key's shade
band only, and cel_fill is the fill color's linear hue at luminance 1 (Atmosphere.Hue). So with phi = strength * hue (a
linear rgb vector), a class's lit face is a * R_lit and its shade face a * (S0 + M phi): S0 the shade under the sky alone
(fill 0), M (3x3) the fill's response, both read off white swatches (--b3-white colors) shot under four fills (none, and
three hues at 0.12; --rigs-file, day_town's fill only). Her skin's shade at the close camera takes the same form (H0 + Mh
phi) from the same four fills (her own shader, her own albedo: a constraint, not a sample). The solve: least squares in
Oklab over every class's day lit and shade samples on the boards (MB2-MB4, 07's shade), at the play and the close view,
the albedos (3 per class) and phi (3) together, with a soft-l1 loss (a board's odd sample does not drag the world's fill)
and penalties for rule 2: the world's day shade (the classes' modelled shade, chroma-weighted) h 240-310, her skin's
shade h 300-340, C 0.02+, 0.25 L under her lit band. The bands and grade are not linear, so the swatches are redrawn in
the solved colors under the solved fill, each face's drawn/predicted ratio kept as a correction, and solved again.

    bash wtlock.sh python tools/look/joint.py basis          -> b3r3/calib/{f0,fr,fg,fb} (white swatches) and her_{..}
    python tools/look/joint.py solve [ITER ...]              -> fill.json, materials.json paint.albedo v2 (joint), albedo.json
    bash wtlock.sh python tools/look/joint.py relit NAME     -> NAME: the swatches in the solved colors under the solved fill
                                                                (day; night with the stage's lamps off), measured and checked
    bash wtlock.sh python tools/look/joint.py her NAME       -> her close-up day bands under the solved fill (rigs.json as written)
    python tools/look/joint.py write                         -> the solved fill into godot/data/look/rigs.json (day_town)
"""
import json, os, re, subprocess, sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import calib  # noqa: E402
from calib import bm, lin_to_oklab, srgb_to_lin  # noqa: E402

ROOT = calib.ROOT
OUT = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1\b3r3\calib"
calib.OUT = OUT
RIGS = os.path.join(ROOT, "godot", "data", "look", "rigs.json")
DAY = "day_town"
BASIS = {"f0": ("#6a5ce0", 0.0), "fr": ("#ff4a4a", 0.12), "fg": ("#4aff4a", 0.12), "fb": ("#4a4aff", 0.12)}
WORLD = ("plank", "wrought", "stone", "plaster", "roof", "setts", "road", "soil", "rock", "bark", "grass", "foliage")
KEYS = ("day_play", "day_close")
LUM = np.array([0.2126, 0.7152, 0.0722])


def hex_lin(h): return srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]))


def hue(h):
    """Atmosphere.Hue: the fill color's linear rgb at luminance 1, its largest channel capped at 3."""
    v = hex_lin(h); v = v / max(float(v @ LUM), 1e-4); m = v.max()
    return v * (3 / m) if m > 3 else v


def phi_of(h, s): return hue(h) * s


def fill_of(phi):
    """phi back to the rig's (color, strength): strength its luminance, the color its hue (largest channel 1)."""
    v = phi / max(phi.max(), 1e-9)
    c = np.where(v <= 0.0031308, 12.92 * v, 1.055 * np.power(np.clip(v, 0, 1), 1 / 2.4) - 0.055)
    hx = "#%02x%02x%02x" % tuple(int(round(255 * x)) for x in np.clip(c, 0, 1))
    return hx, round(float(phi.max() / hue(hx).max()), 4)  # (the strength: phi over the hex's own hue, the cap included)


def rigs_file(name, color, strength):
    r = json.load(open(RIGS, encoding="utf-8"))
    r["rigs"][DAY]["fill"]["color"], r["rigs"][DAY]["fill"]["strength"] = color, strength
    os.makedirs(OUT, exist_ok=True)
    f = os.path.join(OUT, f"rigs_{name}.json"); json.dump(r, open(f, "w", encoding="utf-8"), indent=1)
    return f.replace("\\", "/")


def lookdev(out, rigs, extra):
    # (--stale-ok: the swatch row and her skin's bands measure this worktree's own rig and shaders, not her newest art)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "style", "lookdev.py"), "shoot", "--out", out, "--rigs", rigs, "--extra", extra, "--stale-ok"], check=False)


def shoot_swatches(name, rf, colors=None, rigs="day"):
    """The swatch row (white, or the given colors) under a rigs file; frames and the log under OUT/name."""
    out = os.path.join(OUT, name); os.makedirs(out, exist_ok=True)
    lib = json.load(open(calib.LIB, encoding="utf-8"))
    rough = lambda c: 0.45 if lib["classes"][c]["cel"]["spec"][2] > 0 else 1.0
    spec = {c: f"{(colors or {}).get(c, '#ffffff')} {rough(c)}" for c in lib["classes"] if colors is None or c in colors}
    sp = os.path.join(out, "swatch_colors.json"); json.dump(spec, open(sp, "w"), indent=1)
    lookdev(out, rigs, f"--lookdev-swatches --lookdev-fire 0 --lookdev-lamps 0 --b3-cams swatches --b3-albedo {sp} --rigs-file {rf}")
    shots, t0 = os.path.join(ROOT, "godot", ".shots"), os.path.getmtime(sp)
    for r in rigs.split(","):
        f = os.path.join(shots, f"lookdev_{r}_item_swatches_1.png")
        if os.path.exists(f) and os.path.getmtime(f) > t0: Image.open(f).save(os.path.join(out, f"lookdev_{r}_item_swatches.png"))
    return calib.measure(name)


def shoot_her(name, rf, masks=False):
    """Her close-up by day under a rigs file (the stage as the game has it: its fire at the rig's share); masks: the band
    and skin views too (B1c's method, work/b4/bands.py)."""
    base = os.path.join(OUT, name)
    lookdev(base, "day", f"--rigs-file {rf}")
    if masks:
        lookdev(base + "_band", "day", f"--rigs-file {rf} --cel-dbg band --ink off")
        lookdev(base + "_skin", "day", f"--rigs-file {rf} --cel-dbg skin --ink off")


def her_bands(name, mask_name):
    """Her skin's lit and shade at the close camera: (mean linear lit, mean linear shade, oklab stats)."""
    ld = lambda p: np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255
    on = ld(os.path.join(OUT, name, "lookdev_day_close.png"))
    band = ld(os.path.join(OUT, mask_name + "_band", "lookdev_day_close.png"))
    skin = ld(os.path.join(OUT, mask_name + "_skin", "lookdev_day_close.png"))
    sk = nd.binary_erosion(skin.mean(-1) > 0.5, iterations=3)
    bl = band.mean(-1); ref = np.percentile(bl[sk], 99)
    lit, sh = sk & (bl > 0.6 * ref), sk & (bl < 0.15 * ref)
    lin = srgb_to_lin(on)
    out = {}
    for k, m in (("lit", lit), ("shade", sh)):
        v = lin[m].mean(0); lab = lin_to_oklab(v)
        out[k] = dict(lin=v.round(5).tolist(), L=round(float(lab[0]), 3), C=round(float(np.hypot(*lab[1:])), 3),
                      h=round(float(np.degrees(np.arctan2(lab[2], lab[1])) % 360), 1), n=int(m.sum()))
    return out


def basis():
    for k, (c, s) in BASIS.items():
        rf = rigs_file(k, c, s)
        shoot_swatches(k, rf)
        shoot_her("her_" + k, rf, masks=(k == "f0"))


# ---- the model ------------------------------------------------------------------------------------------------------
def model():
    """Per class and key: R_lit, the shade face's S0 and M (3x3), from the four white runs; her shade H0, Mh."""
    W = {k: json.load(open(os.path.join(OUT, k, "swatches.json"))) for k in BASIS}
    P = np.stack([phi_of(*BASIS[k]) for k in ("fr", "fg", "fb")], 1)  # (columns: each run's phi)
    Pi = np.linalg.inv(P)
    m = {}
    for cls, d in W["f0"].items():
        for key in KEYS:
            if key not in d or any(key not in W[k].get(cls, {}) for k in BASIS): continue
            lf, sf = d[key]["lit_face"], d[key]["shade_face"]
            if any(sf not in W[k][cls][key]["faces"] for k in BASIS): continue
            S = {k: np.array(W[k][cls][key]["faces"][sf]) for k in BASIS}
            Lf = np.array(d[key]["faces"][lf])
            dS = np.stack([S[k] - S["f0"] for k in ("fr", "fg", "fb")], 1)
            m.setdefault(cls, {})[key] = dict(lit=Lf, S0=S["f0"], M=dS @ Pi, lit_face=lf, shade_face=sf)
    her = {k: her_bands("her_" + k, "her_f0") for k in BASIS}
    H0 = np.array(her["f0"]["shade"]["lin"])
    Mh = np.stack([np.array(her[k]["shade"]["lin"]) - H0 for k in ("fr", "fg", "fb")], 1) @ Pi
    return m, dict(lit=np.array(her["f0"]["lit"]["lin"]), H0=H0, M=Mh, runs=her)


def lab(v): return lin_to_oklab(np.maximum(v, 1e-7))


def hue_of(l): return float(np.degrees(np.arctan2(l[2], l[1])) % 360)


def solve(iters=()):
    lib = json.load(open(calib.LIB, encoding="utf-8"))
    boards = {k: Image.open(os.path.join(bm.INPUTS, v)) for k, v in lib["boards"].items()}
    S = calib.board_samples(lib, boards)
    m, her = model()
    # the corrections from relit runs (drawn / predicted, per face), the last run's
    corr = {}
    for it in iters:
        drawn = json.load(open(os.path.join(OUT, it, "swatches.json")))
        sol = json.load(open(os.path.join(OUT, it, "solved.json")))
        ph = np.array(sol["phi"])
        for cls, d in drawn.items():
            if cls not in m or cls not in sol["albedo"]: continue
            a = np.array(sol["albedo"][cls])
            for key in KEYS:
                if key not in d or key not in m[cls]: continue
                mm = m[cls][key]; f = d[key]["faces"]
                for side, face, pred in (("lit", mm["lit_face"], a * mm["lit"]), ("shade", mm["shade_face"], a * (mm["S0"] + mm["M"] @ ph))):
                    if face in f:
                        k0 = corr.get((cls, key, side), np.ones(3))
                        corr[(cls, key, side)] = k0 * np.where(pred > 1e-3, np.array(f[face]) / np.maximum(pred, 1e-6), 1.0)
    classes = [c for c in lib["classes"] if c in S and c in m and not lib["classes"][c]["paint"].get("emissive")]
    rows = []  # (class index, key, side, board mean, weight, box index)
    for ci, c in enumerate(classes):
        for j, s in enumerate(S[c]):
            if s["rig"] != "day" or s["role"] not in ("lit", "shade"): continue
            for key in KEYS:
                if key in m[c]: rows.append((ci, key, s["role"], s["b"], 1.0, j))
    ph0 = phi_of("#6a5ce0", 0.12)

    def resp(ci, key, side, ph):
        mm = m[classes[ci]][key]
        r = mm["lit"] if side == "lit" else mm["S0"] + mm["M"] @ ph
        return r * corr.get((classes[ci], key, side), 1.0)

    def unpack(x):
        return np.exp(x[:3]), np.exp(x[3:]).reshape(-1, 3)

    def penalties(ph, A):
        out = []
        hs = lab(her["H0"] + her["M"] @ ph); hl = lab(her["lit"])
        h = hue_of(hs)
        out += [max(0, 300 - h) / 10, max(0, h - 340) / 10, max(0, 0.02 - float(np.hypot(*hs[1:]))) * 50, max(0, 0.25 - (hl[0] - hs[0])) * 20]
        # the world's day shade: the world classes' modelled shade at the play camera, chroma-weighted hue
        ws = [lab(A[ci] * resp(ci, "day_play", "shade", ph)) for ci, c in enumerate(classes) if c in WORLD and "day_play" in m[c]]
        a_, b_ = sum(w[1] for w in ws), sum(w[2] for w in ws)
        hw = float(np.degrees(np.arctan2(b_, a_)) % 360)
        out += [max(0, 240 - hw) / 10, max(0, hw - 310) / 10]
        return np.array(out), h, hw

    def f(x):
        ph, A = unpack(x)
        r = [(lab(A[ci] * resp(ci, key, side, ph)) - lab(b)) * w for ci, key, side, b, w, j in rows]
        return np.concatenate([np.concatenate(r), penalties(ph, A)[0]])

    # start: each class's lit-only albedo under the old fill
    A0 = []
    for ci, c in enumerate(classes):
        lr = [(b, resp(ci, key, side, ph0)) for cj, key, side, b, w, j in rows if cj == ci and side == "lit"] or \
             [(b, resp(ci, key, side, ph0)) for cj, key, side, b, w, j in rows if cj == ci]
        B = np.array([x[0] for x in lr]); R = np.array([x[1] for x in lr])
        A0.append(np.clip((B * R).sum(0) / np.maximum((R * R).sum(0), 1e-9), 0.008, 0.9))
    x0 = np.concatenate([np.log(np.maximum(ph0, 1e-4)), np.log(np.array(A0)).ravel()])
    lo = np.concatenate([np.full(3, np.log(1e-4)), np.full(3 * len(classes), np.log(0.008))])
    hi = np.concatenate([np.full(3, np.log(1.5)), np.full(3 * len(classes), np.log(0.9))])
    res = least_squares(f, np.clip(x0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss="soft_l1", f_scale=0.03, max_nfev=4000)
    ph, A = unpack(res.x)
    pen, hh, hw = penalties(ph, A)
    color, strength = fill_of(ph)
    # each class written through calib.finish (rule 4 clamps, the distribution), its rows the modelled responses
    alb_hex, report, solved = {}, {}, {}
    for ci, c in enumerate(classes):
        crow = [(b, resp(ci, key, side, ph), w, j) for cj, key, side, b, w, j in rows if cj == ci]
        p = lib["classes"][c]["paint"]
        mt, rp = calib.finish(c, p, A[ci], crow, S[c], f"B3r3 (tools/look/joint.py): the board's day lit and shade samples over the game's own response, "
                              f"solved with the day fill ({color} at {strength}) by least squares in Oklab at the play and close cameras")
        if mt is None: continue
        alb_hex[c] = mt["mid"]; solved[c] = mt["linear"]
        sh = [x for x in crow if S[c][x[3]]["role"] == "shade"]
        lt = [x for x in crow if S[c][x[3]]["role"] == "lit"]
        de = lambda xs: round(float(np.mean([np.linalg.norm(lab(np.array(mt["linear"]) * x[1]) - lab(x[0])) for x in xs])), 4) if xs else None
        rp.update(lit_dE=de(lt), shade_dE=de(sh), board_shade=bm.oklab_to_hex(*_lch(lab(np.mean([x[0] for x in sh], 0)))) if sh else None)
        report[c] = rp
    calib.write_lib(lib)
    tag = "_".join(iters) if iters else "white"
    sol = dict(phi=ph.round(5).tolist(), fill=dict(color=color, strength=strength), albedo=solved,
               her_shade_h=round(hh, 1), world_shade_h=round(hw, 1), penalties=pen.round(4).tolist(), cost=round(float(res.cost), 5),
               old_fill=dict(color="#6a5ce0", strength=0.12), iters=list(iters))
    json.dump(sol, open(os.path.join(OUT, f"solved_{tag}.json"), "w"), indent=1)
    json.dump(sol, open(os.path.join(OUT, "fill.json"), "w"), indent=1)
    json.dump(alb_hex, open(os.path.join(OUT, "albedo.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(OUT, f"report_{tag}.json"), "w"), indent=1)
    print(f"fill {color} at {strength} (phi {ph.round(4)}), model: her shade h {hh:.1f}, world shade h {hw:.1f}, penalties {pen.round(3)}")
    for k, v in report.items():
        print(f"{k:11s} board {v['board']} old {v['old']} new {v['new']} lit dE {v['lit_dE']} shade dE {v['shade_dE']} (board shade {v['board_shade']}) {v['clamp'] or ''}")
    return sol


def _lch(l): return float(l[0]), float(np.hypot(*l[1:])), hue_of(l)


def relit(name):
    """The swatches in the solved colors under the solved fill: day (the solve's correction run and the check) and night
    (the stage's lamps off); then calib's relit check with the shade side."""
    sol = json.load(open(os.path.join(OUT, "fill.json")))
    rf = rigs_file(name, sol["fill"]["color"], sol["fill"]["strength"])
    alb = json.load(open(os.path.join(OUT, "albedo.json")))
    shoot_swatches(name, rf, colors=alb, rigs="day,night")
    json.dump(sol, open(os.path.join(OUT, name, "solved.json"), "w"), indent=1)
    calib.check(name)


def her(name):
    """Her close-up day bands with rigs.json as written (after `write`), against rule 2 and 11."""
    rf = RIGS.replace("\\", "/")
    shoot_her(name, rf, masks=True)
    b = her_bands(name, name)
    ok = 300 <= b["shade"]["h"] <= 340 and b["shade"]["C"] >= 0.02 and b["lit"]["L"] - b["shade"]["L"] >= 0.25
    print(f"her day close: lit L {b['lit']['L']} h {b['lit']['h']} C {b['lit']['C']} | shade L {b['shade']['L']} h {b['shade']['h']} "
          f"C {b['shade']['C']} | dL {b['lit']['L'] - b['shade']['L']:.3f} {'OK' if ok else '--'}")
    json.dump(b, open(os.path.join(OUT, name, "bands.json"), "w"), indent=1)


def write():
    sol = json.load(open(os.path.join(OUT, "fill.json")))
    s = open(RIGS, encoding="utf-8").read()
    r = json.loads(s)
    old = r["rigs"][DAY]["fill"]
    c, k = sol["fill"]["color"], sol["fill"]["strength"]
    pat = re.compile(r'("' + DAY + r'": \{.*?"fill": \{ "color": ")(#[0-9a-f]{6})(", "strength": )([0-9.]+)', re.S)
    s2, n = pat.subn(lambda mm: mm.group(1) + c + mm.group(3) + f"{k}", s, count=1)
    assert n == 1, "day_town fill not found"
    note = (f" B3r3 (tools/look/joint.py): the fill solved with every class's albedo over the boards' lit and shade samples "
            f"(MB2-MB4, 07's shade): {old['color']} {old['strength']} to {c} {k} (the shade sides at the boards' share of the lit).")
    s2 = s2.replace('"day_town": {\n      "from": "', '"day_town": {\n      "from": "', 1)
    i = s2.index('"day_town"'); j = s2.index('"from": "', i) + len('"from": "'); e = s2.index('",\n', j)
    if "B3r3" not in s2[j:e]: s2 = s2[:e] + note + s2[e:]
    json.loads(s2)
    open(RIGS, "w", encoding="utf-8", newline="\n").write(s2)
    print(f"rigs.json day_town fill {old['color']} {old['strength']} -> {c} {k}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == "basis": basis()
    elif a[0] == "solve": solve(tuple(a[1:]))
    elif a[0] == "relit": relit(a[1])
    elif a[0] == "her": her(a[1])
    elif a[0] == "write": write()
    else: print(__doc__)
