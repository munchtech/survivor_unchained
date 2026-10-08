"""Test poses for her joints as JSON clips (one pose a frame), for
anim_review.gd to play unpacked: elbows, shoulders, knees, wrists.

    python rigtest.py <out dir>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import WT, elbow, knee, wrist_turn, arm_twist, arm_raise, turned, bone_dir, FRONT  # noqa: E402
from rig import Skeleton, Clip, write_clip  # noqa: E402


def arm_forward(s, deg):
    """The upper arm lifted forward (flexed) by deg."""
    def f(sk, rot):
        u = bone_dir(sk, rot, f"upperarm_{s}", f"lowerarm_{s}")
        return turned(sk, rot, sk.index[f"upperarm_{s}"], np.cross(u, FRONT), deg)
    return f


def thigh_forward(s, deg):
    def f(sk, rot):
        u = bone_dir(sk, rot, f"thigh_{s}", f"calf_{s}")
        return turned(sk, rot, sk.index[f"thigh_{s}"], np.cross(u, FRONT), deg)
    return f


def both(fn, *a):
    return [fn("l", *a), fn("r", *a)]


SETS = {
    "rig_arm": [[], both(elbow, 45), both(elbow, 90), both(elbow, 120), both(elbow, 145),
                both(elbow, 90) + [wrist_turn("l", 80, 0.5), wrist_turn("r", 80, 0.5)],
                both(elbow, 90) + [wrist_turn("l", -80, 0.5), wrist_turn("r", -80, 0.5)],
                both(elbow, 145) + [wrist_turn("l", 80, 0.5), wrist_turn("r", 80, 0.5)]],
    "rig_shoulder": [[], both(arm_raise, 60), both(arm_raise, 100), both(arm_raise, 130),
                     both(arm_twist, 70), both(arm_twist, -70),
                     both(arm_raise, 100) + both(elbow, 90), both(arm_forward, 90) + both(elbow, 45)],
    "rig_knee": [[], both(knee, 45), both(knee, 90), both(knee, 120), both(knee, 145),
                 both(thigh_forward, 90) + both(knee, 90), both(thigh_forward, 110) + both(knee, 135),
                 both(thigh_forward, -25) + both(knee, 100)],
}


def main(out):
    sk = Skeleton.load(WT / "tools" / "anim" / "data" / "heroine_skeleton.json")
    for name, poses in SETS.items():
        rots = []
        for edits in poses:
            rot = sk.rest_rot.copy()
            for fn in edits:
                rot = fn(sk, rot)
            rots.append(rot)
        # (a rest frame first: the review photographs from the second frame on)
        rot = np.array([sk.rest_rot.copy()] + rots)
        pos = np.tile(sk.rest_pos, (len(rot), 1, 1))
        write_clip(Clip(name, 30.0, rot, pos, False, {}), sk, Path(out))
        print("wrote", name, len(rots), "poses")


if __name__ == "__main__":
    main(sys.argv[1])
