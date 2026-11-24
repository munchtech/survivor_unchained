"""The standing memory check (the tester lane, 23 Nov: a tester's next4 reached 6.8 GB of RAM and crashed; the owner: "yeah we
really need to optimize don't we - thats really too much"). Runs an exported build for SECONDS on one route, samples it from
outside (tools/perf/memrun.py) and fails if it is over budget:

    python tools/perf/memcheck.py EXE [den|town|denloop ...] [--seconds 150] [--out DIR]

denloop (24 Nov) goes round the den about 16 times (960 s) and prints each loop's RAM and VRAM; it fails if they climb.

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
    # The den again and again, as a tester goes round it (the coordinator, 24 Nov): each map cleared at 30 s of it, left by its
    # way out at 45 s, its page read and Confirmed, a fresh den (src/Game/Game.cs --loop-maps); split per loop below.
    "denloop": ["--quick", "warden", "--sex", "female", "--zone", "map", "--dungeon", "hollow", "--veteran", "9", "--seed", "1",
                "--auto", "idle", "--clear", "30", "--leave", "45", "--loop-maps"],
    "town": ["--quick", "warden", "--sex", "female", "--zone", "waystation", "--veteran", "9", "--seed", "1"],
}
BUDGET = {  # MB
    "den": {"ws": 3072, "gpu": 3072, "private": 8192},
    "town": {"ws": 4096, "gpu": 3072, "private": 8192},
}
BUDGET["denloop"] = BUDGET["den"]
# (24 Nov, session 3: on D3D12 the loop medians rise for ~8 loops, then hold: L3, 16 loops, RAM 3324 -> ~3850 from loop 9 on,
# VRAM ~3880-3940; a 7-loop run reads only the rise. So the run is 16 loops and growth is judged on its second half, and the last
# loop's median may stand at most LOOP_RISE_CAP over the first's (the coordinator, 24 Nov: a plateau check alone hides a slow
# leak or a big one-off rise). UNPROVEN reading of the rise: the engine's upload staging pools fill to their caps and are never
# given back (Godot 4.7.2 rendering_device.cpp: each transfer worker's staging buffer grows to the next power of two of its
# biggest single upload, one worker per CPU thread, freed at shutdown; the frame staging blocks up to
# rendering/rendering_device/staging_buffer/max_size_mb), with the D3D12 driver's heaps; on Vulkan RAM rose +10 MB a loop
# (L1_vk), and GPU shared memory stepped +64/+128 MB at some loops on D3D12 only.)
LOOP_SECS = 960.0  # denloop's default run: about 16 full loops (a loop is ~55-60 s: 45 s in the den, the page, the load)
LOOPS_MIN = 12
LOOP_RISE_CAP = 700.0  # MB, the last loop's median over the first's, RAM and VRAM each
LOOP_GROWTH = 20.0  # MB a loop: the loop medians' RAM and VRAM over the second half of the loops, least-squares
# The game's own window: a run with args other than --shot/--perf goes fullscreen at the monitor's size (src/Game/Settings.cs
# ApplyWindow), as a tester's does; on this machine that is 2560x1440, stricter than a tester's 1080p (23 Nov: GPU dedicated
# 3,469 MB at 1440p vs 3,180-3,250 at 1080p). --resolution alone does not change it (a vram probe, 8d9cda78b).
# (MEMCHECK_ENGINE / MEMCHECK_GAME: extra engine / game args, space-split, for a leg: e.g. MEMCHECK_ENGINE="--rendering-driver vulkan",
# MEMCHECK_GAME="--mem-fresh"; the tester lane's loop check, 24 Nov)
ENGINE = os.environ.get("MEMCHECK_ENGINE", "").split()
GAME = os.environ.get("MEMCHECK_GAME", "").split()
GROWTH = 20.0  # MB/min, the working set over the second half
SETTLE = 45.0  # s


def check(exe, route, secs, out):
    os.environ.setdefault("MEMRUN_GPU_EVERY", "5")
    memrun.GPU_EVERY = int(os.environ["MEMRUN_GPU_EVERY"])
    rows, exited = memrun.run(os.path.join(out, route), secs, [exe] + ENGINE + ["--"] + ROUTES[route] + ["--mem-log", os.environ.get("MEMCHECK_MEMLOG", "10")] + GAME)
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
    checks = [("RAM", ram < b["ws"]), ("VRAM", gpu < b["gpu"]), ("commit", pv < b["private"])]
    if route == "denloop":
        checks += loops(rows, os.path.join(out, route, "log.txt"))
    else:
        checks.append(("growth", grow < GROWTH))
    fails = [n for n, ok in checks if not ok]
    print(f"memcheck {route}: {'PASS' if not fails else 'FAIL ' + ', '.join(fails)}; RAM (private - GPU dedicated) peak {ram} / {b['ws']} MB (working set peak {ws}), "
          f"VRAM (GPU dedicated) peak {gpu} / {b['gpu']} MB, commit (private) peak {pv} / {b['private']} MB, "
          f"growth {grow:+.1f} / {GROWTH:+.0f} MB/min ({len(rows)} samples, {rows[-1][0]:.0f} s; {os.path.join(out, route)})", flush=True)
    return 1 if fails else 0


def loops(rows, log):
    """Per loop of the denloop route: its samples are those logged before its "auto: map over #N" line and after the last
    one's (memrun's log_bytes column). Prints each loop's RAM and VRAM (median and peak at the GPU-read samples) and fails
    "loop growth" if, past the first loop (its warm-up), the medians climb by LOOP_GROWTH MB a loop or more, or if fewer
    than 4 loops ended."""
    data = open(log, "rb").read()
    ends, at = [], 0
    while (i := data.find(b"auto: map over #", at)) >= 0:
        at = data.find(b"\n", i) + 1 or len(data); ends.append(at)
    per, lo = [], 0
    for n, hi in enumerate(ends, 1):
        g = [r for r in rows if len(r) > 5 and lo <= r[5] < hi and r[3]]
        lo = hi
        if not g:
            continue
        ram = sorted(r[2] - r[3] for r in g); vr = sorted(r[3] for r in g)
        per.append((n, ram[len(ram) // 2], ram[-1], vr[len(vr) // 2], vr[-1]))
        print(f"  loop {n}: RAM median {per[-1][1]} peak {per[-1][2]} MB, VRAM median {per[-1][3]} peak {per[-1][4]} MB ({len(g)} samples)")
    def slope(col, p=None):
        p = per[1:] if p is None else p
        if len(p) < 2: return 0.0
        mx = sum(q[0] for q in p) / len(p); my = sum(q[col] for q in p) / len(p)
        return sum((q[0] - mx) * (q[col] - my) for q in p) / sum((q[0] - mx) ** 2 for q in p)
    sr, sv = slope(1), slope(3)
    late = per[len(per) // 2:]
    lr, lv = slope(1, late), slope(3, late)
    print(f"  loops ended {len(ends)}; past the first, RAM {sr:+.0f} MB a loop, VRAM {sv:+.0f} MB a loop; "
          f"the second half (loops {late[0][0] if late else '-'}-{late[-1][0] if late else '-'}), RAM {lr:+.0f}, VRAM {lv:+.0f} (limit {LOOP_GROWTH:+.0f})")
    rise_r = per[-1][1] - per[0][1] if per else 0; rise_v = per[-1][3] - per[0][3] if per else 0
    print(f"  the last loop over the first: RAM {rise_r:+d} MB, VRAM {rise_v:+d} MB (cap {LOOP_RISE_CAP:+.0f})")
    return [("loops", len(ends) >= LOOPS_MIN), ("loop growth", lr < LOOP_GROWTH and lv < LOOP_GROWTH),
            ("loop rise", rise_r <= LOOP_RISE_CAP and rise_v <= LOOP_RISE_CAP)]


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        print(__doc__); sys.exit(2)
    exe = os.path.abspath(a.pop(0))
    secs = float(a[a.index("--seconds") + 1]) if "--seconds" in a else None
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(exe), ".memcheck")
    routes = [r for r in a if r in ROUTES] or ["den"]
    sys.exit(max(check(exe, r, secs or (LOOP_SECS if r == "denloop" else 150.0), out) for r in routes))


if __name__ == "__main__":
    main()
