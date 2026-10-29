"""Ink round 2 (Storybook 3): the GPU steps that replace round 1's failed parts.

    python tools/storybook/ink_r2.py slots      # CPU: p5 slot masks + an overlay on the pick (_work/p5/slots.jpg)
    python tools/storybook/ink_r2.py p5clean    # GPU: refill the right ditch's ghosts in S_clean (3 seeds -> clean_fix_s*.png)
    python tools/storybook/ink_r2.py p5apply N  # CPU: apply ghost-fix seed N to S_clean (+ S_far/S_sky where they were S_clean)
    python tools/storybook/ink_r2.py p5drowned  # GPU: (tried, failed) each ditch on a 2x crop, one mask per slot
    python tools/storybook/ink_r2.py p5frieze [seeds]  # GPU: a frieze of drowned figures per seed + SAM cut
    python tools/storybook/ink_r2.py p5place  [seeds]  # CPU: the frieze's figures into the slots -> st_drowned_s*.png (2x gen)
    python tools/storybook/ink_r2.py p7head     # GPU: head_up retry, generous mask, denoise 1.0, 4 seeds
Then `ink_layers.py build p5 p6 p7 p7u` (the build reads these outputs).
"""
import os
import shutil
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402


def slot_mask(shape, slots, grow=1.0):
    """Figure-shaped slots (head + body capsule), gen px."""
    H, W = shape
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for cx, fy, h in slots:
        h = h * grow
        bw = 0.42 * h
        d.rounded_rectangle([cx - bw / 2, fy - 0.80 * h, cx + bw / 2, fy + 0.04 * h], radius=bw * 0.45, fill=255)
        r = 0.15 * h
        d.ellipse([cx - r, fy - 0.99 * h, cx + r, fy - 0.99 * h + 2 * r], fill=255)
    return np.asarray(im) > 127


def cart():
    return nd.binary_dilation(L.load_mask(os.path.join(L.WORK, "p5_sam_wooden_cart.png")), iterations=10)


def p5_slots():
    H, W = L.pick("p5").shape[:2]
    c = cart()
    allm = np.zeros((H, W), bool)
    for k, sl in L.P5_SLOTS.items():
        m = nd.binary_dilation(slot_mask((H, W), sl), iterations=4) & ~c
        x0, y0, x1, y1 = L.P5_DITCHES[k]
        m[:, :x0] = 0
        m[:, x1:] = 0
        m[:y0] = 0
        L.save_mask(m, L.wd("p5", f"slots_{k}.png"))
        allm |= m
    L.save_mask(allm, L.wd("p5", "slots.png"))
    img = (L.pick("p5") * 255).astype(np.uint8)
    img[allm] = (img[allm] * 0.55 + np.array([255, 40, 40]) * 0.45).astype(np.uint8)
    img[c] = (img[c] * 0.6 + np.array([40, 255, 40]) * 0.4).astype(np.uint8)
    Image.fromarray(img[400:]).resize((1024, 344)).save(L.wd("p5", "slots.jpg"), quality=85)
    return allm


