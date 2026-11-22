"""Task 1 (movement baseline): the numbers from the --moves12 takes (tools/motion/move_baseline.py).

  python tools/motion/move_baseline_table.py [OUT.md]

Reads godot/.shots/move_baseline/TAKE/{ticks.csv,frames.csv,log.txt}; prints and writes one markdown table plus
per-take detail. Frames are 60 fps drawn frames (movie maker, one sim step a frame). Angles: atan2(dx, dz) deg,
0 = +Z (toward the camera, down-screen), 90 = +X (screen-right). Body length = 1.70 m (her standing height, assumed).
"""
import csv, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "godot/.shots" / __import__("os").environ.get("MOVES_OUT", "move_baseline")  # the takes' folder, as move_baseline.py
BODY = 1.70
FPS = 60


def load(take):
    p = D / take
    if not (p / "frames.csv").exists(): return None
    f = [{k: v for k, v in r.items()} for r in csv.DictReader(open(p / "frames.csv"))]
    t = [{k: v for k, v in r.items()} for r in csv.DictReader(open(p / "ticks.csv"))]
    for rows in (f, t):
        for r in rows:
            for k, v in list(r.items()):
                try: r[k] = float(v)
                except (ValueError, TypeError): pass
    log = (p / "log.txt").read_text(errors="replace")
    ins = [(float(m[1]), int(m[2]), m[3]) for m in re.finditer(r"MOVES12 in (\S+) frame (\d+) (.+)", log)]
    errs = len(re.findall(r"ERROR|Exception", log))
    return dict(f=f, t=t, ins=ins, errs=errs, log=log)


def ang(x, z): return math.degrees(math.atan2(x, z))
def adiff(a, b): return (a - b + 180) % 360 - 180
def hyp(x, z): return math.hypot(x, z)


def at_frame(rows, fr):
    for i, r in enumerate(rows):
        if r["frame"] >= fr: return i
    return len(rows) - 1


def input_frame(d, what):
    for t, fr, w in d["ins"]:
        if what.lower() in w.lower(): return fr
    return None


def cam_metrics(f, i_move, i_rest):
    """Camera trail on start (frames from her first drawn motion to the look point's), and after her final rest: frames
    until the look point is still (< 0.02 m/s and stays), its travel after she stopped, her screen drift then (px)."""
    out = {}
    if i_move is not None:
        l0 = (f[i_move - 1]["look_x"], f[i_move - 1]["look_z"])
        j = next((k for k in range(i_move, len(f)) if hyp(f[k]["look_x"] - l0[0], f[k]["look_z"] - l0[1]) > 0.005), None)
        out["cam_trail_start_f"] = None if j is None else j - i_move
    if i_rest is not None:
        still = None
        for k in range(i_rest + 1, len(f)):
            ok = all(hyp(f[m]["look_x"] - f[m - 1]["look_x"], f[m]["look_z"] - f[m - 1]["look_z"]) * FPS < 0.02 for m in range(k, min(len(f), k + 10)))
            if ok: still = k; break
        out["cam_still_after_stop_f"] = None if still is None else still - i_rest
        e = still if still is not None else len(f) - 1
        out["cam_travel_after_stop_m"] = hyp(f[e]["look_x"] - f[i_rest]["look_x"], f[e]["look_z"] - f[i_rest]["look_z"])
        out["her_screen_drift_after_stop_px"] = hyp(f[e]["her_px_x"] - f[i_rest]["her_px_x"], f[e]["her_px_y"] - f[i_rest]["her_px_y"])
        out["cam_still_reached"] = still is not None
        tot = out["cam_travel_after_stop_m"]
        out["cam_90pct_travel_f"] = next((k - i_rest for k in range(i_rest, e + 1) if hyp(f[k]["look_x"] - f[i_rest]["look_x"], f[k]["look_z"] - f[i_rest]["look_z"]) >= 0.9 * tot), None)
        out["cam_speed_at_her_rest_ms"] = hyp(f[i_rest]["look_x"] - f[i_rest - 1]["look_x"], f[i_rest]["look_z"] - f[i_rest - 1]["look_z"]) * FPS
    return out


def first_motion(f, i0):
    x0, z0 = f[i0]["dx"], f[i0]["dz"]
    return next((k for k in range(i0, len(f)) if hyp(f[k]["dx"] - x0, f[k]["dz"] - z0) > 0.005), None)


def rest_after(f, i0):
    """First drawn frame after i0 from which her drawn position moves < 1 mm a frame for 10 frames."""
    for k in range(max(i0, 1), len(f) - 10):
        if all(hyp(f[m]["dx"] - f[m - 1]["dx"], f[m]["dz"] - f[m - 1]["dz"]) < 0.001 for m in range(k, k + 10)): return k
    return None


