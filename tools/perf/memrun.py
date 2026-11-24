"""A game run with its memory sampled from outside (the tester lane, 23 Nov: a tester's next4 reached 6.8 GB working set).

    python tools/perf/memrun.py OUT_DIR SECONDS EXE [exe args ...]

Starts EXE (the exported game, or the Godot console exe with --path), samples the game process every 2 s for SECONDS
(working set, private bytes, both in MB), stops it, and writes OUT_DIR/mem.csv, OUT_DIR/log.txt and a summary line:
peak and end working set, peak private, and the growth per minute over the run's second half (a leak shows as a slope;
a flat run is ~0). The game's own monitors (static, video, texture memory, objects, resources) are logged by the game
under --mem-log N (src/MemLog.cs), into the same log.txt. Take a godot turn first (tools/turn.py run).
"""
import csv
import os
import subprocess
import sys
import time

import psutil

# the GPU counters every Nth sample (a read takes ~1-2 s); MEMRUN_GPU_EVERY=1 for a short probe
GPU_EVERY = max(1, int(os.environ.get("MEMRUN_GPU_EVERY", "10")))


def gpu(pid):
    """(Windows) The process's GPU memory in MB: dedicated (the card's own) and shared (system RAM the card uses)."""
    # (the instance is "pid_N_luid_..._phys_0", one per adapter: list them, then read; a wildcard path returned nothing)
    ps = (rf"$p = (Get-Counter -ListSet 'GPU Process Memory').PathsWithInstances | Where-Object {{ $_ -like '*pid_{pid}_*' -and "
          r"($_ -like '*\Dedicated Usage' -or $_ -like '*\Shared Usage') }; if ($p) { (Get-Counter $p -ErrorAction SilentlyContinue)"
          r".CounterSamples | ForEach-Object { $_.Path.Split([char]92)[-1].Replace(' ', '') + '=' + [int]($_.CookedValue/1MB) } }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=20)
    except Exception:
        return 0, 0
    d = s = 0
    for line in r.stdout.split():
        k, _, v = line.partition("=")
        if v.isdigit():
            if k.startswith("dedicated"): d += int(v)
            elif k.startswith("shared"): s += int(v)
    return d, s


def tree(p):
    try:
        return [p] + p.children(recursive=True)
    except psutil.Error:
        return [p]


def run(out, secs, cmd, env=None):
    """Runs cmd for secs, sampling it; writes out/mem.csv and out/log.txt; returns (rows, exit code or None)."""
    os.makedirs(out, exist_ok=True)
    rows = []
    t0 = time.time()
    with open(os.path.join(out, "log.txt"), "w", encoding="utf-8", errors="replace") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env)
        ps = psutil.Process(proc.pid)
        try:
            while time.time() - t0 < secs and proc.poll() is None:
                ws = pv = 0; big = ps
                for q in tree(ps):
                    try:
                        m = q.memory_info()
                        # (the game is the biggest of the tree: the console wrapper is a few MB)
                        if m.rss > ws: ws, pv, big = m.rss, getattr(m, "private", m.vms), q
                    except psutil.Error:
                        pass
                g = gpu(big.pid) if len(rows) % GPU_EVERY == GPU_EVERY // 2 else (None, None)
                # (log_bytes: how far the game's log had got at this sample, so a line in it can be placed in time:
                # memcheck's denloop route splits its samples by the log's "auto: map over #N" lines)
                rows.append((round(time.time() - t0, 1), round(ws / 1048576), round(pv / 1048576), g[0], g[1], os.fstat(lf.fileno()).st_size))
                time.sleep(2)
        finally:
            exited = proc.poll()
            for q in reversed(tree(ps)):
                try:
                    q.kill()
                except psutil.Error:
                    pass
    with open(os.path.join(out, "mem.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "working_set_mb", "private_mb", "gpu_dedicated_mb", "gpu_shared_mb", "log_bytes"])
        w.writerows(rows)
    return rows, exited


def slope_mb_min(rows, col=1):
    """Growth per minute of a column over the run's second half (least squares)."""
    half = [r for r in rows if r[0] >= rows[-1][0] / 2]
    slope = 0.0
    if len(half) > 2:
        n = len(half); mx = sum(r[0] for r in half) / n; my = sum(r[col] for r in half) / n
        den = sum((r[0] - mx) ** 2 for r in half)
        slope = sum((r[0] - mx) * (r[col] - my) for r in half) / den * 60 if den else 0
    return slope


def main():
    out, secs, cmd = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
    rows, exited = run(out, secs, cmd)
    if not rows:
        print("memrun: no samples"); return
    slope = slope_mb_min(rows)
    print(f"memrun: {len(rows)} samples over {rows[-1][0]:.0f} s, exit {exited}; working set peak {max(r[1] for r in rows)} MB, "
          f"end {rows[-1][1]} MB; private peak {max(r[2] for r in rows)} MB; second-half growth {slope:+.1f} MB/min; "
          f"gpu dedicated peak {max((r[3] or 0) for r in rows)} MB, shared peak {max((r[4] or 0) for r in rows)} MB")


if __name__ == "__main__":
    main()