def sketch(base, slots, seed, face=0):
    """Paint drowned-body silhouettes into the slots, the init the img2img shapes: bare heads with long dark hair
    hanging to the chest, a narrow pale face turned toward the road, thin pale arms and hands, a soaked shift (dark
    or gray) with a ragged hem, thin legs into the water. (A bare figure-shaped latent mask comes back as a pale blob.)"""
    rng = np.random.default_rng(seed)
    im = Image.fromarray((base * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(im)
    hair, pale, wet = (10, 11, 18), (158, 172, 184), (8, 10, 16)
    for cx, fy, h in slots:
        cx += rng.normal(0, 0.03 * h)
        tilt = rng.normal(0, 0.03 * h) + face * 0.02 * h
        shift = (14, 16, 26) if rng.random() < 0.5 else (88, 98, 112)
        sh, wa, hem = 0.22 * h, 0.16 * h, 0.21 * h
        y_hem = fy - (0.24 + 0.05 * rng.random()) * h
        n = 7
        jag = [(cx + hem / 2 - hem * i / n, y_hem + (0.04 * h if i % 2 else 0) * rng.random()) for i in range(n + 1)]
        body = [(cx - sh / 2, fy - 0.78 * h), (cx + sh / 2, fy - 0.78 * h), (cx + wa / 2, fy - 0.50 * h)] + jag + [(cx - wa / 2, fy - 0.50 * h)]
        for sx in (-1, 1):       # thin legs into the water
            d.line([(cx + sx * 0.045 * h, y_hem), (cx + sx * 0.05 * h, fy)], fill=pale, width=max(2, int(0.04 * h)))
        d.polygon(body, fill=shift)
        for sx in (-1, 1):       # slack thin pale arms, the hands hanging
            d.line([(cx + sx * 0.12 * h, fy - 0.76 * h), (cx + sx * 0.14 * h, fy - 0.44 * h)], fill=pale, width=max(2, int(0.035 * h)))
            r = 0.028 * h
            d.ellipse([cx + sx * 0.14 * h - r, fy - 0.45 * h - r, cx + sx * 0.14 * h + r, fy - 0.45 * h + 1.6 * r], fill=pale)
        hx, hy = cx + tilt, fy - 0.89 * h
        d.polygon([(hx - 0.075 * h, hy - 0.02 * h), (hx - 0.09 * h, fy - 0.62 * h), (hx + 0.09 * h, fy - 0.62 * h), (hx + 0.075 * h, hy - 0.02 * h)], fill=hair)
        d.ellipse([hx - 0.075 * h, hy - 0.095 * h, hx + 0.075 * h, hy + 0.06 * h], fill=hair)
        fx = hx + face * 0.03 * h          # the face turned toward the road, between the hanging strands
        d.ellipse([fx - 0.03 * h, hy - 0.035 * h, fx + 0.03 * h, hy + 0.075 * h], fill=pale)
        d.rectangle([cx - 0.12 * h, fy - 0.09 * h, cx + 0.12 * h, fy + 0.02 * h], fill=wet)     # the water to the shins
    return np.asarray(im).astype(np.float32) / 255


def feather(m, s=1.2):
    return nd.gaussian_filter(m.astype(np.float32), s) * nd.binary_dilation(m, iterations=2)


def inpaint_crop(base, box, mask, prompt, seed, tag, scale=2, denoise=1.0, latent_mask=True):
    """Krea inpaint of base[box] at scale x; returns (patch at gen size float, 2x composite path)."""
    import ink_comfy as C
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * scale, (y1 - y0) * scale
    crop = Image.fromarray((base[y0:y1, x0:x1] * 255 + 0.5).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    mk = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)
    ip, mp = L.wd("p5", f"_in_{tag}.png"), L.wd("p5", f"_mk_{tag}.png")
    crop.save(ip)
    mk.save(mp)
    raw = L.wd("p5", f"raw2_{tag}_s{seed}.png")
    # latent_mask False: img2img of the whole crop, kept only inside the mask (narrow latent noise masks come back as
    # pale unfinished blobs with Krea turbo)
    C.krea(prompt, w, h, seed, raw, init=ip, denoise=denoise, mask=mp if latent_mask else None)
    big = L.composite_back(ip, raw, mp)
    bp = L.wd("p5", f"x2_{tag}_s{seed}.png")
    big.save(bp)
    small = np.asarray(big.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32) / 255
    return small, bp


def p5_clean(seeds=(31, 61, 89)):
    base = np.asarray(Image.open(L.wd("p5", "S_clean.png")).convert("RGB")).astype(np.float32) / 255
    rem = L.load_mask(L.wd("p5", "remove.png"))
    x0, y0, x1, y1 = L.P5_GHOST_BOX
    box = np.zeros_like(rem)
    box[y0:y1, x0:x1] = True
    # a broad soft-cornered patch over the whole bank, not the figures' shapes (a figure-shaped mask gets redrawn as a figure)
    m = nd.binary_dilation(nd.binary_dilation(rem & box, iterations=10) & box, iterations=14)
    m = nd.binary_closing(m, iterations=40) | nd.binary_fill_holes(nd.binary_closing(m, iterations=40))
    m &= np.arange(m.shape[0])[:, None] >= 528        # below the lamp posts
    L.save_mask(m, L.wd("p5", "ghost_fix.png"))
    crop = (1024, 448, 1536, 832)
    prompt = L.full("r3", L.P5_CLEAN_LOCAL)
    for s in seeds:
        t0 = time.time()
        small, _ = inpaint_crop(base, crop, m, prompt, s, "ghost")
        out = base.copy()
        f = feather(m)[crop[1]:crop[3], crop[0]:crop[2], None]
        out[crop[1]:crop[3], crop[0]:crop[2]] = out[crop[1]:crop[3], crop[0]:crop[2]] * (1 - f) + small * f
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(L.wd("p5", f"clean_fix_s{s}.png"))
        print("ghost", s, f"{time.time() - t0:.0f}s", flush=True)
    sheet = Image.new("RGB", (len(seeds) * 516, 388))
    for j, s in enumerate(seeds):
        sheet.paste(Image.open(L.wd("p5", f"clean_fix_s{s}.png")).crop(crop), (j * 516, 0))
    sheet.save(L.wd("p5", "clean_fix.jpg"), quality=85)


def p5_apply(seed):
    old_p = L.wd("p5", "S_clean.png")
    bak = L.wd("p5", "S_clean_r1.png")
    if not os.path.exists(bak):
        shutil.copy(old_p, bak)
    old = np.asarray(Image.open(bak).convert("RGB"))
    new = np.asarray(Image.open(L.wd("p5", f"clean_fix_s{seed}.png")).convert("RGB"))
    Image.fromarray(new).save(old_p)
    ch = (old != new).any(-1)
    for n in ("far", "sky"):
        p = L.wd("p5", f"S_{n}.png")
        b = L.wd("p5", f"S_{n}_r1.png")
        if not os.path.exists(b):
            shutil.copy(p, b)
        a = np.asarray(Image.open(b).convert("RGB")).copy()
        same = (a == old).all(-1) & ch
        a[same] = new[same]
        Image.fromarray(a).save(p)
        print(n, "patched px", int(same.sum()))
    print("S_clean patched px", int(ch.sum()))


def count(fig, min_px=150):
    lab, n = nd.label(fig)
    if not n:
        return 0
    return int((nd.sum(fig, lab, range(1, n + 1)) >= min_px).sum())


def p5_drowned(only=None):
    import ink_comfy as C
    H, W = L.pick("p5").shape[:2]
    base = np.asarray(Image.open(L.wd("p5", "S_clean.png")).convert("RGB")).astype(np.float32) / 255
    prompt = L.full("r3", L.P5_DROWNED_LOCAL)
    for s in (only or L.P5_SEEDS):
        dst = L.wd("p5", f"st_drowned_s{s}.png")
        if os.path.exists(dst):
            continue
        t0 = time.time()
        out = base.copy()
        fig = np.zeros((H, W), bool)
        for k, box in L.P5_DITCHES.items():
            m = L.load_mask(L.wd("p5", f"slots_{k}.png"))
            init = sketch(base, L.P5_SLOTS[k], s, 1 if k == "left" else -1)
            small, bp = inpaint_crop(init, box, m, prompt, s, f"d{k}", denoise=L.P5_DROWNED_DENOISE, latent_mask=False)
            x0, y0, x1, y1 = box
            f = feather(m)[y0:y1, x0:x1, None]
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - f) + small * f
            sp = L.wd("p5", f"sam_d{k}_s{s}.png")
            C.sam(bp, "person", sp, 0.3)
            sm = np.asarray(Image.open(sp).convert("L").resize((x1 - x0, y1 - y0), Image.BILINEAR)) > 127
            fig[y0:y1, x0:x1] |= sm & nd.binary_dilation(m, iterations=3)[y0:y1, x0:x1]
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(dst)
        L.save_mask(fig, L.wd("p5", f"st_drowned_s{s}_fig.png"))
        print("drowned", s, "figures", count(fig), f"{time.time() - t0:.0f}s", flush=True)


def frieze(seed):
    """GPU: one frieze of drowned figures per seed + its SAM 'person' mask (cached)."""
    import ink_comfy as C
    dst = L.wd("p5", f"frieze_s{seed}.png")
    if not os.path.exists(dst):
        C.krea(L.full("r3", L.P5_FRIEZE), *L.P5_FRIEZE_SIZE, seed, dst)
    mp = L.wd("p5", f"frieze_s{seed}_sam.png")
    if not os.path.exists(mp):      # BiRefNet: every figure (SAM 3 by text returned only one of the row)
        C.birefnet(dst, mp)
    return dst, mp


RAMP = [(0.0, (0.055, 0.051, 0.078)), (0.22, (0.110, 0.149, 0.259)), (0.42, (0.243, 0.306, 0.455)),
        (0.62, (0.408, 0.486, 0.557)), (0.86, (0.80, 0.84, 0.86))]      # black, navy, slate, snow, pale dead skin


def grade(rgb, hh):
    """Into the night: the drawing's lightness through the ink ramp; the big pale areas (the shifts) pushed down to
    slate/snow so only the faces, hands and arms stay pale."""
    l = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    pale = nd.binary_closing(l > 0.40, structure=np.ones((int(0.02 * hh) | 1,) * 2, bool))
    big = nd.binary_opening(pale, structure=np.ones((int(0.07 * hh),) * 2, bool))
    big[:int(0.15 * hh)] = False                          # the head stays
    k = 1 - 0.5 * np.clip(nd.gaussian_filter(big.astype(np.float32), 0.008 * hh), 0, 1)
    g = np.clip(l * k, 0, 1) ** 1.15
    xs = [p for p, _ in RAMP]
    return np.stack([np.interp(g, xs, [c[i] for _, c in RAMP]) for i in range(3)], -1).astype(np.float32)


def frieze_figures(seed):
    """The frieze's separate figures: [(rgb float, alpha float, facing -1/0/+1)], tallest first."""
    img = np.asarray(Image.open(L.wd("p5", f"frieze_s{seed}.png")).convert("RGB")).astype(np.float32) / 255
    m = np.asarray(Image.open(L.wd("p5", f"frieze_s{seed}_sam.png")).convert("L")) > 127
    H = m.shape[0]
    # the water and reflections join the figures at the feet: split by columns empty above the water
    occ = m[:int(0.80 * H)].sum(0) > 2
    runs, lab = [], np.zeros(m.shape, np.int32)
    xs = np.flatnonzero(np.diff(np.r_[0, occ.astype(np.int8), 0]))
    for i, (a0, a1) in enumerate(zip(xs[::2], xs[1::2])):
        lab[:, a0:a1][m[:, a0:a1]] = i + 1
    n = lab.max()
    out = []
    for i, sl in enumerate(nd.find_objects(lab)):
        c = lab[sl] == i + 1
        hh, ww = c.shape
        if hh < 0.45 * H or ww > 0.7 * hh or c.sum() < 0.08 * hh * ww:
            continue
        c = nd.binary_closing(c, iterations=2)      # no hole fill: the gaps by the arms are the frieze's black
        lab2, n2 = nd.label(c)             # the figure: its largest piece (no stray reflections)
        if n2 > 1:
            c = lab2 == 1 + int(np.argmax(nd.sum(c, lab2, range(1, n2 + 1))))
        rgb = grade(img[sl], hh)
        a = nd.gaussian_filter(c.astype(np.float32), 1.0)
        # facing: the pale face's offset from the head's centre (top 16%)
        top = int(0.16 * hh)
        lum = rgb[:top] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        w8 = (lum > 0.45) & c[:top]
        xs = np.nonzero(c[:top])[1]
        face = 0
        if w8.sum() > 20 and len(xs):
            off = np.nonzero(w8)[1].mean() - xs.mean()
            face = int(np.sign(off)) if abs(off) > 0.06 * ww else 0
        out.append((rgb, a, face, hh))
    out.sort(key=lambda f: -f[3])
    return [f[:3] for f in out]


def place(seed, scale=2):
    """The state image at scale x gen (clean plate + the frieze's figures, one per slot, far first) and its cut (gen px)."""
    base = Image.open(L.wd("p5", "S_clean.png")).convert("RGB")
    W, H = base.width * scale, base.height * scale
    canvas = np.asarray(base.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    alpha = np.zeros((H, W), np.float32)
    figs = frieze_figures(seed)
    if not figs:
        return None
    rng = np.random.default_rng(seed)
    slots = [(k, sl) for k in L.P5_SLOTS for sl in L.P5_SLOTS[k]]
    slots.sort(key=lambda t: t[1][1])            # far (high on the plate) first
    order = rng.permutation(len(slots))
    used = 0
    for j, (k, (cx, fy, h)) in enumerate(slots):
        rgb, a, face = figs[order[j] % len(figs)]
        toward = 1 if k == "left" else -1          # the road is right of the left ditch, left of the right one
        if face and face != toward or (not face and rng.random() < 0.5):
            rgb, a = rgb[:, ::-1], a[:, ::-1]
        th = int(h * scale * rng.uniform(0.96, 1.04))
        tw = max(2, int(rgb.shape[1] * th / rgb.shape[0]))
        r = np.asarray(Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).resize((tw, th), Image.LANCZOS)).astype(np.float32) / 255
        aa = np.clip(np.asarray(Image.fromarray(a).resize((tw, th), Image.LANCZOS)), 0, 1)
        # the shins in the ditch water: the figure fades out at the water line
        wl = int(th * (1 - L.P5_WATER))
        ramp = np.clip((np.arange(th) - wl) / max(1, 0.05 * th), 0, 1)[:, None]
        aa = aa * (1 - ramp)
        x0, y0 = int(cx * scale - tw / 2), int(fy * scale - th * (1 - L.P5_WATER * 0.6))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + tw), min(H, y0 + th)
        if xb <= xa or yb <= ya:
            continue
        rr, al = r[ya - y0:yb - y0, xa - x0:xb - x0], aa[ya - y0:yb - y0, xa - x0:xb - x0, None]
        canvas[ya:yb, xa:xb] = canvas[ya:yb, xa:xb] * (1 - al) + rr * al
        alpha[ya:yb, xa:xb] = np.maximum(alpha[ya:yb, xa:xb] * (1 - al[..., 0]), al[..., 0])
        used += 1
    cart = nd.binary_dilation(L.load_mask(os.path.join(L.WORK, "p5_sam_wooden_cart.png")), iterations=2)
    fig = np.asarray(Image.fromarray(alpha).resize((base.width, base.height), Image.BOX)) > 0.5
    fig &= ~cart
    return canvas, fig, used, len(figs)


