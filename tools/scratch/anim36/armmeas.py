"""Arm carriage per run/sprint clip: upper-arm abduction (torso frame), elbow lateral from midline,
fist at the forward extreme (height vs shoulder, lateral from midline, forward of chest).
usage: python armmeas.py <worktree> [her|him] [name filters...]"""
import sys, math, os
from pathlib import Path
import numpy as np
WT = Path(sys.argv[1]); body = sys.argv[2] if len(sys.argv) > 2 else "her"; want = sys.argv[3:]
sys.path.insert(0, str(WT / "tools/anim"))
from keyed import Rig
from rig import DATA, Skeleton
from dataclasses import replace
from clips.run import RUNS
from clips.sprint_stop import sprint
from gait import run_cycle
sk = Skeleton.load(DATA / ("heroine_skeleton.json" if body == "her" else "hero_skeleton.json"))
rig = Rig(sk, body=body)
I = sk.index
def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)
sys.path.insert(0, str(Path(__file__).parent))
from armmetrics import metrics, fmt
j = dict(shL=I["upperarm_l"], shR=I["upperarm_r"], elL=I["lowerarm_l"], elR=I["lowerarm_r"], hdL=I["hand_l"], hdR=I["hand_r"],
         hipL=I["thigh_l"], hipR=I["thigh_r"], spine_lo=I["spine_01"], neck=I["neck_01"], chest=I["spine_03"])
for name, (g, arms, weapon) in RUNS.items():
    for kind in ("run", "sprint"):
        nm = name if kind == "run" else "sprint" + name[3:]
        if want and not any(w in nm for w in want): continue
        if os.environ.get("DEF"):
            from gait import Gait
            D = Gait(); g = replace(g, arm_fwd=D.arm_fwd, arm_back=D.arm_back, elbow_out=D.elbow_out)
        clip = run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon}) if kind == "run" else sprint(rig, name)
        grot, gp = sk.fk(clip.rot, clip.pos)
        print(fmt(nm, metrics(gp, j)), flush=True)
