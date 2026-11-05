# Tests for cut_check.py's dip hand-back rule: tiny synthetic --cutlog logs in a temp dir.
# Run: python tools/experience/test_cut_check.py
import os
import subprocess
import sys
import tempfile

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cut_check.py")
tmp = tempfile.mkdtemp()


def frame(t, phase, pos, hud, cap, dip, scr, shot=-1, vfov=40.0):
    her = "root=0.000,0.000,0.000 head=0.000,1.600,0.000 hand=0.300,1.000,0.000" if scr else "her=-"
    s = f" scr={scr}" if scr else ""
    d = f" dip={dip:0.2f}" if dip is not None else ""
    return (f"CUTLOG c99 t={t:0.3f} dt=0.0167 phase={phase} shot={shot} pos={pos[0]:0.3f},{pos[1]:0.3f},{pos[2]:0.3f} fwd=0.0000,-0.5000,-0.8660 "
            f"vfov={vfov:0.00} hud={hud:0.2f} cap={cap}{d} {her}{s}")


def dip_log(with_dip):
    """A film's last frame 126 m off held 0.4 s, black, the play camera placed at black, a 0.5 s rise, control."""
    out, t, dt = [], -1.0, 1 / 60
    far, play = (126, 20, 0), (0, 9, 14)
    while t < 0: out.append(frame(t, "cine", far, 0, 1, 0 if with_dip else None, None, shot=7)); t += dt
    out.append("CUTSEAM c99 dur=1.00 metres=126.00 degrees=40.0 skipped=False arc=False" + (" dip=True" if with_dip else ""))
    s = 0.0
    while s < 1.0:
        black = (s / 0.4) ** 2 if s < 0.4 else 1 if s < 0.5 else 1 - (lambda r: r * r * (3 - 2 * r))(min(1, (s - 0.5) / 0.5))
        pos = far if s < 0.4 else play
        vfov_scr = "0.5000,0.3000,0.5000,0.6000" if s >= 0.4 else "9,9,9,9"   # (her behind the lens of the far frame)
        hud = 0 if s < 0.65 else min(1, (s - 0.65) / 0.5)
        out.append(frame(t, "seam", pos, hud, 1, black if with_dip else None, vfov_scr, vfov=40.0 if s < 0.4 else 34.0))
        t += dt; s += dt
    out.append("CUTCONTROL c99")
    for _ in range(200):
        out.append(frame(t, "play", play, min(1, 0.7 + (t - 1) / 0.5), 0, 0 if with_dip else None, "0.5000,0.3000,0.5000,0.6000", vfov=34.0)); t += dt
    return "\n".join(out) + "\n"


def run(text):
    p = os.path.join(tmp, f"log{len(os.listdir(tmp))}.txt")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, CHECK, p], capture_output=True, text=True)
    return r.returncode, r.stdout


code, out = run(dip_log(True))
assert code == 0 and out.startswith("PASS") and " dip black=" in out, out
code, out = run(dip_log(False))   # the same cut without the dip: a 126 m jump, her out of frame
assert code == 1 and "camera jump" in out and " dip" not in out.split("\n")[0], out
print("cut_check dip tests: 2 passed")
