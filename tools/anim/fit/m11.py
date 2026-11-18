"""m11.py (solver 11) DIR [names] [--frames FILE]: per clip AS PLAYED (clavhold + armroll(meta wrist_caps) + chain, the
worktree's live armroll), the sword line read at the PLAY CAMERA (FollowCamera: pitch 56 down, yaw 0, 23 m: taken as
orthographic). She faces psi (0 = toward the camera, down-screen; 180 = away). Blade b (clip space: +Z ahead, -X her
right, the grip's tilt from the meta, 0.95 m to the tip). World = R_y(psi) b; screen up = w.y cos56 - w.z sin56,
screen x = w.x. ANGLE = deg the blade points below screen-horizontal from the fist (+ down, - up): atan2(-up, |x|);
LEN = its on-screen length / 0.95 m. Reported: front (psi 0) worst angle + its frame, front len there and min, the
worst angle over psi in [-45, 45], over [-90, 90] and the whole circle; behind (psi 180) sideways share |b.x| max;
the sides (psi +-90) worst angle. Then head/down, tip height min, hand height, bend, hand fore-aft travel (m, vs the
pelvis), lag (m7's first harmonic vs the fist's fore-aft, frames + behind), the line's largest one-frame turn (loop
wrap), armroll's turn (report) and per-frame wrist turn max."""
import sys, json, math
from pathlib import Path
import numpy as np
W = str(Path(__file__).resolve().parents[3]) + "/"   # (the repo root of whichever checkout runs it)
sys.path.insert(0, W + "tools/anim")
from rig import Skeleton, qmul, qrot, qaxis, qinv
from keyed import grip_of
import armroll, clavhold

sk = Skeleton.load()
I = sk.i
P = math.radians(float(__import__("os").environ.get("PITCH", "56")))
CP, SP = math.cos(P), math.sin(P)


def arrays(d):
    T = len(d["tracks"][0]["keys"])
    rot = np.broadcast_to(sk.rest_rot, (T,) + sk.rest_rot.shape).copy()
    pos = np.broadcast_to(sk.rest_pos, (T,) + sk.rest_pos.shape).copy()
    for t in d["tracks"]:
        if t["bone"] in sk.names:
            (rot if t["type"] == "rot" else pos)[:, sk.i(t["bone"])] = np.array(t["keys"])
    return rot, pos


def played(d):
    rep = {}
    d0 = clavhold.hold_json(sk, d) if clavhold.on() else d
    r0, _ = arrays(d0)
    d1 = armroll.solve_json(sk, d0, report=rep)
    r1, _ = arrays(d1)
    armroll.chain_tracks(d1)
    h = I("hand_r")
    dq = qmul(qinv(r0[:, h]), r1[:, h])
    turn = np.degrees(2 * np.arccos(np.clip(np.abs(dq[:, 3]), 0, 1)))
    return d1, rep, turn


def screen(b, psi_deg):
    s, c = math.sin(math.radians(psi_deg)), math.cos(math.radians(psi_deg))
    wx = b[..., 0] * c + b[..., 2] * s
    wz = -b[..., 0] * s + b[..., 2] * c
    up = b[..., 1] * CP - wz * SP
    return np.degrees(np.arctan2(-up, np.abs(wx))), np.hypot(up, wx)


def harm_lag(ref, X):
    T = len(ref); w = np.exp(-2j * np.pi * np.arange(T) / T)
    a, b = np.sum((ref - ref.mean()) * w), np.sum((X - X.mean()) * w)
    if abs(a) < 1e-9 or abs(b) < 1e-9:
        return 0.0
    return float(-np.angle(b / a) / (2 * np.pi) * T)


def measure(d):
    loop = bool(d.get("loop", False))
    tilt = float((d.get("meta") or {}).get("grip_tilt", 0.0) or 0.0)
    dp, rep, turn = played(d)
    rot, pos = arrays(dp)
    g, p = sk.fk(rot, pos)
    h, la, ua, pel = I("hand_r"), I("lowerarm_r"), I("upperarm_r"), I("pelvis")
    lq = qaxis([1.0, 0, 0], -grip_of("sword+shield", tilt)["r"])
    N = len(rot)
    b = qrot(qmul(g[:, h], lq), np.broadcast_to([0, 0, 1.0], (N, 3)))
    T = N - 1 if loop else N
    R = {}
    R["head"] = np.degrees(np.arctan2(b[:, 0], b[:, 2]))
    R["down"] = np.degrees(np.arcsin(-np.clip(b[:, 1], -1, 1)))
    R["front"], R["flen"] = screen(b, 0.0)
    R["back"], _ = screen(b, 180.0)
    R["sideL"], _ = screen(b, -90.0)
    R["sideR"], _ = screen(b, 90.0)
    psis = np.arange(-180, 180, 5.0)
    A = np.array([screen(b, q)[0] for q in psis])  # (psi, frame)
    R["A"] = A; R["psis"] = psis
    R["share"] = np.abs(b[:, 0])
    tipw = p[:, h] + 0.95 * b
    R["tip_h"] = tipw[:, 1]
    R["hand_h"] = p[:, h, 1]
    hz = (p[:, h] - p[:, pel])[:, 2]
    R["hand_z"] = hz
    u = p[:, la] - p[:, ua]; v = p[:, h] - p[:, la]
    R["bend"] = np.degrees(np.arccos(np.einsum("ti,ti->t", u, v) / np.linalg.norm(u, axis=1) / np.linalg.norm(v, axis=1)))
    m = armroll.measure(sk, rot, pos)["r"]
    R["pro"], R["flex"], R["dev"] = m["pro"], m["flex"], m["dev"]
    bb = np.concatenate([b[:T], b[:1]]) if loop else b
    R["jl"] = np.degrees(np.arccos(np.clip(np.sum(bb[1:] * bb[:-1], 1), -1, 1)))
    R["turn"] = turn
    R["T"] = T; R["loop"] = loop; R["tilt"] = tilt; R["rep"] = rep.get("r", {})
    R["lag"] = (harm_lag(hz[:T], R["head"][:T]), harm_lag(hz[:T], R["down"][:T]), harm_lag(hz[:T], (tipw - p[:, pel])[:T, 2])) if loop else None
    return R


