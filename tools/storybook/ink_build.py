"""Build stage of ink_layers.py: post every layer with ink_post (one hand), cut RGBA layers,
glow layers, state candidates, layers.json, the contact sheet and the numeric checks."""
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

import ink_layers as L
import ink_post as IP


def soft(m, s=0.8):
    return np.clip(nd.gaussian_filter(m.astype(np.float32), s), 0, 1)


def up_alpha(a, W, H):
    return np.clip(np.asarray(Image.fromarray(a.astype(np.float32)).resize((W, H), Image.BICUBIC)), 0, 1)


class Plate:
    def __init__(self, plate):
        self.p = plate
        self.P = L.PLATES[plate]
        self.pick = L.pick(plate)
        self.h, self.w = self.pick.shape[:2]
        self.TW = self.P["target"]
        self.TH = round(self.h * self.TW / self.w)
        self.upp = L.COMPS[plate]["size"][0] / self.TW          # canvas units per target px
        self.ug = L.COMPS[plate]["size"][0] / self.w             # canvas units per gen px
        self._up = {}
        _, self.mg = L.fill_jobs(plate)
        self.M = {n: L.load_mask(L.wd(plate, f"M_{n}.png")) for n, _ in self.P["layers"]}

    def src(self, name):
        if name not in self._up:
            if name == "pick":
                im = Image.open(os.path.join(L.HERE, "out", self.P["src"]))
            else:
                im = Image.open(name if os.path.isabs(name) else L.wd(self.p, f"S_{name}.png"))
            self._up[name] = IP.upscale(im, self.TW, self.TH)
        return self._up[name]

    def ext(self, i):
        """The layer's mask plus its extension under the nearer layers (fill margin)."""
        names = [n for n, _ in self.P["layers"]]
        m = self.M[names[i]]
        nearer = np.zeros_like(m)
        for n in names[i + 1:]:
            nearer |= self.M[n]
        return m | ((nd.distance_transform_edt(~m) <= self.mg[i]) & nearer)

    def cutout(self, rgb_full, alpha_gen, opaque=False):
        """Upscale alpha, crop to it, post the crop with the paper at its place. -> (rgba float, x0, y0)."""
        if opaque:
            a = np.ones((self.TH, self.TW), np.float32)
            x0, y0, x1, y1 = 0, 0, self.TW, self.TH
        else:
            a = up_alpha(alpha_gen, self.TW, self.TH)
            ys, xs = np.nonzero(a > 0.004)
            x0, y0 = max(0, xs.min() - 4), max(0, ys.min() - 4)
            x1, y1 = min(self.TW, xs.max() + 5), min(self.TH, ys.max() + 5)
        rgb = IP.post(rgb_full[y0:y1, x0:x1], offset=(x0, y0))
        al = a[y0:y1, x0:x1]
        al = np.where(al < 0.004, 0, al)
        return np.dstack([rgb, al]), x0, y0


def glow(P, mask_gen, kind):
    m = up_alpha(mask_gen.astype(np.float32), P.TW, P.TH)
    s = P.TW / 2048
    if kind == "lamp_glare":
        g = nd.gaussian_filter(m, 10 * s) * 6 + nd.gaussian_filter(m, 45 * s) * 14 + nd.gaussian_filter(m, 130 * s) * 30
        ys, xs = np.nonzero(m > 0.5)
        cy, cx = ys.mean(), xs.mean()
        Y, X = np.mgrid[0:P.TH, 0:P.TW]
        # the glare swallows the chain: a tall soft plume from the flame to the top of the frame
        plume = np.exp(-((X - cx) / (55 * s)) ** 2) * np.clip((cy + 40 * s - Y) / (cy + 40 * s), 0, 1) ** 0.35 * (Y < cy + 40 * s)
        g = g / g.max() + 0.85 * plume
        return np.clip(g, 0, 1) * 0.95
    sig = {"lamps": (6, 30, 90), "fire_glow": (8, 35, 110), "reflection_blue": (5, 18, 50), "lamp_warped": (20, 60, 160)}[kind]
    g = sum(nd.gaussian_filter(m, a * s) * wt for a, wt in zip(sig, (1, 2.5, 5)))
    g = g / max(1e-6, np.percentile(g[m > 0.5], 90)) if (m > 0.5).any() else g
    peak = {"lamps": 0.4, "fire_glow": 0.6, "reflection_blue": 0.6, "lamp_warped": 0.3}[kind]
    return np.clip(g * peak, 0, 1)


