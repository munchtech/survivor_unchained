import json, os, sys
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2dfc75e2d351105a"
sys.path.insert(0, os.path.join(ROOT, "tools", "comfy"))
import comfy
OUT = sys.argv[1]
base = json.load(open(os.path.join(ROOT, "tools/comfy/graphs/krea_t2i.json"), encoding="utf-8"))
STYLES = {
 "A": "Cinematic film storyboard frame, widescreen, drawn in charcoal and soft graphite on warm grey paper, loose confident strokes, smudged grey washes, strong value design, the only colour in the drawing is the light itself: ",
 "B": "Rough storyboard panel for a dark fantasy film, ink and grey marker sketch, quick gestural lines, flat grey tones, clear staging, monochrome except for small touches of coloured light: ",
}
SHOTS = {
 "c01s08": "close-up, a young woman's face, frontal, slightly below her eye line, wet dark hair clinging to her cheeks and forehead, a ribbon of green river weed in her hair, she breathes out slowly with lips parted and no breath shows in the freezing air, black birch forest behind her, frost on the grass, warm orange ember light from the left side of her face, cold blue moonlight rim on the right.",
 "c02s11": "wide shot from low on a river bank at night: a shallow river ford with mist on the water, three iron posts with cold pale blue flames, a hooded giant twice the height of a man standing in the water with a long wet beard and a lamp in his left fist, rows of drowned people standing waist deep in the pool behind him, a small young woman with a round shield and sword facing him on the near bank, ice spreading across the water from each post.",
}
for s, sp in STYLES.items():
    for k, p in SHOTS.items():
        api = json.loads(json.dumps(base))
        api["30:24"]["inputs"]["value"] = False
        api["30:23"]["inputs"]["value"] = False
        api["30:3"]["inputs"]["seed"] = 4242
        api["30:19"]["inputs"]["value"] = sp + p
        api["30:5"]["inputs"]["width"] = 1536
        api["30:5"]["inputs"]["height"] = 640
        api["29"]["inputs"]["filename_prefix"] = f"cine_{s}_{k}"
        comfy.run(api, os.path.join(OUT, f"{s}_{k}"))