def p5_frieze(seeds=None):
    for s in (seeds or L.P5_SEEDS):
        t0 = time.time()
        frieze(s)
        print("frieze", s, f"{time.time() - t0:.0f}s", flush=True)


def p5_place(seeds=None):
    for s in (seeds or L.P5_SEEDS):
        res = place(s)
        if res is None:
            print("place", s, "no figures in the frieze")
            continue
        canvas, fig, used, nf = res
        Image.fromarray((canvas * 255 + 0.5).astype(np.uint8)).save(L.wd("p5", f"st_drowned_s{s}.png"))
        L.save_mask(fig, L.wd("p5", f"st_drowned_s{s}_fig.png"))
        print("place", s, "frieze figures", nf, "placed", used, "cut components", count(fig, 40), flush=True)


def p7_head():
    import ink_comfy as C
    img = L.pick("p7")
    H, W = img.shape[:2]
    yy = np.arange(H)[:, None] * np.ones((1, W))
    person = L.load_mask(os.path.join(L.WORK, "p7_sam_person.png"))
    lamp = L.load_mask(os.path.join(L.WORK, "p7_sam_hanging_iron_lantern.png"))
    m = nd.binary_dilation(person & (yy < 0.52 * H), iterations=40)
    m[int(0.03 * H):int(0.40 * H), int(0.36 * W):int(0.60 * W)] = True     # room for the lifted head, toward the lamp
    m &= ~nd.binary_dilation(lamp, iterations=24)
    m &= yy < 0.60 * H
    L.save_mask(m, L.wd("p7", "state_head_up2.png"))
    src = os.path.join(L.HERE, "out", L.PLATES["p7"]["src"])
    for s in L.SEEDS:
        dst = L.wd("p7", f"st_head_up2_s{s}.png")
        if os.path.exists(dst):
            continue
        t0 = time.time()
        raw = L.wd("p7", f"raw_st_head_up2_s{s}.png")
        C.krea(L.full("r2", L.P7_HEAD2), W, H, s, raw, init=src, denoise=1.0, mask=L.wd("p7", "state_head_up2.png"))
        L.composite_back(src, raw, L.wd("p7", "state_head_up2.png")).save(dst)
        C.sam(dst, "hooded person", L.wd("p7", f"st_head_up2_s{s}_person.png"), 0.3)
        print("head_up2", s, f"{time.time() - t0:.0f}s", flush=True)
    sheet = Image.new("RGB", (4 * 512, 384))
    for j, s in enumerate(L.SEEDS):
        sheet.paste(Image.open(L.wd("p7", f"st_head_up2_s{s}.png")).resize((512, 384)), (j * 512, 0))
    sheet.save(L.wd("p7", "head_up2.jpg"), quality=85)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "slots":
        p5_slots()
    elif a == "p5clean":
        p5_clean()
    elif a == "p5apply":
        p5_apply(int(sys.argv[2]))
    elif a == "p5drowned":
        p5_slots()
        p5_drowned([int(x) for x in sys.argv[2:]] or None)
    elif a == "p5frieze":
        p5_frieze([int(x) for x in sys.argv[2:]] or None)
    elif a == "p5place":
        p5_place([int(x) for x in sys.argv[2:]] or None)
    elif a == "p7head":
        p7_head()
