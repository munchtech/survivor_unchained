"""The blade's contact measure on a built P4 clip (the rule every cut is built to): (1) a contact mark sits ON the
blade's crossing of the target, measured; (2) a blend into a cut never carries a faster sweep than the cut itself.

    python tools/anim/p4_contact.py <clip> [...] [--from <clip>[:frame]] [--blend <seconds>]
        reads godot/art/people/body_p1/p4/<clip>.json and tools/anim/p4/specs/<clip>.json; no rebuild, seconds.

Frames, signs, units. Times are clip seconds; a line gives them as the clip's own frames (f = t * fps) and as frames at
60 fps (f60 = t * 60). The node frame: +Y up, +Z her heading, +X her LEFT. Per contact mark (spec beats.contact):
  tip_peak   the sub-frame time of the sword tip's peak speed in the swing window (the mark - 0.25 s .. + 0.25 s, or
             beats.target.window_s [before, after]). The tip's speed is its chord between two keys times fps, stamped
             at the mid-key; the peak is the vertex of the parabola through the largest sample and its two neighbours.
  cross      the instant the blade's OUTER HALF (grip + 0.5 .. 1.0 of the blade's length) passes NEAREST the target
             point T, inside the swing (the run of keys round the peak whose tip speed is >= 25% of the peak), on the
             pose the game plays (linear tracks, sampled at 480 Hz; the vertex of the parabola through the nearest
             sample's squared distance and its neighbours). One definition for every cut: a flat sweep passes over T
             when the blade's line in plan crosses it (its bearing passes T's), an overhead chop when its outer half
             comes down through T's height, a diagonal cut in between. A pass that is nearest at the swing's edge is
             no crossing (NO-CROSS: the blade never passed the target there, or the mark is no blade contact).
  T          beats.target {bearing_deg (+ toward her LEFT, 0 = her heading), height_cm (110: her chest), dist_cm (110),
             from ("node": the node's origin, default; "pelvis": her pelvis's ground point at the mark),
             window_s [before, after]}; every key optional.
  contact_minus_cross_f60 / contact_minus_peak_f60   (mark - cross) * 60, (mark - tip_peak) * 60: NEGATIVE = the mark is
             EARLY (ahead of the blade). MISS when |contact - cross| > 0.5 frame at 60 fps.
  pass_cm, along   how near the outer half passes T and where on the blade (0.5 = mid, 1 = the tip): a far pass says the
             target is badly placed for this cut, not that the mark is wrong.
The blend rule: the game's cross-fade (linear weight over beats.blend_in seconds, 0.1 when unset; locals slerped, the
from-clip frozen at its frame) from the idle's pose (--from, else beats.blend_from {clip, frame}, else fit.start, else
fit.end) into the clip's start; the tip's peak speed over it (its chord over one 60 fps frame, x 60) against the first
cut's own peak: blend_peak_ratio, MISS at >= 1.0.
"""
from __future__ import annotations

import json
import sys

import numpy as np

TARGET = {"bearing_deg": 0.0, "height_cm": 110.0, "dist_cm": 110.0, "from": "node", "window_s": [0.25, 0.25]}
MISS_F60 = 0.5          # |contact - cross| over this, frames at 60 fps, is a MISS
SWING_FRAC = 0.25       # the swing: the keys round the peak at this share of the peak's tip speed or more
FINE_HZ = 480.0         # the game's linear tracks sampled at this rate for the crossing and the blend
BLEND_S = 0.1           # the cross-fade when beats.blend_in is unset


