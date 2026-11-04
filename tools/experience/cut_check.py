"""The cut check (H4): every cinematic-to-play hand-back held to the one cut rule, in numbers.

    python tools/experience/cut_check.py LOG [LOG ...] [--csv DIR]

Reads the CUTLOG / CUTSEAM / CUTCONTROL lines a run with --cutlog prints (godot/src/Game/GameSeam.cs) and,
for each hand-back, reports:
  cam   the camera's worst one-frame step (metres and degrees) against the frames around it: a pop or a cut
        shows as a step many times its neighbours'; its peak speed and turn rate over the window;
  fov   the worst one-frame change of the vertical lens (degrees);
  hud   when the HUD starts and ends its fade, against when the camera lands (control back);
  her   her head's and right hand's worst one-frame jump relative to her root (a pose popping to idle),
        and her root's (a teleport).
A cut FAILS on: a camera frame over 0.3 m or 4 deg moving 4x faster than the frames around it (a new shot
inside the cinematic is not counted); a lens step over 1.5 deg; the HUD starting more than 0.3 s before the
camera lands; through the hand-back (to 0.5 s after control), her head or hand moving over 0.12 m, or her
root over 0.2 m, per 60th of a second (speeds, since a picture run's frames are 0.1 s). --csv writes each cut's frames to DIR/<cine>_<n>.csv for plotting.
"""
import math, os, re, sys

LINE = re.compile(r"CUTLOG (\S+) t=(\S+) dt=(\S+) phase=(\w+) (?:shot=(-?\d+) )?pos=(\S+) fwd=(\S+) vfov=(\S+) hud=(\S+) cap=(\d)(.*)")
VEC = lambda s: tuple(float(x) for x in s.split(","))


def parse(path):
    cuts, cur = [], None
    for raw in open(path, encoding="utf-8", errors="replace"):
        if "CUTSEAM " in raw and cur is not None:
            m = re.search(r"dur=(\S+) metres=(\S+) degrees=(\S+) skipped=(\w+)", raw)
            cur["seam"] = dict(dur=float(m[1]), metres=float(m[2]), degrees=float(m[3]), skipped=m[4] == "True")
            cur["seam_t"] = cur["frames"][-1]["t"] if cur["frames"] else 0
            continue
        if "CUTCONTROL " in raw and cur is not None:
            cur["control_t"] = cur["frames"][-1]["t"] if cur["frames"] else 0
            continue
        m = LINE.search(raw)
        if not m: continue
        t = float(m[2])
        if cur is None or m[1] != cur["id"] or t < cur["frames"][-1]["t"] - 1e-6:
            cur = dict(id=m[1], frames=[], seam=None, seam_t=None, control_t=None); cuts.append(cur)
        rest = dict(re.findall(r"(\w+)=([-\d.,]+)", m[11]))
        cur["frames"].append(dict(t=t, dt=float(m[3]), phase=m[4], shot=int(m[5]) if m[5] else -1, pos=VEC(m[6]), fwd=VEC(m[7]), vfov=float(m[8]),
                                  hud=float(m[9]), cap=int(m[10]), root=VEC(rest["root"]) if "root" in rest else None,
                                  head=VEC(rest["head"]) if "head" in rest else None, hand=VEC(rest["hand"]) if "hand" in rest else None))
    return cuts


def dist(a, b): return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def ang(a, b):
    d = sum(x * y for x, y in zip(a, b)) / max(1e-9, math.sqrt(sum(x * x for x in a) * sum(y * y for y in b)))
    return math.degrees(math.acos(max(-1, min(1, d))))


