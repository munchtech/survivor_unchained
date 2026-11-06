"""B's walk/run blend as the move graph plays it once the arm-hold layer is retired (ArmHold.Layered): every bone's
local rotation slerped between the walk and the run at the shared stride phase (both seek phase*length; phase 0 = the
left foot down). For each weight in 0, .25, .5, .75, 1 across one cycle:
  - the piece's deviation: hand_r (the sword) and lowerarm_l (the shield) global turn against the straight path
    (the slerp between the two holds' own turns at that phase), deg; the old per-bone mix read 43-54 deg at 0.5;
  - the piece against her body: the warden set's pieces (tools/anim/data/arms_local.json, A's hand space, laid on B's
    bone by the rest-world rule Arms.HoldSheathed uses), mm inside her skin (clipcheck's posed B, torso: arms left out).

    python tools/anim/p4_blend.py [walk_clip run_clip] [--phases N]     (default walk_warden run_warden)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402  (Marionette's core on the path)
from motion import clip as MC  # noqa: E402
from motion import quat as Q  # noqa: E402
from motion.rig import Rig  # noqa: E402

REPO = p4.REPO
WEIGHTS = (0, 0.25, 0.5, 0.75, 1)


def locals_at(c, rig, u):
    """The clip's keyed locals at phase u (0..1), interpolated as the game's linear tracks."""
    n = c["frames"]
    x = u * (n - 1)
    a = int(np.floor(x)) % (n - 1)
    t = x - np.floor(x)
    rot = {b: Q.slerp(np.array(q[a]), np.array(q[a + 1]), t) for b, q in c["rot"].items()}
    pos = {b: (1 - t) * np.array(p[a]) + t * np.array(p[a + 1]) for b, p in c["pos"].items()}
    return rot, pos


def pose(rig, rot, pos):
    Lr, Lt = rig.rest_locals(1)
    for b, q in rot.items():
        Lr[0, rig.index[b]] = Q.to_mat(np.array(q)[None])[0]
    for b, p in pos.items():
        Lt[0, rig.index[b]] = p
    G, P = rig.fk(Lr, Lt)
    return G[0], P[0]


def ang(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def main(argv):
    names = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--phases")] or ["walk_warden", "run_warden"]
    nph = int(argv[argv.index("--phases") + 1]) if "--phases" in argv else 12
    rig = Rig(p4.RIG)
    cw, cr = (MC.read(p4.OUT / f"{n}.json") for n in names)
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    P1 = REPO / "godot/art/people/body_p1"
    body = CC.Body(str(P1 / "body.glb"), json.loads((P1 / "rig.json").read_text()), rig.names,
                   p4.m44(rig.R0, rig.head), True)
    arms = json.loads((REPO / "tools/anim/data/arms_local.json").read_text())
    pieces = {"sword": ("chevalier_sword@hand_r", "hand_r"), "shield": ("shield_round@lowerarm_l", "lowerarm_l")}
    pts = {}
    for k, (key, bone) in pieces.items():
        v = np.array(arms[key]["v"], float)
        # The game's mount on B: Arms.Hold puts the same bone-local MountTransform/Seat on B's own hand_r / lowerarm_l
        # (PersonView.BoneOf; no B mapping, unlike HoldSheathed), so ArmsDump's bone-local points ride B's bone as they are
        M = np.eye(4)
        sel = v[np.random.default_rng(1).choice(len(v), min(len(v), 1500), replace=False)]
        pts[k] = (np.c_[sel, np.ones(len(sel))] @ M.T)[:, :3]
    rows = []
    for w in WEIGHTS:
        dev = {"sword": 0.0, "shield": 0.0}
        depth = {"sword": 0.0, "shield": 0.0}
        for i in range(nph):
            u = i / nph
            (rw, pw), (rr, pr) = locals_at(cw, rig, u), locals_at(cr, rig, u)
            rot = {b: Q.slerp(rw[b], rr[b], w) for b in rw if b in rr}
            pos = {b: (1 - w) * pw[b] + w * pr[b] for b in pw if b in pr}
            G, P = pose(rig, rot, pos)
            Gw, _ = pose(rig, rw, pw)
            Gr, _ = pose(rig, rr, pr)
            Gd = p4.m44(G, P)
            for k, (_, bone) in pieces.items():
                j = rig.index[bone]
                straight = Q.to_mat(Q.slerp(Q.from_mat(Gw[j][None])[0], Q.from_mat(Gr[j][None])[0], w)[None])[0]
                dev[k] = max(dev[k], ang(G[j], straight))
            # the body posed at this blend
            body.cache.clear()
            Vb, _, Nb, tr = body.pose(Gd, set(rot), 0)
            for k, (_, bone) in pieces.items():
                j = rig.index[bone]
                Pw = pts[k] @ G[j].T + P[j]
                Pg = (np.c_[Pw, np.ones(len(Pw))] @ body.X.T)[:, :3]
                s, d, _ = CC.signed(Vb, Nb, tr, body.tidx, Pg)
                inside = s[(s < 0) & (d < 0.03)]
                depth[k] = max(depth[k], float(-inside.min() * 1000) if len(inside) else 0.0)
        rows.append({"w": w, "sword_dev_deg": round(dev["sword"], 2), "shield_dev_deg": round(dev["shield"], 2),
                     "sword_in_mm": round(depth["sword"], 1), "shield_in_mm": round(depth["shield"], 1)})
        print(rows[-1], flush=True)
    out = REPO / "tools/body/out"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"p4blend_{names[0]}_{names[1]}.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