def top_speed(t): return max(r["speed"] for r in t)


def shot_start(d, key):
    f, t = d["f"], d["t"]
    fi = input_frame(d, key)
    i_in = at_frame(f, fi)
    i_mv = first_motion(f, i_in)
    top = top_speed(t)
    ti = at_frame(t, fi)
    k90 = next(k for k in range(ti, len(t)) if t[k]["speed"] >= 0.9 * top)
    k99 = next(k for k in range(ti, len(t)) if t[k]["speed"] >= 0.99 * top)
    dist99 = hyp(t[k99]["x"] - t[ti]["x"], t[k99]["z"] - t[ti]["z"])
    r = dict(top_ms=top, input_to_motion_f=i_mv - i_in, to90_f=k90 - ti, to99_f=k99 - ti, dist_to99_m=dist99)
    r.update(cam_metrics(f, i_mv, None))
    # camera lead at full run: look point ahead of her along her velocity (m)
    k = at_frame(f, fi + 100)
    vx, vz = t[at_frame(t, fi + 100)]["vx"], t[at_frame(t, fi + 100)]["vz"]
    v = hyp(vx, vz) or 1
    r["cam_lead_at_run_m"] = ((f[k]["look_x"] - f[k]["dx"]) * vx + (f[k]["look_z"] - f[k]["dz"]) * vz) / v
    # frames until the look point leads her (crosses from behind to ahead)
    cross = next((j for j in range(i_mv, len(f)) if ((f[j]["look_x"] - f[j]["dx"]) * vx + (f[j]["look_z"] - f[j]["dz"]) * vz) / v > 0.05), None)
    r["cam_behind_then_leads_after_f"] = None if cross is None else cross - i_mv
    return r


def shot_stop(d, key):
    f, t = d["f"], d["t"]
    fu = input_frame(d, key)
    i_up = at_frame(f, fu)
    ti = at_frame(t, fu)
    ks = next((k for k in range(ti, len(t)) if t[k]["speed"] < 0.05), len(t) - 1)
    i_rest = rest_after(f, i_up)
    r = dict(sim_stop_f=ks - ti, stop_dist_m=hyp(t[ks]["x"] - t[ti]["x"], t[ks]["z"] - t[ti]["z"]),
             drawn_rest_f=None if i_rest is None else i_rest - i_up)
    r.update(cam_metrics(f, None, i_rest))
    return r


def shot_turn(d, old_key, new_dir):
    """new_dir: unit (x, z). Frames from the key change: until her velocity's part along the new direction is > 0 (turned
    round), to 90% of top speed along it; the overshoot along the old way; her drawn facing within 10 deg of the aim."""
    f, t = d["f"], d["t"]
    fc = input_frame(d, old_key + " up")
    ti = at_frame(t, fc)
    top = top_speed(t)
    nx, nz = new_dir
    k0 = next(k for k in range(ti, len(t)) if t[k]["vx"] * nx + t[k]["vz"] * nz > 0.05)
    k90 = next((k for k in range(ti, len(t)) if t[k]["vx"] * nx + t[k]["vz"] * nz >= 0.9 * top), None)
    ox, oz = t[ti]["vx"], t[ti]["vz"]; on = hyp(ox, oz) or 1
    over = max((t[k]["x"] - t[ti]["x"]) * ox / on + (t[k]["z"] - t[ti]["z"]) * oz / on for k in range(ti, k90 or len(t)))
    i_c = at_frame(f, fc)
    face_ok = next((k for k in range(i_c, len(f)) if f[k]["aim_deg"] != "" and abs(adiff(f[k]["face_deg"], f[k]["aim_deg"])) < 10
                    and all(f[m]["aim_deg"] != "" and abs(adiff(f[m]["face_deg"], f[m]["aim_deg"])) < 10 for m in range(k, min(len(f), k + 5)))), None)
    # camera: frames its look point keeps moving the old way after the change, and its peak speed relative to her top speed
    lk = next((k for k in range(i_c + 1, len(f)) if ((f[k]["look_x"] - f[k - 1]["look_x"]) * ox + (f[k]["look_z"] - f[k - 1]["look_z"]) * oz) / on <= 0), None)
    cam_pk = max(hyp(f[k]["look_x"] - f[k - 1]["look_x"], f[k]["look_z"] - f[k - 1]["look_z"]) * FPS for k in range(i_c + 1, min(len(f), i_c + 120)))
    r = dict(turned_f=k0 - ti, new_dir90_f=None if k90 is None else k90 - ti, overshoot_m=over,
             face_on_aim_f=None if face_ok is None else face_ok - i_c,
             cam_keeps_old_way_f=None if lk is None else lk - i_c, cam_peak_speed_x_run=cam_pk / top)
    return r


