"""Batches of review sheets in one Godot turn: python shots.py <set> <tag> [only...]
Each set is a list of (name, clip, env). Takes and gives back the godot turn."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
TURN = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
SETS = {
    "ws": [
        # The creation screen looks at her from the front, full length.
        ("front", "her/warden_show", dict(VIEW="front", WEAPON="sword+shield", FRAMES="12", STEP="6", W="300", H="520", COLS="12", LOOKY="1.0", FOV="24")),
        ("close", "her/warden_show", dict(LOOK="spine_03", OFF="-1.0,0.1,1.0", FOV="38", WEAPON="sword+shield", FIXCAM="1", FRAMES="18", STEP="4", W="240", H="300", COLS="9")),
        ("lthree", "her/warden_show", dict(LOOK="spine_03", OFF="1.0,0.15,1.1", FOV="40", WEAPON="sword+shield", FIXCAM="1", FRAMES="18", STEP="4", W="240", H="300", COLS="9")),
        ("side", "her/warden_show", dict(LOOK="spine_03", OFF="-1.7,0.15,0.2", FOV="40", WEAPON="sword+shield", FIXCAM="1", FRAMES="6", STEP="6", START="0.33", W="300", H="360", COLS="6")),
        ("hold", "her/warden_show", dict(VIEW="front", WEAPON="sword+shield", FRAMES="1", START="1.0", W="900", H="1200", COLS="1", LOOKY="1.15", FOV="16")),
    ],
    "wr": [
        # The sword hand close, from her right front, every frame of a run cycle.
        ("run", "her/run_warden", dict(LOOK="hand_r", OFF="-0.9,0.2,0.6", FOV="30", WEAPON="sword+shield", FRAMES="20", STEP="1", W="200", H="220", COLS="10")),
        ("idle", "her/idle_warden", dict(LOOK="hand_r", OFF="-0.9,0.2,0.6", FOV="30", WEAPON="sword+shield", FRAMES="5", STEP="20", W="200", H="220", COLS="5")),
        ("fore", "her/sword_fore", dict(LOOK="hand_r", OFF="-0.9,0.3,0.9", FOV="40", WEAPON="sword+shield", FRAMES="20", STEP="1", W="200", H="220", COLS="10")),
        ("cup", "her/cup_hands", dict(LOOK="hand_r", OFF="-0.5,0.3,0.7", FOV="30", FRAMES="5", STEP="12", W="200", H="220", COLS="5")),
        ("runwide", "her/run_warden", dict(VIEW="three", WEAPON="sword+shield", FRAMES="10", STEP="2", W="240", H="360", COLS="10")),
        ("runright", "her/run_warden", dict(VIEW="left", WEAPON="sword+shield", FRAMES="11", STEP="2", W="240", H="360", COLS="11", FOV="22")),
        ("reaver", "her/sprint_reaver", dict(VIEW="left", WEAPON="axe", FRAMES="10", STEP="2", W="240", H="360", COLS="10", FOV="22")),
        ("daggers", "her/run_stalker_daggers", dict(VIEW="rthree", WEAPON="daggers", FRAMES="10", STEP="2", W="240", H="360", COLS="10", FOV="24")),
    ],
    "strikes": [
        (n, f"her/{n}", dict(VIEW="arena", PLAY="1.6", WEAPON=w, FRAMES="16", STEP="1", W="140", H="140", COLS="16", YAW="30"))
        for n, w in (("sword_back", "sword+shield"), ("sword_fore", "sword+shield"), ("sword_heavy", "sword+shield"),
                     ("axe_back", "axe"), ("axe_fore", "axe"), ("axe_heavy", "axe"), ("axes_left", "axes"), ("axes_right", "axes"),
                     ("daggers_back", "daggers"), ("daggers_fore", "daggers"), ("daggers_heavy", "daggers"),
                     ("cast_flick", "wand"), ("cast_bolt", "staff"), ("throw", "daggers"), ("chain_strike", "axe"), ("vault_back", "sword+shield"))
    ] + [
        ("sword_heavy_near", "her/sword_heavy", dict(VIEW="day", PLAY="1.6", WEAPON="sword+shield", FRAMES="16", STEP="1", W="200", H="200", COLS="16", YAW="30")),
    ],
    "c01": [
        (n, f"her/{n}", dict(VIEW=v, FRAMES="12", STEP=st, W="240", H="260", COLS="12", LOOKY=ly, FOV=fov))
        for n, v, st, ly, fov in (("lie_side_wake", "three", "18", "0.3", "26"), ("sit_back_heels", "three", "15", "0.5", "26"),
                                  ("reach_coals", "three", "12", "0.6", "26"), ("letter", "three", "18", "0.9", "24"),
                                  ("cup_hands", "three", "9", "0.9", "24"), ("kneel_to_stand_snap", "three", "6", "0.7", "28"),
                                  ("take_from_log", "rthree", "8", "0.8", "28"))
    ],
    "flinch": [
        ("run_three", "her/run_warden", dict(VIEW="rthree", WEAPON="sword+shield", GESTURE="her/flinch", GESTUREAT="0.1", FRAMES="16", STEP="1", W="200", H="300", COLS="16", FOV="24")),
        ("run_arena", "her/run_warden", dict(VIEW="arena", WEAPON="sword+shield", GESTURE="her/flinch", GESTUREAT="0.1", FRAMES="16", STEP="1", W="140", H="140", COLS="16", YAW="40")),
        ("cut_three", "her/sword_fore", dict(VIEW="rthree", WEAPON="sword+shield", GESTURE="her/flinch", GESTUREAT="0.15", PLAY="1.6", FRAMES="16", STEP="1", W="200", H="300", COLS="16", FOV="24")),
    ],
    "fist": [
        ("idle_a", "her/idle_warden", dict(LOOK="hand_r", OFF="-0.35,0.05,0.25", FOV="30", WEAPON="sword", FRAMES="1", START="1.0", W="600", H="600", COLS="1")),
        ("idle_b", "her/idle_warden", dict(LOOK="hand_r", OFF="-0.1,0.1,0.45", FOV="30", WEAPON="sword", FRAMES="1", START="1.0", W="600", H="600", COLS="1")),
        ("idle_c", "her/idle_warden", dict(LOOK="hand_r", OFF="0.05,0.05,-0.45", FOV="30", WEAPON="sword", FRAMES="1", START="1.0", W="600", H="600", COLS="1")),
        ("fore_a", "her/sword_fore", dict(LOOK="hand_r", OFF="-0.35,0.15,0.3", FOV="30", WEAPON="sword", FRAMES="1", START="0.6", W="600", H="600", COLS="1")),
    ],
    "after": [
        ("ws_front", "her/warden_show", dict(VIEW="front", WEAPON="sword+shield", FRAMES="12", STEP="6", W="300", H="520", COLS="12", LOOKY="1.0", FOV="24")),
        ("ws_hero", "him/warden_show", dict(MODEL="hero", VIEW="front", WEAPON="sword+shield", FRAMES="12", STEP="6", W="300", H="520", COLS="12", LOOKY="1.0", FOV="24")),
        ("death_game", "her/death", dict(VIEW="arena", WEAPON="sword+shield", FRAMES="12", STEP="3", W="200", H="200", COLS="12")),
        ("death_back_game", "her/death_back", dict(VIEW="arena", WEAPON="sword+shield", FRAMES="14", STEP="3", W="200", H="200", COLS="14")),
        ("death_side", "her/death", dict(VIEW="side", WEAPON="sword+shield", FRAMES="12", STEP="3", W="260", H="300", COLS="12", LOOKY="0.5", FOV="30")),
        ("getup_side", "her/get_up", dict(VIEW="side", FRAMES="12", STEP="4", W="260", H="300", COLS="12", LOOKY="0.5", FOV="30")),
        ("bull", "her/bull_rush", dict(VIEW="rthree", WEAPON="sword+shield", FRAMES="16", STEP="2", W="220", H="320", COLS="16", FOV="26")),
        ("chain", "her/chain_strike", dict(VIEW="rthree", WEAPON="axe", FRAMES="14", STEP="1", W="220", H="320", COLS="14", FOV="26")),
        ("raise", "her/cast_raise", dict(VIEW="three", WEAPON="staff", FRAMES="14", STEP="2", W="220", H="360", COLS="14", FOV="28")),
        ("twirl", "her/idle_reaver_break", dict(LOOK="hand_r", OFF="-0.8,0.3,0.9", FOV="40", WEAPON="axe", START="1.3", FRAMES="14", STEP="2", W="200", H="220", COLS="14")),
        ("flask", "her/flask_drink", dict(LOOK="Head", OFF="0.5,0.0,0.7", FOV="34", WEAPON="flask", FRAMES="12", STEP="12", W="240", H="260", COLS="12")),
        ("cup", "her/cup_hands", dict(LOOK="hand_r", OFF="-0.4,0.4,0.6", FOV="34", FRAMES="9", STEP="12", W="220", H="240", COLS="9")),
        ("letter", "her/letter", dict(LOOK="hand_r", OFF="-0.4,0.4,0.6", FOV="34", FRAMES="10", STEP="18", W="220", H="240", COLS="10")),
        ("reach", "her/reach_coals", dict(VIEW="three", FRAMES="10", STEP="12", W="220", H="300", COLS="10", LOOKY="0.6", FOV="26")),
        ("folk_die", "folk/m_die_front_armed", dict(MODEL="male", WEAPON="sword+shield", VIEW="three", FRAMES="13", STEP="2", W="220", H="300", COLS="13", LOOKY="0.6", FOV="30")),
    ],
}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
name, tag = args[0], args[1]
only = args[2:]
who = f"animation: {name} sheets"
if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", "600"]).returncode:
    sys.exit(1)
try:
    # --pack: her library (and --hero: his) packed from tools/anim/out first.
    WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274")
    sys.path.insert(0, str(WT / "tools" / "anim"))
    if "--pack" in sys.argv or "--hero" in sys.argv:
        import build
        if "--pack" in sys.argv:
            build.pack()
        if "--hero" in sys.argv:
            build.pack(WT / "tools" / "anim" / "out" / "hero", "hero")
    if "--folk" in sys.argv:
        import folk
        folk.pack()
    for shot, clip, env in SETS[name]:
        if only and shot not in only:
            continue
        args = [f"{k}={v}" for k, v in env.items()]
        subprocess.run([sys.executable, str(HERE / "rsheet.py"), f"{name}_{shot}_{tag}.png", clip, *args])
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