def save_rgba(rgba, path):
    IP.save(rgba[..., :3], path, rgba[..., 3])


def over(base, rgba, x0, y0, add=False):
    h, w = rgba.shape[:2]
    reg = base[y0:y0 + h, x0:x0 + w]
    a = rgba[..., 3:4]
    if add:
        reg[:] = np.clip(reg + rgba[..., :3] * a, 0, 1)
    else:
        reg[:] = reg * (1 - a) + rgba[..., :3] * a


def checker(w, h, c=16):
    y, x = np.mgrid[0:h, 0:w]
    return np.where(((x // c + y // c) % 2)[..., None] == 0, 0.42, 0.30).repeat(3, -1).astype(np.float32)


def render(P, layers, cam, W=1920, H=1080, mode="rgb"):
    """The player's lens: every layer through the camera, back to front (bilinear)."""
    R = P.P["rest"]
    sy, sx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = (sx + 0.5 - W / 2) / (W / 2)
    v = (sy + 0.5 - H / 2) / (H / 2) / L.BAND           # v = +-1 at the band's edge
    out = np.zeros((H, W, 3), np.float32)
    bad = np.zeros((H, W), np.float32)
    for ly in layers:
        cxp, cyp = L.lens_point(R, cam, ly["z"], 0, 0)
        ex, _ = L.lens_point(R, cam, ly["z"], 1, 0)
        _, ey = L.lens_point(R, cam, ly["z"], 0, 1)
        px = (cxp + u * (ex - cxp)) / P.upp - ly["x0"]
        py = (cyp + v * (ey - cyp)) / P.upp - ly["y0"]
        img = ly["rgba"]
        inside = (px >= 0) & (py >= 0) & (px <= img.shape[1] - 1) & (py <= img.shape[0] - 1)
        ch = [nd.map_coordinates(img[..., c], [py, px], order=1, mode="constant", cval=0) for c in range(4)]
        a = (ch[3] * inside)[..., None]
        col = np.dstack(ch[:3])
        if ly["blend"] == "add":
            out = np.clip(out + col * a, 0, 1)
        else:
            out = out * (1 - a) + col * a
            if "valid" in ly:   # the backmost: where it shows outside its drawn/filled part
                vv = nd.map_coordinates(ly["valid"].astype(np.float32), [py, px], order=0, mode="constant", cval=0)
                bad = np.where(inside, 1 - vv, 1)
            else:
                bad = bad * (1 - a[..., 0])
    return out, bad


def label(im, text, xy=(6, 4)):
    d = ImageDraw.Draw(im)
    d.rectangle([xy[0] - 3, xy[1] - 2, xy[0] + 7 * len(text) + 3, xy[1] + 12], fill=(0, 0, 0))
    d.text(xy, text, fill=(255, 230, 120))


def to_im(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def build(plate):
    P = Plate(plate)
    out = os.path.join(L.OUT, plate)
    os.makedirs(out, exist_ok=True)
    names = [n for n, _ in P.P["layers"]]
    zs = dict(P.P["layers"])
    srcs = {"p5": {"sky": "sky", "far": "far", "trees": "clean", "road": "clean"},
            "p6": {"sky": "sky", "far": "far", "near": "clean"},
            "p7": {"far_water": "bg", "water": "bg", "lamp": "pick", "traveler": "pick"},
            "p7u": {"under": "bg", "bubbles": "pick"}}[plate]
    layers, files = [], []
    for i, n in enumerate(names):
        opaque = i == 0
        e = P.ext(i)
        if plate == "p7" and n == "lamp":          # the chain fades out above the cage: the glare holds it
            m = e.astype(np.float32)
            wid = m.sum(1)
            top = int(np.argmax(wid > 0.4 * wid.max()))
            ramp = np.clip((np.arange(P.h) - (top - 30)) / 30.0, 0, 1)[:, None]
            alpha = soft(e) * ramp
        else:
            alpha = soft(e)
        # the part a layer owns is the clean drawing itself; fills only where it runs under nearer layers
        own = up_alpha(soft(P.M[n], 1.5), P.TW, P.TH)[..., None]
        base = P.src("clean" if plate in ("p5", "p6") else "pick")
        rgb = base * own + P.src(srcs[n]) * (1 - own)
        rgba, x0, y0 = P.cutout(rgb, alpha, opaque)
        ly = dict(name=n, z=zs[n], blend="mix", rgba=rgba, x0=x0, y0=y0, state=None)
        if opaque:
            if plate in ("p5", "p6"):
                ly["valid"] = up_alpha((nd.distance_transform_edt(~P.M[n]) <= P.mg[0]).astype(np.float32), P.TW, P.TH) > 0.5
            else:
                ly["valid"] = np.ones((P.TH, P.TW), bool)
        layers.append(ly)
    # states
    states = []
    sl = P.P["state_layer"]
    if plate == "p5":
        reg = L.load_mask(L.wd(plate, "state_region.png"))
        for s in L.SEEDS:
            st = L.wd(plate, f"st_drowned_s{s}.png")
            d = np.asarray(Image.open(L.wd(plate, f"st_drowned_s{s}_depth.png")).convert("L")).astype(np.float32)
            fig = L.figures_by_depth(d, 0.40, ~nd.binary_dilation(reg, iterations=6)) & nd.binary_dilation(reg, iterations=6)
            states.append(("drowned", s, st, soft(fig)))
    elif plate == "p6":
        person = L.load_mask(os.path.join(L.WORK, "p6_sam_person.png"))
        states.append(("sit", 0, "pick", soft(nd.binary_dilation(person, iterations=1))))
        for k in L.P6_STATES:
            reg = L.load_mask(L.wd(plate, f"state_{k}.png"))
            for s in L.SEEDS:
                fig = L.load_mask(L.wd(plate, f"st_{k}_s{s}_person.png")) & reg
                states.append((k, s, L.wd(plate, f"st_{k}_s{s}.png"), soft(fig)))
    elif plate == "p7":
        head = L.load_mask(L.wd(plate, "state_head_up.png"))
        trav = P.M["traveler"]
        for s in L.SEEDS:
            fig = L.load_mask(L.wd(plate, f"st_head_up_s{s}_person.png"))
            a = np.where(head, fig | (trav & ~L.load_mask(os.path.join(L.WORK, "p7_sam_person.png"))), trav)
            states.append(("head_up", s, L.wd(plate, f"st_head_up_s{s}.png"), soft(a)))
    st_layers = []
    for k, s, src, a in states:
        if a.max() < 0.5:
            print(plate, "state", k, s, "empty cut: no figure found, skipped")
            continue
        rgba, x0, y0 = P.cutout(P.src(src), a)
        st_layers.append(dict(name=sl[0], z=sl[1], blend="mix", rgba=rgba, x0=x0, y0=y0, state=k, seed=s))
    # glows
    gl = []
    for gname, gz, col in P.P["glows"]:
        m = L.load_mask(L.wd(plate, f"glow_{gname}.png"))
        g = glow(P, m, gname)
        ys, xs = np.nonzero(g > 0.004)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        c = np.array([int(col[j:j + 2], 16) for j in (0, 2, 4)], np.float32) / 255
        rgba = np.dstack([np.broadcast_to(c, (y1 - y0, x1 - x0, 3)), g[y0:y1, x0:x1]])
        gl.append(dict(name=gname, z=gz, blend="add", rgba=rgba, x0=x0, y0=y0, state=None))
    # ---- files + layers.json
    rec = []
    for ly in layers + st_layers + gl:
        f = ly["name"] + (f"_{ly['state']}" if ly["state"] else "") + (f"_s{ly['seed']}" if ly.get("seed") else "") + ".png"
        save_rgba(ly["rgba"], os.path.join(out, f))
        rec.append(dict(file=f, name=ly["name"], z=ly["z"], blend=ly["blend"], state=ly["state"], seed=ly.get("seed"),
                        pos=[round(ly["x0"] * P.upp, 1), round(ly["y0"] * P.upp, 1)], scale=round(P.upp, 5),
                        size_px=[ly["rgba"].shape[1], ly["rgba"].shape[0]]))
    # ---- checks
    ref = IP.post(P.src("pick"))
    IP.save(ref, os.path.join(out, "_posted_whole.png"))
    comp = np.zeros_like(ref)
    for ly in layers:
        over(comp, ly["rgba"], ly["x0"], ly["y0"])
    excl = np.zeros((P.h, P.w), bool)
    for f in ("remove.png",):
        if os.path.exists(L.wd(plate, f)):
            excl |= nd.binary_dilation(L.load_mask(L.wd(plate, f)), iterations=4)
    keep = up_alpha((~excl).astype(np.float32), P.TW, P.TH) > 0.99
    diff = np.abs(comp - ref).mean(-1)[keep] * 255
    checks = {"mean_abs_diff_255": round(float(diff.mean()), 3), "p99_abs_diff_255": round(float(np.percentile(diff, 99)), 2),
              "compared_fraction": round(float(keep.mean()), 3), "keys": []}
    base_rest = comp.copy()
    default = [x for x in st_layers if x["seed"] == L.SEEDS[0] or x["state"] in ("sit",)][:1]
    allv = sorted(layers + ([d for d in st_layers if d["state"] in ("sit",)] or default) + gl, key=lambda d: -d["z"])
    for g in gl:
        over(comp, g["rgba"], g["x0"], g["y0"], add=True)
    for d in ([x for x in st_layers if x["state"] == "sit"] or default):
        over(comp, d["rgba"], d["x0"], d["y0"])
    W0, H0 = P.TW * P.upp, P.TH * P.upp
    key_renders = []
    for cam in P.P["cams"]:
        wins = []
        for n, z in P.P["layers"] + ([sl] if sl else []):
            a, b = L.lens_point(P.P["rest"], cam, z, -1, -1), L.lens_point(P.P["rest"], cam, z, 1, 1)
            wins.append(min(a[0], a[1], W0 - b[0], H0 - b[1]))
        _, bad = render(P, allv, cam, 480, 270)
        band = np.abs((np.arange(270) + 0.5 - 135) / 135) <= L.BAND
        rgb, _ = render(P, allv, cam, 640, 360)
        key_renders.append((cam, rgb))
        checks["keys"].append({"cam": cam, "min_edge_clearance_units": round(min(wins)), "unfilled_px_fraction": round(float((bad[band] > 0.5).mean()), 5)})
    lay_json = dict(plate=plate, title=L.COMPS[plate]["title"], source=P.P["src"], canvas_units=L.COMPS[plate]["size"],
                    image_px=[P.TW, P.TH], units_per_px=round(P.upp, 5), rest=P.P["rest"],
                    lens_note="pos/scale in comps canvas units, painted as seen from 'rest'; wiring into sb00.json shifts pos and camera keys by (1600,900)-rest",
                    fill_margin_units=[round(m * P.ug) for m in P.mg], checks=checks, layers=rec)
    json.dump(lay_json, open(os.path.join(out, "layers.json"), "w", encoding="utf-8"), indent=1)
    # ---- the 1:1 crop (p5 at its zoom-1.6 opening)
    if plate == "p5":
        rgb, _ = render(P, allv, (1880, 700, 1.6, 0.15))
        to_im(rgb).save(os.path.join(out, "crop_1to1_zoom1.6.png"))
    # ---- contact sheet ~1600 wide
    SW = 1600
    rows = []
    r0 = to_im(comp).resize((SW, round(P.TH * SW / P.TW)), Image.LANCZOS)
    label(r0, f"{plate} recomposited at rest (layers + glows + default state)   diff vs posted whole: mean {checks['mean_abs_diff_255']}/255")
    rows.append(r0)
    kw = SW // len(key_renders) - 4
    kr = Image.new("RGB", (SW, round(kw * 9 / 16) + 4), (30, 30, 30))
    for j, (cam, rgb) in enumerate(key_renders):
        im = to_im(rgb).resize((kw, round(kw * 9 / 16)), Image.LANCZOS)
        label(im, f"key x{cam[0]} y{cam[1]} zoom{cam[2]} dolly{cam[3]}")
        kr.paste(im, (j * (kw + 4), 0))
    rows.append(kr)
    cells = [(ly["name"] + (" (add)" if ly["blend"] == "add" else ""), ly) for ly in layers + gl]
    cw = SW // len(cells) - 4
    lr = Image.new("RGB", (SW, round(cw * P.TH / P.TW) + 4), (30, 30, 30))
    for j, (t, ly) in enumerate(cells):
        bg = checker(P.TW, P.TH, 48)
        if ly["blend"] == "add":
            bg[:] = 0.05
            over(bg, ly["rgba"], ly["x0"], ly["y0"], add=True)
        else:
            over(bg, ly["rgba"], ly["x0"], ly["y0"])
        im = to_im(bg).resize((cw, round(cw * P.TH / P.TW)), Image.LANCZOS)
        label(im, f"{t} z{ly['z']}")
        lr.paste(im, (j * (cw + 4), 0))
    rows.append(lr)
    if st_layers:
        groups = {}
        for d in st_layers:
            groups.setdefault(d["state"], []).append(d)
        for k, ds in groups.items():
            ys = [d["y0"] for d in ds] + [d["y0"] + d["rgba"].shape[0] for d in ds]
            xs = [d["x0"] for d in ds] + [d["x0"] + d["rgba"].shape[1] for d in ds]
            x0, x1, y0, y1 = max(0, min(xs) - 40), min(P.TW, max(xs) + 40), max(0, min(ys) - 40), min(P.TH, max(ys) + 40)
            if plate == "p6":       # show the whole walk lane
                x0, x1 = max(0, x0 - 300), min(P.TW, x1 + 300)
            n = len(ds)
            cwid = (SW - 4 * (n - 1)) // n
            ch = round(cwid * (y1 - y0) / (x1 - x0))
            sr = Image.new("RGB", (SW, ch + 4), (30, 30, 30))
            for j, d in enumerate(ds):
                bg = base_rest.copy()
                for g in gl:
                    over(bg, g["rgba"], g["x0"], g["y0"], add=True)
                over(bg, d["rgba"], d["x0"], d["y0"])
                im = to_im(bg[y0:y1, x0:x1]).resize((cwid, ch), Image.LANCZOS)
                label(im, f"{k} seed {d['seed']}" if d["seed"] else k)
                sr.paste(im, (j * (cwid + 4), 0))
            rows.append(sr)
    S = Image.new("RGB", (SW, sum(r.height + 6 for r in rows)), (20, 20, 20))
    y = 0
    for r in rows:
        S.paste(r, (0, y))
        y += r.height + 6
    S.save(os.path.join(L.OUT, f"sheet_{plate}.jpg"), quality=88)
    print(plate, json.dumps(checks))
