"""m14.py RUNDIR [RUNDIR2 ...] [--legs 0-15] [--frames LEG]: the side carry's measures per leg of the eight set, from the
BLADE lines (one a drawn frame; frame index = the SCR2 line before it). Leg i runs frames s=60+60i .. s+36, then stands.
Angles are on screen (px space): a = the blade's angle from straight down (+ = tip toward her back side on screen when she
is side-on, |sin face| > 0.3; else + = screen right); 'below' = below screen level (90 straight down)."""
import sys, math
import numpy as np
LEGS = ["away", "toward", "side_x", "side_mx", "away_x", "toward_mx", "away_mx", "toward_x",
        "back_ft", "back_fa", "back_fx", "back_fmx", "strafe_fx_t", "strafe_fx_a", "strafe_fmx_a", "strafe_fmx_t"]
R_TH = (0.123, 0.081); R_CA = (0.074, 0.046)


def load(d):
    rows = {}; fi = -1; ppm = []
    for ln in open(d + "/views.log", errors="ignore"):
        if ln.startswith("SCR2 "):
            fi += 1; t = ln.split(); rows.setdefault(fi, {})["pel"] = (float(t[1]), float(t[2]))
        elif ln.startswith("BODY2 ") and fi >= 0:
            t = ln.split(); v = [float(x) for x in t[1:40]]
            rows.setdefault(fi, {})["body"] = np.array(v).reshape(13, 3)
        elif ln.startswith("BLADE ") and fi >= 0:
            t = ln.split(); r = rows.setdefault(fi, {})
            r["g"] = (float(t[1]), float(t[2])); r["t"] = (float(t[3]), float(t[4]))

            def K(k, n):
                i = t.index(k); return [float(x) for x in t[i + 1:i + 1 + n]]
            r["hr"] = K("hr", 2); r["hd"] = K("hd", 2); r["ft"] = K("ft", 8)
            r["gw"] = np.array(K("gw", 3)); r["tw"] = np.array(K("tw", 3)); r["ax"] = np.array(K("ax", 3))
            if "kn" in t: r["kn"] = np.array(K("kn", 6)).reshape(2, 3)
            sc = K("sc", 3 if "kn" in t else 2); r["w"] = sc[0]; r["tilt"] = sc[1]; r["spr"] = sc[2] if len(sc) > 2 else 0
            r["face"] = K("face", 1)[0]
        elif ln.startswith("TURN2 "):
            t = ln.split(); i = t.index("ppm"); ppm.append(float(t[i + 1]))
    return rows, (float(np.median(ppm)) if ppm else 74.0)


def segdist(p0, p1, q0, q1):
    """closest points of segments p0p1, q0q1: (dist, s along p, u along q)"""
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c = d1 @ r; b = d1 @ d2; den = a * e - b * b
    s = float(np.clip((b * f - c * e) / den, 0, 1)) if den > 1e-12 else 0.0
    u = (b * s + f) / e
    if u < 0: u = 0.0; s = float(np.clip(-c / a, 0, 1))
    elif u > 1: u = 1.0; s = float(np.clip((b - c) / a, 0, 1))
    return float(np.linalg.norm(p0 + d1 * s - (q0 + d2 * u))), s, u


def frame(r, ppm=74.0):
    f = math.radians(r["face"]); sf = math.sin(f)
    dx, dy = r["t"][0] - r["g"][0], r["t"][1] - r["g"][1]
    a = math.degrees(math.atan2(dx, dy)); plen = math.hypot(dx, dy) / ppm
    side = abs(sf) > 0.3
    ab = a * (-np.sign(sf)) if side else a
    below = math.degrees(math.atan2(dy, abs(dx)))
    b = r["tw"] - r["gw"]; L = float(np.linalg.norm(b)); b = b / L
    fwd = np.array([math.sin(f), 0, math.cos(f)]); right = np.array([-math.cos(f), 0, math.sin(f)])
    back3 = math.degrees(math.atan2(-(b @ fwd), -b[1])); splay = math.degrees(math.asin(float(np.clip(b @ right, -1, 1))))
    pel = r.get("pel", (0, 0))
    fist_fwd = (r["hr"][0] - pel[0]) * (np.sign(sf) if side else 1)
    ft = r["ft"]; low = max(ft[1], ft[3], ft[5], ft[7])
    clr = None
    if "kn" in r and "body" in r:
        B = r["body"]; best = (9, "")
        for s, (H, Fo) in enumerate(((B[0], B[2]), (B[1], B[3]))):
            Kn = r["kn"][s]
            for nm, p, q, rad in (("th", H, Kn, R_TH), ("ca", Kn, Fo, R_CA)):
                g0 = r["gw"] + (r["tw"] - r["gw"]) * (0.10 / L)
                dd, sb, uu = segdist(g0, r["tw"], p, q); sb = (0.10 + sb * (L - 0.10)) / L
                c = dd - (rad[0] + (rad[1] - rad[0]) * uu)
                if c < best[0]: best = (c, nm + "lr"[s] + "@%.2f" % (sb * L))
        clr = best
    return dict(plen=plen, tipw=r["tw"][1], a=a, ab=ab, below=below, side=side, back3=back3, splay=splay, fist_fwd=fist_fwd, tipy=r["t"][1], low=low,
                fisty=r["hr"][1], heady=r["hd"][1], w=r["w"], tilt=r["tilt"], spr=r["spr"], face=r["face"], clr=clr, L=L)


