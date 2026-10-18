import sys, math
from pathlib import Path
args0 = sys.argv[1:]
sys.argv = ["x"] + [a for a in args0 if a in ("--body", "hero")]
P = Path(__file__).with_name("stance.py")
exec(open(P).read().split("if args and")[0].replace("Path(__file__)", f"Path(r'{P}')"))
from rig import qangle
pairs = [a for a in args0 if ":" in a]
body_bones = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head", "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r",
              "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r"]
for i in range(0, len(pairs), 2):
    (na, wa), (nb, wb) = pairs[i].split(":"), pairs[i + 1].split(":")
    ra, pa = load(na); rb, pb = load(nb)
    ia = -1 if wa == "end" else 0; ib = -1 if wb == "end" else 0
    ga, _ = sk.fk(ra, pa); gb, _ = sk.fk(rb, pb)
    d = sorted(((qangle(qmul(qinv(ga[ia, sk.i(b)]), gb[ib, sk.i(b)])), b) for b in body_bones), reverse=True)[:5]
    print(pairs[i], "->", pairs[i + 1], "global turn:", ", ".join(f"{b} {v:.1f}" for v, b in d))
