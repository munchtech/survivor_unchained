"""Her clavicles held down while the arm is low: a pass at pack time (build.pack).

The owner (Body 2): "her shoulders were too high". Every captured idle and show
lifted the shoulder joint through its clavicle keys while the arm hung below
level (retarget.py aims the clavicle at the capture's own shoulder joint, so the
mocap actor's collar shrug comes through; keyed clips add clav_l/r raises):
+0.7-1.4 cm in idle_reaver_town, 1.3-2 cm in the warden and stalker town idles,
3.5-5.6 cm in the arcanist town idle. The game's ClavicleLift (helpers.shrug)
only lifts above 90 deg, so nothing took it back.

The rule, per frame and side, on the clip's clavicle elevation above its rest
in the chest's frame (clavicle head to shoulder joint against spine_03's down),
weighted by the arm: full while the upper arm is below CLAV_HOLD_FROM deg from
hanging (the game's arm angle, against the pelvis-to-neck_01 line), faded out
by CLAV_HOLD_TO, so overhead poses keep the clip's lift and ClavicleLift's job.
  - A loop (idles, cycles): the clip's slow lift (a 1 s smoothed baseline) is
    held to at most CLAV_HOLD_CAP - a, where a is the clip's own small
    oscillation about it (its 95th percentile, at most CLAV_HOLD_AMP deg), and
    that oscillation (breathing, sway) is kept up to a: a low arm's clavicle
    never rises more than CLAV_HOLD_CAP deg above rest.
  - A one-shot (shows, attacks, reactions, cinematics): only its slow lift
    (the same baseline) comes down to CLAV_HOLD_CAP; its quicker gestures on
    top (a flinch's shrug) keep their whole shape, so acting survives and the
    shoulder meets the held idles it blends from. No frame of a one-shot is taken below CAP (a leap's
    take-off is not lowered by its landing's carriage).
Nothing is ever raised; the drop is eased over DROP_S so nothing pops. Only elevation turns: the
clavicle rotates about (its own direction x down), so protraction and
retraction stay as keyed. The upper arm's global rotation is kept, so the arm
moves down whole with the shoulder joint (the hand by the joint's own shift),
unless the hand is on her body (near the trunk line or the head: a hand on the
hip, a flask at her teeth): then a two-bone solve keeps the wrist where the clip
put it, the hand's global turn and the arm's bend plane kept.

Off with CLAV_HOLD=0 (the clips are then packed as written).
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np

from rig import Skeleton, qaxis, qbetween, qcontinuous, qinv, qmul, qnorm, qrot

CAP = float(os.environ.get("CLAV_HOLD_CAP", "1.0"))        # deg above rest, at most, while the arm is low
AMP = float(os.environ.get("CLAV_HOLD_AMP", "1.0"))        # the clip's own oscillation kept, up to this
FROM = float(os.environ.get("CLAV_HOLD_FROM", "80"))       # arm angle from hanging: full hold below
TO = float(os.environ.get("CLAV_HOLD_TO", "95"))           # no hold from here
SMOOTH_S = 1.0                                             # the baseline's smoothing (Gaussian sigma, s)
DROP_S = 0.1                                               # the drop's own easing (Gaussian sigma, s)
# A hand on her body (a hand on the hip, a flask at her teeth) stays where the clip put it (two-bone IK, the
# hand's turn kept); a free hand moves down with the shoulder. Wrist to the pelvis-neck_01 line (m), to Head (m):
PIN_TRUNK = (0.23, 0.28)                                   # pinned under the first, free past the second
PIN_HEAD = (0.24, 0.32)


def _seg(p, a, b):
    ab = b - a
    t = np.clip(np.einsum("ti,ti->t", p - a, ab) / np.einsum("ti,ti->t", ab, ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=-1)


def _near(d, lim):
    x = np.clip((d - lim[0]) / (lim[1] - lim[0]), 0, 1)
    return 1 - x * x * (3 - 2 * x)


def on():
    return os.environ.get("CLAV_HOLD", "1") != "0"


def _smooth(x, sigma, loop):
    if sigma < 0.5 or len(x) < 3:
        return x.copy()
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    if loop:    # (a loop's last frame is its first again)
        body = x[:-1]
        n = len(body)
        idx = np.arange(-r, n + r) % n
        out = np.convolve(body[idx], k, mode="valid")
        return np.append(out, out[0])
    pad = np.concatenate([np.full(r, x[0]), x, np.full(r, x[-1])])
    return np.convolve(pad, k, mode="valid")


def _elev(v, down):
    return np.degrees(np.arcsin(np.clip(-np.einsum("...i,...i", v, down) / np.linalg.norm(v, axis=-1), -1, 1)))


def _down(gpos, I):
    d = gpos[..., I["pelvis"], :] - gpos[..., I["neck_01"], :]
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def hold_rot(sk: Skeleton, rot, pos, fps, loop, report=None):
    """rot [T, J, 4] local rotations (changed copy returned), pos [T, J, 3]."""
    I = sk.index
    if "clavicle_l" not in I or "pelvis" not in I:
        return rot
    rot = rot.copy()
    g0, p0 = sk.fk(sk.rest_rot[None], sk.rest_pos[None])
    d0 = _down(p0, I)
    grot, gpos = sk.fk(rot, pos)
    down = _down(gpos, I)                                   # the game's arm angle (ClavicleLift) reads this
    ch = I["spine_03"]                                      # the clavicle's lift is read in the chest's frame
    dl = qrot(qinv(g0[0, ch]), d0[0])
    cdown = qrot(grot[:, ch], np.broadcast_to(dl, (rot.shape[0], 3)))
    T = rot.shape[0]
    for s in "lr":
        c, u, lo = I[f"clavicle_{s}"], I[f"upperarm_{s}"], I[f"lowerarm_{s}"]
        rest = _elev(p0[:, u] - p0[:, c], d0)[0]
        v = gpos[:, u] - gpos[:, c]
        e = _elev(v, cdown) - rest
        arm = gpos[:, lo] - gpos[:, u]
        A = np.degrees(np.arccos(np.clip(np.einsum("ti,ti->t", arm / np.linalg.norm(arm, axis=-1, keepdims=True), down), -1, 1)))
        x = np.clip((A - FROM) / (TO - FROM), 0, 1)
        w = 1 - x * x * (3 - 2 * x)
        b = _smooth(e, SMOOTH_S * fps, loop)            # the slow lift (carriage); e - b: breath, sway, gestures
        osc = e - b
        if loop:    # an idle or a cycle: its slow lift held, its own small oscillation kept up to AMP
            a = float(np.clip(np.percentile(osc, 95), 0, AMP)) if T > 2 else 0.0
            target = np.minimum(b, CAP - a) + np.minimum(osc, a)
        else:       # a one-shot: only its slow lift comes down, its quick gestures (a flinch's shrug) kept whole
            target = np.minimum(b, CAP) + osc
        drop = w * np.maximum(0.0, e - target)          # deg, >= 0
        # (Eased over DROP_S: an arm hovering in the fade band with a big lift, a leap's landing, never pops.)
        drop = np.maximum(0.0, _smooth(drop, DROP_S * fps, loop))
        if not loop:    # (a one-shot's frames under its carriage, a leap's take-off under its landing's, never go below CAP)
            drop = np.minimum(drop, np.maximum(0.0, e - CAP))
        if report is not None:
            report[s] = dict(rise=float(np.mean(e)), max_rise=float(np.max(e)), drop=float(np.max(drop)),
                             mean_drop=float(np.mean(drop)), A=float(np.mean(A)))
        if np.max(drop) < 1e-4:
            continue
        h = I[f"hand_{s}"]
        H = gpos[:, h]
        pin = np.maximum(_near(_seg(H, gpos[:, I["pelvis"]], gpos[:, I["neck_01"]]), PIN_TRUNK),
                         _near(np.linalg.norm(H - gpos[:, I["Head"]], axis=-1), PIN_HEAD))
        pin = np.clip(_smooth(pin, DROP_S * fps, loop), 0, 1)
        if report is not None:
            report[s]["pin"] = float(np.max(pin))
        p = sk.parent[c]
        for f in np.nonzero(drop > 1e-4)[0]:
            n = np.cross(v[f], cdown[f])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            q = qaxis(n / nn, drop[f])                              # turned toward down: elevation only
            Cg = qnorm(qmul(q, grot[f, c]))
            Ug, Lg, Hg = grot[f, u], grot[f, lo], grot[f, h]
            rot[f, c] = qnorm(qmul(qinv(grot[f, p]), Cg))
            Pc, S, E = gpos[f, c], gpos[f, u], gpos[f, lo]
            S2 = Pc + qrot(q, S - Pc)
            if pin[f] > 1e-3:   # the wrist to its clip place (pinned) or down with the shoulder (free), bend plane kept
                Ht = H[f] + (1 - pin[f]) * (S2 - S)
                L1, L2 = np.linalg.norm(E - S), np.linalg.norm(H[f] - E)
                Dv = Ht - S2
                D = min(np.linalg.norm(Dv), 0.9995 * (L1 + L2))
                ax = Dv / np.linalg.norm(Dv)
                pole = (E - S) - ((E - S) @ ax) * ax
                if np.linalg.norm(pole) > 1e-6:
                    pole = pole / np.linalg.norm(pole)
                    ca = float(np.clip((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1))
                    E2 = S2 + L1 * (ca * ax + np.sqrt(1 - ca * ca) * pole)
                    Ug = qnorm(qmul(qbetween(E - S, E2 - S2), Ug))
                    Lg = qnorm(qmul(qbetween(H[f] - E, S2 + D * ax - E2), Lg))
                    rot[f, lo] = qnorm(qmul(qinv(Ug), Lg))
                    rot[f, h] = qnorm(qmul(qinv(Lg), Hg))          # the hand's global turn kept
            rot[f, u] = qnorm(qmul(qinv(Cg), Ug))                  # (free: the arm's global turn kept)
    return rot


def hold_json(sk: Skeleton, d, report=None):
    """A clip JSON (rig.Clip.to_json's form) with the hold applied (a new dict)."""
    I = sk.index
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = I.get(t["bone"])
        if j is None:
            continue
        (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    new = hold_rot(sk, rot, pos, float(d["fps"]), bool(d.get("loop", False)), report)
    out = dict(d)
    tracks = [dict(t) for t in d["tracks"]]
    have = {t["bone"]: t for t in tracks if t["type"] == "rot"}
    for s in "lr":
        for b in (f"clavicle_{s}", f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}"):
            j = I[b]
            if np.max(np.abs(new[:, j] - rot[:, j])) < 1e-7:
                continue
            keys = np.round(qcontinuous(new[:, j]), 6).tolist()
            if b in have:
                have[b]["keys"] = keys
            else:
                t = {"bone": b, "type": "rot", "keys": keys}
                tracks.insert(0, t)
                have[b] = t
    out["tracks"] = tracks
    return out


def stage(src: Path, dst: Path, sk: Skeleton, log=print):
    """Every clip JSON in src, held, into dst (cleared of JSONs first). Returns dst."""
    if dst.resolve() == src.resolve():
        raise ValueError("clavhold.stage: dst must not be the clips folder")
    dst.mkdir(parents=True, exist_ok=True)
    for f in dst.glob("*.json"):
        f.unlink()
    moved = []
    for f in sorted(src.glob("*.json")):
        d = json.loads(f.read_text())
        rep = {}
        h = hold_json(sk, d, rep)
        (dst / f.name).write_text(json.dumps(h, separators=(",", ":")))
        m = max(rep[s]["drop"] for s in rep) if rep else 0.0
        if m > 0.05:
            moved.append(f"{d['name']} {m:.1f}")
    log(f"  clavicle hold: {len(moved)} clips lowered (max deg): {', '.join(moved)}")
    return dst


def stage_copy(src: Path, dst: Path):
    """Every clip JSON in src copied unchanged into dst (cleared of JSONs first), for later passes. Returns dst."""
    if dst.resolve() == src.resolve():
        raise ValueError("clavhold.stage_copy: dst must not be the clips folder")
    dst.mkdir(parents=True, exist_ok=True)
    for f in dst.glob("*.json"):
        f.unlink()
    for f in sorted(src.glob("*.json")):
        shutil.copyfile(f, dst / f.name)
    return dst
