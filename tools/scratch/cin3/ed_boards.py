p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\tools\cinematics\boards.py'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)


rep('''{name} in a shot's prompt is replaced by that person's fixed description, so
each person is drawn the same way in every frame. Frames are made with
Krea 2 turbo (tools/comfy/graphs/krea_t2i.json, prompt expansion off) at
1536x640 and saved as docs/cinematics/shoot/boards/<id>/s<shot>.jpg. It
waits for ComfyUI's queue to be empty first, and frees the models after.
"""''', '''{name} in a shot's prompt is replaced by that person's fixed description, so
each person is drawn the same way in every frame. Frames are made with
Krea 2 turbo (tools/comfy/graphs/krea_t2i.json, prompt expansion off) at
1536x640 and saved as docs/cinematics/shoot/boards/<id>/s<shot>.jpg. It
waits for ComfyUI's queue to be empty first, and frees the models after.

A shot can be drawn over the engine's own frame of it, so the staging, the
scale and the lens are the surveyed camera's and only the drawing is the
model's:

    "7": {"prompt": "...", "from": "staging", "denoise": 0.62}

The staging frames are the previs stills (the game run with --shot NAME
--clean), cropped to the picture inside the bars:

    python tools/cinematics/boards.py c02 --stage st2   # godot/.shots/st2_c02_s*_1.png

and are kept out of git, in tools/comfy/out/staging/<id>/s<shot>.png.
"""''')
rep('''STYLE = (''', '''STAGING = os.path.join(ROOT, "tools", "comfy", "out", "staging")
SHOTS = os.path.join(ROOT, "godot", ".shots")
STYLE = (''')
rep('''def main():''', '''def stage(cid, prefix):
    """The previs stills of a cinematic, cut to the picture inside the bars and
    sized as a board, into the staging folder."""
    import glob
    import re
    out = os.path.join(STAGING, cid)
    os.makedirs(out, exist_ok=True)
    pat = re.compile(re.escape(f"{prefix}_{cid}_s") + r"(.+)_1\\.png")
    for f in sorted(glob.glob(os.path.join(SHOTS, f"{prefix}_{cid}_s*_1.png"))):
        shot = pat.match(os.path.basename(f)).group(1)
        im = Image.open(f).convert("RGB")
        # The bars: the first and last rows with picture in them.
        g = im.convert("L")
        w, h = im.size
        rows = [y for y in range(h) if g.crop((0, y, w, y + 1)).getextrema()[1] > 12]
        top, bottom = (rows[0], rows[-1] + 1) if rows else (0, h)
        pic = im.crop((0, top, w, bottom))
        # Fill the board's 12:5 frame, cutting the excess evenly.
        want = 1536 / 640
        pw, ph = pic.size
        if pw / ph > want:
            cw = int(ph * want)
            pic = pic.crop(((pw - cw) // 2, 0, (pw - cw) // 2 + cw, ph))
        else:
            ch = int(pw / want)
            pic = pic.crop((0, (ph - ch) // 2, pw, (ph - ch) // 2 + ch))
        dst = os.path.join(out, f"s{shot}.png")
        pic.resize((1536, 640), Image.LANCZOS).save(dst)
        print("  staged", dst)


def main():''')
rep('''    ap.add_argument("--sheet", default="")
    a = ap.parse_args()''', '''    ap.add_argument("--sheet", default="")
    ap.add_argument("--stage", default="", help="cut the previs stills with this --shot name into staging, and stop")
    a = ap.parse_args()
    if a.stage:
        stage(a.id, a.stage)
        return''')
rep('''        for i, (shot, prompt) in enumerate(spec["shots"].items()):
            dst = os.path.join(out_dir, f"s{shot}.jpg")
            if (only and shot not in only) or (os.path.exists(dst) and not a.force and not only):
                continue''', '''        for i, (shot, entry) in enumerate(spec["shots"].items()):
            dst = os.path.join(out_dir, f"s{shot}.jpg")
            if (only and shot not in only) or (os.path.exists(dst) and not a.force and not only):
                continue
            entry = entry if isinstance(entry, dict) else {"prompt": entry}
            prompt = entry["prompt"]''')
rep('''            api["29"]["inputs"]["filename_prefix"] = f"board_{a.id}_s{shot}"''', '''            api["29"]["inputs"]["filename_prefix"] = f"board_{a.id}_s{shot}"
            if entry.get("from") == "staging":
                # Drawn over the engine's frame: its staging kept, its rendering replaced.
                src = os.path.join(STAGING, a.id, f"s{shot}.png")
                if not os.path.exists(src):
                    raise SystemExit(f"no staging for {a.id} s{shot}: run --stage first")
                api["50"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(src)}}
                api["51"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["50", 0], "vae": ["30:12", 0]}}
                api["30:3"]["inputs"]["latent_image"] = ["51", 0]
                api["30:3"]["inputs"]["denoise"] = entry.get("denoise", 0.62)''')
rep('''        frames = [os.path.join(out_dir, f"s{s}.jpg") for s in spec["shots"] if os.path.exists(os.path.join(out_dir, f"s{s}.jpg"))]''',
    '''        frames = [os.path.join(out_dir, f"s{s}.jpg") for s in spec["shots"] if os.path.exists(os.path.join(out_dir, f"s{s}.jpg"))
                  and (not only or s in only)]''')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
