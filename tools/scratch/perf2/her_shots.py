"""The heroine at each of the game's zooms, standing in town by day: 8 frames 1/30 s apart each.
    python her_shots.py TAG BUILD [extra game args...]
Then: python her_shots.py --report TAG [TAG...]  (crops round her, and how much her pixels flicker frame to frame)."""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294\godot\.shots"
CAMS = ["12.5", "23", "31"]


def take(tag, build, extra):
    for cam in CAMS:
        name = f"her_{tag}_{cam.replace('.', '_')}"
        args = ["--quick", "warden", "--sex", "female", "--zone", "waystation", "--time", "day", "--quality", "high",
                "--cam", cam, "--seconds", "8", "--every", "0.0333", "--count", "8", *extra]
        subprocess.run([sys.executable, os.path.join(HERE, "shot.py"), build, name, *args], check=False)


def frames(tag, cam):
    pre = f"her_{tag}_{cam.replace('.', '_')}_"
    return [np.asarray(Image.open(os.path.join(SHOTS, f)).convert("RGB")).astype(float)
            for f in sorted(os.listdir(SHOTS)) if f.startswith(pre) and f.endswith(".png")]


def report(tags):
    for cam in CAMS:
        size = {"12.5": 150, "23": 85, "31": 66}[cam]
        crops = []
        for tag in tags:
            fs = frames(tag, cam)
            if not fs:
                continue
            h, w, _ = fs[0].shape
            cy, cx = h // 2, w // 2
            box = (slice(cy - size, cy + size), slice(cx - int(size * 0.7), cx + int(size * 0.7)))
            stack = np.stack([f[box] for f in fs])
            flick = np.abs(np.diff(stack, axis=0)).mean()
            print(f"cam {cam} {tag}: frame-to-frame change round her {flick:.2f}")
            crops.append(Image.fromarray(fs[-1][box].astype(np.uint8)))
        if crops:
            k = {"12.5": 2, "23": 4, "31": 5}[cam]
            out = Image.new("RGB", (sum(c.width * k for c in crops) + 10 * len(crops), crops[0].height * k), "white")
            x = 0
            for c in crops:
                out.paste(c.resize((c.width * k, c.height * k), Image.NEAREST), (x, 0))
                x += c.width * k + 10
            out.save(os.path.join(HERE, f"her_cmp_{cam.replace('.', '_')}.png"))


if __name__ == "__main__":
    if sys.argv[1] == "--report":
        report(sys.argv[2:])
    else:
        take(sys.argv[1], sys.argv[2], sys.argv[3:])
