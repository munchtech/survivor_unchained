"""Storyboard frames for the cinematics, painted by Krea 2 (local ComfyUI,
tools/comfy/graphs/krea_t2i.json), 21:9, saved as JPEG in docs/cinematics/boards."""
import json, os, subprocess, sys

ROOT = os.getcwd()
COMFY = os.path.join(ROOT, 'tools', 'comfy', 'comfy.py')
GRAPH = os.path.join(ROOT, 'tools', 'comfy', 'graphs', 'krea_t2i.json')
OUT = os.path.join(ROOT, 'docs', 'cinematics', 'boards')
STYLE = ("Cinematic film still, anamorphic widescreen, dark fantasy, painterly, low-key lighting, deep shadows, "
         "realistic proportions, muted colour grade with blue-green shadows and warm firelight, film grain. ")

FRAMES = {
    "c01_s08_no_breath": "Extreme close-up of a young woman's face at night, soaked to the skin, wet dark hair plastered to her cheek with a "
                         "ribbon of green river weed caught in it, lying awake by dying embers; warm orange ember light on one side of her face, "
                         "cold blue moonlight on the other; behind her a wall of black birch trunks; frost glittering on the grass; her lips "
                         "slightly parted as she breathes out, and no vapour at all in the freezing air; an uneasy stillness.",
    "c02_s07_lamp_to_face": "Night, a wide shallow river ford in thick mist; a giant hooded figure with a long beard heavy with river water, "
                            "eyes like two points of cold blue light, stands knee-deep and bends down to hold an iron lantern burning with "
                            "cold blue light up to the face of a much smaller woman warrior standing at the water's edge, looking up into it; "
                            "two iron lamp posts with blue flames behind them in the mist; drowned figures standing waist-deep in the water "
                            "in the background, heads bowed. Profile two-shot.",
    "c03_s08_heart": "Close side view of a woman's outstretched fingertips reaching toward a rough, fist-sized lump of grey stone, "
                     "irregular like a river stone, not heart-shaped, glowing from within with cold blue-white light, hovering above "
                     "dark river water at night; its glow stretches toward her fingers like light drawn through a keyhole; water "
                     "dripping from the stone; mist; everything else in darkness; no flame, no candle.",
    "c04_a5_first_breath": "Close-up of a tired young woman in a forest at dawn, low golden sunlight from the right raking across her face, "
                           "her breath a long white plume of vapour in the frozen air, lit gold against the dark shade of birch trees behind "
                           "her; frost on her collar; damp hair; the faintest smile, as if surprised by her own breath.",
    "c07_s04_hammer_raised": "A broad blacksmith with close-cropped dark hair, stripped to the waist in a leather apron, seen from across the anvil, his hammer "
                             "raised and held still above glowing iron that is cooling from orange to grey; forge fire behind him rim-lighting "
                             "his shoulders; on the wall beside the forge door a wooden rack with two black iron lamp cages hanging from hooks; "
                             "a dusty village street in daylight in the foreground, out of focus; a silence you can see.",
    "c09_s01_tower_roof": "High wide shot of a flat lead tower roof at night above a small walled medieval town; an old woman in violet robes "
                          "seated at a small square table with a single warm oil lamp and a closed ledger; a low parapet; beyond her, a vast "
                          "black wooded valley under stars with only a few tiny distant lights in it, a red pump light in far hills, a few "
                          "small campfires in a ravine; a hatch in the roof opening as a figure climbs up; cold wind.",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    from PIL import Image
    for k, (name, prompt) in enumerate(FRAMES.items()):
        dst = os.path.join(OUT, name + '.jpg')
        if os.path.exists(dst):
            continue
        tmp = os.path.join(OUT, '_' + name)
        cmd = [sys.executable, COMFY, 'run', GRAPH, '--set', '30:24.value=false', '--set', f'30:3.seed={4200 + k}',
               '--set', f'30:19.value={json.dumps(STYLE + prompt)}', '--set', '30:5.width=1536', '--set', '30:5.height=640', '--out', tmp]
        subprocess.run(cmd, check=True, capture_output=True)
        made = [f for f in os.listdir(tmp) if f.endswith('.png')][0]
        Image.open(os.path.join(tmp, made)).convert('RGB').save(dst, quality=86)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
        print(name, flush=True)


if __name__ == '__main__':
    main()
