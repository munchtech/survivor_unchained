"""Her arms' roll and wrist brought into a real arm's range, the hand kept: a pose-fix pass on clip JSONs.

The owner (24 Oct, Body 6, on reaver_show overhead and Warden cast_raise): "still twisting like a towel, even the
wrist angle is bizarre". The twist chain (helpers SPEC "twist_chain") spreads the upper arm's roll; this pass takes
the roll out of the motion where the hand allows it. Measured: reaver_show@0.77 overhead, right arm 105 deg external
roll with the wrist 53 deg ulnar; cast_raise@0.10, 74-78 external both arms, the right wrist 42 deg ulnar.

Per frame and side, the hand's world position and turn are kept (the weapon does not move) and the arm between
shoulder and wrist is re-solved over its two free turns: the elbow's swivel about the shoulder-to-wrist line (phi)
and, where the elbow is near straight, the upper arm's roll traded into the forearm (rho: the hinge leaves the
bend's plane by rho; a bent elbow pays for that as an off-hinge error, a straight one barely). Every pose on the
grid is read as anatomy (`angles`): the humerus's roll from her rest (A pose, neutral), the forearm's pronation
(the hand's turn about the forearm with the forearm bone's own roll handed down, as HerJoints's "unroll" does),
the wrist's extension/flexion and ulnar/radial deviation; the cost is each one's excess over LIMITS, squared, plus
staying near the clip's own elbow and a smaller roll. The frames' choices are joined by a Viterbi path (no flips,
small steps) and smoothed, then rebuilt exactly (shoulder, wrist and hand turn as they were).

Only the upper arm, forearm and hand rotations change; the clavicle, fingers, helpers (HerJoints drives them) and
positions stay. A clip already fixed (its meta "arm_roll_fix" at this VERSION) is passed over: idempotent.

    python tools/anim/arm_roll_fix.py --report out/clips/reaver_show.json ...   dry run: before/after per clip
    python tools/anim/arm_roll_fix.py --apply --out DIR clips/*.json             write fixed copies into DIR

build.pack runs it on her clips named in CLIPS (ARM_ROLL_FIX=0: off) after clavhold, into the same stage.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rig import Skeleton, qaxis, qcontinuous, qfrom_basis, qinv, qmul, qrot, two_bone_ik  # noqa: E402

VERSION = 1
# Her clips the pack fixes: name (an entry ending in "*" is a prefix) -> the hand's slack, degrees (0: the hand and
# what it holds never turn; only the elbow's swivel and the roll's trade into the forearm).
CLIPS = {"reaver_show": 30.0, "cast_raise": 30.0}

# A real arm's comfortable range, degrees (beyond: cost). Roll: the humerus about its length from her rest (A pose,
# elbow crease forward, thumb forward: neutral). Pronation from the rest's mid-prone hand.
LIMITS = {"roll_ext": 90.0, "roll_int": 60.0, "pron": 80.0, "sup": 80.0,
          "ext": 45.0, "flex": 55.0, "ulnar": 22.0, "radial": 20.0, "hinge": 2.0}
W_PHI = 1 / 70.0 ** 2       # cost per deg^2 of elbow swivel away from the clip's
W_RHO = 1 / 90.0 ** 2       # per deg^2 of roll traded into the forearm
W_EX = 1 / 6.0 ** 2         # per deg^2 of excess over a limit
W_STEP = 1 / 4.0 ** 2       # per deg^2 of change frame to frame (the path)
PHI = np.arange(-120.0, 120.1, 3.0)
RHO = np.arange(-120.0, 120.1, 6.0)
SMOOTH = 1.5                # frames (Gaussian sigma) on the path before the rebuild
HINGE = {"l": (0.985, 0.0, -0.17), "r": (0.985, 0.0, 0.16)}   # the elbow's axis in the upper arm (as keyed.Rig bends it)
Y = np.array([0.0, 1.0, 0.0])


def _twist_y(d):
    t = np.array([0.0, d[..., 1], 0.0, d[..., 3]]) if np.ndim(d) == 1 else None
    if t is None:
        t = np.zeros(d.shape)
        t[..., 1], t[..., 3] = d[..., 1], d[..., 3]
    n = np.linalg.norm(t, axis=-1, keepdims=True)
    t = np.where(n > 1e-9, t / np.maximum(n, 1e-12), np.array([0, 0, 0, 1.0]))
    t = np.where(t[..., 3:4] < 0, -t, t)
    ang = np.degrees(2 * np.arctan2(t[..., 1], t[..., 3]))
    return qmul(d, qinv(t)), t, ang


def _n(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def _qbetween_v(a, b):
    """Minimal rotation from unit a to unit b, broadcast (b never opposite a here)."""
    c = np.cross(a, b)
    w = 1.0 + np.sum(a * b, axis=-1, keepdims=True)
    return _n(np.concatenate([c, w], axis=-1))


def _qrot_v(a, v):
    shp = np.broadcast_shapes(np.shape(a)[:-1], np.shape(v)[:-1])
    a = np.broadcast_to(a, shp + (4,))
    v = np.broadcast_to(v, shp + (3,))
    u, w = a[..., :3], a[..., 3:4]
    t = 2 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def _qbasis_v(x, y, z):
    """Quaternions with columns x, y, z (orthonormal), broadcast."""
    m = np.stack([x, y, z], axis=-1)
    flat = m.reshape(-1, 3, 3)
    return np.array([qfrom_basis(f[:, 0], f[:, 1], f[:, 2]) for f in flat]).reshape(m.shape[:-2] + (4,))


class Arm:
    """One side's bones and rests."""

    def __init__(self, sk: Skeleton, s):
        I = sk.index
        self.s, self.u, self.l, self.h = s, I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"]
        self.ru, self.rl, self.rh = sk.rest_rot[self.u], sk.rest_rot[self.l], sk.rest_rot[self.h]
        self.L1, self.L2 = np.linalg.norm(sk.rest_pos[self.l]), np.linalg.norm(sk.rest_pos[self.h])
        self.hinge = _n(np.array(HINGE[s]))
        self.mirror = -1.0 if s == "l" else 1.0   # the palm is +X on the left hand, -X on the right

    def angles(self, gu, lloc, gh):
        """(roll ext+, pronation+, extension+, ulnar+, bend) from the upper arm's global turn `gu` relative to its
        parent's (passed as the local times the parent's: callers give gu in the parent's frame), the forearm's local
        and the hand's global turn in the same frame. Broadcast over leading axes."""
        _, _, roll = _twist_y(qmul(qinv(self.ru), gu))
        dl = qmul(qinv(self.rl), lloc)
        sw, tl, _ = _twist_y(dl)
        hrel = qmul(qinv(qmul(gu, qmul(self.rl, sw))), gh)      # the hand in the unrolled forearm
        d = qmul(qinv(self.rh), hrel)
        hs, _, pro = _twist_y(d)
        hs = np.where(hs[..., 3:4] < 0, -hs, hs)
        a = hs[..., :3]
        n = np.linalg.norm(a, axis=-1)
        ang = np.degrees(2 * np.arctan2(n, hs[..., 3]))
        ax = a / np.maximum(n, 1e-12)[..., None]
        flex = ang * ax[..., 2] * self.mirror        # about the thumb axis: + toward the palm
        dev = ang * ax[..., 0]                       # about the palm normal: + toward the thumb (radial)
        bend = np.degrees(np.arccos(np.clip(_qrot_v(lloc, Y)[..., 1], -1, 1)))
        # Signs as anatomy: roll + external (the right arm's + roll turns out, the left's in), pronation +.
        rs = 1.0 if self.s == "r" else -1.0
        return {"roll": roll * rs, "pron": pro * rs, "ext": -flex, "ulnar": -dev, "bend": bend}


