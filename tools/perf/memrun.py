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


def tree(p):
    try:
        return [p] + p.children(recursive=True)
    except psutil.Error:
        return [p]


def main():
    out, secs, cmd = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    rows = []
    t0 = time.time()
    with open(os.path.join(out, "log.txt"), "w", encoding="utf-8", errors="replace") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)
        ps = psutil.Process(proc.pid)
        try:
            while time.time() - t0 < secs and proc.poll() is None:
                ws = pv = 0
                for q in tree(ps):
                    try:
                        m = q.memory_info()
                        # (the game is the biggest of the tree: the console wrapper is a few MB)
                        if m.rss > ws: ws, pv = m.rss, getattr(m, "private", m.vms)
                    except psutil.Error:
                        pass
                rows.append((round(time.time() - t0, 1), round(ws / 1048576), round(pv / 1048576)))
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
        w.writerow(["t_s", "working_set_mb", "private_mb"])
        w.writerows(rows)
    if not rows:
        print("memrun: no samples"); return
    half = [r for r in rows if r[0] >= rows[-1][0] / 2]
    slope = 0.0
    if len(half) > 2:
        n = len(half); mx = sum(r[0] for r in half) / n; my = sum(r[1] for r in half) / n
        den = sum((r[0] - mx) ** 2 for r in half)
        slope = sum((r[0] - mx) * (r[1] - my) for r in half) / den * 60 if den else 0
    print(f"memrun: {len(rows)} samples over {rows[-1][0]:.0f} s, exit {exited}; working set peak {max(r[1] for r in rows)} MB, "
          f"end {rows[-1][1]} MB; private peak {max(r[2] for r in rows)} MB; second-half growth {slope:+.1f} MB/min")


if __name__ == "__main__":
    main()
