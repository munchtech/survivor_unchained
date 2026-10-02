"""The effects library's source clips, made with LTX 2.5 on the local
ComfyUI (tools/comfy/graphs/ltx_t2v.json), each shot on black so it can be
cut into a flipbook (tools/comfy/flipbook.py).

    python tools/comfy/fx_clips.py <out dir> [name ...]

A clip already in the folder is not made again. Seeds are fixed so a clip
can be made again exactly; change the seed to try another take.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# What every prompt shares: an element on black, nothing else, the camera
# still, so it cuts cleanly into a flipbook and sits on any ground.
FRAME = ("Visual effects element for a video game, isolated on a pure black background, "
         "locked-off camera, seen from high above looking down at a steep angle, "
         "high contrast, nothing else in frame, no ground, no scenery, no text. ")

CLIPS = {
    "fire_blast": ("A violent burst of orange fire explodes outward in a ring from a single point at the centre, "
                   "roiling flames and glowing embers flung outward, then it curls into dark smoke and fades to black.", 3, 11),
    "fire_loop": ("A steady campfire flame seen from above, tongues of yellow and orange fire licking upward and "
                  "flickering continuously, sparks drifting up, the flame never changes size.", 4, 12),
    "frost_burst": ("A burst of pale blue ice and frost explodes outward from the centre, sharp ice crystals and "
                    "glittering cold mist spray out in a ring, then the frost vapour drifts and fades to black.", 3, 13),
    "storm_strike": ("A bolt of bright blue-white lightning strikes down into the centre, a blinding flash, branching "
                     "electric arcs crackle outward along the ground in every direction, then flicker out to black.", 2, 14),
    "holy_burst": ("A radiant burst of warm golden holy light blooms from the centre, soft rays and glowing motes "
                   "spread outward in a ring, shimmering, then the light gently fades to black.", 3, 15),
    "shadow_burst": ("A burst of dark violet shadow magic erupts from the centre, writhing smoky tendrils and purple "
                     "sparks lash outward, then the dark wisps dissolve and fade to black.", 3, 16),
    "nature_burst": ("A burst of vivid green spectral nature magic erupts from the centre, swirling glowing green "
                     "wisps, leaves of light and spores spiral outward, then fade to black.", 3, 17),
    "blood_splat": ("Top-down overhead shot of a single gush of thick dark red blood splashing onto a black floor: a "
                    "heavy central splash with long radial streaks, spatter and droplets thrown outward, glossy and wet, "
                    "realistic, cinematic horror film gore, the splash spreads and settles.", 2, 31),
    "blood_spray": ("A spray of dark red blood droplets and mist sprays sideways across the frame from the left, "
                    "realistic arterial spray, glossy droplets of many sizes in flight, cinematic horror, then they fall away.", 2, 32),
    "blood_burst": ("A splash of dark red blood bursts outward from the centre in a ring of droplets and streaks, "
                    "thick and glossy, then the droplets fall away out of frame.", 2, 18),
    "dust_ring": ("A heavy ground impact seen from above: a ring of brown dust and dirt and small stones blasts "
                  "outward from the centre in a shockwave, then the dust cloud settles and thins to black.", 3, 19),
    "smoke_puff": ("A thick puff of grey smoke billows outward and upward from the centre, soft and rolling, "
                   "then slowly thins and fades to black.", 3, 20),
    "sparks": ("A shower of bright orange-white sparks bursts from the centre, hot metal sparks flying outward "
               "in every direction with short glowing trails, then they cool and vanish.", 2, 21),
    "ember_motes": ("Glowing orange embers and tiny sparks float and swirl gently upward through the frame, "
                    "drifting, flickering, continuous, no flames.", 4, 22),
    "arcane_burst": ("A burst of bright magenta and violet arcane energy erupts from the centre, a ring of crackling "
                     "glowing runes and light shards spreads outward, then it shimmers and fades to black.", 3, 23),
}


def main():
    out = os.path.abspath(sys.argv[1])
    want = sys.argv[2:] or list(CLIPS)
    os.makedirs(out, exist_ok=True)
    graph = os.path.join(HERE, "graphs", "ltx_t2v.json")
    for name in want:
        dst = os.path.join(out, f"{name}.mp4")
        if os.path.exists(dst):
            continue
        text, seconds, seed = CLIPS[name]
        tmp = os.path.join(out, f"_{name}")
        print(f"{name}: {seconds}s, seed {seed}", flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, "comfy.py"), "run", graph,
                        "--set", f"405:376.value={json.dumps(FRAME + text)}",
                        "--set", f"405:362.value={seconds}",
                        "--set", f"405:339.noise_seed={seed}",
                        "--out", tmp], check=True)
        made = [f for f in os.listdir(tmp) if f.endswith(".mp4")]
        os.replace(os.path.join(tmp, made[0]), dst)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)


if __name__ == "__main__":
    main()
