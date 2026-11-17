"""t10.py SHOTDIR..: judge r9's targets on the GAME's blade, every leg, windows +44..+59 and -10..+6.
T1 cane: |a| < 20 and tip > 4 px under the lower boot (exempt, listed with *, where shown < 0.25 of full length).
T2 world guard: pivot frames (her yaw moving > 1 deg/f) with |a| < 30: pitch <= 55 deg below level or tip >= 0.30 m up.
T3 snap: a frame step > 25 deg unless shown <= 0.5 on both frames; spike: step > 12 and > 2x both neighbours' steps."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from simlog import load, jac
import m14
W = lambda d: (d + 180) % 360 - 180
for d in sys.argv[1:]:
    R = load(d); rows, ppm = m14.load(d)
    floor = min(min(r["body"][4][1], r["body"][5][1]) for r in R.values()) - 0.03
    info = {}
    for k in R:
        if k not in rows: continue
        r = R[k]
        try: F = m14.frame(rows[k], ppm)
        except Exception: continue
        if F.get('a') is None: continue
        dd = (r["tw"] - r["gw"]) / r["L"]; jx, jy = jac(r["gw"], r["O"]); n = math.sqrt((jx @ jx + jy @ jy) / 2)
        info[k] = dict(a=F['a'], under=F['tipy'] - F['low'], shown=math.hypot(jx @ dd, jy @ dd) / n,
                       pitch=math.degrees(math.asin(max(-1, min(1, -dd[1])))), tipH=r["tw"][1] - floor,
                       yaw=abs(W(r["face"] - R[k-1]["face"])) if k - 1 in R else 0.)
    print("==", os.path.basename(d.rstrip("/")))
    tot = [0, 0, 0, 0]
    for i in range(16):
        s = 60 + 60 * i; ks = [k for k in list(range(s - 10, s + 7)) + list(range(s + 44, s + 60)) if k in info]
        t1 = []; t2 = []; t3 = []; t1p = []
        for k in ks:
            q = info[k]
            if abs(q['a']) < 20 and q['under'] > 4: t1.append(f"{k-s:+d}{'*' if q['shown'] < 0.25 else ''}")
            if q['shown'] >= 0.6 and q['under'] > 8 and abs(q['a']) < 28: t1p.append(k - s)
            if q['yaw'] > 1 and abs(q['a']) < 30 and q['pitch'] > 55 and q['tipH'] < 0.30: t2.append(k - s)
            p = info.get(k - 1)
            if p:
                st = abs(W(q['a'] - p['a']))
                if st > 25 and not (q['shown'] <= 0.5 and p['shown'] <= 0.5): t3.append(f"{k-s:+d}:{st:.0f}")
                pp, nx = info.get(k - 2), info.get(k + 1)
                if pp and nx:
                    s0, s2 = abs(W(p['a'] - pp['a'])), abs(W(nx['a'] - q['a']))
                    if st > 12 and st > 2 * s0 and st > 2 * s2 and not (q['shown'] <= 0.5 and p['shown'] <= 0.5): t3.append(f"{k-s:+d}^{st:.0f}")
        tot[0] += len([x for x in t1 if not x.endswith('*')]); tot[1] += len(t2); tot[2] += len(t3); tot[3] += len(t1p)
        print(f"{i:2d} {m14.LEGS[i]:12s} T1 {' '.join(t1) or '-'} | T2 {t2 or '-'} | T3 {' '.join(t3) or '-'} | T1' {t1p or '-'}")
    print(f"   totals: T1 {tot[0]} (non-exempt)  T2 {tot[1]}  T3 {tot[2]}  T1' {tot[3]}")
