"""P4 clips: SOMA motion (Kimodo / MotionBricks) retargeted onto B, the game-side front of Marionette's motion core
(Marionette tools/motion/: one implementation the app and this CLI share).

    python tools/anim/p4.py import <bvh> <clip> [--loop] [--inplace]   source -> tools/anim/p4/src/<clip>.npz (committed:
                                                                      generation is not reproducible) + a stub spec
                                                                      tools/anim/p4/specs/<clip>.json
    python tools/anim/p4.py build [clips]     every spec -> godot/art/people/body_p1/p4/<clip>.json (build output,
                                              git-ignored; bash tools/anim/p4_pack.sh packs them into p4_clips.res)
    python tools/anim/p4.py gen [clips] [--encode-only] the specs' gen blocks -> Kimodo (motion/kimodo_run.py): every prompt
                                              encoded ONCE into the embedding cache (only with 18 GB of RAM free), then
                                              the diffusion model alone makes the takes from the cache (take the gpu
                                              turn first) -> TAKES_DIR/<clip>__p<i>_<k>.bvh
    python tools/anim/p4.py strip <clip|built.json> [--every 2] [--views game,side] [--spin tps]   an offline pose strip (p4_strip.py)
    python tools/anim/p4.py takes [clips]     every take through the core with the spec's post, measured against its bands
                                              (motion/measures.py), logged in specs/<clip>.takes.json; the best is imported
    python tools/anim/p4.py check [clips]     tools/body/clipcheck.py's measures on the built clips (pops, seam, feet,
                                              arm contact, hand gap) plus the core's fidelity and planted slide, a table
                                              and the freeze: `statue: n frames (fa-fb)` (measures.statue; MISS over 2
                                              on a one-shot) and `quiet: n%`; bands may use statue_frames, quiet_pct

The law bones (LAW_BONES: the clavicles, B's girdle law's): a build DROPS a law bone's track that never leaves rest
(`law tracks dropped: clavicle_l, clavicle_r`: the game reads a track there as keyed), and build, pose and check print
a MISS for a law bone that leaves rest (a P4 clip never keys the clavicle); check says STALE for a built file that
still carries one at rest (built before the drop).

The rig is tools/body/rig/{b_skeleton,soma_to_b}.json (tools/body/rig_map.py).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
# Where Marionette lives (its tools/motion is the core). One constant, overridable by env MARIONETTE_DIR; the
# motion-a1 worktree for now, Marionette's main checkout once the core is merged there.
MARIONETTE = os.environ.get("MARIONETTE_DIR", "C:/Users/munch/Desktop/Marionette_motion")
sys.path.insert(0, str(Path(MARIONETTE) / "tools"))
from motion import clip as MC  # noqa: E402
from motion import footlock, measures, paths, retarget, soma  # noqa: E402

P4 = REPO / "tools/anim/p4"
RIG = REPO / "tools/body/rig"
OUT = REPO / "godot/art/people/body_p1/p4"
KIMODO_PY = os.environ.get("KIMODO_PY", "C:/Users/munch/Tools/kimodo/.venv/Scripts/python.exe")
TAKES_DIR = Path(os.environ.get("P4_TAKES", "C:/Users/munch/Tools/mocap/kimodo_p4"))
CACHE = Path(os.environ.get("KIMODO_CACHE", "C:/Users/munch/Tools/mocap/kimodo_cache"))
KFPS = 30


def specs(names, ungenerated=False):
    """The specs named (all without names). A gen-only spec with no source yet (its takes not imported: a new
    directional walk) is left out of the build-side commands unless named, and always kept for gen and takes."""
    allp = sorted(p for p in (P4 / "specs").glob("*.json") if not p.stem.endswith(".takes"))
    return [p for p in allp if (not names or p.stem in names)
            and (ungenerated or names or "source" in json.loads(p.read_text()))]


PLAYS = ("name", "fps", "frames", "loop", "rot", "pos", "beats", "speed_mps")   # what P4Pack reads: all that plays


def clip_hash(built):
    """The pack gate's fingerprint of a built clip: sha256 (first 16 hex) of what plays (not notes, not `judged`)."""
    obj = {k: built[k] for k in PLAYS[:6] if k in built}
    for k in PLAYS[6:]:
        if built.get(k) is not None:
            obj[k] = built[k]
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def judged_state(spec, built):
    """"judged" (spec flag matches the build), "stale" (flag present, build changed) or "not judged" (no flag)."""
    j = spec.get("judged")
    if not j:
        return "not judged"
    return "judged" if j.get("build") == clip_hash(built) else "stale"


def judged_note(name, spec, built):
    """Writes (or strips) the top-level `judged` in `built` by the state; returns the printed line."""
    st = judged_state(spec, built)
    built.pop("judged", None)
    if st == "judged":
        j = spec["judged"]
        built["judged"] = j
        return f"p4: {name}: judged ({j.get('by')}, {j.get('on')}), build matches"
    if st == "stale":
        return (f"p4: {name}: JUDGED FLAG STALE: the build changed since its judge ({spec['judged'].get('build')} -> "
                f"{clip_hash(built)}); the pack will skip it")
    return f"p4: {name}: not judged (the pack skips it; review packs only)"


def cmd_import(a):
    s = soma.read_bvh(a.bvh)
    (P4 / "src").mkdir(parents=True, exist_ok=True)
    (P4 / "specs").mkdir(parents=True, exist_ok=True)
    soma.save_npz(s, P4 / "src" / f"{a.clip}.npz")
    sp = P4 / "specs" / f"{a.clip}.json"
    spec = json.loads(sp.read_text()) if sp.exists() else {"notes": ""}
    spec.update({"loop": a.loop, "inplace": a.inplace, "source": f"src/{a.clip}.npz",
                 "bvh": os.path.basename(a.bvh), "sha1": s.sha1})
    sp.write_text(json.dumps(spec, indent=1) + "\n")
    print(f"{a.clip}: {s.frames} frames from {os.path.basename(a.bvh)} -> src/{a.clip}.npz, specs/{a.clip}.json")


def _cs_vec(name):
    """A Vector3 constant from godot/logic/Play/WeaponSockets.cs (the game's data, one source)."""
    import re
    src = (REPO / "godot/logic/Play/WeaponSockets.cs").read_text(encoding="utf-8")
    m = re.search(name + r"\s*=\s*new\(([^)]*)\)", src)
    return [float(x.strip().rstrip("f")) for x in m.group(1).split(",")]


def pieces():
    """B's held pieces in their bones' spaces, as the game seats them on B: the sword's and the shield's points are
    tools/anim/data/arms_local_b.json's (ArmsDump with Arms.Seat isB: the game's own seat on B's fist pocket, WeaponSockets
    BladeAtRB / BladeDirRB). Only when that file is missing: the old model, A's dump (arms_local.json) with the sword moved
    onto B's pocket by the least turn. And the pockets the fit aims by: the blade's axis and grip, the shield's boss (its
    points' centroid) and face (its thin axis, out of the arm)."""
    if "_pc" in globals():
        return _pc
    from motion import quat as Q
    atB, dirB = np.array(_cs_vec("BladeAtRB")), np.array(_cs_vec("BladeDirRB"))
    dirB = dirB / np.linalg.norm(dirB)
    fb = REPO / "tools/anim/data/arms_local_b.json"
    if fb.exists():
        arms = json.loads(fb.read_text())
        sw = np.array(arms["chevalier_sword@hand_r"]["v"], float)
    else:
        arms = json.loads((REPO / "tools/anim/data/arms_local.json").read_text())
        atA, dirA = np.array(_cs_vec("BladeAtR")), np.array(_cs_vec("BladeDirR"))
        dirA = dirA / np.linalg.norm(dirA)
        sw = np.array(arms["chevalier_sword@hand_r"]["v"], float)
        sw = atB + (sw - atA) @ Q.arc(dirA, dirB).T
    tip = float(np.max((sw - atB) @ dirB))
    sh = np.array(arms["shield_round@lowerarm_l"]["v"], float)
    c = sh.mean(0)
    _, _, vt = np.linalg.svd(sh - c)
    face = vt[2] if vt[2] @ np.array([-1.0, 0, 0]) > 0 else -vt[2]
    rad = float(np.max(np.linalg.norm((sh - c) - np.outer((sh - c) @ face, face), axis=1)))
    globals()["_pc"] = {"sword": sw, "shield": sh, "blade": {"dir": dirB.tolist(), "at": atB.tolist(), "tip": tip},
                        "shieldp": {"at": c.tolist(), "face": face.tolist(), "radius": rad}}
    return _pc


def fit_of(spec):
    """The spec's fit block with the game's pocket data filled in."""
    f = spec.get("fit")
    if not f:
        return None
    f = json.loads(json.dumps(f))
    if "blade" in f:
        f["blade"]["pocket"] = pieces()["blade"]
    if "shield" in f:
        f["shield"]["pocket"] = pieces()["shieldp"]
    if "end" in f:
        # (an action's blend out: the built clip it ends in (fit.end.clip, at fit.end.frame), its locals, its pelvis's
        # world turn and height on B)
        f["end"]["pose"] = end_pose(f["end"]["clip"], f["end"].get("frame", 0))
        if f.get("shield", {}).get("hand") == "end":    # (the shield hand held at the end pose's local all through)
            f["shield"]["hand_rot"] = f["end"]["pose"]["rot"]["hand_l"]
    if "start" in f:                # (an action's blend in from a built clip's frame (fit.start: the mirror of end))
        f["start"]["pose"] = end_pose(f["start"]["clip"], f["start"].get("frame", 0))
        if f.get("shield", {}).get("hand") == "start":  # (the shield hand held at the start pose's local all through:
            f["shield"]["hand_rot"] = f["start"]["pose"]["rot"]["hand_l"]   # the stance's grip kept through a cut)
    if "clear" in f:
        # (the game's mount on B: the pieces' points in their bones' spaces, a fixed sample)
        pc, bones = pieces(), {"sword": ("hand_r", "r"), "shield": ("lowerarm_l", "l")}
        rng = np.random.default_rng(1)
        f["clear"]["pieces"] = {k: {"bone": bones[k][0], "side": bones[k][1],
                                    "pts": pc[k][rng.choice(len(pc[k]), min(len(pc[k]), 800), replace=False)].tolist()}
                                for k in f["clear"].get("held", spec.get("held", []))}
    return f


def end_pose(clip, frame=0):
    """A built clip's pose at one frame (OUT/<clip>.json): {rot: {bone: [x, y, z, w] local}, pelvis_rot: its world turn,
    pelvis_y: its world height, spot: {pelvis, heel_l, ball_l, heel_r, ball_r: [x, z]} where it stands in the node's
    frame, m (fit.end.spot: an action ends there)}."""
    from motion import fit as FIT
    from motion.rig import Rig
    c = MC.read(OUT / f"{clip}.json")
    G, P = MC.globals_of(c, Rig(RIG))
    pv = Rig(RIG).index["pelvis"]
    return {"rot": {b: q[frame] for b, q in c["rot"].items()}, "pelvis_rot": G[frame, pv].tolist(),
            "pelvis_y": float(P[frame, pv, 1]),
            "spot": {k: [float(v[frame][0]), float(v[frame][2])] for k, v in FIT.ground_points(Rig(RIG), G, P).items()}}