def _excess(a, hinge_err):
    L = LIMITS
    e = (np.maximum(a["roll"] - L["roll_ext"], 0) ** 2 + np.maximum(-a["roll"] - L["roll_int"], 0) ** 2
         + np.maximum(a["pron"] - L["pron"], 0) ** 2 + np.maximum(-a["pron"] - L["sup"], 0) ** 2
         + np.maximum(a["ext"] - L["ext"], 0) ** 2 + np.maximum(-a["ext"] - L["flex"], 0) ** 2
         + np.maximum(a["ulnar"] - L["ulnar"], 0) ** 2 + np.maximum(-a["ulnar"] - L["radial"], 0) ** 2
         + np.maximum(hinge_err - L["hinge"], 0) ** 2 * 50)
    return e


def build(arm: Arm, S, W, E, rho, lloc0):
    """The arm through elbow(s) E (broadcast [..., 3]) from shoulder S to wrist W, all in one frame (the
    clavicle's, so the result is local): the upper arm's turn (its hinge on the bend's plane, turned about the
    upper arm by rho, radians, broadcast), the forearm's local (the clip's own forearm roll kept) and the hinge
    error (deg: the forearm out of the hinge's plane)."""
    yu, f, n = _plane(S, E, W)
    cr, sr = np.cos(rho)[..., None], np.sin(rho)[..., None]
    hx = n * cr + np.cross(yu, n) * sr
    # columns (hx, yu, hx x yu) for the bone's (hinge, Y, hinge x Y)
    gu = qmul(_qbasis_v(hx, yu, np.cross(hx, yu)), qinv(qfrom_basis(arm.hinge, Y, np.cross(arm.hinge, Y))))
    fr = _qrot_v(qinv(arm.rl), _qrot_v(qinv(gu), f))
    sw = _qbetween_v(np.broadcast_to(Y, fr.shape), fr)
    _, tl, _ = _twist_y(qmul(qinv(arm.rl), lloc0))
    lloc = qmul(qmul(arm.rl, sw), tl)
    herr = np.degrees(np.arcsin(np.clip(np.abs(np.sum(f * hx, axis=-1)), 0, 1)))
    return gu, lloc, herr


