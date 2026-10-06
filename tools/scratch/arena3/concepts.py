"""Concept frames for the ember scars, as a target to build toward: Krea 2 on
the local ComfyUI. python concepts.py OUT [name ...] [--seeds N]"""
import json, os, subprocess, sys

TOOLS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\tools\comfy"
STYLE = ("Video game screenshot of a dark fantasy action RPG like Diablo IV and Path of Exile 2, "
         "the camera high above looking steeply down at the ground at 55 degrees, an arena-sized clearing filling the frame, "
         "night, highly detailed ground textures and props, rich but dark colours, cinematic lighting, no characters, no UI. ")
PLACES = {
    "hollow": "A clearing in an ancient dark forest at night. Thick black-brown leaf litter with patches of deep green moss, "
              "huge gnarled roots creeping in from enormous trees at the edge, a slow stream winding across one side carrying faintly glowing "
              "sickly yellow-green slurry between wet black mud banks and pale stones, fallen mossy trunks, clumps of ferns, "
              "moonlight falling through the canopy in soft blue pools, cold mist lying low by the water, "
              "a thin glowing orange ember line burning round the clearing's edge like the edge of burning paper.",
    "dig": "An open clay quarry mine at night. Ochre and rust-brown clay ground stained dark, black spoil heaps, "
           "a straight line of mine cart rails on wooden sleepers crossing the working, puddles of glossy slurry faintly glowing yellow-green, "
           "stepped terraced quarry walls round the edge, oil lamps on poles casting warm gold pools of light, "
           "at one side a deep pit mouth glowing red from far below with a timber headframe and winding wheel over it and smoke rising lit red, "
           "a thin glowing orange ember line burning round the edge.",
    "barrow": "An ancient barrow field at night. A straight broken old imperial road of sunken stone slabs crossing dark withered grass, "
              "long grassy burial mounds, opened graves with heaps of dark earth, weathered headstones in ordered rows, patches of burned ash, "
              "cold blue moonlight with long shadows, low mist in the hollows, a sealed stone door in a great mound at the edge, "
              "a thin glowing orange ember line burning round the edge.",
    "ruts": "A sunken muddy caravan road in a narrow ravine at night. Deep wagon ruts filled with water reflecting the moon, trampled mud, "
            "grassy verges, a bandit camp at one side with small campfires, a wooden palisade, red rags on poles, a cage, "
            "wrecked wagons and spilled crates on the road, rocky ravine walls, "
            "a thin glowing orange ember line burning round the edge.",
}


def main():
    a = sys.argv[1:]
    out = os.path.abspath(a[0])
    seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 2
    want = [x for x in a[1:] if x in PLACES] or list(PLACES)
    os.makedirs(out, exist_ok=True)
    for name in want:
        for k in range(seeds):
            dst = os.path.join(out, f"{name}_{k}.png")
            if os.path.exists(dst):
                continue
            tmp = os.path.join(out, "_" + name)
            cmd = [sys.executable, os.path.join(TOOLS, "comfy.py"), "run", os.path.join(TOOLS, "graphs", "krea_t2i.json"),
                   "--set", "30:24.value=false", "--set", f"30:3.seed={2000 + k}", "--set", f"30:19.value={json.dumps(STYLE + PLACES[name])}",
                   "--set", '49.aspect_ratio="16:9 (Widescreen)"', "--out", tmp]
            subprocess.run(cmd, check=True, capture_output=True)
            made = [f for f in os.listdir(tmp) if f.endswith(".png")][0]
            os.replace(os.path.join(tmp, made), dst)
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)
            print(name, k, flush=True)


if __name__ == "__main__":
    main()
