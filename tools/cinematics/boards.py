"""Make a cinematic's storyboard frames on the local GPU, one per shot, in
the house board language: ink and grey marker, colour only in the light.

    python tools/cinematics/boards.py c01 [--only 2,3] [--force] [--sheet OUT.jpg]

The prompts are docs/cinematics/shoot/boards/<id>.json:

    {"seed": 1100,                       # each shot's seed is seed + its index
     "people": {"her": "a young woman with long wet dark red hair, ..."},
     "shots": {"2": "top shot looking straight down: ... {her} ...", ...}}

{name} in a shot's prompt is replaced by that person's fixed description, so
each person is drawn the same way in every frame. Frames are made with
Krea 2 turbo (tools/comfy/graphs/krea_t2i.json, prompt expansion off) at
1536x640 and saved as docs/cinematics/shoot/boards/<id>/s<shot>.jpg. It
takes the GPU's turn first (tools/turn.py; --wait minutes for it), waits for
ComfyUI's queue to be empty, and gives the turn back (freeing the models) after.

A shot can be drawn over the engine's own frame of it, so the staging, the
scale and the lens are the surveyed camera's and only the drawing is the
model's:

    "7": {"prompt": "...", "from": "staging", "denoise": 0.62}

The staging frames are the previs stills (the game run with --shot NAME
--clean), cropped to the picture inside the bars:

    python tools/cinematics/boards.py c02 --stage st2   # godot/.shots/st2_c02_s*_1.png

and are kept out of git, in tools/comfy/out/staging/<id>/s<shot>.png.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "comfy"))
import comfy  # noqa: E402

BOARDS = os.path.join(ROOT, "docs", "cinematics", "shoot", "boards")
GRAPH = os.path.join(ROOT, "tools", "comfy", "graphs", "krea_t2i.json")
STAGING = os.path.join(ROOT, "tools", "comfy", "out", "staging")
SHOTS = os.path.join(ROOT, "godot", ".shots")
STYLE = ("Rough storyboard panel for a dark fantasy film, ink and grey marker sketch, quick gestural lines, "
         "flat grey tones, clear staging, monochrome except for small touches of coloured light: ")


def wait_idle():
    while True:
        q = comfy.get("/queue")
        if not q.get("queue_running") and not q.get("queue_pending"):
            return
        print("  waiting for ComfyUI's queue...")
        time.sleep(15)


def free():
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


def stage(cid, prefix):
    """The previs stills of a cinematic, cut to the picture inside the bars and
    sized as a board, into the staging folder."""
    import glob
    import re
    out = os.path.join(STAGING, cid)
    os.makedirs(out, exist_ok=True)
    pat = re.compile(re.escape(f"{prefix}_{cid}_s") + r"(.+)_1\.png")
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sheet", default="")
    ap.add_argument("--wait", default="0", help="minutes to wait for the GPU's turn")
    ap.add_argument("--stage", default="", help="cut the previs stills with this --shot name into staging, and stop")
    a = ap.parse_args()
    if a.stage:
        stage(a.id, a.stage)
        return
    spec = json.load(open(os.path.join(BOARDS, f"{a.id}.json"), encoding="utf-8"))
    out_dir = os.path.join(BOARDS, a.id)
    os.makedirs(out_dir, exist_ok=True)
    only = {s for s in a.only.split(",") if s}
    base = json.load(open(GRAPH, encoding="utf-8"))
    made = []
    # Heavy work takes turns on this machine (docs/team/README.md).
    turn = os.path.join(ROOT, "tools", "turn.py")
    who = f"cinematics: boards {a.id}"
    if subprocess.run([sys.executable, turn, "take", "gpu", who, "--wait", a.wait]).returncode != 0:
        raise SystemExit(1)
    try:
        wait_idle()
        for i, (shot, entry) in enumerate(spec["shots"].items()):
            dst = os.path.join(out_dir, f"s{shot}.jpg")
            if (only and shot not in only) or (os.path.exists(dst) and not a.force and not only):
                continue
            entry = entry if isinstance(entry, dict) else {"prompt": entry}
            prompt = entry["prompt"]
            for name, desc in spec.get("people", {}).items():
                prompt = prompt.replace("{" + name + "}", desc)
            api = json.loads(json.dumps(base))
            api["30:24"]["inputs"]["value"] = False
            api["30:23"]["inputs"]["value"] = False
            api["30:3"]["inputs"]["seed"] = entry.get("seed", spec.get("seed", 1000) + i)
            api["30:19"]["inputs"]["value"] = STYLE + prompt
            api["30:5"]["inputs"]["width"] = 1536
            api["30:5"]["inputs"]["height"] = 640
            api["29"]["inputs"]["filename_prefix"] = f"board_{a.id}_s{shot}"
            if entry.get("from") == "staging":
                # Drawn over the engine's frame: its staging kept, its rendering replaced.
                src = os.path.join(STAGING, a.id, f"s{shot}.png")
                if not os.path.exists(src):
                    raise SystemExit(f"no staging for {a.id} s{shot}: run --stage first")
                api["50"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(src)}}
                api["51"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["50", 0], "vae": ["30:12", 0]}}
                api["30:3"]["inputs"]["latent_image"] = ["51", 0]
                api["30:3"]["inputs"]["denoise"] = entry.get("denoise", 0.62)
            tmp = tempfile.mkdtemp(prefix="board_")
            files = comfy.run(api, tmp)
            Image.open(files[0]).convert("RGB").save(dst, quality=90)
            made.append(dst)
            print("  ", dst)
    finally:
        subprocess.run([sys.executable, turn, "give", "gpu", who])
    if a.sheet:
        frames = [os.path.join(out_dir, f"s{s}.jpg") for s in spec["shots"] if os.path.exists(os.path.join(out_dir, f"s{s}.jpg"))
                  and (not only or s in only)]
        w = 760
        ims = [Image.open(f) for f in frames]
        hh = int(640 * w / 1536)
        sheet = Image.new("RGB", (2 * w + 6, ((len(ims) + 1) // 2) * (hh + 6)), (20, 20, 20))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((w, hh)), ((k % 2) * (w + 6), (k // 2) * (hh + 6)))
        sheet.save(a.sheet, quality=85)
        print("sheet", a.sheet)


if __name__ == "__main__":
    main()
