"""The material library's colors, measured from the boards (L1 B2; docs/design/LOOK_BIBLE.md rule 9).

    python tools/style/board_measure.py [--sheet OUT.jpg]

For each class in godot/data/look/materials.json, each box in its paint.boxes (board pixels x0,y0,x1,y1 on the board
the JSON's "boards" names, under survivorsunchained_inputs) is read as sRGB, converted to Oklab, and kept where its
optional mask holds (mask L, C as [lo, hi]; h as [lo, hi] degrees, Oklab hue; lit: true keeps the lit side, L at or
over the box's median, since a board paints its light and cast shade in and the class is the paint). The class's "lit" boxes (role lit or
transition; the chips' highlight and shade are recorded per role, not pooled) give paint.measured:
  L, C: the 10th, 50th and 90th percentiles; h: the circular mean and the 10th/90th percentile of the deviation from it
  (degrees); mid: the middle color (L50, C50, mean h) as sRGB hex, which the swatch row shows; n: pixels;
  roles: per role (highlight, lit, transition, shade) the same middle color, where a board gives that role.
ALBEDO (B2r2): a board paints its surfaces under its own light (the day row under a warm sun: plaster lit #fdbb8b), so
paint.lit is lit paint. paint.albedo is the same statistics on each kept pixel divided (in linear RGB) by that light's
color, from "lights" in the JSON: each panel of LB_light.png (night, dawn, day, arena; the same street under each light)
gives E, the mean linear color of its lit neutral references (gray setts and limewashed plaster in the sun or the pool,
the lit side of each box), scaled to luminance 1: the light's color is divided out, its strength stays the rig's (B4).
Each board row names its panel ("rows"); a row with neutral references of its own ("refs") takes the panel of its kind
("candidates": a sun row the sun panels) whose E is nearest its own (the log-chromaticity distance, printed), so the
match is measured. A class with "emissive" (a light
source) keeps albedo = lit. Nothing is measured by eye or from the game's textures; re-run this after moving a box. --sheet draws every box on its
board crop (magenta) with the measured middle color beside it, for checking the boxes sit on their swatches.
"""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(ROOT, "godot", "data", "look", "materials.json")
INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"


def srgb_to_oklab(rgb):
    c = rgb / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(lin @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ m2.T


def oklab_to_hex(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    lin = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
    out = []
    for v in lin:
        v = min(max(v, 0.0), 1.0)
        out.append(round(255 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)))
    return "#%02x%02x%02x" % tuple(out)


def pixels(img, bx):
    x0, y0, x1, y1 = bx["box"]
    rgb = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.float64).reshape(-1, 3)
    lab = srgb_to_oklab(rgb)
    L, a, b = lab[:, 0], lab[:, 1], lab[:, 2]
    C, h = np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360
    keep = np.ones(len(L), bool)
    mask = bx.get("mask") or {}
    for k, v in mask.items():
        if k == "lit": continue
        x = {"L": L, "C": C, "h": h}[k]
        keep &= (x >= v[0]) & (x <= v[1])
    # (lit: the band's lit side only, L at or over the kept pixels' median: the board's cast shade is light, not paint)
    if mask.get("lit") and keep.any(): keep &= L >= np.median(L[keep])
    return L[keep], C[keep], h[keep], a[keep], b[keep], linear(rgb[keep])


Y = np.array([0.2126, 0.7152, 0.0722])


def linear(rgb):
    c = rgb / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_lab5(lin):
    """Linear RGB rows -> (L, C, h, a, b) as pixels() gives them (values over 1 kept: an albedo is clamped at the end)."""
    lin = np.clip(lin, 0.0, None)
    srgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    lab = srgb_to_oklab(srgb * 255.0)
    C, h = np.hypot(lab[:, 1], lab[:, 2]), np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    return lab[:, 0], C, h, lab[:, 1], lab[:, 2]


def light_of(img, refs):
    """A light's color E from neutral references: the mean linear color of each box's lit side, scaled to luminance 1."""
    ps = []
    for r in refs:
        x0, y0, x1, y1 = r["box"]
        lin = linear(np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.float64).reshape(-1, 3))
        y = lin @ Y
        ps.append(lin[y >= np.median(y)].mean(0))
    m = np.mean(ps, axis=0)
    return m / float(m @ Y)


def lights(lib, boards):
    """E per LB panel, and per board row its panel (measured where the row has neutral references). Writes them back."""
    li = lib["lights"]; lb = Image.open(os.path.join(INPUTS, lib["boards"][li["board"]]))
    for name, pn in li["panels"].items():
        pn["E"] = [round(float(v), 4) for v in light_of(lb, pn["refs"])]
    E = {k: np.array(v["E"]) for k, v in li["panels"].items()}
    for row in li["rows"]:
        if row.get("refs"):
            own = light_of(boards[row["board"]], row["refs"])
            d = {k: float(np.linalg.norm(np.log(own) - np.log(e))) for k, e in E.items() if k in row.get("candidates", E)}
            row["panel"] = min(d, key=d.get)
            row["match"] = {"own_E": [round(float(v), 4) for v in own], "distance": {k: round(v, 3) for k, v in sorted(d.items(), key=lambda kv: kv[1])}}
            print(f"light {row['board']} y{row['y']}: {row['panel']} ({row['match']['distance']})")
    return E


