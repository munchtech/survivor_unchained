"""B3 round 2: each class's albedo through the game's own rig (L1 texture authoring; docs/design/look/TEXTURE_AUTHORING.md
"Albedo v2"). Round 1's paint.albedo divided each board's color by a light guessed from its "gray" setts and plaster, which
the boards paint warm, so the classes came out lilac and pale. Here the light is the game's: each class's swatch is drawn
at albedo 1 under the day and night rigs (the lookdev stage's swatch row, --lookdev-swatches --b3-white, the stage's fire
off: the boards' day row has none and their night panels are moonlit), at the play camera and the close view's (the
per-item camera, --b3-cams swatches); its lit and shade faces give the class's response R (linear RGB) per rig and camera.
The albedo is then the board's sample over that response, per channel, solved by least squares over every sample the
boards give of it (the lit side under the day sun,
the shade chips where a board gives them; a moonlit sample only where a board paints the class by night alone: the
others' moonlit samples are the relit check's), so the albedo answers the day as the boards paint it. The shading is not
linear (bands, grade, clipping at albedo 1), so the solve is iterated: the swatches redrawn in the solved colors
(--b3-albedo), each sample's response re-read as drawn/albedo, and solved again.

    bash wtlock.sh python tools/look/calib.py shoot NAME [--albedo FILE.json]   -> b3r2/calib/NAME (frames, log)
    python tools/look/calib.py measure NAME          -> NAME/swatches.json (each class's faces per rig and camera)
    python tools/look/calib.py solve RESP [PREV]     -> materials.json paint.albedo v2 (RESP the white run; PREV a relit
                                                        run whose drawn colors refine the response) and b3r2/calib/albedo.json
    python tools/look/calib.py check NAME            -> NAME/relit.json: per class the Oklab difference, lit side, drawn
                                                        against the board, per rig (the relit check: at most 0.04)
"""
import json, os, re, shutil, subprocess, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "style")); sys.path.insert(0, HERE)
import board_measure as bm  # noqa: E402
from paint_core import lin_to_oklab, srgb_to_lin  # noqa: E402

OUT = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1\b3r2\calib"
LIB = os.path.join(ROOT, "godot", "data", "look", "materials.json")
RIGS = ("day", "night")
PANEL_RIG = {"day": "day", "moon": "night"}  # (the boards' lights the game's rigs stand for; lantern and arena pools are fires)
TOWN = ("plank", "stone", "plaster", "roof", "setts", "road", "soil", "rock", "bark", "iron")  # (rule 4's surfaces)


def shoot(name, albedo=None):
    out = os.path.join(OUT, name); os.makedirs(out, exist_ok=True)
    # (each class drawn as B3's painted maps draw it: metallic 0, the painter's roughness; white for the response)
    lib = json.load(open(LIB, encoding="utf-8"))
    alb = json.load(open(albedo)) if albedo else {}
    rough = lambda c: 0.45 if lib["classes"][c]["cel"]["spec"][2] > 0 else 1.0
    spec = {c: f"{alb.get(c, '#ffffff')} {rough(c)}" for c in lib["classes"] if (albedo is None or c in alb)}
    sp = os.path.join(out, "swatch_colors.json"); json.dump(spec, open(sp, "w"), indent=1)
    extra = f"--lookdev-swatches --lookdev-fire 0 --b3-cams swatches --b3-albedo {sp}"
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "style", "lookdev.py"), "shoot", "--out", out, "--rigs", ",".join(RIGS), "--extra", extra], check=False)
    shots = os.path.join(ROOT, "godot", ".shots")
    for r in RIGS:
        f = os.path.join(shots, f"lookdev_{r}_item_swatches_1.png")
        if os.path.exists(f): shutil.copy2(f, os.path.join(out, f"lookdev_{r}_item_swatches.png"))


# ---- the log: swatches and each frame's camera -------------------------------------------------------------------
def parse_log(path):
    sw, frame, cams, last = {}, None, {}, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        w = ln.split()
        if not w: continue
        if w[0] == "b3-swatch" and len(w) >= 6: sw[w[1]] = np.array([float(v) for v in w[2:5]])
        elif w[0] == "b3-swatch-frame": frame = [float(v) for v in w[1:6]]
        elif w[0] == "saved":
            m = re.search(r"lookdev_(\w+?)_1\.png", ln); last = m.group(1) if m else None
        elif w[0] == "camera" and last:
            v = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", ln.split("fov")[0])]
            fov = float(ln.split("fov")[1])
            B = np.array(v[:9]).reshape(3, 3).T  # (columns X, Y, Z)
            cams[last] = (B, np.array(v[9:12]), fov); last = None
    return sw, frame, cams


