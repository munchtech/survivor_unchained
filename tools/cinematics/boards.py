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
waits for ComfyUI's queue to be empty first, and frees the models after.
"""
import argparse
import json
import os
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sheet", default="")
    a = ap.parse_args()
    spec = json.load(open(os.path.join(BOARDS, f"{a.id}.json"), encoding="utf-8"))
    out_dir = os.path.join(BOARDS, a.id)
    os.makedirs(out_dir, exist_ok=True)
    only = {s for s in a.only.split(",") if s}
    base = json.load(open(GRAPH, encoding="utf-8"))
    made = []
    wait_idle()
    try:
        for i, (shot, prompt) in enumerate(spec["shots"].items()):
            dst = os.path.join(out_dir, f"s{shot}.jpg")
            if (only and shot not in only) or (os.path.exists(dst) and not a.force and not only):
                continue
            for name, desc in spec.get("people", {}).items():
                prompt = prompt.replace("{" + name + "}", desc)
            api = json.loads(json.dumps(base))
            api["30:24"]["inputs"]["value"] = False
            api["30:23"]["inputs"]["value"] = False
            api["30:3"]["inputs"]["seed"] = spec.get("seed", 1000) + i
            api["30:19"]["inputs"]["value"] = STYLE + prompt
            api["30:5"]["inputs"]["width"] = 1536
            api["30:5"]["inputs"]["height"] = 640
            api["29"]["inputs"]["filename_prefix"] = f"board_{a.id}_s{shot}"
            tmp = tempfile.mkdtemp(prefix="board_")
            files = comfy.run(api, tmp)
            Image.open(files[0]).convert("RGB").save(dst, quality=90)
            made.append(dst)
            print("  ", dst)
    finally:
        free()
    if a.sheet:
        frames = [os.path.join(out_dir, f"s{s}.jpg") for s in spec["shots"] if os.path.exists(os.path.join(out_dir, f"s{s}.jpg"))]
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
