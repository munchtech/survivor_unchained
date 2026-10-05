"""Concept pictures for a creature, made locally with Z-Image-Turbo.

    python tools/creatures/concept.py boar --out DIR [--seeds 1,2,3] [--views side,three_quarter] [--size 1344x896]

Z-Image-Turbo is Apache-2.0 with no revenue cap (legal brief 5(g), path 2),
so a model made from its picture carries no Krea condition. Every picture is
written with a record beside it (prompt, seed, model and its hash, date), the
ledger line the legal rules ask for before anything lands.

Take the GPU turn first (tools/turn.py take gpu ...) and give it back after:
the script frees ComfyUI's models when it ends, but the turn is the caller's.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "comfy"))
import comfy  # noqa: E402

GRAPH = os.path.join(HERE, "..", "comfy", "graphs", "zimage_t2i.json")
MODELS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Comfy-Desktop", "ComfyUI-Shared", "models")
WEIGHTS = {
    "diffusion_models/z_image_turbo_bf16.safetensors": "2407613050b809ffdff18a4ac99af83ea6b95443ecebdf80e064a79c825574a6",
    "text_encoders/qwen_3_4b.safetensors": "6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a",
    "vae/ae.safetensors": "afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38",
}

# What TRELLIS needs to read a body well: the whole animal, square on its
# legs, nothing crossing, on a plain ground, lit evenly so the paint carries
# no baked shadow. The look itself is the creature's own brief.
STAGING = ("Full body in frame with space around it, standing square on all four legs, legs straight and apart, "
           "head level, mouth closed, tail hanging clear. Plain flat light grey studio background, soft even "
           "overcast light from all sides, no cast shadow, no ground clutter, no text. Photorealistic creature "
           "design, sharp focus, highly detailed.")

VIEWS = {
    "side": "Seen exactly side-on from its left, at the height of its shoulder.",
    "three_quarter": "Seen from three-quarters in front of its left shoulder, slightly above, so both tusks and the whole flank show.",
    "front": "Seen straight from the front at the height of its snout, both tusks and both shoulders showing.",
}

CREATURES = {
    # The Verge's tusker: the boar of the thickets at the valley's edge, which
    # runs with the Pack. Heavy in front like every boar, but built up beyond
    # nature: a hump of shoulder, a crest of bristle down the spine like a
    # hedge, tusks that sweep out sideways so they read from above, and a
    # hide that has met hunters, thorns and other boars and won.
    "boar": ("A huge old wild boar of a dark northern forest, a dark-fantasy beast. Massive muscular shoulder hump, "
             "the body deep and heavy at the front and narrowing to lean hindquarters, short thick neck, long wedge-shaped "
             "head with a broad leathery snout disc. Coarse wiry hide of near-black brown bristles, grizzled rust and grey at "
             "the tips. A tall stiff crest of long black bristles stands along the whole spine from behind the ears to the "
             "rump, like a ridge of dead thorns. Two great curved ivory tusks, yellowed and chipped, sweep out sideways and "
             "up from the lower jaw past the cheeks, with shorter upper tusks curling above them. Small deep-set amber eyes, "
             "one ear torn. Old pale scars across the snout, the shoulder and the flank, a ragged notch in one ear. Dried dark "
             "mud caked up the legs to the knees, heavy black cloven hooves, a thin tufted tail."),
}


def free():
    """Unload ComfyUI's models, so the next turn starts with the GPU empty."""
    import urllib.request
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("creature", choices=sorted(CREATURES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="1,2,3,4")
    ap.add_argument("--views", default="three_quarter,side")
    ap.add_argument("--size", default="1344x896")
    ap.add_argument("--check", action="store_true", help="hash the weights against the ledger first")
    a = ap.parse_args()
    if a.check:
        for rel, want in WEIGHTS.items():
            got = sha256(os.path.join(MODELS, rel))
            print(rel, "OK" if got == want else f"MISMATCH {got}")
            if got != want:
                raise SystemExit(1)
    w, h = (int(x) for x in a.size.split("x"))
    os.makedirs(a.out, exist_ok=True)
    try:
        for view in a.views.split(","):
            prompt = f"{CREATURES[a.creature]} {VIEWS[view]} {STAGING}"
            for seed in (int(s) for s in a.seeds.split(",")):
                api = json.load(open(GRAPH, encoding="utf-8"))
                api["5"]["inputs"]["text"] = prompt
                api["7"]["inputs"].update(width=w, height=h)
                api["8"]["inputs"]["seed"] = seed
                api["10"]["inputs"]["filename_prefix"] = f"creatures/{a.creature}_{view}_{seed}"
                saved = comfy.run(api, a.out)
                for path in saved:
                    record = {
                        "file": os.path.basename(path), "creature": a.creature, "view": view, "prompt": prompt, "seed": seed,
                        "size": [w, h], "steps": api["8"]["inputs"]["steps"], "sampler": api["8"]["inputs"]["sampler_name"],
                        "model": "Z-Image-Turbo (Tongyi-MAI), Apache-2.0, Comfy-Org/z_image_turbo split files",
                        "weights": WEIGHTS, "graph": "tools/comfy/graphs/zimage_t2i.json",
                        "tool": "local ComfyUI " + comfy.get("/system_stats")["system"]["comfyui_version"],
                        "date": datetime.datetime.now().isoformat(timespec="seconds"),
                    }
                    with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as f:
                        json.dump(record, f, indent=1)
    finally:
        free()


if __name__ == "__main__":
    main()