def _plane(S, E, W):
    """The upper arm's line, the forearm's and the bend's plane normal (a near-straight arm: a fixed one)."""
    yu = _n(E - S)
    f = _n(W - E)
    n = np.cross(yu, f)
    nn = np.linalg.norm(n, axis=-1, keepdims=True)
    n = np.where(nn > 1e-4, n / np.maximum(nn, 1e-12), _n(np.cross(yu, [0.0, 0.0, 1.0])))
    return yu, f, n


def candidates(arm: Arm, S, W, E0, lloc0, phi, rho, gu0):
    """Every (phi, rho) pose for one frame (degree grids -> [P, R, ...]): the elbow swung by phi about the
    shoulder-to-wrist line, the hinge turned by rho from where the clip's own upper arm `gu0` has it about the
    bend's plane (so (0, 0) is the clip's pose). Returns (gu, lloc, hinge error)."""
    a = _n(W - S)
    yu0, _, n0 = _plane(S, E0, W)
    h0 = qrot(gu0, arm.hinge)
    rho0 = math.atan2(float(np.dot(np.cross(n0, h0), yu0)), float(np.dot(n0, h0)))
    P, R = np.meshgrid(np.radians(phi), np.radians(rho), indexing="ij")
    R = R + rho0
    e0 = E0 - S
    c, s = np.cos(P)[..., None], np.sin(P)[..., None]
    e = e0 * c + np.cross(a, e0) * s + a * np.dot(a, e0) * (1 - c)
    return build(arm, S, W, S + e, R, lloc0)


def _frame(sk, grot, gpos, t, arm):
    """One frame's shoulder, elbow, wrist and hand turn in the clavicle's frame, and the clavicle's turn."""
    pu = sk.parent[arm.u]
    gp = grot[t, pu]
    S, E, W = (qrot(qinv(gp), gpos[t, j] - gpos[t, pu]) for j in (arm.u, arm.l, arm.h))
    return gp, S, E, W, qmul(qinv(gp), grot[t, arm.h])


def _wrist_fix(arm, gu, lloc, gh, slack):
    """The hand's own turn (cz about its thumb axis, cx about its palm's normal, degrees, local and
    post-multiplied: the hand and what it holds turn about the wrist) that brings extension and deviation inside
    LIMITS, at most `slack` degrees."""
    L = LIMITS

    def wa(c):
        a = arm.angles(gu, lloc, qmul(gh, qmul(qaxis([0, 0, 1.0], c[0]), qaxis([1.0, 0, 0], c[1]))))
        return np.array([float(a["ext"]), float(a["ulnar"])])

    c = np.zeros(2)
    for _ in range(6):
        v = wa(c)
        tgt = np.array([np.clip(v[0], -L["flex"], L["ext"]), np.clip(v[1], -L["radial"], L["ulnar"])])
        r = tgt - v
        if np.max(np.abs(r)) < 0.2:
            break
        J = np.stack([wa(c + d) - v for d in (np.array([1.0, 0]), np.array([0, 1.0]))], axis=1)
        try:
            c = c + np.linalg.solve(J, r)
        except np.linalg.LinAlgError:
            break
    m = float(np.linalg.norm(c))
    if m > slack:
        c *= slack / m
    return c


