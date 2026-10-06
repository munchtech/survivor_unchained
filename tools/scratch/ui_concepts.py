"""Style-target concept frames for the UI art brief (not final art): Krea 2
turbo on the local ComfyUI through the project's own graph and client."""
import json, os, subprocess, sys

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec'
HERE = os.path.join(WT, 'tools', 'comfy')
OUT = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\concepts'

STYLE = ("Dark fantasy video game user interface asset, front orthographic view, centred on a pure black background, "
         "hand-painted forged blackened iron with thin inlaid gold filigree, warm ember-orange glow, worn and battle-scarred, "
         "AAA game UI art in the style of Diablo IV and Hades, crisp edges, no text, no letters. ")

ITEMS = {
    "plate": ("1:1 (Square)", "An empty rectangular UI window frame: a dark iron panel border with riveted corner plates shaped like small "
              "shield bosses, a thin gold inlay line running inside the border, the inside of the frame plain flat dark charcoal, symmetrical."),
    "card": ("2:3 (Portrait Photo)", "An empty tall playing-card frame for a level-up choice: blackened iron border with gold filigree, a small "
             "ember gemstone set at the top centre glowing orange, a circular empty medallion socket in the upper third, plain dark inside, symmetrical."),
    "minimap": ("1:1 (Square)", "An empty circular minimap frame ring: a thick round band of blackened iron with gold inlay, four small compass "
                "studs at north east south west, the north stud a small gold arrowhead, the centre of the ring empty and pure black."),
    "slots": ("16:9 (Widescreen)", "A row of six empty square inventory slot frames sunk into dark iron, each with a different coloured thin "
              "inner rim: grey, green, blue, violet, orange, red-orange, subtle glow inside the rarer ones, symmetrical, evenly spaced."),
    "icons": ("1:1 (Square)", "A three by three grid of painted fantasy skill icons on dark round medallions: a flaming sword slash, a frost shard, "
              "a lightning bolt, a holy sun, a shadow tendril, a thorned vine, an arcane star, a wolf head, a healing heart; bold readable silhouettes."),
    "bars": ("16:9 (Widescreen)", "Three long horizontal resource bar frames stacked vertically with gaps: an ornate iron bar casing with gold end caps; "
             "the top bar filled with glowing ember orange liquid fire, the middle with deep blood red, the bottom with pale moonlit blue."),
    "logo": ("16:9 (Widescreen)", "A dark fantasy game title logo reading \"SURVIVOR UNCHAINED\" in carved gold Roman capital letters with a broken iron "
             "chain worked through the letters, glowing embers, on black."),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1:] or list(ITEMS)
    for name in want:
        ratio, text = ITEMS[name]
        dst = os.path.join(OUT, f"{name}.png")
        if os.path.exists(dst):
            continue
        prompt = (STYLE if name != "logo" else "") + text
        tmp = os.path.join(OUT, f"_{name}")
        cmd = [sys.executable, os.path.join(HERE, "comfy.py"), "run", os.path.join(HERE, "graphs", "krea_t2i.json"),
               "--set", "30:24.value=false", "--set", "30:3.seed=4242", "--set", f"30:19.value={json.dumps(prompt)}",
               "--set", f'49.aspect_ratio="{ratio}"', "--out", tmp]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(name, "failed", r.stdout[-400:], r.stderr[-400:], flush=True)
            continue
        made = [f for f in os.listdir(tmp) if f.endswith(".png")][0]
        os.replace(os.path.join(tmp, made), dst)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
        print(name, "done", flush=True)


if __name__ == "__main__":
    main()