def action_of(spec):
    """An action's post (Marionette motion/action.py) with its named moments resolved to clip seconds: post.action
    {seconds, retime, derotate_tps, travel: [a, b], planted: {foot_l|foot_r: [[a, b, "ball"|"ankle"], ...]}}, where a
    and b are seconds, "start", "end" or a beats event."""
    if spec.get("kind") != "action":
        return None, None
    beats = spec.get("beats", {})
    act = json.loads(json.dumps(spec.get("post", {}).get("action", {})))
    T = float(act.setdefault("seconds", spec.get("seconds", 1.0)))
    ev = beats.get("events", {})

    def sec(x):
        return 0.0 if x == "start" else T if x == "end" else float(ev[x]) if isinstance(x, str) else float(x)
    act["planted"] = {k: [[sec(w[0]), sec(w[1])] + list(w[2:]) for w in ws] for k, ws in act.get("planted", {}).items()}
    return act, beats


# The bones a body law OWNS on B: the game drives them at run time and reads a clip's TRACK on one as keyed. Today the
# clavicles: rig.json girdle "clavicle": "clavicle_{s}" (P1Rig.Girdle / ClavicleTurn lay the girdle law on it; A's
# ClavicleLift is the same rule on A). Not the scapula and the other helper rows' bones (P1Rig.Helpers: the core never
# keys them), not the "unroll" rows' lowerarm / calf (keyed limb bones). The export's rule (run_post, so build, check,
# takes and pose share it): a law bone's track that is at rest on every frame is DROPPED (the core keys the clavicles
# NEUTRAL, B's rest local), and a law bone that leaves rest is a MISS (a P4 clip never keys the clavicle).
LAW_BONES = ("clavicle_l", "clavicle_r")
LAW_TOL_DEG = 0.05       # at rest: every frame within this of B's rest local (a 7-digit key's noise is ~1e-5 deg)


def law_lines(clip, rig, dropped=()):
    """The law bones' lines for a clip as it stands (a build's clip after run_post's drop; check's built file):
    the tracks dropped, then per law bone still tracked a MISS where it leaves rest, or STALE where the track sits at
    rest (a file built before the drop: the game would read it as keyed until a rebuild takes it out)."""
    L = [f"  law tracks dropped: {', '.join(dropped)}"] if dropped else []
    for b, (deg, f) in MC.off_rest(clip, rig, LAW_BONES).items():
        if deg > LAW_TOL_DEG:
            L.append(f"  law bone {b}: keyed, {deg:.2f} deg off rest @f{f} MISS (a body law owns it: a clip never keys it)")
        else:
            L.append(f"  law bone {b}: a track at rest in the built clip STALE (built before the drop: a rebuild takes it out)")
    return L


def run_post(src, spec, name):
    """The core on one source with the spec's post steps (loop, in place, whole cycles, the gait lock, an action's
    post) and its fit; then the export's law rule (LAW_BONES): r.law = (dropped, {bone: (deg, frame)} off rest)."""
    po = spec.get("post", {})
    act, beats = action_of(spec)
    cyc = po.get("cycle_s")
    r = MC.run(src, RIG, loop=po.get("loop", spec.get("loop", False)), inplace=po.get("inplace", spec.get("inplace", False)),
               name=name, gait=po.get("gait", False), duty=po.get("duty"),
               cycle=(int(round(cyc[0] * KFPS)), int(round(cyc[1] * KFPS))) if cyc else None,
               crop=tuple(po["crop"]) if po.get("crop") else None, fit=fit_of(spec),
               body=body_field() if "clear" in spec.get("fit", {}) else None, action=act, beats=beats,
               # (a directional gait: its travel's heading in her frame, its cycle resampled to the paired walk's frames)
               travel_deg=po.get("travel_deg", 0.0), frames=po.get("cycle_frames"))
    r.law = MC.drop_rest(r.clip, r.rig, LAW_BONES, LAW_TOL_DEG)
    if spec.get("meta"):     # (the spec's meta carried onto the clip as data: P4Pack sets each key on the Animation;
        r.clip["meta"] = {**r.clip.get("meta", {}), **spec["meta"]}   # e.g. {"stance": true}: a cut with a _run)
    return r


def build_one(p):
    spec = json.loads(p.read_text())
    return run_post(P4 / spec["source"], spec, p.stem)


def measure(r, spec):
    """The bible's numbers on a core result (B's side), per the spec's kind."""
    fps = r.src.fps
    if spec.get("kind") == "action":
        m = measures.action(r.P, r.G, r.rig, fps, spec.get("bands", {}), r.clip.get("beats", {}),
                            extra=action_held(r, spec), head_top=head_top())
        m.update(steps(r))
        m.update(statue_of(r.clip, r.G, r.P, r.rig))
        return m
    if spec.get("kind") == "gait":
        m = measures.gait(r.P, r.rig, fps, r.clip.get("speed_mps"), loop=r.clip["loop"])
        m.update(held(r, spec))
        m.update(steps(r))
        m.update(statue_of(r.clip, r.G, r.P, r.rig))
        return m
    m = measures.idle(r.P, r.rig, fps, loop=r.clip["loop"])
    m.update(hand_targets(r, spec))
    m.update(held(r, spec))
    m.update(steps(r))
    m.update(statue_of(r.clip, r.G, r.P, r.rig))
    return m


STATUE_FRAMES = 2        # the fail line on a one-shot: more frames than this frozen outside its hold reads as a statue


def statue_of(c, G, P, rig, at=False):
    """A clip's freeze numbers for the bands (measures.statue): statue_frames (the longest run of frozen frames
    outside beats.hold, and outside beats.loop on a one-shot) and quiet_pct (the share of steps outside the hold in
    which no major joint turns 1 deg); at: with statue_at [first, last frame] (check's line)."""
    m = measures.statue(P, G, rig, c["fps"], c.get("beats") or {}, c["loop"])
    return m if at else {k: m[k] for k in ("statue_frames", "quiet_pct")}


def statue_lines(m, loop):
    """check's two lines: the run with MISS over STATUE_FRAMES on a one-shot (a whole-clip loop prints it unflagged)."""
    a = m["statue_at"]
    return [f"  statue: {m['statue_frames']} frames" + (f" (f{a[0]}-f{a[1]})" if a else "")
            + (" MISS" if m["statue_frames"] > STATUE_FRAMES and not loop else ""),
            f"  quiet: {m['quiet_pct']}%"]


def held(r, spec):
    """The held pieces' numbers on B (the game's seat on B: pieces()): the blade's angle below the horizontal (mean, and
    its pitch swing peak to peak), its heading off her forward (+ her left), its tip's height; the shield's boss in her
    pelvis frame (cm: left, up, forward of the pelvis head), its top edge's height and its face's heading (+ open)."""
    out = {}
    rig, G, P = r.rig, r.G, r.P
    n = r.m
    pv = rig.index["pelvis"]
    Rp = G[:n, pv] @ rig.R0[pv].T
    pc = pieces()
    def local(v):
        return np.einsum("fji,fj->fi", Rp, v)
    if "sword" in spec.get("held", []):
        h = rig.index["hand_r"]
        d = local(np.einsum("fij,j->fi", G[:n, h], pc["blade"]["dir"]))
        below = np.degrees(np.arctan2(-d[:, 1], np.hypot(d[:, 0], d[:, 2])))
        out["blade_below_deg"] = round(float(below.mean()), 1)
        out["blade_swing_deg"] = round(float(np.ptp(below)), 1)
        out["blade_heading_deg"] = round(float(np.degrees(np.arctan2(d[:, 0], d[:, 2])).mean()), 1)
        grip = P[:n, h] + np.einsum("fij,j->fi", G[:n, h], pc["blade"]["at"])
        tip = grip + np.einsum("fij,j->fi", G[:n, h], pc["blade"]["dir"]) * pc["blade"]["tip"]
        out["blade_tip_cm"] = round(100 * float(tip[:, 1].mean()), 1)
    if "shield" in spec.get("held", []):
        la = rig.index["lowerarm_l"]
        boss = P[:n, la] + np.einsum("fij,j->fi", G[:n, la], pc["shieldp"]["at"])
        b = local(boss - P[:n, pv]).mean(0)
        out["boss_l_cm"], out["boss_up_cm"], out["boss_fwd_cm"] = (round(100 * float(x), 1) for x in b)
        pts = np.einsum("fij,kj->fki", G[:n, la], pc["shield"]) + P[:n, la][:, None]
        out["shield_top_cm"] = round(100 * float(pts[:, :, 1].max(1).mean()), 1)
        f = local(np.einsum("fij,j->fi", G[:n, la], pc["shieldp"]["face"]))
        out["shield_open_deg"] = round(float(np.degrees(np.arctan2(f[:, 0], f[:, 2])).mean()), 1)
        # (the face tipped down = the top edge leaning out from her, deg)
        out["shield_tilt_deg"] = round(float(np.degrees(np.arctan2(-f[:, 1], np.hypot(f[:, 0], f[:, 2]))).mean()), 1)
    return out


