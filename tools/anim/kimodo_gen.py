"""Motion for her from words: Kimodo (NVIDIA, Kimodo-SOMA-RP, NVIDIA Open
Model License; trained on Bones Studio's game motion capture).

    python tools/anim/kimodo_gen.py [names]        every take in PROMPTS (or those named)

Each take is generated in Kimodo's own environment (C:/Users/munch/Tools/
kimodo/.venv: Python 3.11, torch for CUDA 12.8, Kimodo built from source with
Visual Studio's compiler) and written as T-pose BVH to C:/Users/munch/Tools/
mocap/kimodo/<name>.bvh, which clips/generated.py retargets onto her.

Kimodo's text encoder is LLM2Vec on Meta's Llama 3 8B Instruct, a gated
model: the Hugging Face account whose read token is in
%USERPROFILE%/.cache/huggingface/token must have been granted it. The text
encoder runs on the CPU (TEXT_ENCODER_DEVICE=cpu) so Kimodo needs under 3 GB
of the shared GPU.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

KIMODO = Path(os.environ.get("KIMODO_DIR", r"C:\Users\munch\Tools\kimodo"))
PY = KIMODO / ".venv" / "Scripts" / "python.exe"
OUT = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap")) / "kimodo"

# name: (prompt, seconds, seed). Written in Kimodo's own plain, physical
# terms (its card asks for neutral descriptions).
PROMPTS = {
    "leap": ("A person runs forward and leaps high over an obstacle, landing on both feet and running on.", 3.0, 7),
    "vault": ("A person runs forward, plants one hand on a low wall and vaults sideways over it, landing running.", 3.0, 7),
    "bull_rush": ("A person charges forward low behind a shield held in the left arm, then stops hard with a shove.", 2.5, 7),
    "chain_haul": ("A person throws a rope forward with the right hand and hauls it back hand over hand, leaning back.", 3.0, 7),
    "hit_heavy": ("A person is struck hard in the chest, staggers backward two steps, almost falls, and recovers.", 2.5, 7),
    "hit_left": ("A person is hit on the left side of the head, the head snaps right, they stagger and recover.", 2.0, 7),
    "hit_right": ("A person is hit on the right side of the head, the head snaps left, they stagger and recover.", 2.0, 7),
    "knockdown": ("A person is knocked backward off their feet onto their back, then rolls and gets up.", 4.0, 7),
    "talk": ("A woman stands talking, gesturing with both hands while she speaks, shifting her weight.", 6.0, 7),
    "kneel": ("A person kneels down on one knee, rests a moment with head bowed, and stands up.", 5.0, 7),
    "cheer": ("A person raises a fist in the air and cheers.", 2.5, 7),
    "wave": ("A person waves to someone far away with the right hand.", 2.5, 7),
    "shrug": ("A person shrugs with both shoulders and spreads their hands.", 2.0, 7),
    "bow": ("A person bows politely, one hand on the chest.", 2.5, 7),
}


def gen(name, prompt, seconds, seed):
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEXT_ENCODER_DEVICE="cpu", TEXT_ENCODER_MODE="local")
    stem = OUT / name
    r = subprocess.run([str(PY), "-m", "kimodo.scripts.generate", prompt, "--model", "Kimodo-SOMA-RP-v1.1",
                        "--duration", str(seconds), "--seed", str(seed), "--output", str(stem), "--bvh",
                        "--bvh_standard_tpose"], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:])
        return None
    return stem.with_suffix(".bvh")


def main(argv):
    for name, (prompt, seconds, seed) in PROMPTS.items():
        if argv and name not in argv:
            continue
        print(name, gen(name, prompt, seconds, seed))


if __name__ == "__main__":
    main(sys.argv[1:])
