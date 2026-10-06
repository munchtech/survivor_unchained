"""Every built clip's worst sink below the ground (cm, past the flesh round
each joint): python groundall.py [min_cm=3] [--before]"""
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
import audit
from rig import DATA, Skeleton
mn = float([a for a in sys.argv[1:] if not a.startswith("--")][0]) if [a for a in sys.argv[1:] if not a.startswith("--")] else 3.0
base = Path(__file__).parent / "out_before" if "--before" in sys.argv else W / "out"
flesh = {"calf_l": 0.05, "calf_r": 0.05, "pelvis": 0.11, "foot_l": 0.06, "foot_r": 0.06, "ball_l": 0.015, "ball_r": 0.015,
         "hand_l": 0.02, "hand_r": 0.02, "lowerarm_l": 0.04, "lowerarm_r": 0.04, "Head": 0.10, "spine_02": 0.11}
for label, folder, skel in audit.SETS:
    sk = Skeleton.load(DATA / skel)
    I = sk.index
    files = sorted((base / folder.name).glob("*.json"))
    if label == "folk_f":
        files = [f for f in files if f.stem.startswith("f_")]
    if label == "folk_m":
        files = [f for f in files if f.stem.startswith("m_")]
    for fp in files:
        d, rot, pos = audit.load(fp, sk)
        g, p = sk.fk(rot, pos)
        worst = (0.0, None, None)
        for k, r in flesh.items():
            y = p[:, I[k], 1] - r
            f = int(np.argmin(y))
            if -y[f] > worst[0]:
                worst = (-float(y[f]), k, f)
        if worst[0] * 100 >= mn:
            print(f"{label:6s} {fp.stem:28s} {worst[1]} {100 * worst[0]:.0f} cm under at f{worst[2]} (of {rot.shape[0]})")
