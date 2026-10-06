import os
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a"
p = os.path.join(W, "tools", "uiforge", "krea.py")
s = open(p, encoding="utf-8").read()
a = s.index('if __name__ == "__main__":')
s = s[:a] + '''def i2i_many(jobs, n=2, lora=0.8, out=None, steps=8):
    """Several paintings over guides in one queued graph (one place in a shared queue, one
    model load): jobs = [(tag, guide, prompt, denoise, seed)]. Each lands as TAG_SEED_N.png
    in `out`; what an earlier run made is reused. Returns {tag: [paths]}."""
    import uuid
    out = out or os.path.join(OUT, "i2i_many")
    os.makedirs(out, exist_ok=True)
    res = {t: _done(out, t, sd) for t, g, p, dn, sd in jobs if _done(out, t, sd)}
    jobs = [j for j in jobs if j[0] not in res]
    if not jobs:
        return res
    tok = uuid.uuid4().hex[:6]
    base = _graph("", 0, lora=lora, steps=steps)
    g = {k: base[k] for k in ("unet", "lora", "clip", "vae")}
    model = ["lora", 0] if lora > 0 else ["unet", 0]
    for i, (tag, guide, prompt, dn, seed) in enumerate(jobs):
        name = comfy.upload(guide)
        g[f"img{i}"] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[f"enc{i}"] = {"class_type": "VAEEncode", "inputs": {"pixels": [f"img{i}", 0], "vae": ["vae", 0]}}
        g[f"rep{i}"] = {"class_type": "RepeatLatentBatch", "inputs": {"samples": [f"enc{i}", 0], "amount": n}}
        g[f"pos{i}"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}}
        g[f"neg{i}"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": [f"pos{i}", 0]}}
        g[f"ks{i}"] = {"class_type": "KSampler", "inputs": {"model": model, "positive": [f"pos{i}", 0], "negative": [f"neg{i}", 0],
                                                         "latent_image": [f"rep{i}", 0], "seed": seed, "steps": steps, "cfg": 1,
                                                         "sampler_name": "euler", "scheduler": "simple", "denoise": dn}}
        g[f"dec{i}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"ks{i}", 0], "vae": ["vae", 0]}}
        g[f"save{i}"] = {"class_type": "SaveImage", "inputs": {"images": [f"dec{i}", 0], "filename_prefix": f"i2im_{tok}_{i:03d}_"}}
    files = qrun(g, out)
    for i, (tag, guide, prompt, dn, seed) in enumerate(jobs):
        mine = sorted(f for f in files if os.path.basename(f).startswith(f"i2im_{tok}_{i:03d}_"))
        res[tag] = []
        for j, f in enumerate(mine):
            dst = os.path.join(out, f"{tag}_{seed}_{j}.png")
            os.replace(f, dst)
            res[tag].append(dst)
    return res


''' + s[a:]
open(p, "w", encoding="utf-8").write(s)

p = os.path.join(W, "tools", "uiforge", "emblems.py")
s = open(p, encoding="utf-8").read()
x = '''def fit(key, src, dst=None):'''
y = '''def paint_many(keys, denoise=0.5, seed=1200, n=3):
    """All their paintings in one queued graph (the GPU is shared: one place in the queue)."""
    import krea
    import icons
    jobs = []
    for k in keys:
        p, a, school = make_guide(k)
        prompt = LOOK + SUBJECT[k] + ", " + icons.SCHOOL.get(school, "") + ". " + krea.STYLE
        jobs.append((f"em_{k}_{int(denoise * 100)}", p, prompt, denoise, seed))
    return krea.i2i_many(jobs, n=n, out=RAW)


def fit(key, src, dst=None):'''
assert x in s
s = s.replace(x, y)
x = '''    else:
        for k in args or list(DESIGNS):
            print(k, paint(k)[0])'''
y = '''    elif args and args[0] == "--many":
        for k, v in paint_many(args[1:] or list(DESIGNS)).items():
            print(k, len(v))
    else:
        for k in args or list(DESIGNS):
            print(k, paint(k)[0])'''
assert x in s
s = s.replace(x, y)
open(p, "w", encoding="utf-8").write(s)
print("ok")