def steady(d, t0, t1, aim_fixed=True):
    f, t = d["f"], d["t"]
    tt = [r for r in t if t0 <= r["t_shot"] <= t1]
    ff = [r for r in f if t0 <= r["t_shot"] <= t1 and r["aim_deg"] != ""]
    sp = sum(r["speed"] for r in tt) / len(tt)
    fe = [abs(adiff(r["face_deg"], r["aim_deg"])) for r in ff]
    mv = [abs(adiff(r["face_deg"], ang(r2["vx"], r2["vz"]))) for r, r2 in zip(ff, tt)] if ff else []
    return dict(speed_ms=sp, face_to_aim_mean_deg=sum(fe) / len(fe) if fe else None, face_to_aim_max_deg=max(fe) if fe else None,
                face_to_travel_mean_deg=sum(mv) / len(mv) if mv else None)


def dash(d, key):
    f, t = d["f"], d["t"]
    fp = input_frame(d, key)
    ti = at_frame(t, fp)
    ks = next(k for k in range(ti, len(t)) if t[k]["dashT"] > 0)
    ke = next(k for k in range(ks, len(t)) if t[k]["dashT"] <= 0)
    p0 = (t[ks - 1]["x"], t[ks - 1]["z"]); p1 = (t[ke]["x"], t[ke]["z"])
    dd = hyp(p1[0] - p0[0], p1[1] - p0[1])
    di = ang(p1[0] - p0[0], p1[1] - p0[1])
    r = dict(press_to_dash_f=ks - ti, dash_f=ke - ks, dash_m=dd, dash_body=dd / BODY, dash_dir_deg=di)
    pr = t[ti]
    if pr["ptr_x"] != "": r["cursor_dir_deg"] = ang(pr["ptr_x"] - pr["x"], pr["ptr_z"] - pr["z"])
    if hyp(pr["mx"], pr["mz"]) > 0.05: r["keys_dir_deg"] = ang(pr["mx"], pr["mz"])
    r["facing_before_deg"] = f[at_frame(f, fp)]["face_deg"]
    r["_ke"] = ke
    return r


def dash_out(d, key, top):
    t = d["t"]
    r = dash(d, key)
    ke = r.pop("_ke")
    k95 = next((k for k in range(ke, len(t)) if t[k]["speed"] >= 0.95 * top), None)
    r["exit_speed_ms"] = t[ke]["speed"]
    r["exit_vel_dir_deg"] = ang(t[ke]["vx"], t[ke]["vz"])
    r["to_run_speed_after_dash_f"] = None if k95 is None else k95 - ke
    r["min_speed_after_dash_ms"] = min(t[k]["speed"] for k in range(ke, min(len(t), ke + 30)))
    r["peak_speed_after_dash_ms"] = max(t[k]["speed"] for k in range(ke, min(len(t), ke + 60)))
    # the path's bend after the dash: how far she drifts off the line of the keys in the 30 ticks after
    mx, mz = t[ke]["mx"], t[ke]["mz"]
    if hyp(mx, mz) > 0.05:
        n = hyp(mx, mz); px, pz = -mz / n, mx / n
        r["exit_drift_off_keys_line_m"] = max(abs((t[k]["x"] - t[ke]["x"]) * px + (t[k]["z"] - t[ke]["z"]) * pz) for k in range(ke, min(len(t), ke + 30)))
    return r


def strike(d, top):
    t, f = d["t"], d["f"]
    fp = input_frame(d, "LMB down")
    ti = at_frame(t, fp)
    w = [k for k in range(ti, min(len(t), ti + 90)) if t[k]["castT"] > 0]
    r = dict(cast_ticks=len(w))
    end = (w[-1] + 1) if w else ti + 30
    seg = range(ti, end)
    r["min_speed_ms"] = min(t[k]["speed"] for k in seg)
    r["mean_speed_ms"] = sum(t[k]["speed"] for k in seg) / len(seg)
    r["dist_during_swing_m"] = hyp(t[end]["x"] - t[ti]["x"], t[end]["z"] - t[ti]["z"])
    lo = next((k for k in range(ti, len(t)) if t[k]["speed"] < 0.95 * top), None)
    r["frames_below_95"] = 0 if lo is None else next((k for k in range(lo, len(t)) if t[k]["speed"] >= 0.95 * top), len(t)) - lo
    m = r["min_speed_ms"] / top
    r["verdict"] = "planted" if m < 0.1 else "slowed" if m < 0.9 else "free"
    return r