def action_held(r, spec):
    """Per-frame series of the held pieces for an action's bands (measures.at): blade_below_deg (the blade's angle
    below the horizontal), tip_cm (its tip's height), tip_ahead_cm (the tip ahead of the pelvis along her heading),
    shield_top_cm (its top edge's height), shield_face_deg (its face's heading off hers, + open), boss_sternum_cm
    (the boss from the chest, spine_05's head)."""
    out = {}
    rig, G, P = r.rig, r.G, r.P
    pv = rig.index["pelvis"]
    Rp = G[:, pv] @ rig.R0[pv].T
    fwd = Rp @ np.array([0, 0, 1.0])
    hd = np.stack([fwd[:, 0], np.zeros(len(fwd)), fwd[:, 2]], 1)
    hd /= np.linalg.norm(hd, axis=1, keepdims=True) + 1e-12
    pc = pieces()
    if "sword" in spec.get("held", []):
        h = rig.index["hand_r"]
        d = np.einsum("fij,j->fi", G[:, h], pc["blade"]["dir"])
        out["blade_below_deg"] = np.degrees(np.arctan2(-d[:, 1], np.hypot(d[:, 0], d[:, 2])))
        grip = P[:, h] + np.einsum("fij,j->fi", G[:, h], pc["blade"]["at"])
        tip = grip + d * pc["blade"]["tip"]
        out["tip_cm"] = 100 * tip[:, 1]
        out["tip_ahead_cm"] = 100 * np.einsum("fi,fi->f", tip - P[:, pv], hd)
        out["grip_cm"] = 100 * grip[:, 1]                                       # (the grip's height)
        out["grip_ahead_cm"] = 100 * np.einsum("fi,fi->f", grip - P[:, pv], hd)
        # (solver R1, the leap's line: the tip's speed (m/s) and when it peaks (s, one number on every frame); the
        # sword arm's elbow bend (deg, 0 = straight) and the hand behind the Head bone along her heading (cm): a cocked
        # wind-up reads bent and behind, a raised flag straight and over)
        v = np.linalg.norm(np.diff(tip, axis=0), axis=1) * r.src.fps
        out["tip_mps"] = np.r_[v, v[-1:]]
        out["tip_peak_s"] = np.full(len(tip), float(np.argmax(v)) / r.src.fps)
        ua_, la_ = P[:, rig.index["upperarm_r"]] - P[:, rig.index["lowerarm_r"]], P[:, h] - P[:, rig.index["lowerarm_r"]]
        cs = np.einsum("fi,fi->f", ua_, la_) / (np.linalg.norm(ua_, axis=1) * np.linalg.norm(la_, axis=1) + 1e-12)
        out["elbow_r_deg"] = 180 - np.degrees(np.arccos(np.clip(cs, -1, 1)))
        out["hand_r_behind_head_cm"] = -100 * np.einsum("fi,fi->f", P[:, h] - P[:, rig.index["Head"]], hd)
    # (the shoulders turned against the hips about the vertical, deg, + = her left shoulder forward)
    sl = P[:, rig.index["upperarm_l"]] - P[:, rig.index["upperarm_r"]]
    hl = P[:, rig.index["thigh_l"]] - P[:, rig.index["thigh_r"]]
    tw = np.degrees(np.arctan2(sl[:, 2], sl[:, 0]) - np.arctan2(hl[:, 2], hl[:, 0]))
    out["twist_deg"] = -((tw + 180) % 360 - 180)
    # (her look: the face's forward (Head's rest +Z) below the horizontal, deg, + down)
    hz = np.einsum("fij,j->fi", G[:, rig.index["Head"]] @ rig.R0[rig.index["Head"]].T, [0, 0, 1.0])
    out["head_down_deg"] = np.degrees(np.arctan2(-hz[:, 1], np.hypot(hz[:, 0], hz[:, 2])))
    hold = r.clip.get("beats", {}).get("hold")
    if hold:                           # (the settle: the pelvis below its hold height, % of the hold's drop from frame 0)
        y = P[:, pv, 1]
        yh = y[int(round(hold[0] * r.src.fps))]
        out["settle_pct"] = 100 * (yh - y) / max(y[0] - yh, 1e-6)
    if spec.get("fit", {}).get("end"):  # (each frame's largest keyed-bone turn off the clip it ends in, deg; its pelvis
        e = spec["fit"]["end"]          # by its world turn)
        tg = end_pose(e["clip"], e.get("frame", 0))
        from motion import quat as Q
        dd = []
        for b, q in tg["rot"].items():
            if b in ("root", "pelvis") or b not in rig.index:
                continue
            j = rig.index[b]
            L = np.swapaxes(G[:, rig.parent[j]], -1, -2) @ G[:, j]
            dd.append(np.degrees(Q.angle(L, Q.to_mat(np.asarray(q, float)[None]))))
        dd.append(np.degrees(Q.angle(G[:, pv], np.asarray(tg["pelvis_rot"])[None])))
        out["end_deg"] = np.max(dd, 0)
    if "shield" in spec.get("held", []):
        la = rig.index["lowerarm_l"]
        boss = P[:, la] + np.einsum("fij,j->fi", G[:, la], pc["shieldp"]["at"])
        pts = np.einsum("fij,kj->fki", G[:, la], pc["shield"]) + P[:, la][:, None]
        out["shield_top_cm"] = 100 * pts[:, :, 1].max(1)
        f = np.einsum("fji,fj->fi", Rp, np.einsum("fij,j->fi", G[:, la], pc["shieldp"]["face"]))
        out["shield_face_deg"] = np.degrees(np.arctan2(f[:, 0], f[:, 2]))
        out["boss_sternum_cm"] = 100 * np.linalg.norm(boss - P[:, rig.index["spine_05"]], axis=1)
        out["boss_cm"] = 100 * boss[:, 1]                                       # (the shield's centre height)
        # (the shield's top edge under her left shoulder joint, cm, + = under: a shield carried low and out, not over her)
        out["shield_under_shoulder_cm"] = 100 * P[:, rig.index["upperarm_l"], 1] - out["shield_top_cm"]
        out["boss_left_cm"] = 100 * np.einsum("fi,fi->f", boss - P[:, pv], np.cross([0, 1.0, 0], hd))
        out["boss_ahead_cm"] = 100 * np.einsum("fi,fi->f", boss - P[:, pv], hd)  # (ahead of the pelvis, her heading)
        # (a block's cover: the shield's top edge over her eyes (EYE_BELOW_TOP under the head's top, along the Head's
        # up), and its face ahead of the head's top along her heading (+ = the head tucked behind it))
        hj = rig.index["Head"]
        top = P[:, hj] + np.einsum("fij,j->fi", G[:, hj] @ rig.R0[hj].T, [0, 1.0, 0]) * head_top()
        eye = top - np.einsum("fij,j->fi", G[:, hj] @ rig.R0[hj].T, [0, 1.0, 0]) * EYE_BELOW_TOP
        out["shield_over_eyes_cm"] = out["shield_top_cm"] - 100 * eye[:, 1]
        out["head_behind_cm"] = 100 * np.einsum("fi,fi->f", boss - top, hd)
    if "sword" in spec.get("held", []) or "shield" in spec.get("held", []):
        for sd in "lr":                # (the hands ahead of the pelvis along her heading: a shove's reach)
            out[f"hand_{sd}_ahead_cm"] = 100 * np.einsum("fi,fi->f", P[:, rig.index[f"hand_{sd}"]] - P[:, pv], hd)
    # (a guard's numbers, R3: each heel's ground point over the floor; the pelvis and the boss along the clip's +Z (the
    # node's facing: a press, a punch's travel); the shoulders' yaw against the hips' (+ = the chest to her left); the
    # blade's heading off hers (+ = to her left); the sword's closest point to the shield (a blade laid over the rim))
    from motion import fit as FIT
    gp = FIT.ground_points(rig, G, P)
    for sd in "lr":
        out[f"heel_{sd}_cm"] = 100 * gp[f"heel_{sd}"][:, 1]
    out["pelvis_z_cm"] = 100 * P[:, pv, 2]
    sl, hl = P[:, rig.index["upperarm_l"]] - P[:, rig.index["upperarm_r"]], P[:, rig.index["thigh_l"]] - P[:, rig.index["thigh_r"]]
    tw = np.degrees(np.arctan2(sl[:, 2], sl[:, 0]) - np.arctan2(hl[:, 2], hl[:, 0]))
    out["twist_deg"] = -((tw + 180.0) % 360.0 - 180.0)
    if "sword" in spec.get("held", []):
        dl = np.einsum("fji,fj->fi", Rp, d)
        out["blade_yaw_deg"] = np.degrees(np.arctan2(dl[:, 0], dl[:, 2]))
    if "shield" in spec.get("held", []):
        out["boss_z_cm"] = 100 * boss[:, 2]
        if "sword" in spec.get("held", []):
            sw = np.einsum("fij,kj->fki", G[:, h], pc["sword"][::3]) + P[:, h][:, None]
            sh = pts[:, ::2]
            out["blade_rim_cm"] = 100 * np.array([np.linalg.norm(sw[f][:, None] - sh[f][None], axis=2).min() for f in range(len(P))])
    return out


EYE_BELOW_TOP = 0.11     # m: an adult's eyes under the top of the head (vertex to pupil, ~11-12 cm)


def head_top():
    """The top of her head over the Head bone's head at rest (m): the skin's highest point, B's rest."""
    if "_ht" not in globals():
        body_field()
        B = globals()["_bfB"]
        from motion.rig import Rig
        rig = Rig(RIG)
        V = (np.c_[B.p.P0, np.ones(len(B.p.P0))] @ np.linalg.inv(B.X).T)[:, :3]
        globals()["_ht"] = float(V[:, 1].max() - rig.head[rig.index["Head"]][1])
    return _ht


def hand_targets(r, spec):
    """The keyed hands' distance from their targets on B (cm; mean and worst over the clip): each target rides the
    pelvis at its rest offset (gen.keys.hands, B meters from the pelvis head, her left/up/forward)."""
    K = spec.get("gen", {}).get("keys")
    if not K:
        return {}
    rig, out = r.rig, {}
    pv = rig.index["pelvis"]
    Rrel = r.G[:, pv] @ rig.R0[pv].T
    for h, off in K.get("hands", {}).items():
        b = rig.index["hand_l" if h.startswith("Left") else "hand_r"]
        t = r.P[:, pv] + Rrel @ np.asarray(off)
        d = np.linalg.norm(r.P[:, b] - t, axis=1) * 100
        s = "l" if h.startswith("Left") else "r"
        out[f"hand_{s}_target_cm"] = round(float(d.mean()), 2)
        out[f"hand_{s}_target_max_cm"] = round(float(d.max()), 2)
    return out


def gen_specs(names):
    return [(p, json.loads(p.read_text())) for p in specs(names, True) if json.loads(p.read_text()).get("gen")]


def soma_k(spec):
    """B's size over SOMA's (the retarget's scale), from the clip's current source."""
    return float(retarget.scale_of(retarget.Rig(RIG), soma.load_npz(P4 / spec["source"])))


def path_of(g, sc):
    r = dict(g["root2d"])
    for k in ("travel", "overshoot"):
        if k in r:
            r[k] = r[k] * sc
    # (heading_tps: a heading track at that rate, turns a second, + to her left: a spin's turn, Kimodo's heading)
    # (orbit [x, z]: the root circles a pivot at the origin, at that offset when the heading is 0 and turning with it:
    # a spin over a planted foot)
    tps, h0, orb = r.pop("heading_tps", None), r.pop("heading_deg0", 0.0), r.pop("orbit", None)
    # (face_deg: a constant heading track, her facing held while the path goes any way: a back or side walk's)
    face = r.pop("face_deg", None)
    out = {"xz": paths.make(r, g["seconds"], KFPS).round(5).tolist(), "every": r.get("every", 1)}
    if face is not None and not tps:
        out["heading"] = [round(float(np.radians(face)), 6)] * len(out["xz"])
    if tps:
        h = np.radians(h0) + 2 * np.pi * tps * np.arange(len(out["xz"])) / KFPS
        out["heading"] = h.round(6).tolist()
        if orb:
            c, s_ = np.cos(h), np.sin(h)
            out["xz"] = (np.array(out["xz"]) + np.stack([c * orb[0] + s_ * orb[1], -s_ * orb[0] + c * orb[1]], 1)
                         ).round(5).tolist()
    return out


