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
    "shamble_lurch": ("A zombie lurches forward on stiff legs, swaying, both arms reaching out in front", 6.0, 5),

    # Her deaths, to set beside the keyed ones.
    "death_back": ("A person is hit hard in the chest, staggers back one step and collapses onto their back and lies still", 4.0, 9),
    "death_front": ("A person is hit hard in the back, drops to their knees and falls forward onto their face and lies still", 4.0, 9),

    # Combat's new minions and heavies (docs/team/combat.md).
    "kneel_shoot": ("A person drops to one knee, raises a crossbow to the shoulder, aims and shoots", 4.0, 7),
    "slam": ("A big heavy man raises both fists high above his head and slams them down onto the ground", 3.0, 7),

    # The cinematics (docs/team/cinematics.md), C01: the survivor wakes.
    "lie_side_wake": ("A person lies completely still on their right side on the ground, then slowly and wearily pushes up onto one elbow", 7.0, 13),
    "sit_back_heels": ("A person lying propped on one elbow slowly sits up and settles back to kneel on their heels, looking down at their hands", 6.0, 13),
    "letter": ("A kneeling person takes a folded letter from inside their coat, unfolds it, reads it, folds it again and puts it back", 8.0, 13),
    "kneel_to_stand_snap": ("A kneeling person snaps their head round to look behind them and springs to their feet in one movement without using their hands", 3.0, 13),
    "take_from_log": ("A person grabs a sword leaning against a log at hip height and turns round holding it ready to fight", 3.0, 13),
    "cup_hands": ("A kneeling person cups both hands in front of their chest, looks down into them and waits", 4.0, 13),
    # C02: the Warden in the ford, and the drowned.
    "lie_arm_up": ("A person lies still on their back with the left forearm held straight up", 4.0, 13),
    "rise_stiff": ("An old man lying on his back slowly sits up and then stiffly gets to his feet, like getting out of a cold bath", 7.0, 13),
    "wade_drag": ("A big man wades slowly forward through deep water, dragging a heavy sword behind him in the right hand", 6.0, 13),
    "bend_lift": ("A tall man bends a long way down and lifts a lamp up to a face low in front of him, tilting his head", 4.0, 13),
    "bowed_turn": ("A person stands still with the head bowed, then slowly turns the head to the left", 5.0, 13),
    # C03.
    "kneel_fall": ("A big man drops to his knees holding his left arm up, slowly lowers the arm, and folds forward to lie face down", 7.0, 13),
    "reach_flinch": ("A woman slowly reaches one hand toward something floating in front of her chest, then flinches back", 4.0, 13),
    "burst_hug": ("A crouching person bursts upward, snatches something with both hands and hugs it to their chest", 3.0, 13),
    "sniff": ("A person sniffs the air twice, head raised", 2.5, 13),
    "laugh": ("A person laughs so hard their shoulders and belly shake", 3.0, 13),
    "dive": ("A person dives head first down toward the ground", 2.5, 13),
    # C04: the morning, the walk to the Waystation.
    "wade_out": ("A woman wades out of shin-deep water and steps up onto a bank", 5.0, 13),
    "sun_face": ("A woman stands still with her face tilted up to the sun and her eyes closed, breathing slowly", 5.0, 13),
    "flask_drink": ("A person lifts a flask hanging on a cord, pulls the cork out with their teeth, sniffs it and takes a long drink", 6.0, 13),
    "walk_uphill": ("A tired person walks slowly up a hill, leaning forward", 6.0, 13),
    "unfold_arms": ("A person standing with arms folded unfolds them and lets them hang", 3.0, 13),
    "ladder": ("A man carrying a long ladder on his shoulder walks, stops and turns round", 5.0, 13),
    "well_bucket": ("A woman hauls a bucket up out of a well and pauses, holding it", 5.0, 13),
    "child_run": ("A child runs forward happily", 4.0, 13),
}

# Made first, so a run stopped early has what is wanted soonest: the
# opening's wake (C01), the Warden's rise (C02), combat's crossbow and slam,
# the Warden's fall (C03) and the flask (C04).
FIRST = ["lie_side_wake", "sit_back_heels", "rise_stiff", "bend_lift", "kneel_shoot", "slam", "kneel_fall", "flask_drink"]


def main(argv):
    dry = "--dry" in argv
    names = [a for a in argv if not a.startswith("--")]
    order = FIRST + [n for n in PROMPTS if n not in FIRST]
    jobs = [dict(name=n, prompt=PROMPTS[n][0] + ".", seconds=PROMPTS[n][1], seed=PROMPTS[n][2], takes=TAKES)
            for n in order if not names or n in names]
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
