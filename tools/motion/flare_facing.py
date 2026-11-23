"""Measure where the Flare (the Long Cut) faces: the cursor, or her travel / her facing (--moves12 f01 / f02, godot/src/Game/MoveShots.Flare.cs).

  python tools/motion/flare_facing.py [TAG] [--exe PATH]

Three legs, one godot turn (tools/turn.py) given back in a finally: f01 with --move-new, f02 with --move-new, f01 without it (the old
movement). Each runs the game in her den (Warden, hollow dungeon on a test map, boss-mid, no foes (cleared once by the harness: --no-foes also releases the dummies every frame), facing mode always, no cinematics),
8 Long Cut presses with the cursor on bearing 45 i deg and (f01) the keys held toward that bearing + 135. Logs: godot/.shots/flare_facing/TAG/LEG/log.txt
(git-ignored). Env FLARE_EXTRA adds game flags (e.g. "--facing-mode skill", which overrides the boot's `--facing-mode always`).
--exe PATH runs an exported SurvivorUnchained.exe instead of the editor binary (same flags, no --path). Bearings: atan2(dx, dz) in
degrees, 0 = +Z (toward the camera), 90 = +X. err = the largest of |press - cursor|, |seam - cursor|, |body - cursor| (wrapped to +-180);
PASS = err <= 5 on all 8 rows.
"""
import os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
FPS = 60
LEGS = [("f01_new", "f01", True), ("f02_new", "f02", True), ("f01_old", "f01", False)]
LINE = re.compile(r"FLAREFACE i=(\d+) cursor=(\S+) travel=(\S+) press=(\S+) line=(\S+) seam=(\S+) sweep=(\S+) body=(\S+) hitC=(\S+) hitT=(\S+)")


def main():
    args = sys.argv[1:]
    exe = None
    if "--exe" in args:
        k = args.index("--exe")
        exe = args[k + 1]
        del args[k:k + 2]
    tag = args[0] if args else "run"
    ov = ROOT / "godot" / "override.cfg"
    if ov.exists():
        ov.unlink()
    label = os.environ.get("TURN_LABEL", "flare facing")
    subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "1800"], check=True)
    legs = LEGS
    if os.environ.get("FLARE_LEGS"):
        legs = [l for l in LEGS if l[0] in os.environ["FLARE_LEGS"].split(",")]
    try:
        for leg in legs:
            run_leg(tag, exe, *leg)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", label])


def wrap(d):
    return (d + 180) % 360 - 180


def run_leg(tag, exe, leg, take, move_new):
    out = ROOT / "godot" / ".shots" / "flare_facing" / tag / leg
    out.mkdir(parents=True, exist_ok=True)
    boot = ["--quick", "warden", "--zone", "map", "--dungeon", "hollow", "--seed", "1", "--at", "boss-mid", "--at-off", "0,0",
            "--facing-mode", "always", "--nocine", "--flare", "the_long_cut"]
    if move_new:
        boot.append("--move-new")
    boot += os.environ.get("FLARE_EXTRA", "").split()
    tail = ["--moves12", take, "--moves12-input", "kbm", "--moves12-out", str(out)]
    common = ["--resolution", "1920x1080", "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", "9000"]
    head = [exe] if exe else [GODOT, "--path", str(ROOT / "godot")]
    gargs = head + common + ["--"] + boot + tail
    print("RUN", " ".join(gargs), flush=True)
    with open(out / "log.txt", "w", encoding="utf-8", errors="replace") as lf:
        r = subprocess.run(gargs, stdout=lf, stderr=subprocess.STDOUT)
    log = (out / "log.txt").read_text(encoding="utf-8", errors="replace")
    rows = [m.groups() for m in LINE.finditer(log)]
    print(f"\n== {leg} ({take}{' --move-new' if move_new else ' old movement'}{' ' + os.environ['FLARE_EXTRA'] if os.environ.get('FLARE_EXTRA') else ''}) exit {r.returncode}, {len(rows)} presses ==")
    print(f"{'i':>2} {'cursor':>6} {'travel':>6} {'press':>6} {'line':>6} {'seam':>6} {'sweep':>6} {'body':>6} {'hitC':>7} {'hitT':>7} {'err':>6}")
    npass = oncursor = 0
    for g in rows:
        i, cur, trv, pr, ln, se, sw, bd, hc, ht = g
        errs = []
        for v in (pr, se, bd):
            errs.append(abs(wrap(float(v) - float(cur))) if v != "-" and cur != "-" else 999.0)
        err = max(errs)
        npass += err <= 5
        oncursor += float(hc) > 0
        print(f"{i:>2} {cur:>6} {trv:>6} {pr:>6} {ln:>6} {se:>6} {sw:>6} {bd:>6} {float(hc):>7.0f} {float(ht):>7.0f} {err:>6.1f}")
    print(f"{leg}: {'PASS' if len(rows) == 8 and npass == 8 else 'FAIL'} ({npass}/8 rows err <= 5); hit on cursor line: {oncursor}/8", flush=True)


if __name__ == "__main__":
    main()