JOIN = 0.16     # m: hands this close at a frame hold one thing (a two-handed grip): the other hand follows


def fix_rot(sk: Skeleton, rot, pos, sides="lr", report=None, slack=0.0):
    """rot [T, J, 4] local: a new rot with the arms re-solved (see the module doc). slack: degrees the hand (and
    what it holds) may turn to bring the wrist in range. report: dict filled per side, rows before/after."""
    rot = np.array(rot, float)
    grot, gpos = sk.fk(rot, pos)
    T = rot.shape[0]
    out = rot.copy()
    arms = {s: Arm(sk, s) for s in sides}
    Pm, Rm = np.meshgrid(PHI, RHO, indexing="ij")
    Pg, Rg = Pm.ravel(), Rm.ravel()
    step = W_STEP * ((Pg[:, None] - Pg[None, :]) ** 2 + (Rg[:, None] - Rg[None, :]) ** 2)
    path_of = {}
    for s, arm in arms.items():
        costs = []
        for t in range(T):
            gp, S, E, W, gh = _frame(sk, grot, gpos, t, arm)
            gu, lloc, herr = candidates(arm, S, W, E, rot[t, arm.l], PHI, RHO, rot[t, arm.u])
            a = arm.angles(gu, lloc, gh)
            # never a bigger roll than the clip's own where that is already past the limit (the towel is the
            # roll: the wrist is not bought with it)
            r0 = abs(float(arm.angles(rot[t, arm.u], rot[t, arm.l], gh)["roll"]))
            worse = np.maximum(np.abs(a["roll"]) - max(r0, LIMITS["roll_int"]), 0)
            # the clip's own elbow out of the hinge's plane (her rest's carrying angle) is not an error to fix
            f0 = (W - E) / np.linalg.norm(W - E)
            h0 = float(np.degrees(np.arcsin(min(1.0, abs(float(np.dot(f0, qrot(rot[t, arm.u], arm.hinge))))))))
            c = W_EX * (_excess(a, np.maximum(herr - h0, 0)) + 4 * worse ** 2) + W_PHI * Pm ** 2 + W_RHO * Rm ** 2
            costs.append(c.ravel())
        acc, back = costs[0].copy(), []
        for t in range(1, T):
            m = acc[:, None] + step
            b = np.argmin(m, axis=0)
            back.append(b)
            acc = m[b, np.arange(len(b))] + costs[t]
        path = [int(np.argmin(acc))]
        for b in reversed(back):
            path.append(int(b[path[-1]]))
        path = path[::-1]
        ph, rh = Pg[path].astype(float), Rg[path].astype(float)
        if T > 2 and SMOOTH > 0:
            ph, rh = _gauss(ph, SMOOTH), _gauss(rh, SMOOTH)
        path_of[s] = (ph, rh)
        for t in range(T):
            if abs(ph[t]) < 0.5 and abs(rh[t]) < 0.5:
                continue
            gp, S, E, W, gh = _frame(sk, grot, gpos, t, arm)
            gu, lloc, _ = candidates(arm, S, W, E, rot[t, arm.l], np.array([ph[t]]), np.array([rh[t]]), rot[t, arm.u])
            out[t, arm.u], out[t, arm.l] = gu[0, 0], lloc[0, 0]
            out[t, arm.h] = qmul(qinv(qmul(gu[0, 0], lloc[0, 0])), gh)
    # The wrist: the hand's own turn, where the swivel could not bring it in range.
    cw = {s: np.zeros((T, 2)) for s in arms}
    if slack > 0:
        g2, p2 = sk.fk(out, pos)
        for s, arm in arms.items():
            for t in range(T):
                _, _, _, _, gh = _frame(sk, g2, p2, t, arm)
                cw[s][t] = _wrist_fix(arm, out[t, arm.u], out[t, arm.l], gh, slack)
            if T > 2:
                cw[s] = np.stack([_gauss(cw[s][:, k], 2.0) for k in range(2)], axis=1)
        lead = {}
        if len(arms) == 2:
            for t in range(T):
                if np.linalg.norm(p2[t, arms["l"].h] - p2[t, arms["r"].h]) < JOIN:
                    lead[t] = "l" if np.linalg.norm(cw["l"][t]) > np.linalg.norm(cw["r"][t]) else "r"
        new = out.copy()
        for t in range(T):
            for s, arm in arms.items():
                if t in lead and lead[t] != s:
                    continue
                cz, cx = cw[s][t]
                if abs(cz) < 0.05 and abs(cx) < 0.05:
                    continue
                C = qmul(qaxis([0, 0, 1.0], cz), qaxis([1.0, 0, 0], cx))
                new[t, arm.h] = qmul(out[t, arm.h], C)
                if t in lead:
                    # the other hand carried round this wrist, its arm re-reached (its elbow toward where it was)
                    o = arms["r" if s == "l" else "l"]
                    gH = g2[t, arm.h]
                    D = qmul(qmul(gH, C), qinv(gH))          # the turn, in skeleton space
                    Wo = p2[t, arm.h] + qrot(D, p2[t, o.h] - p2[t, arm.h])
                    gho = qmul(D, g2[t, o.h])
                    pu = sk.parent[o.u]
                    gp = g2[t, pu]
                    S, E, W0 = (qrot(qinv(gp), p2[t, j] - p2[t, pu]) for j in (o.u, o.l, o.h))
                    Wn = qrot(qinv(gp), Wo - p2[t, pu])
                    En, Wr = two_bone_ik(S, E, W0, Wn, E + (E - (S + W0) / 2) * 0.5)
                    yu0, _, n0 = _plane(S, E, W0)
                    h0 = qrot(out[t, o.u], o.hinge)
                    rho0 = math.atan2(float(np.dot(np.cross(n0, h0), yu0)), float(np.dot(n0, h0)))
                    gu, lloc, _ = build(o, S, Wr, En, np.array(rho0), out[t, o.l])
                    new[t, o.u], new[t, o.l] = gu, lloc
                    new[t, o.h] = qmul(qinv(qmul(gu, lloc)), qmul(qinv(gp), gho))
        out = new
    if report is not None:
        g2, p2 = sk.fk(out, pos)
        for s, arm in arms.items():
            rows_b, rows_a = [], []
            for t in range(T):
                _, _, _, _, gh0 = _frame(sk, grot, gpos, t, arm)
                _, _, _, _, gh1 = _frame(sk, g2, p2, t, arm)
                rows_b.append({k: float(v) for k, v in arm.angles(rot[t, arm.u], rot[t, arm.l], gh0).items()})
                rows_a.append({**{k: float(v) for k, v in arm.angles(out[t, arm.u], out[t, arm.l], gh1).items()},
                               "phi": float(path_of[s][0][t]), "rho": float(path_of[s][1][t]),
                               "hand": float(np.linalg.norm(cw[s][t])),
                               "wrist_moved": float(np.linalg.norm(p2[t, arm.h] - gpos[t, arm.h]))})
            report[s] = {"before": rows_b, "after": rows_a}
    for j in range(out.shape[1]):
        out[:, j] = qcontinuous(out[:, j])
    return out


