"""Style r2, step 1: the painted target (Krea 2 turbo + the darkbrush LoRA on the local ComfyUI; previews only, never shipped).

  python krea_r2.py prep                                   r2/src/<F>_L.png: the A frame with B's light design (light block-in)
  python krea_r2.py paint F TAG d=0.5 lora=0.8 seeds=1,2 [src=PATH] [p=KEY] [n=1]
                                                            Krea img2img over the source (default r2/src/<F>_L.png); one model load
  python krea_r2.py comp F IMG... [feather=3]               her engine pixels (relit source) back in -> <IMG>_c.png; prints the scores
  python krea_r2.py sheet OUT.jpg [w=640] IMG...            a labelled grid at w px a cell (for the lead's look)

F is town | ford | close (the r1 frames town_00, ford_03, close_03). Scores against the source: edge = correlation of
coarse edges (layout held: 1.0 is the same drawing), drift = mean low-pass colour change (0-1), keep = her mask share.
GPU: take a turn first (tools/turn.py take gpu "art-style: krea target"), give it back after each batch.
"""
import os, sys, glob
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SHOTS = os.path.join(WT, "godot", ".shots")
SCR = os.environ.get("ART_SCR", r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\746784c6-95b9-4ef2-95bf-f24b9874f4bb\scratchpad\art_style")
SOL, R2 = os.path.join(SCR, "solver"), os.path.join(SCR, "r2")
FR = {"town": "r3_town_t_00.png", "ford": "r3_ford_t_03.png", "close": "r3_close_t_03.png"}
DEP = {"town": "b1/tB_d70_35_ctrl.png", "ford": "b2/fB1_s1_50_ctrl.png", "close": "b2/cB1_s1_50_ctrl.png"}
KEEP = {"town": "masks/k_town.png", "ford": "masks/k_ford.png", "close": "masks/k_close.png"}
LW = np.array([0.2126, 0.7152, 0.0722], np.float32)

QUAL = ("Visible, confident brushwork at one consistent scale, simplified texture detail, large readable value shapes, "
        "soft painted edges in shadow and crisp edges in the light, colour in every shadow and never black, no outlines. "
        "Painterly realism: believable forms and proportions treated like a rich oil painting, a beautiful hand-painted fantasy world.")
PROMPTS = {
    "town": ("An oil painting of a medieval market square seen from high above, looking steeply down: worn cobblestones of varied size "
             "with packed ochre mud between them, a round stone well under a small timber roof, market stalls with striped canvas awnings, "
             "wooden benches, barrels and crates, a few villagers. Warm golden afternoon sunlight from the right, long cool blue-violet shadows, "
             "rich ochre, umber and moss-green earth colours, a glowing brazier in the corner. " + QUAL),
    "ford": ("An oil painting of a shallow river ford at night seen from high above: dark moonlit water with soft ripples and drifting mist, "
             "a line of pale stepping stones crossing it, a small figure on the stones carrying a warm ember light, an amber lantern on a post "
             "at the near bank glowing on the water, a frosty pebbled bank along the bottom. Deep blue and violet moonlight, warm amber pools "
             "of light. " + QUAL),
    "close": ("An oil painting of a young woman warrior in blue steel armour with a round wooden shield standing beside a crackling campfire "
              "at night in a pine forest clearing, logs and a small chest by the fire, tall dark pine trunks and a canvas tent behind her. "
              "Warm orange firelight from the lower left on her and the ground, cool blue moonlight and haze between the far trunks. " + QUAL),
}


def rd(p):
    return np.asarray(Image.open(p).convert("RGB"), np.float32) / 255


def wr(p, x):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(np.clip(np.rint(x * 255), 0, 255).astype(np.uint8)).save(p)
    return p


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def light(fr, x, s=1.0):
    """B's light design (r1, paintprep_r1.light): what an engine light, fog and pool pass could do, by hand."""
    H, W = x.shape[:2]
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    dep = np.asarray(Image.open(os.path.join(SOL, DEP[fr])).convert("L").resize((W, H), Image.BILINEAR), np.float32) / 255
    pool = lambda cx, cy, sig: np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (2 * sig * sig))[..., None]
    def fbm(seed, sigs):
        r = np.random.default_rng(seed); n = 0
        for sg in sigs: n = n + cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), sg) * sg
        return (n - n.mean()) / (n.std() + 1e-6)
    lum = x @ LW
    if fr == "town":
        lb = cv2.GaussianBlur(lum, (0, 0), 3); lit = ss(0.17, 0.25, lb)[..., None]
        x = x * (lit * np.array([1 + 0.10 * s, 1 + 0.035 * s, 1 - 0.10 * s], np.float32) + (1 - lit))
        sh = 1 - lit
        x = x * (1 - sh) + sh * (x * np.array([1 - 0.05 * s, 1 - 0.025 * s, 1 + 0.08 * s], np.float32) + np.array([0.007, 0.007, 0.016], np.float32) * s)
        x = x + cv2.GaussianBlur(lit[..., 0], (0, 0), 35)[..., None] * sh * np.array([0.030, 0.016, 0.004], np.float32) * s
        far = (1 - ss(0.05, 0.45, dep))[..., None]
        x = x * (1 - 0.10 * s * far) + 0.10 * s * far * np.array([0.62, 0.58, 0.60], np.float32)
        x = x + pool(W * 1.05, -H * 0.15, 900) * np.array([0.060, 0.038, 0.008], np.float32) * s
        x = x + pool(1855, 1015, 70) * np.array([0.20, 0.09, 0.02], np.float32) * s
    elif fr == "ford":
        x = x + pool(961, 525, 120) * np.array([0.20, 0.075, 0.015], np.float32) * s
        x = x + pool(958, 751, 85) * np.array([0.17, 0.10, 0.03], np.float32) * s
        x = x + pool(958, 830, 40) * np.array([0.06, 0.035, 0.01], np.float32) * s
        x = x + (1 - ss(0.0, 0.55, YY / H))[..., None] * np.array([0.0, 0.020, 0.035], np.float32) * s
        hp = np.maximum(lum - cv2.GaussianBlur(lum, (0, 0), 3), 0)[..., None]
        water = ((YY < 800) & (dep < 0.75))[..., None].astype(np.float32)
        x = x + hp * water * np.array([0.6, 0.9, 1.2], np.float32) * 0.8 * s
        mist = ss(0.6, 2.0, fbm(3, (90, 45)))[..., None] * water * (1 - ss(0.5, 0.75, YY / H))[..., None]
        x = x * (1 - 0.10 * s * mist) + 0.10 * s * mist * np.array([0.30, 0.42, 0.58], np.float32)
        x = x + ss(0.78, 0.86, YY / H)[..., None] * np.maximum(lum - 0.12, 0)[..., None] * np.array([0.05, 0.12, 0.2], np.float32) * s
    else:
        fire = pool(420, 960, 380)
        x = x * (1 + fire * np.array([0.50, 0.18, -0.06], np.float32) * s) + fire * np.array([0.060, 0.024, 0.0], np.float32) * s
        x = x + pool(400, 780, 140) * np.array([0.10, 0.04, 0.0], np.float32) * s
        far = (1 - ss(0.08, 0.40, dep))[..., None] * (1 - fire)
        x = x * (1 - 0.18 * s * far) + 0.18 * s * far * np.array([0.10, 0.17, 0.27], np.float32)
        x = x + far * np.maximum(lum - cv2.GaussianBlur(lum, (0, 0), 6), 0)[..., None] * np.array([0.5, 0.8, 1.1], np.float32) * s
    return np.clip(x, 0, 1)