def project(P, cam, W=1920, H=1080):
    B, O, fov = cam
    q = (P - O) @ B  # (camera space: x right, y up, -z forward)
    f = (H / 2) / np.tan(np.radians(fov) / 2)
    z = -q[..., 2]
    return np.stack([W / 2 + f * q[..., 0] / z, H / 2 - f * q[..., 1] / z], -1), z


def faces(c, R, F, h=0.25):
    U = np.array([0, 1.0, 0])
    return {"top": (U, R, F), "+r": (R, U, F), "-r": (-R, U, F), "+f": (F, U, R), "-f": (-F, U, R)}


def occluded(O, P, boxes, own):
    """Whether the ray from the lens to P passes through another swatch first (boxes in the stage frame)."""
    d = P - O; L = np.linalg.norm(d); d = d / L
    for k, (c, R, F) in boxes.items():
        if k == own: continue
        M = np.stack([R, np.array([0, 1.0, 0]), F])
        o, dd = M @ (O - c), M @ d
        with np.errstate(divide="ignore", invalid="ignore"):
            t1, t2 = (-0.25 - o) / dd, (0.25 - o) / dd
        tn, tf = np.nanmax(np.minimum(t1, t2)), np.nanmin(np.maximum(t1, t2))
        if tn <= tf and 0 < tn < L - 0.02: return True
    return False


def measure(name):
    d = os.path.join(OUT, name)
    sw, fr, cams = parse_log(os.path.join(d, "run", "logs", "lookdev.log"))
    R = np.array([fr[0], 0, fr[1]]); F = np.array([fr[2], 0, fr[3]])
    boxes = {k: (c, R, F) for k, c in sw.items()}
    res = {}
    for rig in RIGS:
        for cam in ("play", "item_swatches"):
            tag = f"{rig}_{cam}"; f = os.path.join(d, f"lookdev_{tag}.png")
            if tag not in cams or not os.path.exists(f): print("no", tag); continue
            img = srgb_to_lin(np.asarray(Image.open(f).convert("RGB"), np.float64) / 255)
            camk = "close" if cam != "play" else "play"
            for cls, c in sw.items():
                out = {}
                for fn, (n, s, t) in faces(c, R, F).items():
                    fc = c + n * 0.25
                    O = cams[tag][1]
                    if (O - fc) @ n < 0.15 * np.linalg.norm(O - fc): continue
                    pts = np.array([fc + u * s + v * t for u in (-0.11, 0, 0.11) for v in (-0.11, 0, 0.11)])
                    px, z = project(pts, cams[tag])
                    vals = []
                    for (x, y), zz, P in zip(px, z, pts):
                        if zz <= 0 or not (3 <= x < 1917 and 3 <= y < 1077) or occluded(O, P, boxes, cls): continue
                        vals.append(np.median(img[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3].reshape(-1, 3), 0))
                    if len(vals) >= 5:
                        v = np.array(vals); med = np.median(v, 0)
                        # (a label or a seam under a point: the points far from the face's median left out)
                        ok = np.abs(v - med).max(1) <= 0.25 * med.max() + 0.01
                        if ok.sum() >= 5: out[fn] = v[ok].mean(0).round(5).tolist()
                if len(out) >= 2:
                    Y = {k: np.dot(v, bm.Y) for k, v in out.items()}
                    lit, sh = max(Y, key=Y.get), min(Y, key=Y.get)
                    res.setdefault(cls, {})[f"{rig}_{camk}"] = {"lit": out[lit], "shade": out[sh], "faces": out, "lit_face": lit, "shade_face": sh}
    json.dump(res, open(os.path.join(d, "swatches.json"), "w"), indent=1)
    print(f"{len(res)} classes measured in {name}")
    return res


# ---- the boards' samples ------------------------------------------------------------------------------------------
def board_samples(lib, boards):
    """Per class: each box's (role, rig, mean linear color, the box's kept pixels in linear) by the box's light."""
    out = {}
    for name, cls in lib["classes"].items():
        p = cls.get("paint", {})
        for bx in p.get("boxes", []):
            panel = bx.get("panel") or bm.panel_of(lib, bx["board"], bx["box"])
            px = bm.pixels(boards[bx["board"]], bx)
            if len(px[5]) == 0: continue
            out.setdefault(name, []).append(dict(role=bx["role"], rig=PANEL_RIG.get(panel), panel=panel, b=px[5].mean(0), px=px, box=bx))
    return out


SIDE = {"lit": "lit", "lit_night": "lit", "shade": "shade"}  # (transition and highlight chips: in the spread, not the solve)


