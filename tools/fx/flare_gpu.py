"""GPU per beat for a Flare clip shot with --perf NAME (godot/.shots/perf/NAME.csv, t = frame/60 under --fixed-fps):
mean GPU ms over press-60..press, the stop (press+1..release), the band (main blow..+22 f), and +60..+120 f after the blow.
  python tools/fx/flare_gpu.py NAME [NAME ...]   (NAME is both the clip folder and the perf name)
A live run (no movie, vsync off: FlareFx prints 'flare perf press/release/blow t S' on the perf clock under --perf) is
read the same way when its log has those lines: windows in seconds (pre 1 s, the stop, the band 0.37 s from the blow).
  python tools/fx/flare_gpu.py --run NAME --flare ID --quick CALLING [--time day --cast 3] [--godot-args "..."]
starts that live run itself (windowed 1920x1080, the godot turn taken), leaving OUT/NAME/log.txt and the perf CSV."""
import csv, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7")
if len(sys.argv) > 1 and sys.argv[1] == "--run":
    import argparse, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--flare", required=True)
    ap.add_argument("--quick", default="warden"); ap.add_argument("--time", default="night"); ap.add_argument("--cast", type=float, default=50)
    ap.add_argument("--godot-args", default="")
    a = ap.parse_args()
    GODOT = "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
    TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
    zone = "verge" if a.time == "day" else "arena"
    extra = (["--horde", "25", "--dist", "4", "--spread", "8", "--no-spawn"] if zone == "verge" else []) + a.godot_args.split()
    warm = max(2.0, a.cast - 8)
    cmd = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--", "--quick", a.quick, "--zone", zone, "--offer", "0",
           "--auto", "idle", "--flare", a.flare, "--cast", str(a.cast), "--time", a.time, "--clip",
           "--perf", a.run, "--perf-warm", f"{warm:.0f}", "--perf-for", "22"] + extra
    ov = ROOT / "godot" / "override.cfg"
    if ov.exists(): ov.unlink()
    (OUT / a.run).mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, TURN, "take", "godot", f"flare-h7: gpu {a.run}", "--wait", "600"], check=True)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=400)
        (OUT / a.run / "log.txt").write_text(r.stdout + chr(10) + r.stderr, encoding="utf-8")
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", f"flare-h7: gpu {a.run}"])
    sys.argv = [sys.argv[0], a.run]
for n in sys.argv[1:]:
    log = (OUT / n / "log.txt").read_text(encoding="utf-8", errors="replace")
    lp = re.search(r"flare perf press t ([\d.]+)", log)
    if lp:
        rows = list(csv.DictReader(open(ROOT / "godot" / ".shots" / "perf" / f"{n}.csv")))
        tp = float(lp.group(1))
        tr = float(m.group(1)) if (m := re.search(r"flare perf release t ([\d.]+)", log)) else tp + 0.37
        tb = float(m.group(1)) if (m := re.search(r"flare perf blow t ([\d.]+)", log)) else tr
        def wins(a, b):
            v = [float(r["gpu"]) for r in rows if a <= float(r["t"]) < b]
            return (sum(v) / len(v) if v else float("nan")), len(v)
        pre, npre = wins(tp - 1.0, tp)
        st, nst = wins(tp + 0.005, tr); bd, nbd = wins(tb, tb + 0.37); af, _ = wins(tb + 1.0, tb + 2.0)
        print(f"{n} (live): gpu pre {pre:.2f} ms ({npre} f), stop {st - pre:+.2f} ({nst} f), band {bd - pre:+.2f} ({nbd} f), after {af - pre:+.2f} (deltas, ms)")
        continue
    pf = int(re.search(r"flare press frame (\d+)", log).group(1))
    rl = re.search(r"flare release frame (\d+)", log); rel = int(rl.group(1)) if rl else pf + 22
    bm = re.search(r"main \S+ at \+([\d.]+) s real", log); blow = pf + round(float(bm.group(1)) * 60) if bm else rel
    rows = list(csv.DictReader(open(ROOT / "godot" / ".shots" / "perf" / f"{n}.csv")))
    def win(a, b):
        v = [float(r["gpu"]) for r in rows if a <= round(float(r["t"]) * 60) < b]
        return sum(v) / len(v) if v else float("nan")
    pre = win(pf - 60, pf)
    print(f"{n}: gpu pre {pre:.2f} ms, stop {win(pf + 1, rel) - pre:+.2f}, band {win(blow, blow + 22) - pre:+.2f}, after {win(blow + 60, blow + 120) - pre:+.2f} (deltas, ms)")