def panel_of(lib, board, box):
    xc, yc = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    for row in lib["lights"]["rows"]:
        x = row.get("x", [0, 1e9])
        if row["board"] == board and row["y"][0] <= yc < row["y"][1] and x[0] <= xc < x[1]: return row["panel"]
    raise SystemExit(f"no light row for {board} at y {yc}: add one to lights.rows")


def stats(L, C, h, a, b):
    if len(L) == 0: return None
    mh = math.degrees(math.atan2(float(np.mean(b)), float(np.mean(a)))) % 360
    dev = (h - mh + 180) % 360 - 180
    r = lambda x: [round(float(v), 4) for v in x]
    pL, pC, pd = np.percentile(L, [10, 50, 90]), np.percentile(C, [10, 50, 90]), np.percentile(dev, [10, 90])
    return {"L": r(pL), "C": r(pC), "h": [round(mh, 1), round(float(pd[0]), 1), round(float(pd[1]), 1)],
            "mid": oklab_to_hex(float(pL[1]), float(pC[1]), mh), "n": int(len(L))}


def main():
    lib = json.load(open(LIB, encoding="utf-8"))
    boards = {k: Image.open(os.path.join(INPUTS, v)) for k, v in lib["boards"].items()}
    E = lights(lib, boards)
    tiles = []
    for name, cls in lib["classes"].items():
        p = cls["paint"]
        p.pop("measured", None)
        pool, roles, apool, aroles = [], {}, [], {}
        for bx in p["boxes"]:
            px = pixels(boards[bx["board"]], bx)
            e = None if p.get("emissive") else E[panel_of(lib, bx["board"], bx["box"])]
            ax = px[:5] if e is None else lin_to_lab5(px[5] / e)
            roles.setdefault(bx["role"], []).append(px); aroles.setdefault(bx["role"], []).append(ax)
            if bx["role"] in ("lit", "transition"): pool.append(px); apool.append(ax)
            tiles.append((name, bx))
        cat = lambda ps: [np.concatenate([q[i] for q in ps]) for i in range(5)]
        for key, pl, rl in (("lit", pool, roles), ("albedo", apool, aroles)):
            if pl:
                m = stats(*cat(pl))
                m["roles"] = {r: stats(*cat(ps))["mid"] for r, ps in rl.items() if stats(*cat(ps))}
                p[key] = m
            else:
                p.pop(key, None)
    s = json.dumps(lib, indent=1)
    import re
    s = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]', lambda mm: '[' + re.sub(r'\s+', ' ', mm.group(1)) + ']', s)
    s = re.sub(r'"roles": \{\s+([^{}]*?)\s+\}', lambda mm: '"roles": {' + re.sub(r'\s+', ' ', mm.group(1)) + '}', s)
    open(LIB, "w", encoding="utf-8", newline="\n").write(s + "\n")
    for name, cls in lib["classes"].items():
        m, a = cls["paint"].get("lit"), cls["paint"].get("albedo")
        if m: print(f"{name:11s} lit L {m['L']} C {m['C']} h {m['h']} mid {m['mid']} n {m['n']} | albedo L {a['L']} C {a['C']} h {a['h']} mid {a['mid']}")
    if "--sheet" in sys.argv:
        out = sys.argv[sys.argv.index("--sheet") + 1]
        T = []
        for name, bx in tiles:
            x0, y0, x1, y1 = bx["box"]; pad = 60
            cr = boards[bx["board"]].convert("RGB").crop((x0 - pad, y0 - pad, x1 + pad, y1 + pad))
            ImageDraw.Draw(cr).rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), outline=(255, 0, 255))
            cr.thumbnail((200, 200))
            t = Image.new("RGB", (260, 215)); t.paste(cr, (0, 15))
            mid = (lib["classes"][name]["paint"].get("lit") or {}).get("mid", "#000000")
            ImageDraw.Draw(t).rectangle((205, 20, 255, 70), fill=mid)
            ImageDraw.Draw(t).text((2, 1), f"{name} {bx['board']} {bx['role']}", fill=(255, 255, 0))
            T.append(t)
        n = 6; sh = Image.new("RGB", (260 * n, 215 * ((len(T) + n - 1) // n)))
        for i, t in enumerate(T): sh.paste(t, ((i % n) * 260, (i // n) * 215))
        sh.save(out, quality=88); print(out)


if __name__ == "__main__":
    main()