def jobs_of(names):
    """Each prompt x each path scale (root2d_scales: Kimodo's hips swing past its smooth root, and not linearly, so
    the path's amplitude is searched; the scale is in the job name, s<percent>). gen.keys: hand end-effector keys
    (kimodo_run.hand_keys) taken from our own take {src: {prompt, scale, pick}} at the B offsets (meters from the
    pelvis, her left/up/forward) mapped to SOMA's scale, regenerated per keys.prompts x keys.scales as __k<i>s<pct>."""
    jobs = []
    for p, sp in gen_specs(names):
        g = sp["gen"]
        def job(i, sc, nm):
            j = {"name": nm, "prompt": g["prompts"][i], "seconds": g["seconds"], "seed": g["seeds"][i % len(g["seeds"])],
                 "takes": g["takes"]}
            if g.get("root2d"):
                j["root2d"] = path_of(g, sc)
            return j
        for i in range(len(g["prompts"])):
            if not g.get("root2d") or "root2d_scales" not in g:
                jobs.append(job(i, 1.0, f"{p.stem}__p{i}"))
                continue
            for sc in g["root2d_scales"]:
                jobs.append(job(i, sc, f"{p.stem}__p{i}s{round(sc * 100)}"))
        if g.get("more"):              # (more takes of chosen prompts, new seeds: __m<i>)
            for i in g["more"]["prompts"]:
                j = job(i, 1.0, f"{p.stem}__m{i}")
                j.update(takes=g["more"]["takes"], seed=j["seed"] + g["more"]["seed_add"])
                jobs.append(j)

        def pz(d):
            d = dict(d)
            if isinstance(d.get("prompt"), int):
                d["prompt"] = g["prompts"][d["prompt"]]
            d.setdefault("seconds", g["seconds"])
            d.setdefault("takes", g["takes"])
            if d.get("keys", {}).get("poses"):          # (a source that is itself a keyed take)
                d["keys"] = dict(d["keys"], poses=[dict(q, src=pz(q["src"])) for q in d["keys"]["poses"]])
            return d
        if g.get("keys") and g["keys"].get("poses") and not g["keys"].get("src"):
            # (keyed beats: FullBody key poses from native takes {src: {prompt: index | text, seed, seconds, takes},
            # pick, frame (the source take's), at (this job's frame), xz, yaw, lift} (kimodo_run.pose_keys); Kimodo
            # makes only the in-betweens, per keys.prompts x keys.seeds as __q<tag><i>s<seed>)
            K = g["keys"]
            poses = [dict(q, src=pz(q["src"])) for q in K["poses"]]
            for i in K.get("prompts", range(len(g["prompts"]))):
                for sd in K.get("seeds", [g["seeds"][i % len(g["seeds"])]]):
                    j = job(i, 1.0, f"{p.stem}__q{K.get('tag', '')}{i}s{sd}")
                    j.update(seed=sd, keys={"poses": poses})
                    if K.get("seconds"):
                        j["seconds"] = K["seconds"]
                    if K.get("takes"):
                        j["takes"] = K["takes"]
                    jobs.append(j)
        elif g.get("keys"):
            K = g["keys"]
            k = soma_k(sp)
            src = job(K["src"]["prompt"], K["src"].get("scale", 1.0), "src")
            src = {kk: src[kk] for kk in ("prompt", "seconds", "seed", "takes", "root2d") if kk in src}
            src["pick"] = K["src"].get("pick", 0)
            # (a source made by its own seed, length and keys: a keyed take, the hands then keyed on it)
            src.update({kk: K["src"][kk] for kk in ("seed", "seconds", "takes") if kk in K["src"]})
            if K["src"].get("keys"):
                src["keys"] = pz({"prompt": "", "keys": K["src"]["keys"]})["keys"]
            # (aim: what is sent = the target minus the take's measured mean miss on B, in the pelvis frame: the
            # retarget's arm calibration lands Kimodo's wrist a few cm from where it put SOMA's)
            aim = K.get("aim", {})
            hands = {h: [(x + a) / k for x, a in zip(off, aim.get(h, [0, 0, 0]))] for h, off in K.get("hands", {}).items()}
            # (an action's keys: end effectors at given take frames {joint: {frame: [l, u, f] B m from the pelvis}},
            # and FullBody key poses at given take frames (the take's pose there, after those edits))
            tgts = {jn: {f: [(x + a) / k for x, a in zip(off, aim.get(jn, [0, 0, 0]))] for f, off in d.items()}
                    for jn, d in K.get("targets", {}).items()}
            for i in K.get("prompts", [K["src"]["prompt"]]):
                for sc in K.get("scales", [K["src"].get("scale", 1.0)]):
                    for sd in K.get("seeds", [None]):     # (seeds: more takes of the keyed job, __k<tag><i>s<pct>r<seed>)
                        j = job(i, sc, f"{p.stem}__k{K.get('tag', '')}{i}s{round(sc * 100)}" + (f"r{sd}" if sd else ""))
                        j["keys"] = {"src": src, "hands": hands, "targets": tgts, "fullbody": K.get("fullbody", []),
                                     "start": K.get("start", 15), "every": K.get("every", 30)}
                        if sd:
                            j["seed"] = sd
                        for kk in ("seconds", "takes"):
                            if K.get(kk):
                                j[kk] = K[kk]
                        jobs.append(j)
    return jobs


def cmd_gen(a):
    import subprocess
    import tempfile
    jobs = jobs_of(a.clips)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f)
    core = str(Path(MARIONETTE) / "tools/motion/kimodo_run.py")
    env = dict(os.environ, TEXT_ENCODER_DEVICE="cpu", PYTHONUNBUFFERED="1")
    r = subprocess.run([KIMODO_PY, core, "encode", f.name, "--cache", str(CACHE)], env=env)
    if r.returncode or a.encode_only:
        os.unlink(f.name)
        sys.exit(r.returncode)
    r = subprocess.run([KIMODO_PY, core, "generate", f.name, str(TAKES_DIR), "--cache", str(CACHE)], env=env)
    os.unlink(f.name)
    sys.exit(r.returncode)


def cmd_takes(a):
    for p, sp in gen_specs(a.clips):
        bvhs = sorted(TAKES_DIR.glob(f"{p.stem}__*_*.bvh"))
        log = []
        tl = P4 / "specs" / f"{p.stem}.takes.json"
        if a.match and tl.exists():    # (score only the takes matching; the rest keep their logged scores)
            log = [t for t in json.loads(tl.read_text()) if a.match not in t["take"]]
            bvhs = [b for b in bvhs if a.match in b.name]
        for b in bvhs:
            try:
                r = run_post(b, sp, p.stem)
                m = measure(r, sp)
                sl = footlock.slide(r.P, r.rig, r.wins, r.belt, r.src.fps, r.m)
                m["slide_mm"] = round(max(sl) * 1000, 2)
                m["seam_cost"] = round(r.prep.seam_cost, 3) if getattr(r.prep, "seam_cost", None) is not None else None
                sc = measures.score(m, sp["bands"])
                log.append({"take": b.name, "score": sc, "frames": r.clip["frames"], "crop": list(r.prep.crop), **m})
            except Exception as e:  # (a take the core cannot read is logged, not fatal)
                log.append({"take": b.name, "score": 1e9, "error": str(e)})
        for t in log:                  # (logged takes re-scored against the spec's bands as they are now)
            if "error" not in t:
                t["score"] = measures.score(t, sp["bands"])
        # gate: bands a take must pass to be chosen at all (a run's cadence: playback scale cannot fix it)
        gate = {k: sp["bands"][k] for k in sp.get("gate", [])}
        log.sort(key=lambda x: (not all(k in x and lo <= x[k] <= hi for k, (lo, hi) in gate.items()), x["score"]))
        (P4 / "specs" / f"{p.stem}.takes.json").write_text(json.dumps(log, indent=1) + "\n")
        for t in log[:3]:
            print(f"{p.stem}: {t['take']} score {t['score']}")
        if log and log[0]["score"] < 1e9:
            best = TAKES_DIR / log[0]["take"]
            s = soma.read_bvh(str(best))
            soma.save_npz(s, P4 / "src" / f"{p.stem}.npz")
            sp.update({"source": f"src/{p.stem}.npz", "bvh": best.name, "sha1": s.sha1, "take_score": log[0]["score"]})
            p.write_text(json.dumps(sp, indent=1) + "\n")


OVER_GAIT_WINDOW = (0.1, 0.35)      # the cut's window the over-gait measure reads (s)
OVER_GAIT_OFFSETS = (0.0, 0.25, 0.5, 0.75)
OVER_GAIT_K = (0.5, 1.0)          # the counter's shares measured (the game runs PelvisCounter.K = 0.5)


def over_gait_of(spec, name):
    """A {"kind": "over_gait", "of": <stance clip>, "gait": <gait clip>, "arms": "node", "anchor": "pelvis"} spec built
    from the two BUILT clips (OUT): (the _run clip, its log, the stance clip, the gait clip). Marionette's over_gait."""
    from motion import over_gait as OG
    from motion.rig import Rig
    st, ga = MC.read(OUT / f"{spec['of']}.json"), MC.read(OUT / f"{spec['gait']}.json")
    sp = pieces()["shieldp"]["at"] if "shield" in spec.get("held", ["shield"]) else None
    up, log = OG.over_gait(st, ga, Rig(RIG), keep={"l": sp} if sp is not None else None, name=name,
                           arms=spec.get("arms", "node"), anchor=spec.get("anchor", "pelvis"), soft=spec.get("soft"),
                           targets=spec.get("targets", "world"))
    return up, log, st, ga


def over_gait_measure(up, st, ga, body=None, rig=None):
    """The _run laid over the gait (at its mean pelvis, then at OVER_GAIT_OFFSETS of its cycle) against its stance clip
    through OVER_GAIT_WINDOW, in the carried node frame: hand / blade tip / boss (cm), blade / chest (deg); pops
    (clipcheck.pops) and arms inside her body (clipcheck.contact) on each laid pose. {row: {key: value}}."""
    from motion import over_gait as OG
    from motion.rig import Rig
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    rig = rig or Rig(RIG)
    pc = pieces()
    bl = (pc["blade"]["at"], pc["blade"]["dir"], pc["blade"]["tip"])
    Gs, Ps = MC.globals_of(st, rig)
    Ps = Ps + np.array(up["meta"]["anchor_m"])[:, None]
    Gw, Pw = Gs, Ps                     # (the world path: the stance's in the carried node frame)
    if up["meta"].get("targets", "world") == "chest":    # the path the solve aimed at: carried by the re-solved chest
        Gm, Pm = OG.lay(up, ga, rig, 0.0, pelvis_mean=True)
        ch = rig.index["spine_05"]
        Gs, Ps = OG.carry(Gs, Ps, Gm[:, ch], Pm[:, ch], ch)
    fr = [f for f in range(st["frames"]) if OVER_GAIT_WINDOW[0] - 1e-6 <= f / st["fps"] <= OVER_GAIT_WINDOW[1] + 1e-6]
    rows = {}
    runs = [("mean", 0.0, None)] + [(str(o), o, None) for o in OVER_GAIT_OFFSETS]
    runs += [(f"k{k:g}@{o}", o, k) for k in OVER_GAIT_K for o in OVER_GAIT_OFFSETS]
    for o, at, k in runs:      # (k: the engine's pelvis counter, PelvisCounter's math, at that share of the swing)
        G, P = OG.lay(up, ga, rig, at, pelvis_mean=o == "mean", k=k)
        m = OG.paths(G, P, Gs, Ps, rig, fr, bl, pc["shieldp"]["at"])
        if Gw is not Gs:
            w = OG.paths(G, P, Gw, Pw, rig, fr, bl, pc["shieldp"]["at"])
            m.update({f"w_{k}": w[k] for k in ("tip_cm", "blade_deg", "hand_cm", "boss_cm")})
        Gb = m44(G, P)
        m["pops"] = len(CC.pops(rig.names, list(rig.parent), Gb, list(up["bones"]), False)[0])
        if body is not None:
            body.cache.clear()
            ct = CC.contact(body, Gb, list(range(len(Gb))), set(up["bones"]) | {n for n in rig.names if OG.lower(n)})
            m["arm_in_l"], m["arm_in_r"] = ct["l"]["inside"], ct["r"]["inside"]
        rows[o] = m
    return rows


