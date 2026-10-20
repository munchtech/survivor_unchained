"""Town idles measured against idle_warden_town (animation 44, solver idle 1).
usage: python idlemeasure.py <clip> [<clip> ...] [--pieces axe,axes,wand,crossbow,daggers,staff]
Per clip: pelvis lateral sway p-p (cm) and its period (s), pelvis roll range (deg), the share of the loop with her
weight clearly on one foot (over 70/30), shoulder rise over rest in the chest's frame (cm, l/r), elbow bend (deg,
min-max l/r), finger curl (mean joint deg, l/r), head pitch and roll range (deg), foot slide (mm), loop seam jump
(the worst bone's last-to-first step over its median step), and each hand/forearm's nearest skin point to each
sheathed piece (mm, l/r; the socket clearance of the reaver/arcanist/ranger outfit). Staff: the held staff's butt
(its lowest point) drift over the loop (cm) and height above the ground (cm)."""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
from skin import Body  # noqa
from armscheck import sample, CLEARANCE, DATA  # noqa

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
OUTFIT = {"reaver": "reaver", "arcanist": "arcanist", "stalker": "ranger", "warden": "warden"}
PIECES = {"axe": ["viking_axe@hand_r"], "axes": ["viking_axe@hand_r", "viking_axe@hand_l"], "wand": ["wand@hand_r"],
          "crossbow": ["crossbow@hand_r"], "daggers": ["daggers@hand_r", "dagger_b@hand_l"], "sword": ["viking_sword@hand_r", "shield_round@lowerarm_l"]}

b = Body.heroine(jiggle=False, helpers=True)
I = b.sk.index
raw = json.loads((DATA / "arms_local.json").read_text())
sheathed = raw.get("sheathed", {})
clr = json.loads(CLEARANCE.read_text())
vb = np.array(b.sk.names)[b.J[np.arange(len(b.P)), b.W.argmax(1)]]
FING = ("index", "middle", "ring", "pinky")
arm_v = {s: np.array([i for i, n in enumerate(vb) if n.endswith("_" + s) and (n.startswith(("lowerarm", "hand")) or n.split("_")[0] in FING + ("thumb",))]) for s in "lr"}
rg, rp = b.sk.rest_globals()
G0 = b.globals(b.clip(args[0]), 0)


def rot_of(G, j):
    return G[j][:3, :3]


def ang(u, v):
    return math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


