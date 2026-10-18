"""Hand/forearm into her legs (skin, mm) per run/sprint for candidate back-swing changes, built in memory.
usage: python sweep.py <worktree> <cands.json> [clip names...]
cands.json: {"label": {"*": [dth, dout, del, dturn]} or {"GAIT-run-name": [[fwd4],[back4]]}}  ("*" adds to every back key)"""
import sys, json, time
from pathlib import Path
from dataclasses import replace
import numpy as np
WT = Path(sys.argv[1]); cands = json.loads(Path(sys.argv[2]).read_text()); want = sys.argv[3:]
sys.path.insert(0, str(WT / "tools/anim")); sys.path.insert(0, str(WT / "tools/scratch/anim36"))
import clips.run as R
import clips.sprint_stop as SS
from clips.sprint_stop import sprint
SS0 = SS.SPRINT_SWING
from gait import run_cycle
from keyed import Rig
from skin import Body
from motion import Measure
from armmetrics import metrics
from rig import qrot, qinv
rr, rpos = sk.rest_globals() if False else (None, None)
def shield(clip):
    """Arm into the slung shield (Arms.cs Back socket: 66 cm across, centred (0, 1.22, -0.20) at rest on spine_03,
    inner face taken at z -0.19): max depth mm per side over the frames."""
    grot, gp = sk.fk(clip.rot, clip.pos)
    r0, p0 = sk.rest_globals(); r0, p0 = r0[0], p0[0]
    S = I["spine_03"]; out = {}
    for sd in "lr":
        U, E, H = I[f"upperarm_{sd}"], I[f"lowerarm_{sd}"], I[f"hand_{sd}"]
        worst = 0.0
        for f in range(len(gp)):
            pts = [(gp[f, U] * 0.5 + gp[f, E] * 0.5, 0.045), (gp[f, E], 0.04), (gp[f, E] * 0.75 + gp[f, H] * 0.25, 0.035), (gp[f, E] * 0.5 + gp[f, H] * 0.5, 0.032)]
            for p, r in pts:
                q = qrot(r0[S], qrot(qinv(grot[f, S]), p - gp[f, S])) + p0[S]
                if (q[0] ** 2 + (q[1] - 1.22) ** 2) ** 0.5 < 0.33:
                    worst = max(worst, (-0.19 - (q[2] - r)) * 1000)
        out[sd] = worst
    return out
b = Body.heroine(jiggle=False); m = Measure(b); sk = b.sk; I = sk.index
rig = Rig(sk, body="her")
j = dict(shL=I["upperarm_l"], shR=I["upperarm_r"], elL=I["lowerarm_l"], elR=I["lowerarm_r"], hdL=I["hand_l"], hdR=I["hand_r"],
         hipL=I["thigh_l"], hipR=I["thigh_r"], spine_lo=I["spine_01"], neck=I["neck_01"], chest=I["spine_03"])
legs = [i for i, p in enumerate(b.parts) if p.startswith("leg")]
BASE = dict(R.RUNS)
names = want or ["run_warden_town", "sprint_warden_town", "run_reaver", "sprint_reaver", "run_stalker_daggers", "run_arcanist"]
for label, spec in cands.items():
    for n, (g, arms, w) in BASE.items():
        sw = g.swing
        if sw is None: R.RUNS[n] = (g, arms, w); continue
        if n in spec: sw = tuple(tuple(x) for x in spec[n])
        elif "*" in spec: sw = (sw[0], tuple(np.add(sw[1], spec["*"]).tolist()))
        if "fwd*" in spec: sw = (tuple(np.add(sw[0], spec["fwd*"]).tolist()), sw[1])
        g = replace(g, swing=sw)
        if "g:" + n in spec: g = replace(g, **spec["g:" + n])
        if "xbow" in spec and n == "run_stalker":
            x = spec["xbow"]
            def xb(ph, k, hand, x=x):
                return {"arc": R.arc_of((x[0], x[1], x[2] + 0.06 * (k - 0.5))), "pole": tuple(x[3]),
                        "knuckles": (0.0, -0.55, 0.83), "blade": (0.0, 0.83, 0.55), "frame": "chest", "twist": 0.5}
            arms = {**arms, "r": xb}
        R.RUNS[n] = (g, arms, w)
    SS.SPRINT_SWING = tuple(spec.get("sprint", SS0))
    for nm in names:
        t0 = time.time()
        run = nm if nm.startswith("run_") else "run_" + nm[len("sprint_"):]
        g, arms, w = R.RUNS[run]
        clip = run_cycle(run, rig, replace(g, arms=arms), {"weapon": w}) if nm.startswith("run_") else sprint(rig, run)
        Gs = b.frames(clip)
        worst = {"l": (0, -1), "r": (0, -1)}
        for f, G in enumerate(Gs):
            P = b.pose(G); con = m.contact(P)
            for s in "lr":
                dist, along, hit, brst, near = con[s]
                ok = np.isfinite(dist) & (along >= 1) & np.isin(hit, legs)
                if ok.any():
                    d = float((-dist[ok]).max()) * 1000
                    if d > worst[s][0]: worst[s] = (d, f)
        _, gp = sk.fk(clip.rot, clip.pos)
        r = metrics(gp, j)
        sh = shield(clip) if "town" in nm else None
        a = " ".join(f"{s}: leg {worst[s][0]:4.0f}mm@f{worst[s][1]:<2d} abd {r[s]['abd_max']:4.1f} trav {r[s]['hand_travel']:.2f}L sag {r[s]['sag_fwd']:+4.0f}/{r[s]['sag_back']:+4.0f} elb {r[s]['elb_min']:3.0f}-{r[s]['elb_max']:3.0f}" for s in "lr")
        if sh: a += f"  SHIELD l {sh['l']:3.0f} r {sh['r']:3.0f}"
        print(f"{label:10s} {nm:24s} {a} ({time.time()-t0:.0f}s)", flush=True)