def _gauss(x, sig):
    r = int(3 * sig + 1)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
    k /= k.sum()
    xp = np.pad(x, r, mode="edge")
    return np.convolve(xp, k, mode="valid")


def summary(rep):
    """Per side, the max |roll| ext/int, pron, ext, ulnar before and after."""
    out = {}
    for s, r in rep.items():
        for key in ("before", "after"):
            rows = r[key]
            if not rows:
                continue
            out.setdefault(s, {})[key] = {k: (float(max(x[k] for x in rows)), float(min(x[k] for x in rows)))
                                          for k in ("roll", "pron", "ext", "ulnar")}
        out[s]["hand"] = max(x["hand"] for x in r["after"])
        out[s]["moved"] = max(x["wrist_moved"] for x in r["after"])
    return out


def load_json(sk, d):
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = sk.index.get(t["bone"])
        if j is not None:
            (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    return rot, pos


def fix_json(sk: Skeleton, d, report=None, slack=0.0):
    """A clip JSON with the fix (a new dict); unchanged (same dict) if already fixed at this VERSION."""
    if d.get("meta", {}).get("arm_roll_fix") == VERSION:
        return d
    rot, pos = load_json(sk, d)
    new = fix_rot(sk, rot, pos, report=report, slack=slack)
    out = dict(d)
    out["meta"] = {**d.get("meta", {}), "arm_roll_fix": VERSION}
    tracks = [dict(t) for t in d["tracks"]]
    have = {t["bone"]: t for t in tracks if t["type"] == "rot"}
    for s in "lr":
        for b in (f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}"):
            j = sk.index[b]
            if np.max(np.abs(new[:, j] - rot[:, j])) < 1e-7:
                continue
            keys = np.round(new[:, j], 6).tolist()
            if b in have:
                have[b]["keys"] = keys
            else:
                t = {"bone": b, "type": "rot", "keys": keys}
                tracks.insert(0, t)
                have[b] = t
    out["tracks"] = tracks
    return out


def wanted(name, clips=None):
    """The hand's slack for clip `name` if the pass fixes it, else None."""
    clips = CLIPS if clips is None else clips
    for c, v in clips.items():
        if (name.startswith(c[:-1]) if c.endswith("*") else name == c):
            return v
    return None


def on():
    return os.environ.get("ARM_ROLL_FIX", "1") != "0"


def stage(dst: Path, sk: Skeleton, clips=None, log=print):
    """Fix the wanted clips' JSONs in a stage folder (clavhold's) in place."""
    done = []
    for f in sorted(dst.glob("*.json")):
        d = json.loads(f.read_text())
        sl = wanted(d["name"], clips)
        if sl is None:
            continue
        rep = {}
        n = fix_json(sk, d, rep, sl)
        if n is not d:
            f.write_text(json.dumps(n, separators=(",", ":")))
            sm = summary(rep)
            done.append(d["name"] + " " + " ".join(f"{s}:roll {v['before']['roll'][0]:.0f}->{v['after']['roll'][0]:.0f}"
                                                     for s, v in sm.items()))
    log(f"  arm roll fix: {len(done)} clips: {'; '.join(done)}")


def _fmt(v):
    return (f"roll {v['roll'][1]:5.0f}..{v['roll'][0]:4.0f}  pron {v['pron'][1]:4.0f}..{v['pron'][0]:4.0f}  "
            f"ext {v['ext'][1]:4.0f}..{v['ext'][0]:4.0f}  ulnar {v['ulnar'][1]:4.0f}..{v['ulnar'][0]:4.0f}")


def main(argv):
    sk = Skeleton.load()
    apply = "--apply" in argv
    out_dir = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
    opt = {k: argv[argv.index(k) + 1] for k in ("--out", "--slack", "--frames") if k in argv}
    files = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in opt)]
    frames = [int(x) for x in opt["--frames"].split(",")] if "--frames" in opt else []
    for f in files:
        d = json.loads(Path(f).read_text())
        sl = float(opt["--slack"]) if "--slack" in opt else (wanted(d["name"]) or 0.0)
        rep = {}
        n = fix_json(sk, dict(d, meta={k: v for k, v in d.get("meta", {}).items() if k != "arm_roll_fix"}), rep, sl)
        for s, v in summary(rep).items():
            print(f"{d['name']:24s} {s} before {_fmt(v['before'])}")
            print(f"{'':24s} {s} after  {_fmt(v['after'])}  hand turned <= {v['hand']:.0f} deg, wrist moved "
                  f"<= {v['moved'] * 1000:.0f} mm")
        for t in frames:
            for s, r in rep.items():
                b, a = r["before"][t], r["after"][t]
                print(f"  f{t} {s} " + " ".join(f"{k} {b[k]:4.0f}>{a[k]:4.0f}" for k in ("roll", "pron", "ext", "ulnar"))
                      + f"  phi {a['phi']:4.0f} rho {a['rho']:4.0f} hand {a['hand']:3.0f}")
        if apply and out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / Path(f).name).write_text(json.dumps(n, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1:])