def keep(fr, feather=3.0, shape=None):
    m = np.asarray(Image.open(os.path.join(SOL, KEEP[fr])).convert("L"), np.float32) / 255
    if shape and m.shape != shape: m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    if feather > 0: m = cv2.GaussianBlur(m, (0, 0), feather)
    return np.clip(m, 0, 1)


def scores(src, out, m):
    def edges(x):
        l = cv2.GaussianBlur(cv2.resize(x @ LW, (x.shape[1] // 2, x.shape[0] // 2), interpolation=cv2.INTER_AREA), (0, 0), 2.0)
        return np.hypot(cv2.Sobel(l, cv2.CV_32F, 1, 0), cv2.Sobel(l, cv2.CV_32F, 0, 1)).ravel()
    a, b = edges(src), edges(out)
    edge = float(np.corrcoef(a, b)[0, 1])
    lp = lambda x: cv2.GaussianBlur(x, (0, 0), 8)
    drift = float(np.abs(lp(src) - lp(out)).mean())
    return edge, drift, float(m.mean())


def main():
    a = sys.argv[1:]
    cmd = a.pop(0)
    kw = dict(v.split("=", 1) for v in a if "=" in v and not os.path.exists(v))
    pos = [v for v in a if v not in [f"{k}={x}" for k, x in kw.items()]]
    if cmd == "prep":
        for fr, f in FR.items():
            print(wr(os.path.join(R2, "src", f"{fr}_A.png"), rd(os.path.join(SHOTS, f))))
            print(wr(os.path.join(R2, "src", f"{fr}_L.png"), light(fr, rd(os.path.join(SHOTS, f)), float(kw.get("s", 1.0)))))
    elif cmd == "paint":
        # d=0.4 or d=0.4/0.3 (a second pass over the first's latent); ref=index|offset|... adds the source as a reference latent
        fr, tag = pos[0], pos[1]
        sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
        import krea, comfy
        src = kw.get("src", os.path.join(R2, "src", f"{fr}_L.png"))
        ds, lora, ref = [float(v) for v in kw.get("d", "0.5").split("/")], float(kw.get("lora", 0.8)), kw.get("ref")
        prompt = PROMPTS[kw.get("p", fr)] if kw.get("p", fr) in PROMPTS else kw["p"]
        seeds = [int(s) for s in kw.get("seeds", "1").split(",")]
        out = os.path.join(R2, "paint"); os.makedirs(out, exist_ok=True)
        todo = [sd for sd in seeds if not os.path.exists(os.path.join(out, f"{fr}_{tag}_{sd}_0.png"))]
        if todo:
            g = {k: v for k, v in krea._graph(prompt, 0, lora=lora).items() if k in ("unet", "lora", "clip", "vae", "pos")}
            model = ["lora", 0] if lora > 0 else ["unet", 0]
            g["img"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(src)}}
            g["enc"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["img", 0], "vae": ["vae", 0]}}
            cond = ["pos", 0]
            if ref:
                g["refc"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["pos", 0], "latent": ["enc", 0]}}
                g["refm"] = {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["refc", 0], "reference_latents_method": ref}}
                cond = ["refm", 0]
            g["neg"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": cond}}
            for sd in todo:
                lat = ["enc", 0]
                for i, d in enumerate(ds):
                    g[f"ks{sd}_{i}"] = {"class_type": "KSampler", "inputs": {"model": model, "positive": cond, "negative": ["neg", 0], "latent_image": lat,
                                         "seed": sd + 1000 * i, "steps": 8, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": d}}
                    lat = [f"ks{sd}_{i}", 0]
                g[f"dec{sd}"] = {"class_type": "VAEDecode", "inputs": {"samples": lat, "vae": ["vae", 0]}}
                g[f"save{sd}"] = {"class_type": "SaveImage", "inputs": {"images": [f"dec{sd}", 0], "filename_prefix": f"k2r2_{fr}_{tag}_{sd}_"}}
            files = krea.qrun(g, out)
            for sd in todo:
                mine = sorted(f for f in files if os.path.basename(f).startswith(f"k2r2_{fr}_{tag}_{sd}_"))
                if mine: os.replace(mine[0], os.path.join(out, f"{fr}_{tag}_{sd}_0.png"))
        for sd in seeds: print(os.path.join(out, f"{fr}_{tag}_{sd}_0.png"))
    elif cmd == "tile":
        # The frame upscaled `up` times and painted in overlapping tiles (each captioned by the Qwen3-VL encoder, so a tile is
        # painted as what it holds, not as the whole scene), stitched with feathered seams and brought back to frame size.
        # Strokes come out 1/up the size, and the camera's top-down view survives (the model reads a tile as a close view).
        fr, tag = pos[0], pos[1]
        sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
        import krea, comfy
        src_p = kw.get("src", os.path.join(R2, "src", f"{fr}_L.png"))
        up, tw, th, ov = float(kw.get("up", 2)), int(kw.get("tw", 1536)), int(kw.get("th", 864)), int(kw.get("ov", 256))
        d, lora = float(kw.get("d", 0.4)), float(kw.get("lora", 0.8))
        seeds = [int(s) for s in kw.get("seeds", "1").split(",")]
        style = kw.get("style", QUAL)
        view = kw.get("view", "The view looks straight down from high above." if fr != "close" else "")
        src = rd(src_p); H, W = src.shape[:2]
        S = cv2.resize(src, (round(W * up), round(H * up)), interpolation=cv2.INTER_LANCZOS4); SH, SW = S.shape[:2]
        def steps(n, t):
            k = max(1, int(np.ceil((n - ov) / (t - ov)))); return [round(i * (n - t) / max(1, k - 1)) for i in range(k)] if k > 1 else [0]
        boxes = [(x, y) for y in steps(SH, th) for x in steps(SW, tw)]
        out = os.path.join(R2, "paint"); tdir = os.path.join(R2, "tiles", f"{fr}_{tag}"); os.makedirs(tdir, exist_ok=True)
        todo = [sd for sd in seeds if not os.path.exists(os.path.join(out, f"{fr}_{tag}_{sd}_0.png"))]
        if todo:
            g = {k: v for k, v in krea._graph("", 0, lora=lora).items() if k in ("unet", "lora", "clip", "vae")}
            model = ["lora", 0] if lora > 0 else ["unet", 0]
            ask = ("Describe this picture for a painter in two sentences: what is in it (objects, materials, any people) and where, "
                   "and its light and colours. Plain description only. " + view)
            for i, (x, y) in enumerate(boxes):
                tp = wr(os.path.join(tdir, f"t{i}.png"), S[y:y + th, x:x + tw])
                g[f"img{i}"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(tp)}}
                g[f"cap{i}"] = {"class_type": "TextGenerate", "inputs": {"clip": ["clip", 0], "prompt": ask, "image": [f"img{i}", 0], "max_length": 160,
                                "sampling_mode": "off", "thinking": False, "use_default_template": True}}
                g[f"cat{i}"] = {"class_type": "StringConcatenate", "inputs": {"string_a": [f"cap{i}", 0], "string_b": "An oil painting. " + view + " " + style, "delimiter": " "}}
                g[f"pos{i}"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": [f"cat{i}", 0]}}
                g[f"neg{i}"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": [f"pos{i}", 0]}}
                g[f"enc{i}"] = {"class_type": "VAEEncode", "inputs": {"pixels": [f"img{i}", 0], "vae": ["vae", 0]}}
                for sd in todo:
                    g[f"ks{i}_{sd}"] = {"class_type": "KSampler", "inputs": {"model": model, "positive": [f"pos{i}", 0], "negative": [f"neg{i}", 0],
                                         "latent_image": [f"enc{i}", 0], "seed": sd * 100 + i, "steps": 8, "cfg": 1, "sampler_name": "euler",
                                         "scheduler": "simple", "denoise": d}}
                    g[f"dec{i}_{sd}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"ks{i}_{sd}", 0], "vae": ["vae", 0]}}
                    g[f"save{i}_{sd}"] = {"class_type": "SaveImage", "inputs": {"images": [f"dec{i}_{sd}", 0], "filename_prefix": f"k2r2t_{fr}_{tag}_{sd}_{i:02d}_"}}
            g = {k: v for k, v in g.items() if v is not None}
            files = krea.qrun(g, tdir)
            for sd in todo:
                acc = np.zeros((SH, SW, 3), np.float32); wsum = np.zeros((SH, SW, 1), np.float32)
                for i, (x, y) in enumerate(boxes):
                    f = sorted(p for p in files if os.path.basename(p).startswith(f"k2r2t_{fr}_{tag}_{sd}_{i:02d}_"))[0]
                    t = rd(f)
                    if t.shape[:2] != (th, tw): t = cv2.resize(t, (tw, th), interpolation=cv2.INTER_LANCZOS4)
                    wx = np.minimum(np.minimum(np.arange(tw) + 1, tw - np.arange(tw)) / ov, 1.0)
                    wy = np.minimum(np.minimum(np.arange(th) + 1, th - np.arange(th)) / ov, 1.0)
                    if x == 0: wx[:tw // 2] = 1
                    if x + tw >= SW: wx[tw // 2:] = 1
                    if y == 0: wy[:th // 2] = 1
                    if y + th >= SH: wy[th // 2:] = 1
                    wgt = (wy[:, None] * wx[None, :])[..., None].astype(np.float32)
                    acc[y:y + th, x:x + tw] += t * wgt; wsum[y:y + th, x:x + tw] += wgt
                big = acc / np.maximum(wsum, 1e-6)
                wr(os.path.join(out, f"{fr}_{tag}_{sd}_0.png"), cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA))
        for sd in seeds: print(os.path.join(out, f"{fr}_{tag}_{sd}_0.png"))
    elif cmd == "comp":
        fr, imgs = pos[0], pos[1:]
        src = rd(os.path.join(R2, "src", f"{fr}_L.png"))
        for p in imgs:
            out = rd(p)
            if out.shape != src.shape: out = cv2.resize(out, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_LANCZOS4)
            m = keep(fr, float(kw.get("feather", 3)), src.shape[:2])[..., None]
            c = out * (1 - m) + src * m
            e, dr, k = scores(src, c, m)
            q = wr(p[:-4] + "_c.png", c)
            print(f"{os.path.basename(q)}  edge {e:.3f}  drift {dr:.3f}  keep {k:.4f}")
    elif cmd == "sheet":
        out, w = pos[0], int(kw.get("w", 640))
        imgs = pos[1:]
        cols = int(kw.get("cols", min(3, len(imgs))))
        cells = []
        crop = [int(v) for v in kw["crop"].split(",")] if "crop" in kw else None   # x,y,h: a 1:1 crop w px wide under each frame
        for p in imgs:
            src = Image.open(p).convert("RGB"); h = round(src.height * w / src.width)
            im = src.resize((w, h), Image.LANCZOS)
            if crop:
                cx, cy, ch = crop
                both = Image.new("RGB", (w, h + ch)); both.paste(im, (0, 0)); both.paste(src.crop((cx, cy, cx + w, cy + ch)), (0, h))
                ImageDraw.Draw(both).rectangle([round(cx * w / src.width), round(cy * w / src.width),
                                                round((cx + w) * w / src.width), round((cy + ch) * w / src.width)], outline=(255, 255, 0))
                im = both
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, w, 18], fill=(0, 0, 0)); dr.text((4, 3), os.path.basename(p)[:80], fill=(255, 255, 255))
            cells.append(im)
        h = cells[0].height; rows = (len(cells) + cols - 1) // cols
        sh = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
        for i, c in enumerate(cells): sh.paste(c, ((i % cols) * w, (i // cols) * h))
        sh.save(out, quality=88); print(out, sh.size)


if __name__ == "__main__":
    main()
