"""Before/after strips for the wrist pass: python strips.py <tag>
Each clip: a close-up strip on the arm at full frame rate, and one at the game's camera."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
tag = sys.argv[1]
only = sys.argv[2:]
JOBS = [
    # name, clip, close-up env, frames
    ("run_reaver", "her/run_reaver", dict(LOOK="spine_03", OFF="1.1,0.15,0.75", FOV="34", WEAPON="axe"), 19),
    ("idle_arcanist_break", "her/idle_arcanist_break", dict(LOOK="spine_03", OFF="0.9,0.1,1.0", FOV="34", WEAPON="staff", STEP="3"), 30),
    ("death_back", "her/death_back", dict(LOOK="pelvis", OFF="1.6,0.6,1.4", FOV="40"), 30),
    ("warden_show", "her/warden_show", dict(LOOK="spine_03", OFF="-1.0,0.1,1.0", FOV="38", WEAPON="sword+shield", STEP="2"), 30),
    ("f_die_side", "folk/f_die_side", dict(MODEL="female", LOOK="pelvis", OFF="1.6,0.8,1.4", FOV="40"), 24),
]
for name, clip, env, frames in JOBS:
    if only and name not in only:
        continue
    step = env.pop("STEP", "1")
    args = [f"{k}={v}" for k, v in env.items()]
    subprocess.run([sys.executable, str(HERE / "rsheet.py"), f"w_{name}_{tag}_close.png", clip, *args, "FIXCAM=1",
                    f"FRAMES={frames}", f"STEP={step}", "W=200", "H=260", "COLS=10"])
    model = [a for a in args if a.startswith("MODEL=") or a.startswith("WEAPON=")]
    subprocess.run([sys.executable, str(HERE / "rsheet.py"), f"w_{name}_{tag}_game.png", clip, "VIEW=arena", *model,
                    f"FRAMES={min(frames, 20)}", f"STEP={step}", "W=160", "H=200", "COLS=10"])
