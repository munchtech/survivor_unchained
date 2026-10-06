"""The wrist's bend split as anatomy splits it: flexion/extension (about the
thumb axis) and radial/ulnar deviation (about the palm's normal), per clip.
python wrist.py [names...] [--frames]   Reports maxima and frames past
FLEX 80 / EXT 70 / RADIAL 25 / ULNAR 40."""
import math
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
import audit  # noqa: E402
from rig import DATA, Skeleton, qinv, qmul  # noqa: E402

LIM = {"flex": 80, "ext": 70, "rad": 25, "uln": 40}


def split(sk, rot, f, s):
    """(flex, dev) degrees of side s's wrist at frame f: flex + toward the
    palm, dev + toward the thumb (radial)."""
    I = sk.index
    h = I[f"hand_{s}"]
    mid = I[f"middle_01_{s}"]
    y = sk.rest_pos[mid] / np.linalg.norm(sk.rest_pos[mid])
    dh = qmul(qinv(sk.rest_rot[h]), rot[f, h])
    sw, tw = audit.swing_twist(dh, y)
    # The swing itself: dh with the twist taken off.
    t = np.array([*(y * np.dot(dh[:3], y)), dh[3]])
    t = t / np.linalg.norm(t)
    # The swing in the frame the twist leaves (the wrist's axes turn with
    # the radius as the forearm rolls): dh = t * s.
    s_q = qmul(qinv(t), dh)
    if s_q[3] < 0:
        s_q = -s_q
    ang = 2 * math.acos(min(1.0, s_q[3]))
    if ang < 1e-6:
        return 0.0, 0.0
    ax = s_q[:3] / np.linalg.norm(s_q[:3])
    # The hand's own axes in its rest frame: Y along the fingers (y), Z the
    # thumb side, X = Y x Z. (Rest local frame: the rig's hand +Z is the thumb side.)
    z = np.array([0, 0, 1.0])
    z = z - y * np.dot(z, y)
    z = z / np.linalg.norm(z)
    x = np.cross(y, z)
    a = math.degrees(ang)
    flex = a * float(np.dot(ax, z)) * (1 if s == "r" else -1)
    dev = a * float(np.dot(ax, x))
    return flex, dev


def main(argv):
    want = [a for a in argv if not a.startswith("--")]
    show = "--frames" in argv
    tot = 0
    sets = audit.SETS
    if "--before" in argv:
        B = Path(__file__).parent / "out_before"
        sets = [(l, B / f.name, s) for l, f, s in sets]
    for label, folder, skel in sets:
        sk = Skeleton.load(DATA / skel)
        files = sorted(folder.glob("*.json"))
        if label == "folk_f":
            files = [f for f in files if f.stem.startswith("f_")]
        if label == "folk_m":
            files = [f for f in files if f.stem.startswith("m_")]
        for fp in files:
            if want and not any(w in fp.stem for w in want):
                continue
            d, rot, pos = audit.load(fp, sk)
            n = rot.shape[0]
            parts = []
            bad_n = 0
            for s in "lr":
                fl = np.array([split(sk, rot, f, s) for f in range(n)])
                flex, dev = fl[:, 0], fl[:, 1]
                bad = (flex > LIM["flex"]) | (-flex > LIM["ext"]) | (dev > LIM["rad"]) | (-dev > LIM["uln"])
                bad_n += int(bad.sum())
                parts.append(f"{s}: flex {flex.max():+4.0f} ext {flex.min():+4.0f} rad {dev.max():+4.0f} uln {dev.min():+4.0f} ({int(bad.sum())})")
                if show and bad.any():
                    fr = np.nonzero(bad)[0]
                    parts[-1] += " f" + ",".join(str(x) for x in fr[:12])
            tot += bad_n
            if bad_n or want:
                print(f"{label:6s} {fp.stem:28s} " + " | ".join(parts))
    print(tot, "frames past the wrist's range")


if __name__ == "__main__":
    main(sys.argv[1:])
