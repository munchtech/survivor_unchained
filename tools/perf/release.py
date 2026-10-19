"""Measured runs in the Release build (export preset "Windows (perf)": the release
template, the C# compiled ExportRelease, and the developer's switches read).

    python tools/perf/release.py export                      (builds release/godot/perf/)
    python tools/perf/release.py run OUT NAME RES QUALITY [game args ...]
    python tools/perf/release.py windows OUT NAME             (per-window table with the stage)

`run` starts the exported game, waits for the GPU to be quiet (tools/perf/run.py's
check), and copies NAME.json/.csv and the log into OUT; driver.log gets the line.
Take a godot turn first (tools/turn.py). docs/handoff/performance.md has the why.
"""
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time
try:
    import psutil
except ImportError:
    psutil = None

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as perfrun  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
EXE_DIR = os.path.join(ROOT, "release", "godot", "perf")
EXE = os.path.join(EXE_DIR, "SurvivorUnchained.exe")
SHOTS = os.path.join(EXE_DIR, ".shots", "perf")
STAGES = ["Wake", "Rising", "Road", "Ambush", "Road2", "Post", "Barrow", "ToFord", "Intro", "Boss", "Victory", "Dawn", "Exit"]


def export():
    g = os.path.join(ROOT, "godot")
    os.makedirs(EXE_DIR, exist_ok=True)
    with open(os.path.join(ROOT, "release", "godot", "perf.log"), "w", encoding="utf-8") as f:
        subprocess.run([perfrun.GODOT, "--headless", "--path", g, "--export-release", "Windows (perf)", EXE], stdout=f, stderr=subprocess.STDOUT)
    print("exported" if os.path.exists(EXE) else "no export (release/godot/perf.log)")


def run(out, name, res, quality, args):
    os.makedirs(out, exist_ok=True)
    busy, mem, rivals = perfrun.quiet(float(os.environ.get("PERF_QUIET", "1200")))
    cmd = [EXE, "--resolution", res, "--", *args, "--quality", quality, "--perf", name]
    line = f"{name}: GPU before {busy}% {mem} MB, {rivals} other games; {' '.join(cmd[1:])}"
    print(line, flush=True)
    t0 = time.time()
    with open(os.path.join(out, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(cmd, cwd=EXE_DIR, stdout=lf, stderr=subprocess.STDOUT)
        # Other games on the shared GPU while this one ran, sampled every 20 s.
        seen, cpu = [], []
        while p.poll() is None and time.time() - t0 < 2400:
            seen.append(len(perfrun.others()))
            cpu.append(psutil.cpu_percent(1) if psutil else -1)
            time.sleep(19)
        if p.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
            line += " TIMEOUT"
        line += f" | other games during: {sum(1 for x in seen if x)}/{len(seen)} samples (max {max(seen, default=0)}); machine CPU {statistics.mean(cpu) if cpu else -1:.0f}% mean, {max(cpu, default=-1):.0f}% max"
    took = time.time() - t0
    ok = True
    for ext in (".json", ".csv"):
        src = os.path.join(SHOTS, name + ext)
        if os.path.exists(src) and os.path.getmtime(src) >= t0:
            shutil.copy2(src, os.path.join(out, name + ext))
        else:
            ok = False
    line += f" | {took:.0f}s wall, {'ok' if ok else 'NO RESULT'}"
    with open(os.path.join(out, "driver.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def windows(out, name, window=20.0):
    with open(os.path.join(out, name + ".csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    t0 = float(rows[0]["t"])
    print(f"| window | stage | cine % | fps | ms | p99 ms | gpu ms | gpu p99 | render cpu ms | main ms | draws | shadow draws | prims mean | prims max | foes |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    w = 0
    while True:
        a, b = t0 + w * window, t0 + (w + 1) * window
        sel = [r for r in rows if a <= float(r["t"]) < b]
        if not sel:
            break
        ms = sorted(float(r["ms"]) for r in sel)
        gpu = sorted(float(r["gpu"]) for r in sel)
        p99 = lambda v: v[min(len(v) - 1, int(len(v) * 0.99))]
        st = [STAGES[int(float(r["stage"]))] if float(r["stage"]) >= 0 else "-" for r in sel]
        stages = []
        for s in st:
            if s not in stages:
                stages.append(s)
        cine = sum(float(r["cine"]) for r in sel) / len(sel) * 100
        m = lambda c: statistics.mean(float(r[c]) for r in sel)
        print(f"| {a:.0f}-{b:.0f}s | {'/'.join(stages)} | {cine:.0f} | {1000 / statistics.mean(ms):.0f} | {statistics.mean(ms):.1f} | {p99(ms):.1f} | "
              f"{statistics.mean(gpu):.1f} | {p99(gpu):.1f} | {m('render_cpu') + m('setup'):.1f} | {m('main'):.2f} | {m('draws'):.0f} | {m('shadow_draws'):.0f} | "
              f"{m('primitives') / 1e6:.2f}M | {max(float(r['primitives']) for r in sel) / 1e6:.2f}M | {m('foes'):.0f} |")
        w += 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "export":
        export()
    elif a[0] == "run":
        run(a[1], a[2], a[3], a[4], a[5:])
    elif a[0] == "windows":
        windows(a[1], a[2], float(a[3]) if len(a) > 3 else 20.0)