def solve(resp_name, prev_name=None):
    lib = json.load(open(LIB, encoding="utf-8"))
    boards = {k: Image.open(os.path.join(bm.INPUTS, v)) for k, v in lib["boards"].items()}
    white = json.load(open(os.path.join(OUT, resp_name, "swatches.json")))
    prev = json.load(open(os.path.join(OUT, prev_name, "swatches.json"))) if prev_name else {}
    prev_alb = json.load(open(os.path.join(OUT, "albedo.json"))) if prev_name else {}
    S = board_samples(lib, boards)
    alb_hex, report = {}, {}
    for name, cls in lib["classes"].items():
        p = cls.get("paint", {})
        if name not in S or name not in white: continue
        if p.get("emissive"): continue
        rows = []  # (board mean, response, weight, box index)
        day_any = any(s["rig"] == "day" and s["role"] in SIDE for s in S[name])
        for j, s in enumerate(S[name]):
            if s["rig"] is None or s["role"] not in SIDE: continue
            # (the class's color is the boards' day paint where they give it: the moonlit samples are the relit check's,
            # since the game's night grade and the boards' moon panel need not keep the same ratio class by class)
            if day_any and s["rig"] != "day": continue
            for camk in ("play", "close"):
                key = f"{s['rig']}_{camk}"
                if key not in white[name]: continue
                r = np.array(white[name][key][SIDE[s["role"]]])
                if name in prev and key in prev[name] and name in prev_alb:
                    a0 = srgb_to_lin(np.array([int(prev_alb[name][i:i + 2], 16) / 255 for i in (1, 3, 5)]))
                    m = np.array(prev[name][key][SIDE[s["role"]]])
                    # (the drawn color over its albedo; a channel the grade crushed to black keeps the white run's)
                    r = np.where(m > 0.01, m / np.maximum(a0, 1e-4), r)
                rows.append((s["b"], r, 1.0, j))
        if not rows: continue
        B = np.array([x[0] for x in rows]); Rr = np.array([x[1] for x in rows]); wt = np.array([x[2] for x in rows])[:, None]
        a = (wt * B * Rr).sum(0) / np.maximum((wt * Rr * Rr).sum(0), 1e-9)
        a = np.clip(a, 0.008, 0.9)  # (an albedo is reflectance: under 1, and nothing black)
        clamp = []
        # rule 4: the town's surfaces stay weathered by day (the relit day lit side at C 0.07 or under, unless the board's
        # own lit paint is stronger: then the board's), and nothing goes acid (C 0.14 at most on a natural class)
        lab = lin_to_oklab(a)
        Cmax = 0.14 if name not in ("cloth", "satin", "gloss", "folk_cloth", "crowd_fur", "glass", "water", "skin", "folk_skin", "hair", "gold", "bronze") else 0.3
        if name in TOWN:
            dayr = [x for x in rows if S[name][x[3]]["rig"] == "day" and SIDE[S[name][x[3]]["role"]] == "lit"]
            if dayr:
                drawn = lin_to_oklab(np.mean([a * x[1] for x in dayr], 0)); bC = max(float(np.hypot(*lin_to_oklab(np.mean([x[0] for x in dayr], 0))[1:])), 0.07)
                dC = float(np.hypot(*drawn[1:]))
                if dC > bC + 1e-4:
                    k = bC / dC; lab = lab * [1, k, k]; clamp.append(f"rule 4: day C {dC:.3f} -> {bC:.3f}")
        if np.hypot(*lab[1:]) > Cmax:
            k = Cmax / np.hypot(*lab[1:]); lab = lab * [1, k, k]; clamp.append(f"C cap {Cmax}")
        from paint_core import oklab_to_lin
        a2 = np.clip(oklab_to_lin(lab), 0.008, 0.9)
        # the distribution: each lit box's kept pixels scaled so its mean lands on the albedo (its own spread kept)
        pool, roles = [], {}
        for s in S[name]:
            if s["role"] not in ("lit", "transition", "highlight", "shade"): continue
            if s["rig"] is None and not p.get("emissive"): continue
            ax = bm.lin_to_lab5(s["px"][5] * (a2 / np.maximum(s["b"], 1e-6)) if s["role"] in ("lit", "transition") else s["px"][5] * (a2 / np.maximum(s["b"], 1e-6)))
            roles.setdefault(s["role"], []).append(ax)
            if s["role"] in ("lit", "transition"): pool.append(ax)
        if not pool: continue
        cat = lambda ps: [np.concatenate([q[i] for q in ps]) for i in range(5)]
        m = bm.stats(*cat(pool))
        m["mid"] = bm.oklab_to_hex(*[float(v) for v in (lin_to_oklab(a2)[0], np.hypot(*lin_to_oklab(a2)[1:]), np.degrees(np.arctan2(lin_to_oklab(a2)[2], lin_to_oklab(a2)[1])) % 360)])
        m["roles"] = {r: bm.stats(*cat(ps))["mid"] for r, ps in roles.items()}
        resid = [float(np.linalg.norm(lin_to_oklab(a2 * x[1]) - lin_to_oklab(x[0]))) for x in rows]
        m["v"] = 2
        m["method"] = ("B3r2 (tools/look/calib.py): the board's samples over the game's own response, per channel, least "
                       "squares over the samples (rig_cam: side)" + (f"; clamped: {'; '.join(clamp)}" if clamp else ""))
        m["samples"] = sorted({f"{S[name][x[3]]['rig']} {S[name][x[3]]['role']}" for x in rows})
        m["linear"] = [round(float(v), 4) for v in a2]
        m["fit_dE"] = round(float(np.sqrt(np.mean(np.square(resid)))), 4)
        old = p.get("albedo", {}).get("mid")
        p["albedo"] = m
        alb_hex[name] = m["mid"]
        report[name] = dict(board=p.get("lit", {}).get("mid"), old=old, new=m["mid"], fit_dE=m["fit_dE"], clamp=clamp, samples=m["samples"])
    lib["what"] = lib["what"].replace("paint.albedo the same with the board's light divided out (lights; B2r2)",
                                      "paint.albedo (v2, B3r2) the board's samples over the game's own response to each class (tools/look/calib.py: the swatch row at albedo 1 under the day and night rigs, solved per channel, then iterated on the swatches redrawn in it)")
    s = json.dumps(lib, indent=1)
    s = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]', lambda mm: '[' + re.sub(r'\s+', ' ', mm.group(1)) + ']', s)
    s = re.sub(r'"roles": \{\s+([^{}]*?)\s+\}', lambda mm: '"roles": {' + re.sub(r'\s+', ' ', mm.group(1)) + '}', s)
    open(LIB, "w", encoding="utf-8", newline="\n").write(s + "\n")
    json.dump(alb_hex, open(os.path.join(OUT, "albedo.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(OUT, f"solve_{prev_name or resp_name}.json"), "w"), indent=1)
    for k, v in report.items(): print(f"{k:11s} board {v['board']} old {v['old']} new {v['new']} fit {v['fit_dE']} {v['clamp'] or ''}")


def check(name):
    """The relit check: each class's swatch drawn in its albedo, its lit side against the board's lit sample under the
    same light (Oklab, L a b), per rig (both cameras: the worse)."""
    lib = json.load(open(LIB, encoding="utf-8"))
    boards = {k: Image.open(os.path.join(bm.INPUTS, v)) for k, v in lib["boards"].items()}
    drawn = json.load(open(os.path.join(OUT, name, "swatches.json")))
    S = board_samples(lib, boards)
    out = {}
    for cls, ss in S.items():
        if cls not in drawn: continue
        for rig in RIGS:
            bl = [s["b"] for s in ss if s["rig"] == rig and s["role"] in ("lit", "lit_night")]
            if not bl: continue
            b = lin_to_oklab(np.mean(bl, 0))
            for camk in ("play", "close"):
                k = f"{rig}_{camk}"
                if k not in drawn[cls]: continue
                g = lin_to_oklab(np.array(drawn[cls][k]["lit"]))
                out.setdefault(cls, {})[k] = dict(dE=round(float(np.linalg.norm(g - b)), 4), dL=round(float(g[0] - b[0]), 3),
                                                  dC=round(float(np.hypot(*g[1:]) - np.hypot(*b[1:])), 3))
    json.dump(out, open(os.path.join(OUT, name, "relit.json"), "w"), indent=1)
    worst = {c: max(v.values(), key=lambda x: x["dE"]) for c, v in out.items()}
    n = sum(w["dE"] <= 0.04 for w in worst.values())
    for c, v in sorted(out.items(), key=lambda kv: -worst[kv[0]]["dE"]):
        print(f"{c:11s} " + "  ".join(f"{k} {x['dE']:.3f} (dL {x['dL']:+.3f} dC {x['dC']:+.3f})" for k, x in v.items()))
    print(f"relit: {n}/{len(worst)} classes within 0.04 at every rig and camera")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "shoot": shoot(a[1], a[a.index("--albedo") + 1] if "--albedo" in a else None)
    elif a[0] == "measure": measure(a[1])
    elif a[0] == "solve": solve(a[1], a[2] if len(a) > 2 else None)
    elif a[0] == "check": check(a[1])
    else: print(__doc__)