def build_over_gait(p, sp):
    up, log, st, ga = over_gait_of(sp, p.stem)
    up["source"] = {"kind": "over_gait", "of": sp["of"], "gait": sp["gait"], "of_sha1": clip_hash(st), "gait_sha1": clip_hash(ga)}
    print(judged_note(p.stem, sp, up))
    MC.write(up, OUT / f"{p.stem}.json")
    print(f"  {p.stem} over {sp['gait']}: " + ", ".join(f"{k} {v}" for k, v in log.items()))
    print(f"  {p.stem} beats: {json.dumps(up['beats'])}; meta {json.dumps({k: v for k, v in up['meta'].items() if k != 'anchor_m'})}")
    print(f"{p.stem}: {up['frames']} frames, {len(up['rot'])} upper tracks (no root / pelvis / leg track) -> "
          f"{OUT.relative_to(REPO).as_posix()}/{p.stem}.json")


def check_over_gait(p, sp, body):
    built = OUT / f"{p.stem}.json"
    if not built.exists():
        print(f"{p.stem}: not built"); return None
    up = MC.read(built)
    st, ga = MC.read(OUT / f"{sp['of']}.json"), MC.read(OUT / f"{sp['gait']}.json")
    rows = over_gait_measure(up, st, ga, body)
    print("\n" + f"{p.stem}: {judged_state(sp, up)} (pack gate); over {sp['gait']}, against {sp['of']} in "
          f"{OVER_GAIT_WINDOW[0]}-{OVER_GAIT_WINDOW[1]} s (offset = share of the gait's cycle; mean = its mean pelvis)")
    keys = ("tip_cm", "blade_deg", "hand_cm", "boss_cm", "chest_deg", "chest_cm", "head_deg", "pops", "arm_in_l", "arm_in_r")
    if any("w_tip_cm" in m for m in rows.values()):     # (targets chest: the columns above against the chest-carried path)
        keys += ("w_tip_cm", "w_blade_deg", "w_hand_cm", "w_boss_cm")
    print("  " + "offset".ljust(9) + "".join(k.rjust(11) for k in keys))
    for o, m in rows.items():
        print("  " + o.ljust(9) + "".join(str(m.get(k, "-")).rjust(11) for k in keys))
    return {"clip": p.stem, "over_gait": rows}


def cmd_build(a):
    OUT.mkdir(parents=True, exist_ok=True)
    for p in specs(a.clips):
        if json.loads(p.read_text()).get("kind") == "over_gait":
            continue
        r = build_one(p)
        sp = json.loads(p.read_text())
        line = judged_note(p.stem, sp, r.clip)
        MC.write(r.clip, OUT / f"{p.stem}.json")
        print(line)
        for ln in law_lines(r.clip, r.rig, r.law[0]):
            print(ln)
        if sp.get("bands"):
            m = measure(r, sp)
            ok = measures.passes(m, sp["bands"])
            print(f"  {p.stem}: " + ", ".join(f"{k} {m.get(k)}{'' if ok[k] else ' MISS'}" for k in sp["bands"]))
            print(f"  {p.stem} more: " + ", ".join(f"{k} {v}" for k, v in m.items() if k not in sp["bands"] and
                                                     k.startswith(("step_", "wrist_", "blade_", "shield_", "boss_"))))
        for L in r.fitlog or []:
            print(f"  fit {L['layer']}: " + ", ".join(f"{k} {v}" for k, v in L.items() if k != "layer"))
        if r.clip.get("beats"):
            print(f"  {p.stem} beats: {json.dumps(r.clip['beats'])}")
        for nt in r.prep.notes:
            print(f"  note: {nt}")
        print(f"{p.stem}: {r.clip['frames']} frames, source crop {r.prep.crop}, yaw {r.prep.yaw_deg:.1f} deg, "
              f"windows L {len(r.wins[0])} R {len(r.wins[1])} -> {OUT.relative_to(REPO).as_posix()}/{p.stem}.json")
    for p in specs(a.clips):
        sp = json.loads(p.read_text())
        if sp.get("kind") == "over_gait":
            build_over_gait(p, sp)


POSE_OUT = REPO / "tools/anim/out/pose"      # git-ignored (/tools/anim/out/): nothing packs or judges it
POSE_AXES = ("node frame: +Y up, +Z her heading (the node's forward), +X her LEFT; every yaw / heading / facing is about the "
             "vertical against +Z, + = toward her left unless the key says right; cm and deg")


def _ang(u, v):
    return float(np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12), -1, 1))))


def _turn(R):
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def pose_measures(rig, G, P, f, held=("sword", "shield")):
    """A STANCE's numbers on one frame of B's FK (G, P: (F,J,3,3), (F,J,3) world; the held pieces mounted as the game
    seats them, pieces()). Everything is in the NODE's frame (POSE_AXES), never the pelvis's. {group: {key: value}}:
      feet    stagger_fwd_cm (left heel z - right heel z), across_cm (left heel x - right heel x), turnout_l/r_deg (the
              heel->ball line about the vertical against +Z, + = toes OUT on each side)
      pelvis  height_cm, drop_cm (B's rest height - now), yaw_deg (+ toward her left), roll_deg (+ = left hip up),
              weight_to_back_pct (the pelvis head along the heel-to-heel line: 0 over the front heel, 100 over the back
              heel, 50 centred), back_foot
      knees   flex_l/r_deg (thigh against calf, 0 = straight)
      trunk   lean_fwd_deg / lean_left_deg (pelvis->neck_01 against the vertical), chest_yaw_deg (spine_05's world turn
              against its rest), head_yaw_deg, head_roll_deg (+ = left ear up), head_pitch_deg (+ = chin down) (the
              Head's world turn against its rest: G @ R0.T, as fit.head)
      arm_l/r elbow_flex_deg (0 = straight), elbow_out_cm (the elbow joint's x from the shoulder joint's, + = out from
              the body), shoulder_lift_cm (measures.idle's: the shoulder joint over neck_01 against rest)
      sword   hand_right/up/fwd_cm (hand_r against the pelvis head), heading_right_deg (the blade about the vertical
              from +Z, + = toward her RIGHT, 180 = straight back), below_deg (under the horizontal), tip_x/y/z_cm,
              crosses_front_leg + past_leg_edge_cm: the blade's base (past the guard), middle and tip against the
              LEADING leg's knee and ankle x: yes when a point is beyond both on the side away from the sword hand,
              or within 6 cm of their x-span while in front (z) of the knee-ankle line at its height;
              past_leg_edge_cm = the worst point's x past the leg's edge nearest the sword hand (- = short of it)
      shield  boss_y_cm, top_cm, bottom_cm (max / min y of its points), facing_deg (the outward face normal's heading,
              + toward her left), rim_low_to_thigh_l_cm (the lowest point's horizontal distance to the left
              hip-joint->knee line at that point's height, clamped to the segment; its _left_cm / _fwd_cm parts)
      collar  spine05_local_deg / spine05_rest_deg / spine05_diff_deg (spine_05's LOCAL turn angle: nobody keys the
              collar, the diff must read 0), clavicle_l/r_vs_rest_deg (local against rest: 0)"""
    from motion import fit as FIT
    I = rig.index
    gp = {k: v[f] for k, v in FIT.ground_points(rig, G, P).items()}
    G, P = G[f], P[f]
    r1 = lambda x: round(float(x), 1)
    cm = lambda x: round(100 * float(x), 1)
    hd = lambda x, z: float(np.degrees(np.arctan2(x, z)))
    up = lambda y, x, z: float(np.degrees(np.arctan2(y, np.hypot(x, z))))
    rel = lambda b: G[I[b]] @ rig.R0[I[b]].T
    out = {}
    hl, hr = gp["heel_l"], gp["heel_r"]
    dl, dr = gp["ball_l"] - hl, gp["ball_r"] - hr
    out["feet"] = {"stagger_fwd_cm": cm(hl[2] - hr[2]), "across_cm": cm(hl[0] - hr[0]),
                   "turnout_l_deg": r1(hd(dl[0], dl[2])), "turnout_r_deg": r1(-hd(dr[0], dr[2]))}
    pv = I["pelvis"]
    Rp = rel("pelvis")
    back = "l" if hl[2] < hr[2] else "r"
    hb, hf = (hl, hr) if back == "l" else (hr, hl)
    ab = (hb - hf)[[0, 2]]
    out["pelvis"] = {"height_cm": cm(P[pv, 1]), "drop_cm": cm(rig.head[pv][1] - P[pv, 1]), "yaw_deg": r1(hd(Rp[0, 2], Rp[2, 2])),
                     "roll_deg": r1(up(Rp[1, 0], Rp[0, 0], Rp[2, 0])),
                     "weight_to_back_pct": r1(100 * ((P[pv] - hf)[[0, 2]] @ ab) / (ab @ ab + 1e-12)), "back_foot": back}
    out["knees"] = {f"flex_{s}_deg": r1(_ang(P[I[f"calf_{s}"]] - P[I[f"thigh_{s}"]], P[I[f"foot_{s}"]] - P[I[f"calf_{s}"]])) for s in "lr"}
    nk = I["neck_01"]
    v = P[nk] - P[pv]
    Rc, Rh = rel("spine_05"), rel("Head")
    out["trunk"] = {"lean_fwd_deg": r1(hd(v[2], v[1])), "lean_left_deg": r1(hd(v[0], v[1])), "chest_yaw_deg": r1(hd(Rc[0, 2], Rc[2, 2])),
                    "head_yaw_deg": r1(hd(Rh[0, 2], Rh[2, 2])), "head_roll_deg": r1(up(Rh[1, 0], Rh[0, 0], Rh[2, 0])),
                    "head_pitch_deg": r1(-up(Rh[1, 2], Rh[0, 2], Rh[2, 2]))}
    for s, sx in (("l", 1.0), ("r", -1.0)):
        S, E, Wr = P[I[f"upperarm_{s}"]], P[I[f"lowerarm_{s}"]], P[I[f"hand_{s}"]]
        lift = (S[1] - P[nk, 1]) - (rig.head[I[f"upperarm_{s}"]][1] - rig.head[nk][1])
        out[f"arm_{s}"] = {"elbow_flex_deg": r1(_ang(E - S, Wr - E)), "elbow_out_cm": cm(sx * (E[0] - S[0])), "shoulder_lift_cm": cm(lift)}
    pc = pieces()
    if "sword" in held:
        h = I["hand_r"]
        at, dr0, tl = np.array(pc["blade"]["at"]), np.array(pc["blade"]["dir"]), pc["blade"]["tip"]
        d = G[h] @ dr0
        grip = P[h] + G[h] @ at
        tip = grip + d * tl
        al = (pc["sword"] - at) @ dr0
        g0 = float(al[np.argmax(np.linalg.norm((pc["sword"] - at) - np.outer(al, dr0), axis=1))]) + 0.015    # (past the guard)
        lead = "r" if back == "l" else "l"
        K, A = P[I[f"calf_{lead}"]], P[I[f"foot_{lead}"]]
        sg = float(np.sign((K[0] + A[0]) / 2 - P[h, 0])) or 1.0
        near, far = min(sg * K[0], sg * A[0]), max(sg * K[0], sg * A[0])
        past, hit = [], []
        for p in (grip + d * g0, grip + d * (g0 + tl) / 2, tip):
            t = float(np.clip((K[1] - p[1]) / (K[1] - A[1] + 1e-12), 0, 1))
            u = sg * p[0]
            past.append(u - near)
            hit.append(bool(u > far or (near - 0.06 <= u <= far + 0.06 and p[2] > K[2] + t * (A[2] - K[2]))))
        hp = P[h] - P[pv]
        out["sword"] = {"hand_right_cm": cm(-hp[0]), "hand_up_cm": cm(hp[1]), "hand_fwd_cm": cm(hp[2]),
                        "heading_right_deg": r1(hd(-d[0], d[2])), "below_deg": r1(up(-d[1], d[0], d[2])),
                        "tip_x_cm": cm(tip[0]), "tip_y_cm": cm(tip[1]), "tip_z_cm": cm(tip[2]),
                        "crosses_front_leg": "yes" if any(hit) else "no", "front_leg": lead,
                        "past_leg_edge_cm": cm(max(p for p, k in zip(past, hit) if k) if any(hit) else max(past))}
    if "shield" in held:
        la = I["lowerarm_l"]
        pts = pc["shield"] @ G[la].T + P[la]
        n = G[la] @ np.array(pc["shieldp"]["face"])
        low = pts[np.argmin(pts[:, 1])]
        Hj, K = P[I["thigh_l"]], P[I["calf_l"]]
        q = Hj + float(np.clip((Hj[1] - low[1]) / (Hj[1] - K[1] + 1e-12), 0, 1)) * (K - Hj)
        out["shield"] = {"boss_y_cm": cm((P[la] + G[la] @ np.array(pc["shieldp"]["at"]))[1]), "top_cm": cm(pts[:, 1].max()),
                         "bottom_cm": cm(pts[:, 1].min()), "facing_deg": r1(hd(n[0], n[2])),
                         "rim_low_to_thigh_l_cm": cm(np.hypot(low[0] - q[0], low[2] - q[2])),
                         "rim_low_left_cm": cm(low[0] - q[0]), "rim_low_fwd_cm": cm(low[2] - q[2])}
    loc = lambda b: G[rig.parent[I[b]]].T @ G[I[b]]
    a, b = _turn(loc("spine_05")), _turn(rig.Lr0[I["spine_05"]])
    out["collar"] = {"spine05_local_deg": r1(a), "spine05_rest_deg": r1(b), "spine05_diff_deg": r1(a - b),
                     **{f"clavicle_{s}_vs_rest_deg": r1(_turn(rig.Lr0[I[f"clavicle_{s}"]].T @ loc(f"clavicle_{s}"))) for s in "lr"}}
    return out


