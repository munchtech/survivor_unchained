"""Motion for her and the townsfolk from words: Kimodo (NVIDIA,
Kimodo-SOMA-RP, NVIDIA Open Model License; trained on Bones Studio's game
motion capture).

    python tools/anim/kimodo_gen.py [names]        every prompt below (or those named)
    python tools/anim/kimodo_gen.py --dry [names]  the run with noise for words (tests the rest)

One run in Kimodo's own environment (C:/Users/munch/Tools/kimodo/.venv:
Python 3.11, torch for CUDA 12.8, Kimodo built from source) loads the model
once and makes every prompt, TAKES takes each, as T-pose BVH in
C:/Users/munch/Tools/mocap/kimodo/<name>_<k>.bvh (kimodo_batch.py), which
clips/generated.py retargets. Prompts already made are skipped, so a run
that stops can be started again; delete a prompt's BVHs to make it anew.

Kimodo's text encoder is LLM2Vec on Meta's Llama 3 8B Instruct, a gated
model: the Hugging Face account whose read token is in
%USERPROFILE%/.cache/huggingface/token must have been granted it (the first
run downloads it, about 16 GB). The encoder runs on the CPU in about 16 GB
of RAM, so Kimodo needs under 3 GB of the shared GPU.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIMODO = Path(os.environ.get("KIMODO_DIR", r"C:\Users\munch\Tools\kimodo"))
PY = KIMODO / ".venv" / "Scripts" / "python.exe"
MOCAP = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap"))
TAKES = 3

# name: (prompt, seconds, seed). One sentence each (Kimodo reads a full stop
# as the start of the next prompt), in its own plain, physical terms (its
# card asks for neutral descriptions). What each is for is beside it.
PROMPTS = {
    # Her arts, as the game plays them (godot/logic/Sim/Arts.cs).
    # Vault: she springs 6 m back from where she aims, 0.32 s in the air.
    "vault": ("A person jumps far backward off both feet, tucks the knees in the air and lands low in a crouch", 2.5, 11),
    # Bull Rush: 9 m in 0.4 s behind a shield, ramming through.
    "bull_rush": ("A person charges forward with the left shoulder lowered, rams into something hard and stops", 2.5, 11),
    # Grapple Chain: the chain bites and hauls her to it, a blow on arrival.
    "chain_haul": ("A person is yanked forward off their feet, flies forward with both arms reaching out and lands striking down hard with the right hand", 3.0, 11),
    # The Crashing Leap (Mixamo's is in the game): one to compare.
    "leap": ("A person runs two steps, leaps high and smashes down with both hands as they land in a crouch", 3.0, 11),
    # Blows taken and falls.
    "hit_heavy": ("A person is struck hard in the chest, staggers backward two steps, almost falls, and recovers", 2.5, 7),
    "hit_left": ("A person is hit on the left side of the head, the head snaps right, they stagger and recover", 2.0, 7),
    "hit_right": ("A person is hit on the right side of the head, the head snaps left, they stagger and recover", 2.0, 7),
    "hit_back": ("A person is struck in the back and stumbles forward two steps, then turns around", 2.5, 7),
    "knockdown": ("A person is knocked backward off their feet onto their back, then rolls and gets up", 4.0, 7),
    # Her in town and in the story.
    "her_hip_idle": ("A woman stands with her weight on one leg and a hand on her hip, looking around", 6.0, 5),
    "her_walk": ("A confident woman walks slowly with a strong sway of her hips", 5.0, 5),
    "kneel": ("A person kneels down on one knee, rests a moment with head bowed, and stands up", 5.0, 7),
    "shrug": ("A person shrugs with both shoulders and spreads their hands", 2.0, 7),
    "bow": ("A person bows politely, one hand on the chest", 2.5, 7),
    # The townsfolk (Folk.cs, Zone.cs): what the game asks of them by name.
    "walk_man": ("A man walks forward at an easy, relaxed pace", 6.0, 3),
    "walk_woman": ("A woman walks forward at an easy pace", 6.0, 3),
    "walk_old": ("An old man walks forward slowly with a stoop", 6.0, 3),
    "arms_crossed": ("A person stands with arms crossed, shifting weight from one foot to the other", 6.0, 3),
    "talk": ("A woman stands talking, gesturing with both hands while she speaks, shifting her weight", 6.0, 7),
    "talk_man": ("A man stands talking, gesturing with one hand, shifting his weight", 6.0, 3),
    "cheer": ("A person raises a fist in the air and cheers", 2.5, 7),
    "clap": ("A person claps their hands happily", 3.0, 3),
    "wave": ("A person waves to someone far away with the right hand", 2.5, 7),
    "work": ("A person stands at a table and works at something with both hands", 4.0, 3),
    # The walking dead (the crowd's shamble).
    "shamble": ("A person shambles forward slowly, dragging the left foot, arms hanging limp", 6.0, 3),
}


def main(argv):
    dry = "--dry" in argv
    names = [a for a in argv if not a.startswith("--")]
    jobs = [dict(name=n, prompt=p + ".", seconds=s, seed=seed, takes=TAKES)
            for n, (p, s, seed) in PROMPTS.items() if not names or n in names]
    out = MOCAP / ("kimodo_dry" if dry else "kimodo")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f)
    env = dict(os.environ, TEXT_ENCODER_DEVICE="cpu", TEXT_ENCODER_MODE="local", PYTHONUNBUFFERED="1")
    print(f"Kimodo: {len(jobs)} prompts, {TAKES} takes each, into {out}")
    r = subprocess.run([str(PY), str(HERE / "kimodo_batch.py"), f.name, str(out)] + (["--dry"] if dry else []), env=env)
    os.unlink(f.name)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main(sys.argv[1:])