def _slerp(a, b, t):
    """Rows of quaternions a -> b at t (a scalar or one per row), the short way."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = np.broadcast_to(np.asarray(t, float).reshape(-1, *([1] * (a.ndim - 1))), a.shape[:-1] + (1,))
    d = np.sum(a * b, -1, keepdims=True)
    b = np.where(d < 0, -b, b)
    d = np.clip(np.abs(d), 0, 1)
    th = np.arccos(d)
    s = np.sin(th)
    lin = s < 1e-6
    s = np.where(lin, 1.0, s)
    q = np.where(lin, (1 - t) * a + t * b, (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / s)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def locals_at(clip, rig, times):
    """The clip's locals at clip seconds (N,), as the game's linear tracks play them: (q (N,J,4), p (N,J,3)); the bones
    the clip does not key at their rest local."""
    from motion import quat as Q
    times = np.atleast_1d(np.asarray(times, float))
    n = clip["frames"]
    x = np.clip(times * clip["fps"], 0, n - 1)
    a = np.minimum(np.floor(x).astype(int), max(0, n - 2))
    u = x - a
    b = np.minimum(a + 1, n - 1)
    q = np.repeat(Q.from_mat(rig.Lr0)[None], len(times), 0)
    p = np.repeat(rig.rest_locals(1)[1], len(times), 0)
    for bone, qs in clip["rot"].items():
        qs = np.array(qs, float)
        q[:, rig.index[bone]] = _slerp(qs[a], qs[b], u)
    for bone, ps in clip["pos"].items():
        ps = np.array(ps, float)
        p[:, rig.index[bone]] = (1 - u)[:, None] * ps[a] + u[:, None] * ps[b]
    return q, p


def blade_of(p4, rig, q, p):
    """The sword as the game seats it (p4.pieces(): hand_r, the fist pocket) on locals (q, p): {grip, dir, tip, pelvis:
    (N,3) world, len: the blade's length, m}."""
    from motion import quat as Q
    G, P = rig.fk(Q.to_mat(q), p)
    pc = p4.pieces()["blade"]
    h = rig.index["hand_r"]
    d = G[:, h] @ np.array(pc["dir"])
    grip = P[:, h] + G[:, h] @ np.array(pc["at"])
    return {"grip": grip, "dir": d, "tip": grip + d * pc["tip"], "len": float(pc["tip"]), "pelvis": P[:, rig.index["pelvis"]]}


def _vertex(y0, y1, y2):
    """The offset (-0.5 .. 0.5 of a step) of the parabola's vertex through three even samples round the middle one."""
    den = y0 - 2 * y1 + y2
    return 0.0 if abs(den) < 1e-18 else float(np.clip(0.5 * (y0 - y2) / den, -0.5, 0.5))


def tip_speed(p4, rig, clip):
    """The tip's speed between the clip's keys: (mid-key seconds (F-1,), m/s (F-1,))."""
    n, fps = clip["frames"], clip["fps"]
    tip = blade_of(p4, rig, *locals_at(clip, rig, np.arange(n) / fps))["tip"]
    return (np.arange(n - 1) + 0.5) / fps, np.linalg.norm(np.diff(tip, axis=0), axis=1) * fps


def target_of(p4, rig, clip, beats, mark):
    """(T (3,) in the node frame, the target block with its defaults filled) for one contact mark."""
    tg = {**TARGET, **(beats.get("target") or {})}
    b, d = np.radians(tg["bearing_deg"]), tg["dist_cm"] / 100
    T = np.array([d * np.sin(b), tg["height_cm"] / 100, d * np.cos(b)])
    if tg["from"] == "pelvis":
        pv = blade_of(p4, rig, *locals_at(clip, rig, [mark]))["pelvis"][0]
        T[[0, 2]] += pv[[0, 2]]
    return T, tg


def _pass(bl, T):
    """The blade's outer half against T on every sample: (squared distance, where along the blade 0.5 .. 1)."""
    s = np.clip(np.sum((T - bl["grip"]) * bl["dir"], 1), 0.5 * bl["len"], bl["len"])
    return np.sum((bl["grip"] + s[:, None] * bl["dir"] - T) ** 2, 1), s / bl["len"]


def mark_of(p4, rig, clip, beats, mark, speed=None):
    """One contact mark's numbers (the module's docstring): {contact, tip_peak, tip_peak_mps, cross (None: no crossing),
    pass_cm, along, contact_minus_cross_f60, contact_minus_peak_f60, miss, swing: [a, b], target}; times in seconds."""
    fps, end = clip["fps"], (clip["frames"] - 1) / clip["fps"]
    tm, sp = speed if speed is not None else tip_speed(p4, rig, clip)
    T, tg = target_of(p4, rig, clip, beats, mark)
    out = {"contact": float(mark), "tip_peak": None, "tip_peak_mps": None, "cross": None, "pass_cm": None, "along": None,
           "contact_minus_cross_f60": None, "contact_minus_peak_f60": None, "miss": True, "swing": None, "target": tg}
    w = np.flatnonzero((tm >= mark - tg["window_s"][0] - 1e-9) & (tm <= mark + tg["window_s"][1] + 1e-9))
    if not len(w) or sp[w].max() < 1e-6:
        return out
    i = int(w[np.argmax(sp[w])])
    off = _vertex(sp[i - 1], sp[i], sp[i + 1]) if 0 < i < len(sp) - 1 else 0.0
    out["tip_peak"] = float(tm[i] + off / fps)
    out["tip_peak_mps"] = float(sp[i] - 0.25 * (sp[i - 1] - sp[i + 1]) * off) if 0 < i < len(sp) - 1 else float(sp[i])
    out["contact_minus_peak_f60"] = float((mark - out["tip_peak"]) * 60)
    lo = hi = i
    while lo - 1 >= w[0] and sp[lo - 1] >= SWING_FRAC * sp[i]:
        lo -= 1
    while hi + 1 <= w[-1] and sp[hi + 1] >= SWING_FRAC * sp[i]:
        hi += 1
    a, b = max(0.0, tm[lo] - 1.5 / fps), min(end, tm[hi] + 1.5 / fps)      # (the run's keys and one more each side)
    out["swing"] = [float(a), float(b)]
    ts = np.linspace(a, b, max(3, int(round((b - a) * FINE_HZ)) + 1))
    d2, al = _pass(blade_of(p4, rig, *locals_at(clip, rig, ts)), T)
    k = int(np.argmin(d2))
    if 0 < k < len(ts) - 1:
        o = _vertex(d2[k - 1], d2[k], d2[k + 1])
        out["cross"] = float(ts[k] + o * (ts[1] - ts[0]))
        out["pass_cm"] = float(100 * np.sqrt(max(0.0, d2[k] - 0.25 * (d2[k - 1] - d2[k + 1]) * o)))
        out["along"] = float(al[k])
        out["contact_minus_cross_f60"] = float((mark - out["cross"]) * 60)
        out["miss"] = bool(abs(out["contact_minus_cross_f60"]) > MISS_F60)
    return out


def blend_in(p4, rig, clip, frm, frame=0, seconds=BLEND_S, cut_peak_mps=None):
    """The cross-fade from the built clip `frm` (a clip dict) frozen at `frame` into `clip`'s start over `seconds`:
    {seconds, peak_mps, peak_at (seconds: the middle of the fastest 60 fps frame), ratio (peak / cut_peak_mps), miss}."""
    step = 1.0 / FINE_HZ
    ts = np.arange(0.0, seconds + 1 / 60 + step / 2, step)       # (one 60 fps frame past the fade's end: its last chord)
    q1, p1 = locals_at(clip, rig, ts)
    q0, p0 = locals_at(frm, rig, [frame / frm["fps"]])
    w = np.clip(ts / max(seconds, 1e-9), 0, 1)
    q = _slerp(np.repeat(q0, len(ts), 0), q1, w)
    p = (1 - w)[:, None, None] * p0 + w[:, None, None] * p1
    tip = blade_of(p4, rig, q, p)["tip"]
    m = int(round(FINE_HZ / 60))
    v = np.linalg.norm(tip[m:] - tip[:-m], axis=1) * 60
    v = v[ts[:-m] < seconds - 1e-9]                               # (chords that start inside the fade)
    k = int(np.argmax(v))
    r = float(v[k] / cut_peak_mps) if cut_peak_mps else None
    return {"seconds": float(seconds), "peak_mps": float(v[k]), "peak_at": float(ts[k] + 1 / 120), "ratio": r,
            "miss": bool(r is not None and r >= 1.0)}


def measure(p4, rig, clip, spec, frm=None, frame=None, seconds=None):
    """A clip's whole measure: {clip, fps, marks: [mark_of ...], blend: blend_in ... | None (+ from, frame)}. `frm`: the
    from-clip's name (read from p4.OUT) or a clip dict; unset = beats.blend_from, fit.start, fit.end in that order."""
    beats = spec.get("beats") or clip.get("beats") or {}
    sp = tip_speed(p4, rig, clip) if beats.get("contact") and "sword" in spec.get("held", ["sword"]) else None
    marks = [mark_of(p4, rig, clip, beats, float(t), sp) for t in (beats.get("contact") or [])] if sp else []
    out = {"clip": clip.get("name"), "fps": clip["fps"], "marks": marks, "blend": None}
    src = beats.get("blend_from") or spec.get("fit", {}).get("start") or spec.get("fit", {}).get("end") or {}
    frm = frm if frm is not None else src.get("clip")
    frame = int(frame if frame is not None else src.get("frame", 0))
    if marks and marks[0]["tip_peak_mps"] and frm is not None:
        name = frm if isinstance(frm, str) else frm.get("name")
        if isinstance(frm, str):
            f = p4.OUT / f"{frm}.json"
            frm = json.loads(f.read_text()) if f.exists() else None
        if frm is not None:
            out["blend"] = {"from": name, "frame": frame,
                            **blend_in(p4, rig, clip, frm, frame, float(seconds or beats.get("blend_in") or BLEND_S), marks[0]["tip_peak_mps"])}
    return out


def lines(res):
    """The measure as p4.py check prints it."""
    fps = res["fps"]
    ff = lambda t: f"f{t * fps:.2f} (f60 {t * 60:.2f})"
    out = []
    for i, m in enumerate(res["marks"]):
        tg = m["target"]
        tgs = f"target bearing {tg['bearing_deg']:g} deg, {tg['height_cm']:g} cm up, {tg['dist_cm']:g} cm out from the {tg['from']}"
        if m["tip_peak"] is None:
            out.append(f"  contact {i} @{ff(m['contact'])}: the tip does not move in the swing window NO-CROSS")
            continue
        pk = f"tip peak {ff(m['tip_peak'])} {m['tip_peak_mps']:.1f} m/s, contact - peak {m['contact_minus_peak_f60']:+.2f} f60"
        if m["cross"] is None:
            out.append(f"  contact {i} @{ff(m['contact'])}: no blade crossing in the swing f{m['swing'][0] * fps:.1f}-f{m['swing'][1] * fps:.1f} "
                       f"(its nearest pass is at the swing's edge) NO-CROSS; {pk} ({tgs})")
            continue
        out.append(f"  contact {i} @{ff(m['contact'])}: blade cross {ff(m['cross'])}, contact - cross {m['contact_minus_cross_f60']:+.2f} f60"
                   f"{' MISS' if m['miss'] else ''}; {pk}; pass {m['pass_cm']:.1f} cm at {m['along']:.2f} of the blade ({tgs})")
    b = res["blend"]
    if b:
        out.append(f"  blend-in {b['seconds']:g} s from {b['from']} f{b['frame']}: tip peak {b['peak_mps']:.1f} m/s @f60 {b['peak_at'] * 60:.1f} "
                   f"against the cut's {res['marks'][0]['tip_peak_mps']:.1f}: blend_peak_ratio {b['ratio']:.2f}{' MISS' if b['miss'] else ''}")
    return out


def of_built(p4, name, frm=None, frame=None, seconds=None):
    """The measure of a built clip by name (p4.OUT/<name>.json + its spec); what cmd_check calls. None when the clip
    has no contact mark or holds no sword."""
    from motion.rig import Rig
    clip = json.loads((p4.OUT / f"{name}.json").read_text())
    sp = p4.REPO / "tools/anim/p4/specs" / f"{name}.json"
    spec = json.loads(sp.read_text()) if sp.exists() else {}
    res = measure(p4, Rig(p4.RIG), clip, spec, frm, frame, seconds)
    return res if res["marks"] else None


def main(argv):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import p4
    opt = {k: argv[argv.index(k) + 1] for k in ("--from", "--blend") if k in argv}
    names = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in opt)]
    frm, _, fr = opt.get("--from", "").partition(":")
    for n in names:
        res = of_built(p4, n, frm or None, int(fr) if fr else None, float(opt["--blend"]) if "--blend" in opt else None)
        print(f"{n}:")
        print("\n".join(lines(res)) if res else "  no contact beat (or no sword held): nothing to measure")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
