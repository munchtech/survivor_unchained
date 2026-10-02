"""Concept art for the survivors' looks: each calling, as a woman and a man,
full figure, painted by Krea 2 on the local ComfyUI (graphs/krea_t2i.json),
or Krea 2 Large in the cloud with --large (needs a Comfy API key in
~/.comfy_api_key; never printed or written anywhere else).

    python tools/comfy/concepts.py <out dir> [--large] [--seeds 3] [name ...]

The look: dark fantasy, adult heroes, toned and generously shaped, in
revealing fantasy armour and garb, as the genre's box art paints them.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

STYLE = ("Dark fantasy video game character concept art, full body, standing heroic pose, facing the viewer, "
         "plain neutral grey studio background, painterly yet detailed, dramatic rim lighting, Diablo and Baldur's Gate art style. ")

LOOKS = {
    "warden_f": "An attractive adult woman warrior, toned athletic hourglass figure with a generous bust and wide hips, "
                "wearing revealing ornate steel plate armour: a sculpted steel breastplate with deep cleavage, bare toned midriff, "
                "an armoured battle skirt with high slits showing her thighs, steel pauldrons, gauntlets and greaves, a round shield and longsword, "
                "a short green tabard, long braided hair, confident.",
    "warden_m": "A handsome adult man, broad shouldered and heavily muscled, a hard V-shaped torso, wearing open steel plate armour: "
                "pauldrons and a leather harness over a bare muscular chest and abdomen, armoured kilt, gauntlets and greaves, round shield and longsword, "
                "short beard, strong jaw.",
    "reaver_f": "An attractive adult barbarian woman, muscular and curvy, a generous bust, wearing a skimpy fur and leather bikini armour top, "
                "a loincloth skirt of leather strips and fur, bare toned abdomen and thighs, war paint, bone and iron jewellery, a huge two-handed axe, "
                "wild red hair, fierce.",
    "reaver_m": "A handsome adult barbarian man, enormously muscular, bare chested with leather straps across the chest, fur over one shoulder, "
                "a loincloth and fur boots, war paint and scars, a huge two-handed axe, long dark hair, fierce.",
    "arcanist_f": "An attractive adult sorceress, slender with a generous bust and wide hips, wearing a revealing dark violet silk robe with a "
                  "plunging neckline and thigh-high slits, a corset belt, gold jewellery and arm bands, glowing runes, holding a carved staff, "
                  "long silver hair, sultry and dangerous.",
    "arcanist_m": "A handsome adult sorcerer, lean and toned, an open dark robe showing a sculpted chest and abdomen, gold arm bands, "
                  "glowing rune tattoos, a carved staff, swept back black hair, dangerous charm.",
    "stalker_f": "An attractive adult huntress rogue, athletic and curvy, wearing a skimpy dark leather ranger outfit: a laced leather corset top, "
                 "bare midriff, very short leather shorts, thigh-high boots, a hooded short cloak, bracers, a bow and daggers, a confident smirk.",
    "stalker_m": "A handsome adult hunter rogue, lean and muscular, a sleeveless open leather jerkin over a toned chest, hooded cloak, "
                 "leather trousers and boots, bracers, a bow and daggers, stubble, a confident smirk.",
}


def main():
    args = sys.argv[1:]
    out = os.path.abspath(args[0])
    large = "--large" in args
    seeds = 3
    if "--seeds" in args:
        seeds = int(args[args.index("--seeds") + 1])
    want = [a for a in args[1:] if a in LOOKS] or list(LOOKS)
    os.makedirs(out, exist_ok=True)
    for name in want:
        for k in range(seeds):
            dst = os.path.join(out, f"{name}_{k}.png")
            if os.path.exists(dst):
                continue
            prompt = STYLE + LOOKS[name]
            tmp = os.path.join(out, f"_{name}")
            if large:
                cmd = [sys.executable, os.path.join(HERE, "comfy.py"), "run", os.path.join(HERE, "graphs", "krea2_large.json"),
                       "--set", '1.model="Krea 2 Large"', "--set", '1.model.aspect_ratio="2:3"', "--set", f"1.seed={1000 + k}",
                       "--set", f"1.prompt={json.dumps(prompt)}", "--out", tmp]
            else:
                cmd = [sys.executable, os.path.join(HERE, "comfy.py"), "run", os.path.join(HERE, "graphs", "krea_t2i.json"),
                       "--set", "30:24.value=false", "--set", f"30:3.seed={1000 + k}", "--set", f"30:19.value={json.dumps(prompt)}",
                       "--set", '49.aspect_ratio="2:3 (Portrait Photo)"', "--out", tmp]
            subprocess.run(cmd, check=True, capture_output=True)
            made = [f for f in os.listdir(tmp) if f.endswith(".png")][0]
            os.replace(os.path.join(tmp, made), dst)
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)
            print(name, k, flush=True)


if __name__ == "__main__":
    main()
