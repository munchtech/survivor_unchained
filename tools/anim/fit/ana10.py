"""ana10.py LEG lo hi: the GAME's drawn blade per frame (views.log at $LOG): yaw/f, moving, weight, screen angle,
tip px under the lower boot, shown fraction, world pitch below horizontal, tip height over the floor, clip's pitch."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from simlog import load, jac, proj
import m14
d = os.environ["LOG"]; R = load(d); rows, ppm = m14.load(d)
floor = min(min(r["body"][4][1], r["body"][5][1]) for r in R.values()) - 0.03
L, lo, hi = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]); s = 60 + 60 * L
for k in range(s + lo, s + hi + 1):
    if k not in R or k not in rows: continue
    r = R[k]; F = m14.frame(rows[k], ppm); dd = (r["tw"] - r["gw"]) / r["L"]
    jx, jy = jac(r["gw"], r["O"]); n = math.sqrt((jx @ jx + jy @ jy) / 2)
    shown = math.hypot(jx @ dd, jy @ dd) / n
    pitch = math.degrees(math.asin(max(-1, min(1, -dd[1])))); p0 = math.degrees(math.asin(max(-1, min(1, -r["b0"][1]))))
    yaw = abs((r["face"] - R[k-1]["face"] + 180) % 360 - 180) if k - 1 in R else 0
    dh = math.degrees(math.atan2(dd[0], dd[2])); print(f"hd {dh:6.1f} ", end=""); print(f"{k-s:+3d} yaw {yaw:5.1f} mov {r['mov']:.2f} w {r['w']:.2f} a {F['a']:6.1f} under {F['tipy']-F['low']:5.0f}px shown {shown:.2f} pitch {pitch:5.1f} (clip {p0:5.1f}) tipH {r['tw'][1]-floor:5.2f} gripH {r['gw'][1]-floor:4.2f} loc {r['tw'][1]-min(r['body'][4][1], r['body'][5][1])+0.03:5.2f} {r['gw'][1]-min(r['body'][4][1], r['body'][5][1])+0.03:4.2f} tilt {r['tilt']:6.1f} inw {r['inw']:6.1f}")