def wrap(x): return (x + 180) % 360 - 180


def leg(rows, ppm, i, verbose=False):
    s = 60 + 60 * i
    F = {k: frame(rows[k], ppm) for k in range(s - 6, s + 58) if k in rows and "g" in rows[k]}
    if not F: return None
    run = [k for k in range(s + 12, s + 37) if k in F]
    ab = np.array([F[k]["ab"] for k in run]); ff = np.array([F[k]["fist_fwd"] for k in run])
    best = (-2, 0)
    for Lg in range(-4, 9):
        if Lg < 0: x = -ff[-Lg:]; y = ab[:len(ab) + Lg]
        else: x = -ff[:len(ff) - Lg] if Lg else -ff; y = ab[Lg:]
        if len(x) > 6 and np.std(x) > 0 and np.std(y) > 0:
            c = float(np.corrcoef(x, y)[0, 1])
            if c > best[0]: best = (c, Lg)

    def rate(ks):
        ks = [k for k in ks if k in F and k - 1 in F and min(F[k]["plen"], F[k - 1]["plen"]) >= 0.2]
        return max((abs(wrap(F[k]["a"] - F[k - 1]["a"])), k - s) for k in ks) if ks else (0, 0)
    st = rate(range(s - 2, s + 14)); sp = rate(range(s + 36, s + 54)); allr = rate(range(s - 2, s + 56))
    down = [k - s for k in sorted(F) if abs(F[k]["a"]) < 10 and F[k]["tipy"] > F[k]["low"] + 4]
    chin = max((F[k]["heady"] - F[k]["fisty"]) / ppm for k in F)      # + = fist above the head joint (m on screen)
    tipb = max((F[k]["tipy"] - F[k]["low"]) / ppm for k in run)        # + = tip below the lowest boot point
    below = min(F[k]["below"] for k in run)
    clr = [F[k]["clr"] for k in F if F[k]["clr"] is not None]
    cmin = min(clr, key=lambda c: c[0]) if clr else None
    out = dict(name=LEGS[i], amin=ab.min(), amax=ab.max(), swing=ab.max() - ab.min(), lag=best[1], lagc=best[0],
               st=st, sp=sp, allr=allr, down=down, chin=chin, tipb=tipb, below=below, cmin=cmin,
               b3=(min(F[k]["back3"] for k in run), max(F[k]["back3"] for k in run)),
               spl=(min(F[k]["splay"] for k in run), max(F[k]["splay"] for k in run)),
               w=max(F[k]["w"] for k in run), tilt=(min(F[k]["tilt"] for k in run), max(F[k]["tilt"] for k in run)), side=F[run[0]]["side"])
    if verbose:
        for k in sorted(F):
            x = F[k]
            print(f"  f{k} {k - s:+3d} face {x['face']:7.1f} a {x['a']:6.1f} ab {x['ab']:6.1f} below {x['below']:5.1f} b3 {x['back3']:6.1f} spl {x['splay']:5.1f} "
                  f"len {x['plen']:.2f} tipw {x['tipw']:+.2f} fist {x['fist_fwd']:6.1f} w {x['w']:.2f} tilt {x['tilt']:6.2f} spr {x['spr']:6.2f} tipb {(x['tipy'] - x['low']) / ppm:+.2f}"
                  + (f" clr {x['clr'][0] * 100:5.1f} {x['clr'][1]}" if x['clr'] else ""))
    return out


def main():
    a = sys.argv[1:]
    legs = (0, 15)
    if "--legs" in a: i = a.index("--legs"); legs = tuple(int(x) for x in a[i + 1].split("-")); del a[i:i + 2]
    vf = None
    if "--frames" in a: i = a.index("--frames"); vf = int(a[i + 1]); del a[i:i + 2]
    for d in a:
        rows, ppm = load(d)
        print(f"== {d}  ppm {ppm:.1f}  frames {len(rows)}")
        for i in range(legs[0], legs[1] + 1):
            o = leg(rows, ppm, i, verbose=(vf == i))
            if not o: continue
            c = f"{o['cmin'][0] * 100:5.1f}cm {o['cmin'][1]}" if o["cmin"] else "-"
            dn = ",".join(str(x) for x in o["down"]) if o["down"] else "-"
            print(f"{i:2d} {o['name']:12s} {'S' if o['side'] else '.'} ang {o['amin']:6.1f}..{o['amax']:6.1f} sw {o['swing']:5.1f} lag {o['lag']:+d}({o['lagc']:.2f}) "
                  f"3d {o['b3'][0]:5.1f}..{o['b3'][1]:5.1f} spl {o['spl'][0]:5.1f}..{o['spl'][1]:5.1f} | turn st {o['st'][0]:5.1f}@{o['st'][1]:+d} sp {o['sp'][0]:5.1f}@{o['sp'][1]:+d} all {o['allr'][0]:5.1f}@{o['allr'][1]:+d} "
                  f"| down {dn} | fist-head {o['chin']:+.2f} tipb {o['tipb']:+.2f} below {o['below']:5.1f} | clr {c} | w {o['w']:.2f} tilt {o['tilt'][0]:5.1f}..{o['tilt'][1]:5.1f}")


if __name__ == '__main__': main()
