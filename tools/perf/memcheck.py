"""The standing memory check (the tester lane, 23 Nov: a tester's next4 reached 6.8 GB of RAM and crashed; the owner: "yeah we
really need to optimize don't we - thats really too much"). Runs an exported build for SECONDS on one route, samples it from
outside (tools/perf/memrun.py) and fails if it is over budget:

    python tools/perf/memcheck.py EXE [den|town ...] [--seconds 150] [--out DIR]

Budgets (the coordinator, 23 Nov): RAM (den < 3 GB, town < 4 GB), read as commit less the card's own memory (private bytes
minus GPU dedicated, at the samples that read the GPU): the working set is the same number on a quiet machine (den, tester1:
9,170 ws vs 12,700 - 3,490), but Windows trims a working set under RAM pressure (cold1, 23 Nov: 7,624 -> 197 MB in 35 s while
private stood at 12 GB), so a working set alone can pass a build that is over; VRAM = GPU dedicated < 3 GB (a 4 GB card:
inference from shipped min specs, not measured on one); commit (private bytes) < 8 GB (a small page file dies on commit, and on
this NVIDIA/WDDM machine private bytes include the card's memory: a probe's 1.6 GB of textures added 1.8 GB private, 0 working
set). Flat: private bytes' growth over the run's second half under +20 MB/min. Peaks are read after the first 45 s (the
load: the warm-up's driver work and loading's buffers come and go). Exit 0 = every route passed, 1 = a route over budget,
2 = the game did not run. Take a godot turn first (tools/turn.py run); another Godot on the machine does not change a
process's own numbers, but heavy RAM pressure trims working sets, so a PASS under pressure is still a PASS, a FAIL is
rerun quiet before it is believed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memrun  # noqa: E402

ROUTES = {
    "den": ["--quick", "warden", "--sex", "female", "--zone", "map", "--dungeon", "hollow", "--veteran", "9", "--seed", "1"],
    "town": ["--quick", "warden", "--sex", "female", "--zone", "waystation", "--veteran", "9", "--seed", "1"],
}
BUDGET = {  # MB
    "den": {"ws": 3072, "gpu": 3072, "private": 8192},
    "town": {"ws": 4096, "gpu": 3072, "private": 8192},
}
GROWTH = 20.0  # MB/min, the working set over the second half
SETTLE = 45.0  # s


def check(exe, route, secs, out):
    os.environ.setdefault("MEMRUN_GPU_EVERY", "5")
    memrun.GPU_EVERY = int(os.environ["MEMRUN_GPU_EVERY"])
    rows, exited = memrun.run(os.path.join(out, route), secs, [exe, "--"] + ROUTES[route] + ["--mem-log", "10"])
    late = [r for r in rows if r[0] >= SETTLE]
    if not late or exited is not None:
        print(f"memcheck {route}: NO RUN (exit {exited}, {len(rows)} samples; {os.path.join(out, route, 'log.txt')})")
        return 2
    b = BUDGET[route]
    ws = max(r[1] for r in late); pv = max(r[2] for r in late); gpu = max((r[3] or 0) for r in late)
    ram = max((r[2] - r[3] for r in late if r[3]), default=0)
    if not ram:
        print(f"memcheck {route}: NO GPU SAMPLE (the GPU counters read nothing; {os.path.join(out, route)})")
        return 2
    grow = memrun.slope_mb_min(rows, 2)
    fails = [n for n, ok in (("RAM", ram < b["ws"]), ("VRAM", gpu < b["gpu"]), ("commit", pv < b["private"]), ("growth", grow < GROWTH)) if not ok]
    print(f"memcheck {route}: {'PASS' if not fails else 'FAIL ' + ', '.join(fails)}; RAM (private - GPU dedicated) peak {ram} / {b['ws']} MB (working set peak {ws}), "
          f"VRAM (GPU dedicated) peak {gpu} / {b['gpu']} MB, commit (private) peak {pv} / {b['private']} MB, "
          f"growth {grow:+.1f} / {GROWTH:+.0f} MB/min ({len(rows)} samples, {rows[-1][0]:.0f} s; {os.path.join(out, route)})", flush=True)
    return 1 if fails else 0


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        print(__doc__); sys.exit(2)
    exe = os.path.abspath(a.pop(0))
    secs = float(a[a.index("--seconds") + 1]) if "--seconds" in a else 150.0
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(exe), ".memcheck")
    routes = [r for r in a if r in ROUTES] or ["den"]
    sys.exit(max(check(exe, r, secs, out) for r in routes))


if __name__ == "__main__":
    main()
