"""Reference faces for the heroine's faces, painted by the local ComfyUI
(Krea 2 turbo): each a photograph of one beautiful young woman, seen from in
front and from three-quarters side by side, in flat studio light, so the
shape of her face can be read off it (tools/assets/face_fit.py fits the
heroine's sliders to it, by the landmarks of each view).

    python tools/assets/face_refs.py <out dir> [name ...]

The faces are FACES below (docs/FACE_RESEARCH.md says why each is as it is).
Several seeds a face are painted (SEEDS), for the best to be chosen by eye.
ComfyUI must be running; its models are freed after.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comfy"))
import comfy  # noqa: E402

# What every reference shares: one woman, two views, nothing in the way of
# her face's shape (hair back, no makeup to speak of, even light).
FRAME = ("A high-end beauty campaign photograph for a luxury cosmetics brand, two head-and-shoulders portraits of the same "
         "breathtakingly beautiful young woman side by side on a plain warm-grey studio background. On the left she faces the "
         "camera straight on; on the right the same woman is turned to a three-quarter view, facing to the left. Same face, same "
         "hair, same light in both. Her hair is pulled back sleekly off her face and ears, her forehead and hairline visible. Bare "
         "shoulders. Serene, alluring neutral expression, full lips softly closed, eyes looking ahead. Soft flattering beauty-dish "
         "light, even and glowing, no harsh shadows. Shot on an 85mm lens at eye level, sharp focus, luminous healthy skin with fine "
         "natural texture, subtle elegant makeup: defined lashes, groomed brows, a soft lip tint. {who}")

# Each face: who she is (the words that make her), for a preset of the same name.
FACES = {
    "heroine": "She is a stunningly beautiful woman of twenty-four with fair porcelain skin and light freckles across her nose "
               "and cheeks, bright green almond eyes with a slight upward tilt, softly arched auburn brows, a small straight nose "
               "with a gently upturned tip, full soft rose lips, high cheekbones, a delicate tapered jaw and a small chin, a slender neck. "
               "Copper-red hair.",
    # Her other faces to start from: each a different bone structure and
    # blood, every one of them beautiful (FACE_RESEARCH.md 3: presets differ
    # by bone structure, never by oddity).
    "highborn": "She is a stunningly beautiful Scandinavian woman of twenty-five with pale porcelain skin, clear ice-blue eyes, high "
                "sculpted cheekbones, a long elegant straight nose, a narrow refined jaw and a delicate pointed chin, fine straight ash-blonde "
                "brows, full soft lips, a long slender neck. Platinum blonde hair.",
    "vixen": "She is a breathtakingly beautiful Slavic woman of twenty-three with fair skin, striking upturned feline grey-green eyes, high "
             "wide cheekbones, a small straight nose, full pouting lips with a sharply defined cupid's bow, a small sharp chin, softly arched "
             "dark brows. Dark brown hair.",
    "doe": "She is a stunningly beautiful Mediterranean woman of twenty-four from southern Italy with warm olive skin, large soft dark brown "
           "almond eyes, thick dark arched brows, a refined straight nose, full lips, a soft rounded jaw, a gentle oval face. Dark brown hair.",
    "sunborn": "She is a stunningly beautiful West African woman of twenty-four with deep dark brown skin, large wide-set dark eyes, high "
               "rounded cheekbones, a soft broad nose, full sculpted lips, a smooth oval face with a delicate chin, a graceful long neck. "
               "Black hair.",
    "moonlit": "She is a stunningly beautiful East Asian woman of twenty-three with fair luminous skin, elegant almond-shaped dark eyes, "
               "straight soft brows, a small refined nose, full soft lips, a smooth heart-shaped face with a small delicate chin. Black hair.",
    "saffron": "She is a stunningly beautiful South Asian woman of twenty-four with warm golden-brown skin, large expressive dark eyes with "
               "long lashes, strong elegantly arched dark brows, a refined gently aquiline nose, full lips, high cheekbones, an oval face. "
               "Black hair.",
    "wildling": "She is a stunningly beautiful Latina woman of twenty-four with warm tan skin, wide bright hazel eyes, a wide mouth with "
                "full lips made for laughing, a softly rounded nose tip, high full cheekbones, a heart-shaped face. Dark brown hair.",
    "hardwon": "She is a stunningly beautiful athletic woman of twenty-six with lightly tanned skin and a few freckles, steady grey eyes, "
               "straight strong brows, a defined angular jaw, a straight nose, full firm lips, sculpted cheekbones: a fierce warrior beauty "
               "with the face of a fashion model. Dark blonde hair.",
    "fey": "She is a stunningly beautiful ethereal elfin woman of twenty-two with luminous pale skin, very large wide-set grey eyes with an "
           "upward tilt, very high sharp cheekbones, a tiny refined nose, small full lips, a narrow pointed chin, delicate fine brows, and "
           "softly pointed elf ears. Silver-white hair.",
}
SEEDS = [11, 23, 37, 41]


def graph(text, seed, prefix, size=(1536, 1024)):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": size[0], "height": size[1], "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0],
                                                    "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                                                    "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


def free():
    """The GPU given back (the server answers with nothing)."""
    import urllib.request
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    names = sys.argv[2:] or list(FACES)
    try:
        for name in names:
            for seed in SEEDS:
                dst = os.path.join(out, f"{name}_{seed}.png")
                if os.path.exists(dst):
                    continue
                got = comfy.run(graph(FRAME.format(who=FACES[name]), seed, f"face_ref_{name}"), out)
                os.replace(got[0], dst)
                print("REF", dst)
    finally:
        free()
