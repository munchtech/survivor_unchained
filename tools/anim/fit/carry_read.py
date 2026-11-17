"""carry_read.py DUMP_DIR [clips...] [--targets carry_targets.json]: the drawn-sword carry's arm read on a baked body, held
to A's judged read (carry_targets.json 'pose'; reference carry_ref_a.json, fr.py's numbers on A's clips).

Reads the clip bridge's keys dump (tools/body/out/clips/NAME.json, written by tools/body/bake_clips.sh for clips with a
tools/body/p1_clips.json entry or under --p1-bake-only: A's posed globals 'A' and the body's baked globals 'B' per frame,
Godot skeleton space, 3x4 rows). Per clip and facing psi it prints the fist below the right shoulder on screen (dn), the
fist out from the pelvis (ox) and the elbow below the shoulder, for A (from the dump: checks the dump's frame against
fr.py's, so a mismatch there is the tool's, not the body's) and for the body, and flags each body number off A's
reference by more than its tolerance, and the rules (fist under the shoulder, elbow relaxed). Exit 1 on any flag.
Positions only: the blade's angle is the seat's (WeaponSockets.Pocket on B) and is measured in the game shoot (ana10.py).
"""
import sys, os, json, math
from pathlib import Path
import numpy as np

here = Path(__file__).resolve().parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
tgt_path = here / "carry_targets.json"
if "--targets" in sys.argv:
    tgt_path = Path(sys.argv[sys.argv.index("--targets") + 1]); args.remove(str(tgt_path)) if str(tgt_path) in args else None
T = json.load(open(tgt_path))["pose"]
REF = json.load(open(here / T["ref"]))["clips"]
tol = T["tol_m"]
P = math.radians(T["pitch"]); CP, SP = math.cos(P), math.sin(P)
D = Path(args[0]); clips = args[1:] or T["clips"]


def scr(v, psi):
    s, c = math.sin(math.radians(psi)), math.cos(math.radians(psi))
    wx = v[..., 0] * c + v[..., 2] * s; wz = -v[..., 0] * s + v[..., 2] * c
    return wx, v[..., 1] * CP - wz * SP


def read(G, names):
    ix = {n: i for i, n in enumerate(names)}
    def at(n): return G[:, ix[n], :3, 3]
    h, la, ua, pel = at("hand_r"), at("lowerarm_r"), at("upperarm_r"), at("pelvis")
    out = {}
    for psi in (0, -30, 30, 90, 180):
        fx, fy = scr(h - ua, psi); ex, ey = scr(la - ua, psi); px, _ = scr(h - pel, psi)
        sgn = -1.0 if math.cos(math.radians(psi)) >= 0 else 1.0
        out[str(psi)] = {"fist_dn": [float((-fy).min()), float((-fy).mean())], "ox": float((sgn * px).min()), "elbow_dn": float((-ey).mean())}
    return out


bad = 0
for n in clips:
    f = D / f"{n}.json"
    if not f.exists():
        print(f"{n}: no dump ({f})"); bad += 1; continue
    d = json.load(open(f))
    A = np.stack([np.asarray(x, float).reshape(-1, 3, 4) for x in d["A"]])
    B = np.stack([np.asarray(x, float).reshape(-1, 3, 4) for x in d["B"]])
    ra, rb, ref = read(A, d["a_names"]), read(B, d["b_names"]), REF.get(n)
    print(n)
    for psi in ("0", "-30", "30", "90", "180"):
        a, b = ra[psi], rb[psi]; flags = []
        if ref:
            r = ref[psi]
            for key, val, rv in (("fist_dn_mean", b["fist_dn"][1], r["fist_dn"][1]), ("fist_dn_min", b["fist_dn"][0], r["fist_dn"][0]),
                                 ("ox", b["ox"], r["ox"]), ("elbow_dn", b["elbow_dn"], r["elbow_dn"])):
                if abs(val - rv) > tol[key]: flags.append(f"{key} {val - rv:+.3f}")
        if b["fist_dn"][1] < 0.05: flags.append("fist over the shoulder line")
        if psi == "0" and b["elbow_dn"] < -0.03: flags.append("elbow raised")
        bad += bool(flags)
        rr = f"ref dn {ref[psi]['fist_dn'][1]:.2f} ox {ref[psi]['ox']:.2f} el {ref[psi]['elbow_dn']:.2f} | " if ref else ""
        print(f"   psi{int(psi):4d}: {rr}A dn {a['fist_dn'][1]:.2f} ox {a['ox']:.2f} el {a['elbow_dn']:.2f} | body dn {b['fist_dn'][0]:.2f}/{b['fist_dn'][1]:.2f} ox {b['ox']:.2f} el {b['elbow_dn']:.2f}" + (f"  << {'; '.join(flags)}" if flags else ""))
print(f"flags: {bad}")
sys.exit(1 if bad else 0)