def heavy(d):
    t, f = d["t"], d["f"]
    hits = [r for r in t if "Hit" in str(r["ev"])]
    heavy = [r for r in t if "heavy" in str(r["ev"])]
    holds, cur = [], []
    for k, r in enumerate(f):
        if r["her_held"] == 1: cur.append(k)
        elif cur: holds.append(cur); cur = []
    if cur: holds.append(cur)
    out = dict(hit_ticks=len(hits), heavy_ticks=len(heavy), holds=len(holds))
    det = []
    for h in holds:
        a, b = h[0] - 1, h[-1]
        det.append(dict(frames=len(h), her_slide_m=hyp(f[b]["dx"] - f[a]["dx"], f[b]["dz"] - f[a]["dz"]),
                        cam_slide_m=hyp(f[b]["look_x"] - f[a]["look_x"], f[b]["look_z"] - f[a]["look_z"]),
                        her_screen_px=hyp(f[b]["her_px_x"] - f[a]["her_px_x"], f[b]["her_px_y"] - f[a]["her_px_y"]),
                        speed_ms=t[at_frame(t, f[b]["frame"])]["speed"], rate=min(f[k]["her_rate"] for k in h)))
    out["hold_detail"] = det
    return out


def circle(d, c_off=(0, -5)):
    t, f = d["t"], d["f"]
    s0 = next(r for r in t if r["t_shot"] >= 0)
    cx, cz = s0["x"] + c_off[0], s0["z"] + c_off[1]
    tt = [r for r in t if 0.8 <= r["t_shot"] <= 6.0]
    rad = [hyp(r["x"] - cx, r["z"] - cz) for r in tt]
    sp = [r["speed"] for r in tt]
    out = dict(mean_speed_ms=sum(sp) / len(sp), min_speed_ms=min(sp), radius_mean=sum(rad) / len(rad), radius_min=min(rad), radius_max=max(rad),
               key_changes=sum(1 for _, _, w in d["ins"] if "down" in w and 0 < _ < 6.0))
    out.update(steady(d, 0.8, 6.0))
    return out


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    res = {}
    s01 = load("s01"); top = top_speed(s01["t"])
    for tk, on, off in [("s01", "D down", "D up"), ("p01", "stick on", "stick off")]:
        d = load(tk)
        if d: res[tk + " start"] = shot_start(d, on); res[tk + " stop"] = shot_stop(d, off); res[tk + " stop"]["errs"] = d["errs"]
    for tk, ok, nd in [("s03", "D", (-1, 0)), ("p03", "stick", (-1, 0)), ("s04", "D", (0, -1))]:
        d = load(tk)
        if not d: continue
        try:
            if tk == "p03":
                # the stick flick has no key line: the change is the first 'stick' transition after the press
                fc = [fr for tt, fr, w in d["ins"] if tt > 1.0][0]
                d["ins"].insert(0, (1.5, fc, "stick up"))
                res[tk] = shot_turn(d, "stick", nd)
            else: res[tk] = shot_turn(d, ok, nd)
            if tk == "p03":   # the stop that counts is the LAST stick-off (the first one is the reversal's one-frame release)
                lo = [(tt, fr) for tt, fr, w in d["ins"] if w == "stick off"][-1]
                d["ins"].insert(0, (lo[0], lo[1], "stick final off"))
            res[tk + " stop"] = shot_stop(d, "A up" if tk == "s03" else "W up" if tk == "s04" else "stick final off" if tk == "p03" else "stick off")
        except StopIteration as e: res[tk] = {"error": "metric not found"}
    for tk, rng in [("s05", (0.8, 1.4)), ("s06", (0.8, 1.4))]:
        d = load(tk)
        if d: res[tk] = steady(d, *rng); res[tk]["speed_x_forward"] = res[tk]["speed_ms"] / top
    d = load("s05")
    if d: res["s05 left"] = steady(d, 2.3, 2.9); res["s05 left"]["speed_x_forward"] = res["s05 left"]["speed_ms"] / top
    d = load("s07")
    if d: res["s07"] = circle(d)
    for tk, key in [("s08", "Space down"), ("p08", "LB down")]:
        d = load(tk)
        if d: r = dash(d, key); r.pop("_ke"); res[tk] = r
    for tk, key in [("s09", "Space down"), ("s10a", "Space down"), ("s10b", "Space down"), ("p10a", "LB down"), ("p10b", "LB down")]:
        d = load(tk)
        if d: res[tk] = dash_out(d, key, top)
    d = load("s11")
    if d: res["s11"] = strike(d, top)
    d = load("s12")
    if d: res["s12"] = heavy(d)
    lines = []
    for k, v in res.items():
        lines.append(f"{k}: " + ", ".join(f"{a}={(round(b, 3) if isinstance(b, float) else b)}" for a, b in v.items()))
    txt = "\n".join(lines)
    print(txt)
    if out: out.write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