def median(xs):
    xs = sorted(xs); return xs[len(xs) // 2] if xs else 0


def check(c):
    f = c["frames"]; out = {"id": c["id"], "fails": []}
    # Per frame: metres and degrees moved, and as speeds (frames differ in length: a picture's frame is 0.1 s).
    # A cut inside the cinematic (a new shot) is the film's own and not counted.
    steps = []
    for i in range(1, len(f)):
        a, b = f[i - 1], f[i]
        if a["phase"] == "cine" and b["phase"] == "cine" and a["shot"] != b["shot"]: continue
        dt = max(b["dt"], 1e-3); m, d = dist(a["pos"], b["pos"]), ang(a["fwd"], b["fwd"])
        steps.append((m, d, b["t"], dt, m / dt, d / dt))
    worst = (0, 0, 0, 0, 0)  # score, metres, degrees, t, ratio
    for i, (m, d, t, dt, v, w) in enumerate(steps):
        around = [s for j, s in enumerate(steps) if j != i and abs(j - i) <= 4]
        mv, mw = median([s[4] for s in around]), median([s[5] for s in around])
        ratio = max(v / max(mv, 2.0), w / max(mw, 15.0))
        big = m > 0.3 or d > 4
        if big and ratio > worst[4]: worst = (1, m, d, t, ratio)
        if big and ratio >= 4: out["fails"].append(f"camera jump {m:.2f} m / {d:.1f} deg at t={t:+.2f} ({ratio:.0f}x the speed around)")
    out["speed"] = max((s[4] for s in steps), default=0)
    out["turn"] = max((s[5] for s in steps), default=0)
    out["step"] = worst
    fov = max(((abs(f[i]["vfov"] - f[i - 1]["vfov"]), f[i]["t"]) for i in range(1, len(f))), default=(0, 0))
    out["fov"] = fov
    if fov[0] > 1.5: out["fails"].append(f"lens step {fov[0]:.1f} deg at t={fov[1]:+.2f}")
    hud0 = next((x["t"] for x in f if x["hud"] > 0.02), None); hud1 = next((x["t"] for x in f if x["hud"] > 0.98), None)
    land = c["control_t"] if c["control_t"] is not None else next((x["t"] for x in f if x["cap"] == 0), None)
    out.update(hud0=hud0, hud1=hud1, land=land, seam=c["seam"], seam_t=c["seam_t"])
    if hud0 is not None and land is not None and hud0 < land - 0.3: out["fails"].append(f"HUD starts {land - hud0:.2f} s before the camera lands")
    # Her pose, through the hand-back only (to 0.5 s after control; later it is play, her own attacks).
    pj = (0, 0, ""); rj = (0, 0)
    end = (land if land is not None else 0) + 0.5
    for i in range(1, len(f)):
        a, b = f[i - 1], f[i]
        if b["t"] > end: break
        if a["head"] and b["head"]:
            for k in ("head", "hand"):
                j = dist(a[k], b[k]) / max(b["dt"], 1e-3) * (1 / 60)  # metres per 60th of a second
                if j > pj[0]: pj = (j, b["t"], k)
        if a["root"] and b["root"]:
            j = dist(a["root"], b["root"]) / max(b["dt"], 1e-3) * (1 / 60)
            if j > rj[0]: rj = (j, b["t"])
    out["pose"], out["root"] = pj, rj
    if pj[0] > 0.12: out["fails"].append(f"her {pj[2]} jumps {pj[0]:.2f} m a 60th at t={pj[1]:+.2f}")
    if rj[0] > 0.2: out["fails"].append(f"her root jumps {rj[0]:.2f} m a 60th at t={rj[1]:+.2f}")
    return out


def main():
    args = sys.argv[1:]; csv = None
    if "--csv" in args: i = args.index("--csv"); csv = args[i + 1]; del args[i:i + 2]
    allok = True
    for path in args:
        for n, c in enumerate(parse(path)):
            r = check(c); ok = not r["fails"]; allok &= ok
            s = r["seam"]
            print(f"{'PASS' if ok else 'FAIL'} {r['id']} ({os.path.basename(path)} #{n}) frames={len(c['frames'])}"
                  f" seam={'%.2fs from %.1f m/%.0f deg' % (s['dur'], s['metres'], s['degrees']) if s else '-'}"
                  f" land={r['land'] if r['land'] is None else '%+.2f' % r['land']}"
                  f" hud={'-' if r['hud0'] is None else '%+.2f' % r['hud0']}..{'-' if r['hud1'] is None else '%+.2f' % r['hud1']}")
            st = r["step"]
            print(f"     cam worst step {st[1]:.2f} m / {st[2]:.1f} deg at t={st[3]:+.2f} ({st[4]:.1f}x); peak {r['speed']:.1f} m/s, {r['turn']:.0f} deg/s;"
                  f" lens {r['fov'][0]:.2f} deg; her pose {r['pose'][0]:.3f} m ({r['pose'][2]} t={r['pose'][1]:+.2f}), root {r['root'][0]:.2f} m")
            for x in r["fails"]: print("     -", x)
            if csv:
                os.makedirs(csv, exist_ok=True)
                with open(os.path.join(csv, f"{r['id']}_{n}.csv"), "w") as fh:
                    fh.write("t,phase,x,y,z,fx,fy,fz,vfov,hud,cap\n")
                    for x in c["frames"]: fh.write(",".join(map(str, [x["t"], x["phase"], *x["pos"], *x["fwd"], x["vfov"], x["hud"], x["cap"]])) + "\n")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
