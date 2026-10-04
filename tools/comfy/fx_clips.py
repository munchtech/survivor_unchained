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
         "high contrast, nothing else in frame, no ground, no scenery, no text. "
         "The effect stays small and contained in the middle of the frame, with wide empty black space "
         "all around it; it never reaches the edges of the frame. ")

CLIPS = {
    "fire_blast": ("A violent burst of orange fire explodes outward in a ring from a single point at the centre, "
                   "roiling flames and glowing embers flung outward, then it curls into dark smoke and fades to black.", 3, 11),
    "fire_loop": ("A steady campfire flame seen from above, tongues of yellow and orange fire licking upward and "
                  "flickering continuously, sparks drifting up, the flame never changes size.", 4, 212),
    "frost_burst": ("A burst of pale blue ice and frost explodes outward from the centre, sharp ice crystals and "
                    "glittering cold mist spray out in a ring, then the frost vapour drifts and fades to black.", 3, 213),
    "storm_strike": ("A bolt of bright blue-white lightning strikes down into the centre, a blinding flash, branching "
                     "electric arcs crackle outward along the ground in every direction, then flicker out to black.", 2, 14),
    "holy_burst": ("A radiant burst of warm golden holy light blooms from the centre, soft rays and glowing motes "
                   "spread outward in a ring, shimmering, then the light gently fades to black.", 3, 215),
    "shadow_burst": ("A burst of dark violet shadow magic erupts from the centre, writhing smoky tendrils and purple "
                     "sparks lash outward, then the dark wisps dissolve and fade to black.", 3, 216),
    "nature_burst": ("A burst of vivid green spectral nature magic erupts from the centre, swirling glowing green "
                     "wisps, leaves of light and spores spiral outward, then fade to black.", 3, 217),
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
                   "then slowly thins and fades to black.", 3, 220),
    "sparks": ("A shower of bright orange-white sparks bursts from the centre, hot metal sparks flying outward "
               "in every direction with short glowing trails, then they cool and vanish.", 2, 221),
    "ember_motes": ("Glowing orange embers and tiny sparks float and swirl gently upward through the frame, "
                    "drifting, flickering, continuous, no flames.", 4, 222),
    "arcane_burst": ("A burst of bright magenta and violet arcane energy erupts from the centre, a ring of crackling "
                     "glowing runes and light shards spreads outward, then it shimmers and fades to black.", 3, 23),
    # The skills' own landings (docs/team/skills.md): each school's shape, not a generic burst.
    "frost_spikes": ("A star of jagged pale blue ice crystals bursts up out of a single point at the centre and spreads outward "
                     "along the ground in every direction, sharp glassy spikes catching the light, glittering frost, then the ice "
                     "cracks and crumbles into cold mist and fades to black.", 3, 301),
    "holy_ring": ("A thin perfect ring of brilliant white-gold light expands outward from the centre like a shockwave, fine golden "
                  "rays and glittering motes along its edge, the middle stays dark, then the ring fades as it widens.", 2, 302),
    "blood_scythe": ("A sweeping circular slash of dark crimson energy spins once around the centre in a full circle, a curved "
                     "blade of blood-red light trailing red mist and black shadowy wisps, then it dissolves into dark red smoke "
                     "and fades to black.", 2, 303),
    "moon_burst": ("A burst of cold silver and lavender moonlight erupts from the centre, a bright white crescent flashes and "
                   "shatters into pale violet shards of light and glittering stardust that drift outward, then fade to black.", 3, 304),
    "ice_shatter": ("A block of pale blue ice shatters at the centre into dozens of glittering transparent crystal fragments that "
                    "fly outward in every direction, with a small puff of frosty white mist, then the shards vanish.", 2, 305),
    "poison_cloud": ("A churning cloud of sickly luminous green poison gas swirls slowly in place at the centre, thick toxic vapour "
                     "curling and rolling, small bubbles of green light rising and popping, continuous, the cloud never grows.", 4, 306),
    "bramble_burst": ("Dark twisted thorny bramble vines with long sharp thorns burst up out of the centre and spread outward in a "
                      "tangle of curling stems, faint green light glowing along them, then they wither and fade to black.", 3, 307),
    "gold_flare": ("A sudden brilliant flash of golden sunlight at the centre with long sharp star-shaped rays and a lens flare, "
                   "it blooms and fades quickly to black.", 2, 308),
    "fireball_impact": ("A fireball slams down into the centre: a violent splash of orange fire and molten glowing embers bursts "
                        "outward in a ring, chunks of burning debris flung out, then thick dark smoke rises and fades to black.", 3, 309),
    "dust_chop": ("A heavy blade chops into dry earth at the centre: a sharp spray of brown dirt clods, pebbles and dust fans "
                  "outward, then the dust settles and fades to black.", 2, 310),
    "shadow_wisps": ("Inky black-violet shadow smoke tendrils lash outward from the centre like grasping fingers, with faint purple "
                     "sparks, then curl back and dissolve to black.", 3, 311),
    "leaf_burst": ("A burst of glowing green leaves, seeds and pollen spores swirls outward from the centre in a spiral gust, then "
                   "drifts and fades to black.", 3, 312),
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
                        # Square, so a burst has room to finish in every
                        # direction: in 16:9 it ran into the top and bottom of
                        # the frame and was cut off in straight lines.
                        "--set", "409.aspect_ratio=\"1:1 (Square)\"",
                        "--out", tmp], check=True)
        made = [f for f in os.listdir(tmp) if f.endswith(".mp4")]
        os.replace(os.path.join(tmp, made[0]), dst)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)


if __name__ == "__main__":
    main()
