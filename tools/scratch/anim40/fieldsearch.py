"""Score hip-socket rows on sockfield_<kind>.npz (animation 44, solver idle 2): instant, for a grid search; the winners
go to socktry.py (armscheck's exact measure). Rows as socksearch.py's docstring says.
usage: python fieldsearch.py axe|wand '--grid={"th":[..],...}' [--top=20] [--air=0.008] [--sort=r]"""
import json, sys, math, itertools
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator as RGI

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
import armscheck as ac  # noqa

kind = sys.argv[1]
opt = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--") and "=" in a)
F = np.load(Path(__file__).with_name(f"sockfield_{kind}.npz"))
ax = (F["x"], F["y"], F["z"])
fld = {k: RGI(ax, F[k], bounds_error=False, fill_value=9.0) for k in ("skin", "outfit", "hand_idle", "hand_run", "hand_sprint")}
KEY = {"axe": "viking_axe@hand_r", "wand": "wand@hand_r"}[kind]
raw = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"][KEY]
M0 = np.vstack([np.array(raw["mount"], float), [0, 0, 0, 1]])
v = ac.sample(np.array(raw["v"], float), np.array(raw["t"], int), spacing=0.01, cap=3000)
u = (np.linalg.inv(M0) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
head = u[:, 1] > (0.42 if kind == "axe" else 0.20)
air = float(opt.get("air", 0.008))


def unit(a):
    return a / np.linalg.norm(a)


def rowfor(th, r, hy, tb, tt, ph=0, spin=0):
    t = math.radians(th)
    rad = np.array([-math.sin(t), 0, math.cos(t)])
    tan = unit(np.cross([0, 1, 0], rad))
    if np.dot(tan, [0, 0, -1]) < 0:
        tan = -tan
    H = np.array([0, hy, 0]) + r * rad
    if kind == "axe":
        foot = -np.array([0, 1, 0]) * math.cos(math.radians(tb)) + rad * math.sin(math.radians(tb))
        foot = unit(foot + tan * math.tan(math.radians(tt)))
        shaft = -foot
        p = math.radians(ph)
        want = unit(np.array([0, 0, -1]) * math.cos(p) + np.array([-1, 0, 0]) * math.sin(p))
        third = unit(want - shaft * want.dot(shaft))
        thick = np.cross(third, shaft)
        at = H - 0.56 * shaft
    else:
        shaft = unit(np.array([0, -math.cos(math.radians(tb)), -math.sin(math.radians(tb))]) + rad * math.tan(math.radians(tt)))
        thick = unit(-rad - shaft * (-rad).dot(shaft))
        third = np.cross(shaft, thick)
        at = H
    return at, shaft, thick, third


def place(at, shaft, thick, third, left):
    M = np.diag([-1, 1, 1]) if left else np.eye(3)
    return u @ np.column_stack([M @ third, M @ shaft, M @ thick]).T + M @ at


def score(row):
    res = {}
    for left in ((False, True) if kind == "axe" else (False,)):
        Q = place(*row, left)
        res["L" if left else "R"] = dict(
            skin=float(fld["skin"](Q).min()), outfit=float(fld["outfit"](Q).min()),
            **{f"h{p}": float(fld[f"hand_{p}"](Q[head]).min()) for p in ("idle", "run", "sprint")},
            **{f"p{p}": float(fld[f"hand_{p}"](Q).min()) for p in ("idle", "run", "sprint")})
    return res


if __name__ == "__main__":
    grid = json.loads(opt["grid"])
    out = []
    for vals in itertools.product(*grid.values()):
        p = dict(zip(grid.keys(), vals))
        row = rowfor(**p)
        sc = score(row)
        hi = min(s["hidle"] for s in sc.values()); hr = min(min(s["hrun"], s["hsprint"]) for s in sc.values())
        pr = min(min(s["prun"], s["psprint"]) for s in sc.values())
        sk = min(s["skin"] for s in sc.values())
        ok = int(hi >= 0.10) + int(hr >= 0.04) + int(sk >= air) + (int(pr >= 0.04) if kind == "wand" else 0)
        out.append((ok, sk, p, sc, row))
    key = opt.get("sort")
    tuck = lambda p: p["r"] + 0.002 * abs(p["tb"]) + 0.0015 * abs(p["tt"])
    out.sort(key=lambda o: (-o[0], tuck(o[2]) if key == "tuck" else (o[2][key] if key else -o[1])))
    print(f"{sum(o[0] == max(x[0] for x in out) for o in out)} of {len(out)} at the best ok count {max(x[0] for x in out)}")
    for ok, sk, p, sc, row in out[: int(opt.get("top", 20))]:
        print(ok, p, " | ".join(f"{k}: skin {1000 * s['skin']:+.0f} outfit {1000 * s['outfit']:+.0f} head i/r/s {1000 * s['hidle']:.0f}/{1000 * s['hrun']:.0f}/{1000 * s['hsprint']:.0f} piece {1000 * s['pidle']:.0f}/{1000 * s['prun']:.0f}/{1000 * s['psprint']:.0f}" for k, s in sc.items()))
        print("   row", ";".join(",".join(f"{x:.3f}" for x in a) for a in row[:3]))