def pose_lines(pm):
    """pose_measures as print lines: one per group, and the plain blade line."""
    L = [f"  {g}: " + ", ".join(f"{k} {v}" for k, v in d.items()) for g, d in pm.items()]
    if "sword" in pm:
        s = pm["sword"]
        L.append(f"  blade crosses front leg (front view): {s['crosses_front_leg']}"
                 + (f", by {s['past_leg_edge_cm']} cm past leg_{s['front_leg']}'s near edge" if s["crosses_front_leg"] == "yes"
                    else f" (nearest blade point {-s['past_leg_edge_cm']} cm short of leg_{s['front_leg']}'s near edge in x)"))
    return L


def cmd_pose(a):
    """A spec built as a short STILL for a pose loop (seconds, not minutes): `--frames` source frames around `--at`
    (default: the middle of post.crop), loop off, no cycle search, fit.clear dropped unless --clear (so body_field()
    is not built for the fit). Writes tools/anim/out/pose/<clip>.json (never OUT), prints the build's measures and
    fit notes, then the STANCE's own numbers on the middle frame (pose_measures -> <clip>.measures.json), and draws
    that frame as one row of four large tiles: game, front, side, three-quarter (p4_strip.pose_sheet) -> <clip>.jpg.
    --beside a,b: frame 0 of the built clips a, b (OUT) as rows under it, same cameras and scale."""
    import time
    import types
    t0 = time.time()
    spec = json.loads((P4 / "specs" / f"{a.clip}.json").read_text())
    po = spec.setdefault("post", {})
    crop = po.get("crop") or [0, soma.load_npz(P4 / spec["source"]).frames - 1]
    at = a.at if a.at is not None else (crop[0] + crop[1]) // 2
    lo = max(0, at - a.frames // 2)
    po.update({"crop": [lo, lo + a.frames - 1], "loop": False})
    po.pop("cycle_s", None)
    spec["loop"] = False
    if not a.clear and spec.get("fit"):
        spec["fit"].pop("clear", None)
    r = run_post(P4 / spec["source"], spec, a.clip)
    POSE_OUT.mkdir(parents=True, exist_ok=True)
    out = POSE_OUT / f"{a.clip}.json"
    MC.write(r.clip, out)
    t1 = time.time()
    m = measure(r, spec)
    ok = measures.passes(m, spec.get("bands", {}))
    print(f"pose {a.clip}: source frames {po['crop'][0]}-{po['crop'][1]} (still, loop off, clear {'ON' if a.clear else 'off'}), "
          f"{r.clip['frames']} frames, build {t1 - t0:.1f} s")
    print("  bands: " + ", ".join(f"{k} {m.get(k)}{'' if ok[k] else ' MISS'}" for k in spec.get("bands", {})))
    print("  more: " + ", ".join(f"{k} {v}" for k, v in m.items() if k not in spec.get("bands", {})))
    for L in r.fitlog or []:
        print(f"  fit {L['layer']}: " + ", ".join(f"{k} {v}" for k, v in L.items() if k != "layer"))
    for nt in r.prep.notes:
        print(f"  note: {nt}")
    for ln in law_lines(r.clip, r.rig, r.law[0]):
        print(ln)
    import p4_strip
    mid = r.clip["frames"] // 2
    held_ = spec.get("held", [])
    pm = pose_measures(r.rig, *MC.globals_of(MC.read(out), r.rig), mid, held_)     # (the written clip: what the sheet draws)
    print(f"  stance (frame {mid}; node frame: +X her left, +Y up, +Z her heading):")
    print("\n".join("  " + L for L in pose_lines(pm)))
    (POSE_OUT / f"{a.clip}.measures.json").write_text(json.dumps(
        {"clip": a.clip, "frame": mid, "source_frames": po["crop"], "axes": POSE_AXES, "measures": pm}, indent=1))
    rows = [(f"{a.clip} pose f{mid}", out, mid, held_)]
    for nm in [x.strip() for x in (a.beside or "").split(",") if x.strip()]:
        bp, sp = OUT / f"{nm}.json", P4 / "specs" / f"{nm}.json"
        if not bp.exists():
            print(f"  beside {nm}: no built clip at {bp.relative_to(REPO).as_posix()}, skipped")
            continue
        # (a spec without `held` is a sheathed clip: nothing in the hands)
        rows.append((f"{nm} f0", bp, 0, json.loads(sp.read_text()).get("held", []) if sp.exists() else ["sword", "shield"]))
    jpg = p4_strip.pose_sheet(sys.modules[__name__], rows, a.tile, POSE_OUT / f"{a.clip}.jpg")
    print(f"pose {a.clip}: {time.time() - t0:.1f} s in all -> {jpg}")


def clearance(G, P, held, target_mm=10.0, n=None, pts=800):
    """Each held piece against her skin (body_field: the winding number's sign) on every frame of a clip: the closest
    gap (mm, + outside), the deepest in (mm, 0 if never), the frames inside and the frames under target_mm."""
    from motion import fit as FIT
    bones = {"sword": "hand_r", "shield": "lowerarm_l"}
    pc, rng = pieces(), np.random.default_rng(1)
    sel = {k: pc[k][rng.choice(len(pc[k]), min(len(pc[k]), pts), replace=False)] for k in held}
    from motion.rig import Rig
    rig = Rig(RIG)
    out = {k: {"gap_mm": 1e9, "in_mm": 0.0, "inside": [], "under": []} for k in held}
    bf = body_field()
    for f in range(n or len(G)):
        field = bf(G[f], P[f])
        for k in held:
            j = rig.index[bones[k]]
            sd = float(field(sel[k] @ G[f, j].T + P[f, j])[0].min()) * 1000
            o = out[k]
            o["gap_mm"] = min(o["gap_mm"], sd)
            if sd < 0:
                o["in_mm"] = max(o["in_mm"], -sd)
                o["inside"].append(f)
            if sd < target_mm:
                o["under"].append(f)
    return {k: {"gap_mm": round(v["gap_mm"], 1), "in_mm": round(v["in_mm"], 1), "inside": FIT._ranges(v["inside"]),
                "under": FIT._ranges(v["under"])} for k, v in out.items()}


GROUND_CM = 2.5          # a foot is on the floor where its ball AND its heel point are within this of their floor heights
SKATE_CM = 1.0           # the fail line: a foot's grounded travel outside its planted windows, cm a clip (see skate())


def _foot_pts(rig, G, P, s, tps=None, fps=30):
    """One foot's ball and heel ground point (F,3) (a de-rotated spin's in the WORLD: the game's turn put back),
    its sole's tilt from flat (deg) and its leg's reach (the hip-ankle distance over the leg's length)."""
    from motion.footlock import heel_local
    th, ca, fo, ba = (rig.index[f"{b}_{s}"] for b in ("thigh", "calf", "foot", "ball"))
    ball, heel = P[:, ba].copy(), P[:, fo] + np.einsum("fij,j->fi", G[:, fo], heel_local(rig, fo))
    if tps:
        w = 2 * np.pi * tps * np.arange(len(P)) / fps
        c, sn = np.cos(w), np.sin(w)
        ball, heel = (np.stack([c * q[:, 0] + sn * q[:, 2], q[:, 1], -sn * q[:, 0] + c * q[:, 2]], 1) for q in (ball, heel))
    tilt = np.degrees(np.arccos(np.clip((G[:, fo] @ rig.R0[fo].T)[:, 1, 1], -1, 1)))
    reach = np.linalg.norm(P[:, fo] - P[:, th], axis=1) / (np.linalg.norm(P[:, ca] - P[:, th], axis=1) +
                                                             np.linalg.norm(P[:, fo] - P[:, ca], axis=1))
    return ball, heel, tilt, reach


def skate(r, spec, G=None, P=None):
    """Skating, per foot: its grounded travel OUTSIDE its planted windows, cm. On each frame step where the foot is on
    the floor at both ends (ball and heel point within GROUND_CM of their floor heights: the ball's rest height, 0)
    the smaller of the ball's and the heel point's horizontal step is summed (the belt out for a gait, in the world
    for a de-rotated spin), so a pivot on the heel or the ball is free and a drag is counted. Over SKATE_CM is a MISS."""
    G, P = (r.G, r.P) if G is None else (G, P)
    rig, fps, n, m = r.rig, r.src.fps, len(P), r.m
    tps = (spec.get("post", {}).get("action") or {}).get("derotate_tps")
    out = {}
    for si, s in enumerate("lr"):
        ball, heel, _, _ = _foot_pts(rig, G, P, s, tps, fps)
        hb = rig.head[rig.index[f"ball_{s}"]][1]
        on = (np.abs(ball[:, 1] - hb) < GROUND_CM / 100) & (np.abs(heel[:, 1]) < GROUND_CM / 100)
        pl = {(ws + k) % m for ws, ln, _ in _contacts(r, si) for k in range(ln)}
        pl |= set((getattr(r, "rides", None) or [[], []])[si])   # (a push-off foot riding the travel strip on the floor
        #                                                          (plant ride): still in the world, the node carries her)
        tot, worst, cnt = 0.0, (0.0, 0), 0
        for f in range(m if r.clip["loop"] else n - 1):
            g = (f + 1) % m if r.clip["loop"] else f + 1
            inw = f in pl and g in pl
            # (a de-rotated spin (solver S1): a window pinned in the clip is not still in the WORLD unless it is on the
            # turn's axis or turned back, so its planted windows are counted too, by the ball's travel in the world)
            if (inw and not tps) or not (inw or (on[f] and on[g])):
                continue
            d = min(np.linalg.norm((q[g] - q[f] - r.belt / fps)[[0, 2]]) for q in ((ball,) if inw else (ball, heel))) * 100
            tot, cnt = tot + d, cnt + 1
            if d > worst[0]:
                worst = (float(d), g)
        out[s] = {"cm": round(tot, 2), "frames": cnt, "worst_cm": round(worst[0], 2), "at": worst[1]}
        if tps:                              # (a spin's floor: the ball over its rest height and the sole's lowest point)
            ba = rig.index[f"ball_{s}"]
            toe = P[:, ba] + np.einsum("fij,j->fi", G[:, ba], rig.R0[ba].T @ np.array([0.0, -hb, 0.11]))
            low = np.minimum(np.minimum(heel[:m, 1], ball[:m, 1] - hb), toe[:m, 1])
            out[s].update(ball_cm=[round(float(x) * 100, 2) for x in (ball[:m, 1].min() - hb, ball[:m, 1].max() - hb)],
                          low_cm=round(float(low.min()) * 100, 2), low_at=int(np.argmin(low)))
    return out


def _contacts(r, si):
    """One foot's planted windows: the lock's, and a spin's world-still steps (fit.axis.steps)."""
    return list(r.wins[si]) + list((getattr(r, "steps", None) or [[], []])[si])


def floors(r, G=None, P=None):
    """Each planted window's floor numbers: the ankle's and the ball's height over rest (cm, the largest either way),
    the sole's tilt from flat (deg, max) and the leg's reach (max)."""
    G, P = (r.G, r.P) if G is None else (G, P)
    rig, out = r.rig, {}
    for si, s in enumerate("lr"):
        ball, _, tilt, reach = _foot_pts(rig, G, P, s)
        fo, ba = rig.index[f"foot_{s}"], rig.index[f"ball_{s}"]
        out[s] = []
        for ws, ln, _ in _contacts(r, si):
            fr = [(ws + k) % r.m for k in range(ln)]
            big = lambda v: round(float(v[np.argmax(np.abs(v))]) * 100, 2)  # noqa: E731
            out[s].append({"frames": [int(fr[0]), int(fr[-1])], "ankle_cm": big(P[fr, fo, 1] - rig.head[fo][1]),
                           "ball_cm": big(ball[fr, 1] - rig.head[ba][1]), "tilt_deg": round(float(tilt[fr].max()), 1),
                           "reach": round(float(reach[fr].max()), 3)})
    return out


def spot_off(rig, G, P, sj):
    """Where an action with an `end` clip stands against that clip's place (the node's frame, cm): its first frame's
    heels and pelvis, and the largest miss of its last frame's pelvis, heels and balls (over 0.5 = a slide when the
    game crossfades to the idle on her node). Explicit fit.end.spot points are the targets where given."""
    from motion import fit as FIT
    e = (sj.get("fit") or {}).get("end") or {}
    if not e.get("clip") or not (OUT / f"{e['clip']}.json").exists():
        return None
    tg = end_pose(e["clip"], e.get("frame", 0))["spot"]
    if isinstance(e.get("spot"), dict):
        tg.update({k: v for k, v in e["spot"].items() if k in FIT.SPOTS})
    pts = FIT.ground_points(rig, G, P)
    off = lambda k, f: round(100 * float(np.hypot(pts[k][f][0] - tg[k][0], pts[k][f][2] - tg[k][1])), 2)  # noqa: E731
    return {"start": [off(k, 0) for k in ("heel_l", "heel_r", "pelvis")], "end": max(off(k, -1) for k in tg)}


def m44(R, P):
    M = np.zeros(R.shape[:-2] + (4, 4))
    M[..., :3, :3], M[..., :3, 3], M[..., 3, 3] = R, P, 1
    return M


def _rest():
    from motion.rig import Rig
    rig = Rig(RIG)
    return rig.R0, rig.head


def MC_rig_names():
    from motion.rig import Rig
    return Rig(RIG).names


def cmd_check(a):
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    P1 = REPO / "godot/art/people/body_p1"
    rigj = json.loads((P1 / "rig.json").read_text())
    body = None
    rows, rows_og = [], []
    for p in specs(a.clips):
        sj0 = json.loads(p.read_text())
        if sj0.get("kind") == "over_gait":
            if body is None:
                body = CC.Body(str(P1 / "body.glb"), rigj, MC_rig_names(), m44(*_rest()), True)
            ro = check_over_gait(p, sj0, body)
            if ro:
                rows_og.append(ro)
            continue
        built = OUT / f"{p.stem}.json"
        if not built.exists():
            print(f"{p.stem}: not built"); continue
        c = MC.read(built)
        print(f"{p.stem}: " + judged_state(json.loads(p.read_text()), c)+ " (pack gate)")
        r = build_one(p)                       # (in memory: SOMA's side, for the contact windows and fidelity)
        rig = r.rig
        G, P = MC.globals_of(c, rig)
        Gb = m44(G, P)
        rest = m44(rig.R0, rig.head)
        # "A" for clipcheck's feet: SOMA's joints (scaled into B's space) under the B names they drive
        an = [n for n in rig.keyed if "joint" in rig.map.get(n, {})]
        Ga = m44(np.stack([r.Gs[:, r.src.index(rig.map[n]["joint"])] for n in an], 1),
                 np.stack([r.Ps[:, r.src.index(rig.map[n]["joint"])] for n in an], 1))
        d = {"name": p.stem, "fps": c["fps"], "loop": c["loop"], "a_names": an, "b_names": rig.names}
        if body is None:
            body = CC.Body(str(P1 / "body.glb"), rigj, rig.names, rest, True)
        body.cache.clear()
        n = len(Gb)
        frames = list(range(0, n, max(1, n // 30)))
        sp, worst, seam = CC.pops(rig.names, list(rig.parent), Gb, c["bones"], c["loop"])
        ft = CC.feet(d, Ga, Gb)
        ct = CC.contact(body, Gb, frames, set(c["bones"]))
        fid = retarget.fidelity_table(retarget.fidelity(rig, r.src, G, P))
        sl = footlock.slide(P, rig, r.wins, r.belt, c["fps"], r.m)
        sj = json.loads(p.read_text())
        cl = clearance(G, P, sj.get("held", []), n=n - 1 if c["loop"] else n) if sj.get("held") else {}
        rows.append({"clip": p.stem, "frames": n, "pops": len(sp), "clearance": cl, "worst_step": [round(worst[0], 2), worst[1], worst[2]],
                     "seam_deg": round(seam[0], 4) if c["loop"] else None, "feet": ft, "contact": ct,
                     "slide_mm": [round(x * 1000, 2) for x in sl], "fidelity": fid,
                     "locked_frames": [sum(w[1] for w in ws) for ws in r.wins],
                     "skate": skate(r, sj, G, P), "skate_line_cm": SKATE_CM, "floors": floors(r, G, P),
                     "spot": spot_off(rig, G, P, sj), "statue": statue_of(c, G, P, rig, at=True), "loop": c["loop"],
                     # (the built file's law bones: the tracks it still carries, and what a build now drops)
                     "law": {"lines": law_lines(c, rig), "dropped_by_build": r.law[0],
                             "tracks": {b: [round(v[0], 3), v[1]] for b, v in MC.off_rest(c, rig, LAW_BONES).items()}}})
    for R in rows:
        f, b = R["feet"], R["contact"]
        print(f"\n{R['clip']}: {R['frames']} frames, pops {R['pops']} (worst step {R['worst_step'][0]} deg {R['worst_step'][1]} "
              f"@{R['worst_step'][2]}), seam {R['seam_deg']} deg")
        print(f"  feet: locked frames L {R['locked_frames'][0]} R {R['locked_frames'][1]}, planted slide (core) L {R['slide_mm'][0]} "
              f"R {R['slide_mm'][1]} mm; clipcheck drift SOMA/B mm L {f['l']['A']}/{f['l']['B']} R {f['r']['A']}/{f['r']['B']} (belt {f['belt_mps']} m/s)")
        print("  skate (grounded travel outside the planted windows, cm; line %s): " % SKATE_CM + "  ".join(
            f"{s.upper()} {v['cm']}{' MISS' if v['cm'] > SKATE_CM else ''} ({v['frames']} steps, worst {v['worst_cm']} @{v['at']})"
            for s, v in R["skate"].items()))
        if any("low_cm" in v for v in R["skate"].values()):
            print("  floor (a spin; skate counts its planted windows in the world): " + "  ".join(
                f"{s.upper()} ball {v['ball_cm'][0]:+}..{v['ball_cm'][1]:+} cm over rest, lowest sole point {v['low_cm']:+} cm @{v['low_at']}"
                for s, v in R["skate"].items()))
        if R["spot"]:
            so = R["spot"]
            print(f"  spot: start off idle L {so['start'][0]:.1f} R {so['start'][1]:.1f} pelvis {so['start'][2]:.1f} cm; "
                  f"end off idle max {so['end']:.1f} cm{' MISS' if so['end'] > 0.5 else ''}")
        for ln in statue_lines(R["statue"], R["loop"]):
            print(ln)
        for ln in R["law"]["lines"] or [f"  law bones: no track ({', '.join(LAW_BONES)}: the law's, at rest under it)"]:
            print(ln)
        import p4_contact                      # (the blade's contact measure: contact on the crossing, the blend rule)
        R["blade"] = p4_contact.of_built(sys.modules[__name__], R["clip"])
        for ln in (p4_contact.lines(R["blade"]) if R["blade"] else []):
            print(ln)
        for s, ws in R["floors"].items():
            for w in ws:
                print(f"  planted {s} f{w['frames'][0]}-{w['frames'][1]}: ankle {w['ankle_cm']:+} cm, ball {w['ball_cm']:+} cm over rest, "
                      f"sole {w['tilt_deg']} deg from flat, reach {w['reach']}")
        print("  fidelity deg (mean / max, worst):  " + "  ".join(f"{g} {v['mean']}/{v['max']} {v['worst']}" for g, v in R["fidelity"].items()))
        for k, v in R["clearance"].items():
            print(f"  held {k}: closest gap {v['gap_mm']} mm, deepest in {v['in_mm']} mm (frames in: {v['inside'] or '-'}; "
                  f"under 10 mm: {v['under'] or '-'})")
        for s in "lr":
            v = b[s]
            print(f"  arm {s}: inside {v['inside']} verts, deepest {v['depth_mm']} mm @f{v['frame']} {v.get('where', '')}; "
                  f"axilla {v['axilla']}/{v['axilla_mm']} mm; hand gap {v['hand_gap_mm']} mm")
    out = REPO / "tools/body/out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "p4check.json").write_text(json.dumps(rows + rows_og, indent=1))


def cmd_judged(a):
    ps = specs(a.clips)
    if a.list or not a.clips:
        for p in ps:
            b = OUT / f"{p.stem}.json"
            st = "not built" if not b.exists() else {"judged": "judged", "not judged": "NOT JUDGED", "stale": "STALE"}[
                judged_state(json.loads(p.read_text()), MC.read(b))]
            print(f"{p.stem}: {st}")
        return
    for p in ps:
        b = OUT / f"{p.stem}.json"
        if not b.exists():
            sys.exit(f"{p.stem}: not built (build it first)")
        sp, built = json.loads(p.read_text()), MC.read(b)
        sp.pop("judged", None)
        built.pop("judged", None)
        if a.clear:
            print(f"{p.stem}: judged flag cleared")
        else:
            if not a.by:
                sys.exit("--by is required")
            sp["judged"] = {"by": a.by, "on": a.on or datetime.date.today().isoformat(), "verdict": a.verdict, "build": clip_hash(built)}
            built["judged"] = sp["judged"]
            print(f"{p.stem}: judged, build {sp['judged']['build']}")
        p.write_text(json.dumps(sp, indent=1) + "\n")
        MC.write(built, b)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("import")
    i.add_argument("bvh")
    i.add_argument("clip")
    i.add_argument("--loop", action="store_true")
    i.add_argument("--inplace", action="store_true")
    g = sub.add_parser("gen")
    g.add_argument("clips", nargs="*")
    g.add_argument("--encode-only", action="store_true")
    for nm in ("build", "check", "takes"):
        s = sub.add_parser(nm)
        s.add_argument("clips", nargs="*")
        if nm == "takes":
            s.add_argument("--match", default="")
    j = sub.add_parser("judged")
    j.add_argument("clips", nargs="*")
    j.add_argument("--by", default="")
    j.add_argument("--verdict", default="PASS")
    j.add_argument("--on", default="")
    j.add_argument("--list", action="store_true")
    j.add_argument("--clear", action="store_true")
    st = sub.add_parser("strip", help="an offline pose strip of a built clip (p4_strip.py): PNG + JPEG under tools/anim/out/strips")
    st.add_argument("clip", help="a built clip's name, or a path to a built JSON (a candidate)")
    st.add_argument("--every", type=int, default=2, help="every n-th 30 fps frame (beat frames are always drawn)")
    st.add_argument("--from", dest="frm", type=int, default=None)
    st.add_argument("--to", type=int, default=None)
    st.add_argument("--views", default="game,side", help="game, side, front, quarter")
    st.add_argument("--cols", type=int, default=12)
    st.add_argument("--tile", default="165x240")
    st.add_argument("--spin", type=float, default=0.0, help="turns/s: yaw her about the node's vertical axis (to her left), as the game does a de-rotated loop")
    st.add_argument("--pitch", type=float, default=None, help="the game view's pitch, deg down (default: FollowCamera.cs Pitch)")
    st.add_argument("--out", default="")
    ps = sub.add_parser("pose", help="a spec built as a short still (no loop search, no clear) + its measures and a large pose sheet: tools/anim/out/pose")
    ps.add_argument("clip")
    ps.add_argument("--at", type=int, default=None, help="the source frame to pose on (default: the middle of post.crop)")
    ps.add_argument("--frames", type=int, default=10)
    ps.add_argument("--clear", action="store_true", help="run fit.clear anyway (slow: her skin field)")
    ps.add_argument("--tile", default="330x480")
    ps.add_argument("--beside", default="", help="built clips (comma list): frame 0 of each as a row under the candidate's")
    a = ap.parse_args()
    if a.cmd == "pose":
        return cmd_pose(a)
    if a.cmd == "strip":
        import p4_strip
        return p4_strip.run(sys.modules[__name__], a)
    {"judged": cmd_judged, "import": cmd_import, "build": cmd_build, "check": cmd_check, "gen": cmd_gen, "takes": cmd_takes}[a.cmd](a)



EDGE = 0.013              # m: a skin vertex's patch for the field (her edges on B: median 6.8 mm, p95 12.7)


def skin_gap(d, pr, inside):
    """The field's signed distance (m, + outside) from the nearest skin vertex's distance d, the point's offset along
    that vertex's normal pr, and the winding's inside: along the normal where that agrees with the sign, but only
    within the vertex's own patch: past EDGE sideways the tangent plane is not her skin, the sideways rest counts (a
    point 40-57 cm off her side in a vertex's tangent plane read 0-8 mm: the leap's raised sword and out-held shield,
    and the clear layer moved arms that touched nothing; solver F3)."""
    t = np.sqrt(np.maximum(d * d - pr * pr, 0.0))
    mag = np.where((pr < 0) == inside, np.hypot(pr, np.maximum(t - EDGE, 0.0)), d)
    return np.where(inside, -mag, mag)


def body_field():
    """Her skin as the fit's `clear` layer and p4_blend read it: body(G, P) -> a field: world points -> (signed
    distance m, + outside; outward normals), B posed by clipcheck's poser (the glb's skin + B's laws).

    The sign is the generalized winding number of her whole closed skin (body + head pieces: Marionette
    motion/winding.py), so it holds deep inside her and far outside (the old nearest-vertex sign read any point over
    8 cm from her skin as outside: idle_warden's shield rim sat in her thigh at that ceiling and read clear). A point
    nearer her arms' skin than the rest is never inside (a held piece's strap in its own forearm, a blade against the
    other arm: the arms are clipcheck's matter). The distance: to the nearest skin vertex but the arms' (torso, legs,
    neck, head), along its normal where that agrees with the sign; the normal is that vertex's."""
    if "_bf" in globals():
        return _bf
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    from scipy.spatial import cKDTree
    from motion.rig import Rig
    from motion.winding import Winding
    rig = Rig(RIG)
    P1 = REPO / "godot/art/people/body_p1"
    B = CC.Body(str(P1 / "body.glb"), json.loads((P1 / "rig.json").read_text()), rig.names, m44(rig.R0, rig.head), True)
    Xi = np.linalg.inv(B.X)
    keyed = set(rig.keyed)
    arm = B.arm["l"] | B.arm["r"] | B.hand["l"] | B.hand["r"]
    skin = np.nonzero(~arm)[0]
    armi = np.nonzero(arm)[0]
    # (a point well inside the rest mesh for the winding's orientation: the pelvis head, in glb space)
    pv = rig.index["pelvis"]
    W = Winding(B.p.T, B.p.P0, inside=(B.X @ np.r_[rig.head[pv], 1.0])[:3])

    def body(G, P):
        B.cache.clear()
        V, _, N, _ = B.pose(m44(G, P), keyed, 0)
        ts, ta = cKDTree(V[skin]), cKDTree(V[armi])

        def field(pts):
            Pg = (np.c_[pts, np.ones(len(pts))] @ B.X.T)[:, :3]
            d, i = ts.query(Pg)
            q = skin[i]
            da, _ = ta.query(Pg)
            inside = (W(V, Pg) > 0.5) & (da >= d)
            pr = np.einsum("ij,ij->i", Pg - V[q], N[q])
            s = skin_gap(d, pr, inside)
            nrm = N[q] @ Xi[:3, :3].T
            nrm = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
            return s, nrm
        return field
    globals()["_bf"], globals()["_bfB"] = body, B
    return body


class _Pose:
    """A built result as the fit's measures read it (fit.wrist_of)."""
    def __init__(self, r):
        self.rig, self.G, self.P = r.rig, r.G, r.P

    def j(self, n):
        return self.rig.index[n]


def steps(r):
    """The worst one-frame local turn (deg) of each foot and knee (calf) over the loop, and the wrists' worst bends."""
    from motion import fit as FIT
    from motion import quat as Q
    rig, G = r.rig, r.G
    out = {}
    for b in ("foot_l", "foot_r", "calf_l", "calf_r"):
        j = rig.index[b]
        L = np.swapaxes(G[:, rig.parent[j]], -1, -2) @ G[:, j]
        a = np.degrees(np.arccos(np.clip((np.trace(np.swapaxes(L[:-1], -1, -2) @ L[1:], axis1=1, axis2=2) - 1) / 2, -1, 1)))
        out[f"step_{b}_deg"] = round(float(a.max()), 1)
    F = _Pose(r)
    for s in "lr":
        fl, de = FIT.wrist_of(F, s)
        out[f"wrist_{s}_flex_deg"] = round(float(np.abs(fl[:r.m]).max()), 1)
        out[f"wrist_{s}_dev_deg"] = round(float(np.abs(de[:r.m]).max()), 1)
        # (the hand's roll on the forearm, from B's rest: a candy-wrapper wrist the flex/dev cap cannot see)
        la, ha = rig.index[f"lowerarm_{s}"], rig.index[f"hand_{s}"]
        D = np.swapaxes(rig.Lr0[ha], -1, -2)[None] @ (np.swapaxes(G[:, la], -1, -2) @ G[:, ha])
        q = Q.from_mat(D)
        tw = np.degrees((2 * np.arctan2(q[:, 1], q[:, 3]) + np.pi) % (2 * np.pi) - np.pi)
        out[f"wrist_{s}_twist_deg"] = round(float(np.abs(tw[:r.m]).max()), 1)
    return out

if __name__ == "__main__":
    main()
