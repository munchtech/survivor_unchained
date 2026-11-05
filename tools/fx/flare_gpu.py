"""GPU per beat for a Flare clip shot with --perf NAME (godot/.shots/perf/NAME.csv, t = frame/60 under --fixed-fps):
mean GPU ms over press-60..press, the stop (press+1..release), the band (main blow..+22 f), and +60..+120 f after the blow.
  python tools/fx/flare_gpu.py NAME [NAME ...]   (NAME is both the clip folder and the perf name)"""
import csv, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7")
for n in sys.argv[1:]:
    log = (OUT / n / "log.txt").read_text(encoding="utf-8", errors="replace")
    pf = int(re.search(r"flare press frame (\d+)", log).group(1))
    rl = re.search(r"flare release frame (\d+)", log); rel = int(rl.group(1)) if rl else pf + 22
    bm = re.search(r"main \S+ at \+([\d.]+) s real", log); blow = pf + round(float(bm.group(1)) * 60) if bm else rel
    rows = list(csv.DictReader(open(ROOT / "godot" / ".shots" / "perf" / f"{n}.csv")))
    def win(a, b):
        v = [float(r["gpu"]) for r in rows if a <= round(float(r["t"]) * 60) < b]
        return sum(v) / len(v) if v else float("nan")
    pre = win(pf - 60, pf)
    print(f"{n}: gpu pre {pre:.2f} ms, stop {win(pf + 1, rel) - pre:+.2f}, band {win(blow, blow + 22) - pre:+.2f}, after {win(blow + 60, blow + 120) - pre:+.2f} (deltas, ms)")
