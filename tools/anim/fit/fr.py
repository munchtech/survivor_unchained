"""fr.py DIR [names] (PITCH env, default 62): the sword arm's read at the den camera, as played (m11's played()).
Per facing psi (0 = facing the camera): on-screen (m, ortho) fist below the right shoulder (dn, + = lower on screen),
fist out from the pelvis (ox, + = out to her right side on screen), elbow below shoulder, blade tip below fist and
its on-screen length; min/mean over frames.
FR_JSON=FILE also writes the numbers as data ({clip: {psi: {fist_dn: [min, mean], ox, elbow_dn, tip_dn: [min, mean], len}}}):
tools/anim/fit/carry_ref_a.json is this run on A's judged clips, the reference carry_read.py holds any body to."""
import sys, math, os
sys.argv += [] ; os.environ.setdefault("PITCH", "62")
sys.path.insert(0, os.path.dirname(__file__))
import m11, json
import numpy as np
from m11 import sk, played, arrays, I, qrot, qmul, qaxis, grip_of
from pathlib import Path
P = math.radians(float(os.environ["PITCH"])); CP, SP = math.cos(P), math.sin(P)
def scr(v, psi):
    s, c = math.sin(math.radians(psi)), math.cos(math.radians(psi))
    wx = v[..., 0] * c + v[..., 2] * s; wz = -v[..., 0] * s + v[..., 2] * c
    return wx, v[..., 1] * CP - wz * SP
REF = {}
D = Path(sys.argv[1]); names = sys.argv[2:] or [f.stem for f in sorted(D.glob("*.json"))]
for n in names:
    d = json.load(open(D / f"{n}.json")); tilt = float((d.get("meta") or {}).get("grip_tilt", 0) or 0)
    dp, _, _ = played(d); rot, pos = arrays(dp); g, p = sk.fk(rot, pos)
    h, la, ua, pel = I("hand_r"), I("lowerarm_r"), I("upperarm_r"), I("pelvis")
    lq = qaxis([1.0, 0, 0], -grip_of("sword+shield", tilt)["r"])
    b = qrot(qmul(g[:, h], lq), np.broadcast_to([0, 0, 1.0], (len(rot), 3)))
    out = [n]
    for psi in (0, -30, 30, 90, 180):
        fx, fy = scr(p[:, h] - p[:, ua], psi); ex, ey = scr(p[:, la] - p[:, ua], psi)
        px, _ = scr(p[:, h] - p[:, pel], psi); tx, ty = scr(0.95 * b, psi)
        sgn = -1.0 if math.cos(math.radians(psi)) >= 0 else 1.0  # her right is screen-left facing the camera
        REF.setdefault(n, {})[str(psi)] = {"fist_dn": [round(float((-fy).min()), 3), round(float((-fy).mean()), 3)], "ox": round(float((sgn*px).min()), 3), "elbow_dn": round(float((-ey).mean()), 3), "tip_dn": [round(float((-ty).min()), 3), round(float((-ty).mean()), 3)], "len": round(float(np.hypot(tx, ty).min()), 3)}
        out.append(f"psi{psi:4d}: fist dn {(-fy).min():.2f}/{(-fy).mean():.2f} ox {(sgn*px).min():.2f} elbow dn {(-ey).mean():.2f} tip dn {(-ty).min():.2f}/{(-ty).mean():.2f} len {np.hypot(tx,ty).min():.2f}")
    print("\n   ".join(out))
if os.environ.get("FR_JSON"):
    json.dump({"pitch": float(os.environ["PITCH"]), "clips": REF}, open(os.environ["FR_JSON"], "w"), indent=1)