def summary(n, R):
    T = R["T"]
    fa = R["front"][:T]; k = int(np.argmin(fa))
    A = R["A"][:, :T]; ps = R["psis"]
    def worst(lo, hi):
        m = (ps >= lo) & (ps <= hi)
        a = A[m]
        i, f = np.unravel_index(np.argmin(a), a.shape)
        return f"{a.min():5.1f} (psi {ps[m][i]:+.0f} f{f})"
    sh = R["share"][:T]; ks = int(np.argmax(sh))
    side = np.minimum(R["sideL"][:T], R["sideR"][:T])
    s = (f"{n:20s} {'loop' if R['loop'] else ''} T{T} tilt {R['tilt']:+.0f}\n"
         f"   FRONT worst {fa.min():5.1f} at f{k} (len {R['flen'][k]:.2f}; len min {R['flen'][:T].min():.2f}) mean {fa.mean():.1f}"
         f" | +-45 {worst(-45, 45)} | +-90 {worst(-90, 90)} | all {worst(-180, 175)} | sides {side.min():.1f}"
         f" | BEHIND share max {sh.max():.3f} (f{ks}) ang min {R['back'][:T].min():.1f}\n"
         f"   head {R['head'][:T].min():.1f}..{R['head'][:T].max():.1f} down {R['down'][:T].min():.1f}..{R['down'][:T].max():.1f}"
         f" | tip h min {R['tip_h'][:T].min():.3f} | hand h {R['hand_h'][:T].min():.2f}..{R['hand_h'][:T].max():.2f}"
         f" | bend {R['bend'][:T].min():.1f}..{R['bend'][:T].max():.1f} | hand travel {np.ptp(R['hand_z'][:T]):.3f}"
         f" | jump {R['jl'].max():.1f} | armroll turn {R['rep'].get('turn', 0):.1f} (frame max {R['turn'].max():.1f})"
         f" | pro {R['pro'][:T].min():.0f}..{R['pro'][:T].max():.0f} flex {R['flex'][:T].min():.0f}..{R['flex'][:T].max():.0f}"
         f" dev {R['dev'][:T].min():.0f}..{R['dev'][:T].max():.0f}")
    if R["lag"]:
        s += f" | lag head {R['lag'][0]:+.2f} down {R['lag'][1]:+.2f} tipz {R['lag'][2]:+.2f}"
    return s


def frames(n, R):
    out = [n]
    for f in range(len(R["head"])):
        out.append(f"  f{f:3d} head {R['head'][f]:7.1f} down {R['down'][f]:5.1f} FRONT {R['front'][f]:6.1f} len {R['flen'][f]:.2f}"
                   f" share {R['share'][f]:.2f} back {R['back'][f]:5.1f} sideL {R['sideL'][f]:5.1f} sideR {R['sideR'][f]:5.1f}"
                   f" tip {R['tip_h'][f]:.3f} hand {R['hand_h'][f]:.3f} z {R['hand_z'][f]:+.3f} bend {R['bend'][f]:5.1f}"
                   f" pro {R['pro'][f]:6.1f} flex {R['flex'][f]:6.1f} dev {R['dev'][f]:6.1f} turn {R['turn'][f]:4.1f}")
    return "\n".join(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ff = None
    if "--frames" in sys.argv:
        ff = sys.argv[sys.argv.index("--frames") + 1]
        args = [a for a in args if a != ff]
    D = Path(args[0]); names = args[1:] or sorted(p.stem for p in D.glob("*.json"))
    fr = []
    for n in names:
        d = json.load(open(D / f"{n}.json"))
        R = measure(d)
        print(summary(n, R), flush=True)
        fr.append(frames(n, R))
    if ff:
        Path(ff).write_text("\n".join(fr) + "\n")