for name in args:
    clip = b.clip(name)
    Gs = [b.globals(clip, f) for f in range(clip.frames)]
    n = len(Gs)
    calling = name.split("_")[1]
    P = lambda G, k: G[I[k]][:3, 3]
    fwd = np.mean([P(G, "ball_l") - P(G, "foot_l") + P(G, "ball_r") - P(G, "foot_r") for G in Gs], axis=0)
    fwd[1] = 0; fwd /= np.linalg.norm(fwd)
    left = np.cross([0, 1, 0], fwd)
    pel = np.array([P(G, "pelvis") for G in Gs])
    lat = pel @ left
    sp = np.abs(np.fft.rfft(lat - lat.mean()))
    k = int(np.argmax(sp[1:]) + 1)
    period = clip.frames / clip.fps / k
    roll = [math.degrees(math.asin(np.clip(((P(G, "thigh_l") - P(G, "thigh_r")) / np.linalg.norm(P(G, "thigh_l") - P(G, "thigh_r")))[1], -1, 1))) for G in Gs]
    w = []
    for G in Gs:
        a, c = P(G, "foot_r") @ left, P(G, "foot_l") @ left
        w.append((P(G, "pelvis") @ left - a) / (c - a))
    w = np.array(w)
    one = float(np.mean(np.abs(w - 0.5) > 0.2))
    # Shoulders: upperarm heads in spine_03's frame, over rest's.
    s3 = I["spine_03"]
    rise = {}
    for s in "lr":
        u = I[f"upperarm_{s}"]
        r0 = rg[0][s3] if False else None
        vals = [(np.linalg.inv(G[s3]) @ np.append(P(G, f"upperarm_{s}"), 1))[1] for G in Gs]
        Gr = b.globals(type(clip)(clip.name, clip.fps, np.tile(b.sk.rest_rot, (1, 1, 1)).astype(float), np.tile(b.sk.rest_pos, (1, 1, 1)).astype(float), False, {}), 0)
        v0 = (np.linalg.inv(Gr[s3]) @ np.append(Gr[u][:3, 3], 1))[1]
        rise[s] = 100 * (np.mean(vals) - v0)
    elb = {s: [ang(P(G, f"lowerarm_{s}") - P(G, f"upperarm_{s}"), P(G, f"hand_{s}") - P(G, f"lowerarm_{s}")) for G in Gs] for s in "lr"}
    curl = {}
    for s in "lr":
        vals = []
        for G in (Gs[0], Gs[n // 2]):
            for fn in FING:
                for q in (1, 2):
                    a, bb, c = P(G, f"{fn}_0{q}_{s}"), P(G, f"{fn}_0{q + 1}_{s}"), None
                    par = P(G, f"{fn}_0{q - 1}_{s}") if q > 1 else P(G, f"hand_{s}")
                    vals.append(ang(a - par, bb - a))
        curl[s] = np.mean(vals)
    hp, hr = [], []
    Rr = Gr[I["Head"]][:3, :3]
    for G in Gs:
        R = G[I["Head"]][:3, :3] @ Rr.T
        f2, l2 = R @ fwd, R @ left
        hp.append(math.degrees(math.asin(np.clip(-f2[1], -1, 1))))   # + = chin down
        hr.append(math.degrees(math.asin(np.clip(l2[1], -1, 1))))
    slide = max(np.ptp(np.array([P(G, f"foot_{s}") for G in Gs]), axis=0).max() for s in "lr") * 1000
    pos = np.array([[G[j][:3, 3] for j in range(len(G))] for G in Gs])
    steps = np.linalg.norm(np.diff(pos, axis=0), axis=2)
    seam = np.linalg.norm(pos[0] - pos[-1], axis=1)
    seamr = float(np.max(seam / np.maximum(np.median(steps, axis=0), 1e-5))) if clip.loop else 0
    seam_mm = float(seam.max() * 1000)
    print(f"{name}: {n} f {n / clip.fps:.2f}s | sway {100 * np.ptp(lat):.1f} cm period {period:.2f}s | roll {min(roll):+.1f}..{max(roll):+.1f} | "
          f"one-foot {100 * one:.0f}% (w {w.min():.2f}-{w.max():.2f}) | shoulder rise l {rise['l']:+.1f} r {rise['r']:+.1f} cm | "
          f"elbow l {min(elb['l']):.0f}-{max(elb['l']):.0f} r {min(elb['r']):.0f}-{max(elb['r']):.0f} | curl l {curl['l']:.0f} r {curl['r']:.0f} | "
          f"head pitch {min(hp):+.1f}..{max(hp):+.1f} roll {min(hr):+.1f}..{max(hr):+.1f} | foot slide {slide:.1f} mm | seam {seam_mm:.1f} mm ({seamr:.1f}x step)")
    pieces = opt.get("pieces", "").split(",") if opt.get("pieces") else []
    out = OUTFIT.get(calling, "none")
    for pc in pieces:
        if pc == "staff":
            pts = sample(np.array(raw["mage_staff@hand_r"]["v"], float), np.array(raw["mage_staff@hand_r"]["t"], int))
            butt = []
            for G in Gs:
                M = G[I["hand_r"]]
                Q = pts @ M[:3, :3].T + M[:3, 3]
                butt.append(Q[np.argmin(Q[:, 1])])
            butt = np.array(butt)
            print(f"   staff butt: drift {100 * np.ptp(butt[:, [0, 2]], axis=0).max():.1f} cm (x {100 * np.ptp(butt[:, 0]):.1f}, z {100 * np.ptp(butt[:, 2]):.1f}) "
                  f"height {100 * butt[:, 1].min():.1f}-{100 * butt[:, 1].max():.1f} cm")
            continue
        for key in PIECES[pc]:
            d = sheathed[key]
            pts = sample(np.array(d["v"], float), np.array(d["t"], int)) + np.array(d["normal"], float) * clr.get(out, {}).get(d["socket"], 0)
            worst = {"l": 9e9, "r": 9e9}
            for f in range(0, n, 2):
                G = Gs[f]
                M = G[I[d["bone"]]]
                Q = pts @ M[:3, :3].T + M[:3, 3]
                tr = cKDTree(Q)
                Psk = b.pose(G)
                for s in "lr":
                    dd, _ = tr.query(Psk[arm_v[s]])
                    worst[s] = min(worst[s], float(dd.min()))
            print(f"   {key} sheathed ({d['socket']}, {out}): nearest hand/forearm skin l {1000 * worst['l']:.0f} r {1000 * worst['r']:.0f} mm")
